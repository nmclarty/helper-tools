import logging
import tomllib
from asyncio import gather, to_thread
from pathlib import Path
from typing import Annotated, Union

import rich
from pydantic import BaseModel, Field, FilePath, ValidationError
from pydantic_settings import BaseSettings, CliApp, SettingsConfigDict
from rich.columns import Columns

from py_motd.modules.backup import Backup
from py_motd.modules.system import System
from py_motd.modules.update import Update

logger = logging.getLogger(__name__)

Module = Annotated[Union[Backup, System, Update], Field(discriminator="module")]


class Config(BaseModel):
    modules: list[Module]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(cli_kebab_case=True)
    log_level: str = Field(description="Logging level to use.", default="WARNING")
    config_file: FilePath = Field(
        description="Path to configuration file.",
        default=Path("~/.config/py-motd/config.toml").expanduser(),
    )

    async def cli_cmd(self) -> None:
        logging.basicConfig(level=self.log_level)
        with self.config_file.open("rb") as file:
            config = Config.model_validate(tomllib.load(file))

        columns = Columns()
        # run each module in a thread, and then print the ordered output
        for m in await gather(*[to_thread(m.run) for m in config.modules]):
            columns.renderables.append(m)

        rich.print(columns)


def main() -> None:
    """Sync wrapper function for pydantic-settings since cli_cmd
    needs to be called with CliApp.run to work properly."""
    try:
        CliApp.run(Settings)
    except ValidationError as e:
        logger.error(e)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt detected, exiting...")


if __name__ == "__main__":
    main()
