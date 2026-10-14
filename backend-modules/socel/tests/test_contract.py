"""The HTTP operations the generated frontend client is built from."""

from ocelescope_backend.app.modules.loader import build_module

from ocelescope_module_socel.module import Socel


def test_the_module_offers_these_operations() -> None:
    schema = build_module(Socel).create_app().openapi()

    operations = {
        (method.upper(), path, operation["operationId"])
        for path, methods in schema["paths"].items()
        for method, operation in methods.items()
    }

    assert operations == {
        ("GET", "/taxonomy", "getClassTaxonomies"),
        ("GET", "/{ocel_id}/status", "getSocelStatus"),
        ("GET", "/{ocel_id}/classes", "getClassCounts"),
        ("GET", "/{ocel_id}/flows", "getFlowInventory"),
        ("GET", "/{ocel_id}/flows/{flow_id}/instances", "getFlowInstances"),
        ("GET", "/{ocel_id}/classification", "getLogClassification"),
        ("POST", "/{ocel_id}/socel", "buildSocel"),
        ("PUT", "/{ocel_id}/socel", "configureSocel"),
        ("POST", "/{ocel_id}/flow-records", "uploadRecordFile"),
        ("POST", "/{ocel_id}/flow-records/{upload_id}/preview", "previewRecordFile"),
        ("POST", "/{ocel_id}/impact", "calculateImpact"),
    }
