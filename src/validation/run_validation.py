
from pathlib import Path
import pandas as pd

from src.validation.quality_checks import validate_redemptions


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_PATH = PROJECT_ROOT / "data" / "raw"
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"


def main():

    # Load source data
    redemptions = pd.read_csv(
        RAW_PATH / "redemptions.csv"
    )

    visits = pd.read_csv(
        RAW_PATH / "visits.csv"
    )

    # Run validation
    quality_report = validate_redemptions(
        redemptions,
        visits
    )

    # Create output directory
    PROCESSED_PATH.mkdir(
        parents=True,
        exist_ok=True
    )

    # Export quality report
    output_file = (
        PROCESSED_PATH / "redemption_quality_issues.csv"
    )

    quality_report.to_csv(
        output_file,
        index=False
    )

    # Display summary
    print("\nDATA QUALITY SUMMARY")
    print("=" * 40)

    if quality_report.empty:
        print("No issues found.")
    else:
        print(
            quality_report.groupby(
                ["issue_type", "severity"]
            ).size().to_string()
        )
    print(f"\nTotal issue occurrences: {len(quality_report)}")
    unique_flagged = quality_report["redemption_id"].nunique()
    print(f"Unique redemption IDs affected: {unique_flagged}")
    print(f"Report saved to: {output_file}")


if __name__ == "__main__":
    main()
