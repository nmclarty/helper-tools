"""Simple tool for loading secrets from a YAML file to podman."""

import asyncio
import logging
import subprocess

import ruamel.yaml
from pydantic import Field, FilePath, ValidationError
from pydantic_settings import BaseSettings, CliApp, SettingsConfigDict

logger = logging.getLogger(__name__)
yaml = ruamel.yaml.YAML()


def flatten(d: dict, parent: str = "", sep: str = "__") -> dict:
    items = {}
    for k, v in d.items():
        new_key = f"{parent}{sep}{k}" if parent else k
        if isinstance(v, dict):
            items.update(flatten(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        cli_kebab_case=True,
        cli_enforce_required=True,
        cli_prog_name="podman_sops",
    )
    log_level: str = Field(description="The logging level to use.", default="INFO")
    secret_file: FilePath = Field(description="The secrets YAML file to be loaded.")

    async def cli_cmd(self) -> None:
        logging.basicConfig(level=self.log_level)

        logger.info("Clearing existing podman secrets")
        subprocess.run(["podman", "secret", "rm", "--all"], check=True)

        logger.info("Adding secrets from %s", self.secret_file)
        tasks = [
            asyncio.to_thread(
                subprocess.run,
                ["podman", "secret", "create", name, "-"],
                check=True,
                text=True,
                input=str(value),
            )
            for name, value in flatten(yaml.load(self.secret_file)).items()
        ]
        await asyncio.gather(*tasks)


def main():
    """Sync wrapper function for pydantic-settings since cli_cmd
    needs to be called with CliApp.run to work properly."""
    try:
        CliApp.run(Settings)
    except ValidationError as e:
        logger.error(e)


if __name__ == "__main__":
    main()
