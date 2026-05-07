"""Mouse scroll action."""

import logging

from move_mouse.actions.base import ActionBase, ActionResult
from move_mouse.mouse_controller import MouseController

logger = logging.getLogger(__name__)


class ScrollMouseAction(ActionBase):
    """Action that simulates vertical mouse scroll via buttons 4/5 (X11).

    Button 4 = scroll up, button 5 = scroll down.
    """

    def __init__(
        self,
        action_id: str = "scroll_mouse",
        name: str = "Mouse scroll",
        is_enabled: bool = True,
        repeat: bool = False,
        trigger: str = "interval",
        repeat_mode: str = "forever",
        interval_throttle: int = 0,
        interval_execution_count: int = 1,
        scroll_amount: int = 1,
        scroll_direction: str = "up",
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
        self._scroll_amount = scroll_amount
        self._scroll_direction = scroll_direction

    @property
    def scroll_amount(self) -> int:
        return self._scroll_amount

    @scroll_amount.setter
    def scroll_amount(self, value: int) -> None:
        if value < 1:
            raise ValueError(f"scroll_amount must be >= 1: {value}")
        self._scroll_amount = value

    @property
    def scroll_direction(self) -> str:
        return self._scroll_direction

    @scroll_direction.setter
    def scroll_direction(self, value: str) -> None:
        if value not in ("up", "down"):
            raise ValueError(
                f"Invalid scroll_direction: {value}. Must be 'up' or 'down'."
            )
        self._scroll_direction = value

    def execute(self, controller: MouseController) -> ActionResult:
        """Execute vertical scroll delegating to the controller."""
        if not self.can_execute():
            return ActionResult(aborted=False, error="Action disabled")

        try:
            # X11: button 4 = scroll up, button 5 = scroll down
            button = 4 if self._scroll_direction == "up" else 5
            for _ in range(self._scroll_amount):
                controller.click(button)
            self._execution_count += 1
            logger.debug(
                "Scroll executed: %s, amount %d (button %d)",
                self._scroll_direction,
                self._scroll_amount,
                button,
            )
            return ActionResult()
        except Exception as exc:
            logger.error("Error executing scroll %s: %s", self._id, exc)
            return ActionResult(error=str(exc))
