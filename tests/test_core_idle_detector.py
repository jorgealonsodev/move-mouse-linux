"""Tests para el detector de inactividad."""

import time

from move_mouse.core.idle_detector import IdleDetector


class TestIdleDetector:
    def test_default_polling_interval(self):
        det = IdleDetector()
        assert det._polling_interval_ms == 1000

    def test_add_callback(self):
        det = IdleDetector()

        def cb(idle_ms):
            pass

        det.add_callback(cb)
        assert len(det._callbacks) == 1

    def test_get_idle_time_dbus_fallback(self, mocker):
        det = IdleDetector()
        det._primary_backend = True
        mocker.patch.object(
            det, "_get_idle_time_xscreensaver", side_effect=RuntimeError("X11 fail")
        )
        dbus_mock = mocker.patch.object(det, "_get_idle_time_dbus", return_value=42)
        result = det._get_idle_time()
        assert result == 42
        assert det._primary_backend is False
        dbus_mock.assert_called_once()

    def test_run_invokes_callbacks(self, mocker):
        det = IdleDetector(polling_interval_ms=50)
        mocker.patch.object(det, "_get_idle_time", return_value=123)
        called = []

        def cb(idle_ms):
            called.append(idle_ms)

        det.add_callback(cb)
        det.start()
        time.sleep(0.15)
        det.stop()
        det.join(timeout=1)
        assert len(called) >= 1
        assert called[0] == 123

    def test_callback_exception_does_not_crash(self, mocker, caplog):
        det = IdleDetector(polling_interval_ms=50)
        mocker.patch.object(det, "_get_idle_time", return_value=0)

        def bad_cb(idle_ms):
            raise RuntimeError("ops")

        det.add_callback(bad_cb)
        det.start()
        time.sleep(0.15)
        det.stop()
        det.join(timeout=1)
        assert "ops" in caplog.text
