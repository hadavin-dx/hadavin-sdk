"""Scan git-tracked files for secrets and banned names; exit 1 on any hit (the repo is public).

Usage: python tools/scan_repo.py [--root DIR]
Output per hit: path:line: rule  (matched text masked after 4 characters).
False positives: add `path:reason` (one per line, `#` comments ok) to tools/scan_allowlist.txt; the whole file is skipped.
Banned names: BANNED in tests/test_no_reference_material.py (read, not copied) plus tools/scan_banned_extra.txt.
"""

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXAMPLE_KEY = "AKIAIOSFODNN7EXAMPLE"  # the one literal AWS documents as a placeholder

SECRET_RULES = {
    "aws-access-key-id": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "anthropic-api-key": re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
    "sk-api-key": re.compile(r"\bsk-[A-Za-z0-9]{32,}"),
    "private-key-header": re.compile(r"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----"),
    "slack-token": re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    "github-token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}"),
    "github-fine-grained-token": re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,}"),
    "password-literal": re.compile(r"""(?i)\bpassword["']?(?:\s*=\s*|:\s*)(['"])[^'"\s]{8,}\1"""),
}


def _lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return [ln for ln in path.read_text(encoding="utf-8").splitlines()]


def _banned() -> list[str]:
    src = (HERE.parent / "tests" / "test_no_reference_material.py").read_text(encoding="utf-8")
    names: list[str] = []
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and any(
            getattr(t, "id", "") == "BANNED" for t in node.targets
        ):
            names += list(ast.literal_eval(node.value))
    names += [
        n.strip()
        for n in _lines(HERE / "scan_banned_extra.txt")
        if n.strip() and not n.startswith("#")
    ]
    return names


def _allowed() -> set[str]:
    out = set()
    for ln in _lines(HERE / "scan_allowlist.txt"):
        if ln.strip() and not ln.startswith("#"):
            out.add(ln.split(":", 1)[0].strip())
    return out


def _mask(text: str) -> str:
    return text[:4] + "*" * min(len(text) - 4, 8)


def scan(repo: Path) -> list[str]:
    banned, allowed = _banned(), _allowed()
    cmd = ["git", "-C", str(repo), "ls-files", "-z"]
    listing = subprocess.run(cmd, capture_output=True, check=True).stdout  # noqa: S603
    hits = []
    for rel in sorted(listing.decode("utf-8").split("\0")):
        path = repo / rel
        if not rel or rel in allowed or not path.is_file():
            continue
        data = path.read_bytes()
        if b"\0" in data[:8000]:
            continue  # binary
        for n, line in enumerate(data.decode("utf-8", errors="replace").splitlines(), 1):
            for rule, rx in SECRET_RULES.items():
                for m in rx.finditer(line):
                    if m.group(0) != EXAMPLE_KEY:
                        hits.append(f"{rel}:{n}: {rule} {_mask(m.group(0))}")
            hits += [f"{rel}:{n}: banned-name {_mask(b)}" for b in banned if b in line]
    return hits


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(HERE.parent))
    hits = scan(Path(ap.parse_args().root))
    print("\n".join(hits))
    sys.exit(1 if hits else 0)
