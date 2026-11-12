
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = (
    PROJECT_ROOT / "database" / "casino_analytics.duckdb"
)

SQL_PATH = (
    PROJECT_ROOT / "sql" / "marts" / "campaign_performance.sql"
)


def main():

    connection = duckdb.connect(str(DATABASE_PATH))

    print("BUILDING SQL REPORTING MARTS")
    print("=" * 50)

    sql = SQL_PATH.read_text(encoding="utf-8")

    connection.execute(sql)

    print("Created mart_campaign_performance")

    print("\nCAMPAIGN PERFORMANCE")
    print("=" * 90)

    results = connection.execute("""
        SELECT *
        FROM mart_campaign_performance
        ORDER BY incremental_net_value DESC
    """).df()

    print(results.to_string(index=False))

    print("\nVALIDATION")
    print("=" * 50)

    campaign_count = connection.execute("""
        SELECT COUNT(*)
        FROM mart_campaign_performance
    """).fetchone()[0]

    assert campaign_count == 4

    print(f"Campaign records: {campaign_count}")
    print("SQL reporting mart validated successfully.")

    connection.close()


if __name__ == "__main__":
    main()
