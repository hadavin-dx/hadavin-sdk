"""The vendoring contract of the kit: which files are runtime, their hashes, and a check that a copy is intact.

    python -m hadavin_kit.kitsum --check [DIR]      verify DIR (default: this kit) against its KIT.lock
    python -m hadavin_kit.kitsum --print [DIR]      print the per-file hashes and the tree hash

A demo VENDORS the kit: it copies the runtime files (hadavin_kit/*.py except docgen and testing, schema/, console/) from
a MERGED kit commit with `portal-kit/tools/vendor.py copy`, which writes `vendor/KIT.lock` in the demo (the merged commit, a SHA-256 per
file, a tree hash and the minimum pins; the files sit in `vendor/portal-kit/`). `--check` fails on a changed, missing or
unlisted file. The kit's own repository keeps `KIT-SHA256SUMS` (sha256sum lines, no commit) and a test keeps it current.
One format: the one `tools/core_sync_check.py` verifies. tests/ and tools/ are not
vendored.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from hadavin_kit import paths

LOCK_FORMAT = "hadavin-kit-lock/1"
NOT_VENDORED = (
    "docgen.py",
    "testing.py",
    "asks.v1.json",
)  # development helpers and the ask ledger: they read examples and fixtures that are not shipped
CONSOLE_FILES = ("app.css", "app.js", "build_console.py", "chain.js", "index.template.html")
SCHEMA_FILES = ("demo-export.v1.json",)


def runtime_files(root: Path) -> list[str]:
    """Relative POSIX paths of every runtime file that exists under `root` (sorted)."""
    found = [
        f"hadavin_kit/{p.name}"
        for p in (root / "hadavin_kit").glob("*.py")
        if p.name not in NOT_VENDORED
    ]
    found += [f"schema/{n}" for n in SCHEMA_FILES if (root / "schema" / n).is_file()]
    found += [f"console/{n}" for n in CONSOLE_FILES if (root / "console" / n).is_file()]
    return sorted(found)


def _sha(path: Path) -> str:
    # core_sync_check.py hashes with line endings normalised to LF by default; so do we, and .gitattributes pins the
    # runtime files to LF as well, so a checkout on any platform has the same bytes
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def digests(root: Path) -> dict[str, str]:
    return {rel: _sha(root / rel) for rel in runtime_files(root)}


def tree_hash(files: dict[str, str]) -> str:
    """sha256 of the sorted "<sha>  <relpath>" lines: the format tools/core_sync_check.py verifies."""
    return hashlib.sha256("".join(f"{files[k]}  {k}\n" for k in sorted(files)).encode()).hexdigest()


def sums_text(files: dict[str, str]) -> str:
    """KIT-SHA256SUMS: sha256sum lines `<64 hex>  <relpath>`, sorted."""
    return "".join(f"{files[k]}  {k}\n" for k in sorted(files))


def parse_sums(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        if line.strip():
            sha, rel = line.split("  ", 1)
            out[rel] = sha
    return out


def expected_names() -> list[str]:
    return sorted([f"console/{n}" for n in CONSOLE_FILES] + [f"schema/{n}" for n in SCHEMA_FILES])


def _vendored_dir_files(root: Path) -> list[str]:
    """Every file in the three vendored directories except the development helpers (so a stray file is "unlisted")."""
    return sorted(
        p.relative_to(root).as_posix()
        for d in ("hadavin_kit", "schema", "console")
        for p in (root / d).rglob("*")
        if p.is_file()
        and "__pycache__" not in p.parts
        and p.suffix != ".pyc"
        and p.name not in NOT_VENDORED
    )


def check(root: Path, lock_path: Path | None = None) -> list[str]:
    """Problems between the files under `root` and a lock; an empty list means the copy is intact.

    `lock_path` is a `KIT.lock` (JSON: kit_commit, files, tree_sha256; every file under `root` must be listed) or a
    `KIT-SHA256SUMS` (sha256sum lines; only the runtime files are compared, the kit repository holds more)."""
    lock_path = lock_path or (root / "KIT-SHA256SUMS")
    strict = lock_path.suffix == ".lock"
    try:
        text = lock_path.read_text(encoding="utf-8")
        if strict:
            lock = json.loads(text)
            want: dict[str, str] = lock["files"]
        else:
            want, lock = parse_sums(text), {}
    except (OSError, ValueError, KeyError, TypeError) as err:
        return [f"{lock_path.name} is unreadable: {type(err).__name__}"]
    have = digests(root)
    out = [
        f"{rel}: missing"
        for rel in sorted(
            set(want) - set(have) if not strict else set(want) - set(_vendored_dir_files(root))
        )
    ]
    if strict:
        everything = {rel: _sha(root / rel) for rel in _vendored_dir_files(root)}
        out += [
            f"{rel}: not in the lock (unlisted file)" for rel in sorted(set(everything) - set(want))
        ]
        out += [
            f"{rel}: changed since it was vendored"
            for rel in sorted(set(everything) & set(want))
            if everything[rel] != want[rel]
        ]
        if tree_hash(want) != lock.get("tree_sha256"):
            out.append("the lock's own tree hash does not match its file list")
    else:
        out += [
            f"{rel}: not in KIT-SHA256SUMS (extra runtime file)"
            for rel in sorted(set(have) - set(want))
        ]
        out += [
            f"{rel}: changed since the sums were written"
            for rel in sorted(set(have) & set(want))
            if have[rel] != want[rel]
        ]
    return out


def lock_data(root: Path) -> dict[str, Any]:
    files = digests(root)
    return {"files": files, "tree_sha256": tree_hash(files)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="kitsum", description=__doc__.splitlines()[0])
    ap.add_argument(
        "directory",
        nargs="?",
        type=Path,
        default=paths.ROOT,
        help="a demo repository (vendor/KIT.lock) or a kit root",
    )
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--print", action="store_true", dest="show")
    args = ap.parse_args(argv)
    if args.show:
        data = lock_data(args.directory)
        for rel, h in data["files"].items():
            print(f"{h}  {rel}")
        print(f"tree {data['tree_sha256']}")
        return 0
    d = args.directory
    if (
        d / "vendor" / "KIT.lock"
    ).is_file():  # a demo repository: the files sit where the lock says
        lock_path = d / "vendor" / "KIT.lock"
        vend = d / (
            json.loads(lock_path.read_text(encoding="utf-8")).get("vendor_dir")
            or "vendor/portal-kit"
        )
        problems = check(vend, lock_path)
    elif (d / "KIT.lock").is_file():
        problems = check(d, d / "KIT.lock")
    else:
        problems = check(d)
    for p in problems:
        print(f"kitsum: {p}")
    print(f"kitsum {args.directory}: {'OK' if not problems else 'MISMATCH'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
