import json
import subprocess
from typing import Literal

import psutil
from pydantic import BaseModel, Field, RootModel

from py_motd.utils import format_ts, os_version


def get_services() -> list[dict]:
    return json.loads(
        subprocess.run(
            [
                "systemctl",
                "list-units",
                "--type",
                "service",
                "--all",
                "--output",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    )


class Service(BaseModel):
    name: str = Field(alias="unit")
    status: str = Field(alias="sub")


Services = RootModel[list[Service]]


class System(BaseModel):
    module: Literal["system"]
    name: str = "System"
    services: list[str]

    def run(self) -> str:
        output = (
            f"[bold]{self.name}:[/bold]\n"
            f"  Version: {os_version()}\n"
            f"  Uptime: {format_ts(psutil.boot_time())}\n"
            f"  Load: {', '.join([str(round(t, 2)) for t in psutil.getloadavg()])}\n"
        )
        services = Services.model_validate(get_services())

        if len(self.services) > 0:
            output += "  Services:\n"
            for service in self.services:
                if (
                    srv := next((s for s in services.root if s.name == service), None)
                ) is not None:
                    output += f"    - {service}: {srv.status}\n"
                else:
                    output += f"    - {service}: Not found\n"

        return output
