"""Compare the pinned core copies with the files at their pinned core commits in a local core checkout.

    python tools/check_core_copies.py <path to a hadavin-sdk checkout>

Each file is read at its own `pr_snapshot` (an open core pull request commit) or, when it has none, at the table's `core_commit`. Exit 0 only if every
commit exists there and every file hashes to its pin once the listed import rewrite is applied back (CRLF normalised)."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def commit_of(pins: dict, p: dict) -> str:
    return p.get("pr_snapshot") or pins["core_commit"]


def main(core: str) -> int:
    pins = json.loads((ROOT / "core_copies.json").read_text(encoding="utf-8"))
    bad = 0
    for path, p in pins["files"].items():
        r = subprocess.run(["git", "-C", core, "show", f"{commit_of(pins, p)}:{p['core_path']}"], capture_output=True)  # noqa: S603, S607
        if r.returncode:
            print(f"MISSING {path}")
            bad += 1
            continue
        got = hashlib.sha256(r.stdout.decode("utf-8").replace("\r\n", "\n").encode()).hexdigest()
        ok = got == p["core_sha256"]
        bad += not ok
        print(("ok      " if ok else "DIFFERS ") + path)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]) if len(sys.argv) == 2 else print(__doc__) or 2)
