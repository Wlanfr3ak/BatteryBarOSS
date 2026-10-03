# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden hier dokumentiert.
Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
Versionierung nach [Semantic Versioning](https://semver.org/lang/de/).
Regeln: siehe `AGENTS.md` §1–§3.

## [0.1.0] - 2026-10-03

Erster MVP. Grundstein des Projekts: Projektregeln, Dokumentationsgerüst und
eine lauffähige schwebende Akku-Leiste ausschließlich mit
Python-Standardbibliothek.

### Hinzugefügt

- **Floating Battery Bar** (`src/batterybar/`):
  - Rahmenloses, transparentes, always-on-top Fenster (Tkinter,
    `overrideredirect` + `-transparentcolor`)
  - Akkustand via Win32 `GetSystemPowerStatus` (ctypes, keine externen
    Module): Prozent, Ladezustand, Restlaufzeit
  - Zustands-Farbcodierung: Entladen, Laden, Voll, Niedrig, Kritisch,
    Kein Akku – Farben frei konfigurierbar
  - Anzeige-Template mit Platzhaltern `{percent}`, `{time}`, `{state}`,
    `{state_text}`, `{state_icon}` (Conky-artige Formatstrings)
  - Drag & Drop mit Positionspersistenz nach `settings.local.json`
  - Kontextmenü (Rechtsklick): Always-on-Top, Click-Through,
    Positionssperre, Config-Reload, Beenden
  - Click-Through-Modus (WS_EX_TRANSPARENT via ctypes) + globale Hotkeys
    `Strg+Alt+B` (Toggle) und `Strg+Alt+Q` (Beenden) via
    `GetAsyncKeyState`-Polling
  - Warn-Toast (unten rechts, `winsound`-Beep optional) beim
    Unterschreiten der Low-/Critical-Schwellen, einmalig pro Ereignis
  - DPI-Awareness (shcore `SetProcessDpiAwareness(2)`, Fallback user32)
  - Logging via `RotatingFileHandler` nach `logs/batterybar.log`
  - CLI: `--selftest` (Config + Akku lesen, kein GUI)
- **Konfiguration** (`config/`):
  - `settings.json` (committed Defaults), `settings.local.json`
    (gitignored Overrides), `secrets.example.json`/`secrets.json`
    (Secrets-Infrastruktur, gitignored)
- **Projekt-Regelwerk**:
  - `AGENTS.md` – SemVer-Versionierung, Changelog-Pflicht, Commit-Konvention
    `vX.Y.Z`, Dependencies-Tabelle, Secrets-/Recherche-Regeln
  - `PROJECT_MEMORY.md` – Projektgedächtnis (Entscheidungen, Umgebung,
    Architektur, Roadmap)
- **Dokumentation**:
  - `README.md` (Installations-, Konfigurations-, Bedienungsanleitung)
  - `docs/REQUIREMENTS.md` – Funktions-Sichtung aus den Referenz-Tools,
    MoSCoW-priorisierte Anforderungen, Roadmap
  - `docs/DEPENDENCIES.md` – Abhängigkeiten-Tabelle mit Quellen, Lizenzen,
    Installationsanleitungen
  - `docs/RESEARCH.md` – Recherche-Quellen (Rohdateien bewusst nicht im Git)
- **Repo-Grundlagen**: `LICENSE` (MIT), `.gitignore` (Secrets, Recherchen,
  Build-Artefakte, Logs ausgeschlossen), `.gitattributes` (Zeilenenden),
  `run.bat` (Starter ohne Konsole)

### Technik-Entscheidungen

- Tech-Stack **Python + Tkinter, nur Standardbibliothek** – vom User bestätigt;
  Ziel: null Installationsaufwand nach `git clone` (Details:
  `PROJECT_MEMORY.md`)
- Keine Deskband/Taskbar-Integration möglich unter Windows 11 → frei
  schwebendes Fenster als Ersatzkonzept
