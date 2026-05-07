"""Tests para el modelo de configuración."""

import pytest

from move_mouse.models.settings import Settings


class TestSettings:
    def test_defaults(self):
        s = Settings()
        assert s.interval_lower_ms == 30000
        assert s.interval_upper_ms is None
        assert s.action_list == []
        assert s.auto_pause_enabled is True
        assert s.auto_pause_threshold_ms == 3000
        assert s.auto_resume_enabled is True
        assert s.auto_resume_after_ms == 10000
        assert s.cursor_direction == "square"
        assert s.cursor_distance == 5
        assert s.cursor_speed == "normal"

    def test_to_dict_roundtrip(self):
        s = Settings(interval_lower_ms=5000, cursor_direction="north")
        d = s.to_dict()
        assert d["interval_lower_ms"] == 5000
        assert d["cursor_direction"] == "north"

    def test_from_dict_partial(self):
        s = Settings.from_dict({"interval_lower_ms": 5000})
        assert s.interval_lower_ms == 5000
        assert s.cursor_direction == "square"  # default

    def test_from_dict_ignores_unknown(self):
        s = Settings.from_dict({"interval_lower_ms": 5000, "foo": "bar"})
        assert s.interval_lower_ms == 5000
        assert not hasattr(s, "foo")

    def test_save_load_roundtrip(self, tmp_path):
        path = tmp_path / "settings.json"
        original = Settings(interval_lower_ms=1234, cursor_speed="fast")
        original.save(str(path))
        loaded = Settings.load(str(path))
        assert loaded.interval_lower_ms == 1234
        assert loaded.cursor_speed == "fast"
        assert loaded.cursor_direction == "square"

    def test_load_missing_file_returns_defaults(self, tmp_path):
        path = tmp_path / "no_existe.json"
        s = Settings.load(str(path))
        assert s.interval_lower_ms == 30000

    def test_load_corrupt_json_returns_defaults(self, tmp_path):
        path = tmp_path / "corrupto.json"
        path.write_text("no es json")
        s = Settings.load(str(path))
        assert s.interval_lower_ms == 30000

    def test_load_non_dict_returns_defaults(self, tmp_path):
        path = tmp_path / "lista.json"
        path.write_text("[1, 2, 3]")
        s = Settings.load(str(path))
        assert s.interval_lower_ms == 30000

    def test_save_creates_directories(self, tmp_path):
        path = tmp_path / "sub" / "dir" / "settings.json"
        s = Settings()
        s.save(str(path))
        assert path.exists()
