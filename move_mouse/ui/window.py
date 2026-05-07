"""Move Mouse Linux main GTK window."""

import logging
from typing import Callable, Optional

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

from move_mouse.core.engine import EngineState

logger = logging.getLogger(__name__)

# State to text mapping
STATE_TEXT = {
    EngineState.IDLE: "Idle",
    EngineState.RUNNING: "Running",
    EngineState.PAUSED: "Paused",
    EngineState.EXECUTING: "Executing action",
    EngineState.SLEEPING: "In scheduled sleep",
    EngineState.LOCKED: "Locked (session locked)",
}


class MainWindow(Gtk.Window):
    """Main window with status controls and start/stop button."""

    def __init__(self, app: "Gtk.Application"):
        super().__init__(title="Move Mouse Linux")
        self._app = app
        self._engine = None

        # Widgets
        self._label_status: Optional[Gtk.Label] = None
        self._label_time: Optional[Gtk.Label] = None
        self._button_toggle: Optional[Gtk.Button] = None
        self._button_settings: Optional[Gtk.Button] = None

        # Callbacks
        self._on_close: Optional[Callable[[], None]] = None
        self._on_settings: Optional[Callable[[], None]] = None

        self._build_ui()
        self._connect_signals()

    # -- Properties --

    @property
    def engine(self):
        return self._engine

    @engine.setter
    def engine(self, engine) -> None:
        self._engine = engine
        self._update_state(engine.state)

    @property
    def on_close(self) -> Optional[Callable[[], None]]:
        return self._on_close

    @on_close.setter
    def on_close(self, callback: Callable[[], None]) -> None:
        self._on_close = callback

    @property
    def on_settings(self) -> Optional[Callable[[], None]]:
        return self._on_settings

    @on_settings.setter
    def on_settings(self, callback: Callable[[], None]) -> None:
        self._on_settings = callback

    # -- UI Construction --

    def _build_ui(self) -> None:
        self.set_default_size(320, 180)
        self.set_border_width(12)
        self.set_resizable(False)

        # Vertical container
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add(box)

        # Status label
        self._label_status = Gtk.Label(label="Status: Idle")
        self._label_status.set_halign(Gtk.Align.CENTER)
        box.pack_start(self._label_status, False, False, 0)

        # Next action label
        self._label_time = Gtk.Label(label="Next action: --")
        self._label_time.set_halign(Gtk.Align.CENTER)
        box.pack_start(self._label_time, False, False, 0)

        # Start/Stop button
        self._button_toggle = Gtk.Button(label="Start")
        self._button_toggle.set_halign(Gtk.Align.CENTER)
        self._button_toggle.set_size_request(120, -1)
        box.pack_start(self._button_toggle, False, False, 0)

        # Settings button
        self._button_settings = Gtk.Button(label="Settings")
        self._button_settings.set_halign(Gtk.Align.CENTER)
        self._button_settings.set_size_request(120, -1)
        box.pack_start(self._button_settings, False, False, 0)

        box.show_all()

    def _connect_signals(self) -> None:
        self.connect("delete-event", self._on_window_close)
        if self._button_toggle:
            self._button_toggle.connect("clicked", self._on_toggle_click)
        if self._button_settings:
            self._button_settings.connect("clicked", self._on_settings_click)

    # -- State updates --

    def update_from_thread(self, state: EngineState) -> None:
        """Update UI from engine thread using GLib.idle_add."""
        GLib.idle_add(self._update_state, state)

    def _update_state(self, state: EngineState) -> None:
        text = STATE_TEXT.get(state, str(state.value))
        if self._label_status:
            self._label_status.set_text(f"Status: {text}")

        if self._button_toggle:
            if state == EngineState.RUNNING:
                self._button_toggle.set_label("Stop")
            else:
                self._button_toggle.set_label("Start")

    def update_time(self, seconds: int) -> None:
        """Update the remaining time label."""
        GLib.idle_add(self._label_time.set_text, f"Next action: {seconds}s")

    # -- Event handlers --

    def _on_toggle_click(self, widget) -> None:
        if self._engine is None:
            return

        if self._engine.state == EngineState.RUNNING:
            self._engine.stop()
        elif self._engine.state == EngineState.IDLE:
            self._engine.start()
        elif self._engine.state == EngineState.PAUSED:
            self._engine.resume()
        elif self._engine.state == EngineState.LOCKED:
            self._engine.unlock()

    def _on_settings_click(self, widget) -> None:
        """Open settings dialog when Settings button is clicked."""
        if self._on_settings:
            self._on_settings()

    def _on_window_close(self, widget, event) -> bool:
        """On window close, hide instead of exiting."""
        self.hide()
        if self._on_close:
            self._on_close()
        return True  # Stop event propagation

    def show_window(self) -> None:
        """Show the window and bring it to front."""
        self.show_all()
        self.present()

    def iconify(self) -> None:
        """Minimise the window (safe wrapper around Gtk.Window.iconify)."""
        super().iconify()

    def show_window_from_tray(self) -> None:
        """Restore a minimised window and bring it to front.

        Called from the system tray "Show Window" menu item.
        Deiconifies if minimised, then presents the window.
        """
        self.deiconify()
        self.show_all()
        self.present()

    def set_button_animation(self, enabled: bool) -> None:
        """Enable or disable button relief animation.

        When disabled, buttons use NONE relief (flat, no press animation).
        When enabled, buttons use NORMAL relief (default GTK behaviour).
        """
        relief = Gtk.ReliefStyle.NORMAL if enabled else Gtk.ReliefStyle.NONE
        if self._button_toggle:
            self._button_toggle.set_relief(relief)
        if self._button_settings:
            self._button_settings.set_relief(relief)
