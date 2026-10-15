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
        ("GET", "/logs/{ocel_id}/summary", "getSocelStatus"),
        ("GET", "/logs/{ocel_id}/class-counts", "getClassCounts"),
        ("GET", "/logs/{ocel_id}/flows", "getFlowInventory"),
        ("GET", "/logs/{ocel_id}/flows/{flow_id}/instances", "getFlowInstances"),
        ("GET", "/logs/{ocel_id}/classification", "getLogClassification"),
        ("POST", "/logs/{ocel_id}/derivations", "buildSocel"),
        ("PATCH", "/logs/{ocel_id}/socel", "configureSocel"),
        ("POST", "/logs/{ocel_id}/record-uploads", "uploadRecordFile"),
        ("POST", "/logs/{ocel_id}/record-uploads/{upload_id}/preview", "previewRecordFile"),
        ("POST", "/logs/{ocel_id}/impact", "calculateImpact"),
    }


def test_creation_and_partial_configuration_have_resource_semantics() -> None:
    schema = build_module(Socel).create_app().openapi()
    paths = schema["paths"]
    assert "201" in paths["/logs/{ocel_id}/derivations"]["post"]["responses"]
    assert "201" in paths["/logs/{ocel_id}/record-uploads"]["post"]["responses"]
    assert "204" in paths["/logs/{ocel_id}/socel"]["patch"]["responses"]
