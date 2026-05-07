"""Sleep (pause) action between other actions."""

import logging
import random
import time

from move_mouse.actions.base import ActionBase, ActionResult
from move_mouse.mouse_controller import MouseController

logger = logging.getLogger(__name__)


class SleepAction(ActionBase):
    """Action that pauses execution for a configured duration.

    When executed, signals the Executor that the engine should transition
    to the Sleeping state via the ``puts_engine_to_sleep`` attribute.
    """

    # Marker for Executor to detect it should put engine in Sleeping
    puts_engine_to_sleep = True

    def __init__(
        self,
        action_id: str = "sleep",
        name: str = "Sleep",
        is_enabled: bool = True,
        repeat: bool = False,
        trigger: str = "interval",
        repeat_mode: str = "forever",
        interval_throttle: int = 0,
        interval_execution_count: int = 1,
        duration_seconds: float = 1.0,
        random_duration: bool = False,
        upper_duration_ms: float = 0.0,
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
        self._random_duration = random_duration
        self._upper_duration_ms = upper_duration_ms

    @property
    def duration_seconds(self) -> float:
        return self._duration_seconds

    @duration_seconds.setter
    def duration_seconds(self, value: float) -> None:
        if value < 0:
            raise ValueError("Duration cannot be negative")
        self._duration_seconds = value

    @property
    def random_duration(self) -> bool:
        return self._random_duration

    @random_duration.setter
    def random_duration(self, value: bool) -> None:
        self._random_duration = value

    @property
    def upper_duration_ms(self) -> float:
        return self._upper_duration_ms

    @upper_duration_ms.setter
    def upper_duration_ms(self, value: float) -> None:
        if value < 0:
            raise ValueError("upper_duration_ms cannot be negative")
        self._upper_duration_ms = value

    def _resolve_duration(self) -> float:
        """Calculate effective duration, applying randomization if applicable."""
        upper_s = self._upper_duration_ms / 1000.0
        if self._random_duration and upper_s > self._duration_seconds:
            return random.uniform(self._duration_seconds, upper_s)
        return self._duration_seconds

    def execute(self, controller: MouseController) -> ActionResult:
        """Pause execution for the configured duration."""
        if not self.can_execute():
            return ActionResult(aborted=False, error="Action disabled")

        try:
            duration = self._resolve_duration()
            logger.debug("Sleep for %.3f seconds", duration)
            time.sleep(duration)
            self._execution_count += 1
            return ActionResult()
        except Exception as exc:
            logger.error("Error in sleep %s: %s", self._id, exc)
            return ActionResult(error=str(exc))
