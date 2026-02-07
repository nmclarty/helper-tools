"""MOTD module for backup status."""

import json
from datetime import datetime
from functools import cached_property
from json.decoder import JSONDecodeError
from typing import ClassVar

from pydantic import BaseModel, FilePath, computed_field

from ..lib import sizeof_fmt


def parse_status(status: dict) -> dict[str, str]:
    """Parse a resticprofile status file to calculate details.

    :param status: A dict containing the unprocessed file.
    :return: A tuple containing the profile name and its age.
    """

    backup = status["profiles"]["default"]["backup"]
    return {
        "status": "Success" if backup["success"] else backup["error"],
        "age": str(
            datetime.now() - datetime.fromisoformat(backup["time"]).replace(tzinfo=None)
        ),
        "added": sizeof_fmt(backup["bytes_added"]),
        "total": sizeof_fmt(backup["bytes_total"]),
    }


class Backup(BaseModel):
    display_name: ClassVar[str] = "Backup"
    status_file: FilePath

    @computed_field
    @cached_property
    def _status(self) -> dict | None:
        with self.status_file.open() as file:
            try:
                return parse_status(json.load(file))
            except (JSONDecodeError, KeyError):
                return None

    def as_dict(self) -> dict:
        """Return the formatted output of the module.

        :return: The module output
        """
        if self._status is not None:
            return {
                "Status": self._status["status"],
                "Run": f"{self._status['age'][:-7]} ago",
                "Added": self._status["added"],
                "Total": self._status["total"],
            }
        else:
            return {"Status": "Failed to parse status file"}
