# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
versioning follows [Semantic Versioning](https://semver.org/).
Rules: see `AGENTS.md` sections 1-3.

## [0.4.0] - 2026-10-03

### Added

- **Battery health info — real wear value** (FR-13, partial): reads
  design capacity, full-charge capacity, cycle count, serial number and
  manufacture date from the `root\wmi` classes `BatteryStaticData`,
  `BatteryFullChargedCapacity`, `BatteryCycleCount`, `BatteryStatus`
  via a one-shot PowerShell subprocess (OS component, ~300 ms,
  refreshed hourly + on reload). On the dev machine this exposes the
  **real** wear of ~4.1 % (Design 55994 mWh vs. Full 53673 mWh,
  120 cycles) — values that tools reading only `Win32_Battery` never
  see (that class returns empty capacity fields).
- **New `health` display mode** in the click cycle:
  `default → time → percent → rate → capacity → health` — shows e.g.
  `53.7 Wh · 4.1% wear · 120 cyc`. New format placeholders:
  `{health}`, `{wear}`, `{cycles}`, `{design_wh}`, `{full_wh}`,
  `{machine}`, `{bhm}`.
- **Machine identification** (`sysinfo.read_machine_info()`): reads
  manufacturer/product/BIOS version from the registry
  (`HKLM\...\SystemInformation`) — no elevation needed. Detects HP
  machines via `is_hp`.
- **HP Battery Health Manager marker** (unique BIOS-mode detection,
  user request): `tools/read_bios_battery_mode.bat` runs an elevated
  PowerShell query against HP's official BIOS WMI interface
  (`root\hp\instrumentedbios`, `HP_BIOSSetting`) and caches the real
  BIOS setting value to `config/hp_bios.local.json` (gitignored). The
  bar then shows it in health mode as `BHM: <mode>`. This is an
  explicit firmware marker — **not** inferred from battery values.
  Access denied without elevation: there is no non-privileged unique
  marker on HP machines; on non-HP machines everything degrades
  gracefully (`bhm` stays empty).
- `--selftest` output now includes `static_info`, `machine` and
  `hp_bios_cache` blocks.
- `sysinfo.py` module; `config.HP_BIOS_FILE` constant.

### Changed

- `.gitignore` translated to English (missed in v0.2.0) +
  `config/hp_bios.local.json` added.

### Notes

- `IOCTL_BATTERY_QUERY_INFORMATION` (originally planned for FR-13)
  was investigated: the `GUID_DEVICE_BATTERY` device interface cannot
  be enumerated via setupapi on this machine (no interfaces returned,
  tried `72631e55`/`72631e54` class GUIDs). `root\wmi` via the
  PowerShell subprocess turned out to be the dependable stdlib path —
  same data, no COM plumbing in-process.

## [0.3.1] - 2026-10-03

### Fixed

- **"0:00 h" estimate on batteries that report no drain rate** (user
  report): `RateOfDrain` was `0x80000000` = `BATTERY_UNKNOWN_RATE`
  (signed: `-2147483648`) on the dev machine — the "not reported"
  sentinel, not a real rate. Division produced ~0 s. Sentinel is now
  mapped to `rate_mw=None` and the rate branch is skipped.
- `PowerDetails.rate_mw` is now `int | None` (`None` = hardware reports
  no rate); `{rate}` placeholder shows nothing then — matching
  BatteryBar, which marks such cases "(Estimated)".

### Added

- **Learned discharge rate with persistence** (FR-12, partial): the
  estimator learns the average drain from real capacity deltas
  (mWh/s → mW) while discharging, blends it into `avg_drain_mw` via
  EWMA (α = 0.3) and persists it to `config/stats.local.json`
  (gitignored) every 60 s and on AC reconnect. When the hardware
  reports no rate, this learned rate produces a plausible estimate
  **immediately after unplugging** — BatteryBar's documented
  historical-data behavior.
- **Merged capacity quantity**: the slope tracks
  `min(remaining_mwh, percent·max_mwh/100)` so drain is detected even
  while the fuel gauge still reports "full" at 100 %.

## [0.3.0] - 2026-10-03

### Added

- **Fuel-gauge data source** (`battery.read_power_details()`): queries
  `CallNtPowerInformation(SYSTEM_BATTERY_STATE)` — real capacities in mWh
  (`MaxCapacity`, `RemainingCapacity`), live drain rate (`RateOfDrain`,
  signed mW) and driver `EstimatedTime`. New format placeholders
  `{rate}` ("-12.3 W") and `{capacity}` ("46.7 / 53.7 Wh").
- **Hybrid remaining-time estimator** (`estimate.TimeEstimator`), modeled
  on BatteryBar's documented fallback chain (see new research doc
  `docs/BATTERY_ESTIMATION.md`):
  1. rate-based `usable_mWh / |RateOfDrain|` — plausible within seconds
     after unplugging (replaces the previously shown Windows-only value)
  2. own slope estimate from capacity samples (5-minute window) when the
     battery reports no rate — time is prefixed with "~" like
     BatteryBar's "(Estimated)"
  3. driver `EstimatedTime`
  4. Windows `BatteryLifeTime` (raw fallback)
  Estimates count down to a configurable **soft minimum level**
  (`estimation.soft_min_percent`, default 5 %) instead of real 0 % —
  same concept as BatteryBar's "Soft minimum level".
- **Click-to-cycle display mode**: a left-click (< 6 px movement) on the
  bar cycles `default(format)` → `time` → `percent` → `rate` →
  `capacity` → back — BatteryBar's confirmed click behavior (enum
  `BatteryBarTextDisplayState` + wiki). Persisted as
  `window.display_mode` in `settings.local.json`. Drag still moves,
  `lock_position` still works (click toggles, drag is ignored).
- `docs/BATTERY_ESTIMATION.md`: research write-up — what Windows APIs
  actually deliver (incl. live probe results: WMI `EstimatedRunTime`
  garbage vs. `SYSTEM_BATTERY_STATE` real mWh/mW), BatteryBar's
  statistical/rate/fallback strategy from the Osiris Wiki, design adopted.
- `--selftest` output now includes the `power_details` block.

### Changed

- `{time}` placeholder now uses the own estimator (was: Windows
  `BatteryLifeTime` only) — shows a plausible value much sooner after
  switching to battery.

## [0.2.1] - 2026-10-03

### Added

- **Mandatory AI authorship disclosure** (maintainer decision): the
  project must remain clearly marked as AI-generated, naming the tool
  used — **Devin (Cognition AI), model SWE-2 High**:
  - New `AGENTS.md` §12 defines the rule and required locations
    (README top block, `NOTICE` file, app context menu, commit footer)
  - `NOTICE` file at repo root: AI authorship + third-party references
  - `README.md`: prominent disclosure blockquote at the top
  - Context menu header now shows "built with Devin (SWE-2 High)"

## [0.2.0] - 2026-10-03

### Changed

- **Project language switched to English**: all documentation
  (`AGENTS.md`, `README.md`, `CHANGELOG.md`, `PROJECT_MEMORY.md`,
  `docs/*`), config comments and launcher comments translated to English.
  Rationale: broader reach for the open-source project. The maintainer
  may continue to communicate in German outside the repository.
- **UI strings switched to English**: context menu ("Always on top",
  "Click-through", "Lock position", "Reload settings", "Exit"), toast
  messages and battery state texts ("Charging", "Discharging", "Low",
  "Critical", "Full", "On AC", "No battery"). `STATE_TEXT_DE` in
  `battery.py` renamed to `STATE_TEXT` accordingly.
- `AGENTS.md` §7 updated: documentation language is now English
  (was: German); commit messages are English as well.

## [0.1.2] - 2026-10-03

### Fixed

- **Lockout caused by persisted click-through mode**: once `click_through`
  was enabled and saved to `settings.local.json`, the bar stayed
  permanently unclickable even after restarts (user report). Immediate
  fix: entry removed from the local config.

### Added

- **Hint toast on startup with active click-through**: appears 600 ms
  after launch when `click_through` was loaded, and shows the return
  hotkey (`Ctrl+Alt+B`) — prevents silent lockouts after restarts.

## [0.1.1] - 2026-10-03

### Added

- **GitHub integration documented** (`PROJECT_MEMORY.md`): remote URL
  (`git@github.com:Wlanfr3ak/BatteryBarOSS.git`), SSH key setup
  (`~/.ssh/fabian`, `Host github.com` entry), account/author info —
  eases resumption after a fresh clone and on other machines.

## [0.1.0] - 2026-10-03

First MVP. Project foundation: rulebook, documentation skeleton and a
working floating battery bar using only the Python standard library.

### Added

- **Floating battery bar** (`src/batterybar/`):
  - Frameless, transparent, always-on-top window (Tkinter,
    `overrideredirect` + `-transparentcolor`)
  - Battery status via Win32 `GetSystemPowerStatus` (ctypes, no external
    modules): percent, charge state, remaining time
  - State color coding: discharging, charging, full, low, critical,
    no battery — colors freely configurable
  - Display template with placeholders `{percent}`, `{time}`, `{state}`,
    `{state_text}`, `{state_icon}` (Conky-style format strings)
  - Drag & drop with position persistence to `settings.local.json`
  - Context menu (right click): always-on-top, click-through,
    position lock, config reload, exit
  - Click-through mode (WS_EX_TRANSPARENT via ctypes) + global hotkeys
    `Ctrl+Alt+B` (toggle) and `Ctrl+Alt+Q` (quit) via
    `GetAsyncKeyState` polling
  - Warning toast (bottom right, optional `winsound` beep) on crossing
    the low/critical thresholds, once per event
  - DPI awareness (shcore `SetProcessDpiAwareness(2)`, user32 fallback)
  - Logging via `RotatingFileHandler` to `logs/batterybar.log`
  - CLI: `--selftest` (read config + battery, no GUI)
- **Configuration** (`config/`):
  - `settings.json` (committed defaults), `settings.local.json`
    (gitignored overrides), `secrets.example.json`/`secrets.json`
    (secrets infrastructure, gitignored)
- **Project rules**:
  - `AGENTS.md` – SemVer versioning, changelog requirement, commit
    convention `vX.Y.Z`, dependencies/secrets/research rules
  - `PROJECT_MEMORY.md` – project memory (decisions, environment,
    architecture, roadmap)
- **Documentation**:
  - `README.md` (installation, configuration, usage guide)
  - `docs/REQUIREMENTS.md` – feature survey of the reference tools,
    MoSCoW-prioritized requirements, roadmap
  - `docs/DEPENDENCIES.md` – dependency table with sources, licenses,
    installation instructions
  - `docs/RESEARCH.md` – research sources (raw files deliberately not
    committed)
- **Repo basics**: `LICENSE` (MIT), `.gitignore` (secrets, research
  files, build artifacts, logs excluded), `.gitattributes` (line
  endings), `run.bat` (launcher without console)

### Technical decisions

- Tech stack **Python + Tkinter, standard library only** — confirmed by
  the user; goal: zero setup effort after `git clone` (details:
  `PROJECT_MEMORY.md`)
- No deskband/taskbar integration possible on Windows 11 → floating
  window as replacement concept
