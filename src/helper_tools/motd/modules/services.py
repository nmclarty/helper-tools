import logging

from pydantic import BaseModel, computed_field, field_validator, FilePath, model_validator, Field
from typing import Literal, Any
from subprocess import run, DEVNULL
from ..utils import fmt_table
from rich.console import Group
from rich.padding import Padding
from pathlib import Path
from datetime import datetime
from ..utils import fmt_delta
logger = logging.getLogger(__name__)

class Unit(BaseModel):
    name: str

    state: str = Field(alias="ActiveState")
    exit_time: datetime = Field(alias="ExecMainExitTimestamp")


    @computed_field
    @property
    def is_active(self) -> bool:
        return self.exit_time == "active"
    
    @computed_field
    @property
    def exited(self) -> str:
        return fmt_delta(parser.parse(self.exit_time))

    @classmethod
    def from_name(cls, name: str) -> "Unit":
        # raw = run(["systemctl", "show", name], check=True, capture_output=True, text=True, timeout=1).stdout
        with Path("data/motd/service.txt").open() as f:
            raw = f.read()
        props = dict(item.split("=", 1) for item in raw.split("\n") if "=" in item)
        return cls(name=name, **props)

class Services(BaseModel):
    module: Literal["services"]
    name: str = "Services"
    units: list[Unit] = []
    tasks: list[Unit] = []

    @field_validator("units", "tasks", mode="before")
    @classmethod
    def load_from_name(cls, names: list[str]):
        return [Unit.from_name(name) for name in names]


    def run(self) -> Group:
        group = Group(f"[bold]{self.name}:[/bold]")

        if len(self.units) > 0:
            active = [s for s in self.units if s.is_active]
            if len(active) > 0:
                group.renderables.append(f"  Running: [green]{len(active)}[/green]")

            failed = [s for s in self.units if not s.is_active]
            if len(failed) > 0:
                table = fmt_table("Failed")
                for f in failed:
                    table.add_row(f"- [red]{f.name}[/red]")

                group.renderables.append(Padding.indent(table, 2))

        if len(self.tasks) > 0:
            table = fmt_table("Tasks")
            for t in self.tasks:
                table.add_row(f"{t.name} ({t.state}): {t.exited}")

            group.renderables.append(Padding.indent(table, 2))

        
        # table.add_row("backup ([green]Success[/]): [green]1 day, 5:01:06[/]")
        return group
