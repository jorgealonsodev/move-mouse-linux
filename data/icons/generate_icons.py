#!/usr/bin/env python3
"""Generate transparent PNG icons for Move Mouse Linux.

The generated icon is a centered mouse cursor with a dark outline and a light
fill. The outline is important for status trays because panels can be either
light or dark, and small icon sizes are usually rendered at 16px or 24px.
"""

from __future__ import annotations

import os
import struct
import zlib


SIZES = [16, 24, 32, 48, 64, 128, 256]
BG_COLOR = (0, 0, 0, 0)
OUTLINE_COLOR = (46, 52, 64, 255)
FILL_COLOR = (236, 239, 244, 255)

# Cursor polygon in a 128x128 coordinate system.
# Shape: classic pointer arrow, centered with enough padding for 16px trays.
CURSOR_POLYGON = [
    (34, 18),
    (34, 98),
    (52, 80),
    (67, 112),
    (82, 105),
    (66, 73),
    (92, 73),
]


def create_png(size: int) -> bytes:
    """Create one RGBA PNG icon at the requested size."""
    pixels = bytearray()
    outline_width = max(1.0, 128 / size)

    for y in range(size):
        for x in range(size):
            sx = (x + 0.5) * 128 / size
            sy = (y + 0.5) * 128 / size

            if _inside_polygon(sx, sy, CURSOR_POLYGON):
                pixels.extend(FILL_COLOR)
            elif _near_polygon_edge(sx, sy, CURSOR_POLYGON, outline_width * 1.8):
                pixels.extend(OUTLINE_COLOR)
            else:
                pixels.extend(BG_COLOR)

    return _png_from_pixels(pixels, size, size)


def _inside_polygon(x: float, y: float, polygon: list[tuple[int, int]]) -> bool:
    """Return whether the point is inside the polygon using ray casting."""
    inside = False
    j = len(polygon) - 1
    for i, (xi, yi) in enumerate(polygon):
        xj, yj = polygon[j]
        intersects = (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi
        if intersects:
            inside = not inside
        j = i
    return inside


def _near_polygon_edge(
    x: float,
    y: float,
    polygon: list[tuple[int, int]],
    max_distance: float,
) -> bool:
    """Return whether the point is close enough to any polygon edge."""
    for index, start in enumerate(polygon):
        end = polygon[(index + 1) % len(polygon)]
        if _distance_to_segment(x, y, start, end) <= max_distance:
            return True
    return False


def _distance_to_segment(
    x: float,
    y: float,
    start: tuple[int, int],
    end: tuple[int, int],
) -> float:
    """Calculate distance from a point to a line segment."""
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1

    if dx == 0 and dy == 0:
        return ((x - x1) ** 2 + (y - y1) ** 2) ** 0.5

    t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
    projection_x = x1 + t * dx
    projection_y = y1 + t * dy
    return ((x - projection_x) ** 2 + (y - projection_y) ** 2) ** 0.5


def _png_from_pixels(pixels: bytearray, width: int, height: int) -> bytes:
    """Convert RGBA pixels to a valid PNG byte stream."""

    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        payload = chunk_type + data
        return (
            struct.pack(">I", len(data))
            + payload
            + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)
        )

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))

    raw = bytearray()
    for y in range(height):
        raw.append(0)
        row_start = y * width * 4
        raw.extend(pixels[row_start : row_start + width * 4])

    idat = chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    iend = chunk(b"IEND", b"")
    return signature + ihdr + idat + iend


def main() -> None:
    """Generate all hicolor PNG icon sizes."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for size in SIZES:
        png_data = create_png(size)
        out_dir = os.path.join(base_dir, "hicolor", f"{size}x{size}", "apps")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "org.movemouse.MoveMouse.png")
        with open(out_path, "wb") as file:
            file.write(png_data)
        print(f"{size}x{size} -> {out_path}")


if __name__ == "__main__":
    main()
