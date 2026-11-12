
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"
DATABASE_PATH = PROJECT_ROOT / "database" / "casino_analytics.duckdb"


def main():

    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = duckdb.connect(str(DATABASE_PATH))

    print("BUILDING CASINO ANALYTICS WAREHOUSE")
    print("=" * 50)

    # Load cleaned source data and analytical outputs.
    tables = {
        "clean_assignments": "clean_assignments.csv",
        "fact_visits": "clean_visits.csv",
        "fact_redemptions": "final_redemptions.csv",
        "fact_campaign_assignments": "fact_campaign_assignments.csv",
        "mart_campaign_incrementality": "campaign_incrementality.csv"
    }

    for table_name, filename in tables.items():

        file_path = (
            PROCESSED_PATH / filename
        ).as_posix()

        connection.execute(
            f"""
            CREATE OR REPLACE TABLE {table_name} AS
            SELECT *
            FROM read_csv_auto('{file_path}')
            """
        )

        row_count = connection.execute(
            f"SELECT COUNT(*) FROM {table_name}"
        ).fetchone()[0]

        print(f"{table_name}: {row_count:,} rows")

        # Validate expected source and fact table counts.
    expected_counts = {
        "clean_assignments": 24000,
        "fact_visits": 30315,
        "fact_redemptions": 4965,
        "fact_campaign_assignments": 24000,
        "mart_campaign_incrementality": 4
    }

    print("\nTABLE VALIDATION")
    print("=" * 50)

    for table_name, expected in expected_counts.items():
        actual = connection.execute(
            f"SELECT COUNT(*) FROM {table_name}"
        ).fetchone()[0]

        assert actual == expected, (
            f"{table_name}: expected {expected:,}, "
            f"found {actual:,}"
        )

        print(f"{table_name}: {actual:,} rows - PASS")

    # Create dimensions from the cleaned assignment population.
    connection.execute("""
        CREATE OR REPLACE TABLE dim_campaign AS
        SELECT DISTINCT
            campaign_id,
            campaign_name
        FROM clean_assignments
    """)

    connection.execute("""
        CREATE OR REPLACE TABLE dim_property AS
        SELECT DISTINCT
            property
        FROM clean_assignments
    """)

    connection.execute("""
        CREATE OR REPLACE TABLE dim_player_segment AS
        SELECT DISTINCT
            player_segment
        FROM clean_assignments
        WHERE player_segment IS NOT NULL
    """)

    print("\nDIMENSION TABLES")
    print("=" * 50)

        # Validate dimension counts.
    expected_dimensions = {
        "dim_campaign": 4,
        "dim_property": 2,
        "dim_player_segment": 3
    }

    for table_name, expected in expected_dimensions.items():
        actual = connection.execute(
            f"SELECT COUNT(*) FROM {table_name}"
        ).fetchone()[0]

        assert actual == expected, (
            f"{table_name}: expected {expected}, found {actual}"
        )

        print(f"{table_name}: {actual} rows - PASS")

    for table_name in [
        "dim_campaign",
        "dim_property",
        "dim_player_segment"
    ]:

        count = connection.execute(
            f"SELECT COUNT(*) FROM {table_name}"
        ).fetchone()[0]

        print(f"{table_name}: {count:,} rows")

    # Confirm the assignment fact table has the expected grain.
    total_assignments = connection.execute("""
        SELECT COUNT(*)
        FROM fact_campaign_assignments
    """).fetchone()[0]

    unique_assignments = connection.execute("""
        SELECT COUNT(DISTINCT assignment_id)
        FROM fact_campaign_assignments
    """).fetchone()[0]

    assert total_assignments == 24000
    assert unique_assignments == total_assignments

    print("\nWAREHOUSE VALIDATION")
    print("=" * 50)
    print(f"Total assignments: {total_assignments:,}")
    print(f"Unique assignments: {unique_assignments:,}")

        # Validate primary-key uniqueness in event tables.
    primary_keys = {
        "fact_visits": "visit_id",
        "fact_redemptions": "redemption_id"
    }

    for table_name, key in primary_keys.items():
        total = connection.execute(
            f"SELECT COUNT(*) FROM {table_name}"
        ).fetchone()[0]

        unique = connection.execute(
            f"SELECT COUNT(DISTINCT {key}) FROM {table_name}"
        ).fetchone()[0]

        assert total == unique, (
            f"{table_name} contains duplicate {key} values."
        )

        print(f"{table_name}.{key}: unique - PASS")

    print("\nCAMPAIGN INCREMENTALITY")
    print("=" * 50)

    results = connection.execute("""
        SELECT
            campaign_name,
            incremental_gaming_revenue,
            promotional_cost,
            incremental_net_value,
            roi
        FROM mart_campaign_incrementality
        ORDER BY incremental_net_value DESC
    """).df()

    print(results.to_string(index=False))

    connection.close()

    print("\nWAREHOUSE BUILD COMPLETE")
    print(f"Database: {DATABASE_PATH}")


if __name__ == "__main__":
    main()
