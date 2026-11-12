
from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw"


def main():

    redemptions = pd.read_csv(
        RAW_DATA_PATH / "redemptions.csv"
    )

    visits = pd.read_csv(
        RAW_DATA_PATH / "visits.csv"
    )

    # 1. Investigate repeated assignment IDs
    print("\n=== REPEATED ASSIGNMENTS ===")

    repeated_assignments = redemptions[
        redemptions.duplicated(
            subset=["assignment_id"],
            keep=False
        )
    ].sort_values("assignment_id")

    print(repeated_assignments.to_string(index=False))

    # 2. Investigate repeated visit IDs
    print("\n=== REPEATED VISITS ===")

    repeated_visits = redemptions[
        redemptions.duplicated(
            subset=["visit_id"],
            keep=False
        )
    ].sort_values("visit_id")

    print(repeated_visits.to_string(index=False))

    # 3. Check redemption visit references
    print("\n=== VISIT REFERENTIAL INTEGRITY ===")

    unmatched = redemptions[
        ~redemptions["visit_id"].isin(visits["visit_id"])
    ]

    print(f"Unmatched visit IDs: {len(unmatched)}")

    # 4. Join redemption records to visit information
    print("\n=== REDEMPTION / VISIT DETAILS ===")

    joined = redemptions.merge(
        visits,
        on="visit_id",
        how="left",
        indicator=True
    )

    print(
        joined[
            joined["assignment_id"].isin(
                repeated_assignments["assignment_id"]
            )
        ].sort_values(
            ["assignment_id", "redemption_id"]
        ).to_string(index=False)
    )

    # 5. Check negative promotional costs
    print("\n=== INVALID PROMOTIONAL COSTS ===")

    invalid_costs = redemptions[
        redemptions["promo_cost"] < 0
    ]

    print(invalid_costs.to_string(index=False))


if __name__ == "__main__":
    main()
