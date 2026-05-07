"""Action pipeline executor."""

import logging
from typing import Callable, List, Optional

from move_mouse.actions.base import ActionBase, ActionResult
from move_mouse.mouse_controller import MouseController

logger = logging.getLogger(__name__)


class Executor:
    """Executes a list of actions in order respecting repetition and throttle
    configuration.

    The executor receives a list of actions and a trigger type.
    Only actions whose ``trigger`` matches the provided one are executed.
    Each action runs sequentially; if an action is aborted due to user
    activity and has ``abort_if_user_activity`` enabled, the pipeline stops.

    If an action sets ``puts_engine_to_sleep = True`` (like SleepAction),
    the ``on_sleep`` callback is invoked so the engine transitions to
    the Sleeping state.
    """

    def __init__(
        self,
        actions: List[ActionBase],
        trigger: str = "interval",
        controller: Optional[MouseController] = None,
        on_sleep: Optional[Callable[[], None]] = None,
    ):
        self._actions = actions
        self._trigger = trigger
        self._controller = controller
        self._on_sleep = on_sleep

    @property
    def actions(self) -> List[ActionBase]:
        return self._actions

    @property
    def trigger(self) -> str:
        return self._trigger

    @property
    def controller(self) -> Optional[MouseController]:
        return self._controller

    @controller.setter
    def controller(self, value: MouseController) -> None:
        self._controller = value

    def execute(self, controller: Optional[MouseController] = None) -> bool:
        """Execute all actions in the pipeline.

        Args:
            controller: Mouse controller. If not provided, uses the one
                configured in the constructor.

        Returns:
            True if execution was aborted by user activity,
            False otherwise.
        """
        ctrl = controller or self._controller
        if ctrl is None:
            logger.error("No mouse controller available")
            return False

        logger.info("Starting action pipeline execution (trigger=%s)", self._trigger)
        actions_to_run = [
            a for a in self._actions
            if a.trigger == self._trigger and a.is_enabled and a.can_execute()
        ]
        actions_skipped = [
            a for a in self._actions
            if a.trigger == self._trigger and (not a.is_enabled or not a.can_execute())
        ]
        logger.info(
            "Actions to execute: %d, skipped: %d",
            len(actions_to_run),
            len(actions_skipped),
        )
        for a in actions_skipped:
            if not a.is_enabled:
                logger.debug("Action skipped (disabled): %s", a.id)
            else:
                logger.debug("Action skipped (cannot execute): %s", a.id)

        aborted = False
        for action in self._actions:
            # Filter by trigger
            if action.trigger != self._trigger:
                continue

            if not action.is_enabled:
                logger.debug("Action %s disabled, skipping", action.id)
                continue

            if not action.can_execute():
                logger.debug("Action %s cannot execute this cycle", action.id)
                continue

            logger.debug("Executing action: %s", action.id)
            try:
                result = action.execute(ctrl)
            except Exception as exc:
                logger.error("Error in action %s: %s", action.id, exc)
                result = ActionResult(error=str(exc))

            logger.debug("Action %s result: aborted=%s, error=%s",
                         action.id, result.aborted, result.error)

            if result.aborted:
                logger.info(
                    "Action %s aborted by user activity", action.id
                )
                aborted = True
                # Mark all remaining actions as aborted
                for remaining in self._actions:
                    if remaining is action:
                        continue
                    if remaining.trigger == self._trigger:
                        remaining.aborted = True
                break

            # Detect SleepAction and notify engine
            if getattr(action, "puts_engine_to_sleep", False):
                logger.debug("SleepAction detected, notifying engine")
                if self._on_sleep is not None:
                    self._on_sleep()

        logger.info("Pipeline execution completed (aborted=%s)", aborted)
        return aborted

    def reset_all_cycles(self) -> None:
        """Reset execution count for all actions."""
        for action in self._actions:
            action.reset_cycle()

    def get_actions_for_trigger(self, trigger: str) -> List[ActionBase]:
        """Return actions matching a given trigger."""
        return [a for a in self._actions if a.trigger == trigger]
