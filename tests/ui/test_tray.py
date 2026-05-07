"""Tests for the system tray module."""

import sys
from unittest.mock import MagicMock, patch

import pytest


def _mock_gi_modules():
    """Set up mocks for gi and gi.repository in sys.modules."""
    mock_gi = MagicMock()
    mock_gtk = MagicMock()
    mock_appindicator = MagicMock()

    mock_repo = MagicMock()
    mock_repo.Gtk = mock_gtk
    mock_repo.AppIndicator3 = mock_appindicator
    mock_repo.AyatanaAppIndicator3 = mock_appindicator

    mock_gi.repository = mock_repo

    sys.modules["gi"] = mock_gi
    sys.modules["gi.repository"] = mock_repo
    return mock_gtk, mock_appindicator


def _clean_modules():
    """Clear cached modules to allow reimport."""
    for mod in list(sys.modules.keys()):
        if mod.startswith("move_mouse.ui"):
            del sys.modules[mod]


class TestSystemTray:
    """Tests for SystemTray with GTK mocks."""

    def setup_method(self):
        _clean_modules()

    def teardown_method(self):
        _clean_modules()
        for mod in ["gi", "gi.repository"]:
            sys.modules.pop(mod, None)

    def _create_tray_appindicator(self):
        """Create tray with AppIndicator available."""
        mock_gtk, mock_appindicator = _mock_gi_modules()

        # Set up AppIndicator
        mock_indicator = MagicMock()
        mock_appindicator.Indicator.new.return_value = mock_indicator
        mock_appindicator.IndicatorCategory.SYSTEM_SERVICES = 0
        mock_appindicator.IndicatorStatus.ACTIVE = 1

        # Set up GTK widgets
        mock_menu = MagicMock()
        mock_gtk.Menu.return_value = mock_menu
        mock_item = MagicMock()
        mock_item.get_label.return_value = "Start"
        mock_gtk.MenuItem.return_value = mock_item
        mock_gtk.SeparatorMenuItem.return_value = MagicMock()

        # Patch tray module variables
        import move_mouse.ui.tray as tray_mod

        tray_mod._INDICATOR_AVAILABLE = True
        tray_mod._INDICATOR_LIB = "AppIndicator3"
        tray_mod.AppIndicator3 = mock_appindicator

        from move_mouse.ui.tray import SystemTray

        return SystemTray(), mock_gtk, mock_appindicator, mock_indicator

    def _create_tray_status_icon(self):
        """Create tray with StatusIcon (fallback)."""
        mock_gtk, mock_appindicator = _mock_gi_modules()

        mock_status_icon = MagicMock()
        mock_gtk.StatusIcon.return_value = mock_status_icon
        mock_menu = MagicMock()
        mock_gtk.Menu.return_value = mock_menu
        mock_item = MagicMock()
        mock_item.get_label.return_value = "Start"
        mock_gtk.MenuItem.return_value = mock_item
        mock_gtk.SeparatorMenuItem.return_value = MagicMock()

        import move_mouse.ui.tray as tray_mod

        tray_mod._INDICATOR_AVAILABLE = False
        tray_mod._INDICATOR_LIB = None

        from move_mouse.ui.tray import SystemTray

        return SystemTray(), mock_gtk, mock_status_icon

    def test_creation_with_appindicator(self):
        """Tray is created using AppIndicator when available."""
        tray, mock_gtk, mock_appindicator, mock_indicator = (
            self._create_tray_appindicator()
        )

        assert tray.using_appindicator is True
        mock_appindicator.Indicator.new.assert_called_once()
        mock_indicator.set_status.assert_called_once()
        mock_indicator.set_menu.assert_called_once()

    def test_creation_with_status_icon_fallback(self):
        """Tray uses Gtk.StatusIcon when AppIndicator is not available."""
        tray, mock_gtk, mock_status_icon = self._create_tray_status_icon()

        assert tray.using_appindicator is False
        mock_gtk.StatusIcon.assert_called_once()
        mock_status_icon.set_from_icon_name.assert_called_once()
        mock_status_icon.set_tooltip_text.assert_called_once()

    def test_callbacks_are_assigned(self):
        """Callbacks can be assigned and read."""
        tray, _, _ = self._create_tray_status_icon()

        callback_start = MagicMock()
        callback_stop = MagicMock()
        callback_show = MagicMock()
        callback_quit = MagicMock()

        tray.on_start = callback_start
        tray.on_stop = callback_stop
        tray.on_show_window = callback_show
        tray.on_quit = callback_quit

        assert tray.on_start is callback_start
        assert tray.on_stop is callback_stop
        assert tray.on_show_window is callback_show
        assert tray.on_quit is callback_quit

    def test_update_state_changes_label(self):
        """update_state changes the toggle label."""
        tray, mock_gtk, mock_status_icon = self._create_tray_status_icon()
        mock_item = MagicMock()
        tray._item_toggle = mock_item

        tray.update_state(True)
        mock_item.set_label.assert_called_with("Stop")

        tray.update_state(False)
        mock_item.set_label.assert_called_with("Start")

    def test_toggle_start_executes_callback(self):
        """On toggle with label 'Start', executes on_start."""
        tray, mock_gtk, mock_status_icon = self._create_tray_status_icon()
        mock_item = MagicMock()
        mock_item.get_label.return_value = "Start"
        tray._item_toggle = mock_item
        callback = MagicMock()
        tray.on_start = callback

        tray._on_toggle_activate(None)

        callback.assert_called_once()

    def test_toggle_stop_executes_callback(self):
        """On toggle with label 'Stop', executes on_stop."""
        tray, mock_gtk, mock_status_icon = self._create_tray_status_icon()
        mock_item = MagicMock()
        mock_item.get_label.return_value = "Stop"
        tray._item_toggle = mock_item
        callback = MagicMock()
        tray.on_stop = callback

        tray._on_toggle_activate(None)

        callback.assert_called_once()

    def test_menu_items_are_connected(self):
        """Menu items are connected to their handlers."""
        tray, mock_gtk, mock_status_icon = self._create_tray_status_icon()

        # Verify multiple MenuItems were created
        assert mock_gtk.MenuItem.call_count >= 3
        mock_gtk.Menu.return_value.show_all.assert_called_once()
