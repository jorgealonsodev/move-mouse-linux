# Linux Port — Delta Specification

## Core Engine

### Requirement: State Machine

The system SHALL maintain engine state as one of: `Idle`, `Running`, `Paused`, `Executing`, `Sleeping`.

| Transition | Trigger |
|---|---|
| Idle→Running | User starts / schedule trigger |
| Running→Paused | User pauses / auto-pause on activity |
| Running→Executing | Interval fires, action dispatch begins |
| Executing→Running | Action completes, next interval starts |
| Executing→Sleeping | Sleep action encountered |
| Sleeping→Running | Sleep timer expires |
| Running→Idle | User stops |
| Paused→Running | User resumes / auto-resume after idle timeout |
| Paused→Idle | User stops |

The system MUST reject invalid transitions. State changes MUST emit signals observable by UI.

#### Scenario: Start from idle
- GIVEN engine is Idle
- WHEN user presses start
- THEN engine transitions to Running and emits state-changed signal

#### Scenario: Invalid stop from idle
- GIVEN engine is Idle
- WHEN stop is requested
- THEN state remains Idle, no error raised

#### Scenario: Auto-pause interrupt
- GIVEN engine is Running
- WHEN idle detector signals user activity
- THEN engine transitions to Paused and notifies UI

### Requirement: Interval Timer

The system MUST execute the action list at a configurable interval. Interval SHALL be randomized between `lower_ms` and `upper_ms` when both are set. When only `lower_ms` is set, interval is fixed. Timer MUST use GLib `timeout_add` on the GTK main loop (no threads). Timer MUST be cancelled on state transition to Idle or Paused.

#### Scenario: Fixed interval
- GIVEN lower_ms=5000, upper_ms=None
- WHEN engine is Running
- THEN actions execute every 5000ms ±0

#### Scenario: Randomized interval
- GIVEN lower_ms=3000, upper_ms=7000
- WHEN engine is Running
- THEN each interval is a random value in [3000,7000]

### Requirement: Action Dispatcher

The system SHALL iterate the action list sequentially each interval tick. Each action produces a side-effect via its backend. If any action fails, the system SHALL log the error and continue with the next action. The dispatcher MUST complete all actions before the next interval tick begins.

#### Scenario: Action list with failure
- GIVEN action list [Move, Click, Sleep]
- WHEN Click fails (backend error)
- THEN Move result preserved, Sleep still executes, error logged

---

## Mouse Actions

### Requirement: Move Cursor

The system SHALL support all 15 `CursorDirection` values (square, none, random, N/NE/E/SE/S/SW/W/NW, up-down, down-up, left-right, right-left). Move MUST accept `distance` (px) and `speed` preset (slow/normal/fast/custom with delay_ms). Random distance MUST be supported between `distance` and `upper_distance`.

#### Scenario: Square pattern
- GIVEN direction=SQUARE, distance=5
- WHEN move executes
- THEN cursor traces east→south→west→north (5px each side)

#### Scenario: Random distance
- GIVEN direction=NORTH, distance=3, upper_distance=10, random_distance=True
- WHEN move executes
- THEN actual distance is randint(3,10)

### Requirement: Click Mouse

The system SHALL simulate left (button=1), middle (2), and right (3) clicks. Click MUST press then release with a configurable hold duration (default 50ms).

#### Scenario: Right click
- GIVEN button=3, hold_ms=50
- WHEN click executes
- THEN XTest ButtonPress(3) → 50ms delay → ButtonRelease(3)

### Requirement: Sleep Action

The system SHALL pause execution for `duration_ms`. When `random_duration` is enabled, actual duration SHALL be randint(`duration_ms`, `upper_duration_ms`). During sleep, the engine state MUST be `Sleeping`.

#### Scenario: Random sleep
- GIVEN duration_ms=2000, upper_duration_ms=5000, random=True
- WHEN sleep executes
- THEN engine enters Sleeping for randint(2000,5000)ms, then returns to Running

### Requirement: Position Cursor

The system SHALL move the cursor to absolute (x,y) coordinates. MUST work on X11 via `XTestFakeMotionEvent(relative=False)`. On Wayland via `ydotool --absolute`.

#### Scenario: Absolute position
- GIVEN x=100, y=200
- WHEN position executes
- THEN cursor moves to screen coordinate (100,200)

---

## Auto-Pause/Resume

### Requirement: User Activity Detection

The system SHALL detect user input (mouse move, key press) via XScreenSaver `idle` timer (X11 primary). If XScreenSaver is unavailable, MUST fall back to D-Bus `org.freedesktop.ScreenSaver.GetSessionIdleTime`. Idle time polling interval SHALL be configurable (default 1000ms).

#### Scenario: XScreenSaver detects activity
- GIVEN XScreenSaver available, auto-pause enabled, idle_threshold=3000ms
- WHEN user moves mouse (idle reset to 0)
- THEN engine transitions to Paused

#### Scenario: XScreenSaver missing
- GIVEN XScreenSaver unavailable
- WHEN engine starts
- THEN D-Bus fallback is used automatically, warning logged

### Requirement: Auto-Pause

When auto-pause is enabled and user idle time drops below threshold (user became active), engine MUST transition from Running to Paused. Auto-pause MUST NOT trigger when engine is Idle or already Paused.

#### Scenario: Pause on user activity
- GIVEN engine Running, auto-pause enabled, idle_threshold=3000ms
- WHEN user presses a key (idle < threshold)
- THEN engine transitions to Paused within 1 polling cycle

### Requirement: Auto-Resume

When auto-resume is enabled and user idle time exceeds `resume_after_ms`, engine MUST transition from Paused to Running. Auto-resume MUST NOT trigger when engine is Idle.

#### Scenario: Resume after inactivity
- GIVEN engine Paused, auto-resume enabled, resume_after_ms=10000ms
- WHEN user idle time exceeds 10000ms
- THEN engine transitions to Running

---

## Settings

### Requirement: JSON Persistence

Settings SHALL be stored at `~/.config/move-mouse-linux/settings.json` (XDG via pyxdg). Save MUST be atomic (write temp file → rename). Missing file on load MUST produce defaults, not an error. Corrupt file MUST be logged and replaced with defaults.

#### Scenario: First run, no config
- GIVEN settings file does not exist
- WHEN app starts
- THEN default settings loaded, file created with defaults

#### Scenario: Corrupt JSON
- GIVEN settings file contains invalid JSON
- WHEN app starts
- THEN defaults loaded, error logged, file overwritten with defaults

### Requirement: Settings Model

Settings SHALL include: `interval_lower_ms`, `interval_upper_ms`, `action_list` (ordered list of action configs), `auto_pause_enabled`, `auto_pause_threshold_ms`, `auto_resume_enabled`, `auto_resume_after_ms`, `cursor_direction`, `cursor_distance`, `cursor_speed`. All fields MUST have sensible defaults. Settings changes MUST be auto-saved within 2 seconds.

#### Scenario: Partial settings file
- GIVEN file has only `interval_lower_ms: 5000`
- WHEN loaded
- THEN missing fields filled with defaults, full file saved

---

## GTK UI

### Requirement: System Tray Icon

The system SHALL display a tray icon via AppIndicator3. If AppIndicator3 is unavailable, MUST fall back to `Gtk.StatusIcon`. Tray menu SHALL contain: Start/Stop (toggle), Pause/Resume (toggle), Quit. Icon and label MUST reflect current engine state.

#### Scenario: AppIndicator3 unavailable
- GIVEN AppIndicator3 import fails
- WHEN app starts
- THEN Gtk.StatusIcon used, warning logged

#### Scenario: Start from tray
- GIVEN engine Idle, tray visible
- WHEN user clicks "Start" in tray menu
- THEN engine transitions to Running, tray label updates

### Requirement: Main Window

The system SHALL provide a minimal GTK window with: Start/Stop button, current state label, interval display. Window MUST close to tray (not quit) on window delete. Quit only via tray menu or Ctrl+Q.

#### Scenario: Close to tray
- GIVEN window is visible
- WHEN user clicks window close button
- THEN window hides, tray icon persists, engine continues

### Requirement: Settings Dialog (Future)

The system MAY provide a settings dialog in a future release. V1 SHALL allow configuration via settings.json only. Placeholder menu item "Settings…" SHALL be grayed out.

#### Scenario: Grayed-out settings
- GIVEN main window open
- WHEN user views menu
- THEN "Settings…" item is disabled (sensitive=False)

---

## Packaging

### Requirement: Flatpak Manifest

The system SHALL provide a Flatpak manifest with `--socket=x11`, `--share=ipc`, `--talk-name=org.freedesktop.ScreenSaver`, `--talk-name=org.freedesktop.login1`, `--talk-name=org.freedesktop.Notifications`, `--filesystem=xdg-config/move-mouse-linux:create`. Wayland socket SHALL NOT be included (ydotool incompatible with sandbox). Build MUST succeed on Flathub build system.

#### Scenario: X11 access in sandbox
- GIVEN Flatpak is running
- WHEN app calls XTestFakeMotionEvent
- THEN call succeeds via X11 socket

#### Scenario: Wayland blocked
- GIVEN Flatpak is running on Wayland session
- WHEN app tries ydotool
- THEN operation fails gracefully, X11 fallback used

### Requirement: Debian Package

The system SHALL provide a .deb package with dependencies: `python3-xlib`, `python3-gi`, `gir1.2-ayatanaappindicator3-0.1` (or `gir1.2-appindicator3-0.1`), `python3-dbus`, `python3-xdg`. Package MUST install to `/usr/lib/python3/dist-packages/move_mouse/` and include a `.desktop` file.

#### Scenario: Install on Ubuntu 22.04
- GIVEN clean Ubuntu 22.04
- WHEN `dpkg -i move-mouse-linux_1.0.0_all.deb`
- THEN all deps resolved, app launchable from desktop menu
