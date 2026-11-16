"""Round 7C, finding B: `checked_argv` / `popen_program` refuse what their docstring says they refuse.

Found by the review of r7b: `git -ccore.pager=x` and `--config-env` were accepted, the keywords `executable=` and
`shell=` were passed through, a path-prefixed look-alike (`/tmp/x/git`) passed on its basename, and the scan "no other
file starts a program" missed `from subprocess import run`. Rejected samples first, then the allowed shapes."""

from __future__ import annotations

import ast
import stat
from pathlib import Path

import pytest
from support import RefusedProgram, checked_argv, popen_program

HERE = Path(__file__).resolve().parent


# CONTROL (r7e, with the r7c helper): passes on r7b, a pin; mutant NOT run, the intended one:
# the helper or scan lets another program start.
@pytest.mark.parametrize(
    "argv",
    [
        ["git", "-ccore.pager=x", "log"],
        ["git", "-c", "core.pager=x", "log"],
        ["git", "-c", "alias.x=!id", "x"],
        ["git", "--config-env=core.pager=X", "log"],
        ["git", "--config-env", "core.pager=X", "log"],
        ["git", "--exec-path=/" + "tmp/x", "log"],
        ["git", "-C", ".", "-ccore.sshCommand=id", "fetch"],
    ],
)
def test_git_settings_that_run_a_program_are_refused(argv: list[str]) -> None:
    with pytest.raises(RefusedProgram):
        checked_argv(argv)


# CONTROL (r7e, with the r7c helper): passes on r7b, a pin; mutant NOT run, the intended one:
# the helper or scan lets another program start.
def test_git_user_settings_and_plain_commands_are_allowed() -> None:
    assert checked_argv(["git", "-c", "user.name=a", "-c", "user.email=a@example.test", "log"])
    assert checked_argv(["git", "-cuser.name=a", "log"])
    assert checked_argv(["git", "-C", ".", "status", "--short"])


# CONTROL (r7e, with the r7c helper): passes on r7b, a pin; mutant NOT run, the intended one:
# the helper or scan lets another program start.
def test_a_path_prefixed_look_alike_of_a_listed_tool_is_refused(tmp_path: Path) -> None:
    fake = tmp_path / "git"
    fake.write_text("#!/bin/sh\necho X\n", encoding="utf-8")
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    for name in ("git", "true", "ps"):
        look_alike = tmp_path / name
        look_alike.write_text("#!/bin/sh\necho X\n", encoding="utf-8")
        with pytest.raises(RefusedProgram):
            checked_argv([str(look_alike)])
    with pytest.raises(RefusedProgram):
        checked_argv([str(fake), "log"])


# CONTROL (r7e, with the r7c helper): passes on r7b, a pin; mutant NOT run, the intended one:
# the helper or scan lets another program start.
@pytest.mark.parametrize("keyword", ["executable", "shell", "preexec_fn"])
def test_keywords_that_start_something_else_are_refused_and_nothing_starts(keyword: str, tmp_path: Path) -> None:
    marker = tmp_path / "ran"
    value = {"executable": "/bin/sh", "shell": True, "preexec_fn": lambda: marker.write_text("x")}[keyword]
    with pytest.raises(RefusedProgram):
        popen_program(["true", "-c", f"echo X > {marker}"], **{keyword: value})
    assert not marker.exists()


_PROGRAM_START_NAMES = {"run", "Popen", "call", "check_output", "check_call", "getoutput", "getstatusoutput"}
_OS_START_NAMES = {"system", "popen", "fork", "posix_spawn", "posix_spawnp"}


def _starts_a_program(tree: ast.AST) -> list[int]:
    """Lines that import a start-a-program name (any spelling), call one through `subprocess`, `os` or an alias."""
    hits: list[int] = []
    aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name == "subprocess" and a.asname:
                    aliases.add(a.asname)
                    hits.append(node.lineno)
        elif isinstance(node, ast.ImportFrom):
            names = {a.name for a in node.names}
            if node.module == "subprocess" and names & _PROGRAM_START_NAMES:
                hits.append(node.lineno)
            if node.module == "os" and any(n in _OS_START_NAMES or n.startswith(("exec", "spawn")) for n in names):
                hits.append(node.lineno)
            if node.module in {"pty", "asyncio.subprocess"} or (
                node.module == "asyncio" and any(n.startswith("create_sub") for n in names)
            ):
                hits.append(node.lineno)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            f = node.func
            base = f.value.id if isinstance(f.value, ast.Name) else ""
            if (base in {"subprocess"} | aliases and f.attr in _PROGRAM_START_NAMES) or (
                base == "os" and (f.attr in _OS_START_NAMES or f.attr.startswith(("exec", "spawn")))
            ):
                hits.append(node.lineno)
    return hits


# CONTROL (r7e, with the r7c helper): passes on r7b, a pin; mutant NOT run, the intended one:
# the helper or scan lets another program start.
def test_the_scan_notices_every_spelling_of_a_program_start() -> None:
    for text in (
        "from subprocess import run",
        "from subprocess import Popen as P",
        "import subprocess as sp\nsp.run(['x'])",
        "import subprocess\nsubprocess.check_output(['x'])",
        "from os import system",
        "import os\nos.execv('x', [])",
    ):
        assert _starts_a_program(ast.parse(text)), text
    assert not _starts_a_program(ast.parse("import subprocess\nsubprocess.TimeoutExpired\nx = subprocess.PIPE"))


# CONTROL (r7e, with the r7c helper): passes on r7b, a pin; mutant NOT run, the intended one:
# the helper or scan lets another program start.
def test_no_other_file_of_tests_starts_a_program_in_any_spelling() -> None:
    allowed = {"support.py", "test_file_call_guard.py", "test_r7b_program_helper.py", Path(__file__).name}
    found = []
    for path in sorted(HERE.glob("*.py")):
        if path.name in allowed:
            continue
        found += [f"{path.name}:{n}" for n in _starts_a_program(ast.parse(path.read_text(encoding="utf-8")))]
    assert found == [], found
