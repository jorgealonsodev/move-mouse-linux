"""Mouse click action."""

import logging
import time

from move_mouse.actions.base import ActionBase, ActionResult
from move_mouse.mouse_controller import MouseController

logger = logging.getLogger(__name__)


class ClickMouseAction(ActionBase):
    """Action that simulates a mouse click."""

    def __init__(
        self,
        action_id: str = "click_mouse",
        name: str = "Mouse click",
        is_enabled: bool = True,
        repeat: bool = False,
        trigger: str = "interval",
        repeat_mode: str = "forever",
        interval_throttle: int = 0,
        interval_execution_count: int = 1,
        button: int = 1,
        hold_ms: int = 50,
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
        self._hold_ms = hold_ms

    @property
    def button(self) -> int:
        return self._button

    @button.setter
    def button(self, value: int) -> None:
        if value not in (1, 2, 3):
            raise ValueError(f"Invalid button: {value}. Must be 1, 2, or 3.")
        self._button = value

    @property
    def hold_ms(self) -> int:
        return self._hold_ms

    @hold_ms.setter
    def hold_ms(self, value: int) -> None:
        if value < 0:
            raise ValueError(f"hold_ms cannot be negative: {value}")
        self._hold_ms = value

    def execute(self, controller: MouseController) -> ActionResult:
        """Execute click with press->hold->release pattern."""
        if not self.can_execute():
            return ActionResult(aborted=False, error="Action disabled")

        try:
            logger.debug("Executing click: button=%d, hold=%dms", self._button, self._hold_ms)
            controller.press(self._button)
            if self._hold_ms > 0:
                time.sleep(self._hold_ms / 1000.0)
            controller.release(self._button)
            self._execution_count += 1
            logger.debug("Click completed: button %d", self._button)
            return ActionResult()
        except Exception as exc:
            logger.error("Error executing click %s: %s", self._id, exc)
            return ActionResult(error=str(exc))
