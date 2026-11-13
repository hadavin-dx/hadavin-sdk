"""Scan git-tracked files for secrets and banned names; exit 1 on any hit (the repo is public).

Usage: python tools/scan_repo.py [--root DIR] [--allowlist FILE] [--extra FILE] [--banned-src FILE]
Output per hit: path:line: rule (the matched text is never printed, so CI logs hold no secret).
False positives: add `path:rule:reason` (one per line, `#` comments ok) to tools/scan_allowlist.txt. The entry skips ONLY that
rule on that file (rule `*` skips all rules; avoid it). An entry whose file is no longer tracked, or without a reason, is itself a hit.
Banned names: the BANNED tuple in tests/test_no_reference_material.py (read, not copied) plus tools/scan_banned_extra.txt.
If BANNED cannot be found or is empty the scan fails (it never silently turns the check off).
"""

import argparse
import ast
import re
import sys
from pathlib import Path


def _load_fixed_run():
    """The program starter next to this file, read by its file path: never an installed or foreign `tools`
    package, and it works when the file is run alone with `-I` (the script folder is not on the path then).
    The same body is in the folder guard next to this file: each must load the starter before it
    can import anything, so the two copies stay and `test_the_two_loaders_of_the_program_starter_are_the_same`
    compares them."""
    from importlib import util

    spec = util.spec_from_file_location(
        "fixed_run", Path(__file__).resolve().with_name("fixed_run.py")
    )
    if spec is None or spec.loader is None:
        raise SystemExit("the program starter next to this file (fixed_run.py) cannot be read")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run_fixed


run_fixed = _load_fixed_run()

HERE = Path(__file__).resolve().parent
EXAMPLE_KEY = "AKIAIOSFODNN7EXAMPLE"  # the one literal AWS documents as a placeholder
LIST_FILES = {
    "tools/scan_banned_extra.txt",
    "tools/scan_allowlist.txt",
}  # they hold names by design: skip banned-name only

PATTERNS = {
    "cloud-id-prefix": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "llm-id-ant": re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
    "llm-id-sk": re.compile(r"\bsk-[A-Za-z0-9_-]{32,}"),
    "pem-block-header": re.compile(r"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY(?: BLOCK)?-----"),
    "chat-id-xox": re.compile(r"\bxox[abeoprs]-[A-Za-z0-9-]{10,}"),
    "vcs-id-classic": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}"),
    "vcs-id-fine": re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,}"),
    "credential-literal": re.compile(r"""(?i)password["']?(?:\s*=\s*|:\s*)(['"])[^'"\s]{8,}\1"""),
}


def _lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines() if path.is_file() else []


def _banned(banned_src: Path, extra: Path) -> list[str]:
    names: list[str] = []
    for node in ast.parse(banned_src.read_text(encoding="utf-8")).body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(getattr(t, "id", "") == "BANNED" for t in targets) and node.value is not None:
                names += list(ast.literal_eval(node.value))
    if not names:
        raise SystemExit(
            f"scan_repo: no BANNED names found in {banned_src}; refusing to run with the check off"
        )
    names += [n.strip() for n in _lines(extra) if n.strip() and not n.startswith("#")]
    return names


def _allowed(allowlist: Path) -> tuple[dict[str, set[str]], list[str]]:
    """Return ({path: {rules}}, problems in the allowlist file itself)."""
    out: dict[str, set[str]] = {}
    problems = []
    for n, ln in enumerate(_lines(allowlist), 1):
        if not ln.strip() or ln.startswith("#"):
            continue
        parts = [p.strip() for p in ln.split(":", 2)]
        if len(parts) < 3 or not parts[0] or not parts[1] or not parts[2]:
            problems.append(f"{allowlist.name}:{n}: allowlist-entry needs path:rule:reason")
            continue
        out.setdefault(parts[0], set()).add(parts[1])
    return out, problems


def tracked_paths(repo: Path) -> set[str]:
    """The files git tracks (`git ls-files -z`: exact names, no quoting of unusual ones; ignore files do not matter)."""
    cmd = ["git", "-C", str(repo), "ls-files", "-z"]
    listing = run_fixed(cmd, capture_output=True, check=True).stdout
    return {rel for rel in listing.decode("utf-8").split("\0") if rel}


def scan(repo: Path, allowlist: Path, extra: Path, banned_src: Path) -> list[str]:
    banned = _banned(banned_src, extra)
    allowed, hits = _allowed(allowlist)
    tracked = tracked_paths(repo)
    hits += [
        f"{allowlist.name}: stale entry, {rel} is not tracked"
        for rel in sorted(set(allowed) - tracked)
    ]
    for rel in sorted(tracked):
        path = repo / rel
        if not path.is_file():
            continue
        skip = allowed.get(rel, set())
        if "*" in skip:
            continue
        data = path.read_bytes()
        if b"\0" in data[:8000]:
            continue  # binary
        for n, line in enumerate(data.decode("utf-8", errors="replace").splitlines(), 1):
            for rule, rx in PATTERNS.items():
                if rule in skip:
                    continue
                for m in rx.finditer(line):
                    if m.group(0) != EXAMPLE_KEY:
                        hits.append(f"{rel}:{n}: {rule}")
            if "banned-name" not in skip and rel not in LIST_FILES:
                hits += [f"{rel}:{n}: banned-name" for b in banned if b in line]
    return hits


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(HERE.parent))
    ap.add_argument("--allowlist", default=str(HERE / "scan_allowlist.txt"))
    ap.add_argument("--extra", default=str(HERE / "scan_banned_extra.txt"))
    ap.add_argument(
        "--banned-src", default=str(HERE.parent / "tests" / "test_no_reference_material.py")
    )
    a = ap.parse_args()
    found = scan(Path(a.root), Path(a.allowlist), Path(a.extra), Path(a.banned_src))
    print("\n".join(found))
    sys.exit(1 if found else 0)
