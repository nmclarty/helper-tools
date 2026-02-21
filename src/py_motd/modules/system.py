from typing import Literal

import psutil
from pydantic import BaseModel

from py_motd.utils import format_ts, os_version


class System(BaseModel):
    module: Literal["system"]
    name: str = "System"

    def run(self) -> str:
        return (
            f"[bold]{self.name}:[/bold]\n"
            f"  Version: {os_version()}\n"
            f"  Uptime: {format_ts(psutil.boot_time())}\n"
            f"  Load: {', '.join([str(round(t, 2)) for t in psutil.getloadavg()])}\n"
        )
