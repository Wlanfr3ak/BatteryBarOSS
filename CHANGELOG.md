# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
versioning follows [Semantic Versioning](https://semver.org/).
Rules: see `AGENTS.md` sections 1-3.

## [0.7.0] - 2026-10-03

### Added

- **Self-updater (frozen builds only)** — new module `updater.py`:
  - First-start consent dialog asks once whether automatic update
    checks are allowed; the answer is persisted as
    `updates.enabled` in `settings.local.json` and honored forever
    (declined = never checked). Manual checks stay available via
    context-menu "Check for updates now" regardless.
  - Checks `api.github.com/.../releases/latest` over enforced HTTPS
    (`https:` scheme whitelist, system-CA TLS verification via
    `ssl.create_default_context()`), at most every
    `updates.check_interval_hours` (default 24 h, timestamped via
    `updates.last_check` — only successful checks advance it).
  - New release asset `SHA256SUMS.txt` (CI-generated) pins the
    expected digest; a downloaded binary is **discarded** unless its
    SHA-256 matches the entry for the exact asset name
    `BatteryBarOSS-<version>.exe`. Hash = integrity/corruption proof;
    authenticity via code signing is planned (SignPath, see below).
  - One-step apply: helper `.bat` in `%TEMP%` waits for the process to
    exit, moves the verified exe over `sys.executable` and relaunches.
    Config/stats in `%LOCALAPPDATA%` are untouched → settings survive.
  - New context-menu item "Check for updates now" (frozen builds);
    `updater.available()` is False for source runs — dev flow stays
    `git pull`. `--selftest` reports `updater_available` +
    `updates_enabled`.
- Config block `updates` (`enabled`, `check_interval_hours`,
  `last_check`) in `config/settings.json` + `DEFAULT_SETTINGS`.
- `docs/DEPENDENCIES.md` §6: SignPath Foundation noted as the planned
  code-signing path (free for qualifying OSS projects).

### Changed

- `release.yml`: CI now generates `SHA256SUMS.txt` (sha256sum-format)
  for both release assets and attaches it — required by the updater.

## [0.6.2] - 2026-10-03

### Changed

- `docs/DEPENDENCIES.md` §6: documented that the portable/installer
  EXE is fully self-contained (bundle verified: interpreter, VC++
  runtime, tk embedded) + honest caveats (rare PowerShell spawn for
  `root\wmi` statics, unsigned-exe SmartScreen notes, x64-only,
  `%TEMP%` unpack per start).

## [0.6.1] - 2026-10-03

### Added

- **Automated GitHub Releases** (`.github/workflows/release.yml`):
  pushing a `vX.Y.Z` tag triggers a Windows runner that installs
  PyInstaller, builds `dist\BatteryBarOSS.exe`, compiles the Inno
  installer (preinstalled on the runner) and publishes a Release
  containing `BatteryBarOSS-Setup-X.Y.Z.exe`, the portable exe and the
  extracted CHANGELOG section as release notes.
- `tools/release_notes.py`: extracts the `## [X.Y.Z]` changelog section
  (used by the workflow, also handy locally).
- Release rule added to `AGENTS.md` §3: every version commit is tagged
  `vX.Y.Z`; the tag push triggers the release build.

## [0.6.0] - 2026-10-03

### Added

- **Autostart via HKCU Run key** (FR-15): new context-menu checkbutton
  "Start with Windows". Writes/removes the `BatteryBarOSS` value under
  `HKCU\...\Run` — per-user, no admin needed, toggleable any time.
  Source-tree installs register `pythonw.exe BatteryBarOSS.pyw`;
  the frozen exe registers itself.
- **`BatteryBarOSS.pyw` launcher** at repo root (double-clickable,
  used by the autostart entry). Named distinctly from the package:
  since Python 3.14, `.pyw` is an importable source suffix — a
  same-named `batterybar.pyw` would shadow the package (found via an
  infinite-recursion import failure).
- **Frozen-exe support**: `config.ROOT_DIR` resolves to
  `%LOCALAPPDATA%\BatteryBarOSS` when `sys.frozen` — settings, stats,
  logs and caches go to a writable per-user location after install.
- **PyInstaller build** (FR-19): `tools/build_exe.bat` produces
  `dist\BatteryBarOSS.exe` (one-file, noconsole, ~13 MB) —
  `installer/entry.py` is the entry point.
- **Inno Setup installer**: `installer\setup.iss` +
  `tools\build_installer.bat` (injects `__version__` via `/D`) build
  `installer\Output\BatteryBarOSS-Setup-X.Y.Z.exe` — per-user install
  (`PrivilegesRequired=lowest`, no UAC), start-menu entries,
  uninstaller, optional autostart task, optional launch after install.

### Changed

- `sys.stderr`-less environments (pythonw / --noconsole): the stderr
  log handler is only attached when a console exists — prevents
  logging errors in the frozen exe.
- Write paths (`settings.local.json`, stats, logs) now create their
  parent directories — required for the fresh `%LOCALAPPDATA%` layout.

## [0.5.1] - 2026-10-03

### Added

- **README screenshot** (`docs/screenshot-compare.jpg`): live
  comparison provided by the maintainer — BatteryBar OSS (top, showing
  `93% · ~4:34 h` with the `~` estimate marker), the original
  BatteryBar Pro (middle, `5:00`) and the Windows 11 tray indicator
  (bottom) side by side.

## [0.5.0] - 2026-10-03

### Added

- **Hover tooltip with full battery details** (FR-21, user request):
  resting the pointer on the bar for ~400 ms shows a Toplevel tooltip
  with machine name, percent/state/remaining time, live Wh + drain
  rate, design/full capacity, wear %, cycle count, voltage, HP BIOS
  battery mode (when the elevated tool has cached it) and the current
  estimate source incl. soft-min level. Hidden on leave, drag and
  context menu.
- **Resizable bar via edge drag** (user request): the right edge
  resizes width, the bottom edge height, the corner both (mouse
  cursor changes to the matching resize cursor in an 8 px grip zone).
  Clamped to 140–1200 × 18–160 px; the size is persisted to
  `settings.local.json` on release. A click inside the grip zone does
  not cycle the display mode.
- **"Reset size" menu entry**: restores the default 220×28 size from
  the context menu.

## [0.4.2] - 2026-10-03

### Fixed

- **Wildly swinging runtime estimates** (user report: 7:49 then 3:52
  while BatteryBar showed a stable ~5:20 at the same charge level).
  Root cause: the slope estimator tracked
  `min(remaining_mwh, percent·max/100)` — the percent signal is
  quantized to ~1% steps (≈537 mWh on this pack), so every percent
  tick injected a huge fake delta into the 5-minute window and the
  rate estimate oscillated. The polluted rates also fed the learned
  EWMA profile.
- **Session-average rate replaces the sliding window**: the estimator
  now measures `total drop since unplug / elapsed time` from
  `remaining_mwh` only (smooth ~tens-of-mWh fuel-gauge ticks; the
  percent fallback is used solely when no mWh data exists, never
  merged). The session average converges to the true mean drain —
  BatteryBar's statistical-mode behavior — and gets more stable the
  longer the session runs.
- **Learning gate**: a session rate is folded into the EWMA profile
  only after ≥ 90 s elapsed **and** ≥ 30 mWh real drop — single
  gauge ticks can no longer poison the learned rate.
- **Stats migration**: `config/stats.local.json` now carries a
  `version` field; values trained by the old algorithm are discarded
  automatically on first read.

## [0.4.1] - 2026-10-03

### Changed

- `PROJECT_MEMORY.md`: documented the verification result of the HP
  Battery Health Manager investigation — no unprivileged marker exists
  (registry sweep found no HP software persisting the mode; only
  "HP Accessory WMI Provider" is installed, which is exactly the
  elevated-only `root\hp` provider). The actual BHM value read via
  `tools/read_bios_battery_mode.bat` remains pending user opt-in (UAC).

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
