import logging
from typing import Literal
import platform

import psutil
from pydantic import BaseModel

from ..utils import fmt_delta, os_version

logger = logging.getLogger(__name__)


class System(BaseModel):
    module: Literal["system"]
    name: str = "System"

    def run(self) -> str:
        return (
            f"[bold]{self.name}:[/bold]\n"
            f"  Version: [blue]{os_version()}[/blue]\n"
            f"  Kernel: [blue]{platform.release().split('-')[0]}[/blue]\n"
            f"  Uptime: {fmt_delta(psutil.boot_time())}\n"
            f"  Load: {', '.join([str(round(t, 2)) for t in psutil.getloadavg()])}\n"
        )
