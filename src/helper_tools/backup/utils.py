import logging
import shlex
from subprocess import run

logger = logging.getLogger(__name__)

# read as utils.dry_run; importing it by name copies this default
dry_run = True


def run_cmd(cmd: list[str], check: bool = True) -> bool:
    """Run a command that changes the system, or only log it in a dry run."""
    if dry_run:
        logger.info(f"Would run: {shlex.join(cmd)}")
        return True
    logger.info(f"Running: {shlex.join(cmd)}")
    return run(cmd, check=check).returncode == 0
