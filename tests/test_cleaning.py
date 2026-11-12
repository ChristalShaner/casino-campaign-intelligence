
import pandas as pd

from src.transformations.clean_assignments import clean_assignments
from src.transformations.clean_visits import clean_visits
from src.transformations.clean_redemptions import clean_redemptions


# ==================================================
# TEST DATA HELPERS
# ==================================================

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
        "offer_value": 15.0,
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


# ==================================================
# ASSIGNMENT CLEANING TESTS
# ==================================================

def test_exact_duplicate_assignment_is_removed():

    duplicate = make_assignment()

    data = pd.DataFrame([duplicate, duplicate])

    clean, quarantine, warnings = clean_assignments(data)

    assert len(clean) == 1
    assert len(quarantine) == 1
    assert len(warnings) == 0

    assert (
        quarantine.iloc[0]["quarantine_reason"]
        == "Exact duplicate removed; original retained."
    )


def test_conflicting_assignment_ids_are_quarantined():

    first = make_assignment(player_segment="Core")
    second = make_assignment(player_segment="VIP")

    data = pd.DataFrame([first, second])

    clean, quarantine, warnings = clean_assignments(data)

    assert len(clean) == 0
    assert len(quarantine) == 2
    assert len(warnings) == 0

    assert quarantine["assignment_id"].nunique() == 1


def test_missing_player_segment_is_retained_with_warning():

    data = pd.DataFrame([
        make_assignment(player_segment=None)
    ])

    clean, quarantine, warnings = clean_assignments(data)

    assert len(clean) == 1
    assert len(quarantine) == 0
    assert len(warnings) == 1

    assert pd.isna(clean.iloc[0]["player_segment"])

    assert "missing" in warnings.iloc[0]["quality_warning"].lower()


def test_invalid_assignment_group_is_quarantined():

    data = pd.DataFrame([
        make_assignment(group="invalid")
    ])

    clean, quarantine, warnings = clean_assignments(data)

    assert len(clean) == 0
    assert len(quarantine) == 1

    assert (
        quarantine.iloc[0]["quarantine_reason"]
        == "Assignment group must be offer or holdout."
    )


def test_offer_without_offer_value_is_quarantined():

    data = pd.DataFrame([
        make_assignment(group="offer", offer_value=None)
    ])

    clean, quarantine, warnings = clean_assignments(data)

    assert len(clean) == 0
    assert len(quarantine) == 1


def test_holdout_with_offer_value_is_quarantined():

    data = pd.DataFrame([
        make_assignment(group="holdout", offer_value=15.0)
    ])

    clean, quarantine, warnings = clean_assignments(data)

    assert len(clean) == 0
    assert len(quarantine) == 1


def test_valid_holdout_assignment_is_retained():

    data = pd.DataFrame([
        make_assignment(group="holdout", offer_value=None)
    ])

    clean, quarantine, warnings = clean_assignments(data)

    assert len(clean) == 1
    assert len(quarantine) == 0
    assert len(warnings) == 0


# ==================================================
# VISIT CLEANING TESTS
# ==================================================

def test_exact_duplicate_visit_is_removed():

    duplicate = make_visit()

    data = pd.DataFrame([duplicate, duplicate])

    clean, quarantine = clean_visits(data)

    assert len(clean) == 1
    assert len(quarantine) == 1


def test_conflicting_visit_ids_are_quarantined():

    first = make_visit(gaming_revenue=100.0)
    second = make_visit(gaming_revenue=200.0)

    data = pd.DataFrame([first, second])

    clean, quarantine = clean_visits(data)

    assert len(clean) == 0
    assert len(quarantine) == 2

    assert quarantine["visit_id"].nunique() == 1


def test_negative_gaming_revenue_is_retained():

    data = pd.DataFrame([
        make_visit(gaming_revenue=-24.85)
    ])

    clean, quarantine = clean_visits(data)

    assert len(clean) == 1
    assert len(quarantine) == 0

    assert clean.iloc[0]["gaming_revenue"] == -24.85


def test_invalid_visit_date_is_quarantined():

    data = pd.DataFrame([
        make_visit(visit_date="not-a-date")
    ])

    clean, quarantine = clean_visits(data)

    assert len(clean) == 0
    assert len(quarantine) == 1

    assert (
        quarantine.iloc[0]["quarantine_reason"]
        == "Visit date is missing or invalid."
    )


# ==================================================
# REDEMPTION CLEANING TESTS
# ==================================================

def test_exact_duplicate_redemption_is_removed():

    duplicate = make_redemption()

    data = pd.DataFrame([duplicate, duplicate])

    clean, quarantine = clean_redemptions(data)

    assert len(clean) == 1
    assert len(quarantine) == 1


def test_conflicting_redemption_ids_are_quarantined():

    first = make_redemption(promo_cost=15.0)
    second = make_redemption(promo_cost=20.0)

    data = pd.DataFrame([first, second])

    clean, quarantine = clean_redemptions(data)

    assert len(clean) == 0
    assert len(quarantine) == 2

    assert quarantine["redemption_id"].nunique() == 1


def test_negative_promotional_cost_is_quarantined():

    data = pd.DataFrame([
        make_redemption(promo_cost=-5.0)
    ])

    clean, quarantine = clean_redemptions(data)

    assert len(clean) == 0
    assert len(quarantine) == 1

    assert (
        quarantine.iloc[0]["quarantine_reason"]
        == "Promotional cost cannot be negative."
    )


def test_multiple_redemptions_per_assignment_are_quarantined():

    first = make_redemption(redemption_id="R001")
    second = make_redemption(
        redemption_id="R002",
        visit_id="V002"
    )

    data = pd.DataFrame([first, second])

    clean, quarantine = clean_redemptions(data)

    assert len(clean) == 0
    assert len(quarantine) == 2

    assert quarantine["assignment_id"].nunique() == 1


def test_valid_redemption_is_retained():

    data = pd.DataFrame([
        make_redemption()
    ])

    clean, quarantine = clean_redemptions(data)

    assert len(clean) == 1
    assert len(quarantine) == 0
