"""Detector de inactividad del usuario via XScreenSaver o D-Bus."""

import logging
import threading
import time
from typing import Callable, List

logger = logging.getLogger(__name__)


class IdleDetector(threading.Thread):
    """Hilo daemon que consulta periódicamente el tiempo de inactividad."""

    def __init__(self, polling_interval_ms: int = 1000):
        super().__init__(daemon=True, name="IdleDetector")
        self._polling_interval_ms = polling_interval_ms
        self._running = False
        self._callbacks: List[Callable[[int], None]] = []
        self._primary_backend = True  # True = XScreenSaver, False = D-Bus fallback

    def add_callback(self, callback: Callable[[int], None]) -> None:
        """Registra callback(idle_ms) invocado en cada ciclo de polling."""
        self._callbacks.append(callback)

    def start(self) -> None:
        """Inicia el hilo de polling."""
        self._running = True
        super().start()

    def stop(self) -> None:
        """Solicita la detención del hilo."""
        self._running = False

    def run(self) -> None:
        """Loop principal de polling."""
        while self._running:
            try:
                idle_ms = self._get_idle_time()
                for cb in self._callbacks:
                    try:
                        cb(idle_ms)
                    except Exception:
                        logger.exception("Error en callback de idle")
            except Exception:
                logger.exception("Error consultando tiempo de inactividad")
            # Usar polling_interval_ms dividido en chunks para poder salir rápido
            esperado = self._polling_interval_ms / 1000.0
            chunk = 0.1
            transcurrido = 0.0
            while self._running and transcurrido < esperado:
                time.sleep(min(chunk, esperado - transcurrido))
                transcurrido += chunk

    def _get_idle_time(self) -> int:
        """Devuelve el tiempo de inactividad en milisegundos."""
        if self._primary_backend:
            try:
                return self._get_idle_time_xscreensaver()
            except Exception as exc:
                logger.warning("XScreenSaver falló (%s), intentando D-Bus", exc)
                self._primary_backend = False
        return self._get_idle_time_dbus()

    def _get_idle_time_xscreensaver(self) -> int:
        """Consulta via XScreenSaver extension."""
        from Xlib import display as xdisplay
        from Xlib.ext import screensaver  # noqa: F401

        dpy = xdisplay.Display()
        try:
            root = dpy.screen().root
            info = root.screensaver_query_info()
            return int(info.idle)
        finally:
            dpy.close()

    def _get_idle_time_dbus(self) -> int:
        """Consulta via D-Bus org.freedesktop.ScreenSaver."""
        import dbus

        bus = dbus.SessionBus()
        proxy = bus.get_object(
            "org.freedesktop.ScreenSaver", "/org/freedesktop/ScreenSaver"
        )
        iface = dbus.Interface(proxy, "org.freedesktop.ScreenSaver")
        return int(iface.GetSessionIdleTime())
