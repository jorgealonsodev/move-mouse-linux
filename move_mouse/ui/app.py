"""Aplicación GTK principal de Move Mouse Linux."""

import logging
from typing import Optional

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

from move_mouse.core.engine import Engine, EngineState
from move_mouse.models.settings import Settings
from move_mouse.services.session_monitor import SessionMonitor
from move_mouse.ui.tray import BandejaSistema
from move_mouse.ui.window import VentanaPrincipal

logger = logging.getLogger(__name__)


class MoveMouseApp(Gtk.Application):
    """Aplicación GTK con bandeja de sistema y control del motor.

    Coordina la ventana principal, la bandeja del sistema, el motor
    de acciones y el monitor de sesión.
    """

    def __init__(self):
        super().__init__(
            application_id="org.movemouse.MoveMouse",
            flags=Gtk.ApplicationFlags.FLAGS_NONE,
        )
        self._motor: Optional[Engine] = None
        self._config: Optional[Settings] = None
        self._monitor_sesion: Optional[SessionMonitor] = None
        self._ventana: Optional[VentanaPrincipal] = None
        self._bandeja: Optional[BandejaSistema] = None
        self._intervalo_ms: int = 30000
        self._timer_ui: Optional[int] = None

    # -- Ciclo de vida de Gtk.Application --

    def do_startup(self) -> None:
        Gtk.Application.do_startup(self)
        logger.debug("Inicializando MoveMouseApp")

        # Cargar configuración
        self._config = Settings()
        self._intervalo_ms = self._config.interval_lower_ms

        # Crear motor
        self._motor = Engine(
            tick_callback=self._on_tick_motor,
            interval_ms=self._intervalo_ms,
        )
        self._motor.add_listener(self._on_cambio_estado)

        # Crear bandeja
        self._bandeja = BandejaSistema(
            app_id=self.props.application_id,
            titulo="Move Mouse Linux",
        )
        self._conectar_bandeja()

        # Crear monitor de sesión
        self._monitor_sesion = SessionMonitor()
        self._conectar_monitor_sesion()

    def do_activate(self) -> None:
        Gtk.Application.do_activate(self)
        logger.debug("Aplicación activada")

        if self._ventana is None:
            self._ventana = VentanaPrincipal(self)
            self._ventana.motor = self._motor
            self._ventana.on_cerrar = self._on_ventana_oculta
            self.add_window(self._ventana)

        self._ventana.mostrar()

    def do_shutdown(self) -> None:
        Gtk.Application.do_shutdown(self)
        logger.info("Aplicación cerrándose")
        self._detener_todo()

    # -- Conexiones de eventos --

    def _conectar_bandeja(self) -> None:
        if self._bandeja is None:
            return
        self._bandeja.on_iniciar = self._bandeja_iniciar
        self._bandeja.on_detener = self._bandeja_detener
        self._bandeja.on_mostrar_ventana = self._bandeja_mostrar_ventana
        self._bandeja.on_acerca_de = self._bandeja_acerca_de
        self._bandeja.on_salir = self._bandeja_salir

    def _conectar_monitor_sesion(self) -> None:
        if self._monitor_sesion is None:
            return
        self._monitor_sesion.on_lock(self._motor_bloquear)
        self._monitor_sesion.on_unlock(self._motor_desbloquear)
        self._monitor_sesion.on_suspend(self._motor_detener)
        self._monitor_sesion.on_resume(self._motor_reanudar)

    # -- Acciones de la bandeja --

    def _bandeja_iniciar(self) -> None:
        if self._motor and self._motor.state == EngineState.IDLE:
            self._motor.start()
            self._iniciar_timer_ui()

    def _bandeja_detener(self) -> None:
        if self._motor:
            self._motor.stop()
            self._detener_timer_ui()

    def _bandeja_mostrar_ventana(self) -> None:
        self.activate()

    def _bandeja_acerca_de(self) -> None:
        dialogo = Gtk.AboutDialog(
            transient_for=self._ventana,
            modal=True,
            program_name="Move Mouse Linux",
            version="1.0.0",
            comments="Simula actividad de usuario para prevenir bloqueo de sesión.",
            license_type=Gtk.License.MIT,
        )
        dialogo.run()
        dialogo.destroy()

    def _bandeja_salir(self) -> None:
        self._detener_todo()
        self.quit()

    # -- Callbacks del motor --

    def _on_tick_motor(self) -> None:
        """Callback ejecutado en cada tick del motor."""
        logger.debug("Tick del motor ejecutado")
        # Reiniciar el timer de UI
        self._iniciar_timer_ui()

    def _on_cambio_estado(
        self, estado_anterior: EngineState, estado_nuevo: EngineState
    ) -> None:
        """Notificación de cambio de estado del motor."""
        logger.debug("Motor: %s → %s", estado_anterior.value, estado_nuevo.value)

        # Actualizar bandeja
        if self._bandeja:
            self._bandeja.actualizar_estado(estado_nuevo == EngineState.RUNNING)

        # Actualizar ventana
        if self._ventana:
            self._ventana.actualizar_desde_hilo(estado_nuevo)

        if estado_nuevo == EngineState.RUNNING:
            self._iniciar_timer_ui()
        else:
            self._detener_timer_ui()

    # -- Monitor de sesión --

    def _motor_bloquear(self) -> None:
        if self._motor:
            self._motor.lock()

    def _motor_desbloquear(self) -> None:
        if self._motor:
            self._motor.unlock()

    def _motor_detener(self) -> None:
        if self._motor:
            self._motor.stop()

    def _motor_reanudar(self) -> None:
        if self._motor and self._config and self._config.auto_resume_enabled:
            self._motor.start()

    # -- Timer de UI --

    def _iniciar_timer_ui(self) -> None:
        """Inicia un timer GLib que actualiza el contador en la ventana."""
        self._detener_timer_ui()
        self._tiempo_restante_ms = self._intervalo_ms

        def _actualizar() -> bool:
            self._tiempo_restante_ms -= 1000
            if self._tiempo_restante_ms <= 0:
                self._detener_timer_ui()
                return False
            if self._ventana:
                self._ventana.actualizar_tiempo(self._tiempo_restante_ms // 1000)
            return True

        self._timer_ui = GLib.timeout_add(1000, _actualizar)

    def _detener_timer_ui(self) -> None:
        if self._timer_ui is not None:
            GLib.source_remove(self._timer_ui)
            self._timer_ui = None
        if self._ventana:
            self._ventana.actualizar_tiempo(0)

    # -- Ventana --

    def _on_ventana_oculta(self) -> None:
        logger.debug("Ventana ocultada, aplicación sigue en bandeja")

    # -- Limpieza --

    def _detener_todo(self) -> None:
        if self._motor:
            self._motor.stop()
        self._detener_timer_ui()
        if self._monitor_sesion:
            self._monitor_sesion.stop()
