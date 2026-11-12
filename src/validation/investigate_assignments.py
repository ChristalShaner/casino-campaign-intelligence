
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = PROJECT_ROOT / "data" / "raw"


def main():
    assignments = pd.read_csv(
        RAW_PATH / "assignments.csv"
    )

    print("\n=== ASSIGNMENT GROUP DISTRIBUTION ===")
    print(assignments["group"].value_counts(dropna=False))

    print("\n=== OFFER VALUE BY GROUP ===")
    print(
        assignments.groupby("group", dropna=False)
        ["offer_value"]
        .agg(
            total="size",
            non_missing="count"
        )
    )

    print("\n=== MISSING OFFER VALUES BY GROUP ===")
    print(
        assignments.assign(
            offer_value_missing=assignments["offer_value"].isna()
        )
        .groupby("group", dropna=False)
        ["offer_value_missing"]
        .agg(["sum", "count"])
    )

    print("\n=== MISSING PLAYER SEGMENT ===")
    missing_segment = assignments[
        assignments["player_segment"].isna()
    ]
    print(missing_segment.to_string(index=False))

    print("\n=== DUPLICATE ASSIGNMENT IDs ===")
    duplicate_ids = assignments[
        assignments.duplicated(
            "assignment_id", keep=False
        )
    ].sort_values("assignment_id")

    print(duplicate_ids.to_string(index=False))

    print("\n=== PLAYERS WITH MULTIPLE ASSIGNMENTS ===")
    duplicate_players = assignments[
        assignments.duplicated(
            "player_id", keep=False
        )
    ].sort_values("player_id")

    print(duplicate_players.to_string(index=False))
    print(
        f"Rows belonging to repeated players: "
        f"{len(duplicate_players)}"
    )

    print("\n=== CAMPAIGN DISTRIBUTION ===")
    print(
        assignments.groupby(
            ["campaign_id", "campaign_name"]
        ).size().to_string()
    )

    print("\n=== PROPERTY DISTRIBUTION ===")
    print(assignments["property"].value_counts())

    print("\n=== PLAYER SEGMENT DISTRIBUTION ===")
    print(
        assignments["player_segment"]
        .value_counts(dropna=False)
    )

    print("\n=== GROUP DISTRIBUTION BY CAMPAIGN ===")
    print(
        pd.crosstab(
            assignments["campaign_name"],
            assignments["group"],
            margins=True
        )
    )

    print("\n=== ASSIGNMENT DATE RANGE ===")
    print(
        pd.to_datetime(assignments["assigned_date"])
        .agg(["min", "max"])
    )


if __name__ == "__main__":
    main()
