"""Application settings model."""

import json
import logging
import os
import tempfile
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Settings:
    """Move Mouse settings with default values matching the original Windows app."""

    # Interval
    lower_interval: int = 30  # seconds
    upper_interval: int = 60  # seconds
    random_interval: bool = False

    # Auto Pause/Resume
    auto_pause: bool = False
    auto_resume: bool = False
    auto_resume_seconds: int = 30

    # Behavior
    active_when_locked: bool = False
    minimise_on_stop: bool = False
    start_at_launch: bool = False

    # UI Options
    hide_from_taskbar: bool = False
    hide_main_window: bool = False
    hide_system_tray_icon: bool = False
    show_system_tray_notifications: bool = False
    show_taskbar_status: bool = True

    # Actions (list of action dicts)
    actions: List[Dict[str, Any]] = field(default_factory=list)

    # Schedules
    schedules: List[Dict[str, Any]] = field(default_factory=list)

    # Blackouts
    blackouts: List[Dict[str, Any]] = field(default_factory=list)

    # Logging
    enable_logging: bool = False
    log_level: str = "INFO"

    # UI / Platform Options (from original Windows app)
    hide_from_alt_tab: bool = False
    topmost_when_running: bool = False
    prevent_screen_burn: bool = False
    show_move_mouse_status: bool = False
    disable_button_animation: bool = False
    pause_on_battery: bool = False
    launch_at_logon: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Settings":
        """Create an instance from a dictionary, filling missing fields with defaults."""
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)

    def save(self, path: str) -> None:
        """Save settings to JSON atomically."""
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", dir=directory, delete=False, suffix=".json"
        ) as tmp:
            json.dump(self.to_dict(), tmp, indent=2)
            tmp_name = tmp.name
        os.replace(tmp_name, path)
        logger.info("Settings saved to %s", path)

    @classmethod
    def load(cls, path: str) -> "Settings":
        """Load settings from JSON.

        If the file does not exist or is corrupt, returns defaults.
        """
        if not os.path.exists(path):
            logger.info(
                "Settings file not found at %s, using defaults", path
            )
            return cls()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("Content is not a dictionary")
            logger.info("Settings loaded from %s", path)
            return cls.from_dict(data)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.error(
                "Corrupt settings at %s: %s. Using defaults.", path, exc
            )
            return cls()

    @classmethod
    def default_path(cls) -> str:
        """Return the default path based on XDG."""
        try:
            from xdg.BaseDirectory import xdg_config_home

            config_home = xdg_config_home  # type: ignore
        except ImportError:
            config_home = os.path.expanduser("~/.config")
        return os.path.join(config_home, "move-mouse-linux", "settings.json")
