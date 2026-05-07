"""Tests para la ventana principal GTK."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from move_mouse.core.engine import EngineState


def _mock_gi_modules():
    """Configura mocks para gi y gi.repository en sys.modules."""
    mock_gi = MagicMock()
    mock_gtk = MagicMock()
    mock_glib = MagicMock()

    mock_repo = MagicMock()
    mock_repo.Gtk = mock_gtk
    mock_repo.GLib = mock_glib

    mock_gi.repository = mock_repo

    sys.modules["gi"] = mock_gi
    sys.modules["gi.repository"] = mock_repo
    return mock_gtk, mock_glib


def _limpiar_modulos():
    """Limpia los módulos cacheados para permitir reimport."""
    for mod in list(sys.modules.keys()):
        if mod.startswith("move_mouse.ui"):
            del sys.modules[mod]


class TestVentanaPrincipal:
    """Tests para VentanaPrincipal con mocks de GTK."""

    def setup_method(self):
        _limpiar_modulos()

    def teardown_method(self):
        _limpiar_modulos()
        for mod in ["gi", "gi.repository"]:
            sys.modules.pop(mod, None)

    def _crear_ventana(self):
        """Crea una ventana con mocks de GTK."""
        mock_gtk, mock_glib = _mock_gi_modules()

        # Configurar widgets GTK
        mock_box = MagicMock()
        mock_gtk.Box.return_value = mock_box
        mock_gtk.Orientation.VERTICAL = 0
        mock_gtk.Align.CENTER = 0

        mock_etiqueta_estado = MagicMock()
        mock_etiqueta_tiempo = MagicMock()
        mock_boton = MagicMock()

        # Gtk.Label crea diferentes mocks según el contexto
        mock_gtk.Label.side_effect = [mock_etiqueta_estado, mock_etiqueta_tiempo]
        mock_gtk.Button.return_value = mock_boton

        # Crear una clase base mock para Gtk.Window
        class MockWindow:
            def __init__(self, **kwargs):
                self._title = kwargs.get("title", "")
                self._windows = []

            def set_default_size(self, w, h):
                pass

            def set_border_width(self, w):
                pass

            def set_resizable(self, r):
                pass

            def add(self, widget):
                pass

            def connect(self, signal, handler):
                pass

            def hide(self):
                pass

            def show_all(self):
                pass

            def present(self):
                pass

        mock_gtk.Window = MockWindow

        from move_mouse.ui.window import VentanaPrincipal

        app_mock = MagicMock()
        ventana = VentanaPrincipal(app_mock)
        return ventana, mock_gtk, mock_glib

    def test_creacion_ventana(self):
        """La ventana se crea correctamente."""
        ventana, mock_gtk, mock_glib = self._crear_ventana()
        assert ventana is not None
        mock_gtk.Box.assert_called_once()

    def test_actualizar_estado_ejecuta_en_idle(self):
        """actualizar_desde_hilo usa GLib.idle_add."""
        ventana, mock_gtk, mock_glib = self._crear_ventana()

        ventana.actualizar_desde_hilo(EngineState.RUNNING)

        mock_glib.idle_add.assert_called_once()

    def test_actualizar_estado_cambia_texto(self):
        """_actualizar_estado cambia el texto de la etiqueta correctamente."""
        ventana, mock_gtk, mock_glib = self._crear_ventana()
        mock_etiqueta = MagicMock()
        ventana._etiqueta_estado = mock_etiqueta
        ventana._boton_toggle = MagicMock()

        ventana._actualizar_estado(EngineState.RUNNING)

        mock_etiqueta.set_text.assert_called_with("Estado: En ejecución")

    def test_actualizar_estado_idle(self):
        """Estado IDLE muestra texto correcto."""
        ventana, mock_gtk, mock_glib = self._crear_ventana()
        mock_etiqueta = MagicMock()
        ventana._etiqueta_estado = mock_etiqueta
        ventana._boton_toggle = MagicMock()

        ventana._actualizar_estado(EngineState.IDLE)

        mock_etiqueta.set_text.assert_called_with("Estado: Inactivo")

    def test_actualizar_estado_locked(self):
        """Estado LOCKED muestra texto correcto."""
        ventana, mock_gtk, mock_glib = self._crear_ventana()
        mock_etiqueta = MagicMock()
        ventana._etiqueta_estado = mock_etiqueta
        ventana._boton_toggle = MagicMock()

        ventana._actualizar_estado(EngineState.LOCKED)

        mock_etiqueta.set_text.assert_called_with(
            "Estado: Bloqueado (sesión bloqueada)"
        )

    def test_boton_toggle_inicia_motor(self):
        """Al hacer clic en el botón con motor IDLE, inicia el motor."""
        ventana, mock_gtk, mock_glib = self._crear_ventana()
        motor_mock = MagicMock()
        motor_mock.state = EngineState.IDLE
        ventana._motor = motor_mock

        ventana._on_toggle_click(None)

        motor_mock.start.assert_called_once()

    def test_boton_toggle_detiene_motor(self):
        """Al hacer clic en el botón con motor RUNNING, detiene el motor."""
        ventana, mock_gtk, mock_glib = self._crear_ventana()
        motor_mock = MagicMock()
        motor_mock.state = EngineState.RUNNING
        ventana._motor = motor_mock

        ventana._on_toggle_click(None)

        motor_mock.stop.assert_called_once()

    def test_cerrar_ventana_la_oculta(self):
        """Al cerrar la ventana, se oculta en lugar de salir."""
        ventana, mock_gtk, mock_glib = self._crear_ventana()
        ventana.hide = MagicMock()

        resultado = ventana._on_cerrar_ventana(None, None)

        ventana.hide.assert_called_once()
        assert resultado is True

    def test_callback_cerrar_se_ejecuta(self):
        """El callback on_cerrar se ejecuta al cerrar la ventana."""
        ventana, mock_gtk, mock_glib = self._crear_ventana()
        ventana.hide = MagicMock()
        callback = MagicMock()
        ventana.on_cerrar = callback

        ventana._on_cerrar_ventana(None, None)

        callback.assert_called_once()

    def test_actualizar_tiempo(self):
        """actualizar_tiempo actualiza la etiqueta de tiempo."""
        ventana, mock_gtk, mock_glib = self._crear_ventana()
        ventana._etiqueta_tiempo = MagicMock()

        ventana.actualizar_tiempo(25)

        mock_glib.idle_add.assert_called_once()

    def test_motor_setter_actualiza_estado(self):
        """Al asignar el motor, se actualiza el estado de la ventana."""
        ventana, mock_gtk, mock_glib = self._crear_ventana()
        mock_etiqueta = MagicMock()
        ventana._etiqueta_estado = mock_etiqueta
        ventana._boton_toggle = MagicMock()

        motor_mock = MagicMock()
        motor_mock.state = EngineState.PAUSED
        ventana.motor = motor_mock

        assert ventana.motor is motor_mock
        mock_etiqueta.set_text.assert_called_with("Estado: Pausado")
