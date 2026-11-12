
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"


def main():

    print("DATA QUALITY OUTPUT INVENTORY")
    print("=" * 70)

    files = sorted(PROCESSED_PATH.glob("*.csv"))

    for file_path in files:

        df = pd.read_csv(file_path)

        print(f"\nFILE: {file_path.name}")
        print("-" * 50)

        print(f"Records: {len(df):,}")
        print(f"Columns: {len(df.columns)}")

        print("Column names:")
        print(", ".join(df.columns.astype(str)))

        if "quarantine_reason" in df.columns:
            print("\nQuarantine reasons:")
            print(df["quarantine_reason"].value_counts().to_string())

        if "issue_type" in df.columns:
            print("\nIssue types:")
            print(df["issue_type"].value_counts().to_string())

        if "severity" in df.columns:
            print("\nSeverity:")
            print(df["severity"].value_counts().to_string())


if __name__ == "__main__":
    main()
