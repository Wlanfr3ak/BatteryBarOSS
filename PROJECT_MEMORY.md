# PROJECT_MEMORY.md – BatteryBar OSS project memory

This file is the **project's memory** (per AGENTS.md section 8).
Every working instance reads it at the start and updates it when
relevant decisions/insights are made.

---

## Vision

Open-source rebuild of "BatteryBar (Pro)" (discontinued, Osiris
Development) for Windows 11: a floating, always-on-top battery status
bar. Long-term goal: extensible to a Conky-/BGInfo-style desktop info
tool (additional data providers beyond battery: CPU, RAM, network,
uptime, ...).

## Decisions made

| Date | Decision | Rationale |
|---|---|---|
| 2026-10-03 | **Tech stack: Python + Tkinter, standard library only** (ctypes for the Win32 battery API) | User requirement: minimal dependencies; Python 3.14 already installed; runs without setup after `git clone`. Alternatives .NET/WPF (needs SDK, not installed) and PowerShell+WPF (clunky) rejected – decision confirmed by the user. |
| 2026-10-03 | License: **MIT** | Standard for small OSS tools, maximally permissive. Can still be changed early. |
| 2026-10-03 | **Project language: English** (docs, UI, commits, changelog); maintainer communicates in German outside the repo | User decision with v0.2.0: broader OSS reach. |
| 2026-10-03 | Windows 11 reality: deskbands/taskbar toolbars (BatteryBar's original approach) no longer exist on Win11 → **floating window** as replacement | `overrideredirect` + `-topmost` + `-transparentcolor` in Tkinter. |
| 2026-10-03 | Versioning: SemVer, single source = `__version__` in `src/batterybar/__init__.py`; every version = 1 commit with `vX.Y.Z:` prefix | User requirement for GitHub traceability. |
| 2026-10-03 | Config layering: `config/settings.json` (defaults, committed) <- `config/settings.local.json` (user overrides, gitignored) <- `config/secrets.json` (gitignored) | Secrets rule + clone compatibility without local leaks. |
| 2026-10-03 | `Recherchen/` stays local (gitignored); sources in `docs/RESEARCH.md` | User requirement; licensing/size reasons. |
| 2026-10-03 | Click-through toggled via global hotkey `Ctrl+Alt+B` (GetAsyncKeyState polling, no RegisterHotKey – Tk would never see WM_HOTKEY otherwise); `Ctrl+Alt+Q` = quit | Otherwise the bar would be unreachable in click-through mode. |
| 2026-10-03 | Startup toast when `click_through` is loaded from config (v0.1.2) | Prevents silent lockout – user reported unclickable bar after restart. |
| 2026-10-03 | GitHub remote via **SSH** (`~/.ssh/fabian` key registered on GitHub), branch `main` | User chose SSH over HTTPS+GCM. |
| 2026-10-03 | **Mandatory AI disclosure** (AGENTS.md §12): marked as generated with **Devin (Cognition AI), model SWE-2 High** — in README top block, `NOTICE`, app menu header, commit footers | User requirement: AI authorship must stay clearly visible. |
| 2026-10-03 | **Estimation = hybrid fallback chain** (v0.3.0): fuel-gauge `RateOfDrain`/`mWh` via `CallNtPowerInformation(SYSTEM_BATTERY_STATE)` → own 5-min slope → driver `EstimatedTime` → Windows `BatteryLifeTime`; soft-min level 5 % | BatteryBar's documented strategy (Osiris Wiki); WMI `EstimatedRunTime` proven garbage by live probe. Findings: `docs/BATTERY_ESTIMATION.md`. |
| 2026-10-03 | **Click = cycle display mode** (`default→time→percent→rate→capacity`), drag threshold 6 px | Confirmed BatteryBar behavior (`BatteryBarTextDisplayState` enum found via reflection on `BatteryBar.exe`). |

## Environment facts (dev machine)

- Windows 11 (10.0.26100), Git 2.52
- Python 3.14.8 + 3.13 at `C:\Program Files\Python314\` / `Python313\`, `py` launcher present
- Windows PowerShell 5.1 (no pwsh 7)
- .NET runtimes 8/9/10 present, **no .NET SDK** (relevant if the stack ever changes)
- Repo path contains spaces → always quote paths in scripts

## GitHub / remote

- Remote: `git@github.com:Wlanfr3ak/BatteryBarOSS.git` (SSH), branch `main`
- GitHub account: **Wlanfr3ak**, git author `Wlanfr3ak <6292882+Wlanfr3ak@users.noreply.github.com>`
- SSH auth: key `~/.ssh/fabian` (ed25519, registered on GitHub 2026-10-03);
  `~/.ssh/config` contains `Host github.com` with
  `IdentityFile ~/.ssh/fabian` + `IdentitiesOnly yes`
- `gh` CLI not installed; Git Credential Manager 2.6.1 present
  (HTTPS fallback would work with it)

## Architecture status

```
src/batterybar/
  __init__.py    # __version__ (single source of truth)
  __main__.py    # entry: DPI awareness, console encoding, logging, CLI (--selftest)
  battery.py     # Win32 GetSystemPowerStatus -> BatteryStatus;
                 # CallNtPowerInformation(SYSTEM_BATTERY_STATE) -> PowerDetails (mWh/mW)
  estimate.py    # TimeEstimator: rate -> slope -> driver -> windows fallback, soft-min level
  config.py      # JSON config: defaults <- settings.json <- settings.local.json (+ secrets.json)
  bar_window.py  # Tkinter floating bar: canvas, drag & drop, click-to-cycle display,
                 # context menu, click-through, hotkeys, warning toast, format templates
run.bat          # launch without console (pythonw), sets PYTHONPATH=src
config/          # settings.json, secrets.example.json (+ gitignored: local/secrets)
docs/            # REQUIREMENTS, DEPENDENCIES, RESEARCH, BATTERY_ESTIMATION
```

Data flow: `battery.read_status()` + `read_power_details()` ->
`TimeEstimator.remaining_seconds()` -> format fields
(`{percent} {time} {rate} {capacity} {state*}`, `~` prefix when
slope-estimated) -> canvas redraw in the `after()` interval.
Left-click (< 6 px) cycles `window.display_mode`; drag moves the bar.

## Open items / roadmap (details: docs/REQUIREMENTS.md section 8)

- [ ] More providers (Conky-style): CPU/RAM via `GetSystemTimes`/
      `GlobalMemoryStatusEx` (stdlib!), network IP, uptime, date/time
- [ ] Theme system (JSON themes instead of BatteryBar's PNG themes)
- [ ] Battery details via `IOCTL_BATTERY_QUERY_INFORMATION`: charge rate,
      wear (FullCharged vs. DesignCapacity), statistics/history
- [x] ~~Own remaining-time estimate~~ v0.3.0: hybrid estimator implemented
      (rate -> slope -> driver -> windows). Still open: **persisted
      statistical discharge profile** (BatteryBar's statistical mode —
      survives restarts, learns long-term drain patterns)
- [ ] Multi-monitor/DPI refinements, rounded corners (PNG/alpha)
- [ ] Optional PyInstaller single-EXE build (optional dev tool only!)
- [ ] Autostart option (registry Run key or autostart shortcut)
- [ ] UI translations (de/en) – strings are English since v0.2.0
- [ ] Tests: currently `--selftest`; unit tests for config/format useful
- [ ] README screenshots

## Lessons learned / pitfalls

- `tk.Menu` context menu is unreachable under a click-through window
  → hotkey escape route is mandatory (user hit this in v0.1.2).
- Call `SetProcessDpiAwareness(2)` **before** `tk.Tk()` (shcore -> user32 fallback).
- `winsound` is a Windows stdlib module → beeps without extra deps.
- Windows consoles use cp1252 → reconfigure stdout/stderr to UTF-8 with
  `errors="replace"` or unicode icons crash printing/logging.
- Git config must not be modified (project rule) – line endings are
  handled via `.gitattributes`.
- The `read`/`edit` file tools refuse gitignored files (e.g.
  `settings.local.json`) – modify them via `exec`/python instead.
- `RateOfDrain` can be `0x80000000` = `BATTERY_UNKNOWN_RATE` — dev
  machine's battery reports **no rate at all** (v0.3.1 bug: showed
  "0:00 h"). Always treat the sentinel as "not reported". Learned
  drain rate in `config/stats.local.json` (EWMA) is then the only
  instant estimate — exactly like BatteryBar's historical profile.
- `q1 - floor <= 0` edge: estimates count to the soft-min floor, so
  "0:00" near the reserve is correct behavior, not a bug.
