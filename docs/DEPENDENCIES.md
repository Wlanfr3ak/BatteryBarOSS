# DEPENDENCIES.md – Abhängigkeiten, Quellen & Lizenzen

Verbindliche Tabelle lt. `AGENTS.md` §4. Wird bei jeder Änderung mitgepflegt.
**Laufzeit-Prinzip: nur Python-Standardbibliothek – kein `pip install` nötig.**

Stand: 2026-10-03 (v0.1.0)

---

## 1. Laufzeit-Abhängigkeiten

| # | Abhängigkeit | Version | Zweck | Quelle | Lizenz | Installation |
|---|---|---|---|---|---|---|
| 1 | **Python** | ≥ 3.11 (entwickelt mit 3.14.8) | Interpreter/Laufzeit | https://www.python.org/downloads/ | [PSF-2.0](https://docs.python.org/3/license.html) (OSI-approved, GPL-kompatibel) | `winget install Python.Python.3.14` oder Installer von python.org. Option „Add python.exe to PATH" aktivieren; Tkinter ist im Standard-Installer enthalten |
| 2 | **Tkinter / tk** | im Python-Installer enthalten | GUI-Fenster (schwebende Leiste, Canvas, Menü) | gebündelt mit Python (Tk 8.6.x) | Tcl/Tk License (BSD-ähnlich, frei) | enthalten – kein separater Schritt; nur bei „custom install" die Option *tcl/tk and IDLE* aktiviert lassen |
| 3 | **Win32-API** | OS-Komponente | Akku-Status (`kernel32!GetSystemPowerStatus`), Fenster-Styles (`user32`), Sound (`winmm` via `winsound`) | Bestandteil von Windows | Microsoft Windows – keine separate Lizenz nötig | nicht installierbar – OS-Bestandteil, Zugriff via `ctypes`/`winsound` (stdlib) |

**Python-Module, die genutzt werden (alle Standardbibliothek):**
`tkinter`, `ctypes`, `json`, `argparse`, `logging`, `logging.handlers`,
`pathlib`, `dataclasses`, `winsound`, `sys`, `os`

## 2. Entwicklungs-Werkzeuge

| # | Werkzeug | Version | Zweck | Quelle | Lizenz | Installation |
|---|---|---|---|---|---|---|
| 1 | **Git** | 2.x (entwickelt mit 2.52) | Versionskontrolle | https://git-scm.com/download/win | [GPL-2.0](https://git-scm.com/about/free-and-open-source) | `winget install Git.Git` oder Installer |

## 3. Optionale Werkzeuge (nie Laufzeitvoraussetzung)

| # | Werkzeug | Version | Zweck | Quelle | Lizenz | Installation |
|---|---|---|---|---|---|---|
| 1 | **PyInstaller** | ≥ 6.x (optional, noch nicht im Einsatz) | Bauen einer Einzel-EXE für Nutzer ohne Python | https://pyinstaller.org/ | GPL-2.0 **mit** [Bootloader-Ausnahme](https://pyinstaller.org/en/stable/license.html) (kompilierte Ausgaben lizenzfrei verwendbar) | `pip install pyinstaller` – nur für Maintainer-Releases; Endnutzer brauchen dann überhaupt kein Python |

## 4. Ressourcen aus Drittquellen

Aktuell **keine** fremden Ressourcen (Icons, Bilder, Code, Fonts) im Projekt.
Falls zukünftig hinzugefügt: Eintrag hier Pflicht (AGENTS.md §11).

| Ressource | Quelle | Lizenz | Verwendung |
|---|---|---|---|
| – | – | – | – |

## 5. Recherche-Referenzen (kein Bestandteil der Software)

Siehe `docs/RESEARCH.md` – dort sind alle analysierten Fremd-Tools mit
Quelle und Lizenz dokumentiert. Deren Rohdateien liegen lokal unter
`Recherchen/` und werden **nicht** ins Git übernommen.

## 6. Kompatibilitäts-Notizen

- Windows 10/11 (entwickelt auf Windows 11 24H2)
- Python 3.11+ nötig für verwendete Typannotationen/`tomllib`-reife Struktur;
  getestet mit 3.14
- Keine Admin-Rechte erforderlich
