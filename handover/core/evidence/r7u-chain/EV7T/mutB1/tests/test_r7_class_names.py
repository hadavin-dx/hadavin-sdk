"""F10 (round 7): where a class name of an error may be used. A name such as KeyError, URLError or a vendor's class
tells a person nothing and may name a product or a place. Every use of `type(x).__name__` (and `x.__class__.__name__`,
`__qualname__`) in scripts, tools, load_tools, demo_only and src is found by an ast walk and must be on the list below
with its reason; a new use fails this test until someone writes the reason. The three uses that STORE a code for a
person go through `error_code` (src/lead_desk/errcode.py)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from lead_desk.errcode import error_code

REPO = Path(__file__).resolve().parents[1]
FOLDERS = ("scripts", "tools", "load_tools", "demo_only", "src")

LOG = "operator log line: the class name only, never the text; the log is for the operator, not shown to a person"
INNER = (
    "the text of an adapter error (SendRefused, CrmError ...): it is never stored or printed; the desk records its own "
    "fixed words (refused, unreachable, ambiguous) or error_code(); only the operator log may show it"
)
TRACE = (
    "the operator timing file (stage, times, outcome): a class name, no text; read by the load tools, not by a person"
)

# file -> reason for every use in that file (the reason covers the file; the log/raise check below enforces the shape)
ALLOWED = {
    "src/lead_desk/desk.py": LOG,
    "src/lead_desk/server.py": LOG,
    "src/lead_desk/portal_api.py": LOG,
    "src/lead_desk/trace.py": TRACE,
    "src/lead_desk/smtp_provider.py": INNER,
    "src/lead_desk/smtp_outbox.py": INNER,
    "src/lead_desk/adapters.py": INNER,
    "src/lead_desk/crm_hubspot.py": INNER,
}
SAFE_PARENTS = {"warning", "info", "error", "exception", "debug"}  # log.warning(...) and the like


def _uses(path: Path) -> list[tuple[int, str]]:
    """(line, kind) of every read of a class name (`type(x).__name__`): kind is "log", "raise", "assign" or "other"."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    parents = {id(c): n for n in ast.walk(tree) for c in ast.iter_child_nodes(n)}
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Attribute) and node.attr in {"__name__", "__qualname__"}):
            continue
        inner = node.value
        is_type_call = isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name) and inner.func.id == "type"
        is_class_attr = isinstance(inner, ast.Attribute) and inner.attr == "__class__"
        if not (is_type_call or is_class_attr):
            continue
        up: ast.AST | None = parents.get(id(node))
        kind = "other"
        while up is not None:
            if isinstance(up, ast.Call) and isinstance(up.func, ast.Attribute) and up.func.attr in SAFE_PARENTS:
                kind = "log"
                break
            if isinstance(up, ast.Raise):
                kind = "raise"
                break
            if isinstance(up, ast.Assign | ast.AnnAssign):
                kind = "assign"
                break
            if isinstance(up, ast.JoinedStr | ast.FormattedValue | ast.Call | ast.Tuple | ast.Compare | ast.BoolOp):
                up = parents.get(id(up))
                continue
            break
        found.append((node.lineno, kind))
    return found


def _all_uses() -> dict[str, list[tuple[int, str]]]:
    out: dict[str, list[tuple[int, str]]] = {}
    for folder in FOLDERS:
        for p in sorted((REPO / folder).rglob("*.py")):
            if "__pycache__" in p.parts:
                continue
            uses = _uses(p)
            if uses:
                out[p.relative_to(REPO).as_posix()] = uses
    return out


def test_every_use_of_a_class_name_is_on_the_list_with_its_reason() -> None:
    uses = _all_uses()
    unknown = {f: u for f, u in uses.items() if f not in ALLOWED}
    assert not unknown, f"a class name is used in a file with no written reason: {unknown}"
    stale = [f for f in ALLOWED if f not in uses]
    assert not stale, f"the list names files that no longer use a class name: {stale}"


def test_the_shape_of_each_use_matches_its_reason() -> None:
    """A log file may only log or raise an inner class name; the only "assign" is the trace outcome; nothing else."""
    for f, uses in _all_uses().items():
        for line, kind in uses:
            if ALLOWED[f] == LOG:
                assert kind == "log", f"{f}:{line} is a {kind} use in a file that is allowed to log only"
            elif ALLOWED[f] == INNER:
                assert kind == "raise", f"{f}:{line} is a {kind} use in a file that is allowed to raise only"
            else:
                assert (f, kind) == ("src/lead_desk/trace.py", "assign")


def test_desk_log_files_keep_their_class_names_out_of_stored_text() -> None:
    """Both files of the desk that LOG class names have no `internal:` code built from one: the stored codes use
    error_code (the old shape f"internal:{type(e).__name__}" is gone)."""
    for f in ("src/lead_desk/desk.py", "src/lead_desk/server.py"):
        text = (REPO / f).read_text(encoding="utf-8")
        assert 'f"internal:{type(' not in text and "internal:{type(" not in text
    assert "error_code(" in (REPO / "src/lead_desk/desk.py").read_text(encoding="utf-8")


class Mine(Exception):
    __module__ = "lead_desk.somewhere"


@pytest.mark.parametrize(
    ("exc", "want"),
    [
        (KeyError("x"), "data"),
        (ValueError("x"), "data"),
        (LookupError("x"), "data"),
        (IndexError("x"), "error"),  # a subclass of LookupError is NOT "data": the ranking pins the three exact classes
        (OSError("x"), "error"),
        (TimeoutError("x"), "error"),
        (Mine("x"), "Mine"),
    ],
)
def test_error_code_gives_the_class_name_only_for_this_package(exc: BaseException, want: str) -> None:
    assert error_code(exc) == want


def test_a_foreign_class_name_never_becomes_a_stored_code() -> None:
    import http.client
    import urllib.error

    for exc in (urllib.error.URLError("secret-host.test"), http.client.IncompleteRead(b""), ConnectionResetError("p")):
        assert error_code(exc) == "error"
