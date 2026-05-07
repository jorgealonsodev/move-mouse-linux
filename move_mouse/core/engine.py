"""Motor principal con máquina de estados."""

import logging
import threading
from enum import Enum
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)


class EngineState(Enum):
    """Estados posibles del motor."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    EXECUTING = "executing"
    SLEEPING = "sleeping"
    LOCKED = "locked"


class Engine:
    """Orquesta la ejecución periódica de acciones con pausas automáticas."""

    def __init__(
        self,
        tick_callback: Optional[Callable[[], None]] = None,
        interval_ms: int = 30000,
        timer_class: type = threading.Timer,
    ):
        self._tick_callback = tick_callback
        self._interval_ms = interval_ms
        self._timer_class = timer_class
        self._timer: Optional[threading.Timer] = None
        self._listeners: List[Callable[[EngineState, EngineState], None]] = []
        self._lock = threading.Lock()
        self._state = EngineState.IDLE

    @property
    def state(self) -> EngineState:
        """Estado actual del motor."""
        with self._lock:
            return self._state

    def add_listener(
        self, callback: Callable[[EngineState, EngineState], None]
    ) -> None:
        """Registra un callback que se invoca en cada cambio de estado."""
        self._listeners.append(callback)

    def _notify(self, old_state: EngineState, new_state: EngineState) -> None:
        logger.debug("Transición: %s → %s", old_state.value, new_state.value)
        for listener in self._listeners:
            try:
                listener(old_state, new_state)
            except Exception:
                logger.exception("Error en listener de estado")

    def _transition(
        self, new_state: EngineState, expected_old: Optional[EngineState] = None
    ) -> bool:
        """Cambia el estado notificando listeners. Retorna True si el cambio fue efectivo."""
        with self._lock:
            if expected_old is not None and self._state != expected_old:
                return False
            old_state = self._state
            self._state = new_state
        self._notify(old_state, new_state)
        return True

    # -- Transiciones públicas --

    def start(self) -> None:
        """Arranca el motor desde Idle."""
        if self._transition(EngineState.RUNNING, expected_old=EngineState.IDLE):
            self._schedule_tick()

    def stop(self) -> None:
        """Detiene el motor y vuelve a Idle."""
        with self._lock:
            if self._state == EngineState.IDLE:
                return
        self._cancel_timer()
        self._transition(EngineState.IDLE)

    def pause(self) -> None:
        """Pausa el motor si está Running o Executing."""
        with self._lock:
            if self._state not in (EngineState.RUNNING, EngineState.EXECUTING):
                return
        self._cancel_timer()
        self._transition(EngineState.PAUSED)

    def resume(self) -> None:
        """Reanuda el motor si está Paused."""
        if self._transition(EngineState.RUNNING, expected_old=EngineState.PAUSED):
            self._schedule_tick()

    def lock(self) -> None:
        """Bloquea el motor si está Running."""
        with self._lock:
            if self._state != EngineState.RUNNING:
                return
        self._cancel_timer()
        self._transition(EngineState.LOCKED)

    def unlock(self) -> None:
        """Desbloquea el motor si está Locked."""
        if self._transition(EngineState.RUNNING, expected_old=EngineState.LOCKED):
            self._schedule_tick()

    def sleep(self, duration_ms: int) -> None:
        """Pone el motor en Sleeping durante un tiempo (usado por SleepAction)."""
        if self._transition(EngineState.SLEEPING, expected_old=EngineState.EXECUTING):
            self._timer = self._timer_class(
                duration_ms / 1000.0, self._wake_from_sleep
            )
            self._timer.start()

    def _wake_from_sleep(self) -> None:
        """Callback del timer de sleep."""
        if self._transition(EngineState.RUNNING, expected_old=EngineState.SLEEPING):
            self._schedule_tick()

    # -- Temporizador --

    def _schedule_tick(self) -> None:
        """Programa el próximo tick."""
        self._timer = self._timer_class(self._interval_ms / 1000.0, self._tick)
        self._timer.start()

    def _cancel_timer(self) -> None:
        """Cancela el timer activo."""
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def _tick(self) -> None:
        """Callback del timer: ejecuta la acción programada."""
        if not self._transition(EngineState.EXECUTING, expected_old=EngineState.RUNNING):
            return
        if self._tick_callback is not None:
            try:
                self._tick_callback()
            except Exception:
                logger.exception("Error en tick callback")
        if self._transition(EngineState.RUNNING, expected_old=EngineState.EXECUTING):
            self._schedule_tick()
