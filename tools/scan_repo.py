"""Scan git-tracked files for secrets and banned names; exit 1 on any hit (the repo is public).

Usage: python tools/scan_repo.py [--root DIR] [--allowlist FILE] [--extra FILE] [--banned-src FILE]
Output per hit: path:line: rule (the matched text is never printed, so CI logs hold no secret).
False positives: add `path:rule:reason` (one per line, `#` comments ok) to tools/scan_allowlist.txt. The entry skips ONLY that
rule on that file (rule `*` skips all rules; avoid it). An entry whose file is no longer tracked, or without a reason, is itself a hit.
Suppressions: a comment that switches a scanner or linter off (the nosec, semgrep, gitleaks, trivy, sonar, pmd, checkov, tfsec, zizmor,
detect-secrets, lgtm and codeql markers, a ruff range switch, a noqa that is blanket or names a ruff `S` security code; all matched
without regard to case) and every scanner or linter config file (.gitleaksignore, .gitleaks.toml, .semgrepignore, .trivyignore, .flake8,
sonar and codeql files, .coderabbit.yaml, any pyproject.toml below the root, ...) is a hit unless tools/scan_suppressions.txt lists it:
`path:rule:value:reason`, value = `count@sha256` (the number of markers in that file and the sha256 of their sorted line texts, so a
widened, replaced or moved-to-other-code marker is a change), or the sha256 of the config file. The two list files
tools/scan_allowlist.txt and tools/scan_banned_extra.txt are pinned the same way. `python tools/scan_repo.py --print-list` writes a
fresh list (reasons of existing lines are kept; a new line gets the placeholder reason that the scan REFUSES until a reviewer replaces it
with a real reason of at least 15 characters). A stale, wrong-count, wrong-hash, reasonless or unknown-rule line is itself a hit. The list
is the one place a reviewer reads. Never listable: a file-level `ruff: noqa` without codes, and a ruff, bandit or semgrep table in a
pyproject.toml below the root. A NUL byte in a file whose extension is not on the short known-binary list is a hit (fail closed); such a
file is still scanned as text.
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

# Suppression comments. Matched without regard to case. The comment prefix is required except for markers that are
# unambiguous on their own (the semgrep, gitleaks, lgtm and codeql markers), so prose that only names `nosec` is not a hit.
# Marker words are written in parts so this file does not hold a live marker.
_C = r"(?:#|//|--|/\*)\s*"
_I = re.IGNORECASE
SUPPRESSIONS = {
    "suppress-nosec": re.compile(_C + "nos" + "ec", _I),
    "suppress-semgrep-ignore": re.compile("nosem" + "grep|" + _C + r"nosem\b", _I),
    "suppress-gitleaks-allow": re.compile("gitleaks:" + "allow", _I),
    "suppress-trivy-ignore": re.compile(_C + "trivy:" + "ignore", _I),
    # blanket noqa, or a noqa naming a ruff security (S) code; style codes (BLE001, F401, ...) are not scanner suppressions
    # a file-level `ruff: noqa` / `flake8: noqa` switches rules off for the whole file, so it is always a hit
    "suppress-noqa-security": re.compile(
        _C
        + r"noqa\b(?!\s*:)|"
        + _C
        + r"noqa\s*:[^#]*\bS\d{3}\b|"
        + _C
        + r"(?:ruff|flake8)\s*:\s*noqa\b",
        _I,
    ),
    # ruff range switches: `ruff: disable[...]`, `ruff: ignore[...]`, `ruff: enable[...]`
    "suppress-ruff-range": re.compile(_C + r"ruff\s*:\s*(?:disable|ignore|enable)", _I),
    "suppress-nosonar": re.compile(_C + "NO" + "SONAR", _I),
    "suppress-lgtm": re.compile(r"lgtm\s*\[", _I),
    "suppress-codeql": re.compile(r"codeql\s*\[", _I),
    "suppress-zizmor-ignore": re.compile(_C + r"zizmor\s*:\s*ignore", _I),
    "suppress-allowlist-secret": re.compile(
        _C + r"pragma\s*:\s*(?:allow|white)list\s+(?:next\s*line\s+)?secret", _I
    ),
    "suppress-nopmd": re.compile(_C + "NO" + "PMD", _I),
    "suppress-checkov-skip": re.compile(_C + "checkov:" + "skip", _I),
    "suppress-tfsec-ignore": re.compile(_C + "tfsec:" + "ignore", _I),
}
# A file-level `ruff: noqa` / `flake8: noqa` must name its codes; a bare one is a hit that no list line can cover.
BLANKET_FILE_NOQA = re.compile(_C + r"(?:ruff|flake8)\s*:\s*noqa\b(?!\s*:\s*[A-Za-z]{1,10}\d)", _I)
BLANKET_FILE_NOQA_RULE = "file-noqa-without-codes"
# Scanner and linter configuration files, found by file name (compared in lower case) in any folder.
SCANNER_CONFIG_NAMES = {
    ".gitleaksignore",
    ".gitleaks.toml",
    "gitleaks.toml",
    ".semgrepignore",
    ".semgrep.yml",
    ".semgrep.yaml",
    ".trivyignore",
    ".trivyignore.yaml",
    "trivy.yaml",
    "trivy.yml",
    ".bandit",
    ".zizmor.yml",
    ".zizmor.yaml",
    "zizmor.yml",
    "ruff.toml",
    ".ruff.toml",
    "trivy-secret.yaml",
    "bandit.yaml",
    "bandit.yml",
    "setup.cfg",
    "tox.ini",
    ".flake8",
    "mypy.ini",
    "sonar-project.properties",
    ".sonarcloud.properties",
    ".coderabbit.yaml",
    ".coderabbit.yml",
    ".pre-commit-config.yaml",
    ".secrets.baseline",
    ".snyk",
}
# Whole folders of scanner configuration (any file below them).
SCANNER_CONFIG_DIRS = (".github/codeql/", ".semgrep/")
# Files that steer this scan itself: pinned by hash like a scanner config, found by exact path.
SCANNER_CONFIG_PATHS = {"tools/scan_allowlist.txt", "tools/scan_banned_extra.txt"}
# A non-root pyproject.toml is a scanner config (pinned by hash) and may never hold a ruff or bandit table
# (the root one is checked by tests/test_ci_gitleaks_scope.py).
NESTED_PYPROJECT_TABLE = re.compile(
    r"^\s*\[tool\.(?:ruff|bandit|semgrep)", re.IGNORECASE | re.MULTILINE
)
NESTED_PYPROJECT_RULE = "nested-pyproject-scanner-table"
# A NUL byte in a file whose extension is not on this short list of real binary formats is refused (fail closed: a NUL would
# otherwise hide the whole file from the secret patterns). A file with no extension (Dockerfile, Makefile) is refused too.
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".bmp", ".webp", ".avif", ".tif", ".tiff",
    ".pdf", ".zip", ".gz", ".tgz", ".bz2", ".xz", ".7z", ".tar", ".whl", ".jar",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".parquet", ".db", ".sqlite", ".sqlite3", ".pyc", ".so", ".dll", ".exe", ".wasm",
    ".mp3", ".mp4", ".mov", ".wav", ".npy", ".bin",
}  # fmt: skip
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
        if any(ch in parts[0] for ch in "*?["):
            problems.append(
                f"{allowlist.name}:{n}: allowlist-entry path must be one exact file, no glob"
            )
            continue
        out.setdefault(parts[0], set()).add(parts[1])
    return out, problems


MIN_REASON = 15


def reason_problem(reason: str) -> str:
    """Why a reason cannot stand ('' if it can): the generator's placeholder or a reason too short to say anything."""
    if re.match(r"NEW\b", reason):
        return "is the placeholder from --print-list, write a reviewed reason"
    if len(reason) < MIN_REASON:
        return f"is shorter than {MIN_REASON} characters"
    return ""


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
        elif parts[1] != SCANNER_CONFIG_RULE and not re.fullmatch(
            r"[1-9][0-9]*@[0-9a-f]{64}", parts[2]
        ):
            problems.append(f"{where}: suppression-list value must be a positive count@sha256")
        else:
            out[(parts[0], parts[1])] = parts[2]
        if len(parts) == 4 and all(parts) and reason_problem(parts[3]):
            problems.append(f"{where}: suppression-list reason {reason_problem(parts[3])}")
    return out, problems


def marker_value(lines: list[str]) -> str:
    """`count@sha256` of the sorted marker line texts (the text pins the marker, not only the number)."""
    digest = hashlib.sha256(
        "\n".join(sorted(ln.rstrip() for ln in lines)).encode("utf-8")
    ).hexdigest()
    return f"{len(lines)}@{digest}"


def _marker_lines(text: str) -> dict[str, tuple[list[int], list[str]]]:
    """{rule: (line numbers, line texts)} for every suppression marker in `text`."""
    out: dict[str, tuple[list[int], list[str]]] = {}
    for n, line in enumerate(text.splitlines(), 1):
        for rule, rx in SUPPRESSIONS.items():
            if rx.search(line):
                nums, texts = out.setdefault(rule, ([], []))
                nums.append(n)
                texts.append(line)
    return out


def _is_config(rel: str) -> bool:
    name = rel.rsplit("/", 1)[-1].lower()
    low = rel.lower()
    return (
        rel in SCANNER_CONFIG_PATHS
        or name in SCANNER_CONFIG_NAMES
        or low.startswith(SCANNER_CONFIG_DIRS)
        or (name == "pyproject.toml" and "/" in rel)
    )


def _check_suppressions(
    rel: str, text: str, data: bytes, listed: dict[tuple[str, str], str], seen: set[tuple[str, str]]
) -> list[str]:
    hits = []
    low = rel.rsplit("/", 1)[-1].lower()
    if low == "pyproject.toml" and "/" in rel and NESTED_PYPROJECT_TABLE.search(text):
        hits.append(
            f"{rel}:1: {NESTED_PYPROJECT_RULE}"
        )  # never listable: only the root pyproject may configure these
    hits += [
        f"{rel}:{n}: {BLANKET_FILE_NOQA_RULE}"
        for n, line in enumerate(text.splitlines(), 1)
        if BLANKET_FILE_NOQA.search(line)
    ]
    if _is_config(rel):
        key = (rel, SCANNER_CONFIG_RULE)
        seen.add(key)
        if key not in listed:
            hits.append(f"{rel}:1: {SCANNER_CONFIG_RULE}")
        elif listed[key] != hashlib.sha256(data).hexdigest():
            hits.append(f"{rel}:1: suppression-list hash differs for {SCANNER_CONFIG_RULE}")
    for rule, (nums, texts) in _marker_lines(text).items():
        key = (rel, rule)
        seen.add(key)
        value = marker_value(texts)
        if key not in listed:
            hits += [f"{rel}:{n}: {rule}" for n in nums]
        elif listed[key] != value:
            if int(listed[key].split("@")[0]) != len(nums):
                hits.append(
                    f"{rel}:{nums[0]}: suppression-list count is {len(nums)}, list says "
                    f"{listed[key].split('@')[0]} ({rule})"
                )
            else:
                hits.append(f"{rel}:{nums[0]}: suppression-list text hash differs ({rule})")
    return hits


def print_list(repo: Path, suppressions: Path) -> str:
    """A fresh suppression list for the tracked files; the header and the reasons of lines that still exist are kept."""
    old = _lines(suppressions)
    header = [ln for ln in old if ln.startswith("#")]
    reasons = {}
    for ln in old:
        parts = [p.strip() for p in ln.split(":", 3)]
        if len(parts) == 4 and not ln.startswith("#"):
            reasons[(parts[0], parts[1])] = parts[3]
    cmd = ["git", "-C", str(repo), "ls-files", "-z"]
    listing = subprocess.run(cmd, capture_output=True, check=True).stdout  # noqa: S603
    rows = []
    for rel in sorted(r for r in listing.decode("utf-8").split("\0") if r):
        path = repo / rel
        if not path.is_file():
            continue
        data = path.read_bytes()
        text = data.decode("utf-8", errors="replace")
        if _is_config(rel):
            key = (rel, SCANNER_CONFIG_RULE)
            reason = reasons.get(key, "NEW, needs a reviewed reason")
            rows.append(f"{rel}:{SCANNER_CONFIG_RULE}:{hashlib.sha256(data).hexdigest()}:{reason}")
        for rule, (_, texts) in _marker_lines(text).items():
            reason = reasons.get((rel, rule), "NEW, needs a reviewed reason")
            rows.append(f"{rel}:{rule}:{marker_value(texts)}:{reason}")
    return "\n".join(header + rows) + "\n"


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
        text = data.decode("utf-8", errors="replace")
        # config-name and marker checks run before the binary skip and even for a file the allowlist skips
        hits += _check_suppressions(rel, text, data, listed, seen)
        if b"\0" in data:
            if Path(rel).suffix.lower() in BINARY_EXTENSIONS:
                continue  # a known binary format
            hits.append(
                f"{rel}:1: nul-in-text-file"
            )  # fail closed: it is scanned as text below as well
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
        "--print-list", action="store_true", help="print a fresh suppression list and exit"
    )
    ap.add_argument(
        "--banned-src", default=str(HERE.parent / "tests" / "test_no_reference_material.py")
    )
    a = ap.parse_args()
    if a.print_list:
        sys.stdout.write(print_list(Path(a.root), Path(a.suppressions)))
        sys.exit(0)
    found = scan(
        Path(a.root), Path(a.allowlist), Path(a.extra), Path(a.banned_src), Path(a.suppressions)
    )
    print("\n".join(found))
    sys.exit(1 if found else 0)
