# REQUIREMENTS.md – Anforderungen BatteryBar OSS

Stand: 2026-10-03 · Version des Dokuments: 1.0 · zugehörige App-Version: v0.1.0

---

## 1. Ziel & Scope

Nachbau der eingestellten Software **BatteryBar (Pro)** als Open-Source-Tool
für Windows 11: eine kompakte, frei schwebende Leiste, die den Akkustand auf
den ersten Blick zeigt. Zweite Zielrichtung: die Leiste soll – inspiriert von
**Conky** (Linux) und **BGInfo/DesktopInfo** (Windows) – um weitere
Desktop-Informationen erweiterbar sein.

**Außerhalb des Scopes** (bewusste Abgrenzung):

- Keine Taskbar-Deskbar-Integration – Deskbands gibt es unter Windows 11
  nicht mehr (Original-Ansatz von BatteryBar nicht reproduzierbar).
- Kein Wallpaper-Rendering (Ansatz von BGInfo/PowerBGInfo) – wir zeichnen ein
  eigenes Live-Fenster, keine Hintergrundbild-Manipulation.
- Kein Skin-Ökosystem à la Rainmeter (Overkill); stattdessen schlanke
  JSON-Konfiguration + später optionale JSON-Themes.

## 2. Ausgangslage / Motivation

- BatteryBar wurde als Taskbar-Toolbar (Deskband) installiert; das Projekt
  (Osiris Development) ist eingestellt, Windows 11 unterstützt keine
  Deskbands mehr.
- Bedarf: kleines, ressourcenschonendes, immer sichtbares Akku-Widget ohne
  Installations- und Dependency-Ballast → Kernprinzip **„clone & run"**.

## 3. Funktions-Sichtung der Referenz-Tools

Quellen: `Recherchen/` (lokal, nicht im Git) + `docs/RESEARCH.md`.

| Tool | Relevante Features | Was wir übernehmen |
|---|---|---|
| **BatteryBar (Pro) 3.6.6** | Akku-%, Ladezustand, Restlaufzeit-Schätzung (aus eigener Historie!), Zustands-Themes (Default/Discharging/Low/Critical/Charging), Low-/Critical-Warnungen (Windows-Sounds), Schwellen konfigurierbar, Font/Größe wählbar, Übersetzungen | Zustandsmodell + Schwellen + Farbcodierung, Formatstring-Flexibilität (statt PNG-Themes zunächst Farb-Themes), Warnungen, später: eigene Laufzeit-Schätzung aus Entladehistorie |
| **BGInfo (Sysinternals)** | Systemdaten (Host, OS, CPU, RAM, IP …) als Desktop-Text, frei wählbare Felder | Idee der konfigurierbaren Daten-Felder (Provider-Konzept) |
| **DesktopInfo 3.23** | INI-Config, sehr viele Daten-Provider (WMI, Registry, Dateien, Performance-Counter), Seiten/Navigation, Drag-Position, portable EXE | Provider-Registry; Prinzip „Textdatei-Config reicht"; Portabilität |
| **PowerBGInfo** (PS-Modul) | Wallpaper-Generierung mit konfigurierbaren Werten/Charts, JSON-Export, Builtin-Values | Bestätigt Bedarf an Builtin-Providern; JSON-Config-Ansatz |
| **Rainmeter 4.5.26** | Skin-/Widget-System, Messwerke (Measures) + Darstellung (Meters), variabel platzierte Fenster | Grobidee „Provider liefert Wert, View zeichnet ihn" – stark vereinfacht |
| **Conky** (Vergleich, Linux) | Formatstrings mit Variablen (`${battery_percent}`), Skriptbarkeit, minimaler Footprint | Format-Template `{percent}` etc. in `window.format` |

**Gemeinsamer Nenner:** Provider (Datenquelle) → Aufbereitung/Formatierung →
leichtgewichtige Desktop-Anzeige. Genau dieses Muster legt unsere Architektur
an (`battery.py` als Provider, `bar_window.py` als View).

## 4. Funktionale Anforderungen (MoSCoW)

### Muss (MVP – mit v0.1.0 umgesetzt)

| ID | Anforderung | Status |
|---|---|---|
| FR-01 | Frei schwebende, rahmenlose, always-on-top Leiste | ✅ v0.1.0 |
| FR-02 | Akkustand in % (Win32 `GetSystemPowerStatus`) | ✅ v0.1.0 |
| FR-03 | Ladezustände: Lädt / Entlädt / Voll / Niedrig / Kritisch / Kein Akku, farbcodiert | ✅ v0.1.0 |
| FR-04 | Restlaufzeit-Anzeige (Windows-Schätzwert, „—" wenn unbekannt) | ✅ v0.1.0 |
| FR-05 | Frei positionierbar per Drag & Drop, Position persistent | ✅ v0.1.0 |
| FR-06 | Konfiguration per JSON (Farben, Schwellen, Format, Intervall, Startposition) | ✅ v0.1.0 |
| FR-07 | Kontextmenü: Vordergrund, Click-Through, Positionssperre, Reload, Beenden | ✅ v0.1.0 |
| FR-08 | Warnung bei Low-/Critical-Schwelle (Toast + optional Beep) | ✅ v0.1.0 |
| FR-09 | Keine externen Abhängigkeiten (nur Python-stdlib) | ✅ v0.1.0 |
| FR-10 | Start ohne Konsole (`run.bat` / `pythonw`), Logging in Datei | ✅ v0.1.0 |

### Sollte (nächste Releases)

| ID | Anforderung |
|---|---|
| FR-11 | Provider-Architektur ausbauen: weitere Datenquellen via stdlib (`GetSystemTimes` CPU, `GlobalMemoryStatusEx` RAM, Uptime, Datum/Zeit, IP) – Vorbild DesktopInfo/Conky |
| FR-12 | Eigene Laufzeit-Schätzung aus Entladehistorie (BatteryBar-Pro-Feature: Windows-Schätzung ist oft ungenau); History persistieren |
| FR-13 | Akku-Gesundheit: Design- vs. Vollladekapazität, Laderate (`IOCTL_BATTERY_QUERY_INFORMATION` / `CallNtPowerInformation`) |
| FR-14 | Theme-System: JSON-Themes (Farbsets), Theme-Wechsel im Kontextmenü |
| FR-15 | Autostart-Option (Task/Registry Run-Key, vom Menü aus (de)aktivierbar) |
| FR-16 | Multi-Monitor-Bewusstsein (Monitorwahl, korrekte Eckverankerung) |
| FR-17 | Mehrere/Leiste zusätzliche Zeilen oder Blöcke für Provider-Werte |
| FR-18 | Konfigurierbare Hotkeys |

### Könnte (später / optional)

| ID | Anforderung |
|---|---|
| FR-19 | Optionaler Einzel-EXE-Build via PyInstaller (nur Dev-Tool, keine Laufzeit-Dep) |
| FR-20 | Runde Ecken / Icons via PNG-Assets mit Alpha (Chroma-Alternative) |
| FR-21 | Tooltip mit Detailinfos (Kapazität mWh, Health, Spannung) |
| FR-22 | Mini-Verlaufsgraph (Entladekurve) im Popup |
| FR-23 | Übersetzungen (de/en) für UI-Texte |
| FR-24 | Einstellungs-Dialog (GUI statt JSON-Edit) |

### Won't (abgelehnt)

| ID | Entscheidung | Grund |
|---|---|---|
| W-01 | Taskbar-Deskband | unter Windows 11 technisch nicht möglich |
| W-02 | Wallpaper-Rendering (BGInfo-Ansatz) | anderes Konzept; Live-Fenster gewählt |
| W-03 | Skin-Engine/Plugin-API à la Rainmeter | Komplexität vs. Nutzen; JSON reicht |

## 5. Nicht-funktionale Anforderungen

| ID | Anforderung |
|---|---|
| NFR-01 | **Zero-Dependency-Laufzeit**: nach `git clone` + installiertem Python ≥ 3.11 startet `run.bat` ohne weitere Schritte |
| NFR-02 | Geringer Footprint: Idle-CPU ~0 % (Intervall-Polling ≥ 500 ms), RAM < ~50 MB (gemessen v0.1.0: ~41 MB inkl. Python/Tkinter) |
| NFR-03 | Windows 10/11; DPI-skalierungsfest |
| NFR-04 | Secrets niemals im Repo (`config/secrets.json`, gitignored) |
| NFR-05 | Dokumentationspflicht: Changelog, README, Dependencies-Tabelle bei jeder Änderung (AGENTS.md) |
| NFR-06 | Jede Version ein Commit `vX.Y.Z` mit Changelog-Body (GitHub-Nachverfolgbarkeit) |
| NFR-07 | Repo ist self-contained: keine lokalen Pfade/Artefakte nötig, Klon → weiterarbeiten möglich |
| NFR-08 | Keine Admin-Rechte für Normalbetrieb |

## 6. Akzeptanzkriterien MVP (v0.1.0)

- [x] `run.bat` startet die Leiste ohne Konsole; sie zeigt aktuellen Akku-%
- [x] Zustandsfarben wechseln korrekt (Laden/Entladen/Niedrig/Kritisch)
- [x] Leiste ist verschiebbar; nach Neustart an alter Position
- [x] `--selftest` läuft fehlerfrei (Config + Akku gelesen)
- [x] `python -m compileall src` ohne Fehler
- [x] `git status` zeigt keine Recherche-Rohdateien/Secrets als getrackt

## 7. Datenquellen (technisch)

| Daten | Quelle | Zugriff |
|---|---|---|
| Akku-%, Ladezustand, Restsekunden | Win32 `GetSystemPowerStatus` | ctypes (kernel32) |
| (später) Akku-Details, Health | `IOCTL_BATTERY_QUERY_INFORMATION`, `CallNtPowerInformation` | ctypes (setupapi/powrprof) |
| (später) CPU/RAM | `GetSystemTimes`, `GlobalMemoryStatusEx` | ctypes (kernel32) |
| (später) IP/Netz | `GetAdaptersAddresses` o. ä. | ctypes (iphlpapi) |
| Config | JSON-Dateien `config/` | stdlib json |
| Beep | `winsound` | stdlib |

## 8. Roadmap (grobe Zielbilder)

- **v0.1.0** ✅ MVP: schwebende Akku-Leiste, Config, Warnungen, Doku-Gerüst
- **v0.2.x**: Provider-Framework + CPU/RAM/Zeit-Felder; Formatstring mit
  beliebigen Providern; FR-11, FR-17
- **v0.3.x**: Akku-Details & eigene Laufzeitschätzung (FR-12, FR-13), Tooltip
- **v0.4.x**: JSON-Themes + Theme-Menü (FR-14), Autostart (FR-15)
- **v0.5.x**: Multi-Monitor (FR-16), konfigurierbare Hotkeys (FR-18)
- **v1.0.0**: Feature-Parität mit BatteryBar Pro Kernfunktionen + Stabilität
