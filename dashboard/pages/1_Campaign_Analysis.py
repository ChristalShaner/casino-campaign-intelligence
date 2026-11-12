
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

# page config

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = (
    PROJECT_ROOT / "database" / "casino_analytics.duckdb"
)

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
st.set_page_config(
    page_title="Campaign Analysis",
    layout="wide"
)

# style 
st.markdown("""
<style>
    /* Main application background */
    .stApp {
        background-color: #101B18;
        color: #F2EBDD;
    }

    [data-testid="stHeader"] {
        background-color: #101B18;
    }

    /* Main content spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    /* Dashboard header */
    .dashboard-header,
    .page-header {
        background: linear-gradient(
            110deg,
            #123C30,
            #202C27
        );
        border: 1px solid #D4AF65;
        padding: 30px 35px;
        border-radius: 12px;
        margin-bottom: 25px;
    }

    .dashboard-header h1,
    .page-header h1 {
        color: #D4AF65;
        font-size: 32px;
        font-weight: 750;
    }

    .dashboard-header p,
    .page-header p {
        color: #F2EBDD;
        font-size: 15px;
    }

    /* Section headings */
    .section-title {
        color: #D4AF65;
        font-size: 21px;
        font-weight: 700;
        margin-top: 25px;
        margin-bottom: 12px;
    }

    /* KPI cards */
    .kpi-card {
        background-color: #202C27;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #665B40;
        min-height: 125px;
    }

    .kpi-label {
        color: #A6B2AA;
        font-size: 13px;
        font-weight: 600;
    }

    .kpi-value {
        color: #D4AF65;
        font-size: 28px;
        font-weight: 750;
        margin-top: 10px;
    }

    .kpi-caption {
        color: #A6B2AA;
        font-size: 12px;
    }

    /* Insight cards */
    .insight-card {
        background-color: #202C27;
        border-left: 5px solid #D4AF65;
        padding: 18px 22px;
        border-radius: 8px;
        margin-top: 15px;
    }

    .insight-card h4 {
        color: #D4AF65;
    }

    .insight-card p {
        color: #F2EBDD;
    }

    /* Data tables */
    [data-testid="stDataFrame"] {
        border: 1px solid #665B40;
        border-radius: 10px;
    }

    /* Selectboxes and inputs */
    div[data-baseweb="select"] > div {
        background-color: #202C27;
        border-color: #665B40;
        color: #F2EBDD;
    }

    /* Buttons */
    .stButton button {
        background-color: #123C30;
        color: #D4AF65;
        border: 1px solid #D4AF65;
        border-radius: 8px;
    }

    .stButton button:hover {
        background-color: #D4AF65;
        color: #101B18;
        border-color: #D4AF65;
    }

    /* Dividers */
    hr {
        border-color: #665B40;
    }

    /* General text */
    p, label, .stMarkdown {
        color: #F2EBDD;
    }
</style>
""", unsafe_allow_html=True)



# Load data


@st.cache_data
def load_data():

    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True
    )

    df = connection.execute("""
        SELECT *
        FROM fact_campaign_assignments
    """).df()

    connection.close()

    return df


try:
    df = load_data()

except Exception as error:
    st.error(f"Unable to load campaign data: {error}")
    st.stop()



# Header


st.markdown("""
    <div class="page-header">
        <h1>Campaign Analysis</h1>
        <p>
            Explore campaign effectiveness across casino properties
            and player segments.
        </p>
    </div>
""", unsafe_allow_html=True)


# Filters


st.markdown(
    '<div class="section-title">Campaign Filters</div>',
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns(3)

campaign_options = sorted(
    df["campaign_name"].dropna().unique().tolist()
)

property_options = sorted(
    df["property"].dropna().unique().tolist()
)

segment_options = sorted(
    df["player_segment"].dropna().unique().tolist()
)

with col1:
    selected_campaign = st.selectbox(
        "Campaign",
        ["All Campaigns"] + campaign_options
    )

with col2:
    selected_property = st.selectbox(
        "Property",
        ["All Properties"] + property_options
    )

with col3:
    selected_segment = st.selectbox(
        "Player Segment",
        ["All Segments"] + segment_options + ["Missing Segment"]
    )


filtered = df.copy()

if selected_campaign != "All Campaigns":
    filtered = filtered[
        filtered["campaign_name"] == selected_campaign
    ]

if selected_property != "All Properties":
    filtered = filtered[
        filtered["property"] == selected_property
    ]

if selected_segment == "Missing Segment":
    filtered = filtered[
        filtered["player_segment"].isna()
    ]

elif selected_segment != "All Segments":
    filtered = filtered[
        filtered["player_segment"] == selected_segment
    ]


if filtered.empty:
    st.warning("No assignments match the selected filters.")
    st.stop()



# Aggregate performance


summary = (
    filtered.groupby("group")
    .agg(
        assignments=("assignment_id", "nunique"),
        players_with_visits=(
            "response_visit_count",
            lambda x: (x > 0).sum()
        ),
        gaming_revenue=("response_gaming_revenue", "sum"),
        redemptions=("redemption_count", "sum"),
        promotional_cost=("promotional_cost", "sum")
    )
    .reset_index()
)

summary["visit_rate"] = (
    summary["players_with_visits"]
    / summary["assignments"]
)

summary["revenue_per_player"] = (
    summary["gaming_revenue"]
    / summary["assignments"]
)

summary["redemption_rate"] = (
    summary["redemptions"]
    / summary["assignments"]
)


offer = summary[
    summary["group"] == "offer"
]

holdout = summary[
    summary["group"] == "holdout"
]


def get_value(data, column):
    if data.empty:
        return 0
    return float(data.iloc[0][column])


offer_assignments = get_value(offer, "assignments")
holdout_assignments = get_value(holdout, "assignments")

offer_visit_rate = get_value(offer, "visit_rate")
holdout_visit_rate = get_value(holdout, "visit_rate")

offer_revenue = get_value(offer, "revenue_per_player")
holdout_revenue = get_value(holdout, "revenue_per_player")

visit_lift = offer_visit_rate - holdout_visit_rate
revenue_lift = offer_revenue - holdout_revenue

redemption_rate = get_value(
    offer,
    "redemption_rate"
)



# KPI cards


st.markdown(
    '<div class="section-title">Performance Summary</div>',
    unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Offer Assignments",
    f"{offer_assignments:,.0f}"
)

col2.metric(
    "Holdout Assignments",
    f"{holdout_assignments:,.0f}"
)

col3.metric(
    "Visit Rate Lift",
    f"{visit_lift:+.1%}"
)

col4.metric(
    "Offer Redemption Rate",
    f"{redemption_rate:.1%}"
)


# Offer vs holdout comparison


st.markdown(
    '<div class="section-title">Offer vs. Holdout</div>',
    unsafe_allow_html=True
)

if offer.empty or holdout.empty:

    st.warning(
        "Both offer and holdout groups are needed "
        "to calculate a comparison."
    )

else:

    left, right = st.columns(2)

    with left:

        st.markdown("**Visit Rate**")

        visit_chart = pd.DataFrame({
            "Group": ["Offer", "Holdout"],
            "Visit Rate": [
                offer_visit_rate,
                holdout_visit_rate
            ]
        })

        fig_visit = px.bar(
            visit_chart,
            x="Group",
            y="Visit Rate",
            color="Group",
            color_discrete_map={
                "Offer": TEAL,
                "Holdout": GOLD
            },
            text="Visit Rate"
        )

        fig_visit.update_traces(
            texttemplate="%{text:.1%}",
            textposition="outside"
        )

        fig_visit.update_layout(
            showlegend=False,
            yaxis_tickformat=".0%",
            yaxis_range=[0, 1],
            plot_bgcolor="white",
            paper_bgcolor="white",
            yaxis_title=None,
            xaxis_title=None
        )

        st.plotly_chart(
            fig_visit,
            use_container_width=True
        )

    with right:

        st.markdown("**Gaming Revenue per Assigned Player**")

        revenue_chart = pd.DataFrame({
            "Group": ["Offer", "Holdout"],
            "Revenue": [
                offer_revenue,
                holdout_revenue
            ]
        })

        fig_revenue = px.bar(
            revenue_chart,
            x="Group",
            y="Revenue",
            color="Group",
            color_discrete_map={
                "Offer": TEAL,
                "Holdout": GOLD
            },
            text="Revenue"
        )

        fig_revenue.update_traces(
            texttemplate="$%{text:,.2f}",
            textposition="outside"
        )

        fig_revenue.update_layout(
            showlegend=False,
            plot_bgcolor="white",
            paper_bgcolor="white",
            yaxis_title=None,
            xaxis_title=None
        )

        st.plotly_chart(
            fig_revenue,
            use_container_width=True
        )



# Segment comparison


st.markdown(
    '<div class="section-title">Player Segment Performance</div>',
    unsafe_allow_html=True
)

segment_data = (
    filtered.dropna(subset=["player_segment"])
    .groupby(["player_segment", "group"])
    .agg(
        assignments=("assignment_id", "nunique"),
        players_with_visits=(
            "response_visit_count",
            lambda x: (x > 0).sum()
        ),
        gaming_revenue=("response_gaming_revenue", "sum")
    )
    .reset_index()
)

segment_data["visit_rate"] = (
    segment_data["players_with_visits"]
    / segment_data["assignments"]
)

segment_data["revenue_per_player"] = (
    segment_data["gaming_revenue"]
    / segment_data["assignments"]
)

if not segment_data.empty:

    left, right = st.columns(2)

    with left:

        st.markdown("**Visit Rate by Player Segment**")

        fig_segment_visits = px.bar(
            segment_data,
            x="player_segment",
            y="visit_rate",
            color="group",
            barmode="group",
            color_discrete_map={
                "offer": TEAL,
                "holdout": GOLD
            },
            labels={
                "player_segment": "Player Segment",
                "visit_rate": "Visit Rate",
                "group": "Group"
            }
        )

        fig_segment_visits.update_layout(
            yaxis_tickformat=".0%",
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis_title=None,
            yaxis_title=None,
            legend_title=None
        )

        st.plotly_chart(
            fig_segment_visits,
            use_container_width=True
        )

    with right:

        st.markdown("**Revenue per Player by Segment**")

        fig_segment_revenue = px.bar(
            segment_data,
            x="player_segment",
            y="revenue_per_player",
            color="group",
            barmode="group",
            color_discrete_map={
                "offer": TEAL,
                "holdout": GOLD
            },
            labels={
                "player_segment": "Player Segment",
                "revenue_per_player": "Revenue per Player ($)",
                "group": "Group"
            }
        )

        fig_segment_revenue.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis_title=None,
            yaxis_title=None,
            legend_title=None
        )

        st.plotly_chart(
            fig_segment_revenue,
            use_container_width=True
        )



# Detailed data table


st.markdown(
    '<div class="section-title">Detailed Group Metrics</div>',
    unsafe_allow_html=True
)

display = summary.copy()

display["visit_rate"] = display["visit_rate"].map(
    lambda x: f"{x:.1%}"
)

display["redemption_rate"] = display["redemption_rate"].map(
    lambda x: f"{x:.1%}"
)

display["gaming_revenue"] = display["gaming_revenue"].map(
    lambda x: f"${x:,.2f}"
)

display["revenue_per_player"] = display[
    "revenue_per_player"
].map(
    lambda x: f"${x:,.2f}"
)

display["promotional_cost"] = display[
    "promotional_cost"
].map(
    lambda x: f"${x:,.2f}"
)

display.columns = [
    "Group",
    "Assignments",
    "Players with Visits",
    "Gaming Revenue",
    "Redemptions",
    "Promotional Cost",
    "Visit Rate",
    "Revenue per Player",
    "Redemption Rate"
]

st.dataframe(
    display,
    use_container_width=True,
    hide_index=True
)


# Methods

st.markdown("---")

st.caption(
    "Metrics use the 14-day response window. Visit rate is the "
    "percentage of assignments with at least one visit. Revenue "
    "per player uses all assigned players, including those with "
    "no visits. Gaming revenue can be negative."
)

st.caption(
    "Note: These filtered comparisons are descriptive offer-versus-holdout "
    "results. The official campaign incrementality estimates use matched "
    "campaign, property, and player-segment strata."
)
