import logging
import subprocess
import asyncio
from typing import Union

import yaml
from pydantic import BaseModel, FilePath, Field


logger = logging.getLogger(__name__)


def flatten(d: dict, parent: str = "", sep: str = "__") -> dict:
    items = {}
    for k, v in d.items():
        new_key = f"{parent}{sep}{k}" if parent else k
        if isinstance(v, dict):
            items.update(flatten(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items


class Secret(BaseModel):
    """Declaratively load secrets into Podman"""

    dry_run: bool = Field(description="show what would be done", default=False)
    file: FilePath = Field(description="YAML file containing secrets to be synced")

    async def cli_cmd(self) -> None:
        logger.debug("Removing existing secrets from Podman")
        if not self.dry_run:
            subprocess.run(
                ["podman", "secret", "rm", "--all"],
                check=True,
                stdout=subprocess.DEVNULL,
            )
            logger.info("Removed existing secrets from Podman")

        with self.file.open() as file:
            secrets = flatten(yaml.safe_load(file) or {})

        logger.debug(f"Adding {len(secrets)} secrets from {self.file}")
        if not self.dry_run:
            tasks = [
                asyncio.to_thread(
                    subprocess.run,
                    ["podman", "secret", "create", name, "-"],
                    check=True,
                    text=True,
                    input=str(value),
                    stdout=subprocess.DEVNULL,
                )
                for name, value in secrets.items()
            ]
            await asyncio.gather(*tasks)
            logger.info("Added secrets to Podman")
