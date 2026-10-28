import json
from collections.abc import Mapping
from typing import Any

from fastapi.testclient import TestClient
from httpx import Response


class Api:
    """The module's HTTP operations, by operation id. The paths live here only,
    so a change of the routes changes this file and not the tests."""

    def __init__(self, client: TestClient) -> None:
        self._client = client

    def get_class_taxonomies(self) -> Response:
        return self._client.get("/taxonomy")

    def get_log_classification(self, ocel_id: str, *, original: bool = False) -> Response:
        return self._client.get(
            f"/logs/{ocel_id}/classification",
            params={"ocel_version": "original" if original else "filtered"},
        )

    def build_socel(self, ocel_id: str, body: dict[str, Any]) -> Response:
        return self._client.post(f"/logs/{ocel_id}/derivations", json=body)

    def configure_socel(self, ocel_id: str, body: dict[str, Any]) -> Response:
        return self._client.patch(f"/logs/{ocel_id}/socel", json=body)

    def upload_record_file(self, ocel_id: str, content: bytes) -> Response:
        return self._client.post(
            f"/logs/{ocel_id}/record-uploads", files={"file": ("records.csv", content, "text/csv")}
        )

    def preview_record_file(
        self, ocel_id: str, upload_id: str, mapping: Mapping[str, str | None]
    ) -> Response:
        return self._client.post(
            f"/logs/{ocel_id}/record-uploads/{upload_id}/preview", json=dict(mapping)
        )

    def get_socel_status(self, ocel_id: str) -> Response:
        return self._client.get(f"/logs/{ocel_id}/summary")

    def get_class_counts(self, ocel_id: str) -> Response:
        return self._client.get(f"/logs/{ocel_id}/class-counts")

    def get_flow_inventory(self, ocel_id: str) -> Response:
        return self._client.get(f"/logs/{ocel_id}/flows")

    def get_flow_instances(self, ocel_id: str, flow_id: str, **params: Any) -> Response:
        return self._client.get(f"/logs/{ocel_id}/flows/{flow_id}/instances", params=params)

    def get_flow_records(self, ocel_id: str, flow_id: str, **params: Any) -> Response:
        return self._client.get(f"/logs/{ocel_id}/flows/{flow_id}/records", params=params)

    def calculate_impact(
        self, ocel_id: str, factors: dict[str, dict[str, float]], period: str = "day"
    ) -> Response:
        return self.calculate_impact_from_json(
            ocel_id, json.dumps({"period": period, "factors": factors}).encode()
        )

    def calculate_impact_from_json(self, ocel_id: str, body: bytes) -> Response:
        """The request as raw JSON, for values such as Infinity that a dict
        cannot be sent with."""
        return self._client.post(
            f"/logs/{ocel_id}/impact", content=body, headers={"content-type": "application/json"}
        )
