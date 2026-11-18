import logging
from pathlib import Path
from subprocess import DEVNULL, CalledProcessError, run

from pydantic import BaseModel, DirectoryPath, Field

from .utils import run_cmd

logger = logging.getLogger(__name__)


class ZpoolConfig(BaseModel):
    name: str = Field(description="name of the ZFS Pool containing the datasets")
    datasets: list[str] = Field(
        description="name(s) of the ZFS datasets to snapshot", min_length=1
    )
    directory: DirectoryPath = Field(description="where to mount snapshots for backup")


class Snapshot:
    """Low-level class operating on a ZFS snapshot."""

    def __init__(self, name: str, zpool: str, directory: DirectoryPath) -> None:
        self.name = f"{zpool}/{name}@backup"
        self.path = Path(f"{directory}/{name}")

    def cleanup(self) -> None:
        """Unmount and destroy snapshot."""
        if self.path.is_mount():
            run_cmd(["umount", str(self.path)])

        exists = run(
            ["zfs", "list", self.name], check=False, stdout=DEVNULL, stderr=DEVNULL
        )
        if exists.returncode == 0:
            run_cmd(["zfs", "destroy", self.name])

    def mount(self) -> None:
        run_cmd(["mkdir", "-p", str(self.path)])
        run_cmd(["mount", "-t", "zfs", self.name, str(self.path)])


class SnapshotManager:
    """Manages a collection of ZFS snapshots, creating and then cleaning them up when finished."""

    def __init__(self, zpool: ZpoolConfig):
        self.snapshots = [
            Snapshot(name, zpool.name, zpool.directory) for name in zpool.datasets
        ]

    def __enter__(self):
        # leftovers from an interrupted run
        for s in self.snapshots:
            s.cleanup()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb) -> None:
        failed = []
        for s in self.snapshots:
            try:
                s.cleanup()
            except CalledProcessError as e:
                logger.error(f"Failed to clean up {s.name}: {e}")
                failed.append(s.name)
        # an error already in flight is the one worth reporting
        if failed and exc_type is None:
            raise RuntimeError(f"Failed to clean up snapshots: {failed}")

    def create(self) -> None:
        # one command, so all datasets are snapshotted atomically
        run_cmd(["zfs", "snapshot", *(s.name for s in self.snapshots)])
        # create long-term snapshots for local recovery
        run_cmd(["systemctl", "start", "sanoid.service"])

    def mount(self) -> None:
        for s in self.snapshots:
            s.mount()
