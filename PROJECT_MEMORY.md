# PROJECT_MEMORY.md – Projektgedächtnis BatteryBar OSS

Diese Datei ist das **Gedächtnis des Projekts** (lt. AGENTS.md §8).
Jede bearbeitende Instanz liest sie zu Beginn und aktualisiert sie bei
relevanten Entscheidungen/Erkenntnissen.

---

## Zielbild

Open-Source-Nachbau von „BatteryBar (Pro)" (eingestellt, Osiris Development)
für Windows 11: eine frei schwebende, always-on-top Akku-Statusleiste.
Perspektivisch erweiterbar zu einem Conky-/BGInfo-artigen Desktop-Info-Tool
(weitere Daten-Provider neben Akku: CPU, RAM, Netz, Uptime …).

## Getroffene Entscheidungen

| Datum | Entscheidung | Begründung |
|---|---|---|
| 2026-10-03 | **Tech-Stack: Python + Tkinter, ausschließlich Standardbibliothek** (ctypes für Win32-Akku-API) | User-Wunsch: minimale Abhängigkeiten; Python 3.14 bereits installiert; nach `git clone` ohne Setup lauffähig. Alternativen .NET/WPF (braucht SDK, nicht installiert) und PowerShell+WPF (unhandlich) verworfen – Entscheidung vom User bestätigt. |
| 2026-10-03 | Lizenz: **MIT** | Standard für kleine OSS-Tools, maximal permissiv. Kann früh noch geändert werden. |
| 2026-10-03 | Doku-Sprache **Deutsch**, Code-Kommentare/Identifier **Englisch** | User kommuniziert Deutsch; OSS-Internationalisierung später möglich. |
| 2026-10-03 | Windows-11-Realität: Deskbands/Taskbar-Toolbars (Original-Ansatz von BatteryBar) existieren unter Win11 nicht mehr → **frei schwebendes Fenster** als Ersatz | `overrideredirect` + `-topmost` + `-transparentcolor` in Tkinter. |
| 2026-10-03 | Versionierung: SemVer, Single Source = `__version__` in `src/batterybar/__init__.py`; jede Version = 1 Commit mit `vX.Y.Z:`-Präfix | User-Anforderung Nachverfolgbarkeit auf GitHub. |
| 2026-10-03 | Config-Schichtung: `config/settings.json` (Defaults, committed) ← `config/settings.local.json` (User-Overrides, gitignored) ← `config/secrets.json` (gitignored) | Secrets-Regel + Klon-Kompatibilität ohne lokale Leaks. |
| 2026-10-03 | `Recherchen/` bleibt lokal (gitignored); Quellen in `docs/RESEARCH.md` | User-Anforderung; Lizenz-/Größengründe. |
| 2026-10-03 | Click-Through per globalem Hotkey `Strg+Alt+B` umschaltbar (GetAsyncKeyState-Polling, kein RegisterHotKey – Tk sieht WM_HOTKEY sonst nicht); `Strg+Alt+Q` = Beenden | Sonst wäre die Leiste im Durchklick-Modus nicht mehr erreichbar. |

## Umgebungs-Fakten (Entwicklungsmaschine)

- Windows 11 (10.0.26100), Git 2.52
- Python 3.14.8 + 3.13 unter `C:\Program Files\Python314\` / `Python313\`, `py`-Launcher vorhanden
- Windows PowerShell 5.1 (kein pwsh 7)
- .NET-Runtimes 8/9/10 vorhanden, **kein .NET SDK** (relevant falls Stack-Wechsel)
- Repo-Pfad enthält Leerzeichen → Pfade in Skripten immer quoten

## Architektur-Stand

```
src/batterybar/
  __init__.py    # __version__ (Single Source of Truth)
  __main__.py    # Entry: DPI-Awareness, Logging, CLI (--selftest), App-Start
  battery.py     # Win32 GetSystemPowerStatus via ctypes -> BatteryStatus
  config.py      # JSON-Config: Defaults <- settings.json <- settings.local.json (+ secrets.json)
  bar_window.py  # Tkinter-Floating-Bar: Canvas, Drag&Drop, Kontextmenü,
                 # Click-Through, Hotkeys, Warn-Toast, Format-Templates
run.bat          # Start ohne Konsole (pythonw), setzt PYTHONPATH=src
config/          # settings.json, secrets.example.json (+ gitignored: local/secrets)
docs/            # REQUIREMENTS, DEPENDENCIES, RESEARCH
```

Datenfluss: `battery.read_status()` → `derive_state()` → Format-String
(`window.format`, Platzhalter `{percent} {time} {state_text} {state_icon}`)
→ Canvas-Redraw im `after()`-Intervall.

## Offene Punkte / Roadmap (Details: docs/REQUIREMENTS.md §8)

- [ ] Weitere Provider (Conky-artig): CPU/RAM via `GetSystemTimes`/
      `GlobalMemoryStatusEx` (stdlib!), Netz-IP, Uptime, Datum/Zeit
- [ ] Theme-System (JSON-Themes statt PNG-Themes wie BatteryBar)
- [ ] Akku-Details via `IOCTL_BATTERY_QUERY_INFORMATION`: Laderate,
      Verschleiß (FullCharged vs. DesignCapacity), Statistik/History
- [ ] Verbleibende-Laufzeit-Lernkurve (BatteryBar-Pro-Stil: eigene Schätzung
      aus Entladehistorie statt Windows-Schätzwert)
- [ ] Multi-Monitor-/DPI-Feinschliff, abgerundete Ecken (PNG/Alpha)
- [ ] Optionaler PyInstaller-Einzel-EXE-Build (nur optionales Dev-Tool!)
- [ ] Auto-Start-Option (Registry Run-Key oder Autostart-Shortcut)
- [ ] Tests: derzeit `--selftest`; Unit-Tests für config/format sinnvoll
- [ ] README-Screenshots, englische README-Variante

## Lessons Learned / Fallstricke

- `tk.Menu`-Kontextmenü ist unter einem „durchklickbaren" Fenster
  unerreichbar → Hotkey-Ausweg ist Pflicht.
- `SetProcessDpiAwareness(2)` **vor** `tk.Tk()` aufrufen (shcore → user32-Fallback).
- `winsound` ist Windows-stdlib → Warntöne ohne Extra-Dep möglich.
- `git config` darf nicht verändert werden (Projektregel) – Zeilenenden über
  `.gitattributes` geregelt.
