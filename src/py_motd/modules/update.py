"""MOTD module for system updates."""

from typing import Literal

from pydantic import BaseModel, FilePath

from py_motd.utils import format_ts


class Input(BaseModel):
    name: str
    age: float


class Data(BaseModel):
    commit: str
    age: float
    inputs: list[Input]
    version: str


class Update(BaseModel):
    module: Literal["update"]
    name: str = "Update"
    file: FilePath

    def run(self) -> str:
        """Return the formatted output of the module.

        :return: The module output
        """
        with self.file.open() as file:
            data = Data.model_validate_json(file.read())
        
        output = (
            f"[bold]{self.name}:[/bold]\n"
            f"  Nixpkgs: [blue]{'.'.join(data.version.split('.')[:-1])}[/blue]\n"
            f"  Commit: [yellow]{data.commit}[/yellow] ({format_ts(data.age)})\n"
        )
        if len(data.inputs) > 0:
            output += f"  Inputs:\n"
            for i in data.inputs:
                output += f'    {i.name}: {format_ts(i.age)}\n'
    
        return output
