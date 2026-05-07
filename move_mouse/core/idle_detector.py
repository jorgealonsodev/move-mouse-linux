"""User idle detector via XScreenSaver or D-Bus."""

import logging
import threading
import time
from typing import Callable, List

logger = logging.getLogger(__name__)


class IdleDetector(threading.Thread):
    """Daemon thread that periodically queries idle time."""

    def __init__(self, polling_interval_ms: int = 1000):
        super().__init__(daemon=True, name="IdleDetector")
        self._polling_interval_ms = polling_interval_ms
        self._running = False
        self._callbacks: List[Callable[[int], None]] = []
        self._primary_backend = True  # True = XScreenSaver, False = D-Bus fallback
        self._last_debug_log = 0.0  # For throttling DEBUG logs every 5 seconds
        self._xdisplay = None  # Cached X display connection
        self._dbus_iface = None  # Cached D-Bus interface

    def add_callback(self, callback: Callable[[int], None]) -> None:
        """Register callback(idle_ms) invoked on each polling cycle."""
        self._callbacks.append(callback)

    def start(self) -> None:
        """Start the polling thread."""
        self._running = True
        super().start()

    def stop(self) -> None:
        """Request thread termination."""
        self._running = False
        if self._xdisplay is not None:
            try:
                self._xdisplay.close()
            except Exception:
                pass
            self._xdisplay = None

    def run(self) -> None:
        """Main polling loop."""
        while self._running:
            try:
                idle_ms = self._get_idle_time()
                # Log throttled: only every 5 seconds
                now = time.time()
                if now - self._last_debug_log >= 5.0:
                    logger.debug("IdleDetector: idle time=%d ms", idle_ms)
                    self._last_debug_log = now
                for cb in self._callbacks:
                    try:
                        cb(idle_ms)
                    except Exception:
                        logger.exception("Error in idle callback")
            except Exception:
                logger.exception("Error querying idle time")
            # Use polling_interval_ms divided into chunks for fast exit
            expected = self._polling_interval_ms / 1000.0
            chunk = 0.1
            elapsed = 0.0
            while self._running and elapsed < expected:
                time.sleep(min(chunk, expected - elapsed))
                elapsed += chunk

    def _get_idle_time(self) -> int:
        """Return idle time in milliseconds."""
        if self._primary_backend:
            try:
                return self._get_idle_time_xscreensaver()
            except Exception as exc:
                logger.warning(
                    "XScreenSaver failed (%s), switching to D-Bus backend", exc
                )
                self._primary_backend = False
        return self._get_idle_time_dbus()

    def _get_idle_time_xscreensaver(self) -> int:
        """Query via XScreenSaver extension."""
        from Xlib import display as xdisplay
        from Xlib.ext import screensaver  # noqa: F401

        try:
            if self._xdisplay is None:
                self._xdisplay = xdisplay.Display()
            dpy = self._xdisplay
            root = dpy.screen().root
            info = root.screensaver_query_info()
            return int(info.idle)
        except Exception:
            self._xdisplay = None
            raise

    def _get_idle_time_dbus(self) -> int:
        """Query via D-Bus org.freedesktop.ScreenSaver."""
        import dbus

        try:
            if self._dbus_iface is None:
                bus = dbus.SessionBus()
                proxy = bus.get_object(
                    "org.freedesktop.ScreenSaver", "/org/freedesktop/ScreenSaver"
                )
                self._dbus_iface = dbus.Interface(
                    proxy, "org.freedesktop.ScreenSaver"
                )
            return int(self._dbus_iface.GetSessionIdleTime())
        except Exception:
            self._dbus_iface = None
            raise
