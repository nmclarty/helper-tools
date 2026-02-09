"""MOTD module for system updates."""

from datetime import datetime, timedelta
from functools import cached_property
from typing import ClassVar

from pydantic import BaseModel, FilePath, computed_field


def timestamp_age(ts: float) -> timedelta:
    return datetime.now() - datetime.fromtimestamp(ts)


class Data(BaseModel):
    commit: str
    flake: float
    inputs: list[dict[str, float]]
    version: str


class Update(BaseModel):
    """MOTD module to show information about NixOS generations and flake inputs."""

    display_name: ClassVar[str] = "Update"
    data_file: FilePath

    @computed_field
    @cached_property
    def _data(self) -> Data:
        with self.data_file.open() as file:
            return Data.model_validate_json(file.read())

    def as_dict(self) -> dict:
        """Return the formatted output of the module.

        :return: The module output
        """
        return {
            "Version": ".".join(self._data.version.split(".")[:-1]),
            "Commit": f"{self._data.commit} ({str(timestamp_age(self._data.flake))[:-7]} ago)",
            "Inputs": [
                {k: f"{str(timestamp_age(v))[:-7]} ago"}
                for input in self._data.inputs
                for k, v in input.items()
            ],
        }
