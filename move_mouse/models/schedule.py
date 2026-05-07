"""Modelos de agenda y blackout (stub para V2)."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Schedule:
    """Configuración de horario de ejecución (V2)."""
    enabled: bool = False


@dataclass
class Blackout:
    """Período de blackout donde el motor no debe ejecutarse (V2)."""
    start_hour: Optional[int] = None
    end_hour: Optional[int] = None
