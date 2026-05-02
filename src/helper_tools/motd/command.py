import logging
from asyncio import gather, to_thread
from typing import Annotated, Union

from pydantic import BaseModel, Field
from rich.console import Console
from rich.columns import Columns

from .modules import Backup, System, Update

logger = logging.getLogger(__name__)
console = Console(highlight=False)

Module = Annotated[Union[Backup, System, Update], Field(discriminator="module")]


class Motd(BaseModel):
    """Display a message of the day"""

    columns: bool = Field(description="Display modules horizontally", default=True)
    modules: list[Module] = Field(
        description="Settings and order of modules",
        default=[],
    )

    async def cli_cmd(self) -> None:
        # run each module in a thread, and then print the ordered output
        modules = await gather(*[to_thread(m.run) for m in self.modules])
        if self.columns:
            console.print(Columns(modules, column_first=True))
        else:
            console.print(*modules, end="")
