"""Fail when a package in the locked set declares a GPL, LGPL or AGPL licence in its own metadata.

Usage: python tools/licence_check.py NAMES_FILE [EXCEPTIONS_FILE]
NAMES_FILE has one package name per line (e.g. from `uv export --locked --no-hashes`). EXCEPTIONS_FILE (see
tools/licence_exceptions.txt) lists names that may stay, each with its reason; they are printed as ALLOWED.
Reads each installed distribution's METADATA (License-Expression, License, License :: classifiers). A package with no
licence field at all is listed as UNKNOWN and also fails, so a missing field is never read as "fine". Prints one
line per package: name, version, what it declares.
"""

from __future__ import annotations

import re
import sys
from importlib import metadata
from pathlib import Path

COPYLEFT = re.compile(
    r"\b(?:A|L)?GPL\b|GNU (?:Affero |Lesser |Library )?General Public", re.IGNORECASE
)
NAME = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)")


def declared(dist: metadata.Distribution) -> list[str]:
    md = dist.metadata
    out = [v for v in md.get_all("License-Expression") or [] if v]
    lic = md.get("License")
    if lic and len(lic) < 200:  # a long value is the licence text itself, not a name
        out.append(lic.strip())
    out += [
        c.split("::")[-1].strip()
        for c in md.get_all("Classifier") or []
        if c.startswith("License ::")
    ]
    return out


def main(argv: list[str]) -> int:
    names = []
    for line in Path(argv[1]).read_text(encoding="utf-8").splitlines():
        m = NAME.match(line.strip())
        if m and not line.lstrip().startswith(("#", "-")):
            names.append(m.group(1))
    allowed = set()
    if len(argv) > 2:
        for line in Path(argv[2]).read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#"):
                allowed.add(line.split("#")[0].strip().lower())
    bad = 0
    for name in sorted(set(names), key=str.lower):
        try:
            dist = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            print(f"MISSING  {name}: not installed (marker-excluded on this platform?)")
            continue
        lic = declared(dist)
        text = "; ".join(lic) or "UNKNOWN"
        flag = (
            "COPYLEFT" if any(COPYLEFT.search(x) for x in lic) else "UNKNOWN" if not lic else "ok"
        )
        if flag != "ok" and name.lower() in allowed:
            flag = "ALLOWED"
        bad += flag not in {"ok", "ALLOWED"}
        print(f"{flag:9}{name} {dist.version}: {text}")
    print(f"{len(set(names))} packages, {bad} copyleft or unknown")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
