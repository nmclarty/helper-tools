import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Deploy(BaseModel):
    """Deploy configuration to host(s)"""

    yes: bool | None = True

    def cli_cmd(self) -> None:
        logger.info("info")
        logger.error("error")
        # raise ValueError
