"""Tests para PositionCursorAction."""

from unittest.mock import MagicMock

import pytest

from move_mouse.actions.position_cursor import PositionCursorAction


class TestPositionCursorAction:
    def test_default_properties(self):
        action = PositionCursorAction()
        assert action.id == "position_cursor"
        assert action.x == 0
        assert action.y == 0

    def test_custom_position(self):
        action = PositionCursorAction(x=100, y=200)
        assert action.x == 100
        assert action.y == 200

    def test_setters(self):
        action = PositionCursorAction()
        action.x = 500
        action.y = 300
        assert action.x == 500
        assert action.y == 300

    def test_execute_calls_move_to(self):
        mock_controller = MagicMock()
        action = PositionCursorAction(x=100, y=200)
        result = action.execute(mock_controller)

        assert result.aborted is False
        mock_controller.move_to.assert_called_once_with(100, 200)

    def test_execute_disabled(self):
        mock_controller = MagicMock()
        action = PositionCursorAction(is_enabled=False, x=10, y=20)
        result = action.execute(mock_controller)

        assert result.error == "Acción deshabilitada"
        mock_controller.move_to.assert_not_called()

    def test_execute_exception(self):
        mock_controller = MagicMock()
        mock_controller.move_to.side_effect = RuntimeError("move_to falló")

        action = PositionCursorAction(x=10, y=20)
        result = action.execute(mock_controller)

        assert result.error == "move_to falló"

    def test_execute_increments_count(self):
        mock_controller = MagicMock()
        action = PositionCursorAction()
        action.execute(mock_controller)
        assert action.execution_count == 1
