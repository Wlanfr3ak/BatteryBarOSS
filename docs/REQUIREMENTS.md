# REQUIREMENTS.md – BatteryBar OSS requirements

Status: 2026-10-03 · Document version: 1.1 · corresponding app version: v0.2.0

---

## 1. Goal & scope

Rebuild the discontinued **BatteryBar (Pro)** software as an open-source
tool for Windows 11: a compact, floating bar that shows the battery level
at a glance. Second direction: the bar should – inspired by **Conky**
(Linux) and **BGInfo/DesktopInfo** (Windows) – be extensible with
additional desktop information.

**Out of scope** (deliberate boundaries):

- No taskbar deskbar integration – deskbands no longer exist on
  Windows 11 (BatteryBar's original approach is not reproducible).
- No wallpaper rendering (BGInfo/PowerBGInfo's approach) – we draw our
  own live window, not background image manipulation.
- No skin ecosystem like Rainmeter (overkill); instead a lean JSON
  configuration + optional JSON themes later.

## 2. Background / motivation

- BatteryBar installed as a taskbar toolbar (deskband); the project
  (Osiris Development) is discontinued and Windows 11 no longer supports
  deskbands.
- Requirement: small, resource-friendly, always-visible battery widget
  without installation and dependency baggage → core principle
  **"clone & run"**.

## 3. Feature survey of reference tools

Sources: `Recherchen/` (local, not in git) + `docs/RESEARCH.md`.

| Tool | Relevant features | What we adopt |
|---|---|---|
| **BatteryBar (Pro) 3.6.6** | Battery %, charge state, remaining-time estimate (from own history!), state themes (Default/Discharging/Low/Critical/Charging), low/critical warnings (Windows sounds), configurable thresholds, font/size selection, translations | State model + thresholds + color coding, format-string flexibility (color themes instead of PNG themes initially), warnings, later: own runtime estimate from discharge history |
| **BGInfo (Sysinternals)** | System data (host, OS, CPU, RAM, IP ...) as desktop text, freely selectable fields | Idea of configurable data fields (provider concept) |
| **DesktopInfo 3.23** | INI config, very many data providers (WMI, registry, files, performance counters), pages/navigation, drag position, portable EXE | Provider registry; principle "a text config file is enough"; portability |
| **PowerBGInfo** (PS module) | Wallpaper generation with configurable values/charts, JSON export, builtin values | Confirms need for builtin providers; JSON config approach |
| **Rainmeter 4.5.26** | Skin/widget system, measures + meters, freely placed windows | Rough idea "provider supplies value, view renders it" – heavily simplified |
| **Conky** (comparison, Linux) | Format strings with variables (`${battery_percent}`), scriptability, minimal footprint | Format template `{percent}` etc. in `window.format` |

**Common denominator:** provider (data source) -> preparation/formatting
-> lightweight desktop display. Exactly this pattern is our architecture
(`battery.py` as provider, `bar_window.py` as view).

## 4. Functional requirements (MoSCoW)

### Must (MVP – implemented with v0.1.0)

| ID | Requirement | Status |
|---|---|---|
| FR-01 | Floating, frameless, always-on-top bar | ✅ v0.1.0 |
| FR-02 | Battery level in % (Win32 `GetSystemPowerStatus`) | ✅ v0.1.0 |
| FR-03 | Charge states: charging / discharging / full / low / critical / no battery, color-coded | ✅ v0.1.0 |
| FR-04 | Remaining-time display (Windows estimate, "—" when unknown) → **v0.3.0: own hybrid estimator** (fuel-gauge rate → own slope → driver estimate → Windows fallback; see `docs/BATTERY_ESTIMATION.md`) | ✅ v0.1.0 / improved v0.3.0 |
| FR-05 | Freely positionable via drag & drop, position persisted | ✅ v0.1.0 |
| FR-06 | JSON configuration (colors, thresholds, format, interval, start position) | ✅ v0.1.0 |
| FR-07 | Context menu: always-on-top, click-through, position lock, reload, exit | ✅ v0.1.0 |
| FR-08 | Warning on low/critical threshold (toast + optional beep) | ✅ v0.1.0 |
| FR-09 | No external dependencies (Python stdlib only) | ✅ v0.1.0 |
| FR-10 | Start without console (`run.bat` / `pythonw`), file logging | ✅ v0.1.0 |
| FR-10a | Click-to-cycle display mode (time/percent/rate/capacity) — BatteryBar behavior | ✅ v0.3.0 |

### Should (next releases)

| ID | Requirement |
|---|---|
| FR-11 | Extend provider architecture: more data sources via stdlib (`GetSystemTimes` CPU, `GlobalMemoryStatusEx` RAM, uptime, date/time, IP) – modelled on DesktopInfo/Conky |
| FR-12 | Own runtime estimate from discharge history (BatteryBar Pro feature); persist history. **Partially done v0.3.0**: rate-based + slope + driver fallback implemented; still open: persisted statistical discharge profile |
| FR-13 | Battery health: design vs. full-charge capacity, charge rate — **partially done v0.4.0**: design/full capacity, cycle count, serial, wear % via `root\wmi` classes (IOCTL path investigated, not enumerable on dev HW); still open: charge rate, statistics |
| FR-13a | Vendor BIOS battery-management mode via explicit firmware marker (not inferred from battery values) — **v0.4.0 for HP**: `tools/read_bios_battery_mode.bat` reads `root\hp\instrumentedbios` `HP_BIOSSetting` elevated, caches to `hp_bios.local.json`; shown in `health` mode as `BHM:` |
| FR-14 | Theme system: JSON themes (color sets), theme switch in the context menu |
| FR-15 | Autostart option (task/registry Run key, toggleable from the menu) | ✅ v0.6.0 — HKCU Run key + "Start with Windows" menu toggle |
| FR-16 | Multi-monitor awareness (monitor choice, correct corner anchoring) |
| FR-17 | Additional rows/blocks in the bar for provider values |
| FR-18 | Configurable hotkeys |

### Could (later / optional)

| ID | Requirement |
|---|---|
| FR-19 | Optional single-EXE build via PyInstaller (dev tool only, no runtime dep) | ✅ v0.6.0 — `tools\build_exe.bat` → `dist\BatteryBarOSS.exe`; plus Inno Setup installer `tools\build_installer.bat` |
| FR-20 | Rounded corners / icons via PNG assets with alpha (chroma alternative) |
| FR-21 | Tooltip with details (capacity mWh, health, voltage) | ✅ v0.5.0 — hover tooltip with all details incl. estimate source |
| FR-25 | Resizable bar (edge drag) | ✅ v0.5.0 — right/bottom edge + corner grips, persisted size, "Reset size" menu entry |
| FR-26 | Self-update from GitHub Releases: one-time consent question, HTTPS-only, SHA-256-verified download (`SHA256SUMS.txt` release asset), one-step replace+relaunch, settings preserved | ✅ v0.7.0 — `updater.py`, frozen builds only |
| FR-22 | Mini history graph (discharge curve) in a popup |
| FR-23 | UI translations (de/en) – English is the default since v0.2.0 |
| FR-24 | Settings dialog (GUI instead of JSON editing) |

### Won't (rejected)

| ID | Decision | Reason |
|---|---|---|
| W-01 | Taskbar deskband | technically impossible on Windows 11 |
| W-02 | Wallpaper rendering (BGInfo approach) | different concept; live window chosen |
| W-03 | Skin engine/plugin API like Rainmeter | complexity vs. benefit; JSON suffices |

## 5. Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-01 | **Zero-dependency runtime**: after `git clone` + installed Python >= 3.11, `run.bat` starts without further steps |
| NFR-02 | Small footprint: idle CPU ~0% (interval polling >= 500 ms), RAM < ~50 MB (measured v0.1.0: ~41 MB incl. Python/Tkinter) |
| NFR-03 | Windows 10/11; DPI-scaling safe |
| NFR-04 | Secrets never in the repo (`config/secrets.json`, gitignored) |
| NFR-05 | Documentation requirement: changelog, README, dependencies table with every change (AGENTS.md) |
| NFR-06 | Every version one commit `vX.Y.Z` with changelog body (GitHub traceability) |
| NFR-07 | Repo is self-contained: no local paths/artifacts needed, clone -> continue working |
| NFR-08 | No admin rights required for normal operation |

## 6. MVP acceptance criteria (v0.1.0)

- [x] `run.bat` starts the bar without a console; it shows the current battery %
- [x] State colors switch correctly (charging/discharging/low/critical)
- [x] Bar is draggable; restarts return to the old position
- [x] `--selftest` runs cleanly (config + battery read)
- [x] `python -m compileall src` without errors
- [x] `git status` shows no research raw files/secrets as tracked

## 7. Data sources (technical)

| Data | Source | Access |
|---|---|---|
| Battery %, charge state, remaining seconds | Win32 `GetSystemPowerStatus` | ctypes (kernel32) |
| Battery mWh/mW live values | `CallNtPowerInformation(SYSTEM_BATTERY_STATE)` | ctypes (powrprof) |
| Battery statics (design/full capacity, cycles, serial) | `root\wmi` classes `BatteryStaticData`, `BatteryFullChargedCapacity`, `BatteryCycleCount` | PowerShell one-shot subprocess (COM needs no stdlib binding; IOCTL path not enumerable on dev HW) |
| Machine model / BIOS / vendor | Registry `HKLM\SYSTEM\CurrentControlSet\Control\SystemInformation` | stdlib `winreg` |
| (optional) HP BIOS battery mode | `root\hp\instrumentedbios` `HP_BIOSSetting` | elevated PowerShell tool, JSON cache |
| (later) CPU/RAM | `GetSystemTimes`, `GlobalMemoryStatusEx` | ctypes (kernel32) |
| (later) IP/network | `GetAdaptersAddresses` or similar | ctypes (iphlpapi) |
| Config | JSON files `config/` | stdlib json |
| Beep | `winsound` | stdlib |

## 8. Roadmap (rough targets)

- **v0.1.x** ✅ MVP: floating battery bar, config, warnings, doc skeleton
- **v0.2.0** ✅ Project language switched to English (docs + UI)
- **v0.3.0** ✅ Hybrid remaining-time estimator (fuel-gauge mWh/mW), click-to-cycle display; research doc `docs/BATTERY_ESTIMATION.md`
- **v0.4.0** ✅ Battery health info (wear %, cycles, capacities via `root\wmi`),
  machine identification, HP Battery Health Manager marker (elevated tool),
  `health` display mode (FR-13 partial, FR-13a)
- **v0.5.x**: Provider framework + CPU/RAM/time fields (FR-11, FR-17),
  JSON themes (FR-14), autostart (FR-15), tooltip (FR-21)
- **v0.6.x**: Multi-monitor (FR-16), configurable hotkeys (FR-18)
- **v1.0.0**: Feature parity with BatteryBar Pro core functions + stability
