"""Acción de click del mouse."""

import logging

from move_mouse.actions.base import ActionBase, ActionResult
from move_mouse.mouse_controller import MouseController

logger = logging.getLogger(__name__)


class ClickMouseAction(ActionBase):
    """Acción que simula un click del mouse."""

    def __init__(
        self,
        action_id: str = "click_mouse",
        name: str = "Click del mouse",
        is_enabled: bool = True,
        repeat: bool = False,
        trigger: str = "interval",
        repeat_mode: str = "forever",
        interval_throttle: int = 0,
        interval_execution_count: int = 1,
        button: int = 1,
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
        self._button = button

    @property
    def button(self) -> int:
        return self._button

    @button.setter
    def button(self, value: int) -> None:
        if value not in (1, 2, 3):
            raise ValueError(f"Botón inválido: {value}. Debe ser 1, 2 o 3.")
        self._button = value

    def execute(self, controller: MouseController) -> ActionResult:
        """Ejecuta el click delegando al controlador."""
        if not self.can_execute():
            return ActionResult(aborted=False, error="Acción deshabilitada")

        try:
            controller.click(self._button)
            self._execution_count += 1
            logger.debug("Click ejecutado: botón %d", self._button)
            return ActionResult()
        except Exception as exc:
            logger.error("Error ejecutando click %s: %s", self._id, exc)
            return ActionResult(error=str(exc))
