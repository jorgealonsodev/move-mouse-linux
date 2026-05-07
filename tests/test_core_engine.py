"""Tests para el motor (state machine)."""

from unittest.mock import MagicMock

import pytest

from move_mouse.core.engine import Engine, EngineState


class FakeTimer:
    """Timer de prueba que no dispara automáticamente."""

    def __init__(self, interval, function, args=None, kwargs=None):
        self.interval = interval
        self.function = function
        self.args = args or []
        self.kwargs = kwargs or {}
        self._started = False
        self._cancelled = False

    def start(self):
        self._started = True

    def cancel(self):
        self._cancelled = True

    def fire(self):
        if not self._cancelled:
            self.function(*self.args, **self.kwargs)


class TestEngine:
    def test_initial_state(self):
        engine = Engine()
        assert engine.state == EngineState.IDLE

    def test_start_transitions_to_running(self):
        engine = Engine(timer_class=FakeTimer)
        engine.start()
        assert engine.state == EngineState.RUNNING

    def test_stop_from_running_to_idle(self):
        engine = Engine(timer_class=FakeTimer)
        engine.start()
        engine.stop()
        assert engine.state == EngineState.IDLE

    def test_stop_from_idle_is_noop(self):
        engine = Engine(timer_class=FakeTimer)
        engine.stop()
        assert engine.state == EngineState.IDLE

    def test_pause_from_running(self):
        engine = Engine(timer_class=FakeTimer)
        engine.start()
        engine.pause()
        assert engine.state == EngineState.PAUSED

    def test_pause_from_idle_is_noop(self):
        engine = Engine(timer_class=FakeTimer)
        engine.pause()
        assert engine.state == EngineState.IDLE

    def test_resume_from_paused(self):
        engine = Engine(timer_class=FakeTimer)
        engine.start()
        engine.pause()
        engine.resume()
        assert engine.state == EngineState.RUNNING

    def test_resume_from_running_is_noop(self):
        engine = Engine(timer_class=FakeTimer)
        engine.start()
        engine.resume()
        assert engine.state == EngineState.RUNNING

    def test_lock_from_running(self):
        engine = Engine(timer_class=FakeTimer)
        engine.start()
        engine.lock()
        assert engine.state == EngineState.LOCKED

    def test_unlock_from_locked(self):
        engine = Engine(timer_class=FakeTimer)
        engine.start()
        engine.lock()
        engine.unlock()
        assert engine.state == EngineState.RUNNING

    def test_listener_called_on_transition(self):
        engine = Engine(timer_class=FakeTimer)
        listener = MagicMock()
        engine.add_listener(listener)
        engine.start()
        listener.assert_called_once_with(EngineState.IDLE, EngineState.RUNNING)

    def test_tick_transitions_to_executing_and_back(self):
        engine = Engine(timer_class=FakeTimer)
        engine.start()
        timer = engine._timer
        assert isinstance(timer, FakeTimer)
        timer.fire()
        assert engine.state == EngineState.RUNNING

    def test_tick_callback_invoked(self):
        callback = MagicMock()
        engine = Engine(tick_callback=callback, timer_class=FakeTimer)
        engine.start()
        engine._timer.fire()  # type: ignore
        callback.assert_called_once()

    def test_pause_during_tick_prevents_next_schedule(self):
        engine = Engine(timer_class=FakeTimer)
        engine.start()

        def pausing_callback():
            engine.pause()

        engine._tick_callback = pausing_callback
        engine._timer.fire()  # type: ignore
        assert engine.state == EngineState.PAUSED

    def test_sleep_transitions(self):
        engine = Engine(timer_class=FakeTimer)
        engine.start()
        engine._transition(EngineState.EXECUTING)
        engine.sleep(100)
        assert engine.state == EngineState.SLEEPING
        engine._timer.fire()  # type: ignore
        assert engine.state == EngineState.RUNNING

    def test_stop_cancels_timer(self):
        engine = Engine(timer_class=FakeTimer)
        engine.start()
        timer = engine._timer
        engine.stop()
        assert timer._cancelled is True  # type: ignore

    def test_invalid_start_from_running_is_ignored(self):
        engine = Engine(timer_class=FakeTimer)
        engine.start()
        engine.start()
        assert engine.state == EngineState.RUNNING

    def test_tick_exception_logged(self, caplog):
        callback = MagicMock(side_effect=RuntimeError("boom"))
        engine = Engine(tick_callback=callback, timer_class=FakeTimer)
        engine.start()
        engine._timer.fire()  # type: ignore
        assert "boom" in caplog.text
        assert engine.state == EngineState.RUNNING
