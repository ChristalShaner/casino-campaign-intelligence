# Methodology and assumptions

## Experiment design

The supplied data contains four campaigns across two casino properties.
Within campaign, property, and player segment, assignments are assumed
to have been randomized into:

-   **Offer:** player receives the campaign offer.
-   **Holdout:** player does not receive the offer.

The supplied population contains 24,000 clean assignments: 19,200 offer
and 4,800 holdout. Each campaign has 6,000 assignments, with 4,800 offer
and 1,200 holdout assignments.

The analysis treats assignment as the unit of analysis. Players who do
not visit or redeem remain in the denominator.

## Analysis windows

-   **Baseline period:** the 28 days before the assignment date.
-   **Response period:** 14 days beginning on the assignment date,
    including the assignment date.
-   **Extract cutoff:** October 31, 2026.

The response period is treated as the half-open date interval
`[assigned_date, assigned_date + 14 days)`. A response window is
complete when its exclusive end date is no later than November 1, 2026.
The supplied assignment dates (September 1--22, 2026) therefore have
complete response windows at the stated cutoff.

The pre-period provides descriptive context. It is not used as a
substitute for the randomized holdout comparison.

## Primary incremental-value estimate

The primary estimate is stratified by:

1.  Campaign
2.  Casino property
3.  Player segment

For each stratum, the analysis calculates the offer and holdout group
outcomes. It then applies the within-stratum difference to the number of
eligible offer assignments in that stratum.

For outcome `Y`, the estimated incremental amount is:

`sum((average Y in offer - average Y in holdout) × eligible offer assignments)`

This is calculated separately for visit incidence and gaming revenue per
assigned player.

Incremental net value is:

`incremental gaming revenue - actual promotional cost`

ROI is:

`incremental net value / promotional cost`

If promotional cost is zero, ROI is undefined and is represented as
missing rather than infinity.

## Important distinction between reported metrics

The SQL campaign performance mart includes direct campaign-level
offer-versus-holdout visit-rate lift. The incremental-value outputs use
stratified differences across campaign, property, and player segment.
These measures can differ because one is an unstratified campaign-level
comparison and the other adjusts for the defined strata.

The campaign mart's incremental revenue, net value, and ROI are sourced
from the stratified incrementality output.

## Data-quality rules

### Assignments

-   Exact duplicate rows: retain one copy and quarantine the extra copy.
-   Conflicting values for the same assignment ID: quarantine all
    conflicting rows.
-   Group must be `offer` or `holdout`.
-   Offer assignments must have a non-null, nonnegative offer value.
-   Holdout assignments must have a null offer value.
-   Missing player segment: retain the assignment with a warning;
    exclude it from segment and stratified analyses.

### Visits

-   Exact duplicate rows: retain one copy and quarantine the extra copy.
-   Conflicting values for the same visit ID: quarantine all conflicting
    rows.
-   Invalid visit dates: quarantine.
-   Negative gaming revenue: retain because net gaming revenue can
    legitimately be negative.

### Redemptions

-   Exact duplicate rows: retain one copy and quarantine the extra copy.
-   Conflicting values for the same redemption ID: quarantine all
    conflicting rows.
-   Multiple redemption records for one assignment: quarantine the
    ambiguous assignment-level redemption records.
-   Negative promotional cost: quarantine.
-   Relationship validation requires a matching assignment and visit.
-   Redemption assignment must be an offer assignment.
-   Assignment and visit player IDs must match.
-   Assignment and visit properties must match.
-   Visit date must fall within the 14-day response window.

A record may trigger more than one quality issue. Issue counts therefore
represent issue occurrences, not necessarily unique affected records.

## Current findings

The current run produced these campaign estimates:

  -------------------------------------------------------------------------------------
  Campaign      Incremental gaming   Promotional cost    Incremental net            ROI
                           revenue                                 value 
  ------------- ------------------ ------------------ ------------------ --------------
  Weekend Match       \$101,969.38        \$20,010.00        \$81,959.38        409.59%

  Dining Credit        \$48,477.87        \$25,660.00        \$22,817.87         88.92%

  Midweek Play         \$45,277.62        \$30,550.00        \$14,727.62         48.21%

  New Member           \$31,939.52        \$33,780.00        -\$1,840.48         -5.45%
  Welcome                                                                

  **Overall**     **\$227,664.39**   **\$110,000.00**   **\$117,664.39**    **106.97%**
  -------------------------------------------------------------------------------------

### Business interpretation

-   Weekend Match is the strongest campaign by incremental net value and
    estimated ROI.
-   Dining Credit and Midweek Play have positive estimated net value,
    though their returns are lower.
-   New Member Welcome has negative estimated net value in this extract;
    its offer design, audience, and cost should be reviewed before
    further investment.
-   These estimates are based on the supplied synthetic dataset and
    stated randomization assumption. They should not be treated as
    guaranteed future performance.

## Limitations and further statistical work

The current project does not calculate confidence intervals, p-values,
minimum detectable effects, or statistical power. Before using these
estimates for high-impact budget decisions, a production analysis should
quantify uncertainty and verify experiment assignment integrity.

Other useful extensions include:

-   Validate balance between offer and holdout groups within each
    stratum.
-   Add confidence intervals for incremental visits, gaming revenue, and
    net value.
-   Add sensitivity analysis for outliers and negative gaming revenue.
-   Track incomplete response windows when future extracts contain
    recent assignments.
-   Separate promotional cost components if the business provides richer
    cost data.
-   Compare campaign effects across time and repeat campaign exposure.
