"""Paquete de acciones del motor."""
from .base import ActionBase, ActionResult
from .move_mouse import MoveMouseAction
from .click_mouse import ClickMouseAction
from .position_cursor import PositionCursorAction
from .sleep_action import SleepAction

__all__ = [
    "ActionBase",
    "ActionResult",
    "MoveMouseAction",
    "ClickMouseAction",
    "PositionCursorAction",
    "SleepAction",
]
