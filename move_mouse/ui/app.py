"""Main GTK application for Move Mouse Linux."""

import logging
import os
import random
import shutil
from typing import Any, Dict, List, Optional

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gio, GLib, Gtk

from move_mouse.core.engine import Engine, EngineState
from move_mouse.core.executor import Executor
from move_mouse.core.idle_detector import IdleDetector
from move_mouse.models.settings import Settings
from move_mouse.mouse_controller import MouseController, CursorDirection, CursorSpeed
from move_mouse.actions.base import ActionBase
from move_mouse.actions.move_mouse import MoveMouseAction
from move_mouse.actions.click_mouse import ClickMouseAction
from move_mouse.actions.scroll_mouse import ScrollMouseAction
from move_mouse.actions.position_cursor import PositionCursorAction
from move_mouse.actions.sleep_action import SleepAction
from move_mouse.services.session_monitor import SessionMonitor
from move_mouse.ui.tray import SystemTray
from move_mouse.ui.window import MainWindow
from move_mouse.ui.settings_window import SettingsWindow

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Autostart helpers
# ---------------------------------------------------------------------------

_AUTOSTART_DIR = os.path.expanduser("~/.config/autostart")
_AUTOSTART_FILE = os.path.join(_AUTOSTART_DIR, "move-mouse-linux.desktop")
_SYSTEM_DESKTOP = "/usr/share/applications/move-mouse-linux.desktop"


def _set_autostart(enabled: bool) -> None:
    """Install or remove the autostart .desktop entry."""
    if enabled:
        os.makedirs(_AUTOSTART_DIR, exist_ok=True)
        src = _SYSTEM_DESKTOP if os.path.exists(_SYSTEM_DESKTOP) else None
        if src:
            shutil.copy2(src, _AUTOSTART_FILE)
            logger.info("Autostart enabled: %s", _AUTOSTART_FILE)
        else:
            # Write a minimal .desktop if the system one is missing
            with open(_AUTOSTART_FILE, "w") as f:
                f.write(
                    "[Desktop Entry]\n"
                    "Type=Application\n"
                    "Name=Move Mouse Linux\n"
                    "Exec=move-mouse\n"
                    "Hidden=false\n"
                    "NoDisplay=false\n"
                    "X-GNOME-Autostart-enabled=true\n"
                )
            logger.info("Autostart entry created: %s", _AUTOSTART_FILE)
    else:
        if os.path.exists(_AUTOSTART_FILE):
            os.remove(_AUTOSTART_FILE)
            logger.info("Autostart disabled: removed %s", _AUTOSTART_FILE)


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def _apply_log_level(enabled: bool, level_name: str) -> None:
    """Apply the log level to the root move_mouse logger."""
    root_logger = logging.getLogger("move_mouse")
    if not enabled:
        root_logger.setLevel(logging.WARNING)
        logger.debug("Logging disabled — level set to WARNING")
        return
    level = getattr(logging, level_name.upper(), logging.INFO)
    root_logger.setLevel(level)
    logger.debug("Log level set to %s", level_name.upper())


# ---------------------------------------------------------------------------
# Action builder
# ---------------------------------------------------------------------------

def _dict_to_action(d: Dict[str, Any], index: int) -> ActionBase:
    """Convert a settings action dict to an ActionBase instance."""
    action_type = d.get("type", "move_mouse")
    action_id = d.get("id", f"{action_type}_{index}")
    name = d.get("name", action_type)
    is_enabled = d.get("enabled", True)
    repeat_mode = d.get("repeat_mode", "forever")
    interval_execution_count = d.get("interval_execution_count", 1)

    if action_type == "move_mouse":
        return MoveMouseAction(
            action_id=action_id,
            name=name,
            is_enabled=is_enabled,
            repeat_mode=repeat_mode,
            interval_execution_count=interval_execution_count,
            direction=CursorDirection(d.get("direction", "square")),
            distance=int(d.get("distance", 5)),
            upper_distance=d.get("upper_distance"),
            random=d.get("random", False),
            speed=CursorSpeed(d.get("speed", "normal")),
            abort_if_user_activity=d.get("abort_if_user_activity", True),
        )
    if action_type == "click_mouse":
        return ClickMouseAction(
            action_id=action_id,
            name=name,
            is_enabled=is_enabled,
            repeat_mode=repeat_mode,
            interval_execution_count=interval_execution_count,
            button=int(d.get("button", 1)),
            hold_ms=int(d.get("hold_ms", 50)),
        )
    if action_type == "position_cursor":
        return PositionCursorAction(
            action_id=action_id,
            name=name,
            is_enabled=is_enabled,
            repeat_mode=repeat_mode,
            interval_execution_count=interval_execution_count,
            x=int(d.get("x", 0)),
            y=int(d.get("y", 0)),
        )
    if action_type == "scroll_mouse":
        return ScrollMouseAction(
            action_id=action_id,
            name=name,
            is_enabled=is_enabled,
            repeat_mode=repeat_mode,
            interval_execution_count=interval_execution_count,
            scroll_amount=int(d.get("scroll_amount", 1)),
            scroll_direction=d.get("scroll_direction", "up"),
        )
    if action_type == "sleep":
        return SleepAction(
            action_id=action_id,
            name=name,
            is_enabled=is_enabled,
            repeat_mode=repeat_mode,
            interval_execution_count=interval_execution_count,
            duration_seconds=float(d.get("duration_seconds", 1.0)),
            random_duration=d.get("random_duration", False),
            upper_duration_ms=float(d.get("upper_duration_seconds", 5.0)),
        )

    raise ValueError(f"Unknown action type: {action_type}")


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

class MoveMouseApp(Gtk.Application):
    """GTK application with system tray and engine control."""

    def __init__(self):
        super().__init__(
            application_id="org.movemouse.MoveMouse",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self._engine: Optional[Engine] = None
        self._config: Optional[Settings] = None
        self._session_monitor: Optional[SessionMonitor] = None
        self._window: Optional[MainWindow] = None
        self._tray: Optional[SystemTray] = None
        self._idle_detector: Optional[IdleDetector] = None
        self._interval_ms: int = 30000
        self._timer_ui: Optional[int] = None
        self._mouse_controller: Optional[MouseController] = None
        self._actions: List[ActionBase] = []
        self._executor: Optional[Executor] = None
        self._inhibit_cookie: Optional[int] = None
        self._paused_by_battery: bool = False
        self._battery_timer_id: Optional[int] = None

    # -- Gtk.Application lifecycle --

    def do_startup(self) -> None:
        Gtk.Application.do_startup(self)
        logger.debug("Initializing MoveMouseApp")

        Gtk.Window.set_default_icon_name("org.movemouse.MoveMouse")

        self._config = Settings.load(Settings.default_path())

        # Apply logging settings from config
        _apply_log_level(self._config.enable_logging, self._config.log_level)

        self._interval_ms = self._config.lower_interval * 1000

        self._mouse_controller = MouseController()
        self._build_actions()

        self._engine = Engine(
            tick_callback=self._on_engine_tick,
            interval_ms=self._interval_ms,
        )
        self._engine.add_listener(self._on_state_change)

        self._tray = SystemTray(
            app_id=self.props.application_id,
            title="Move Mouse Linux",
        )
        self._connect_tray()

        self._session_monitor = SessionMonitor()
        self._connect_session_monitor()
        self._session_monitor.start()

        self._idle_detector = IdleDetector(polling_interval_ms=250)
        self._connect_auto_pause_resume()

        # Apply UI/platform settings that are relevant at startup
        self._apply_ui_settings(self._config)

        # Auto-start engine if configured
        if self._config.start_at_launch:
            logger.info("start_at_launch: auto-starting engine")
            GLib.idle_add(self._engine.start)

    def do_activate(self) -> None:
        Gtk.Application.do_activate(self)
        logger.debug("Application activated")

        if self._window is None:
            self._window = MainWindow(self)
            self._window.engine = self._engine
            self._window.on_close = self._on_window_hidden
            self._window.on_settings = self._open_settings
            self.add_window(self._window)

        # Honour hide_main_window at startup
        if self._config and self._config.hide_main_window:
            logger.debug("hide_main_window: skipping initial show")
        else:
            self._window.show_window()

    def do_shutdown(self) -> None:
        Gtk.Application.do_shutdown(self)
        logger.info("Application shutting down")
        self._stop_all()

    # -- Event connections --

    def _connect_tray(self) -> None:
        if self._tray is None:
            return
        self._tray.on_start = self._tray_start
        self._tray.on_stop = self._tray_stop
        self._tray.on_show_window = self._tray_show_window
        self._tray.on_settings = self._tray_settings
        self._tray.on_about = self._tray_about
        self._tray.on_quit = self._tray_quit

    def _connect_session_monitor(self) -> None:
        if self._session_monitor is None:
            return
        self._session_monitor.on_lock(self._engine_lock)
        self._session_monitor.on_unlock(self._engine_unlock)
        self._session_monitor.on_suspend(self._engine_stop)
        self._session_monitor.on_resume(self._engine_resume)

    def _connect_auto_pause_resume(self) -> None:
        """Connect IdleDetector to engine for auto-pause/resume."""
        if self._idle_detector is None or self._engine is None:
            return

        def _on_idle(idle_ms: int) -> None:
            if self._config is None:
                return

            state = self._engine.state

            if (
                self._config.auto_pause
                and state == EngineState.RUNNING
                and idle_ms < 3000
            ):
                logger.debug("Auto-pause: activity detected (idle=%dms)", idle_ms)
                GLib.idle_add(self._engine.pause)

            if (
                self._config.auto_resume
                and state == EngineState.PAUSED
                and idle_ms > self._config.auto_resume_seconds * 1000
            ):
                logger.debug("Auto-resume: prolonged inactivity (idle=%dms)", idle_ms)
                GLib.idle_add(self._engine.resume)

        self._idle_detector.add_callback(_on_idle)
        self._idle_detector.start()

    # -- Tray actions --

    def _tray_start(self) -> None:
        if self._engine and self._engine.state == EngineState.IDLE:
            self._engine.start()
            self._start_timer_ui()

    def _tray_stop(self) -> None:
        if self._engine:
            self._engine.stop()
            self._stop_timer_ui()

    def _tray_show_window(self) -> None:
        if self._window:
            self._window.show_window_from_tray()
        else:
            self.activate()

    def _tray_settings(self) -> None:
        self._open_settings()

    def _open_settings(self) -> None:
        logger.info("Opening settings window")
        dialog = SettingsWindow(
            parent=self._window,
            settings=self._config,
        )
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            new_config = dialog.get_settings()
            self._save_and_apply_settings(new_config)
        dialog.destroy()

    def _tray_about(self) -> None:
        dialog = Gtk.AboutDialog(
            transient_for=self._window,
            modal=True,
            program_name="Move Mouse Linux",
            version="1.0.0",
            comments="Simulates user activity to prevent session lock.",
            license_type=Gtk.License.GPL_3_0,
        )
        dialog.run()
        dialog.destroy()

    def _tray_quit(self) -> None:
        self._stop_all()
        self.quit()

    # -- Engine callbacks --

    def _on_engine_tick(self) -> None:
        """Callback on each engine tick — compute interval then execute."""
        logger.debug("Engine tick — executing actions")

        # Random interval: reschedule with a new random value BEFORE executing
        if self._config and self._config.random_interval:
            lo = self._config.lower_interval * 1000
            hi = max(lo, self._config.upper_interval * 1000)
            new_interval = random.randint(lo, hi)
            self._engine._interval_ms = new_interval
            self._interval_ms = new_interval
            logger.debug("Random interval: next tick in %d ms", new_interval)

        if self._executor:
            self._executor.execute(self._mouse_controller)
        GLib.idle_add(self._start_timer_ui)

    def _on_state_change(
        self, old_state: EngineState, new_state: EngineState
    ) -> None:
        logger.debug("Engine: %s -> %s", old_state.value, new_state.value)

        if self._tray:
            GLib.idle_add(
                self._tray.update_state, new_state == EngineState.RUNNING
            )

        if self._window:
            self._window.update_from_thread(new_state)

        # Prevent screen burn — inhibit idle/saver while RUNNING
        if self._config and self._config.prevent_screen_burn:
            if new_state == EngineState.RUNNING and self._inhibit_cookie is None:
                GLib.idle_add(self._do_inhibit)
                logger.debug("Screen saver inhibit scheduled (cookie=%s)", self._inhibit_cookie)
            elif new_state != EngineState.RUNNING and self._inhibit_cookie is not None:
                cookie = self._inhibit_cookie
                self._inhibit_cookie = None
                GLib.idle_add(self.uninhibit, cookie)
                logger.debug("Screen saver uninhibit scheduled (cookie=%s)", cookie)

        # Show move mouse status in window title
        if self._config and self._config.show_move_mouse_status and self._window:
            status_text = {
                EngineState.RUNNING: "Running",
                EngineState.IDLE: "Idle",
                EngineState.PAUSED: "Paused",
            }.get(new_state, new_state.value.title())
            GLib.idle_add(
                self._window.set_title, f"Move Mouse Linux — {status_text}"
            )

        if new_state == EngineState.RUNNING:
            GLib.idle_add(self._start_timer_ui)
        else:
            GLib.idle_add(self._stop_timer_ui)

        # Minimise on stop
        if (
            new_state == EngineState.IDLE
            and self._config
            and self._config.minimise_on_stop
            and self._window
        ):
            GLib.idle_add(self._window.iconify)

        # Tray notification
        if self._config and self._config.show_system_tray_notifications:
            GLib.idle_add(
                self._send_tray_notification, old_state, new_state
            )

    def _send_tray_notification(
        self, old_state: EngineState, new_state: EngineState
    ) -> None:
        """Send a desktop notification on relevant state transitions."""
        if new_state == EngineState.RUNNING and old_state == EngineState.IDLE:
            self._notify_desktop("Move Mouse Linux", "Started — keeping session active.")
        elif new_state == EngineState.IDLE and old_state != EngineState.IDLE:
            self._notify_desktop("Move Mouse Linux", "Stopped.")
        elif new_state == EngineState.PAUSED:
            self._notify_desktop("Move Mouse Linux", "Paused.")

    def _notify_desktop(self, title: str, body: str) -> None:
        try:
            notification = Gio.Notification.new(title)
            notification.set_body(body)
            self.send_notification(None, notification)
        except Exception as exc:
            logger.debug("Desktop notification failed: %s", exc)

    def _do_inhibit(self) -> None:
        """Run inhibit on the main thread and store the cookie."""
        if self._inhibit_cookie is None:
            self._inhibit_cookie = self.inhibit(
                self._window,
                Gtk.ApplicationInhibitFlags.IDLE,
                "Move Mouse active",
            )
            logger.debug("Screen saver inhibited (cookie=%s)", self._inhibit_cookie)

    # -- Session monitor --

    def _engine_lock(self) -> None:
        if self._engine:
            if self._config and self._config.active_when_locked:
                logger.debug("active_when_locked: ignoring session lock")
                return
            self._engine.lock()

    def _engine_unlock(self) -> None:
        if self._engine:
            self._engine.unlock()

    def _engine_stop(self) -> None:
        if self._engine:
            self._engine.stop()

    def _engine_resume(self) -> None:
        if self._engine and self._config and self._config.auto_resume:
            self._engine.start()

    # -- UI Timer --

    def _start_timer_ui(self) -> None:
        self._stop_timer_ui()
        self._time_remaining_ms = self._interval_ms

        def _update() -> bool:
            self._time_remaining_ms -= 1000
            if self._time_remaining_ms <= 0:
                self._stop_timer_ui()
                return False
            if self._window:
                self._window.update_time(self._time_remaining_ms // 1000)
            return True

        self._timer_ui = GLib.timeout_add(1000, _update)

    def _stop_timer_ui(self) -> None:
        if self._timer_ui is not None:
            GLib.source_remove(self._timer_ui)
            self._timer_ui = None
        if self._window:
            self._window.update_time(0)

    # -- Window --

    def _on_window_hidden(self) -> None:
        logger.debug("Window hidden, application continues in tray")

    # -- Settings application --

    def _save_and_apply_settings(self, config: Settings) -> None:
        logger.info("Saving and applying new settings")
        old_config = self._config
        self._config = config

        config.save(Settings.default_path())

        # Logging
        _apply_log_level(config.enable_logging, config.log_level)

        # Actions + interval
        self._build_actions()
        self._interval_ms = config.lower_interval * 1000
        if self._engine is not None:
            self._engine._interval_ms = self._interval_ms
            logger.info("Engine interval updated to %d ms", self._interval_ms)

        # Autostart
        if old_config is None or config.start_at_launch != old_config.start_at_launch:
            _set_autostart(config.start_at_launch)

        # UI / platform settings
        self._apply_ui_settings(config)

        logger.info("Settings applied successfully")

    def _apply_ui_settings(self, config: Settings) -> None:
        """Apply UI/platform settings that affect the live session."""

        # Hide system tray icon
        if self._tray:
            self._tray.set_visible(not config.hide_system_tray_icon)

        # Taskbar visibility (skip_taskbar_hint)
        if self._window:
            self._window.set_skip_taskbar_hint(config.hide_from_taskbar)
            self._window.set_skip_pager_hint(config.hide_from_taskbar)

        # Hide from Alt+Tab (skip_pager_hint already handles most WMs;
        # set_accept_focus=False also helps)
        if self._window:
            if config.hide_from_alt_tab:
                self._window.set_accept_focus(False)
            else:
                self._window.set_accept_focus(True)

        # Topmost when running — connect once, guard with flag
        if self._window and not getattr(self, "_topmost_connected", False):
            self._topmost_connected = True
            self._engine.add_listener(self._on_state_change_topmost)

        # Disable button animation
        if self._window:
            self._window.set_button_animation(not config.disable_button_animation)

        # Pause on battery — start or stop the polling timer
        self._apply_battery_monitoring(config.pause_on_battery)

    def _on_state_change_topmost(
        self, old_state: EngineState, new_state: EngineState
    ) -> None:
        """Keep window above all others while engine is running (if configured)."""
        if self._config and self._config.topmost_when_running and self._window:
            keep_above = new_state == EngineState.RUNNING
            GLib.idle_add(self._window.set_keep_above, keep_above)

    # -- Action building --

    def _build_actions(self) -> None:
        self._actions = []
        for i, action_dict in enumerate(self._config.actions):
            try:
                action = _dict_to_action(action_dict, i)
                self._actions.append(action)
            except (ValueError, KeyError) as exc:
                logger.warning("Skipping invalid action %d: %s", i, exc)

        self._executor = Executor(
            actions=self._actions,
            trigger="interval",
            on_sleep=self._engine.on_executor_sleep if self._engine else None,
        )
        logger.info("Built %d actions from settings", len(self._actions))

    # -- Battery monitoring --

    def _apply_battery_monitoring(self, enabled: bool) -> None:
        """Start or stop the UPower battery polling timer."""
        if enabled:
            if self._battery_timer_id is not None:
                return  # already running
            logger.info("Battery monitoring enabled — polling every 30s")
            self._battery_timer_id = GLib.timeout_add(
                30_000, self._check_battery
            )
            # Do an immediate check
            self._check_battery()
        else:
            if self._battery_timer_id is not None:
                GLib.source_remove(self._battery_timer_id)
                self._battery_timer_id = None
                logger.info("Battery monitoring disabled")
            # If we had paused due to battery, resume now
            if self._paused_by_battery and self._engine:
                logger.debug("Resuming after battery monitoring disabled")
                self._engine.resume()
                self._paused_by_battery = False

    def _check_battery(self) -> bool:
        """Poll UPower via D-Bus to check if on battery.

        Returns True to keep the timer running, False to cancel it.
        """
        try:
            import dbus
        except ImportError:
            logger.warning(
                "pause_on_battery: python-dbus not installed, "
                "battery monitoring unavailable"
            )
            self._battery_timer_id = None
            return False  # cancel timer

        try:
            bus = dbus.SystemBus()
            upower = bus.get_object("org.freedesktop.UPower", "/org/freedesktop/UPower")
            props = dbus.Interface(upower, "org.freedesktop.DBus.Properties")
            # State: 1=charging, 2=discharging, 3=empty, 4=fully-charged
            on_battery = props.Get("org.freedesktop.UPower", "OnBattery")
            is_on_battery = bool(on_battery)
        except Exception as exc:
            logger.warning("UPower query failed: %s", exc)
            return True  # keep trying

        if is_on_battery:
            if self._engine and self._engine.state == EngineState.RUNNING:
                logger.info("On battery — pausing engine")
                self._engine.pause()
                self._paused_by_battery = True
        else:
            if self._paused_by_battery and self._engine:
                logger.info("On AC power — resuming engine")
                self._engine.resume()
                self._paused_by_battery = False

        return True  # keep timer running

    # -- Cleanup --

    def _stop_all(self) -> None:
        if self._engine:
            self._engine.stop()
        self._stop_timer_ui()
        if self._session_monitor:
            self._session_monitor.stop()
        if self._idle_detector:
            self._idle_detector.stop()
        # Clean up battery monitoring
        if self._battery_timer_id is not None:
            GLib.source_remove(self._battery_timer_id)
            self._battery_timer_id = None
        # Clean up screen saver inhibition
        if self._inhibit_cookie is not None:
            self.uninhibit(self._inhibit_cookie)
            self._inhibit_cookie = None
