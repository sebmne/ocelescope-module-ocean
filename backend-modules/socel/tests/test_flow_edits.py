"""Editing the flows of an sOCEL in place: rename, redefine, convert, delete."""

from typing import Any

from api import Api


def edit(flow_id: str, **changes: Any) -> dict[str, Any]:
    """A flow edit that keeps everything of the example's flow but `changes`."""
    current = {
        "electricity": {"unit": "kWh", "category": "energy.electricity"},
        "heat": {"unit": "kWh", "category": "energy.thermal"},
    }[flow_id]
    return {"flowId": flow_id, "name": flow_id, **current, **changes}


def flows(api: Api, ocel_id: str) -> dict[str, dict[str, Any]]:
    return {flow["flowId"]: flow for flow in api.get_flow_inventory(ocel_id).json()}


def test_a_renamed_flow_keeps_its_records_and_containment(api: Api, socel: str) -> None:
    response = api.configure_socel(socel, {"flowEdits": [edit("electricity", name="power")]})

    assert response.status_code == 204
    power = flows(api, socel)["power"]
    assert (power["instances"], power["contained"], power["intervalRecords"]) == (3, 2, 3)
    assert "electricity" not in flows(api, socel)


def test_two_flows_can_swap_their_names(api: Api, socel: str) -> None:
    response = api.configure_socel(
        socel,
        {"flowEdits": [edit("electricity", name="heat"), edit("heat", name="electricity")]},
    )

    assert response.status_code == 204
    after = flows(api, socel)
    assert after["heat"]["category"] == "energy.electricity"
    assert after["heat"]["intervalRecords"] == 3
    assert after["electricity"]["category"] == "energy.thermal"
    assert after["electricity"]["eventRecords"] == 1


def test_a_conversion_multiplies_every_record(api: Api, socel: str) -> None:
    api.configure_socel(socel, {"flowEdits": [edit("electricity", unit="MJ", conversion=3.6)]})

    report = api.calculate_impact(socel, {"electricity": {"inflow": 1.0}}).json()
    electricity = next(flow for flow in report["flows"] if flow["flowId"] == "electricity")
    assert electricity["unit"] == "MJ"
    assert electricity["inflow"] == 360.0


def test_a_deleted_flow_goes_with_its_records(api: Api, socel: str) -> None:
    api.configure_socel(socel, {"flowEdits": [edit("heat", delete=True)]})

    assert set(flows(api, socel)) == {"electricity"}
    status = api.get_socel_status(socel).json()
    assert (status["flows"], status["eventRecords"]) == (1, 0)


def test_a_deleted_flow_takes_its_containment_along(api: Api, socel: str) -> None:
    api.configure_socel(socel, {"flowEdits": [edit("electricity", delete=True)]})

    assert api.get_socel_status(socel).json()["containments"] == 0


def test_a_name_another_flow_keeps_is_refused(api: Api, socel: str) -> None:
    response = api.configure_socel(socel, {"flowEdits": [edit("heat", name="electricity")]})

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Two flows would be called 'electricity'; flow names are unique."
    }


def test_the_name_of_a_deleted_flow_is_free(api: Api, socel: str) -> None:
    response = api.configure_socel(
        socel,
        {"flowEdits": [edit("electricity", delete=True), edit("heat", name="electricity")]},
    )

    assert response.status_code == 204
    assert set(flows(api, socel)) == {"electricity"}


def test_a_flow_cannot_be_changed_twice_in_one_go(api: Api, socel: str) -> None:
    response = api.configure_socel(
        socel, {"flowEdits": [edit("heat", name="warmth"), edit("heat", name="hot")]}
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "A flow is changed twice in one go."}


def test_an_unknown_flow_is_refused(api: Api, socel: str) -> None:
    response = api.configure_socel(socel, {"flowEdits": [edit("heat", flowId="steam")]})

    assert response.status_code == 422
    assert response.json() == {"detail": "The log has no flow 'steam'."}


def test_a_flow_needs_a_name_and_a_unit(api: Api, socel: str) -> None:
    no_name = api.configure_socel(socel, {"flowEdits": [edit("heat", name="  ")]})
    no_unit = api.configure_socel(socel, {"flowEdits": [edit("heat", unit="")]})

    assert no_name.status_code == 422
    assert no_name.json() == {"detail": "The flow 'heat' needs a name."}
    assert no_unit.status_code == 422


def test_a_conversion_must_be_a_number_other_than_zero(api: Api, socel: str) -> None:
    response = api.configure_socel(socel, {"flowEdits": [edit("heat", conversion=0)]})

    assert response.status_code == 422
    assert response.json() == {"detail": "The conversion of 'heat' must be a number other than 0."}


def test_a_category_outside_the_taxonomy_is_refused(api: Api, socel: str) -> None:
    response = api.configure_socel(socel, {"flowEdits": [edit("heat", category="vibes")]})

    assert response.status_code == 422
    assert response.json() == {"detail": "'vibes' is no flow category of the taxonomy."}
