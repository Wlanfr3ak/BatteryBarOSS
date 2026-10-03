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
| FR-04 | Remaining-time display (Windows estimate, "—" when unknown) | ✅ v0.1.0 |
| FR-05 | Freely positionable via drag & drop, position persisted | ✅ v0.1.0 |
| FR-06 | JSON configuration (colors, thresholds, format, interval, start position) | ✅ v0.1.0 |
| FR-07 | Context menu: always-on-top, click-through, position lock, reload, exit | ✅ v0.1.0 |
| FR-08 | Warning on low/critical threshold (toast + optional beep) | ✅ v0.1.0 |
| FR-09 | No external dependencies (Python stdlib only) | ✅ v0.1.0 |
| FR-10 | Start without console (`run.bat` / `pythonw`), file logging | ✅ v0.1.0 |

### Should (next releases)

| ID | Requirement |
|---|---|
| FR-11 | Extend provider architecture: more data sources via stdlib (`GetSystemTimes` CPU, `GlobalMemoryStatusEx` RAM, uptime, date/time, IP) – modelled on DesktopInfo/Conky |
| FR-12 | Own runtime estimate from discharge history (BatteryBar Pro feature: the Windows estimate is often inaccurate); persist history |
| FR-13 | Battery health: design vs. full-charge capacity, charge rate (`IOCTL_BATTERY_QUERY_INFORMATION` / `CallNtPowerInformation`) |
| FR-14 | Theme system: JSON themes (color sets), theme switch in the context menu |
| FR-15 | Autostart option (task/registry Run key, toggleable from the menu) |
| FR-16 | Multi-monitor awareness (monitor choice, correct corner anchoring) |
| FR-17 | Additional rows/blocks in the bar for provider values |
| FR-18 | Configurable hotkeys |

### Could (later / optional)

| ID | Requirement |
|---|---|
| FR-19 | Optional single-EXE build via PyInstaller (dev tool only, no runtime dep) |
| FR-20 | Rounded corners / icons via PNG assets with alpha (chroma alternative) |
| FR-21 | Tooltip with details (capacity mWh, health, voltage) |
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
| (later) Battery details, health | `IOCTL_BATTERY_QUERY_INFORMATION`, `CallNtPowerInformation` | ctypes (setupapi/powrprof) |
| (later) CPU/RAM | `GetSystemTimes`, `GlobalMemoryStatusEx` | ctypes (kernel32) |
| (later) IP/network | `GetAdaptersAddresses` or similar | ctypes (iphlpapi) |
| Config | JSON files `config/` | stdlib json |
| Beep | `winsound` | stdlib |

## 8. Roadmap (rough targets)

- **v0.1.x** ✅ MVP: floating battery bar, config, warnings, doc skeleton
- **v0.2.0** ✅ Project language switched to English (docs + UI)
- **v0.3.x**: Provider framework + CPU/RAM/time fields; format string with
  arbitrary providers; FR-11, FR-17
- **v0.4.x**: Battery details & own runtime estimate (FR-12, FR-13), tooltip
- **v0.5.x**: JSON themes + theme menu (FR-14), autostart (FR-15)
- **v0.6.x**: Multi-monitor (FR-16), configurable hotkeys (FR-18)
- **v1.0.0**: Feature parity with BatteryBar Pro core functions + stability
