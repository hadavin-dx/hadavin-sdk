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
        ("AKIA" + "ABCDEFGHIJKLMNOP", "key"),
        ("sk-" + "a" * 30, "key"),
        ("ghp_" + "A1" * 20, "key"),
        ("Zq9Lm2Xk7Rp4Vb8N" * 3, "long-secret-shape"),
        ("123456789012", "account-id"),
        ("arn:aws:iam::123456789012:role/x", "arn"),
        ("https://kubernetes.default.svc", "url"),
        ("https://api.internal.example.com/v1", "url"),
        ("db.prod.corp", "host"),
        ("billing-db.internal", "host"),
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
