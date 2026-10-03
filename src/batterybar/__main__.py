"""Entry point: python -m batterybar [--selftest]."""
from __future__ import annotations

import argparse
import ctypes
import json
import logging
import logging.handlers
import sys

from . import __app_name__, __version__, config


def _fix_console_encoding() -> None:
    """Avoid cp1252 UnicodeEncodeError for icons/umlauts on Windows consoles."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass


def _enable_dpi_awareness() -> None:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # per-monitor aware
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


def _setup_logging(settings: dict) -> None:
    cfg = settings.get("logging", {})
    if not cfg.get("enabled", True):
        return
    config.LOGS_DIR.mkdir(exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        config.LOGS_DIR / "batterybar.log",
        maxBytes=512 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    logging.basicConfig(
        level=getattr(logging, str(cfg.get("level", "INFO")).upper(), logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        handlers=[handler, logging.StreamHandler(sys.stderr)],
    )


def _selftest() -> int:
    """Validate config + battery read without opening the GUI."""
    from . import battery

    settings = config.load_settings()
    t = settings["thresholds"]
    status = battery.read_status(
        low_threshold=int(t["low"]), critical_threshold=int(t["critical"])
    )
    details = battery.read_power_details()
    result = {
        "app": __app_name__,
        "version": __version__,
        "config_file": str(config.SETTINGS_FILE),
        "local_file_exists": config.LOCAL_SETTINGS_FILE.exists(),
        "battery": {
            "present": status.present,
            "percent": status.percent,
            "state": status.state,
            "charging": status.charging,
            "ac_online": status.ac_online,
            "seconds_remaining": status.seconds_remaining,
        },
        "power_details": None if details is None else {
            "max_mwh": details.max_mwh,
            "remaining_mwh": details.remaining_mwh,
            "rate_mw": details.rate_mw,
            "estimated_s": details.estimated_s,
        },
        "fields": battery.render_fields(status, details=details),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="batterybar", description=__app_name__)
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="read config + battery status, print JSON, exit (no GUI)",
    )
    args = parser.parse_args(argv)

    _fix_console_encoding()
    settings = config.load_settings()
    _setup_logging(settings)

    if args.selftest:
        return _selftest()

    _enable_dpi_awareness()
    from .bar_window import BarWindow

    BarWindow().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
