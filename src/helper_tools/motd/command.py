import logging
from asyncio import gather, to_thread

from pydantic import BaseModel, Field
from rich.console import Console
from rich.columns import Columns

from .modules import Module

logger = logging.getLogger(__name__)
console = Console(highlight=False)


async def run_module(m: Module):
    try:
        return await to_thread(m.run)
    except Exception as e:
        logger.error(e)
        return f"{m.name}: [red]Failed to run module[/]\n"


class Motd(BaseModel):
    """Display a message of the day"""

    columns: bool = Field(description="Display modules horizontally", default=True)
    modules: list[Module] = Field(
        description="Settings and order of modules",
        default=[],
    )

    async def cli_cmd(self) -> None:
        # run each module in a thread, and then print the ordered output
        modules = await gather(*[run_module(m) for m in self.modules])
        if self.columns:
            console.print(Columns(modules, column_first=True))
        else:
            console.print(*modules, sep="", end="")
