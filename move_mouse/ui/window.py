"""Ventana principal GTK de Move Mouse Linux."""

import logging
from typing import Callable, Optional

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

from move_mouse.core.engine import EngineState

logger = logging.getLogger(__name__)

# Mapeo de estados a texto en español
ESTADO_TEXTO = {
    EngineState.IDLE: "Inactivo",
    EngineState.RUNNING: "En ejecución",
    EngineState.PAUSED: "Pausado",
    EngineState.EXECUTING: "Ejecutando acción",
    EngineState.SLEEPING: "En pausa programada",
    EngineState.LOCKED: "Bloqueado (sesión bloqueada)",
}


class VentanaPrincipal(Gtk.Window):
    """Ventana principal con controles de estado y botón iniciar/detener."""

    def __init__(self, app: "Gtk.Application"):
        super().__init__(title="Move Mouse Linux")
        self._app = app
        self._motor = None

        # Callbacks
        self._on_cerrar: Optional[Callable[[], None]] = None

        # Widgets
        self._etiqueta_estado: Optional[Gtk.Label] = None
        self._etiqueta_tiempo: Optional[Gtk.Label] = None
        self._boton_toggle: Optional[Gtk.Button] = None

        self._construir_ui()
        self._conectar_senales()

    # -- Propiedades --

    @property
    def motor(self):
        return self._motor

    @motor.setter
    def motor(self, motor) -> None:
        self._motor = motor
        self._actualizar_estado(motor.state)

    @property
    def on_cerrar(self) -> Optional[Callable[[], None]]:
        return self._on_cerrar

    @on_cerrar.setter
    def on_cerrar(self, callback: Callable[[], None]) -> None:
        self._on_cerrar = callback

    # -- Construcción de UI --

    def _construir_ui(self) -> None:
        self.set_default_size(320, 180)
        self.set_border_width(12)
        self.set_resizable(False)

        # Contenedor vertical
        caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add(caja)

        # Etiqueta de estado
        self._etiqueta_estado = Gtk.Label(label="Estado: Inactivo")
        self._etiqueta_estado.set_halign(Gtk.Align.CENTER)
        caja.pack_start(self._etiqueta_estado, False, False, 0)

        # Etiqueta de próximo intervalo
        self._etiqueta_tiempo = Gtk.Label(label="Próxima acción: --")
        self._etiqueta_tiempo.set_halign(Gtk.Align.CENTER)
        caja.pack_start(self._etiqueta_tiempo, False, False, 0)

        # Botón iniciar/detener
        self._boton_toggle = Gtk.Button(label="Iniciar")
        self._boton_toggle.set_halign(Gtk.Align.CENTER)
        self._boton_toggle.set_size_request(120, -1)
        caja.pack_start(self._boton_toggle, False, False, 0)

        caja.show_all()

    def _conectar_senales(self) -> None:
        self.connect("delete-event", self._on_cerrar_ventana)
        if self._boton_toggle:
            self._boton_toggle.connect("clicked", self._on_toggle_click)

    # -- Actualización de estado --

    def actualizar_desde_hilo(self, estado: EngineState) -> None:
        """Actualiza la UI desde el hilo del motor usando GLib.idle_add."""
        GLib.idle_add(self._actualizar_estado, estado)

    def _actualizar_estado(self, estado: EngineState) -> None:
        texto = ESTADO_TEXTO.get(estado, str(estado.value))
        if self._etiqueta_estado:
            self._etiqueta_estado.set_text(f"Estado: {texto}")

        if self._boton_toggle:
            if estado == EngineState.RUNNING:
                self._boton_toggle.set_label("Detener")
            else:
                self._boton_toggle.set_label("Iniciar")

    def actualizar_tiempo(self, segundos: int) -> None:
        """Actualiza la etiqueta de tiempo restante."""
        GLib.idle_add(self._etiqueta_tiempo.set_text, f"Próxima acción: {segundos}s")

    # -- Manejadores de eventos --

    def _on_toggle_click(self, widget) -> None:
        if self._motor is None:
            return

        if self._motor.state == EngineState.RUNNING:
            self._motor.stop()
        elif self._motor.state == EngineState.IDLE:
            self._motor.start()
        elif self._motor.state == EngineState.PAUSED:
            self._motor.resume()
        elif self._motor.state == EngineState.LOCKED:
            self._motor.unlock()

    def _on_cerrar_ventana(self, widget, event) -> bool:
        """Al cerrar la ventana, ocultarla en lugar de salir."""
        self.hide()
        if self._on_cerrar:
            self._on_cerrar()
        return True  # Detener propagación del evento

    def mostrar(self) -> None:
        """Muestra la ventana y la trae al frente."""
        self.show_all()
        self.present()
