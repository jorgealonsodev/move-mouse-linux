"""Tests para MoveMouseAction."""

from unittest.mock import MagicMock, patch

import pytest

from move_mouse.actions.move_mouse import MoveMouseAction
from move_mouse.mouse_controller import CursorDirection, CursorSpeed


class TestMoveMouseAction:
    def test_default_properties(self):
        action = MoveMouseAction()
        assert action.id == "move_mouse"
        assert action.direction == CursorDirection.SQUARE
        assert action.distance == 5
        assert action.upper_distance is None
        assert action.random is False
        assert action.speed == CursorSpeed.NORMAL
        assert action.delay == 0
        assert action.abort_if_user_activity is True

    def test_custom_properties(self):
        action = MoveMouseAction(
            action_id="custom_move",
            direction=CursorDirection.NORTH,
            distance=10,
            upper_distance=20,
            random=True,
            speed=CursorSpeed.FAST,
            delay=5,
            abort_if_user_activity=False,
        )
        assert action.direction == CursorDirection.NORTH
        assert action.distance == 10
        assert action.upper_distance == 20
        assert action.random is True
        assert action.speed == CursorSpeed.FAST
        assert action.delay == 5
        assert action.abort_if_user_activity is False

    def test_setters(self):
        action = MoveMouseAction()
        action.direction = CursorDirection.EAST
        action.distance = 15
        action.upper_distance = 30
        action.random = True
        action.speed = CursorSpeed.SLOW
        action.delay = 10
        action.abort_if_user_activity = False

        assert action.direction == CursorDirection.EAST
        assert action.distance == 15
        assert action.upper_distance == 30
        assert action.random is True
        assert action.speed == CursorSpeed.SLOW
        assert action.delay == 10
        assert action.abort_if_user_activity is False

    def test_execute_calls_controller(self):
        mock_controller = MagicMock()
        mock_controller.execute_move_action.return_value = False

        action = MoveMouseAction(
            direction=CursorDirection.NORTH,
            distance=10,
            speed=CursorSpeed.NORMAL,
        )
        result = action.execute(mock_controller)

        assert result.aborted is False
        assert result.error is None
        mock_controller.execute_move_action.assert_called_once()
        mock_controller.break_on_user_activity = True

    def test_execute_aborted_by_user_activity(self):
        mock_controller = MagicMock()
        mock_controller.execute_move_action.return_value = True

        action = MoveMouseAction()
        result = action.execute(mock_controller)

        assert result.aborted is True
        assert action.aborted is True

    def test_execute_disabled_returns_error(self):
        mock_controller = MagicMock()
        action = MoveMouseAction(is_enabled=False)
        result = action.execute(mock_controller)

        assert result.error == "Acción deshabilitada"
        mock_controller.execute_move_action.assert_not_called()

    def test_execute_uses_delay_when_provided(self):
        mock_controller = MagicMock()
        mock_controller.execute_move_action.return_value = False

        action = MoveMouseAction(delay=10, speed=CursorSpeed.FAST)
        action.execute(mock_controller)

        # delay=10 debe usarse en lugar del SPEED_DELAYS de FAST (0)
        call_kwargs = mock_controller.execute_move_action.call_args[1]
        assert call_kwargs["delay_ms"] == 10

    def test_execute_uses_speed_delay_when_no_delay(self):
        mock_controller = MagicMock()
        mock_controller.execute_move_action.return_value = False

        action = MoveMouseAction(speed=CursorSpeed.SLOW, delay=0)
        action.execute(mock_controller)

        call_kwargs = mock_controller.execute_move_action.call_args[1]
        assert call_kwargs["delay_ms"] == 10  # SLOW = 10ms

    def test_execute_exception_returns_error(self):
        mock_controller = MagicMock()
        mock_controller.execute_move_action.side_effect = RuntimeError("fallo X11")

        action = MoveMouseAction()
        result = action.execute(mock_controller)

        assert result.error == "fallo X11"
        assert result.aborted is False

    def test_execute_increments_count(self):
        mock_controller = MagicMock()
        mock_controller.execute_move_action.return_value = False

        action = MoveMouseAction()
        action.execute(mock_controller)
        assert action.execution_count == 1
