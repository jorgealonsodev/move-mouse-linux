"""Tests para el monitor de sesión."""

from unittest.mock import MagicMock, patch

from move_mouse.services.session_monitor import SessionMonitor


class TestSessionMonitor:
    def test_on_lock_callback(self):
        mon = SessionMonitor()
        cb = MagicMock()
        mon.on_lock(cb)
        mon._emit("lock")
        cb.assert_called_once()

    def test_on_unlock_callback(self):
        mon = SessionMonitor()
        cb = MagicMock()
        mon.on_unlock(cb)
        mon._emit("unlock")
        cb.assert_called_once()

    def test_on_suspend_callback(self):
        mon = SessionMonitor()
        cb = MagicMock()
        mon.on_suspend(cb)
        mon._emit("suspend")
        cb.assert_called_once()

    def test_on_resume_callback(self):
        mon = SessionMonitor()
        cb = MagicMock()
        mon.on_resume(cb)
        mon._emit("resume")
        cb.assert_called_once()

    def test_start_without_dbus_logs_warning(self, caplog):
        mon = SessionMonitor()
        with patch.dict("sys.modules", {"dbus": None}):
            mon.start()
        assert "No se pudo iniciar SessionMonitor" in caplog.text

    def test_prepare_for_sleep_true_emits_suspend(self):
        mon = SessionMonitor()
        cb = MagicMock()
        mon.on_suspend(cb)
        mon._on_prepare_for_sleep(True)
        cb.assert_called_once()

    def test_prepare_for_sleep_false_emits_resume(self):
        mon = SessionMonitor()
        cb = MagicMock()
        mon.on_resume(cb)
        mon._on_prepare_for_sleep(False)
        cb.assert_called_once()
