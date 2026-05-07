"""Tests for the main GTK window."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from move_mouse.core.engine import EngineState


def _mock_gi_modules():
    """Set up mocks for gi and gi.repository in sys.modules."""
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


def _clean_modules():
    """Clear cached modules to allow reimport."""
    for mod in list(sys.modules.keys()):
        if mod.startswith("move_mouse.ui"):
            del sys.modules[mod]


class TestMainWindow:
    """Tests for MainWindow with GTK mocks."""

    def setup_method(self):
        _clean_modules()

    def teardown_method(self):
        _clean_modules()
        for mod in ["gi", "gi.repository"]:
            sys.modules.pop(mod, None)

    def _create_window(self):
        """Create a window with GTK mocks."""
        mock_gtk, mock_glib = _mock_gi_modules()

        # Set up GTK widgets
        mock_box = MagicMock()
        mock_gtk.Box.return_value = mock_box
        mock_gtk.Orientation.VERTICAL = 0
        mock_gtk.Align.CENTER = 0

        mock_label_status = MagicMock()
        mock_label_time = MagicMock()
        mock_button = MagicMock()

        # Gtk.Label creates different mocks depending on context
        mock_gtk.Label.side_effect = [mock_label_status, mock_label_time]
        mock_gtk.Button.return_value = mock_button

        # Create a mock base class for Gtk.Window
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

        from move_mouse.ui.window import MainWindow

        app_mock = MagicMock()
        window = MainWindow(app_mock)
        return window, mock_gtk, mock_glib

    def test_window_creation(self):
        """Window is created correctly."""
        window, mock_gtk, mock_glib = self._create_window()
        assert window is not None
        mock_gtk.Box.assert_called_once()

    def test_update_state_runs_in_idle(self):
        """update_from_thread uses GLib.idle_add."""
        window, mock_gtk, mock_glib = self._create_window()

        window.update_from_thread(EngineState.RUNNING)

        mock_glib.idle_add.assert_called_once()

    def test_update_state_changes_text(self):
        """_update_state changes the label text correctly."""
        window, mock_gtk, mock_glib = self._create_window()
        mock_label = MagicMock()
        window._label_status = mock_label
        window._button_toggle = MagicMock()

        window._update_state(EngineState.RUNNING)

        mock_label.set_text.assert_called_with("Status: Running")

    def test_update_state_idle(self):
        """IDLE state shows correct text."""
        window, mock_gtk, mock_glib = self._create_window()
        mock_label = MagicMock()
        window._label_status = mock_label
        window._button_toggle = MagicMock()

        window._update_state(EngineState.IDLE)

        mock_label.set_text.assert_called_with("Status: Idle")

    def test_update_state_locked(self):
        """LOCKED state shows correct text."""
        window, mock_gtk, mock_glib = self._create_window()
        mock_label = MagicMock()
        window._label_status = mock_label
        window._button_toggle = MagicMock()

        window._update_state(EngineState.LOCKED)

        mock_label.set_text.assert_called_with(
            "Status: Locked (session locked)"
        )

    def test_button_toggle_starts_engine(self):
        """Clicking button with engine IDLE starts the engine."""
        window, mock_gtk, mock_glib = self._create_window()
        engine_mock = MagicMock()
        engine_mock.state = EngineState.IDLE
        window._engine = engine_mock

        window._on_toggle_click(None)

        engine_mock.start.assert_called_once()

    def test_button_toggle_stops_engine(self):
        """Clicking button with engine RUNNING stops the engine."""
        window, mock_gtk, mock_glib = self._create_window()
        engine_mock = MagicMock()
        engine_mock.state = EngineState.RUNNING
        window._engine = engine_mock

        window._on_toggle_click(None)

        engine_mock.stop.assert_called_once()

    def test_close_window_hides_it(self):
        """On window close, it hides instead of exiting."""
        window, mock_gtk, mock_glib = self._create_window()
        window.hide = MagicMock()

        result = window._on_window_close(None, None)

        window.hide.assert_called_once()
        assert result is True

    def test_close_callback_executes(self):
        """The on_close callback executes when closing the window."""
        window, mock_gtk, mock_glib = self._create_window()
        window.hide = MagicMock()
        callback = MagicMock()
        window.on_close = callback

        window._on_window_close(None, None)

        callback.assert_called_once()

    def test_update_time(self):
        """update_time updates the time label."""
        window, mock_gtk, mock_glib = self._create_window()
        window._label_time = MagicMock()

        window.update_time(25)

        mock_glib.idle_add.assert_called_once()

    def test_engine_setter_updates_state(self):
        """When assigning the engine, the window state is updated."""
        window, mock_gtk, mock_glib = self._create_window()
        mock_label = MagicMock()
        window._label_status = mock_label
        window._button_toggle = MagicMock()

        engine_mock = MagicMock()
        engine_mock.state = EngineState.PAUSED
        window.engine = engine_mock

        assert window.engine is engine_mock
        mock_label.set_text.assert_called_with("Status: Paused")
