"""Battery status via Win32 GetSystemPowerStatus (stdlib ctypes only)."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass


class _SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [
        ("ACLineStatus", wintypes.BYTE),
        ("BatteryFlag", wintypes.BYTE),
        ("BatteryLifePercent", wintypes.BYTE),
        ("Reserved1", wintypes.BYTE),
        ("BatteryLifeTime", wintypes.DWORD),
        ("BatteryFullLifeTime", wintypes.DWORD),
    ]


_FLAG_HIGH = 0x01
_FLAG_LOW = 0x02
_FLAG_CRITICAL = 0x04
_FLAG_CHARGING = 0x08
_FLAG_NO_BATTERY = 0x80
_FLAG_UNKNOWN = 0xFF
_UNKNOWN_SECONDS = 0xFFFFFFFF
_UNKNOWN_PERCENT = 0xFF


@dataclass
class BatteryStatus:
    present: bool
    percent: int | None
    charging: bool
    ac_online: bool
    seconds_remaining: int | None
    state: str


def read_status(low_threshold: int = 30, critical_threshold: int = 15) -> BatteryStatus:
    """Read the current system power/battery status."""
    sps = _SYSTEM_POWER_STATUS()
    ok = ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(sps))
    if not ok:
        raise ctypes.WinError(ctypes.get_last_error())

    percent = None if sps.BatteryLifePercent == _UNKNOWN_PERCENT else int(sps.BatteryLifePercent)
    seconds = None if sps.BatteryLifeTime == _UNKNOWN_SECONDS else int(sps.BatteryLifeTime)
    ac_online = sps.ACLineStatus in (1, 2)  # 1 = online, 2 = backup power (UPS)
    flag = sps.BatteryFlag

    if flag in (_FLAG_NO_BATTERY, _FLAG_UNKNOWN):
        state = "nobattery"
    elif flag & _FLAG_CHARGING:
        state = "charging"
    elif percent is not None and percent <= critical_threshold:
        state = "critical"
    elif percent is not None and percent <= low_threshold:
        state = "low"
    elif ac_online and percent is not None and percent >= 100:
        state = "charged"
    elif ac_online:
        state = "ac"  # on AC, not charging, not full (e.g. charge limit)
    else:
        state = "discharging"

    return BatteryStatus(
        present=flag not in (_FLAG_NO_BATTERY, _FLAG_UNKNOWN),
        percent=percent,
        charging=bool(flag & _FLAG_CHARGING),
        ac_online=ac_online,
        seconds_remaining=seconds,
        state=state,
    )


def format_duration(seconds: int | None) -> str:
    """Format remaining seconds as '1:23 h'; '-' when unknown."""
    if seconds is None:
        return "—"
    hours, rem = divmod(seconds, 3600)
    minutes = rem // 60
    return f"{hours}:{minutes:02d} h"


STATE_TEXT_DE = {
    "charging": "Lädt",
    "discharging": "Entlädt",
    "low": "Niedrig",
    "critical": "Kritisch",
    "charged": "Voll",
    "ac": "Netzbetrieb",
    "nobattery": "Kein Akku",
}

STATE_ICON = {
    "charging": "⚡",
    "discharging": "",
    "low": "▼",
    "critical": "⚠",
    "charged": "✓",
    "ac": "🔌",
    "nobattery": "✕",
}

_FILL_COLOR_KEY = {
    "charging": "fill_charging",
    "discharging": "fill_discharging",
    "low": "fill_low",
    "critical": "fill_critical",
    "charged": "fill_charged",
    "ac": "fill_charged",
    "nobattery": "fill_nobattery",
}


def render_fields(status: BatteryStatus) -> dict[str, str]:
    """Build the placeholder dict used by the window format string."""
    percent = status.percent if status.percent is not None else 0
    return {
        "percent": str(percent),
        "time": format_duration(status.seconds_remaining),
        "state": status.state,
        "state_text": STATE_TEXT_DE.get(status.state, status.state),
        "state_icon": STATE_ICON.get(status.state, ""),
    }


def fill_color_key(state: str) -> str:
    return _FILL_COLOR_KEY.get(state, "fill_discharging")
