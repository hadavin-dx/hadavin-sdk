"""The one place that starts a program from a test (`support.popen_program`, `run_program`, `checked_argv`).

The S603 ruling: ONE inline marker, on the single start in `popen_program`, and a test that proves the helper refuses a
command line that is tainted or not a literal list of strings. Here: what is refused (an interpreter given text to run
with -c, -e, -p or --eval, a module outside this repository with -m, a shell name, an element that is not a plain str,
a program that is not on the short list), what is allowed, that a refused line starts nothing, and that no other file
of tests/ starts a program by itself. Made-up data only; nothing here touches a /dev path."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
from support import REPO, RefusedProgram, checked_argv, popen_program, run_program, text_file

PY = sys.executable
HERE = Path(__file__).resolve().parent


def _script(tmp_path: Path) -> str:
    path = tmp_path / "ok.py"
    path.write_text("print('hi')\n", encoding="utf-8")
    return str(path)


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
@pytest.mark.parametrize(
    "tail",
    [
        ["-c", "print(1)"],
        ["-I", "-c", "print(1)"],
        ["-Ic", "print(1)"],
        ["-m", "http.server"],
        ["-m", "pip"],
        ["-m", "lead_desk.server; id"],
        ["-m", ""],
        ["-m"],
        ["-X", "dev", "x.py"],
        ["-W", "ignore", "x.py"],
        ["--command", "print(1)"],
        [],
        ["no_such_script.py"],
    ],
    ids=lambda t: " ".join(t) or "nothing",
)
def test_python_is_refused_with_text_to_run_a_foreign_module_or_no_script(tail: list[str]) -> None:
    with pytest.raises(RefusedProgram):
        checked_argv([PY, *tail])


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
@pytest.mark.parametrize("flag", ["-e", "--eval", "-p", "--print", "-r", "-c"])
def test_node_and_other_interpreters_are_refused_with_text_to_run(flag: str, tmp_path: Path) -> None:
    for program in ("node", "perl", "ruby", "php"):
        with pytest.raises(RefusedProgram):
            checked_argv([program, flag, "1"])
    with pytest.raises(RefusedProgram):
        checked_argv(["node", flag, _script(tmp_path)])


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
@pytest.mark.parametrize("program", ["sh", "bash", "dash", "zsh", "ksh", "cmd", "powershell", "pwsh", "/bin/sh"])
def test_a_shell_name_is_refused_without_a_script_file(program: str) -> None:
    for tail in ([], ["-c", "id"], ["-e", "-c", "id"], ["no_such_file" + ".sh"], ["-x"]):
        with pytest.raises(RefusedProgram):
            checked_argv([program, *tail])


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
def test_a_shell_is_refused_with_an_option_before_a_real_script(tmp_path: Path) -> None:
    script = tmp_path / ("s" + ".sh")
    script.write_text("echo hi\n", encoding="utf-8")
    with pytest.raises(RefusedProgram):
        checked_argv(["bash", "-x", str(script)])
    assert checked_argv(["bash", str(script)]) == ["bash", str(script)]


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
@pytest.mark.parametrize(
    "bad",
    [
        "a string, not a list",
        b"bytes",
        None,
        [],
        (),
        [PY, 5],
        [PY, None],
        [PY, b"x.py"],
        [PY, Path("x.py")],
        [Path(PY)],
        [PY, "a\0b"],
        ["git", ["nested"]],
        [object()],
    ],
    ids=repr,
)
def test_a_command_line_that_is_not_a_literal_list_of_plain_strings_is_refused(bad: object) -> None:
    with pytest.raises(RefusedProgram):
        checked_argv(bad)


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
def test_an_element_that_is_a_str_subclass_is_refused() -> None:
    class Tainted(str):
        pass

    with pytest.raises(RefusedProgram):
        checked_argv([PY, Tainted(str(HERE / "support.py"))])
    with pytest.raises(RefusedProgram):
        checked_argv([Tainted("git"), "status"])


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
@pytest.mark.parametrize(
    "line",
    [
        ["curl", "http://127.0.0.1/"],
        ["rm", "-rf", "x"],
        ["sudo", "id"],
        ["env", "id"],
        ["xargs", "id"],
        ["/usr" + "/bin/python3-not-ours", "x.py"],
        ["python3", "x.py"],
        ["git", "-c", "core.sshCommand=id", "status"],
        ["git", "-c", "alias.x=!id", "x"],
        ["unshare", "-n", "-c", "id"],
        ["unshare", "--mount", "true"],
        ["unshare", "-n", "sh", "-c", "id"],
        ["unshare", "-n", "curl", "x"],
        ["unshare", "-n"],
    ],
    ids=lambda x: " ".join(x),
)
def test_a_program_that_is_not_on_the_short_list_or_is_given_a_loader_option_is_refused(line: list[str]) -> None:
    with pytest.raises(RefusedProgram):
        checked_argv(line)


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
def test_the_shapes_the_tests_use_are_accepted(tmp_path: Path) -> None:
    script = _script(tmp_path)
    assert checked_argv([PY, script, "arg"]) == [PY, script, "arg"]
    assert checked_argv((PY, "-I", script))
    assert checked_argv([PY, "-m", "lead_desk.server"])
    assert checked_argv([PY, "-m", "demo_only.fakes_server", "--outbox", "keyed"])
    assert checked_argv([PY, "-m", "pytest", "-q"])
    assert checked_argv([PY, text_file("print(1)")])
    assert checked_argv(["node", text_file("1", ".js"), "x"])
    assert checked_argv(["git", "-c", "user.name=a", "-c", "user.email=a@example.test", "init"])
    assert checked_argv(["unshare", "-n", "true"])
    assert checked_argv(["unshare", "-n", PY, script])
    assert checked_argv(["ps", "-p", "1", "-o", "stat="])


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
def test_a_refused_line_starts_nothing(tmp_path: Path) -> None:
    mark = tmp_path / "started"
    code = f"open({str(mark)!r}, 'w').close()"
    with pytest.raises(RefusedProgram):
        popen_program([PY, "-c", code])
    with pytest.raises(RefusedProgram):
        run_program([PY, "-c", code], capture_output=True)
    with pytest.raises(RefusedProgram):
        run_program(["sh", "-c", f"touch {mark}"], capture_output=True)
    assert not mark.exists()


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
def test_run_program_runs_a_script_file_and_text_goes_through_a_file(tmp_path: Path) -> None:
    done = run_program(
        [PY, text_file("import sys; print('x' + sys.argv[1]); sys.exit(3)"), "q"], capture_output=True, text=True
    )
    assert (done.returncode, done.stdout.strip()) == (3, "xq")
    with pytest.raises(subprocess.CalledProcessError):
        run_program([PY, text_file("import sys; sys.exit(2)")], capture_output=True, check=True)
    with pytest.raises(subprocess.TimeoutExpired):
        run_program([PY, text_file("import time; time.sleep(30)")], timeout=0.5)
    fed = run_program(
        [PY, text_file("import sys; print(sys.stdin.read().upper())")], input="abc", capture_output=True, text=True
    )
    assert fed.stdout.strip() == "ABC"


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
def test_text_file_is_content_addressed_and_read_back_exactly() -> None:
    a, b = text_file("print(1)\n"), text_file("print(1)\n")
    assert a == b and Path(a).read_text(encoding="utf-8") == "print(1)\n"
    assert text_file("1", ".js").endswith(".js") and text_file("1") != text_file("1", ".js")


_START = re.compile(
    r"\b(?:subprocess\s*\.\s*(?:run|Popen|call|check_output|check_call|getoutput|getstatusoutput)"
    r"|os\s*\.\s*(?:system|popen|exec\w*|spawn\w*|posix_spawn\w*|fork)"
    r"|create_subprocess_\w+|pty\s*\.\s*spawn)\b"
)


def test_no_other_file_of_tests_starts_a_program_by_itself() -> None:
    """Every start goes through the helper; test_file_call_guard.py and this file only name the calls inside text."""
    found = []
    for path in sorted(HERE.glob("*.py")):
        if path.name in {"support.py", "test_file_call_guard.py", "test_r7b_program_helper.py"}:
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if _START.search(line.split("#", 1)[0]):
                found.append(f"{path.name}:{number}")
    assert found == [], found


def test_the_helper_line_is_the_only_s603_marker_in_tests() -> None:
    marker = "noqa: " + "S603"
    hits = [
        p.name for p in HERE.glob("*.py") if marker in p.read_text(encoding="utf-8") and p.name != Path(__file__).name
    ]
    assert hits == ["support.py"], hits
    assert (HERE / "support.py").read_text(encoding="utf-8").count(marker) == 1


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
def test_this_repository_paths_exist_for_the_accepted_shapes() -> None:
    assert (REPO / "src" / "lead_desk").is_dir() and (REPO / "demo_only").is_dir()
