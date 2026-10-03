# AGENTS.md – Projektregeln für BatteryBar OSS

Diese Datei ist die **verbindliche Regelbasis** für alle Beiträge an diesem
Projekt – egal ob von Menschen oder Coding-Agenten (z. B. Devin).
Lies zu Beginn jeder Session zuerst diese Datei und `PROJECT_MEMORY.md`.

> Projekt: Open-Source-Ersatz für das eingestellte „BatteryBar (Pro)" –
> eine frei schwebende Akku-Statusleiste für Windows 11, erweiterbar zu einem
> Conky/BGInfo-artigen Desktop-Info-Widget. Tech-Stack: **Python ≥ 3.11,
> ausschließlich Standardbibliothek** (Tkinter + ctypes/Win32).

---

## 1. Versionierung (SemVer)

- Es gilt [Semantic Versioning](https://semver.org/lang/de/): `MAJOR.MINOR.PATCH`.
- **Jede Änderung** am Projekt erhöht die Versionsnummer – mindestens `PATCH`.
  - `PATCH`: Bugfixes, Doku-Korrekturen ohne Verhaltensänderung
  - `MINOR`: neue Features, rückwärtskompatibel
  - `MAJOR`: Breaking Changes (Config-Format, API, Verhalten)
- **Single Source of Truth** für die Version: `__version__` in
  `src/batterybar/__init__.py`. Kein zweiter Ort darf eine Versionsnummer
  hartkodieren (außer CHANGELOG.md als Historie).
- Aktueller Stand: siehe `src/batterybar/__init__.py` und `CHANGELOG.md`.

## 2. Changelog-Pflicht

- Jede Änderung wird **ausführlich** in `CHANGELOG.md` dokumentiert
  (Format: [Keep a Changelog](https://keepachangelog.com/de/1.1.0/), deutsch).
- Pro Version die Kategorien: `Hinzugefügt`, `Geändert`, `Veraltet`,
  `Entfernt`, `Behoben`, `Sicherheit`.
- Der Changelog-Eintrag beschreibt das **Warum** und das **Was**, nicht nur
  Dateinamen.

## 3. Commits & Git-Historie

- **Jede Versionserhöhung = ein Commit** mit dem Muster
  `v<version>: <Kurzbeschreibung>` und dem vollständigen Changelog-Eintrag im
  Commit-Body. So bleibt auf GitHub alles nachverfolgbar.
- Keine Secrets committen (siehe §5). Keine Recherche-Rohdateien (§6).
- Kein `--force`-Push, kein Umschreiben der Historie, kein Ändern der
  Git-Config.

## 4. Abhängigkeiten – Philosophie & Pflichten

- **Grundsatz: so wenig Abhängigkeiten wie möglich.** Ziel ist, dass ein Nutzer
  nach `git clone` nur `run.bat` starten muss.
- Laufzeit: **nur Python-Standardbibliothek**. `pip install` darf für die
  Laufzeit nicht nötig sein.
- Neue externe Abhängigkeit nur mit: (a) schriftlicher Begründung im
  Changelog, (b) Lizenzprüfung (nur OSS-kompatible Lizenzen), (c) Eintrag in
  `docs/DEPENDENCIES.md`.
- `docs/DEPENDENCIES.md` enthält die **verbindliche Tabelle** aller
  Abhängigkeiten: Name, Version, Zweck, Quelle (URL), Lizenz,
  **Installationsanleitung**. Die Tabelle wird bei jeder Änderung
  mitgepflegt.
- Optionale Werkzeuge (z. B. PyInstaller zum EXE-Bau) werden als *optional*
  markiert und sind nie Laufzeitvoraussetzung.

## 5. Secrets & Konfiguration

- Secrets, Keys, Tokens etc. gehören **ausschließlich** in
  `config/secrets.json` – diese Datei ist in `.gitignore` und wird **niemals**
  committed.
- `config/secrets.example.json` ist die committed Vorlage (Platzhalter statt
  echter Werte).
- Benutzerdefinierte Einstellungen: `config/settings.local.json`
  (gitignored) überlagert `config/settings.json` (committed Defaults).
- Vor jedem Commit prüfen, dass keine Secrets im Diff sind.

## 6. Recherche-Material

- Der Ordner `Recherchen/` enthält Rohdateien (Installer, gespeicherte
  Webseiten, Fremd-Binaries). Er ist in `.gitignore` und wird **nicht**
  committed – Lizenz- und Größengründe.
- Stattdessen werden alle Quellen in **`docs/RESEARCH.md`** benannt:
  Tool, Version, Bezugsquelle (URL), Lizenz, was daraus übernommen wurde.

## 7. README & Dokumentation

- `README.md` wird **bei jeder nutzerrelevanten Änderung** mitgepflegt
  (Features, Installation, Konfiguration, Screenshots).
- Dokumentationsstruktur:
  - `README.md` – Einstieg, Installation, Nutzung, Konfiguration
  - `CHANGELOG.md` – Versionshistorie
  - `docs/REQUIREMENTS.md` – Anforderungen (Funktions-Sichtung, MoSCoW)
  - `docs/DEPENDENCIES.md` – Abhängigkeiten, Quellen, Lizenzen, Installation
  - `docs/RESEARCH.md` – Recherche-Quellen
  - `PROJECT_MEMORY.md` – Projektgedächtnis (§8)
- Sprache: Doku auf **Deutsch**, Code-Bezeichner und Kommentare auf Englisch.
  (README kann später eine englische Variante bekommen.)

## 8. Projektgedächtnis

- `PROJECT_MEMORY.md` wird von jeder bearbeitenden Instanz gepflegt:
  getroffene Architektur-Entscheidungen, Umgebungs-Fakten, offene Punkte,
  Lessons Learned. So kann nach einem frischen Clone jede(r) nahtlos
  weiterarbeiten.

## 9. Klon-/Weitergabe-Kompatibilität

- Kein lokaler Zustand im Repo: keine absoluten Pfade, keine
  Maschinen-spezifischen Einstellungen, keine generierten Dateien.
- Alles Nötige zur Weiterentwicklung ist im Repo: Doku, Quellen, Launcher.
- Plattform: Windows 10/11 primär; Python-Versionen laut `docs/DEPENDENCIES.md`.

## 10. Code-Konventionen

- Python ≥ 3.11, nur Standardbibliothek; `from __future__ import annotations`.
- Kompakter, idiomatischer Code; keine unnötigen Kommentare, keine
  Kommentar-Löschungen.
- Fehlerbehandlung an sinnvollen Grenzen (Win32-Aufrufe, Config-I/O), nicht
  jede Zeile in try/except.
- Verifikation vor jedem Commit:
  `python -m compileall -q src` und `python -m batterybar --selftest`
  (mit `PYTHONPATH=src`).
- Security: keine Befehlsausführung aus Config-Daten heraus, keine Secrets in
  Logs, Fenster/Canvas-Eingaben validieren.

## 11. Lizenz

- Projekt-Lizenz: **MIT** (siehe `LICENSE`).
- Fremde Ressourcen (Icons, Code-Snippets, Themes) nur mit OSS-kompatibler
  Lizenz und nur mit Quellen-/Lizenzvermerk in `docs/DEPENDENCIES.md` bzw.
  `docs/RESEARCH.md`.
