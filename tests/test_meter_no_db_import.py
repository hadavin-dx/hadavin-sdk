"""P4b1-a T4: the meter imports no database library, only an allow-listed set of modules, and holds no stray number."""

import ast
import subprocess
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src" / "hadavin_sdk"
FILES = ("meter.py", "money.py")  # llm/metered.py joins with P4b1-b (BLOCKED on P4a)
# `collections` (collections.abc, type annotations only) is one addition to the ticket's list; recorded in the evidence.
ALLOWED = {
    "contextlib", "contextvars", "dataclasses", "datetime", "decimal", "logging", "re", "threading", "time",
    "typing", "__future__", "hadavin_sdk", "collections",
}  # fmt: skip
ALLOWED_FIRST_PARTY = {
    "hadavin_sdk.models", "hadavin_sdk.defaults", "hadavin_sdk.money", "hadavin_sdk.store.protocol",
    "hadavin_sdk.store", "hadavin_sdk",
}  # fmt: skip
FORBIDDEN = ("psycopg", "sqlite3", "boto3")


def imported_modules(source):
    """Every imported module name, including lazy ones inside functions and string literals given to import_module."""
    found = []
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            found.append(base)
            found += [f"{base}.{a.name}" for a in node.names if base.startswith("hadavin_sdk")]
        elif isinstance(node, ast.Call):
            f = node.func
            name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
            if name in {"import_module", "__import__"} and node.args:
                arg = node.args[0]
                found.append(
                    arg.value
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
                    else "<dynamic>"
                )
    return found


def violations(source):
    bad = []
    for mod in imported_modules(source):
        top = mod.split(".")[0]
        if mod == "<dynamic>" or top in FORBIDDEN:
            bad.append(mod)
        elif top == "hadavin_sdk":
            known = mod in ALLOWED_FIRST_PARTY or mod.startswith("hadavin_sdk.store.protocol")
            if not known and mod.rsplit(".", 1)[0] not in ALLOWED_FIRST_PARTY:
                bad.append(mod)
        elif top not in ALLOWED:
            bad.append(mod)
    return bad


def number_literals(source):
    return [
        n.value
        for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.Constant)
        and type(n.value) in (int, float, complex)
        and n.value not in (0, 1)
    ] + [
        n.operand.value
        for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.UnaryOp)
        and isinstance(n.op, ast.USub)
        and isinstance(n.operand, ast.Constant)
        and n.operand.value not in (1,)
        and type(n.operand.value) in (int, float)
        and n.operand.value != 0
    ]


def test_t4_1_a_clean_interpreter_imports_the_meter_without_a_database_library():
    code = (
        "import sys, hadavin_sdk.meter, hadavin_sdk.money, hadavin_sdk.limits;"
        "print(sorted(m for m in ('psycopg','sqlite3','boto3') if m in sys.modules))"
    )
    root = Path(__file__).resolve().parents[1] / "src"
    out = subprocess.run(  # noqa: S603 - this interpreter, a fixed script
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
        env={"PYTHONPATH": str(root)},
    )
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "[]"


@pytest.mark.parametrize("name", FILES)
def test_t4_2_only_allow_listed_imports(name):
    assert violations((SRC / name).read_text()) == []


@pytest.mark.parametrize(
    "line",
    [
        "import psycopg",
        "from psycopg import sql",
        "import sqlite3 as s",
        "def f():\n    import psycopg\n",
        "import importlib\nimportlib.import_module('psycopg')",
        "import importlib\nimportlib.import_module(name)",
        "__import__('boto3')",
        "import requests",
    ],
)
def test_t4_3_a_planted_import_is_caught(line):
    clean = (SRC / "meter.py").read_text()
    assert violations(clean + "\n" + line + "\n") != []


@pytest.mark.parametrize("name", FILES)
def test_t4_4_no_numeric_literal_but_0_1_minus1(name):
    assert number_literals((SRC / name).read_text()) == []


@pytest.mark.parametrize("planted", ["x = 2", "x = 1_000", "x = 0.5", "x = -2", "x = 10**6"])
def test_t4_4_scan_catches_a_planted_number(planted):
    assert number_literals((SRC / "meter.py").read_text() + "\n" + planted + "\n") != []
