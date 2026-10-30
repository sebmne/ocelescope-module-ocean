"""The factor catalogs' keys, kept in a file across restarts."""

import stat
from pathlib import Path

from ocelescope_module_socel.application.ports.catalog_credentials import CatalogKey
from ocelescope_module_socel.infrastructure.adapters.factor_catalogs.file_credentials import (
    FileCatalogCredentials,
)


def test_without_a_key_there_is_none(tmp_path: Path) -> None:
    assert FileCatalogCredentials(tmp_path / "keys.json").key("climatiq") is None


def test_a_saved_key_outlasts_a_restart(tmp_path: Path) -> None:
    FileCatalogCredentials(tmp_path / "socel" / "keys.json").save("climatiq", "secret")

    assert FileCatalogCredentials(tmp_path / "socel" / "keys.json").key("climatiq") == CatalogKey(
        "secret", "saved"
    )


def test_each_catalog_keeps_its_own_key(tmp_path: Path) -> None:
    credentials = FileCatalogCredentials(tmp_path / "keys.json")
    credentials.save("climatiq", "one")
    credentials.save("openlca", "two")
    credentials.remove("openlca")

    assert credentials.key("climatiq") == CatalogKey("one", "saved")
    assert credentials.key("openlca") is None


def test_saved_keys_are_readable_by_the_user_alone(tmp_path: Path) -> None:
    FileCatalogCredentials(tmp_path / "keys.json").save("climatiq", "secret")

    assert stat.S_IMODE((tmp_path / "keys.json").stat().st_mode) == 0o600


def test_a_new_key_replaces_the_saved_one(tmp_path: Path) -> None:
    credentials = FileCatalogCredentials(tmp_path / "keys.json")
    credentials.save("climatiq", "old")
    credentials.save("climatiq", "new")

    assert credentials.key("climatiq") == CatalogKey("new", "saved")
    assert [path.name for path in tmp_path.iterdir()] == ["keys.json"]


def test_a_removed_key_is_gone(tmp_path: Path) -> None:
    credentials = FileCatalogCredentials(tmp_path / "keys.json")
    credentials.save("climatiq", "secret")
    credentials.remove("climatiq")
    credentials.remove("climatiq")

    assert credentials.key("climatiq") is None


def test_the_environments_key_comes_first(tmp_path: Path) -> None:
    FileCatalogCredentials(tmp_path / "keys.json").save("climatiq", "saved")

    credentials = FileCatalogCredentials(
        tmp_path / "keys.json", environment={"climatiq": " from-env "}
    )

    assert credentials.key("climatiq") == CatalogKey("from-env", "environment")


def test_a_blank_environment_key_is_none(tmp_path: Path) -> None:
    credentials = FileCatalogCredentials(tmp_path / "keys.json", environment={"climatiq": "  "})

    assert credentials.key("climatiq") is None


def test_an_unreadable_file_holds_no_key(tmp_path: Path) -> None:
    (tmp_path / "keys.json").write_text("not json")

    assert FileCatalogCredentials(tmp_path / "keys.json").key("climatiq") is None


def test_the_key_is_not_shown_in_logs() -> None:
    assert "secret" not in repr(CatalogKey("secret", "saved"))
