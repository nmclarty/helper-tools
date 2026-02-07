import logging
from pathlib import Path
from subprocess import DEVNULL, run

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ZpoolConfig(BaseModel):
    name: str
    directory: str
    datasets: list[str]


class Snapshot:
    """Low-level class operating on a ZFS snapshot."""

    def __init__(self, name: str, zpool: str, directory: str) -> None:
        self.name = f"{zpool}/{name}@backup"
        self.path = Path(f"{directory}/{name}")

    def __str__(self) -> str:
        return f"{self.name}:{self.path}"

    def cleanup(self) -> None:
        """Unmount and destroy snapshot."""
        if self.path.is_mount():
            run(["umount", self.path], check=True)

        check_exists = run(
            ["zfs", "list", self.name],
            check=False,
            stdout=DEVNULL,
            stderr=DEVNULL,
        )
        if check_exists.returncode == 0:
            run(["zfs", "destroy", self.name], check=True)

    def snapshot(self) -> None:
        """Create and mount snapshot."""
        run(["zfs", "snapshot", self.name], check=True)

        if not self.path.exists():
            self.path.mkdir()
        run(["mount", "-t", "zfs", self.name, self.path], check=True)


class SnapshotManager:
    """Manages a collection of ZFS snapshots, creating and then cleaning them up when finished."""

    def __init__(self, zpool: ZpoolConfig, services: list[str]):
        self.snapshots = [
            Snapshot(name, zpool.name, zpool.directory) for name in zpool.datasets
        ]
        self.services = services

    def __enter__(self):
        # stop all the services before
        if len(self.services) != 0:
            run(["systemctl", "stop", *self.services], check=True)
            logger.info("Stopped services")

        for s in self.snapshots:
            s.cleanup()
            s.snapshot()
        logger.info("Created temporary snapshots")

        # create long-term snapshots for local recovery
        run(["systemctl", "start", "sanoid.service"], check=True)
        logger.info("Created long-term snapshots")

        # start all the services after
        if len(self.services) != 0:
            run(["systemctl", "start", *self.services], check=True)
            logger.info("Started services")

        return self

    def __exit__(self, exc_type, exc_value, exc_tb) -> None:
        for s in self.snapshots:
            s.cleanup()
        logger.info("Cleaned up snapshots")
