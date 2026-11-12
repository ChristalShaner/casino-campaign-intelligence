
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = PROJECT_ROOT / "data" / "raw"
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"


def clean_visits(visits: pd.DataFrame):
    """
    Remove exact duplicate visits and quarantine
    conflicting visit IDs.

    Negative gaming revenue is valid and retained.
    """

    df = visits.copy()
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

    # 2. Identify conflicting visit IDs
    conflicting_ids = df[
        df.duplicated("visit_id", keep=False)
    ]["visit_id"].unique()

    conflicting = df[
        df["visit_id"].isin(conflicting_ids)
    ].copy()

    if not conflicting.empty:
        conflicting["quarantine_reason"] = (
            "Conflicting values for the same visit ID."
        )
        quarantine_parts.append(conflicting)

    df = df[
        ~df["visit_id"].isin(conflicting_ids)
    ].copy()

    # 3. Convert visit dates to datetime
    df["visit_date"] = pd.to_datetime(
        df["visit_date"],
        errors="coerce"
    )

    invalid_dates = df[df["visit_date"].isna()].copy()

    if not invalid_dates.empty:
        invalid_dates["quarantine_reason"] = (
            "Visit date is missing or invalid."
        )
        quarantine_parts.append(invalid_dates)

        df = df[df["visit_date"].notna()].copy()

    # 4. Build quarantine dataset
    if quarantine_parts:
        quarantine = pd.concat(
            quarantine_parts,
            ignore_index=True
        )
    else:
        quarantine = pd.DataFrame(
            columns=list(visits.columns) + ["quarantine_reason"]
        )

    return df, quarantine


def main():
    visits = pd.read_csv(RAW_PATH / "visits.csv")

    clean, quarantine = clean_visits(visits)

    PROCESSED_PATH.mkdir(parents=True, exist_ok=True)

    clean.to_csv(
        PROCESSED_PATH / "clean_visits.csv",
        index=False
    )

    quarantine.to_csv(
        PROCESSED_PATH / "quarantined_visits.csv",
        index=False
    )

    print("\nVISIT CLEANING SUMMARY")
    print("=" * 45)
    print(f"Original records: {len(visits):,}")
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

    print("\nGAMING REVENUE SUMMARY")
    print(clean["gaming_revenue"].describe().round(2))

    print("\nOUTPUT FILES")
    print(PROCESSED_PATH / "clean_visits.csv")
    print(PROCESSED_PATH / "quarantined_visits.csv")


if __name__ == "__main__":
    main()
