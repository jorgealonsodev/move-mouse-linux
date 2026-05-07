# Move Mouse Linux

A GTK3 desktop application that simulates user activity by moving the mouse cursor at configurable
intervals, preventing session lock or screensaver activation during long unattended tasks.

This is a Linux port of the original [Move Mouse](https://github.com/sw3103/movemouse) Windows
application by Steve Towner.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Settings Reference](#settings-reference)
- [Project Structure](#project-structure)
- [Tests](#tests)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Credits](#credits)
- [Contact and Support](#contact-and-support)

---

## Prerequisites

**Runtime**

- Python 3.8 or later
- X11 display server (Wayland support via XWayland or `ydotool`)

**System dependencies**

```bash
# Debian / Ubuntu
sudo apt install \
  python3-gi \
  python3-xlib \
  python3-pydbus \
  gir1.2-gtk-3.0 \
  gir1.2-appindicator3-0.1
```

> On systems without AppIndicator3 (e.g. pure GNOME), install
> `libayatana-appindicator3-1` instead and the app falls back automatically
> to a GTK StatusIcon.

**Python packages** (installed automatically)

| Package | Minimum version |
|---|---|
| `python-xlib` | 0.33 |
| `pydbus` | 0.6.0 |

---

## Installation

### Option 1 — Debian package (recommended for Debian/Ubuntu)

Download the latest `.deb` from the
[Releases](https://github.com/jorgealonsodev/move-mouse-linux/releases) page and install it:

```bash
sudo dpkg -i move-mouse_1.0.0_all.deb
sudo apt-get install -f   # resolve missing dependencies if needed
```

### Option 2 — Flatpak bundle (any distro)

Download the latest `.flatpak` from the
[Releases](https://github.com/jorgealonsodev/move-mouse-linux/releases) page and install it:

```bash
# Install the bundle (one-time)
flatpak install move-mouse_1.0.0.flatpak

# Run
flatpak run org.movemouse.MoveMouse
```

> Requires the GNOME Platform runtime 46. If not present, flatpak will prompt to install it.

### Option 4 — pip (development install)

```bash
git clone https://github.com/jorgealonsodev/move-mouse-linux.git
cd move-mouse-linux
pip install -e .
```

### Option 5 — make (from source)

```bash
git clone https://github.com/jorgealonsodev/move-mouse-linux.git
cd move-mouse-linux
make install   # installs via pip in editable mode
```

To build the `.deb` yourself:

```bash
make deb
sudo dpkg -i ../move-mouse_1.0.0-1_all.deb
```

---

## Usage

### Launch the GUI

```bash
move-mouse
```

### Launch without GUI (headless mode)

```bash
move-mouse --no-gui
```

The application starts minimised to the system tray. Use the tray icon menu to start, stop,
pause, or open the settings dialog.

### Keyboard workflow

| Action | How |
|---|---|
| Start / Stop | Click the main button in the window |
| Pause | Click Pause or trigger auto-pause |
| Open Settings | Tray icon -> Settings |
| Quit | Tray icon -> Quit |

---

## Configuration

Settings are persisted automatically to:

```
~/.config/move-mouse-linux/settings.json
```

The file is written atomically on every change. If the file does not exist or is corrupt,
all settings reset to their defaults.

<!-- Update the path below if you add an .env.example in the future -->

There are no environment variables or `.env` files required for normal operation.

---

## Settings Reference

All settings are available through the five-tab Settings dialog. They are also readable and
writable directly in the JSON file.

### Interval

| Key | Type | Default | Description |
|---|---|---|---|
| `lower_interval` | int (seconds) | `30` | Minimum interval between actions |
| `upper_interval` | int (seconds) | `60` | Maximum interval between actions |
| `random_interval` | bool | `false` | Pick a random interval between lower and upper each cycle |

### Auto Pause / Resume

| Key | Type | Default | Description |
|---|---|---|---|
| `auto_pause` | bool | `false` | Pause automatically when user activity is detected |
| `auto_resume` | bool | `false` | Resume automatically after a period of inactivity |
| `auto_resume_seconds` | int (seconds) | `30` | Inactivity time before auto-resume |

### Behaviour

| Key | Type | Default | Description |
|---|---|---|---|
| `active_when_locked` | bool | `false` | Continue running when the session is locked |
| `minimise_on_stop` | bool | `false` | Minimise the window when movement is stopped |
| `start_at_launch` | bool | `false` | Start movement automatically when the app opens |
| `launch_at_logon` | bool | `false` | Add a desktop autostart entry for the current user |
| `pause_on_battery` | bool | `false` | Pause when the system is running on battery power |

### Interface

| Key | Type | Default | Description |
|---|---|---|---|
| `hide_from_taskbar` | bool | `false` | Do not show the window in the taskbar |
| `hide_main_window` | bool | `false` | Start with the main window hidden |
| `hide_system_tray_icon` | bool | `false` | Do not show the system tray icon |
| `show_system_tray_notifications` | bool | `false` | Show notifications from the tray icon |
| `show_taskbar_status` | bool | `true` | Show running/paused status in the taskbar entry |
| `hide_from_alt_tab` | bool | `false` | Exclude the window from the Alt+Tab switcher |
| `topmost_when_running` | bool | `false` | Keep the window above other windows while running |
| `prevent_screen_burn` | bool | `false` | Inhibit the screensaver via the GNOME session API |
| `show_move_mouse_status` | bool | `false` | Show current state in the window title |
| `disable_button_animation` | bool | `false` | Disable the animated start/stop button |

### Logging

| Key | Type | Default | Description |
|---|---|---|---|
| `enable_logging` | bool | `false` | Write log output to a file |
| `log_level` | string | `"INFO"` | Log verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

---

## Project Structure

```
move-mouse-linux/
├── move_mouse/                 # Main Python package
│   ├── actions/                # Pluggable action implementations
│   │   ├── base.py             # ActionBase ABC and ActionResult
│   │   ├── move_mouse.py       # Cursor movement (15 directions + circle)
│   │   ├── click_mouse.py      # Mouse click simulation
│   │   ├── scroll_mouse.py     # Mouse scroll simulation
│   │   ├── position_cursor.py  # Absolute cursor positioning
│   │   └── sleep_action.py     # Timed pause between actions
│   ├── backends/               # Display backend abstraction
│   ├── core/
│   │   ├── engine.py           # State machine (stopped/running/paused)
│   │   ├── executor.py         # Sequential action pipeline
│   │   └── idle_detector.py    # XScreenSaver + D-Bus idle detection
│   ├── models/
│   │   ├── settings.py         # 26-field settings dataclass with JSON persistence
│   │   └── schedule.py         # Schedule and blackout models
│   ├── services/
│   │   └── session_monitor.py  # D-Bus session lock/unlock/suspend signals
│   ├── ui/
│   │   ├── app.py              # GTK Application, wires engine to UI
│   │   ├── window.py           # Main window
│   │   ├── tray.py             # System tray (AppIndicator3 / StatusIcon fallback)
│   │   └── settings_window.py  # 5-tab settings dialog
│   ├── mouse_controller.py     # X11 / Wayland mouse control
│   └── main.py                 # CLI entry point
├── data/
│   ├── icons/                  # Hicolor icons (16 to 256 px + scalable SVG)
│   ├── org.movemouse.MoveMouse.desktop
│   └── org.movemouse.MoveMouse.metainfo.xml
├── debian/                     # Debian packaging files
├── flatpak/                    # Flatpak manifest
├── tests/                      # Pytest test suite (159 tests)
├── openspec/                   # SDD specification artifacts
├── Makefile                    # Development tasks
└── pyproject.toml
```

---

## Tests

Run the full test suite:

```bash
make test
# or directly:
pytest tests/ -v --tb=short
```

Run a specific module:

```bash
pytest tests/core/test_executor.py -v
```

The suite covers unit tests for the engine state machine, executor pipeline, all action classes,
settings persistence, session monitor, and GTK UI components (mocked). 159 tests pass with no
X11 display required.

<!-- Add a coverage badge here once CI is configured to report it -->

---

## Roadmap

Planned for v1.1 and beyond:

- [ ] Schedules and blackout windows enforcement in the engine
- [ ] Keystroke action (simulate key press)
- [ ] End-to-end tests with a virtual display
- [ ] Publication on Flathub
- [ ] Wayland-native backend (without XWayland)

See [open issues](https://github.com/jorgealonsodev/move-mouse-linux/issues) for the full list.

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit following [Conventional Commits](https://www.conventionalcommits.org/):
   `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`
4. Push and open a Pull Request against `main`

<!-- Add CONTRIBUTING.md and CODE_OF_CONDUCT.md and link them here when available -->

All code, comments, docstrings, and commit messages must be written in **English**.

---

## License

Licensed under the [GNU General Public License v3.0](LICENSE).

---

## Credits

**Original application**

Move Mouse for Windows was created by [Steve Towner](https://github.com/sw3103/movemouse).
This Linux port is an independent reimplementation and is not affiliated with the original project.

**Linux port**

Developed by [Jorge Alonso](https://github.com/jorgealonsodev).

---

## Contact and Support

- **Bug reports**: [open an issue](https://github.com/jorgealonsodev/move-mouse-linux/issues)
- **Questions**: use the
  [Discussions](https://github.com/jorgealonsodev/move-mouse-linux/discussions) tab

<!-- Add Discord or other community channels here if they become available -->
