from typing import Literal

from pydantic import BaseModel


class Services(BaseModel):
    module: Literal["services"]
    name: str = "Services"

    def run(self) -> str:
        return f"[bold]{self.name}[/bold]\n"
