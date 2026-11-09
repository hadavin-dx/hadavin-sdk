"""Scan git-tracked files for secrets and banned names; exit 1 on any hit (the repo is public).

Usage: python tools/scan_repo.py [--root DIR] [--allowlist FILE] [--extra FILE] [--banned-src FILE]
Output per hit: path:line: rule (the matched text is never printed, so CI logs hold no secret).
False positives: add `path:rule:reason` (one per line, `#` comments ok) to tools/scan_allowlist.txt. The entry skips ONLY that
rule on that file (rule `*` skips all rules; avoid it). An entry whose file is no longer tracked, or without a reason, is itself a hit.
Suppressions: a comment that switches a scanner off (nosec, nosemgrep, the gitleaks allow marker, trivy ignore, a noqa that is blanket or names a
ruff `S` security code) and every scanner-config file (.gitleaksignore, .gitleaks.toml, .semgrepignore, .trivyignore, ...) is a hit unless
tools/scan_suppressions.txt lists it: `path:rule:value:reason`, value = the exact number of markers in that file, or the sha256 of the
config file. A stale, wrong-count, wrong-hash, reasonless or unknown-rule line is itself a hit. The list is the one place a reviewer reads.
Banned names: the BANNED tuple in tests/test_no_reference_material.py (read, not copied) plus tools/scan_banned_extra.txt.
If BANNED cannot be found or is empty the scan fails (it never silently turns the check off).
"""

import argparse
import ast
import hashlib
import re
import subprocess
import sys
from pathlib import Path

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

# Suppression comments. The comment prefix is required, so prose that only names a marker is not a hit.
_C = r"(?:#|//|--|/\*)\s*"
SUPPRESSIONS = {
    "suppress-nosec": re.compile(_C + r"nosec\b"),
    "suppress-nosemgrep": re.compile(_C + r"nosemgrep\b"),
    "suppress-gitleaks-allow": re.compile(r"gitleaks:" r"allow\b"),
    "suppress-trivy-ignore": re.compile(_C + r"trivy:ignore\b"),
    # blanket noqa, or a noqa naming a ruff security (S) code; style codes (BLE001, F401, ...) are not scanner suppressions
    "suppress-noqa-security": re.compile(_C + r"noqa\b(?!\s*:)|" + _C + r"noqa\s*:[^#]*\bS\d{3}\b"),
}
SCANNER_CONFIG_NAMES = {
    ".gitleaksignore",
    ".gitleaks.toml",
    "gitleaks.toml",
    ".semgrepignore",
    ".trivyignore",
    ".trivyignore.yaml",
    "trivy.yaml",
    ".bandit",
    ".zizmor.yml",
    ".zizmor.yaml",
    "zizmor.yml",
}
SCANNER_CONFIG_RULE = "scanner-config-file"
LIST_RULES = set(SUPPRESSIONS) | {SCANNER_CONFIG_RULE}


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


def _suppressions(path: Path | None) -> tuple[dict[tuple[str, str], str], list[str]]:
    """Return ({(path, rule): value}, problems in the list file itself). Line: path:rule:value:reason."""
    out: dict[tuple[str, str], str] = {}
    problems = []
    for n, ln in enumerate(_lines(path) if path else [], 1):
        if not ln.strip() or ln.startswith("#"):
            continue
        parts = [p.strip() for p in ln.split(":", 3)]
        where = f"{path.name}:{n}"
        if len(parts) < 4 or not all(parts):
            problems.append(f"{where}: suppression-list malformed, needs path:rule:value:reason")
        elif parts[1] not in LIST_RULES:
            problems.append(f"{where}: suppression-list unknown rule")
        elif (parts[0], parts[1]) in out:
            problems.append(f"{where}: suppression-list duplicate entry")
        elif parts[1] == SCANNER_CONFIG_RULE and not re.fullmatch(r"[0-9a-f]{64}", parts[2]):
            problems.append(f"{where}: suppression-list value must be a sha256")
        elif parts[1] != SCANNER_CONFIG_RULE and not re.fullmatch(r"[1-9][0-9]*", parts[2]):
            problems.append(f"{where}: suppression-list value must be a positive count")
        else:
            out[(parts[0], parts[1])] = parts[2]
    return out, problems


def _check_suppressions(
    rel: str, text: str, data: bytes, listed: dict[tuple[str, str], str], seen: set[tuple[str, str]]
) -> list[str]:
    hits = []
    if rel.rsplit("/", 1)[-1] in SCANNER_CONFIG_NAMES:
        key = (rel, SCANNER_CONFIG_RULE)
        seen.add(key)
        if key not in listed:
            hits.append(f"{rel}:1: {SCANNER_CONFIG_RULE}")
        elif listed[key] != hashlib.sha256(data).hexdigest():
            hits.append(f"{rel}:1: suppression-list hash differs for {SCANNER_CONFIG_RULE}")
    for rule, rx in SUPPRESSIONS.items():
        found = [n for n, line in enumerate(text.splitlines(), 1) if rx.search(line)]
        if not found:
            continue
        key = (rel, rule)
        seen.add(key)
        if key not in listed:
            hits += [f"{rel}:{n}: {rule}" for n in found]
        elif int(listed[key]) != len(found):
            hits.append(
                f"{rel}:{found[0]}: suppression-list count is {len(found)}, list says {listed[key]} ({rule})"
            )
    return hits


def scan(
    repo: Path, allowlist: Path, extra: Path, banned_src: Path, suppressions: Path | None = None
) -> list[str]:
    banned = _banned(banned_src, extra)
    allowed, hits = _allowed(allowlist)
    listed, problems = _suppressions(suppressions)
    hits += problems
    seen: set[tuple[str, str]] = set()
    cmd = ["git", "-C", str(repo), "ls-files", "-z"]
    listing = subprocess.run(cmd, capture_output=True, check=True).stdout  # noqa: S603
    tracked = {rel for rel in listing.decode("utf-8").split("\0") if rel}
    hits += [
        f"{allowlist.name}: stale entry, {rel} is not tracked"
        for rel in sorted(set(allowed) - tracked)
    ]
    for rel in sorted(tracked):
        path = repo / rel
        if not path.is_file():
            continue
        skip = allowed.get(rel, set())
        data = path.read_bytes()
        if b"\0" in data[:8000]:
            continue  # binary
        text = data.decode("utf-8", errors="replace")
        hits += _check_suppressions(
            rel, text, data, listed, seen
        )  # even for a file the allowlist skips
        if "*" in skip:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for rule, rx in PATTERNS.items():
                if rule in skip:
                    continue
                for m in rx.finditer(line):
                    if m.group(0) != EXAMPLE_KEY:
                        hits.append(f"{rel}:{n}: {rule}")
            if "banned-name" not in skip and rel not in LIST_FILES:
                hits += [f"{rel}:{n}: banned-name" for b in banned if b in line]
    if suppressions is not None:
        for p_rel, rule in sorted(set(listed) - seen):
            why = "not tracked" if p_rel not in tracked else "has no such marker any more"
            hits.append(f"{suppressions.name}: stale entry, {p_rel} {rule} {why}")
    return hits


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(HERE.parent))
    ap.add_argument("--allowlist", default=str(HERE / "scan_allowlist.txt"))
    ap.add_argument("--extra", default=str(HERE / "scan_banned_extra.txt"))
    ap.add_argument("--suppressions", default=str(HERE / "scan_suppressions.txt"))
    ap.add_argument(
        "--banned-src", default=str(HERE.parent / "tests" / "test_no_reference_material.py")
    )
    a = ap.parse_args()
    found = scan(
        Path(a.root), Path(a.allowlist), Path(a.extra), Path(a.banned_src), Path(a.suppressions)
    )
    print("\n".join(found))
    sys.exit(1 if found else 0)
