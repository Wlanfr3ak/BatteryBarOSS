"""System load provider (stdlib ctypes).

Windows has no Unix-style load average (runnable-queue length is not
exposed); the Windows stand-in is CPU utilisation in %, sampled via
GetSystemTimes deltas. LoadTracker keeps a rolling history and reports
1/5/15-minute averages - the familiar load-avg display, mapped onto
Windows semantics.
"""
from __future__ import annotations

import ctypes
import time
from collections import deque
from ctypes import wintypes

LOAD_WINDOWS_S = (60, 300, 900)  # 1 / 5 / 15 min, like Unix loadavg


class _FILETIME(ctypes.Structure):
    _fields_ = [
        ("dwLowDateTime", wintypes.DWORD),
        ("dwHighDateTime", wintypes.DWORD),
    ]


def _read_times() -> tuple[int, int]:
    """(idle, kernel+user) in 100-ns units. Kernel time includes idle."""
    idle, kern, user = _FILETIME(), _FILETIME(), _FILETIME()
    ctypes.windll.kernel32.GetSystemTimes(
        ctypes.byref(idle), ctypes.byref(kern), ctypes.byref(user)
    )
    def v(ft: _FILETIME) -> int:
        return (ft.dwHighDateTime << 32) | ft.dwLowDateTime
    return v(idle), v(kern) + v(user)


class CpuMonitor:
    """CPU busy fraction (0..1) between consecutive sample() calls."""

    def __init__(self) -> None:
        self._prev = _read_times()

    def sample(self) -> float:
        cur = _read_times()
        d_idle = cur[0] - self._prev[0]
        d_total = cur[1] - self._prev[1]
        self._prev = cur
        if d_total <= 0:
            return 0.0
        return max(0.0, min(1.0, 1.0 - d_idle / d_total))


class LoadTracker:
    """Sliding-window averages of sampled CPU fractions."""

    def __init__(self, keep_s: float | None = None) -> None:
        self._keep = keep_s if keep_s is not None else max(LOAD_WINDOWS_S) + 60
        self._samples: deque[tuple[float, float]] = deque()

    def add(self, frac: float, now: float | None = None) -> None:
        t = time.monotonic() if now is None else now
        self._samples.append((t, frac))
        while self._samples and t - self._samples[0][0] > self._keep:
            self._samples.popleft()

    def avg(self, window_s: float, now: float | None = None) -> float | None:
        """Mean CPU % over the last `window_s` seconds, or None when less
        than half the window is covered by samples."""
        t = time.monotonic() if now is None else now
        vals = [(ts, f) for ts, f in self._samples if ts > t - window_s]
        if not vals or t - vals[0][0] < window_s * 0.5:
            return None
        return sum(f for _, f in vals) / len(vals) * 100.0

    def averages(self, now: float | None = None) -> list[float | None]:
        return [self.avg(w, now) for w in LOAD_WINDOWS_S]
