"""Tests para el Executor de acciones."""

from unittest.mock import MagicMock

import pytest

from move_mouse.actions.base import ActionBase, ActionResult
from move_mouse.core.executor import Executor
from move_mouse.mouse_controller import MouseController


class _FakeAction(ActionBase):
    """Acción falsa para tests del executor."""

    def __init__(self, action_id="fake", name="Fake", trigger="interval",
                 is_enabled=True, abort_on_execute=False, raise_on_execute=False,
                 repeat_mode="forever", interval_throttle=0,
                 interval_execution_count=1):
        super().__init__(action_id=action_id, name=name, trigger=trigger,
                         is_enabled=is_enabled, repeat_mode=repeat_mode,
                         interval_throttle=interval_throttle,
                         interval_execution_count=interval_execution_count)
        self._abort_on_execute = abort_on_execute
        self._raise_on_execute = raise_on_execute

    def execute(self, controller: MouseController) -> ActionResult:
        if self._raise_on_execute:
            raise RuntimeError("error simulado")
        if self._abort_on_execute:
            self._aborted = True
            return ActionResult(aborted=True)
        self._execution_count += 1
        return ActionResult()


class TestExecutor:
    def test_default_properties(self):
        executor = Executor(actions=[])
        assert executor.actions == []
        assert executor.trigger == "interval"
        assert executor.controller is None

    def test_controller_setter(self):
        mock_ctrl = MagicMock()
        executor = Executor(actions=[])
        executor.controller = mock_ctrl
        assert executor.controller is mock_ctrl

    def test_execute_single_action(self):
        action = _FakeAction(action_id="a1")
        mock_ctrl = MagicMock()
        executor = Executor(actions=[action], controller=mock_ctrl)

        aborted = executor.execute()

        assert aborted is False
        assert action.execution_count == 1

    def test_execute_multiple_actions(self):
        actions = [
            _FakeAction(action_id="a1"),
            _FakeAction(action_id="a2"),
            _FakeAction(action_id="a3"),
        ]
        mock_ctrl = MagicMock()
        executor = Executor(actions=actions, controller=mock_ctrl)

        aborted = executor.execute()

        assert aborted is False
        for a in actions:
            assert a.execution_count == 1

    def test_execute_filters_by_trigger(self):
        interval_action = _FakeAction(action_id="a1", trigger="interval")
        start_action = _FakeAction(action_id="a2", trigger="start")
        mock_ctrl = MagicMock()
        executor = Executor(actions=[interval_action, start_action],
                            trigger="interval", controller=mock_ctrl)

        executor.execute()

        assert interval_action.execution_count == 1
        assert start_action.execution_count == 0

    def test_execute_skips_disabled_actions(self):
        enabled = _FakeAction(action_id="a1", is_enabled=True)
        disabled = _FakeAction(action_id="a2", is_enabled=False)
        mock_ctrl = MagicMock()
        executor = Executor(actions=[enabled, disabled], controller=mock_ctrl)

        executor.execute()

        assert enabled.execution_count == 1
        assert disabled.execution_count == 0

    def test_execute_skips_cannot_execute(self):
        action = _FakeAction(
            action_id="a1",
            repeat_mode="throttle",
            interval_throttle=1,
            interval_execution_count=1,
        )
        action._execution_count = 1  # Ya alcanzó el límite
        mock_ctrl = MagicMock()
        executor = Executor(actions=[action], controller=mock_ctrl)

        executor.execute()

        assert action.execution_count == 1  # No se incrementó

    def test_execute_aborted_stops_pipeline(self):
        a1 = _FakeAction(action_id="a1")
        a2 = _FakeAction(action_id="a2", abort_on_execute=True)
        a3 = _FakeAction(action_id="a3")
        mock_ctrl = MagicMock()
        executor = Executor(actions=[a1, a2, a3], controller=mock_ctrl)

        aborted = executor.execute()

        assert aborted is True
        assert a1.execution_count == 1
        assert a2.execution_count == 0  # abort_on_execute no incrementa
        assert a3.execution_count == 0  # No se ejecutó
        assert a3.aborted is True  # Marcada como abortada

    def test_execute_no_controller_returns_false(self):
        action = _FakeAction(action_id="a1")
        executor = Executor(actions=[action])

        aborted = executor.execute()

        assert aborted is False

    def test_execute_with_controller_param(self):
        action = _FakeAction(action_id="a1")
        mock_ctrl = MagicMock()
        executor = Executor(actions=[action])

        executor.execute(controller=mock_ctrl)

        assert action.execution_count == 1

    def test_execute_error_does_not_stop_pipeline(self):
        a1 = _FakeAction(action_id="a1", raise_on_execute=True)
        a2 = _FakeAction(action_id="a2")
        mock_ctrl = MagicMock()
        executor = Executor(actions=[a1, a2], controller=mock_ctrl)

        aborted = executor.execute()

        assert aborted is False
        assert a2.execution_count == 1  # a2 se ejecuta aunque a1 falló

    def test_reset_all_cycles(self):
        actions = [
            _FakeAction(action_id="a1"),
            _FakeAction(action_id="a2"),
        ]
        for a in actions:
            a._execution_count = 5

        executor = Executor(actions=actions)
        executor.reset_all_cycles()

        for a in actions:
            assert a.execution_count == 0

    def test_get_actions_for_trigger(self):
        a1 = _FakeAction(action_id="a1", trigger="interval")
        a2 = _FakeAction(action_id="a2", trigger="start")
        a3 = _FakeAction(action_id="a3", trigger="interval")
        executor = Executor(actions=[a1, a2, a3])

        interval_actions = executor.get_actions_for_trigger("interval")

        assert len(interval_actions) == 2
        assert a1 in interval_actions
        assert a3 in interval_actions
        assert a2 not in interval_actions

    def test_on_sleep_callback_invoked_for_sleep_action(self):
        """El callback on_sleep se invoca cuando una acción marca puts_engine_to_sleep."""
        from move_mouse.actions.sleep_action import SleepAction

        action = SleepAction(duration_seconds=0.0)
        mock_ctrl = MagicMock()
        on_sleep = MagicMock()
        executor = Executor(actions=[action], controller=mock_ctrl, on_sleep=on_sleep)

        executor.execute()

        on_sleep.assert_called_once()

    def test_on_sleep_callback_not_invoked_for_regular_action(self):
        """El callback on_sleep NO se invoca para acciones normales."""
        action = _FakeAction(action_id="a1")
        mock_ctrl = MagicMock()
        on_sleep = MagicMock()
        executor = Executor(actions=[action], controller=mock_ctrl, on_sleep=on_sleep)

        executor.execute()

        on_sleep.assert_not_called()

    def test_on_sleep_defaults_to_none(self):
        """El parámetro on_sleep por defecto es None."""
        executor = Executor(actions=[])
        assert executor._on_sleep is None
