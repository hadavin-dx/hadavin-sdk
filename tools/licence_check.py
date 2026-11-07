"""Fail when a package in the locked set declares a copyleft licence, or cannot be checked.

Usage: python tools/licence_check.py EXPORT_FILE [EXCEPTIONS_FILE]

EXPORT_FILE is the output of `uv export --locked --no-hashes --no-emit-project ...` (lines `name==version ; marker`).
For each package whose marker is true on this platform, the installed distribution's METADATA is read (License-Expression,
License - the whole value, however long - and `License ::` classifiers). The check fails when
  - a declared licence matches the copyleft pattern (GPL, LGPL, AGPL, GNU/Affero/Lesser General Public, SSPL, EUPL), unless
    an `allow name==version` line in EXCEPTIONS_FILE covers that exact version;
  - a package is not installed and no `unchecked name==version` line says so (those lines name the packages that a platform
    marker leaves out on Linux, with the licence read from the package index by hand). A wrong environment or a partial
    sync therefore fails on every missing package. A package with no licence field also fails;
  - an exception line is stale: the package is gone, the version differs, the package is not copyleft, or an `unchecked`
    package is in fact installed.
Weak copyleft such as MPL-2.0 is not matched; docs/lint-tools.md lists it.
"""

from __future__ import annotations

import re
import sys
from importlib import metadata
from pathlib import Path

COPYLEFT = re.compile(
    r"\b(?:a|l)?gpl"  # GPL, LGPL, AGPL, GPLv3, GPL-2.0-or-later, LGPL-2.1+, AGPLv3
    r"|\bgnu\b"
    r"|affero"
    r"|lesser general public"
    r"|\bgeneral public licen[cs]e"
    r"|\bsspl\b|server side public licen[cs]e"
    r"|\beupl\b|european union public licen[cs]e",
    re.IGNORECASE,
)
LINE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s;]+)\s*(?:;\s*(.*))?$")
EXC = re.compile(r"^(allow|unchecked)\s+([A-Za-z0-9][A-Za-z0-9._-]*)==(\S+)\s*(?:#.*)?$")


def declared(dist: metadata.Distribution) -> list[str]:
    md = dist.metadata
    out = [v for v in md.get_all("License-Expression") or [] if v]
    lic = md.get("License")
    if lic:
        out.append(lic.strip())
    out += [
        c.split("::")[-1].strip()
        for c in md.get_all("Classifier") or []
        if c.startswith("License ::")
    ]
    return out


def is_copyleft(texts: list[str]) -> bool:
    return any(COPYLEFT.search(t) for t in texts)


def short(texts: list[str]) -> str:
    return "; ".join(t.splitlines()[0][:80] if t else "" for t in texts) or "UNKNOWN"


def _installed(name: str) -> metadata.Distribution | None:
    try:
        return metadata.distribution(name)
    except metadata.PackageNotFoundError:
        return None


def read_exceptions(path: str | None) -> dict[tuple[str, str], str]:
    out: dict[tuple[str, str], str] = {}
    if path:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#"):
                m = EXC.match(line.strip())
                if not m:
                    raise SystemExit(f"bad exception line: {line!r}")
                out[(m.group(1), m.group(2).lower() + "==" + m.group(3))] = line
    return out


def main(argv: list[str]) -> int:
    exceptions = read_exceptions(argv[2] if len(argv) > 2 else None)
    used: set[tuple[str, str]] = set()
    problems: list[str] = []
    seen: set[str] = set()
    checked = 0
    for raw in Path(argv[1]).read_text(encoding="utf-8").splitlines():
        m = LINE.match(raw.strip())
        if not m:
            continue
        name, version, marker = m.group(1), m.group(2), m.group(3)
        key = name.lower() + "==" + version
        seen.add(key)
        installed = _installed(name)
        if installed is None:
            if ("unchecked", key) in exceptions:
                used.add(("unchecked", key))
                print(
                    f"UNCHECKED {name} {version}: not installed here ({marker or 'no marker'}); licence entered by hand"
                )
            else:
                problems.append(
                    f"{name} {version}: not installed and not listed as `unchecked` (wrong environment?)"
                )
            continue
        dist = installed
        texts = declared(dist)
        checked += 1
        if dist.version != version:
            problems.append(f"{name}: installed {dist.version} but the lock says {version}")
        if not texts:
            problems.append(f"{name} {version}: no licence field at all")
        elif is_copyleft(texts):
            if ("allow", key) in exceptions:
                used.add(("allow", key))
                print(f"ALLOWED   {name} {version}: {short(texts)}")
            else:
                problems.append(f"{name} {version}: copyleft licence declared: {short(texts)}")
        else:
            print(f"ok        {name} {version}: {short(texts)}")
    for kind, key in sorted(set(exceptions) - used):
        why = "package not in the lock at that version" if key not in seen else "no longer needed"
        problems.append(f"stale exception `{kind} {key}`: {why}")
    for p in problems:
        print("PROBLEM   " + p)
    print(f"{checked} packages read, {len(used)} exceptions used, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
