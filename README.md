# BatteryBar OSS

Frei schwebende Akku-Statusleiste für Windows 11 – der Open-Source-Ersatz für
das eingestellte **BatteryBar (Pro)**. Langfristig erweiterbar zu einem
Conky-/BGInfo-artigen Desktop-Info-Widget.

- **Keine externen Abhängigkeiten** – läuft komplett mit der
  Python-Standardbibliothek (Tkinter + Win32-API via ctypes)
- Nach `git clone` sofort startklar: `run.bat` doppelklicken, fertig
- Aktuelle Version: siehe `CHANGELOG.md` | Lizenz: MIT

---

## Features (v0.1.0)

- Schwebende, rahmenlose, transparente Statusleiste (always-on-top)
- Akkustand in %, Ladezustand (Lädt/Entlädt/Voll/Niedrig/Kritisch),
  verbleibende Laufzeit-Schätzung
- Farbcodierte Füllung je Zustand (konfigurierbar)
- Frei verschiebbar per Drag & Drop – Position wird gespeichert
- Kontextmenü (Rechtsklick): Vordergrund, Durchklick-Modus,
  Positionssperre, Config-Reload, Beenden
- Warn-Popup bei Unterschreiten der Niedrig-/Kritisch-Schwellen
- Vollständig über JSON konfigurierbar (Farben, Schwellen, Format, Intervalle)
- Logging nach `logs/batterybar.log`

**Globale Hotkeys** (immer aktiv, auch im Durchklick-Modus):

| Hotkey | Aktion |
|---|---|
| `Strg + Alt + B` | Durchklick-Modus (Click-Through) umschalten |
| `Strg + Alt + Q` | Beenden |

## Voraussetzungen

- Windows 10/11
- Python ≥ 3.11 (Tkinter ist in der Standardinstallation enthalten)

Details und Installationsanleitungen: [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md)

## Installation & Start

```bat
git clone <repo-url>
cd "2026-10-03 - BatteryBarOSS"
run.bat
```

`run.bat` startet die Leiste ohne Konsole (`pythonw`). Zum Debuggen mit
sichtbarer Konsole:

```bat
set PYTHONPATH=%CD%\src
python -m batterybar
```

Selbsttest ohne GUI (liest Config + Akkustand, Exit-Code 0 = ok):

```bat
set PYTHONPATH=%CD%\src
python -m batterybar --selftest
```

## Konfiguration

| Datei | Zweck | Im Git? |
|---|---|---|
| `config/settings.json` | Standard-Einstellungen | ja |
| `config/settings.local.json` | persönliche Overrides (überschreiben Defaults) | nein |
| `config/secrets.json` | Secrets/Keys (Vorlage: `secrets.example.json`) | nein, niemals |

Wichtigste Optionen (Auszug, vollständige Referenz in `settings.json`):

| Schlüssel | Default | Beschreibung |
|---|---|---|
| `window.width` / `window.height` | `220` / `28` | Größe der Leiste (px) |
| `window.format` | `{state_icon} {percent}%` | Anzeige-Template. Platzhalter: `{percent}`, `{time}`, `{state}`, `{state_text}`, `{state_icon}` |
| `window.corner` / `offset_x` / `offset_y` | `top-right` / `20` / `20` | Startposition (wenn keine gespeicherte Position) |
| `thresholds.low` / `thresholds.critical` | `30` / `15` | Schwellen für Warnfarben + Warnungen (%) |
| `colors.*` | diverse | Farben je Zustand (`charging`, `discharging`, `low`, `critical`, …) |
| `warnings.enabled` / `beep` | `true` / `false` | Warn-Popup/Ton bei Schwellen-Unterschreitung |
| `update_interval_ms` | `1000` | Aktualisierungsintervall |

Format-Beispiel: `"{state_icon} {percent}% · {time}"` → `⚡ 87% · 1:42 h`

## Bedienung

- **Linksklick + Ziehen**: Leiste verschieben (Position wird beim Loslassen
  nach `settings.local.json` gespeichert)
- **Rechtsklick**: Kontextmenü
- **Warn-Toast**: erscheint unten rechts, sobald Low-/Critical-Schwelle
  unterschritten wird (einmalig pro Ereignis)

## Projektstruktur

```
├── AGENTS.md            # verbindliche Projektregeln (Versionierung, Changelog, Lizenzen)
├── CHANGELOG.md         # Versionshistorie (Keep a Changelog)
├── PROJECT_MEMORY.md    # Projektgedächtnis (Entscheidungen, Stand, Roadmap)
├── LICENSE              # MIT
├── README.md
├── run.bat              # Starter (pythonw, kein Konsolenfenster)
├── config/
│   ├── settings.json           # Defaults
│   └── secrets.example.json    # Vorlage für secrets.json
├── src/batterybar/      # Anwendungscode (siehe PROJECT_MEMORY.md §Architektur)
├── docs/
│   ├── REQUIREMENTS.md  # Anforderungen (Funktions-Sichtung, MoSCoW, Roadmap)
│   ├── DEPENDENCIES.md  # Abhängigkeiten: Quellen, Lizenzen, Installation
│   └── RESEARCH.md      # Recherche-Quellen (Rohdateien nicht im Repo)
└── Recherchen/          # lokale Recherche-Rohdateien (nicht im Git)
```

## Mitmachen / Entwicklung

Vor Änderungen bitte `AGENTS.md` lesen – dort sind Changelog-Pflicht,
SemVer-Versionierung, Commit-Konvention (`vX.Y.Z:`) und Lizenz-/Quellen-Regeln
festgelegt.

## Lizenz & Quellen

- Eigenes Projekt: [MIT](LICENSE)
- Referenz-Implementierungen/Recherche: [docs/RESEARCH.md](docs/RESEARCH.md)
- Abhängigkeiten & deren Lizenzen: [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md)
- Inspiriert von **BatteryBar** (Osiris Development, eingestellt) – komplette
  Neuentwicklung, kein fremder Code übernommen.
