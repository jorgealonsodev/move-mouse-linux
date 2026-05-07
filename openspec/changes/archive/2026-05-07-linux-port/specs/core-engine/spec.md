# Core Engine Specification

## Purpose

State machine, interval timer, and action dispatcher — the heart of the app.

## Requirements

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
