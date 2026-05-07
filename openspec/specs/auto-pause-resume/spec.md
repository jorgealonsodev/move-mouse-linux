# Auto-Pause/Resume Specification

## Purpose

Detect user activity, auto-pause engine on input, auto-resume after idle.

## Requirements

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
