"""Move Mouse Linux settings window."""

import logging
from typing import Any, Dict, List, Optional

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from move_mouse.models.settings import Settings
from move_mouse.mouse_controller import CursorDirection, CursorSpeed

logger = logging.getLogger(__name__)

# Available action types
ACTION_TYPES = [
    ("Move Cursor", "move_mouse"),
    ("Click", "click_mouse"),
    ("Position", "position_cursor"),
    ("Scroll", "scroll_mouse"),
    ("Sleep", "sleep"),
]


class SettingsWindow(Gtk.Dialog):
    """Settings dialog with tabs: General, Actions, Schedules, Blackouts, Logging."""

    def __init__(
        self,
        parent: Optional[Gtk.Window] = None,
        settings: Optional[Settings] = None,
    ):
        super().__init__(
            title="Settings - Move Mouse Linux",
            transient_for=parent,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
        )
        self._settings = settings or Settings()
        self._actions: List[Dict[str, Any]] = list(self._settings.actions)
        self._schedules: List[Dict[str, Any]] = list(self._settings.schedules)
        self._blackouts: List[Dict[str, Any]] = list(self._settings.blackouts)
        self._current_action_index: Optional[int] = None

        self.set_default_size(750, 550)
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK,
        )

        # Notebook with tabs
        self._notebook = Gtk.Notebook()
        self._notebook.set_margin_start(10)
        self._notebook.set_margin_end(10)
        self._notebook.set_margin_top(10)
        self._notebook.set_margin_bottom(10)

        # Tab: General
        general_tab = self._create_general_tab()
        self._notebook.append_page(general_tab, Gtk.Label(label="General"))

        # Tab: Actions
        actions_tab = self._create_actions_tab()
        self._notebook.append_page(actions_tab, Gtk.Label(label="Actions"))

        # Tab: Schedules
        schedules_tab = self._create_schedules_tab()
        self._notebook.append_page(schedules_tab, Gtk.Label(label="Schedules"))

        # Tab: Blackouts
        blackouts_tab = self._create_blackouts_tab()
        self._notebook.append_page(blackouts_tab, Gtk.Label(label="Blackouts"))

        # Tab: Logging
        logging_tab = self._create_logging_tab()
        self._notebook.append_page(logging_tab, Gtk.Label(label="Logging"))

        box = self.get_content_area()
        box.pack_start(self._notebook, True, True, 0)

        self.show_all()

    # ------------------------------------------------------------------
    # Tab: General
    # ------------------------------------------------------------------

    def _create_general_tab(self) -> Gtk.Widget:
        """Create the General settings tab."""
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        container.set_margin_start(15)
        container.set_margin_end(15)
        container.set_margin_top(15)
        container.set_margin_bottom(15)

        # Interval section
        frame_interval = Gtk.Frame(label="Interval (seconds)")
        frame_interval.set_margin_bottom(5)
        box_interval = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        box_interval.set_margin_start(10)
        box_interval.set_margin_end(10)
        box_interval.set_margin_top(5)
        box_interval.set_margin_bottom(5)

        box_interval.pack_start(
            Gtk.Label(label="Lower:"), False, False, 0
        )
        self._spin_lower_interval = Gtk.SpinButton.new_with_range(1, 3600, 1)
        self._spin_lower_interval.set_value(self._settings.lower_interval)
        box_interval.pack_start(self._spin_lower_interval, False, False, 0)

        self._check_random_interval = Gtk.CheckButton(label="Random interval")
        self._check_random_interval.set_active(self._settings.random_interval)
        box_interval.pack_start(self._check_random_interval, False, False, 0)

        box_interval.pack_start(
            Gtk.Label(label="Upper:"), False, False, 0
        )
        self._spin_upper_interval = Gtk.SpinButton.new_with_range(1, 3600, 1)
        self._spin_upper_interval.set_value(self._settings.upper_interval)
        self._spin_upper_interval.set_sensitive(self._settings.random_interval)
        box_interval.pack_start(self._spin_upper_interval, False, False, 0)

        self._check_random_interval.connect(
            "toggled", self._on_toggle_random_interval
        )

        frame_interval.add(box_interval)
        container.pack_start(frame_interval, False, False, 0)

        # Auto Pause/Resume section
        frame_autopause = Gtk.Frame(label="Auto Pause/Resume")
        frame_autopause.set_margin_bottom(5)
        box_autopause = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        box_autopause.set_margin_start(10)
        box_autopause.set_margin_end(10)
        box_autopause.set_margin_top(5)
        box_autopause.set_margin_bottom(5)

        # Auto-pause checkbox
        self._check_auto_pause = Gtk.CheckButton(label="Auto-pause")
        self._check_auto_pause.set_active(self._settings.auto_pause)
        box_autopause.pack_start(self._check_auto_pause, False, False, 0)

        # Auto-resume row
        box_autoresume = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self._check_auto_resume = Gtk.CheckButton(label="Auto-resume")
        self._check_auto_resume.set_active(self._settings.auto_resume)
        box_autoresume.pack_start(self._check_auto_resume, False, False, 0)

        box_autoresume.pack_start(
            Gtk.Label(label="Resume after (seconds):"), False, False, 0
        )
        self._spin_auto_resume_seconds = Gtk.SpinButton.new_with_range(1, 3600, 1)
        self._spin_auto_resume_seconds.set_value(self._settings.auto_resume_seconds)
        box_autoresume.pack_start(self._spin_auto_resume_seconds, False, False, 0)

        box_autopause.pack_start(box_autoresume, False, False, 0)
        frame_autopause.add(box_autopause)
        container.pack_start(frame_autopause, False, False, 0)

        # Behavior section
        frame_behavior = Gtk.Frame(label="Behavior")
        frame_behavior.set_margin_bottom(5)
        box_behavior = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        box_behavior.set_margin_start(10)
        box_behavior.set_margin_end(10)
        box_behavior.set_margin_top(5)
        box_behavior.set_margin_bottom(5)

        self._check_active_when_locked = Gtk.CheckButton(label="Active when locked")
        self._check_active_when_locked.set_active(self._settings.active_when_locked)
        box_behavior.pack_start(self._check_active_when_locked, False, False, 0)

        self._check_minimise_on_stop = Gtk.CheckButton(label="Minimise on stop")
        self._check_minimise_on_stop.set_active(self._settings.minimise_on_stop)
        box_behavior.pack_start(self._check_minimise_on_stop, False, False, 0)

        self._check_start_at_launch = Gtk.CheckButton(label="Start at launch")
        self._check_start_at_launch.set_active(self._settings.start_at_launch)
        box_behavior.pack_start(self._check_start_at_launch, False, False, 0)

        frame_behavior.add(box_behavior)
        container.pack_start(frame_behavior, False, False, 0)

        # UI Options section
        frame_ui = Gtk.Frame(label="UI Options")
        frame_ui.set_margin_bottom(5)
        box_ui = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        box_ui.set_margin_start(10)
        box_ui.set_margin_end(10)
        box_ui.set_margin_top(5)
        box_ui.set_margin_bottom(5)

        self._check_hide_from_taskbar = Gtk.CheckButton(label="Hide from taskbar")
        self._check_hide_from_taskbar.set_active(self._settings.hide_from_taskbar)
        box_ui.pack_start(self._check_hide_from_taskbar, False, False, 0)

        self._check_hide_main_window = Gtk.CheckButton(label="Hide main window")
        self._check_hide_main_window.set_active(self._settings.hide_main_window)
        box_ui.pack_start(self._check_hide_main_window, False, False, 0)

        self._check_hide_system_tray_icon = Gtk.CheckButton(label="Hide system tray icon")
        self._check_hide_system_tray_icon.set_active(self._settings.hide_system_tray_icon)
        box_ui.pack_start(self._check_hide_system_tray_icon, False, False, 0)

        self._check_show_tray_notifications = Gtk.CheckButton(label="Show tray notifications")
        self._check_show_tray_notifications.set_active(self._settings.show_system_tray_notifications)
        box_ui.pack_start(self._check_show_tray_notifications, False, False, 0)

        self._check_show_taskbar_status = Gtk.CheckButton(label="Show taskbar status")
        self._check_show_taskbar_status.set_active(self._settings.show_taskbar_status)
        box_ui.pack_start(self._check_show_taskbar_status, False, False, 0)

        frame_ui.add(box_ui)
        container.pack_start(frame_ui, False, False, 0)

        # Platform Options section
        frame_platform = Gtk.Frame(label="Platform Options")
        frame_platform.set_margin_bottom(5)
        box_platform = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        box_platform.set_margin_start(10)
        box_platform.set_margin_end(10)
        box_platform.set_margin_top(5)
        box_platform.set_margin_bottom(5)

        self._check_hide_from_alt_tab = Gtk.CheckButton(label="Hide from Alt+Tab")
        self._check_hide_from_alt_tab.set_active(self._settings.hide_from_alt_tab)
        box_platform.pack_start(self._check_hide_from_alt_tab, False, False, 0)

        self._check_topmost_when_running = Gtk.CheckButton(label="Topmost when running")
        self._check_topmost_when_running.set_active(self._settings.topmost_when_running)
        box_platform.pack_start(self._check_topmost_when_running, False, False, 0)

        self._check_prevent_screen_burn = Gtk.CheckButton(label="Prevent screen burn")
        self._check_prevent_screen_burn.set_active(self._settings.prevent_screen_burn)
        box_platform.pack_start(self._check_prevent_screen_burn, False, False, 0)

        self._check_show_move_status = Gtk.CheckButton(label="Show move mouse status")
        self._check_show_move_status.set_active(self._settings.show_move_mouse_status)
        box_platform.pack_start(self._check_show_move_status, False, False, 0)

        self._check_disable_animation = Gtk.CheckButton(label="Disable button animation")
        self._check_disable_animation.set_active(self._settings.disable_button_animation)
        box_platform.pack_start(self._check_disable_animation, False, False, 0)

        self._check_pause_on_battery = Gtk.CheckButton(label="Pause on battery")
        self._check_pause_on_battery.set_active(self._settings.pause_on_battery)
        box_platform.pack_start(self._check_pause_on_battery, False, False, 0)

        self._check_launch_at_logon = Gtk.CheckButton(label="Launch at logon")
        self._check_launch_at_logon.set_active(self._settings.launch_at_logon)
        box_platform.pack_start(self._check_launch_at_logon, False, False, 0)

        frame_platform.add(box_platform)
        container.pack_start(frame_platform, False, False, 0)

        return container

    def _on_toggle_random_interval(self, check: Gtk.CheckButton) -> None:
        """Toggle the upper interval spin sensitivity."""
        self._spin_upper_interval.set_sensitive(check.get_active())

    # ------------------------------------------------------------------
    # Tab: Actions
    # ------------------------------------------------------------------

    def _create_actions_tab(self) -> Gtk.Widget:
        """Create the Actions configuration tab."""
        main_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_container.set_margin_start(10)
        main_container.set_margin_end(10)
        main_container.set_margin_top(10)
        main_container.set_margin_bottom(10)

        # Left panel: action list
        left_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        left_panel.set_size_request(250, -1)

        # TreeView for actions (Name, Type, Enabled)
        store = Gtk.ListStore(str, str, bool)  # name, type, enabled
        for action in self._actions:
            store.append([
                action.get("name", "Unnamed"),
                action.get("type", "move_mouse"),
                action.get("enabled", True),
            ])
        self._actions_store = store

        treeview = Gtk.TreeView(model=store)

        col_name = Gtk.TreeViewColumn("Name", Gtk.CellRendererText(), text=0)
        treeview.append_column(col_name)

        col_type = Gtk.TreeViewColumn("Type", Gtk.CellRendererText(), text=1)
        treeview.append_column(col_type)

        col_enabled = Gtk.TreeViewColumn("Enabled", Gtk.CellRendererToggle(), active=2)
        treeview.append_column(col_enabled)

        self._action_selection = treeview.get_selection()
        self._action_selection.connect("changed", self._on_action_selection_changed)

        scroll = Gtk.ScrolledWindow()
        scroll.add(treeview)
        scroll.set_size_request(-1, 200)
        left_panel.pack_start(scroll, True, True, 0)

        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        # Add button with action type dropdown
        self._action_type_combo = Gtk.ComboBoxText()
        for label, _ in ACTION_TYPES:
            self._action_type_combo.append_text(label)
        self._action_type_combo.set_active(0)
        button_box.pack_start(self._action_type_combo, False, False, 0)

        btn_add = Gtk.Button(label="Add")
        btn_add.connect("clicked", self._on_add_action)
        button_box.pack_start(btn_add, False, False, 0)

        btn_remove = Gtk.Button(label="Remove")
        btn_remove.connect("clicked", self._on_remove_action)
        button_box.pack_start(btn_remove, False, False, 0)

        btn_up = Gtk.Button(label="Up")
        btn_up.connect("clicked", self._on_move_action_up)
        button_box.pack_start(btn_up, False, False, 0)

        btn_down = Gtk.Button(label="Down")
        btn_down.connect("clicked", self._on_move_action_down)
        button_box.pack_start(btn_down, False, False, 0)

        left_panel.pack_start(button_box, False, False, 0)
        main_container.pack_start(left_panel, False, False, 0)

        # Right panel: action editor
        right_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        right_panel.set_size_request(350, -1)

        self._action_editor = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self._action_editor.set_margin_start(5)
        self._action_editor.set_margin_end(5)
        self._action_editor.set_margin_top(5)
        self._action_editor.set_margin_bottom(5)

        scroll_editor = Gtk.ScrolledWindow()
        scroll_editor.add(self._action_editor)
        right_panel.pack_start(scroll_editor, True, True, 0)

        main_container.pack_start(right_panel, True, True, 0)

        return main_container

    def _on_action_selection_changed(self, selection: Gtk.TreeSelection) -> None:
        """Show editor for the selected action."""
        model, iter_ = selection.get_selected()
        if iter_ is None:
            return

        # Save current editor before switching
        self._save_action_editor()

        index = model.get_path(iter_).get_indices()[0]
        if index < len(self._actions):
            self._current_action_index = index
            self._show_action_editor(self._actions[index])

    def _show_action_editor(self, action: Dict[str, Any]) -> None:
        """Clear and rebuild the editor for the given action."""
        for child in self._action_editor.get_children():
            self._action_editor.remove(child)

        action_type = action.get("type", "move_mouse")

        if action_type == "move_mouse":
            self._editor_move_cursor(action)
        elif action_type == "click_mouse":
            self._editor_click(action)
        elif action_type == "position_cursor":
            self._editor_position(action)
        elif action_type == "scroll_mouse":
            self._editor_scroll(action)
        elif action_type == "sleep":
            self._editor_sleep(action)

        self._action_editor.show_all()

    def _save_action_editor(self) -> None:
        """Save current editor widget values back to the active action."""
        if self._current_action_index is None:
            return
        if self._current_action_index >= len(self._actions):
            return

        action = self._actions[self._current_action_index]
        self._read_editor_widgets(self._action_editor, action)
        logger.debug("Action editor saved for index %d", self._current_action_index)

    def _read_editor_widgets(
        self, container: Gtk.Container, action: Dict[str, Any]
    ) -> None:
        """Recursively read widget values from the editor into the action dict."""
        for child in container.get_children():
            widget_id = getattr(child, "_widget_id", None)
            if widget_id is not None:
                if isinstance(child, Gtk.ComboBoxText):
                    active_id = child.get_active_id()
                    if active_id is not None:
                        action[widget_id] = active_id
                elif isinstance(child, Gtk.SpinButton):
                    action[widget_id] = child.get_value()
                elif isinstance(child, Gtk.CheckButton):
                    action[widget_id] = child.get_active()
                elif isinstance(child, Gtk.Entry):
                    action[widget_id] = child.get_text()
            # Recurse into frames and boxes that may contain widgets
            if isinstance(child, (Gtk.Frame, Gtk.Box)):
                self._read_editor_widgets(child, action)

    def _editor_move_cursor(self, action: Dict[str, Any]) -> None:
        """Editor for move cursor action."""
        self._action_editor.pack_start(
            Gtk.Label(label="Move Cursor", xalign=0), False, False, 0
        )

        # Direction
        box_dir = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        box_dir.pack_start(Gtk.Label(label="Direction:"), False, False, 0)
        combo_dir = Gtk.ComboBoxText()
        for d in CursorDirection:
            combo_dir.append(d.value, d.value.replace("_", " ").title())
        current_dir = action.get("direction", "square")
        combo_dir.set_active_id(current_dir)
        combo_dir._widget_id = "direction"
        box_dir.pack_start(combo_dir, True, True, 0)
        self._action_editor.pack_start(box_dir, False, False, 0)

        # Distance
        box_dist = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        box_dist.pack_start(Gtk.Label(label="Distance:"), False, False, 0)
        spin_dist = Gtk.SpinButton.new_with_range(1, 500, 1)
        spin_dist.set_value(action.get("distance", 5))
        spin_dist._widget_id = "distance"
        box_dist.pack_start(spin_dist, True, True, 0)
        self._action_editor.pack_start(box_dist, False, False, 0)

        # Random distance
        box_random = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        check_random = Gtk.CheckButton(label="Random distance")
        check_random.set_active(action.get("random", False))
        check_random._widget_id = "random"
        box_random.pack_start(check_random, False, False, 0)
        box_random.pack_start(Gtk.Label(label="Upper:"), False, False, 0)
        spin_upper = Gtk.SpinButton.new_with_range(1, 500, 1)
        spin_upper.set_value(action.get("upper_distance", 20))
        spin_upper._widget_id = "upper_distance"
        spin_upper.set_sensitive(action.get("random", False))
        check_random.connect("toggled", lambda c: spin_upper.set_sensitive(c.get_active()))
        box_random.pack_start(spin_upper, True, True, 0)
        self._action_editor.pack_start(box_random, False, False, 0)

        # Speed
        box_speed = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        box_speed.pack_start(Gtk.Label(label="Speed:"), False, False, 0)
        combo_speed = Gtk.ComboBoxText()
        for s in CursorSpeed:
            combo_speed.append(s.value, s.value.title())
        combo_speed.set_active_id(action.get("speed", "normal"))
        combo_speed._widget_id = "speed"
        box_speed.pack_start(combo_speed, True, True, 0)
        self._action_editor.pack_start(box_speed, False, False, 0)

        # Abort on user activity
        check_abort = Gtk.CheckButton(label="Abort on user activity")
        check_abort.set_active(action.get("abort_if_user_activity", True))
        check_abort._widget_id = "abort_if_user_activity"
        self._action_editor.pack_start(check_abort, False, False, 0)

        # Repeat mode
        box_repeat = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        combo_repeat = Gtk.ComboBoxText()
        combo_repeat.append("forever", "Repeat forever")
        combo_repeat.append("throttle", "Throttle")
        combo_repeat.set_active_id(action.get("repeat_mode", "forever"))
        combo_repeat._widget_id = "repeat_mode"
        box_repeat.pack_start(Gtk.Label(label="Repeat:"), False, False, 0)
        box_repeat.pack_start(combo_repeat, True, True, 0)
        self._action_editor.pack_start(box_repeat, False, False, 0)

        # Throttle count
        box_throttle = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        box_throttle.pack_start(Gtk.Label(label="Throttle count:"), False, False, 0)
        spin_throttle = Gtk.SpinButton.new_with_range(1, 100, 1)
        spin_throttle.set_value(action.get("interval_execution_count", 1))
        spin_throttle._widget_id = "interval_execution_count"
        box_throttle.pack_start(spin_throttle, True, True, 0)
        self._action_editor.pack_start(box_throttle, False, False, 0)

    def _editor_click(self, action: Dict[str, Any]) -> None:
        """Editor for click action."""
        self._action_editor.pack_start(
            Gtk.Label(label="Mouse Click", xalign=0), False, False, 0
        )

        # Button
        box_btn = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        box_btn.pack_start(Gtk.Label(label="Button:"), False, False, 0)
        combo_btn = Gtk.ComboBoxText()
        combo_btn.append("1", "Left")
        combo_btn.append("2", "Middle")
        combo_btn.append("3", "Right")
        combo_btn.set_active_id(str(action.get("button", 1)))
        combo_btn._widget_id = "button"
        box_btn.pack_start(combo_btn, True, True, 0)
        self._action_editor.pack_start(box_btn, False, False, 0)

        # Hold ms
        box_hold = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        box_hold.pack_start(Gtk.Label(label="Hold (ms):"), False, False, 0)
        spin_hold = Gtk.SpinButton.new_with_range(0, 5000, 10)
        spin_hold.set_value(action.get("hold_ms", 50))
        spin_hold._widget_id = "hold_ms"
        box_hold.pack_start(spin_hold, True, True, 0)
        self._action_editor.pack_start(box_hold, False, False, 0)

    def _editor_position(self, action: Dict[str, Any]) -> None:
        """Editor for absolute position action."""
        self._action_editor.pack_start(
            Gtk.Label(label="Position Cursor", xalign=0), False, False, 0
        )

        box_xy = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        box_xy.pack_start(Gtk.Label(label="X:"), False, False, 0)
        spin_x = Gtk.SpinButton.new_with_range(0, 7680, 1)
        spin_x.set_value(action.get("x", 0))
        spin_x._widget_id = "x"
        box_xy.pack_start(spin_x, True, True, 0)

        box_xy.pack_start(Gtk.Label(label="Y:"), False, False, 0)
        spin_y = Gtk.SpinButton.new_with_range(0, 4320, 1)
        spin_y.set_value(action.get("y", 0))
        spin_y._widget_id = "y"
        box_xy.pack_start(spin_y, True, True, 0)

        self._action_editor.pack_start(box_xy, False, False, 0)

        btn_capture = Gtk.Button(label="Capture Position")
        btn_capture.connect("clicked", self._on_capture_position, spin_x, spin_y)
        self._action_editor.pack_start(btn_capture, False, False, 0)

    def _on_capture_position(
        self, _btn: Gtk.Button, spin_x: Gtk.SpinButton, spin_y: Gtk.SpinButton
    ) -> None:
        """Capture the current cursor position."""
        try:
            from move_mouse.mouse_controller import MouseController
            ctrl = MouseController()
            if ctrl.available:
                x, y = ctrl.get_position()
                spin_x.set_value(x)
                spin_y.set_value(y)
                logger.info("Position captured: (%d, %d)", x, y)
        except Exception as exc:
            logger.warning("Could not capture position: %s", exc)

    def _editor_scroll(self, action: Dict[str, Any]) -> None:
        """Editor for scroll action."""
        self._action_editor.pack_start(
            Gtk.Label(label="Mouse Scroll", xalign=0), False, False, 0
        )

        box_dir = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        box_dir.pack_start(Gtk.Label(label="Direction:"), False, False, 0)
        combo_dir = Gtk.ComboBoxText()
        combo_dir.append("up", "Up")
        combo_dir.append("down", "Down")
        combo_dir.set_active_id(action.get("scroll_direction", "up"))
        combo_dir._widget_id = "scroll_direction"
        box_dir.pack_start(combo_dir, True, True, 0)
        self._action_editor.pack_start(box_dir, False, False, 0)

        box_amt = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        box_amt.pack_start(Gtk.Label(label="Amount:"), False, False, 0)
        spin_amt = Gtk.SpinButton.new_with_range(1, 100, 1)
        spin_amt.set_value(action.get("scroll_amount", 1))
        spin_amt._widget_id = "scroll_amount"
        box_amt.pack_start(spin_amt, True, True, 0)
        self._action_editor.pack_start(box_amt, False, False, 0)

    def _editor_sleep(self, action: Dict[str, Any]) -> None:
        """Editor for sleep action."""
        self._action_editor.pack_start(
            Gtk.Label(label="Sleep", xalign=0), False, False, 0
        )

        box_dur = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        box_dur.pack_start(Gtk.Label(label="Duration (seconds):"), False, False, 0)
        spin_dur = Gtk.SpinButton.new_with_range(0.1, 3600, 0.1)
        spin_dur.set_value(action.get("duration_seconds", 1.0))
        spin_dur._widget_id = "duration_seconds"
        box_dur.pack_start(spin_dur, True, True, 0)
        self._action_editor.pack_start(box_dur, False, False, 0)

        box_random = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        check_random = Gtk.CheckButton(label="Random duration")
        check_random.set_active(action.get("random_duration", False))
        check_random._widget_id = "random_duration"
        box_random.pack_start(check_random, False, False, 0)
        box_random.pack_start(Gtk.Label(label="Upper (seconds):"), False, False, 0)
        spin_upper = Gtk.SpinButton.new_with_range(0.1, 3600, 0.1)
        spin_upper.set_value(action.get("upper_duration_seconds", 5.0))
        spin_upper._widget_id = "upper_duration_seconds"
        spin_upper.set_sensitive(action.get("random_duration", False))
        check_random.connect("toggled", lambda c: spin_upper.set_sensitive(c.get_active()))
        box_random.pack_start(spin_upper, True, True, 0)
        self._action_editor.pack_start(box_random, False, False, 0)

    # ------------------------------------------------------------------
    # Action list operations
    # ------------------------------------------------------------------

    def _on_add_action(self, _btn: Gtk.Button) -> None:
        """Add a new action of the selected type."""
        # Save current editor before adding
        self._save_action_editor()

        type_index = self._action_type_combo.get_active()
        if type_index < 0 or type_index >= len(ACTION_TYPES):
            return

        label, action_type = ACTION_TYPES[type_index]
        new_action: Dict[str, Any] = {"type": action_type, "name": label, "enabled": True}

        # Defaults per type
        if action_type == "move_mouse":
            new_action.update({
                "direction": "square",
                "distance": 5,
                "upper_distance": 20,
                "random": False,
                "speed": "normal",
                "abort_if_user_activity": True,
                "repeat_mode": "forever",
                "interval_execution_count": 1,
            })
        elif action_type == "click_mouse":
            new_action.update({
                "button": 1,
                "hold_ms": 50,
            })
        elif action_type == "position_cursor":
            new_action.update({
                "x": 0,
                "y": 0,
            })
        elif action_type == "scroll_mouse":
            new_action.update({
                "scroll_direction": "up",
                "scroll_amount": 1,
            })
        elif action_type == "sleep":
            new_action.update({
                "duration_seconds": 1.0,
                "upper_duration_seconds": 5.0,
                "random_duration": False,
            })

        self._actions.append(new_action)
        self._actions_store.append([label, action_type, True])
        logger.info("Action added: %s (%s)", label, action_type)

        # Select the newly added action so its editor appears
        new_index = len(self._actions) - 1
        self._current_action_index = new_index
        path = Gtk.TreePath(new_index)
        self._action_selection.select_path(path)

    def _on_remove_action(self, _btn: Gtk.Button) -> None:
        """Remove the selected action from the list."""
        # Save before removing
        self._save_action_editor()

        model, iter_ = self._action_selection.get_selected()
        if iter_ is None:
            return

        index = model.get_path(iter_).get_indices()[0]
        name = model.get_value(iter_, 0)
        model.remove(iter_)
        if index < len(self._actions):
            self._actions.pop(index)
            logger.info("Action removed: %s", name)

        # Reset index tracking
        self._current_action_index = None

        # Clear editor
        for child in self._action_editor.get_children():
            self._action_editor.remove(child)

    def _on_move_action_up(self, _btn: Gtk.Button) -> None:
        """Move selected action up in the list."""
        # Save before moving
        self._save_action_editor()

        model, iter_ = self._action_selection.get_selected()
        if iter_ is None:
            return

        index = model.get_path(iter_).get_indices()[0]
        if index <= 0:
            return

        # Swap in list
        self._actions[index], self._actions[index - 1] = self._actions[index - 1], self._actions[index]

        # Swap in store
        row_a = model[index]
        row_b = model[index - 1]
        model.swap(row_a, row_b)

        # Update tracked index
        if self._current_action_index == index:
            self._current_action_index = index - 1
        elif self._current_action_index == index - 1:
            self._current_action_index = index

        # Re-select
        path = Gtk.TreePath(index - 1)
        self._action_selection.select_path(path)

    def _on_move_action_down(self, _btn: Gtk.Button) -> None:
        """Move selected action down in the list."""
        # Save before moving
        self._save_action_editor()

        model, iter_ = self._action_selection.get_selected()
        if iter_ is None:
            return

        index = model.get_path(iter_).get_indices()[0]
        if index >= len(self._actions) - 1:
            return

        # Swap in list
        self._actions[index], self._actions[index + 1] = self._actions[index + 1], self._actions[index]

        # Swap in store
        row_a = model[index]
        row_b = model[index + 1]
        model.swap(row_a, row_b)

        # Update tracked index
        if self._current_action_index == index:
            self._current_action_index = index + 1
        elif self._current_action_index == index + 1:
            self._current_action_index = index

        # Re-select
        path = Gtk.TreePath(index + 1)
        self._action_selection.select_path(path)

    # ------------------------------------------------------------------
    # Tab: Schedules
    # ------------------------------------------------------------------

    def _create_schedules_tab(self) -> Gtk.Widget:
        """Create the Schedules tab."""
        container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        container.set_margin_start(10)
        container.set_margin_end(10)
        container.set_margin_top(10)
        container.set_margin_bottom(10)

        # Left panel: schedule list
        left_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        left_panel.set_size_request(250, -1)

        store = Gtk.ListStore(str, str, str)  # name, cron, action
        for sched in self._schedules:
            store.append([
                sched.get("name", "Unnamed"),
                sched.get("cron", ""),
                sched.get("action", "start"),
            ])
        self._schedules_store = store

        treeview = Gtk.TreeView(model=store)
        col_name = Gtk.TreeViewColumn("Name", Gtk.CellRendererText(), text=0)
        treeview.append_column(col_name)
        col_cron = Gtk.TreeViewColumn("Cron", Gtk.CellRendererText(), text=1)
        treeview.append_column(col_cron)
        col_action = Gtk.TreeViewColumn("Action", Gtk.CellRendererText(), text=2)
        treeview.append_column(col_action)

        self._schedule_selection = treeview.get_selection()
        self._schedule_selection.connect("changed", self._on_schedule_selection_changed)

        scroll = Gtk.ScrolledWindow()
        scroll.add(treeview)
        scroll.set_size_request(-1, 200)
        left_panel.pack_start(scroll, True, True, 0)

        # Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        btn_add = Gtk.Button(label="Add")
        btn_add.connect("clicked", self._on_add_schedule)
        btn_box.pack_start(btn_add, False, False, 0)
        btn_remove = Gtk.Button(label="Remove")
        btn_remove.connect("clicked", self._on_remove_schedule)
        btn_box.pack_start(btn_remove, False, False, 0)
        left_panel.pack_start(btn_box, False, False, 0)

        container.pack_start(left_panel, False, False, 0)

        # Right panel: editor
        right_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        right_panel.set_size_request(350, -1)

        self._schedule_editor = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self._schedule_editor.set_margin_start(5)
        self._schedule_editor.set_margin_end(5)
        self._schedule_editor.set_margin_top(5)
        self._schedule_editor.set_margin_bottom(5)

        scroll_editor = Gtk.ScrolledWindow()
        scroll_editor.add(self._schedule_editor)
        right_panel.pack_start(scroll_editor, True, True, 0)

        container.pack_start(right_panel, True, True, 0)

        return container

    def _on_schedule_selection_changed(self, selection: Gtk.TreeSelection) -> None:
        """Show editor for selected schedule."""
        model, iter_ = selection.get_selected()
        if iter_ is None:
            return

        for child in self._schedule_editor.get_children():
            self._schedule_editor.remove(child)

        index = model.get_path(iter_).get_indices()[0]
        if index < len(self._schedules):
            sched = self._schedules[index]
            self._schedule_editor.pack_start(
                Gtk.Label(label="Schedule", xalign=0), False, False, 0
            )

            # Name
            box_name = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            box_name.pack_start(Gtk.Label(label="Name:"), False, False, 0)
            entry_name = Gtk.Entry()
            entry_name.set_text(sched.get("name", ""))
            entry_name._widget_id = "name"
            box_name.pack_start(entry_name, True, True, 0)
            self._schedule_editor.pack_start(box_name, False, False, 0)

            # Cron expression
            box_cron = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            box_cron.pack_start(Gtk.Label(label="Cron:"), False, False, 0)
            entry_cron = Gtk.Entry()
            entry_cron.set_text(sched.get("cron", ""))
            entry_cron._widget_id = "cron"
            box_cron.pack_start(entry_cron, True, True, 0)
            self._schedule_editor.pack_start(box_cron, False, False, 0)

            # Action
            box_action = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            box_action.pack_start(Gtk.Label(label="Action:"), False, False, 0)
            combo_action = Gtk.ComboBoxText()
            combo_action.append("start", "Start")
            combo_action.append("stop", "Stop")
            combo_action.set_active_id(sched.get("action", "start"))
            combo_action._widget_id = "action"
            box_action.pack_start(combo_action, True, True, 0)
            self._schedule_editor.pack_start(box_action, False, False, 0)

            self._schedule_editor.show_all()

    def _on_add_schedule(self, _btn: Gtk.Button) -> None:
        """Add a new schedule."""
        new_sched: Dict[str, Any] = {
            "name": "New Schedule",
            "cron": "0 9 * * *",
            "action": "start",
        }
        self._schedules.append(new_sched)
        self._schedules_store.append(["New Schedule", "0 9 * * *", "start"])
        logger.info("Schedule added")

    def _on_remove_schedule(self, _btn: Gtk.Button) -> None:
        """Remove the selected schedule."""
        model, iter_ = self._schedule_selection.get_selected()
        if iter_ is None:
            return

        index = model.get_path(iter_).get_indices()[0]
        model.remove(iter_)
        if index < len(self._schedules):
            self._schedules.pop(index)
            logger.info("Schedule removed")

        for child in self._schedule_editor.get_children():
            self._schedule_editor.remove(child)

    # ------------------------------------------------------------------
    # Tab: Blackouts
    # ------------------------------------------------------------------

    def _create_blackouts_tab(self) -> Gtk.Widget:
        """Create the Blackouts tab."""
        container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        container.set_margin_start(10)
        container.set_margin_end(10)
        container.set_margin_top(10)
        container.set_margin_bottom(10)

        # Left panel: blackout list
        left_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        left_panel.set_size_request(250, -1)

        store = Gtk.ListStore(str, str, str, str)  # name, days, time, duration
        for bo in self._blackouts:
            store.append([
                bo.get("name", "Unnamed"),
                bo.get("days", ""),
                bo.get("time", "00:00"),
                str(bo.get("duration_hours", 1)),
            ])
        self._blackouts_store = store

        treeview = Gtk.TreeView(model=store)
        col_name = Gtk.TreeViewColumn("Name", Gtk.CellRendererText(), text=0)
        treeview.append_column(col_name)
        col_days = Gtk.TreeViewColumn("Days", Gtk.CellRendererText(), text=1)
        treeview.append_column(col_days)
        col_time = Gtk.TreeViewColumn("Time", Gtk.CellRendererText(), text=2)
        treeview.append_column(col_time)
        col_dur = Gtk.TreeViewColumn("Duration", Gtk.CellRendererText(), text=3)
        treeview.append_column(col_dur)

        self._blackout_selection = treeview.get_selection()
        self._blackout_selection.connect("changed", self._on_blackout_selection_changed)

        scroll = Gtk.ScrolledWindow()
        scroll.add(treeview)
        scroll.set_size_request(-1, 200)
        left_panel.pack_start(scroll, True, True, 0)

        # Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        btn_add = Gtk.Button(label="Add")
        btn_add.connect("clicked", self._on_add_blackout)
        btn_box.pack_start(btn_add, False, False, 0)
        btn_remove = Gtk.Button(label="Remove")
        btn_remove.connect("clicked", self._on_remove_blackout)
        btn_box.pack_start(btn_remove, False, False, 0)
        left_panel.pack_start(btn_box, False, False, 0)

        container.pack_start(left_panel, False, False, 0)

        # Right panel: editor
        right_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        right_panel.set_size_request(350, -1)

        self._blackout_editor = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self._blackout_editor.set_margin_start(5)
        self._blackout_editor.set_margin_end(5)
        self._blackout_editor.set_margin_top(5)
        self._blackout_editor.set_margin_bottom(5)

        scroll_editor = Gtk.ScrolledWindow()
        scroll_editor.add(self._blackout_editor)
        right_panel.pack_start(scroll_editor, True, True, 0)

        container.pack_start(right_panel, True, True, 0)

        return container

    def _on_blackout_selection_changed(self, selection: Gtk.TreeSelection) -> None:
        """Show editor for selected blackout."""
        model, iter_ = selection.get_selected()
        if iter_ is None:
            return

        for child in self._blackout_editor.get_children():
            self._blackout_editor.remove(child)

        index = model.get_path(iter_).get_indices()[0]
        if index < len(self._blackouts):
            bo = self._blackouts[index]
            self._blackout_editor.pack_start(
                Gtk.Label(label="Blackout", xalign=0), False, False, 0
            )

            # Name
            box_name = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            box_name.pack_start(Gtk.Label(label="Name:"), False, False, 0)
            entry_name = Gtk.Entry()
            entry_name.set_text(bo.get("name", ""))
            entry_name._widget_id = "name"
            box_name.pack_start(entry_name, True, True, 0)
            self._blackout_editor.pack_start(box_name, False, False, 0)

            # Day checkboxes
            days_frame = Gtk.Frame(label="Days")
            days_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            days_box.set_margin_start(5)
            days_box.set_margin_end(5)
            days_box.set_margin_top(5)
            days_box.set_margin_bottom(5)
            day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            selected_days = bo.get("days", "")
            self._day_checks = []
            for i, label in enumerate(day_labels):
                cb = Gtk.CheckButton(label=label)
                cb.set_active(str(i) in selected_days.split(","))
                cb._widget_id = f"day_{i}"
                self._day_checks.append(cb)
                days_box.pack_start(cb, False, False, 0)
            days_frame.add(days_box)
            self._blackout_editor.pack_start(days_frame, False, False, 0)

            # Time
            box_time = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            box_time.pack_start(Gtk.Label(label="Time:"), False, False, 0)
            entry_time = Gtk.Entry()
            entry_time.set_text(bo.get("time", "00:00"))
            entry_time._widget_id = "time"
            box_time.pack_start(entry_time, True, True, 0)
            self._blackout_editor.pack_start(box_time, False, False, 0)

            # Duration
            box_dur = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            box_dur.pack_start(Gtk.Label(label="Duration (hours):"), False, False, 0)
            spin_dur = Gtk.SpinButton.new_with_range(0.5, 24, 0.5)
            spin_dur.set_value(bo.get("duration_hours", 1))
            spin_dur._widget_id = "duration_hours"
            box_dur.pack_start(spin_dur, True, True, 0)
            self._blackout_editor.pack_start(box_dur, False, False, 0)

            self._blackout_editor.show_all()

    def _on_add_blackout(self, _btn: Gtk.Button) -> None:
        """Add a new blackout."""
        new_bo: Dict[str, Any] = {
            "name": "New Blackout",
            "days": "0,1,2,3,4",
            "time": "00:00",
            "duration_hours": 1,
        }
        self._blackouts.append(new_bo)
        self._blackouts_store.append(["New Blackout", "Mon-Fri", "00:00", "1"])
        logger.info("Blackout added")

    def _on_remove_blackout(self, _btn: Gtk.Button) -> None:
        """Remove the selected blackout."""
        model, iter_ = self._blackout_selection.get_selected()
        if iter_ is None:
            return

        index = model.get_path(iter_).get_indices()[0]
        model.remove(iter_)
        if index < len(self._blackouts):
            self._blackouts.pop(index)
            logger.info("Blackout removed")

        for child in self._blackout_editor.get_children():
            self._blackout_editor.remove(child)

    # ------------------------------------------------------------------
    # Tab: Logging
    # ------------------------------------------------------------------

    def _create_logging_tab(self) -> Gtk.Widget:
        """Create the Logging tab."""
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        container.set_margin_start(15)
        container.set_margin_end(15)
        container.set_margin_top(15)
        container.set_margin_bottom(15)

        # Enable logging
        self._check_enable_logging = Gtk.CheckButton(label="Enable logging")
        self._check_enable_logging.set_active(self._settings.enable_logging)
        container.pack_start(self._check_enable_logging, False, False, 0)

        # Log level
        box_level = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        box_level.pack_start(Gtk.Label(label="Log level:"), False, False, 0)
        self._combo_log_level = Gtk.ComboBoxText()
        for level in ("DEBUG", "INFO", "WARNING", "ERROR"):
            self._combo_log_level.append(level, level)
        self._combo_log_level.set_active_id(self._settings.log_level)
        self._combo_log_level._widget_id = "log_level"
        box_level.pack_start(self._combo_log_level, True, True, 0)
        container.pack_start(box_level, False, False, 0)

        return container

    # ------------------------------------------------------------------
    # Data collection
    # ------------------------------------------------------------------

    def _collect_general(self) -> Settings:
        """Collect values from the General tab."""
        lower = int(self._spin_lower_interval.get_value())
        upper = int(self._spin_upper_interval.get_value())
        random_interval = self._check_random_interval.get_active()

        return Settings(
            lower_interval=lower,
            upper_interval=upper if random_interval else lower,
            random_interval=random_interval,
            auto_pause=self._check_auto_pause.get_active(),
            auto_resume=self._check_auto_resume.get_active(),
            auto_resume_seconds=int(self._spin_auto_resume_seconds.get_value()),
            active_when_locked=self._check_active_when_locked.get_active(),
            minimise_on_stop=self._check_minimise_on_stop.get_active(),
            start_at_launch=self._check_start_at_launch.get_active(),
            hide_from_taskbar=self._check_hide_from_taskbar.get_active(),
            hide_main_window=self._check_hide_main_window.get_active(),
            hide_system_tray_icon=self._check_hide_system_tray_icon.get_active(),
            show_system_tray_notifications=self._check_show_tray_notifications.get_active(),
            show_taskbar_status=self._check_show_taskbar_status.get_active(),
            hide_from_alt_tab=self._check_hide_from_alt_tab.get_active(),
            topmost_when_running=self._check_topmost_when_running.get_active(),
            prevent_screen_burn=self._check_prevent_screen_burn.get_active(),
            show_move_mouse_status=self._check_show_move_status.get_active(),
            disable_button_animation=self._check_disable_animation.get_active(),
            pause_on_battery=self._check_pause_on_battery.get_active(),
            launch_at_logon=self._check_launch_at_logon.get_active(),
            actions=list(self._actions),
            schedules=list(self._schedules),
            blackouts=list(self._blackouts),
            enable_logging=self._check_enable_logging.get_active(),
            log_level=self._combo_log_level.get_active_id(),
        )

    def get_settings(self) -> Settings:
        """Return the complete settings from the dialog."""
        # Save any pending editor changes before collecting
        self._save_action_editor()
        return self._collect_general()
