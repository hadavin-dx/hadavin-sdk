"""Class: a reader or writer of a file named by a person (or by a setting) must not wait for ever on a named pipe
(FIFO). `lead_desk.regfile` is the one way in; the read path of tools/pathconfine.py refuses a pipe, a device or a
socket as the last part of a path too. One case per tool of load_tools/ and demo_only/, each in a child process with a
5 second limit; the answer is the tool's own fixed refusal or its safe default. Made-up data only, no network."""

from __future__ import annotations

import ast
import multiprocessing
import os
import sys
from pathlib import Path
from queue import Empty
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[1]
FIFO_SKIP = pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="no named pipes on this platform")
TOOL_FILES = [
    *sorted((REPO / "load_tools").glob("*.py")),
    REPO / "demo_only" / "fake_model_server.py",
    REPO / "demo_only" / "fakes.py",
    REPO / "demo_only" / "portal_demo.py",
]


def _outcome(case: str, path: str, queue: Any) -> None:
    """Runs in a child process: use `path` (a pipe) in one tool; put "ok|<answer>" or "Kind|text"."""
    sys.path.insert(0, str(REPO))
    sys.path.insert(0, str(REPO / "src"))
    p = Path(path)
    try:
        if case == "pathconfine_read":
            from tools.pathconfine import PathRefused, confine_anywhere, confine_existing

            answers = []
            for fn in (confine_existing, confine_anywhere):
                try:
                    fn(p, what="--x")
                except PathRefused as e:
                    answers.append(str(e))
            queue.put("ok|" + " ## ".join(answers))
            return
        if case == "invariants_live":
            from load_tools import check_invariants as ci

            queue.put(f"ok|{ci._facts_say_live(p)}")
            return
        if case.startswith("invariants_"):
            from load_tools import check_invariants as ci

            fn = {
                "jsonl": ci.read_jsonl,
                "crm": ci.read_crm,
                "facts": ci._intended,
                "drain": ci._drain_marker,
            }[case.split("_", 1)[1]]
            fn(p)
        elif case == "catcher_control":
            from load_tools.catcher import read_mode

            queue.put(f"ok|{read_mode(p)}")
            return
        elif case == "catcher_out":
            from load_tools.catcher import Catcher

            Catcher(p, p.parent / "none")._write({"a": 1})
        elif case == "driver_kernel":
            from load_tools.load_driver import _read_int

            queue.put(f"ok|{_read_int(str(p))}")
            return
        elif case == "model_control":
            from demo_only.fake_model_server import ModelState

            queue.put(f"ok|{ModelState('ok', None, None, p).current_mode()}")
            return
        elif case == "fakes_replies":
            from demo_only.fakes import RecordedQualifier

            RecordedQualifier(p)
        elif case == "portal_armed":
            from demo_only.portal_demo import PortalDemo
            from lead_desk.hooks import FlagFileHooks

            queue.put(f"ok|{PortalDemo._armed(None, FlagFileHooks(p))}")  # type: ignore[arg-type]
            return
        queue.put("ok|accepted")
    except Exception as e:  # report every kind of failure to the parent
        queue.put(type(e).__name__ + "|" + str(e))


def _in_child(case: str, path: Path) -> str:
    ctx = multiprocessing.get_context("spawn")
    queue = ctx.Queue()
    child = ctx.Process(target=_outcome, args=(case, str(path), queue))
    child.start()
    try:
        return str(queue.get(timeout=5))
    except Empty:
        pytest.fail(f"{case} waited for ever (or took over 5 seconds) on a named pipe")
    finally:
        child.terminate()
        child.join(10)


@pytest.fixture
def pipe(tmp_path: Path) -> Path:
    p = tmp_path / "pipe-name"
    os.mkfifo(p)
    return p


@FIFO_SKIP
def test_the_read_path_of_pathconfine_refuses_a_pipe_as_the_last_part(pipe: Path) -> None:
    out = _in_child("pathconfine_read", pipe)
    assert out.count("is not a regular file") == 2, out
    assert "pipe-name" not in out


@FIFO_SKIP
@pytest.mark.parametrize("case", ["invariants_jsonl", "invariants_crm", "invariants_facts", "invariants_drain"])
def test_the_invariants_checker_refuses_a_pipe_at_once(pipe: Path, case: str) -> None:
    kind, _, text = _in_child(case, pipe).partition("|")
    # r7 split the bad-path refusal into PathInputError (a subclass of InputError, exit 4); pin the exact class
    assert kind == "PathInputError", (kind, text)
    assert "is not a regular file" in text
    assert "pipe-name" not in text


@FIFO_SKIP
def test_the_invariants_checker_counts_a_pipe_as_live_facts_closed(pipe: Path) -> None:
    assert _in_child("invariants_live", pipe) == "ok|True"  # fail closed: an unreadable facts file counts as live


@FIFO_SKIP
def test_the_catcher_reads_no_mode_from_a_pipe_and_writes_nothing_to_one(pipe: Path) -> None:
    assert _in_child("catcher_control", pipe) == "ok|('ok', 0.0)"
    kind, _, text = _in_child("catcher_out", pipe).partition("|")
    assert kind == "NotRegularFile" and "pipe-name" not in text


@FIFO_SKIP
def test_the_load_driver_reads_no_number_from_a_pipe(pipe: Path) -> None:
    assert _in_child("driver_kernel", pipe) == "ok|unreadable"


@FIFO_SKIP
def test_the_model_stand_in_reads_no_mode_from_a_pipe(pipe: Path) -> None:
    assert _in_child("model_control", pipe) == "ok|ok"


@FIFO_SKIP
def test_the_recorded_replies_file_as_a_pipe_is_refused(pipe: Path) -> None:
    kind, _, text = _in_child("fakes_replies", pipe).partition("|")
    assert kind == "NotRegularFile" and "pipe-name" not in text


@FIFO_SKIP
def test_the_portal_demo_reads_no_armed_point_from_a_pipe(pipe: Path) -> None:
    assert _in_child("portal_armed", pipe) == "ok|None"


def _plain_file_calls(path: Path) -> list[str]:
    """Calls in `path` that read or write a file by name without regfile: Path.read_text/read_bytes/write_text/
    write_bytes, open(), and X.open() unless X is a URL opener."""
    found = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if isinstance(f, ast.Attribute) and f.attr in ("read_text", "read_bytes", "write_text", "write_bytes"):
            found.append(f"{path.name}:{node.lineno} .{f.attr}()")
        elif isinstance(f, ast.Name) and f.id == "open":
            found.append(f"{path.name}:{node.lineno} open()")
        elif isinstance(f, ast.Attribute) and f.attr == "open" and "opener" not in ast.unparse(f.value).lower():
            found.append(f"{path.name}:{node.lineno} .open()")
    return found


def test_no_tool_or_fake_reads_or_writes_a_named_file_outside_regfile() -> None:
    """The class check behind the cases above: the files named by a person or a setting go through regfile."""
    found = [hit for f in TOOL_FILES for hit in _plain_file_calls(f)]
    assert found == [], found
