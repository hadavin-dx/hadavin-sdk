"""Tests of the three opt-in keywords of ``tools.mutation_runner.run_mutants`` (``conftest``, ``pass_env``, ``forbid_skips``) and of the
changes that are always on (the ``FIXTURE ERROR`` row and the judge's ERROR for a failing run that names no test: two changes of
result; plus the ``COLLECTION ERROR`` label, which only renames a row that was already ERROR).

Class: a mutant that "dies" because the tests could not run (skipped, or no database address, or a missing fixture file, or a fixture that
failed) is a FALSE kill. The fix sits at the runner (one choke point for every caller). Without a keyword the arguments of a run are the
old ones, and the only changed results are the always-on ones, each tested below.

Most killer tests give their assertion a message that names the guard (``_must_refuse`` and ``_must_raise`` write one too), so the
mutants in ``tests/mutation_runner_mutants.py`` can tell which guard was removed from the first line of the failure.
"""

import contextlib
import errno
import hashlib
import importlib.util
import itertools
import json
import os
import re
import stat
import sys
import threading
import time
from pathlib import Path

import pytest
from tools import mutation_runner as mr
from tools.mutation_runner import PASS_ENV_ALLOWED, Mutant, run_mutants

from hadavin_sdk.testing.mutation import (
    Verdict,
    fixture_errors,
    judge,
    read_junit,
    skipped_tests,
)

DSN_NAME = "HADAVIN_TEST_PG_DSN"
SENTINEL = "sentinel-of-the-test-guard"  # not an address: nothing may ever connect to it
FLIP = Mutant("flip", "src/pk/core.py", "return flag", "return not flag", "assert")
CORE_TEST = "tests/test_core.py"


@contextlib.contextmanager
def _dsn_left_as_found():
    """Put a sentinel in the database address variable for the length of the block and prove the block left it exactly as it was. The
    caller's real value (CI sets one) is put back afterwards whatever happens, so one failing test can never hide a later database test."""
    before = os.environ.get(DSN_NAME)
    os.environ[DSN_NAME] = SENTINEL
    try:
        yield
        assert os.environ.get(DSN_NAME) == SENTINEL, (
            f"a test changed or removed {DSN_NAME} and did not put it back (use monkeypatch)"
        )
    finally:
        if before is None:
            os.environ.pop(DSN_NAME, None)
        else:
            os.environ[DSN_NAME] = before


@pytest.fixture(autouse=True)
def _guard_the_database_address():
    # set up before the test's own ``monkeypatch`` and checked after it has undone its changes: only a direct os.environ write is caught
    with _dsn_left_as_found():
        yield


@pytest.fixture(autouse=True)
def _own_lock_folder(_guard_the_database_address, tmp_path, monkeypatch):
    # asks for the guard first, so the guard is set up before this ``monkeypatch`` and checked after it is undone
    monkeypatch.setattr(
        mr, "_lock_dir", lambda: tmp_path
    )  # each test its own lock folder: two test processes never share a lock


def test_the_guard_fails_a_test_that_deletes_the_database_address_and_puts_nothing_back():
    # the old body of the masking test did exactly this: ``os.environ[DSN] = x`` ... ``del os.environ[DSN]`` in a ``finally``
    with pytest.raises(AssertionError, match="did not put it back"), _dsn_left_as_found():
        del os.environ[DSN_NAME]
    assert os.environ[DSN_NAME] == SENTINEL  # the outer guard's value is back in place
    with pytest.raises(AssertionError, match="did not put it back"), _dsn_left_as_found():
        os.environ[DSN_NAME] = "another value"
    assert os.environ[DSN_NAME] == SENTINEL


def _must_refuse(label, call, *args, **kwargs):
    """``call`` must raise ``ValueError``; otherwise the first assertion line is ``<label>: was not refused`` (another error, a ``TypeError`` from a missing keyword for example, is a failure of its own)."""
    try:
        call(*args, **kwargs)
    except ValueError:
        return
    raise AssertionError(f"{label}: was not refused")


def _must_raise(label, error, call, *args, match="", **kwargs):
    """``call`` must raise ``error`` (its text holding ``match``); otherwise the first assertion line says ``label``."""
    try:
        call(*args, **kwargs)
    except error as exc:
        assert match in str(exc), f"{label}: raised another message: {exc}"
        return
    raise AssertionError(f"{label}: nothing was raised")


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


def _run(root: Path, mutants=(), **kw):
    return run_mutants(root, list(mutants), [CORE_TEST], extra_dirs=(), timeout=120, **kw)


def _short(rows):
    return [(n, v, good) for n, v, _, good in rows]


def _fake_dsn() -> str:
    user, secret = "someone", "pw"  # built from parts: no URL with a password stands in the source
    return f"postgresql://{user}:{secret}@db.invalid/x"


def _secret_dsn() -> tuple[str, str]:
    user, head, tail = "svc_user", "Zq9x", "K4mTw"
    word = head + tail  # built from parts
    return f"postgresql://{user}:{word}@db.invalid/scratch", word


SKIP_FIRST = (
    "import pytest\nfrom pk.core import go\n\n"
    "def test_setup_works():\n    if go(False) is not False:\n        pytest.skip('cannot run here')\n\n"
    "def test_a():\n    assert go(True) is True\n"
)
PASSES = "def test_a():\n    assert True\n"
USES_GO = "from pk.core import go\n\ndef test_a():\n    assert go(True) is True\n"


# ---- conftest ---------------------------------------------------------------------------------------------------------------


CONFTEST_FIXTURE = "import pytest\n\n@pytest.fixture\ndef answer():\n    return 42\n"
USES_FIXTURE = "def test_a(answer):\n    assert answer == 42\n"


def test_conftest_loads_the_given_file_as_a_plugin_and_without_it_nothing_is_loaded(tmp_path):
    root = _tree(tmp_path, {"tests/conftest.py": CONFTEST_FIXTURE, CORE_TEST: USES_FIXTURE})
    try:
        rows = _run(root, conftest="tests/conftest.py")
    except RuntimeError as exc:
        raise AssertionError(f"the conftest was not loaded for the baseline: {exc}") from None
    assert rows == [], "a run with no mutants returned a row"
    # the default is unchanged: --noconftest, so the fixture is missing and the unmutated copy fails
    _must_raise(
        "the default run loaded a conftest", RuntimeError, _run, root, match="does not pass"
    )


def test_a_mutant_is_judged_with_the_conftest_loaded(tmp_path):
    body = "from pk.core import go\n\ndef test_a(answer):\n    assert answer == 42\n    assert go(True) is True\n"
    root = _tree(tmp_path, {"tests/conftest.py": CONFTEST_FIXTURE, CORE_TEST: body})
    rows = _run(root, [FLIP], conftest="tests/conftest.py")
    assert _short(rows) == [("flip", Verdict.KILLED, True)], (
        f"the mutant run was not judged with the conftest loaded: {rows}"
    )


def test_a_conftest_that_is_not_a_plain_python_path_is_refused_before_anything_runs(tmp_path):
    root = _tree(tmp_path, {CORE_TEST: PASSES})
    for bad in (
        "tests/my-conf.py",
        "tests/no:conf.py",
        "../conftest.py",
        "/abs/conftest.py",
        "-p.py",
        "@x.py",
        "tests/1x.py",
        "tésts/conftest.py",
        "tests/",
    ):
        _must_refuse(f"conftest {bad!r}", _run, root, conftest=bad)
    assert _run(root, conftest="") == [], "an empty conftest (the default) was not accepted"


def test_a_conftest_with_a_python_keyword_part_is_refused():
    for bad in ("tests/class.py", "tests/import.py", "class/conftest.py"):
        _must_refuse(f"a keyword part in {bad!r}", mr._plugin_module, bad)


def test_a_conftest_with_a_non_ascii_part_is_refused():
    for bad in ("tests/café.py", "tests/ä.py"):  # identifiers for Python, but not plain ASCII
        _must_refuse(f"a non-ascii part in {bad!r}", mr._plugin_module, bad)


def test_a_conftest_that_does_not_end_in_py_is_refused():
    for bad in ("tests/conftest.txt", "tests/conftest", "tests/conftest.pyx"):
        _must_refuse(f"a conftest without the .py ending: {bad!r}", mr._plugin_module, bad)


def test_a_conftest_must_be_called_conftest_or_lie_in_a_tests_folder(tmp_path):
    root = _tree(tmp_path, {CORE_TEST: PASSES})
    (root / "src" / "pk" / "conftest.py").write_text("", encoding="utf-8")
    (root / "tests" / "plugin.py").write_text("", encoding="utf-8")
    for bad in ("src/pk/core.py", "src/pk/__init__.py", "plugin.py"):
        _must_refuse(
            f"a tree file that is no conftest and no test helper: {bad!r}", mr._plugin_module, bad
        )
        if (root / bad).is_file():  # the run refuses it too, though the file exists
            _must_refuse(f"the run took {bad!r} as a conftest", _run, root, conftest=bad)
    # both accepted forms: the name conftest.py anywhere, and any .py file under a folder called tests
    assert _run(root, conftest="src/pk/conftest.py") == [], "conftest.py outside tests was refused"
    assert _run(root, conftest="tests/plugin.py") == [], "a helper under tests was refused"


def test_a_conftest_path_that_is_valid_but_missing_is_a_value_error_before_any_temp_folder(
    tmp_path, monkeypatch
):
    root = _tree(tmp_path, {CORE_TEST: PASSES})
    made = []
    real = mr.tempfile.mkdtemp
    monkeypatch.setattr(mr.tempfile, "mkdtemp", lambda *a, **k: made.append(1) or real(*a, **k))
    caught: ValueError | OSError | None = None
    try:
        _run(root, conftest="tests/conftest.py")
    except (ValueError, OSError) as exc:
        caught = exc
    assert caught is not None, "a missing conftest was accepted"
    assert isinstance(caught, ValueError), (
        f"a missing conftest was noticed late, as {type(caught).__name__}"
    )
    assert "not a file of the tree" in str(caught), f"refused with another message: {caught}"
    assert made == [], "a temp folder was made before the missing conftest was noticed"


# ---- pass_env ---------------------------------------------------------------------------------------------------------------


READS_DSN = (
    f"import os\n\ndef test_a():\n    assert os.environ.get({DSN_NAME!r}) == {_fake_dsn()!r}\n"
)


def test_pass_env_hands_the_listed_variable_to_the_child_and_default_does_not(
    tmp_path, monkeypatch
):
    monkeypatch.setenv(DSN_NAME, _fake_dsn())
    root = _tree(tmp_path, {CORE_TEST: READS_DSN})
    assert _run(root, pass_env=(DSN_NAME,)) == [], "the listed variable did not reach the child"
    _must_raise(
        "the default run passed the variable", RuntimeError, _run, root, match="does not pass"
    )


def test_a_mutant_run_sees_the_passed_variable(tmp_path, monkeypatch):
    monkeypatch.setenv(DSN_NAME, _fake_dsn())
    body = (
        f"import os\nfrom pk.core import go\n\ndef test_a():\n    assert os.environ.get({DSN_NAME!r}) == {_fake_dsn()!r}, 'the variable is missing'\n"
        "    assert go(True) is True, 'the flip was seen'\n"
    )
    root = _tree(tmp_path, {CORE_TEST: body})
    lines: dict[str, str] = {}
    flip_seen = Mutant(
        "flip", "src/pk/core.py", "return flag", "return not flag", "the flip was seen"
    )
    rows = _run(root, [flip_seen], pass_env=(DSN_NAME,), first_lines=lines)
    assert _short(rows) == [("flip", Verdict.KILLED, True)], (
        f"the mutant run did not see the passed variable: {rows}"
    )
    assert "the flip was seen" in lines["flip"], (
        f"the mutant run did not see the passed variable: {lines}"
    )


def test_pass_env_never_widens_to_other_variables(tmp_path, monkeypatch):
    monkeypatch.setenv(DSN_NAME, _fake_dsn())
    monkeypatch.setenv("SOME_API_TOKEN", "tok")
    body = "import os\n\ndef test_a():\n    assert 'SOME_API_TOKEN' not in os.environ\n"
    root = _tree(tmp_path, {CORE_TEST: body})
    assert _run(root, pass_env=(DSN_NAME,)) == [], "another variable reached the child"


def test_pass_env_with_an_unset_variable_passes_nothing(tmp_path, monkeypatch):
    monkeypatch.delenv(DSN_NAME, raising=False)
    body = f"import os\n\ndef test_a():\n    assert {DSN_NAME!r} not in os.environ\n"
    root = _tree(tmp_path, {CORE_TEST: body})
    assert _run(root, pass_env=(DSN_NAME,)) == [], "an unset variable was passed"


UNLISTED_NAMES = (
    ("SOME_API_TOKEN",),
    ("AWS_SECRET_ACCESS_KEY",),
    (DSN_NAME, "PATH"),
    (DSN_NAME.lower(),),
    (DSN_NAME + " ",),
    ("A=B",),
    ("",),
)


def test_an_unlisted_env_name_is_refused_before_anything_runs(tmp_path, monkeypatch):
    monkeypatch.setenv("SOME_API_TOKEN", "tok")
    root = _tree(tmp_path, {CORE_TEST: PASSES})
    seen = []
    monkeypatch.setattr(mr, "_pytest", lambda *a, **k: seen.append(a) or 0)
    for names in UNLISTED_NAMES:
        _must_refuse("an unlisted pass_env name was accepted", _run, root, pass_env=names)
        assert seen == [], "a refused name must not start a single pytest run"


def test_the_pytest_step_refuses_an_unlisted_env_name_by_itself(tmp_path):
    (tmp_path / "t.py").write_text(PASSES, encoding="utf-8")
    _must_refuse(
        "the pytest step passed an unlisted name",
        mr._pytest,
        tmp_path,
        ["t.py"],
        tmp_path / "r.xml",
        60,
        env_names=("SOME_API_TOKEN",),
    )
    assert not (tmp_path / "r.xml").exists(), "pytest was started for a refused name"


def test_a_bare_string_for_pass_env_is_refused_not_read_letter_by_letter(tmp_path):
    root = _tree(tmp_path, {CORE_TEST: PASSES})
    caught = None
    try:
        _run(root, pass_env=DSN_NAME)
    except (TypeError, ValueError) as exc:
        caught = exc
    assert isinstance(caught, TypeError), f"a bare string was read as names: {caught!r}"
    assert "not one string" in str(caught), f"another refusal: {caught}"


def test_property_no_name_outside_the_allowlist_is_ever_accepted():
    # 500 fixed pseudo-random names (hash prefixes of 0..499, lengths 0..39), the same every run
    names = [hashlib.sha256(str(i).encode()).hexdigest()[: i % 40] for i in range(500)]
    names += [n + suffix for n in PASS_ENV_ALLOWED for suffix in ("_", "2", " ", "\n", "\x00")]
    for name in names:
        if name in PASS_ENV_ALLOWED:
            continue
        _must_refuse(f"the name {name!r} was accepted", mr._checked_env_names, (name,))
    assert mr._checked_env_names(PASS_ENV_ALLOWED) == PASS_ENV_ALLOWED


def test_property_the_allowlist_holds_only_the_test_database_address():
    assert PASS_ENV_ALLOWED == (DSN_NAME,)
    assert not set(PASS_ENV_ALLOWED) & {
        "PATH",
        "HOME",
    }  # already inherited names are not what this is for


# ---- pass_env: masking ------------------------------------------------------------------------------------------------------


def _showing_value_tree(tmp_path, dsn):
    """A tree whose test fails after the flip and whose failure line and test id both show the value."""
    body = (
        "import os\nimport pytest\nfrom pk.core import go\n\n"
        f"@pytest.mark.parametrize('v', [{dsn!r}])\n"
        f"def test_a(v):\n    assert go(True) == (os.environ[{DSN_NAME!r}] == v), os.environ[{DSN_NAME!r}]\n"
    )
    return _tree(tmp_path, {CORE_TEST: body})


def test_pass_env_values_never_reach_first_lines(tmp_path, monkeypatch):
    dsn, word = _secret_dsn()
    monkeypatch.setenv(DSN_NAME, dsn)
    lines: dict[str, str] = {}
    _run(_showing_value_tree(tmp_path, dsn), [FLIP], pass_env=(DSN_NAME,), first_lines=lines)
    assert word not in lines["flip"] and dsn not in lines["flip"], (
        "the passed value reached first_lines"
    )
    assert "[REDACTED]" in lines["flip"], f"the failure line was not shown with a marker: {lines}"


def test_pass_env_values_never_reach_the_failing_test_id_of_a_row(tmp_path, monkeypatch):
    dsn, word = _secret_dsn()
    monkeypatch.setenv(DSN_NAME, dsn)
    shows_value = Mutant("flip", "src/pk/core.py", "return flag", "return not flag", "postgresql")
    rows = _run(_showing_value_tree(tmp_path, dsn), [shows_value], pass_env=(DSN_NAME,))
    assert len(rows) == 1 and rows[0][1] is Verdict.KILLED, rows
    assert word not in rows[0][2] and dsn not in rows[0][2], (
        "the passed value reached the test id of a row"
    )
    assert "[REDACTED]" in rows[0][2], f"the test id was not shown with a marker: {rows[0][2]}"


def test_the_baseline_skip_message_never_holds_the_passed_value(tmp_path, monkeypatch):
    dsn, word = _secret_dsn()
    monkeypatch.setenv(DSN_NAME, dsn)
    body = (
        "import pytest\n\n"
        f"@pytest.mark.parametrize('v', [{dsn!r}])\n"
        "def test_a(v):\n    pytest.skip('no database')\n"
    )
    root = _tree(tmp_path, {CORE_TEST: body})
    refusal = ""
    try:
        _run(root, [FLIP], pass_env=(DSN_NAME,), forbid_skips=True)
    except RuntimeError as exc:
        refusal = str(exc)
    assert "skipped" in refusal, (
        f"a baseline that skips was accepted or refused otherwise: {refusal!r}"
    )
    assert dsn not in refusal and word not in refusal, (
        "the baseline skip message held the passed value"
    )


def test_masked_replaces_the_value_and_the_url_password(monkeypatch):
    dsn, word = _secret_dsn()
    assert mr._secret_values(()) == (), "no names must give no secrets"
    monkeypatch.setenv(DSN_NAME, dsn)
    secrets = mr._secret_values((DSN_NAME,))
    assert set(secrets) == {dsn, word}, (
        f"the secrets were not the value and its password: {secrets}"
    )
    out = mr._masked(f"E assert {dsn} and only {word} here", secrets)
    assert dsn not in out and word not in out, "a secret survived the masking"


def test_a_percent_encoded_password_is_masked_in_both_forms(monkeypatch):
    first, second = "Qw7", "Rt5"
    raw = (
        first + "%40" + second
    )  # the URL carries the encoded form; a test may print the decoded one
    decoded = first + "@" + second
    monkeypatch.setenv(DSN_NAME, f"postgresql://svc:{raw}@db.invalid/scratch")
    secrets = mr._secret_values((DSN_NAME,))
    assert raw in secrets and decoded in secrets, (
        f"the decoded password was not a secret: {secrets}"
    )
    out = mr._masked(f"E {raw} and {decoded}", secrets)
    assert raw not in out and decoded not in out, "a form of the password survived the masking"


def _long_value() -> str:
    # 300 characters in a pattern no ordinary text has; built from parts, never a real credential
    return "".join(f"{hashlib.sha256(str(i).encode()).hexdigest()[:10]}-" for i in range(27))[:300]


def _key_value_value() -> tuple[str, str]:
    """A 60-character key=value address (no URL) with the password at the tail, and that password; built from parts."""
    head = "host=db.invalid dbname=scratch user=svc password="
    word = hashlib.sha256(b"fragment").hexdigest()[: 60 - len(head)]
    return head + word, word


def _windows(secret: str, size: int = 6) -> set[str]:
    return {secret[i : i + size] for i in range(len(secret) - size + 1)}


def test_a_shortened_value_is_masked_by_its_fragments(monkeypatch):
    for value in (_key_value_value()[0], _long_value()):
        monkeypatch.setenv(DSN_NAME, value)
        secrets = mr._secret_values((DSN_NAME,))
        shown = f"E   AssertionError: assert '{value[:12]}...{value[-12:]}' == 'other'"
        out = mr._masked(shown, secrets)
        assert not any(w in out for w in _windows(value)), (
            f"a fragment of the shortened value survived the masking: {out}"
        )
        assert "AssertionError: assert" in out and "== 'other'" in out, (
            f"the line was not kept around the markers: {out}"
        )
    assert mr._masked("E   x == 'a...l'", ("abcdefghijkl",)) == "E   x == 'a...l'", (
        "a one-character piece next to the dots was masked"
    )
    assert (
        mr._masked("E   x == 'ab...kl'", ("abcdefghijkl",)) == "E   x == [REDACTED]...[REDACTED]"
    ), "a two-character head or tail next to the dots was not masked"
    assert mr._masked("E   x == 'abc...def'", ("abcdefghijkl",)) == "E   x == [REDACTED]...def'", (
        "a head of 3 characters next to the dots was not masked, or a piece that is not the end of the secret was"
    )


def _plain_compare_tree(tmp_path, value):
    # the plainest failing line there is: no message of the test's own, so what shows is what pytest prints
    body = (
        "import os\nfrom pk.core import go\n\n"
        f"def test_a():\n    v = os.environ[{DSN_NAME!r}]\n    if go(True) is not True:\n        assert v == 'other'\n"
    )
    return _tree(tmp_path, {CORE_TEST: body})


def test_pass_env_values_shortened_by_pytest_never_reach_first_lines(tmp_path, monkeypatch):
    for n, value in enumerate((_key_value_value()[0], _long_value())):
        monkeypatch.setenv(DSN_NAME, value)
        root = _plain_compare_tree(tmp_path / str(n), value)
        # positive control: with the masking off, the line really holds a fragment (so the check below can fail)
        with monkeypatch.context() as m:
            m.setattr(mr, "_masked", lambda text, secrets: text)
            seen: dict[str, str] = {}
            _run(root, [FLIP], pass_env=(DSN_NAME,), first_lines=seen)
        assert any(w in seen["flip"] for w in _windows(value)), (
            f"the positive control failed: pytest printed no fragment of the value: {seen}"
        )
        lines: dict[str, str] = {}
        _run(root, [FLIP], pass_env=(DSN_NAME,), first_lines=lines)
        assert not any(w in lines["flip"] for w in _windows(value)), (
            f"a fragment of the shortened value reached first_lines: {lines}"
        )


def test_a_password_after_a_password_word_or_in_a_url_query_is_a_secret(monkeypatch):
    value, word = _key_value_value()
    monkeypatch.setenv(DSN_NAME, value)
    assert word in mr._secret_values((DSN_NAME,)), (
        "the password of a key=value address was not a secret"
    )
    query = "postgresql://db.invalid/scratch?sslmode=require&password=" + "Tk8" + "%2F" + "Vq2&x=1"
    monkeypatch.setenv(DSN_NAME, query)
    secrets = mr._secret_values((DSN_NAME,))
    assert "Tk8%2FVq2" in secrets and "Tk8/Vq2" in secrets, (
        f"the password of a URL query was not a secret: {secrets}"
    )
    monkeypatch.setenv(DSN_NAME, "host=db.invalid user=svc")
    assert mr._secret_values((DSN_NAME,)) == ("host=db.invalid user=svc",), (
        "a value with no password word gave another secret"
    )


def test_a_value_with_a_backslash_is_masked_as_repr_prints_it(monkeypatch):
    word = "Ab3" + "\\" + "Xy9Zq1"  # one backslash: repr and many log formats print it doubled
    monkeypatch.setenv(DSN_NAME, "host=db.invalid user=svc password=" + word)
    secrets = mr._secret_values((DSN_NAME,))
    assert "\\\\" in repr(word)  # the positive control: the doubled form is really a different text
    out = mr._masked(f"E {word!r}", secrets)
    assert "Xy9Zq1" not in out, (
        f"the repr form of a value with a backslash survived the masking: {out}"
    )
    assert word in mr._masked(f"E {word}", ()), (
        "the control is wrong: nothing masks without secrets"
    )
    assert "Xy9Zq1" not in mr._masked(f"E {word}", secrets), "the plain form survived the masking"
    # a value with both quote marks: repr writes a backslash before the single quote, which unicode_escape does not
    both = (
        "host=db.invalid user=svc password=Ab3'Xy9" + '"' + "Zq1\u00e9"
    )  # a non-ASCII letter too: no other form prints it raw
    assert "\\'" in repr(both)
    monkeypatch.setenv(DSN_NAME, both)
    out = mr._masked(f"E {both!r}", mr._secret_values((DSN_NAME,)))
    assert "Xy9" not in out, (
        f"the repr form of a value with both quote marks survived the masking: {out}"
    )


def test_a_value_with_a_non_ascii_letter_is_masked_as_unicode_escape_prints_it(monkeypatch):
    word = "Ab3" + chr(233) + "Xy9Zq1"  # unicode_escape prints the letter as a backslash and x e 9
    monkeypatch.setenv(DSN_NAME, "host=db.invalid user=svc password=" + word)
    secrets = mr._secret_values((DSN_NAME,))
    shown = word.encode("unicode_escape").decode("ascii")
    assert shown != word
    out = mr._masked(f"E {shown}", secrets)
    assert "Xy9Zq1" not in out, (
        f"the unicode_escape form of a non-ASCII value survived the masking: {out}"
    )


def _secrets_of(value: str, monkeypatch) -> tuple[str, ...]:
    monkeypatch.setenv(DSN_NAME, value)
    return mr._secret_values((DSN_NAME,))


def test_passwd_and_pwd_words_and_a_quoted_password_are_secrets(monkeypatch):
    base = "host=db.invalid user=svc "
    assert "Hk4Lm8Pq2" in _secrets_of(base + "passwd=Hk4Lm8Pq2", monkeypatch), (
        "the password after passwd= was not a secret"
    )
    assert "Hk4Lm8Pq2" in _secrets_of(base + "pwd=Hk4Lm8Pq2", monkeypatch), (
        "the password after pwd= was not a secret"
    )
    assert "Hk4Lm8Pq2" in _secrets_of(base + "PWD=Hk4Lm8Pq2", monkeypatch), (
        "the password after PWD= was not a secret"
    )
    assert "Hk4 Lm8 Pq2" in _secrets_of(base + "password='Hk4 Lm8 Pq2'", monkeypatch), (
        "a quoted password with spaces was not a secret"
    )
    assert "Hk4 Lm8 Pq2" in _secrets_of(base + 'password="Hk4 Lm8 Pq2"', monkeypatch), (
        "a double-quoted password with spaces was not a secret"
    )


def test_a_piece_of_exactly_the_edge_minimum_is_masked_and_a_shorter_one_is_not():
    secret = "Qw7xK2mTp9" + "Zr4Vb8Nc3L"  # built from parts
    head6 = mr._masked(f"E x == '{secret[:6]}...zzz'", (secret,))
    assert secret[:6] not in head6, f"a 6-character head next to the dots was not masked: {head6}"
    tail6 = mr._masked(f"E x == 'zzz...{secret[-6:]}'", (secret,))
    assert secret[-6:] not in tail6, f"a 6-character tail next to the dots was not masked: {tail6}"
    head2 = mr._masked(f"E x == '{secret[:2]}...zzz'", (secret,))
    assert secret[:2] not in head2, f"a 2-character head next to the dots was not masked: {head2}"
    with pytest.MonkeyPatch.context() as only_raw:
        only_raw.setattr(mr, "_stripped_spans", lambda text, bases, dots: [])
        raw = mr._masked(f"E x == '{secret[:1]}...zzz'", (secret,))
    assert secret[:1] in raw, (
        f"a 1-character head was masked by the raw scan, below the minimum: {raw}"
    )
    short = mr._masked(f"E x == '{secret[:1]}...zzz'", (secret,))
    assert secret[:1] in short, (
        f"a 1-character head was masked by the edge pattern, below the minimum: {short}"
    )
    tail = mr._masked(f"E x == 'zzz...{secret[-1:]}'", (secret,))
    assert secret[-1:] in tail, (
        f"a 1-character tail was masked by the edge pattern, below the minimum: {tail}"
    )


class _Det:
    """A seeded, repeatable source of choices (a hash stream): the property tests need no random library and no secret-grade randomness."""

    def __init__(self, seed: int) -> None:
        self._seed, self._n = seed, 0

    def randint(self, lo: int, hi: int) -> int:
        self._n += 1
        digest = hashlib.sha256(f"{self._seed}:{self._n}".encode()).digest()
        return lo + int.from_bytes(digest[:8], "big") % (hi - lo + 1)

    def choice(self, items: str) -> str:
        return items[self.randint(0, len(items) - 1)]


def _printed_forms(value: str) -> dict[str, str]:
    """The ways a value may be printed in an assertion line or a log line."""
    return {
        "raw": value,
        "repr": repr(value)[1:-1],
        "unicode_escape": value.encode("unicode_escape").decode("ascii"),
        "json": json.dumps(value)[1:-1],
        "json_utf8": json.dumps(value, ensure_ascii=False)[1:-1],
        "bytes": repr(value.encode("utf-8"))[2:-1],
    }


JSON_VALUE = (
    "host=db.invalid user=svc password=" + 'Ab3"' + chr(1) + chr(233) + "Xy9Zq1"
)  # a quote, a control character and a non-ASCII letter: only the UTF-8 JSON form writes the control character as \\u0001 and the letter as it is


def test_a_value_is_masked_as_json_writes_it(monkeypatch):
    monkeypatch.setenv(DSN_NAME, JSON_VALUE)
    secrets = mr._secret_values((DSN_NAME,))
    out = mr._masked('{"dsn": "' + _printed_forms(JSON_VALUE)["json"] + '"}', secrets)
    assert "Xy9Zq1" not in out, f"the ASCII JSON form survived the masking: {out}"
    out = mr._masked('{"dsn": "' + _printed_forms(JSON_VALUE)["json_utf8"] + '"}', secrets)
    assert "Xy9Zq1" not in out, f"the UTF-8 JSON form survived the masking: {out}"


def test_a_value_is_masked_as_the_repr_of_its_bytes_prints_it(monkeypatch):
    monkeypatch.setenv(DSN_NAME, JSON_VALUE)
    secrets = mr._secret_values((DSN_NAME,))
    out = mr._masked("E   b'" + _printed_forms(JSON_VALUE)["bytes"] + "'", secrets)
    assert "Xy9Zq1" not in out, f"the repr of the UTF-8 bytes survived the masking: {out}"


def test_masking_removes_a_random_value_in_every_printed_form_whole_or_shortened(monkeypatch):
    """Property test (seeded, no extra library): for random values with quotes, backslashes, non-ASCII letters and control characters,
    no printed form of the value survives ``_masked``, and neither does a head or tail piece of 6 or more characters next to ``...``
    (what pytest prints for a long text). A piece is searched as a window of the printed form, so the check is stricter than the rule."""
    rng = _Det(20261110)
    alphabet = (
        "abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        + "'\""
        + "\\"
        + chr(233)
        + chr(252)
        + "\t\n%+;&"
    )
    for n in range(150):
        core = "".join(rng.choice(alphabet[:56]) for _ in range(rng.randint(8, 16)))
        pad = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 6)))
        value = f"host=db.invalid user=svc password={pad}{core}"
        monkeypatch.setenv(DSN_NAME, value)
        secrets = mr._secret_values((DSN_NAME,))
        for extra in (
            "'",
            '"',
        ):  # the same value inside a larger text that holds the other quote kind: repr picks its quote from the whole text
            larger = repr(extra + value + extra)[1:-1]
            inside = mr._masked(f"E   assert {larger} == 1", secrets)
            assert core not in inside, (
                f"case {n}: a value inside a larger text with {extra} survived: {inside!r}"
            )
            as_ascii = ascii(extra + value + extra)[1:-1]
            inside = mr._masked(f"E   assert {as_ascii} == 1", secrets)
            assert core not in inside, (
                f"case {n}: the ascii() form inside a larger text with {extra} survived: {inside!r}"
            )
            in_bytes = repr((extra + value + extra).encode("utf-8"))[2:-1]
            inside = mr._masked(f"E   assert b{extra}{in_bytes}{extra} == 1", secrets)
            assert core not in inside, (
                f"case {n}: the bytes form inside larger bytes with {extra} survived: {inside!r}"
            )
            again = repr(json.dumps(value))[1:-1]
            inside = mr._masked(f"E   assert {again} == 1", secrets)
            assert core not in inside, (
                f"case {n}: the repr of a JSON text of the value survived: {inside!r}"
            )
        for name, printed in _printed_forms(value).items():
            whole = mr._masked(f"E   AssertionError: assert '{printed}' == 'other'", secrets)
            assert core not in whole and printed not in whole, (
                f"case {n}: the {name} form of a random value survived: {whole!r}"
            )
            if len(printed) < 30:
                continue
            cut = f"E   AssertionError: assert '{printed[:12]}...{printed[-13:]}' == 'other'"
            out = mr._masked(cut, secrets)
            windows = {printed[i : i + 6] for i in range(len(printed) - 5)}
            left = [w for w in windows if w in out]
            assert not left, f"case {n}: the {name} form shortened by pytest left {left} in {out!r}"


def test_a_short_secret_inside_a_shortened_long_one_does_not_hide_the_long_one():
    # found by the property test: cutting the short long_value out first changed the text, and the tail of the long one no longer matched
    long_value = "north-river-stone-bridge-glacier-delta"  # readable words: 38 characters, more than the 12 + 13 shown
    shown = f"E   assert '{long_value[:12]}...{long_value[-13:]}' == 'other'"
    out = mr._masked(shown, (long_value, "ta"))
    assert "glacier" not in out and "north-" not in out, (
        f"a short secret inside the tail hid the shortened long secret: {out}"
    )


def test_a_line_with_a_hostile_number_of_dots_is_replaced_fast(monkeypatch):
    value, _word = _key_value_value()
    monkeypatch.setenv(DSN_NAME, value)
    secrets = mr._secret_values((DSN_NAME,))
    line = "E   " + (value[:6] + "...") * 20000 + value[-13:]
    start = time.monotonic()
    out = mr._masked(line, secrets)
    took = time.monotonic() - start
    assert "more than" in out and value[:6] not in out, (
        f"a line with a hostile number of dots was not replaced as a whole: {out[:80]!r}"
    )
    # the marker above is the exact check; this bound only catches a scan that takes minutes, so a slow machine does not fail it
    assert took < 30, f"the check of a hostile line took {took:.1f} seconds"
    assert mr._masked("E   x == 'abc...def'", secrets) == "E   x == 'abc...def'", (
        "an honest line with dots was replaced"
    )


def _dots(text):
    return list(re.finditer(r"(?=\.\.\.)", text))


def test_the_fragment_scan_agrees_with_the_plain_definition():
    """The scan was rewritten to be fast; it must still return the spans of the plain definition (every length from the largest down)."""
    rng = _Det(7)
    for _ in range(300):
        secret = "".join(rng.choice("abcd") for _ in range(rng.randint(3, 20)))
        text = "".join(rng.choice("abcd.") for _ in range(rng.randint(0, 60)))
        plain: list[tuple[int, int]] = []
        for at in range(len(text) - 2):
            if text[at : at + 3] != "...":
                continue
            start, end, top = at, at + 3, len(secret) - 1
            for k in range(min(top, start), 1, -1):
                if text[start - k : start] == secret[:k]:
                    plain.append((start - k, start))
                    break
            for k in range(min(top, len(text) - end), 1, -1):
                if text[end : end + k] == secret[-k:]:
                    plain.append((end, end + k))
                    break
        assert sorted(mr._fragment_spans(text, secret, _dots(text))) == sorted(plain), (
            f"the fast scan found other spans than the plain definition: {text!r} {secret!r}"
        )
    # the largest head and tail (one character short of the whole secret) at every length, which random text almost never hits
    for size in range(3, 21):
        secret = "".join("pqrstuvwxyz"[(i * 3 + size) % 11] for i in range(size))
        top = size - 1
        text = secret[:top] + "..." + secret[-top:]
        assert sorted(mr._fragment_spans(text, secret, _dots(text))) == [
            (0, top),
            (top + 3, len(text)),
        ], f"the largest head and tail of a {size}-character secret were not both found: {text!r}"


# ---- pass_env: the shared database ------------------------------------------------------------------------------------------


# the "database" is a file: the test fails the way a dirty database does when the earlier run left something behind
DIRTY_AFTER_FLIP = (
    "import os\nfrom pathlib import Path\nfrom pk.core import go\n\n"
    f"def test_a():\n    state = Path(os.environ[{DSN_NAME!r}])\n    assert not state.exists(), 'a leftover of an earlier run'\n"
    "    if go(True) is not True:\n        state.write_text('x')\n    assert go(True) is True\n"
)


def test_a_database_that_a_mutant_left_dirty_stops_the_run_after_that_mutant(tmp_path, monkeypatch):
    monkeypatch.setenv(DSN_NAME, str(tmp_path / "state.flag"))
    root = _tree(tmp_path, {CORE_TEST: DIRTY_AFTER_FLIP})
    other = Mutant("second", "src/pk/core.py", "return flag", "return not flag", "assert")
    seen = []
    failure = None
    try:
        _run(root, [FLIP, other], pass_env=(DSN_NAME,), on_result=seen.append)
    except mr.CanaryFailed as exc:
        failure = exc
    assert failure is not None, "a dirty database did not stop the run"
    assert "'flip'" in str(failure), f"the message does not name the mutant: {failure}"
    assert "no longer passes" in str(failure), f"another refusal: {failure}"
    assert [r[0] for r in failure.rows] == ["flip"], (
        f"the failure did not carry the rows so far: {failure.rows}"
    )
    assert [r[0] for r in seen] == ["flip"], f"the second mutant ran on a dirty database: {seen}"


def test_a_clean_database_costs_one_extra_run_per_mutant_and_changes_no_row(tmp_path, monkeypatch):
    monkeypatch.setenv(DSN_NAME, str(tmp_path / "state.flag"))
    root = _tree(tmp_path, {CORE_TEST: USES_GO})
    count = []
    real = mr._pytest
    monkeypatch.setattr(mr, "_pytest", lambda *a, **k: count.append(a[2].name) or real(*a, **k))
    rows = _run(root, [FLIP], pass_env=(DSN_NAME,))
    assert _short(rows) == [("flip", Verdict.KILLED, True)], rows
    assert count == ["base.xml", "r.xml", "again.xml"], (
        f"the unmutated copy was not run again after the mutant: {count}"
    )


def test_without_a_passed_value_there_is_no_extra_run(tmp_path, monkeypatch):
    monkeypatch.delenv(DSN_NAME, raising=False)
    root = _tree(tmp_path, {CORE_TEST: USES_GO})
    count = []
    real = mr._pytest
    monkeypatch.setattr(mr, "_pytest", lambda *a, **k: count.append(a[2].name) or real(*a, **k))
    _run(root, [FLIP], pass_env=(DSN_NAME,))
    _run(root, [FLIP])
    assert count == ["base.xml", "r.xml", "base.xml", "r.xml"], (
        f"a run with no passed value made an extra run: {count}"
    )


def test_the_canary_runs_the_unmutated_copy(tmp_path, monkeypatch):
    monkeypatch.setenv(DSN_NAME, str(tmp_path / "state.flag"))
    root = _tree(tmp_path, {CORE_TEST: USES_GO})
    try:
        rows = _run(root, [FLIP], pass_env=(DSN_NAME,))
    except RuntimeError as exc:
        raise AssertionError(f"the canary ran the mutated copy: {exc}") from None
    assert _short(rows) == [("flip", Verdict.KILLED, True)], rows


def test_a_passed_name_set_to_an_empty_text_still_gets_the_canary(tmp_path, monkeypatch):
    monkeypatch.setenv(DSN_NAME, "")
    root = _tree(tmp_path, {CORE_TEST: USES_GO})
    count = []
    real = mr._pytest
    monkeypatch.setattr(mr, "_pytest", lambda *a, **k: count.append(a[2].name) or real(*a, **k))
    _run(root, [FLIP], pass_env=(DSN_NAME,))
    assert count == ["base.xml", "r.xml", "again.xml"], (
        f"an empty passed value got no canary run: {count}"
    )


SKIPS_WHEN_THE_DATABASE_IS_GONE = (
    "import os\nimport pytest\nfrom pathlib import Path\nfrom pk.core import go\n\n"
    f"def test_a():\n    state = Path(os.environ[{DSN_NAME!r}])\n    if state.exists():\n        pytest.skip('no database')\n"
    "    if go(True) is not True:\n        state.write_text('x')\n    assert go(True) is True\n"
)


def test_a_canary_run_that_skips_is_refused_under_forbid_skips(tmp_path, monkeypatch):
    monkeypatch.setenv(DSN_NAME, str(tmp_path / "state.flag"))
    root = _tree(tmp_path, {CORE_TEST: SKIPS_WHEN_THE_DATABASE_IS_GONE})
    caught = None
    try:
        _run(root, [FLIP], pass_env=(DSN_NAME,), forbid_skips=True)
    except RuntimeError as exc:
        caught = exc
    assert caught is not None, "a canary run that skipped was accepted under forbid_skips"
    assert isinstance(caught, mr.CanaryFailed), (
        f"a canary run that skipped was not a CanaryFailed: {caught!r}"
    )
    assert "skipped" in str(caught), f"the canary skip message does not say why: {caught}"
    assert [r[:2] for r in caught.rows] == [("flip", Verdict.KILLED)], (
        f"the canary skip carried no rows of the mutants judged so far: {caught.rows}"
    )


def test_a_canary_run_that_skips_passes_without_forbid_skips(tmp_path, monkeypatch):
    # the control of the test above: the skip is what the refusal is about
    monkeypatch.setenv(DSN_NAME, str(tmp_path / "state.flag"))
    root = _tree(tmp_path, {CORE_TEST: SKIPS_WHEN_THE_DATABASE_IS_GONE})
    assert _short(_run(root, [FLIP], pass_env=(DSN_NAME,))) == [("flip", Verdict.KILLED, True)]


def test_a_copy_that_cannot_be_rebuilt_for_the_canary_is_a_clear_refusal(tmp_path, monkeypatch):
    monkeypatch.setenv(DSN_NAME, str(tmp_path / "state.flag"))
    root = _tree(tmp_path, {CORE_TEST: USES_GO})
    real, real_copy = mr._pytest, mr.shutil.copytree
    broken = []

    def after_the_mutant_run(*a, **k):
        rc = real(*a, **k)
        if a[2].name == "r.xml":
            broken.append(1)
        return rc

    def copytree(*a, **k):
        if broken:
            raise OSError("disk full")
        return real_copy(*a, **k)

    monkeypatch.setattr(mr, "_pytest", after_the_mutant_run)
    monkeypatch.setattr(mr.shutil, "copytree", copytree)
    monkeypatch.setattr(mr, "SETUP_WAIT", 0)
    caught = None
    try:
        _run(root, [FLIP], pass_env=(DSN_NAME,))
    except (RuntimeError, OSError) as exc:
        caught = exc
    assert isinstance(caught, RuntimeError), (
        f"the canary copy failure was not a clear refusal: {caught!r}"
    )
    assert "could not be rebuilt for the canary" in str(caught), f"another refusal: {caught}"


def _lock_name(value: str) -> str:
    return f"hadavin_mutation_{hashlib.sha256(value.encode()).hexdigest()[:16]}.lock"


def test_a_second_runner_with_the_same_passed_value_is_refused(tmp_path, monkeypatch):
    value = str(tmp_path / "state.flag")
    monkeypatch.setenv(DSN_NAME, value)
    root = _tree(tmp_path, {CORE_TEST: USES_GO})
    with mr._one_run_per_database([value]):
        _must_raise(
            "a second runner on the same passed value was accepted",
            RuntimeError,
            _run,
            root,
            [FLIP],
            pass_env=(DSN_NAME,),
            match="another mutation run",
        )
    assert _short(_run(root, [FLIP], pass_env=(DSN_NAME,))) == [("flip", Verdict.KILLED, True)], (
        "the lock was not given back after a run"
    )
    assert [f.name for f in tmp_path.glob("hadavin_mutation_*.lock")] == [_lock_name(value)], (
        "the lock file was not named by the first 16 hex digits of the SHA-256 of the value (and by nothing else)"
    )


def test_the_lock_is_still_held_while_the_mutants_run(tmp_path, monkeypatch):
    value = str(tmp_path / "state.flag")
    monkeypatch.setenv(DSN_NAME, value)
    root = _tree(tmp_path, {CORE_TEST: USES_GO})
    seen: list[object] = []

    def look(_row):
        try:
            with mr._one_run_per_database([value]):
                seen.append("taken")
        except RuntimeError as exc:
            seen.append(str(exc))

    _run(root, [FLIP], pass_env=(DSN_NAME,), on_result=look)
    assert len(seen) == 1 and "another mutation run" in str(seen[0]), (
        f"the lock was not held while a mutant result came in: {seen}"
    )


def test_a_lock_that_fails_for_another_reason_is_not_called_another_run(tmp_path, monkeypatch):
    if os.name == "nt":
        pytest.skip("flock is POSIX")
    import fcntl

    def no_space(*_a):
        raise OSError(errno.ENOLCK, "no locks available")

    monkeypatch.setattr(fcntl, "flock", no_space)
    caught = None
    try:
        with mr._one_run_per_database(["x"]):
            pass
    except RuntimeError as exc:
        caught = exc
    assert caught is not None, "a lock that failed for another reason was not refused"
    assert "another mutation run" not in str(caught) and "could not be locked" in str(caught), (
        f"a lock failure that is not a second run was called one: {caught}"
    )


def test_a_lock_file_that_cannot_be_opened_is_a_clear_refusal(tmp_path, monkeypatch):
    def refuse(*a, **k):
        raise PermissionError(errno.EACCES, "refused")

    monkeypatch.setattr(os, "open", refuse)
    caught = None
    try:
        with mr._one_run_per_database(["x"]):
            pass
    except (RuntimeError, OSError) as exc:
        caught = exc
    assert isinstance(caught, RuntimeError), f"the open failure was not a clear refusal: {caught!r}"
    assert "could not be opened" in str(caught), f"another refusal: {caught}"


def test_a_lock_file_that_is_a_symbolic_link_is_refused_and_the_file_has_mode_0600(tmp_path):
    if os.name == "nt":
        pytest.skip("symbolic links and file modes are POSIX here")
    target = tmp_path / "target"
    target.write_text("x")
    (tmp_path / _lock_name("x")).symlink_to(target)
    caught = None
    try:
        with mr._one_run_per_database(["x"]):
            pass
    except (RuntimeError, OSError) as exc:
        caught = exc
    assert isinstance(caught, RuntimeError) and "symbolic link" in str(caught), (
        f"a planted symbolic link was followed or refused otherwise: {caught!r}"
    )
    try:
        with mr._one_run_per_database(["y"]):
            pass
    except RuntimeError as exc:
        raise AssertionError(f"the lock file was not private: {exc}") from None
    mode = (tmp_path / _lock_name("y")).stat().st_mode & 0o777
    assert mode == 0o600, f"the lock file was not private: {oct(mode)}"


def _canary_ends_with(tmp_path, monkeypatch, code):
    monkeypatch.setenv(DSN_NAME, str(tmp_path / "state.flag"))
    root = _tree(tmp_path, {CORE_TEST: USES_GO})
    real = mr._pytest

    def pytest_run(*a, **k):
        return code if a[2].name == "again.xml" else real(*a, **k)

    monkeypatch.setattr(mr, "_pytest", pytest_run)
    try:
        _run(root, [FLIP], pass_env=(DSN_NAME,))
    except mr.CanaryFailed as exc:
        return str(exc)
    raise AssertionError("a canary run that did not pass was accepted")


def test_a_canary_run_that_timed_out_says_so(tmp_path, monkeypatch):
    text = _canary_ends_with(tmp_path, monkeypatch, mr.TIMED_OUT)
    assert "timed out" in text and "-1000" not in text, (
        f"the canary timeout was not in words: {text}"
    )


def test_a_canary_run_that_was_reaped_says_so(tmp_path, monkeypatch):
    text = _canary_ends_with(tmp_path, monkeypatch, mr.REAPED_ELSEWHERE)
    assert "reaped" in text and "-1001" not in text, f"the reaped canary was not in words: {text}"


def test_a_canary_run_with_an_exit_code_shows_the_code(tmp_path, monkeypatch):
    text = _canary_ends_with(tmp_path, monkeypatch, 3)
    assert "exit code 3" in text, f"the exit code of the canary run was lost: {text}"


# ---- forbid_skips -----------------------------------------------------------------------------------------------------------


def test_default_counts_a_run_with_a_skipped_test_as_before(tmp_path):
    root = _tree(tmp_path, {CORE_TEST: SKIP_FIRST})
    rows = _run(root, [FLIP])
    assert _short(rows) == [("flip", Verdict.KILLED, True)], (
        f"a skipped test changed the result of a run without forbid_skips: {rows}"
    )


def test_forbid_skips_makes_a_mutant_run_with_a_skipped_test_an_error_not_a_kill(tmp_path):
    root = _tree(tmp_path, {CORE_TEST: SKIP_FIRST})
    rows = _run(root, [FLIP], forbid_skips=True)
    assert rows == [("flip", Verdict.ERROR, "SKIPPED TESTS", False)], (
        f"a skipped test was counted as a kill under forbid_skips: {rows}"
    )


def test_forbid_skips_refuses_a_baseline_that_skips(tmp_path):
    body = "import pytest\n\ndef test_a():\n    pytest.skip('no database')\n"
    root = _tree(tmp_path, {CORE_TEST: body})
    _must_raise(
        "a baseline that skips was accepted",
        RuntimeError,
        _run,
        root,
        [FLIP],
        forbid_skips=True,
        match="skipped",
    )


def test_forbid_skips_counts_an_expected_failure_as_a_skip(tmp_path):
    body = "import pytest\n\n@pytest.mark.xfail\ndef test_a():\n    assert False\n"
    root = _tree(tmp_path, {CORE_TEST: body})
    _must_raise(
        "an expected failure was not counted as a skip",
        RuntimeError,
        _run,
        root,
        forbid_skips=True,
        match="skipped",
    )


def test_forbid_skips_leaves_a_clean_run_alone(tmp_path):
    root = _tree(tmp_path, {CORE_TEST: USES_GO})
    rows = _run(root, [FLIP], forbid_skips=True)
    assert _short(rows) == [("flip", Verdict.KILLED, True)], (
        f"a clean run was changed by forbid_skips: {rows}"
    )


def test_skipped_tests_reads_skips_and_refuses_doctype():
    xml = (
        '<testsuites><testsuite><testcase classname="tests.test_x" name="test_a"><skipped message="s"/></testcase>'
        '<testcase classname="tests.test_x" name="test_b"/></testsuite></testsuites>'
    )
    assert skipped_tests(xml) == ["tests/test_x::test_a"]
    assert skipped_tests("<testsuites/>") == []
    with pytest.raises(ValueError):
        skipped_tests('<!DOCTYPE x [<!ENTITY e "v">]><testsuites/>')


def test_forbid_skips_with_a_missing_or_empty_junit_file_is_an_error_row_never_judged(
    tmp_path, monkeypatch
):
    root = _tree(tmp_path, {CORE_TEST: PASSES})
    real = mr._pytest

    def fake(cwd, tests, junit, timeout, **kw):
        if junit.name == "base.xml":
            return real(cwd, tests, junit, timeout, **kw)
        return 1  # a failing exit code and NO junit file

    monkeypatch.setattr(mr, "_pytest", fake)
    rows = _run(root, [FLIP], forbid_skips=True)
    assert rows == [("flip", Verdict.ERROR, "JUNIT MISSING", False)], (
        f"no JUNIT file under forbid_skips was not the JUNIT MISSING row: {rows}"
    )

    def fake_empty(cwd, tests, junit, timeout, **kw):
        if junit.name != "base.xml":
            junit.write_text("", encoding="utf-8")
            return 1
        return real(cwd, tests, junit, timeout, **kw)

    monkeypatch.setattr(mr, "_pytest", fake_empty)
    rows = _run(root, [FLIP], forbid_skips=True)
    assert rows == [("flip", Verdict.ERROR, "JUNIT MISSING", False)], (
        f"an empty JUNIT file under forbid_skips was not the JUNIT MISSING row: {rows}"
    )


# ---- defaults unchanged -----------------------------------------------------------------------------------------------------


def test_a_default_call_passes_pytest_no_plugin_and_no_env_names(tmp_path, monkeypatch):
    root = _tree(tmp_path, {CORE_TEST: PASSES})
    calls = []

    def fake(*args, **kwargs):
        calls.append((len(args), kwargs))
        return 0

    monkeypatch.setattr(mr, "_pytest", fake)
    _run(root)
    assert calls == [(4, {"plugin": "", "env_names": ()})]


def test_the_default_child_environment_has_no_database_address(tmp_path, monkeypatch):
    monkeypatch.setenv(DSN_NAME, _fake_dsn())
    seen = {}
    real = mr.subprocess.Popen

    def spy(cmd, **kw):
        seen["env"], seen["cmd"] = kw["env"], cmd
        return real(cmd, **kw)

    monkeypatch.setattr(mr.subprocess, "Popen", spy)
    (tmp_path / "t.py").write_text(PASSES, encoding="utf-8")
    assert mr._pytest(tmp_path, ["t.py"], tmp_path / "r.xml", 60) == 0
    assert DSN_NAME not in seen["env"] and "--noconftest" in seen["cmd"]
    assert [a for a in seen["cmd"] if a.startswith("tests")] == []  # no plugin module added
    assert seen["cmd"].count("-p") == 1  # only the runner's own `-p no:cacheprovider`
    assert os.environ[DSN_NAME] == _fake_dsn()  # the caller's own value is untouched


# ---- always on: a failing run that names no test, and fixture errors --------------------------------------------------------


def test_judge_never_returns_killed_for_an_empty_failing_test_id():
    line = "E   AssertionError: assert 1 == 2"
    assert judge(1, "", line) is Verdict.ERROR, "an empty failing test id was judged as a kill"
    assert judge(1, "", line, expect="assert 1") is Verdict.ERROR, (
        "an empty test id with expect was a kill"
    )
    assert judge(1, "t.py::a", line) is Verdict.KILLED  # a named test still kills


def test_a_run_that_fails_with_no_junit_file_is_never_a_kill_even_without_forbid_skips(
    tmp_path, monkeypatch
):
    root = _tree(tmp_path, {CORE_TEST: PASSES})
    real = mr._pytest
    monkeypatch.setattr(
        mr,
        "_pytest",
        lambda cwd, tests, junit, timeout, **kw: (
            real(cwd, tests, junit, timeout, **kw) if junit.name == "base.xml" else 1
        ),
    )
    rows = _run(root, [FLIP])
    assert rows == [("flip", Verdict.ERROR, "NO FAILING TEST NAMED", False)], (
        f"a failing run with no JUNIT file was not the plain empty ERROR row: {rows}"
    )


def test_a_baseline_that_left_no_usable_junit_file_is_refused_under_forbid_skips(
    tmp_path, monkeypatch
):
    root = _tree(tmp_path, {CORE_TEST: PASSES})
    real = mr._pytest

    def without_the_file(cwd, tests, junit, timeout, **kw):
        rc = real(cwd, tests, junit, timeout, **kw)
        if junit.name == "base.xml":
            junit.unlink()
        return rc

    monkeypatch.setattr(mr, "_pytest", without_the_file)
    caught = None
    try:
        _run(root, [FLIP], forbid_skips=True)
    except (RuntimeError, OSError, ValueError, SyntaxError) as exc:
        caught = exc
    assert isinstance(caught, RuntimeError), (
        f"no refusal for a baseline without a JUnit file: {caught!r}"
    )
    assert "no usable JUnit file" in str(caught), f"another refusal: {caught}"


COLLECTION_ASSERTS = "from pk.core import go\n\nassert go(True) is True, 'at import'\n\ndef test_a():\n    assert True\n"


def test_a_test_file_that_cannot_be_imported_is_an_error_row_never_a_kill(tmp_path):
    root = _tree(tmp_path, {CORE_TEST: COLLECTION_ASSERTS})
    lines: dict[str, str] = {}
    rows = _run(root, [FLIP], first_lines=lines)
    assert rows == [("flip", Verdict.ERROR, "COLLECTION ERROR", False)], (
        f"an assert at import time was counted as a kill: {rows}"
    )
    assert "at import" in lines["flip"], f"the COLLECTION ERROR row kept no message: {lines}"


def test_read_junit_marks_a_collection_error_of_a_real_pytest_run(tmp_path):
    # the shape was read from a real pytest 9.2 run: an empty classname, the dotted module as
    # the name, message "collection failure"; pytest exits 2 for it, and the judge turns every exit code other than 1 into ERROR, so the
    # row was an ERROR row before the label existed (observed with the unchanged runner of main, see the module docstring of the runner)
    root = _tree(tmp_path, {CORE_TEST: COLLECTION_ASSERTS.replace("go(True) is True", "go(False)")})
    out = tmp_path / "c.xml"
    rc = mr._pytest(root, [CORE_TEST], out, 60)
    report = read_junit(out.read_text(encoding="utf-8"))
    assert rc == 2 and report.collection_failed and not report.fixture_failed, (
        f"a real collection error was not read as one: rc={rc} {report}"
    )
    assert report.test_id, (
        "pytest named the collection error (a non-empty id), so only the message tells it apart"
    )


FIXTURE_ASSERTS = (
    "import pytest\nfrom pk.core import go\n\n"
    "@pytest.fixture\ndef checked():\n    assert go(True) is True\n    return 1\n\n"
    "def test_a(checked):\n    assert checked == 1\n"
)
TEARDOWN_ASSERTS = (
    "import pytest\nfrom pk.core import go\n\n"
    "@pytest.fixture\ndef checked():\n    yield 1\n    assert go(True) is True\n\n"
    "def test_a(checked):\n    assert checked == 1\n"
)
BODY_AND_TEARDOWN_FAIL = (
    "import pytest\nfrom pk.core import go\n\n"
    "@pytest.fixture\ndef checked():\n    yield 1\n    assert go(True) is True\n\n"
    "def test_a(checked):\n    assert go(True) is True, 'the body failed'\n"
)


def test_a_fixture_error_in_the_mutant_run_is_an_error_row_not_a_kill(tmp_path):
    # the mutant makes the FIXTURE assert; the first line is an AssertionError, which the judge alone reads as a kill
    root = _tree(tmp_path, {CORE_TEST: FIXTURE_ASSERTS})
    lines: dict[str, str] = {}
    rows = _run(root, [FLIP], first_lines=lines)
    assert rows == [("flip", Verdict.ERROR, "FIXTURE ERROR", False)], (
        f"a fixture that failed at setup was not the FIXTURE ERROR row: {rows}"
    )
    assert "assert" in lines.get("flip", ""), f"the FIXTURE ERROR row kept no message: {lines}"


def test_a_teardown_error_of_a_fixture_is_an_error_row_not_a_kill(tmp_path):
    # the test body passes; the mutant makes the fixture's teardown assert
    root = _tree(tmp_path, {CORE_TEST: TEARDOWN_ASSERTS})
    rows = _run(root, [FLIP])
    assert rows == [("flip", Verdict.ERROR, "FIXTURE ERROR", False)], (
        f"a fixture that failed at teardown was not the FIXTURE ERROR row: {rows}"
    )


def test_a_failing_body_and_a_failing_teardown_are_judged_by_the_failure(tmp_path):
    # the test ran as written and failed by its own assertion: that is the reason, the teardown error after it is not
    root = _tree(tmp_path, {CORE_TEST: BODY_AND_TEARDOWN_FAIL})
    lines: dict[str, str] = {}
    body_fails = Mutant(
        "flip", "src/pk/core.py", "return flag", "return not flag", "the body failed"
    )
    rows = _run(root, [body_fails], first_lines=lines)
    assert _short(rows) == [("flip", Verdict.KILLED, True)], (
        f"a test body that failed was hidden behind its failing teardown: {rows}"
    )
    assert "the body failed" in lines["flip"], lines


FIXTURE_AND_SKIP_JUNIT = (
    '<testsuites><testsuite><testcase classname="tests.test_core" name="test_a"><skipped message="s"/></testcase>'
    '<testcase classname="tests.test_core" name="test_b"><error message="failed on setup with &quot;AssertionError&quot;">E   AssertionError: the fixture</error></testcase>'
    "</testsuite></testsuites>"
)


def test_a_fixture_error_and_a_skipped_test_in_one_run_are_a_fixture_error(tmp_path, monkeypatch):
    root = _tree(tmp_path, {CORE_TEST: PASSES})
    real = mr._pytest

    def fake(cwd, tests, junit, timeout, **kw):
        if junit.name != "r.xml":
            return real(cwd, tests, junit, timeout, **kw)
        junit.write_text(FIXTURE_AND_SKIP_JUNIT, encoding="utf-8")
        return 1

    monkeypatch.setattr(mr, "_pytest", fake)
    rows = _run(root, [FLIP], forbid_skips=True)
    assert rows == [("flip", Verdict.ERROR, "FIXTURE ERROR", False)], (
        f"a skip was judged before a fixture error: {rows}"
    )


def test_the_skipped_tests_row_keeps_a_masked_message(tmp_path, monkeypatch):
    dsn, word = _secret_dsn()
    monkeypatch.setenv(DSN_NAME, dsn)
    # the flip makes the test skip itself (rc 0); its id carries the passed value
    body = (
        "import pytest\nfrom pk.core import go\n\n"
        f"@pytest.mark.parametrize('v', [{dsn!r}])\n"
        "def test_a(v):\n    if go(False) is not False:\n        pytest.skip('x')\n    assert go(True) is True\n"
    )
    root = _tree(tmp_path, {CORE_TEST: body})
    lines: dict[str, str] = {}
    rows = _run(root, [FLIP], pass_env=(DSN_NAME,), forbid_skips=True, first_lines=lines)
    assert rows == [("flip", Verdict.ERROR, "SKIPPED TESTS", False)], rows
    shown = lines.get("flip", "")
    assert shown.startswith("skipped:"), f"the SKIPPED TESTS row kept no message: {lines}"
    assert dsn not in shown and word not in shown, "the SKIPPED TESTS message held the passed value"
    assert "[REDACTED]" in shown, "the SKIPPED TESTS message was not shown with a marker"


def test_a_skipped_tests_row_without_a_failure_says_which_tests_were_skipped(tmp_path, monkeypatch):
    root = _tree(tmp_path, {CORE_TEST: PASSES})
    real = mr._pytest
    xml = '<testsuites><testsuite><testcase classname="tests.test_core" name="test_a"><skipped message="s"/></testcase></testsuite></testsuites>'

    def fake(cwd, tests, junit, timeout, **kw):
        if junit.name != "r.xml":
            return real(cwd, tests, junit, timeout, **kw)
        junit.write_text(xml, encoding="utf-8")
        return 0

    monkeypatch.setattr(mr, "_pytest", fake)
    lines: dict[str, str] = {}
    rows = _run(root, [FLIP], forbid_skips=True, first_lines=lines)
    assert rows == [("flip", Verdict.ERROR, "SKIPPED TESTS", False)], rows
    assert lines.get("flip") == "skipped: tests/test_core::test_a", (
        f"the SKIPPED TESTS row did not say which tests were skipped: {lines}"
    )


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


def test_read_junit_gives_the_same_answers_as_the_three_single_readers_in_one_parse():
    xml = (
        "<testsuites><testsuite>"
        '<testcase classname="tests.test_x" name="test_s"><skipped message="s"/></testcase>'
        '<testcase classname="tests.test_x" name="test_a"><error message="failed on setup with &quot;X&quot;">E   X: boom</error></testcase>'
        '<testcase classname="tests.test_x" name="test_c"><failure message="m">E   AssertionError: later</failure></testcase>'
        "</testsuite></testsuites>"
    )
    report = read_junit(xml)
    assert report.test_id == "tests/test_x::test_a" and report.first_line == "E   X: boom"
    assert report.skipped == skipped_tests(xml) == ["tests/test_x::test_s"]
    assert report.fixture_errors == fixture_errors(xml) == ["tests/test_x::test_a"]
    assert report.fixture_failed is True, "the first failing case is a fixture error"
    later = (
        "<testsuites><testsuite>"
        '<testcase classname="tests.test_x" name="test_c"><failure message="m">E   AssertionError: first</failure></testcase>'
        '<testcase classname="tests.test_x" name="test_a"><error message="failed on setup with &quot;X&quot;">E   X: boom</error></testcase>'
        "</testsuite></testsuites>"
    )
    assert read_junit(later).fixture_failed is False, (
        "a later fixture error is not the first failure"
    )
    assert read_junit("<testsuites/>").test_id == ""


def test_a_mutant_whose_old_text_is_absent_is_an_error_not_a_kill(tmp_path):
    root = _tree(tmp_path, {CORE_TEST: PASSES})
    gone = Mutant("gone", "src/pk/core.py", "text that is not there", "x", "assert")
    rows = _run(root, [gone])
    assert rows == [("gone", Verdict.ERROR, "SNIPPET NOT FOUND", False)]


def test_a_value_with_one_quote_kind_is_masked_inside_a_text_that_holds_the_other_kind(monkeypatch):
    # repr of the larger text uses single quotes and escapes the single quote of the value: a form that repr of the value alone never writes
    value = "host=db.invalid user=svc password=Ab3'Xy9Zq1"
    monkeypatch.setenv(DSN_NAME, value)
    secrets = mr._secret_values((DSN_NAME,))
    larger = repr(value + '"')
    assert "\\'" in larger and "\\'" not in repr(value), (
        "the control is wrong: the larger text must escape the quote"
    )
    out = mr._masked(f"E   assert {larger} == 1", secrets)
    assert "Xy9Zq1" not in out, f"a single-quote-escaped form survived the masking: {out}"
    value = "host=db.invalid user=svc password=Ab3'Xy9" + chr(34) + "Zq1"
    monkeypatch.setenv(DSN_NAME, value)
    c_style = value.replace(chr(39), "\\" + chr(39)).replace(
        chr(34), "\\" + chr(34)
    )  # a C or JavaScript string literal: both quote marks escaped
    out = mr._masked(
        "E   char *dsn = " + chr(34) + c_style + chr(34) + ";", mr._secret_values((DSN_NAME,))
    )
    assert "Zq1" not in out, f"a form with both quote marks escaped survived the masking: {out}"


def test_libpq_backslash_escapes_in_a_password_are_read(monkeypatch):
    monkeypatch.setenv(DSN_NAME, "host=db.invalid password='Ab3\\'Xy9Zq1' user=svc")
    assert "Xy9Zq1" not in mr._masked("E   Ab3'Xy9Zq1", mr._secret_values((DSN_NAME,))), (
        "the unescaped password of a quoted libpq value survived the masking"
    )
    monkeypatch.setenv(DSN_NAME, "host=db.invalid password=Ab3\\ Xy9Zq1 user=svc")
    assert "Xy9Zq1" not in mr._masked("E   Ab3 Xy9Zq1", mr._secret_values((DSN_NAME,))), (
        "the unescaped password after a backslash and a space survived the masking"
    )


def test_a_url_password_with_unencoded_separators_is_masked(monkeypatch):
    monkeypatch.setenv(DSN_NAME, "postgresql://svc:Ab3/Xy9@Zq1#Wm2@db.invalid/app")
    secrets = mr._secret_values((DSN_NAME,))
    out = mr._masked("E   password was Ab3/Xy9@Zq1#Wm2 here", secrets)
    assert "Zq1#Wm2" not in out and "Ab3/Xy9" not in out, (
        f"a URL password with an unencoded slash or hash survived the masking: {out}"
    )
    monkeypatch.setenv(DSN_NAME, "postgresql://svc:Ab3/Xy9Zq1?Wm2#Kd7@db.invalid/app")
    out = mr._masked("E   Ab3/Xy9Zq1?Wm2#Kd7", mr._secret_values((DSN_NAME,)))
    assert "Wm2#Kd7" not in out, f"a URL password with an unencoded question mark survived: {out}"


def test_a_one_character_secret_on_a_huge_line_is_replaced_fast_and_a_normal_line_is_not():
    start = time.monotonic()
    out = mr._masked("E   " + "a" * 3_000_000 + "b", ("a", "ta"))
    took = time.monotonic() - start
    assert "more than" in out and "aaaa" not in out, (
        f"a huge line with millions of matches was not replaced as a whole: {out[:80]!r}"
    )
    # the marker above is the exact check; this bound only catches a scan that takes minutes, so a slow machine does not fail it
    assert took < 30, f"the check of a huge line took {took:.1f} seconds"
    assert (
        mr._masked("E   a banana", ("a",)) == "E   [REDACTED] b[REDACTED]n[REDACTED]n[REDACTED]"
    ), "a normal line with a few matches was replaced as a whole or not masked"


def test_nothing_is_rebuilt_when_no_secret_is_set():
    text = "E   assert 1 == 2"
    assert mr._masked(text, ()) is text and mr._masked(text, ("",)) is text, (
        "a text with no secret was rebuilt"
    )


def _own_lock_file(tmp_path, name):
    path = tmp_path / _lock_name(name)
    path.write_bytes(b"")
    return path


def _refusal(value):
    try:
        with mr._one_run_per_database([value]):
            pass
    except RuntimeError as exc:
        return exc
    return None


def test_a_lock_file_with_a_wider_mode_is_refused(tmp_path):
    if os.name == "nt":
        pytest.skip("file modes are POSIX here")
    path = _own_lock_file(tmp_path, "wide")
    path.chmod(0o666)
    caught = _refusal("wide")
    assert caught is not None and "mode 0600 or narrower" in str(caught), (
        f"a lock file with a wide mode was accepted: {caught!r}"
    )
    path.chmod(0o400)  # narrower is fine
    assert _refusal("wide") is None


def _fstat_with(monkeypatch, **fields):
    """``os.fstat`` as the lock check sees it, with some fields changed (``st_uid``, ``st_nlink``): no root and no second user needed."""
    real = os.fstat
    names = (
        "st_mode",
        "st_ino",
        "st_dev",
        "st_nlink",
        "st_uid",
        "st_gid",
        "st_size",
        "st_atime",
        "st_mtime",
        "st_ctime",
    )

    def changed(fd):
        info = real(fd)
        return os.stat_result(tuple(fields.get(name, getattr(info, name)) for name in names))

    monkeypatch.setattr(os, "fstat", changed)


def test_a_lock_file_of_another_user_is_refused(tmp_path, monkeypatch):
    if os.name == "nt":
        pytest.skip("file owners are POSIX here")
    _own_lock_file(tmp_path, "other").chmod(
        0o600
    )  # only the owner differs, so the owner check alone must refuse it
    _fstat_with(monkeypatch, st_uid=os.getuid() + 1)
    caught = _refusal("other")
    assert caught is not None and "regular file of this user" in str(caught), (
        f"a lock file of another user was accepted: {caught!r}"
    )


def test_a_lock_file_with_two_hard_links_is_refused(tmp_path):
    if os.name == "nt":
        pytest.skip("hard link counts are POSIX here")
    path = _own_lock_file(tmp_path, "linked")
    path.chmod(0o600)
    os.link(path, tmp_path / "second-name")
    caught = _refusal("linked")
    assert caught is not None and "one name" in str(caught), (
        f"a lock file with two hard links was accepted: {caught!r}"
    )


def test_a_lock_file_that_cannot_be_opened_names_the_cause(monkeypatch):
    cases = (
        (errno.ELOOP, "symbolic link"),
        (errno.EACCES, "may not open it"),
        (errno.EPERM, "may not open it"),
        (errno.EISDIR, "it is a folder"),
        (errno.ENOTDIR, "is not a folder"),
        (errno.EIO, "errno 5"),
    )
    for code, words in cases:

        def refuse(*a, _code=code, **k):
            raise OSError(_code, "refused")

        monkeypatch.setattr(os, "open", refuse)
        caught = _refusal("cause")
        assert (
            caught is not None and "could not be opened" in str(caught) and words in str(caught)
        ), f"the open failure with errno {code} did not name its cause ({words}): {caught!r}"


def test_a_lock_file_that_is_not_a_regular_file_is_refused(tmp_path, monkeypatch):
    if os.name == "nt":
        pytest.skip("file modes are POSIX here")
    real = os.fstat

    def a_directory(fd):
        info = real(fd)
        return os.stat_result((stat.S_IFDIR | 0o600, *tuple(info)[1:]))

    monkeypatch.setattr(os, "fstat", a_directory)
    caught = _refusal("pipe")
    assert caught is not None and "regular file of this user" in str(caught), (
        f"a lock file that is not a regular file was accepted: {caught!r}"
    )


def test_the_descriptor_is_closed_when_no_file_object_can_take_it(tmp_path, monkeypatch):
    opened: list[int] = []
    real_open = os.open

    def spy(*a, **k):
        fd = real_open(*a, **k)
        opened.append(fd)
        return fd

    def refuse(*a, **k):
        raise OSError(errno.EMFILE, "no file object")

    monkeypatch.setattr(os, "open", spy)
    monkeypatch.setattr(os, "fdopen", refuse)
    with (
        pytest.raises(RuntimeError, match="could not be opened"),
        mr._one_run_per_database(["leak"]),
    ):
        pass
    assert len(opened) == 1
    try:
        os.fstat(opened[0])
        still_open = True
    except OSError:
        still_open = False
    assert not still_open, "the descriptor stayed open"


def test_a_value_with_a_non_ascii_letter_and_a_quote_is_masked_as_ascii_and_bytes_print_it_in_a_larger_text(
    monkeypatch,
):
    value = "host=db.invalid user=svc password=Ab3" + chr(233) + "'Xy9Zq1"
    monkeypatch.setenv(DSN_NAME, value)
    secrets = mr._secret_values((DSN_NAME,))
    larger = ascii(value + '"')
    assert "\\'" in larger and "\\xe9" in larger, (
        "the control is wrong: ascii() must escape the quote and the letter"
    )
    out = mr._masked(f"E   assert {larger} == 1", secrets)
    assert "Xy9Zq1" not in out, (
        f"the ascii() form with an escaped quote survived the masking: {out}"
    )
    in_bytes = repr((value + '"').encode("utf-8"))
    assert "\\'" in in_bytes and "\\xc3" in in_bytes, (
        "the control is wrong: the bytes repr must escape the quote"
    )
    out = mr._masked(f"E   assert {in_bytes} == 1", secrets)
    assert "Xy9Zq1" not in out, f"the bytes form with an escaped quote survived the masking: {out}"


def test_a_value_with_a_control_character_and_a_non_ascii_letter_is_masked_as_repr_prints_it(
    monkeypatch,
):
    value = "host=db.invalid user=svc password=Ab3" + chr(1) + chr(233) + "Xy9Zq1"
    monkeypatch.setenv(DSN_NAME, value)
    shown = repr(value)[1:-1]
    assert "\\x01" in shown and chr(233) in shown, (
        "the control is wrong: repr writes the control character as x01 and keeps the letter"
    )
    out = mr._masked(f"E   assert '{shown}' == 1", mr._secret_values((DSN_NAME,)))
    assert "Xy9Zq1" not in out, (
        f"the repr form with a control character survived the masking: {out}"
    )


def test_an_unquoted_password_with_a_quote_a_semicolon_or_an_ampersand_is_masked_in_full_when_printed_alone(
    monkeypatch,
):
    for odd in ("'", ";", "&"):
        monkeypatch.setenv(DSN_NAME, f"host=db.invalid password=Ab3{odd}Xy9Zq1 user=svc")
        out = mr._masked(f"E   assert 'Ab3{odd}Xy9Zq1' == 1", mr._secret_values((DSN_NAME,)))
        assert "Xy9Zq1" not in out, (
            f"an unquoted password with {odd!r} printed alone was not masked in full: {out}"
        )


def test_a_backslash_and_a_newline_in_a_quoted_libpq_password_are_read(monkeypatch):
    monkeypatch.setenv(
        DSN_NAME, "host=db.invalid password='Ab3" + chr(92) + chr(10) + "Xy9Zq1' user=svc"
    )
    out = mr._masked("E   assert 'Ab3" + chr(10) + "Xy9Zq1' == 1", mr._secret_values((DSN_NAME,)))
    assert "Xy9Zq1" not in out, (
        f"a quoted libpq password with a backslash and a newline was not read: {out}"
    )


def test_a_repr_of_a_json_text_and_a_doubled_backslash_form_are_masked(monkeypatch):
    value = "host=db.invalid user=svc password=Ab3" + chr(34) + chr(92) + chr(233) + "Xy9Zq1"
    monkeypatch.setenv(DSN_NAME, value)
    secrets = mr._secret_values((DSN_NAME,))
    again = repr(json.dumps(value))[1:-1]
    assert chr(92) * 3 in again, (
        "the control is wrong: the repr of a JSON text has doubled backslashes"
    )
    out = mr._masked(f"E   assert '{again}' == 1", secrets)
    assert "Xy9Zq1" not in out, f"the repr of a JSON text of the value survived the masking: {out}"
    doubled = value.replace(chr(92), chr(92) * 2)
    out = mr._masked(f"E   assert '{doubled}' == 1", secrets)
    assert "Xy9Zq1" not in out, f"a form with doubled backslashes survived the masking: {out}"
    nested = json.dumps(repr(value))[1:-1]
    out = mr._masked(f"E   {nested}", secrets)
    assert "Xy9Zq1" not in out, (
        f"the JSON text of the repr of the value survived the masking: {out}"
    )


def test_the_lock_file_is_opened_read_only_on_posix(monkeypatch):
    if os.name == "nt":
        pytest.skip("Windows locks a byte and needs write access")
    seen: list[int] = []
    real = os.open

    def spy(path, flags, *a, **k):
        seen.append(flags)
        return real(path, flags, *a, **k)

    monkeypatch.setattr(os, "open", spy)
    assert _refusal("readonly") is None
    assert seen and not any(f & (os.O_WRONLY | os.O_RDWR) for f in seen), (
        f"the lock file was opened for writing: {seen}"
    )


_LAYER_PRINTERS = (
    repr,
    ascii,
    json.dumps,
    lambda s: json.dumps(s, ensure_ascii=False),
    lambda s: repr(s.encode("utf-8")),
    lambda s: s.encode("unicode_escape").decode("ascii"),
)
_INNER_PRINTERS = (  # the text each printer writes between its own quote marks, built apart from the runner
    lambda s: repr(s)[1:-1],
    lambda s: ascii(s)[1:-1],
    lambda s: json.dumps(s)[1:-1],
    lambda s: json.dumps(s, ensure_ascii=False)[1:-1],
    lambda s: repr(s.encode("utf-8"))[2:-1],
    lambda s: s.encode("unicode_escape").decode("ascii"),
)
# a quote of each kind, a backslash, a non-ASCII letter, a space, %, +, &, ;, @, a new line, a control character, a character beyond U+FFFF, letters
TWO_LAYER_ALPHABET = (
    "'" + '"' + chr(92) + chr(233) + " %+&;@" + chr(10) + chr(1) + chr(0x1F600) + "ac"
)  # no letter b: ``_readable`` rightly ignores the b that starts a bytes print, so a leaked b would be ignored too
NO_WHITE_ALPHABET = TWO_LAYER_ALPHABET.replace(" ", "").replace(
    chr(10), ""
)  # a bare password has no white space (libpq ends it there)
EXHAUSTIVE_ALPHABET = "'" + '"' + chr(92) + chr(233) + "+" + chr(0x1F600)
MARKER = "Xy9Zq1"
QUOTES = "'" + '"'
LINE = "E>"


def _printed_n(value, sequence):
    """``value`` printed once for each printer index in ``sequence``, by the real functions."""
    for index in sequence:
        value = _LAYER_PRINTERS[index](value)
    return value


PRINTER_NAMES = (
    "repr",
    "ascii",
    "json",
    "json_utf8",
    "bytes",
    "unicode_escape",
)  # of _LAYER_PRINTERS, in order


def _two_layers(value):
    """Every text that ``second(first(value))`` makes with the real functions, also when the larger text holds both quote kinds: ``(text, exact,
    label)``, the label naming both printers (it goes into the failure message, so a failure says which printer was not covered); only the plain
    ones are hidden down to the last quote mark."""
    for i, first in enumerate(_LAYER_PRINTERS):
        once = first(value)
        for j, second in enumerate(_LAYER_PRINTERS):
            label = f"{PRINTER_NAMES[i]} then {PRINTER_NAMES[j]}"
            yield second(once), True, label
            yield second(once + QUOTES), False, label + ", both quote kinds in the text"
            yield second(first(value + QUOTES)), False, label + ", both quote kinds in the text"


def _readable(out):
    """What a reader can still read of a masked line: the text without the mask, the backslashes, the quote marks and the b that starts a bytes print
    (the alphabets of the bodies hold no letter b, so a leaked secret never hides in it)."""
    shown = re.sub(
        r"b(?=[\\'\"]|" + re.escape(mr.MASK) + ")", "", out
    )  # a bytes print starts with b: a marker, not the secret
    shown = shown.replace(mr.MASK, "")
    return "".join(c for c in shown if c not in "\\'" + '"')


def _leaks_of_two_layers(value, secrets, whole=True):
    """The printed texts of ``value`` that are not hidden. ``whole`` (a secret of FRAGMENT_MIN characters or more): the plain two-layer print must
    become exactly the mask. Always: nothing but the line itself is readable afterwards."""
    leaked = []
    for text, exact, label in _two_layers(value):
        out = mr._masked(LINE + text, secrets)
        if (whole and exact and out != LINE + mr.MASK) or _readable(out) != _readable(LINE):
            leaked.append(f"[{label}] {text}")
    return leaked


def _exact_forms_only(monkeypatch):
    """Turn the stripped-text and run-pattern layer off, so a test sees only what the exact written forms of a value hide (the pattern layer is tested on its own)."""
    monkeypatch.setattr(mr, "_stripped_spans", lambda text, bases, dots: [])


def _random_body(rng, alphabet):
    return "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 5)))


def test_a_value_printed_in_two_layers_is_masked_whatever_quotes_it_holds(monkeypatch):
    rng = _Det(7)
    leaked: list[str] = []
    for _ in range(120):
        value = "host=db.invalid user=svc password=" + _random_body(rng, TWO_LAYER_ALPHABET)
        value += MARKER + _random_body(rng, TWO_LAYER_ALPHABET)
        monkeypatch.setenv(DSN_NAME, value)
        leaked += _leaks_of_two_layers(value, mr._secret_values((DSN_NAME,)))
    assert not leaked, f"{len(leaked)} two-layer forms survived the masking, first: {leaked[0]}"


def test_a_bare_password_printed_in_two_layers_is_masked_whatever_quotes_it_holds(monkeypatch):
    rng = _Det(11)
    leaked: list[str] = []
    for _ in range(120):
        # a leading quote would make a libpq reader treat it as a quoted password
        password = "pw" + _random_body(rng, NO_WHITE_ALPHABET) + MARKER
        password += _random_body(rng, NO_WHITE_ALPHABET)
        monkeypatch.setenv(DSN_NAME, "host=db.invalid user=svc password=" + password)
        leaked += _leaks_of_two_layers(password, mr._secret_values((DSN_NAME,)))
    assert not leaked, (
        f"{len(leaked)} bare-password two-layer forms survived the masking, first: {leaked[0]}"
    )


def test_every_short_body_and_tail_printed_in_two_layers_is_masked(monkeypatch):
    """Not a sample: every body and tail of the exhaustive alphabet with a combined length of 3 or less, around the marker, as a bare password."""
    leaked: list[str] = []
    bodies = [""]
    for size in range(1, 4):
        bodies += ["".join(p) for p in itertools.product(EXHAUSTIVE_ALPHABET, repeat=size)]
    count = 0
    for body in bodies:
        for tail in bodies:
            if len(body) + len(tail) > 3:
                continue
            count += 1
            password = "pw" + body + MARKER + tail
            monkeypatch.setenv(DSN_NAME, "password=" + password)
            secrets = mr._secret_values((DSN_NAME,))
            for first in range(len(_LAYER_PRINTERS)):
                text = _printed_n(password, (first, (first + 1) % 6))
                if mr._masked(LINE + text, secrets) != LINE + mr.MASK:
                    leaked.append(text)
    assert count == 985, f"the exhaustive pass changed size: {count}"
    assert not leaked, (
        f"{len(leaked)} short-value two-layer forms survived the masking, first: {leaked[0]}"
    )


def test_a_short_value_printed_in_two_layers_leaves_nothing_readable(monkeypatch):
    """A value whose stripped text (without backslashes and quote marks) has fewer than FRAGMENT_MIN characters: every body of
    ``_short_bodies`` as the whole value, printed in two layers."""
    _exact_forms_only(monkeypatch)
    leaked: list[str] = []
    bodies = _short_bodies()
    for body in bodies:
        monkeypatch.setenv(DSN_NAME, body)
        leaked += _leaks_of_two_layers(body, mr._secret_values((DSN_NAME,)), whole=False)
    assert not leaked, (
        f"{len(leaked)} short-value two-layer forms survived the masking, first: {leaked[0]}"
    )


def test_a_short_bare_password_printed_in_two_layers_leaves_nothing_readable(monkeypatch):
    _exact_forms_only(monkeypatch)
    leaked: list[str] = []
    rng = _Det(43)
    for _ in range(150):
        password = "pw" + "".join(rng.choice(NO_WHITE_ALPHABET) for _ in range(rng.randint(1, 3)))
        monkeypatch.setenv(DSN_NAME, "host=db.invalid user=svc password=" + password)
        secrets = mr._secret_values((DSN_NAME,))
        for text, _, label in _two_layers(password):
            out = mr._masked(LINE + text, secrets)
            if _readable(out) != _readable(LINE):
                leaked.append(f"[{label}] {text}")
    assert not leaked, (
        f"{len(leaked)} short bare-password two-layer forms survived the masking, first: {leaked[0]}"
    )


def _short_bodies():
    """Every body of the exhaustive alphabet and a control character up to 3 letters, then seeded longer ones: all shorter than FRAGMENT_MIN once the quote marks are dropped."""
    bodies = [
        "".join(p)
        for size in (1, 2, 3)
        for p in itertools.product(EXHAUSTIVE_ALPHABET + chr(1), repeat=size)
    ]  # the control character shows the looks that only JSON and ``repr`` write differently (``\\u0001`` and ``\\x01``)
    rng = _Det(47)
    return bodies + [_random_body(rng, TWO_LAYER_ALPHABET) for _ in range(150)]


def _escaped_quote_mixes(body):
    """``body`` as a C or JavaScript string literal writes it: only the single quotes escaped, only the double quotes, or both."""
    single = body.replace("'", chr(92) + "'")
    double = body.replace(chr(34), chr(92) + chr(34))
    return single, double, single.replace(chr(34), chr(92) + chr(34))


def test_a_short_value_written_with_its_quotes_escaped_leaves_nothing_readable(monkeypatch):
    """A value with fewer than FRAGMENT_MIN characters is matched by its written forms only: one list per quote kind that a text may escape."""
    _exact_forms_only(monkeypatch)
    leaked: list[list[str]] = [[], [], []]
    plain: list[str] = []
    for body in _short_bodies():
        monkeypatch.setenv(DSN_NAME, body)
        secrets = mr._secret_values((DSN_NAME,))
        if _readable(mr._masked(LINE + body, secrets)) != _readable(LINE):
            plain.append(body)
        for mix, written in zip(leaked, _escaped_quote_mixes(body), strict=True):
            if body != written and _readable(mr._masked(LINE + written, secrets)) != _readable(
                LINE
            ):
                mix.append(written)
    assert not plain, f"a short value written as it is survived the masking: {plain[0]}"
    assert not leaked[0], (
        f"a short value with only its single quotes escaped survived the masking: {leaked[0][0]}"
    )
    assert not leaked[1], (
        f"a short value with only its double quotes escaped survived the masking: {leaked[1][0]}"
    )
    assert not leaked[2], (
        f"a short value with both quote kinds escaped survived the masking: {leaked[2][0]}"
    )


def test_a_short_libpq_password_with_a_backslash_escape_is_read_the_way_libpq_reads_it(monkeypatch):
    """A short password is found by its exact forms and its run pattern, and the unescaped form is the one that hides it when it is printed the way libpq reads it."""
    _exact_forms_only(monkeypatch)
    monkeypatch.setenv(DSN_NAME, "host=db.invalid password='p" + chr(92) + "'q' user=svc")
    out = mr._masked(LINE + "p'q", mr._secret_values((DSN_NAME,)))
    assert _readable(out) == _readable(LINE), (
        f"the unescaped short quoted libpq password survived the masking: {out}"
    )
    monkeypatch.setenv(DSN_NAME, "host=db.invalid password=pq" + chr(92) + " rs user=svc")
    out = mr._masked(LINE + "pq rs", mr._secret_values((DSN_NAME,)))
    assert _readable(out) == _readable(LINE), (
        f"the unescaped short password with a space survived the masking: {out}"
    )


def test_a_short_value_printed_once_leaves_nothing_readable(monkeypatch):
    """The first printed layer: by each real printer, alone and inside a text that holds both quote kinds (where ``repr`` escapes the single quote)."""
    _exact_forms_only(monkeypatch)
    alone: list[str] = []
    inside: list[str] = []
    for body in _short_bodies():
        monkeypatch.setenv(DSN_NAME, body)
        secrets = mr._secret_values((DSN_NAME,))
        for printer in _LAYER_PRINTERS:
            for texts, text in ((alone, printer(body)), (inside, printer(body + QUOTES))):
                if _readable(mr._masked(LINE + text, secrets)) != _readable(LINE):
                    texts.append(text)
    assert not alone, f"a short value printed once survived the masking: {alone[0]}"
    assert not inside, (
        f"a short value printed once among both quote kinds survived the masking: {inside[0]}"
    )


def test_a_short_value_printed_once_does_not_hide_the_backslash_after_it(monkeypatch):
    """The run pattern of a short value stops at the end of the print: the backslash that follows it is ordinary text (the pattern layer is ON here)."""
    eaten: list[str] = []
    for body in _short_bodies():
        monkeypatch.setenv(DSN_NAME, body)
        secrets = mr._secret_values((DSN_NAME,))
        if (
            body[-1] not in QUOTES + chr(92)
        ):  # (a body that ends in a quote or a backslash makes one run with a backslash that follows it)
            for inner in _INNER_PRINTERS:
                text = inner(body) + chr(92) + "Z"
                if not mr._masked(LINE + text, secrets).endswith(chr(92) + "Z"):
                    eaten.append(text)
    assert not eaten, f"a short value printed once hid the backslash after it: {eaten[0]}"


DEEP_VALUE = (
    "host=db.invalid user=svc password=it's"
    + chr(34)
    + chr(92)
    + chr(233)
    + MARKER
    + chr(1)
    + chr(0x1F600)
    + " 50%+up;x&y@z"
    + chr(10)
)


def _depth_leaks(secrets, value, sequences):
    return [
        sequence
        for sequence in sequences
        if mr._masked(LINE + _printed_n(value, sequence), secrets) != LINE + mr.MASK
    ]


def test_a_value_printed_three_times_in_any_order_is_masked_in_full(monkeypatch):
    monkeypatch.setenv(DSN_NAME, DEEP_VALUE)
    secrets = mr._secret_values((DSN_NAME,))
    every = [s for depth in (1, 2, 3) for s in itertools.product(range(6), repeat=depth)]
    leaks = _depth_leaks(secrets, DEEP_VALUE, every)
    assert not leaks, (
        f"{len(leaks)} of {len(every)} printing orders of depth 3 or less left something: {leaks[:3]}"
    )


def test_a_value_printed_four_and_five_times_is_masked_in_full(monkeypatch):
    monkeypatch.setenv(DSN_NAME, DEEP_VALUE)
    secrets = mr._secret_values((DSN_NAME,))
    rng = _Det(23)
    chosen = [
        tuple(rng.randint(0, 5) for _ in range(depth)) for depth in (4, 5) for _ in range(150)
    ]
    leaks = _depth_leaks(secrets, DEEP_VALUE, chosen)
    assert not leaks, (
        f"{len(leaks)} of {len(chosen)} printing orders of depth 4 or 5 left something: {leaks[:3]}"
    )


def test_a_bare_password_printed_three_to_five_times_is_masked_in_full(monkeypatch):
    password = (
        "pw" + "it's" + chr(34) + chr(92) + chr(233) + MARKER + chr(1) + chr(0x1F600) + "50%+up"
    )
    monkeypatch.setenv(DSN_NAME, "host=db.invalid user=svc password=" + password)
    secrets = mr._secret_values((DSN_NAME,))
    rng = _Det(31)
    chosen = list(itertools.product(range(6), repeat=3))
    chosen += [
        tuple(rng.randint(0, 5) for _ in range(depth)) for depth in (4, 5) for _ in range(100)
    ]
    leaks = _depth_leaks(secrets, password, chosen)
    assert not leaks, (
        f"{len(leaks)} bare-password printing orders of depth 3 to 5 left something: {leaks[:3]}"
    )


def _short_secret_bodies_for_depth():
    """Every body of up to 2 letters of the exhaustive alphabet and a control character, and seeded bodies of up to 5 letters with a quote mark or
    a backslash in the middle: each has fewer than FRAGMENT_MIN characters once its quote marks and backslashes are dropped."""
    rng = _Det(53)
    bodies = [
        "".join(p)
        for size in (1, 2)
        for p in itertools.product(EXHAUSTIVE_ALPHABET + chr(1), repeat=size)
    ]
    for _ in range(60):
        body = _random_body(rng, TWO_LAYER_ALPHABET)
        bodies.append(body[:2] + rng.choice(QUOTES + chr(92)) + body[2:])
    return [body for body in bodies if len(mr._stripped(body)) < mr.FRAGMENT_MIN]


def test_a_short_value_printed_three_to_five_times_leaves_nothing_readable(monkeypatch):
    """A short secret (under FRAGMENT_MIN characters once its quote marks and backslashes are dropped) that holds a quote mark, a backslash or a
    non-ASCII character is found at any print depth by its run pattern (the exact forms reach layer 2 only)."""
    rng = _Det(59)
    leaked: list[tuple[str, tuple[int, ...]]] = []
    embedded: list[tuple[str, tuple[int, ...]]] = []
    count = 0
    for body in _short_secret_bodies_for_depth():
        monkeypatch.setenv(DSN_NAME, body)
        secrets = mr._secret_values((DSN_NAME,))
        sequences = list(itertools.product(range(6), repeat=3))
        sequences += [
            tuple(rng.randint(0, 5) for _ in range(depth)) for depth in (4, 5) for _ in range(12)
        ]
        for sequence in sequences:
            count += 1
            text = _printed_n(body, sequence)
            if _readable(mr._masked(LINE + text, secrets)) != _readable(LINE):
                leaked.append((body, sequence))
            if (
                count % 3 == 0
            ):  # inside a larger text that holds both quote kinds (``repr`` then escapes the single quote)
                text = _printed_n(body + QUOTES, sequence)
                if _readable(mr._masked(LINE + text, secrets)) != _readable(LINE):
                    embedded.append((body, sequence))
    assert count > 10_000, f"the property test shrank: {count} cases"
    assert not leaked, (
        f"{len(leaked)} short values printed 3 to 5 times left something readable, first: {leaked[0]}"
    )
    assert len(embedded) == 0, (
        f"{len(embedded)} short values inside a text with both quote kinds, printed 3 to 5 times, left something readable, first: {embedded[0]}"
    )


def test_a_short_value_that_is_only_quote_marks_and_backslashes_leaves_no_long_run(monkeypatch):
    """Such a secret has nothing but its runs to look for: every run of QUOTE_RUN_MIN or more of them is hidden, and the shortest print that the exact
    forms miss is that long."""
    leaked: list[tuple[str, tuple[int, ...]]] = []
    rng = _Det(61)
    bodies = [
        "".join(p) for size in (1, 2, 3) for p in itertools.product(QUOTES + chr(92), repeat=size)
    ]
    bodies += [
        "".join(rng.choice(QUOTES + chr(92)) for _ in range(size))
        for size in (4, 5, 6, 8)
        for _ in range(25)
    ]  # longer ones: a sample (3 to the power 8 is too many for every one)
    for body in bodies:
        monkeypatch.setenv(DSN_NAME, body)
        secrets = mr._secret_values((DSN_NAME,))
        sequences = list(itertools.product(range(6), repeat=3))
        sequences += [
            tuple(rng.randint(0, 5) for _ in range(depth)) for depth in (4, 5) for _ in range(20)
        ]
        for sequence in sequences:
            out = mr._masked(LINE + _printed_n(body, sequence), secrets)
            if re.search("[" + re.escape(chr(92) + QUOTES) + "]{10,}", out):
                leaked.append((body, sequence))
    assert not leaked, f"{len(leaked)} long quote runs were not hidden, first: {leaked[0]}"
    ordinary = "E   assert 'a' == \"b\" and 'c' != 'd'"
    monkeypatch.setenv(DSN_NAME, QUOTES)  # a secret of both quote marks
    secrets = mr._secret_values((DSN_NAME,))
    assert mr._masked(ordinary, secrets) == ordinary, (
        "a quotes-only secret hid the short quote runs of an ordinary line"
    )
    nine = "E   " + "'" * 9 + " x"
    assert mr._masked(nine, secrets) == nine, (
        "a run of 9 quote marks was hidden: the run limit is 10"
    )
    ten = "E   " + "'" * 10 + " x"
    assert mr._masked(ten, secrets) == "E   " + mr.MASK + " x", (
        "a run of 10 quote marks was not hidden"
    )
    monkeypatch.setenv(DSN_NAME, "host=db.invalid user=svc password=" + MARKER)
    assert mr._masked(ten, mr._secret_values((DSN_NAME,))) == ten, (
        "a secret that holds a letter hid a run of quote marks"
    )


def test_a_head_or_tail_cut_inside_an_escape_is_hidden(monkeypatch):
    """pytest cuts a long text at any character, also inside the escape of one (``\\xc3`` + ``\\xa9`` for ``é``). The head or the tail that stands next to
    ``...`` then ends or starts inside an escape, which the stripped-text match cannot follow: the raw pieces of every written form are scanned."""
    _exact_forms_only(
        monkeypatch
    )  # the stripped-text match also hides these; here only the scan of the written forms is looked at
    value = "host=db.invalid user=svc password=Pass" + chr(233) + "Wxyz7Q"
    monkeypatch.setenv(DSN_NAME, value)
    secrets = mr._secret_values((DSN_NAME,))
    printed = repr(value.encode("utf-8"))[
        2:-1
    ]  # the bytes print: é is the two escapes \xc3 and \xa9
    inside = printed.index(chr(92) + "xa9")
    head = printed[:inside]  # ends after the first escape of é
    tail = printed[inside + 1 :]  # starts after the backslash of the second escape
    assert head.endswith(chr(92) + "xc3") and tail.startswith("xa9"), (
        "the control is wrong: the cut is not inside an escape"
    )
    head_text, tail_text = "b'" + head + "...zz'", "b'zz..." + tail + "'"
    out = mr._masked(LINE + head_text, secrets)
    assert out == LINE + "b'" + mr.MASK + "...zz'", (
        f"the head cut inside an escape was left readable: {out}"
    )
    out = mr._masked(LINE + tail_text, secrets)
    assert out == LINE + "b'zz..." + mr.MASK + "'", (
        f"the tail cut inside an escape was left readable: {out}"
    )


def _cut_around_dots(printed, kept=8):
    """What pytest leaves of a long printed text: its head and its tail, each the shortest piece with ``kept`` characters that are not a backslash or
    a quote mark, around ``...``."""
    head = next(i for i in range(1, len(printed)) if len(_plain(printed[:i])) == kept)
    tail = next(i for i in range(1, len(printed)) if len(_plain(printed[-i:])) == kept)
    return printed[:head] + "..." + printed[-tail:]


def _plain(text):
    """The characters of ``text`` that are not a backslash, a quote mark or the b that starts a bytes print."""
    return "".join(c for c in re.sub(r"b(?=[\\'\"])", "", text) if c not in "\\'" + '"')


def test_the_head_and_the_tail_next_to_dots_are_hidden_at_any_print_depth(monkeypatch):
    """pytest cuts a long text to ``head...tail``; the pieces of a value that holds quote marks, backslashes and non-ASCII characters are found
    at every depth (the exact forms reach layer 2 only)."""
    rng = _Det(67)
    sequences = list(itertools.product(range(6), repeat=3))
    sequences += [tuple(rng.randint(0, 5) for _ in range(d)) for d in (4, 5) for _ in range(60)]
    leaked = []
    ends_wide = (
        DEEP_VALUE.rstrip() + "Pw3" + chr(233) + chr(0x1F600) + chr(1)
    )  # ends in characters that print as several
    for value in (DEEP_VALUE, ends_wide):
        monkeypatch.setenv(DSN_NAME, value)
        secrets = mr._secret_values((DSN_NAME,))
        for sequence in sequences:
            cut = _cut_around_dots(_printed_n(value, sequence))
            out = mr._masked(LINE + cut, secrets)
            if _readable(out) != _readable(LINE + "..."):
                leaked.append((sequence, cut))
    monkeypatch.setenv(DSN_NAME, DEEP_VALUE)
    secrets = mr._secret_values((DSN_NAME,))
    assert not leaked, (
        f"{len(leaked)} head or tail pieces next to '...' were left, first: {leaked[0]}"
    )
    elsewhere = (
        LINE + " host=d here and a cut ... elsewhere"
    )  # the first 6 characters of the value, not next to the dots
    assert mr._masked(elsewhere, secrets) == elsewhere, (
        "a piece of the value that does not stand next to '...' was hidden"
    )


def test_a_head_that_starts_with_characters_that_print_as_escapes_is_hidden(monkeypatch):
    """The raw scan compares the line with the plain value, so a head whose first characters are printed as escapes (``\\xe9``) is found only by the stripped
    text layer: its head pattern must hold every character of the piece, not only the first."""
    value = chr(233) + chr(1) + "Pw3Tk5Zq9Lm2" + chr(233) + chr(2)
    monkeypatch.setenv(DSN_NAME, value)
    secrets = mr._secret_values((DSN_NAME,))
    leaked = []
    for sequence in itertools.product(range(6), repeat=3):
        cut = _cut_around_dots(_printed_n(value, sequence), kept=6)
        if _readable(mr._masked(LINE + cut, secrets)) != _readable(LINE + "..."):
            leaked.append((sequence, cut))
    assert not leaked, (
        f"{len(leaked)} head or tail pieces that print as escapes were left, first: {leaked[0]}"
    )


def test_the_stripped_text_match_costs_over_masking_and_pins_it(monkeypatch):
    """The accepted cost: text whose letters, in order, read as a secret once its backslashes and quote marks are ignored is hidden too."""
    monkeypatch.setenv(DSN_NAME, "host=db.invalid password=" + MARKER + "Tail")
    secrets = mr._secret_values((DSN_NAME,))
    spread = (
        "X'y9" + chr(92) + "Zq1T" + '"' + "ail"
    )  # the same letters with quote marks and a backslash between them
    assert (
        mr._masked(LINE + "see " + spread + " here", secrets) == LINE + "see " + mr.MASK + " here"
    )
    assert (
        mr._masked(LINE + "Zq1Xy9Tail", secrets) == LINE + "Zq1Xy9Tail"
    )  # another order is not hidden


def test_a_short_secret_does_not_hide_plain_text_that_has_no_quote_mark_where_its_own_has_one(
    monkeypatch,
):
    """The over-masking of a short secret is bounded: ``ab'c`` is hidden where a run of quote marks or backslashes stands between ``ab`` and ``c``,
    never in ordinary text (``abc``, ``ab c``), and a short secret with no quote, backslash or non-ASCII character needs no pattern at all."""
    assert mr._stripped_pattern("a'bcdef") is not None, (
        "a stripped text of exactly FRAGMENT_MIN characters got no pattern"
    )
    assert mr._stripped_pattern("a'bc") is None, (
        "a stripped text shorter than FRAGMENT_MIN must not get a pattern"
    )
    monkeypatch.setenv(DSN_NAME, "ab'c")  # the whole value is the short secret
    secrets = mr._secret_values((DSN_NAME,))
    for ordinary in ("abc", "ab c", "ab.c", "xab-c"):
        assert mr._masked(LINE + ordinary, secrets) == LINE + ordinary, (
            f"ordinary text {ordinary!r} was hidden by a short secret"
        )
    assert mr._masked(LINE + "ab" + chr(92) * 3 + "c", secrets) == LINE + mr.MASK, (
        "a run of backslashes where the secret has a quote mark was not hidden"
    )
    assert mr._run_pattern("abcd") is None, "a plain short secret got a pattern it does not need"
    assert mr._run_pattern("a'bc") is not None, "a short secret with a quote mark got no pattern"


def test_the_stripped_text_match_builds_one_pattern_per_plain_text_not_one_per_written_form(
    monkeypatch,
):
    """One pattern covers a plain text at every depth, so the cost of a line does not grow with the hundreds of written forms (about 50 times slower)."""
    monkeypatch.setenv(DSN_NAME, DEEP_VALUE)
    secrets = mr._secret_values((DSN_NAME,))
    built: list[str] = []
    real = mr._stripped_pattern
    monkeypatch.setattr(mr, "_stripped_pattern", lambda base: built.append(base) or real(base))
    mr._masked(LINE + "x" * 100, secrets)
    assert len(secrets) > 100, "the control is wrong: the value must have many written forms"
    assert len(built) == len(secrets.bases) <= 8, (
        f"the stripped-text match built {len(built)} patterns for {len(secrets)} written forms: one per plain text is enough"
    )


def test_a_line_with_more_spread_out_matches_than_the_limit_is_replaced_as_a_whole(monkeypatch):
    """Only the stripped-text match can find ``X'y9Zq1`` (the value has no quote mark): more matches than ``MAX_MATCHES`` replace the whole line."""
    monkeypatch.setenv(DSN_NAME, "host=db.invalid password=" + MARKER)
    secrets = mr._secret_values((DSN_NAME,))
    line = ("X'y9Zq1" + " ") * (mr.MAX_MATCHES + 5)
    started = time.monotonic()
    out = mr._masked(line, secrets)
    spent = time.monotonic() - started
    assert "line with more than" in out, (
        "a line with too many stripped-text matches was not replaced as a whole"
    )
    assert spent < 10, f"{mr.MAX_MATCHES} stripped-text matches took {spent:.1f} s"


def test_masking_a_quote_heavy_secret_on_a_long_line_stays_fast(monkeypatch):
    password = (
        "pw" + "".join("'" + '"' + chr(92) + "ab"[i % 2] for i in range(40)) + MARKER + chr(233)
    )
    value = "host=db.invalid password=" + password
    monkeypatch.setenv(DSN_NAME, value)
    started = time.perf_counter()
    secrets = mr._secret_values((DSN_NAME,))
    built = time.perf_counter() - started
    # the worst text for the patterns: the secret again and again, each time one character short, so every start is a long partial match
    kept = mr._stripped(value)
    for name, text in (
        ("near misses", ("ab'" + '"' + chr(92)) * 40_000),
        ("partial matches", (kept[:-1] + " ") * (400_000 // len(kept))),
        ("cut pieces", (kept[:8] + "..." + kept[-8:] + " ") * mr.MAX_FRAGMENT_HITS),
    ):
        started = time.perf_counter()
        out = mr._masked(text, secrets)
        spent = time.perf_counter() - started
        assert len(out) >= 1, "the masked text is empty"
        assert built < 5 and spent < 10, (
            f"masking is slow: {built:.2f} s to build, {spent:.2f} s for {len(text):,} characters of {name}"
        )


# ---- round 11: the run pattern is for short secrets only, pieces next to dots from EDGE_MIN, password pieces, exact forms, caches --------------


def test_a_long_base_with_a_quote_mark_has_no_run_pattern_and_does_not_halve_the_match_limit(
    monkeypatch,
):
    for base in ("ab'cdefghij", "Qw7xK2m" + chr(233), "a" + chr(92) + "bcdefg"):
        assert mr._run_pattern(base) is None, (
            f"a base of more than FRAGMENT_MIN stripped characters got a run pattern: {base!r}"
        )
    assert mr._run_pattern("ab'cdef") is None, (
        "a base of exactly FRAGMENT_MIN stripped characters got a run pattern"
    )
    assert mr._run_pattern("ab'cde") is not None, (
        "a base with fewer than FRAGMENT_MIN stripped characters got no run pattern"
    )
    monkeypatch.setenv(DSN_NAME, "ab'cdefgh")
    secrets = mr._secret_values((DSN_NAME,))
    line = (
        "E> " + "ab'cdefgh " * 60_000
    )  # 60,000 matches of the stripped-text pattern: a second pattern would make 120,000
    out = mr._masked(line, secrets)
    assert "line with more than" not in out and out.count(mr.MASK) == 60_000, (
        f"60,000 matches of a long base were treated as too many: {out[:80]}"
    )


EDGE_SECRETS = ("Qw7xK2m", "Qw'xK2m", "Qw7xK" + chr(233) + "m", 'Q"7xK2' + chr(92) + "m")


def test_every_head_and_tail_of_a_short_secret_next_to_dots_is_hidden(monkeypatch):
    """pytest's cut can fall anywhere in a 7-character secret: the 5 of 7 characters that a floor of 6 left readable are masked too (from EDGE_MIN on)."""
    leaked: list[tuple] = []
    cases = 0
    for secret in EDGE_SECRETS:
        monkeypatch.setenv(DSN_NAME, secret)
        secrets = mr._secret_values((DSN_NAME,))
        for k in range(mr.EDGE_MIN, len(secret)):
            for inner in (lambda x: x, *_INNER_PRINTERS):
                for outer in (lambda x: x, *_INNER_PRINTERS):
                    head, tail = outer(inner(secret[:k])), outer(inner(secret[-k:]))
                    if len(mr._stripped(secret[:k])) >= mr.EDGE_MIN:
                        cases += 1
                        out = mr._masked(LINE + head + "...zz", secrets)
                        if _readable(out) != _readable(LINE + "...zz"):
                            leaked.append(("head", k, head))
                    if len(mr._stripped(secret[-k:])) >= mr.EDGE_MIN:
                        cases += 1
                        out = mr._masked(LINE + "zz..." + tail, secrets)
                        if _readable(out) != _readable(LINE + "zz..."):
                            leaked.append(("tail", k, tail))
    assert cases > 500, f"the test shrank: {cases} cases"
    assert not leaked, (
        f"{len(leaked)} short head or tail pieces next to '...' were left readable, first: {leaked[0]}"
    )


def test_a_piece_next_to_dots_hides_only_that_piece_of_a_short_secret(monkeypatch):
    """The cost of masking from EDGE_MIN characters on is bounded: only a start of the secret right before ``...`` and an end of it right after one."""
    monkeypatch.setenv(DSN_NAME, "Qw7xK2m")
    secrets = mr._secret_values((DSN_NAME,))
    line = "E   'ab...cd' 'Qw...yz' 'zz...K2' 'to be...or not' Qw7 K2m 'x...2m'"
    out = mr._masked(line, secrets)
    assert (
        out == "E   'ab...cd' [REDACTED]...yz' 'zz...K2' 'to be...or not' Qw7 K2m 'x...[REDACTED]"
    ), (
        f"a piece that is not a start or an end of the secret, or one not next to dots, was changed: {out}"
    )
    many = "E>" + "Qw...Qw" * mr.MAX_FRAGMENT_HITS
    out = mr._masked(many, secrets)
    assert "line with more than" not in out and out.count(mr.MASK) == mr.MAX_FRAGMENT_HITS, (
        "a line full of pieces next to dots was replaced or masked wrongly"
    )


def test_dots_that_share_a_dot_are_all_found(monkeypatch):
    """``....`` holds two ``...`` (a head that ends in a dot, then the cut): both are looked at."""
    monkeypatch.setenv(DSN_NAME, "Zq1Xy9" + "." + "Pw3Tk5")
    secrets = mr._secret_values((DSN_NAME,))
    out = mr._masked("E   x == 'Zq1Xy9....bb'", secrets)
    assert out == "E   x == [REDACTED]...bb'", (
        f"a head that ends in a dot, before the cut, was not all hidden: {out}"
    )
    # the raw scan on its own (the stripped-text layer also finds this head, so only a direct call shows each ``...`` is looked at)
    secret = "Zq1Xy9" + "." + "Pw3Tk5"
    text = "x " + "Zq1Xy9" + "...." + "bb"
    spans = mr._fragment_spans(text, secret, list(mr._DOTS.finditer(text)))
    assert (2, 9) in spans and (2, 8) in spans, (
        f"a head that ends in a dot, before the cut, was not all hidden by the raw scan: {spans}"
    )


def test_the_pieces_of_an_unquoted_password_that_holds_a_quote_a_semicolon_or_an_ampersand_are_secrets(
    monkeypatch,
):
    monkeypatch.setenv(DSN_NAME, "host=db.invalid password=Ab3'Cd4Xy9;Pq7&Rs2Tk5 user=svc")
    bases = mr._secret_values((DSN_NAME,)).bases
    assert "Cd4Xy9" in bases, "a long piece of an unquoted password after a quote was not a secret"
    assert "Rs2Tk5" in bases, "a piece of an unquoted password after an ampersand was not a secret"
    assert "Pq7" in bases, "a piece of exactly PASSWORD_PIECE_MIN characters was not a secret"
    monkeypatch.setenv(DSN_NAME, "host=db.invalid password=Ab3'Zz;Qw user=svc")
    bases = mr._secret_values((DSN_NAME,)).bases
    assert "Zz" not in bases and "Qw" not in bases, (
        "a piece shorter than PASSWORD_PIECE_MIN characters was a secret"
    )
    out = mr._masked("E   saw Cd4Xy9 here", mr._secret_values((DSN_NAME,)))
    assert "Cd4Xy9" in out, "a piece of another value was hidden"
    monkeypatch.setenv(DSN_NAME, "host=db.invalid password=Ab3'Cd4Xy9;Pq7 user=svc")
    out = mr._masked("E   saw Cd4Xy9 here", mr._secret_values((DSN_NAME,)))
    assert "Cd4Xy9" not in out, "a piece that stands alone in a line was left readable"


def test_masking_a_short_quote_secret_on_a_long_line_stays_fast(monkeypatch):
    secret = "ab'c" + chr(92) + "d'" + chr(233)  # 5 stripped characters: a run pattern
    monkeypatch.setenv(DSN_NAME, secret)
    secrets = mr._secret_values((DSN_NAME,))
    assert mr._run_pattern(secret) is not None, (
        "the control is wrong: the secret has no run pattern"
    )
    near = (
        "ab'c" + chr(92) + "d'"
    )  # the secret without its last character, as written: a real near miss
    for name, text in (
        ("near misses", ("E> " + near + " ") * 40_000),
        ("runs only", "'a" * 150_000),
        ("runs and dots", ("E> " + near + " ... " + near + " ") * 500),
    ):
        started = time.perf_counter()
        out = mr._masked(text, secrets)
        spent = time.perf_counter() - started
        assert out == text, f"a near miss was hidden: {name}"
        assert spent < 10, f"masking is slow: {spent:.2f} s for {len(text):,} characters of {name}"


def test_a_short_secret_is_cut_out_exactly_where_its_run_pattern_found_it(monkeypatch):
    """The run view keeps a position for every character: the span cut out starts at the first character of the secret and ends after its last."""
    secret = "ab'c" + chr(233)
    monkeypatch.setenv(DSN_NAME, secret)
    secrets = mr._secret_values((DSN_NAME,))
    out = mr._masked("Aab'c" + chr(233) + "Z", secrets)
    assert out.startswith("A" + mr.MASK), (
        f"a match in plain text started at the wrong character: {out}"
    )
    assert out.endswith(mr.MASK + "Z"), f"a match in plain text ended at the wrong character: {out}"
    for sequence in ((0, 2, 0), (1, 0, 2), (4, 3, 1)):
        out = mr._masked("x1 " + _printed_n(secret, sequence) + " y2", secrets)
        assert out.startswith("x1 ") and out.endswith(" y2"), (
            f"the text around a short secret was changed: {out}"
        )
        before, mask, after = out.partition(mr.MASK)
        assert mask and _readable(before) == "x1 ", (
            f"a printed short secret was left readable at its start: {out}"
        )
        assert _readable(after) == " y2", (
            f"a printed short secret was left readable at its end: {out}"
        )
    monkeypatch.setenv(DSN_NAME, "'ab" + chr(233))  # starts with a quote mark
    out = mr._masked(
        "pre " + chr(92) * 2 + "'ab" + chr(92) + "xe9 post", mr._secret_values((DSN_NAME,))
    )
    assert out == "pre " + mr.MASK + " post", (
        f"a match that starts with a run did not start at the run: {out}"
    )
    monkeypatch.setenv(DSN_NAME, "ab" + chr(233) + "'")  # ends with a quote mark
    out = mr._masked("pre ab" + chr(92) + "xe9''' post", mr._secret_values((DSN_NAME,)))
    assert out == "pre " + mr.MASK + " post", (
        f"a match that ends with a run did not end at the run: {out}"
    )


def test_a_run_pattern_reads_runs_of_marks_and_the_escape_after_a_run():
    pattern = mr._run_pattern("ab'c")
    assert pattern is not None, "a short base with a quote mark got no run pattern"
    view = mr._run_view
    assert not pattern.search(view("abc")) and not pattern.search(view("ab c")), (
        "a run pattern matched text with no quote mark where the base has one"
    )
    two = mr._run_pattern("ab'" + chr(34) + "c")  # two marks in a row in the base are one run
    assert two is not None and two.search(view("ab" + chr(92) + "'c")), (
        "the marks in a row of a base were not read as one run in a run pattern"
    )
    accent = mr._run_pattern("a'" + chr(233) + "b")
    assert accent is not None and accent.search(view("a'" + chr(92) + "xe9b")), (
        "the backslash of an escape right after a run was required again"
    )


def test_the_written_forms_hold_what_each_printer_makes_of_a_value():
    value = "a'b" + chr(34) + "c" + chr(92) + chr(233) + chr(1)
    forms = mr._written_forms(value)
    messages = (
        "the repr print of a value is not one of its written forms",
        "the ascii print of a value is not one of its written forms",
        "the JSON print of a value is not one of its written forms",
        "the UTF-8 JSON print of a value is not one of its written forms",
        "the bytes print of a value is not one of its written forms",
        "the unicode_escape print of a value is not one of its written forms",
    )
    for printer, message in zip(_INNER_PRINTERS, messages, strict=True):
        assert printer(value) in forms, message


def test_the_written_forms_hold_a_print_of_a_print_and_the_double_quote_forms():
    plain = (
        "a" + chr(92) + "b" + chr(233)
    )  # no quote mark: layer 0 has one form, so a double print is a layer-2 form only
    for first in _INNER_PRINTERS:
        for second in _INNER_PRINTERS:
            assert second(first(plain)) in mr._written_forms(plain), (
                "a value printed twice is not one of its written forms"
            )
    value = "a'b" + chr(34) + "c" + chr(233)
    forms = mr._written_forms(value)
    assert value in forms, "a value with an unescaped double quote is not one of its written forms"
    assert _INNER_PRINTERS[0](_INNER_PRINTERS[0](value)) in forms, (
        "a value with both quote kinds printed twice by repr is not one of its written forms"
    )
    assert value.replace("'", chr(92) + "'") in forms, (
        "a value with an escaped single quote and an unescaped double quote is not one of its written forms"
    )
    assert value.replace(chr(34), chr(92) + chr(34)) in forms, (
        "a value with an escaped double quote and an unescaped single quote is not one of its written forms"
    )


def test_the_printed_forms_of_a_password_are_secrets_too(monkeypatch):
    password = "Pw" + chr(34) + "x" + chr(233) + "Z9"
    monkeypatch.setenv(DSN_NAME, "host=db.invalid user=svc password=" + password + " ")
    secrets = mr._secret_values((DSN_NAME,))
    assert ascii(password)[1:-1] in secrets, (
        "the ascii print of a password was not one of the secrets"
    )


def test_the_secret_caches_are_emptied_when_a_run_ends(tmp_path, monkeypatch):
    value = _key_value_value()[0]
    monkeypatch.setenv(DSN_NAME, value)
    root = _plain_compare_tree(tmp_path, value)
    lines: dict[str, str] = {}
    _run(root, [FLIP], pass_env=(DSN_NAME,), first_lines=lines)
    sizes = [
        cached.cache_info().currsize
        for cached in (mr._char_looks, mr._stripped_pattern, mr._run_pattern, mr._edge_patterns)
    ]
    assert sizes == [0, 0, 0, 0], f"a secret stayed in a cache after the run ended: {sizes}"


def _the_conftest_module():
    """The conftest module that pytest already loaded (its module-level lines, which set the fake cloud keys, are not run a second time); a run that
    has not loaded it (a plugin of another name) loads it from the file."""
    path = Path(__file__).with_name("conftest.py").resolve()
    for module in list(sys.modules.values()):
        if Path(getattr(module, "__file__", None) or "/").resolve() == path:
            return module
    spec = importlib.util.spec_from_file_location("repo_conftest", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_fixture_that_guards_the_database_address_fails_a_test_that_changes_it():
    module = _the_conftest_module()
    fixture = module._test_database_address_is_left_as_found
    body = getattr(fixture, "__wrapped__", fixture)
    quiet = body()
    next(quiet)
    with contextlib.suppress(StopIteration):
        next(quiet)  # nothing changed: no failure
    loud = body()
    next(loud)
    os.environ[DSN_NAME] = "changed by a test"
    try:
        next(loud)
    except pytest.fail.Exception as failure:
        assert "did not put it back" in str(failure)
    except StopIteration:
        raise AssertionError(
            "the fixture did not fail a test that changed the database address"
        ) from None
    else:
        raise AssertionError("the fixture did not fail a test that changed the database address")
    assert os.environ[DSN_NAME] == SENTINEL, "the fixture did not put the old value back"


def test_a_value_written_with_a_backslash_before_its_quote_is_masked_when_printed(monkeypatch):
    value = "host=db.invalid password=" + "it's" + MARKER + " user=svc"
    monkeypatch.setenv(DSN_NAME, value)
    secrets = mr._secret_values((DSN_NAME,))
    escaped = value.replace("'", chr(92) + "'")  # the way a libpq text or a shell writes it
    for name, text in (("repr", repr(escaped)), ("json", json.dumps(escaped))):
        out = mr._masked("E   " + text, secrets)
        assert MARKER not in out, (
            f"the backslash-escaped form printed by {name} survived the masking: {out}"
        )


def test_a_value_with_both_quote_kinds_is_masked_as_repr_of_repr_and_json_of_repr(monkeypatch):
    value = "host=db.invalid password=" + "it's" + chr(34) + "Xy9Zq1" + " user=svc"
    monkeypatch.setenv(DSN_NAME, value)
    secrets = mr._secret_values((DSN_NAME,))
    for name, text in (
        ("repr(repr(x))", repr(repr(value))),
        ("repr(json.dumps(x))", repr(json.dumps(value))),
        ("json.dumps(repr(x))", json.dumps(repr(value))),
    ):
        out = mr._masked("E   " + text, secrets)
        assert MARKER not in out, f"{name} survived the masking: {out}"


def test_a_plus_in_a_url_password_is_also_read_as_a_space(monkeypatch):
    value = "postgresql://svc:" + "Open+Sesame9" + "@db.invalid/app"
    monkeypatch.setenv(DSN_NAME, value)
    secrets = mr._secret_values((DSN_NAME,))
    assert "Open Sesame9" in secrets, "the plus-as-space form of the password was not a secret"
    assert "Sesame9" not in mr._masked("E   password Open Sesame9 wrong", secrets)
    # a percent code beside a plus: the plain percent rule keeps the plus, the form rule turns it into a space; both are secrets
    value = "postgresql://svc:" + "Open+Sesame%219" + "@db.invalid/app"
    monkeypatch.setenv(DSN_NAME, value)
    secrets = mr._secret_values((DSN_NAME,))
    assert "Open+Sesame!9" in secrets, "the percent-decoded form with a plus kept was not a secret"
    assert "Open Sesame!9" in secrets


def test_a_lock_file_that_is_a_fifo_is_refused_and_does_not_hang(tmp_path, monkeypatch):
    if not hasattr(os, "mkfifo"):
        pytest.skip("this system has no named pipes")
    path = tmp_path / _lock_name("fifo")
    os.mkfifo(path, 0o600)
    result: dict[str, object] = {}

    def attempt():
        result["exc"] = _refusal("fifo")

    worker = threading.Thread(target=attempt, daemon=True)
    worker.start()
    worker.join(10)
    hung = worker.is_alive()
    if hung:  # free the blocked open so the test run itself does not hang
        release = os.open(path, os.O_WRONLY | getattr(os, "O_NONBLOCK", 0))
        os.close(release)
        worker.join(5)
    assert not hung, "a FIFO under the lock file name hung the runner (the open blocked)"
    exc = result.get("exc")
    assert exc is not None, "a FIFO as the lock file was accepted"
    assert "regular file of this user" in str(exc), f"the refusal did not name the cause: {exc}"


def test_a_permission_refusal_of_the_lock_file_names_the_temp_folder_way_out():
    for code in (errno.EACCES, errno.EPERM):
        text = mr._why_not_opened(code)
        assert "TMPDIR" in text, f"no way out named for errno {code}: {text}"
        assert "read-only" in text, f"a read-only temp folder not named for errno {code}: {text}"


def _junit_refusal(junit):
    out: dict[str, object] = {}

    def attempt():
        try:
            out["text"] = mr._junit_text(junit)
        except ValueError as exc:
            out["exc"] = exc

    worker = threading.Thread(target=attempt, daemon=True)
    worker.start()
    worker.join(10)
    hung = worker.is_alive()
    if hung:
        release = os.open(junit, os.O_WRONLY | getattr(os, "O_NONBLOCK", 0))
        os.close(release)
        worker.join(5)
    assert not hung, "a FIFO as the JUnit file hung the runner"
    return out


def test_a_junit_path_that_is_not_a_regular_file_is_refused_and_does_not_hang(tmp_path):
    kinds = ["folder"]
    if hasattr(os, "mkfifo"):
        kinds.append("fifo")
    if hasattr(os, "symlink") and os.name != "nt":
        kinds.append("symlink")
    for kind in kinds:
        junit = tmp_path / f"{kind}.xml"
        if kind == "fifo":
            os.mkfifo(junit, 0o600)
        elif kind == "symlink":
            real = tmp_path / "real.xml"
            real.write_text("<testsuites/>", encoding="utf-8")
            junit.symlink_to(real)
        else:
            junit.mkdir()
        out = _junit_refusal(junit)
        assert "exc" in out, f"a {kind} as the JUnit file was read: {out}"
        assert "regular file" in str(out["exc"])
    assert mr._junit_text(tmp_path / "missing.xml") == ""


def test_an_over_sized_junit_file_is_refused_before_it_is_read(tmp_path, monkeypatch):
    junit = tmp_path / "junit.xml"
    junit.write_text("<testsuites>" + " " * 50 + "</testsuites>", encoding="utf-8")
    monkeypatch.setattr(mr, "MAX_JUNIT_CHARS", 10)

    def never(*_a, **_k):
        raise AssertionError("the file was read before its size was looked at")

    monkeypatch.setattr(Path, "read_text", never)
    with pytest.raises(ValueError, match="over the ceiling"):
        mr._junit_text(junit)
