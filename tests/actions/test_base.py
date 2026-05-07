"""Tests para las clases base de acciones."""

import pytest

from move_mouse.actions.base import ActionBase, ActionResult
from move_mouse.mouse_controller import MouseController


class _ConcreteAction(ActionBase):
    """Acción concreta para probar ActionBase."""

    def execute(self, controller: MouseController) -> ActionResult:
        self._execution_count += 1
        return ActionResult()


class TestActionResult:
    def test_default_values(self):
        result = ActionResult()
        assert result.aborted is False
        assert result.error is None

    def test_with_aborted(self):
        result = ActionResult(aborted=True)
        assert result.aborted is True

    def test_with_error(self):
        result = ActionResult(error="algo falló")
        assert result.error == "algo falló"


class TestActionBase:
    def test_default_properties(self):
        action = _ConcreteAction(
            action_id="test_1",
            name="Prueba",
        )
        assert action.id == "test_1"
        assert action.name == "Prueba"
        assert action.is_enabled is True
        assert action.repeat is False
        assert action.trigger == "start"
        assert action.repeat_mode == "forever"
        assert action.interval_throttle == 0
        assert action.interval_execution_count == 1
        assert action.aborted is False
        assert action.execution_count == 0

    def test_custom_properties(self):
        action = _ConcreteAction(
            action_id="t2",
            name="Test 2",
            is_enabled=False,
            repeat=True,
            trigger="start",
            repeat_mode="throttle",
            interval_throttle=3,
            interval_execution_count=2,
        )
        assert action.id == "t2"
        assert action.is_enabled is False
        assert action.repeat is True
        assert action.trigger == "start"
        assert action.repeat_mode == "throttle"
        assert action.interval_throttle == 3
        assert action.interval_execution_count == 2

    def test_is_enabled_setter(self):
        action = _ConcreteAction(action_id="t3", name="T3")
        action.is_enabled = False
        assert action.is_enabled is False

    def test_aborted_setter(self):
        action = _ConcreteAction(action_id="t4", name="T4")
        action.aborted = True
        assert action.aborted is True

    def test_can_execute_when_enabled(self):
        action = _ConcreteAction(action_id="t5", name="T5", is_enabled=True)
        assert action.can_execute() is True

    def test_can_execute_when_disabled(self):
        action = _ConcreteAction(action_id="t6", name="T6", is_enabled=False)
        assert action.can_execute() is False

    def test_can_execute_throttle_not_reached(self):
        action = _ConcreteAction(
            action_id="t7",
            name="T7",
            repeat_mode="throttle",
            interval_throttle=3,
            interval_execution_count=2,
        )
        # Simular 1 ejecución (menos que el límite de 2)
        action._execution_count = 1
        assert action.can_execute() is True

    def test_can_execute_throttle_reached(self):
        action = _ConcreteAction(
            action_id="t8",
            name="T8",
            repeat_mode="throttle",
            interval_throttle=3,
            interval_execution_count=2,
        )
        action._execution_count = 2
        assert action.can_execute() is False

    def test_reset_cycle(self):
        action = _ConcreteAction(action_id="t9", name="T9")
        action._execution_count = 5
        action.reset_cycle()
        assert action.execution_count == 0

    def test_repr(self):
        action = _ConcreteAction(action_id="t10", name="Test", is_enabled=True)
        repr_str = repr(action)
        assert "ConcreteAction" in repr_str
        assert "t10" in repr_str

    def test_execute_increments_count(self):
        action = _ConcreteAction(action_id="t11", name="T11")
        ctrl = MouseController()
        action.execute(ctrl)
        assert action.execution_count == 1
