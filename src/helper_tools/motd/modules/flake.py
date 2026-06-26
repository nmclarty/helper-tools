from typing import Literal
from subprocess import run, CalledProcessError, TimeoutExpired
from datetime import datetime

from pydantic import AliasPath, BaseModel, Field, FilePath, ValidationError
from rich.console import Group
from rich.markup import escape
from rich.padding import Padding
from rich.table import Table

from ..utils import fmt_delta, fmt_table


class Input(BaseModel):
    name: str
    rev: str
    modified: float


class Data(BaseModel):
    inputs: list[Input]


class Flake(BaseModel):
    module: Literal["flake"]
    name: str = "Flake"
    file: FilePath

    def run(self) -> Table | str:
        try:
            with self.file.open() as file:
                data = Data.model_validate_json(file.read())

            table = fmt_table(f"[bold]{self.name}[/bold]")
            for i in data.inputs:
                table.add_row(
                    f"{i.name} ([yellow]{i.rev}[/yellow]):", f"{fmt_delta(i.modified)}"
                )

        except ValidationError:
            return("  Inputs: [red]Failed to parse file[/red]")

        return table
