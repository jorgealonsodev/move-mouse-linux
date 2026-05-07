# Design: Linux Port of Move Mouse

## Technical Approach

Layered Python/GTK architecture: a state-machine engine orchestrates an interval executor that dispatches actions through a unified `MouseController`. The engine pauses on user activity (XScreenSaver/D-Bus) and resumes after idle timeout. X11 is primary via python-xlib XTest; Wayland falls back to ydotool. UI is GTK3 + AppIndicator3. Settings persist as JSON under `~/.config`.

The existing `mouse_controller.py` is refactored into `backends/` for backend abstraction; its direction/speed enums and movement logic become the `MoveMouseCursor` action. Everything else is new.

## Architecture Decisions

### Decision: Module layout

**Choice**: Package-based with `core/`, `actions/`, `backends/`, `models/`, `ui/`, `services/`
**Alternatives**: Flat single module, feature-based slices
**Rationale**: Separates concerns cleanly. Actions and services are independently testable. Matches proposal capability map 1:1.

```
move_mouse/
├── __init__.py
├── __main__.py                # Entry: CLI arg parse → GTK main loop
├── mouse_controller.py        # Facade over backends (kept, refactored)
├── core/
│   ├── __init__.py
│   ├── engine.py              # State machine + interval timer
│   ├── executor.py            # Action dispatcher (pipeline runner)
│   └── idle_detector.py       # XScreenSaver + D-Bus idle query
├── actions/
│   ├── __init__.py
│   ├── base.py                # ActionBase ABC: execute() → ActionResult
│   ├── move_mouse.py          # MoveMouseCursor (delegates to mouse_controller)
│   ├── click_mouse.py         # ClickMouse (left/middle/right)
│   ├── scroll_mouse.py        # ScrollMouse (vertical/horizontal)
│   ├── position_cursor.py     # PositionCursor (absolute x,y)
│   └── sleep_action.py        # Sleep (fixed or random range)
├── backends/
│   ├── __init__.py
│   ├── mouse_backend.py       # ABC: get_position, move_relative, move_absolute, click, scroll
│   ├── x11_backend.py         # python-xlib + XTest (extracted from current code)
│   └── wayland_backend.py     # ydotool subprocess
├── models/
│   ├── __init__.py
│   ├── settings.py            # Settings dataclass + defaults
│   └── schedule.py            # V2 stub: Schedule/Blackout models
├── ui/
│   ├── __init__.py
│   ├── app.py                 # Gtk.Application subclass
│   ├── window.py              # Main window (start/stop, direction picker, interval)
│   └── tray.py                # AppIndicator3 tray with Gtk.StatusIcon fallback
└── services/
    ├── __init__.py
    └── session_monitor.py     # D-Bus: lock/unlock (logind), suspend/resume
```

### Decision: State machine

**Choice**: 6 states: Idle, Running, Paused, Executing, Sleeping, Locked
**Alternatives**: 4-state simplified (Idle/Running/Paused/Locked), 8-state with OnBattery
**Rationale**: Executing and Sleeping are transient sub-states of Running — the engine needs them to know whether to dispatch another action. OnBattery is V2 scope.

```
                   ┌──────────┐
    Stop/Complete  │   IDLE   │ ← Initial
                   └────┬─────┘
                        │ start()
                   ┌────▼─────┐  interval_tick()  ┌────────────┐
                   │ RUNNING  │──────────────────→ │ EXECUTING  │
                   └────┬─────┘←──────────────────└────────────┘
                        │           action_done()
              ┌─────────┼──────────┐
     pause()  │         │          │ lock_event()
              ▼         │          ▼
        ┌──────────┐    │   ┌──────────┐
        │  PAUSED  │    │   │  LOCKED  │
        └────┬─────┘    │   └────┬─────┘
             │          │        │ unlock_event()
    resume() │          │        │
             └──────────┴────────┘
                   → RUNNING
```

Transitions:
| From → To | Event | Condition |
|-----------|-------|-----------|
| Idle → Running | `start()` | Backend available |
| Running → Executing | `interval_tick()` | Timer fires |
| Executing → Running | `action_done()` | Action completed |
| Running → Paused | `pause()` or `user_activity()` | `break_on_activity=True` |
| Paused → Running | `resume()` or `idle_timeout()` | Configurable idle seconds |
| Running → Locked | `lock_event()` | D-Bus session lock |
| Locked → Running | `unlock_event()` | D-Bus session unlock |
| Running → Idle | `stop()` | User stop |
| Paused → Idle | `stop()` | User stop |
| Locked → Idle | `stop()` | User stop |

### Decision: Threading model

**Choice**: GTK main thread + `threading.Timer` for intervals; Xlib Display locked per-backend
**Alternatives**: asyncio event loop, GLib `idle_add` for all operations
**Rationale**: `threading.Timer` is simple and matches the original's interval model. python-xlib `Display` is NOT thread-safe, so each backend holds a `threading.Lock`serialized around all Display calls. GTK UI updates marshal via `GLib.idle_add()` from the action thread.

```
┌─────────────────────────────────────────────────┐
│ GTK Main Thread                                 │
│  ├── Gtk.Application.run()                      │
│  ├── Window signals → Engine.start/stop/pause   │
│  └── GLib.idle_add() ← action thread callbacks  │
├─────────────────────────────────────────────────┤
│ Timer Thread (threading.Timer)                  │
│  ├── Engine._tick()                             │
│  ├── Executor.run_action()                      │
│  ├── Action.execute() → MouseController         │
│  └── GLib.idle_add(notify_ui)                   │
├─────────────────────────────────────────────────┤
│ Idle Detector Thread (threading.Thread, daemon) │
│  ├── Polls XScreenSaver every 1s               │
│  └── Signals Engine.on_user_activity()          │
└─────────────────────────────────────────────────┘
```

### Decision: Backend auto-detection

**Choice**: Try X11 first via `Xlib.Display()` probe; if unavailable fall back to Wayland/ydotool
**Alternatives**: Env var `XDG_SESSION_TYPE` only; explicit CLI flag only
**Rationale**: Env var `XDG_SESSION_TYPE` is used as HINT, but runtime probe is the source of truth. X11 under XWayland still works, so `XDG_SESSION_TYPE=wayland` with a working X11 display is valid. Probe first, then respect user override.

### Decision: Settings persistence

**Choice**: JSON to `~/.config/move-mouse-linux/settings.json` (XDG_CONFIG_HOME aware via `pyxdg`)
**Alternatives**: GSettings/dconf, TOML, INI
**Rationale**: JSON is human-readable, debuggable, and trivially serializable from dataclasses. GSettings adds GLib schema compilation overhead. Atomic write via temp file + `os.rename()`.

### Decision: Packaging

**Choice**: Flatpak primary, .deb secondary
**Alternatives**: Snap, AppImage, PyPI-only
**Rationale**: Flatpak is the standard GNOME distribution; `.deb` covers server/headless. AppImage doesn't sandbox. Flatpak manifest uses `org.gnome.Sdk` runtime with `--socket=x11` and D-Bus talk permissions. Wayland/ydotool is unsupported inside Flatpak (document this).

## Data Flow

```
settings.json ──load──→ Settings(dataclass)
                            │
                            ▼
                     Engine(Settings, MouseController, IdleDetector)
                     │  │  │
                     │  │  ├── IdleDetector ──poll──→ XScreenSaver / D-Bus
                     │  │  └── SessionMonitor ──listen──→ D-Bus logind
                     │  │
                     │  └──interval_tick──→ Executor.run_next_action()
                     │                          │
                     │                          ▼
                     │                     ActionPipeline[action, action, ...]
                     │                          │
                     │                     Action.execute(MouseController)
                     │                          │
                     │                          ▼
                     │                     X11Backend / WaylandBackend
                     │
                     └──status──→ UI(Tray + Window)  via GLib.idle_add()
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `move_mouse/__main__.py` | Create | CLI entry: arg parse, GTK main loop |
| `move_mouse/mouse_controller.py` | Modify | Thin facade over backends; move logic to backends/ and actions/ |
| `move_mouse/core/__init__.py` | Create | Package init |
| `move_mouse/core/engine.py` | Create | State machine, interval timer, start/stop/pause/resume |
| `move_mouse/core/executor.py` | Create | Action pipeline dispatcher, interval with randomization |
| `move_mouse/core/idle_detector.py` | Create | XScreenSaver + D-Bus idle time query |
| `move_mouse/actions/__init__.py` | Create | Package init |
| `move_mouse/actions/base.py` | Create | ActionBase ABC with execute() → ActionResult |
| `move_mouse/actions/move_mouse.py` | Create | MoveMouseCursor action (delegates to controller) |
| `move_mouse/actions/click_mouse.py` | Create | ClickMouse action (button: L/M/R) |
| `move_mouse/actions/scroll_mouse.py` | Create | ScrollMouse action (vertical/horizontal) |
| `move_mouse/actions/position_cursor.py` | Create | PositionCursor action (absolute x,y) |
| `move_mouse/actions/sleep_action.py` | Create | Sleep action (fixed or random delay) |
| `move_mouse/backends/__init__.py` | Create | Package init |
| `move_mouse/backends/mouse_backend.py` | Create | ABC: get_position, move_relative, move_absolute, click, scroll |
| `move_mouse/backends/x11_backend.py` | Create | Extracted from current _X11Controller, add scroll + thread lock |
| `move_mouse/backends/wayland_backend.py` | Create | Extracted from current _YdotoolController, add scroll |
| `move_mouse/models/__init__.py` | Create | Package init |
| `move_mouse/models/settings.py` | Create | Settings dataclass with defaults |
| `move_mouse/models/schedule.py` | Create | V2 stub (empty or minimal) |
| `move_mouse/ui/__init__.py` | Create | Package init |
| `move_mouse/ui/app.py` | Create | Gtk.Application with engine wiring |
| `move_mouse/ui/window.py` | Create | Main window: start/stop, direction, interval config |
| `move_mouse/ui/tray.py` | Create | AppIndicator3 tray icon with menu |
| `move_mouse/services/__init__.py` | Create | Package init |
| `move_mouse/services/session_monitor.py` | Create | D-Bus logind lock/unlock listener |
| `move-mouse-linux/flatpak/org.movemouse.MoveMouse.yaml` | Create | Flatpak build manifest |
| `move-mouse-linux/debian/control` | Create | Debian package metadata |
| `move-mouse-linux/debian/rules` | Create | Debian build rules |

## Interfaces / Contracts

```python
# backends/mouse_backend.py
class MouseBackend(ABC):
    @property
    def available(self) -> bool: ...
    def get_position(self) -> Tuple[int, int]: ...
    def move_relative(self, dx: int, dy: int) -> None: ...
    def move_absolute(self, x: int, y: int) -> None: ...
    def click(self, button: int) -> None: ...    # 1=left, 2=middle, 3=right
    def scroll(self, delta: int, horizontal: bool = False) -> None: ...

# actions/base.py
@dataclass
class ActionResult:
    aborted: bool = False       # User activity interrupted
    error: Optional[str] = None

class ActionBase(ABC):
    @abstractmethod
    def execute(self, controller: MouseController) -> ActionResult: ...

# core/engine.py
class EngineState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    EXECUTING = "executing"
    LOCKED = "locked"

class Engine:
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def pause(self) -> None: ...
    def resume(self) -> None: ...
    @property
    def state(self) -> EngineState: ...

# models/settings.py
@dataclass
class Settings:
    interval_seconds: int = 30
    interval_randomize: bool = False
    interval_upper: Optional[int] = None
    direction: str = "square"        # CursorDirection value
    distance: int = 5
    speed: str = "normal"             # CursorSpeed value
    click_button: Optional[int] = None
    break_on_activity: bool = True
    idle_resume_seconds: int = 5
    actions: List[dict] = field(default_factory=list)
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Action classes (move, click, scroll, sleep) | Mock MouseController, verify correct calls |
| Unit | Engine state transitions | State machine transitions with mocked timer |
| Unit | Settings load/save | JSON round-trip with temp dir |
| Unit | IdleDetector logic | Mock XScreenSaver values, D-Bus responses |
| Integration | Engine + Executor + MockBackend | Full pipeline execution without GTK |
| Integration | Backend auto-detection | Fake env vars, mock Display availability |
| E2E | GTK app launch + tray | Virtual framebuffer (Xvfb), verify window appears |
| E2E | Flatpak build | `flatpak-builder` verify build succeeds |

## Migration / Rollout

No migration required. This is a greenfield port — no existing user data or settings to migrate. The Windows original uses XML in `%AppData%`; V2 could add XML import from Windows installations.

## Open Questions

- [ ] Should `Sleep` action be part of the `actions` pipeline or a separate engine concept? (Current design: pipeline action)
- [ ] Flatpak sidebar distribution: Flathub submission requirements need verification
- [ ] AppIndicator3 vs. libayatana-appindicator — which is available in the target GNOME SDK runtime?