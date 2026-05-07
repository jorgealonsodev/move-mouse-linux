"""System tray icon with AppIndicator and Gtk.StatusIcon support."""

import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Try to import AppIndicator3; fallback to Gtk.StatusIcon
try:
    import gi

    gi.require_version("Gtk", "3.0")
    # Prefer AyatanaAppIndicator3 if available, otherwise AppIndicator3
    try:
        gi.require_version("AyatanaAppIndicator3", "0.1")
        from gi.repository import AyatanaAppIndicator3 as AppIndicator3

        _INDICATOR_AVAILABLE = True
        _INDICATOR_LIB = "AyatanaAppIndicator3"
    except ValueError:
        try:
            gi.require_version("AppIndicator3", "0.1")
            from gi.repository import AppIndicator3

            _INDICATOR_AVAILABLE = True
            _INDICATOR_LIB = "AppIndicator3"
        except ValueError:
            _INDICATOR_AVAILABLE = False
            _INDICATOR_LIB = None
except ImportError:
    _INDICATOR_AVAILABLE = False
    _INDICATOR_LIB = None


class SystemTray:
    """System tray icon with context menu.

    Uses AppIndicator3 (or AyatanaAppIndicator3) if available;
    otherwise falls back to Gtk.StatusIcon.
    """

    def __init__(
        self,
        app_id: str = "org.movemouse.MoveMouse",
        icon_name: str = "org.movemouse.MoveMouse",
        title: str = "Move Mouse Linux",
    ):
        self._app_id = app_id
        self._icon_name = icon_name
        self._title = title
        self._indicator = None
        self._status_icon = None
        self._menu = None
        self._using_appindicator = False

        # Callbacks
        self._on_start: Optional[Callable[[], None]] = None
        self._on_stop: Optional[Callable[[], None]] = None
        self._on_show_window: Optional[Callable[[], None]] = None
        self._on_settings: Optional[Callable[[], None]] = None
        self._on_about: Optional[Callable[[], None]] = None
        self._on_quit: Optional[Callable[[], None]] = None

        self._create()

    # -- Callback properties --

    @property
    def on_start(self) -> Optional[Callable[[], None]]:
        return self._on_start

    @on_start.setter
    def on_start(self, callback: Callable[[], None]) -> None:
        self._on_start = callback

    @property
    def on_stop(self) -> Optional[Callable[[], None]]:
        return self._on_stop

    @on_stop.setter
    def on_stop(self, callback: Callable[[], None]) -> None:
        self._on_stop = callback

    @property
    def on_show_window(self) -> Optional[Callable[[], None]]:
        return self._on_show_window

    @on_show_window.setter
    def on_show_window(self, callback: Callable[[], None]) -> None:
        self._on_show_window = callback

    @property
    def on_settings(self) -> Optional[Callable[[], None]]:
        return self._on_settings

    @on_settings.setter
    def on_settings(self, callback: Callable[[], None]) -> None:
        self._on_settings = callback

    @property
    def on_about(self) -> Optional[Callable[[], None]]:
        return self._on_about

    @on_about.setter
    def on_about(self, callback: Callable[[], None]) -> None:
        self._on_about = callback

    @property
    def on_quit(self) -> Optional[Callable[[], None]]:
        return self._on_quit

    @on_quit.setter
    def on_quit(self, callback: Callable[[], None]) -> None:
        self._on_quit = callback

    # -- State --

    @property
    def using_appindicator(self) -> bool:
        return self._using_appindicator

    @property
    def indicator(self):
        """Return the active indicator or status_icon."""
        return self._indicator if self._using_appindicator else self._status_icon

    # -- Visibility --

    def set_visible(self, visible: bool) -> None:
        """Show or hide the system tray icon.

        For AppIndicator: toggles between ACTIVE and PASSIVE status.
        For Gtk.StatusIcon: calls set_visible directly.
        """
        if self._using_appindicator and self._indicator is not None:
            status = (
                AppIndicator3.IndicatorStatus.ACTIVE
                if visible
                else AppIndicator3.IndicatorStatus.PASSIVE
            )
            self._indicator.set_status(status)
            logger.debug("AppIndicator visibility: %s", visible)
        elif self._status_icon is not None:
            self._status_icon.set_visible(visible)
            logger.debug("StatusIcon visibility: %s", visible)

    # -- Creation --

    def _create(self) -> None:
        if _INDICATOR_AVAILABLE:
            self._create_with_appindicator()
        else:
            logger.info(
                "AppIndicator not available, using Gtk.StatusIcon as fallback"
            )
            self._create_with_status_icon()

    def _create_with_appindicator(self) -> None:
        """Create the icon using AppIndicator3."""
        from gi.repository import Gtk

        self._indicator = AppIndicator3.Indicator.new(
            self._app_id, self._icon_name, AppIndicator3.IndicatorCategory.SYSTEM_SERVICES
        )
        self._indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self._indicator.set_title(self._title)

        self._menu = self._build_menu(Gtk)
        self._indicator.set_menu(self._menu)
        self._using_appindicator = True
        logger.debug("Tray created with %s", _INDICATOR_LIB)

    def _create_with_status_icon(self) -> None:
        """Create the icon using Gtk.StatusIcon (fallback)."""
        from gi.repository import Gtk

        self._status_icon = Gtk.StatusIcon()
        self._status_icon.set_from_icon_name(self._icon_name)
        self._status_icon.set_tooltip_text(self._title)
        self._status_icon.connect("activate", self._on_status_icon_activate)
        self._status_icon.connect("popup-menu", self._on_status_icon_popup)

        self._menu = self._build_menu(Gtk)
        logger.debug("Tray created with Gtk.StatusIcon")

    def _build_menu(self, gtk_module) -> "gtk_module.Menu":
        """Build the context menu with standard options."""
        menu = gtk_module.Menu()

        # Start / Stop
        self._item_toggle = gtk_module.MenuItem(label="Start")
        self._item_toggle.connect("activate", self._on_toggle_activate)
        menu.append(self._item_toggle)

        # Show Window
        item_window = gtk_module.MenuItem(label="Show Window")
        item_window.connect("activate", self._on_window_activate)
        menu.append(item_window)

        # Separator
        menu.append(gtk_module.SeparatorMenuItem())

        # Settings
        item_settings = gtk_module.MenuItem(label="Settings")
        item_settings.connect("activate", self._on_settings_activate)
        menu.append(item_settings)

        # About
        item_about = gtk_module.MenuItem(label="About")
        item_about.connect("activate", self._on_about_activate)
        menu.append(item_about)

        # Quit
        item_quit = gtk_module.MenuItem(label="Quit")
        item_quit.connect("activate", self._on_quit_activate)
        menu.append(item_quit)

        menu.show_all()
        return menu

    # -- Event handlers --

    def update_state(self, is_running: bool) -> None:
        """Update the toggle button text based on engine state."""
        if hasattr(self, "_item_toggle") and self._item_toggle is not None:
            if is_running:
                self._item_toggle.set_label("Stop")
            else:
                self._item_toggle.set_label("Start")

    def _on_toggle_activate(self, widget) -> None:
        if self._on_start and self._item_toggle.get_label() == "Start":
            self._on_start()
        elif self._on_stop and self._item_toggle.get_label() == "Stop":
            self._on_stop()

    def _on_window_activate(self, widget) -> None:
        if self._on_show_window:
            self._on_show_window()

    def _on_settings_activate(self, widget) -> None:
        if self._on_settings:
            self._on_settings()

    def _on_about_activate(self, widget) -> None:
        if self._on_about:
            self._on_about()

    def _on_quit_activate(self, widget) -> None:
        if self._on_quit:
            self._on_quit()

    def _on_status_icon_activate(self, icon) -> None:
        """On StatusIcon click, show window."""
        if self._on_show_window:
            self._on_show_window()

    def _on_status_icon_popup(self, icon, button, activate_time) -> None:
        """Show context menu on StatusIcon."""
        if self._menu:
            self._menu.popup(None, None, None, None, button, activate_time)
