# Settings Persistence Specification

## Purpose

JSON-based settings model with atomic load/save.

## Requirements

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
