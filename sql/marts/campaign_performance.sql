
CREATE OR REPLACE VIEW mart_campaign_performance AS

WITH campaign_metrics AS (

    SELECT
        campaign_id,
        campaign_name,

        COUNT(*) AS total_assignments,

        SUM(
            CASE WHEN "group" = 'offer'
            THEN 1 ELSE 0 END
        ) AS offer_assignments,

        SUM(
            CASE WHEN "group" = 'holdout'
            THEN 1 ELSE 0 END
        ) AS holdout_assignments,

        -- Players with at least one response-period visit.
        SUM(
            CASE
                WHEN "group" = 'offer'
                 AND response_visit_count > 0
                THEN 1 ELSE 0
            END
        ) AS offer_players_with_visits,

        SUM(
            CASE
                WHEN "group" = 'holdout'
                 AND response_visit_count > 0
                THEN 1 ELSE 0
            END
        ) AS holdout_players_with_visits,

        -- Response-period gaming revenue.
        SUM(
            CASE WHEN "group" = 'offer'
            THEN response_gaming_revenue ELSE 0 END
        ) AS offer_gaming_revenue,

        SUM(
            CASE WHEN "group" = 'holdout'
            THEN response_gaming_revenue ELSE 0 END
        ) AS holdout_gaming_revenue,

        -- Valid redemptions and promotional costs.
        SUM(
            CASE WHEN "group" = 'offer'
            THEN redemption_count ELSE 0 END
        ) AS total_redemptions,

        SUM(
            CASE WHEN "group" = 'offer'
            THEN promotional_cost ELSE 0 END
        ) AS actual_promotional_cost

    FROM fact_campaign_assignments

    GROUP BY
        campaign_id,
        campaign_name
),

campaign_rates AS (

    SELECT
        *,

        offer_players_with_visits * 1.0
            / NULLIF(offer_assignments, 0)
            AS offer_visit_rate,

        holdout_players_with_visits * 1.0
            / NULLIF(holdout_assignments, 0)
            AS holdout_visit_rate,

        offer_gaming_revenue * 1.0
            / NULLIF(offer_assignments, 0)
            AS offer_revenue_per_player,

        holdout_gaming_revenue * 1.0
            / NULLIF(holdout_assignments, 0)
            AS holdout_revenue_per_player,

        total_redemptions * 1.0
            / NULLIF(offer_assignments, 0)
            AS redemption_rate

    FROM campaign_metrics
)

SELECT
    c.campaign_id,
    c.campaign_name,

    c.total_assignments,
    c.offer_assignments,
    c.holdout_assignments,

    c.offer_visit_rate,
    c.holdout_visit_rate,

    c.offer_visit_rate - c.holdout_visit_rate
        AS visit_rate_lift,

    c.offer_revenue_per_player,
    c.holdout_revenue_per_player,

    c.redemption_rate,

    c.actual_promotional_cost,

    i.incremental_visits,
    i.incremental_gaming_revenue,
    i.incremental_net_value,
    i.roi

FROM campaign_rates c

LEFT JOIN mart_campaign_incrementality i
    ON c.campaign_id = i.campaign_id;
