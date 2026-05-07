"""Tests para ClickMouseAction."""

from unittest.mock import MagicMock

import pytest

from move_mouse.actions.click_mouse import ClickMouseAction


class TestClickMouseAction:
    def test_default_properties(self):
        action = ClickMouseAction()
        assert action.id == "click_mouse"
        assert action.button == 1

    def test_custom_button(self):
        action = ClickMouseAction(button=3)
        assert action.button == 3

    def test_button_setter_valid(self):
        action = ClickMouseAction()
        for btn in (1, 2, 3):
            action.button = btn
            assert action.button == btn

    def test_button_setter_invalid(self):
        action = ClickMouseAction()
        with pytest.raises(ValueError, match="Botón inválido"):
            action.button = 5

    def test_execute_calls_controller_click(self):
        mock_controller = MagicMock()
        action = ClickMouseAction(button=2)
        result = action.execute(mock_controller)

        assert result.aborted is False
        assert result.error is None
        mock_controller.click.assert_called_once_with(2)

    def test_execute_disabled(self):
        mock_controller = MagicMock()
        action = ClickMouseAction(is_enabled=False)
        result = action.execute(mock_controller)

        assert result.error == "Acción deshabilitada"
        mock_controller.click.assert_not_called()

    def test_execute_exception(self):
        mock_controller = MagicMock()
        mock_controller.click.side_effect = RuntimeError("click falló")

        action = ClickMouseAction()
        result = action.execute(mock_controller)

        assert result.error == "click falló"

    def test_execute_increments_count(self):
        mock_controller = MagicMock()
        action = ClickMouseAction()
        action.execute(mock_controller)
        assert action.execution_count == 1
