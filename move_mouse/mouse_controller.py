"""Mouse pointer control via X11 XTest (X11) or ydotool (Wayland)."""

import logging
import os
import subprocess
import time
from enum import Enum
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Backend detection
# ---------------------------------------------------------------------------

def _is_wayland() -> bool:
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"

# ---------------------------------------------------------------------------
# X11 backend (primary)
# ---------------------------------------------------------------------------

class _X11Controller:
    """Mouse control via python-xlib + XTest extension."""

    def __init__(self):
        try:
            from Xlib import display as xdisplay, X as Xlib_X
            from Xlib.ext import xtest
            self._display = xdisplay.Display()
            self._xtest = xtest
            self._X = Xlib_X
            self._root = self._display.screen().root
            self._available = True
        except Exception as exc:
            logger.warning("X11 backend unavailable: %s", exc)
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def get_position(self) -> Tuple[int, int]:
        data = self._root.query_pointer()
        return data.root_x, data.root_y

    def move_relative(self, dx: int, dy: int):
        data = self._root.query_pointer()
        tx = data.root_x + dx
        ty = data.root_y + dy
        self._xtest.fake_input(self._display, self._X.MotionNotify, x=tx, y=ty)
        self._display.sync()

    def move_absolute(self, x: int, y: int):
        self._xtest.fake_input(self._display, self._X.MotionNotify, x=x, y=y)
        self._display.sync()

    def press(self, button: int = 1):
        """Press a mouse button without releasing it."""
        bm = {1: 1, 2: 2, 3: 3}
        b = bm.get(button, 1)
        self._xtest.fake_input(self._display, self._X.ButtonPress, detail=b)
        self._display.sync()

    def release(self, button: int = 1):
        """Release a previously pressed mouse button."""
        bm = {1: 1, 2: 2, 3: 3}
        b = bm.get(button, 1)
        self._xtest.fake_input(self._display, self._X.ButtonRelease, detail=b)
        self._display.sync()

    def click(self, button: int = 1):
        """Mouse click. button: 1=left, 2=middle, 3=right."""
        bm = {1: 1, 2: 2, 3: 3}
        b = bm.get(button, 1)
        self._xtest.fake_input(self._display, self._X.ButtonPress, detail=b)
        self._display.sync()
        self._xtest.fake_input(self._display, self._X.ButtonRelease, detail=b)
        self._display.sync()

# ---------------------------------------------------------------------------
# Wayland fallback (ydotool)
# ---------------------------------------------------------------------------

class _YdotoolController:
    """Mouse control via ydotool (requires uinput + permissions)."""

    def __init__(self):
        self._available = False
        try:
            result = subprocess.run(
                ["ydotool", "--version"], capture_output=True, timeout=3
            )
            if result.returncode == 0:
                self._available = True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("ydotool not found for Wayland backend")

    @property
    def available(self) -> bool:
        return self._available

    def move_relative(self, dx: int, dy: int):
        try:
            subprocess.run(
                ["ydotool", "mousemove", "--", str(dx), str(dy)],
                capture_output=True, timeout=2,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
            logger.warning("Error in relative movement with ydotool: %s", exc)

    def move_absolute(self, x: int, y: int):
        try:
            subprocess.run(
                ["ydotool", "mousemove", "--absolute", "--", str(x), str(y)],
                capture_output=True, timeout=2,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
            logger.warning("Error in absolute movement with ydotool: %s", exc)

    def press(self, button: int = 1):
        """Press a mouse button (ydotool does not support native hold)."""
        bmap = {1: "mousedown", 2: "mousedown", 3: "mousedown"}
        try:
            subprocess.run(
                ["ydotool", bmap.get(button, "mousedown"), str(button)],
                capture_output=True, timeout=2,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
            logger.warning("Error in press with ydotool: %s", exc)

    def release(self, button: int = 1):
        """Release a mouse button (ydotool does not support native hold)."""
        bmap = {1: "mouseup", 2: "mouseup", 3: "mouseup"}
        try:
            subprocess.run(
                ["ydotool", bmap.get(button, "mouseup"), str(button)],
                capture_output=True, timeout=2,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
            logger.warning("Error in release with ydotool: %s", exc)

    def click(self, button: int = 1):
        bmap = {1: "click", 2: "click", 3: "click"}
        try:
            subprocess.run(
                ["ydotool", bmap.get(button, "click"), str(button)],
                capture_output=True, timeout=2,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
            logger.warning("Error in click with ydotool: %s", exc)

# ---------------------------------------------------------------------------
# Unified controller
# ---------------------------------------------------------------------------

class CursorDirection(Enum):
    SQUARE = "square"
    CIRCLE = "circle"
    NONE = "none"
    RANDOM = "random"
    NORTH = "north"
    NORTH_EAST = "north_east"
    EAST = "east"
    SOUTH_EAST = "south_east"
    SOUTH = "south"
    SOUTH_WEST = "south_west"
    WEST = "west"
    NORTH_WEST = "north_west"
    UP_AND_DOWN = "up_and_down"
    DOWN_AND_UP = "down_and_up"
    LEFT_AND_RIGHT = "left_and_right"
    RIGHT_AND_LEFT = "right_and_left"


class CursorSpeed(Enum):
    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"
    CUSTOM = "custom"


SPEED_DELAYS = {
    CursorSpeed.SLOW: 10,      # ms per pixel
    CursorSpeed.NORMAL: 5,
    CursorSpeed.FAST: 0,
}


class MouseController:
    """Unified mouse controller for X11 and Wayland."""

    def __init__(self):
        if not _is_wayland():
            self._backend = _X11Controller()
            logger.info("Mouse backend: X11 (python-xlib + XTest)")
        else:
            self._backend = _YdotoolController()
            logger.info("Mouse backend: Wayland (ydotool)")
        self._break_on_user_activity: bool = False
        self._user_activity_detected: bool = False
        self._expected_pos: Optional[Tuple[int, int]] = None  # expected pos after our last move

    @property
    def available(self) -> bool:
        return self._backend.available

    @property
    def break_on_user_activity(self) -> bool:
        return self._break_on_user_activity

    @break_on_user_activity.setter
    def break_on_user_activity(self, value: bool):
        self._break_on_user_activity = value

    @property
    def user_activity_detected(self) -> bool:
        return self._user_activity_detected

    def get_position(self) -> Tuple[int, int]:
        if hasattr(self._backend, "get_position"):
            return self._backend.get_position()
        return (0, 0)

    def _check_user_activity(self) -> bool:
        """Return True if user moved the mouse to an unexpected position."""
        if not self._break_on_user_activity:
            return False
        if self._expected_pos is None:
            # No reference yet — can't detect activity
            return False
        current = self.get_position()
        ex, ey = self._expected_pos
        # Allow 2px tolerance for rounding/multi-monitor offsets
        if abs(current[0] - ex) > 2 or abs(current[1] - ey) > 2:
            self._user_activity_detected = True
            logger.debug(
                "User activity: expected (%d,%d) got (%d,%d)", ex, ey, *current
            )
            return True
        return False

    def _record_position(self):
        pos = self.get_position()
        self._expected_pos = pos

    def _move_one_pixel(self, dx: int, dy: int):
        self._backend.move_relative(dx, dy)

    def move_from_current(self, dx: int, dy: int):
        """Move dx,dy pixels from current position."""
        if self._check_user_activity():
            return
        # Compute expected position before moving
        current = self.get_position()
        self._move_one_pixel(dx, dy)
        # Record where we expect the cursor to be after this move
        self._expected_pos = (current[0] + dx, current[1] + dy)

    def _move_direction(self, distance: int, dx: int, dy: int, delay_ms: int):
        logger.debug("Moving cursor: direction (%d, %d), distance=%d, delay=%dms", dx, dy, distance, delay_ms)
        for _ in range(distance):
            self.move_from_current(dx, dy)
            if self._user_activity_detected:
                break
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)

    def move_north(self, distance: int, delay_ms: int = 0):
        self._move_direction(distance, 0, -1, delay_ms)

    def move_south(self, distance: int, delay_ms: int = 0):
        self._move_direction(distance, 0, 1, delay_ms)

    def move_east(self, distance: int, delay_ms: int = 0):
        self._move_direction(distance, 1, 0, delay_ms)

    def move_west(self, distance: int, delay_ms: int = 0):
        self._move_direction(distance, -1, 0, delay_ms)

    def move_north_east(self, distance: int, delay_ms: int = 0):
        self._move_direction(distance, 1, -1, delay_ms)

    def move_south_east(self, distance: int, delay_ms: int = 0):
        self._move_direction(distance, 1, 1, delay_ms)

    def move_south_west(self, distance: int, delay_ms: int = 0):
        self._move_direction(distance, -1, 1, delay_ms)

    def move_north_west(self, distance: int, delay_ms: int = 0):
        self._move_direction(distance, -1, -1, delay_ms)

    def move_to(self, x: int, y: int):
        if hasattr(self._backend, "move_absolute"):
            self._backend.move_absolute(x, y)

    def click(self, button: int = 1):
        self._backend.click(button)

    def press(self, button: int = 1):
        """Press a mouse button without releasing it."""
        if hasattr(self._backend, "press"):
            self._backend.press(button)
        else:
            self._backend.click(button)

    def release(self, button: int = 1):
        """Release a previously pressed mouse button."""
        if hasattr(self._backend, "release"):
            self._backend.release(button)
        else:
            self._backend.click(button)

    def execute_move_action(
        self,
        direction: CursorDirection,
        distance: int,
        delay_ms: int = 5,
        random_distance: bool = False,
        upper_distance: Optional[int] = None,
    ) -> bool:
        """Execute a move action. Returns True if aborted by user activity."""
        import random

        self._user_activity_detected = False

        # Record current position as baseline so first pixel is also checked
        self._expected_pos = self.get_position()

        actual_distance = distance
        if random_distance and upper_distance and upper_distance > distance:
            actual_distance = random.randint(distance, upper_distance)

        method_map = {
            CursorDirection.NORTH: lambda: self.move_north(actual_distance, delay_ms),
            CursorDirection.SOUTH: lambda: self.move_south(actual_distance, delay_ms),
            CursorDirection.EAST: lambda: self.move_east(actual_distance, delay_ms),
            CursorDirection.WEST: lambda: self.move_west(actual_distance, delay_ms),
            CursorDirection.NORTH_EAST: lambda: self.move_north_east(actual_distance, delay_ms),
            CursorDirection.SOUTH_EAST: lambda: self.move_south_east(actual_distance, delay_ms),
            CursorDirection.SOUTH_WEST: lambda: self.move_south_west(actual_distance, delay_ms),
            CursorDirection.NORTH_WEST: lambda: self.move_north_west(actual_distance, delay_ms),
        }

        if direction == CursorDirection.NONE:
            self._move_one_pixel(0, 0)
            self._record_position()
            return False

        if direction in method_map:
            method_map[direction]()
            return self._user_activity_detected

        if direction == CursorDirection.UP_AND_DOWN:
            self.move_north(actual_distance, delay_ms)
            if not self._user_activity_detected:
                self.move_south(actual_distance, delay_ms)
            return self._user_activity_detected

        if direction == CursorDirection.DOWN_AND_UP:
            self.move_south(actual_distance, delay_ms)
            if not self._user_activity_detected:
                self.move_north(actual_distance, delay_ms)
            return self._user_activity_detected

        if direction == CursorDirection.LEFT_AND_RIGHT:
            self.move_west(actual_distance, delay_ms)
            if not self._user_activity_detected:
                self.move_east(actual_distance, delay_ms)
            return self._user_activity_detected

        if direction == CursorDirection.RIGHT_AND_LEFT:
            self.move_east(actual_distance, delay_ms)
            if not self._user_activity_detected:
                self.move_west(actual_distance, delay_ms)
            return self._user_activity_detected

        if direction == CursorDirection.SQUARE:
            self.move_east(actual_distance, delay_ms)
            if not self._user_activity_detected:
                self.move_south(actual_distance, delay_ms)
            if not self._user_activity_detected:
                self.move_west(actual_distance, delay_ms)
            if not self._user_activity_detected:
                self.move_north(actual_distance, delay_ms)
            return self._user_activity_detected

        if direction == CursorDirection.CIRCLE:
            # Approximate a circle using 8 directional segments
            steps = max(4, actual_distance // 4)
            radius = max(1, actual_distance // 4)
            for _ in range(steps):
                if self._user_activity_detected:
                    break
                # 8 points around a circle: N, NE, E, SE, S, SW, W, NW
                for ddx, ddy in [(0, -1), (1, -1), (1, 0), (1, 1),
                                 (0, 1), (-1, 1), (-1, 0), (-1, -1)]:
                    if self._user_activity_detected:
                        break
                    self.move_from_current(ddx * radius, ddy * radius)
                    if delay_ms > 0:
                        time.sleep(delay_ms / 1000.0)
            return self._user_activity_detected

        if direction == CursorDirection.RANDOM:
            remaining = actual_distance
            last_dir = 0
            dirs = [1, 2, 3, 4, 5, 6, 7, 8]
            dir_move = {
                1: lambda d: self.move_north(d, delay_ms),
                2: lambda d: self.move_east(d, delay_ms),
                3: lambda d: self.move_south(d, delay_ms),
                4: lambda d: self.move_west(d, delay_ms),
                5: lambda d: self.move_north_east(d, delay_ms),
                6: lambda d: self.move_south_east(d, delay_ms),
                7: lambda d: self.move_south_west(d, delay_ms),
                8: lambda d: self.move_north_west(d, delay_ms),
            }
            while remaining > 0 and not self._user_activity_detected:
                step = random.randint(1, min(remaining, 150))
                remaining -= step
                d = last_dir
                while d == last_dir:
                    d = random.choice(dirs)
                last_dir = d
                dir_move[d](step)
            return self._user_activity_detected

        return False
