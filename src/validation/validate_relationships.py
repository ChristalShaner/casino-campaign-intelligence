
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"


def validate_relationships(
    redemptions: pd.DataFrame,
    assignments: pd.DataFrame,
    visits: pd.DataFrame
):
    """
    Validate redemption relationships against assignments and visits.

    Returns:
        joined: All redemption records with related assignment and visit data.
        issues: Detailed issue report, with one row per issue occurrence.
    """

    assignments = assignments.copy()
    visits = visits.copy()
    redemptions = redemptions.copy()

    # Convert dates
    assignments["assigned_date"] = pd.to_datetime(
        assignments["assigned_date"], errors="coerce"
    )
    visits["visit_date"] = pd.to_datetime(
        visits["visit_date"], errors="coerce"
    )

    # Join redemptions to assignments
    joined = redemptions.merge(
        assignments[
            [
                "assignment_id",
                "player_id",
                "campaign_id",
                "campaign_name",
                "property",
                "player_segment",
                "assigned_date",
                "group"
            ]
        ],
        on="assignment_id",
        how="left",
        indicator="assignment_match"
    )

    joined = joined.rename(
        columns={
            "player_id": "assignment_player_id",
            "property": "assignment_property"
        }
    )

    # Join the corresponding visit
    joined = joined.merge(
        visits[
            [
                "visit_id",
                "player_id",
                "property",
                "visit_date",
                "gaming_revenue"
            ]
        ].rename(
            columns={
                "player_id": "visit_player_id",
                "property": "visit_property"
            }
        ),
        on="visit_id",
        how="left",
        indicator="visit_match"
    )

    # Calculate days between assignment and visit
    joined["days_after_assignment"] = (
        joined["visit_date"] - joined["assigned_date"]
    ).dt.days

    # Define relationship checks
    checks = {
        "UNMATCHED_ASSIGNMENT":
            joined["assignment_match"] == "left_only",

        "UNMATCHED_VISIT":
            joined["visit_match"] == "left_only",

        "HOLDOUT_REDEMPTION": (
            (joined["assignment_match"] == "both")
            & (joined["group"] == "holdout")
        ),

        "PLAYER_MISMATCH": (
            (joined["assignment_match"] == "both")
            & (joined["visit_match"] == "both")
            & (
                joined["assignment_player_id"]
                != joined["visit_player_id"]
            )
        ),

        "PROPERTY_MISMATCH": (
            (joined["assignment_match"] == "both")
            & (joined["visit_match"] == "both")
            & (
                joined["assignment_property"]
                != joined["visit_property"]
            )
        ),

        "OUTSIDE_RESPONSE_WINDOW": (
            (joined["assignment_match"] == "both")
            & (joined["visit_match"] == "both")
            & (
                (joined["days_after_assignment"] < 0)
                | (joined["days_after_assignment"] >= 14)
            )
        )
    }

    # Build detailed issue report
    issue_parts = []

    for issue_type, mask in checks.items():
        affected = joined[mask].copy()

        if not affected.empty:
            affected["issue_type"] = issue_type
            issue_parts.append(affected)

    if issue_parts:
        issues = pd.concat(issue_parts, ignore_index=True)
    else:
        issues = pd.DataFrame(
            columns=list(joined.columns) + ["issue_type"]
        )

    return joined, issues


def main():
    # Load independently cleaned datasets
    assignments = pd.read_csv(
        PROCESSED_PATH / "clean_assignments.csv"
    )
    visits = pd.read_csv(
        PROCESSED_PATH / "clean_visits.csv"
    )
    redemptions = pd.read_csv(
        PROCESSED_PATH / "clean_redemptions.csv"
    )

    joined, issues = validate_relationships(
        redemptions,
        assignments,
        visits
    )

    # Save detailed results
    PROCESSED_PATH.mkdir(parents=True, exist_ok=True)

    joined.to_csv(
        PROCESSED_PATH / "redemption_relationships.csv",
        index=False
    )

    issues.to_csv(
        PROCESSED_PATH / "relationship_issues.csv",
        index=False
    )

    print("\nCROSS-DATASET VALIDATION SUMMARY")
    print("=" * 50)

    print(f"Clean assignments: {len(assignments):,}")
    print(f"Clean visits: {len(visits):,}")
    print(f"Clean redemptions: {len(redemptions):,}")

    print("\nRELATIONSHIP CHECKS")

    issue_counts = (
        issues["issue_type"].value_counts()
        if not issues.empty
        else pd.Series(dtype="int64")
    )

    issue_types = [
        "UNMATCHED_ASSIGNMENT",
        "UNMATCHED_VISIT",
        "HOLDOUT_REDEMPTION",
        "PLAYER_MISMATCH",
        "PROPERTY_MISMATCH",
        "OUTSIDE_RESPONSE_WINDOW"
    ]

    for issue_type in issue_types:
        print(
            f"{issue_type}: "
            f"{issue_counts.get(issue_type, 0):,}"
        )

    print("\nTOTAL ISSUE OCCURRENCES")
    print(len(issues))

    print(
        "\nUnique redemption IDs affected:",
        issues["redemption_id"].nunique()
        if not issues.empty else 0
    )

    # Investigate multiple redemption records per visit
    print("\nMULTIPLE REDEMPTIONS PER VISIT")

    repeated_visits = joined[
        joined.duplicated("visit_id", keep=False)
    ].sort_values("visit_id")

    print(
        f"Rows referencing repeated visits: "
        f"{len(repeated_visits):,}"
    )

    if not repeated_visits.empty:
        print(
            repeated_visits[
                [
                    "redemption_id",
                    "assignment_id",
                    "visit_id",
                    "assignment_player_id",
                    "visit_player_id",
                    "assignment_property",
                    "visit_property"
                ]
            ].to_string(index=False)
        )

    print("\nOUTPUT FILES")
    print(PROCESSED_PATH / "redemption_relationships.csv")
    print(PROCESSED_PATH / "relationship_issues.csv")


if __name__ == "__main__":
    main()
