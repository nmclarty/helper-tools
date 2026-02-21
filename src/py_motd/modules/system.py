import subprocess
from functools import cached_property
from typing import Literal

import psutil
from pydantic import BaseModel, computed_field, field_validator

from py_motd.utils import format_ts, os_version, fmt_table
from rich.console import Group
from rich.padding import Padding


class Service(BaseModel):
    name: str

    @computed_field
    @cached_property
    def status(self) -> str:
        return subprocess.run(
            ["systemctl", "is-active", self.name],
            capture_output=True,
            text=True,
        ).stdout.strip()


class System(BaseModel):
    module: Literal["system"]
    name: str = "System"
    services: list[Service] = []

    @field_validator("services", mode="before")
    @classmethod
    def load_services(cls, names: list[str]):
        return [Service(name=name) for name in names]

    def run(self) -> Group:
        group = Group(
            (
                f"[bold]{self.name}:[/bold]\n"
                f"  Version: {os_version()}\n"
                f"  Uptime: {format_ts(psutil.boot_time())}\n"
                f"  Load: {', '.join([str(round(t, 2)) for t in psutil.getloadavg()])}"
            )
        )

        if len(self.services) > 0:
            table = fmt_table("Services")
            for s in self.services:
                color = "green" if s.status == "active" else "red"
                table.add_row(f"{s.name}:", f"[{color}]{s.status}[/{color}]")
            group.renderables.append(Padding(table, (0, 0, 0, 2)))

        return group
