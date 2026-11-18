import logging
from collections.abc import Iterator
from contextlib import contextmanager
from subprocess import PIPE, run

from .utils import run_cmd

logger = logging.getLogger(__name__)

RUNNING_STATES = {"active", "activating", "reloading"}


def running_units(units: list[str]) -> list[str]:
    if not units:
        return []
    # is-active prints one state per unit and exits non-zero if any isn't active
    result = run(
        ["systemctl", "is-active", *units], stdout=PIPE, text=True, check=False
    )
    states = result.stdout.splitlines()
    return [u for u, s in zip(units, states) if s in RUNNING_STATES]


class Services:
    def __init__(self, units: list[str]) -> None:
        self.units = units
        self.start_failed = False

    @contextmanager
    def stopped(self) -> Iterator[None]:
        running = running_units(self.units)
        skipped = [u for u in self.units if u not in running]
        if skipped:
            logger.info(f"Leaving services that aren't running alone: {skipped}")

        try:
            if running:
                run_cmd(["systemctl", "stop", *running])
            yield
        finally:
            if running:
                self._start(running)

    def _start(self, units: list[str]) -> None:
        # systemctl still starts the rest when one fails, so the backup can go ahead
        if not run_cmd(["systemctl", "start", *units], check=False):
            self.start_failed = True
            running = running_units(units)
            logger.error(
                f"Failed to start services: {[u for u in units if u not in running]}"
            )
