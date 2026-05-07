"""CLI entry point for Move Mouse Linux."""

import argparse
import logging
import sys
from typing import List, Optional

from move_mouse.core.engine import Engine


def _cli_mode(args) -> int:
    """Run in command-line mode (no graphical interface)."""
    logger = logging.getLogger(__name__)
    logger.info("Starting Move Mouse Linux (CLI mode)")

    def tick() -> None:
        logger.debug("Engine tick")

    engine = Engine(tick_callback=tick, interval_ms=args.interval)
    engine.start()

    try:
        import signal

        signal.pause()
    except KeyboardInterrupt:
        logger.info("Interrupt received, stopping...")
    finally:
        engine.stop()
        logger.info("Engine stopped, exiting CLI mode")

    return 0


def _gui_mode(args) -> int:
    """Run the GTK application with system tray."""
    import gi

    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk

    from move_mouse.ui.app import MoveMouseApp

    logger = logging.getLogger(__name__)
    logger.info("Starting Move Mouse Linux (GTK mode)")

    app = MoveMouseApp()
    return app.run(None)


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="move-mouse-linux",
        description="Simulates user activity to prevent session lock.",
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s 1.0.0"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug logging"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30000,
        help="Interval between actions in milliseconds (default: 30000)",
    )
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Run in CLI mode without graphical interface",
    )
    args = parser.parse_args(argv)

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    if args.no_gui:
        return _cli_mode(args)

    try:
        return _gui_mode(args)
    except Exception as exc:
        logging.getLogger(__name__).warning(
            "Could not start graphical interface (%s), falling back to CLI mode", exc
        )
        return _cli_mode(args)


if __name__ == "__main__":
    sys.exit(main())
