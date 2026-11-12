
from pathlib import Path
import pandas as pd


# Resolve the project root regardless of where the script is executed
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw"


def load_source(filename: str) -> pd.DataFrame:
    """Load a CSV source into a Pandas DataFrame."""

    file_path = RAW_DATA_PATH / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"Source file not found: {file_path}"
        )

    return pd.read_csv(file_path)


def profile_dataframe(
    df: pd.DataFrame,
    dataset_name: str,
    primary_key: str
) -> None:
    """Display a basic data quality and profiling report."""

    print("\n" + "=" * 60)
    print(f"DATA PROFILE: {dataset_name.upper()}")
    print("=" * 60)

    # Basic information
    print(f"\nTotal records: {len(df):,}")
    print(f"Total columns: {len(df.columns)}")

    # Column information
    print("\nCOLUMN INFORMATION")
    print(df.dtypes.to_string())

    # Missing values
    print("\nMISSING VALUES")
    missing = df.isnull().sum()
    print(missing[missing > 0] if missing.any() else "None")

    # Duplicate primary keys
    print("\nDUPLICATE PRIMARY KEYS")
    duplicates = df[df.duplicated(
        subset=[primary_key],
        keep=False
    )]

    if duplicates.empty:
        print("None")
    else:
        print(duplicates.sort_values(primary_key).to_string(index=False))

    # Exact duplicate records
    print("\nEXACT DUPLICATE ROWS")
    print(df.duplicated().sum())

    # Numeric summaries
    print("\nNUMERIC SUMMARIES")
    numeric_columns = df.select_dtypes(include="number").columns

    if len(numeric_columns) > 0:
        print(df[numeric_columns].describe().round(2))

    # Date summaries
    print("\nDATE SUMMARIES")

    for column in df.columns:
        if "date" in column.lower():
            dates = pd.to_datetime(df[column], errors="coerce")
            print(f"{column}: {dates.min()} to {dates.max()}")


def main():

    # Load available sources
    visits = load_source("visits.csv")
    redemptions = load_source("redemptions.csv")
    assignments = load_source("assignments.csv")

    # Profile each dataset
    profile_dataframe(
        visits,
        "Visits",
        "visit_id"
    )

    profile_dataframe(
        redemptions,
        "Redemptions",
        "redemption_id"
    )

    profile_dataframe(assignments, "Assignments", "assignment_id")

    # Additional relationship checks
    print("\n" + "=" * 60)
    print("REDEMPTION RELATIONSHIP CHECKS")
    print("=" * 60)

    for column in ["assignment_id", "visit_id"]:
        duplicate_count = redemptions[column].duplicated(
            keep=False
        ).sum()

        print(
            f"{column} repeated records: {duplicate_count}"
        )

    # Promotional cost validation
    negative_costs = redemptions[
        redemptions["promo_cost"] < 0
    ]

    print(
        f"\nNegative promotional costs: {len(negative_costs)}"
    )

    if not negative_costs.empty:
        print(negative_costs.to_string(index=False))


if __name__ == "__main__":
    main()
