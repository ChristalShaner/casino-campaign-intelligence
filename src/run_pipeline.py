
from pathlib import Path
import subprocess
import sys
import time


PROJECT_ROOT = Path(__file__).resolve().parents[1]


PIPELINE_STEPS = [
    (
        "Automated Tests",
        [sys.executable, "-m", "pytest", "-v"]
    ),
    (
        "Clean Assignments",
        [sys.executable, "-m", "src.transformations.clean_assignments"]
    ),
    (
        "Clean Visits",
        [sys.executable, "-m", "src.transformations.clean_visits"]
    ),
    (
        "Clean Redemptions",
        [sys.executable, "-m", "src.transformations.clean_redemptions"]
    ),
    (
        "Validate Source Data",
        [sys.executable, "-m", "src.validation.run_validation"]
    ),
    (
        "Validate Relationships",
        [sys.executable, "-m", "src.validation.validate_relationships"]
    ),
    (
        "Finalize Redemptions",
        [sys.executable, "-m", "src.transformations.finalize_redemptions"]
    ),
    (
        "Build Campaign Facts",
        [sys.executable, "-m", "src.transformations.build_campaign_facts"]
    ),
    (
        "Analyze Campaign Performance",
        [sys.executable, "-m", "src.validation.analyze_campaign_performance"]
    ),
    (
        "Calculate Incrementality",
        [sys.executable, "-m", "src.validation.calculate_incrementality"]
    ),
    (
        "Build Analytics Warehouse",
        [sys.executable, "-m", "src.database.build_warehouse"]
    ),
    (
        "Build SQL Reporting Marts",
        [sys.executable, "-m", "src.database.build_marts"]
    ),
    (
        "Load Data Quality Tables",
        [sys.executable, "-m", "src.database.load_quality_tables"]
    )
]


def run_pipeline():

    pipeline_start = time.perf_counter()

    print("\n" + "=" * 65)
    print("CASINO CAMPAIGN INTELLIGENCE")
    print("END-TO-END DATA PIPELINE")
    print("=" * 65)

    print(f"\nProject directory: {PROJECT_ROOT}")
    print(f"Pipeline steps: {len(PIPELINE_STEPS)}")

    completed_steps = []

    for index, (step_name, command) in enumerate(
        PIPELINE_STEPS, start=1
    ):

        step_start = time.perf_counter()

        print("\n" + "=" * 65)
        print(f"STEP {index}/{len(PIPELINE_STEPS)}: {step_name}")
        print("=" * 65, flush=True)

        try:

            subprocess.run(
                command,
                cwd=PROJECT_ROOT,
                check=True
            )

            duration = time.perf_counter() - step_start

            completed_steps.append(step_name)

            print(
                f"\nSUCCESS: {step_name} "
                f"({duration:.2f} seconds)",
                flush=True
            )

        except subprocess.CalledProcessError as error:

            duration = time.perf_counter() - step_start

            print("\n" + "=" * 65)
            print("PIPELINE FAILED")
            print("=" * 65)

            print(f"Failed step: {step_name}")
            print(f"Exit code: {error.returncode}")
            print(f"Duration: {duration:.2f} seconds")

            print(
                f"Completed steps: "
                f"{len(completed_steps)}/{len(PIPELINE_STEPS)}"
            )

            print("\nRemaining steps were not executed.")

            raise SystemExit(error.returncode)

    total_duration = time.perf_counter() - pipeline_start

    print("\n" + "=" * 65)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 65)

    print(f"Completed steps: {len(completed_steps)}")
    print(f"Total runtime: {total_duration:.2f} seconds")

    print("\nCompleted pipeline stages:")

    for step in completed_steps:
        print(f"  [PASS] {step}")

    print("\nAnalytics warehouse is ready.")
    print("You can now launch the Streamlit dashboard.")


if __name__ == "__main__":
    run_pipeline()
