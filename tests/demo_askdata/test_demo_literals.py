"""Two scans over the whole ask-your-data demo tree.

1. Literals that must never be in the repository: keys, account ids, machine paths, regions, model ids, real e-mail
   addresses, quoted Decimal numbers outside settings.py. EVERY file git would commit (tracked, or untracked and not
   ignored) that is not binary is read, whatever its suffix (a `.pem` or `.bak` included); without git, every file
   except caches. An allowlist entry names the file, the pattern AND the exact source line, and an entry nothing
   matches fails the test.
2. Numbers: tunable numbers live in `askdata/settings.py`. The scan reads every Python module of the demo
   (`askdata`, `db`, `data`) for numeric defaults of functions and lambdas, class and module attributes, augmented
   assignments, keyword arguments named like a timeout/limit/delay, positional arguments of sleep/join/wait/range,
   and comparisons against a number; numeric STRINGS given to int/float/Decimal or as an environment default; and
   0, 1 and -1 where they are tunables (an argument of sleep/join/wait/..., a keyword or an assignment named like
   a timeout/retry/limit/delay/attempt). The structural constants that remain are listed with a reason, counted per
   line, and must match exactly.
   Said plainly about the region pattern: it covers the AWS-style names (including gov, cn, il, mx), the Azure names
(continent-direction and country-direction) and the GCP names; a region spelled some other way is not caught.
Out of scope, said plainly: the dataset generators `db/lumen.py` and `db/seed.py` (the numbers ARE the dataset) and the
   core SDK's own constants (for example the retry delays in `hadavin_sdk/llm/retry.py`).
"""

from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
from collections import Counter
from pathlib import Path

import pytest

from .conftest import DEMO

GIT = shutil.which("git") or "git"

SKIP_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".git",
}  # caches only: .venv and the rest ARE scanned (git decides)
SKIP_TOP = {"work"}  # only the UNTRACKED top-level working folder (runtime output)
BINARY_MAGIC = (
    b"\x89PNG",
    b"PK\x03\x04",
    b"%PDF",
    b"\xff\xd8\xff",
    b"GIF8",
    b"\x1f\x8b",
    b"SQLite format",
)
B64 = "[A-Za-z0-9/+=]"
REGION_WORDS = "east|west|north|south|central|southeast|northeast|northwest|southwest"
AZURE_COUNTRIES = (
    "japan|canada|australia|brazil|korea|france|germany|sweden|norway|switzerland|italy|poland|spain|qatar|"
    "israel|mexico|chile|newzealand|uae|southafrica|uk|us|austria|belgium|indonesia|malaysia|taiwan|greece"
)
AZURE_DIRS = (
    "east|west|north|south|central|southeast|northeast|northcentral|southcentral|westcentral"
)
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
        # case-insensitive; AWS names with - or _, gov/iso partitions and availability-zone letters; Azure names with and
        # without a country prefix (including gov and Jio); GCP names
        rf"(?i:\b(us|eu|ap|sa|ca|me|af|il|mx|cn)([-_](gov|iso|isob|isoe|isof))?[-_]({REGION_WORDS})[-_]\d[a-z]?\b"
        r"|\b(eastus|westus|centralus|northeurope|westeurope|uksouth|southeastasia)\d?\b"
        rf"|\b(us|europe|asia|australia|northamerica|southamerica|me|africa)-({REGION_WORDS})\d[a-z]?\b"
        rf"|\b({AZURE_COUNTRIES})({AZURE_DIRS})\d?\b"
        r"|\b(north|south|west)centralus\d?\b|\b(south|central|west)india\b|\beastasia\b|\b(north|west)europe\b"
        r"|\b(east|southeast)asia\b|\bjioindia(west|central)\b|\busgov(virginia|arizona|texas|iowa)\b"
        r"|\busdod(east|central)\b)"
    ),
    "model id literal": re.compile(
        r"(?i:\b(claude[-_ ][a-z0-9]|gpt-[0-9o]|gemini[-_][0-9a-z]|mistral-|mixtral-|deepseek-|qwen[0-9-]|grok-[0-9]"
        r"|o[134]-(mini|preview|pro)|(us|eu|apac)\.anthropic|anthropic\.claude|meta\.llama|amazon\.(nova|titan)))"
    ),
    "windows path": re.compile(
        r"(?<![A-Za-z])[A-Za-z]:\\[A-Za-z$_]|[\"'`][A-Za-z]:[\\/]|\\\\[A-Za-z0-9_.-]+\\[A-Za-z0-9$_]"
    ),
    "posix home path": re.compile(r"(?<![\w.])/(Users|home)/[A-Za-z0-9_.-]+"),
    "e-mail address": re.compile(
        r"[A-Za-z0-9._%+-]+@(?!(example\.(com|org|net)|example|invalid|localhost)(?![A-Za-z0-9-]|\.[A-Za-z0-9]))"
        r"[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.(?!example\b)[A-Za-z]{2,}"
    ),
    "private key block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "password in a URL (DSN)": re.compile(
        r"\b[A-Za-z][A-Za-z0-9+.-]*://[^\s/:@'\"]+:[^\s/@'\"]{3,}@"
    ),
    "password or secret assignment": re.compile(
        r"(?i)\b(password|passwd|pwd|secret|api[_-]?key|token)\b[\"']?(?:\s*=\s*|:\s*)[\"'][^\"'\s]{8,}[\"']"
    ),
    "JWT": re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"),
    "bearer token": re.compile(
        r"(?i)\bauthorization\b[\"']?\s*[:=]\s*[\"']?bearer\s+[A-Za-z0-9._~+/-]{12,}"
    ),
    "Slack webhook": re.compile(r"hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]+"),
    "Stripe key": re.compile(r"\b[sr]k_(live|test)_[A-Za-z0-9]{16,}"),
    "quoted Decimal number outside settings": re.compile(r"Decimal\(\s*[\"'](?!0[\"']|1[\"'])\d"),
}
# (file relative to the demo, pattern name) -> {exact stripped source lines that are fine}: line-specific, so a NEW
# occurrence in the same file is still caught. A line nothing matches fails the test.
ALLOWED: dict[tuple[str, str], set[str]] = {
    ("db/lumen.py", "quoted Decimal number outside settings"): {
        'return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)',
    },
}


def _git_list(root: Path, *flags: str) -> list[Path] | None:
    try:
        done = subprocess.run(  # noqa: S603 - fixed argument list, no shell
            [GIT, "ls-files", *flags, "-z"], cwd=root, capture_output=True, check=True, timeout=30
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return [root / n for n in done.stdout.decode("utf-8").split("\0") if n]


def _candidates(root: Path) -> tuple[list[Path], set[Path]]:
    """(what git would commit under `root`: tracked, or untracked and not ignored; the tracked ones). Every file when
    git cannot say."""
    listed = _git_list(root, "--cached", "--others", "--exclude-standard")
    if listed:
        return sorted(p for p in listed if p.is_file()), set(_git_list(root, "--cached") or [])
    everything = sorted(p for p in root.rglob("*") if p.is_file())
    return everything, set(everything)


def _scan_files(root: Path = DEMO) -> list[Path]:
    """EVERY candidate file, whatever its content: a NUL byte or a binary header does not exempt it. Only caches are
    skipped, and the untracked top-level working folder `work/` (a tracked file there IS scanned)."""
    files, tracked = _candidates(root)
    out = []
    for p in files:
        rel = p.relative_to(root)
        if set(rel.parts) & SKIP_DIRS:
            continue
        if rel.parts[0] in SKIP_TOP and p not in tracked:
            continue
        out.append(p)
    return out


def _read(p: Path) -> str:
    """Decoding that hides nothing. UTF-16 when it starts with a BOM. Otherwise NUL bytes are removed (a planted NUL
    must not split a literal) and the rest must be UTF-8; a file with a known binary header that is not UTF-8 is read
    as Latin-1 so printable runs inside it are still matched. Anything else that cannot be decoded FAILS the scan."""
    raw = p.read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    raw = raw.replace(b"\0", b"")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        if raw.startswith(BINARY_MAGIC):
            return raw.decode("latin-1")
        raise


def _line_of(text: str, pos: int) -> str:
    start = text.rfind("\n", 0, pos) + 1
    end = text.find("\n", pos)
    return text[start : end if end != -1 else len(text)].strip()


def _hits(
    files: list[Path] | None = None, root: Path = DEMO
) -> dict[tuple[str, str], list[tuple[str, str]]]:
    found: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for p in files if files is not None else _scan_files():
        rel = p.relative_to(root).as_posix() if root in p.parents else p.name
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


def test_every_file_is_scanned_whatever_its_name_or_content(tmp_path):
    """Planted in a folder with no git: a `.pem`, a `.bak`, a name with no suffix, a `.venv` folder, a text file with a
    NUL byte in it, a NUL inside the literal itself, a UTF-16 file and a PNG-headed file are all read."""
    secret = "sk-ant-" + "api03-" + "Z" * 40
    names = (
        "deploy.pem",
        "README.md.bak",
        "notes",
        "id_rsa",
        ".venv/leak.txt",
        "sub/dir/x.weird",
        "work/leak.txt",
    )
    for name in names:
        f = tmp_path / name
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(f"token = {secret}\n", encoding="utf-8")
    (tmp_path / "zero.txt").write_bytes(f"token = {secret}\n".encode() + b"\0")
    (tmp_path / "split.txt").write_bytes(
        b"token = " + secret.encode()[:12] + b"\0" + secret.encode()[12:]
    )
    (tmp_path / "wide.txt").write_bytes(f"token = {secret}\n".encode("utf-16"))
    (tmp_path / "image.bin").write_bytes(b"\x89PNG\0\0\xff " + secret.encode())
    found = {p.relative_to(tmp_path).as_posix() for p in _scan_files(tmp_path)}
    assert found == {
        *names,
        "zero.txt",
        "split.txt",
        "wide.txt",
        "image.bin",
    }  # no git here: work/ is scanned too
    flagged = {k[0] for k in _hits(_scan_files(tmp_path), tmp_path)}
    assert found == flagged  # and every one of them is reported


def test_a_tracked_file_under_work_is_scanned_and_an_untracked_one_is_not(tmp_path):
    if shutil.which("git") is None:
        pytest.skip("git is not installed")
    subprocess.run([GIT, "init", "-q"], cwd=tmp_path, check=True, timeout=30)  # noqa: S603
    (tmp_path / "work").mkdir()
    (tmp_path / "work" / "tracked.txt").write_text("x\n", encoding="utf-8")
    (tmp_path / "work" / "scratch.txt").write_text("x\n", encoding="utf-8")
    (tmp_path / "plain.txt").write_text("x\n", encoding="utf-8")
    subprocess.run([GIT, "add", "work/tracked.txt"], cwd=tmp_path, check=True, timeout=30)  # noqa: S603
    found = {p.relative_to(tmp_path).as_posix() for p in _scan_files(tmp_path)}
    assert found == {"work/tracked.txt", "plain.txt"}


def test_an_undecodable_file_without_a_known_binary_header_fails_the_scan(tmp_path):
    f = tmp_path / "mystery"
    f.write_bytes(b"\xff\xfe\xfd text")
    f.write_bytes(b"abc \xfd\xfd")
    with pytest.raises(UnicodeDecodeError):
        _read(f)


def test_the_real_tree_is_scanned_by_what_git_would_commit():
    names = {p.relative_to(DEMO).as_posix() for p in _scan_files()}
    assert {"README.md", "askdata/sealed.py", "db/roles.sql", "askdata.example.yaml"} <= names
    assert not any(n.startswith(("work/", ".git/")) or "__pycache__" in n for n in names)


@pytest.mark.parametrize(
    "region",
    [
        "japan" + "east",
        "canada" + "central",
        "australia" + "southeast",
        "brazil" + "south",
        "korea" + "central",
        "france" + "central",
        "germany" + "westcentral",
        "sweden" + "central",
        "south" + "india",
        "central" + "india",
        "east" + "asia",
        "north" + "europe",
        "uk" + "west",
        "me" + "-west1",
        "africa" + "-south1",
        "west" + "us3",
        "south" + "central" + "us",
    ],
)
def test_the_region_scan_catches_azure_country_style_and_other_gcp_names(region):
    assert PATTERNS["region literal"].search(f"location = '{region}'"), region


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
    "private key block": [
        "-----BEGIN PRIVATE KEY-----",
        "-----BEGIN RSA PRIVATE KEY-----",
        "-----BEGIN OPENSSH PRIVATE KEY-----",
    ],
    "password in a URL (DSN)": [
        "postgresql://ro:hunter2hunter2@localhost:5432/db",
        "postgres://ro:hunter2hunter2@10.1.2.3/db",
    ][:2],
    "password or secret assignment": [
        "password = 'Tr0ub4dor&3xyz'",
        'api_key: "abcdefgh12345678"',
        '{"token": "abcdefgh12345678"}',
    ],
    "JWT": ["eyJhbGciOiJIUzI1NiJ9." + "eyJzdWIiOiIxMjM0NTY3ODkwIn0." + "dozjgNryP4J3jVmNHl0w5N"],
    "bearer token": [
        "Authorization: Bearer abcdefghijklmnop",
        "'authorization': 'bearer abcdefghijklmnop12'",
    ],
    "Slack webhook": [
        "https://hooks.slack.com/services/T0" + "0000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
    ],
    "Stripe key": ["sk_live_" + "a" * 24, "rk_test_" + "b" * 20],
}
PLANTED["region literal"] += [
    "us" + "-east-1a",
    "US" + "-EAST-1",
    "eu" + "_west_1",
    "us" + "-iso-east-1",
    "jioindia" + "west",
    "usgov" + "virginia",
    "austria" + "east",
    "Japan" + "East",
]
PLANTED["model id literal"] += [
    "gemini" + "-pro",
    "Claude" + "-Opus",
    "claude" + "_3_opus",
    "GPT" + "-4o",
]


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
# 0, 1 and -1 are fine as indexes and flags but NOT where a number is a tunable: named like one, or given to a
# call that waits.
TUNABLE = re.compile(
    r"(?i)(timeout|retr(y|ies)|limit|delay|wait|attempt|interval|backoff|ttl|max_|min_|budget|poll|deadline|sleep|period|window|threshold)"
)
WAIT_CALLS = {"sleep", "join", "wait", "wait_for", "settimeout", "communicate", "result"}
ENV_GETTERS = {"os.environ.get", "environ.get", "os.getenv", "getenv"}
NUMERIC_TEXT = re.compile(r"\s*-?\d+([./]\d+)?\s*")
DURATION_TEXT = re.compile(r"\s*\d+(\.\d+)?\s*(ms|s|sec|m|min|h|hr|d)\s*")
NUMBER_CALLS = {"int", "float", "Decimal", "Fraction"}


def _is_number(c: ast.AST) -> bool:
    return (
        isinstance(c, ast.Constant)
        and isinstance(c.value, int | float)
        and not isinstance(c.value, bool)
    )


def _is_numeric_text(c: ast.AST) -> bool:
    return (
        isinstance(c, ast.Constant)
        and isinstance(c.value, str)
        and bool(NUMERIC_TEXT.fullmatch(c.value))
    )


SCHEMA_BOUNDS = {
    "min_length",
    "max_length",
    "min_items",
    "max_items",
}  # pydantic validators, not tunables


def _direct_small(node: ast.AST | None) -> bool:
    """`x = 0`, `x = -1`, `x: int = 1`: the value IS the small number (a Field(gt=0) bound is not)."""
    if isinstance(node, ast.UnaryOp):
        node = node.operand
    return _is_number(node) and node.value in OK_SMALL  # type: ignore[union-attr]


def _small_in(node: ast.AST | None) -> list[int]:
    """Line numbers of the 0 / 1 / -1 constants inside `node`."""
    if node is None:
        return []
    return [c.lineno for c in ast.walk(node) if _is_number(c) and c.value in OK_SMALL]  # type: ignore[attr-defined]


def _small_operands(node: ast.AST) -> list[int]:
    """0 / 1 / -1 / True anywhere in an argument of a waiting call (`sleep(x + 1)`, `join(timeout=1)`), but not inside a
    subscript (`names[0]` is an index)."""
    out: list[int] = []
    stack = [node]
    while stack:
        cur = stack.pop()
        if (
            not isinstance(
                cur,
                ast.BinOp
                | ast.UnaryOp
                | ast.BoolOp
                | ast.IfExp
                | ast.Constant
                | ast.operator
                | ast.unaryop
                | ast.boolop,
            )
            and cur is not node
        ):
            continue  # only the arithmetic of the argument: not calls, subscripts or comprehensions inside it
        if (
            isinstance(cur, ast.Constant)
            and isinstance(cur.value, int | float)
            and cur.value in OK_SMALL
        ):
            out.append(cur.lineno)
        stack.extend(ast.iter_child_nodes(cur))
    return out


def _import_aliases(tree: ast.AST) -> dict[str, str]:
    """`from decimal import Decimal as D` -> {"D": "Decimal"}; `import decimal as d` -> {"d": "decimal"}."""
    out: dict[str, str] = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom | ast.Import):
            for a in n.names:
                if a.asname:
                    out[a.asname] = a.name
    return out


def numeric_lines(path: Path) -> list[str]:
    """The stripped source line of EVERY numeric constant in the module (defaults, assignments in function bodies,
    returns, slices, expressions, arguments of any call, keyword arguments, comparisons: all of it) except 0, 1, -1;
    plus numeric strings given to int/float/Decimal/Fraction (under any import alias) or as an environment default;
    plus numeric or duration strings assigned to a tunable-named target; plus 0, 1, -1 in a tunable context.
    One entry per source LINE that holds one, so two identical lines count twice."""
    src = path.read_text(encoding="utf-8")
    lines = src.splitlines()
    tree = ast.parse(src)
    aliases = _import_aliases(tree)
    hit: set[int] = set()
    for n in ast.walk(tree):
        if _is_number(n) and n.value not in OK_SMALL:  # type: ignore[attr-defined]
            hit.add(n.lineno)  # type: ignore[attr-defined]
        if isinstance(n, ast.Call):
            full = ast.unparse(n.func)
            last = aliases.get(full.rsplit(".", 1)[-1], full.rsplit(".", 1)[-1])
            if last in NUMBER_CALLS:
                for arg in n.args[:1]:
                    for sub_node in ast.walk(arg):  # also `int(os.environ["N"] or "77")`
                        if _is_numeric_text(sub_node) and sub_node.value.strip() not in {
                            "0",
                            "1",
                            "-1",
                        }:  # type: ignore[attr-defined]
                            hit.add(sub_node.lineno)
            if full in ENV_GETTERS:
                defaults = [*n.args[1:2], *(k.value for k in n.keywords if k.arg == "default")]
                hit.update(d.lineno for d in defaults if _is_numeric_text(d))
            if last in WAIT_CALLS:
                for arg in n.args:
                    hit.update(_small_operands(arg))
            if last == "timedelta":
                for kw in n.keywords:
                    hit.update(_small_in(kw.value))
            for kw in n.keywords:
                if kw.arg and kw.arg not in SCHEMA_BOUNDS and TUNABLE.search(kw.arg):
                    hit.update(_small_in(kw.value))
        elif isinstance(n, ast.Assign | ast.AnnAssign | ast.AugAssign):
            targets = n.targets if isinstance(n, ast.Assign) else [n.target]
            if any(TUNABLE.search(ast.unparse(tg)) for tg in targets):
                if _direct_small(n.value):
                    hit.add(n.value.lineno)  # type: ignore[union-attr]
                elif (
                    isinstance(n.value, ast.Constant)
                    and isinstance(n.value.value, str)
                    and (
                        NUMERIC_TEXT.fullmatch(n.value.value)
                        or DURATION_TEXT.fullmatch(n.value.value)
                    )
                ):
                    hit.add(n.value.lineno)
        elif isinstance(n, ast.arguments):
            pos = [*n.posonlyargs, *n.args]
            pairs = list(zip(pos[len(pos) - len(n.defaults) :], n.defaults, strict=True))
            pairs += [(a, d) for a, d in zip(n.kwonlyargs, n.kw_defaults, strict=True) if d]
            for arg, default in pairs:
                if TUNABLE.search(arg.arg):
                    hit.update(_small_in(default))
    return [lines[i - 1].strip() for i in sorted(hit)]


def excess(found: list[str], allowed: list[str]) -> list[str]:
    """Lines found more often than they are allowlisted (a second identical line is NEW)."""
    return sorted((Counter(found) - Counter(allowed)).elements())


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
    new = {k: excess(v, ALLOWLIST.get(k, {}).get("lines", [])) for k, v in found.items()}
    new = {k: v for k, v in new.items() if v}
    assert new == {}, f"numbers outside settings.py on lines not in numeric_allowlist.json: {new}"
    unused = {
        k: excess(v["lines"], found.get(k, []))
        for k, v in ALLOWLIST.items()
        if excess(v["lines"], found.get(k, []))
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
    allowed = ALLOWLIST["askdata/pipeline.py"]["lines"]
    p = tmp_path / "pipeline.py"
    p.write_text("time.sleep(2)\n", encoding="utf-8")
    assert excess(numeric_lines(p), allowed) == [
        "time.sleep(2)"
    ]  # the old value-set allowlist let this pass


def test_the_scan_reads_subpackages_and_top_level_files():
    names = set(_modules())
    assert {"askdata/sealed.py", "data/goldcheck.py", "db/build_verify.py"} <= names
    assert not any(n.startswith("work/") for n in names)


PLANTED_NUMBERS = [
    'x = int("300")',
    'x = float("1.5")',
    'x = os.environ.get("X", "900")',
    'x = os.getenv("X", "900")',
    "time.sleep(1)",
    "time.sleep(0)",
    "thread.join(1)",
    "event.wait(0)",
    "retries = 1",
    "self.max_attempts = 0",
    "poll_interval: float = 1",
    "def f(timeout=1): ...",
    "def f(*, retry_limit=0): ...",
    "queue.get(timeout=1)",
    "call(a, backoff=-1)",
    "return 4",
    "from decimal import Decimal as D\nx = D('0.05')",
    "import decimal as dd\nx = dd.Decimal('0.05')",
    "from fractions import Fraction\nx = Fraction('1/3')",
    'TIMEOUT = "45"',
    'x_delay = "30s"',
    'x = int(os.environ["N"] or "77")',
    'x = os.environ.get("N", default="77")',
    "time.sleep(a_var + 1)",
    "time.sleep(True)",
    "from datetime import timedelta\nx = timedelta(seconds=1)",
]


@pytest.mark.parametrize("line", PLANTED_NUMBERS)
def test_the_numeric_scan_catches_each_planted_number(line, tmp_path):
    p = tmp_path / "x.py"
    p.write_text(line.replace(": ...", ": pass") + "\n", encoding="utf-8")
    assert numeric_lines(p), line


@pytest.mark.parametrize(
    "line",
    [
        "x = 0",
        "i = 1",
        "n = -1",
        "a = items[0]",
        "y = int('0')",
        "z = os.environ.get('X', 'a')",
        "time.sleep(delay)",
        "first = rows[1]",
    ],
)
def test_the_numeric_scan_leaves_alone_what_is_not_a_tunable(line, tmp_path):
    p = tmp_path / "x.py"
    p.write_text(line + "\n", encoding="utf-8")
    assert numeric_lines(p) == [], line


def test_a_second_identical_line_is_counted_as_new_not_swallowed_by_the_first(tmp_path):
    p = tmp_path / "cli.py"
    p.write_text("def a():\n    return 4\ndef b():\n    return 4\n", encoding="utf-8")
    assert numeric_lines(p) == ["return 4", "return 4"]
    assert excess(numeric_lines(p), ["return 4"]) == ["return 4"]  # one allowlisted, two present
    assert (
        excess(["return 4"], ["return 4", "return 4"]) == []
    )  # extra allowlisted lines are caught by `unused`
