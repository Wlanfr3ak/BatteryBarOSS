"""JSON configuration: defaults <- settings.json <- settings.local.json.

secrets.json (gitignored) is merged under the "secrets" key and never
written back.

ROOT_DIR: source tree -> repo root; frozen exe (PyInstaller) ->
%LOCALAPPDATA%\\BatteryBarOSS so installed apps write per-user data
(settings, stats, logs) to a writable location.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _root_dir() -> Path:
    if getattr(sys, "frozen", False):
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "BatteryBarOSS"
    return Path(__file__).resolve().parents[2]


ROOT_DIR = _root_dir()
CONFIG_DIR = ROOT_DIR / "config"
LOGS_DIR = ROOT_DIR / "logs"
SETTINGS_FILE = CONFIG_DIR / "settings.json"
LOCAL_SETTINGS_FILE = CONFIG_DIR / "settings.local.json"
SECRETS_FILE = CONFIG_DIR / "secrets.json"
STATS_FILE = CONFIG_DIR / "stats.local.json"
HP_BIOS_FILE = CONFIG_DIR / "hp_bios.local.json"

DEFAULT_SETTINGS: dict = {
    "window": {
        "width": 220,
        "height": 28,
        "x": None,
        "y": None,
        "corner": "top-right",
        "offset_x": 20,
        "offset_y": 20,
        "opacity": 0.92,
        "always_on_top": True,
        "click_through": False,
        "lock_position": False,
        "display_mode": "default",
        "format": "{state_icon} {percent}% · {time}",
    },
    "estimation": {
        "soft_min_percent": 5.0,
    },
    "display": {
        "font_family": "Segoe UI",
        "font_size": 11,
        "font_weight": "bold",
        "padding": 4,
    },
    "thresholds": {"low": 30, "critical": 15},
    "colors": {
        "background": "#1e1e1e",
        "border": "#3a3a3a",
        "text": "#ffffff",
        "fill_discharging": "#4caf50",
        "fill_low": "#ff9800",
        "fill_critical": "#f44336",
        "fill_charging": "#2196f3",
        "fill_charged": "#9e9e9e",
        "fill_nobattery": "#555555",
    },
    "warnings": {"enabled": True, "beep": False, "toast_seconds": 5},
    "update_interval_ms": 1000,
    "logging": {"enabled": True, "level": "INFO"},
}


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for key, value in override.items():
        if key.startswith("_"):
            continue
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def load_settings() -> dict:
    """Effective settings = DEFAULTS <- settings.json <- settings.local.json."""
    settings = _deep_merge(DEFAULT_SETTINGS, _read_json(SETTINGS_FILE))
    settings = _deep_merge(settings, _read_json(LOCAL_SETTINGS_FILE))
    secrets = _read_json(SECRETS_FILE)
    if secrets:
        settings["secrets"] = secrets
    return settings


def save_local(patch: dict) -> None:
    """Merge `patch` into settings.local.json (user overrides, gitignored)."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    current = _read_json(LOCAL_SETTINGS_FILE)
    merged = _deep_merge(current, patch)
    LOCAL_SETTINGS_FILE.write_text(
        json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
