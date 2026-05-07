"""Modelo de configuración de la aplicación."""

import json
import logging
import os
import tempfile
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Settings:
    """Configuración de Move Mouse con valores por defecto."""

    interval_lower_ms: int = 30000
    interval_upper_ms: Optional[int] = None
    action_list: List[Dict[str, Any]] = field(default_factory=list)
    auto_pause_enabled: bool = True
    auto_pause_threshold_ms: int = 3000
    auto_resume_enabled: bool = True
    auto_resume_after_ms: int = 10000
    cursor_direction: str = "square"
    cursor_distance: int = 5
    cursor_speed: str = "normal"

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la configuración a diccionario."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Settings":
        """Crea una instancia desde un diccionario, completando campos faltantes con defaults."""
        campos_conocidos = {f.name for f in cls.__dataclass_fields__.values()}
        filtrado = {k: v for k, v in data.items() if k in campos_conocidos}
        return cls(**filtrado)

    def save(self, path: str) -> None:
        """Guarda la configuración en JSON de forma atómica."""
        directorio = os.path.dirname(path)
        if directorio:
            os.makedirs(directorio, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", dir=directorio, delete=False, suffix=".json"
        ) as tmp:
            json.dump(self.to_dict(), tmp, indent=2)
            tmp_name = tmp.name
        os.replace(tmp_name, path)
        logger.debug("Configuración guardada en %s", path)

    @classmethod
    def load(cls, path: str) -> "Settings":
        """Carga configuración desde JSON.

        Si el archivo no existe o está corrupto, devuelve defaults.
        """
        if not os.path.exists(path):
            logger.info(
                "Archivo de configuración no encontrado en %s, usando defaults", path
            )
            return cls()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("El contenido no es un diccionario")
            return cls.from_dict(data)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.error(
                "Configuración corrupta en %s: %s. Usando defaults.", path, exc
            )
            return cls()

    @classmethod
    def default_path(cls) -> str:
        """Devuelve la ruta por defecto basada en XDG."""
        try:
            from xdg.BaseDirectory import xdg_config_home

            config_home = xdg_config_home  # type: ignore
        except ImportError:
            config_home = os.path.expanduser("~/.config")
        return os.path.join(config_home, "move-mouse-linux", "settings.json")
