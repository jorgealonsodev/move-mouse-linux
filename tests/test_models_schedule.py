"""Tests para modelos de agenda."""

from move_mouse.models.schedule import Blackout, Schedule


class TestSchedule:
    def test_defaults(self):
        s = Schedule()
        assert s.enabled is False


class TestBlackout:
    def test_defaults(self):
        b = Blackout()
        assert b.start_hour is None
        assert b.end_hour is None
