"""Schedule and blackout models (stub for V2)."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Schedule:
    """Execution schedule configuration (V2)."""
    enabled: bool = False


@dataclass
class Blackout:
    """Blackout period where the engine should not run (V2)."""
    start_hour: Optional[int] = None
    end_hour: Optional[int] = None
