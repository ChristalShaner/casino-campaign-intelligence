
import pandas as pd
import pytest

from src.validation.calculate_incrementality import (
    calculate_incrementality
)


def make_row(
    assignment_id,
    segment,
    group,
    visit_count,
    gaming_revenue,
    promotional_cost
):
    return {
        "assignment_id": assignment_id,
        "campaign_id": "C01",
        "campaign_name": "Weekend Match",
        "property": "Harbor Casino",
        "player_segment": segment,
        "group": group,
        "response_visit_count": visit_count,
        "response_gaming_revenue": gaming_revenue,
        "promotional_cost": promotional_cost
    }


@pytest.fixture
def sample_fact():
    return pd.DataFrame([
        # Core offer group
        make_row("A001", "Core", "offer", 1, 100, 10),
        make_row("A002", "Core", "offer", 1, 200, 20),

        # Core holdout group
        make_row("A003", "Core", "holdout", 1, 50, 0),
        make_row("A004", "Core", "holdout", 0, 50, 0),

        # VIP offer group
        make_row("A005", "VIP", "offer", 1, 100, 10),
        make_row("A006", "VIP", "offer", 0, 0, 10),

        # VIP holdout group
        make_row("A007", "VIP", "holdout", 1, 50, 0),
        make_row("A008", "VIP", "holdout", 1, 50, 0),

        # Missing segment: excluded from stratified estimate
        make_row("A009", None, "offer", 1, 500, 15)
    ])


def test_incrementality_calculates_stratum_results(sample_fact):
    comparison, _, _ = calculate_incrementality(sample_fact)

    core = comparison[
        comparison["player_segment"] == "Core"
    ].iloc[0]

    assert core["assignments_offer"] == 2
    assert core["assignments_holdout"] == 2

    assert core["visit_rate_lift"] == pytest.approx(0.5)
    assert core["revenue_per_player_lift"] == pytest.approx(100)

    assert core["incremental_visits"] == pytest.approx(1)
    assert core["incremental_gaming_revenue"] == pytest.approx(200)


def test_incrementality_calculates_campaign_results(sample_fact):
    _, campaigns, _ = calculate_incrementality(sample_fact)

    campaign = campaigns.iloc[0]

    assert campaign["eligible_offer_assignments"] == 4
    assert campaign["eligible_holdout_assignments"] == 4

    assert campaign["incremental_visits"] == pytest.approx(0)
    assert campaign["incremental_gaming_revenue"] == pytest.approx(200)

    assert campaign["promotional_cost"] == pytest.approx(50)
    assert campaign["incremental_net_value"] == pytest.approx(150)
    assert campaign["roi"] == pytest.approx(3.0)


def test_overall_results_match_campaign_results(sample_fact):
    _, campaigns, overall = calculate_incrementality(sample_fact)

    result = overall.iloc[0]
    campaign = campaigns.iloc[0]

    assert result["eligible_offer_assignments"] == 4
    assert result["eligible_holdout_assignments"] == 4

    assert result["incremental_gaming_revenue"] == pytest.approx(
        campaign["incremental_gaming_revenue"]
    )

    assert result["incremental_net_value"] == pytest.approx(
        campaign["incremental_net_value"]
    )

    assert result["roi"] == pytest.approx(3.0)


def test_missing_segment_is_excluded_from_stratified_results(sample_fact):
    comparison, campaigns, overall = calculate_incrementality(sample_fact)

    assert comparison["player_segment"].notna().all()

    # The missing-segment assignment must not contribute
    # to the eligible offer population.
    assert campaigns["eligible_offer_assignments"].sum() == 4
    assert overall.iloc[0]["eligible_offer_assignments"] == 4


def test_unmatched_stratum_raises_error(sample_fact):
    # Remove the Core holdout population.
    incomplete = sample_fact[
        ~(
            (sample_fact["player_segment"] == "Core")
            & (sample_fact["group"] == "holdout")
        )
    ]

    with pytest.raises(ValueError, match="Every stratum"):
        calculate_incrementality(incomplete)


def test_zero_promotional_cost_produces_missing_roi(sample_fact):
    zero_cost = sample_fact.copy()

    # Set all offer promotional costs to zero.
    zero_cost.loc[
        zero_cost["group"] == "offer",
        "promotional_cost"
    ] = 0

    _, campaigns, overall = calculate_incrementality(zero_cost)

    assert pd.isna(campaigns.iloc[0]["roi"])
    assert pd.isna(overall.iloc[0]["roi"])
