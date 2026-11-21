import asyncio
import json
import logging
import sys
from os.path import expanduser
from pathlib import Path
from subprocess import PIPE, CalledProcessError, run

from pydantic import BaseModel, Field
from pydantic_settings import CliApp, CliSubCommand

logger = logging.getLogger(__name__)

# custom.apps.images.refs comes from nix-modules' quadlet module
REFS_EXPR = (
    "hosts: builtins.concatMap"
    " (host: host.config.custom.apps.images.refs or [ ])"
    " (builtins.attrValues hosts)"
)


def output(cmd: list[str], cwd: Path | None = None) -> str:
    """Run a command and return its stdout, leaving stderr on the terminal."""
    return run(cmd, check=True, stdout=PIPE, text=True, cwd=cwd).stdout.strip()


def digest(ref: str) -> str:
    return output(["crane", "digest", ref])


class Lock(BaseModel):
    """Lock the image digests of a flake's containers in images.lock

    Run inside a flake whose hosts set custom.apps.images.lock from images.lock
    at its root. Locks images missing from it and drops ones no longer used.
    """

    update: bool = Field(
        description="re-lock all images, not only missing ones", default=False
    )
    override_input: dict[str, str] = Field(
        description="flake inputs to override while evaluating, as name=flake-ref",
        default={},
    )

    async def cli_cmd(self) -> None:
        try:
            await self.lock_images()
        except CalledProcessError as e:
            logger.error(f"{e.cmd[0]} failed with exit code {e.returncode}")
            sys.exit(1)

    async def lock_images(self) -> None:
        root = Path(output(["git", "rev-parse", "--show-toplevel"]))
        lock_file = root / "images.lock"
        old: dict[str, str] = json.loads(lock_file.read_text())

        overrides = [
            arg
            for name, ref in self.override_input.items()
            for arg in ("--override-input", name, expanduser(ref))
        ]
        refs = set(
            json.loads(
                output(
                    ["nix", "eval", "--json", ".#nixosConfigurations"]
                    + overrides
                    + ["--apply", REFS_EXPR],
                    cwd=root,
                )
            )
        )

        to_lock = sorted(ref for ref in refs if self.update or ref not in old)
        digests = await asyncio.gather(
            *(asyncio.to_thread(digest, ref) for ref in to_lock)
        )
        new = {ref: old[ref] for ref in refs if ref in old} | dict(
            zip(to_lock, digests)
        )

        for ref in sorted(new.keys() - old.keys()):
            logger.info(f"Added {ref}")
        for ref in sorted(new.keys() & old.keys()):
            if new[ref] != old[ref]:
                logger.info(f"Updated {ref}")
        for ref in sorted(old.keys() - new.keys()):
            logger.info(f"Removed {ref}")

        lock_file.write_text(json.dumps(new, indent=2, sort_keys=True) + "\n")


class Images(BaseModel):
    """Manage the container images of a flake's hosts"""

    lock: CliSubCommand[Lock]

    def cli_cmd(self) -> None:
        CliApp.run_subcommand(self)
