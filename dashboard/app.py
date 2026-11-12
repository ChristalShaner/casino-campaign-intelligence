
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# configuring page

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATABASE_PATH = (
    PROJECT_ROOT / "database" / "casino_analytics.duckdb"
)

st.set_page_config(
    page_title="Casino Campaign Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed"
)

NAVY = "#002d3f"
CORAL = "#fc4f38"
GOLD = "#d8ab50"
TEAL = "#049da5"
LIGHT_TEAL = "#9ee6e8"
GRAY = "#666666"


# specific styling

st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: #f4f7f8;
        }}

        [data-testid="stHeader"] {{
            background-color: #f4f7f8;
        }}

        .block-container {{
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1500px;
        }}

        .dashboard-header {{
            background: linear-gradient(
                110deg,
                {NAVY},
                #064c60
            );
            padding: 30px 35px;
            border-radius: 14px;
            margin-bottom: 25px;
        }}

        .dashboard-header h1 {{
            color: white;
            font-size: 32px;
            margin-bottom: 5px;
        }}

        .dashboard-header p {{
            color: #c8e1e7;
            font-size: 15px;
            margin-bottom: 0;
        }}

        .section-title {{
            color: {NAVY};
            font-size: 21px;
            font-weight: 700;
            margin-top: 20px;
            margin-bottom: 12px;
        }}

        .kpi-card {{
            background-color: white;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #e3e9ec;
            min-height: 125px;
        }}

        .kpi-label {{
            color: {GRAY};
            font-size: 13px;
            font-weight: 600;
        }}

        .kpi-value {{
            color: {NAVY};
            font-size: 28px;
            font-weight: 750;
            margin-top: 10px;
        }}

        .kpi-caption {{
            color: {GRAY};
            font-size: 12px;
            margin-top: 5px;
        }}

        .insight-card {{
            background-color: white;
            border-left: 5px solid {TEAL};
            padding: 18px 22px;
            border-radius: 8px;
            margin-top: 15px;
        }}

        .insight-card h4 {{
            color: {NAVY};
            margin-bottom: 8px;
        }}

        .insight-card p {{
            color: #42545c;
            margin-bottom: 0;
        }}

        div[data-testid="stDataFrame"] {{
            border: 1px solid #e3e9ec;
            border-radius: 10px;
        }}
    </style>
    """,
    unsafe_allow_html=True
)


# database access

@st.cache_data
def load_campaign_data():

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True
    )

    campaigns = connection.execute("""
        SELECT *
        FROM mart_campaign_performance
        ORDER BY incremental_net_value DESC
    """).df()

    totals = connection.execute("""
        SELECT
            COUNT(*) AS total_assignments,

            SUM(
                CASE WHEN "group" = 'offer'
                THEN 1 ELSE 0 END
            ) AS offer_assignments,

            SUM(
                CASE WHEN "group" = 'holdout'
                THEN 1 ELSE 0 END
            ) AS holdout_assignments,

            SUM(
                CASE WHEN "group" = 'offer'
                THEN redemption_count ELSE 0 END
            ) AS total_redemptions,

            SUM(
                CASE WHEN "group" = 'offer'
                THEN promotional_cost ELSE 0 END
            ) AS promotional_cost

        FROM fact_campaign_assignments
    """).df()

    incrementality = connection.execute("""
        SELECT
            SUM(incremental_gaming_revenue),
            SUM(incremental_net_value),
            SUM(incremental_visits)
        FROM mart_campaign_incrementality
    """).fetchone()

    connection.close()

    return campaigns, totals, incrementality


# helpers for KPIs

def currency(value):
    return f"${value:,.0f}"


def percentage(value):
    return f"{value:.1%}"


def render_kpi(label, value, caption):

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# loading data

try:
    campaigns, totals, incrementality = load_campaign_data()

except Exception as error:
    st.error(f"Unable to load dashboard data: {error}")
    st.info(
        "Run the warehouse and SQL mart build scripts first."
    )
    st.stop()


total = totals.iloc[0]

total_assignments = int(total["total_assignments"])
offer_assignments = int(total["offer_assignments"])
total_redemptions = int(total["total_redemptions"])

redemption_rate = (
    total_redemptions / offer_assignments
    if offer_assignments else 0
)

promo_cost = float(total["promotional_cost"])

incremental_revenue = float(incrementality[0])
incremental_net_value = float(incrementality[1])
incremental_visits = float(incrementality[2])

overall_roi = (
    incremental_net_value / promo_cost
    if promo_cost else 0
)


# header

st.markdown(
    """
    <div class="dashboard-header">
        <h1>Casino Campaign Intelligence</h1>
        <p>
            Marketing performance, player engagement,
            and incremental campaign value
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# KPIs

st.markdown(
    '<div class="section-title">Executive Overview</div>',
    unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    render_kpi(
        "TOTAL ASSIGNMENTS",
        f"{total_assignments:,}",
        "Offer and holdout players"
    )

with col2:
    render_kpi(
        "REDEMPTION RATE",
        percentage(redemption_rate),
        f"{total_redemptions:,} valid redemptions"
    )

with col3:
    render_kpi(
        "INCREMENTAL REVENUE",
        currency(incremental_revenue),
        "Estimated gaming revenue"
    )

with col4:
    render_kpi(
        "INCREMENTAL NET VALUE",
        currency(incremental_net_value),
        f"{overall_roi:.1%} estimated net ROI"
    )


# Perforance charts

st.markdown(
    '<div class="section-title">Campaign Performance</div>',
    unsafe_allow_html=True
)

left, right = st.columns(2)

with left:

    st.markdown("**Estimated incremental net value**")

    fig_value = px.bar(
        campaigns,
        x="campaign_name",
        y="incremental_net_value",
        color="incremental_net_value",
        color_continuous_scale=[
            CORAL,
            GOLD,
            TEAL
        ],
        labels={
            "campaign_name": "Campaign",
            "incremental_net_value": "Net value ($)"
        },
        text="incremental_net_value"
    )

    fig_value.update_traces(
        texttemplate="$%{text:,.0f}",
        textposition="outside",
        cliponaxis=False
    )

    fig_value.update_layout(
        showlegend=False,
        coloraxis_showscale=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=20, t=25, b=10),
        xaxis_title=None,
        yaxis_title=None,
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="#e9eef0", zeroline=True)
    )

    st.plotly_chart(
        fig_value,
        use_container_width=True
    )


with right:

    st.markdown(
        "**Incremental revenue versus promotional cost**"
    )

    comparison = campaigns.melt(
        id_vars="campaign_name",
        value_vars=[
            "incremental_gaming_revenue",
            "actual_promotional_cost"
        ],
        var_name="metric",
        value_name="amount"
    )

    comparison["metric"] = comparison["metric"].map({
        "incremental_gaming_revenue": "Incremental revenue",
        "actual_promotional_cost": "Promotional cost"
    })

    fig_cost = px.bar(
        comparison,
        x="campaign_name",
        y="amount",
        color="metric",
        barmode="group",
        color_discrete_map={
            "Incremental revenue": TEAL,
            "Promotional cost": GOLD
        },
        labels={
            "campaign_name": "Campaign",
            "amount": "Amount ($)",
            "metric": "Metric"
        }
    )

    fig_cost.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=20, t=25, b=10),
        xaxis_title=None,
        yaxis_title=None,
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="#e9eef0"),
        legend_title=None
    )

    st.plotly_chart(
        fig_cost,
        use_container_width=True
    )

# Campaign performance table

st.markdown(
    '<div class="section-title">Campaign Scorecard</div>',
    unsafe_allow_html=True
)

display = campaigns[
    [
        "campaign_name",
        "offer_visit_rate",
        "holdout_visit_rate",
        "visit_rate_lift",
        "redemption_rate",
        "incremental_gaming_revenue",
        "actual_promotional_cost",
        "incremental_net_value",
        "roi"
    ]
].copy()

display.columns = [
    "Campaign",
    "Offer Visit Rate",
    "Holdout Visit Rate",
    "Visit Rate Lift",
    "Redemption Rate",
    "Incremental Revenue",
    "Promo Cost",
    "Net Value",
    "Net ROI"
]

for column in [
    "Offer Visit Rate",
    "Holdout Visit Rate",
    "Visit Rate Lift",
    "Redemption Rate",
    "Net ROI"
]:
    display[column] = display[column].map(
        lambda x: f"{x:.1%}"
    )

for column in [
    "Incremental Revenue",
    "Promo Cost",
    "Net Value"
]:
    display[column] = display[column].map(
        lambda x: f"${x:,.0f}"
    )

st.dataframe(
    display,
    use_container_width=True,
    hide_index=True
)


# insights

best_campaign = campaigns.iloc[0]

lowest_campaign = campaigns.loc[
    campaigns["incremental_net_value"].idxmin()
]

st.markdown(
    f"""
    <div class="insight-card">
        <h4>Key Business Insight</h4>
        <p>
            <strong>{best_campaign['campaign_name']}</strong>
            was the strongest campaign, generating an estimated
            <strong>
                {currency(best_campaign['incremental_net_value'])}
            </strong>
            in incremental net value with a
            <strong>{best_campaign['roi']:.1%}</strong>
            net ROI. In contrast,
            <strong>{lowest_campaign['campaign_name']}</strong>
            generated an estimated
            <strong>
                {currency(lowest_campaign['incremental_net_value'])}
            </strong>
            in incremental net value.
            Consider reviewing its offer structure and promotional cost.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# notes

st.markdown("---")

st.caption(
    "Methodology: Incremental value is estimated using offer-versus-holdout "
    "comparisons within campaign, property, and player-segment strata. "
    "Net value equals estimated incremental gaming revenue less promotional "
    "cost. This is not accounting profit. Estimates are point estimates; "
    "statistical significance has not yet been evaluated."
)

st.caption(
    "Data extract through October 31, 2026 | "
    "Campaign response window: 14 days"
)
