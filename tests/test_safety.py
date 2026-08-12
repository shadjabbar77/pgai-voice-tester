import pytest

from app.config import ASSESSMENT_NUMBER, validate_destination
from app.scenarios import load_scenarios


def test_assessment_number_is_exact():
    assert ASSESSMENT_NUMBER == "+18054398008"


def test_allowed_destination_passes():
    validate_destination("+18054398008")


@pytest.mark.parametrize(
    "number",
    ["+18054398009", "+1805439800", "18054398008", "+15555555555", ""],
)
def test_every_other_destination_is_blocked(number):
    with pytest.raises(ValueError):
        validate_destination(number)


def test_minimum_ten_scenarios():
    assert len(load_scenarios()) >= 10


def test_scenario_ids_are_unique():
    scenarios = load_scenarios()
    assert len(scenarios) == len(set(scenarios))
