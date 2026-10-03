# AGENTS.md – Project rules for BatteryBar OSS

This file is the **binding rulebook** for all contributions to this project —
whether by humans or coding agents (e.g. Devin).
At the start of every session, read this file and `PROJECT_MEMORY.md` first.

> Project: open-source replacement for the discontinued "BatteryBar (Pro)" —
> a floating battery status bar for Windows 11, extensible towards a
> Conky/BGInfo-style desktop info widget. Tech stack: **Python >= 3.11,
> standard library only** (Tkinter + ctypes/Win32).

---

## 1. Versioning (SemVer)

- [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`.
- **Every change** to the project bumps the version — at least `PATCH`.
  - `PATCH`: bugfixes, doc fixes without behaviour changes
  - `MINOR`: new features, backwards compatible
  - `MAJOR`: breaking changes (config format, API, behaviour)
- **Single source of truth** for the version: `__version__` in
  `src/batterybar/__init__.py`. No other location may hardcode a version
  number (except CHANGELOG.md as history).
- Current version: see `src/batterybar/__init__.py` and `CHANGELOG.md`.

## 2. Changelog requirement

- Every change is documented **in detail** in `CHANGELOG.md`
  (format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), English).
- Per version use the categories: `Added`, `Changed`, `Deprecated`,
  `Removed`, `Fixed`, `Security`.
- Changelog entries describe the **why** and the **what**, not just file names.

## 3. Commits & git history

- **Every version bump = one commit** following the pattern
  `v<version>: <short description>` with the full changelog entry in the
  commit body. This keeps everything traceable on GitHub.
- Commit messages are written in **English**.
- Never commit secrets (see section 5). Never commit research raw files (section 6).
- No `--force` push, no history rewriting, no changes to git config.

## 4. Dependencies – philosophy & duties

- **Principle: as few dependencies as possible.** Goal: a user only has to
  run `run.bat` after `git clone`.
- Runtime: **Python standard library only**. `pip install` must never be
  required at runtime.
- A new external dependency requires: (a) a written justification in the
  changelog, (b) a license check (OSS-compatible licenses only), (c) an
  entry in `docs/DEPENDENCIES.md`.
- `docs/DEPENDENCIES.md` contains the **authoritative table** of all
  dependencies: name, version, purpose, source (URL), license,
  **installation instructions**. Keep the table updated with every change.
- Optional tools (e.g. PyInstaller for EXE builds) are marked *optional*
  and are never a runtime requirement.

## 5. Secrets & configuration

- Secrets, keys, tokens etc. belong **exclusively** in
  `config/secrets.json` — that file is in `.gitignore` and is **never**
  committed.
- `config/secrets.example.json` is the committed template (placeholders
  instead of real values).
- User-specific settings: `config/settings.local.json`
  (gitignored) overrides `config/settings.json` (committed defaults).
- Before every commit, verify no secrets are in the diff.

## 6. Research material

- The `Recherchen/` folder contains raw files (installers, saved web pages,
  third-party binaries). It is in `.gitignore` and is **not** committed —
  for licensing and size reasons.
- Instead, all sources are listed in **`docs/RESEARCH.md`**: tool, version,
  source URL, license, and what was derived from it.

## 7. README & documentation

- `README.md` is maintained **with every user-facing change**
  (features, installation, configuration, screenshots).
- Documentation structure:
  - `README.md` – getting started, installation, usage, configuration
  - `CHANGELOG.md` – version history
  - `docs/REQUIREMENTS.md` – requirements (feature survey, MoSCoW)
  - `docs/DEPENDENCIES.md` – dependencies, sources, licenses, installation
  - `docs/RESEARCH.md` – research sources
  - `PROJECT_MEMORY.md` – project memory (section 8)
- Language: **English** for all documentation, code identifiers, comments,
  UI strings, changelog entries and commit messages.
  (Switched to English with v0.2.0 — the maintainer may still communicate
  in German outside the repository.)

## 8. Project memory

- `PROJECT_MEMORY.md` is maintained by every working instance:
  architecture decisions, environment facts, open items, lessons learned.
  This allows seamless continuation after a fresh clone.

## 9. Clone / distribution compatibility

- No local state in the repo: no absolute paths, no machine-specific
  settings, no generated files.
- Everything needed to continue development is in the repo: docs, sources,
  launchers.
- Platform: Windows 10/11 primarily; Python versions per
  `docs/DEPENDENCIES.md`.

## 10. Code conventions

- Python >= 3.11, standard library only; `from __future__ import annotations`.
- Compact, idiomatic code; no unnecessary comments; never delete existing
  comments.
- Error handling at sensible boundaries (Win32 calls, config I/O), not
  try/except on every line.
- Verification before every commit:
  `python -m compileall -q src` and `python -m batterybar --selftest`
  (with `PYTHONPATH=src`).
- Security: no command execution from config data, no secrets in logs,
  validate window/canvas input.

## 11. License

- Project license: **MIT** (see `LICENSE`).
- Third-party resources (icons, code snippets, themes) only with an
  OSS-compatible license and only with a source/license note in
  `docs/DEPENDENCIES.md` or `docs/RESEARCH.md`.
