# BATTERY_ESTIMATION.md – how the reference tools compute remaining time

Research status: 2026-10-03 · basis for v0.3.0 implementation
Sources: `docs/RESEARCH.md` (#1 BatteryBar wiki, #3/#4 local research),
live API probes on the dev machine (Windows 11, ~53.7 Wh battery).

---

## 1. What Windows itself provides

| API / source | Data | Verdict |
|---|---|---|
| `GetSystemPowerStatus` → `BatteryLifeTime` | seconds remaining, `0xFFFFFFFF` when unknown | Unreliable: often "unknown" right after unplugging – Windows needs a while to build its own estimate. Still useful as last-resort fallback. |
| `CallNtPowerInformation(SystemBatteryState=5)` → `SYSTEM_BATTERY_STATE` | `AcOnLine`, `BatteryPresent`, `Charging`, `Discharging`, `MaxCapacity` (mWh), `RemainingCapacity` (mWh), `RateOfDrain` (signed mW, <0 while discharging), `EstimatedTime` (s, `0xFFFFFFFF` unknown) | **Best source.** Real mWh capacities + live drain rate straight from the battery fuel gauge. Verified on the dev machine: `MaxCapacity 53673 mWh`, `RemainingCapacity 53673 mWh`, `RateOfDrain 0` on AC. One ctypes call, stdlib only. |
| WMI `Win32_Battery` | `EstimatedRunTime` (min), `EstimatedChargeRemaining`, `DesignCapacity`, `FullChargeCapacity` | **Useless in practice.** Probe returned `EstimatedRunTime = 71582788` (sentinel garbage) and empty capacity fields. Do not use. |
| `IOCTL_BATTERY_QUERY_INFORMATION` | `BATTERY_INFORMATION` incl. `FullChargedCapacity`, `DesignedCapacity`, `RateOfDrain` | Rich data (incl. wear via DesignCapacity), but needs device enumeration (setupapi). Planned for FR-13. |

## 2. How BatteryBar (Pro) computed it

Source: Osiris Wiki (Preferences / Status Popup / Release Notes pages) –
see `docs/RESEARCH.md` #8.

BatteryBar combined **three** strategies, best-first:

1. **Statistical time estimation (default, Pro feature "Use statistical
   time estimation")** — "time remaining is calculated based on
   historical usage data from your battery". BatteryBar kept a per-battery
   discharge profile ("Battery Profile Graph" shows it) and extrapolated
   remaining time from learned usage patterns. Profile data could be
   cleared via preferences ("if the estimated time remaining is not
   accurate, use this button to clear the data").
2. **Rate-based fallback** — when no profile data existed:
   `Time Remaining (hours) = Current Capacity / (Dis)charge Rate`.
   This is exactly what users see "immediately after unplugging" — a
   plausible estimate within seconds.
   If the hardware reports no rate, BatteryBar **estimated the
   (dis)charge rate itself** from capacity deltas over time
   (popup showed "(Estimated)" next to the rate).
3. **Raw Windows value** — "show the raw time remaining (same as
   Windows)" as final fallback.

### Soft minimum level

BatteryBar did **not** count down to 0 % but to a configurable
**soft minimum level** (e.g. 10 %): "most computers are designed to
force a shutdown or hibernate at a certain percentage of battery life
remaining. Thus, the last few percent of your battery are never actually
used." At the soft minimum the bar already reports `0:00`.

### Battery wear

`wear = 1 - (FullChargeCapacity / DesignedCapacity)` in mWh —
a real hardware health metric (FR-13 territory).

### Click-toggle display (confirmed)

`BatteryBarTextDisplayState` enum found in `BatteryBar.exe`
(PowerShell reflection):
`TimeRemaining`, `PercentRemaining`, `DischargeRate`.
Release notes: "Clicking on BatteryBar now also shows the Discharge Rate
in addition to Time Remaining and Percent Remaining" — the toolbar
cycles through these on click. A Pro setting could also pin
"Information to Display on the Toolbar" incl. `Capacity Remaining`.

## 3. How the other tools handle it

| Tool | Approach |
|---|---|
| Windows 11 tray tooltip | Shows only % — Microsoft removed remaining time entirely (its estimate was notoriously bad → UX debt). |
| BGInfo / DesktopInfo / PowerBGInfo | Display system fields; battery time is not their focus (DesktopInfo can show `Win32_Battery` fields incl. the broken `EstimatedRunTime`). |
| Rainmeter | `PowerSource`/`Battery` measures expose Windows API values (percent, lifetime) — same data quality limits as `GetSystemPowerStatus`. |
| Conky | `battery_time`/`battery_percent` variables via sysfs `power_supply` (Linux kernel estimate, similar rate-based approach). |

**Lesson:** the plausible "immediately after unplug" estimate never
comes from Windows — it comes from `RemainingCapacity / |RateOfDrain|`
using the fuel-gauge's own mWh/mW data, optionally refined by a learned
history. Windows' `BatteryLifeTime` is only a fallback.

## 4. Design adopted for BatteryBar OSS (v0.3.0)

Estimator order (while discharging), mirroring BatteryBar's fallbacks:

1. **Rate-based** (primary): if `RateOfDrain < 0` and `MaxCapacity > 0`
   → `t = (RemainingCapacity − soft_min·MaxCapacity) / |RateOfDrain|`.
   Soft minimum = `estimation.soft_min_percent` (default 5 %).
2. **Own slope estimate** ("(Estimated)" equivalent): if the battery
   reports no rate, fit the slope of capacity/% over a sliding
   5-minute sample window → `t = usable / slope`.
3. **Driver `EstimatedTime`** from `SYSTEM_BATTERY_STATE` when the
   gauge already provides one.
4. **Windows `BatteryLifeTime`** (raw fallback = "same as Windows").

Display: left-click on the bar cycles `default(format)` →
`time` → `percent` → `rate` → `capacity` → back, mirroring
BatteryBar's click-toggle (plus our format-template mode).
Persisted to `settings.local.json` (`window.display_mode`).

Full statistical discharge-profile learning (BatteryBar's mode 1)
remains open as FR-12 for a later release — requires persisted history.
