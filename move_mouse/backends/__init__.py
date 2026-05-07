"""Backends de control de mouse (X11, Wayland).

Re-exporta desde mouse_controller para mantener compatibilidad mientras
se satisface la estructura de módulos del diseño.

El diseño especifica un paquete ``backends/`` con una ABC ``MouseBackend``
y backends concretos ``X11Backend``, ``WaylandBackend``. Actualmente la
implementación reside en ``mouse_controller.py``; este paquete re-exporta
los símbolos para cumplir con la estructura esperada sin una refactorización
arriesgada.
"""

from move_mouse.mouse_controller import (
    MouseController,
    CursorDirection,
    CursorSpeed,
    SPEED_DELAYS,
)

__all__ = [
    "MouseController",
    "CursorDirection",
    "CursorSpeed",
    "SPEED_DELAYS",
]
