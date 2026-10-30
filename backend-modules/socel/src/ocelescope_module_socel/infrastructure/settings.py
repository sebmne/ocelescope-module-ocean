"""The module's configuration, read from the environment and `.env` once."""

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class SocelSettings(BaseSettings):
    """What the installation configures for the module. Names are matched to
    environment variables regardless of case (`climatiq_api_key` is read from
    `CLIMATIQ_API_KEY`); an empty variable counts as unset."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_ignore_empty=True,
        str_strip_whitespace=True,
    )

    # The folder the host keeps its data in (the Docker volume); shared with
    # Ocelescope's own DATA_DIR.
    data_dir: Path | None = None
    # A Climatiq key set for the installation; it comes before one saved from the app.
    climatiq_api_key: SecretStr | None = None
    # A fixed Climatiq data release ("38"), or the latest within one ("^38");
    # without it the latest release is followed.
    climatiq_data_version: str | None = None

    @property
    def module_dir(self) -> Path:
        """Where the module keeps what must outlast a restart: in DATA_DIR where
        the installation has one, else in the user's home."""
        return (self.data_dir or Path.home() / ".ocelescope") / "socel"
