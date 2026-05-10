import logging
import subprocess
from functools import cached_property
from typing import Literal
import platform

import psutil
from pydantic import BaseModel, computed_field, field_validator

from ..utils import fmt_delta, os_version

logger = logging.getLogger(__name__)


class Service(BaseModel):
    name: str

    @computed_field
    @cached_property
    def is_active(self) -> bool:
        try:
            return (
                subprocess.run(
                    ["systemctl", "is-active", self.name], stdout=subprocess.DEVNULL
                ).returncode
                == 0
            )
        except FileNotFoundError as e:
            logger.error(e)
            return False


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
            f"  Version: [blue]{os_version()}[/blue]\n"
            f"  Kernel: [blue]{platform.release().split("-")[0]}[/blue]\n"
            f"  Uptime: {fmt_delta(psutil.boot_time())}\n"
            f"  Load: {', '.join([str(round(t, 2)) for t in psutil.getloadavg()])}\n"
        )

        if len(self.services) > 0:
            active = len([s for s in self.services if s.is_active])
            output += f"  Services: [green]{active}[/green] runnning"
            failed = len(self.services) - active
            if failed > 0:
                output += f", [red]{failed}[/red] failed"

        return output + "\n"
