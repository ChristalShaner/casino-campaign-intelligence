# Data dictionary

This document describes the source datasets and the principal warehouse
outputs. Column names below reflect the challenge data and the
transformations described in the project.

## Source datasets

### `assignments.csv`

**Grain:** one row per player campaign assignment.

  -----------------------------------------------------------------------
  Column                              Meaning
  ----------------------------------- -----------------------------------
  `assignment_id`                     Unique identifier for an assignment

  `player_id`                         Player identifier

  `campaign_id`                       Campaign identifier

  `campaign_name`                     Campaign display name

  `property`                          Casino property associated with the
                                      assignment

  `player_segment`                    Player segment (Core, New, or VIP
                                      in the supplied data)

  `assigned_date`                     Date the campaign assignment begins

  `group`                             Experiment group: `offer` or
                                      `holdout`

  `offer_value`                       Offer value; intentionally null for
                                      holdout assignments
  -----------------------------------------------------------------------

### `visits.csv`

**Grain:** one row per casino visit.

  -----------------------------------------------------------------------
  Column                              Meaning
  ----------------------------------- -----------------------------------
  `visit_id`                          Unique visit identifier

  `player_id`                         Player identifier

  `property`                          Casino property where the visit
                                      occurred

  `visit_date`                        Visit date

  `gaming_revenue`                    Casino net gaming revenue for the
                                      visit; may be negative
  -----------------------------------------------------------------------

### `redemptions.csv`

**Grain:** one row per redemption event.

  -----------------------------------------------------------------------
  Column                              Meaning
  ----------------------------------- -----------------------------------
  `redemption_id`                     Unique redemption identifier

  `assignment_id`                     Assignment associated with the
                                      redemption

  `visit_id`                          Visit associated with the
                                      redemption

  `promo_cost`                        Promotional cost associated with
                                      the redemption; must be nonnegative
  -----------------------------------------------------------------------

## Principal derived outputs

### `fact_campaign_assignments.csv` / `fact_campaign_assignments`

**Grain:** one row per cleaned assignment.

The table retains the complete clean assignment population and adds
aggregated activity measures. Derived fields include:

-   Baseline-period visit count and gaming revenue
-   Response-period visit count and gaming revenue
-   Redemption count and promotional cost
-   Redeemed indicator
-   Response-window completeness indicator

The exact set of columns is defined by
`src/transformations/build_campaign_facts.py`.

### Incrementality outputs

  -------------------------------------------------------------------------------
  Output                          Grain                   Purpose
  ------------------------------- ----------------------- -----------------------
  `stratum_incrementality.csv`    Campaign × property ×   Offer/holdout
                                  player segment          comparison within each
                                                          stratum

  `campaign_incrementality.csv`   Campaign                Aggregated incremental
                                                          outcomes and ROI

  `overall_incrementality.csv`    Overall population      Overall stratified
                                                          incremental outcomes
  -------------------------------------------------------------------------------

Important measures:

  -----------------------------------------------------------------------
  Measure                             Definition
  ----------------------------------- -----------------------------------
  Visit rate                          Assigned players with at least one
                                      response-period visit divided by
                                      assignments in the group

  Revenue per assigned player         Response-period gaming revenue
                                      divided by assignments in the group

  Visit-rate lift                     Offer visit rate minus holdout
                                      visit rate

  Incremental visits                  Sum of stratum visit-rate
                                      differences multiplied by the
                                      number of eligible offer
                                      assignments in each stratum

  Incremental gaming revenue          Sum of stratum revenue-per-player
                                      differences multiplied by eligible
                                      offer assignments in each stratum

  Promotional cost                    Actual validated promotional cost
                                      attributed to offer assignments

  Incremental net value               Incremental gaming revenue minus
                                      promotional cost

  ROI                                 Incremental net value divided by
                                      promotional cost
  -----------------------------------------------------------------------

ROI is expressed as a ratio in the data, so `1.069676` corresponds to
approximately `106.97%`.

## Current source counts

  Dataset         Raw records   Clean/final records   Excluded records
  ------------- ------------- --------------------- ------------------
  Assignments          24,003                24,000                  3
  Visits               30,318                30,315                  3
  Redemptions           4,974                 4,965                  9

The missing player-segment assignment is retained in the assignment
population and recorded as a warning. It is excluded from segment-level
and stratified incrementality calculations because it cannot be assigned
to a valid segment stratum.
