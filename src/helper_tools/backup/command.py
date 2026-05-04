import logging
import subprocess

from pydantic import BaseModel, Field
from pydantic_settings import CliPositionalArg

from .snapshot import SnapshotManager, ZpoolConfig

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
        with SnapshotManager(self.zpool, self.services, self.dry_run):
            logger.debug(f"Running command: {self.command}")
            if not self.dry_run:
                subprocess.run(self.command, check=True)
                logger.info("Finished running command")
