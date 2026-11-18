import logging
import signal
import sys

from pydantic import BaseModel, Field
from pydantic_settings import CliPositionalArg

from . import utils
from .services import Services
from .snapshot import SnapshotManager, ZpoolConfig
from .utils import run_cmd

logger = logging.getLogger(__name__)


class Backup(BaseModel):
    """Manage snapshots for a backup commmand"""

    command: CliPositionalArg[list[str]] = Field(
        description="backup commmand to run", default=["sh", "-c", "exit 1"]
    )
    services: list[str] = Field(description="services to stop/start", default=[])
    dry_run: bool = Field(description="show what would be done", default=False)
    zpool: ZpoolConfig

    def cli_cmd(self) -> None:
        signal.signal(signal.SIGTERM, lambda signum, _: sys.exit(128 + signum))

        utils.dry_run = self.dry_run

        services = Services(self.services)
        with SnapshotManager(self.zpool) as snapshots:
            with services.stopped():
                snapshots.create()
            snapshots.mount()
            run_cmd(self.command)

        if services.start_failed:
            logger.error("Backup finished, but some services failed to start")
            sys.exit(1)
