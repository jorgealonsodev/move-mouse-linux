"""Acción de pausa (sleep) entre acciones."""

import logging
import random
import time

from move_mouse.actions.base import ActionBase, ActionResult
from move_mouse.mouse_controller import MouseController

logger = logging.getLogger(__name__)


class SleepAction(ActionBase):
    """Acción que pausa la ejecución durante un tiempo determinado."""

    def __init__(
        self,
        action_id: str = "sleep",
        name: str = "Pausa",
        is_enabled: bool = True,
        repeat: bool = False,
        trigger: str = "interval",
        repeat_mode: str = "forever",
        interval_throttle: int = 0,
        interval_execution_count: int = 1,
        duration_seconds: float = 1.0,
    ):
        super().__init__(
            action_id=action_id,
            name=name,
            is_enabled=is_enabled,
            repeat=repeat,
            trigger=trigger,
            repeat_mode=repeat_mode,
            interval_throttle=interval_throttle,
            interval_execution_count=interval_execution_count,
        )
        self._duration_seconds = duration_seconds

    @property
    def duration_seconds(self) -> float:
        return self._duration_seconds

    @duration_seconds.setter
    def duration_seconds(self, value: float) -> None:
        if value < 0:
            raise ValueError("La duración no puede ser negativa")
        self._duration_seconds = value

    def execute(self, controller: MouseController) -> ActionResult:
        """Pausa la ejecución durante la duración configurada."""
        if not self.can_execute():
            return ActionResult(aborted=False, error="Acción deshabilitada")

        try:
            logger.debug("Pausa de %.3f segundos", self._duration_seconds)
            time.sleep(self._duration_seconds)
            self._execution_count += 1
            return ActionResult()
        except Exception as exc:
            logger.error("Error en pausa %s: %s", self._id, exc)
            return ActionResult(error=str(exc))
