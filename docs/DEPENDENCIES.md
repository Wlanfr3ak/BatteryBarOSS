# DEPENDENCIES.md – dependencies, sources & licenses

Authoritative table per `AGENTS.md` section 4. Kept updated with every change.
**Runtime principle: Python standard library only – no `pip install` needed.**

Status: 2026-10-03 (v0.2.0)

---

## 1. Runtime dependencies

| # | Dependency | Version | Purpose | Source | License | Installation |
|---|---|---|---|---|---|---|
| 1 | **Python** | >= 3.11 (developed with 3.14.8) | Interpreter/runtime | https://www.python.org/downloads/ | [PSF-2.0](https://docs.python.org/3/license.html) (OSI-approved, GPL-compatible) | `winget install Python.Python.3.14` or the installer from python.org. Enable "Add python.exe to PATH"; Tkinter is included in the standard installer |
| 2 | **Tkinter / tk** | bundled with Python | GUI window (floating bar, canvas, menu) | bundled with Python (Tk 8.6.x) | Tcl/Tk License (BSD-style, free) | included – no separate step; with "custom install" keep *tcl/tk and IDLE* enabled |
| 3 | **Win32 API** | OS component | Battery status (`kernel32!GetSystemPowerStatus`), window styles (`user32`), sound (`winmm` via `winsound`) | part of Windows | Microsoft Windows – no separate license needed | not installable – OS component, accessed via `ctypes`/`winsound` (stdlib) |

**Python modules used (all standard library):**
`tkinter`, `ctypes`, `json`, `argparse`, `logging`, `logging.handlers`,
`pathlib`, `dataclasses`, `winsound`, `sys`, `os`

## 2. Development tools

| # | Tool | Version | Purpose | Source | License | Installation |
|---|---|---|---|---|---|---|
| 1 | **Git** | 2.x (developed with 2.52) | Version control | https://git-scm.com/download/win | [GPL-2.0](https://git-scm.com/about/free-and-open-source) | `winget install Git.Git` or installer |

## 3. Optional tools (never a runtime requirement)

| # | Tool | Version | Purpose | Source | License | Installation |
|---|---|---|---|---|---|---|
| 1 | **PyInstaller** | >= 6.x (optional, not in use yet) | Building a single EXE for users without Python | https://pyinstaller.org/ | GPL-2.0 **with** [bootloader exception](https://pyinstaller.org/en/stable/license.html) (compiled outputs freely usable) | `pip install pyinstaller` – for maintainer releases only; end users then need no Python at all |

## 4. Third-party resources

Currently **no** third-party resources (icons, images, code, fonts) in
the project. If added in the future: an entry here is mandatory
(AGENTS.md section 11).

| Resource | Source | License | Usage |
|---|---|---|---|
| – | – | – | – |

## 5. Research references (not part of the software)

See `docs/RESEARCH.md` – all analysed third-party tools are documented
there with source and license. Their raw files live locally under
`Recherchen/` and are **not** committed to git.

## 6. Compatibility notes

- Windows 10/11 (developed on Windows 11 24H2)
- Python 3.11+ required for the type-annotation style used;
  tested with 3.14
- No admin rights required
