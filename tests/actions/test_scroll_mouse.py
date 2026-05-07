"""Tests para ScrollMouseAction."""

from unittest.mock import MagicMock

import pytest

from move_mouse.actions.scroll_mouse import ScrollMouseAction


class TestScrollMouseAction:
    def test_default_properties(self):
        action = ScrollMouseAction()
        assert action.id == "scroll_mouse"
        assert action.scroll_amount == 1
        assert action.scroll_direction == "up"

    def test_custom_scroll_amount(self):
        action = ScrollMouseAction(scroll_amount=3)
        assert action.scroll_amount == 3

    def test_custom_scroll_direction_down(self):
        action = ScrollMouseAction(scroll_direction="down")
        assert action.scroll_direction == "down"

    def test_scroll_amount_setter_valid(self):
        action = ScrollMouseAction()
        action.scroll_amount = 5
        assert action.scroll_amount == 5

    def test_scroll_amount_setter_invalid(self):
        action = ScrollMouseAction()
        with pytest.raises(ValueError, match="debe ser >= 1"):
            action.scroll_amount = 0

    def test_scroll_direction_setter_valid(self):
        action = ScrollMouseAction()
        for direction in ("up", "down"):
            action.scroll_direction = direction
            assert action.scroll_direction == direction

    def test_scroll_direction_setter_invalid(self):
        action = ScrollMouseAction()
        with pytest.raises(ValueError, match="scroll_direction inválido"):
            action.scroll_direction = "left"

    def test_execute_scroll_up(self):
        mock_controller = MagicMock()
        action = ScrollMouseAction(scroll_amount=2, scroll_direction="up")
        result = action.execute(mock_controller)

        assert result.aborted is False
        assert result.error is None
        # Scroll up = button 4
        assert mock_controller.click.call_count == 2
        mock_controller.click.assert_called_with(4)

    def test_execute_scroll_down(self):
        mock_controller = MagicMock()
        action = ScrollMouseAction(scroll_amount=3, scroll_direction="down")
        result = action.execute(mock_controller)

        assert result.aborted is False
        assert result.error is None
        # Scroll down = button 5
        assert mock_controller.click.call_count == 3
        mock_controller.click.assert_called_with(5)

    def test_execute_disabled(self):
        mock_controller = MagicMock()
        action = ScrollMouseAction(is_enabled=False)
        result = action.execute(mock_controller)

        assert result.error == "Acción deshabilitada"
        mock_controller.click.assert_not_called()

    def test_execute_exception(self):
        mock_controller = MagicMock()
        mock_controller.click.side_effect = RuntimeError("scroll falló")

        action = ScrollMouseAction()
        result = action.execute(mock_controller)

        assert result.error == "scroll falló"

    def test_execute_increments_count(self):
        mock_controller = MagicMock()
        action = ScrollMouseAction()
        action.execute(mock_controller)
        assert action.execution_count == 1
