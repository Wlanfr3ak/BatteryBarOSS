# BatteryBar OSS

> **AI disclosure:** this project was generated with the AI coding agent
> **[Devin](https://devin.ai) (Cognition AI, model SWE-2 High)** under
> human direction and review. See `NOTICE` and `AGENTS.md` §12.

A floating battery status bar for Windows 11 – an open-source replacement for
the discontinued **BatteryBar (Pro)**. Designed to grow into a
Conky/BGInfo-style desktop info widget.

- **Zero external dependencies** – runs entirely on the Python standard
  library (Tkinter + Win32 API via ctypes)
- Ready right after `git clone`: double-click `run.bat`, done
- Current version: see `CHANGELOG.md` | License: MIT

---

## Features (v0.5.0)

- Floating, frameless, transparent status bar (always-on-top)
- Battery level in %, charge state (Charging/Discharging/Full/Low/Critical)
- **Real remaining-time estimate** from the battery fuel gauge
  (`SYSTEM_BATTERY_STATE`: mWh capacities + mW drain rate) — plausible
  within seconds after unplugging, counting down to a configurable
  soft-minimum reserve instead of 0 % (see `docs/BATTERY_ESTIMATION.md`)
- **Click-to-cycle display**: left-click on the bar toggles
  `default → time → percent → rate → capacity → health` (BatteryBar-style)
- **Battery health view**: real wear %, cycle count and true
  full-charge capacity from `root\wmi` battery classes — the values
  that `Win32_Battery` hides
- **HP Battery Health Manager marker** (HP business notebooks):
  `tools/read_bios_battery_mode.bat` reads the actual BIOS setting via
  HP's WMI interface (needs admin once, UAC prompt) and the bar shows
  it in health mode as `BHM: <mode>`
- **Hover tooltip**: full battery details (machine, capacities, wear,
  cycles, voltage, estimate source) after ~400 ms on the bar
- **Resizable**: drag the right/bottom edge or the corner; the size is
  remembered, "Reset size" restores the default
- Color-coded fill per state (configurable)
- Freely draggable – position is remembered
- Context menu (right click): always-on-top, click-through mode,
  position lock, config reload, exit
- Warning popup when the low/critical thresholds are crossed
- Fully configurable via JSON (colors, thresholds, format, intervals)
- Logging to `logs/batterybar.log`

**Global hotkeys** (always active, even in click-through mode):

| Hotkey | Action |
|---|---|
| `Ctrl + Alt + B` | Toggle click-through mode |
| `Ctrl + Alt + Q` | Quit |

## Requirements

- Windows 10/11
- Python >= 3.11 (Tkinter is included in the standard installer)

Details and installation instructions: [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md)

## Installation & start

```bat
git clone https://github.com/Wlanfr3ak/BatteryBarOSS.git
cd BatteryBarOSS
run.bat
```

`run.bat` starts the bar without a console window (`pythonw`). For debugging
with a visible console:

```bat
set PYTHONPATH=%CD%\src
python -m batterybar
```

Self-test without GUI (reads config + battery status, exit code 0 = ok):

```bat
set PYTHONPATH=%CD%\src
python -m batterybar --selftest
```

## Configuration

| File | Purpose | In git? |
|---|---|---|
| `config/settings.json` | Default settings | yes |
| `config/settings.local.json` | Personal overrides (override defaults) | no |
| `config/stats.local.json` | Learned average drain rate (runtime state) | no |
| `config/hp_bios.local.json` | Cached HP BIOS battery mode (written by `tools/read_bios_battery_mode.bat`) | no |
| `config/secrets.json` | Secrets/keys (template: `secrets.example.json`) | no, never |

Key options (excerpt, full reference in `settings.json`):

| Key | Default | Description |
|---|---|---|
| `window.width` / `window.height` | `220` / `28` | Bar size (px) |
| `window.format` | `{state_icon} {percent}% · {time}` | Display template. Placeholders: `{percent}`, `{time}`, `{rate}`, `{capacity}`, `{state}`, `{state_text}`, `{state_icon}`, `{health}`, `{wear}`, `{cycles}`, `{design_wh}`, `{full_wh}`, `{machine}`, `{bhm}` |
| `window.display_mode` | `default` | `default` uses `format`; `time`/`percent`/`rate`/`capacity`/`health` show a single field — cycled by left-click |
| `estimation.soft_min_percent` | `5.0` | Reserve floor: time counts down to this %, not to real 0 % |
| `window.corner` / `offset_x` / `offset_y` | `top-right` / `20` / `20` | Start position (when no saved position) |
| `thresholds.low` / `thresholds.critical` | `30` / `15` | Thresholds for warning colors + warnings (%) |
| `colors.*` | various | Colors per state (`charging`, `discharging`, `low`, `critical`, ...) |
| `warnings.enabled` / `beep` | `true` / `false` | Warning popup/beep on threshold crossing |
| `update_interval_ms` | `1000` | Refresh interval |

Format example: `"{state_icon} {percent}% · {time}"` → `⚡ 87% · 1:42 h`

## HP battery mode (optional, HP notebooks only)

HP business notebooks manage the battery in the BIOS ("Battery Health
Manager"). The mode cannot be read without administrator rights — HP
exposes it only via `root\hp\instrumentedbios`. To display it:

1. Run `tools\read_bios_battery_mode.bat` once (accepts a UAC prompt)
2. The tool writes `config/hp_bios.local.json` with the real BIOS
   setting value (e.g. `Let HP manage my battery`)
3. The bar then shows it in `health` display mode as `BHM: <mode>`

This is an explicit firmware marker — never inferred from battery
charge or wear values. On non-HP machines the step is unnecessary;
everything simply stays empty.

## Usage

- **Left-click + drag**: move the bar (position is saved to
  `settings.local.json` on release)
- **Drag the right/bottom edge or corner**: resize the bar (size is
  saved; "Reset size" in the menu restores the default)
- **Left-click (without dragging)**: cycle the display
  `default → time → percent → rate → capacity → health`
- **Hover**: tooltip with all battery details
- **Right-click**: context menu
- **Warning toast**: appears bottom-right when the low/critical threshold is
  crossed (once per event)

## Project structure

```
├── AGENTS.md            # binding project rules (versioning, changelog, licenses)
├── CHANGELOG.md         # version history (Keep a Changelog)
├── PROJECT_MEMORY.md    # project memory (decisions, status, roadmap)
├── LICENSE              # MIT
├── README.md
├── run.bat              # launcher (pythonw, no console window)
├── config/
│   ├── settings.json           # defaults
│   └── secrets.example.json    # template for secrets.json
├── tools/
│   ├── read_bios_battery_mode.bat  # elevated HP BIOS battery-mode query
│   └── read_bios_battery_mode.ps1  # (HP WMI -> config/hp_bios.local.json)
├── src/batterybar/      # application code (see PROJECT_MEMORY.md §Architecture)
├── docs/
│   ├── REQUIREMENTS.md  # requirements (feature survey, MoSCoW, roadmap)
│   ├── DEPENDENCIES.md  # dependencies: sources, licenses, installation
│   └── RESEARCH.md      # research sources (raw files not in the repo)
└── Recherchen/          # local research raw files (not in git)
```

## Contributing / development

Please read `AGENTS.md` before making changes – it defines the changelog
requirement, SemVer versioning, commit convention (`vX.Y.Z`) and
license/source rules.

## License & sources

- This project: [MIT](LICENSE)
- Reference implementations / research: [docs/RESEARCH.md](docs/RESEARCH.md)
- Dependencies and their licenses: [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md)
- Inspired by **BatteryBar** (Osiris Development, discontinued) – a complete
  rewrite, no third-party code reused.
