# RESEARCH.md – research sources

Documentation of all research sources per `AGENTS.md` section 6.
The **raw files** live locally under `Recherchen/` and are **not**
committed to git for licensing/size reasons. Anyone cloning the repo
can re-obtain the sources via the URLs listed below.

Status: 2026-10-03

---

## Source directory

| # | Source / tool | Version | Source (URL) | License | Local path (`Recherchen/`) | Relevance to the project |
|---|---|---|---|---|---|---|
| 1 | **BatteryBar / BatteryBar Pro** (Osiris Development, Chris Thompson) | 3.6.6 (setup, extracted) | http://osirisdevelopment.com/BatteryBar (project discontinued; site partly only reachable via web archive) | Proprietary (Free/Pro) – **no code reused**, feature/UX analysis only | `BatteryBarPro/` | Reference feature set: state model (Discharging/Low/Critical/Charging), theme structure (`theme.xml` with states + colors/fonts), threshold warnings, remaining-time display. Basis for `docs/REQUIREMENTS.md` FR-01…FR-08, FR-12 |
| 2 | **BGInfo** (Microsoft Sysinternals, Bryce Cogswell/Mark Russinovich) | 4.x | https://learn.microsoft.com/sysinternals/downloads/bginfo | Sysinternals Software License Terms (`BGINfo/BGInfo/Eula.txt`) | `BGINfo/` | Reference "show system data on the desktop"; idea of freely selectable data fields -> provider concept |
| 3 | **DesktopInfo** (Glenn Delahoy) | 3.23.0 | https://www.glenn.delahoy.com/desktopinfo/ | Freeware (proprietary) | `DesktopInfo/` | Reference: INI configuration, large provider variety, portable-app approach; manual PDF as feature catalogue |
| 4 | **PowerBGInfo** (EvotecIT, Przemysław Kłys) | branch v2-speedygonzales | https://github.com/EvotecIT/PowerBGInfo · https://www.powershellgallery.com/packages/PowerBGInfo | MIT (`PowerBGInfo*/License`) | `PowerBGInfo/` | Reference: JSON config approach, builtin-values concept, doc structure (CHANGELOG.md, README style). **No code reused** |
| 5 | **Rainmeter** | 4.5.26 | https://www.rainmeter.net/ · https://github.com/rainmeter/rainmeter | GPL-2.0 | `Rainmeter/` | Reference: measure->meter architecture, freely placed desktop widgets; deliberately **not** adopted 1:1 (too heavyweight) |
| 6 | **Article: "Windows Server – show desktop info: tools compared"** | n.d. (saved web page) | saved HTML file (IT magazine comparison of BGInfo/DesktopInfo & co.) | Copyright of the respective portal – findings quoted only | `Windows Server Desktop-Infos anzeigen_ Tools im Vergleich.html(+_files)` | Market overview of alternative desktop-info tools; confirms the gap "lightweight battery/info bar" |
| 7 | **Conky** (comparison reference, Linux) | – | https://github.com/brndnmtthws/conky | GPL-3.0 | *(not stored locally – conceptual reference only)* | Model for the format-string concept (`{percent}` placeholders in `window.format`) |

## Adoption rules

- **No third-party code was reused.** BatteryBar OSS is a fresh
  implementation; only the feature set/UX was analysed.
- BatteryBar's `theme.xml` structure served as an **inspirational model**
  for state colors; our implementation is JSON-based and independent.
- Graphics/themes from `Recherchen/` (PNG assets of the BatteryBar
  themes) are **proprietary** and must not be copied into the repo.
