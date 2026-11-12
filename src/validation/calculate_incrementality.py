
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"

STRATA = [
    "campaign_id",
    "campaign_name",
    "property",
    "player_segment"
]


def calculate_incrementality(fact: pd.DataFrame):
    """
    Calculate stratified campaign incrementality.

    Returns:
        comparison: Offer vs holdout results for each stratum.
        campaign_results: Aggregated campaign-level results.
        overall: Overall stratified results.
    """

    eligible = fact.dropna(
        subset=["player_segment"]
    ).copy()

    # Summarize each randomized group within each stratum.
    summary = (
        eligible.groupby(STRATA + ["group"])
        .agg(
            assignments=("assignment_id", "nunique"),
            players_with_visits=(
                "response_visit_count",
                lambda x: (x > 0).sum()
            ),
            gaming_revenue=(
                "response_gaming_revenue", "sum"
            ),
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

    # Separate randomized groups.
    offer = summary[
        summary["group"] == "offer"
    ].drop(columns="group")

    holdout = summary[
        summary["group"] == "holdout"
    ].drop(columns="group")

    # Outer join allows us to detect unmatched strata.
    comparison = offer.merge(
        holdout,
        on=STRATA,
        how="outer",
        suffixes=("_offer", "_holdout"),
        indicator=True,
        validate="one_to_one"
    )

    unmatched = comparison[
        comparison["_merge"] != "both"
    ]

    if not unmatched.empty:
        raise ValueError(
            "Every stratum must contain both offer and holdout "
            f"assignments. Unmatched strata: {len(unmatched)}"
        )

    comparison = comparison.drop(columns="_merge")

    comparison["visit_rate_lift"] = (
        comparison["visit_rate_offer"]
        - comparison["visit_rate_holdout"]
    )

    comparison["revenue_per_player_lift"] = (
        comparison["revenue_per_player_offer"]
        - comparison["revenue_per_player_holdout"]
    )

    # Estimate incremental results across the offer population.
    comparison["incremental_visits"] = (
        comparison["visit_rate_lift"]
        * comparison["assignments_offer"]
    )

    comparison["incremental_gaming_revenue"] = (
        comparison["revenue_per_player_lift"]
        * comparison["assignments_offer"]
    )

    comparison["incremental_net_value"] = (
        comparison["incremental_gaming_revenue"]
        - comparison["promotional_cost_offer"]
    )

    # Campaign-level results.
    campaign_results = (
        comparison.groupby(
            ["campaign_id", "campaign_name"]
        )
        .agg(
            eligible_offer_assignments=(
                "assignments_offer", "sum"
            ),
            eligible_holdout_assignments=(
                "assignments_holdout", "sum"
            ),
            incremental_visits=(
                "incremental_visits", "sum"
            ),
            incremental_gaming_revenue=(
                "incremental_gaming_revenue", "sum"
            ),
            promotional_cost=(
                "promotional_cost_offer", "sum"
            ),
            incremental_net_value=(
                "incremental_net_value", "sum"
            )
        )
        .reset_index()
    )

    campaign_results["incremental_revenue_per_offer"] = (
        campaign_results["incremental_gaming_revenue"]
        / campaign_results["eligible_offer_assignments"]
    )

    campaign_results["net_value_per_offer"] = (
        campaign_results["incremental_net_value"]
        / campaign_results["eligible_offer_assignments"]
    )

    campaign_results["roi"] = (
        campaign_results["incremental_net_value"]
        / campaign_results["promotional_cost"].replace(0, pd.NA)
    )

    # Overall stratified estimate.
    overall = pd.DataFrame([{
        "eligible_offer_assignments":
            comparison["assignments_offer"].sum(),

        "eligible_holdout_assignments":
            comparison["assignments_holdout"].sum(),

        "incremental_visits":
            comparison["incremental_visits"].sum(),

        "incremental_gaming_revenue":
            comparison["incremental_gaming_revenue"].sum(),

        "promotional_cost":
            comparison["promotional_cost_offer"].sum(),

        "incremental_net_value":
            comparison["incremental_net_value"].sum()
    }])

    overall["roi"] = (
        overall["incremental_net_value"]
        / overall["promotional_cost"].replace(0, pd.NA)
    )

    return comparison, campaign_results, overall


def main():
    fact = pd.read_csv(
        PROCESSED_PATH / "fact_campaign_assignments.csv"
    )

    comparison, campaign_results, overall = (
        calculate_incrementality(fact)
    )

    PROCESSED_PATH.mkdir(parents=True, exist_ok=True)

    comparison.to_csv(
        PROCESSED_PATH / "stratum_incrementality.csv",
        index=False
    )

    campaign_results.to_csv(
        PROCESSED_PATH / "campaign_incrementality.csv",
        index=False
    )

    overall.to_csv(
        PROCESSED_PATH / "overall_incrementality.csv",
        index=False
    )

    print("\nCAMPAIGN INCREMENTAL VALUE")
    print("=" * 80)

    print(
        campaign_results[
            [
                "campaign_name",
                "eligible_offer_assignments",
                "incremental_visits",
                "incremental_gaming_revenue",
                "promotional_cost",
                "incremental_net_value",
                "roi"
            ]
        ].to_string(index=False)
    )

    print("\nOVERALL STRATIFIED INCREMENTAL VALUE")
    print("=" * 80)

    print(overall.to_string(index=False))

    print("\nVALIDATION")
    print("=" * 80)
    print(f"Matched strata: {len(comparison):,}")
    print(
        "Offer assignments included:",
        f"{comparison['assignments_offer'].sum():,}"
    )
    print(
        "Holdout assignments included:",
        f"{comparison['assignments_holdout'].sum():,}"
    )
    print(
        "Offer assignments excluded due to missing segment:",
        f"{fact['player_segment'].isna().sum():,}"
    )

    print("\nOUTPUT FILES")
    print("stratum_incrementality.csv")
    print("campaign_incrementality.csv")
    print("overall_incrementality.csv")


if __name__ == "__main__":
    main()
