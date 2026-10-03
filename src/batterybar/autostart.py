"""Autostart via the per-user HKCU Run key (no admin required)."""
from __future__ import annotations

import sys
import winreg
from pathlib import Path

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "BatteryBarOSS"


def _command() -> str:
    """Launch command: frozen exe -> itself; source -> pythonw BatteryBarOSS.pyw."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    # NOTE: must NOT be named "batterybar.pyw" - since Python 3.14, .pyw is
    # an importable source suffix and a same-named file at repo root would
    # shadow the batterybar package (infinite recursion).
    pyw = Path(__file__).resolve().parents[2] / "BatteryBarOSS.pyw"
    exe = Path(sys.executable)
    # Console builds still autostart console-free via pythonw.exe.
    if exe.name.lower() == "python.exe":
        pyw_exe = exe.with_name("pythonw.exe")
        if pyw_exe.exists():
            exe = pyw_exe
    return f'"{exe}" "{pyw}"'


def is_enabled() -> bool:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY)
        winreg.QueryValueEx(key, _VALUE_NAME)
        winreg.CloseKey(key)
        return True
    except OSError:
        return False


def enable() -> None:
    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, _RUN_KEY)
    winreg.SetValueEx(key, _VALUE_NAME, 0, winreg.REG_SZ, _command())
    winreg.CloseKey(key)


def disable() -> None:
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, _VALUE_NAME)
        winreg.CloseKey(key)
    except OSError:
        pass
