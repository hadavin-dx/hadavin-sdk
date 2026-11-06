"""Tests of the mutation runner (``tools/mutation_runner.py``) and the mutation judge (``hadavin_sdk.testing.mutation``).

Moved from the PR #50 head (21 tests, each of which targets one guard of the runner or judge; the mutants that revert those
guards are in ``tests/mutation_runner_mutants.py``, and the meta-tests that check that list are in
``tests/test_mutation_runner_meta.py``). No test here talks to a network or a model; every tree is built in ``tmp_path``
from made-up files.
"""

import hashlib
import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from tools import mutation_runner as mr
from tools.mutation_runner import Mutant, run_mutants

from hadavin_sdk.testing import mutation as mutmod
from hadavin_sdk.testing.mutation import Verdict, first_failure, first_failure_junit, judge

FIX = Path(__file__).parent / "fixtures"


# ---- helpers of the tests below ---------------------------------------------------------------------------------------------


def _pk_tree(tmp_path, test_body):
    root = tmp_path / "pkg"
    (root / "src" / "pk").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "src" / "pk" / "__init__.py").write_text("", encoding="utf-8")
    (root / "src" / "pk" / "core.py").write_text(
        "def go(flag):\n    return flag\n", encoding="utf-8"
    )
    (root / "tests" / "test_core.py").write_text(test_body, encoding="utf-8")
    return root


def _raising_tree(tmp_path):
    return _pk_tree(
        tmp_path, "from pk.core import go\n\ndef test_a():\n    assert go(True) is True\n"
    )


def _copytree_failing(monkeypatch, fail_calls):
    """Make ``shutil.copytree`` raise ``PermissionError`` on the numbered calls (1-based) made by the runner."""
    import shutil

    from tools import mutation_runner

    real, calls = shutil.copytree, []

    def flaky(*a, **kw):
        dst = Path(
            a[1]
        )  # shutil.copytree calls itself for every sub-folder: count only the runner's own copy of src
        if (
            dst.name == "src"
            and dst.parent.name.startswith("mutants_")
            and "snap" not in dst.parent.name
        ):
            calls.append(1)
        if len(calls) in fail_calls and calls and dst.name == "src":
            raise PermissionError("file in use")
        return real(*a, **kw)

    monkeypatch.setattr(mutation_runner.shutil, "copytree", flaky)
    monkeypatch.setattr(mutation_runner, "SETUP_WAIT", 0.0)


def _pid_alive(pid):
    """True while ``pid`` is a running process. A killed grandchild that nobody has waited for is a zombie
    (state ``Z`` in ``/proc/<pid>/stat``); a zombie counts as dead."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # it exists, it is only not ours
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    except OSError:
        return True  # no /proc here: the signal check above is all there is
    return stat.rpartition(")")[2].split()[0] != "Z"


# ---- mutation judge and runner ------------------------------------------------------------------------------------------


def test_mutation_judge_verdicts():
    a = "E   AssertionError: assert 1 == 2"
    assert judge(1, "t.py::a", a) == Verdict.KILLED and judge(0, "t.py::a", a) == Verdict.SURVIVED
    assert judge(5, "t.py::a", a) == Verdict.NO_TESTS and judge(2, "t.py::a", a) == Verdict.ERROR
    assert (
        judge(1, "t.py::test_aaaa", a, expect="test_aaaa") == Verdict.KILLED
        and judge(1, "t.py::a", a, expect="zzzz") == Verdict.WRONG_REASON
    )
    with pytest.raises(ValueError):
        judge(1, "t.py::a", a, expect="a")  # a one-letter fragment matches almost anything
    assert judge(1, "t.py::a", a, pinned="t.py::b") == Verdict.OTHER_TEST
    for line in (
        "E   KeyError: 'x'",
        "E   TypeError: boom",
        "E   RuntimeError: x",
        "E   ImportError: no",
        "E   demo.fakes.AuditWriteError: audit write failed",
        "E   Failed: custom",
    ):
        assert judge(1, "t.py::a", line) == Verdict.CRASH, line
    assert judge(1, "t.py::a", "E   Failed: DID NOT RAISE <class 'TypeError'>") == Verdict.KILLED
    internal = "E   AssertionError: assert 'denied:internal_error' == 'queued'"
    assert judge(1, "t.py::a", internal) == Verdict.KILLED
    assert (
        judge(
            1, "t.py::a", internal, crash_markers=[re.compile(r"assert 'denied:internal_error' ==")]
        )
        == Verdict.CRASH
    )
    out = "FAILED tests/t.py::test_x[1] - assert 1\nE   AssertionError: assert 1 == 2\n"
    assert first_failure(out) == ("tests/t.py::test_x[1]", "E   AssertionError: assert 1 == 2")
    xml = (
        '<testsuite><testcase classname="tests.t" name="test_ok"/><testcase classname="tests.t" name="test_x[a - b | c]">'
        '<failure message="boom">def f():\nE   AssertionError: assert 1 == 2\n</failure></testcase></testsuite>'
    )
    assert first_failure_junit(xml) == (
        "tests/t::test_x[a - b | c]",
        "E   AssertionError: assert 1 == 2",
    )  # ids with ' - ' and ' | ' are intact


def test_the_runner_kills_a_mutant_of_a_tiny_package(tmp_path):
    (tmp_path / "src" / "pkg").mkdir(parents=True)
    (tmp_path / "src" / "pkg" / "__init__.py").write_text(
        "def guard(x):\n    if x < 0:\n        raise ValueError('negative')\n    return x\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_g.py").write_text(
        "import pytest\nfrom pkg import guard\n\ndef test_guard_refuses_negative():\n    with pytest.raises(ValueError):\n        guard(-1)\n",
        encoding="utf-8",
    )
    res = run_mutants(
        tmp_path,
        [Mutant("guard removed", "src/pkg/__init__.py", "if x < 0:", "if False:", "test_guard_refuses_negative"),
         Mutant("no-op mutant", "src/pkg/__init__.py", "return x", "return x  # same", "test_guard_refuses_negative"),
         Mutant("crash mutant", "src/pkg/__init__.py", "if x < 0:", "if 1 / 0:", "test_guard_refuses_negative"),
         Mutant("missing snippet", "src/pkg/__init__.py", "nope", "x", "test_guard")],
        ["tests/test_g.py"],
    )  # fmt: skip
    by = {n: (v, good) for n, v, _, good in res}
    assert (
        by["guard removed"] == (Verdict.KILLED, True)
        and by["no-op mutant"][1] is False
        and by["missing snippet"][1] is False
    )
    assert by["crash mutant"] == (Verdict.CRASH, False)  # an exception is not an assertion kill


def test_the_runner_refuses_paths_that_leave_its_tree(tmp_path):
    for bad in (
        "../x.py",
        "a/../../x.py",
        "/etc/passwd",
        "C:\\x.py",
        "\\\\host\\share\\x.py",
        "",
        "..\\x.py",
    ):
        with pytest.raises(ValueError):
            Mutant("name", bad, "a", "b", "test_x_assertion")
    outside = tmp_path / "outside.txt"
    with pytest.raises(ValueError):
        mr._inside(tmp_path / "base", "../outside.txt")
    (tmp_path / "base").mkdir()
    assert mr._inside(tmp_path / "base", "src/a.py").is_relative_to((tmp_path / "base").resolve())
    link = tmp_path / "base" / "link"
    os.symlink(
        tmp_path, link, target_is_directory=True
    )  # no fallback: where links cannot be made, this test fails
    assert link.exists(), "the test could not create a link out of the tree"
    with pytest.raises(ValueError):
        mr._inside(tmp_path / "base", "link/outside.txt")  # a link out of the tree is refused too
    (tmp_path / "real.txt").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        mr._locate(
            tmp_path / "base", "link/real.txt"
        )  # the listing does not follow the link out of the tree
    # A link to a FILE is listed (``os.walk`` lists it among the files), so only the real-path check keeps it out; the folder link above
    # never reaches that check on Linux, because ``os.walk`` does not enter it.
    os.symlink(tmp_path / "real.txt", tmp_path / "base" / "file_link.txt")
    with pytest.raises(ValueError):
        mr._locate(tmp_path / "base", "file_link.txt")
    with pytest.raises(ValueError):
        Mutant("name", "a.py", "a", "b", "abc")  # expect shorter than 4 characters
    victim = tmp_path / "victim.txt"
    victim.write_text("before", encoding="utf-8")
    forged = Mutant("forged", "src/a.py", "before", "after", "test_x_assertion")
    object.__setattr__(
        forged, "file", str(victim)
    )  # a Mutant built around __post_init__: the runner checks again
    pkg = tmp_path / "pkg0"
    (pkg / "src").mkdir(parents=True)
    (pkg / "tests").mkdir()
    (pkg / "tests" / "test_a.py").write_text(
        "def test_a():" + chr(10) + "    assert True" + chr(10), encoding="utf-8"
    )
    with pytest.raises(ValueError):
        run_mutants(pkg, [forged], ["tests/test_a.py"], extra_dirs=())
    assert victim.read_text(encoding="utf-8") == "before"
    assert not outside.exists()
    root = tmp_path / "pkg"
    (root / "src").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "tests" / "test_a.py").write_text("def test_a():\n    assert True\n", encoding="utf-8")
    for tests, extra in (
        (["../x.py"], ()),
        (["tests/test_a.py"], ("../x",)),
        (["/abs/test.py"], ()),
    ):
        with pytest.raises(ValueError):
            run_mutants(root, [], tests, extra_dirs=extra)


def test_the_runner_children_see_an_allowlisted_environment_only(tmp_path, monkeypatch):
    monkeypatch.setenv("HADAVIN_TEST_PG_DSN", "postgresql://u:p@h/db")  # the real caller's secret
    monkeypatch.setenv("SOME_API_TOKEN", "tok")
    root = _pk_tree(
        tmp_path,
        "import os\n\ndef test_no_secret_reaches_the_child():\n"
        "    assert 'HADAVIN_TEST_PG_DSN' not in os.environ\n"
        "    assert 'SOME_API_TOKEN' not in os.environ\n"
        "    assert 'PATH' in os.environ\n"
        "    assert os.environ.get('PYTHONNOUSERSITE') == '1'\n",
    )
    # the unmutated baseline must pass: it fails (RuntimeError) while the child inherits os.environ
    assert run_mutants(root, [], ["tests/test_core.py"], extra_dirs=(), timeout=120) == []


def test_an_edit_of_the_tree_during_the_run_does_not_leak_into_a_later_mutant(tmp_path):
    root = _pk_tree(
        tmp_path,
        "from pk.core import go\n\ndef test_go_is_true():\n    assert go(True) is True\n",
    )
    m1 = Mutant("one", "src/pk/core.py", "return flag", "return False", "test_go_is_true")
    m2 = Mutant("two", "src/pk/core.py", "return flag", "return not flag", "test_go_is_true")

    def edit_root_after_first(row):  # a second tool / a save while the run is going
        (root / "src" / "pk" / "core.py").write_text(
            "def go(flag):\n    return None\n", encoding="utf-8"
        )

    out = run_mutants(
        root,
        [m1, m2],
        ["tests/test_core.py"],
        extra_dirs=(),
        timeout=120,
        on_result=edit_root_after_first,
    )
    assert [(n, v) for n, v, _t, _g in out] == [("one", Verdict.KILLED), ("two", Verdict.KILLED)], (
        out
    )


def test_a_mutant_that_loops_forever_times_out_instead_of_hanging_the_run(tmp_path):
    root = tmp_path / "pkg"
    (root / "src" / "pk").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "src" / "pk" / "__init__.py").write_text("FLAG = False\n", encoding="utf-8")
    (root / "src" / "pk" / "core.py").write_text(
        "def go(flag):\n    return flag\n", encoding="utf-8"
    )
    (root / "tests" / "test_core.py").write_text(
        "from pk.core import go\n\ndef test_go_is_true():\n    assert go(True) is True\n",
        encoding="utf-8",
    )
    hang = Mutant(
        "hang", "src/pk/core.py", "return flag", "while True:\n        pass", "test_go_is_true"
    )
    out = run_mutants(
        root, [hang], ["tests/test_core.py"], extra_dirs=(), timeout=6, baseline_timeout=180
    )
    assert out == [("hang", Verdict.ERROR, "TIMEOUT", False)]


def test_a_test_path_that_starts_with_a_dash_is_a_path_not_a_pytest_option(tmp_path):
    (tmp_path / "test_ok.py").write_text("def test_a():\n    assert True\n", encoding="utf-8")
    assert mr._pytest(tmp_path, ["test_ok.py"], tmp_path / "r2.xml", 60) == 0
    # as a bare option "-x" would collect and pass test_ok.py in the cwd; as an operand it is a missing file
    assert mr._pytest(tmp_path, ["-x"], tmp_path / "r.xml", 60) != 0


def test_a_failing_tree_kill_still_kills_the_child(monkeypatch):
    import subprocess
    import sys

    def boom(*a, **k):
        raise FileNotFoundError("taskkill")

    def denied(*a, **k):
        raise PermissionError("killpg")

    monkeypatch.setattr(mr.subprocess, "run", boom)
    monkeypatch.setattr(mr.os, "killpg", denied, raising=False)
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(600)"])
    try:
        mr._kill_tree(proc)
        assert proc.poll() is not None
    finally:
        proc.kill()
        proc.wait()


def test_the_baseline_run_gets_its_own_timeout(tmp_path, monkeypatch):
    root = tmp_path / "pkg"
    (root / "src" / "pk").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "src" / "pk" / "core.py").write_text(
        "def go(flag):\n    return flag\n", encoding="utf-8"
    )
    (root / "tests" / "test_core.py").write_text(
        "def test_a():\n    assert True\n", encoding="utf-8"
    )
    seen = []

    def fake(cwd, tests, junit, timeout):
        seen.append(timeout)
        return 0 if len(seen) == 1 else mr.TIMED_OUT

    monkeypatch.setattr(mr, "_pytest", fake)
    mut = Mutant("m", "src/pk/core.py", "return flag", "return not flag", "test_a_x")
    out = run_mutants(
        root, [mut], ["tests/test_core.py"], extra_dirs=(), timeout=7, baseline_timeout=111
    )
    assert seen == [111, 7] and out == [("m", Verdict.ERROR, "TIMEOUT", False)]
    seen.clear()
    run_mutants(root, [mut], ["tests/test_core.py"], extra_dirs=(), timeout=9)
    assert seen == [9, 9]  # the baseline falls back to the mutant timeout


def test_the_runner_streams_each_result_and_keeps_a_sigkill_apart_from_a_timeout(
    tmp_path, monkeypatch
):
    assert mr.TIMED_OUT != -9 and mr.TIMED_OUT < -64  # no process exit status can equal it
    root = tmp_path / "pkg"
    (root / "src" / "pk").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "src" / "pk" / "core.py").write_text(
        "def go(flag):\n    return flag\n", encoding="utf-8"
    )
    (root / "tests" / "test_core.py").write_text(
        "def test_a():\n    assert True\n", encoding="utf-8"
    )
    codes = iter(
        [0, -9, mr.TIMED_OUT]
    )  # baseline, a mutant killed by SIGKILL (the OOM killer), a mutant that timed out

    monkeypatch.setattr(mr, "_pytest", lambda cwd, tests, junit, timeout: next(codes))
    muts = [
        Mutant(f"m{i}", "src/pk/core.py", "return flag", "return not flag", "test_a_x")
        for i in range(2)
    ]
    seen, finished = [], []
    mr_run = mr.run_mutants

    def on_result(row):
        seen.append(row[0])
        finished.append(len(seen))  # called once per mutant, in order, before the run returns

    out = mr_run(root, muts, ["tests/test_core.py"], extra_dirs=(), on_result=on_result)
    assert seen == ["m0", "m1"] and finished == [1, 2] and [r[0] for r in out] == seen
    assert (
        out[0][1] is Verdict.ERROR and out[0][2] != "TIMEOUT" and out[0][3] is False
    )  # SIGKILL: an error, not a timeout
    assert out[1] == ("m1", Verdict.ERROR, "TIMEOUT", False)


def test_a_timeout_kills_the_whole_process_tree_not_only_pytest(tmp_path):
    import time

    root = tmp_path / "pkg"
    (root / "src" / "pk").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "src" / "pk" / "__init__.py").write_text("", encoding="utf-8")
    (root / "src" / "pk" / "core.py").write_text(
        "def go(flag):\n    return flag\n", encoding="utf-8"
    )
    (root / "tests" / "test_core.py").write_text(
        "from pk.core import go\n\ndef test_go_is_true():\n    assert go(True) is True\n",
        encoding="utf-8",
    )
    pidfile = tmp_path / "pid.txt"
    body = (
        "import subprocess, sys, time\n"
        "    c = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(600)'])\n"
        f"    open({str(pidfile)!r}, 'w').write(str(c.pid))\n"
        "    time.sleep(600)"
    )
    spawn = Mutant("spawn", "src/pk/core.py", "return flag", body, "test_go_is_true")
    out = run_mutants(
        root, [spawn], ["tests/test_core.py"], extra_dirs=(), timeout=30, baseline_timeout=180
    )
    assert out == [("spawn", Verdict.ERROR, "TIMEOUT", False)]
    pid = int(pidfile.read_text(encoding="utf-8"))
    for _ in range(50):
        if not _pid_alive(pid):
            break
        time.sleep(0.2)
    assert not _pid_alive(pid), "the grandchild survived the timeout"


def test_a_setup_failure_for_one_mutant_is_a_result_row_and_a_blip_is_retried(
    tmp_path, monkeypatch
):
    root = _pk_tree(
        tmp_path, "from pk.core import go\n\ndef test_go_is_true():\n    assert go(True) is True\n"
    )
    a = Mutant("a", "src/pk/core.py", "return flag", "return False", "test_go_is_true")
    b = Mutant("b", "src/pk/core.py", "return flag", "return not flag", "test_go_is_true")
    # call 1 = baseline copy; calls 2..6 = every try for mutant a (SETUP_TRIES = 5)
    _copytree_failing(monkeypatch, set(range(2, 7)))
    out = run_mutants(root, [a, b], ["tests/test_core.py"], extra_dirs=(), timeout=120)
    assert [(n, v, t) for n, v, t, _g in out] == [
        ("a", Verdict.ERROR, "SETUP FAILED: PermissionError"),
        ("b", Verdict.KILLED, out[1][2]),
    ], out
    assert [g for *_x, g in out] == [False, True]
    # a lock that clears after two tries costs nothing: the mutant is judged as usual
    _copytree_failing(monkeypatch, {2, 3})
    again = run_mutants(root, [a], ["tests/test_core.py"], extra_dirs=(), timeout=120)
    assert [(n, v) for n, v, _t, _g in again] == [("a", Verdict.KILLED)], again


def test_the_runner_keeps_a_symlink_a_link(tmp_path):
    root = _pk_tree(
        tmp_path,
        "import pathlib, pk\n\ndef test_ext_is_a_link():\n"
        "    assert (pathlib.Path(pk.__file__).parent / 'ext.py').is_symlink()\n",
    )
    outside = tmp_path / "outside.py"
    outside.write_text("X = 1\n", encoding="utf-8")
    try:
        (root / "src" / "pk" / "ext.py").symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("this system does not allow creating symlinks")
    assert run_mutants(root, [], ["tests/test_core.py"], extra_dirs=(), timeout=120) == []


def test_a_test_file_that_is_not_among_the_copied_tests_fails_before_any_mutant_runs(tmp_path):
    root = _pk_tree(
        tmp_path, "from pk.core import go\n\ndef test_go_is_true():\n    assert go(True) is True\n"
    )
    ok = Mutant("ok", "src/pk/core.py", "return flag", "return False", "test_go_is_true")
    bad = Mutant(
        "bad",
        "src/pk/core.py",
        "return flag",
        "return not flag",
        "test_go_is_true",
        test_file="tests/elsewhere.py",
    )
    ran = []
    with pytest.raises(ValueError, match="elsewhere"):
        run_mutants(
            root,
            [ok, bad],
            ["tests/test_core.py"],
            extra_dirs=(),
            timeout=120,
            on_result=ran.append,
        )
    assert ran == []  # the first mutant was not run


def test_junit_with_a_doctype_or_entity_is_refused_not_parsed():
    bomb = '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><testsuite><testcase classname="t" name="n"/></testsuite>'
    with pytest.raises(ValueError):
        first_failure_junit(bomb)  # FAIL-BEFORE: parsed
    ok = '<testsuite><testcase classname="tests.t" name="n"><failure message="m">E   assert 1 == 2</failure></testcase></testsuite>'
    assert first_failure_junit(ok) == ("tests/t::n", "E   assert 1 == 2")


def test_the_runner_wires_pinned_so_another_failing_test_is_other_test(tmp_path):
    body = "from pk.core import go\n\ndef test_a():\n    assert go(True) is True\n\ndef test_b():\n    assert go(True) is True\n"
    root = _pk_tree(tmp_path, body)
    base = ("m", "src/pk/core.py", "return flag", "return False", "test_")
    other = Mutant(*base, pinned="tests/test_core::test_does_not_exist")
    same = Mutant("m2", *base[1:], pinned="tests/test_core::test_a")
    res = run_mutants(root, [other, same], ["tests/test_core.py"], extra_dirs=(), timeout=120)
    verdicts = {name: v for name, v, _tid, _good in res}
    assert verdicts["m"] is Verdict.OTHER_TEST  # FAIL-BEFORE: Mutant had no pinned field
    assert verdicts["m2"] is Verdict.KILLED  # the pinned test is the one that failed first


def test_a_refused_junit_marks_that_mutant_error_and_the_run_goes_on(tmp_path, monkeypatch):
    from tools import mutation_runner

    body = "from pk.core import go\n\ndef test_a():\n    assert go(True) is True\n"
    root = _pk_tree(tmp_path, body)
    real = mutation_runner.first_failure_junit
    state = {"n": 0}

    def flaky(text):
        state["n"] += 1
        if state["n"] == 1:
            raise ValueError("refused")
        return real(text)

    monkeypatch.setattr(mutation_runner, "first_failure_junit", flaky)
    m1 = Mutant("m1", "src/pk/core.py", "return flag", "return False", "test_")
    m2 = Mutant("m2", "src/pk/core.py", "return flag", "return False", "test_")
    res = run_mutants(root, [m1, m2], ["tests/test_core.py"], extra_dirs=(), timeout=120)
    got = {n: (v, tid) for n, v, tid, _ in res}
    assert got["m1"] == (
        Verdict.ERROR,
        "JUNIT REFUSED",
    )  # FAIL-BEFORE: the ValueError aborted the whole run
    assert got["m2"][0] is Verdict.KILLED


def test_a_junit_text_over_the_ceiling_is_refused():
    with pytest.raises(ValueError):
        first_failure_junit(
            "<testsuite>" + " " * getattr(mutmod, "MAX_JUNIT_CHARS", 8_000_000) + "</testsuite>"
        )  # FAIL-BEFORE: no size cap


def test_a_crash_row_is_good_only_when_the_exception_class_is_the_declared_one(tmp_path):
    root = _raising_tree(tmp_path)
    base = ("src/pk/core.py", "return flag", 'raise ValueError("boom")', "test_a")
    right = Mutant("right", *base, allow_crash=True, crash_type="ValueError")
    wrong = Mutant("wrong", *base, allow_crash=True, crash_type="KeyError")
    res = {
        n: (v, good)
        for n, v, _t, good in run_mutants(
            root, [right, wrong], ["tests/test_core.py"], extra_dirs=(), timeout=120
        )
    }
    assert res["right"] == (Verdict.CRASH, True)
    assert res["wrong"] == (Verdict.CRASH, False)  # FAIL-BEFORE: any exception counted as good
    assert "ValueError" in mr.FIRST_LINES["right"]


def test_allow_crash_without_a_crash_type_is_refused_and_a_truncated_junit_marks_the_mutant_error(
    tmp_path, monkeypatch
):
    with pytest.raises(ValueError):
        Mutant("m", "src/pk/core.py", "a", "b", "test_a", allow_crash=True)
    with pytest.raises(ValueError):
        Mutant("m", "src/pk/core.py", "a", "b", "test_a", crash_type="ValueError")
    root = _raising_tree(tmp_path)

    def truncated(text):
        raise ET.ParseError("no element found")

    monkeypatch.setattr(mr, "first_failure_junit", truncated)
    m = Mutant("m", "src/pk/core.py", "return flag", "return False", "test_a")
    ((_name, v, tid, good),) = run_mutants(
        root, [m], ["tests/test_core.py"], extra_dirs=(), timeout=120
    )
    assert (v, tid, good) == (
        Verdict.ERROR,
        "JUNIT REFUSED",
        False,
    )  # FAIL-BEFORE: ParseError aborted the whole run


def test_taskkill_is_resolved_under_system_root():
    path = Path(mr._taskkill())
    assert path.name.lower() == "taskkill.exe" and path.parent.name.lower() == "system32"


# last on purpose: a mutation of a pinned file must be judged by the test aimed at it, not by this hash pin
def test_the_manifest_pins_the_files_a_demo_copies():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((FIX / "mutation_manifest.json").read_text(encoding="utf-8"))
    for rel, sha in manifest["files"].items():
        data = (root / rel).read_bytes().replace(b"\r\n", b"\n")
        assert hashlib.sha256(data).hexdigest() == sha, (
            rel,
            "changed: re-sync the demos and update the manifest and the CHANGELOG",
        )
    assert set(manifest["files"]) == {
        "src/hadavin_sdk/testing/__init__.py",
        "src/hadavin_sdk/testing/mutation.py",
        "tools/__init__.py",
        "tools/mutation_runner.py",
    }
    log = root / "CHANGELOG.md"
    if log.exists():  # the mutation copies do not carry it
        text = log.read_text(encoding="utf-8")
        for rel, sha in manifest["files"].items():
            assert sha in text, rel  # the CHANGELOG re-copy list names every pinned hash
