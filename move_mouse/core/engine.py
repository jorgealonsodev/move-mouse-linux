"""Main engine with state machine."""

import logging
import threading
from enum import Enum
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)


class EngineState(Enum):
    """Possible engine states."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    EXECUTING = "executing"
    SLEEPING = "sleeping"
    LOCKED = "locked"


class Engine:
    """Orchestrates periodic action execution with automatic pauses."""

    def __init__(
        self,
        tick_callback: Optional[Callable[[], None]] = None,
        interval_ms: int = 30000,
        timer_class: type = threading.Timer,
        use_glib: bool = False,
    ):
        self._tick_callback = tick_callback
        self._interval_ms = interval_ms
        self._timer_class = timer_class
        self._timer: Optional[threading.Timer] = None
        self._listeners: List[Callable[[EngineState, EngineState], None]] = []
        self._lock = threading.Lock()
        self._state = EngineState.IDLE
        self._use_glib = use_glib
        self._glib_source_id: Optional[int] = None

    @property
    def state(self) -> EngineState:
        """Current engine state."""
        with self._lock:
            return self._state

    def add_listener(
        self, callback: Callable[[EngineState, EngineState], None]
    ) -> None:
        """Register a callback invoked on each state change."""
        self._listeners.append(callback)

    def _notify(self, old_state: EngineState, new_state: EngineState) -> None:
        logger.info("Engine: %s -> %s", old_state.value, new_state.value)
        for listener in self._listeners:
            try:
                listener(old_state, new_state)
            except Exception:
                logger.exception("Error in state listener")

    def _transition(
        self, new_state: EngineState, expected_old: Optional[EngineState] = None
    ) -> bool:
        """Change state notifying listeners. Returns True if the change was effective."""
        with self._lock:
            if expected_old is not None and self._state != expected_old:
                return False
            old_state = self._state
            self._state = new_state
        self._notify(old_state, new_state)
        return True

    # -- Public transitions --

    def start(self) -> None:
        """Start the engine from Idle."""
        if self._transition(EngineState.RUNNING, expected_old=EngineState.IDLE):
            self._schedule_tick()

    def stop(self) -> None:
        """Stop the engine and return to Idle."""
        with self._lock:
            if self._state == EngineState.IDLE:
                return
        self._cancel_timer()
        self._transition(EngineState.IDLE)

    def pause(self) -> None:
        """Pause the engine if Running or Executing."""
        with self._lock:
            if self._state not in (EngineState.RUNNING, EngineState.EXECUTING):
                return
        self._cancel_timer()
        self._transition(EngineState.PAUSED)

    def resume(self) -> None:
        """Resume the engine if Paused."""
        if self._transition(EngineState.RUNNING, expected_old=EngineState.PAUSED):
            self._schedule_tick()

    def lock(self) -> None:
        """Lock the engine if Running."""
        with self._lock:
            if self._state != EngineState.RUNNING:
                return
        self._cancel_timer()
        self._transition(EngineState.LOCKED)

    def unlock(self) -> None:
        """Unlock the engine if Locked."""
        if self._transition(EngineState.RUNNING, expected_old=EngineState.LOCKED):
            self._schedule_tick()

    def sleep(self, duration_ms: int) -> None:
        """Put the engine in Sleeping for a duration (used by SleepAction)."""
        self._cancel_timer()
        if self._transition(EngineState.SLEEPING, expected_old=EngineState.EXECUTING):
            self._timer = self._timer_class(
                duration_ms / 1000.0, self._wake_from_sleep
            )
            self._timer.start()

    def on_executor_sleep(self, duration_ms: int = 1000) -> None:
        """Callback for Executor to put engine in Sleeping.

        This method is registered as ``on_sleep`` of the Executor when
        a SleepAction is executed.
        """
        logger.debug("Executor requested transition to Sleeping")
        # Try transitioning from EXECUTING (during tick) or RUNNING
        if self._transition(EngineState.SLEEPING, expected_old=EngineState.EXECUTING):
            self._timer = self._timer_class(
                duration_ms / 1000.0, self._wake_from_sleep
            )
            self._timer.start()
        elif self._transition(EngineState.SLEEPING, expected_old=EngineState.RUNNING):
            self._cancel_timer()
            self._timer = self._timer_class(
                duration_ms / 1000.0, self._wake_from_sleep
            )
            self._timer.start()

    def _wake_from_sleep(self) -> None:
        """Sleep timer callback."""
        if self._transition(EngineState.RUNNING, expected_old=EngineState.SLEEPING):
            self._schedule_tick()

    # -- Timer --

    def _schedule_tick(self) -> None:
        """Schedule the next tick."""
        if self._use_glib:
            self._schedule_glib_tick()
        else:
            logger.debug("Scheduling timer for tick in %.1f ms", self._interval_ms)
            self._timer = self._timer_class(self._interval_ms / 1000.0, self._tick)
            self._timer.start()

    def _schedule_glib_tick(self) -> None:
        """Schedule the next tick using GLib.timeout_add."""
        try:
            from gi.repository import GLib
        except (ImportError, RuntimeError):
            # GLib not available, fallback to threading.Timer
            logger.warning("GLib not available, using threading.Timer as fallback")
            self._use_glib = False
            self._timer = self._timer_class(self._interval_ms / 1000.0, self._tick)
            self._timer.start()
            return

        self._cancel_timer()

        def _tick_glib() -> bool:
            self._tick()
            return self.state == EngineState.RUNNING

        self._glib_source_id = GLib.timeout_add(self._interval_ms, _tick_glib)

    def _cancel_timer(self) -> None:
        """Cancel the active timer."""
        if self._use_glib and self._glib_source_id is not None:
            try:
                from gi.repository import GLib
                GLib.source_remove(self._glib_source_id)
                logger.debug("GLib timer cancelled (source_id=%s)", self._glib_source_id)
            except (ImportError, RuntimeError):
                pass
            self._glib_source_id = None
        elif self._timer is not None:
            logger.debug("Threading timer cancelled")
            self._timer.cancel()
            self._timer = None

    def _tick(self) -> None:
        """Timer callback: execute the scheduled action."""
        logger.debug("Engine tick fired")
        if not self._transition(EngineState.EXECUTING, expected_old=EngineState.RUNNING):
            return
        if self._tick_callback is not None:
            try:
                self._tick_callback()
            except Exception:
                logger.exception("Error in tick callback")
        if self._transition(EngineState.RUNNING, expected_old=EngineState.EXECUTING):
            self._schedule_tick()
