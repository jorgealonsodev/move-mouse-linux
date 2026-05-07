# Proposal: Linux Port of Move Mouse

## Intent

Port the Windows "Move Mouse" utility to Linux as a Python/GTK app. Linux lacks a polished native tool to simulate mouse activity and prevent screen lock.

## Scope

### In Scope
- Mouse actions: move (15 directions), click, scroll, position, sleep
- Interval execution with random range
- Auto-pause on activity, auto-resume after idle
- Settings persistence (JSON in `~/.config`)
- GTK window + system tray via AppIndicator3
- Session lock/unlock via D-Bus
- Flatpak + .deb packaging

### Out of Scope
- Keystroke, Command, Script, ActivateApplication actions
- Schedules, blackouts, volume control, battery detection
- Full Wayland support (fallback only)

## Capabilities

### New Capabilities
- `core-engine`: State machine, executor, interval timer
- `mouse-actions`: Move, click, scroll, position, sleep
- `idle-detection`: Activity detection (XScreenSaver / D-Bus)
- `settings-persistence`: JSON model, load/save
- `gtk-ui`: GTK window, system tray
- `session-monitoring`: D-Bus lock/unlock signals

### Modified Capabilities
None

## Approach

Layered modular Python/GTK. Core engine drives actions pipeline; backends abstract X11 (`python-xlib`) and Wayland (`ydotool`); UI uses GTK3 + AppIndicator3; services handle D-Bus. X11 first, Wayland fallback.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `move_mouse/core/` | New | Engine, executor, idle detector |
| `move_mouse/actions/` | New | Action pipeline |
| `move_mouse/backends/` | New | X11 and Wayland backends |
| `move_mouse/settings/` | New | Model, store |
| `move_mouse/ui/` | New | GTK app, tray |
| `move_mouse/services/` | New | Session monitor |
| `flatpak/` | Modified | Manifest + permissions |
| `debian/` | Modified | Packaging metadata |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Wayland ydotool needs root | High | Default X11; document limits |
| Flatpak blocks XTest/Wayland | Med | `--socket=x11`; skip Wayland in Flatpak |
| XScreenSaver missing | Med | D-Bus fallback |
| Xlib thread safety | Med | Single-threaded GTK loop |
| AppIndicator3 deprecated | Low | `Gtk.StatusIcon` fallback |

## Rollback Plan

Revert to last stable commit. Delete new directories; restore `mouse_controller.py` from git. No external state to migrate.

## Dependencies

- `python-xlib`, `PyGObject`, `dbus-python`, `pyxdg`
- GTK 3, AppIndicator3
- Wayland: `ydotool` on host

## Success Criteria

- [ ] Mouse moves in all 15 directions on X11
- [ ] Click and scroll work via XTest
- [ ] Interval execution respects bounds with randomization
- [ ] Auto-pause on input; auto-resume after timeout
- [ ] Settings persist across restarts
- [ ] GTK window + tray reflect engine state
- [ ] Flatpak builds; .deb installs on Ubuntu 22.04+
