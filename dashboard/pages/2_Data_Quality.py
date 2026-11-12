from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st


# page config

st.set_page_config(
    page_title="Data Quality | Casino Campaign Intelligence",
    layout="wide"
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "database" / "casino_analytics.duckdb"

# Casino luxury color palette

BG = "#101B18"
PANEL = "#202C27"
EMERALD = "#123C30"
GOLD = "#D4AF65"
BURGUNDY = "#722F3E"
IVORY = "#F2EBDD"
MUTED = "#A6B2AA"

TEAL = "#4EAA91"
CORAL = "#C96B62"
RED = "#C94A4A"


# connect to database

@st.cache_data
def load_quality_data():

    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True
    )

    try:
        reconciliation = connection.execute(
            "SELECT * FROM data_quality_reconciliation"
        ).df()

        issues = connection.execute(
            "SELECT * FROM data_quality_issues"
        ).df()

        issue_summary = connection.execute(
            "SELECT * FROM data_quality_issue_summary"
        ).df()

        quarantine = connection.execute(
            "SELECT * FROM data_quality_quarantine_summary"
        ).df()

        warnings = connection.execute(
            "SELECT * FROM data_quality_warnings"
        ).df()

    finally:
        connection.close()

    return (
        reconciliation,
        issues,
        issue_summary,
        quarantine,
        warnings
    )


try:
    (
        reconciliation,
        issues,
        issue_summary,
        quarantine,
        warnings
    ) = load_quality_data()

except Exception as error:
    st.error(f"Unable to load data quality tables: {error}")
    st.stop()


# header

st.markdown(
    f"""
    <div style="
        background-color: {BG};
        padding: 25px 30px;
        border-radius: 10px;
        margin-bottom: 25px;
    ">
        <h1 style="color: white; margin: 0;">
            Data Quality & Pipeline Health
        </h1>
        <p style="
            color: #ededed;
            margin: 8px 0 0 0;
            font-size: 16px;
        ">
            Monitor source data quality, validation issues,
            quarantined records, and pipeline reconciliation.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)






# overall metrics

total_original = int(reconciliation["original_records"].sum())
total_clean = int(reconciliation["clean_records"].sum())
total_excluded = int(reconciliation["excluded_records"].sum())

overall_retention = (
    total_clean / total_original * 100
    if total_original else 0
)

critical_count = int(
    issues.loc[issues["severity"] == "CRITICAL"].shape[0]
)

warning_count = int(
    issues.loc[issues["severity"] == "WARNING"].shape[0]
)

total_issue_occurrences = len(issues)

# KPIs

st.subheader("Pipeline Summary")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Original Records",
    f"{total_original:,}"
)

col2.metric(
    "Clean Records",
    f"{total_clean:,}"
)

col3.metric(
    "Excluded Records",
    f"{total_excluded:,}"
)

col4.metric(
    "Overall Retention",
    f"{overall_retention:.2f}%"
)

st.divider()


# reconciling records

st.subheader("Source-to-Clean Reconciliation")

st.caption(
    "Compare the original source population with the records "
    "retained after cleaning and validation."
)

reconciliation_display = reconciliation.copy()

reconciliation_display["dataset"] = (
    reconciliation_display["dataset"].str.title()
)

reconciliation_display = reconciliation_display.rename(
    columns={
        "dataset": "Dataset",
        "original_records": "Original Records",
        "clean_records": "Clean Records",
        "excluded_records": "Excluded Records",
        "retention_rate_pct": "Retention Rate (%)"
    }
)

st.dataframe(
    reconciliation_display,
    hide_index=True,
    width="stretch",
    column_config={
        "Retention Rate (%)": st.column_config.ProgressColumn(
            "Retention Rate (%)",
            min_value=0,
            max_value=100,
            format="%.2f%%"
        )
    }
)

reconciliation_chart = reconciliation.melt(
    id_vars="dataset",
    value_vars=["clean_records", "excluded_records"],
    var_name="record_status",
    value_name="record_count"
)

reconciliation_chart["record_status"] = (
    reconciliation_chart["record_status"]
    .map({
        "clean_records": "Clean Records",
        "excluded_records": "Excluded Records"
    })
)

fig_reconciliation = px.bar(
    reconciliation_chart,
    x="dataset",
    y="record_count",
    color="record_status",
    barmode="stack",
    text_auto=",",
    color_discrete_map={
        "Clean Records": TEAL,
        "Excluded Records": CORAL
    },
    labels={
        "dataset": "Dataset",
        "record_count": "Records",
        "record_status": "Record Status"
    },
    title="Record Retention by Dataset"
)

fig_reconciliation.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    legend_title_text="",
    margin=dict(t=60, b=20),
    yaxis=dict(title="Number of Records"),
    xaxis=dict(title="")
)

st.plotly_chart(
    fig_reconciliation,
    width="stretch"
)

st.divider()


# problem message

st.subheader("Validation Issues")

st.caption(
    "Issue occurrences detected during source profiling "
    "and relationship validation. A single record can "
    "trigger multiple issues."
)

col1, col2, col3 = st.columns(3)

col1.metric(
    "Total Issue Occurrences",
    f"{total_issue_occurrences:,}"
)

col2.metric(
    "Critical Occurrences",
    f"{critical_count:,}"
)

col3.metric(
    "Warning Occurrences",
    f"{warning_count:,}"
)

# Severity chart
severity_summary = (
    issue_summary
    .groupby("severity", as_index=False)["issue_count"]
    .sum()
)

fig_severity = px.pie(
    severity_summary,
    names="severity",
    values="issue_count",
    hole=0.55,
    color="severity",
    color_discrete_map={
        "CRITICAL": RED,
        "WARNING": GOLD
    },
    title="Issue Severity Distribution"
)

fig_severity.update_traces(
    textposition="inside",
    textinfo="label+value"
)

fig_severity.update_layout(
    margin=dict(t=60, b=20),
    legend_title_text=""
)

# Issue type chart
issue_chart = (
    issue_summary
    .groupby(["issue_type", "severity"], as_index=False)
    ["issue_count"]
    .sum()
    .sort_values("issue_count")
)

fig_issues = px.bar(
    issue_chart,
    x="issue_count",
    y="issue_type",
    color="severity",
    orientation="h",
    text="issue_count",
    color_discrete_map={
        "CRITICAL": RED,
        "WARNING": GOLD
    },
    title="Validation Issues by Type",
    labels={
        "issue_count": "Issue Occurrences",
        "issue_type": "Issue Type",
        "severity": "Severity"
    }
)

fig_issues.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    legend_title_text="",
    margin=dict(t=60, b=20),
    xaxis=dict(title="Issue Occurrences"),
    yaxis=dict(title="")
)

left, right = st.columns([1, 2])

with left:
    st.plotly_chart(
        fig_severity,
        width="stretch"
    )

with right:
    st.plotly_chart(
        fig_issues,
        width="stretch"
    )

with st.expander("View detailed issue summary"):

    issue_display = issue_summary.rename(
        columns={
            "dataset": "Dataset",
            "issue_type": "Issue Type",
            "severity": "Severity",
            "issue_count": "Occurrences"
        }
    )

    st.dataframe(
        issue_display,
        hide_index=True,
        width="stretch"
    )

st.divider()


# analysis of quarantined records

st.subheader("Quarantined Records")

st.caption(
    "Records excluded from the analytical datasets, "
    "grouped by the reason they were quarantined."
)

quarantine_chart = quarantine.copy()

quarantine_chart["dataset"] = (
    quarantine_chart["dataset"].str.replace("_", " ").str.title()
)

quarantine_chart = quarantine_chart.sort_values(
    "record_count",
    ascending=True
)

fig_quarantine = px.bar(
    quarantine_chart,
    x="record_count",
    y="quarantine_reason",
    color="dataset",
    orientation="h",
    text="record_count",
    color_discrete_sequence=[
        TEAL,
        CORAL,
        GOLD,
        EMERALD
    ],
    title="Records Excluded by Quarantine Reason",
    labels={
        "record_count": "Records",
        "quarantine_reason": "Quarantine Reason",
        "dataset": "Dataset"
    }
)

fig_quarantine.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    legend_title_text="Dataset",
    margin=dict(t=60, b=20),
    xaxis=dict(title="Number of Records"),
    yaxis=dict(title="")
)

st.plotly_chart(
    fig_quarantine,
    width="stretch"
)

with st.expander("View quarantine summary table"):

    quarantine_display = quarantine.rename(
        columns={
            "dataset": "Dataset",
            "quarantine_reason": "Quarantine Reason",
            "record_count": "Records"
        }
    )

    st.dataframe(
        quarantine_display,
        hide_index=True,
        width="stretch"
    )

st.divider()


# data quality warnings

st.subheader("Retained Records with Warnings")

st.caption(
    "Some records can remain usable for overall analysis "
    "while being excluded from specific analytical breakdowns."
)

if not warnings.empty:

    st.warning(
        f"{len(warnings):,} assignment record(s) contain "
        "a data quality warning but were retained."
    )

    warning_columns = [
        column for column in [
            "assignment_id",
            "campaign_name",
            "property",
            "player_segment",
            "quality_warning"
        ]
        if column in warnings.columns
    ]

    st.dataframe(
        warnings[warning_columns],
        hide_index=True,
        width="stretch"
    )

else:
    st.success("No retained records have outstanding warnings.")


# method notes

st.divider()

with st.expander("Data Quality Methodology"):

    st.markdown(
        """
        **Assignment validation**
        - Removed exact duplicate copies.
        - Quarantined conflicting assignment IDs.
        - Validated offer and holdout group values.
        - Retained missing player segments with a warning.

        **Visit validation**
        - Removed exact duplicate copies.
        - Quarantined conflicting visit IDs.
        - Validated visit dates.
        - Preserved negative gaming revenue as valid data.

        **Redemption validation**
        - Removed exact duplicate copies.
        - Quarantined conflicting redemption IDs.
        - Checked for multiple redemptions per assignment.
        - Rejected negative promotional costs.
        - Validated assignment and visit relationships.
        - Checked player, property, group, and response-window consistency.

        **Important analytical distinction**

        Issue occurrences are not necessarily unique records.
        A redemption can trigger more than one validation rule.
        Quarantined records are excluded from the final analytical
        datasets, while retained warnings are tracked separately.
        """
    )


# footer

st.markdown(
    f"""
    <div style="
        background-color: {BG};
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        margin-top: 25px;
    ">
        <span style="color: white; font-size: 12px;">
            Casino Campaign Intelligence by Christal Love
        </span>
    </div>
    """,
    unsafe_allow_html=True
)
