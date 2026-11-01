"""Two scans over the whole ask-your-data demo tree.

1. Literals that must never be in the repository: keys, account ids, machine paths, regions, model ids, real e-mail
   addresses, quoted Decimal numbers outside settings.py. Every file type that can hold text is read; an allowlist entry
   names the file, the pattern AND the exact source line, and an entry nothing matches fails the test.
2. Numbers: tunable numbers live in `askdata/settings.py`. The scan reads every Python module of the demo
   (`askdata`, `db`, `data`) for numeric defaults of functions and lambdas, class and module attributes, augmented
   assignments, keyword arguments named like a timeout/limit/delay, positional arguments of sleep/join/wait/range,
   and comparisons against a number. The structural constants that remain are listed with a reason and must match exactly.
   Said plainly about the region pattern: it covers the AWS-style names (including gov, cn, il, mx), the common Azure
names and the GCP continent-direction names; a region spelled some other way is not caught.
Out of scope, said plainly: the dataset generators `db/lumen.py` and `db/seed.py` (the numbers ARE the dataset) and the
   core SDK's own constants (for example the retry delays in `hadavin_sdk/llm/retry.py`).
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest

from .conftest import DEMO

SKIP_DIRS = {"__pycache__", ".pytest_cache", ".venv"}  # anywhere in the path
SKIP_TOP = {
    "work"
}  # only the TOP-level working folder (runtime output), not a folder named work deeper down
SCAN_SUFFIXES = {
    ".py", ".sql", ".yaml", ".yml", ".md", ".toml", ".psql", ".json", ".jsonl", ".env", ".sh", ".ps1", ".txt", ".cfg", ".ini",
    ".csv", ".bat", ".cmd", ".example", ".conf", ".properties",
}  # fmt: skip
SCAN_NAMES = {
    "Dockerfile",
    "Makefile",
    ".env",
    ".dockerignore",
    ".gitignore",
}  # files without a telling suffix
B64 = "[A-Za-z0-9/+=]"
REGION_WORDS = "east|west|north|south|central|southeast|northeast|northwest|southwest"
PATTERNS = {
    "anthropic key": re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
    "openai-style key": re.compile(r"\bsk-(proj-|svcacct-|admin-)?[A-Za-z0-9_-]{20,}"),
    "aws access key": re.compile(r"\bA(KIA|SIA)[0-9A-Z]{16}\b"),
    "aws secret (40 chars, no prefix)": re.compile(
        rf"(?<!{B64})(?=[A-Za-z0-9/+=]*[A-Z])(?=[A-Za-z0-9/+=]*[a-z])(?=[A-Za-z0-9/+=]*\d){B64}{{40}}(?!{B64})"
    ),
    "google key": re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    "github or slack token": re.compile(
        r"\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[abprso]-[A-Za-z0-9-]{10,}|xapp-[A-Za-z0-9-]{10,})"
    ),
    "12-digit account id": re.compile(r"(?<![\d.])\d{12}(?!\d)"),
    "region literal": re.compile(
        rf"\b(us|eu|ap|sa|ca|me|af|il|mx|cn)(-gov)?-({REGION_WORDS})-\d\b"
        r"|\b(eastus|westus|centralus|northeurope|westeurope|uksouth|southeastasia)\d?\b"
        rf"|\b(us|europe|asia|australia|northamerica|southamerica)-({REGION_WORDS})\d\b"
    ),
    "model id literal": re.compile(
        r"\b(claude-[a-z0-9]|gpt-[0-9o]|gemini-[0-9]|mistral-|mixtral-|deepseek-|qwen[0-9-]|grok-[0-9]|o[134]-(mini|preview|pro)"
        r"|(us|eu|apac)\.anthropic|anthropic\.claude|meta\.llama|amazon\.(nova|titan))"
    ),
    "windows path": re.compile(
        r"(?<![A-Za-z])[A-Za-z]:\\[A-Za-z$_]|[\"'`][A-Za-z]:[\\/]|\\\\[A-Za-z0-9_.-]+\\[A-Za-z0-9$_]"
    ),
    "posix home path": re.compile(r"(?<![\w.])/(Users|home)/[A-Za-z0-9_.-]+"),
    "e-mail address": re.compile(
        r"[A-Za-z0-9._%+-]+@(?!(example\.(com|org|net)|example|invalid|localhost)(?![A-Za-z0-9-]|\.[A-Za-z0-9]))"
        r"[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.(?!example\b)[A-Za-z]{2,}"
    ),
    "quoted Decimal number outside settings": re.compile(r"Decimal\(\s*[\"'](?!0[\"']|1[\"'])\d"),
}
# (file relative to the demo, pattern name) -> {exact stripped source lines that are fine}: line-specific, so a NEW
# occurrence in the same file is still caught. A line nothing matches fails the test.
ALLOWED: dict[tuple[str, str], set[str]] = {
    ("db/lumen.py", "quoted Decimal number outside settings"): {
        'return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)',
    },
}


def _scan_files() -> list[Path]:
    out = []
    for p in sorted(DEMO.rglob("*")):
        rel = p.relative_to(DEMO)
        if not p.is_file() or (set(rel.parts) & SKIP_DIRS) or rel.parts[0] in SKIP_TOP:
            continue
        if p.suffix in SCAN_SUFFIXES or p.name in SCAN_NAMES:
            out.append(p)
    return out


def _read(p: Path) -> str:
    """Strict decoding: UTF-8, or UTF-16 when it starts with a BOM. A file that cannot be decoded FAILS the scan
    instead of being read with replacement characters (which would hide a literal)."""
    raw = p.read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig")


def _line_of(text: str, pos: int) -> str:
    start = text.rfind("\n", 0, pos) + 1
    end = text.find("\n", pos)
    return text[start : end if end != -1 else len(text)].strip()


def _hits(files: list[Path] | None = None) -> dict[tuple[str, str], list[tuple[str, str]]]:
    found: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for p in files if files is not None else _scan_files():
        rel = p.relative_to(DEMO).as_posix() if DEMO in p.parents else p.name
        text = _read(p)
        for name, rx in PATTERNS.items():
            if name == "quoted Decimal number outside settings" and (
                p.suffix != ".py" or rel.endswith("settings.py")
            ):
                continue
            if name == "model id literal" and p.suffix in {".md", ".jsonl"}:
                continue  # prose and authorship fields in data may NAME a model; code, yaml and config may not
            for m in rx.finditer(text):
                found.setdefault((rel, name), []).append((m.group(0), _line_of(text, m.start())))
    return found


def test_the_whole_demo_tree_holds_no_secret_account_path_region_model_or_email_literal():
    found = _hits()
    unexpected: dict = {}
    used: dict[tuple[str, str], set[str]] = {}
    for key, hits in found.items():
        allowed = ALLOWED.get(key, set())
        for text, line in hits:
            if line in allowed:
                used.setdefault(key, set()).add(line)
            else:
                unexpected.setdefault(key, []).append((text, line[:100]))
    assert unexpected == {}, unexpected
    unused = [
        (k, ln) for k, lines in ALLOWED.items() for ln in lines if ln not in used.get(k, set())
    ]
    assert unused == [], f"allowlist entries nothing matches: {unused}"


def test_every_file_type_that_can_hold_text_is_scanned():
    suffixes = {p.suffix for p in _scan_files()}
    assert {".py", ".sql", ".yaml", ".md"} <= suffixes
    assert {
        ".json",
        ".jsonl",
        ".env",
        ".sh",
        ".ps1",
        ".txt",
        ".cfg",
        ".ini",
        ".csv",
    } <= SCAN_SUFFIXES


PLANTED = {
    "anthropic key": ["sk-ant-api03-" + "A" * 40],
    "openai-style key": ["sk-" + "b" * 24, "sk-proj-" + "c" * 30, "sk-svcacct-" + "d" * 30],
    "aws access key": ["AKIA" + "ABCDEFGHIJKLMNOP", "ASIA" + "ABCDEFGHIJKLMNOP"],
    "aws secret (40 chars, no prefix)": [
        "wJalrXUtnFEMI/K7MDENG/bPxRfiCY" + "ABCDEFGHIJ",
        "wJalrXUtnFEMIK7MDENGbPxRfiCY" + "ABCDEFGHIJ12",
    ],
    "google key": ["AIza" + "B" * 35],
    "github or slack token": [
        "ghp_" + "c" * 24,
        "gho_" + "c" * 24,
        "ghs_" + "c" * 24,
        "ghu_" + "c" * 24,
        "ghr_" + "c" * 24,
        "github_pat_" + "e" * 30,
        "xoxa-" + "1" * 12,
        "xoxs-" + "1" * 12,
        "xapp-" + "1" * 12,
    ],
    "12-digit account id": ["acct " + "1" * 12, "account " + "2" * 12 + ".", "id=" + "3" * 12],
    "region literal": [
        "us" + "-east-1",
        "us" + "-gov-west-1",
        "cn" + "-north-1",
        "il" + "-central-1",
        "mx" + "-central-1",
        "east" + "us2",
        "europe" + "-west4",
    ],
    "model id literal": [
        "model: mistral-large-2411",
        "'deepseek-chat'",
        "qwen2-72b",
        "grok-3",
        "o3-mini",
        "eu." + "anthropic.claude-x",
        "meta." + "llama3-70b",
        "amazon." + "nova-pro-v1:0",
        "gpt-4o",
        "gemini-2.5",
        "claude-sonnet-x",
    ],
    "windows path": ["D:" + "\\data\\x", "'C:" + "\\\\work'", "\\\\" + "fileserver\\share$"],
    "posix home path": ["/Users/" + "someone/x", "/home/" + "someone/x"],
    "e-mail address": ["owner@" + "company.io", "user@example.com" + ".evil.io"],
    "quoted Decimal number outside settings": ["Decimal('0.035')", 'Decimal("3.00")'],
}


@pytest.mark.parametrize(("name", "text"), [(n, t) for n, ts in PLANTED.items() for t in ts])
def test_the_literal_scan_catches_each_planted_value(name, text):
    assert PATTERNS[name].search(text), (name, text)


def test_the_literal_scan_does_not_flag_what_is_allowed():
    assert set(PLANTED) == set(PATTERNS)
    assert not PATTERNS["e-mail address"].search(
        "cust00001@example.com ro@db.example x@example.org"
    )
    assert not PATTERNS["aws secret (40 chars, no prefix)"].search("a" * 40)  # a hash is not a key
    assert not PATTERNS["aws secret (40 chars, no prefix)"].search("A1" * 20)  # no lower case
    assert not PATTERNS["12-digit account id"].search("0.123456789012") and not PATTERNS[
        "12-digit account id"
    ].search("1234567890123")


def test_a_new_occurrence_in_an_allow_listed_file_is_still_caught(tmp_path):
    p = tmp_path / "lumen.py"
    p.write_text('a = Decimal("0.01")\nb = Decimal("9.99")\n', encoding="utf-8")
    hits = _hits([p])[("lumen.py", "quoted Decimal number outside settings")]
    assert {line for _, line in hits} == {
        'a = Decimal("0.01")',
        'b = Decimal("9.99")',
    }  # line-specific, not file-wide


# ====================================================================== numbers
OK_SMALL = {0, 1, -1}
DATASET_GENERATORS = {"db/lumen.py", "db/seed.py"}  # the numbers ARE the synthetic dataset
ALLOWLIST = json.loads(
    (Path(__file__).with_name("numeric_allowlist.json")).read_text(encoding="utf-8")
)


def numeric_lines(path: Path) -> set[str]:
    """The stripped source line of EVERY numeric constant in the module (defaults, assignments in function bodies,
    returns, slices, expressions, arguments of any call, keyword arguments, comparisons: all of it) except 0, 1, -1."""
    src = path.read_text(encoding="utf-8")
    lines = src.splitlines()
    found = set()
    for n in ast.walk(ast.parse(src)):
        if (
            isinstance(n, ast.Constant)
            and isinstance(n.value, int | float)
            and not isinstance(n.value, bool)
            and n.value not in OK_SMALL
        ):
            found.add(lines[n.lineno - 1].strip())
    return found


def _modules() -> dict[str, Path]:
    out = {}
    for p in sorted(DEMO.rglob("*.py")):
        rel = p.relative_to(DEMO).as_posix()
        if (set(p.relative_to(DEMO).parts) & SKIP_DIRS) or p.relative_to(DEMO).parts[0] in SKIP_TOP:
            continue
        if p.name != "settings.py" and rel not in DATASET_GENERATORS:
            out[rel] = p
    return out


def test_every_numeric_constant_of_the_demo_is_on_a_listed_line_or_in_settings_py():
    found = {rel: numeric_lines(p) for rel, p in _modules().items()}
    found = {k: v for k, v in found.items() if v}
    new = {k: sorted(v - set(ALLOWLIST.get(k, {}).get("lines", []))) for k, v in found.items()}
    new = {k: v for k, v in new.items() if v}
    assert new == {}, f"numbers outside settings.py on lines not in numeric_allowlist.json: {new}"
    unused = {
        k: sorted(set(v["lines"]) - found.get(k, set()))
        for k, v in ALLOWLIST.items()
        if set(v["lines"]) - found.get(k, set())
    }
    assert unused == {}, f"allowlisted lines that no longer hold a number: {unused}"
    assert all(v["reason"] != "STRUCTURAL" and len(v["reason"]) > 10 for v in ALLOWLIST.values())


def test_the_numeric_scan_sees_every_context_and_is_line_specific(tmp_path):
    p = tmp_path / "x.py"
    p.write_text(
        "import time\n"
        "def f(timeout: float = 7.5): ...\n"
        "g = lambda wait=33: wait\n"
        "class C:\n    limit = 42\n    other: int = 43\n"
        "LIMIT = 99\nTOTAL = 0\nTOTAL += 17\n"
        "def h(n):\n    deadline = time.monotonic() + 30\n    time.sleep(0.07)\n    chunk = n[:200]\n"
        "    for _ in range(11):\n        pass\n    if n > 101:\n        return 31\n    if (n * 3) > 5:\n        return 1\n"
        "def k(a):\n    return call(a, 8, max_retries=13, poll_every=0.3, other=2)\n",
        encoding="utf-8",
    )
    lines = numeric_lines(p)
    assert "deadline = time.monotonic() + 30" in lines and "return 31" in lines
    assert (
        "chunk = n[:200]" in lines
        and "if (n * 3) > 5:" in lines
        and "return call(a, 8, max_retries=13, poll_every=0.3, other=2)" in lines
    )
    assert (
        "time.sleep(2)" not in lines
    )  # a NEW time.sleep(2) elsewhere is a different line: it is not allowlisted


def test_a_new_number_on_a_new_line_fails_even_when_its_value_is_already_allowlisted(tmp_path):
    allowed = set(ALLOWLIST["askdata/pipeline.py"]["lines"])
    p = tmp_path / "pipeline.py"
    p.write_text("time.sleep(2)\n", encoding="utf-8")
    assert numeric_lines(p) - allowed == {
        "time.sleep(2)"
    }  # the old value-set allowlist let this pass


def test_the_scan_reads_subpackages_and_top_level_files():
    names = set(_modules())
    assert {"askdata/sealed.py", "data/goldcheck.py", "db/build_verify.py"} <= names
    assert not any(n.startswith("work/") for n in names)
