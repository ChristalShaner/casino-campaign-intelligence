
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = PROJECT_ROOT / "data" / "raw"
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"


def clean_assignments(assignments: pd.DataFrame):
    """
    Clean assignment records while preserving questionable
    records in a quarantine dataset.

    Returns:
        clean: assignment records safe for analysis
        quarantine: excluded records with explanations
        warnings: retained records with noncritical issues
    """

    df = assignments.copy()
    quarantine_parts = []
    warnings_parts = []

    # 1. Remove exact duplicate rows
    exact_duplicate_mask = df.duplicated(keep="first")
    exact_duplicates = df[exact_duplicate_mask].copy()

    if not exact_duplicates.empty:
        exact_duplicates["quarantine_reason"] = (
            "Exact duplicate removed; original retained."
        )
        quarantine_parts.append(exact_duplicates)

    df = df.drop_duplicates().copy()

    # 2. Quarantine conflicting assignment IDs
    conflicting_ids = df[
        df.duplicated("assignment_id", keep=False)
    ]["assignment_id"].unique()

    conflicting = df[
        df["assignment_id"].isin(conflicting_ids)
    ].copy()

    if not conflicting.empty:
        conflicting["quarantine_reason"] = (
            "Conflicting values for the same assignment ID."
        )
        quarantine_parts.append(conflicting)

    df = df[
        ~df["assignment_id"].isin(conflicting_ids)
    ].copy()

    # 3. Validate group values
    valid_groups = ["offer", "holdout"]

    invalid_groups = df[
        ~df["group"].isin(valid_groups)
    ].copy()

    if not invalid_groups.empty:
        invalid_groups["quarantine_reason"] = (
            "Assignment group must be offer or holdout."
        )
        quarantine_parts.append(invalid_groups)

    df = df[df["group"].isin(valid_groups)].copy()

    # 4. Validate offer values
    invalid_offer_values = df[
        (
            (df["group"] == "offer") &
            (df["offer_value"].isna() | (df["offer_value"] < 0))
        ) |
        (
            (df["group"] == "holdout") &
            (df["offer_value"].notna())
        )
    ].copy()

    if not invalid_offer_values.empty:
        invalid_offer_values["quarantine_reason"] = (
            "Offer value is inconsistent with assignment group."
        )
        quarantine_parts.append(invalid_offer_values)

    df = df.drop(index=invalid_offer_values.index)

    # 5. Retain missing player segments but flag them
    missing_segments = df[
        df["player_segment"].isna()
    ].copy()

    if not missing_segments.empty:
        missing_segments["quality_warning"] = (
            "Player segment is missing; excluded from segment analysis."
        )
        warnings_parts.append(missing_segments)

    # 6. Build output datasets
    if quarantine_parts:
        quarantine = pd.concat(
            quarantine_parts,
            ignore_index=True
        )
    else:
        quarantine = pd.DataFrame(
            columns=list(assignments.columns) + ["quarantine_reason"]
        )

    if warnings_parts:
        warnings = pd.concat(
            warnings_parts,
            ignore_index=True
        )
    else:
        warnings = pd.DataFrame(
            columns=list(assignments.columns) + ["quality_warning"]
        )

    return df, quarantine, warnings


def main():
    assignments = pd.read_csv(
        RAW_PATH / "assignments.csv"
    )

    clean, quarantine, warnings = clean_assignments(assignments)

    PROCESSED_PATH.mkdir(parents=True, exist_ok=True)

    clean.to_csv(
        PROCESSED_PATH / "clean_assignments.csv",
        index=False
    )

    quarantine.to_csv(
        PROCESSED_PATH / "quarantined_assignments.csv",
        index=False
    )

    warnings.to_csv(
        PROCESSED_PATH / "assignment_quality_warnings.csv",
        index=False
    )

    print("\nASSIGNMENT CLEANING SUMMARY")
    print("=" * 45)
    print(f"Original records: {len(assignments):,}")
    print(f"Clean records: {len(clean):,}")
    print(f"Quarantined records: {len(quarantine):,}")
    print(f"Records with warnings: {len(warnings):,}")

    print("\nQUARANTINE REASONS")
    if quarantine.empty:
        print("None")
    else:
        print(
            quarantine["quarantine_reason"]
            .value_counts()
            .to_string()
        )

    print("\nQUALITY WARNINGS")
    if warnings.empty:
        print("None")
    else:
        print(
            warnings["quality_warning"]
            .value_counts()
            .to_string()
        )

    print("\nCLEAN GROUP DISTRIBUTION")
    print(clean["group"].value_counts().to_string())

    print("\nCLEAN CAMPAIGN DISTRIBUTION")
    print(
        clean.groupby("campaign_name")
        .size()
        .to_string()
    )

    print("\nOUTPUT FILES")
    print(PROCESSED_PATH / "clean_assignments.csv")
    print(PROCESSED_PATH / "quarantined_assignments.csv")
    print(PROCESSED_PATH / "assignment_quality_warnings.csv")


if __name__ == "__main__":
    main()
