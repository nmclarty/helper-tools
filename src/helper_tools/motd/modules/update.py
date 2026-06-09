"""MOTD module for system updates."""

from typing import Literal
from subprocess import run, CalledProcessError, TimeoutExpired
from datetime import datetime

from pydantic import AliasPath, BaseModel, Field, FilePath, ValidationError
from rich.console import Group
from rich.markup import escape
from rich.padding import Padding

from ..utils import fmt_delta, fmt_table


class Status(BaseModel):
    need_to_reboot: bool
    is_suspended: bool
    deployment_status: str = Field(validation_alias=AliasPath("deployer", "deployment", "status"))
    ended_at: datetime = Field(validation_alias=AliasPath("deployer", "deployment", "ended_at"))
    commit_id: str = Field(validation_alias=AliasPath("deployer", "deployment", "generation", "selected_commit_id"))
    commit_msg: str = Field(validation_alias=AliasPath("deployer", "deployment", "generation", "selected_commit_msg"))
    is_testing: bool = Field(validation_alias=AliasPath("deployer", "deployment", "generation", "selected_branch_is_testing"))


class Input(BaseModel):
    name: str
    rev: str
    modified: float


class Data(BaseModel):
    inputs: list[Input]


class Update(BaseModel):
    module: Literal["update"]
    name: str = "Update"
    file: FilePath

    def run(self) -> Group:
        group = Group(f"[bold]{self.name}:[/bold]")

        try:
            status = Status.model_validate_json(
                run(
                    ["comin", "status", "--json"],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=1
                ).stdout
            )

            msg = escape(status.commit_msg.strip()[:20])
            sha = status.commit_id[:7]
            group.renderables.append(f'  Commit: "{msg}" ([yellow]{sha}[/yellow])')

            flags = [
                escape(status.deployment_status),
                "[orange1]testing[/orange1]" if status.is_testing else None,
                "[red]suspended[/red]" if status.is_suspended else None,
                "[magenta]reboot[/magenta]" if status.need_to_reboot else None,
            ]
            built_ago = fmt_delta(status.ended_at)
            group.renderables.append(
                f"  Status: {','.join([f for f in flags if f])} ({built_ago})"
            )

        except FileNotFoundError,CalledProcessError,TimeoutExpired:
            group.renderables.append("  Commit: [red]Failed to run comin[/red]")
        except ValidationError:
            group.renderables.append("  Commit: [red]Failed to parse status[/red]")

        try:
            with self.file.open() as file:
                data = Data.model_validate_json(file.read())

            table = fmt_table("Inputs")
            for i in data.inputs:
                table.add_row(
                    f"{i.name} ([yellow]{i.rev}[/yellow]):", f"{fmt_delta(i.modified)}"
                )
            group.renderables.append(Padding.indent(table, 2))

        except ValidationError:
            group.renderables.append("  Inputs: [red]Failed to parse file[/red]")

        return group
