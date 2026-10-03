# BatteryBar OSS

A floating battery status bar for Windows 11 – an open-source replacement for
the discontinued **BatteryBar (Pro)**. Designed to grow into a
Conky/BGInfo-style desktop info widget.

- **Zero external dependencies** – runs entirely on the Python standard
  library (Tkinter + Win32 API via ctypes)
- Ready right after `git clone`: double-click `run.bat`, done
- Current version: see `CHANGELOG.md` | License: MIT

---

## Features (v0.2.0)

- Floating, frameless, transparent status bar (always-on-top)
- Battery level in %, charge state (Charging/Discharging/Full/Low/Critical),
  remaining-time estimate
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
| `config/secrets.json` | Secrets/keys (template: `secrets.example.json`) | no, never |

Key options (excerpt, full reference in `settings.json`):

| Key | Default | Description |
|---|---|---|
| `window.width` / `window.height` | `220` / `28` | Bar size (px) |
| `window.format` | `{state_icon} {percent}%` | Display template. Placeholders: `{percent}`, `{time}`, `{state}`, `{state_text}`, `{state_icon}` |
| `window.corner` / `offset_x` / `offset_y` | `top-right` / `20` / `20` | Start position (when no saved position) |
| `thresholds.low` / `thresholds.critical` | `30` / `15` | Thresholds for warning colors + warnings (%) |
| `colors.*` | various | Colors per state (`charging`, `discharging`, `low`, `critical`, ...) |
| `warnings.enabled` / `beep` | `true` / `false` | Warning popup/beep on threshold crossing |
| `update_interval_ms` | `1000` | Refresh interval |

Format example: `"{state_icon} {percent}% · {time}"` → `⚡ 87% · 1:42 h`

## Usage

- **Left-click + drag**: move the bar (position is saved to
  `settings.local.json` on release)
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
