"""Self-update via GitHub Releases (stdlib only).

Security model:
- HTTPS only: non-https:// URLs are refused; TLS is verified against
  the system trust store via ssl.create_default_context().
- Integrity: releases publish SHA256SUMS.txt; the downloaded binary's
  SHA-256 must match the entry for the exact asset name, otherwise the
  file is discarded and nothing is replaced.
- Only the exact asset "BatteryBarOSS-<version>.exe" is accepted.
- The hash proves the downloaded file equals the file published in the
  release (integrity + corruption). Authenticity (proof the build came
  from this project) is planned via SignPath code signing.
- Apply: a running exe cannot replace itself on Windows, so a tiny
  helper .bat in %TEMP% waits for exit, moves the verified binary over
  sys.executable and relaunches. Config/state in %LOCALAPPDATA% is
  untouched, so settings survive updates.
"""
from __future__ import annotations

import hashlib
import json
import logging
import ssl
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from . import __app_name__, __version__

log = logging.getLogger(__name__)

GITHUB_REPO = "Wlanfr3ak/BatteryBarOSS"
_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
CHECKSUMS_ASSET = "SHA256SUMS.txt"
_TIMEOUT_S = 20
_MAX_BYTES = 200 * 1024 * 1024  # sanity cap (~14 MB today)

DETACHED = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP


class UpdateError(Exception):
    """Refused or failed update step (never crashes the app)."""


@dataclass
class UpdateInfo:
    version: str  # "0.7.0"
    url: str  # https browser_download_url of the exe asset
    sha256: str  # expected digest from SHA256SUMS.txt
    size: int


def available() -> bool:
    """Self-update only makes sense for the frozen exe, not source runs."""
    return bool(getattr(sys, "frozen", False))


def version_tuple(text: str) -> tuple[int, ...]:
    return tuple(int(p) for p in text.lstrip("v").split("."))


def _fetch(url: str, timeout: int = _TIMEOUT_S) -> bytes:
    if urllib.parse.urlsplit(url).scheme != "https":
        raise UpdateError(f"non-HTTPS URL refused: {url[:80]}")
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"{__app_name__}/{__version__}",
            "Accept": "application/vnd.github+json",
        },
    )
    try:
        with urllib.request.urlopen(
            req, timeout=timeout, context=ssl.create_default_context()
        ) as resp:
            return resp.read(_MAX_BYTES)
    except UpdateError:
        raise
    except Exception as exc:
        raise UpdateError(f"fetch failed: {exc}") from exc


def _asset(release: dict, name: str) -> dict | None:
    return next(
        (a for a in release.get("assets", []) if a.get("name") == name), None
    )


def _parse_checksums(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2 and len(parts[0]) == 64:
            out[parts[1].lstrip("*")] = parts[0].lower()
    return out


def check_for_update(current: str = __version__) -> UpdateInfo | None:
    """Return UpdateInfo if the latest release is newer than `current`."""
    release = json.loads(_fetch(_API_URL))
    tag = str(release.get("tag_name", ""))
    try:
        latest = version_tuple(tag)
        cur = version_tuple(current)
    except ValueError:
        log.warning("unparseable release tag %r", tag)
        return None
    if latest <= cur:
        return None
    version = tag.lstrip("v")
    exe_name = f"BatteryBarOSS-{version}.exe"
    exe = _asset(release, exe_name)
    sums = _asset(release, CHECKSUMS_ASSET)
    if exe is None:
        raise UpdateError(f"asset {exe_name} missing in release {tag}")
    if sums is None:
        raise UpdateError(f"{CHECKSUMS_ASSET} missing in release {tag}")
    checksums = _parse_checksums(
        _fetch(str(sums["browser_download_url"])).decode("ascii", "replace")
    )
    sha = checksums.get(exe_name)
    if sha is None:
        raise UpdateError(f"no checksum entry for {exe_name}")
    return UpdateInfo(
        version=version,
        url=str(exe["browser_download_url"]),
        sha256=sha,
        size=int(exe.get("size") or 0),
    )


def download_verified(info: UpdateInfo) -> Path:
    """Download to %TEMP%, verify SHA-256, return the path or raise."""
    dest = Path(tempfile.gettempdir()) / f"batterybar-update-{info.version}.exe"
    if urllib.parse.urlsplit(info.url).scheme != "https":
        raise UpdateError("non-HTTPS download URL refused")
    req = urllib.request.Request(
        info.url, headers={"User-Agent": f"{__app_name__}/{__version__}"}
    )
    digest = hashlib.sha256()
    total = 0
    try:
        with urllib.request.urlopen(
            req, timeout=120, context=ssl.create_default_context()
        ) as resp, open(dest, "wb") as out:
            while chunk := resp.read(1 << 16):
                total += len(chunk)
                if total > _MAX_BYTES:
                    raise UpdateError("download exceeds size cap")
                digest.update(chunk)
                out.write(chunk)
    except Exception:
        dest.unlink(missing_ok=True)
        raise
    if digest.hexdigest() != info.sha256:
        dest.unlink(missing_ok=True)
        raise UpdateError("SHA-256 mismatch - download discarded")
    log.info("downloaded v%s (%s bytes, sha256 verified)", info.version, total)
    return dest


def apply_update(new_exe: Path) -> None:
    """Replace sys.executable with `new_exe` after this process exits.

    Spawns a detached helper .bat that waits for the exit, moves the
    verified file over the running exe's path and relaunches it.
    """
    target = Path(sys.executable).resolve()
    bat = Path(tempfile.gettempdir()) / "batterybar-update.bat"
    bat.write_text(
        "@echo off\r\n"
        "setlocal EnableDelayedExpansion\r\n"
        'set "NEW=%~1"\r\n'
        'set "OLD=%~2"\r\n'
        "set /a TRIES=0\r\n"
        ":retry\r\n"
        'move /Y "%NEW%" "%OLD%" >nul 2>&1\r\n'
        "if errorlevel 1 (\r\n"
        "    set /a TRIES+=1\r\n"
        "    if !TRIES! GEQ 120 exit /b 1\r\n"
        "    ping -n 2 127.0.0.1 >nul\r\n"
        "    goto retry\r\n"
        ")\r\n"
        'start "" "%OLD%"\r\n'
        'del /Q "%~f0"\r\n',
        encoding="ascii",
    )
    subprocess.Popen(
        ["cmd", "/c", str(bat), str(new_exe), str(target)],
        creationflags=DETACHED,
        close_fds=True,
    )
    log.info("updater helper spawned: %s -> %s", new_exe, target)
