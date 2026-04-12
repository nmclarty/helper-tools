"""MOTD module for system updates."""

from typing import Literal

from pydantic import BaseModel, FilePath
from rich.console import Group
from rich.padding import Padding
from rich.table import Table

from py_motd.utils import fmt_delta, fmt_table


class Input(BaseModel):
    name: str
    rev: str
    modified: float


class Data(BaseModel):
    inputs: list[Input]


class Update(BaseModel):
    module: Literal["update"]
    name: str = "Update"
    file: FilePath

    def run(self) -> Table:
        with self.file.open() as file:
            data = Data.model_validate_json(file.read())

        table = fmt_table("[bold]Inputs[/bold]")
        for i in data.inputs:
            table.add_row(
                f"{i.name} ([yellow]{i.rev}[/yellow]):", f"{fmt_delta(i.modified)}"
            )

        return table
