import sys
import logging
from pathlib import Path
from os import environ

import rich.traceback
from rich.console import Console
from rich.logging import RichHandler
from pydantic import Field, ValidationError, BaseModel
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    CliApp,
    CliSubCommand,
    YamlConfigSettingsSource,
)

from .backup.command import Backup
from .deploy.command import Deploy
from .motd.command import Motd
from .secret.command import Secret

err = Console(stderr=True)
rich.traceback.install()


def user_config_path(name: str) -> Path:
    config = Path(environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return config / name / "config.yaml"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        cli_use_class_docs_for_groups=True,
        cli_hide_none_type=True,
        cli_avoid_json=True,
        cli_implicit_flags="toggle",
        cli_kebab_case=True,
        yaml_file=[
            "/etc/helper-tools/config.yaml",
            user_config_path("helper-tools"),
            "config.yaml",
        ],
    )
    log_level: str = Field(description="logging level to use", default="INFO")

    backup: CliSubCommand[Backup]
    deploy: CliSubCommand[Deploy]
    motd: CliSubCommand[Motd]
    secret: CliSubCommand[Secret]

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            YamlConfigSettingsSource(settings_cls),
        )

    def cli_cmd(self) -> None:
        logging.basicConfig(
            level=self.log_level,
            format="%(message)s",
            handlers=[RichHandler()],
        )
        CliApp.run_subcommand(self)


def main() -> None:
    """Wrapper for pydantic-settings's cli_cmd, since it
    needs to be called with CliApp.run to work properly."""
    try:
        CliApp.run(Settings)
    except ValidationError as e:
        err.print(e)
        sys.exit(1)
    except KeyboardInterrupt:
        err.print("Keyboard interrupt detected, exiting...")
        sys.exit(130)


if __name__ == "__main__":
    main()
