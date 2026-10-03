"""Machine/system identification + optional HP Battery Health Manager cache.

Machine info comes from the registry (no admin needed).
The HP Battery Health Manager (BHM) BIOS mode is read by
tools/read_bios_battery_mode.bat (needs elevation, HP WMI interface)
which caches the result in config/hp_bios.local.json.
"""
from __future__ import annotations

import json
import winreg
from dataclasses import dataclass

from . import config


@dataclass
class MachineInfo:
    manufacturer: str
    product_name: str
    bios_version: str
    is_hp: bool


def read_machine_info() -> MachineInfo:
    """Read the machine type from the registry (stdlib, no elevation)."""
    def _get(name: str) -> str:
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\SystemInformation",
            )
            value, _ = winreg.QueryValueEx(key, name)
            winreg.CloseKey(key)
            return str(value).strip()
        except OSError:
            return ""

    manufacturer = _get("SystemManufacturer")
    return MachineInfo(
        manufacturer=manufacturer,
        product_name=_get("SystemProductName"),
        bios_version=_get("BIOSVersion"),
        is_hp=manufacturer.upper() in ("HP", "HEWLETT-PACKARD", "HEWLETT PACKARD"),
    )


def read_hp_bios_cache() -> dict | None:
    """Cached HP BHM result written by tools/read_bios_battery_mode.bat."""
    try:
        data = json.loads(config.HP_BIOS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) and data.get("mode") else None
    except (OSError, json.JSONDecodeError):
        return None
