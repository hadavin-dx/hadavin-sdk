"""Two scans over the whole ask-your-data demo tree.

1. Literals that must never be in the repository: keys, account ids, machine paths, regions, model ids, real e-mail
   addresses, quoted Decimal numbers outside settings.py. Every file type that can hold text is read; an allowlist entry
   names the file, the pattern AND the exact source line, and an entry nothing matches fails the test.
2. Numbers: tunable numbers live in `askdata/settings.py`. The scan reads every Python module of the demo
   (`askdata`, `db`, `data`) for numeric defaults of functions and lambdas, class and module attributes, augmented
   assignments, keyword arguments named like a timeout/limit/delay, positional arguments of sleep/join/wait/range,
   and comparisons against a number. The structural constants that remain are listed with a reason and must match exactly.
   Out of scope, said plainly: the dataset generators `db/lumen.py` and `db/seed.py` (the numbers ARE the dataset) and the
   core SDK's own constants (for example the retry delays in `hadavin_sdk/llm/retry.py`).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from .conftest import DEMO

SKIP_DIRS = {"__pycache__", ".pytest_cache", ".venv", "work"}
SKIP_FILES = {
    "data/gold.jsonl",
    "data/adversarial.jsonl",
    "data/adversarial.dev.jsonl",
    "data/exemplars.jsonl",
}
SCAN_SUFFIXES = {
    ".py", ".sql", ".yaml", ".yml", ".md", ".toml", ".psql", ".json", ".jsonl", ".env", ".sh", ".ps1", ".txt", ".cfg", ".ini", ".csv",
}  # fmt: skip
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
        if (
            p.is_file()
            and p.suffix in SCAN_SUFFIXES
            and not (set(rel.parts) & SKIP_DIRS)
            and rel.as_posix() not in SKIP_FILES
        ):
            out.append(p)
    return out


def _line_of(text: str, pos: int) -> str:
    start = text.rfind("\n", 0, pos) + 1
    end = text.find("\n", pos)
    return text[start : end if end != -1 else len(text)].strip()


def _hits(files: list[Path] | None = None) -> dict[tuple[str, str], list[tuple[str, str]]]:
    found: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for p in files if files is not None else _scan_files():
        rel = p.relative_to(DEMO).as_posix() if DEMO in p.parents else p.name
        text = p.read_text(encoding="utf-8", errors="replace")
        for name, rx in PATTERNS.items():
            if name == "quoted Decimal number outside settings" and (
                p.suffix != ".py" or rel.endswith("settings.py")
            ):
                continue
            if name == "model id literal" and p.suffix == ".md":
                continue  # prose may name a model family; code, yaml and config may not
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
NAME_HINTS = (
    "timeout",
    "delay",
    "sleep",
    "wait",
    "limit",
    "max",
    "min",
    "retries",
    "backoff",
    "interval",
    "poll",
    "ttl",
    "batch",
    "cap",
)


def _is_num(n: ast.AST) -> bool:
    return (
        isinstance(n, ast.Constant)
        and isinstance(n.value, int | float)
        and not isinstance(n.value, bool)
        and n.value not in OK_SMALL
    )


def _numbers_in(node: ast.AST) -> list[ast.Constant]:
    return [n for n in ast.walk(node) if _is_num(n)]  # type: ignore[misc]


def numeric_literals(path: Path) -> set:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set = set()

    def add(nodes) -> None:
        found.update(n.value for n in nodes)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda):
            for d in [*node.args.defaults, *[k for k in node.args.kw_defaults if k]]:
                add(_numbers_in(d))
        elif (
            isinstance(node, ast.AnnAssign)
            and node.value is not None
            or isinstance(node, ast.AugAssign)
        ):
            add(_numbers_in(node.value))
        elif isinstance(node, ast.Call):
            fname = ast.unparse(node.func).lower()
            for kw in node.keywords:
                if kw.arg and any(w in kw.arg.lower() for w in NAME_HINTS):
                    add(_numbers_in(kw.value))
            if any(w in fname for w in ("sleep", "join", "wait", "timeout", "range")):
                for a in node.args:
                    add(_numbers_in(a))
        elif isinstance(node, ast.Compare):
            add([c for c in [node.left, *node.comparators] if _is_num(c)])  # type: ignore[misc]
    for node in tree.body:
        if isinstance(node, ast.Assign):
            add(_numbers_in(node.value))
        elif isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, ast.Assign):
                    add(_numbers_in(sub.value))
    return found


# file -> (exact set of remaining numbers, why they are structural and not tunable)
STRUCTURAL = {
    "askdata/allowed.py": ({2, 3}, "argument counts of allowed functions"),
    "askdata/cli.py": ({2, 3}, "argparse arity and a two-attempt loop"),
    "askdata/compare.py": ({2}, "decimal places of the result comparison"),
    "askdata/evalrun.py": ({10, 11, 12, 13}, "the documented exit-code band of `eval run`"),
    "askdata/fixtures.py": ({100, 1000, 1024}, "the test-fixture builder's route and tokens"),
    "askdata/htmlexport.py": ({12}, "characters of a hash shown in the HTML export"),
    "askdata/ledger.py": ({2, 5, 64, 300, 4000}, "schema bounds of a ledger line (the question and attempt limits come from settings)"),
    "askdata/llm_io.py": ({4000}, "a hint is cut at 4000 characters"),
    "askdata/meter.py": ({1_000_000}, "tokens per million, the unit of a price"),
    "askdata/pipeline.py": ({2}, "one resend of a dropped statement"),
    "askdata/policy.py": ({2, 3, 4, 5, 6, 7}, "the exit-code table"),
    "askdata/safe_text.py": (
        {32, 127, 128, 159, 173, 256, 1564, 6158, 8203, 8207, 8232, 8238, 8288, 8292, 8294, 8297, 65279, 917504, 917631},
        "unicode ranges stripped from printed text",
    ),
    "askdata/sealed.py": ({16, 20, 64}, "key-id length, the shortest reset reason, the genesis hash width"),
    "askdata/validate.py": ({2, 4, 6, 8, 127, 200, 2000, 4000}, "validator rule limits: part of the rule definitions V01 to V12"),
    "data/goldcheck.py": ({2, 3, 5, 7, 8, 10, 12, 500, 0.8}, "the gold-set contract checks (counts per tier, agreement floor)"),
    "db/build_verify.py": ({92}, "the backslash character code"),
}  # fmt: skip
DATASET_GENERATORS = {"db/lumen.py", "db/seed.py"}  # the numbers ARE the synthetic dataset
SCANNED_DIRS = ("askdata", "db", "data")


def _modules() -> dict[str, Path]:
    out = {}
    for d in SCANNED_DIRS:
        for p in sorted((DEMO / d).glob("*.py")):
            rel = p.relative_to(DEMO).as_posix()
            if p.name != "settings.py" and rel not in DATASET_GENERATORS:
                out[rel] = p
    return out


def test_tunable_numbers_live_in_settings_py_and_nowhere_else():
    found = {rel: numeric_literals(p) for rel, p in _modules().items()}
    found = {k: v for k, v in found.items() if v}
    expected = {k: v[0] for k, v in STRUCTURAL.items()}
    diff = {
        k: (found.get(k), expected.get(k))
        for k in set(found) | set(expected)
        if found.get(k) != expected.get(k)
    }
    assert diff == {}, diff


def test_the_numeric_scan_catches_each_kind_of_planted_number(tmp_path):
    p = tmp_path / "x.py"
    p.write_text(
        "import time\n"
        "def f(timeout: float = 7.5): ...\n"
        "g = lambda wait=33: wait\n"
        "class C:\n    limit = 42\n    other: int = 43\n"
        "LIMIT = 99\n"
        "TOTAL = 0\nTOTAL += 17\n"
        "def h(n):\n    time.sleep(0.07)\n    for _ in range(11):\n        pass\n    if n > 101:\n        return 1\n"
        "def k():\n    return call(max_retries=13, poll_every=0.3)\n",
        encoding="utf-8",
    )
    assert numeric_literals(p) == {7.5, 33, 42, 43, 99, 17, 0.07, 11, 101, 13, 0.3}


def test_a_new_tunable_in_a_scanned_module_fails_the_test(monkeypatch, tmp_path):
    extra = tmp_path / "newmod.py"
    extra.write_text("def f(retries=9): ...\n", encoding="utf-8")
    assert numeric_literals(extra) == {9}
    assert all(rel in STRUCTURAL or not numeric_literals(p) for rel, p in _modules().items())
