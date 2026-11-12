
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"


def summarize_performance(data, group_columns):
    summary = (
        data.groupby(group_columns, dropna=False)
        .agg(
            assignments=("assignment_id", "nunique"),
            players_with_visits=(
                "response_visit_count",
                lambda x: (x > 0).sum()
            ),
            total_visits=("response_visit_count", "sum"),
            total_gaming_revenue=(
                "response_gaming_revenue", "sum"
            ),
            total_redemptions=("redemption_count", "sum"),
            total_promo_cost=("promotional_cost", "sum")
        )
        .reset_index()
    )

    summary["visit_rate"] = (
        summary["players_with_visits"]
        / summary["assignments"]
    )

    summary["avg_revenue_per_assigned_player"] = (
        summary["total_gaming_revenue"]
        / summary["assignments"]
    )

    summary["avg_revenue_per_visitor"] = (
        summary["total_gaming_revenue"]
        / summary["players_with_visits"].replace(0, pd.NA)
    )

    summary["redemption_rate"] = (
        summary["total_redemptions"]
        / summary["assignments"]
    )

    summary["promo_cost_per_assigned_player"] = (
        summary["total_promo_cost"]
        / summary["assignments"]
    )

    return summary


def main():

    fact = pd.read_csv(
        PROCESSED_PATH / "fact_campaign_assignments.csv"
    )

    # Overall offer versus holdout.
    overall = summarize_performance(
        fact,
        ["group"]
    )

    # Compare groups within randomized strata.
    stratified = summarize_performance(
        fact,
        [
            "campaign_id",
            "campaign_name",
            "property",
            "player_segment",
            "group"
        ]
    )

    # Save both summaries.
    overall.to_csv(
        PROCESSED_PATH / "group_performance_summary.csv",
        index=False
    )

    stratified.to_csv(
        PROCESSED_PATH / "stratified_performance_summary.csv",
        index=False
    )

    print("\nOVERALL OFFER VS HOLDOUT PERFORMANCE")
    print("=" * 70)

    print(
        overall[
            [
                "group",
                "assignments",
                "players_with_visits",
                "visit_rate",
                "total_gaming_revenue",
                "avg_revenue_per_assigned_player",
                "total_redemptions",
                "redemption_rate",
                "total_promo_cost"
            ]
        ].to_string(index=False)
    )

    print("\nSTRATIFIED PERFORMANCE")
    print("=" * 70)

    print(
        stratified[
            [
                "campaign_name",
                "property",
                "player_segment",
                "group",
                "assignments",
                "visit_rate",
                "avg_revenue_per_assigned_player",
                "redemption_rate",
                "total_promo_cost"
            ]
        ].to_string(index=False)
    )

    print("\nOUTPUT FILES")
    print(PROCESSED_PATH / "group_performance_summary.csv")
    print(PROCESSED_PATH / "stratified_performance_summary.csv")


if __name__ == "__main__":
    main()
