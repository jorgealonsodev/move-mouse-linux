"""Clase base abstracta para todas las acciones."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from move_mouse.mouse_controller import MouseController

logger = logging.getLogger(__name__)


@dataclass
class ActionResult:
    """Resultado de la ejecución de una acción."""

    aborted: bool = False
    error: Optional[str] = None


class ActionBase(ABC):
    """Clase base abstracta para acciones del motor.

    Cada acción tiene propiedades de configuración (id, nombre, repetición,
    disparador) y debe implementar ``can_execute`` y ``execute``.
    """

    def __init__(
        self,
        action_id: str,
        name: str,
        is_enabled: bool = True,
        repeat: bool = False,
        trigger: str = "start",
        repeat_mode: str = "forever",
        interval_throttle: int = 0,
        interval_execution_count: int = 1,
    ):
        self._id = action_id
        self._name = name
        self._is_enabled = is_enabled
        self._repeat = repeat
        self._trigger = trigger  # start | interval | stop
        self._repeat_mode = repeat_mode  # forever | throttle
        self._interval_throttle = interval_throttle
        self._interval_execution_count = interval_execution_count
        self._aborted = False
        self._execution_count = 0

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_enabled(self) -> bool:
        return self._is_enabled

    @is_enabled.setter
    def is_enabled(self, value: bool) -> None:
        self._is_enabled = value

    @property
    def repeat(self) -> bool:
        return self._repeat

    @property
    def trigger(self) -> str:
        return self._trigger

    @property
    def repeat_mode(self) -> str:
        return self._repeat_mode

    @property
    def interval_throttle(self) -> int:
        return self._interval_throttle

    @property
    def interval_execution_count(self) -> int:
        return self._interval_execution_count

    @property
    def aborted(self) -> bool:
        return self._aborted

    @aborted.setter
    def aborted(self, value: bool) -> None:
        self._aborted = value

    @property
    def execution_count(self) -> int:
        return self._execution_count

    def can_execute(self) -> bool:
        """Determina si la acción puede ejecutarse en este ciclo.

        Verifica ``is_enabled`` y, si el modo es ``throttle``, respeta el
        conteo de ejecuciones por intervalo.
        """
        if not self._is_enabled:
            return False
        if self._repeat_mode == "throttle" and self._interval_throttle > 0:
            if self._execution_count >= self._interval_execution_count:
                return False
        return True

    @abstractmethod
    def execute(self, controller: MouseController) -> ActionResult:
        """Ejecuta la acción usando el controlador de mouse provisto.

        Retorna un ``ActionResult`` indicando si fue abortada o si hubo error.
        """
        ...

    def reset_cycle(self) -> None:
        """Reinicia el conteo de ejecuciones para un nuevo ciclo de intervalo."""
        self._execution_count = 0

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self._id!r}, name={self._name!r}, "
            f"enabled={self._is_enabled})"
        )
