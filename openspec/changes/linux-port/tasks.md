# Tasks: linux-port

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~2,900 (new) + ~300 (modified) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 → PR 4 |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | PR | Base branch | Lines |
|------|------|----|-------------|-------|
| 1 | Foundation: backends + models + core engine | PR 1 | main | ~700 |
| 2 | Action layer: executor + all action types | PR 2 | main (after PR1) | ~900 |
| 3 | UI + system integration: GTK, tray, idle, session | PR 3 | main (after PR2) | ~850 |
| 4 | Packaging: Flatpak manifest + Debian files | PR 4 | main (after PR3) | ~450 |

---

## Phase 1: Foundation (~700 lines)

- [ ] 1.1 Create `move_mouse/backends/mouse_backend.py` — ABC with `available`, `get_position`, `move_relative`, `move_absolute`, `click`, `scroll`
- [ ] 1.2 Create `move_mouse/backends/x11_backend.py` — extracted from existing `_X11Controller`, add thread lock + scroll, `threading.Lock` around all Display calls
- [ ] 1.3 Create `move_mouse/backends/wayland_backend.py` — extracted from existing `_YdotoolController`, add scroll support
- [ ] 1.4 Create `move_mouse/backends/__init__.py` — factory `create_backend()` that probes X11 first, falls back to Wayland
- [ ] 1.5 Modify `move_mouse/mouse_controller.py` — thin facade using `backends` package; keep `CursorDirection`, `CursorSpeed`, `SPEED_DELAYS` enums in place
- [x] 1.6 Create `move_mouse/models/settings.py` — `Settings` dataclass with defaults: `interval_lower_ms=30000`, `interval_upper_ms=None`, `action_list=[]`, `auto_pause_enabled=True`, `auto_pause_threshold_ms=3000`, `auto_resume_enabled=True`, `auto_resume_after_ms=10000`, `cursor_direction="square"`, `cursor_distance=5`, `cursor_speed="normal"`
- [x] 1.7 Create `move_mouse/models/__init__.py` and `move_mouse/backends/__init__.py` (models done; backends pending PR 2)
- [ ] 1.8 Write unit tests for `backends/` (mock Xlib.Display, mock subprocess for ydotool)

---

## Phase 2: Core Engine (~900 lines)

- [x] 2.1 Create `move_mouse/actions/base.py` — `ActionResult` dataclass (`aborted: bool`, `error: Optional[str]`), `ActionBase` ABC with `execute(controller) -> ActionResult`
- [x] 2.2 Create `move_mouse/actions/move_mouse.py` — `MoveMouseCursor` delegates to `MouseController.execute_move_action()`
- [x] 2.3 Create `move_mouse/actions/click_mouse.py` — `ClickMouse` with `button` (1/2/3) and `hold_ms` (default 50)
- [ ] 2.4 Create `move_mouse/actions/scroll_mouse.py` — `ScrollMouse` with `delta` and `horizontal` flag
- [x] 2.5 Create `move_mouse/actions/position_cursor.py` — `PositionCursor` with absolute `x`, `y`
- [x] 2.6 Create `move_mouse/actions/sleep_action.py` — `SleepAction` with `duration_ms`, `random_duration`, `upper_duration_ms`; during sleep engine enters `Sleeping` state
- [x] 2.7 Create `move_mouse/core/engine.py` — `EngineState` enum (Idle/Running/Paused/Executing/Sleeping/Locked), `Engine` class with `start/stop/pause/resume`, state signals, GLib `timeout_add` for interval timer, cancellation on Idle/Paused
- [x] 2.8 Create `move_mouse/core/executor.py` — `ActionExecutor` runs action pipeline sequentially, randomized interval via `random.randint(lower_ms, upper_ms)`, completes all actions before next tick
- [ ] 2.9 Write unit tests for `core/engine.py` (state transitions mocked timer), `core/executor.py` (action list, failure recovery)

---

## Phase 3: UI + System Integration (~850 lines)

- [ ] 3.1 Create `move_mouse/ui/app.py` — `MoveMouseApp(Gtk.Application)` wiring engine signals to GLib `idle_add` for UI updates
- [ ] 3.2 Create `move_mouse/ui/window.py` — `MainWindow` with Start/Stop button, state label, interval display; window delete hides to tray (does not quit)
- [ ] 3.3 Create `move_mouse/ui/tray.py` — `TrayIcon` using AppIndicator3 with fallback to `Gtk.StatusIcon`; menu: Start/Stop toggle, Pause/Resume toggle, Quit
- [x] 3.4 Create `move_mouse/core/idle_detector.py` — `IdleDetector` polling XScreenSaver `idle` timer (X11 primary), D-Bus `org.freedesktop.ScreenSaver.GetSessionIdleTime` fallback; configurable polling interval (default 1000ms)
- [ ] 3.5 Wire auto-pause/resume: `IdleDetector` → `Engine.pause()` / `Engine.resume()` via idle time thresholds
- [x] 3.6 Create `move_mouse/services/session_monitor.py` — D-Bus `org.freedesktop.login1` listener for lock/unlock → `Engine.lock()` / `Engine.unlock()`
- [x] 3.7 Create `move_mouse/main.py` (en lugar de `__main__.py` en PR 1; GTK aún no está disponible) — CLI entry: arg parse, engine instantiation, run loop

---

## Phase 4: Settings Persistence (~200 lines)

- [ ] 4.1 Create `move_mouse/services/settings_persistence.py` — load/save `Settings` to `~/.config/move-mouse-linux/settings.json` using `pyxdg`; atomic write via temp file + `os.rename()`; on missing file → defaults; on corrupt JSON → log + replace with defaults
- [ ] 4.2 Wire settings auto-save on changes (debounced ≤2s)
- [ ] 4.3 Write unit tests for settings load/save round-trip with temp dir

---

## Phase 5: Packaging (~450 lines)

- [ ] 5.1 Create `flatpak/org.movemouse.MoveMouse.yaml` — Flatpak manifest with `org.gnome.Sdk`, `--socket=x11`, `--share=ipc`, D-Bus talk names, XDG config filesystem; Wayland socket excluded
- [ ] 5.2 Create `debian/control` — Package name `move-mouse-linux`,Depends: `python3-xlib`, `python3-gi`, `gir1.2-ayatanaappindicator3-0.1 | gir1.2-appindicator3-0.1`, `python3-dbus`, `python3-xdg`
- [ ] 5.3 Create `debian/rules` — dh-compatible build rules
- [ ] 5.4 Create `debian/move-mouse-linux.desktop` — `.desktop` file for app launcher
- [ ] 5.5 Create `debian/copyright`, `debian/changelog`
- [ ] 5.6 Verify `flatpak-builder` build succeeds locally

---

## Phase 6: Verification (~300 lines)

- [ ] 6.1 Integration test: `Engine` + `Executor` + `MockBackend` full pipeline without GTK
- [ ] 6.2 E2E test: GTK app launch + tray via Xvfb virtual framebuffer
- [ ] 6.3 Flatpak build verification
- [ ] 6.4 Test backend auto-detection (fake XDG_SESSION_TYPE=wayland, mock Display unavailable)

---

## Dependency Order

```
PR 1 (Foundation)
  backends/ → models/ → core/engine.py

PR 2 (Action layer, depends on PR 1)
  actions/ → core/executor.py

PR 3 (UI + system, depends on PR 2)
  ui/ → idle_detector.py → session_monitor.py → __main__.py

PR 4 (Packaging, depends on PR 3)
  flatpak/ → debian/
```

## Notes

- `mouse_controller.py` (existing) is refactored into `backends/` — PR 1 handles this migration
- Scroll action is new (not in current code) — added in PR 2
- Flatpak Wayland/ydotool is unsupported inside sandbox — documented in spec
- `SessionMonitor` (session lock/unlock) is V2 scope stub in this PR chain