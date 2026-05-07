"""Acción de posicionamiento absoluto del cursor."""

import logging

from move_mouse.actions.base import ActionBase, ActionResult
from move_mouse.mouse_controller import MouseController

logger = logging.getLogger(__name__)


class PositionCursorAction(ActionBase):
    """Acción que mueve el cursor a una coordenada absoluta."""

    def __init__(
        self,
        action_id: str = "position_cursor",
        name: str = "Posicionar cursor",
        is_enabled: bool = True,
        repeat: bool = False,
        trigger: str = "interval",
        repeat_mode: str = "forever",
        interval_throttle: int = 0,
        interval_execution_count: int = 1,
        x: int = 0,
        y: int = 0,
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
        self._x = x
        self._y = y

    @property
    def x(self) -> int:
        return self._x

    @x.setter
    def x(self, value: int) -> None:
        self._x = value

    @property
    def y(self) -> int:
        return self._y

    @y.setter
    def y(self, value: int) -> None:
        self._y = value

    def execute(self, controller: MouseController) -> ActionResult:
        """Mueve el cursor a la posición absoluta (x, y)."""
        if not self.can_execute():
            return ActionResult(aborted=False, error="Acción deshabilitada")

        try:
            controller.move_to(self._x, self._y)
            self._execution_count += 1
            logger.debug("Cursor posicionado en (%d, %d)", self._x, self._y)
            return ActionResult()
        except Exception as exc:
            logger.error("Error posicionando cursor %s: %s", self._id, exc)
            return ActionResult(error=str(exc))
