"""Extract the `## [X.Y.Z]` section of CHANGELOG.md for a version.

Usage: python tools/release_notes.py 0.6.0 [outfile]
Used by .github/workflows/release.yml; also handy locally.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

version = sys.argv[1]
text = Path("CHANGELOG.md").read_text(encoding="utf-8")
match = re.search(
    rf"^## \[{re.escape(version)}\][^\n]*\n.*?(?=^## \[|\Z)",
    text,
    re.S | re.M,
)
notes = match.group(0).rstrip() if match else f"## [{version}]\n\n(no changelog section found)"
notes += "\n\n---\nFull history: [CHANGELOG.md](CHANGELOG.md)\n"
if len(sys.argv) > 2:
    Path(sys.argv[2]).write_text(notes + "\n", encoding="utf-8")
else:
    print(notes)
