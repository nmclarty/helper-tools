import logging
from asyncio import gather, to_thread
from os import environ
from pathlib import Path
from typing import Annotated, Union

from pydantic import BaseModel, Field, ValidationError
from pydantic_settings import (
    BaseSettings,
    CliApp,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)
from rich.columns import Columns
from rich.console import Console

from py_motd.modules.backup import Backup
from py_motd.modules.system import System
from py_motd.modules.update import Update

logger = logging.getLogger(__name__)
console = Console(highlight=False)

Module = Annotated[Union[Backup, System, Update], Field(discriminator="module")]


def get_config_path() -> Path:
    config = Path(environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return config / "py-motd" / "config.toml"


class DisplaySettings(BaseModel):
    columns: bool = Field(description="Display modules horizontally", default=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        cli_kebab_case=True,
        cli_avoid_json=True,
        toml_file=get_config_path(),
        env_prefix="PY_MOTD_",
        env_nested_delimiter="__",
    )
    log_level: str = Field(description="Logging level to use", default="WARNING")
    display: DisplaySettings = DisplaySettings()
    modules: list[Module] = Field(
        description="Settings and order of modules",
        default=[],
    )

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
            TomlConfigSettingsSource(settings_cls),
        )

    async def cli_cmd(self) -> None:
        logging.basicConfig(level=self.log_level)

        # run each module in a thread, and then print the ordered output
        modules = await gather(*[to_thread(m.run) for m in self.modules])
        if self.display.columns:
            console.print(Columns(modules, column_first=True))
        else:
            console.print(*modules, end="")


def main() -> None:
    """Wrapper for pydantic-settings since cli_cmd
    needs to be called with CliApp.run to work properly."""
    try:
        CliApp.run(Settings)
    except ValidationError as e:
        logger.error(e)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt detected, exiting...")


if __name__ == "__main__":
    main()
