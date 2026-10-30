"""The module's configuration, as the installation gives it."""

from pathlib import Path

import pytest

from ocelescope_module_socel.infrastructure.settings import SocelSettings


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("DATA_DIR", "CLIMATIQ_API_KEY", "CLIMATIQ_DATA_VERSION"):
        monkeypatch.delenv(name, raising=False)


def read(env_file: Path | None = None) -> SocelSettings:
    # pyright does not know BaseSettings' `_env_file`; None reads no .env file.
    return SocelSettings(_env_file=env_file)  # pyright: ignore[reportCallIssue]


def test_nothing_set_is_nothing_configured() -> None:
    settings = read()

    assert (settings.data_dir, settings.climatiq_api_key, settings.climatiq_data_version) == (
        None,
        None,
        None,
    )


def test_the_environment_is_read_by_its_upper_case_names(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("CLIMATIQ_API_KEY", " secret ")
    monkeypatch.setenv("CLIMATIQ_DATA_VERSION", "^38")

    settings = read()

    assert settings.data_dir == tmp_path
    assert settings.climatiq_api_key is not None
    assert settings.climatiq_api_key.get_secret_value() == "secret"
    assert settings.climatiq_data_version == "^38"


def test_a_dotenv_file_is_read(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text('CLIMATIQ_DATA_VERSION="38"\nFRONTEND_URL="elsewhere"\n')

    assert read(tmp_path / ".env").climatiq_data_version == "38"


def test_an_empty_variable_is_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLIMATIQ_API_KEY", "")

    assert read().climatiq_api_key is None


def test_the_key_is_not_shown_in_logs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLIMATIQ_API_KEY", "secret")

    assert "secret" not in repr(read())


def test_the_module_keeps_its_files_in_the_data_folder(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    assert read().module_dir == tmp_path / "socel"


def test_without_a_data_folder_the_module_keeps_its_files_at_home() -> None:
    assert read().module_dir == Path.home() / ".ocelescope" / "socel"
