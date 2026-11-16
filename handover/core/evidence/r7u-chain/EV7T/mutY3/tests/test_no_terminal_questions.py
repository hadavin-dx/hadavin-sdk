"""Class: a script that asks a question with input() must meet a closed standard input (a pipe, a scheduled job, a
test) with one plain line and a fixed exit code, never an EOFError traceback, and an unanswered question is never a yes.
Made-up data only, no network, nothing is called."""

from __future__ import annotations

import ast
import io
import multiprocessing
import os
import runpy
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

from support import run_program, text_file

REPO = Path(__file__).resolve().parents[1]
ROOTS = ("scripts", "load_tools", "demo_only", "tools", "src")


def _live_args(tmp: Path) -> list[str]:
    # the key file is checked before the "no terminal" line (R4-10), so it must be a real key file: made up here
    (tmp / "k").write_text("made-up-key-" + "x" * 12 + "\n", encoding="utf-8")
    return [
        *("--key-file", str(tmp / "k")),
        *("--ledger", str(tmp / "ledger.jsonl")),
        *("--base-url", "http://127.0.0.1:1"),
        *("--cap-run", "1", "--cap-total", "3"),
        *("--price-date", "2026-01-01", "--model", "m-a=1,2", "--effort", "low"),
    ]


def _run_live_check(args: list[str], cwd: str, queue: Any) -> None:
    """Runs in a child process with a closed standard input: put "code|everything printed" on the queue."""
    sys.path.insert(0, str(REPO / "src"))
    sys.path.insert(0, str(REPO / "scripts"))
    os.chdir(cwd)
    sys.argv = ["run_live_check.py", *args]
    sys.stdin = open(os.devnull, encoding="utf-8")  # no terminal: input() meets the end of the input at once
    out, err = io.StringIO(), io.StringIO()
    code: object = 0
    try:
        with redirect_stdout(out), redirect_stderr(err):
            runpy.run_path(str(REPO / "scripts" / "run_live_check.py"), run_name="__main__")
    except SystemExit as e:
        code = e.code
    except BaseException as e:  # a traceback is the failure this test is for: report it
        code = "raised " + type(e).__name__
    queue.put(f"{code}|{out.getvalue()}|{err.getvalue()}")


def test_the_live_check_meets_a_closed_input_with_one_plain_line(tmp_path: Path) -> None:
    ctx = multiprocessing.get_context("spawn")
    queue = ctx.Queue()
    child = ctx.Process(target=_run_live_check, args=(_live_args(tmp_path), str(tmp_path), queue))
    child.start()
    try:
        code, out, err = str(queue.get(timeout=60)).split("|", 2)
    finally:
        child.join(10)
    assert code == "6", (code, out, err)  # EXIT_STOPPED: the person (here: nobody) said no
    assert err == "" and "Traceback" not in out
    # ONE line: the cost lines and the question are not printed when nobody can answer
    assert out.splitlines() == ["stopped, nothing was called: there is no terminal to answer the question on"], out
    assert not (tmp_path / "ledger.jsonl").exists()  # nothing was reserved or written


def _inputs_without_eof_guard(path: Path) -> list[int]:
    """Line numbers of input() calls that no enclosing try/except EOFError covers."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    parents: dict[ast.AST, ast.AST] = {c: p for p in ast.walk(tree) for c in ast.iter_child_nodes(p)}
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "input":
            cur: ast.AST = node
            guarded = False
            while cur in parents:
                par = parents[cur]
                if isinstance(par, ast.Try) and cur in par.body:
                    names = {ast.unparse(h.type) for h in par.handlers if h.type is not None}
                    guarded = guarded or any("EOFError" in n for n in names)
                cur = par
            if not guarded:
                bad.append(node.lineno)
    return bad


def test_every_input_call_of_the_repository_handles_a_closed_input() -> None:
    bad = {}
    seen = 0
    for root in ROOTS:
        for py in sorted((REPO / root).rglob("*.py")):
            if "input(" in py.read_text(encoding="utf-8"):
                seen += 1
                if lines := _inputs_without_eof_guard(py):
                    bad[str(py.relative_to(REPO))] = lines
    assert seen >= 2  # the two check scripts ask a question: the scan finds them
    assert bad == {}, bad


def test_the_live_check_refuses_a_huge_lead_count_in_one_line_and_builds_nothing(tmp_path: Path) -> None:
    import subprocess

    base = [sys.executable, str(REPO / "scripts" / "run_live_check.py"), *_live_args(tmp_path)]
    for flag in ("--leads", "--runs"):
        for huge in ("99999999999999999999", "1001", "0", "-1"):
            r = run_program(
                [*base, flag, huge], capture_output=True, text=True, timeout=20, stdin=subprocess.DEVNULL, check=False
            )
            assert r.returncode == 2, (flag, huge, r.returncode, r.stderr[-200:])
            assert len(r.stdout.splitlines()) == 1 and r.stderr == "" and (huge[:4] not in r.stdout or len(huge) < 4), (
                flag,
                huge,
                r.stdout,
            )
    assert not (tmp_path / "ledger.jsonl").exists()


def test_the_live_check_with_a_closed_descriptor_prints_one_line(tmp_path: Path) -> None:

    code = (
        "import os, sys, runpy; os.close(0); sys.argv = sys.argv[1:]; runpy.run_path(sys.argv[0], run_name='__main__')"
    )
    r = run_program(
        [sys.executable, text_file(code), str(REPO / "scripts" / "run_live_check.py"), *_live_args(tmp_path)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert r.returncode == 6 and r.stderr == "" and len(r.stdout.splitlines()) == 1, (r.returncode, r.stdout, r.stderr)
