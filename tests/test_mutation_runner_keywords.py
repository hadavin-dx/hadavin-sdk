"""Tests of the three opt-in keywords of ``tools.mutation_runner.run_mutants``: ``conftest``, ``pass_env`` and ``forbid_skips``.

Class: a mutant that "dies" because the tests could not run (skipped, or no database address, or a missing fixture file) is a FALSE
kill. The fix sits at the runner (one choke point for every caller). Defaults must keep the old behaviour exactly.
"""

import hashlib
import os
from pathlib import Path

import pytest
from tools import mutation_runner as mr
from tools.mutation_runner import PASS_ENV_ALLOWED, Mutant, run_mutants

from hadavin_sdk.testing.mutation import Verdict, fixture_errors, judge, skipped_tests

DSN_NAME = "HADAVIN_TEST_PG_DSN"
FLIP = Mutant("flip", "src/pk/core.py", "return flag", "return not flag", "assert")


def _tree(tmp_path: Path, tests: dict[str, str]) -> Path:
    root = tmp_path / "pkg"
    (root / "src" / "pk").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "src" / "pk" / "__init__.py").write_text("", encoding="utf-8")
    (root / "src" / "pk" / "core.py").write_text(
        "def go(flag):\n    return flag\n", encoding="utf-8"
    )
    for name, body in tests.items():
        (root / name).write_text(body, encoding="utf-8")
    return root


def _fake_dsn() -> str:
    user, secret = "someone", "pw"  # built from parts: no URL with a password stands in the source
    return f"postgresql://{user}:{secret}@db.invalid/x"


SKIP_FIRST = (
    "import pytest\nfrom pk.core import go\n\n"
    "def test_setup_works():\n    if go(False) is not False:\n        pytest.skip('cannot run here')\n\n"
    "def test_a():\n    assert go(True) is True\n"
)


# ---- conftest ---------------------------------------------------------------------------------------------------------------


CONFTEST_FIXTURE = "import pytest\n\n@pytest.fixture\ndef answer():\n    return 42\n"
USES_FIXTURE = "def test_a(answer):\n    assert answer == 42\n"


def test_conftest_loads_the_given_file_as_a_plugin_and_without_it_nothing_is_loaded(tmp_path):
    root = _tree(
        tmp_path, {"tests/conftest.py": CONFTEST_FIXTURE, "tests/test_core.py": USES_FIXTURE}
    )
    assert (
        run_mutants(
            root,
            [],
            ["tests/test_core.py"],
            extra_dirs=(),
            conftest="tests/conftest.py",
            timeout=120,
        )
        == []
    )
    # the default is unchanged: --noconftest, so the fixture is missing and the unmutated copy fails
    with pytest.raises(RuntimeError, match="does not pass"):
        run_mutants(root, [], ["tests/test_core.py"], extra_dirs=(), timeout=120)


def test_a_mutant_is_judged_with_the_conftest_loaded(tmp_path):
    body = "from pk.core import go\n\ndef test_a(answer):\n    assert answer == 42\n    assert go(True) is True\n"
    root = _tree(tmp_path, {"tests/conftest.py": CONFTEST_FIXTURE, "tests/test_core.py": body})
    res = run_mutants(
        root,
        [FLIP],
        ["tests/test_core.py"],
        extra_dirs=(),
        conftest="tests/conftest.py",
        timeout=120,
    )
    assert [(n, v, good) for n, v, _, good in res] == [("flip", Verdict.KILLED, True)]


@pytest.mark.parametrize(
    "bad",
    [
        "tests/conftest.txt",
        "tests/my-conf.py",
        "tests/no:conf.py",
        "../conftest.py",
        "/abs/conftest.py",
        "-p.py",
        "@x.py",
        "tests/1x.py",
        "tests/class.py",
        "tests/import.py",
        "tests/caf\u00e9.py",
        "t\u00e9sts/conftest.py",
        "",
    ],
)
def test_a_conftest_that_is_not_a_plain_python_path_is_refused_before_anything_runs(tmp_path, bad):
    root = _tree(tmp_path, {"tests/test_core.py": "def test_a():\n    assert True\n"})
    if bad == "":  # empty means "off": the default
        assert (
            run_mutants(root, [], ["tests/test_core.py"], extra_dirs=(), conftest=bad, timeout=120)
            == []
        )
        return
    with pytest.raises(ValueError):
        run_mutants(root, [], ["tests/test_core.py"], extra_dirs=(), conftest=bad, timeout=120)


# ---- pass_env ---------------------------------------------------------------------------------------------------------------


READS_DSN = (
    f"import os\n\ndef test_a():\n    assert os.environ.get({DSN_NAME!r}) == {_fake_dsn()!r}\n"
)


def test_pass_env_hands_the_listed_variable_to_the_child_and_default_does_not(
    tmp_path, monkeypatch
):
    monkeypatch.setenv(DSN_NAME, _fake_dsn())
    root = _tree(tmp_path, {"tests/test_core.py": READS_DSN})
    assert (
        run_mutants(
            root, [], ["tests/test_core.py"], extra_dirs=(), pass_env=(DSN_NAME,), timeout=120
        )
        == []
    )
    with pytest.raises(RuntimeError, match="does not pass"):  # the default still withholds it
        run_mutants(root, [], ["tests/test_core.py"], extra_dirs=(), timeout=120)


def test_pass_env_never_widens_to_other_variables(tmp_path, monkeypatch):
    monkeypatch.setenv(DSN_NAME, _fake_dsn())
    monkeypatch.setenv("SOME_API_TOKEN", "tok")
    body = "import os\n\ndef test_a():\n    assert 'SOME_API_TOKEN' not in os.environ\n"
    root = _tree(tmp_path, {"tests/test_core.py": body})
    assert (
        run_mutants(
            root, [], ["tests/test_core.py"], extra_dirs=(), pass_env=(DSN_NAME,), timeout=120
        )
        == []
    )


def test_pass_env_with_an_unset_variable_passes_nothing(tmp_path, monkeypatch):
    monkeypatch.delenv(DSN_NAME, raising=False)
    body = f"import os\n\ndef test_a():\n    assert {DSN_NAME!r} not in os.environ\n"
    root = _tree(tmp_path, {"tests/test_core.py": body})
    assert (
        run_mutants(
            root, [], ["tests/test_core.py"], extra_dirs=(), pass_env=(DSN_NAME,), timeout=120
        )
        == []
    )


@pytest.mark.parametrize(
    "names",
    [
        ("SOME_API_TOKEN",),
        ("AWS_SECRET_ACCESS_KEY",),
        (DSN_NAME, "PATH"),
        (DSN_NAME.lower(),),
        (DSN_NAME + " ",),
        ("A=B",),
        ("",),
    ],
)
def test_an_unlisted_env_name_is_refused_before_anything_runs(tmp_path, monkeypatch, names):
    monkeypatch.setenv("SOME_API_TOKEN", "tok")
    root = _tree(tmp_path, {"tests/test_core.py": "def test_a():\n    assert True\n"})
    seen = []
    monkeypatch.setattr(mr, "_pytest", lambda *a, **k: seen.append(a) or 0)
    with pytest.raises(ValueError):
        run_mutants(root, [], ["tests/test_core.py"], extra_dirs=(), pass_env=names, timeout=120)
    assert seen == [], "a refused name must not start a single pytest run"


def test_a_bare_string_for_pass_env_is_refused_not_read_letter_by_letter(tmp_path):
    root = _tree(tmp_path, {"tests/test_core.py": "def test_a():\n    assert True\n"})
    with pytest.raises(TypeError, match="not one string"):
        run_mutants(root, [], ["tests/test_core.py"], extra_dirs=(), pass_env=DSN_NAME, timeout=120)


def test_property_no_name_outside_the_allowlist_is_ever_accepted():
    # 500 fixed pseudo-random names (hash prefixes of 0..499, lengths 0..39), the same every run
    names = [hashlib.sha256(str(i).encode()).hexdigest()[: i % 40] for i in range(500)]
    names += [n + suffix for n in PASS_ENV_ALLOWED for suffix in ("_", "2", " ", "\n", "\x00")]
    for name in names:
        if name in PASS_ENV_ALLOWED:
            continue
        with pytest.raises(ValueError):
            mr._checked_env_names((name,))
    assert mr._checked_env_names(PASS_ENV_ALLOWED) == PASS_ENV_ALLOWED


def test_property_the_allowlist_holds_only_the_test_database_address():
    assert PASS_ENV_ALLOWED == (DSN_NAME,)
    assert not set(PASS_ENV_ALLOWED) & {
        "PATH",
        "HOME",
    }  # already inherited names are not what this is for


# ---- forbid_skips -----------------------------------------------------------------------------------------------------------


def test_default_counts_a_run_with_a_skipped_test_as_before(tmp_path):
    root = _tree(tmp_path, {"tests/test_core.py": SKIP_FIRST})
    res = run_mutants(root, [FLIP], ["tests/test_core.py"], extra_dirs=(), timeout=120)
    assert [(n, v, good) for n, v, _, good in res] == [("flip", Verdict.KILLED, True)]


def test_forbid_skips_makes_a_mutant_run_with_a_skipped_test_an_error_not_a_kill(tmp_path):
    root = _tree(tmp_path, {"tests/test_core.py": SKIP_FIRST})
    res = run_mutants(
        root, [FLIP], ["tests/test_core.py"], extra_dirs=(), forbid_skips=True, timeout=120
    )
    assert res == [("flip", Verdict.ERROR, "SKIPPED TESTS", False)]


def test_forbid_skips_refuses_a_baseline_that_skips(tmp_path):
    body = "import pytest\n\ndef test_a():\n    pytest.skip('no database')\n"
    root = _tree(tmp_path, {"tests/test_core.py": body})
    with pytest.raises(RuntimeError, match="skipped"):
        run_mutants(
            root, [FLIP], ["tests/test_core.py"], extra_dirs=(), forbid_skips=True, timeout=120
        )


def test_forbid_skips_counts_an_expected_failure_as_a_skip(tmp_path):
    body = "import pytest\n\n@pytest.mark.xfail\ndef test_a():\n    assert False\n"
    root = _tree(tmp_path, {"tests/test_core.py": body})
    with pytest.raises(RuntimeError, match="skipped"):
        run_mutants(root, [], ["tests/test_core.py"], extra_dirs=(), forbid_skips=True, timeout=120)


def test_forbid_skips_leaves_a_clean_run_alone(tmp_path):
    body = "from pk.core import go\n\ndef test_a():\n    assert go(True) is True\n"
    root = _tree(tmp_path, {"tests/test_core.py": body})
    res = run_mutants(
        root, [FLIP], ["tests/test_core.py"], extra_dirs=(), forbid_skips=True, timeout=120
    )
    assert [(n, v, good) for n, v, _, good in res] == [("flip", Verdict.KILLED, True)]


def test_skipped_tests_reads_skips_and_refuses_doctype():
    xml = (
        '<testsuites><testsuite><testcase classname="tests.test_x" name="test_a"><skipped message="s"/></testcase>'
        '<testcase classname="tests.test_x" name="test_b"/></testsuite></testsuites>'
    )
    assert skipped_tests(xml) == ["tests/test_x::test_a"]
    assert skipped_tests("<testsuites/>") == []
    with pytest.raises(ValueError):
        skipped_tests('<!DOCTYPE x [<!ENTITY e "v">]><testsuites/>')


# ---- defaults unchanged ------------------------------------------------------------------------------------------------------


def test_a_default_call_reaches_pytest_with_the_old_four_arguments_only(tmp_path, monkeypatch):
    root = _tree(tmp_path, {"tests/test_core.py": "def test_a():\n    assert True\n"})
    calls = []

    def fake(*args, **kwargs):
        calls.append((len(args), kwargs))
        return 0

    monkeypatch.setattr(mr, "_pytest", fake)
    run_mutants(root, [], ["tests/test_core.py"], extra_dirs=(), timeout=120)
    assert calls == [(4, {"plugin": "", "env_names": ()})]


def test_the_default_child_environment_has_no_database_address(tmp_path, monkeypatch):
    monkeypatch.setenv(DSN_NAME, _fake_dsn())
    seen = {}
    real = mr.subprocess.Popen

    def spy(cmd, **kw):
        seen["env"], seen["cmd"] = kw["env"], cmd
        return real(cmd, **kw)

    monkeypatch.setattr(mr.subprocess, "Popen", spy)
    (tmp_path / "t.py").write_text("def test_a():\n    assert True\n", encoding="utf-8")
    assert mr._pytest(tmp_path, ["t.py"], tmp_path / "r.xml", 60) == 0
    assert DSN_NAME not in seen["env"] and "--noconftest" in seen["cmd"]
    assert [a for a in seen["cmd"] if a.startswith("tests")] == []  # no plugin module added
    assert seen["cmd"].count("-p") == 1  # only the runner's own `-p no:cacheprovider`
    assert os.environ[DSN_NAME]


# ---- review fixes (order 194 B) ---------------------------------------------------------------------------------------------


def test_a_conftest_path_that_is_valid_but_missing_is_a_value_error_before_any_temp_folder(
    tmp_path, monkeypatch
):
    root = _tree(tmp_path, {"tests/test_core.py": "def test_a():\n    assert True\n"})
    made = []
    real = mr.tempfile.mkdtemp
    monkeypatch.setattr(mr.tempfile, "mkdtemp", lambda *a, **k: made.append(1) or real(*a, **k))
    with pytest.raises(ValueError, match="not a file of the tree"):
        run_mutants(
            root,
            [],
            ["tests/test_core.py"],
            extra_dirs=(),
            conftest="tests/conftest.py",
            timeout=120,
        )
    assert made == [], "a temp folder was made before the missing conftest was noticed"


def test_forbid_skips_with_a_missing_or_empty_junit_file_is_an_error_row_never_judged(
    tmp_path, monkeypatch
):
    root = _tree(tmp_path, {"tests/test_core.py": "def test_a():\n    assert True\n"})
    real = mr._pytest

    def fake(cwd, tests, junit, timeout, **kw):
        if junit.name == "base.xml":
            return real(cwd, tests, junit, timeout, **kw)
        return 1  # a failing exit code and NO junit file

    monkeypatch.setattr(mr, "_pytest", fake)
    res = run_mutants(
        root, [FLIP], ["tests/test_core.py"], extra_dirs=(), forbid_skips=True, timeout=120
    )
    assert res == [("flip", Verdict.ERROR, "JUNIT MISSING", False)]

    def fake_empty(cwd, tests, junit, timeout, **kw):
        if junit.name != "base.xml":
            junit.write_text("", encoding="utf-8")
            return 1
        return real(cwd, tests, junit, timeout, **kw)

    monkeypatch.setattr(mr, "_pytest", fake_empty)
    res = run_mutants(
        root, [FLIP], ["tests/test_core.py"], extra_dirs=(), forbid_skips=True, timeout=120
    )
    assert res == [("flip", Verdict.ERROR, "JUNIT MISSING", False)]


def test_judge_never_returns_killed_for_an_empty_failing_test_id():
    line = "E   AssertionError: assert 1 == 2"
    assert judge(1, "", line) is Verdict.ERROR
    assert judge(1, "", line, expect="assert 1") is Verdict.ERROR
    assert judge(1, "t.py::a", line) is Verdict.KILLED  # a named test still kills


def test_a_run_that_fails_with_no_junit_file_is_never_a_kill_even_without_forbid_skips(
    tmp_path, monkeypatch
):
    root = _tree(tmp_path, {"tests/test_core.py": "def test_a():\n    assert True\n"})
    real = mr._pytest
    monkeypatch.setattr(
        mr,
        "_pytest",
        lambda cwd, tests, junit, timeout, **kw: (
            real(cwd, tests, junit, timeout, **kw) if junit.name == "base.xml" else 1
        ),
    )
    res = run_mutants(root, [FLIP], ["tests/test_core.py"], extra_dirs=(), timeout=120)
    assert res == [("flip", Verdict.ERROR, "", False)]


FIXTURE_ASSERTS = (
    "import pytest\nfrom pk.core import go\n\n"
    "@pytest.fixture\ndef checked():\n    assert go(True) is True\n    return 1\n\n"
    "def test_a(checked):\n    assert checked == 1\n"
)


def test_a_fixture_error_in_the_mutant_run_is_an_error_row_not_a_kill(tmp_path):
    # the mutant makes the FIXTURE assert; the first line is an AssertionError, which the judge alone reads as a kill
    root = _tree(tmp_path, {"tests/test_core.py": FIXTURE_ASSERTS})
    res = run_mutants(root, [FLIP], ["tests/test_core.py"], extra_dirs=(), timeout=120)
    assert res == [("flip", Verdict.ERROR, "FIXTURE ERROR", False)]


def test_fixture_errors_reads_setup_and_teardown_errors_only():
    xml = (
        "<testsuites><testsuite>"
        '<testcase classname="tests.test_x" name="test_a"><error message="failed on setup with &quot;AssertionError&quot;">E x</error></testcase>'
        '<testcase classname="tests.test_x" name="test_b"><error message="failed on teardown with &quot;KeyError&quot;">E x</error></testcase>'
        '<testcase classname="" name="tests.test_y"><error message="collection failure">E x</error></testcase>'
        '<testcase classname="tests.test_x" name="test_c"><failure message="assert 1 == 2">E assert 1 == 2</failure></testcase>'
        "</testsuite></testsuites>"
    )
    assert fixture_errors(xml) == ["tests/test_x::test_a", "tests/test_x::test_b"]
    assert fixture_errors("<testsuites/>") == []
    with pytest.raises(ValueError):
        fixture_errors('<!DOCTYPE x [<!ENTITY e "v">]><testsuites/>')


def test_a_mutant_whose_old_text_is_absent_is_an_error_not_a_kill(tmp_path):
    root = _tree(tmp_path, {"tests/test_core.py": "def test_a():\n    assert True\n"})
    gone = Mutant("gone", "src/pk/core.py", "text that is not there", "x", "assert")
    res = run_mutants(root, [gone], ["tests/test_core.py"], extra_dirs=(), timeout=120)
    assert res == [("gone", Verdict.ERROR, "SNIPPET NOT FOUND", False)]


def _secret_dsn() -> tuple[str, str]:
    user, head, tail = "svc_user", "Zq9x", "K4mTw"
    word = head + tail  # built from parts
    return f"postgresql://{user}:{word}@db.invalid/scratch", word


def test_pass_env_values_never_reach_first_lines_rows_or_the_baseline_error(tmp_path, monkeypatch):
    dsn, word = _secret_dsn()
    monkeypatch.setenv(DSN_NAME, dsn)
    # the failing assertion prints the value (pytest shows both sides), and the test id carries it too
    body = (
        "import os\nimport pytest\nfrom pk.core import go\n\n"
        f"@pytest.mark.parametrize('v', [{dsn!r}])\n"
        f"def test_a(v):\n    assert go(True) is True\n    assert os.environ[{DSN_NAME!r}] == v\n    assert os.environ[{DSN_NAME!r}] == 'other'\n"
    )
    root = _tree(tmp_path, {"tests/test_core.py": "def test_a():\n    assert True\n"})
    (root / "tests" / "test_core.py").write_text(body, encoding="utf-8")
    # baseline fails (the last assert): the error text names no value
    with pytest.raises(RuntimeError) as err:
        run_mutants(
            root, [FLIP], ["tests/test_core.py"], extra_dirs=(), pass_env=(DSN_NAME,), timeout=120
        )
    assert dsn not in str(err.value) and word not in str(err.value)
    # a passing baseline and a failing mutant whose first line shows the value
    ok = (
        "import os\nimport pytest\nfrom pk.core import go\n\n"
        f"@pytest.mark.parametrize('v', [{dsn!r}])\n"
        f"def test_a(v):\n    assert go(True) == (os.environ[{DSN_NAME!r}] == v), os.environ[{DSN_NAME!r}]\n"
    )
    (root / "tests" / "test_core.py").write_text(ok, encoding="utf-8")
    lines: dict[str, str] = {}
    res = run_mutants(
        root,
        [FLIP],
        ["tests/test_core.py"],
        extra_dirs=(),
        pass_env=(DSN_NAME,),
        first_lines=lines,
        timeout=120,
    )
    shown = repr((res, lines))
    assert word not in shown and dsn not in shown, shown
    assert "[REDACTED]" in lines["flip"], lines


def test_masked_replaces_the_value_and_the_url_password():
    dsn, word = _secret_dsn()
    assert mr._secret_values(()) == ()
    os.environ[DSN_NAME] = dsn
    try:
        secrets = mr._secret_values((DSN_NAME,))
    finally:
        del os.environ[DSN_NAME]
    assert set(secrets) == {dsn, word}
    out = mr._masked(f"E assert {dsn} and only {word} here", secrets)
    assert dsn not in out and word not in out
