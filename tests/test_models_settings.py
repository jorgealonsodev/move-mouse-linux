"""Tests for the settings model."""

import pytest

from move_mouse.models.settings import Settings


class TestSettings:
    def test_defaults(self):
        s = Settings()
        # New interval fields (seconds)
        assert s.lower_interval == 30
        assert s.upper_interval == 60
        assert s.random_interval is False
        # Auto pause/resume
        assert s.auto_pause is False
        assert s.auto_resume is False
        assert s.auto_resume_seconds == 30
        # Behavior
        assert s.active_when_locked is False
        assert s.minimise_on_stop is False
        assert s.start_at_launch is False
        # UI Options
        assert s.hide_from_taskbar is False
        assert s.hide_main_window is False
        assert s.hide_system_tray_icon is False
        assert s.show_system_tray_notifications is False
        assert s.show_taskbar_status is True
        # UI / Platform Options (Windows app parity)
        assert s.hide_from_alt_tab is False
        assert s.topmost_when_running is False
        assert s.prevent_screen_burn is False
        assert s.show_move_mouse_status is False
        assert s.disable_button_animation is False
        assert s.pause_on_battery is False
        assert s.launch_at_logon is False
        # Collections
        assert s.actions == []
        assert s.schedules == []
        assert s.blackouts == []
        # Logging
        assert s.enable_logging is False
        assert s.log_level == "INFO"

    def test_to_dict_roundtrip(self):
        s = Settings(lower_interval=5, auto_pause=True)
        d = s.to_dict()
        assert d["lower_interval"] == 5
        assert d["auto_pause"] is True

    def test_from_dict_partial(self):
        s = Settings.from_dict({"lower_interval": 5})
        assert s.lower_interval == 5
        assert s.auto_pause is False  # default

    def test_from_dict_ignores_unknown(self):
        s = Settings.from_dict({"lower_interval": 5, "foo": "bar"})
        assert s.lower_interval == 5
        assert not hasattr(s, "foo")

    def test_save_load_roundtrip(self, tmp_path):
        path = tmp_path / "settings.json"
        original = Settings(lower_interval=10, auto_resume=True, auto_resume_seconds=60)
        original.save(str(path))
        loaded = Settings.load(str(path))
        assert loaded.lower_interval == 10
        assert loaded.auto_resume is True
        assert loaded.auto_resume_seconds == 60

    def test_load_missing_file_returns_defaults(self, tmp_path):
        path = tmp_path / "no_existe.json"
        s = Settings.load(str(path))
        assert s.lower_interval == 30

    def test_load_corrupt_json_returns_defaults(self, tmp_path):
        path = tmp_path / "corrupto.json"
        path.write_text("no es json")
        s = Settings.load(str(path))
        assert s.lower_interval == 30

    def test_load_non_dict_returns_defaults(self, tmp_path):
        path = tmp_path / "lista.json"
        path.write_text("[1, 2, 3]")
        s = Settings.load(str(path))
        assert s.lower_interval == 30

    def test_save_creates_directories(self, tmp_path):
        path = tmp_path / "sub" / "dir" / "settings.json"
        s = Settings()
        s.save(str(path))
        assert path.exists()
