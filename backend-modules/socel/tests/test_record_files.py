"""Uploading a record file, previewing it against a log, and importing it."""

import pytest
from api import Api
from conftest import build
from example_log import MAPPING, RECORDS_CSV


def upload(api: Api, ocel_id: str, content: bytes = RECORDS_CSV) -> str:
    response = api.upload_record_file(ocel_id, content)
    assert response.status_code == 201, response.text
    return response.json()["uploadId"]


def test_an_upload_shows_the_columns_and_first_rows(api: Api, plain_log: str) -> None:
    uploaded = api.upload_record_file(plain_log, RECORDS_CSV).json()

    assert uploaded["columns"] == ["flow", "object", "quantity", "start", "end", "event"]
    assert (uploaded["rows"], uploaded["delimiter"]) == (5, ",")
    assert uploaded["sample"][3] == ["heat", "m1", "-5", None, None, "e1"]


def test_the_preview_counts_what_fits_the_log(api: Api, plain_log: str) -> None:
    preview = api.preview_record_file(plain_log, upload(api, plain_log), MAPPING).json()

    assert (preview["rows"], preview["usableRows"], preview["eventEnds"]) == (5, 4, 0)
    assert preview["flows"] == [
        {
            "flowId": "electricity",
            "rows": 4,
            "usableRows": 3,
            "intervalRecords": 3,
            "eventRecords": 0,
            "objects": 3,
        },
        {
            "flowId": "heat",
            "rows": 1,
            "usableRows": 1,
            "intervalRecords": 0,
            "eventRecords": 1,
            "objects": 1,
        },
    ]
    assert preview["issues"] == [{"kind": "unknown_object", "rows": 1, "examples": ["nowhere"]}]
    assert preview["sampleIssues"] == [{"row": 4, "kind": "unknown_object"}]
    assert (preview["recordsFrom"], preview["recordsTo"]) == (
        "2026-01-01T00:00:00",
        "2026-01-03T00:00:00",
    )


def test_the_import_takes_the_rows_the_preview_counts_as_usable(api: Api, plain_log: str) -> None:
    preview = api.preview_record_file(plain_log, upload(api, plain_log), MAPPING).json()

    status = api.get_socel_status(build(api, plain_log)).json()

    usable = {flow["flowId"]: flow for flow in preview["flows"]}
    assert status["intervalRecords"] == sum(f["intervalRecords"] for f in usable.values())
    assert status["eventRecords"] == sum(f["eventRecords"] for f in usable.values())


def test_the_preview_reads_german_numbers_and_dates(api: Api, plain_log: str) -> None:
    content = (
        b"flow;object;quantity;start;end\n"
        b"electricity;m1;1.234,5;01.01.2026 00:00;02.01.2026 00:00\n"
    )

    mapping = {**MAPPING, "event": None}

    preview = api.preview_record_file(plain_log, upload(api, plain_log, content), mapping).json()

    assert (preview["usableRows"], preview["decimalComma"], preview["dayFirstDates"]) == (
        1,
        True,
        True,
    )


def test_a_preview_changes_nothing(api: Api, socel: str) -> None:
    before = api.get_socel_status(socel).json()

    api.preview_record_file(socel, upload(api, socel), MAPPING)

    assert api.get_socel_status(socel).json() == before


def test_a_mapping_without_enough_columns_is_refused(api: Api, plain_log: str) -> None:
    response = api.preview_record_file(plain_log, upload(api, plain_log), {"flow": "flow"})

    assert response.status_code == 422


def test_a_mapping_to_a_column_the_file_lacks_is_refused(api: Api, plain_log: str) -> None:
    content = b"flow,object,quantity,start,end\nelectricity,m1,1,2026-01-01,2026-01-02\n"

    response = api.preview_record_file(plain_log, upload(api, plain_log, content), MAPPING)

    assert response.status_code == 422
    assert response.json() == {"detail": "The file has no column event."}


def test_a_file_mapped_for_event_ends_alone_can_be_read(api: Api, plain_log: str) -> None:
    content = b"event,end\ne1,2026-01-01T11:00:00Z\n"

    preview = api.preview_record_file(
        plain_log, upload(api, plain_log, content), {"event": "event", "endTime": "end"}
    ).json()

    assert (preview["usableRows"], preview["eventEnds"]) == (1, 1)


def test_an_unknown_upload_is_refused(api: Api, plain_log: str) -> None:
    response = api.preview_record_file(plain_log, "unknown", MAPPING)

    assert response.status_code == 422
    assert response.json() == {"detail": "The record file is no longer there; upload it again."}


def test_only_the_latest_upload_is_kept(api: Api, plain_log: str) -> None:
    first = upload(api, plain_log)
    second = upload(api, plain_log)

    assert api.preview_record_file(plain_log, first, MAPPING).status_code == 422
    assert api.preview_record_file(plain_log, second, MAPPING).status_code == 200


def test_a_build_with_an_unknown_upload_is_refused(api: Api, plain_log: str) -> None:
    response = api.build_socel(
        plain_log, {"name": "x", "records": {"uploadId": "unknown", "mapping": MAPPING}}
    )

    assert response.status_code == 422


def test_a_build_needs_a_definition_for_every_flow_the_file_brings(
    api: Api, plain_log: str
) -> None:
    response = api.build_socel(
        plain_log,
        {
            "name": "x",
            "flows": {"electricity": {"unit": "kWh", "category": "energy.electricity"}},
            "records": {"uploadId": upload(api, plain_log), "mapping": MAPPING},
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "The flow 'heat' needs a unit and a category."}


def test_a_file_that_is_no_csv_is_refused(api: Api, plain_log: str) -> None:
    response = api.upload_record_file(plain_log, b"\x00\x01\x02 binary")

    assert response.status_code == 422


@pytest.mark.parametrize("content", [b"\x00", b'name\n"text\x00value"\n'])
def test_nul_bytes_are_not_accepted_as_csv_text(api: Api, plain_log: str, content: bytes) -> None:
    assert api.upload_record_file(plain_log, content).status_code == 422
