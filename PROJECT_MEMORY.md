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
| 2026-10-03 | **Click = cycle display mode** (`default→time→percent→rate→capacity→health` since v0.4.0), drag threshold 6 px | Confirmed BatteryBar behavior (`BatteryBarTextDisplayState` enum found via reflection on `BatteryBar.exe`). |
| 2026-10-03 | **Battery statics via `root\wmi` + PowerShell one-shot subprocess** (v0.4.0) — NOT via `IOCTL_BATTERY_QUERY_INFORMATION` | `root\wmi` needs COM; a hidden ~300 ms `powershell` subprocess (OS component) is the cheapest stdlib-conformant path. The IOCTL route was investigated and abandoned: `SetupDiEnumDeviceInterfaces` finds no battery device interface on the dev machine (neither `GUID_DEVICE_BATTERY` `72631e55` nor class `72631e54`). |
| 2026-10-03 | **HP Battery Health Manager via explicit BIOS marker** (v0.4.0): elevated opt-in tool `tools/read_bios_battery_mode.bat` → `root\hp\instrumentedbios` `HP_BIOSSetting` → cache `config/hp_bios.local.json` | User asked for a *unique marker, not inferred from battery values*. HP WMI exists on the machine but returns access denied without elevation — there is no non-privileged marker, so elevation is an explicit documented opt-in. |
| 2026-10-03 | **Autostart = HKCU Run key + menu toggle** (v0.6.0); distribution = **PyInstaller one-file exe + Inno Setup installer** (`PrivilegesRequired=lowest` → per-user install without UAC) | User decision. Startup-folder shortcut and Task Scheduler rejected (no in-app toggle / overkill). |
| 2026-10-03 | **Frozen-mode data dir = `%LOCALAPPDATA%\BatteryBarOSS`** | Installed exe can't write next to itself under Program Files; per-user dir keeps settings/stats/logs writable. Source mode keeps repo `config/`. |

## Environment facts (dev machine)

- **Hardware: HP EliteBook 855 G7 Notebook PC**, BIOS `S77 Ver. 01.25.00`
- Battery (real values via `root\wmi`): Design 55994 mWh, Full 53673 mWh,
  120 cycles → wear ≈ 4.1 %; reports **no drain rate** (`RateOfDrain`
  = `BATTERY_UNKNOWN_RATE`); HP WMI provider `root\hp\instrumentedbios`
  + `HP_BIOSSetting` present but requires elevation
- HP BHM marker **not yet read** (UAC declined at v0.4.0 test);
  registry sweep found no HP software persisting the mode — only
  "HP Accessory WMI Provider" is installed (that IS the `root\hp`
  provider). No unprivileged marker exists, confirmed.
- Windows 11 (10.0.26100), Git 2.52
- **Build tools**: PyInstaller 6.22.2 (pip), Inno Setup 6.7.3 at
  `%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe` (per-user install via
  `winget install JRSoftware.InnoSetup`)
- Python 3.14.8 + 3.13 at `C:\Program Files\Python314\` / `Python313\`, `py` launcher present
- Windows PowerShell 5.1 (no pwsh 7)
- .NET runtimes 8/9/10 present, **no .NET SDK** (relevant if the stack ever changes)
- Repo path contains spaces → always quote paths in scripts

## GitHub / remote

- Remote: `git@github.com:Wlanfr3ak/BatteryBarOSS.git` (SSH), branch `main`
- **Releases are automated** (`.github/workflows/release.yml`, v0.6.1):
  `git tag vX.Y.Z && git push --tags` → Windows runner builds exe +
  installer → GitHub Release with setup, portable exe and the extracted
  CHANGELOG section as notes. Cutting a release = version bump commit +
  tag + push. Since v0.7.0 the release also carries `SHA256SUMS.txt`
  (updater integrity anchor — removing it breaks auto-update).
- **Code signing**: planned via **SignPath Foundation** (free for
  qualifying OSS). Decided 2026-10-03; Azure Artifact Signing rejected
  (individuals: US/CA only), EV certs pointless since 2024
  (no SmartScreen advantage). Open task: SignPath application +
  `release.yml` signing step.
- GitHub account: **Wlanfr3ak**, git author `Wlanfr3ak <6292882+Wlanfr3ak@users.noreply.github.com>`
- **Domain + site** (v0.7.3): `batterybaross.com` registered by the
  maintainer; DNS = apex A/AAAA to GitHub Pages IPs + `www` CNAME →
  `wlanfr3ak.github.io`. Site lives in `site/` (index.html + CNAME),
  deployed by `.github/workflows/pages.yml` on pushes to `main`
  (requires repo Settings → Pages → Source: "GitHub Actions").
  Screenshot is copied from `docs/` at deploy time — keep it there.
  Gotcha: never "Re-run" a failed pages job — each attempt adds another
  `github-pages` artifact and `deploy-pages` then fails with
  "Multiple artifacts". Push to `site/` (or dispatch) for a fresh run.
- **Operator / legal** (site/impressum.html + datenschutz.html):
  Fabian Horst ("Wlanfr3ak"), c/o Toppoint e.V., Holzkoppelweg 20,
  24118 Kiel. Contact channel listed = GitHub Issues (no public
  e-mail so far — adding one later is worth an Impressum update).
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
                 # CallNtPowerInformation(SYSTEM_BATTERY_STATE) -> PowerDetails (mWh/mW);
                 # read_static_info() -> BatteryStaticInfo via root\wmi PS one-shot
  sysinfo.py     # machine info via winreg (HKLM SystemInformation);
                 # HP BHM cache reader (config/hp_bios.local.json)
  autostart.py   # HKCU Run key enable/disable/is_enabled (winreg)
  updater.py     # self-update via GitHub Releases (frozen only): https-only,
                 # SHA256SUMS-verified download, %TEMP% helper-bat replace+relaunch
  estimate.py    # TimeEstimator: rate -> slope -> learned -> driver -> windows, soft-min level
  config.py      # JSON config: defaults <- settings.json <- settings.local.json (+ secrets.json)
  bar_window.py  # Tkinter floating bar: canvas, drag & drop, click-to-cycle display,
                 # context menu, click-through, hotkeys, warning toast, format templates;
                 # tooltip + resize grips + ASCII version-decrypt easter egg (>5s hover)
tools/           # read_bios_battery_mode.*: elevated HP BIOS query;
                 # build_exe.bat / build_installer.bat: PyInstaller + Inno pipeline
installer/       # entry.py (PyInstaller entry), setup.iss (Inno script),
                 # Output/ = built setup.exe (gitignored)
BatteryBarOSS.pyw# source-tree launcher (autostart target + double-click)
run.bat          # launch without console (pythonw), sets PYTHONPATH=src
config/          # settings.json, secrets.example.json (+ gitignored: local/secrets/stats/hp_bios)
docs/            # REQUIREMENTS, DEPENDENCIES, RESEARCH, BATTERY_ESTIMATION
```

Data flow: `battery.read_status()` + `read_power_details()` ->
`TimeEstimator.remaining_seconds()` -> format fields
(`{percent} {time} {rate} {capacity} {health} {wear} {cycles} {state*}`,
`~` prefix when slope/learned-estimated) -> canvas redraw in the
`after()` interval. Left-click (< 6 px) cycles `window.display_mode`;
drag moves the bar; edge drag (8 px grip) resizes it; ~400 ms hover
shows the details tooltip (FR-21).

## Open items / roadmap (details: docs/REQUIREMENTS.md section 8)

- [ ] More providers (Conky-style): CPU/RAM via `GetSystemTimes`/
      `GlobalMemoryStatusEx` (stdlib!), network IP, uptime, date/time
- [ ] Theme system (JSON themes instead of BatteryBar's PNG themes)
- [x] ~~Battery wear/details~~ v0.4.0: `root\wmi` statics (design/full mWh,
      cycles, serial) + `health` display mode. Open: charge rate, long-term
      statistics. **IOCTL path abandoned** (no battery device interface on
      dev HW — see decisions).
- [x] ~~Vendor BIOS battery mode~~ v0.4.0 (HP): explicit marker via
      elevated `tools/read_bios_battery_mode.bat`; other vendors open if
      ever needed
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
- **Percent quantization poisons rate math** (v0.4.2): never merge
  `percent·max/100` into the mWh stream — 1% steps are ~537 mWh fake
  deltas that made estimates swing 7:49↔3:52. Track `remaining_mwh`
  only; use session-average (unplug→now), not a short sliding window.
  Learned stats carry a `version` field for algorithm migrations.
- **setupapi + ctypes**: always set `restype`/`argtypes` or 64-bit
  handles get truncated to c_int (err 6). More importantly:
  `SetupDiEnumDeviceInterfaces` may simply return NO battery interface
  on some machines — do not rely on the IOCTL path, `root\wmi` works.
- **HP WMI** (`root\hp\instrumentedbios`): `HP_BIOSSetting` /
  `HP_BIOSSettingInterface` exist on EliteBooks but every query fails
  with access denied unless elevated. There is no unprivileged way to
  read the Battery Health Manager mode — opt-in elevated tool + cache.
- `Win32_Battery` fields (`EstimatedRunTime`, capacities) are
  sentinel/empty on this hardware; the real values live in `root\wmi`
  classes — and those are reachable without COM code by spawning
  `powershell -NoProfile -Command Get-WmiObject ...` once in a while.
- **Python 3.14: `.pyw` is an importable source suffix** — a file
  `batterybar.pyw` next to `sys.path` entries shadows the `batterybar`
  package (caused an infinite import recursion; hence the launcher is
  `BatteryBarOSS.pyw`).
- **Git Bash mangles `/D` ISCC args** into paths — call
  `MSYS_NO_PATHCONV=1 ISCC.exe /DAppVersion=...` or run via cmd.
- Frozen/`pythonw` runs have `sys.stderr = None` — guard
  `StreamHandler(sys.stderr)` or logging setup fails silently.
