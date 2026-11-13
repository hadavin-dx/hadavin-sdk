"""No hardcoded environment in `src/` (owner rule, K5 review): no key-shaped strings, no account ids, no ARNs with an
account, and no host names or URLs, except in the files that are the home of a vendor endpoint (a kind module) or a
pattern for FINDING such text (the redactor), or a protocol identifier that only looks like a host. Endpoints,
ports, timeouts, caps, retention and the stored redaction kinds are config, manifest or settings fields whose
defaults live in `hadavin_sdk/defaults.py`.

Scanning is over string constants (AST), docstrings included, so a literal cannot hide in a comment-like string.
Fake credentials in tests are built from parts; AWS's documented example key is the only literal allowed.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
AWS_DOC_KEY = "AKIA" + "IOSFODNN7EXAMPLE"  # the one literal allowed anywhere (AWS documentation)

PATTERNS = {
    "key": re.compile(
        r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b|\bsk-[A-Za-z0-9_-]{20,}|\bgh[pousr]_[A-Za-z0-9]{20,}"
        r"|\bxox[baprs]-[A-Za-z0-9-]{10,}|\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
    ),
    "long-secret-shape": re.compile(
        r"(?<![A-Za-z0-9+/_=-])(?=[A-Za-z0-9+/=_-]*[A-Z])(?=[A-Za-z0-9+/=_-]*[a-z])"
        r"(?=[A-Za-z0-9+/=_-]*\d)[A-Za-z0-9+/_-]{32,}"
    ),
    "account-id": re.compile(r"(?<![\d./-])\d{12}(?![\d./-])"),
    "arn": re.compile(r"arn:aws[\w-]*:[\w-]*:[\w-]*:\d{12}:"),
    "url": re.compile(r"https?://[a-z0-9][^\s\"'`)>\]]*", re.IGNORECASE),
    "host": re.compile(
        r"(?<![\w.@/-])(?:[a-z0-9][a-z0-9-]*\.)+"
        r"(?:com|net|org|io|dev|ai|cloud|internal|local|svc|corp|lan)\b",
        re.IGNORECASE,
    ),
}

# file (relative to src/hadavin_sdk) -> kinds of finding it may hold, and why.
ALLOWED: dict[str, tuple[set[str], str]] = {
    "backends/table.py": (
        {"url", "host"},
        "the one table of vendor endpoints per kind (hosts() feeds egress.yaml)",
    ),
    "approvals/slack_channel.py": ({"url"}, "the Slack kind's own API base"),
    "llm/anthropic.py": ({"url"}, "the Anthropic and Vertex kind's endpoints"),
    "llm/gemini.py": ({"url"}, "the Gemini kind's endpoint"),
    "tools.py": (
        {"host"},
        "the deny-list of loopback and metadata names a manifest host may not be",
    ),
    "sources/kubernetes.py": (
        {"host"},
        (
            "Kubernetes API group and annotation names (authorization.k8s.io, deployment.kubernetes.io), "
            "protocol identifiers and not hosts"
        ),
    ),
}


def findings(src: Path, allowed: dict[str, tuple[set[str], str]]) -> list[str]:
    out = []
    for path in sorted(src.rglob("*.py")):
        rel = (
            path.relative_to(src / "hadavin_sdk").as_posix()
            if (src / "hadavin_sdk") in path.parents
            else path.name
        )
        ok = allowed.get(rel, (set(), ""))[0]
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
                continue
            text = node.value.replace(AWS_DOC_KEY, "")
            for kind, rx in PATTERNS.items():
                if kind in ok:
                    continue
                out += [
                    f"{rel}:{node.lineno}: {kind}: {m.group(0)[:60]}" for m in rx.finditer(text)
                ]
    return out


def test_no_key_account_arn_or_host_literal_in_src():
    assert findings(SRC, ALLOWED) == []


def test_every_allowed_file_exists_and_still_needs_its_entry():
    for rel, (kinds, reason) in ALLOWED.items():
        assert (SRC / "hadavin_sdk" / rel).is_file(), rel
        assert reason
        trimmed = {**ALLOWED, rel: (set(), reason)}
        assert findings(SRC, trimmed), f"{rel} no longer holds {sorted(kinds)}: delete the entry"


def _plant(tmp_path: Path, text: str) -> Path:
    pkg = tmp_path / "hadavin_sdk"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "bad.py").write_text(f"X = {text!r}\n", encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        pytest.param(*("AKIA" + "ABCDEFGHIJKLMNOP", "key"), id="plant-key-aws"),
        pytest.param(*("sk-" + "a" * 30, "key"), id="plant-key-sk"),
        pytest.param(*("ghp_" + "A1" * 20, "key"), id="plant-key-ghp"),
        pytest.param(*("Zq9Lm2Xk7Rp4Vb8N" * 3, "long-secret-shape"), id="plant-long-secret"),
        pytest.param(*("123456789012", "account-id"), id="plant-account-id"),
        pytest.param(*("arn:aws:iam::123456789012:role/x", "arn"), id="plant-arn"),
        pytest.param(*("https://kubernetes.default.svc", "url"), id="plant-url-k8s"),
        pytest.param(*("https://api.internal.example.com/v1", "url"), id="plant-url-internal"),
        pytest.param(*("db.prod.corp", "host"), id="plant-host-prod"),
        pytest.param(*("billing-db.internal", "host"), id="plant-host-billing"),
    ],
)
def test_plant_a_hardcoded_value_is_caught(tmp_path, text, kind):
    found = findings(_plant(tmp_path, text), {})
    assert any(f": {kind}: " in f for f in found), (text, found)


def test_the_aws_documentation_key_is_the_one_allowed_literal(tmp_path):
    assert findings(_plant(tmp_path, f"key {AWS_DOC_KEY}"), {}) == []


def test_ordinary_text_is_not_flagged(tmp_path):
    for text in (
        "us-east-1 is not read here",
        "a.b",
        "version 1.2.3",
        "pods/exec",
        "tool_timeout_s",
    ):
        assert findings(_plant(tmp_path, text), {}) == [], text


K5_FILES = (
    "tools.py",
    "app.py",
    "config.py",
    "guard/runmap.py",
    "runtime/agent_loop.py",
    "runtime/evidence.py",
    "runtime/tick.py",
    "sources/__init__.py",
    "sources/kubernetes.py",
)


def test_defaults_live_in_one_module():
    """The numbers of the read path are written once, in defaults.py, and everything else names them."""
    text = "".join((SRC / "hadavin_sdk" / f).read_text(encoding="utf-8") for f in K5_FILES)
    for literal in ("2 * 1024 * 1024", "20_000", "= 65536", "9093, 3100", "= 16384", "86400"):
        assert literal not in text, f"{literal} is written outside defaults.py"


_KEY_SHAPES = (
    re.compile(r"A[KS]IA[0-9A-Z]{16}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9]"),
    re.compile(r"BEGIN [A-Z ]*KEY"),
)
_LONG_RUN = re.compile(r"[A-Za-z0-9]{28,}")


def _shapes_of(text: str) -> list[str]:
    """Which secret shapes ``text`` has: ``key`` (key-shaped or a long mixed run), ``account-number`` (12 digits), ``arn``."""
    shapes = []
    bare = text.replace(AWS_DOC_KEY, "")
    if any(shape.search(bare) for shape in _KEY_SHAPES) or any(
        len(set(run)) >= 8 for run in _LONG_RUN.findall(bare)
    ):
        shapes.append("key")
    if PATTERNS["account-id"].search(text):
        shapes.append("account-number")
    if PATTERNS["arn"].search(text):
        shapes.append("arn")
    return shapes


def _fold(node: ast.AST) -> str | None:
    """The text a literal expression builds (a constant, ``a + b``, ``a * 3``), or None for anything else."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp):
        left, right = _fold(node.left), _fold(node.right)
        if isinstance(node.op, ast.Add) and left is not None and right is not None:
            return left + right
        if isinstance(node.op, ast.Mult) and left is not None:
            count = node.right.value if isinstance(node.right, ast.Constant) else None
            return left * count if isinstance(count, int) and 0 <= count < 10_000 else None
    return None


def _is_param_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "param"
    )


def _literals(node: ast.AST):
    """Every literal text under ``node`` that pytest would print in a test id: not inside ``pytest.param(..., id=...)``."""
    if _is_param_call(node) and any(k.arg == "id" for k in node.keywords):
        return
    text = _fold(node)
    if text is not None:
        yield node.lineno, text
        return
    for child in ast.iter_child_nodes(node):
        yield from _literals(child)


def key_shaped_test_ids(root: Path) -> list[str]:
    """``file:line: shape`` for each parametrize in ``root`` that has no ``ids=`` and a literal value of a secret shape
    (never the text itself). Values that come from a variable or a function call are not seen by this scan."""
    hits = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            is_parametrize = (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "parametrize"
                and len(node.args) >= 2
            )
            if not is_parametrize or any(k.arg == "ids" for k in node.keywords):
                continue
            for line, text in _literals(node.args[1]):
                hits += [f"{path.relative_to(root)}:{line}: {shape}" for shape in _shapes_of(text)]
    return hits


def test_no_literal_parameter_of_a_secret_shape_is_printed_in_a_test_name():
    """pytest prints a parameter value as part of the test name, so a planted fake key, account number or ARN in a parameter
    list lands in logs and reports. Every such parameter needs an explicit readable ``ids=`` or ``pytest.param(id=)``."""
    hits = key_shaped_test_ids(Path(__file__).parent)
    assert hits == [], f"{len(hits)} parameters would be printed: {hits[:8]}"


def test_control_the_scan_sees_a_planted_value_and_ignores_one_with_an_id(tmp_path):
    parts = "AKIA" + "ABCDEFGHIJKLMNOP"
    planted = f'import pytest\n\n@pytest.mark.parametrize("v", [("{parts}")])\ndef test_x(v): ...\n'
    (tmp_path / "test_a.py").write_text(planted, encoding="utf-8")
    assert key_shaped_test_ids(tmp_path) == ["test_a.py:3: key"]
    (tmp_path / "test_a.py").write_text(
        planted.replace('[("', '[pytest.param("').replace('")]', '", id="plant")]'),
        encoding="utf-8",
    )
    assert key_shaped_test_ids(tmp_path) == []
    (tmp_path / "test_a.py").write_text(planted.replace("]", '], ids=["plant"]'), encoding="utf-8")
    assert key_shaped_test_ids(tmp_path) == []
