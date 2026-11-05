"""Scope of the CSV sink (spec 4, I2). A CONVENTION CHECK over our own files, NOT a proof of I2 (the proof of what reaches the file is test_exporter and
test_exporter_history). Scope: only the exporter imports ``csvsink``; the cell guard is reached only through the sink and the exporter; nothing
else in the product code names or opens the CSV file. A convention check over our own files (the file can still be edited by hand)."""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "intake"


def importers(module: str) -> set[str]:
    found = set()
    for p in SRC.rglob("*.py"):
        if "core_copy" in p.parts:
            continue
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom):
                names = {a.name for a in n.names}
                if (n.module or "").split(".")[-1] == module or (n.level and not n.module and module in names):
                    found.add(p.name)
            elif isinstance(n, ast.Import):
                if any(a.name.split(".")[-1] == module for a in n.names):
                    found.add(p.name)
    return found


def test_the_exporter_writes_no_queue_sql():
    """The exporter stores through ``workqueue`` only (record_export, accessors): no ``execute`` call, no ``sqlite3.connect``, no SQL keyword in a string."""
    tree = ast.parse((SRC / "exporter.py").read_text(encoding="utf-8"))
    calls = {n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert not calls & {"execute", "executemany", "executescript", "connect", "cursor"}, calls
    words = ("INSERT INTO", "UPDATE ", "DELETE FROM", "SELECT ", "PRAGMA")
    strings = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    docstring_free = [
        x for x in strings if len(x) < 400
    ]  # module and function docstrings are longer prose; SQL statements here would be short
    assert not [x for x in docstring_free if any(w in x for w in words)], docstring_free


def test_only_exporter_imports_csvsink():
    assert importers("csvsink") == {"exporter.py"}


def test_sink_guard_is_reached_only_by_the_sink_and_the_exporter():
    assert importers("sink_guard") == {"csvsink.py", "exporter.py"}


def test_only_the_sink_and_the_exporter_know_the_csv_file_name():
    names = {p.name for p in SRC.rglob("*.py") if "invoices.csv" in p.read_text(encoding="utf-8") and "core_copy" not in p.parts}
    assert names <= {"exporter.py", "csvsink.py", "sink_guard.py"}, names


def test_only_the_sink_uses_the_csv_writer_and_os_replace():
    writers, replacers = set(), set()
    for p in SRC.rglob("*.py"):
        if "core_copy" in p.parts:
            continue
        src = p.read_text(encoding="utf-8")
        if "csv.writer" in src or "DictWriter" in src:
            writers.add(p.name)
        if "os.replace" in src:
            replacers.add(p.name)
    assert writers == {"csvsink.py"} and replacers <= {"csvsink.py"}, (writers, replacers)
