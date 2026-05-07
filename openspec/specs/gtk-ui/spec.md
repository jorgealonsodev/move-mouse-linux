# GTK UI Specification

## Purpose

System tray icon, minimal main window, and future settings dialog placeholder.

## Requirements

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
