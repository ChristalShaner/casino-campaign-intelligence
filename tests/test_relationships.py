
import pandas as pd
import pytest

from src.validation.validate_relationships import validate_relationships


def make_assignment(**overrides):
    record = {
        "assignment_id": "A001",
        "player_id": "P001",
        "campaign_id": "C01",
        "campaign_name": "Weekend Match",
        "property": "Harbor Casino",
        "player_segment": "Core",
        "assigned_date": "2026-09-01",
        "group": "offer",
    }
    record.update(overrides)
    return record


def make_visit(**overrides):
    record = {
        "visit_id": "V001",
        "player_id": "P001",
        "property": "Harbor Casino",
        "visit_date": "2026-09-05",
        "gaming_revenue": 100.0,
    }
    record.update(overrides)
    return record


def make_redemption(**overrides):
    record = {
        "redemption_id": "R001",
        "assignment_id": "A001",
        "visit_id": "V001",
        "promo_cost": 15.0,
    }
    record.update(overrides)
    return record


def run_validation(
    redemption=None,
    assignment=None,
    visit=None
):
    redemptions = pd.DataFrame([
        redemption or make_redemption()
    ])
    assignments = pd.DataFrame([
        assignment or make_assignment()
    ])
    visits = pd.DataFrame([
        visit or make_visit()
    ])

    return validate_relationships(
        redemptions,
        assignments,
        visits
    )


def test_valid_redemption_has_no_issues():
    joined, issues = run_validation()

    assert len(joined) == 1
    assert issues.empty


def test_unmatched_assignment_is_flagged():
    _, issues = run_validation(
        redemption=make_redemption(
            assignment_id="A999"
        )
    )

    assert issues["issue_type"].tolist() == [
        "UNMATCHED_ASSIGNMENT"
    ]


def test_unmatched_visit_is_flagged():
    _, issues = run_validation(
        redemption=make_redemption(
            visit_id="V999"
        )
    )

    assert issues["issue_type"].tolist() == [
        "UNMATCHED_VISIT"
    ]


def test_holdout_redemption_is_flagged():
    _, issues = run_validation(
        assignment=make_assignment(group="holdout")
    )

    assert issues["issue_type"].tolist() == [
        "HOLDOUT_REDEMPTION"
    ]


def test_player_mismatch_is_flagged():
    _, issues = run_validation(
        visit=make_visit(player_id="P999")
    )

    assert issues["issue_type"].tolist() == [
        "PLAYER_MISMATCH"
    ]


def test_property_mismatch_is_flagged():
    _, issues = run_validation(
        visit=make_visit(property="Ridge Casino")
    )

    assert issues["issue_type"].tolist() == [
        "PROPERTY_MISMATCH"
    ]


@pytest.mark.parametrize(
    "visit_date, expected_issue",
    [
        ("2026-08-31", True),  # Before assignment
        ("2026-09-01", False), # Day 0: assignment date
        ("2026-09-14", False), # Day 13: final valid day
        ("2026-09-15", True),  # Day 14: outside window
    ]
)
def test_response_window_boundaries(
    visit_date,
    expected_issue
):
    _, issues = run_validation(
        visit=make_visit(visit_date=visit_date)
    )

    outside_window = (
        "OUTSIDE_RESPONSE_WINDOW"
        in issues["issue_type"].tolist()
    )

    assert outside_window == expected_issue


def test_multiple_issues_can_be_reported_for_one_redemption():
    _, issues = run_validation(
        visit=make_visit(
            player_id="P999",
            property="Ridge Casino"
        )
    )

    assert set(issues["issue_type"]) == {
        "PLAYER_MISMATCH",
        "PROPERTY_MISMATCH"
    }

    assert issues["redemption_id"].nunique() == 1
    assert len(issues) == 2
