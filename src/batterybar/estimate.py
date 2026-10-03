"""Remaining-time estimation - hybrid fallback chain.

See docs/BATTERY_ESTIMATION.md for the research behind this order
(mirrors BatteryBar's fallbacks):
  1. fuel-gauge rate: usable_mwh / |rate_mw|   (hardware-reported drain)
  2. session rate: own rate since unplug (total drop / elapsed time)
  3. learned rate: persisted avg drain from previous discharge sessions
     (EWMA, config/stats.local.json) - instant estimate after unplug,
     like BatteryBar's historical profile
  4. driver EstimatedTime (SYSTEM_BATTERY_STATE)
  5. Windows BatteryLifeTime                   (raw fallback, "same as Windows")

Notes:
- rate_mw == None means the fuel gauge reports no rate at all
  (BATTERY_UNKNOWN_RATE) - the only path to an immediate estimate is
  then the learned rate.
- The session rate intentionally uses the WHOLE discharge session
  (unplug -> now), not a sliding window: the battery percent signal is
  quantized to ~1% steps (>>500 mWh on a ~54 Wh pack), so a short
  window amplifies step noise into wild estimate swings. The session
  average converges to the true mean drain - BatteryBar's statistical
  mode behavior.
- All estimates count down to `soft_min_percent` of capacity, not 0%.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from .battery import BatteryStatus, PowerDetails

_LEARN_ALPHA = 0.3  # EWMA weight of the newest session rate
_PERSIST_INTERVAL_S = 60.0
_MIN_SESSION_S = 90.0  # minimum elapsed time before trusting a session rate
_MIN_DROP_MWH = 30.0  # minimum mWh drop before folding into the learned rate
_STATS_VERSION = 2  # bump to discard stats trained by older algorithms
_MIN_MODEL_SAMPLES = 8  # (load, drain) pairs before regression kicks in
_MIN_LOAD_VAR = 25.0  # min load variance (%^2, ~5pp std) for a usable slope
_MIN_DRAIN_MW = 500.0  # power floor for predictions


class DrainModel:
    """Learned drain power model P(load%) -> mW via online OLS regression.

    Sufficient statistics are kept incrementally so the model can be
    persisted inside stats.local.json and improves over weeks of use.
    """

    def __init__(self, state: dict | None = None) -> None:
        s = state or {}
        self.n = int(s.get("n", 0))
        self.sx = float(s.get("sx", 0.0))
        self.sy = float(s.get("sy", 0.0))
        self.sxy = float(s.get("sxy", 0.0))
        self.sxx = float(s.get("sxx", 0.0))

    def add(self, load_pct: float, drain_mw: float) -> None:
        if drain_mw <= 0 or load_pct < 0:
            return
        self.n += 1
        self.sx += load_pct
        self.sy += drain_mw
        self.sxy += load_pct * drain_mw
        self.sxx += load_pct * load_pct

    def predict(self, load_pct: float) -> float | None:
        """Predicted drain in mW at `load_pct`, or None when the model
        cannot fit yet (too few samples / load never varied)."""
        if self.n < _MIN_MODEL_SAMPLES:
            return None
        denom = self.n * self.sxx - self.sx * self.sx
        if denom <= 0 or (self.sxx - self.sx * self.sx / self.n) / self.n < _MIN_LOAD_VAR:
            return None
        b = (self.n * self.sxy - self.sx * self.sy) / denom
        a = (self.sy - b * self.sx) / self.n
        b = max(0.0, b)  # drain must not decrease with load
        return max(_MIN_DRAIN_MW, a + b * load_pct)

    def state(self) -> dict:
        return {
            "n": self.n, "sx": self.sx, "sy": self.sy,
            "sxy": self.sxy, "sxx": self.sxx,
        }


class TimeEstimator:
    def __init__(
        self,
        soft_min_percent: float = 5.0,
        window_s: float = 300.0,  # kept for config compatibility, unused
        stats_path: Path | None = None,
    ) -> None:
        self.soft_min = soft_min_percent / 100.0
        self.window_s = window_s
        self._stats_path = stats_path
        self._session_start: tuple[float, float] | None = None
        self._learned_mw = self._load_rate()
        self._model = DrainModel(self._load_model_state())
        self._last_persist = 0.0
        self.session_mw: float | None = None  # last session drain in mW
        self.source: str | None = None
        # "rate" | "slope" | "learned" | "driver" | "windows"

    # ------------------------------------------------------------ persistence
    def _load_rate(self) -> float | None:
        data = self._read_stats()
        if data is None:
            return None
        try:
            value = float(data.get("avg_drain_mw", 0))
            return value if value > 0 else None
        except (ValueError, TypeError):
            return None

    def _load_model_state(self) -> dict | None:
        data = self._read_stats()
        return data.get("drain_model") if data else None

    def _read_stats(self) -> dict | None:
        if not self._stats_path:
            return None
        try:
            data = json.loads(Path(self._stats_path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return data if data.get("version") == _STATS_VERSION else None

    def _persist_rate(self, force: bool = False) -> None:
        if not self._stats_path:
            return
        if self._learned_mw is None and self._model.n == 0:
            return  # nothing learned yet
        now = time.monotonic()
        if not force and now - self._last_persist < _PERSIST_INTERVAL_S:
            return
        self._last_persist = now
        payload = {
            "version": _STATS_VERSION,
            "avg_drain_mw": (
                round(self._learned_mw, 1) if self._learned_mw else None
            ),
            "drain_model": self._model.state(),
            "updated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        try:
            Path(self._stats_path).parent.mkdir(parents=True, exist_ok=True)
            Path(self._stats_path).write_text(
                json.dumps(payload, indent=2) + "\n", encoding="utf-8"
            )
        except OSError:
            pass

    def reset(self) -> None:
        self._session_start = None
        self.source = None

    # ------------------------------------------------------------- estimation
    def remaining_seconds(
        self, status: BatteryStatus, details: PowerDetails | None
    ) -> int | None:
        discharging = status.state in ("discharging", "low", "critical") or (
            details is not None and details.discharging
        )
        if not discharging:
            self._persist_rate(force=True)
            self.reset()
            return None

        qty, floor = self._quantity(status, details)
        now = time.monotonic()
        if qty is not None and self._session_start is None:
            self._session_start = (now, qty)

        # 1) hardware-reported drain rate
        if (
            details is not None
            and details.rate_mw is not None
            and details.rate_mw < 0
            and details.max_mwh > 0
        ):
            usable = max(0.0, details.remaining_mwh - self.soft_min * details.max_mwh)
            self.source = "rate"
            return int(usable / -details.rate_mw * 3600)

        # 2) session-average rate since unplug (BatteryBar's statistical mode)
        session = self._session_rate(status, details, now)
        if session is not None:
            rate, usable, drop = session
            if details is not None and details.max_mwh > 0:
                self.session_mw = rate * 3600  # mWh/s -> mW
                if drop >= _MIN_DROP_MWH:
                    self._learn_mw(self.session_mw)
            self.source = "slope"
            return max(0, int(usable / rate))

        # 3) learned average drain rate (instant estimate after unplug)
        if self._learned_mw and details is not None and details.max_mwh > 0:
            usable = details.remaining_mwh - self.soft_min * details.max_mwh
            self.source = "learned"
            return max(0, int(usable / self._learned_mw * 3600))

        # 4) driver estimate
        if details is not None and details.estimated_s:
            self.source = "driver"
            return details.estimated_s

        # 5) Windows fallback
        self.source = "windows" if status.seconds_remaining is not None else None
        return status.seconds_remaining

    # ------------------------------------------------------ drain model api
    def add_drain_sample(self, load_pct: float, drain_mw: float) -> None:
        """Fold a measured (cpu-load%, drain mW) pair into the model."""
        self._model.add(load_pct, drain_mw)
        self._persist_rate()

    def predict_drain(self, load_pct: float) -> float | None:
        """Predicted drain (mW) at the given load %, or None when the
        model cannot fit yet - caller falls back to proportional scaling."""
        return self._model.predict(load_pct)

    # ---------------------------------------------------------------- helpers
    def _quantity(
        self, status: BatteryStatus, details: PowerDetails | None
    ) -> tuple[float | None, float]:
        """Quantity to track + soft-min floor, in the same unit.

        Prefers the fuel gauge's remaining_mwh (smooth, ~tens-of-mWh
        increments). Only falls back to percent when no mWh data exists -
        never merges the two, because the coarse percent steps would
        inject huge fake deltas into the rate.
        """
        if details is not None and details.max_mwh > 0:
            return float(details.remaining_mwh), self.soft_min * details.max_mwh
        if status.percent is not None:
            return float(status.percent), self.soft_min * 100.0
        return None, 0.0

    def _session_rate(
        self, status: BatteryStatus, details: PowerDetails | None, now: float
    ) -> tuple[float, float, float] | None:
        """Average discharge rate (qty/s), usable qty, total drop."""
        if self._session_start is None:
            return None
        t0, q0 = self._session_start
        qty, floor = self._quantity(status, details)
        if qty is None:
            return None
        dt = now - t0
        drop = q0 - qty
        if dt < _MIN_SESSION_S or drop <= 0:
            return None
        return drop / dt, qty - floor, drop

    def _learn_mw(self, session_rate_mw: float) -> None:
        if session_rate_mw <= 0:
            return
        if self._learned_mw is None:
            self._learned_mw = session_rate_mw
        else:
            self._learned_mw = (
                (1 - _LEARN_ALPHA) * self._learned_mw + _LEARN_ALPHA * session_rate_mw
            )
        self._persist_rate()
