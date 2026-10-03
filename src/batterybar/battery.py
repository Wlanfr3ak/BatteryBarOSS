"""Battery status via Win32 GetSystemPowerStatus (stdlib ctypes only)."""
from __future__ import annotations

import ctypes
import json
import subprocess
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
_UNKNOWN_RATE = -2147483648  # BATTERY_UNKNOWN_RATE (0x80000000 as signed LONG)
_INFO_LEVEL_SYSTEM_BATTERY_STATE = 5


class _SYSTEM_BATTERY_STATE(ctypes.Structure):
    """CallNtPowerInformation(SystemBatteryState) - real mWh/mW values."""

    _fields_ = [
        ("AcOnLine", wintypes.BOOLEAN),
        ("BatteryPresent", wintypes.BOOLEAN),
        ("Charging", wintypes.BOOLEAN),
        ("Discharging", wintypes.BOOLEAN),
        ("Spare1", wintypes.BYTE * 3),
        ("Tag", wintypes.BYTE),
        ("MaxCapacity", wintypes.DWORD),
        ("RemainingCapacity", wintypes.DWORD),
        ("RateOfDrain", wintypes.DWORD),
        ("EstimatedTime", wintypes.DWORD),
        ("DefaultAlert1", wintypes.DWORD),
        ("DefaultAlert2", wintypes.DWORD),
    ]


@dataclass
class PowerDetails:
    """Fuel-gauge data from SYSTEM_BATTERY_STATE."""

    max_mwh: int
    remaining_mwh: int
    rate_mw: int | None  # signed, None = hardware does not report a rate
    estimated_s: int | None
    ac_on_line: bool
    charging: bool
    discharging: bool


def read_power_details() -> PowerDetails | None:
    """Query SYSTEM_BATTERY_STATE via CallNtPowerInformation (powrprof)."""
    sbs = _SYSTEM_BATTERY_STATE()
    ret = ctypes.windll.powrprof.CallNtPowerInformation(
        _INFO_LEVEL_SYSTEM_BATTERY_STATE, None, 0,
        ctypes.byref(sbs), ctypes.sizeof(sbs),
    )
    if ret != 0:
        return None
    rate = ctypes.c_int32(sbs.RateOfDrain).value
    return PowerDetails(
        max_mwh=int(sbs.MaxCapacity),
        remaining_mwh=int(sbs.RemainingCapacity),
        rate_mw=None if rate == _UNKNOWN_RATE else rate,
        estimated_s=None if sbs.EstimatedTime == _UNKNOWN_SECONDS else int(sbs.EstimatedTime),
        ac_on_line=bool(sbs.AcOnLine),
        charging=bool(sbs.Charging),
        discharging=bool(sbs.Discharging),
    )


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


STATE_TEXT = {
    "charging": "Charging",
    "discharging": "Discharging",
    "low": "Low",
    "critical": "Critical",
    "charged": "Full",
    "ac": "On AC",
    "nobattery": "No battery",
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


def render_fields(
    status: BatteryStatus,
    est_seconds: int | None = None,
    details: PowerDetails | None = None,
    estimated: bool = False,
    static: "BatteryStaticInfo | None" = None,
    machine: str = "",
    bhm: str | None = None,
) -> dict[str, str]:
    """Build the placeholder dict used by the window format string."""
    percent = status.percent if status.percent is not None else 0
    seconds = est_seconds if est_seconds is not None else status.seconds_remaining
    time_str = format_duration(seconds)
    if estimated and seconds is not None:
        time_str = "~" + time_str
    if details is not None and details.rate_mw:
        rate_str = f"{details.rate_mw / 1000:.1f} W"
    else:
        rate_str = ""
    if details is not None and details.max_mwh > 0:
        capacity_str = (
            f"{details.remaining_mwh / 1000:.1f} / {details.max_mwh / 1000:.1f} Wh"
        )
    else:
        capacity_str = ""
    health_parts: list[str] = []
    if static is not None:
        if static.full_charge_mwh:
            health_parts.append(f"{static.full_charge_mwh / 1000:.1f} Wh")
        if static.wear_percent is not None:
            health_parts.append(f"{static.wear_percent:.1f}% wear")
        if static.cycle_count:
            health_parts.append(f"{static.cycle_count} cyc")
    if bhm:
        health_parts.append(f"BHM: {bhm}")
    return {
        "percent": str(percent),
        "time": time_str,
        "rate": rate_str,
        "capacity": capacity_str,
        "state": status.state,
        "state_text": STATE_TEXT.get(status.state, status.state),
        "state_icon": STATE_ICON.get(status.state, ""),
        "health": " · ".join(health_parts),
        "wear": f"{static.wear_percent:.1f}" if static and static.wear_percent is not None else "",
        "cycles": str(static.cycle_count) if static and static.cycle_count else "",
        "design_wh": f"{static.design_mwh / 1000:.1f}" if static and static.design_mwh else "",
        "full_wh": f"{static.full_charge_mwh / 1000:.1f}" if static and static.full_charge_mwh else "",
        "machine": machine,
        "bhm": bhm or "",
    }


def fill_color_key(state: str) -> str:
    return _FILL_COLOR_KEY.get(state, "fill_discharging")


# --------------------------------------------------------------------------
# Static battery info (design capacity, cycles, serial) via root\wmi classes.
# Querying root\wmi needs COM; the cheapest stdlib-conformant path is a
# one-shot PowerShell subprocess (OS component, ~300 ms, called rarely).
# --------------------------------------------------------------------------


@dataclass
class BatteryStaticInfo:
    design_mwh: int | None
    full_charge_mwh: int | None
    cycle_count: int | None
    serial: str
    manufacture_date: str
    voltage_mv: int | None

    @property
    def wear_percent(self) -> float | None:
        if self.design_mwh and self.full_charge_mwh is not None:
            return max(0.0, 100.0 - self.full_charge_mwh / self.design_mwh * 100)
        return None


_PS_STATIC_CMD = (
    "$b=Get-WmiObject -Namespace root\\wmi -Class BatteryStaticData;"
    "$f=Get-WmiObject -Namespace root\\wmi -Class BatteryFullChargedCapacity;"
    "$c=Get-WmiObject -Namespace root\\wmi -Class BatteryCycleCount;"
    "$s=Get-WmiObject -Namespace root\\wmi -Class BatteryStatus;"
    "[pscustomobject]@{design_mwh=$b.DesignedCapacity;"
    "full_mwh=$f.FullChargedCapacity;cycles=$c.CycleCount;"
    "serial=([string]$b.SerialNumber).Trim();"
    "mfg=([string]$b.ManufactureDate).Trim();voltage_mv=$s.Voltage}"
    "|ConvertTo-Json -Compress"
)


def read_static_info(timeout: float = 15.0) -> BatteryStaticInfo | None:
    """Read static battery info from root\\wmi via a PowerShell one-shot."""
    try:
        proc = subprocess.run(
            [
                "powershell", "-NoProfile", "-NonInteractive",
                "-ExecutionPolicy", "Bypass", "-Command", _PS_STATIC_CMD,
            ],
            capture_output=True, text=True, timeout=timeout,
            creationflags=0x08000000,  # CREATE_NO_WINDOW
        )
        data = json.loads(proc.stdout)
        return BatteryStaticInfo(
            design_mwh=data.get("design_mwh"),
            full_charge_mwh=data.get("full_mwh"),
            cycle_count=data.get("cycles"),
            serial=str(data.get("serial") or ""),
            manufacture_date=str(data.get("mfg") or ""),
            voltage_mv=data.get("voltage_mv"),
        )
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return None
