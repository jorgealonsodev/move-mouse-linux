"""Tests para SleepAction."""

from unittest.mock import MagicMock, patch

import pytest

from move_mouse.actions.sleep_action import SleepAction


class TestSleepAction:
    def test_default_properties(self):
        action = SleepAction()
        assert action.id == "sleep"
        assert action.duration_seconds == 1.0
        assert action.random_duration is False
        assert action.upper_duration_ms == 0.0
        assert action.puts_engine_to_sleep is True

    def test_custom_duration(self):
        action = SleepAction(duration_seconds=5.5)
        assert action.duration_seconds == 5.5

    def test_setter_valid(self):
        action = SleepAction()
        action.duration_seconds = 3.0
        assert action.duration_seconds == 3.0

    def test_setter_negative_raiseses(self):
        action = SleepAction()
        with pytest.raises(ValueError, match="no puede ser negativa"):
            action.duration_seconds = -1.0

    def test_execute_sleeps(self):
        mock_controller = MagicMock()
        action = SleepAction(duration_seconds=0.01)

        with patch("move_mouse.actions.sleep_action.time.sleep") as mock_sleep:
            result = action.execute(mock_controller)
            mock_sleep.assert_called_once_with(0.01)

        assert result.aborted is False
        assert result.error is None

    def test_execute_disabled(self):
        mock_controller = MagicMock()
        action = SleepAction(is_enabled=False, duration_seconds=1.0)

        with patch("move_mouse.actions.sleep_action.time.sleep") as mock_sleep:
            result = action.execute(mock_controller)
            mock_sleep.assert_not_called()

        assert result.error == "Acción deshabilitada"

    def test_execute_increments_count(self):
        mock_controller = MagicMock()
        action = SleepAction(duration_seconds=0.0)
        action.execute(mock_controller)
        assert action.execution_count == 1

    def test_random_duration_enabled(self):
        action = SleepAction(
            duration_seconds=1.0,
            random_duration=True,
            upper_duration_ms=3000.0,
        )
        assert action.random_duration is True
        assert action.upper_duration_ms == 3000.0

    def test_resolve_duration_random(self):
        action = SleepAction(
            duration_seconds=1.0,
            random_duration=True,
            upper_duration_ms=3000.0,
        )
        duration = action._resolve_duration()
        assert 1.0 <= duration <= 3.0

    def test_resolve_duration_fixed(self):
        action = SleepAction(duration_seconds=2.5)
        assert action._resolve_duration() == 2.5

    def test_resolve_duration_random_disabled_when_upper_not_greater(self):
        """Si upper_duration_ms <= duration_seconds, no randomiza."""
        action = SleepAction(
            duration_seconds=5.0,
            random_duration=True,
            upper_duration_ms=3000.0,  # 3s < 5s
        )
        assert action._resolve_duration() == 5.0
