import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ocelescope_module_socel.application.ports.catalog_credentials import CatalogKey


class FileCatalogCredentials:
    """A catalog's key from the environment if it holds one, else the one saved
    in a JSON file only the user can read: {"<catalog>": {"apiKey": "..."}}."""

    def __init__(self, path: Path, *, environment: Mapping[str, str | None] | None = None) -> None:
        self._path = path
        self._environment = {
            catalog: key.strip()
            for catalog, key in (environment or {}).items()
            if key is not None and key.strip()
        }

    def key(self, catalog: str) -> CatalogKey | None:
        if catalog in self._environment:
            return CatalogKey(self._environment[catalog], "environment")
        entry = self._read().get(catalog)
        saved = entry.get("apiKey") if isinstance(entry, dict) else None
        return CatalogKey(saved, "saved") if isinstance(saved, str) and saved else None

    def save(self, catalog: str, key: str) -> None:
        self._write({**self._read(), catalog: {"apiKey": key}})

    def remove(self, catalog: str) -> None:
        saved = self._read()
        if catalog in saved:
            del saved[catalog]
            self._write(saved)

    def _read(self) -> dict[str, Any]:
        try:
            saved = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return saved if isinstance(saved, dict) else {}

    def _write(self, saved: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # Written beside it and moved over it: the file is never half written.
        partial = self._path.with_suffix(".partial")
        descriptor = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            json.dump(saved, file)
        os.replace(partial, self._path)
