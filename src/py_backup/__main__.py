import logging
import subprocess

import ruamel.yaml
from pydantic import BaseModel, Field, FilePath, ValidationError
from pydantic_settings import BaseSettings, CliApp, SettingsConfigDict

from .snapshot import SnapshotManager, ZpoolConfig

logger = logging.getLogger(__name__)
yaml = ruamel.yaml.YAML()


class Config(BaseModel):
    services: list[str]
    zpool: ZpoolConfig


class Settings(BaseSettings):
    model_config = SettingsConfigDict(cli_kebab_case=True, env_prefix="PY_BACKUP_")
    log_level: str = Field(description="The logging level to use.", default="INFO")
    config_file: FilePath = Field(description="Path to the configuration file.")

    def cli_cmd(self) -> None:
        logging.basicConfig(level=self.log_level)
        config = Config.model_validate(yaml.load(self.config_file))

        with SnapshotManager(config.zpool, config.services):
            subprocess.run(["resticprofile", "backup"], check=True)
            logger.info("Finished backup")


def main() -> None:
    """Sync wrapper function for pydantic-settings since cli_cmd
    needs to be called with CliApp.run to work properly."""
    try:
        CliApp.run(Settings)
    except ValidationError as e:
        logger.error(e)


if __name__ == "__main__":
    main()
