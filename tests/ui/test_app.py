"""Tests for the main GTK application."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from move_mouse.core.engine import EngineState


def _clean_modules():
    """Clear cached modules to allow reimport."""
    for mod in list(sys.modules.keys()):
        if mod.startswith("move_mouse.ui"):
            del sys.modules[mod]


class MockApplication:
    """Mock of Gtk.Application for tests."""

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
    """Tests for MoveMouseApp with GTK mocks."""

    def setup_method(self):
        _clean_modules()

    def teardown_method(self):
        _clean_modules()
        for mod in ["gi", "gi.repository"]:
            sys.modules.pop(mod, None)

    def _create_app(self):
        """Create MoveMouseApp with all required mocks and call do_startup."""
        # Create mocks
        mock_glib = MagicMock()

        # Set up gi modules with MockApplication
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

        # Mock dependencies
        mock_settings = MagicMock()
        mock_settings.return_value.lower_interval = 30

        mock_tray_cls = MagicMock()
        mock_tray_inst = MagicMock()
        mock_tray_cls.return_value = mock_tray_inst

        mock_monitor_cls = MagicMock()
        mock_monitor_inst = MagicMock()
        mock_monitor_cls.return_value = mock_monitor_inst

        mock_engine_cls = MagicMock()
        mock_engine_inst = MagicMock()
        mock_engine_cls.return_value = mock_engine_inst

        with patch("move_mouse.ui.app.Settings", mock_settings):
            with patch("move_mouse.ui.app.Engine", mock_engine_cls):
                with patch("move_mouse.ui.app.SystemTray", mock_tray_cls):
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
                            mock_tray_cls,
                            mock_tray_inst,
                            mock_monitor_cls,
                            mock_monitor_inst,
                            mock_glib,
                            mock_gtk,
                        )

    def test_app_creation(self):
        """Application is created with the correct ID."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_tray_cls,
            mock_tray_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._create_app()

        assert app.props.application_id == "org.movemouse.MoveMouse"

    def test_startup_initializes_components(self):
        """do_startup initializes engine, tray, and monitor."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_tray_cls,
            mock_tray_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._create_app()

        mock_engine_cls.assert_called_once()
        mock_tray_cls.assert_called_once()
        mock_monitor_cls.assert_called_once()
        mock_engine_inst.add_listener.assert_called_once()

    def test_tray_connects_callbacks(self):
        """Tray callbacks are connected correctly."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_tray_cls,
            mock_tray_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._create_app()

        assert mock_tray_inst.on_start is not None
        assert mock_tray_inst.on_stop is not None
        assert mock_tray_inst.on_show_window is not None
        assert mock_tray_inst.on_about is not None
        assert mock_tray_inst.on_quit is not None

    def test_monitor_connects_events(self):
        """Monitor connects session events."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_tray_cls,
            mock_tray_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._create_app()

        mock_monitor_inst.on_lock.assert_called_once()
        mock_monitor_inst.on_unlock.assert_called_once()
        mock_monitor_inst.on_suspend.assert_called_once()
        mock_monitor_inst.on_resume.assert_called_once()

    def test_tray_start_starts_engine(self):
        """tray_start starts the engine if IDLE."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_tray_cls,
            mock_tray_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._create_app()

        mock_engine_inst.state = EngineState.IDLE
        mock_tray_inst.on_start()

        mock_engine_inst.start.assert_called_once()

    def test_tray_stop_stops_engine(self):
        """tray_stop stops the engine."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_tray_cls,
            mock_tray_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._create_app()

        mock_tray_inst.on_stop()

        mock_engine_inst.stop.assert_called_once()

    def test_tray_quit_stops_all(self):
        """tray_quit stops everything and closes the app."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_tray_cls,
            mock_tray_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._create_app()

        app.quit = MagicMock()
        mock_tray_inst.on_quit()

        mock_engine_inst.stop.assert_called_once()
        app.quit.assert_called_once()

    def test_state_change_updates_tray(self):
        """State change updates the tray."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_tray_cls,
            mock_tray_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._create_app()

        app._on_state_change(EngineState.IDLE, EngineState.RUNNING)

        mock_tray_inst.update_state.assert_called_with(True)

    def test_state_change_stops_timer(self):
        """When changing to non-running state, UI timer stops."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_tray_cls,
            mock_tray_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._create_app()

        app._timer_ui = 123
        app._on_state_change(EngineState.RUNNING, EngineState.IDLE)

        mock_glib.source_remove.assert_called_with(123)

    def test_engine_lock_by_lock_event(self):
        """Engine is locked when receiving lock event."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_tray_cls,
            mock_tray_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._create_app()

        callback_lock = mock_monitor_inst.on_lock.call_args[0][0]
        callback_lock()

        mock_engine_inst.lock.assert_called_once()

    def test_engine_unlock_by_unlock_event(self):
        """Engine is unlocked when receiving unlock event."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_tray_cls,
            mock_tray_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._create_app()

        callback_unlock = mock_monitor_inst.on_unlock.call_args[0][0]
        callback_unlock()

        mock_engine_inst.unlock.assert_called_once()

    def test_engine_stop_by_suspend_event(self):
        """Engine is stopped when receiving suspend event."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_tray_cls,
            mock_tray_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._create_app()

        callback_suspend = mock_monitor_inst.on_suspend.call_args[0][0]
        callback_suspend()

        mock_engine_inst.stop.assert_called_once()

    def test_engine_resume_by_resume_event(self):
        """Engine is resumed when receiving resume event."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_tray_cls,
            mock_tray_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._create_app()

        callback_resume = mock_monitor_inst.on_resume.call_args[0][0]
        callback_resume()

        mock_engine_inst.start.assert_called_once()

    def test_stop_all_cleans_resources(self):
        """_stop_all cleans engine, timer, and monitor."""
        (
            app,
            mock_engine_cls,
            mock_engine_inst,
            mock_tray_cls,
            mock_tray_inst,
            mock_monitor_cls,
            mock_monitor_inst,
            mock_glib,
            mock_gtk,
        ) = self._create_app()

        app._timer_ui = 456
        app._stop_all()

        mock_engine_inst.stop.assert_called_once()
        mock_monitor_inst.stop.assert_called_once()
