from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"

EXTRACT_CUTOFF = pd.Timestamp("2026-10-31")


def main():

    # Load cleaned source datasets.
    assignments = pd.read_csv(
        PROCESSED_PATH / "clean_assignments.csv"
    )

    visits = pd.read_csv(
        PROCESSED_PATH / "clean_visits.csv"
    )

    redemptions = pd.read_csv(
        PROCESSED_PATH / "final_redemptions.csv"
    )

    # Convert dates.
    assignments["assigned_date"] = pd.to_datetime(
        assignments["assigned_date"]
    )

    visits["visit_date"] = pd.to_datetime(
        visits["visit_date"]
    )

    # Establish measurement windows.
    assignments["baseline_start"] = (
        assignments["assigned_date"]
        - pd.Timedelta(days=28)
    )

    assignments["response_end_exclusive"] = (
        assignments["assigned_date"]
        + pd.Timedelta(days=14)
    )

    assignments["response_window_complete"] = (
        assignments["response_end_exclusive"]
        <= EXTRACT_CUTOFF + pd.Timedelta(days=1)
    )

    # Match visits to each player's assigned property.
    player_visits = assignments[
        [
            "assignment_id",
            "player_id",
            "property",
            "assigned_date",
            "baseline_start",
            "response_end_exclusive"
        ]
    ].merge(
        visits,
        on=["player_id", "property"],
        how="inner",
        validate="one_to_many"
    )

    # Identify visits within each measurement period.
    baseline_mask = (
        (player_visits["visit_date"]
         >= player_visits["baseline_start"])
        & (player_visits["visit_date"]
           < player_visits["assigned_date"])
    )

    response_mask = (
        (player_visits["visit_date"]
         >= player_visits["assigned_date"])
        & (player_visits["visit_date"]
           < player_visits["response_end_exclusive"])
    )

    player_visits["baseline_visit"] = baseline_mask
    player_visits["response_visit"] = response_mask

    player_visits["baseline_revenue"] = (
        player_visits["gaming_revenue"]
        .where(baseline_mask, 0)
    )

    player_visits["response_revenue"] = (
        player_visits["gaming_revenue"]
        .where(response_mask, 0)
    )

    # Aggregate visits and gaming revenue by assignment.
    visit_metrics = (
        player_visits.groupby("assignment_id")
        .agg(
            baseline_visit_count=("baseline_visit", "sum"),
            baseline_gaming_revenue=("baseline_revenue", "sum"),
            response_visit_count=("response_visit", "sum"),
            response_gaming_revenue=("response_revenue", "sum")
        )
        .reset_index()
    )

    # Aggregate valid redemptions by assignment.
    redemption_metrics = (
        redemptions.groupby("assignment_id")
        .agg(
            redemption_count=("redemption_id", "nunique"),
            promotional_cost=("promo_cost", "sum")
        )
        .reset_index()
    )

    # Start with the full assignment population.
    fact = assignments.merge(
        visit_metrics,
        on="assignment_id",
        how="left",
        validate="one_to_one"
    )

    fact = fact.merge(
        redemption_metrics,
        on="assignment_id",
        how="left",
        validate="one_to_one"
    )

    # Players without visits or redemptions receive zero activity.
    metric_columns = [
        "baseline_visit_count",
        "baseline_gaming_revenue",
        "response_visit_count",
        "response_gaming_revenue",
        "redemption_count",
        "promotional_cost"
    ]

    fact[metric_columns] = fact[metric_columns].fillna(0)

    fact["redeemed"] = (
        fact["redemption_count"] > 0
    )

    # Final quality checks.
    assert len(fact) == 24000
    assert fact["assignment_id"].is_unique
    assert fact["response_window_complete"].all()

    # Save analytical fact table.
    output_path = PROCESSED_PATH / "fact_campaign_assignments.csv"

    fact.to_csv(output_path, index=False)

    print("\nCAMPAIGN FACT TABLE SUMMARY")
    print("=" * 50)

    print(f"Assignment records: {len(fact):,}")
    print(f"Unique assignments: {fact['assignment_id'].nunique():,}")
    print(f"Offer assignments: {(fact['group'] == 'offer').sum():,}")
    print(f"Holdout assignments: {(fact['group'] == 'holdout').sum():,}")

    print("\nPLAYER ACTIVITY")
    print(
        f"Players with response-period visits: "
        f"{(fact['response_visit_count'] > 0).sum():,}"
    )

    print(
        f"Players with valid redemptions: "
        f"{fact['redeemed'].sum():,}"
    )

    print(
        f"Total response-period gaming revenue: "
        f"${fact['response_gaming_revenue'].sum():,.2f}"
    )

    print(
        f"Total promotional cost: "
        f"${fact['promotional_cost'].sum():,.2f}"
    )

    print("\nOUTPUT FILE")
    print(output_path)


if __name__ == "__main__":
    main()