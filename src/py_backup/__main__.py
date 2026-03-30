import logging
import subprocess
import tomllib
from pathlib import Path

from pydantic import BaseModel, Field, FilePath, ValidationError
from pydantic_settings import BaseSettings, CliApp, SettingsConfigDict

from .snapshot import SnapshotManager, ZpoolConfig

logger = logging.getLogger(__name__)


class Config(BaseModel):
    services: list[str]
    zpool: ZpoolConfig


class Settings(BaseSettings):
    model_config = SettingsConfigDict(cli_kebab_case=True, env_prefix="PY_BACKUP_")
    log_level: str = Field(description="The logging level to use.", default="INFO")
    config_file: FilePath = Field(
        description="Path to the configuration file.",
        default=Path("/etc/py-backup/config.toml"),
    )
    command: list[str] = Field(description="Wrapped backup command to run")

    def cli_cmd(self) -> None:
        logging.basicConfig(level=self.log_level)
        with self.config_file.open("rb") as file:
            config = Config.model_validate(tomllib.load(file))

        with SnapshotManager(config.zpool, config.services):
            logger.debug("Starting running command")
            subprocess.run(self.command, check=True)
            logger.info("Finished running command")


def main() -> None:
    """Sync wrapper function for pydantic-settings since cli_cmd
    needs to be called with CliApp.run to work properly."""
    try:
        CliApp.run(Settings)
    except ValidationError as e:
        logger.error(e)


if __name__ == "__main__":
    main()
