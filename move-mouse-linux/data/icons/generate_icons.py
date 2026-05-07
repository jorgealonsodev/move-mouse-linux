#!/usr/bin/env python3
"""Genera placeholders PNG para los iconos de Move Mouse Linux.

Cada PNG es un cuadrado del color del tema Kanagawa (#2e3440) con un
cursor de mouse simple dibujado en blanco. Se necesita Pillow para
ejecutar este script.

Uso: python3 generate_icons.py
"""

import os
import struct
import zlib

SIZES = [16, 24, 32, 48, 64, 128, 256]
BG_COLOR = (46, 52, 64)       # #2e3440 - Kanagawa background
FG_COLOR = (216, 222, 233)    # #d8dee9 - Kanagawa foreground


def create_png(size: int) -> bytes:
    """Crea un PNG minimal con un cursor de mouse dibujado."""
    # Crear imagen RGBA
    pixels = bytearray()
    for y in range(size):
        for x in range(size):
            # Dibujar un cursor de mouse simple (triángulo apuntando arriba-izquierda)
            # Escalar las coordenadas del cursor al tamaño de la imagen
            sx = x * 128 / size
            sy = y * 128 / size

            # Cursor polygon: M 24 16 L 24 104 L 44 84 L 60 112 L 74 104 L 58 76 L 84 76 Z
            # Simplified: check if point is inside the cursor triangle
            inside = False
            # Main triangle body
            if 24 <= sx <= 84 and 16 <= sy <= 104:
                # Left edge (vertical)
                if sx >= 24:
                    # Right edge (diagonal from 24,16 to 84,76)
                    right_edge_y = 16 + (sx - 24) * (76 - 16) / (84 - 24)
                    if sy <= right_edge_y + 8:
                        # Bottom-left diagonal (from 24,104 to 44,84)
                        bl_y = 104 - (sx - 24) * (104 - 84) / (44 - 24)
                        if sy >= bl_y - 8:
                            inside = True
            # Arrow tip
            if 44 <= sx <= 74 and 76 <= sy <= 112:
                tip_left = 76 + (sx - 44) * (104 - 76) / (74 - 44)
                tip_right = 76 + (sx - 60) * (104 - 76) / (74 - 60) if sx > 60 else 112
                if tip_left - 4 <= sy <= tip_right + 4:
                    inside = True

            if inside:
                pixels.extend([*FG_COLOR, 255])
            else:
                pixels.extend([*BG_COLOR, 255])

    return _png_from_pixels(pixels, size, size)


def _png_from_pixels(pixels: bytearray, width: int, height: int) -> bytes:
    """Convierte pixels RGBA a un PNG válido."""
    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)

    # Signature
    sig = b'\x89PNG\r\n\x1a\n'

    # IHDR
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    ihdr = chunk(b'IHDR', ihdr_data)

    # IDAT
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter none
        row_start = y * width * 4
        raw.extend(pixels[row_start:row_start + width * 4])
    compressed = zlib.compress(bytes(raw), 9)
    idat = chunk(b'IDAT', compressed)

    # IEND
    iend = chunk(b'IEND', b'')

    return sig + ihdr + idat + iend


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for size in SIZES:
        png_data = create_png(size)
        out_dir = os.path.join(base_dir, 'hicolor', f'{size}x{size}', 'apps')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, 'org.movemouse.MoveMouse.png')
        with open(out_path, 'wb') as f:
            f.write(png_data)
        print(f"  {size}x{size} -> {out_path}")
    print("Iconos generados.")


if __name__ == '__main__':
    main()
