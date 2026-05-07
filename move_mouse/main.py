"""Punto de entrada CLI de Move Mouse Linux."""

import argparse
import logging
import sys
from typing import List, Optional

from move_mouse.core.engine import Engine


def main(argv: Optional[List[str]] = None) -> int:
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(
        prog="move-mouse-linux",
        description="Simula actividad de usuario para prevenir bloqueo de sesión.",
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s 1.0.0"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Activa logging debug"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30000,
        help="Intervalo entre acciones en milisegundos (default: 30000)",
    )
    args = parser.parse_args(argv)

    nivel = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=nivel,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    logger = logging.getLogger(__name__)
    logger.info("Iniciando Move Mouse Linux")

    def tick() -> None:
        logger.debug("Tick del motor")

    engine = Engine(tick_callback=tick, interval_ms=args.interval)
    engine.start()

    try:
        import signal

        signal.pause()
    except KeyboardInterrupt:
        logger.info("Interrupción recibida, deteniendo...")
    finally:
        engine.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())
