# Architecture

## Overview

Casino Campaign Intelligence is a small analytical data platform. It
separates source validation, cleaning, business transformation,
analytical estimation, storage, and presentation so that each stage can
be run and tested independently.

## Logical flow

``` mermaid
flowchart TD
    A[assignments.csv] --> B[Python validation and cleaning]
    C[visits.csv] --> B
    D[redemptions.csv] --> B
    B --> E[Clean datasets and quarantine outputs]
    E --> F[Cross-dataset relationship checks]
    F --> G[Final valid redemptions]
    E --> H[Assignment-grain campaign fact]
    G --> H
    H --> I[Stratified incrementality calculation]
    H --> J[DuckDB warehouse]
    I --> J
    J --> K[SQL campaign performance mart]
    J --> L[Data quality reporting tables]
    K --> M[Streamlit]
    L --> M
```

## Pipeline stages

The `src/run_pipeline.py` runner executes these 13 stages in order:

  -----------------------------------------------------------------------------
                            \# Stage                 Purpose
  ---------------------------- --------------------- --------------------------
                             1 Automated tests       Run pytest before
                                                     processing

                             2 Clean assignments     Remove exact duplicate
                                                     copies, quarantine
                                                     conflicting keys and
                                                     invalid assignment
                                                     records, retain
                                                     missing-segment warning

                             3 Clean visits          Remove exact duplicate
                                                     copies, quarantine
                                                     conflicting visit IDs and
                                                     invalid dates, retain
                                                     valid negative gaming
                                                     revenue

                             4 Clean redemptions     Handle
                                                     duplicate/conflicting
                                                     redemption IDs, multiple
                                                     redemptions per
                                                     assignment, and invalid
                                                     negative costs

                             5 Validate source data  Produce source-level
                                                     redemption quality issue
                                                     report

                             6 Validate              Check
                               relationships         redemption-to-assignment
                                                     and redemption-to-visit
                                                     relationships

                             7 Finalize redemptions  Exclude redemptions that
                                                     fail relationship rules

                             8 Build campaign facts  Aggregate response and
                                                     baseline activity at
                                                     assignment grain

                             9 Analyze campaign      Produce overall and
                               performance           stratified offer/holdout
                                                     summaries

                            10 Calculate             Estimate incremental
                               incrementality        visits, gaming revenue,
                                                     net value, and ROI

                            11 Build analytics       Load DuckDB tables and
                               warehouse             dimensions

                            12 Build SQL reporting   Create the campaign
                               marts                 performance reporting view

                            13 Load data quality     Load reconciliation,
                               tables                issue, quarantine, and
                                                     warning outputs
  -----------------------------------------------------------------------------

The runner uses the active Python interpreter (`sys.executable`), sets
the repository root as the working directory, measures each stage, and
stops on a failed subprocess.

## Warehouse model

The model uses an assignment-grain analytical fact table supported by
event-level facts and dimensions.

### Core tables

  --------------------------------------------------------------------------------
  Table                            Grain                   Purpose
  -------------------------------- ----------------------- -----------------------
  `clean_assignments`              One row per valid       Cleaned assignment
                                   assignment              population

  `fact_visits`                    One row per valid visit Clean visit events

  `fact_redemptions`               One row per valid       Validated redemption
                                   redemption              events

  `fact_campaign_assignments`      One row per assignment  Campaign outcome
                                                           measures and flags

  `mart_campaign_incrementality`   One row per campaign    Stratified
                                                           incremental-value
                                                           estimates

  `mart_campaign_performance`      One row per campaign    SQL reporting metrics
                                                           combining campaign
                                                           performance and
                                                           incrementality
  --------------------------------------------------------------------------------

### Dimensions

  Dimension              Contents
  ---------------------- -------------------------------
  `dim_campaign`         Campaign ID and campaign name
  `dim_property`         Casino property
  `dim_player_segment`   Non-null player segments

### Data quality tables

-   `data_quality_reconciliation`
-   `data_quality_issues`
-   `data_quality_issue_summary`
-   `data_quality_quarantine_summary`
-   `data_quality_warnings`

## Design decisions

### Assignment-grain fact

The fact table starts with all cleaned assignments and left-joins visit
and redemption aggregates. This preserves assigned players who did not
visit or redeem. A redemption-only or visit-only population would
overstate response rates by excluding nonresponders.

### Event tables remain separate

Visits and redemptions remain available at their own grains. The
assignment fact is a campaign-analysis convenience table, not a
replacement for event-level detail.

### Quarantine rather than silent deletion

Records that violate defined rules are written to quarantine outputs
with reasons. Exact duplicate copies are removed from the clean output
while retained originals remain. Conflicting records are quarantined
because the correct version cannot be inferred safely.

### Python and SQL responsibilities

Python handles record-level validation, cleaning, relationship checks,
fact construction, and stratified calculations. DuckDB stores the
analytical data. SQL creates a reporting mart for dashboard consumption.

## Technology choices

-   **Python/pandas:** accessible data engineering and transformation
    layer.
-   **DuckDB:** embedded analytical database that can query local files
    and support SQL reporting without a separate database server.
-   **SQL:** transparent, reusable reporting logic.
-   **Streamlit/Plotly:** rapid interactive analytical interface.
-   **pytest:** repeatable unit tests for key business and data-quality
    rules.
