import logging

from pydantic import (
    BaseModel,
    computed_field,
    field_validator,
    FilePath,
    model_validator,
    Field,
)
from typing import Literal, Any
from subprocess import run, DEVNULL
from ..utils import fmt_table
from rich.console import Group
from rich.padding import Padding
from pathlib import Path
from datetime import datetime
from ..utils import fmt_delta
from shutil import which

logger = logging.getLogger(__name__)


class Unit(BaseModel):
    name: str
    state: str = Field(alias="ActiveState")
    status: str = Field(alias="ExecMainStatus")
    exit_time: str | None = Field(alias="ExecMainExitTimestamp", default=None)

    @computed_field
    @property
    def active(self) -> bool:
        return self.state == "active"

    @computed_field
    @property
    def succeeded(self) -> bool:
        return self.state == "inactive" and self.status == "0"

    @computed_field
    @property
    def exited(self) -> str:
        if self.exit_time:
            return fmt_delta(
                datetime.strptime(
                    self.exit_time.rsplit(" ", 1)[0], "%a %Y-%m-%d %H:%M:%S"
                )
            )
        else:
            return "N/A"

    @computed_field
    @property
    def task_color(self) -> str:
        if self.succeeded:
            return "green"
        elif self.active:
            return "orange1"
        else:
            return "red"

    @classmethod
    def from_name(cls, name: str, stub_dir: Path | None = None) -> "Unit":
        if stub_dir:
            raw = (stub_dir / name).read_text()
        else:
            raw = run(
                ["systemctl", "show", name],
                check=True,
                capture_output=True,
                text=True,
                timeout=1,
            ).stdout

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
        if not which("systemctl"):
            stub_dir = Path("data/motd/services")
            logger.warning(
                "Systemctl not found. Using unit file stubs in '%s'", stub_dir
            )
        else:
            stub_dir = None

        return [Unit.from_name(name, stub_dir) for name in names]

    def run(self) -> Group:
        group = Group(f"[bold]{self.name}:[/bold]")

        if len(self.units) > 0:
            active = [s for s in self.units if s.active]
            if len(active) > 0:
                group.renderables.append(f"  Running: [green]{len(active)}[/green]")

            failed = [s for s in self.units if not s.active]
            if len(failed) > 0:
                table = fmt_table("Failed")
                for f in failed:
                    table.add_row(f"- [red]{f.name}[/red]")

                group.renderables.append(Padding.indent(table, 2))

        if len(self.tasks) > 0:
            table = fmt_table("Tasks")
            for t in self.tasks:
                table.add_row(
                    f"{t.name} ([{t.task_color}]{t.state}[/]):", f"{t.exited}"
                )

            group.renderables.append(Padding.indent(table, 2))

        return group
