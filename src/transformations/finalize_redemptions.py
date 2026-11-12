from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"


def main():
    relationships = pd.read_csv(
        PROCESSED_PATH / "redemption_relationships.csv"
    )

    invalid_conditions = {
    "Unmatched assignment":
        relationships["assignment_match"] == "left_only",

    "Unmatched visit":
        relationships["visit_match"] == "left_only",

    "Holdout assignment redemption":
        (
            (relationships["assignment_match"] == "both")
            & (relationships["group"] == "holdout")
        ),

    "Player mismatch":
        (
            (relationships["assignment_match"] == "both")
            & (relationships["visit_match"] == "both")
            & (
                relationships["assignment_player_id"]
                != relationships["visit_player_id"]
            )
        ),

    "Property mismatch":
        (
            (relationships["assignment_match"] == "both")
            & (relationships["visit_match"] == "both")
            & (
                relationships["assignment_property"]
                != relationships["visit_property"]
            )
        ),

    "Outside response window":
        (
            (relationships["assignment_match"] == "both")
            & (relationships["visit_match"] == "both")
            & (
                (relationships["days_after_assignment"] < 0)
                | (relationships["days_after_assignment"] >= 14)
            )
        )
}

    invalid_ids = set()
    quarantine_reasons = {}

    for reason, condition in invalid_conditions.items():
        affected = relationships.loc[condition, "redemption_id"]

        for redemption_id in affected:
            invalid_ids.add(redemption_id)
            quarantine_reasons.setdefault(
                redemption_id, []
            ).append(reason)

    # Separate valid and invalid records.
    valid = relationships[
        ~relationships["redemption_id"].isin(invalid_ids)
    ].copy()

    quarantined = relationships[
        relationships["redemption_id"].isin(invalid_ids)
    ].copy()

    quarantined["quarantine_reason"] = (
        quarantined["redemption_id"].map(
            lambda redemption_id: "; ".join(
                quarantine_reasons[redemption_id]
            )
        )
    )

    # Save the final analytical redemption data.
    valid.to_csv(
        PROCESSED_PATH / "final_redemptions.csv",
        index=False
    )

    quarantined.to_csv(
        PROCESSED_PATH / "quarantined_redemption_relationships.csv",
        index=False
    )

    print("\nFINAL REDEMPTION CLEANING SUMMARY")
    print("=" * 50)
    print(f"Relationship records: {len(relationships):,}")
    print(f"Valid redemptions: {len(valid):,}")
    print(f"Quarantined redemptions: {len(quarantined):,}")

    print("\nQUARANTINE REASONS")
    print(
        quarantined[
            ["redemption_id", "quarantine_reason"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()