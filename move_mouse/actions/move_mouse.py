"""Acción de movimiento del cursor."""

import logging
from typing import Optional

from move_mouse.actions.base import ActionBase, ActionResult
from move_mouse.mouse_controller import (
    CursorDirection,
    CursorSpeed,
    MouseController,
    SPEED_DELAYS,
)

logger = logging.getLogger(__name__)


class MoveMouseAction(ActionBase):
    """Acción que mueve el cursor según un patrón direccional."""

    def __init__(
        self,
        action_id: str = "move_mouse",
        name: str = "Mover cursor",
        is_enabled: bool = True,
        repeat: bool = False,
        trigger: str = "interval",
        repeat_mode: str = "forever",
        interval_throttle: int = 0,
        interval_execution_count: int = 1,
        direction: CursorDirection = CursorDirection.SQUARE,
        distance: int = 5,
        upper_distance: Optional[int] = None,
        random: bool = False,
        speed: CursorSpeed = CursorSpeed.NORMAL,
        delay: int = 0,
        abort_if_user_activity: bool = True,
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
        self._direction = direction
        self._distance = distance
        self._upper_distance = upper_distance
        self._random = random
        self._speed = speed
        self._delay = delay
        self._abort_if_user_activity = abort_if_user_activity

    @property
    def direction(self) -> CursorDirection:
        return self._direction

    @direction.setter
    def direction(self, value: CursorDirection) -> None:
        self._direction = value

    @property
    def distance(self) -> int:
        return self._distance

    @distance.setter
    def distance(self, value: int) -> None:
        self._distance = value

    @property
    def upper_distance(self) -> Optional[int]:
        return self._upper_distance

    @upper_distance.setter
    def upper_distance(self, value: Optional[int]) -> None:
        self._upper_distance = value

    @property
    def random(self) -> bool:
        return self._random

    @random.setter
    def random(self, value: bool) -> None:
        self._random = value

    @property
    def speed(self) -> CursorSpeed:
        return self._speed

    @speed.setter
    def speed(self, value: CursorSpeed) -> None:
        self._speed = value

    @property
    def delay(self) -> int:
        return self._delay

    @delay.setter
    def delay(self, value: int) -> None:
        self._delay = value

    @property
    def abort_if_user_activity(self) -> bool:
        return self._abort_if_user_activity

    @abort_if_user_activity.setter
    def abort_if_user_activity(self, value: bool) -> None:
        self._abort_if_user_activity = value

    def execute(self, controller: MouseController) -> ActionResult:
        """Ejecuta el movimiento delegando al controlador."""
        if not self.can_execute():
            return ActionResult(aborted=False, error="Acción deshabilitada")

        try:
            delay_ms = self._delay
            if delay_ms == 0:
                delay_ms = SPEED_DELAYS.get(self._speed, 5)

            controller.break_on_user_activity = self._abort_if_user_activity

            aborted = controller.execute_move_action(
                direction=self._direction,
                distance=self._distance,
                delay_ms=delay_ms,
                random_distance=self._random,
                upper_distance=self._upper_distance,
            )

            self._execution_count += 1

            if aborted:
                self._aborted = True
                logger.debug("Acción %s abortada por actividad de usuario", self._id)
                return ActionResult(aborted=True)

            return ActionResult()

        except Exception as exc:
            logger.error("Error ejecutando acción %s: %s", self._id, exc)
            return ActionResult(error=str(exc))
