"""MOTD module for system updates."""

from typing import Literal

from pydantic import BaseModel, FilePath
from rich.console import Group
from rich.padding import Padding

from py_motd.utils import fmt_delta, fmt_table


class Input(BaseModel):
    rev: str
    modified: float


class NamedInput(Input):
    name: str


class Data(BaseModel):
    nixpkgs: Input
    config: Input
    inputs: list[NamedInput]


class Update(BaseModel):
    module: Literal["update"]
    name: str = "Update"
    file: FilePath

    def run(self) -> Group:
        with self.file.open() as file:
            data = Data.model_validate_json(file.read())

        group = Group(
            (
                f"[bold]{self.name}:[/bold]\n"
                f"  Nixpkgs: [blue]{data.nixpkgs.rev}[/blue] ({fmt_delta(data.nixpkgs.modified)})\n"
                f"  Config: [yellow]{data.config.rev}[/yellow] ({fmt_delta(data.config.modified)})"
            )
        )

        if len(data.inputs) > 0:
            table = fmt_table("Inputs")
            for i in data.inputs:
                table.add_row(f"{i.name}:", fmt_delta(i.modified))
            group.renderables.append(Padding(table, (0, 0, 0, 2)))

        return group
