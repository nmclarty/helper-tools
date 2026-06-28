from typing import Literal

from pydantic import BaseModel, FilePath
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
        with self.file.open() as file:
            data = Data.model_validate_json(file.read())

        table = fmt_table(f"[bold]{self.name}[/bold]")
        for i in data.inputs:
            table.add_row(
                f"{i.name} ([yellow]{i.rev}[/yellow]):",
                f"{fmt_delta(i.modified)}",
            )

        return table
