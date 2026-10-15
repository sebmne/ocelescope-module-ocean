"""Impact of the example sOCEL. Expected values are worked out by hand from the
record file in `example_log.py`:

- electricity flows into the objects: 24 at m1, 12 at m2, 100 at the hall over
  two days. With the machines inside the hall, only the hall's 100 count (its
  records hold the machines' already); without containment all 136 do.
- heat flows out of m1: 5, at event e1 on 1 January.
"""

import pytest
from api import Api
from conftest import build


def test_each_direction_has_its_own_factor(api: Api, socel: str) -> None:
    report = api.calculate_impact(
        socel, {"electricity": {"inflow": 0.5}, "heat": {"outflow": 2.0}}
    ).json()

    flows = {flow["flowId"]: flow for flow in report["flows"]}
    assert flows["electricity"] == {
        "flowId": "electricity",
        "unit": "kWh",
        "inflow": 100.0,
        "outflow": 0.0,
        "factors": {"inflow": 0.5, "outflow": None},
        "impact": 50.0,
    }
    assert flows["heat"]["inflow"] == 0.0
    assert flows["heat"]["outflow"] == 5.0
    assert flows["heat"]["impact"] == 10.0
    assert report["total"] == 60.0


def test_records_are_spread_over_the_periods_they_span(api: Api, socel: str) -> None:
    report = api.calculate_impact(
        socel, {"electricity": {"inflow": 0.5}, "heat": {"outflow": 2.0}}, period="day"
    ).json()

    assert report["byPeriod"] == [
        {"start": "2026-01-01T00:00:00", "flowId": "electricity", "impact": 25.0},
        {"start": "2026-01-01T00:00:00", "flowId": "heat", "impact": 10.0},
        {"start": "2026-01-02T00:00:00", "flowId": "electricity", "impact": 25.0},
    ]


def test_hourly_periods_share_an_interval_by_its_overlap(api: Api, socel: str) -> None:
    report = api.calculate_impact(socel, {"electricity": {"inflow": 1.0}}, period="hour").json()

    hours = [part for part in report["byPeriod"] if part["flowId"] == "electricity"]
    # 100 over 48 hours.
    assert len(hours) == 48
    assert [part["impact"] for part in hours] == pytest.approx([100 / 48] * 48)


def test_an_absent_factor_is_no_impact_and_a_zero_factor_is_zero(api: Api, socel: str) -> None:
    report = api.calculate_impact(socel, {"electricity": {"inflow": 0.0}}).json()

    flows = {flow["flowId"]: flow for flow in report["flows"]}
    assert flows["electricity"]["impact"] == 0.0
    assert flows["heat"]["impact"] is None
    assert flows["heat"]["factors"] == {"inflow": None, "outflow": None}
    assert report["total"] == 0.0
    assert all(part["flowId"] == "electricity" for part in report["byPeriod"])


def test_a_factor_on_a_direction_without_amounts_gives_zero(api: Api, socel: str) -> None:
    report = api.calculate_impact(socel, {"heat": {"inflow": 3.0}}).json()

    heat = next(flow for flow in report["flows"] if flow["flowId"] == "heat")
    assert heat["impact"] == 0.0


def test_factors_of_flows_the_log_does_not_have_are_ignored(api: Api, socel: str) -> None:
    report = api.calculate_impact(socel, {"steam": {"inflow": 1.0}}).json()

    assert {flow["flowId"] for flow in report["flows"]} == {"electricity", "heat"}
    assert report["total"] == 0.0


def test_without_containment_every_record_counts(api: Api, plain_log: str) -> None:
    flat = build(api, plain_log, containment=False)

    report = api.calculate_impact(flat, {"electricity": {"inflow": 1.0}}).json()

    electricity = next(flow for flow in report["flows"] if flow["flowId"] == "electricity")
    assert electricity["inflow"] == 136.0
    assert report["total"] == 136.0


@pytest.mark.parametrize("value", [b"Infinity", b"-Infinity", b"NaN"])
def test_a_factor_must_be_a_finite_number(api: Api, socel: str, value: bytes) -> None:
    response = api.calculate_impact_from_json(
        socel, b'{"period": "day", "factors": {"heat": {"outflow": ' + value + b"}}}"
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "factors", "heat", "outflow"]
    assert response.json()["detail"][0]["type"] == "finite_number"


def test_period_defaults_to_day(api: Api, socel: str) -> None:
    response = api.calculate_impact_from_json(
        socel, b'{"factors": {"electricity": {"inflow": 0.5}}}'
    )

    assert response.status_code == 200
    assert response.json() == api.calculate_impact(socel, {"electricity": {"inflow": 0.5}}).json()
