# Mouse Actions Specification

## Purpose

Action types the engine can dispatch: move, click, sleep, position.

## Requirements

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
