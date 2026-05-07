"""System session monitor via D-Bus (logind)."""

import logging
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)


class SessionMonitor:
    """Listens to session lock/unlock and suspend/resume signals."""

    def __init__(self):
        self._callbacks: dict[str, List[Callable[[], None]]] = {
            "lock": [],
            "unlock": [],
            "suspend": [],
            "resume": [],
        }
        self._bus: Optional = None
        self._running = False

    def on_lock(self, callback: Callable[[], None]) -> None:
        """Register callback for session lock."""
        self._callbacks["lock"].append(callback)

    def on_unlock(self, callback: Callable[[], None]) -> None:
        """Register callback for session unlock."""
        self._callbacks["unlock"].append(callback)

    def on_suspend(self, callback: Callable[[], None]) -> None:
        """Register callback for system suspend."""
        self._callbacks["suspend"].append(callback)

    def on_resume(self, callback: Callable[[], None]) -> None:
        """Register callback for system resume."""
        self._callbacks["resume"].append(callback)

    def _emit(self, event: str) -> None:
        logger.info("Session event: %s", event)
        for cb in self._callbacks[event]:
            try:
                cb()
            except Exception:
                logger.exception("Error in session callback (%s)", event)

    def start(self) -> None:
        """Start listening to D-Bus signals."""
        try:
            import dbus
            from dbus.mainloop.glib import DBusGMainLoop

            DBusGMainLoop(set_as_default=True)
            self._bus = dbus.SystemBus()
            self._bus.add_signal_receiver(
                self._on_lock,
                signal_name="Lock",
                dbus_interface="org.freedesktop.login1.Session",
            )
            self._bus.add_signal_receiver(
                self._on_unlock,
                signal_name="Unlock",
                dbus_interface="org.freedesktop.login1.Session",
            )
            self._bus.add_signal_receiver(
                self._on_prepare_for_sleep,
                signal_name="PrepareForSleep",
                dbus_interface="org.freedesktop.login1.Manager",
            )
            self._running = True
            logger.info("SessionMonitor started")
        except Exception as exc:
            logger.warning("Could not start SessionMonitor: %s", exc)

    def stop(self) -> None:
        """Stop listening to signals."""
        self._running = False
        if self._bus is not None:
            try:
                self._bus.close()
            except Exception:
                pass
            self._bus = None

    def _on_lock(self, *args) -> None:
        self._emit("lock")

    def _on_unlock(self, *args) -> None:
        self._emit("unlock")

    def _on_prepare_for_sleep(self, going_to_sleep: bool) -> None:
        if going_to_sleep:
            self._emit("suspend")
        else:
            self._emit("resume")
