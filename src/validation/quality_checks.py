
import pandas as pd


def validate_redemptions(
    redemptions: pd.DataFrame,
    visits: pd.DataFrame
) -> pd.DataFrame:
    """
    Validate redemption records and return a detailed
    report of data quality issues.

    Original source records remain unchanged.
    """

    issues = []

    def add_issue(rows, issue_type, severity, details):
        """Add flagged records to the quality report."""

        for _, row in rows.iterrows():
            issues.append({
                "issue_type": issue_type,
                "severity": severity,
                "redemption_id": row["redemption_id"],
                "assignment_id": row["assignment_id"],
                "visit_id": row["visit_id"],
                "promo_cost": row["promo_cost"],
                "details": details
            })

    # 1. Duplicate redemption IDs
    duplicate_ids = redemptions[
        redemptions.duplicated(
            subset=["redemption_id"],
            keep=False
        )
    ]

    for redemption_id, group in duplicate_ids.groupby(
        "redemption_id"
    ):
        if group.drop(
            columns=["redemption_id"]
        ).drop_duplicates().shape[0] == 1:

            add_issue(
                group.iloc[1:],
                "EXACT_DUPLICATE",
                "WARNING",
                "Identical redemption record repeated."
            )

        else:
            add_issue(
                group,
                "CONFLICTING_PRIMARY_KEY",
                "CRITICAL",
                "Same redemption ID has conflicting values."
            )

    # 2. Multiple redemptions per assignment
    duplicate_assignments = redemptions[
        redemptions.duplicated(
            subset=["assignment_id"],
            keep=False
        )
    ]

    add_issue(
        duplicate_assignments,
        "MULTIPLE_REDEMPTIONS_PER_ASSIGNMENT",
        "CRITICAL",
        "More than one redemption references this assignment."
    )

    # 3. Multiple redemptions per visit
    duplicate_visits = redemptions[
        redemptions.duplicated(
            subset=["visit_id"],
            keep=False
        )
    ]

    add_issue(
        duplicate_visits,
        "MULTIPLE_REDEMPTIONS_PER_VISIT",
        "WARNING",
        "Multiple redemption records reference this visit."
    )

    # 4. Negative promotional costs
    negative_costs = redemptions[
        redemptions["promo_cost"] < 0
    ]

    add_issue(
        negative_costs,
        "NEGATIVE_PROMO_COST",
        "CRITICAL",
        "Promotional cost must be nonnegative."
    )

    # 5. Unmatched visit references
    unmatched_visits = redemptions[
        ~redemptions["visit_id"].isin(visits["visit_id"])
    ]

    add_issue(
        unmatched_visits,
        "UNMATCHED_VISIT",
        "CRITICAL",
        "Redemption references a nonexistent visit."
    )

    # Return structured results
    columns = [
        "issue_type",
        "severity",
        "redemption_id",
        "assignment_id",
        "visit_id",
        "promo_cost",
        "details"
    ]

    return pd.DataFrame(issues, columns=columns)
