"""Tests para el punto de entrada principal."""

from unittest.mock import MagicMock, patch

import pytest

from move_mouse.main import main


class TestMain:
    def test_version_flag(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["--version"])
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert "1.0.0" in captured.out

    def test_help_flag(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["--help"])
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert "intervalo" in captured.out.lower() or "interval" in captured.out.lower()

    def test_main_starts_engine(self):
        with patch("move_mouse.main.Engine") as MockEngine:
            instance = MockEngine.return_value
            with patch("signal.pause", side_effect=KeyboardInterrupt):
                result = main([])
            assert result == 0
            instance.start.assert_called_once()
            instance.stop.assert_called_once()
