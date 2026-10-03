"""Remaining-time estimation - hybrid fallback chain.

See docs/BATTERY_ESTIMATION.md for the research behind this order
(mirrors BatteryBar's fallbacks):
  1. fuel-gauge rate: usable_mwh / |rate_mw|   (immediate, ~seconds after unplug)
  2. own slope from capacity samples           (when the gauge reports no rate)
  3. driver EstimatedTime (SYSTEM_BATTERY_STATE)
  4. Windows BatteryLifeTime                   (raw fallback, "same as Windows")
"""
from __future__ import annotations

import time
from collections import deque

from .battery import BatteryStatus, PowerDetails


class TimeEstimator:
    def __init__(self, soft_min_percent: float = 5.0, window_s: float = 300.0) -> None:
        self.soft_min = soft_min_percent / 100.0
        self.window_s = window_s
        self._samples: deque[tuple[float, float]] = deque()
        self.source: str | None = None  # "rate" | "slope" | "driver" | "windows"

    def reset(self) -> None:
        self._samples.clear()
        self.source = None

    def remaining_seconds(
        self, status: BatteryStatus, details: PowerDetails | None
    ) -> int | None:
        discharging = status.state in ("discharging", "low", "critical") or (
            details is not None and details.discharging
        )
        if not discharging:
            self.reset()
            return None

        now = time.monotonic()
        qty = self._sample_quantity(status, details)
        if qty is not None:
            self._samples.append((now, qty))
            while self._samples and now - self._samples[0][0] > self.window_s:
                self._samples.popleft()

        # 1) fuel-gauge rate
        if details is not None and details.rate_mw < 0 and details.max_mwh > 0:
            usable_mwh = max(0.0, details.remaining_mwh - self.soft_min * details.max_mwh)
            self.source = "rate"
            return int(usable_mwh / -details.rate_mw * 3600)

        # 2) own slope estimate (capacity drain per second over the window)
        est = self._slope_estimate(status, details)
        if est is not None:
            self.source = "slope"
            return est

        # 3) driver estimate
        if details is not None and details.estimated_s:
            self.source = "driver"
            return details.estimated_s

        # 4) Windows fallback
        self.source = "windows" if status.seconds_remaining is not None else None
        return status.seconds_remaining

    @staticmethod
    def _sample_quantity(status: BatteryStatus, details: PowerDetails | None) -> float | None:
        if details is not None and details.max_mwh > 0:
            return float(details.remaining_mwh)
        if status.percent is not None:
            return float(status.percent)
        return None

    def _slope_estimate(
        self, status: BatteryStatus, details: PowerDetails | None
    ) -> int | None:
        if len(self._samples) < 2:
            return None
        t0, q0 = self._samples[0]
        t1, q1 = self._samples[-1]
        dt = t1 - t0
        if dt < 30 or q1 >= q0:
            return None  # need a real discharge slope over >= 30 s
        if details is not None and details.max_mwh > 0:
            floor = self.soft_min * details.max_mwh
        elif status.percent is not None:
            floor = self.soft_min * 100.0
        else:
            return None
        usable = q1 - floor
        if usable <= 0:
            return 0
        return int(usable / ((q0 - q1) / dt))
