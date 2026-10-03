# RESEARCH.md – Recherche-Quellen

Dokumentation aller Recherche-Quellen lt. `AGENTS.md` §6.
Die **Rohdateien** liegen lokal unter `Recherchen/` und werden aus
Lizenz-/Größengründen **nicht** ins Git übernommen. Wer das Repo klont,
kann die Quellen über die unten genannten URLs erneut beziehen.

Stand: 2026-10-03

---

## Verzeichnis der Quellen

| # | Quelle / Tool | Version | Bezugsquelle (URL) | Lizenz | Lokaler Pfad (`Recherchen/`) | Relevanz fürs Projekt |
|---|---|---|---|---|---|---|
| 1 | **BatteryBar / BatteryBar Pro** (Osiris Development, Chris Thompson) | 3.6.6 (Setup, entpackt) | http://osirisdevelopment.com/BatteryBar (Projekt eingestellt; Seite teils nur noch via Web-Archiv erreichbar) | Proprietär (Free/Pro) – **kein Code übernommen**, nur Feature-/UX-Analyse | `BatteryBarPro/` | Referenz-Funktionsumfang: Zustandsmodell (Discharging/Low/Critical/Charging), Theme-Struktur (`theme.xml` mit Zuständen + Farben/Fonts), Schwellen-Warnungen, Restlaufzeit-Anzeige. Basis für `docs/REQUIREMENTS.md` FR-01…FR-08, FR-12 |
| 2 | **BGInfo** (Microsoft Sysinternals, Bryce Cogswell/Mark Russinovich) | 4.x | https://learn.microsoft.com/sysinternals/downloads/bginfo | Sysinternals Software License Terms (`BGINfo/BGInfo/Eula.txt`) | `BGINfo/` | Referenz „Systemdaten auf dem Desktop anzeigen"; Idee frei wählbarer Daten-Felder → Provider-Konzept |
| 3 | **DesktopInfo** (Glenn Delahoy) | 3.23.0 | https://www.glenn.delahoy.com/desktopinfo/ | Freeware (proprietär) | `DesktopInfo/` | Referenz: INI-Konfiguration, große Provider-Vielfalt, Portable-App-Ansatz; Manual PDF als Feature-Katalog |
| 4 | **PowerBGInfo** (EvotecIT, Przemysław Kłys) | Branch v2-speedygonzales | https://github.com/EvotecIT/PowerBGInfo · https://www.powershellgallery.com/packages/PowerBGInfo | MIT (`PowerBGInfo*/License`) | `PowerBGInfo/` | Referenz: JSON-Config-Ansatz, Builtin-Values-Konzept, Doku-Struktur (CHANGELOG.md, README-Stil). **Kein Code übernommen** |
| 5 | **Rainmeter** | 4.5.26 | https://www.rainmeter.net/ · https://github.com/rainmeter/rainmeter | GPL-2.0 | `Rainmeter/` | Referenz: Measure→Meter-Architektur, frei platzierte Desktop-Widgets; bewusst **nicht** 1:1 übernommen (zu schwergewichtig) |
| 6 | **Fachartikel: „Windows Server – Desktop-Infos anzeigen: Tools im Vergleich"** | o. D. (gespeicherte Webseite) | gespeicherte HTML-Datei (IT-Fachartikel-Vergleich BGInfo/DesktopInfo & Co.) | Copyright des jeweiligen Portals – nur Zitat der Erkenntnisse | `Windows Server Desktop-Infos anzeigen_ Tools im Vergleich.html(+_files)` | Marktüberblick alternativer Desktop-Info-Tools; bestätigt Lücke „leichtgewichtiger Akku-/Info-Bar" |
| 7 | **Conky** (Vergleichsreferenz, Linux) | – | https://github.com/brndnmtthws/conky | GPL-3.0 | *(nicht lokal vorhanden – nur konzeptionelle Referenz)* | Vorbild für Formatstring-Konzept (`{percent}`-Platzhalter in `window.format`) |

## Übernahme-Regeln

- Es wurde **kein Fremd-Code** übernommen. BatteryBar OSS ist eine
  Neuentwicklung; lediglich Funktionsumfang/UX wurden analysiert.
- `theme.xml`-Struktur von BatteryBar diente als **inspiratives Vorbild**
  für Zustands-Farben; unsere Umsetzung ist JSON-basiert und eigenständig.
- Grafiken/Themes aus `Recherchen/` (PNG-Assets der BatteryBar-Themes)
  sind **proprietär** und dürfen nicht ins Repo kopiert werden.
