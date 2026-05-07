"""Tests para la aplicación GTK principal."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from move_mouse.core.engine import EngineState


def _limpiar_modulos():
    """Limpia los módulos cacheados para permitir reimport."""
    for mod in list(sys.modules.keys()):
        if mod.startswith("move_mouse.ui"):
            del sys.modules[mod]


class MockApplication:
    """Mock de Gtk.Application para tests."""

    def __init__(self, application_id=None, flags=None):
        self._application_id = application_id
        self._flags = flags
        self._windows = []

    @property
    def props(self):
        p = MagicMock()
        p.application_id = self._application_id
        return p

    def do_startup(self):
        pass

    def do_activate(self):
        pass

    def do_shutdown(self):
        pass

    def add_window(self, win):
        self._windows.append(win)

    def quit(self):
        pass


class TestMoveMouseApp:
    """Tests para MoveMouseApp con mocks de GTK."""

    def setup_method(self):
        _limpiar_modulos()

    def teardown_method(self):
        _limpiar_modulos()
        for mod in ["gi", "gi.repository"]:
            sys.modules.pop(mod, None)

    def _crear_app(self):
        """Crea MoveMouseApp con todos los mocks necesarios y llama do_startup."""
        # Crear mocks
        mock_glib = MagicMock()

        # Configurar gi modules con MockApplication
        mock_gi = MagicMock()
        mock_gtk = MagicMock()
        mock_gtk.Application = MockApplication
        mock_gtk.ApplicationFlags = MagicMock()
        mock_gtk.ApplicationFlags.FLAGS_NONE = 0

        mock_repo = MagicMock()
        mock_repo.Gtk = mock_gtk
        mock_repo.GLib = mock_glib

        mock_gi.require_version = MagicMock()
        mock_gi.repository = mock_repo

        sys.modules["gi"] = mock_gi
        sys.modules["gi.repository"] = mock_repo

        # Mock de dependencias
        mock_settings = MagicMock()
        mock_settings.return_value.interval_lower_ms = 30000

        mock_bandeja_cls = MagicMock()
        mock_bandeja_inst = MagicMock()
        mock_bandeja_cls.return_value = mock_bandeja_inst

        mock_monitor_cls = MagicMock()
        mock_monitor_inst = MagicMock()
        mock_monitor_cls.return_value = mock_monitor_inst

        mock_engine_cls = MagicMock()
        mock_engine_inst = MagicMock()
        mock_engine_cls.return_value = mock_engine_inst

        with patch("move_mouse.ui.app.Settings", mock_settings):
            with patch("move_mouse.ui.app.Engine", mock_engine_cls):
                with patch("move_mouse.ui.app.BandejaSistema", mock_bandeja_cls):
                    with patch(
                        "move_mouse.ui.app.SessionMonitor", mock_monitor_cls
                    ):
                        from move_mouse.ui.app import MoveMouseApp

                        app = MoveMouseApp()
                        app.do_startup()

                        return (
                            app,
                            mock_engine_cls,
                            mock_engine_inst,
                            mock_bandeja_cls,
                            mock_bandeja_inst,
                            mock_monitor_cls,
                            mock_monitor_inst,
                            mock_glib,
                            mock_gtk,
                        )

    def test_creacion_app(self):
        """La aplicación se crea con el ID correcto."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_bandeja_cls,
            mock_bandeja_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._crear_app()

        assert app.props.application_id == "org.movemouse.MoveMouse"

    def test_startup_inicializa_componentes(self):
        """do_startup inicializa motor, bandeja y monitor."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_bandeja_cls,
            mock_bandeja_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._crear_app()

        mock_engine_cls.assert_called_once()
        mock_bandeja_cls.assert_called_once()
        mock_monitor_cls.assert_called_once()
        mock_engine_inst.add_listener.assert_called_once()

    def test_bandeja_conecta_callbacks(self):
        """Los callbacks de la bandeja se conectan correctamente."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_bandeja_cls,
            mock_bandeja_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._crear_app()

        assert mock_bandeja_inst.on_iniciar is not None
        assert mock_bandeja_inst.on_detener is not None
        assert mock_bandeja_inst.on_mostrar_ventana is not None
        assert mock_bandeja_inst.on_acerca_de is not None
        assert mock_bandeja_inst.on_salir is not None

    def test_monitor_conecta_eventos(self):
        """El monitor conecta eventos de sesión."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_bandeja_cls,
            mock_bandeja_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._crear_app()

        mock_monitor_inst.on_lock.assert_called_once()
        mock_monitor_inst.on_unlock.assert_called_once()
        mock_monitor_inst.on_suspend.assert_called_once()
        mock_monitor_inst.on_resume.assert_called_once()

    def test_bandeja_iniciar_arranca_motor(self):
        """bandeja_iniciar arranca el motor si está IDLE."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_bandeja_cls,
            mock_bandeja_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._crear_app()

        mock_engine_inst.state = EngineState.IDLE
        mock_bandeja_inst.on_iniciar()

        mock_engine_inst.start.assert_called_once()

    def test_bandeja_detener_detiene_motor(self):
        """bandeja_detener detiene el motor."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_bandeja_cls,
            mock_bandeja_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._crear_app()

        mock_bandeja_inst.on_detener()

        mock_engine_inst.stop.assert_called_once()

    def test_bandeja_salir_detiene_todo(self):
        """bandeja_salir detiene todo y cierra la app."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_bandeja_cls,
            mock_bandeja_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._crear_app()

        app.quit = MagicMock()
        mock_bandeja_inst.on_salir()

        mock_engine_inst.stop.assert_called_once()
        app.quit.assert_called_once()

    def test_cambio_estado_actualiza_bandeja(self):
        """El cambio de estado actualiza la bandeja."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_bandeja_cls,
            mock_bandeja_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._crear_app()

        app._on_cambio_estado(EngineState.IDLE, EngineState.RUNNING)

        mock_bandeja_inst.actualizar_estado.assert_called_with(True)

    def test_cambio_estado_detiene_timer(self):
        """Al cambiar a estado no-running, se detiene el timer de UI."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_bandeja_cls,
            mock_bandeja_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._crear_app()

        app._timer_ui = 123
        app._on_cambio_estado(EngineState.RUNNING, EngineState.IDLE)

        mock_glib.source_remove.assert_called_with(123)

    def test_motor_bloquear_por_lock(self):
        """El motor se bloquea al recibir evento de lock."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_bandeja_cls,
            mock_bandeja_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._crear_app()

        callback_lock = mock_monitor_inst.on_lock.call_args[0][0]
        callback_lock()

        mock_engine_inst.lock.assert_called_once()

    def test_motor_desbloquear_por_unlock(self):
        """El motor se desbloquea al recibir evento de unlock."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_bandeja_cls,
            mock_bandeja_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._crear_app()

        callback_unlock = mock_monitor_inst.on_unlock.call_args[0][0]
        callback_unlock()

        mock_engine_inst.unlock.assert_called_once()

    def test_motor_detener_por_suspend(self):
        """El motor se detiene al recibir evento de suspend."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_bandeja_cls,
            mock_bandeja_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._crear_app()

        callback_suspend = mock_monitor_inst.on_suspend.call_args[0][0]
        callback_suspend()

        mock_engine_inst.stop.assert_called_once()

    def test_motor_reanudar_por_resume(self):
        """El motor se reanuda al recibir evento de resume."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_bandeja_cls,
            mock_bandeja_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._crear_app()

        callback_resume = mock_monitor_inst.on_resume.call_args[0][0]
        callback_resume()

        mock_engine_inst.start.assert_called_once()

    def test_detener_todo_limpia_recursos(self):
        """_detener_todo limpia motor, timer y monitor."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_bandeja_cls,
            mock_bandeja_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._crear_app()

        app._timer_ui = 456
        app._detener_todo()

        mock_engine_inst.stop.assert_called_once()
        mock_monitor_inst.stop.assert_called_once()
