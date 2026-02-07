"""MOTD module for system updates."""

from datetime import timedelta
from functools import cached_property
from typing import ClassVar

from pydantic import BaseModel, FilePath, computed_field, field_validator

from ..lib import age


class Data(BaseModel):
    commit: str
    flake: timedelta
    inputs: list[tuple[str, timedelta]]
    version: str

    @field_validator("flake", mode="before")
    @classmethod
    def flake_transformer(cls, flake: str):
        return age(flake)

    @field_validator("inputs", mode="before")
    @classmethod
    def inputs_transformer(cls, inputs: list[dict[str, str]]):
        return [(k, age(v)) for input in inputs for k, v in input.items()]


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
            "Commit": f"{self._data.commit} ({str(self._data.flake)[:-7]} ago)",
            "Inputs": [{k: f"{str(v)[:-7]} ago"} for k, v in self._data.inputs],
        }
