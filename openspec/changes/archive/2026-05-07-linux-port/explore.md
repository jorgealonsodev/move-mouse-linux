# Exploration: Linux Port of Move Mouse

## Current State

The original "Move Mouse" is a WPF .NET Framework app for Windows that simulates user activity to prevent screen lock/sleep. It has a rich feature set built around:

- **Actions pipeline**: 8 action types (MoveMouseCursor, PositionMouseCursor, ClickMouse, Keystroke, Sleep, Script, Command, ActivateApplication, ScrollMouse)
- **Interval execution**: Configurable lower/upper interval with optional randomization, repeat modes (forever/throttle)
- **Auto-pause/resume**: Detects user activity via `GetLastInputInfo` (user32.dll), pauses on input, resumes after configurable idle seconds
- **Schedules**: Cron-based start/stop via Quartz.NET (SimpleSchedule with day-pickers, AdvancedSchedule with raw cron)
- **Blackouts**: Day/time windows where movement is suppressed
- **System tray**: Minimizes to tray with notifications
- **Settings**: XML serialization to `%AppData%`, nullable defaults
- **Volume control**: Adjusts system volume when running
- **Battery detection**: Pauses when on battery power
- **Screen burn prevention**: Randomizes movement patterns

### Current Linux Port State

Only `move_mouse/mouse_controller.py` exists with:
- X11 backend via python-xlib + XTest
- Wayland fallback via ydotool subprocess
- All 15 cursor directions implemented (matching original)
- Speed presets (slow/normal/fast) with ms delays
- Basic user activity detection (cursor position comparison)
- No settings persistence, no UI, no tray, no scheduler, no actions pipeline

## Feature Parity Analysis

### V1 Scope (MVP - Core Functionality)

| Feature | Original | Linux V1 | Rationale |
|---------|----------|----------|-----------|
| MoveMouseCursor action | 15 directions | **Already done** | Core feature, implemented |
| ClickMouse action | Left/Middle/Right + hold | **Include** | Simple, XTest supports it |
| Sleep action | Fixed/random delay | **Include** | Trivial, just `time.sleep` |
| Interval execution | Lower/Upper + random | **Include** | Core engine feature |
| Auto-pause | GetLastInputInfo | **Include** | Essential UX, XScreenSaver/D-Bus |
| Auto-resume | Configurable seconds | **Include** | Pairs with auto-pause |
| Settings persistence | XML in %AppData% | **Include** | JSON in ~/.config |
| System tray icon | WinForms NotifyIcon | **Include** | AppIndicator3 |
| Start/Stop control | UI button + tray | **Include** | Minimal GTK window |
| ScrollMouse action | Vertical + horizontal | **Include** | XTest supports wheel events |

### V2 Scope (Advanced Features)

| Feature | Original | Linux V2 | Rationale |
|---------|----------|----------|-----------|
| Keystroke action | Sequential/simultaneous key codes | **Defer** | Needs Linux keycode mapping (evdev/XKB) |
| Command action | Execute arbitrary binary | **Defer** | Security considerations, subprocess |
| Script action | PowerShell .ps1 execution | **Defer** | Windows-specific, replace with bash/python |
| ActivateApplication action | FindWindow + AppActivate | **Defer** | Needs wmctrl/xdotool/X11 window list |
| PositionMouseCursor action | Absolute positioning | **V1-ready** | Already supported by backend |
| Schedules (cron) | Quartz.NET | **Defer** | APScheduler is heavy for V1 |
| Blackouts | Day/time suppression | **Defer** | Can use cron-like logic later |
| Volume control | CoreAudio API | **Defer** | Needs PulseAudio/PipeWire D-Bus |
| Battery detection | WMI/SysPower | **Defer** | /sys/class/power_supply is simple but edge cases |
| Screen burn prevention | Overlay transparency | **Defer** | Nice-to-have |
| Taskbar status | Win32 taskbar progress | **Skip** | Windows-specific |

### Skip Entirely

| Feature | Reason |
|---------|--------|
| HideFromAltTab (WS_EX_TOOLWINDOW) | X11 `_NET_WM_STATE_SKIP_TASKBAR` works differently |
| OverrideIcon at runtime | Linux themes handle this |
| HookKey (global hotkey) | Commented out in original, not used |
| ReactivatePreviousWindow | Commented out in original |
| LogPath customization | Use standard logging to journal |

## Linux API Equivalents

### Windows API → Linux Mapping

| Windows API | Purpose | Linux Equivalent | Notes |
|-------------|---------|-----------------|-------|
| `user32.SendInput` | Mouse/keyboard input | X11: `XTestFakeMotionEvent` + `XTestFakeButtonEvent` | Already in mouse_controller |
| `user32.SetCursorPos` | Absolute cursor position | X11: `XTestFakeMotionEvent` with absolute coords | Already in mouse_controller |
| `user32.GetCursorPos` | Read cursor position | X11: `XQueryPointer` on root window | Already in mouse_controller |
| `user32.GetLastInputInfo` | Idle time detection | X11: `XScreenSaverQueryInfo` | Most reliable on X11 |
| `user32.GetLastInputInfo` | Idle time detection | Wayland: `org.freedesktop.ScreenSaver.GetSessionIdleTime` | D-Bus call, not universal |
| `user32.mouse_event` | Click/wheel simulation | X11: `XTestFakeButtonEvent` | Already partially in mouse_controller |
| `user32.keybd_event` | Keyboard simulation | X11: `XTestFakeKeyEvent` / Wayland: ydotool | Need keycode mapping |
| Registry / %AppData% | Settings storage | `~/.config/move-mouse-linux/settings.json` | Standard XDG location |
| `SystemEvents.SessionSwitch` | Lock/unlock detection | D-Bus: `org.freedesktop.login1.Session.Lock` / `Unlock` | systemd-logind |
| `SystemEvents.PowerModeChanged` | Suspend/resume | D-Bus: `org.freedesktop.login1.Manager.PrepareForSleep` | systemd-logind |
| `NotifyIcon` | System tray | `gi.repository.AppIndicator3` or `gi.repository.Gtk.StatusIcon` | AppIndicator3 preferred |
| WMI BatteryQueryInformation | Battery status | `/sys/class/power_supply/BAT0/status` | Read file, parse text |
| CoreAudio API | Volume control | PulseAudio: `pulsectl` / PipeWire: D-Bus | Library dependency |
| Quartz.NET | Cron scheduling | `apscheduler` or `croniter` + threading | Python libraries |

## Recommended Python Libraries

### Core Dependencies

| Library | Purpose | Rationale |
|---------|---------|-----------|
| `python-xlib` | X11 mouse/keyboard control | Already used, mature, well-documented |
| `PyGObject` (gi) | GTK 3 + AppIndicator3 | Standard Linux desktop integration |
| `pydbus` or `dbus-python` | D-Bus communication | Idle detection, session lock, systemd |
| `pyxdg` | XDG config paths | Standard `~/.config` location |

### Optional (V2)

| Library | Purpose | Rationale |
|---------|---------|-----------|
| `pulsectl` | PulseAudio volume control | Simple Python wrapper |
| `apscheduler` | Cron-like scheduling | Quartz.NET equivalent |
| `croniter` | Cron expression parsing | For AdvancedSchedule |
| `evdev` | Linux input event codes | For KeystrokeAction keycode mapping |

### Not Recommended

| Library | Why Not |
|---------|---------|
| `pynput` | Doesn't work well under Wayland, conflicts with XTest |
| `pyautogui` | Too high-level, doesn't expose fine-grained control |
| `xdotool` subprocess | Slower than direct Xlib, but usable as fallback |
| `ydotool` for X11 | Overkill when XTest works natively |

## Architecture Approach

### Module Structure

```
move_mouse/
├── __init__.py              # Package init, version
├── __main__.py              # Entry point (CLI + GTK main loop)
├── core/
│   ├── engine.py            # Main state machine (idle/running/paused)
│   ├── executor.py          # Action pipeline executor with interval timer
│   └── idle_detector.py     # Abstract idle detection (X11/Wayland)
├── actions/
│   ├── base.py              # ActionBase abstract class
│   ├── move_cursor.py       # MoveMouseCursor (already in mouse_controller)
│   ├── click_mouse.py       # ClickMouse (left/middle/right + hold)
│   ├── scroll_mouse.py      # ScrollMouse (vertical/horizontal wheel)
│   ├── sleep.py             # Sleep (fixed/random delay)
│   └── position_cursor.py   # PositionMouseCursor (absolute)
├── backends/
│   ├── mouse_backend.py     # Abstract MouseBackend interface
│   ├── x11_backend.py       # python-xlib + XTest (primary)
│   └── wayland_backend.py   # ydotool subprocess (fallback)
├── settings/
│   ├── model.py             # Settings dataclass with defaults
│   ├── store.py             # JSON load/save from ~/.config
│   └── migration.py         # Future: import from Windows XML
├── ui/
│   ├── app.py               # GTK Application + window
│   ├── tray.py              # AppIndicator3 system tray
│   └── widgets/             # GTK widgets for settings panels
├── services/
│   ├── session_monitor.py   # D-Bus: lock/unlock, suspend/resume
│   ├── battery_monitor.py   # /sys/class/power_supply polling
│   └── scheduler.py         # V2: cron-based start/stop
└── utils/
    ├── logger.py            # Logging setup
    └── constants.py         # App ID, paths, defaults
```

### State Machine

```
                    ┌──────────┐
                    │  IDLE    │ ← Start state, Stop action
                    └────┬─────┘
                         │ Start action / Schedule trigger
                    ┌────▼─────┐
              ┌─────│ RUNNING  │─────┐
              │     └────┬─────┘     │
              │          │           │
    Blackout  │     User active      │ Auto-resume
    active    │     + AutoPause      │ timeout
              │     ┌────▼─────┐     │
              │     │  PAUSED  │     │
              │     └──────────┘     │
              │                      │
              └──────────────────────┘
```

### Data Flow

1. **Settings** loaded from JSON → `SettingsModel`
2. **Engine** initialized with settings, backends auto-detected
3. **UI** (GTK window + tray) starts, connects to engine signals
4. **Executor** runs on interval timer, dispatches actions from pipeline
5. **IdleDetector** polls in background, signals engine on user activity
6. **SessionMonitor** listens to D-Bus for lock/unlock/suspend events
7. **Settings** saved on change, auto-saved periodically

## Risk Assessment

### HIGH RISK

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Wayland compatibility** | ydotool requires root or uinput access; may not work on all distros | Default to X11; document Wayland limitations; consider `wlrctl` for wlroots compositors |
| **Flatpak sandboxing** | X11 socket access needed; ydotool impossible inside Flatpak without `--device=all` | Use `--socket=x11` for X11; Wayland support requires host-side daemon |
| **AppIndicator3 deprecation** | Ubuntu/Debian moving to GTK StatusNotifierItem | Support both AppIndicator3 and `Gtk.StatusIcon` fallback |

### MEDIUM RISK

| Risk | Impact | Mitigation |
|------|--------|------------|
| **XScreenSaver extension not available** | Some minimal X11 setups lack it | Fallback to D-Bus `org.freedesktop.ScreenSaver` |
| **D-Bus ScreenSaver not implemented** | Some Wayland compositors don't expose idle time | Poll `/sys/class/input/` events as last resort |
| **python-xlib thread safety** | Xlib display objects are not thread-safe | Use single-threaded GTK main loop, or lock per-display |
| **Battery detection paths vary** | Not all systems use `BAT0` | Enumerate `/sys/class/power_supply/`, find type=Battery |

### LOW RISK

| Risk | Impact | Mitigation |
|------|--------|------------|
| **JSON settings corruption** | Rare but possible on crash | Write to temp file, atomic rename |
| **GTK theme inconsistencies** | App looks different across DEs | Use standard GTK widgets, no custom CSS |
| **Cron expression validation** | APScheduler vs Quartz syntax differs | Use `croniter` for validation, document differences |

## Flatpak Permissions

```json
{
  "finish-args": [
    "--socket=x11",
    "--socket=wayland",
    "--share=ipc",
    "--talk-name=org.freedesktop.ScreenSaver",
    "--talk-name=org.freedesktop.login1",
    "--talk-name=org.freedesktop.Notifications",
    "--filesystem=xdg-config/move-mouse-linux:create"
  ]
}
```

**Wayland note**: ydotool CANNOT work inside Flatpak without `--device=all`, which defeats sandboxing. Recommend documenting that Wayland users run the .deb version or use the X11 backend.

## Recommended v1 Scope Summary

**MUST HAVE (v1):**
1. Mouse movement (all 15 directions) — ✅ Already done
2. Click mouse (left/middle/right)
3. Scroll mouse (vertical/horizontal)
4. Sleep action (fixed/random)
5. Interval execution engine (lower/upper + random)
6. Auto-pause/resume (XScreenSaver + D-Bus fallback)
7. Settings persistence (JSON in ~/.config)
8. GTK main window (start/stop + basic config)
9. System tray (AppIndicator3)
10. Session lock/unlock handling (D-Bus logind)

**NICE TO HAVE (v1 if time permits):**
- PositionMouseCursor (absolute positioning)
- Battery detection (pause on battery)
- Logging to journal

**DEFER TO V2:**
- Keystroke action
- Command/Script actions
- ActivateApplication action
- Schedules (cron)
- Blackouts
- Volume control

## Recommended Approach

1. **Start with the engine**: Build the state machine + interval executor first
2. **Add actions incrementally**: Click → Scroll → Sleep (each is a work unit)
3. **Settings model early**: Define the JSON schema before the UI
4. **GTK window minimal**: Start/stop button + status label, expand later
5. **Tray last**: Window works first, tray is polish
6. **X11 first, Wayland later**: Get X11 working perfectly, then add ydotool fallback
