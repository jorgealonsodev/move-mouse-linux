# Packaging Specification

## Purpose

Flatpak and .deb packaging for distribution.

## Requirements

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
