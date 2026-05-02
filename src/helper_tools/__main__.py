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
from .motd.command import Motd
from .secret.command import Secret

logger = logging.getLogger(__name__)
err = Console(stderr=True)
rich.traceback.install()


def user_config_dir() -> Path:
    return Path(environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))


class Settings(BaseSettings):
    """Unified CLI for system management tools
    
    Looks for config files in:
      - /etc/helper-tools/config.yaml
      - ~/.config/helper-tools/config.yaml
      - $HELPER_TOOLS_CONFIG_FILE or ./config.yaml
    """

    model_config = SettingsConfigDict(
        cli_use_class_docs_for_groups=True,
        cli_hide_none_type=True,
        cli_avoid_json=True,
        cli_implicit_flags=True,
        cli_kebab_case=True,
        env_prefix="HELPER_TOOLS_",
        env_nested_delimiter="__",
        yaml_file=[
            "/etc/helper-tools/config.yaml",
            user_config_dir() / "helper-tools" / "config.yaml",
            environ.get("HELPER_TOOLS_CONFIG_FILE", "config.yaml"),
        ],
    )
    log_level: str = Field(description="logging level to use", default="INFO")

    backup: CliSubCommand[Backup]
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
        logger.debug(f"Using config: {self.model_dump()}")
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
