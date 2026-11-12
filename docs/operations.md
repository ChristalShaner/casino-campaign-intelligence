# Operations and troubleshooting

## Run the project

Activate the virtual environment, install requirements, and run commands
from the repository root.

``` powershell
.\.venv\Scripts\Activate.ps1
python -m src.run_pipeline
```

Run tests independently:

``` powershell
python -m pytest -v
```

Launch the dashboard after a successful pipeline run:

``` powershell
streamlit run dashboard/app.py
```

## Pipeline behavior

The runner invokes each stage as a separate Python process. It uses the
current interpreter, runs from the project root, prints stage-level
success/failure and elapsed time, and stops when a stage fails.

The pipeline regenerates processed CSV outputs and replaces warehouse
tables through `CREATE OR REPLACE TABLE`. Keep a backup of any outputs
you need to preserve before experimenting with changed source data or
transformation logic.

## Expected output artifacts

The processing stages write generated CSV files under `data/processed/`,
including:

-   `clean_assignments.csv`
-   `quarantined_assignments.csv`
-   `assignment_quality_warnings.csv`
-   `clean_visits.csv`
-   `quarantined_visits.csv`
-   `clean_redemptions.csv`
-   `quarantined_redemptions.csv`
-   `redemption_quality_issues.csv`
-   `redemption_relationships.csv`
-   `relationship_issues.csv`
-   `final_redemptions.csv`
-   `quarantined_redemption_relationships.csv`
-   `fact_campaign_assignments.csv`
-   `group_performance_summary.csv`
-   `stratified_performance_summary.csv`
-   `stratum_incrementality.csv`
-   `campaign_incrementality.csv`
-   `overall_incrementality.csv`

The local DuckDB database is stored at:

``` text
database/casino_analytics.duckdb
```

## Common issues

### `ModuleNotFoundError: No module named 'src'`

Run modules from the repository root using `python -m ...`, not by
executing a module file from inside its subdirectory. Confirm
`__init__.py` files exist in `src/` and relevant package directories.

### `FileNotFoundError` for a source CSV

Confirm that `assignments.csv`, `visits.csv`, and `redemptions.csv` are
present in `data/raw/`. Check exact spelling and capitalization.

### Pipeline fails at a test

Fix the failing test or the underlying behavior before continuing. The
runner intentionally stops so that downstream tables are not built from
unverified logic.

### Pipeline fails during warehouse construction

Check that all expected processed CSV files exist and that the expected
row-count assertions still match the source extract. If source data
changes, update expectations only after investigating the reason for the
changed counts.

### Dashboard cannot find a table

Run the full pipeline successfully before starting Streamlit. Confirm
the dashboard is pointing to `database/casino_analytics.duckdb` in the
repository.

### Port 8501 is already in use

Start Streamlit on another port:

``` powershell
streamlit run dashboard/app.py --server.port 8502
```

## Version control guidance

Generally commit source code, SQL, tests, documentation, and a sanitized
requirements file. Do not commit `.venv/`, secrets, raw player-level
data, generated processed extracts, or the local DuckDB database unless
there is an explicit reason and permission.

Review `.gitignore` before the first public push. Confirm that
`data/raw/` is excluded if the challenge data should not be distributed.
