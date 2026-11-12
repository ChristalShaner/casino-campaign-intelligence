
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = PROJECT_ROOT / "data" / "raw"
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"


def clean_redemptions(redemptions: pd.DataFrame):
    """
    Remove exact duplicates and quarantine records that
    cannot safely be used in campaign analysis.

    Returns:
        clean: records safe for current analysis
        quarantine: excluded records with explanations
    """

    df = redemptions.copy()
    quarantine_parts = []

    # 1. Remove exact duplicate rows
    exact_duplicate_mask = df.duplicated(keep="first")
    exact_duplicates = df[exact_duplicate_mask].copy()

    if not exact_duplicates.empty:
        exact_duplicates["quarantine_reason"] = (
            "Exact duplicate removed; original retained."
        )
        quarantine_parts.append(exact_duplicates)

    df = df.drop_duplicates().copy()

    # 2. Quarantine conflicting redemption IDs
    conflicting_ids = df[
        df.duplicated("redemption_id", keep=False)
    ]["redemption_id"].unique()

    conflicting = df[
        df["redemption_id"].isin(conflicting_ids)
    ].copy()

    if not conflicting.empty:
        conflicting["quarantine_reason"] = (
            "Conflicting values for the same redemption ID."
        )
        quarantine_parts.append(conflicting)

    df = df[
        ~df["redemption_id"].isin(conflicting_ids)
    ].copy()

    # 3. Quarantine negative promotional costs
    negative_costs = df[df["promo_cost"] < 0].copy()

    if not negative_costs.empty:
        negative_costs["quarantine_reason"] = (
            "Promotional cost cannot be negative."
        )
        quarantine_parts.append(negative_costs)

    df = df[df["promo_cost"] >= 0].copy()

    # 4. Quarantine multiple redemptions per assignment
    duplicate_assignment_mask = df.duplicated(
        "assignment_id", keep=False
    )

    duplicate_assignments = df[
        duplicate_assignment_mask
    ].copy()

    if not duplicate_assignments.empty:
        duplicate_assignments["quarantine_reason"] = (
            "Multiple redemption records reference the same assignment."
        )
        quarantine_parts.append(duplicate_assignments)

    df = df[~duplicate_assignment_mask].copy()

    # 5. Combine quarantined records
    if quarantine_parts:
        quarantine = pd.concat(
            quarantine_parts,
            ignore_index=True
        )
    else:
        quarantine = pd.DataFrame(
            columns=list(redemptions.columns) + ["quarantine_reason"]
        )

    return df, quarantine


def main():
    redemptions = pd.read_csv(
        RAW_PATH / "redemptions.csv"
    )

    clean, quarantine = clean_redemptions(redemptions)

    PROCESSED_PATH.mkdir(parents=True, exist_ok=True)

    clean.to_csv(
        PROCESSED_PATH / "clean_redemptions.csv",
        index=False
    )

    quarantine.to_csv(
        PROCESSED_PATH / "quarantined_redemptions.csv",
        index=False
    )

    print("\nREDEMPTION CLEANING SUMMARY")
    print("=" * 45)
    print(f"Original records: {len(redemptions):,}")
    print(f"Clean records: {len(clean):,}")
    print(f"Quarantined records: {len(quarantine):,}")

    print("\nQUARANTINE REASONS")
    if quarantine.empty:
        print("None")
    else:
        print(
            quarantine["quarantine_reason"]
            .value_counts()
            .to_string()
        )

    print("\nOUTPUT FILES")
    print(PROCESSED_PATH / "clean_redemptions.csv")
    print(PROCESSED_PATH / "quarantined_redemptions.csv")


if __name__ == "__main__":
    main()
