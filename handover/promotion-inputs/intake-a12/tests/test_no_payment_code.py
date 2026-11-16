"""I3: no payment calls in the files the intake work adds. An AST scan (not a text search) of every .py under src/intake, tools/ and demo_only/ except the
existing files in tests/fixtures/payment_scan_exclude.txt. A scan plus a denylist, not a proof; the untouched order-flow files are out of scope.

Zones: STRICT = src/intake (also bans process, native-code, dynamic-import and extra network modules, with per-file allowances).
TOOLS = tools/*.py and demo_only/** (bans the network and process modules except as the per-file table permits)."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from conftest import ROOT
from intake.executor import FORBIDDEN

EXCLUDE_FILE = ROOT / "tests" / "fixtures" / "payment_scan_exclude.txt"
PAYMENT_SDKS = frozenset(
    "stripe paypal paypalrestsdk paypalcheckoutsdk braintree adyen razorpay squareup square mollie gocardless dwolla plaid paddle authorizenet "
    "checkout_sdk klarna worldpay payu mercadopago midtrans flutterwave paystack transferwise".split()
)
BUILTIN_CALLS = frozenset({"eval", "exec", "compile"})  # an ast.Name call; re.compile is an attribute call and is allowed
STRICT_BANNED = (
    "subprocess ctypes ftplib importlib http.client asyncio multiprocessing runpy pty webbrowser imaplib poplib telnetlib".split()
)
OS_BANNED = re.compile(r"^os\.(system|popen|spawn\w*|exec\w*)$")
# module -> the only src/intake file names that may import it (full module names, not prefixes)
STRICT_ONLY_IN = {
    "urllib.request": {"model_anthropic.py"},
    "ssl": {"model_anthropic.py"},
    "http.server": {"service.py", "lockfile.py"},
    "socket": {"service.py", "lockfile.py"},
    "hmac": {"service.py", "lockfile.py"},
    "msvcrt": {"service.py", "lockfile.py"},
    "fcntl": {"service.py", "lockfile.py"},
    "smtplib": {"notify.py"},
}
TOOLS_BANNED = ("urllib.request", "socket", "ssl", "subprocess")
# path prefix or file -> modules allowed there (the per-file table of the spec)
TOOLS_ALLOWED = {
    "tools/n8n_setup.py": {"urllib.request", "subprocess"},
    "demo_only/e2e/n8n_stub.py": {"socket"},
    "demo_only/e2e/": {"urllib.request", "subprocess"},
    "demo_only/video/": {"subprocess"},
}


def _is(mod: str, banned: str) -> bool:
    return mod == banned or mod.startswith(banned + ".")


def _dotted(node: ast.AST) -> str | None:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def zone(rel: str) -> str | None:
    if rel.startswith("src/intake/"):
        return "strict"
    if rel.startswith(("demo_only/", "tools/")):  # every depth: tools/<subdir>/x.py is scanned like tools/x.py
        return "tools"
    return None


def scan_source(source: str, rel: str) -> list[str]:
    """Findings for one file (rel = repo-relative posix path). Empty = clean."""
    z = zone(rel)
    tree = ast.parse(source)
    base = rel.rsplit("/", 1)[-1]
    found: list[str] = []
    alias: dict[str, str] = {}
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                mods.add(a.name)
                alias[a.asname or a.name.split(".")[0]] = a.name if a.asname else a.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom) and not node.level:
            m = node.module or ""
            mods.add(m)
            for a in node.names:
                mods.add(f"{m}.{a.name}")
                alias[a.asname or a.name] = f"{m}.{a.name}"
    chains: set[str] = set()
    for node in ast.walk(tree):
        d = _dotted(node) if isinstance(node, ast.Attribute) else None
        if d:
            head, _, rest = d.partition(".")
            chains.add(f"{alias.get(head, head)}.{rest}")
    seen = mods | chains
    for m in sorted(mods):
        if m.split(".")[0] in PAYMENT_SDKS:
            found.append(f"payment SDK import: {m}")
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            name = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else ""
            low = name.lower()
            if any(f in low for f in FORBIDDEN):
                found.append(f"call named like a forbidden class: {name} (line {node.lineno})")
            if isinstance(fn, ast.Name) and fn.id in BUILTIN_CALLS:
                found.append(f"builtin call {fn.id} (line {node.lineno})")
            if z == "strict" and isinstance(fn, ast.Name) and fn.id == "__import__":
                found.append(f"__import__ call (line {node.lineno})")
    if z == "strict":
        for m in sorted(seen):
            if OS_BANNED.match(m):
                found.append(f"banned os call: {m}")
            for b in STRICT_BANNED:
                if _is(m, b):
                    found.append(f"banned module in src/intake: {m}")
            for b, only in STRICT_ONLY_IN.items():
                if _is(m, b) and base not in only:
                    found.append(f"{m} only in {sorted(only)}")
    elif z == "tools":
        allowed = set().union(*(v for k, v in TOOLS_ALLOWED.items() if rel == k or (k.endswith("/") and rel.startswith(k))))
        for m in sorted(seen):
            for b in TOOLS_BANNED:
                if _is(m, b) and b not in allowed:
                    found.append(f"{m} not allowed in {rel}")
            if OS_BANNED.match(m):
                found.append(f"banned os call: {m}")
    return sorted(set(found))


def excluded(rel: str, patterns: list[str]) -> bool:
    return any(rel.startswith(p[:-2]) if p.endswith("/**") else rel == p for p in patterns)


def exclude_patterns() -> list[str]:
    return [ln.strip() for ln in EXCLUDE_FILE.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")]


def scan_repo() -> dict[str, list[str]]:
    pats = exclude_patterns()
    out = {}
    for base in ("src/intake", "tools", "demo_only"):
        root = ROOT / base
        if not root.is_dir():  # demo_only is absent in the cut job
            continue
        for p in sorted(root.rglob("*.py")):
            rel = p.relative_to(ROOT).as_posix()
            if "__pycache__" in p.parts or excluded(rel, pats) or zone(rel) is None:
                continue
            f = scan_source(p.read_text(encoding="utf-8"), rel)
            if f:
                out[rel] = f
    return out


def test_no_payment_code_in_the_intake_files():
    assert scan_repo() == {}


def test_the_exclude_list_names_only_existing_files_or_prefixes():
    for pat in exclude_patterns():
        target = ROOT / pat[:-3] if pat.endswith("/**") else ROOT / pat
        if "demo_only" in pat and not (ROOT / "demo_only").is_dir():
            continue  # the cut job deletes the demo-only folder
        assert target.exists(), pat


# ---- positive controls: the scanner must flag each of these ---------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "src,rel",
    [
        ("import stripe\n", "src/intake/x.py"),
        ("from stripe import Charge\n", "tools/x.py"),
        ("import adyen.client\n", "demo_only/x/y.py"),
        ("release_payment(1)\n", "src/intake/x.py"),
        ("client.payment_create(1)\n", "tools/x.py"),
        ("obj.change_credential()\n", "src/intake/x.py"),
        ("x = erp_write\nerp_write(1)\n", "src/intake/x.py"),
        ("eval('1')\n", "src/intake/x.py"),
        ("exec('1')\n", "tools/x.py"),
        ("compile('1', 'x', 'eval')\n", "demo_only/a.py"),
        ("__import__('os')\n", "src/intake/x.py"),
        ("import subprocess\n", "src/intake/x.py"),
        ("from subprocess import run\n", "src/intake/x.py"),
        ("import os\nos.system('x')\n", "src/intake/x.py"),
        ("import os as o\no.popen('x')\n", "src/intake/x.py"),
        ("import os\nos.spawnl(1)\n", "src/intake/x.py"),
        ("from os import execv\n", "src/intake/x.py"),
        ("import ctypes\n", "src/intake/x.py"),
        ("import importlib\n", "src/intake/x.py"),
        ("from importlib import import_module\n", "src/intake/x.py"),
        ("import http.client\n", "src/intake/x.py"),
        ("from http import client\n", "src/intake/x.py"),
        ("import asyncio\n", "src/intake/x.py"),
        ("import urllib.request\n", "src/intake/budget.py"),
        ("from urllib import request\n", "src/intake/budget.py"),
        ("import urllib\nurllib.request.urlopen('x')\n", "src/intake/budget.py"),
        ("import ssl\n", "src/intake/model.py"),
        ("import socket\n", "src/intake/model_anthropic.py"),
        ("import http.server\n", "src/intake/pipeline.py"),
        ("import hmac\n", "src/intake/exporter.py"),
        ("import smtplib\n", "src/intake/service.py"),
        ("import urllib.request\n", "tools/other.py"),
        ("import socket\n", "tools/make_secrets.py"),
        ("import subprocess\n", "demo_only/tools/prepare_fake_env.py"),
        ("import urllib.request\n", "demo_only/video/record.py"),
        ("import ssl\n", "demo_only/e2e/test_x.py"),
    ],
)
def test_scanner_flags(src, rel):
    assert scan_source(src, rel), (src, rel)


@pytest.mark.parametrize(
    "src,rel",
    [
        ("import re\nre.compile('x')\n", "src/intake/x.py"),
        ("import os\nos.path.join('a')\n", "src/intake/x.py"),
        ("import urllib.parse\nimport json\n", "src/intake/x.py"),
        ("import urllib.request\nimport ssl\n", "src/intake/model_anthropic.py"),
        ("import http.server, socket, hmac, msvcrt\n", "src/intake/service.py"),
        ("import socket, fcntl\n", "src/intake/lockfile.py"),
        ("import smtplib\n", "src/intake/notify.py"),
        ("import urllib.request, subprocess\n", "tools/n8n_setup.py"),
        ("import http.server, socket\n", "demo_only/e2e/n8n_stub.py"),
        ("import urllib.request, subprocess\n", "demo_only/e2e/test_x.py"),
        ("import subprocess\n", "demo_only/video/record.py"),
        ("import json\n", "demo_only/tools/prepare_fake_env.py"),
        ("def payee():\n    pass\npayee()\n", "src/intake/x.py"),
    ],
)
def test_scanner_allows(src, rel):
    assert scan_source(src, rel) == [], (src, rel)


def test_scanner_reports_syntax_errors_loudly():
    with pytest.raises(SyntaxError):
        scan_source("def (:\n", "src/intake/x.py")


def test_scan_covers_the_files_this_work_adds():
    pats = exclude_patterns()
    for rel in ("src/intake/settings.py", "src/intake/secret_store.py", "tools/make_secrets.py", "src/intake/cli.py"):
        assert (ROOT / rel).is_file() and not excluded(rel, pats), rel
    assert Path(EXCLUDE_FILE).is_file()


@pytest.mark.parametrize("src", ["import socket\n", "import subprocess\n", "import stripe\n", "eval('1')\n"])
def test_scanner_covers_nested_tools_folders(src):
    assert scan_source(src, "tools/sub/deeper/x.py"), src
