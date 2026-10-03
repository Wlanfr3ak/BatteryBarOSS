# DEPENDENCIES.md – dependencies, sources & licenses

Authoritative table per `AGENTS.md` section 4. Kept updated with every change.
**Runtime principle: Python standard library only – no `pip install` needed.**

Status: 2026-10-03 (v0.4.0)

---

## 1. Runtime dependencies

| # | Dependency | Version | Purpose | Source | License | Installation |
|---|---|---|---|---|---|---|
| 1 | **Python** | >= 3.11 (developed with 3.14.8) | Interpreter/runtime | https://www.python.org/downloads/ | [PSF-2.0](https://docs.python.org/3/license.html) (OSI-approved, GPL-compatible) | `winget install Python.Python.3.14` or the installer from python.org. Enable "Add python.exe to PATH"; Tkinter is included in the standard installer |
| 2 | **Tkinter / tk** | bundled with Python | GUI window (floating bar, canvas, menu) | bundled with Python (Tk 8.6.x) | Tcl/Tk License (BSD-style, free) | included – no separate step; with "custom install" keep *tcl/tk and IDLE* enabled |
| 3 | **Win32 API** | OS component | Battery status (`kernel32!GetSystemPowerStatus`, `powrprof!CallNtPowerInformation`), window styles (`user32`), sound (`winmm` via `winsound`), machine info (registry via `winreg`) | part of Windows | Microsoft Windows – no separate license needed | not installable – OS component, accessed via `ctypes`/`winsound`/`winreg` (stdlib) |
| 4 | **Windows PowerShell** | 5.1+ (OS component) | One-shot query of `root\wmi` battery static classes (design/full capacity, cycles — COM has no stdlib binding); optional elevated HP BIOS mode query (`tools/read_bios_battery_mode.*`) | ships with Windows | Microsoft Windows – OS component | not installable – already on every Windows 10/11 system; launched hidden via `subprocess` |

**Python modules used (all standard library):**
`tkinter`, `ctypes`, `json`, `argparse`, `logging`, `logging.handlers`,
`pathlib`, `dataclasses`, `winsound`, `sys`, `os`, `subprocess`, `winreg`

## 2. Development tools

| # | Tool | Version | Purpose | Source | License | Installation |
|---|---|---|---|---|---|---|
| 1 | **Git** | 2.x (developed with 2.52) | Version control | https://git-scm.com/download/win | [GPL-2.0](https://git-scm.com/about/free-and-open-source) | `winget install Git.Git` or installer |

## 3. Optional tools (never a runtime requirement)

| # | Tool | Version | Purpose | Source | License | Installation |
|---|---|---|---|---|---|---|
| 1 | **PyInstaller** | 6.22.2 (in use since v0.6.0) | Building `dist\BatteryBarOSS.exe` for users without Python (`tools\build_exe.bat`) | https://pyinstaller.org/ | GPL-2.0 **with** [bootloader exception](https://pyinstaller.org/en/stable/license.html) (compiled outputs freely usable) | `pip install pyinstaller` – for maintainer releases only; end users then need no Python at all |
| 2 | **Inno Setup** | 6.7.3 (in use since v0.6.0) | Compiling `installer\setup.iss` into `BatteryBarOSS-Setup-X.Y.Z.exe` (`tools\build_installer.bat`) | https://jrsoftware.org/isinfo.php | [Inno Setup License](https://jrsoftware.org/files/is/license.txt) (free for any use, may be installed/used without fee) | `winget install JRSoftware.InnoSetup` – maintainer build only |

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

- **Portable/installer EXE (v0.6.0+): zero additional dependencies.**
  The PyInstaller bundle embeds the interpreter (`python314.dll`),
  the VC++ runtime (`VCRUNTIME140*.dll`, `ucrtbase.dll`) and
  tk/Tkinter — no Python, vcredist or pip needed on Windows 10/11 x64.
  Notes: `powershell.exe` (OS component) is spawned rarely for
  `root\wmi` battery statics and degrades gracefully if absent;
  unsigned PyInstaller one-file exes may trigger SmartScreen/AV
  warnings (cosmetic, no signing cert yet); x64 build only (ARM64 via
  emulation); ~14 MB unpacked to `%TEMP%` per start.
- Windows 10/11 (developed on Windows 11 24H2)
- Python 3.11+ required for the type-annotation style used;
  tested with 3.14
- No admin rights required for normal operation; the **optional**
  HP BIOS battery-mode readout (`tools/read_bios_battery_mode.bat`)
  triggers a one-time UAC prompt (HP WMI provider requires elevation)
- `root\wmi` battery statics are queried via a PowerShell one-shot
  (~300 ms, hourly + on reload); if PowerShell is unavailable the
  fields simply stay empty
