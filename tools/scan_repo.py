"""Scan git-tracked files for secrets and banned names; exit 1 on any hit (the repo is public).

Usage: python tools/scan_repo.py [--root DIR] [--allowlist FILE] [--extra FILE] [--suppressions FILE] [--banned-src FILE] [--print-list]
Output per hit: path:line: rule (the matched text is never printed, so CI logs hold no secret).
False positives: add `path:rule:reason` (one per line, `#` comments ok) to tools/scan_allowlist.txt. The entry skips ONLY that
rule on that file; the rule must be one of the secret rules, `banned-name` or `nul-in-text-file` (never `*`), and the reason must pass
the same check as a suppression-list reason. An entry whose file is no longer tracked, with an unknown rule or without a reason is itself a hit.
Suppressions: a comment that switches a scanner or linter off (the nosec, semgrep, gitleaks, trivy, sonar, pmd, checkov, tfsec, zizmor,
detect-secrets, lgtm and codeql markers, a ruff range switch, a noqa that is blanket (also an empty `noqa:`) or names a ruff `S`
security code; all matched without regard to case) and every scanner or linter config file (.gitleaksignore, .gitleaks.toml,
.semgrepignore, .trivyignore, .flake8, .gitattributes, any file whose name holds codeql or zizmor, .coderabbit.yaml, any pyproject.toml
below the root, ...) is a hit unless tools/scan_suppressions.txt lists it:
`path:rule:value:reason`, value = `count@sha256` (the number of markers in that file and the sha256 of their sorted line texts, so a
widened, replaced or moved-to-other-code marker is a change), or the sha256 of the config file (line endings read as LF). The two list files
tools/scan_allowlist.txt and tools/scan_banned_extra.txt are pinned the same way. `python tools/scan_repo.py --print-list` writes a
fresh list (reasons of existing lines are kept; a new line gets the placeholder reason that the scan REFUSES until a reviewer replaces it
with a real reason: at least 15 characters and 3 different words, not the generic baseline phrase). A stale, wrong-count, wrong-hash,
reasonless or unknown-rule line is itself a hit. The list is the one place a reviewer reads. Never listable: a file-level `ruff: noqa`
without codes; a ruff, bandit or semgrep key in a pyproject.toml below the root (the file is parsed as TOML, any spelling counts, a file
that does not parse is refused); a tracked symlink or non-regular file with a scanner-config name; a `.gitattributes` line with the
`-diff` or `binary` attribute (the pinned gitleaks reads history with `git log -p` and sees nothing of such a file, probed 2026-11-10);
a tracked Python file under a folder that ruff skips by default. A NUL byte in a file whose extension is not on the short known-binary
list is a hit (fail closed; list it per path with the rule `nul-in-text-file` and a reason); every file with a NUL is still scanned
for secrets (known-binary ones on the latin-1 reading of their bytes).
Banned names: the BANNED tuple in tests/test_no_reference_material.py (read, not copied) plus tools/scan_banned_extra.txt.
If BANNED cannot be found or is empty the scan fails (it never silently turns the check off).
"""

import argparse
import ast
import hashlib
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXAMPLE_KEY = "AKIAIOSFODNN7EXAMPLE"  # the one literal AWS documents as a placeholder
LIST_FILES = {
    "tools/scan_banned_extra.txt",
    "tools/scan_allowlist.txt",
}  # they hold names by design: skip banned-name only

# A secret prefix must not be the tail of a longer letters-and-digits word, but `\b` is wrong for that: it sees no boundary after `_`
# (`id_AKIA...`, `KEY_ghp_...`) or after the letter of an escape (`"a\nAKIA...` holds a backslash, `n`, then the key). So the guard is
# "not preceded by a letter or digit", or preceded by a backslash escape that ends in a letter or hex digits (`\n`, `\x0a`, `\u000a`).
_LEAD = r"(?:(?<![A-Za-z0-9])|(?<=\\[nrtfv])|(?<=\\x[0-9A-Fa-f]{2})|(?<=\\u[0-9A-Fa-f]{4}))"
_TAIL = r"(?![A-Za-z0-9])"
PATTERNS = {
    "cloud-id-prefix": re.compile(_LEAD + r"(?:AKIA|ASIA)[0-9A-Z]{16}" + _TAIL),
    "llm-id-ant": re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
    "llm-id-sk": re.compile(_LEAD + r"sk-[A-Za-z0-9_-]{32,}"),
    "pem-block-header": re.compile(r"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY(?: BLOCK)?-----"),
    "chat-id-xox": re.compile(_LEAD + r"xox[abeoprs]-[A-Za-z0-9-]{10,}"),
    "vcs-id-classic": re.compile(_LEAD + r"gh[pousr]_[A-Za-z0-9]{36,}"),
    "vcs-id-fine": re.compile(_LEAD + r"github_pat_[A-Za-z0-9_]{22,}"),
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
    # blanket noqa (also an empty `noqa:` or one with no code), or a noqa naming a ruff security (S) code; style codes (BLE001, F401, ...)
    # are not scanner suppressions
    # a file-level `ruff: noqa` / `flake8: noqa` switches rules off for the whole file, so it is always a hit
    "suppress-noqa-security": re.compile(
        _C
        + r"noqa\b(?!\s*:\s*[A-Za-z]{1,10}\d)|"
        + _C
        + r"noqa\s*:[^#]*\bS\d{3}\b|"
        + _C
        + r"(?:ruff|flake8)\s*:\s*noqa\b",
        _I,
    ),
    # ruff range switches: `ruff: disable[...]`, `ruff: ignore[...]`, `ruff: enable[...]`
    "suppress-ruff-range": re.compile(_C + r"ruff\s*:\s*(?:disable|ignore|enable)", _I),
    "suppress-nosonar": re.compile(_C + "NO" + "SONAR", _I),
    # the legacy LGTM scanner reads a bare comment of just that word as switching every alert of the line off, like the bracket form
    "suppress-lgtm": re.compile(_C + r"lgtm\b|lgtm\s*\[", _I),
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
    "zizmor.yaml",
    ".checkov.yml",
    ".checkov.yaml",
    ".hadolint.yaml",
    ".hadolint.yml",
    ".gitattributes",
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
SCANNER_CONFIG_DIRS = (".github/codeql/", ".semgrep/", ".tfsec/", ".checkov/")
# Any file whose name holds one of these words is a scanner config too (.github/codeql-config.yml, zizmor.yaml, ...).
SCANNER_CONFIG_WORDS = ("codeql", "zizmor")
# Files that steer this scan itself: pinned by hash like a scanner config, found by exact path.
SCANNER_CONFIG_PATHS = {"tools/scan_allowlist.txt", "tools/scan_banned_extra.txt"}
# A non-root pyproject.toml is a scanner config (pinned by hash) and may never hold a ruff, bandit or semgrep key
# (the root one is checked by tests/test_ci_gitleaks_scope.py). It is parsed as TOML, so every spelling counts (`[ tool.ruff ]`,
# `[tool."ruff"]`, a dotted key, `[tool]` with `ruff = {...}`, an inline table); a file that does not parse is refused.
NESTED_PYPROJECT_TOOLS = {"ruff", "bandit", "semgrep"}
NESTED_PYPROJECT_RULE = "nested-pyproject-scanner-table"
NESTED_PYPROJECT_UNPARSABLE_RULE = "nested-pyproject-unparsable"
# A tracked or missing config-named path that is not a regular file (a link to /dev/null, a folder, a missing file): never listable.
CONFIG_NOT_FILE_RULE = "scanner-config-not-a-file"
# `.gitattributes` with `-diff` or `binary` makes `git log -p` print "Binary files differ" for the file; the pinned gitleaks then sees
# nothing of it (probed with 8.30.1 on 2026-11-10: handover/reports/A24-PR91-fix3-gitleaks-probe.txt). `-text` and `diff=name` did not blind it.
GITATTRIBUTES_BLIND = re.compile(r"(?:^|\s)(?:-diff|binary)(?=\s|$)")
GITATTRIBUTES_RULE = "gitattributes-hides-diff"
# Folders that ruff skips by default: a tracked Python file below one of them is never linted.
RUFF_SKIPPED_DIRS = {
    ".bzr", ".direnv", ".eggs", ".git", ".git-rewrite", ".hg", ".ipynb_checkpoints", ".mypy_cache", ".nox", ".pants.d",
    ".pyenv", ".pytest_cache", ".pytype", ".ruff_cache", ".svn", ".tox", ".venv", ".vscode", "__pypackages__", "_build",
    "buck-out", "build", "dist", "node_modules", "site-packages", "venv",
}  # fmt: skip
RUFF_SKIPPED_RULE = "py-in-ruff-skipped-dir"
# A NUL byte in a file whose extension is not on this short list of real binary formats is refused (fail closed; a file with no
# extension such as Dockerfile or Makefile is refused too). The extension is never trusted to hide a file: every file that holds a
# NUL is still scanned for secrets, a known-binary one on the latin-1 reading of its bytes.
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".bmp", ".webp", ".avif", ".tif", ".tiff",
    ".pdf", ".zip", ".gz", ".tgz", ".bz2", ".xz", ".7z", ".tar", ".whl", ".jar",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".parquet", ".db", ".sqlite", ".sqlite3", ".pyc", ".so", ".dll", ".exe", ".wasm",
    ".mp3", ".mp4", ".mov", ".wav", ".npy", ".bin",
}  # fmt: skip
SCANNER_CONFIG_RULE = "scanner-config-file"
NUL_RULE = "nul-in-text-file"
LIST_RULES = set(SUPPRESSIONS) | {SCANNER_CONFIG_RULE}
ALLOW_RULES = set(PATTERNS) | {
    "banned-name",
    NUL_RULE,
}  # a rule an allowlist line may skip; never `*`


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


MIN_REASON = 15
MIN_REASON_WORDS = 3
# Generic filler that says nothing about this marker (the phrases of the mechanical baseline of 2742c1b).
BOILERPLATE_REASON = re.compile(
    r"not\s+individually\s+reviewed|carries\s+its\s+own\s+inline\s+reason|baseline\s+of\s+[0-9a-f]{7}",
    re.IGNORECASE,
)


def reason_problem(reason: str) -> str:
    """Why a reason cannot stand ('' if it can): the generator's placeholder, generic filler, or too little to say anything."""
    if re.match(r"NEW\b", reason):
        return "is the placeholder from --print-list, write a reviewed reason"
    if len(reason) < MIN_REASON:
        return f"is shorter than {MIN_REASON} characters"
    if BOILERPLATE_REASON.search(reason):
        return "is generic baseline filler, say what the marker does and why it is safe here"
    if len({w.lower() for w in re.findall(r"[A-Za-z]{2,}", reason)}) < MIN_REASON_WORDS:
        return f"has fewer than {MIN_REASON_WORDS} different words"
    return ""


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
        if parts[1] not in ALLOW_RULES:
            problems.append(
                f"{allowlist.name}:{n}: allowlist-entry unknown rule (one of the scan rules, never *)"
            )
            continue
        if reason_problem(parts[2]):
            problems.append(
                f"{allowlist.name}:{n}: allowlist-entry reason {reason_problem(parts[2])}"
            )
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


def config_hash(data: bytes) -> str:
    """sha256 of a config file with CRLF read as LF, so a Windows checkout (autocrlf) hashes like a Linux one."""
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def _is_config(rel: str) -> bool:
    name = rel.rsplit("/", 1)[-1].lower()
    low = rel.lower()
    return (
        rel in SCANNER_CONFIG_PATHS
        or name in SCANNER_CONFIG_NAMES
        or low.startswith(SCANNER_CONFIG_DIRS)
        or (low + "/").startswith(SCANNER_CONFIG_DIRS)
        or any(word in name for word in SCANNER_CONFIG_WORDS)
        or (name == "pyproject.toml" and "/" in rel)
    )


def _nested_pyproject_hit(text: str) -> str:
    """The rule a below-root pyproject.toml breaks ('' if none): a ruff, bandit or semgrep key in any TOML spelling, or no parse."""
    try:
        tool = tomllib.loads(text).get("tool", {})
    except (tomllib.TOMLDecodeError, ValueError, RecursionError):
        return NESTED_PYPROJECT_UNPARSABLE_RULE
    if isinstance(tool, dict) and any(str(k).lower() in NESTED_PYPROJECT_TOOLS for k in tool):
        return NESTED_PYPROJECT_RULE
    return ""


def _check_suppressions(
    rel: str, text: str, data: bytes, listed: dict[tuple[str, str], str], seen: set[tuple[str, str]]
) -> list[str]:
    hits = []
    low = rel.rsplit("/", 1)[-1].lower()
    if low == "pyproject.toml" and "/" in rel and (bad := _nested_pyproject_hit(text)):
        hits.append(
            f"{rel}:1: {bad}"
        )  # never listable: only the root pyproject may configure these
    if low == ".gitattributes":
        hits += [
            f"{rel}:{n}: {GITATTRIBUTES_RULE}"
            for n, line in enumerate(text.splitlines(), 1)
            if not line.lstrip().startswith("#") and GITATTRIBUTES_BLIND.search(line)
        ]
    if low.endswith((".py", ".pyi")) and RUFF_SKIPPED_DIRS & set(rel.split("/")[:-1]):
        hits.append(f"{rel}:1: {RUFF_SKIPPED_RULE}")
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
        elif listed[key] != config_hash(data):
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


def _tracked_bytes(path: Path, is_link: bool) -> bytes:
    """What git holds for this path: the file's bytes, or for a link its target text (the file it points to is a path of its own)."""
    return os.readlink(path).encode("utf-8", "surrogateescape") if is_link else path.read_bytes()


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
        is_link = path.is_symlink()
        if (is_link or not path.is_file()) and (_is_config(rel) or not is_link):
            continue  # never listable: the scan reports a config-named link, folder or missing file
        data = _tracked_bytes(path, is_link)
        text = data.decode("utf-8", errors="replace")
        if _is_config(rel):
            key = (rel, SCANNER_CONFIG_RULE)
            reason = reasons.get(key, "NEW, needs a reviewed reason")
            rows.append(f"{rel}:{SCANNER_CONFIG_RULE}:{config_hash(data)}:{reason}")
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
        # the config-name check runs on the tracked path first: a link such as ruff.toml -> /dev/null is not a file
        # but ruff still reads it, so a config-named link, folder or missing file is a hit that no list line covers
        is_link = path.is_symlink()
        if is_link or not path.is_file():
            if _is_config(rel):
                seen.add((rel, SCANNER_CONFIG_RULE))
                hits.append(f"{rel}:1: {CONFIG_NOT_FILE_RULE}")
                continue
            if not is_link:
                continue  # a folder (submodule) or a file missing from the work tree
        skip = allowed.get(rel, set())
        # git stores a link as its target text, so that text is what is scanned (the file it points to is its own tracked path, or
        # not repository content at all)
        data = _tracked_bytes(path, is_link)
        text = data.decode("utf-8", errors="replace")
        # config-name and marker checks run before anything is skipped and even for a file the allowlist skips
        hits += _check_suppressions(rel, text, data, listed, seen)
        if b"\0" in data:
            if Path(rel).suffix.lower() in BINARY_EXTENSIONS:
                # a known binary format is still read for secrets, as latin-1 (one character per byte, nothing is dropped)
                text = data.decode("latin-1")
            elif NUL_RULE not in skip:
                hits.append(
                    f"{rel}:1: {NUL_RULE}"
                )  # fail closed; the file is scanned as text below as well
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
