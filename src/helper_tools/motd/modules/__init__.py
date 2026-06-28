from typing import Annotated
from pydantic import Field

from .system import System
from .flake import Flake
from .services import Services

Module = Annotated[System | Flake | Services, Field(discriminator="module")]
