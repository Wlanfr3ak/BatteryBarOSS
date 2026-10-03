# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
versioning follows [Semantic Versioning](https://semver.org/).
Rules: see `AGENTS.md` sections 1-3.

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
