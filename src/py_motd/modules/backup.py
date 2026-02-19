"""MOTD module for backup status."""

from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    FilePath,
    ValidationError,
    computed_field,
    field_validator,
    model_validator,
)

from py_motd.utils import format_ts, sizeof_fmt


class Data(BaseModel):
    success: bool
    error: str
    time: datetime
    added: str = Field(alias="bytes_added")
    total: str = Field(alias="bytes_total")

    @model_validator(mode="before")
    @classmethod
    def extract(cls, data: dict):
        return data["profiles"]["default"]["backup"]

    @field_validator("added", "total", mode="before")
    @classmethod
    def size(cls, data: float) -> str:
        return sizeof_fmt(data)

    @computed_field
    @property
    def status(self) -> str:
        return "Success" if self.success else self.error

    @computed_field
    @property
    def age(self) -> str:
        return format_ts(self.time.timestamp())


class Backup(BaseModel):
    name: Literal["backup"]
    display_name: str = "Backup"
    file: FilePath

    def run(self) -> str:
        """Return the formatted output of the module.

        :return: The module output
        """
        try:
            with self.file.open() as file:
                data = Data.model_validate_json(file.read())

                return (
                    f"[bold]{self.display_name}:[/bold]\n"
                    f"  Status: {data.status} ({data.age})\n"
                    f"  Added: {data.added}\n"
                    f"  Total: {data.total}\n"
                )
        except (ValidationError):
            return (
                f"[bold]{self.display_name}:[/bold]\n"
                "  Status: [red]Failed to parse status file[/red]\n"
            )
