"""Class F7b: a lead-book path whose FOLDER cannot be made (a part of the path is a file, a pipe or a device, or the
place refuses folders) ends with the desk's one refusal line and exit code 4: no Python traceback, never the typed
name. The choke points are `desk.book_problem` (looks) and `desk.make_book_folder` (makes the folder and answers for
its failure); `server.main` and scripts/desk_setting.py (so start_all.sh and start_all.ps1) route through them.
Made-up names only, no network."""

from __future__ import annotations

import io
import os
import random
import re
import string
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest
from support import run_program
from test_reset_scripts import WINDOWS, _run
from test_special_output_files import FIFO_SKIP, in_child

from lead_desk.desk import (
    FOLDER_CANNOT_BE_MADE_BOOK_PROBLEM,
    FOLDER_PART_IS_A_FILE_BOOK_PROBLEM,
    book_problem,
    make_book_folder,
)

REPO = Path(__file__).resolve().parents[1]
TYPED = "zqx-typed-name"  # a folder name the operator typed: no refusal may repeat it
NEEDS_PROC = pytest.mark.skipif(not Path("/proc/self").is_dir(), reason="no /proc on this platform")


def _desk_main(path: str) -> str:
    """Child: the desk's own main() with DESK_DB_PATH=path; answers 'CODE|all text printed'."""
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


def _paths(tmp_path: Path) -> dict[str, str]:
    """Book paths whose folder cannot be made, by what is in the way. Each value is the typed book path."""
    (tmp_path / TYPED).write_text("x", encoding="utf-8")
    (tmp_path / "gone").symlink_to(tmp_path / "nowhere")
    found = {
        "a regular file in the way": str(tmp_path / TYPED / "book.db"),
        "a file two levels up": str(tmp_path / TYPED / "a" / "b" / "book.db"),
        "a link to nothing in the way": str(tmp_path / "gone" / "book.db"),
    }
    if Path("/dev/null").exists():
        found["a device in the way"] = "/dev/null/" + TYPED + "/book.db"
    if hasattr(os, "mkfifo"):
        os.mkfifo(tmp_path / "pipe")
        found["a pipe in the way"] = str(tmp_path / "pipe" / TYPED / "book.db")
    return found


def test_the_desk_refuses_a_book_whose_folder_cannot_be_made_in_one_line(tmp_path: Path) -> None:
    for what, path in _paths(tmp_path).items():
        answer = in_child(_desk_main, path)
        code, _, text = answer.partition("|")
        assert code == "4", (what, answer)
        assert "Traceback" not in text and TYPED not in text, (what, answer)
        assert text == "the desk refuses to start: " + FOLDER_PART_IS_A_FILE_BOOK_PROBLEM, (what, answer)
        assert not Path(path + ".lock").exists()


@NEEDS_PROC
def test_the_desk_refuses_a_place_that_will_not_make_a_folder_in_one_line() -> None:
    """/proc takes no new folders (even for root): the part that exists IS a folder, so only the make step can tell."""
    path = f"/proc/{TYPED}/book.db"
    answer = in_child(_desk_main, path)
    code, _, text = answer.partition("|")
    assert code == "4" and "Traceback" not in text and TYPED not in text, answer
    assert text == "the desk refuses to start: " + FOLDER_CANNOT_BE_MADE_BOOK_PROBLEM, answer


def test_make_book_folder_makes_what_can_be_made_and_answers_for_the_rest(tmp_path: Path) -> None:
    book = tmp_path / "new" / "deeper" / "book.db"
    assert book_problem(book) is None and make_book_folder(book) is None and book.parent.is_dir()
    assert make_book_folder(book) is None  # already there
    assert make_book_folder(str(tmp_path / "a\x00b" / "book.db")) in (None, FOLDER_CANNOT_BE_MADE_BOOK_PROBLEM)
    for what, path in _paths(tmp_path).items():
        assert book_problem(path) == FOLDER_PART_IS_A_FILE_BOOK_PROBLEM, what
        assert make_book_folder(path) == FOLDER_PART_IS_A_FILE_BOOK_PROBLEM, what


def test_property_a_path_under_a_file_is_always_refused_and_never_repeats_the_typed_names(tmp_path: Path) -> None:
    """Generated paths: a made-up chain of folder names with a regular file placed at a random depth. For every one,
    both choke points answer with the one plain line (never raise, never contain a typed name) and nothing is made
    under the file; a chain with no file in it is fine and is made."""
    rng = random.Random(7)  # fixed seed: the same 150 paths every run
    letters = string.ascii_lowercase + string.digits + " .-_"
    for i in range(150):
        names = ["q" + "".join(rng.choice(letters) for _ in range(rng.randint(1, 12))).strip(". ") for _ in range(4)]
        names = [n for n in names if n and n not in (".", "..")]
        root = tmp_path / f"case{i}"
        root.mkdir()
        depth = rng.randint(0, len(names) - 1)
        chain = root.joinpath(*names[:depth]) if depth else root
        chain.mkdir(parents=True, exist_ok=True)
        blocker = chain / names[depth]
        blocker.write_text("x", encoding="utf-8")
        book = blocker.joinpath(*names[depth + 1 :], "book.db")
        assert book_problem(book) == FOLDER_PART_IS_A_FILE_BOOK_PROBLEM, book
        assert make_book_folder(book) == FOLDER_PART_IS_A_FILE_BOOK_PROBLEM, book
        assert not any(n in FOLDER_PART_IS_A_FILE_BOOK_PROBLEM for n in names if len(n) > 4)
        assert blocker.is_file()  # nothing was made over the file
        free = root / "free" / names[0] / "book.db"
        assert book_problem(free) is None and make_book_folder(free) is None and free.parent.is_dir()


# ---------------------------------------------------------------- the start script
@pytest.mark.skipif(WINDOWS, reason="the Windows form is pinned by its text below")
def test_start_all_sh_refuses_a_book_folder_that_cannot_be_made_in_one_line(tmp_path: Path) -> None:
    """Only the `data-dir` call of start_all.sh can see this (the settings are all good): a script that loses that
    call goes on and fails some other way, so this test kills the mutant that removes it."""
    for what, path in _paths(tmp_path).items():
        done = _run("start_all.sh", Path(path))
        text = done.stdout + done.stderr
        assert done.returncode == 4, (what, done.returncode, text)
        assert text.strip() == "the desk refuses to start: " + FOLDER_PART_IS_A_FILE_BOOK_PROBLEM, (what, text)
        assert TYPED not in text and "Traceback" not in text and "mkdir" not in text, (what, text)


@NEEDS_PROC
@pytest.mark.skipif(WINDOWS, reason="the Windows form is pinned by its text below")
def test_start_all_sh_refuses_a_place_that_will_not_make_a_folder_in_one_line() -> None:
    done = _run("start_all.sh", Path(f"/proc/{TYPED}/book.db"))
    text = done.stdout + done.stderr
    assert done.returncode == 4, (done.returncode, text)
    assert text.strip() == "the desk refuses to start: " + FOLDER_CANNOT_BE_MADE_BOOK_PROBLEM, text
    assert TYPED not in text and "mkdir" not in text and "Traceback" not in text, text


def test_the_start_scripts_say_the_same_refusal_in_both_forms() -> None:
    """start_all.ps1 cannot run on this machine: its text is pinned (refusal line and exit code 4 when the folder
    cannot be made); start_all.sh is run by the tests above."""
    ps = (REPO / "scripts" / "start_all.ps1").read_text(encoding="utf-8")
    sh = (REPO / "scripts" / "start_all.sh").read_text(encoding="utf-8")
    line = "the desk refuses to start: the lead book folder cannot be made here (no such place, or no write access)"
    # R7: the lines are wrapped to 120 columns; the text and the exit code 4 are the same, one statement per line
    assert re.search(r"catch \{\s+Write-Host '" + re.escape(line) + r"'\s+exit 4\s+\}", ps)
    assert re.search(
        r'mkdir -p "\$data_dir" 2>/dev/null \|\| \{\s+echo "' + re.escape(line) + r'" >&2\s+exit 4\s+\}', sh
    )
    # r7e: the file has an earlier try/catch (the settings read), so the catch that is paired with New-Item is the
    # one that holds the refusal line: New-Item comes first, then that line, and no other catch sits in between
    start = ps.index("try { New-Item")
    assert start < ps.index(line, start)
    assert "catch {" in ps[start : ps.index(line, start)] and ps[start : ps.index(line, start)].count("catch {") == 1
    helper = (REPO / "scripts" / "desk_setting.py").read_text(encoding="utf-8")
    assert "argv[1] in BOOK_WORDS and (problem := book_problem(config.db_path)) is not None" in helper
    assert 'BOOK_WORDS = ("db-path", "data-dir")' in helper


@FIFO_SKIP
def test_a_pipe_as_the_book_is_still_refused_by_its_own_line(tmp_path: Path) -> None:
    os.mkfifo(tmp_path / "book")
    assert book_problem(tmp_path / "book") not in (None, FOLDER_PART_IS_A_FILE_BOOK_PROBLEM)


# -- round-3 finding 9: a book name the lock file cannot follow, and a file that cannot be read, end with exit 4 in both
# the desk and the start/reset helper (they used to disagree: the helper said 0, the desk then ended with exit 2) ---


def _helper(path: str) -> tuple[int, str]:
    """scripts/desk_setting.py db-path with DESK_DB_PATH=path, in its own process."""
    import subprocess  # noqa: S404
    import sys

    env = {k: v for k, v in os.environ.items() if not k.startswith("DESK_")}
    env.update(PYTHONPATH=str(REPO / "src"), PYTHONDONTWRITEBYTECODE="1", DESK_DB_PATH=path)
    done = run_program(
        [sys.executable, str(REPO / "scripts" / "desk_setting.py"), "db-path"],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
        stdin=subprocess.DEVNULL,
    )
    return done.returncode, (done.stdout + done.stderr).strip()


def test_a_book_name_that_leaves_no_room_for_the_lock_ending_is_refused(tmp_path: Path) -> None:
    from lead_desk.constants import BOOK_NAME_MAX_BYTES
    from lead_desk.desk import NAME_TOO_LONG_BOOK_PROBLEM

    assert BOOK_NAME_MAX_BYTES + len(".lock") == 255
    assert book_problem(tmp_path / ("a" * BOOK_NAME_MAX_BYTES)) is None  # the longest name that still has a lock file
    for length in (BOOK_NAME_MAX_BYTES + 1, 255, 256, 300):
        assert book_problem(tmp_path / ("a" * length)) == NAME_TOO_LONG_BOOK_PROBLEM, length
    assert book_problem(tmp_path / ("é" * 126)) == NAME_TOO_LONG_BOOK_PROBLEM  # 252 bytes, only 126 characters


@pytest.mark.parametrize("length", [251, 300])
def test_the_desk_and_the_helper_agree_on_exit_4_for_a_long_book_name(tmp_path: Path, length: int) -> None:
    from lead_desk.desk import NAME_TOO_LONG_BOOK_PROBLEM

    path = str(tmp_path / ("b" * length))
    code, _, text = in_child(_desk_main, path).partition("|")
    assert code == "4" and text == "the desk refuses to start: " + NAME_TOO_LONG_BOOK_PROBLEM, (code, text)
    assert "bbbb" not in text and "Traceback" not in text
    assert not [p for p in tmp_path.iterdir() if p.name.endswith(".lock")]  # no lock file was left behind
    rc, out = _helper(path)
    assert rc == 4 and out == "the desk refuses to start: " + NAME_TOO_LONG_BOOK_PROBLEM, (rc, out)


@NEEDS_PROC
def test_a_special_file_that_looks_regular_is_refused_as_the_book_by_the_desk_and_the_helper() -> None:
    """/proc/self/mem is listed as a regular file, but reading it fails: it is no lead book."""
    from lead_desk.desk import UNREADABLE_BOOK_PROBLEM

    assert book_problem("/proc/self/mem") == UNREADABLE_BOOK_PROBLEM
    code, _, text = in_child(_desk_main, "/proc/self/mem").partition("|")
    assert code == "4" and text == "the desk refuses to start: " + UNREADABLE_BOOK_PROBLEM, (code, text)
    rc, out = _helper("/proc/self/mem")
    assert rc == 4 and out == "the desk refuses to start: " + UNREADABLE_BOOK_PROBLEM, (rc, out)


def test_an_empty_book_and_a_real_book_are_still_accepted(tmp_path: Path) -> None:
    (tmp_path / "empty.db").write_bytes(b"")
    (tmp_path / "real.db").write_bytes(b"SQLite format 3\x00" + b"\x00" * 100)
    assert book_problem(tmp_path / "empty.db") is None
    assert book_problem(tmp_path / "real.db") is None
    assert book_problem(tmp_path / "new.db") is None


@pytest.mark.skipif(not hasattr(os, "geteuid") or os.geteuid() == 0, reason="root can read any file")
def test_a_book_without_read_permission_is_refused(tmp_path: Path) -> None:
    from lead_desk.desk import UNREADABLE_BOOK_PROBLEM

    p = tmp_path / "locked.db"
    p.write_bytes(b"")
    p.chmod(0)
    assert book_problem(p) == UNREADABLE_BOOK_PROBLEM
