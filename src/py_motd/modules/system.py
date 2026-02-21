import subprocess
from functools import cached_property
from typing import Literal

import psutil
from pydantic import BaseModel, computed_field, field_validator

from py_motd.utils import format_ts, os_version


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

    def run(self) -> str:
        output = (
            f"[bold]{self.name}:[/bold]\n"
            f"  Version: {os_version()}\n"
            f"  Uptime: {format_ts(psutil.boot_time())}\n"
            f"  Load: {', '.join([str(round(t, 2)) for t in psutil.getloadavg()])}\n"
        )

        if len(self.services) > 0:
            output += "  Services:\n"
            for s in self.services:
                if s.status == "active":
                    output += f"    {s.name}: [green]{s.status}[/green]\n"
                else:
                    output += f"    {s.name}: [red]{s.status}[/red]\n"

        return output
