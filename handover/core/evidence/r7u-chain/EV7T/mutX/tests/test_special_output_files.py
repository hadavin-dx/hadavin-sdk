"""Class F6a: a file the desk or a script WRITES to (a lock file, the spend ledger, the trace file, the counters file, a
result file, a log) must be a regular file or be refused at once. A named pipe (FIFO), a link to one, or a folder under
that name used to make the writer wait for ever or end with a traceback. A name that does not exist yet must still be
created. Made-up data only, no network.

Every site runs in a child process with a 5 second limit: a writer that waits on the pipe is a failure (the child is
killed and the test fails). The library sites are called directly, the command line tools run through runpy in the
child (no new process of their own, so no subprocess call)."""

from __future__ import annotations

import importlib
import io
import multiprocessing
import os
import runpy
import stat
import sys
from collections.abc import Callable
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from queue import Empty
from typing import Any

import pytest

from lead_desk.desk import book_problem

REPO = Path(__file__).resolve().parents[1]
LIMIT_SECONDS = 5
FIFO_SKIP = pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="no named pipes on this platform")
KINDS = ("pipe", "link-to-pipe", "folder")
NOT_A_FILE_BOOK_PROBLEM = (
    "the lead book path names a pipe, a device or a folder: it must be a regular file or a new name"
)


def make_special(kind: str, path: Path) -> None:
    """Create a pipe, a link to a pipe, or a folder at `path`."""
    if kind == "pipe":
        os.mkfifo(path)
    elif kind == "link-to-pipe":
        real = path.with_name(path.name + ".real-pipe")
        os.mkfifo(real)
        path.symlink_to(real)
    else:
        path.mkdir()


# ---------------------------------------------------------------- the child-process runner
def _child(fn: Callable[[str], str], arg: str, queue: Any) -> None:
    try:
        queue.put(fn(arg))
    except BaseException as e:  # the child reports whatever happened, it never raises
        queue.put(f"{type(e).__name__}|{e}")


def in_child(fn: Callable[[str], str], arg: str) -> str:
    """Run fn(arg) in a child process; the answer is the string it returns, or "KindName|text" when it raised. A child
    that has not answered after LIMIT_SECONDS is killed and the test fails."""
    if "fork" not in multiprocessing.get_all_start_methods():  # the local functions of these tests need fork
        pytest.skip("no fork on this platform")
    ctx = multiprocessing.get_context("fork")
    queue = ctx.Queue()
    child = ctx.Process(target=_child, args=(fn, arg, queue), daemon=True)
    child.start()
    try:
        return str(queue.get(timeout=LIMIT_SECONDS))
    except Empty:
        pytest.fail(f"{fn.__name__} waited for ever (more than {LIMIT_SECONDS} s) on a pipe or a folder")
    finally:
        child.terminate()
        child.join(10)


def run_script(script: Path, *args: str) -> Callable[[str], str]:
    """A function for in_child that runs a command line tool in the child and answers 'CODE|all text it printed'."""

    def go(_: str) -> str:
        sys.argv = [str(script), *args]
        sys.path.insert(0, str(REPO))
        sys.path.insert(0, str(REPO / "src"))
        out = io.StringIO()
        code: object = 0
        with redirect_stdout(out), redirect_stderr(out):
            try:
                runpy.run_path(str(script), run_name="__main__")
            except SystemExit as e:
                code = e.code
        return f"{code}|{out.getvalue()}"

    go.__name__ = "run_" + script.stem
    return go


# ---------------------------------------------------------------- library sites
def _lock(path: str) -> str:
    from lead_desk import lockfile

    lockfile.acquire(Path(path))  # the lock file is "<path>.lock"
    return "ACCEPTED"


def _ledger_lock(path: str) -> str:
    from lead_desk.live_claude import _FileLock

    with _FileLock(Path(path)):
        return "ACCEPTED"


def _ledger_append(path: str) -> str:
    from lead_desk.live_claude import SpendLedger

    SpendLedger(Path(path))._append({"op": "reserve", "id": "x", "usd": "0.01"})
    return "ACCEPTED"


def _trace(path: str) -> str:
    from lead_desk.trace import Tracer

    t = Tracer(Path(path))
    t.event("e1", "stage", 1, 2)
    return f"RETURNED|failures={t.write_failures}"


def _stats(path: str) -> str:
    from lead_desk.run_stats import write_stats

    write_stats(Path(path), {"a": 1})
    return f"RETURNED|created={os.path.lexists(path)}"


def _model_log(path: str) -> str:
    import importlib

    state = importlib.import_module("demo_only.fake_model_server").ModelState(call_log=Path(path))
    state.log_call({"messages": [{"content": "x"}]}, "ok", 200)
    return "ACCEPTED"


LEDGER_LOCK_TEXT = "LiveCapReached|the spend ledger lock file cannot be opened: check the ledger folder"
LEDGER_WRITE_TEXT = "LiveCapReached|the spend ledger cannot be written: check the disk and the ledger file"
SITES: dict[str, tuple[Callable[[str], str], str, str]] = {
    # name: (function, what is added to the name for the place of the special file, the answer that is wanted)
    "lock": (_lock, ".lock", "LockUnavailableError|cannot open the lock file: not a regular file"),
    "ledger-lock": (_ledger_lock, "", LEDGER_LOCK_TEXT),
    "ledger-append": (_ledger_append, "", LEDGER_WRITE_TEXT),
    "trace": (_trace, "", "RETURNED|failures=1"),
    "stats": (_stats, ".tmp", "RETURNED|created=False"),
    "model-log": (_model_log, "", "NotRegularFile|not a regular file"),
}


# FIX TEST for 10 of its 23 cases (r7e review m1, run on the frozen tree): FAILS on the frozen tree for lock-pipe,
# lock-link-to-pipe, lock-folder, model-log-pipe, model-log-link-to-pipe, model-log-folder, stats-pipe,
# stats-link-to-pipe, trace-pipe, trace-link-to-pipe (frozen says 'cannot open the lock file: UnsupportedOperation',
# the test wants 'not a regular file'); the other 13 cases pass on the frozen tree (CONTROL). No mutant run.
@FIFO_SKIP
@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("site", sorted(SITES))
def test_a_writer_refuses_a_pipe_a_link_to_a_pipe_and_a_folder_at_once(tmp_path: Path, site: str, kind: str) -> None:
    fn, suffix, want = SITES[site]
    make_special(kind, tmp_path / ("name" + suffix))
    answer = in_child(fn, str(tmp_path / "name"))
    assert answer == want, answer
    assert str(tmp_path) not in answer


@FIFO_SKIP
def test_the_special_file_is_left_as_it_was(tmp_path: Path) -> None:
    os.mkfifo(tmp_path / "p")
    assert in_child(_trace, str(tmp_path / "p")) == "RETURNED|failures=1"
    assert stat.S_ISFIFO(os.lstat(tmp_path / "p").st_mode)


# ---------------------------------------------------------------- the helper itself
def test_open_output_creates_a_missing_file_and_appends_to_it(tmp_path: Path) -> None:
    from lead_desk.regfile import open_output

    path = tmp_path / "new.log"
    with open_output(path, "a", encoding="utf-8") as f:
        f.write("one\n")
    with open_output(path, "a", encoding="utf-8") as f:
        f.write("two\n")
    assert path.read_text(encoding="utf-8") == "one\ntwo\n"
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o666 & ~_umask()


def _umask() -> int:
    old = os.umask(0)
    os.umask(old)
    return old


def test_open_output_binary_append_reads_and_writes_at_the_end(tmp_path: Path) -> None:
    from lead_desk.regfile import open_output

    path = tmp_path / "ledger"
    path.write_bytes(b"abc\n")
    with open_output(path, "a+b") as f:
        assert f.seek(0, 2) == 4
        f.seek(0)
        assert f.read() == b"abc\n"
        f.write(b"def\n")
    assert path.read_bytes() == b"abc\ndef\n"


def test_open_output_w_empties_a_regular_file_only(tmp_path: Path) -> None:
    from lead_desk.regfile import open_output

    path = tmp_path / "out.json"
    path.write_text("old old old", encoding="utf-8")
    with open_output(path, "w", encoding="utf-8") as f:
        f.write("new")
    assert path.read_text(encoding="utf-8") == "new"


def test_open_output_follows_a_link_to_a_regular_file(tmp_path: Path) -> None:
    from lead_desk.regfile import open_output

    real = tmp_path / "real"
    real.write_text("x", encoding="utf-8")
    (tmp_path / "link").symlink_to(real)
    with open_output(tmp_path / "link", "a", encoding="utf-8") as f:
        f.write("y")
    assert real.read_text(encoding="utf-8") == "xy"


@FIFO_SKIP
@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("mode", ["a", "a+b", "w"])
def test_open_output_refuses_every_special_kind_in_every_mode(tmp_path: Path, kind: str, mode: str) -> None:
    def go(path: str) -> str:
        from lead_desk.regfile import NotRegularFile, open_output

        try:
            open_output(path, mode, encoding="utf-8" if "b" not in mode else None)
        except NotRegularFile as e:
            return f"NotRegularFile|{e}"
        return "ACCEPTED"

    make_special(kind, tmp_path / "x")
    assert in_child(go, str(tmp_path / "x")) == "NotRegularFile|not a regular file"


def test_open_output_refuses_a_nul_character_and_a_wrong_mode(tmp_path: Path) -> None:
    from lead_desk.regfile import NotRegularFile, open_output

    with pytest.raises(NotRegularFile):
        open_output(str(tmp_path / "a\x00b"))
    with pytest.raises(ValueError, match="mode must be"):
        open_output(tmp_path / "f", "r")
    assert not (tmp_path / "f").exists()


def test_open_output_a_missing_folder_is_still_an_ordinary_oserror(tmp_path: Path) -> None:
    from lead_desk.regfile import NotRegularFile, open_output

    with pytest.raises(FileNotFoundError) as caught:
        open_output(tmp_path / "no-such-folder" / "f")
    assert not isinstance(caught.value, NotRegularFile)


@FIFO_SKIP
def test_a_regular_file_is_not_cut_when_the_name_was_a_pipe_check_fails(tmp_path: Path) -> None:
    """The file is emptied only after the kind is known: a link to a pipe leaves the pipe alone, a regular file named
    in "w" mode loses its old text (the old behaviour)."""
    from lead_desk.regfile import NotRegularFile, open_output

    os.mkfifo(tmp_path / "p")
    (tmp_path / "l").symlink_to(tmp_path / "p")
    with pytest.raises(NotRegularFile):
        open_output(tmp_path / "l", "w", encoding="utf-8")
    assert stat.S_ISFIFO(os.stat(tmp_path / "p").st_mode)


# ---------------------------------------------------------------- command line tools and the path check
@FIFO_SKIP
@pytest.mark.parametrize("kind", ["pipe", "link-to-pipe"])
def test_confine_refuses_an_existing_pipe_for_a_written_file_and_keeps_new_names(tmp_path: Path, kind: str) -> None:
    from tools.pathconfine import PathRefused, confine, confine_existing

    make_special(kind, tmp_path / "out")
    with pytest.raises(PathRefused, match="--out: is not a regular file"):
        confine(tmp_path / "out", what="--out", roots=[tmp_path])
    assert confine(tmp_path / "fresh.log", what="--out", roots=[tmp_path]) == tmp_path.resolve() / "fresh.log"
    (tmp_path / "plain").write_text("x", encoding="utf-8")
    assert confine(tmp_path / "plain", what="--out", roots=[tmp_path]) == tmp_path.resolve() / "plain"
    assert confine_existing(tmp_path / "plain", what="--in", roots=[tmp_path]) == tmp_path.resolve() / "plain"


def _answer_is_one_refusal(answer: str, code: str, starts: str) -> None:
    got, _, text = answer.partition("|")
    assert got == code, answer
    assert "Traceback" not in text, text
    assert text.strip().splitlines()[0].startswith(starts), text


@FIFO_SKIP
@pytest.mark.parametrize("kind", ["pipe", "link-to-pipe"])
def test_scrub_catcher_and_burst_driver_refuse_a_pipe_as_their_output(tmp_path: Path, kind: str) -> None:
    (tmp_path / "in.json").write_text('{"name": "w", "nodes": []}', encoding="utf-8")
    make_special(kind, tmp_path / "out")
    scrub = run_script(REPO / "tools" / "scrub_n8n_export.py", str(tmp_path / "in.json"), str(tmp_path / "out"))
    _answer_is_one_refusal(in_child(scrub, ""), "2", "refused: out.json: is not a regular file")
    catcher = run_script(REPO / "load_tools" / "catcher.py", "--out", str(tmp_path / "out"), "--port", "0")
    _answer_is_one_refusal(in_child(catcher, ""), "4", "refused: --out: is not a regular file")
    driver = run_script(
        REPO / "load_tools" / "load_driver.py",
        *("--base-url", "http://127.0.0.1:9", "--scenario", "burst:1", "--log", str(tmp_path / "out")),
    )
    _answer_is_one_refusal(in_child(driver, ""), "4", "ERROR: --log: is not a regular file")


@FIFO_SKIP
def test_burst_driver_refuses_a_pipe_left_under_a_part_file_name(tmp_path: Path) -> None:
    os.mkfifo(tmp_path / "burst.log.part0")
    driver = run_script(
        REPO / "load_tools" / "load_driver.py",
        *(
            "--base-url",
            "http://127.0.0.1:9",
            "--scenario",
            "burst:1",
            "--log",
            str(tmp_path / "burst.log"),
            "--workers",
            "1",
        ),
    )
    _answer_is_one_refusal(in_child(driver, ""), "4", "ERROR: --log: is not a regular file")
    assert not (tmp_path / "burst.log").exists() and not (tmp_path / "burst.log.facts.json").exists()


@FIFO_SKIP
def test_invariant_checker_refuses_a_pipe_as_its_json_output(tmp_path: Path) -> None:
    def go(path: str) -> str:
        sys.path.insert(0, str(REPO))
        sys.path.insert(0, str(REPO / "load_tools"))
        import check_invariants as c

        try:
            c._confined(path, "--json", output=True)
        except c.InputError as e:
            return f"InputError|{e}"
        return "ACCEPTED"

    os.mkfifo(tmp_path / "j")
    assert (
        in_child(go, str(tmp_path / "j"))
        == "InputError|--json: is not a regular file (a pipe, a device or a socket would block): give a file"
    )


@FIFO_SKIP
@pytest.mark.parametrize("flag", ["--call-log", "--key-file"])
def test_fake_model_server_refuses_a_pipe_for_its_files_before_it_starts(tmp_path: Path, flag: str) -> None:
    # a plain import: a broken module fails this test, it is not skipped
    assert importlib.import_module("demo_only.fake_model_server") is not None

    os.mkfifo(tmp_path / "p")
    script = REPO / "demo_only" / "fake_model_server.py"
    answer = in_child(run_script(script, flag, str(tmp_path / "p"), "--port", "0"), "")
    # a pipe named for either option is refused by the path check (tools/pathconfine.py: its read path refuses a pipe,
    # a device or a socket as the last part, like its write path) with its own line, before any open
    _answer_is_one_refusal(answer, "4", f"refused: {flag}: is not a regular file")


# ---------------------------------------------------------------- the lead book itself
@FIFO_SKIP
@pytest.mark.parametrize("kind", KINDS)
def test_the_desk_refuses_a_pipe_or_a_folder_as_its_lead_book_before_it_takes_the_lock(
    tmp_path: Path, kind: str
) -> None:
    def go(path: str) -> str:
        from lead_desk.server import main

        os.environ["DESK_DB_PATH"] = path
        out = io.StringIO()
        code: object = 0
        with redirect_stdout(out), redirect_stderr(out):
            try:
                main()
            except SystemExit as e:
                code = e.code
        return f"{code}|{out.getvalue().strip()}"

    make_special(kind, tmp_path / "book")
    answer = in_child(go, str(tmp_path / "book"))
    code, _, text = answer.partition("|")
    assert code == "4" and "Traceback" not in text, answer
    assert text == "the desk refuses to start: " + NOT_A_FILE_BOOK_PROBLEM, answer
    assert not (tmp_path / "book.lock").exists(), "the refusal came after the lock step"


def test_book_problem_judges_the_kind_of_an_existing_path_only(tmp_path: Path) -> None:
    (tmp_path / "plain").write_text("", encoding="utf-8")
    assert book_problem(tmp_path / "plain") is None
    assert book_problem(tmp_path / "new-name") is None
    assert book_problem(str(tmp_path / "a\x00b")) is not None  # a control character is refused (see test_r4_refusals)
    assert book_problem(tmp_path) == NOT_A_FILE_BOOK_PROBLEM
    assert book_problem(":memory:") is not None and book_problem(":memory:") != NOT_A_FILE_BOOK_PROBLEM
