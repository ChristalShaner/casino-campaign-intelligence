
from pathlib import Path

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = PROJECT_ROOT / "data" / "raw"
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"
DATABASE_PATH = PROJECT_ROOT / "database" / "casino_analytics.duckdb"


def load_csv(folder, filename):
    """Load a CSV and give a clear error if it is missing."""
    path = folder / filename

    if not path.exists():
        raise FileNotFoundError(f"Could not find: {path}")

    return pd.read_csv(path)


def register_table(connection, table_name, dataframe):
    """Replace a DuckDB table using a pandas DataFrame."""
    connection.register("temp_dataframe", dataframe)
    connection.execute(
        f"CREATE OR REPLACE TABLE {table_name} AS "
        "SELECT * FROM temp_dataframe"
    )
    connection.unregister("temp_dataframe")


def main():

    print("BUILDING DATA QUALITY TABLES")
    print("=" * 60)

    # --------------------------------------------------
    # 1. Load raw and final cleaned datasets
    # --------------------------------------------------

    datasets = {
        "assignments": {
            "raw": load_csv(RAW_PATH, "assignments.csv"),
            "clean": load_csv(PROCESSED_PATH, "clean_assignments.csv"),
        },
        "visits": {
            "raw": load_csv(RAW_PATH, "visits.csv"),
            "clean": load_csv(PROCESSED_PATH, "clean_visits.csv"),
        },
        "redemptions": {
            "raw": load_csv(RAW_PATH, "redemptions.csv"),
            "clean": load_csv(PROCESSED_PATH, "final_redemptions.csv"),
        },
    }

    # --------------------------------------------------
    # 2. Build reconciliation summary
    # --------------------------------------------------

    reconciliation_rows = []

    for dataset_name, frames in datasets.items():

        raw_count = len(frames["raw"])
        clean_count = len(frames["clean"])
        excluded_count = raw_count - clean_count

        retention_rate = (
            clean_count / raw_count * 100
            if raw_count > 0 else 0
        )

        reconciliation_rows.append({
            "dataset": dataset_name,
            "original_records": raw_count,
            "clean_records": clean_count,
            "excluded_records": excluded_count,
            "retention_rate_pct": round(retention_rate, 2),
        })

    reconciliation = pd.DataFrame(reconciliation_rows)

    # --------------------------------------------------
    # 3. Load detailed issue records
    # --------------------------------------------------

    redemption_issues = load_csv(
        PROCESSED_PATH,
        "redemption_quality_issues.csv"
    )

    relationship_issues = load_csv(
        PROCESSED_PATH,
        "relationship_issues.csv"
    )

    # Give relationship issues a severity for reporting.
    relationship_issues = relationship_issues.copy()
    relationship_issues["severity"] = "CRITICAL"

    # Standardize the two issue datasets.
    redemption_issues = redemption_issues.copy()
    redemption_issues["dataset"] = "redemptions"

    relationship_issues["dataset"] = "redemption_relationships"

    quality_issues = pd.concat(
        [
            redemption_issues[
                ["dataset", "issue_type", "severity"]
            ],
            relationship_issues[
                ["dataset", "issue_type", "severity"]
            ],
        ],
        ignore_index=True
    )

    issue_summary = (
        quality_issues
        .groupby(["dataset", "issue_type", "severity"])
        .size()
        .reset_index(name="issue_count")
        .sort_values(
            ["severity", "dataset", "issue_count"],
            ascending=[True, True, False]
        )
    )

    # --------------------------------------------------
    # 4. Build quarantine reason summary
    # --------------------------------------------------

    quarantine_files = {
        "assignments": "quarantined_assignments.csv",
        "visits": "quarantined_visits.csv",
        "redemptions": "quarantined_redemptions.csv",
        "redemption_relationships":
            "quarantined_redemption_relationships.csv",
    }

    quarantine_frames = []

    for dataset_name, filename in quarantine_files.items():

        df = load_csv(PROCESSED_PATH, filename)

        if "quarantine_reason" not in df.columns:
            continue

        summary = (
            df["quarantine_reason"]
            .value_counts()
            .rename_axis("quarantine_reason")
            .reset_index(name="record_count")
        )

        summary["dataset"] = dataset_name
        quarantine_frames.append(summary)

    quarantine_summary = pd.concat(
        quarantine_frames,
        ignore_index=True
    )

    # --------------------------------------------------
    # 5. Load assignment warnings
    # --------------------------------------------------

    warnings = load_csv(
        PROCESSED_PATH,
        "assignment_quality_warnings.csv"
    )

    # --------------------------------------------------
    # 6. Write quality tables to DuckDB
    # --------------------------------------------------

    connection = duckdb.connect(str(DATABASE_PATH))

    try:
        register_table(
            connection,
            "data_quality_reconciliation",
            reconciliation
        )

        register_table(
            connection,
            "data_quality_issues",
            quality_issues
        )

        register_table(
            connection,
            "data_quality_issue_summary",
            issue_summary
        )

        register_table(
            connection,
            "data_quality_quarantine_summary",
            quarantine_summary
        )

        register_table(
            connection,
            "data_quality_warnings",
            warnings
        )

    finally:
        connection.close()

    # --------------------------------------------------
    # 7. Print results
    # --------------------------------------------------

    print("\nRECORD RECONCILIATION")
    print(reconciliation.to_string(index=False))

    print("\nQUALITY ISSUE SUMMARY")
    print(issue_summary.to_string(index=False))

    print("\nQUARANTINE SUMMARY")
    print(quarantine_summary.to_string(index=False))

    print("\nDATABASE TABLES CREATED")
    print(" - data_quality_reconciliation")
    print(" - data_quality_issues")
    print(" - data_quality_issue_summary")
    print(" - data_quality_quarantine_summary")
    print(" - data_quality_warnings")

    print("\nData quality tables successfully loaded!")


if __name__ == "__main__":
    main()
