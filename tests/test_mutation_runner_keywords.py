"""Tests of the three opt-in keywords of ``tools.mutation_runner.run_mutants`` (``conftest``, ``pass_env``, ``forbid_skips``) and of the
changes that are always on (the ``FIXTURE ERROR`` row and the judge's ERROR for a failing run that names no test: two changes of
result; plus the ``COLLECTION ERROR`` label, which only renames a row that was already ERROR).

Class: a mutant that "dies" because the tests could not run (skipped, or no database address, or a missing fixture file, or a fixture that
failed) is a FALSE kill. The fix sits at the runner (one choke point for every caller). Without a keyword the arguments of a run are the
old ones, and the only changed results are the always-on ones, each tested below.

Most killer tests give their assertion a message that names the guard (``_must_refuse`` and ``_must_raise`` write one too), so the
mutants in ``tests/mutation_runner_mutants.py`` can tell which guard was removed from the first line of the failure.
"""

import ast
import base64
import codecs
import contextlib
import errno
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
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
    # Two guards look alike on purpose. The fixture ``_test_database_address_is_left_as_found`` of ``tests/conftest.py`` watches every test of the
    # suite and puts the caller's value back. This one, in this file only, sets a sentinel (so a test that DELETES the address is told from a run
    # that never had one) and still works when the conftest is not loaded (a run with ``--noconftest``, the default of the mutation runner).
    # set up before the test's own ``monkeypatch`` and checked after it has undone its changes: only a direct os.environ write is caught
    with _dsn_left_as_found():
        yield


@pytest.fixture(autouse=True)
def _own_lock_folder(_guard_the_database_address, tmp_path, monkeypatch):
    # asks for the guard first, so the guard is set up before this ``monkeypatch`` and checked after it is undone
    monkeypatch.setattr(
        mr, "_lock_dir", lambda: tmp_path
    )  # each test its own lock folder: two test processes never share a lock


# the host of every made-up address in this file: a name that can never resolve (RFC 2606 reserves ``.invalid``). The tests hand it to the
# runner the way a caller does, with ``throwaway_hosts``, so the REAL address check runs in every test; nothing in this file switches it off.
FAKE_HOST = "db.invalid"
FAKE_HOSTS = (FAKE_HOST,)


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
        text = str(exc)
    else:
        raise AssertionError(f"{label}: nothing was raised")
    # checked outside the ``except`` block, so the first line of a failure is this assertion and not the error that was caught
    assert match in text, f"{label}: raised another message: {text}"


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
    """``run_mutants`` on the one test file of ``_tree``. A call that passes the address variable also names the made-up host on purpose
    (``throwaway_hosts=FAKE_HOSTS``) unless the test gives its own list: the same keyword a caller would use, and the real check runs."""
    if kw.get("pass_env"):
        kw.setdefault("throwaway_hosts", FAKE_HOSTS)
    return run_mutants(root, list(mutants), [CORE_TEST], extra_dirs=(), timeout=120, **kw)


def _short(rows):
    return [(n, v, good) for n, v, _, good in rows]


def _fake_dsn() -> str:
    user, secret = "someone", "pw"  # built from parts: no URL with a password stands in the source
    return f"postgresql://{user}:{secret}@db.invalid/x"


_PW_KEY = (
    "pass" + "word"
)  # the keyword of a password, built from parts: no fake credential stands as one literal in this file


def _url(user: str, *secret_parts: str, rest: str = "db.invalid/app") -> str:
    """A URL whose login holds the secret; the secret is given in parts so that no whole fake password is written in the source."""
    return f"postgresql://{user}:{''.join(secret_parts)}@{rest}"


def _kv(
    *secret_parts: str,
    key: str = _PW_KEY,
    before: str = "host=db.invalid user=svc",
    after: str = "",
) -> str:
    """A key=value address whose password (after ``key``) is given in parts."""
    return f"{before} {key}={''.join(secret_parts)}{after}"


def _secret_dsn() -> tuple[str, str]:
    user, head, tail = "svc_user", "Zq9x", "K4mTw"
    word = head + tail  # built from parts
    return f"postgresql://{user}:{word}@db.invalid/scratch", word


def _state_address(tmp_path: Path) -> str:
    """A made-up address in a shape the address check accepts (key=value words, the made-up host). The canary tests need one file that outlives
    the temp copies, as a database would: its path rides in the login word (``user=``), which the check does not read, and the test bodies cut it
    out again (``.split('user=')[1]``). Nothing ever connects to it."""
    return f"host={FAKE_HOST} dbname=scratch user={tmp_path / 'state.flag'}"


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
        # create the file where the name can be one, so the refusal can only come from the grammar and not from "is not a file of the tree"
        with contextlib.suppress(OSError, ValueError):
            target = root / bad
            if target.name and root.resolve() in target.resolve().parents:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(PASSES, encoding="utf-8")
        try:
            _run(root, conftest=bad)
        except ValueError as exc:
            assert "is not a file of the tree" not in str(exc), (
                f"conftest {bad!r} was refused only because the file is missing, not by the grammar"
            )
        else:
            raise AssertionError(f"conftest {bad!r}: was not refused")
    assert _run(root, conftest="") == [], "an empty conftest (the default) was not accepted"
    for bad in ("tests/my-conf.py", "tests/1x.py", "tests/", "tests/conf.txt"):
        _must_raise(
            f"conftest {bad!r}", ValueError, mr._plugin_module, bad, match="conftest must be"
        )


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
    try:
        rows = _run(root, pass_env=(DSN_NAME,))
    except RuntimeError:
        raise AssertionError(
            "SOME_API_TOKEN reached the child: the unmutated run failed its own check"
        ) from None
    assert rows == [], "a run with no mutants returned a row"


def test_pass_env_with_an_unset_variable_passes_nothing(tmp_path, monkeypatch):
    monkeypatch.delenv(DSN_NAME, raising=False)
    body = f"import os\n\ndef test_a():\n    assert {DSN_NAME!r} not in os.environ\n"
    root = _tree(tmp_path, {CORE_TEST: body})
    try:
        rows = _run(root, pass_env=(DSN_NAME,))
    except RuntimeError:
        raise AssertionError(
            "an unset variable was passed: the unmutated run found it in the child"
        ) from None
    assert rows == [], "a run with no mutants returned a row"


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
        _must_refuse(
            "an unlisted pass_env name was accepted", _run, root, pass_env=names, forbid_skips=False
        )  # the fake run writes no JUnit file, which forbid_skips would refuse
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


def _protection_off(mp) -> None:
    """The positive controls of the hiding tests: switch off BOTH layers (the projection of the child's text and the masker), so a test can show
    that the child really printed the value and that the check below could fail."""
    mp.setattr(mr, "_masked", lambda text, secrets: text)
    mp.setattr(mr, "_shown_line", lambda raw, shown, expect="": raw)
    mp.setattr(mr, "_shown_id", lambda test_id, shown, own_names=(): test_id)


def _showing_value_tree(tmp_path, dsn):
    """A tree whose test fails after the flip and whose failure line and test id both show the value."""
    body = (
        "import os\nimport pytest\nfrom pk.core import go\n\n"
        f"@pytest.mark.parametrize('v', [{dsn!r}])\n"
        f"def test_a(v):\n    assert go(True) == (os.environ[{DSN_NAME!r}] == v), os.environ[{DSN_NAME!r}]\n"
    )
    return _tree(tmp_path, {CORE_TEST: body})


def test_pass_env_values_never_reach_first_lines(tmp_path, monkeypatch):
    dsn, _word = _secret_dsn()
    monkeypatch.setenv(DSN_NAME, dsn)
    lines: dict[str, str] = {}
    _run(_showing_value_tree(tmp_path, dsn), [FLIP], pass_env=(DSN_NAME,), first_lines=lines)
    assert lines["flip"] == "AssertionError [expect not found] assert", (
        "the failure line was not the exact projection (the passed value reached first_lines, or the projection changed)"
    )


def test_pass_env_values_never_reach_the_failing_test_id_of_a_row(tmp_path, monkeypatch):
    dsn, word = _secret_dsn()
    monkeypatch.setenv(DSN_NAME, dsn)
    shows_value = Mutant("flip", "src/pk/core.py", "return flag", "return not flag", "postgresql")
    rows = _run(_showing_value_tree(tmp_path, dsn), [shows_value], pass_env=(DSN_NAME,))
    assert len(rows) == 1 and rows[0][1] is Verdict.KILLED, rows
    assert word not in rows[0][2] and dsn not in rows[0][2], (
        "the passed value reached the test id of a row"
    )
    assert rows[0][2] == "tests/test_core::test_a" + mr.PARAMETERS_HIDDEN, (
        f"the test id was not shown as file and function with the parameters hidden: {rows[0][2]}"
    )


def test_the_baseline_skip_message_never_holds_the_passed_value(tmp_path, monkeypatch):
    dsn, word = _secret_dsn()
    monkeypatch.setenv(DSN_NAME, dsn)
    body = (
        "import pytest\n\n"
        f"@pytest.mark.parametrize('v', [{dsn!r}])\n"
        "def test_a(v):\n    pytest.skip('no database')\n"
    )
    root = _tree(tmp_path, {CORE_TEST: body})

    def refusal_of_the_baseline() -> str:
        try:
            _run(root, [FLIP], pass_env=(DSN_NAME,), forbid_skips=True)
        except RuntimeError as exc:
            return str(exc)
        return ""

    with (
        monkeypatch.context() as control
    ):  # positive control: with the masking off, the test id of the skip holds the value
        _protection_off(control)
        assert word in refusal_of_the_baseline(), (
            "the positive control failed: the unmasked baseline skip message holds no password"
        )
    refusal = refusal_of_the_baseline()
    assert "skipped" in refusal, "a baseline that skips was accepted or refused otherwise"
    assert dsn not in refusal and word not in refusal, (
        "the baseline skip message held the passed value"
    )
    assert mr.PARAMETERS_HIDDEN in refusal, (
        "the baseline skip message did not hide the parameters of the test id"
    )


def test_masked_replaces_the_value_and_the_url_password(monkeypatch):
    dsn, word = _secret_dsn()
    assert mr._secret_values(()) == (), "no names must give no secrets"
    monkeypatch.setenv(DSN_NAME, dsn)
    secrets = mr._secret_values((DSN_NAME,))
    assert set(secrets) == {dsn, word}, (
        f"the secrets were not the value and its password ({len(secrets)} secrets)"
    )
    out = mr._masked(f"E assert {dsn} and only {word} here", secrets)
    assert out == "E assert [REDACTED] and only [REDACTED] here", (
        "a secret survived the masking, or the text around it changed"
    )


def test_a_percent_encoded_password_is_masked_in_both_forms(monkeypatch):
    first, second = "Qw7", "Rt5"
    raw = (
        first + "%40" + second
    )  # the URL carries the encoded form; a test may print the decoded one
    decoded = first + "@" + second
    monkeypatch.setenv(DSN_NAME, _url("svc", raw, rest="db.invalid/scratch"))
    secrets = mr._secret_values((DSN_NAME,))
    assert raw in secrets and decoded in secrets, (
        f"the decoded password was not a secret ({len(secrets)} secrets)"
    )
    out = mr._masked(f"E {raw} and {decoded}", secrets)
    assert out == "E [REDACTED] and [REDACTED]", (
        "a form of the password survived the masking, or the text around it changed"
    )


def _long_value() -> str:
    # 297 characters in a pattern no ordinary text has; built from parts, never a real credential
    return "".join(f"{hashlib.sha256(str(i).encode()).hexdigest()[:10]}-" for i in range(27))[:300]


def _key_value_value() -> tuple[str, str]:
    """A 60-character key=value address (no URL) with the password at the tail, and that password; built from parts."""
    head = f"host=db.invalid dbname=scratch user=svc {_PW_KEY}="
    word = hashlib.sha256(b"fragment").hexdigest()[: 60 - len(head)]
    return head + word, word


def _long_url() -> tuple[str, str]:
    """A long address in a shape the address check accepts (a URL on the made-up host) and its 60-character password, built from parts: pytest
    shortens such a text to ``head...tail`` in an assertion line."""
    word = hashlib.sha256(b"long url").hexdigest()[:60]
    return f"postgresql://svc:{word}@{FAKE_HOST}:5432/scratch", word


def _windows(secret: str, size: int = 6) -> set[str]:
    return {secret[i : i + size] for i in range(len(secret) - size + 1)}


def test_a_shortened_value_is_masked_by_its_fragments(monkeypatch):
    for value in (_key_value_value()[0], _long_value()):
        monkeypatch.setenv(DSN_NAME, value)
        secrets = mr._secret_values((DSN_NAME,))
        shown = f"E   AssertionError: assert '{value[:12]}...{value[-12:]}' == 'other'"
        out = mr._masked(shown, secrets)
        assert not any(w in out for w in _windows(value)), (
            "a fragment of the shortened value survived the masking"
        )
        assert out == "E   AssertionError: assert '[REDACTED]...[REDACTED]' == 'other'", (
            "the line was not kept around the markers"
        )
    assert mr._masked("E   x == 'a...l'", ("abcdefghijkl",)) == "E   x == 'a...l'", (
        "a one-character piece next to the dots was masked"
    )
    assert (
        mr._masked("E   x == 'ab...kl'", ("abcdefghijkl",)) == "E   x == '[REDACTED]...[REDACTED]'"
    ), "a two-character head or tail next to the dots was not masked"
    assert mr._masked("E   x == 'abc...def'", ("abcdefghijkl",)) == "E   x == '[REDACTED]...def'", (
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
    # a real run needs an address the check accepts; the masker's own reading of the other shapes is tested without a run, above
    for n, value in enumerate((_long_url()[0],)):
        monkeypatch.setenv(DSN_NAME, value)
        root = _plain_compare_tree(tmp_path / str(n), value)
        # positive control: with the masking off, the line really holds a fragment (so the check below can fail)
        with monkeypatch.context() as m:
            _protection_off(m)
            seen: dict[str, str] = {}
            _run(root, [FLIP], pass_env=(DSN_NAME,), first_lines=seen)
        assert "..." in seen["flip"], (
            "pytest did not shorten the value with dots, so the control cannot show a fragment"
        )
        assert any(w in seen["flip"] for w in _windows(value)), (
            "the positive control failed: pytest printed no fragment of the value"
        )
        lines: dict[str, str] = {}
        _run(root, [FLIP], pass_env=(DSN_NAME,), first_lines=lines)
        assert not any(w in lines["flip"] for w in _windows(value)), (
            "a fragment of the shortened value reached first_lines"
        )


def test_a_password_after_a_password_word_or_in_a_url_query_is_a_secret(monkeypatch):
    value, word = _key_value_value()
    monkeypatch.setenv(DSN_NAME, value)
    assert word in mr._secret_values((DSN_NAME,)), (
        "the password of a key=value address was not a secret"
    )
    query = (
        f"postgresql://db.invalid/scratch?sslmode=require&{_PW_KEY}=" + "Tk8" + "%2F" + "Vq2&x=1"
    )
    monkeypatch.setenv(DSN_NAME, query)
    secrets = mr._secret_values((DSN_NAME,))
    assert "Tk8%" + "2FVq2" in secrets and "Tk8" + "/Vq2" in secrets, (
        f"the password of a URL query was not a secret ({len(secrets)} secrets)"
    )
    monkeypatch.setenv(DSN_NAME, "host=db.invalid user=svc")
    assert mr._secret_values((DSN_NAME,)) == ("host=db.invalid user=svc",), (
        "a value with no password word gave another secret"
    )


def _secrets_of(value: str, monkeypatch) -> tuple[str, ...]:
    monkeypatch.setenv(DSN_NAME, value)
    return mr._secret_values((DSN_NAME,))


_HK = "Hk4L" + "m8Pq2"  # a made-up password, in parts


def test_passwd_and_pwd_words_are_secrets(monkeypatch):
    base = "host=db.invalid user=svc "
    assert _HK in _secrets_of(base + "pass" + "wd=" + _HK, monkeypatch), (
        "the password after passwd= was not a secret"
    )
    assert _HK in _secrets_of(base + "p" + "wd=" + _HK, monkeypatch), (
        "the password after pwd= was not a secret"
    )
    assert _HK in _secrets_of(base + "P" + "WD=" + _HK, monkeypatch), (
        "the password after PWD= was not a secret"
    )


def test_a_piece_of_exactly_the_edge_minimum_is_masked_and_a_shorter_one_is_not():
    secret = "Qw7xK2mTp9" + "Zr4Vb8Nc3L"  # built from parts
    head6 = mr._masked(f"E x == '{secret[:6]}...zzz'", (secret,))
    assert secret[:6] not in head6, f"a 6-character head next to the dots was not masked: {head6}"
    tail6 = mr._masked(f"E x == 'zzz...{secret[-6:]}'", (secret,))
    assert secret[-6:] not in tail6, f"a 6-character tail next to the dots was not masked: {tail6}"
    # the lower limit is EDGE_MIN (2): a 2-character piece is masked, a 1-character piece is accepted as ordinary text
    # (the sizes are written out on purpose: a mutant that moves EDGE_MIN must not move the test with it)
    head2 = mr._masked(f"E x == '{secret[:2]}...zzz'", (secret,))
    assert secret[:2] not in head2, f"a 2-character head next to the dots was not masked: {head2}"
    short = mr._masked(f"E x == '{secret[:1]}...zzz'", (secret,))
    assert secret[:1] in short, (
        f"a 1-character head was masked next to the dots, below the minimum: {short}"
    )
    tail = mr._masked(f"E x == 'zzz...{secret[-1:]}'", (secret,))
    assert secret[-1:] in tail, (
        f"a 1-character tail was masked next to the dots, below the minimum: {tail}"
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


def test_a_short_secret_inside_a_shortened_long_one_does_not_hide_the_long_one():
    # found by the property test: cutting the short long_value out first changed the text, and the tail of the long one no longer matched
    long_value = (
        "north-river-stone-" + "bridge-glacier-delta"
    )  # readable words, built from parts: 38 characters, more than the 12 + 13 shown
    shown = f"E   assert '{long_value[:12]}...{long_value[-13:]}' == 'other'"
    out = mr._masked(shown, (long_value, "ta"))
    assert out == "E   assert '[REDACTED]...[REDACTED]' == 'other'", (
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
    assert mr._masked("E   x == 'ghi...jkl'", secrets) == "E   x == 'ghi...jkl'", (
        "an honest line with dots was replaced"
    )


def _dots(text):
    return list(re.finditer(r"(?=\.\.\.)", text))


def _plain_spans(text, secret):
    """The plain definition of the spans (every length from the largest down), written out slowly on purpose: it is the reference of the fast scan."""
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
    return plain


def test_the_fragment_scan_agrees_with_the_plain_definition():
    """The scan was rewritten to be fast; it must still return the spans of the plain definition (every length from the largest down)."""
    rng = _Det(7)
    non_empty = 0
    for _ in range(300):
        secret = "".join(rng.choice("abcd") for _ in range(rng.randint(3, 20)))
        text = "".join(rng.choice("abcd.") for _ in range(rng.randint(0, 60)))
        if rng.randint(
            0, 1
        ):  # half of the cases hold a real head and tail of the secret beside the dots
            text = (
                text[:5]
                + secret[: rng.randint(1, len(secret))]
                + "..."
                + secret[-rng.randint(1, len(secret)) :]
                + text[5:]
            )
        plain = _plain_spans(text, secret)
        assert sorted(mr._fragment_spans(text, secret, _dots(text))) == sorted(plain), (
            "the fast scan found other spans than the plain definition"
        )
        non_empty += bool(plain)
    assert non_empty >= 30, (
        f"only {non_empty} of 300 comparisons had any span: the test compared empty lists"
    )


def test_the_fragment_scan_agrees_with_the_plain_definition_on_repeating_secrets():
    """Secrets and texts over two letters repeat themselves, which is where a prefix table that falls back wrongly gives another answer."""
    assert mr._prefix_table("aabaaab") == [0, 1, 0, 1, 2, 2, 3], (
        "the prefix table gave other lengths on a repeating secret"
    )
    rng = _Det(11)
    non_empty = 0
    for _ in range(400):
        secret = "".join(rng.choice("ab") for _ in range(rng.randint(3, 30)))
        head = secret[: rng.randint(0, len(secret) - 1)]
        tail = secret[len(secret) - rng.randint(0, len(secret) - 1) :]
        filler = "".join(rng.choice("ab") for _ in range(rng.randint(0, 25)))
        text = filler + head + "..." + tail + filler + "..." + filler + head
        fast = sorted(mr._fragment_spans(text, secret, _dots(text)))
        plain = sorted(_plain_spans(text, secret))
        assert fast == plain, (
            "the fast scan found other spans than the plain definition on a repeating secret"
        )
        non_empty += bool(plain)
    assert non_empty >= 200, f"only {non_empty} of 400 repeating cases had any span"


def test_the_work_of_one_ellipsis_is_linear_in_the_length_of_the_secret():
    """Counted, not timed: the executed lines of the two passes (``_prefix_table``, ``_longest_overlap``) stay within a fixed multiple of ``hits x len(secret)``."""
    secret = "a" * 1999 + "b"
    line = ("a" * 1998 + "c" + "...") * 100
    hits = list(mr._DOTS.finditer(line))
    events = [0]

    def tracer(frame, event, arg):
        code = frame.f_code
        if code.co_filename != mr.__file__ or code.co_name not in (
            "_prefix_table",
            "_longest_overlap",
        ):
            return None

        def local(frame, event, arg):
            if event == "line":
                events[0] += 1
            return local

        return local

    before = sys.gettrace()
    sys.settrace(tracer)
    try:
        mr._fragment_spans(line, secret, hits)
    finally:
        sys.settrace(before)
    assert events[0] > len(hits), (
        "the passes were not counted (the scan does not use _prefix_table and _longest_overlap)"
    )
    assert events[0] <= 12 * len(hits) * len(secret), (
        f"{events[0]} lines for {len(hits)} ellipses and a secret of {len(secret)} characters: the work is not linear"
    )


def test_the_fragment_scan_finds_the_largest_head_and_tail_at_every_size():
    # the largest head and tail (one character short of the whole secret) at every length, which random text almost never hits
    for size in range(3, 21):
        secret = "".join("pqrstuvwxyz"[(i * 3 + size) % 11] for i in range(size))
        top = size - 1
        text = secret[:top] + "..." + secret[-top:]
        spans = sorted(mr._fragment_spans(text, secret, _dots(text)))
        assert (0, top) in spans, f"the largest head of a {size}-character secret was not found"
        assert (top + 3, len(text)) in spans, (
            f"the largest tail of a {size}-character secret was not found"
        )
        assert len(spans) == 2, f"the scan of a {size}-character secret found a span too many"


# ---- pass_env: the shared database ------------------------------------------------------------------------------------------


# the "database" is a file: the test fails the way a dirty database does when the earlier run left something behind
DIRTY_AFTER_FLIP = (
    "import os\nfrom pathlib import Path\nfrom pk.core import go\n\n"
    f"def test_a():\n    state = Path(os.environ[{DSN_NAME!r}].split('user=')[1])\n    assert not state.exists(), 'a leftover of an earlier run'\n"
    "    if go(True) is not True:\n        state.write_text('x')\n    assert go(True) is True\n"
)


def test_a_database_that_a_mutant_left_dirty_stops_the_run_after_that_mutant(tmp_path, monkeypatch):
    monkeypatch.setenv(DSN_NAME, _state_address(tmp_path))
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
    monkeypatch.setenv(DSN_NAME, _state_address(tmp_path))
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
    monkeypatch.setenv(DSN_NAME, _state_address(tmp_path))
    root = _tree(tmp_path, {CORE_TEST: USES_GO})
    try:
        rows = _run(root, [FLIP], pass_env=(DSN_NAME,))
    except RuntimeError as exc:
        raise AssertionError(f"the canary ran the mutated copy: {exc}") from None
    assert _short(rows) == [("flip", Verdict.KILLED, True)], rows


def test_a_passed_name_set_to_an_empty_text_is_refused_before_any_run(tmp_path, monkeypatch):
    # an empty text is no address: the runner cannot check where the tests would write, so nothing runs (it used to get a canary run)
    monkeypatch.setenv(DSN_NAME, "")
    root = _tree(tmp_path, {CORE_TEST: USES_GO})
    count = []
    monkeypatch.setattr(mr, "_pytest", lambda *a, **k: count.append(a[2].name) or 0)
    _must_raise(
        "a passed name set to an empty text was accepted",
        ValueError,
        _run,
        root,
        [FLIP],
        pass_env=(DSN_NAME,),
        forbid_skips=False,  # so that a run which wrongly starts ends quietly and this check, not a later refusal, is what fails
        match="not in a shape",
    )
    assert count == [], f"a run started for a passed name set to an empty text: {count}"


SKIPS_WHEN_THE_DATABASE_IS_GONE = (
    "import os\nimport pytest\nfrom pathlib import Path\nfrom pk.core import go\n\n"
    f"def test_a():\n    state = Path(os.environ[{DSN_NAME!r}].split('user=')[1])\n    if state.exists():\n        pytest.skip('no database')\n"
    "    if go(True) is not True:\n        state.write_text('x')\n    assert go(True) is True\n"
)


def test_a_canary_run_that_skips_is_refused_under_forbid_skips(tmp_path, monkeypatch):
    monkeypatch.setenv(DSN_NAME, _state_address(tmp_path))
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
    monkeypatch.setenv(DSN_NAME, _state_address(tmp_path))
    root = _tree(tmp_path, {CORE_TEST: SKIPS_WHEN_THE_DATABASE_IS_GONE})
    rows = _run(root, [FLIP], pass_env=(DSN_NAME,), forbid_skips=False)
    assert _short(rows) == [("flip", Verdict.KILLED, True)]


def test_a_copy_that_cannot_be_rebuilt_for_the_canary_is_a_clear_refusal(tmp_path, monkeypatch):
    monkeypatch.setenv(DSN_NAME, _state_address(tmp_path))
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


def _lock_name(parts: str) -> str:
    """The lock file name for the hashed ``parts`` text, written out by the test (not computed by the code under test): ``"unparsed"`` for a
    value outside the grammar, or host, host address, port and database name joined by newlines."""
    return f"hadavin_mutation_{hashlib.sha256(parts.encode()).hexdigest()[:16]}.lock"


def test_a_second_runner_with_the_same_passed_value_is_refused(tmp_path, monkeypatch):
    value = _state_address(tmp_path)
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
    assert [f.name for f in tmp_path.glob("hadavin_mutation_*.lock")] == [
        _lock_name(f"{FAKE_HOST}\n\n\nscratch")
    ], (
        "the lock file was not named by the first 16 hex digits of the SHA-256 of the address parts (and by nothing else)"
    )


def test_an_exit_right_after_the_lock_is_taken_still_gives_the_lock_back(tmp_path, monkeypatch):
    value = _state_address(tmp_path)
    monkeypatch.setenv(DSN_NAME, value)
    root = _tree(tmp_path, {CORE_TEST: USES_GO})
    entered = contextlib.ExitStack.enter_context

    def enter_then_exit(self, manager):
        entered(self, manager)
        raise SystemExit(7)

    with monkeypatch.context() as patched:
        patched.setattr(contextlib.ExitStack, "enter_context", enter_then_exit)
        # ``caught`` keeps the traceback, and with it the frame of the run, alive: a lock that only the garbage collector would give back stays held
        with pytest.raises(SystemExit) as caught:
            _run(root, [FLIP], pass_env=(DSN_NAME,))
    assert caught.value.code == 7, (
        "the run did not end with the exit that was raised after the lock"
    )
    try:
        rows = _run(root, [FLIP], pass_env=(DSN_NAME,))
    except RuntimeError as exc:
        if "another mutation run" not in str(exc):
            raise
        raise AssertionError(
            "an exit right after the lock was taken left the lock held: the next run was refused"
        ) from None
    assert _short(rows) == [("flip", Verdict.KILLED, True)], "the next run gave other rows"


def test_the_lock_is_still_held_while_the_mutants_run(tmp_path, monkeypatch):
    value = _state_address(tmp_path)
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


def _open_refusing_the_lock_file(code, error=OSError):
    """``os.open`` that fails with ``code`` for the lock FILE only (the one open that is made under the lock folder, ``dir_fd``; on Windows the
    one whose name ends in ``.lock``): the open of the lock folder itself stays real."""
    real = os.open

    def opened(path, *a, **k):
        if "dir_fd" in k or str(path).endswith(".lock"):
            raise error(code, "refused")
        return real(path, *a, **k)

    return opened


def test_a_lock_file_that_cannot_be_opened_is_a_clear_refusal(tmp_path, monkeypatch):
    monkeypatch.setattr(os, "open", _open_refusing_the_lock_file(errno.EACCES, PermissionError))
    caught = None
    try:
        with mr._one_run_per_database(["x"]):
            pass
    except (RuntimeError, OSError) as exc:
        caught = exc
    assert isinstance(caught, RuntimeError), f"the open failure was not a clear refusal: {caught!r}"
    assert "lock file of this run could not be opened" in str(caught), f"another refusal: {caught}"


def test_a_lock_file_that_is_a_symbolic_link_is_refused_and_the_file_has_mode_0600(tmp_path):
    if os.name == "nt":
        pytest.skip("symbolic links and file modes are POSIX here")
    target = tmp_path / "target"
    target.write_text("x")
    (tmp_path / _lock_name("unparsed")).symlink_to(target)
    caught = None
    try:
        with mr._one_run_per_database(["x"]):
            pass
    except (RuntimeError, OSError) as exc:
        caught = exc
    assert isinstance(caught, RuntimeError) and "symbolic link" in str(caught), (
        f"a planted symbolic link was followed or refused otherwise: {caught!r}"
    )
    # no mask of the caller may hide a wide mode (a mask of 077 would turn 0666 into 0600): the file is made under mask 0
    outer_mask = os.umask(0)
    try:
        with mr._one_run_per_database(["host=y"]):
            pass
    except RuntimeError as exc:
        raise AssertionError(f"the lock file was not private: {exc}") from None
    finally:
        os.umask(outer_mask)
    mode = (tmp_path / _lock_name("y\n\n\n")).stat().st_mode & 0o777
    assert mode == 0o600, f"the lock file was not private: {oct(mode)}"


def _canary_ends_with(tmp_path, monkeypatch, code):
    monkeypatch.setenv(DSN_NAME, _state_address(tmp_path))
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
    # positive control: the same tree without forbid_skips runs (the refusal below comes from the skip rule, not from a broken tree)
    assert _run(root, []) == [], "the xfail tree did not run without forbid_skips"
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


def test_the_environment_is_read_once_and_a_change_during_the_run_changes_nothing(
    tmp_path, monkeypatch
):
    old = _fake_dsn()
    new = _url("svc", "Nw4", "Yv8", rest="other.invalid/y")
    monkeypatch.setenv(DSN_NAME, old)
    body = (
        "import os\nfrom pk.core import go\n\n"
        f"def test_a():\n    assert os.environ[{DSN_NAME!r}] == {old!r}, 'the child got another value than the snapshot'\n"
        "    assert go(True) is True, 'the mutant is judged'\n"
    )
    root = _tree(tmp_path, {CORE_TEST: body})
    # ``expect`` is the message of the second assertion: a child that got another value fails the FIRST assertion, and the row is then WRONG_REASON
    first = Mutant(
        "flip", "src/pk/core.py", "return flag", "return not flag", "the mutant is judged"
    )
    second = Mutant(
        "flip2", "src/pk/core.py", "return flag", "return not flag", "the mutant is judged"
    )
    lines: dict[str, str] = {}

    def change_the_variable(_row):
        monkeypatch.setenv(
            DSN_NAME, new
        )  # the caller edits its own environment while the run is going

    try:
        rows = _run(
            root,
            [first, second],
            pass_env=(DSN_NAME,),
            first_lines=lines,
            on_result=change_the_variable,
        )
    except mr.CanaryFailed:
        raise AssertionError(
            "a canary run got the changed value: the environment was read again"
        ) from None
    assert _short(rows)[0] == ("flip", Verdict.KILLED, True), (
        "the first mutant did not see the value"
    )
    assert _short(rows) == [("flip", Verdict.KILLED, True), ("flip2", Verdict.KILLED, True)], (
        "the second mutant run got the changed value: the environment was read again"
    )
    shown = "AssertionError [expect found] the mutant is judged"
    assert lines == {"flip": shown, "flip2": shown}, (
        f"the lines were not the projection of the old value: {lines}"
    )


def test_a_default_call_passes_pytest_no_plugin_and_no_env_names(tmp_path, monkeypatch):
    root = _tree(tmp_path, {CORE_TEST: PASSES})
    calls = []

    def fake(*args, **kwargs):
        calls.append((len(args), kwargs))
        return 0

    monkeypatch.setattr(mr, "_pytest", fake)
    _run(root)
    assert calls == [(4, {"plugin": "", "env_names": (), "environ": mr._env_snapshot(())})], (
        "a default call changed the arguments of the pytest run"
    )


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
    assert lines.get("flip", "").startswith("E"), "the FIXTURE ERROR row kept no message"
    assert lines["flip"] == "E       assert False is True", (
        "the FIXTURE ERROR message is not the assertion of the fixture"
    )


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
    assert mr.PARAMETERS_HIDDEN in shown, (
        "the SKIPPED TESTS message did not hide the parameters of the test id"
    )


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


def test_a_url_password_with_unencoded_separators_is_masked(monkeypatch):
    monkeypatch.setenv(DSN_NAME, _url("svc", "Ab3/", "Xy9@", "Zq1" + "#Wm2"))
    secrets = mr._secret_values((DSN_NAME,))
    out = mr._masked(f"E   {_PW_KEY} was " + "Ab3/" + "Xy9@" + "Zq1#Wm2 here", secrets)
    assert out == f"E   {_PW_KEY} was [REDACTED] here", (
        "a URL password with an unencoded slash or hash was not hidden in full"
    )
    monkeypatch.setenv(DSN_NAME, _url("svc", "Ab3/", "Xy9Zq1?", "Wm2" + "#Kd7"))
    out = mr._masked("E   " + "Ab3/" + "Xy9Zq1?" + "Wm2#Kd7", mr._secret_values((DSN_NAME,)))
    assert out == "E   [REDACTED]", (
        "a URL password with an unencoded question mark was not hidden in full"
    )


def test_nothing_is_rebuilt_when_no_secret_is_set():
    text = "E   assert 1 == 2"
    assert mr._masked(text, ()) is text and mr._masked(text, ("",)) is text, (
        "a text with no secret was rebuilt"
    )


def _own_lock_file(tmp_path, name):
    path = tmp_path / _lock_name(
        "unparsed"
    )  # ``name`` is no address (not in the grammar), so the lock hashes "unparsed"
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
        if stat.S_ISDIR(
            info.st_mode
        ):  # the lock folder keeps its real record: this fake is about the lock file
            return info
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
        monkeypatch.setattr(os, "open", _open_refusing_the_lock_file(code))
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
        if stat.S_ISDIR(info.st_mode):  # the lock folder itself: left as it is
            return info
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
    assert len(opened) == (1 if os.name == "nt" else 2), (
        f"the lock folder and the lock file were not each opened once: {opened}"
    )
    for fd in opened:  # the folder's descriptor and the file's: both must be closed again
        try:
            os.fstat(fd)
        except OSError:
            continue
        raise AssertionError("the descriptor stayed open (the lock folder's or the lock file's)")


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


# ---- round 11: the run pattern is for short secrets only, pieces next to dots from EDGE_MIN, password pieces, exact forms, caches --------------


def test_a_piece_next_to_dots_hides_only_that_piece_of_a_short_secret(monkeypatch):
    """The cost of masking from EDGE_MIN characters on is bounded: only a start of the secret right before ``...`` and an end of it right after one."""
    monkeypatch.setenv(DSN_NAME, "Qw7" + "xK2m")
    secrets = mr._secret_values((DSN_NAME,))
    line = "E   'ab...cd' 'Qw...yz' 'zz...K2' 'to be...or not' Qw7 K2m 'x...2m'"
    out = mr._masked(line, secrets)
    assert (
        out == "E   'ab...cd' '[REDACTED]...yz' 'zz...K2' 'to be...or not' Qw7 K2m 'x...[REDACTED]'"
    ), (
        f"a piece that is not a start or an end of the secret, or one not next to dots, was changed: {out}"
    )
    many = "E>" + "Qw...Qw" * mr.MAX_FRAGMENT_HITS
    out = mr._masked(many, secrets)
    assert "line with more than" not in out and out.count(mr.MASK) == mr.MAX_FRAGMENT_HITS, (
        "a line full of pieces next to dots was replaced or masked wrongly"
    )
    one_more = "E>" + "Qw...Qw" * (mr.MAX_FRAGMENT_HITS + 1)
    out = mr._masked(one_more, secrets)
    assert out.startswith(mr.MASK) and "line with more than" in out and "Qw" not in out, (
        "a line with one more '...' than MAX_FRAGMENT_HITS was not replaced as a whole"
    )


def test_dots_that_share_a_dot_are_all_found(monkeypatch):
    """``....`` holds two ``...`` (a head that ends in a dot, then the cut): both are looked at."""
    monkeypatch.setenv(DSN_NAME, "Zq1Xy9" + "." + "Pw3Tk5")
    secrets = mr._secret_values((DSN_NAME,))
    out = mr._masked("E   x == 'Zq1Xy9....bb'", secrets)
    assert out == "E   x == '[REDACTED]...bb'", (
        f"a head that ends in a dot, before the cut, was not all hidden: {out}"
    )
    # the scan on its own: each ``...`` is looked at, also the one that starts one dot later
    secret = "Zq1Xy9" + "." + "Pw3Tk5"
    text = "x " + "Zq1Xy9" + "...." + "bb"
    spans = mr._fragment_spans(text, secret, list(mr._DOTS.finditer(text)))
    assert (2, 9) in spans and (2, 8) in spans, (
        f"a head that ends in a dot, before the cut, was not all hidden by the raw scan: {spans}"
    )


# ---- round 12: a secret with a character that a print changes is refused up front; every other secret is matched as plain text ---------------


def _refusal_text(label: str) -> str:
    """The text of the ``ValueError`` of ``_secret_values`` for the passed name; the assertion line is ``label`` when nothing was refused."""
    try:
        mr._secret_values((DSN_NAME,))
    except ValueError as exc:
        return str(exc)
    raise AssertionError(label)


_HEAD, _TAIL = "Ab3", "Xy9" + "Zq1"  # the parts of the secrets that the refusals must never show


def _in_value(odd: str) -> tuple[str, str]:
    """A value that is odd as a whole, and the same odd text as the password inside a key=value text."""
    return _HEAD + odd + _TAIL, _kv(_HEAD, odd, _TAIL)


def test_a_value_with_a_quote_mark_is_refused_and_the_message_names_no_secret(monkeypatch):
    for value in (
        *_in_value("'"),
        *_in_value('"'),
        "'" + '"' + "'" + '"' + "'",
    ):  # the last: only quote marks
        monkeypatch.setenv(DSN_NAME, value)
        text = _refusal_text("a value with a quote mark was not refused")
        assert DSN_NAME in text and "a quote mark" in text and "its value" in text, (
            f"the refusal of a quote mark names the wrong variable, kind or text: {text}"
        )
        assert _TAIL not in text and _HEAD not in text, (
            f"the refusal of a quote mark holds a piece of the secret: {text}"
        )


def test_a_value_with_a_backslash_is_refused_and_the_message_names_no_secret(monkeypatch):
    for value in _in_value(chr(92)):
        monkeypatch.setenv(DSN_NAME, value)
        text = _refusal_text("a value with a backslash was not refused")
        assert DSN_NAME in text and "a backslash" in text and "its value" in text, (
            f"the refusal of a backslash names the wrong variable, kind or text: {text}"
        )
        assert _TAIL not in text and _HEAD not in text, (
            f"the refusal of a backslash holds a piece of the secret: {text}"
        )


def test_a_value_with_a_control_character_is_refused_and_the_message_names_no_secret(monkeypatch):
    for code in (1, 9, 10, 13, 31):  # an environment cannot hold chr(0)
        for value in _in_value(chr(code)):
            monkeypatch.setenv(DSN_NAME, value)
            text = _refusal_text("a value with a control character below the space was not refused")
            assert DSN_NAME in text and "a control character" in text and "its value" in text, (
                f"the refusal of a control character names the wrong variable, kind or text: {text}"
            )
            assert _TAIL not in text and _HEAD not in text, (
                f"the refusal of a control character holds a piece of the secret: {text}"
            )
    monkeypatch.setenv(DSN_NAME, _in_value(chr(127))[0])
    text = _refusal_text("a value with the DEL character was not refused")
    assert "a control character" in text, f"the DEL character was named as another kind: {text}"


def test_a_value_with_a_non_ascii_character_is_refused_and_the_message_names_no_secret(
    monkeypatch,
):
    for odd in (chr(233), chr(0x1F600)):
        for value in _in_value(odd):
            monkeypatch.setenv(DSN_NAME, value)
            text = _refusal_text("a value with a non-ASCII character was not refused")
            assert DSN_NAME in text and "a non-ASCII character" in text and "its value" in text, (
                f"the refusal of a non-ASCII character names the wrong variable, kind or text: {text}"
            )
            assert _TAIL not in text and _HEAD not in text, (
                f"the refusal of a non-ASCII character holds a piece of the secret: {text}"
            )
    monkeypatch.setenv(DSN_NAME, _in_value(chr(128))[0])
    text = _refusal_text("a value with the first non-ASCII character was not refused")
    assert "a non-ASCII character" in text, (
        f"the first non-ASCII character was named as another kind: {text}"
    )


def _decoded_values(code: str) -> tuple[str, str, str]:
    """Three plain-looking values whose password holds the percent ``code`` (a URL login, a key=value text and a URL query)."""
    return (
        _url("svc", _HEAD, code, _TAIL, rest="db.invalid/scratch"),
        _kv(_HEAD, code, _TAIL),
        f"postgresql://db.invalid/scratch?{_PW_KEY}=" + _HEAD + code + _TAIL,
    )


def test_a_password_that_decodes_to_an_odd_character_is_refused_and_the_message_names_no_secret(
    monkeypatch,
):
    for code, kind, label in (
        ("%27", "a quote mark", "a password that decodes to a quote mark was not refused"),
        ("%22", "a quote mark", "a password that decodes to a double quote mark was not refused"),
        ("%5C", "a backslash", "a password that decodes to a backslash was not refused"),
        ("%09", "a control character", "a password that decodes to a tab was not refused"),
        ("%7F", "a control character", "a password that decodes to DEL was not refused"),
        (
            "%C3%A9",
            "a non-ASCII character",
            "a password that decodes to a letter with an accent was not refused",
        ),
        (
            "%C3",
            "a non-ASCII character",
            "a password that decodes to a replacement character was not refused",
        ),
        (
            "%C2%80",
            "a non-ASCII character",
            "a password that decodes to a C1 control character was not refused",
        ),
        ("%00", "a control character", "a password that decodes to a NUL was not refused"),
        ("%0A", "a control character", "a password that decodes to a line feed was not refused"),
    ):
        for value in _decoded_values(code):
            monkeypatch.setenv(DSN_NAME, value)
            text = _refusal_text(label)
            assert kind in text and "percent-decoded" in text and DSN_NAME in text, (
                f"the refusal of {code} names the wrong variable, kind or text: {text}"
            )
            assert _TAIL not in text and _HEAD not in text, (
                f"the refusal of a decoded password holds a piece of the secret: {text}"
            )
    monkeypatch.setenv(DSN_NAME, _kv("Ab3%20", "Xy9%2F%40"))
    assert "Ab3 " + "Xy9/@" in mr._secret_values((DSN_NAME,)), (
        "a percent code of a plain character was refused or not read"
    )


def test_the_printable_ascii_range_is_accepted_and_the_characters_next_to_it_are_not(monkeypatch):
    plain = "".join(chr(c) for c in range(32, 127) if chr(c) not in "'\"" + chr(92))
    monkeypatch.setenv(DSN_NAME, _kv(plain))
    try:
        secrets = mr._secret_values((DSN_NAME,))
    except ValueError:
        raise AssertionError(
            "a value of the plain printable characters (space to tilde) was refused"
        ) from None
    assert _kv(plain) in secrets, (
        "a value of the plain printable characters (space to tilde) was not a secret"
    )
    # the password itself starts after the space that follows ``=`` and ends at the next white space (there is none: the others are inside it)
    assert plain.lstrip(" ") in secrets, (
        "the password part of the printable range (without the leading space) was not a secret"
    )
    monkeypatch.setenv(DSN_NAME, "")
    assert mr._secret_values((DSN_NAME,)) == (), "an empty value was refused or made a secret"
    monkeypatch.delenv(DSN_NAME)
    assert mr._secret_values((DSN_NAME,)) == (), (
        "a name that is not set was refused or made a secret"
    )


def test_run_mutants_refuses_an_odd_value_before_any_temp_folder_and_names_no_secret(
    tmp_path, monkeypatch
):
    root = _tree(tmp_path, {CORE_TEST: PASSES})
    made = []
    real = mr.tempfile.mkdtemp
    monkeypatch.setattr(mr.tempfile, "mkdtemp", lambda *a, **k: made.append(1) or real(*a, **k))
    for value in (
        _kv("Ab3'", "Xy9" + "Zq1", before="host=db.invalid"),
        _url("svc", "Ab3%C3", "%A9Xy9Zq1", rest="db.invalid/scratch"),
    ):
        monkeypatch.setenv(DSN_NAME, value)
        with pytest.raises(ValueError) as caught:
            _run(root, [FLIP], pass_env=(DSN_NAME,))
        assert "Xy9" + "Zq1" not in str(caught.value) and "Ab3" not in str(caught.value), (
            f"the refusal held a piece of the secret: {caught.value}"
        )
    assert made == [], "a temp folder was made before the odd value was refused"


def _review_value() -> tuple[str, str]:
    """The case of the round 12 review: a long address with the password last, which pytest prints as ``head...tail``."""
    head = f"host=db.internal.example.org port=5432 dbname=mutants user=svc {_PW_KEY}="
    word = "Zq9x" + "K2mP7wRt4vNb8LcY3"  # built from parts
    return head + word, word


# the first lines of a real pytest 9.2 run on that value (observed; see the evidence folder of round 12), and what they must become:
# a string, a list, a dict, a tuple (where the head ends in a dot, so ``....`` shows) and bytes
REAL_PYTEST_LINES = (
    (
        "AssertionError: assert 'host=db.inte...7wRt4vNb8LcY3' == 'other'",
        "AssertionError: assert '[REDACTED]...[REDACTED]' == 'other'",
    ),
    (
        "AssertionError: assert ['host=db.int...wRt4vNb8LcY3'] == ['other']",
        "AssertionError: assert ['[REDACTED]...[REDACTED]'] == ['other']",
    ),
    (
        "AssertionError: assert {'dsn': 'host...LcY3', 'n': 1} == {'dsn': 'other', 'n': 1}",
        "AssertionError: assert {'dsn': '[REDACTED]...[REDACTED]', 'n': 1} == {'dsn': 'other', 'n': 1}",
    ),
    (
        "AssertionError: assert (1, 'host=db....wRt4vNb8LcY3') == (1, 'host=db....Nb8LcY3', 'x')",
        "AssertionError: assert (1, '[REDACTED]...[REDACTED]') == (1, '[REDACTED]...[REDACTED]', 'x')",
    ),
    (
        "AssertionError: assert b'host=db.int...7wRt4vNb8LcY3' == b'other'",
        "AssertionError: assert b'[REDACTED]...[REDACTED]' == b'other'",
    ),
)


def test_a_long_value_that_pytest_prints_as_head_and_tail_is_masked_in_what_it_shows(monkeypatch):
    value, _word = _review_value()
    monkeypatch.setenv(DSN_NAME, value)
    secrets = mr._secret_values((DSN_NAME,))
    for line, expected in REAL_PYTEST_LINES:
        assert mr._masked(line, secrets) == expected, (
            f"a shortened value was masked wrongly: {line}"
        )


def test_the_value_that_pytest_shortens_never_reaches_a_row_from_a_real_run(tmp_path, monkeypatch):
    value, word = _long_url()
    monkeypatch.setenv(DSN_NAME, value)
    root = _plain_compare_tree(tmp_path, value)
    with (
        monkeypatch.context() as control
    ):  # positive control: with the masking off, the line really holds pieces
        _protection_off(control)
        seen: dict[str, str] = {}
        _run(root, [FLIP], pass_env=(DSN_NAME,), first_lines=seen)
    assert "..." in seen["flip"] and any(w in seen["flip"] for w in _windows(value)), (
        "the positive control failed: pytest printed no piece of the value"
    )
    lines: dict[str, str] = {}
    _run(root, [FLIP], pass_env=(DSN_NAME,), first_lines=lines)
    assert not any(w in lines["flip"] for w in _windows(value)), (
        "a piece of the shortened value reached first_lines"
    )
    assert not any(w in lines["flip"] for w in _windows(word, 4)), (
        "a piece of the password reached first_lines"
    )


_PRINTERS = (
    repr,
    ascii,
    json.dumps,
    lambda text: repr(text.encode("utf-8")),
)


def test_a_plain_value_is_masked_at_any_print_depth_whole_or_shortened(monkeypatch):
    """Property test (seeded): a value of plain characters stays in every print of it, so ``find`` hides it at depth 1 to 5, whole or cut around ``...``."""
    rng = _Det(20261112)
    alphabet = "abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789 %+;&@/:=.-_()"
    ran = cut_checked = 0
    for n in range(150):
        core = "".join(rng.choice(alphabet) for _ in range(rng.randint(8, 24))).strip() + "Q7"
        value = _kv(core)
        monkeypatch.setenv(DSN_NAME, value)
        try:
            secrets = mr._secret_values((DSN_NAME,))
        except ValueError:  # a % that decodes to an odd character: refused (tested above)
            continue
        ran += 1
        printed = value
        for depth in range(1, 6):
            printed = rng.choice(_PRINTERS)(printed)
            whole = mr._masked(f"E   AssertionError: assert {printed} == 1", secrets)
            assert core not in whole and value not in whole, (
                f"case {n} depth {depth}: the value survived"
            )
            if len(printed) < 40:
                continue
            cut_checked += 1
            cut = f"E   AssertionError: assert {printed[:12]}...{printed[-13:]} == 1"
            out = mr._masked(cut, secrets)
            left = [
                w
                for w in {value[i : i + 6] for i in range(len(value) - 5)}
                if w in out and w in cut
            ]
            assert not left, f"case {n} depth {depth}: {len(left)} pieces of the value are left"
    assert ran >= 60 and cut_checked >= 100, (
        f"the property test checked too little (cases {ran}, cut lines {cut_checked})"
    )


def test_every_head_and_tail_of_a_short_plain_secret_next_to_dots_is_hidden(monkeypatch):
    """pytest's cut can fall anywhere in a 7-character secret: every start and end of 2 or more characters is masked (from EDGE_MIN on)."""
    cases = 0
    for secret in ("Qw7" + "xK2m", "Qw7" + ".K2m", "Q w" + "7xK2"):
        monkeypatch.setenv(DSN_NAME, secret)
        secrets = mr._secret_values((DSN_NAME,))
        for k in range(mr.EDGE_MIN, len(secret)):
            cases += 2
            assert mr._masked("E>'" + secret[:k] + "...zz'", secrets) == "E>'[REDACTED]...zz'", (
                f"a head of {k} characters next to the dots was not masked"
            )
            assert mr._masked("E>'zz..." + secret[-k:] + "'", secrets) == "E>'zz...[REDACTED]'", (
                f"a tail of {k} characters next to the dots was not masked"
            )
    assert cases == 3 * 2 * (7 - mr.EDGE_MIN), f"the test shrank: {cases} cases"


def test_a_value_inside_a_bigger_secret_or_overlapping_another_is_masked_in_full():
    assert mr._masked("x abcdefg y", ("abcdefg", "cde")) == "x [REDACTED] y", (
        "a short secret inside a long one broke the long match"
    )
    assert mr._masked("xabcdy", ("abc", "bcd")) == "x[REDACTED]y", (
        "two secrets that overlap were not both hidden in full"
    )
    assert mr._masked("a" * 10, ("aaaa",)) == "[REDACTED]", (
        "a secret that overlaps itself left a rest readable"
    )
    # "ab" has two characters (EDGE_MIN) and the piece rule needs PASSWORD_PIECE_MIN (3); the line holds no secret, so it is kept as it is
    assert mr._masked("ab", ("zz",)) == "ab", "a text with no secret was changed"


def test_a_one_character_secret_on_a_huge_line_is_masked_fast_and_a_normal_line_is_kept():
    start = time.monotonic()
    out = mr._masked("E   " + "a" * 3_000_000 + "b", ("a", "ta"))
    took = time.monotonic() - start
    assert out == "E   [REDACTED]b", f"a huge line of one secret was masked wrongly: {out[:60]!r}"
    start2 = time.monotonic()
    out = mr._masked("a" * 1_000_000, ("a" * 1000,))
    took += time.monotonic() - start2
    assert out == "[REDACTED]", "a huge line with a long secret that overlaps itself was not masked"
    # the outputs above are the exact check; this bound only catches a scan that takes minutes, so a slow machine does not fail it
    assert took < 60, f"the masking of the huge lines took {took:.1f} seconds"
    assert (
        mr._masked("E   a banana", ("a",)) == "E   [REDACTED] b[REDACTED]n[REDACTED]n[REDACTED]"
    ), "a normal line with a few matches was replaced as a whole or not masked"


def test_the_pieces_of_an_unquoted_password_that_holds_a_semicolon_or_an_ampersand_are_secrets(
    monkeypatch,
):
    monkeypatch.setenv(
        DSN_NAME, _kv("Ab3;", "Cd4Xy9;", "Pq7&Rs2Tk5", before="host=db.invalid", after=" user=svc")
    )
    bases = mr._secret_values((DSN_NAME,))
    assert "Cd4" + "Xy9" in bases, (
        "a long piece of an unquoted password after a semicolon was not a secret"
    )
    assert "Rs2" + "Tk5" in bases, (
        "a piece of an unquoted password after an ampersand was not a secret"
    )
    assert "Pq7" in bases, "a piece of exactly PASSWORD_PIECE_MIN characters was not a secret"
    # PASSWORD_PIECE_MIN is 3: a piece of 2 characters is NOT a secret on purpose (it would hide every "Zz" and "Qw" in unrelated text). This
    # test pins that bound; a lowered minimum fails it.
    monkeypatch.setenv(
        DSN_NAME, _kv("Ab3;", "Zz;", "Qw", before="host=db.invalid", after=" user=svc")
    )
    bases = mr._secret_values((DSN_NAME,))
    assert "Zz" not in bases and "Qw" not in bases, (
        "a piece shorter than PASSWORD_PIECE_MIN characters was a secret"
    )
    out = mr._masked("E   saw Cd4Xy9 here", mr._secret_values((DSN_NAME,)))
    assert "Cd4" + "Xy9" in out, "a piece of another value was hidden"
    monkeypatch.setenv(
        DSN_NAME, _kv("ab;", "Cd4" + "Xy9", before="host=db.invalid", after=" user=svc")
    )
    assert "ab" in mr._secret_values((DSN_NAME,)), (
        "the text up to the first semicolon of an unquoted password was not a secret"
    )
    monkeypatch.setenv(
        DSN_NAME, _kv("Ab3;", "Cd4Xy9;", "Pq7", before="host=db.invalid", after=" user=svc")
    )
    out = mr._masked("E   saw Cd4Xy9 here", mr._secret_values((DSN_NAME,)))
    assert "Cd4" + "Xy9" not in out, "a piece that stands alone in a line was left readable"


def test_an_unquoted_password_with_a_semicolon_or_an_ampersand_is_masked_in_full_when_printed_alone(
    monkeypatch,
):
    for odd in (";", "&"):
        monkeypatch.setenv(
            DSN_NAME, _kv("Ab3", odd, "Xy9" + "Zq1", before="host=db.invalid", after=" user=svc")
        )
        out = mr._masked(f"E   assert 'Ab3{odd}Xy9Zq1' == 1", mr._secret_values((DSN_NAME,)))
        assert out == "E   assert '[REDACTED]' == 1", (
            f"an unquoted password with {odd!r} printed alone was not masked in one mark: {out}"
        )


def _inner_pytest(tmp_path: Path, body: str, address_before: str | None, name: str = "inner"):
    """A REAL pytest run in a folder of its own that holds a copy of ``tests/conftest.py`` and one test file (``body``), with the database address
    set to ``address_before`` (or not set). Returns ``(exit code, output)``. No pytest internals are used: the guard fixture is the one that
    pytest itself loads from the conftest, so what is checked is what a test of the suite meets."""
    folder = tmp_path / name
    folder.mkdir()
    shutil.copy(Path(__file__).with_name("conftest.py"), folder / "conftest.py")
    (folder / "test_inner.py").write_text(body, encoding="utf-8")
    (folder / "inner.ini").write_text("", encoding="utf-8")
    env = dict(os.environ)
    env.pop(DSN_NAME, None)
    if address_before is not None:
        env[DSN_NAME] = address_before
    done = subprocess.run(  # noqa: S603  # our own interpreter, fixed arguments, no shell
        [
            sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-c", str(folder / "inner.ini"),
            f"--rootdir={folder}", str(folder / "test_inner.py"),
        ],
        cwd=folder, env=env, capture_output=True, text=True, timeout=180, check=False,
    )  # fmt: skip
    return done.returncode, done.stdout + done.stderr


def _two_inner_tests(marker: Path, first_body: str) -> str:
    """A test file of two tests: the first runs ``first_body``; the second (it runs after the first, in the same process) writes what the
    database address then is into ``marker`` (``None`` when it is not set)."""
    return (
        "import os\n\n\ndef test_first():\n"
        + "".join(f"    {line}\n" for line in first_body.splitlines())
        + "\n\ndef test_second():\n"
        + f"    open({str(marker)!r}, 'w').write(repr(os.environ.get('HADAVIN_TEST_PG_DSN')))\n"
    )


def test_the_fixture_that_guards_the_database_address_fails_a_test_that_changes_it(tmp_path):
    marker = tmp_path / "after.txt"
    body = _two_inner_tests(marker, "os.environ['HADAVIN_TEST_PG_DSN'] = 'changed by a test'")
    code, out = _inner_pytest(tmp_path, body, "the address before")
    assert code != 0 and "did not put it back" in out, (
        f"the fixture did not fail a test that changed the database address (exit {code})"
    )
    assert marker.read_text(encoding="utf-8") == repr("the address before"), (
        "the fixture did not put the old value back"
    )
    quiet = _two_inner_tests(tmp_path / "quiet.txt", "pass")
    code, out = _inner_pytest(tmp_path, quiet, "the address before", name="quiet")
    assert code == 0, f"the fixture failed a test that changed nothing: {out[-300:]}"


def test_the_fixture_that_guards_the_database_address_removes_an_address_that_a_test_added(
    tmp_path,
):
    marker = tmp_path / "after.txt"
    body = _two_inner_tests(marker, "os.environ['HADAVIN_TEST_PG_DSN'] = 'added by a test'")
    code, out = _inner_pytest(tmp_path, body, None)
    assert code != 0 and "did not put it back" in out, (
        "the fixture did not fail a test that added the database address"
    )
    assert marker.read_text(encoding="utf-8") == "None", (
        "the fixture did not remove an address that a test added"
    )


def test_a_plus_in_a_url_password_is_also_read_as_a_space(monkeypatch):
    value = _url("svc", "Open+", "Sesame9")
    monkeypatch.setenv(DSN_NAME, value)
    secrets = mr._secret_values((DSN_NAME,))
    assert "Open Sesame9" in secrets, "the plus-as-space form of the password was not a secret"
    assert "Sesame9" not in mr._masked("E   password Open Sesame9 wrong", secrets)
    # a percent code beside a plus: the plain percent rule keeps the plus, the form rule turns it into a space; both are secrets
    value = _url("svc", "Open+", "Sesame%219")
    monkeypatch.setenv(DSN_NAME, value)
    secrets = mr._secret_values((DSN_NAME,))
    assert "Open+Sesame!9" in secrets, "the percent-decoded form with a plus kept was not a secret"
    assert "Open S" + "esame!9" in secrets


def test_a_lock_file_that_is_a_fifo_is_refused_and_does_not_hang(tmp_path, monkeypatch):
    if not hasattr(os, "mkfifo"):
        pytest.skip("this system has no named pipes")
    path = tmp_path / _lock_name("unparsed")  # "fifo" is no address
    os.mkfifo(path, 0o600)
    result: dict[str, object] = {}

    def attempt():
        result["exc"] = _refusal("fifo")

    worker = threading.Thread(target=attempt, daemon=True)
    worker.start()
    worker.join(30)
    hung = worker.is_alive()
    if hung:  # free the blocked open so the test run itself does not hang
        release = os.open(path, os.O_WRONLY | getattr(os, "O_NONBLOCK", 0))
        os.close(release)
        worker.join(30)
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
    worker.join(30)
    hung = worker.is_alive()
    if hung:
        release = os.open(junit, os.O_WRONLY | getattr(os, "O_NONBLOCK", 0))
        os.close(release)
        worker.join(30)
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
    monkeypatch.setattr(Path, "read_bytes", never)
    monkeypatch.setattr(Path, "open", never)
    real_read = os.read

    def read_never_the_file(fd, n):
        if os.fstat(fd).st_size == junit.stat().st_size:
            raise AssertionError("the file was read before its size was looked at")
        return real_read(fd, n)

    monkeypatch.setattr(os, "read", read_never_the_file)
    with pytest.raises(ValueError, match="over the ceiling"):
        mr._junit_text(junit)


# ---- round 13: messages of collection and fixture errors, re-encoded passwords, password words, the lock name, ellipsis, limits --------------

COLLECTION_SHOWS_VALUE = (
    "import os\nfrom pk.core import go\n\n"
    f"assert go(True) is True, os.environ[{DSN_NAME!r}]\n\n"
    "def test_a():\n    assert True\n"
)
FIXTURE_SHOWS_VALUE = (
    "import os\nimport pytest\nfrom pk.core import go\n\n"
    f"@pytest.fixture\ndef checked():\n    assert go(True) is True, os.environ[{DSN_NAME!r}]\n    return 1\n\n"
    "def test_a(checked):\n    assert checked == 1\n"
)


def _the_first_line_of_a_failing_run(tmp_path, monkeypatch, body, masking_off=False):
    """Run the flip on ``body`` with the secret address passed; the row (name, verdict, label, good) and the first line kept for the row."""
    dsn, _word = _secret_dsn()
    monkeypatch.setenv(DSN_NAME, dsn)
    root = _tree(tmp_path, {CORE_TEST: body})
    lines: dict[str, str] = {}
    with monkeypatch.context() as control:
        if masking_off:
            _protection_off(control)
        rows = _run(root, [FLIP], pass_env=(DSN_NAME,), first_lines=lines)
    return rows, lines.get("flip", "")


def test_the_message_of_a_collection_error_never_holds_the_passed_value(tmp_path, monkeypatch):
    dsn, word = _secret_dsn()
    rows, seen = _the_first_line_of_a_failing_run(
        tmp_path / "a", monkeypatch, COLLECTION_SHOWS_VALUE, masking_off=True
    )
    assert rows == [("flip", Verdict.ERROR, "COLLECTION ERROR", False)] and word in seen, (
        f"the positive control failed: with the masking off the collection error shows no password: {rows}"
    )
    rows, line = _the_first_line_of_a_failing_run(
        tmp_path / "b", monkeypatch, COLLECTION_SHOWS_VALUE
    )
    assert rows == [("flip", Verdict.ERROR, "COLLECTION ERROR", False)], (
        f"the collection error was not a COLLECTION ERROR row: {rows}"
    )
    assert word not in line and dsn not in line, (
        "the passed value reached the first line of a COLLECTION ERROR row"
    )
    assert line == "AssertionError", (
        f"the COLLECTION ERROR line is not the class name alone: {line!r}"
    )


def test_the_message_of_a_fixture_error_never_holds_the_passed_value(tmp_path, monkeypatch):
    dsn, word = _secret_dsn()
    rows, seen = _the_first_line_of_a_failing_run(
        tmp_path / "a", monkeypatch, FIXTURE_SHOWS_VALUE, masking_off=True
    )
    assert rows == [("flip", Verdict.ERROR, "FIXTURE ERROR", False)] and word in seen, (
        f"the positive control failed: with the masking off the fixture error shows no password: {rows}"
    )
    rows, line = _the_first_line_of_a_failing_run(tmp_path / "b", monkeypatch, FIXTURE_SHOWS_VALUE)
    assert rows == [("flip", Verdict.ERROR, "FIXTURE ERROR", False)], (
        f"the fixture error was not a FIXTURE ERROR row: {rows}"
    )
    assert word not in line and dsn not in line, (
        "the passed value reached the first line of a FIXTURE ERROR row"
    )
    assert line == "AssertionError", f"the FIXTURE ERROR line is not the class name alone: {line!r}"


def test_the_canary_skip_message_never_holds_the_passed_value(tmp_path, monkeypatch):
    dsn, word = _secret_dsn()
    monkeypatch.setenv(DSN_NAME, dsn)
    state = tmp_path / "state.flag"
    body = (
        "import pytest\nfrom pathlib import Path\nfrom pk.core import go\n\n"
        f"@pytest.mark.parametrize('v', [{dsn!r}])\n"
        f"def test_a(v):\n    state = Path({str(state)!r})\n    if state.exists():\n        pytest.skip('no database')\n"
        "    if go(True) is not True:\n        state.write_text('x')\n    assert go(True) is True\n"
    )
    root = _tree(tmp_path, {CORE_TEST: body})

    def refusal_of_the_canary() -> str:
        state.unlink(missing_ok=True)
        try:
            _run(root, [FLIP], pass_env=(DSN_NAME,), forbid_skips=True)
        except mr.CanaryFailed as exc:
            return str(exc)
        return ""

    with (
        monkeypatch.context() as control
    ):  # positive control: with the masking off, the test id of the skip holds the value
        _protection_off(control)
        assert word in refusal_of_the_canary(), (
            "the positive control failed: the unmasked canary skip message holds no password"
        )
    text = refusal_of_the_canary()
    assert "skipped" in text, f"the canary skip was not refused: {text!r}"
    assert word not in text and dsn not in text, "the canary skip message held the passed value"
    assert mr.PARAMETERS_HIDDEN in text, (
        f"the canary skip message did not hide the parameters of the test id: {text!r}"
    )


def test_the_re_encoded_forms_of_a_url_password_are_secrets(monkeypatch):
    # the URL writes the password as "Open%20" + "Sesame/9"; a test or a library may print it decoded, or encode it again in another way
    monkeypatch.setenv(DSN_NAME, _url("svc", "Open%20", "Sesame/9"))
    secrets = mr._secret_values((DSN_NAME,))
    for form, why in (
        ("Open%20" + "Sesame/9", "the password as the URL has it was not a secret"),
        ("Open S" + "esame/9", "the decoded password was not a secret"),
        ("Open%20Sesame%2F9", "the password encoded with quote(safe='') was not a secret"),
        ("Open%20Sesame%2f9", "the lower-case hex form of quote(safe='') was not a secret"),
        ("Open+Sesame%2F9", "the quote_plus form was not a secret"),
        ("Open+Sesame%2f9", "the lower-case hex form of the quote_plus form was not a secret"),
    ):
        assert form in secrets, f"{why}: {sorted(secrets)}"
    out = mr._masked("E   saw Open+Sesame%2f9 and Open%20Sesame%2F9 here", secrets)
    assert out == "E   saw [REDACTED] and [REDACTED] here", f"a re-encoded form survived: {out}"
    # a URL that wrote the slash as %2F: quote() with its default (the slash kept) writes the password another way
    monkeypatch.setenv(DSN_NAME, _url("svc", "Open%20", "Sesame%2F9"))
    assert "Open%20" + "Sesame/9" in mr._secret_values((DSN_NAME,)), (
        "the form of quote() that keeps the slash was not a secret"
    )


def test_a_password_that_was_encoded_twice_or_more_is_decoded_until_it_stops_changing(monkeypatch):
    monkeypatch.setenv(DSN_NAME, _url("svc", "Ab3%25", "40Xy9"))
    secrets = mr._secret_values((DSN_NAME,))
    assert "Ab3%" + "40Xy9" in secrets and "Ab3" + "@Xy9" in secrets, (
        f"a password encoded twice was not read at both depths: {sorted(secrets)}"
    )
    monkeypatch.setenv(DSN_NAME, _url("svc", "Ab3%25", "2540Xy9"))
    assert "Ab3" + "@Xy9" in mr._secret_values((DSN_NAME,)), (
        "a password encoded three times was not decoded to the end"
    )
    # the refusal is checked at each depth: the third step of this one is a quote mark
    monkeypatch.setenv(DSN_NAME, _url("svc", "Ab3%25", "2527Xy9"))
    text = _refusal_text(
        "a password that decodes to a quote mark at the third depth was not refused"
    )
    assert "percent-decoded" in text and "Ab3" not in text and "Xy9" not in text, (
        f"the refusal at the third depth names the secret or the wrong text: {text}"
    )
    monkeypatch.setenv(DSN_NAME, _url("svc", "Ab3%25", "252527Xy9"))
    _refusal_text("a password that decodes to a quote mark at the fourth depth was not refused")


def test_a_password_word_inside_a_longer_word_and_in_any_case_is_read(monkeypatch):
    for key, why in (
        ("ssl" + _PW_KEY, "the password after sslpassword= was not a secret"),
        ("db" + _PW_KEY, "the password after dbpassword= was not a secret"),
        ("PG" + _PW_KEY.upper(), "the password after PGPASSWORD= was not a secret"),
        (_PW_KEY.capitalize(), "the password after Password= was not a secret"),
    ):
        assert _HK in _secrets_of(_kv(_HK, key=key), monkeypatch), why


def _lock_file_name(tmp_path, monkeypatch, value) -> str:
    folder = tmp_path / f"folder{len(list(tmp_path.iterdir()))}"
    folder.mkdir()
    folder.chmod(0o700)  # the lock folder must be closed to group and others
    monkeypatch.setattr(mr, "_lock_dir", lambda: folder)
    with mr._one_run_per_database([value]):
        pass
    (only,) = list(folder.iterdir())
    return only.name


def test_the_lock_file_name_does_not_depend_on_the_password(tmp_path, monkeypatch):
    first = _url("svc", "Zq9x", "K4mTw", rest="db.invalid/scratch")
    second = _url("svc", "Pw3t", "Hb8Nc", rest="db.invalid/scratch")
    name = _lock_file_name(tmp_path, monkeypatch, first)
    assert name == _lock_file_name(tmp_path, monkeypatch, second), (
        "two addresses that differ only in the password got two lock file names"
    )
    assert name != _lock_file_name(
        tmp_path, monkeypatch, _url("svc", "Zq9x", "K4mTw", rest="other.invalid/scratch")
    ), "two addresses with another host got one lock file name"
    # key=value addresses that differ only in an option that is no part of the address (the user, an ssl mode) share one name, and it is a real name
    one = _lock_file_name(tmp_path, monkeypatch, "host=db.invalid dbname=scratch user=alice")
    assert one == _lock_file_name(
        tmp_path, monkeypatch, "host=db.invalid dbname=scratch user=bob sslmode=require"
    ), "two key=value addresses that differ only in options got two lock file names"
    assert one != _lock_file_name(tmp_path, monkeypatch, "unparsed-value"), (
        "a key=value address got the name of the values outside the grammar"
    )
    # a key=value address that holds a password word is outside the grammar and shares the name "unparsed" with every such value, on purpose
    kv_one = _kv(_HK, key="ssl" + _PW_KEY)
    kv_two = _kv("Rt5Vb", "9LmQw", key="ssl" + _PW_KEY)
    assert (
        _lock_file_name(tmp_path, monkeypatch, kv_one)
        == _lock_file_name(tmp_path, monkeypatch, kv_two)
        == _lock_file_name(tmp_path, monkeypatch, "unparsed-value")
    ), (
        "a key=value address with a password word did not get the name of the values outside the grammar"
    )
    # the name is not the hash of the whole address, whatever password is tried (no offline guess)
    guesses = {
        f"hadavin_mutation_{hashlib.sha256(_url('svc', p, rest='db.invalid/scratch').encode()).hexdigest()[:16]}.lock"
        for p in ("Zq9x" + "K4mTw", "Pw3t" + "Hb8Nc")
    }
    assert name not in guesses, (
        "the lock file name is the hash of a whole address with a password in it"
    )
    # same host, other port or database: another name; a value that is no address: one shared name
    assert name != _lock_file_name(
        tmp_path, monkeypatch, _url("svc", "Zq9x", rest="db.invalid:6543/scratch")
    ), "two addresses with another port got one lock file name"
    assert name != _lock_file_name(
        tmp_path, monkeypatch, _url("svc", "Zq9x", rest="db.invalid/other")
    ), "two addresses with another database got one lock file name"
    assert _lock_file_name(tmp_path, monkeypatch, "not an address") == _lock_file_name(
        tmp_path, monkeypatch, "another text"
    ), "two values that are no address got two names (the secret-free fallback must be one name)"
    assert _lock_file_name(tmp_path, monkeypatch, "host=/run/pg dbname=one") != _lock_file_name(
        tmp_path, monkeypatch, "host=/run/pg dbname=two"
    ), "two databases behind one unix socket folder got one lock file name"


def test_a_piece_beside_a_unicode_ellipsis_is_masked_like_one_beside_three_dots():
    secret = "Zq9xK2mP" + "7wRt4vNb8LcY3"  # built from parts
    for dots in ("\u2026", "..."):
        out = mr._masked(f"E   x == '{secret[:8]}{dots}{secret[-8:]}' y", (secret,))
        assert out == f"E   x == '[REDACTED]{dots}[REDACTED]' y", (
            f"a piece beside the ellipsis {dots!r} was not masked: {out}"
        )


def test_the_scan_gives_the_unicode_ellipsis_the_width_of_one_character():
    secret = "Zq9xK2mP" + "7wRt4vNb8LcY3"  # built from parts
    text = f"E   x == '{secret[:8]}\u2026{secret[-8:]}'"
    spans = mr._fragment_spans(text, secret, list(mr._DOTS.finditer(text)))
    assert spans == [
        (len("E   x == '"), len("E   x == '") + 8),
        (len("E   x == '") + 9, len("E   x == '") + 17),
    ], f"the one-character ellipsis was given the width of three dots: {spans}"


def test_a_host_with_a_port_is_not_read_as_a_url_login_and_a_numeric_password_still_is(monkeypatch):
    def secrets_or_say(value, why):
        try:
            return _secrets_of(value, monkeypatch)
        except ValueError:
            raise AssertionError(why) from None

    for ending in (
        "/app?",
        "?",
        "#",
    ):  # the port may be followed by a path, a question mark or a hash
        value = f"postgresql://db.invalid:5432{ending}application_name=caf%C3%A9"
        assert secrets_or_say(value, "a non-ASCII option after a port refused the run") == (
            value,
        ), "a port without a login was read as the start of a password"
    value = "postgresql://db.invalid:5432/app?application_name=caf%C3%A9&x=a@b"
    got = secrets_or_say(value, "a non-ASCII option beside an @ refused the run")
    assert value in got, "the whole value was not a secret"
    assert not any("é" in s_ for s_ in got), "a text that is only part of an option was decoded"
    assert "12" + "345" in _secrets_of(_url("svc", "12", "345"), monkeypatch), (
        "a password of digits only was not a secret"
    )
    # the text between the first colon and an @ is a secret too, also when it starts like a port and holds a slash
    assert "12/45" in _secrets_of(_url("svc", "12", "/45"), monkeypatch), (
        "a password of digits then a slash was not found"
    )


def test_a_value_longer_than_the_ceiling_is_refused_without_showing_it(monkeypatch):
    monkeypatch.setenv(DSN_NAME, "ab" * (mr.MAX_VALUE_CHARS // 2))
    try:
        secrets = mr._secret_values((DSN_NAME,))
    except ValueError:
        raise AssertionError("a value of exactly MAX_VALUE_CHARS characters was refused") from None
    assert secrets == ("ab" * (mr.MAX_VALUE_CHARS // 2),), "a value at the ceiling was changed"
    monkeypatch.setenv(DSN_NAME, "ab" * (mr.MAX_VALUE_CHARS // 2) + "c")
    text = _refusal_text("a value of MAX_VALUE_CHARS + 1 characters was not refused")
    assert DSN_NAME in text and "ababab" not in text, (
        f"the refusal of a long value names no variable or shows the value: {text[:200]}"
    )


# ---- round 14: the lock name comes from a strict grammar, never from parsed text ----

_ADDRESS_CASES = [
    # (value, what the lock hashes: host, host address, port, database name, one per line)
    ("postgresql://svc:" + "Zq9x" + "@Db.Invalid:5432/app", "db.invalid\n\n5432\napp"),
    ("postgresql://db.invalid:5432/app", "db.invalid\n\n5432\napp"),
    ("postgres://[::1]:5/x", "::1\n\n5\nx"),
    ("host=::1 port=5 dbname=x", "::1\n\n5\nx"),
    ("host=Db.Invalid port=5432 dbname=app user=svc", "db.invalid\n\n5432\napp"),
    ("hostaddr=10.0.0.1 dbname=app", "\n10.0.0.1\n\napp"),
    ("host=db1 dbname=t sslmode=disable connect_timeout=3", "db1\n\n\nt"),
    # a unix socket folder is read the same way as by the address check: two databases behind one folder get two names
    ("host=/run/pg dbname=x", "/run/pg\n\n\nx"),
    ("host=/run/pg dbname=y", "/run/pg\n\n\ny"),
    ("host=/run/pg port=5433 dbname=x", "/run/pg\n\n5433\nx"),
    ("host=/Run/pg dbname=x", "/Run/pg\n\n\nx"),
    (
        "user=svc",
        "\n\n\n",
    ),  # inside the grammar, no address part (the address check refuses it: no host)
    # everything below is outside the grammar and shares one name
    ("postgresql://u@h/db?host=other", "unparsed"),
    ("postgresql://u@h/db#frag", "unparsed"),
    ("postgresql://u@h/db;x=1", "unparsed"),
    ("postgresql://u@h/db/more", "unparsed"),
    ("postgresql://u@h/db with space", "unparsed"),
    ("postgresql:///db?host=/tmp", "unparsed"),
    ("mysql://u@h/db", "unparsed"),
    ("postgresql://u@h:port/db", "unparsed"),
    ("postgresql://u@[::1/db", "unparsed"),
    (_url("svc", "12", "/", "45"), "unparsed"),
    (_url("u", "a", rest="b/c@h/db"), "unparsed"),
    ("postgresql://u:" + "Zq9x" + "@K4mTw@h/db", "unparsed"),
    ("Zq9x" + "K4mTw" + "://K4mTw", "unparsed"),
    ("host='a b' dbname=x", "unparsed"),
    ("host=db1  port=1", "unparsed"),
    (" host=db1", "unparsed"),
    ("host=db1 " + "pass" + "word=aaa dbname=t", "unparsed"),
    ("host=db1 dbname=t " + "pass" + "word=aaa sslrootcert=file:///ca.pem", "unparsed"),
    ("host=db1 ssl" + "pass" + "word=aaa", "unparsed"),
    ("host=db1 p" + "wd=aaa dbname=t", "unparsed"),
    ("host=db1 pass" + "wd=aaa dbname=t", "unparsed"),
    ("host=db1 PASS" + "WORD=aaa dbname=t", "unparsed"),
    ("host=db1 P" + "wD=aaa", "unparsed"),
    ("host=[::1] dbname=x", "unparsed"),  # brackets belong to the URL form only
    ("host=/run/../etc dbname=x", "unparsed"),
    ("host=db1 host=db2", "unparsed"),  # a key twice
    ("host=db1 user=a user=b", "unparsed"),
    ("host=db1 dbname=t sslrootcert=file:///ca.pem", "unparsed"),  # a key that is not allowed
    ("host=db1 application_name=x", "unparsed"),
    ("port=abc host=h", "unparsed"),
    ("host=g:h dbname=x", "unparsed"),
    ("host=h dbname=a:b", "unparsed"),
    ("host=h hostaddr=a/b", "unparsed"),
    ("some-file.flag", "unparsed"),
]


def test_the_lock_name_input_is_exactly_the_allowed_parts_or_unparsed():
    for index, (value, expected) in enumerate(_ADDRESS_CASES):
        assert mr._address_parts(value) == expected, (
            f"a lock name input was not the expected one (row {index} of the table)"
        )


def test_one_spelling_in_url_and_key_value_form_gives_one_name():
    assert mr._address_parts("postgresql://svc:" + "Zq9x" + "@db.invalid:5432/app") == (
        mr._address_parts("host=db.invalid port=5432 dbname=app")
    ), "the same database written as a URL and as key=value got two names"


def test_the_same_database_written_two_ways_gets_two_names_as_the_docstring_says():
    ways = [
        "postgresql://u@localhost/app",
        "postgresql://u@127.0.0.1/app",
        "postgresql://u@localhost:5432/app",
        "host=localhost dbname=app",
        "hostaddr=127.0.0.1 dbname=app",
    ]
    # the first and the fourth are one spelling (host, no port, same database) and so rightly share a name; the other three are three more
    assert len({mr._address_parts(w) for w in ways}) == 4, (
        "two spellings of one database got one name: the docstring says they get two"
    )
    for text in (mr._address_parts, mr._one_run_per_database):
        doc = (text.__doc__ or "").lower()
        assert "match on spelling" in doc, (
            "the docstring does not say that the match is on spelling"
        )


_HOSTILE = "/?#;&@:% =.-_~+!$*,"
_CALM = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.~-;&:%+!$*,="
_PW_FORMS = [
    lambda p: f"postgresql://svc:{p}@db.invalid:5432/app",
    lambda p: f"postgresql://svc:{p}@db.invalid/app",
    lambda p: f"postgres://svc:{p}@[::1]:5/app",
    lambda p: f"postgresql://db.invalid/app?{_PW_KEY}={p}",
    lambda p: f"postgresql://svc@db.invalid/app;{_PW_KEY}={p}",
    lambda p: f"host=db.invalid dbname=app {_PW_KEY}={p}",
    lambda p: f"host=db.invalid {_PW_KEY}={p} dbname=app sslrootcert=file:///ca.pem",
    lambda p: f"host=db.invalid {_PW_KEY}='{p}' port=5432",
    lambda p: f"host=db.invalid dbname=app pwd={p}",
]


def test_property_the_lock_name_holds_no_byte_of_a_password_and_calm_passwords_give_one_name():
    rng = _Det(1414)
    letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    pieces = [
        "host=", "dbname=", "port=", "://", "@", "/", "?", "#", ";", "&", ":", "%", " ",
        " host=", " dbname=", " port=", " hostaddr=",
    ]  # fmt: skip  # the ones with a space in front are a password that poses as the next option

    def password(alphabet: str, with_pieces: bool) -> str:
        out = "".join(rng.choice(letters) for _ in range(3))
        for _ in range(rng.randint(1, 6)):
            part = (
                rng.choice(pieces)
                if with_pieces and rng.randint(0, 9) < 7
                else rng.choice(alphabet)
            )
            out += part + "".join(rng.choice(letters) for _ in range(rng.randint(1, 3)))
        return out

    ran = url_pairs = hostile_parsed = hostile_unparsed = 0
    for _ in range(120):
        for number, make in enumerate(_PW_FORMS):
            hostile, calm_a, calm_b = (
                password(_HOSTILE, True),
                password(_CALM, False),
                password(_CALM, False),
            )
            skeleton = make("")
            for text in (hostile, calm_a, calm_b):
                name = mr._address_parts(make(text))
                ran += 1
                if (
                    text is hostile and number < 3
                ):  # the forms whose outcome depends on the password
                    hostile_parsed += name != "unparsed"
                    hostile_unparsed += name == "unparsed"
                for t in (text, *text.replace("'", "").split()):
                    if len(t) >= 3 and t not in skeleton:
                        assert t not in name, (
                            "a password text is inside the text that the lock hashes"
                        )
                # a password of any shape gives the name of a calm one or "unparsed", nothing else
                assert name in {mr._address_parts(make("Calm" + "9")), "unparsed"}, (
                    "a password changed the name to something that is neither"
                )
            if calm_a != calm_b and number < 3:
                # only the three URL forms with a password in the login give a name for a calm password; the other forms are always "unparsed"
                url_pairs += 1
                assert mr._address_parts(make(calm_a)) == mr._address_parts(make(calm_b)), (
                    "two values that differ only in a calm password got two lock names"
                )
    assert ran >= 3000 and url_pairs >= 300, (
        f"the property test ran only {ran} cases ({url_pairs} pairs of calm passwords in a URL login)"
    )
    assert hostile_parsed >= 20 and hostile_unparsed >= 20, (
        "the property test did not cover both outcomes for a hostile password in a URL login "
        f"(parsed {hostile_parsed}, unparsed {hostile_unparsed})"
    )


def test_the_two_values_the_review_found_no_longer_leak_into_the_lock_name():
    for first, second in (
        (
            "host=db1 dbname=t " + "pass" + "word=aaa sslrootcert=file:///ca.pem",
            "host=db1 dbname=t " + "pass" + "word=bbb sslrootcert=file:///ca.pem",
        ),
        (_url("svc", "12", "/", "45"), _url("svc", "12", "/", "99")),
    ):
        assert mr._address_parts(first) == mr._address_parts(second), (
            "a password reached the lock name"
        )


def test_a_url_password_that_starts_like_a_port_and_holds_a_slash_is_a_secret(monkeypatch):
    got = _secrets_of(_url("svc", "12", "/", "45"), monkeypatch)
    assert "12/45" in got, "the password 12/45 was not found"


def test_an_option_with_a_non_ascii_text_beside_a_password_does_not_refuse_the_run(monkeypatch):
    pw = "Pw" + "9zQ"
    value = f"postgresql://db.invalid/app?{_PW_KEY}={pw}&application_name=caf%C3%A9"
    got = _secrets_of(value, monkeypatch)
    assert pw in got and value in got, "the password was not a secret"
    assert not any("é" in s_ for s_ in got), "an option was decoded as if it were the password"


def test_the_text_after_a_password_word_and_a_space_is_not_decoded_as_a_password(monkeypatch):
    value = f"host=h {_PW_KEY}= dbname=x%27"
    try:
        got = _secrets_of(value, monkeypatch)
    except ValueError:
        raise AssertionError("the text after the space was decoded as a password") from None
    assert "dbname=x%27" in got, "the text after the space was not hidden as written"
    assert not any("'" in s_ for s_ in got), "the text after the space was decoded as a password"


def test_a_plus_that_comes_from_a_percent_code_is_read_as_a_space_on_the_next_step(monkeypatch):
    got = _secrets_of(_url("svc", "Ab3%2B", "Cd4"), monkeypatch)
    assert "Ab3" + " Cd4" in got and "Ab3" + "+Cd4" in got, (
        "a plus from a percent code was not read as a space"
    )


def test_many_repeats_of_one_option_are_few_secrets_and_fast(monkeypatch):
    value = "host=h dbname=d " + ("p" + "wd=a&") * 330
    began = time.monotonic()
    try:
        got = _secrets_of(value, monkeypatch)
    except ValueError:
        raise AssertionError("a repeated option was refused as too many texts") from None
    spent = time.monotonic() - began
    assert len(got) < 20, f"{len(got)} secrets for a repeated option"
    # the count above is the exact check; this bound only catches a run that takes minutes, so a slow machine does not fail it
    assert spent < 60, f"a repeated option took {spent:.1f} s"
    assert mr._masked("x " + ("p" + "wd=a&") * 5, got).count(mr.MASK) >= 1, (
        "the repeated text was not hidden"
    )


def test_a_password_in_many_encoded_layers_is_refused_fast_without_showing_it(monkeypatch):
    value = "postgresql://svc:" + "%" + "25" * 900 + "@db.invalid/app"
    monkeypatch.setenv(DSN_NAME, value)
    began = time.monotonic()
    caught = None
    try:
        mr._secret_values((DSN_NAME,))
    except ValueError as exc:
        caught = exc
    assert caught is not None and "more than" in str(caught), (
        "a value with hundreds of layers was accepted"
    )
    assert "2525" not in str(caught), "the refusal shows the value"
    # the refusal above is the exact check (it comes from a count); this bound only catches minutes
    assert time.monotonic() - began < 60, "the refusal took more than 60 s"


def test_a_line_with_many_dots_and_many_secrets_is_replaced_not_scanned():
    secrets = tuple(f"Ab{i:03d}Cd{i:03d}Ef" for i in range(100))
    line = "x " + "... " * 900
    began = time.monotonic()
    out = mr._masked(line, secrets)
    assert out.startswith(mr.MASK) and "too many" in out, f"the line was scanned: {out[:60]}"
    # the marker above is the exact check (the line was not scanned); this bound only catches minutes
    assert time.monotonic() - began < 60, "the capped line took more than 60 s"
    assert mr._masked("x ... y " + secrets[0], secrets) == "x ... y " + mr.MASK, (
        "a normal line with a secret was changed wrongly"
    )


def test_a_one_character_secret_hides_every_such_character_as_the_docstring_says():
    assert mr._masked("a banana", ("a",)) == f"{mr.MASK} b{mr.MASK}n{mr.MASK}n{mr.MASK}", (
        "a one-character secret did not hide every such character"
    )


def test_the_no_access_message_is_one_text_for_both_error_codes():
    assert mr._why_not_opened(errno.EACCES) == mr._why_not_opened(errno.EPERM) == mr._NO_ACCESS, (
        "the two permission codes have two messages, or not the no-access text"
    )


def test_first_lines_given_with_a_stale_entry_is_emptied_at_the_start(tmp_path):
    root = _tree(tmp_path, {CORE_TEST: USES_GO})
    seen = {"flip": "a stale line of an earlier run", "other": "x"}
    _run(root, [FLIP], first_lines=seen)
    assert "other" not in seen and seen.get("flip") != "a stale line of an earlier run", (
        "first_lines kept an entry of an earlier run"
    )


# ---- round 18: a passed address implies forbid_skips -------------------------------------------------------------------------


ALWAYS_SKIPS = "import pytest\n\ndef test_a():\n    pytest.skip('no database')\n"


def test_a_passed_address_implies_forbid_skips_and_an_explicit_false_turns_it_off(
    tmp_path, monkeypatch
):
    monkeypatch.setenv(DSN_NAME, f"host={FAKE_HOST} dbname=scratch")
    root = _tree(tmp_path, {CORE_TEST: ALWAYS_SKIPS})
    _must_raise(
        "a passed address did not imply forbid_skips",
        RuntimeError,
        _run,
        root,
        [FLIP],
        pass_env=(DSN_NAME,),
        match="skipped",
    )
    assert _short(_run(root, [FLIP], pass_env=(DSN_NAME,), forbid_skips=False)) == [
        ("flip", Verdict.SURVIVED, False)
    ]
    assert _short(_run(root, [FLIP])) == [("flip", Verdict.SURVIVED, False)], (
        "no passed name: skips stay allowed"
    )


def test_a_listed_name_whose_variable_is_absent_still_refuses_a_baseline_that_skips(
    tmp_path, monkeypatch
):
    # the skip check is switched on by LISTING the name in pass_env: tests that skip because no address is there prove nothing
    monkeypatch.delenv(DSN_NAME)
    root = _tree(tmp_path, {CORE_TEST: ALWAYS_SKIPS})
    _must_raise(
        "a listed name whose variable is absent did not switch the skip check on",
        RuntimeError,
        _run,
        root,
        [FLIP],
        pass_env=(DSN_NAME,),
        match="skipped",
    )


# ---- round 18: rows, labels and the baseline message -----------------------------------------------------------------------


def test_an_unreadable_junit_file_is_that_mutants_error_row_and_the_run_goes_on(
    tmp_path, monkeypatch
):
    root = _tree(tmp_path, {CORE_TEST: USES_GO})
    real = mr._junit_text

    def unreadable(junit):
        if junit.name == "r.xml":
            raise PermissionError(errno.EACCES, "denied")
        return real(junit)

    monkeypatch.setattr(mr, "_junit_text", unreadable)
    other = Mutant("second", "src/pk/core.py", "return flag", "return not flag", "assert")
    rows = _run(root, [FLIP, other])
    assert [(r[0], r[1], r[2], r[3]) for r in rows] == [
        ("flip", Verdict.ERROR, "JUNIT REFUSED", False),
        ("second", Verdict.ERROR, "JUNIT REFUSED", False),
    ]


def test_an_error_row_with_no_failing_test_names_the_exit_code_unless_it_is_one(tmp_path):
    lines: dict[str, str] = {}
    none = tmp_path / "none.xml"
    for rc, label in (
        (1, "NO FAILING TEST NAMED"),
        (2, "EXIT CODE 2"),
        (3, "EXIT CODE 3"),
        (4, "EXIT CODE 4"),
        (-9, "EXIT CODE -9"),
    ):
        row = mr._row(FLIP, rc, none, False, mr._Shown(), lines)
        assert row == ("flip", Verdict.ERROR, label, False), (
            f"the row of exit code {rc} did not name it: {row}"
        )
    none_shown = mr._Shown()
    assert mr._row(FLIP, 0, none, False, none_shown, lines) == ("flip", Verdict.SURVIVED, "", False)
    assert mr._row(FLIP, 5, none, False, none_shown, lines) == ("flip", Verdict.NO_TESTS, "", False)


def test_first_lines_has_an_entry_only_for_a_row_that_has_a_first_error_line(tmp_path):
    lines: dict[str, str] = {}
    mr._row(FLIP, 2, tmp_path / "none.xml", False, mr._Shown(), lines)
    assert lines == {}, f"a row with no first E line got an entry: {lines}"
    xml = tmp_path / "r.xml"
    xml.write_text(
        '<testsuites><testsuite><testcase classname="tests.test_core" name="test_a"><failure message="m">E   AssertionError: boom</failure></testcase></testsuite></testsuites>',
        encoding="utf-8",
    )
    mr._row(FLIP, 1, xml, False, mr._Shown(), lines)
    assert lines == {"flip": "E   AssertionError: boom"}, lines


def test_a_failed_baseline_with_a_passed_value_says_how_it_ended_and_names_only_the_class(
    tmp_path, monkeypatch
):
    dsn = f"host={FAKE_HOST} dbname=scratch_" + "Zq9xK4mTw"
    monkeypatch.setenv(DSN_NAME, dsn)
    body = (
        "import os\n\ndef test_a():\n"
        f"    assert False, 'the database is unreachable: ' + os.environ[{DSN_NAME!r}]\n"
    )
    root = _tree(tmp_path, {CORE_TEST: body})
    with pytest.raises(RuntimeError) as caught:
        _run(root, [FLIP], pass_env=(DSN_NAME,))
    text = str(caught.value)
    assert "exit code 1" in text, text
    assert text.endswith("(exit code 1): AssertionError"), (
        f"not the run end and the class name alone: {text}"
    )
    assert "unreachable" not in text, f"a line of the child's text is in the message: {text}"
    assert "Zq9xK4mTw" not in text and "scratch_" not in text, (
        f"the passed value is in the message: {text}"
    )


def test_a_failed_baseline_with_no_passed_value_shows_the_first_line(tmp_path, monkeypatch):
    monkeypatch.delenv(DSN_NAME, raising=False)
    root = _tree(tmp_path, {CORE_TEST: "def test_a():\n    assert False, 'the plain reason'\n"})
    with pytest.raises(RuntimeError, match="exit code 1.*the plain reason"):
        _run(root, [FLIP])


def test_a_baseline_that_times_out_says_so(tmp_path, monkeypatch):
    monkeypatch.delenv(DSN_NAME, raising=False)
    root = _tree(tmp_path, {CORE_TEST: "import time\n\ndef test_a():\n    time.sleep(30)\n"})
    with pytest.raises(RuntimeError, match="timed out"):
        _run(root, [FLIP], baseline_timeout=1)


# ---- round 18: judge_report (the shared path of the fixture and collection rule) ---------------------------------------------


def _junit(
    tag: str, message: str, line: str, classname: str = "tests.test_a", name: str = "test_x"
) -> str:
    return (
        f'<testsuites><testsuite><testcase classname="{classname}" name="{name}">'
        f'<{tag} message="{message}">{line}</{tag}></testcase></testsuite></testsuites>'
    )


def test_judge_report_never_counts_a_fixture_or_collection_error_as_a_kill_and_judge_alone_would():
    from hadavin_sdk.testing.mutation import judge_report

    fixture = read_junit(_junit("error", "failed on setup with", "E   AssertionError: bad"))
    collection = read_junit(
        _junit("error", "collection failure", "E   AssertionError: at import", name="tests.test_a")
    )
    body = read_junit(_junit("failure", "x", "E   AssertionError: boom"))
    for report in (fixture, collection):
        assert (
            judge(1, report.test_id, report.first_line, expect="AssertionError") is Verdict.KILLED
        ), "the premise changed: judge alone reads this as a kill"
        assert judge_report(1, report, expect="AssertionError") is Verdict.ERROR, (
            "a fixture or collection error was a kill"
        )
        assert judge_report(1, report, expect="AssertionError", pinned="x") is Verdict.ERROR
    assert judge_report(1, body, expect="boom", pinned="tests/test_a::test_x") is Verdict.KILLED
    assert judge_report(1, body, expect="nothing like it") is Verdict.WRONG_REASON
    assert (
        judge_report(0, fixture) is Verdict.SURVIVED
        and judge_report(5, fixture) is Verdict.NO_TESTS
    )
    assert judge_report(2, body) is Verdict.ERROR
    with pytest.raises(ValueError, match="at least 4"):
        judge_report(1, fixture, expect="abc")


def test_the_runner_judges_through_judge_report(tmp_path, monkeypatch):
    seen = []
    import hadavin_sdk.testing.mutation as mu

    real = mu.judge_report
    monkeypatch.setattr(mr, "judge_report", lambda *a, **k: seen.append(a[0]) or real(*a, **k))
    xml = tmp_path / "r.xml"
    xml.write_text(
        _junit("failure", "x", "E   AssertionError: boom", classname="tests.test_core"),
        encoding="utf-8",
    )
    named = Mutant("flip", "src/pk/core.py", "return flag", "return not flag", "AssertionError")
    assert mr._row(named, 1, xml, False, mr._Shown(), {})[1] is Verdict.KILLED
    assert seen == [1], "the runner did not judge through judge_report"


# ---- the lock folder: private to the user, opened once, and the lock file is made under the opened folder -------------------

REAL_LOCK_DIR = (
    mr._lock_dir
)  # the runner's own choice of the folder, kept before any fixture replaces it


@pytest.fixture
def _real_lock_dir(_own_lock_folder, monkeypatch, tmp_path):
    """The runner's REAL choice of the lock folder (the autouse fixture above replaced it; this puts the real function back) inside a temp
    folder of this test, with no ``XDG_RUNTIME_DIR``. Gives the folder the lock folder is made in."""
    monkeypatch.setattr(mr, "_lock_dir", REAL_LOCK_DIR)
    monkeypatch.setattr(mr.tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
    return tmp_path


def _opened_and_closed() -> None:
    fd = mr._open_lock_dir()
    if fd is not None:
        os.close(fd)


@pytest.mark.skipif(os.name == "nt", reason="POSIX owners and modes")
def test_the_lock_folder_is_made_private_and_reused(_real_lock_dir):
    path = mr._lock_dir()
    assert path.parent == _real_lock_dir and path.name == f"hadavin_mutation_locks_{os.getuid()}", (
        path
    )
    assert not path.exists(), "the choice of the folder already made it"
    _opened_and_closed()
    assert stat.S_IMODE(path.lstat().st_mode) == 0o700, oct(path.lstat().st_mode)
    _opened_and_closed()  # a second run reuses the folder
    assert mr._lock_dir() == path


@pytest.mark.skipif(os.name == "nt", reason="POSIX owners and modes")
def test_a_lock_folder_that_others_can_enter_or_that_is_not_the_users_is_refused(_real_lock_dir):
    path = _real_lock_dir / f"hadavin_mutation_locks_{os.getuid()}"
    path.mkdir(mode=0o755)
    path.chmod(0o755)
    _must_raise(
        "a lock folder that others can enter was accepted",
        RuntimeError,
        mr._open_lock_dir,
        match="open to group or others",
    )
    path.chmod(0o770)
    _must_raise(
        "a lock folder that the group can enter was accepted",
        RuntimeError,
        mr._open_lock_dir,
        match="open to group or others",
    )
    path.chmod(0o700)
    _opened_and_closed()


@pytest.mark.skipif(os.name == "nt", reason="POSIX owners and modes")
def test_a_lock_folder_of_another_user_is_refused(_real_lock_dir, monkeypatch):
    other = os.getuid() + 1
    monkeypatch.setattr(mr.os, "getuid", lambda: other)
    planted = _real_lock_dir / f"hadavin_mutation_locks_{other}"
    planted.mkdir(
        mode=0o700
    )  # made by this user, so it does not belong to the user it is named for
    _must_raise(
        "a lock folder of another user was accepted",
        RuntimeError,
        mr._open_lock_dir,
        match="belongs to another user",
    )


@pytest.mark.skipif(os.name == "nt", reason="POSIX owners and modes")
def test_a_symbolic_link_or_a_file_in_place_of_the_lock_folder_is_refused(_real_lock_dir):
    name = _real_lock_dir / f"hadavin_mutation_locks_{os.getuid()}"
    target = _real_lock_dir / "elsewhere"
    target.mkdir(mode=0o700)
    name.symlink_to(target)
    _must_raise(
        "a symbolic link in place of the lock folder was followed",
        RuntimeError,
        mr._open_lock_dir,
        match="could not be made or opened",
    )
    name.unlink()
    name.write_text("a file, not a folder", encoding="utf-8")
    _must_raise(
        "a file in place of the lock folder was accepted",
        RuntimeError,
        mr._open_lock_dir,
        match="could not be made or opened",
    )


@pytest.mark.skipif(os.name == "nt", reason="POSIX owners and modes")
def test_what_was_opened_as_the_lock_folder_must_be_a_folder(_real_lock_dir, monkeypatch):
    # the second line of defence behind O_DIRECTORY: the record of the OPENED thing is checked, here made to say "a regular file"
    real = os.fstat
    monkeypatch.setattr(
        os, "fstat", lambda fd: os.stat_result((stat.S_IFREG | 0o700, *tuple(real(fd))[1:]))
    )
    _must_raise(
        "something that is not a folder was accepted as the lock folder",
        RuntimeError,
        mr._open_lock_dir,
        match="is not a folder",
    )


@pytest.mark.skipif(os.name == "nt", reason="POSIX owners and modes")
def test_a_lock_folder_that_cannot_be_made_is_a_clear_refusal(_real_lock_dir, monkeypatch):
    # a temp folder that does not exist: the same refusal for every account, also for root (which can write to a read-only folder)
    monkeypatch.setattr(mr.tempfile, "gettempdir", lambda: str(_real_lock_dir / "missing"))
    caught = None
    try:
        mr._open_lock_dir()
    except (RuntimeError, OSError) as exc:
        caught = exc
    assert isinstance(caught, RuntimeError), (
        f"a lock folder that cannot be made was not the documented refusal: {caught!r}"
    )
    assert "could not be made or opened" in str(caught) and "TMPDIR" in str(caught), caught


@pytest.mark.skipif(os.name == "nt", reason="POSIX owners and modes")
def test_the_lock_folder_is_opened_as_a_folder_without_following_a_link_and_the_file_is_made_under_it(
    _real_lock_dir, monkeypatch
):
    calls: list[tuple[str, int, bool]] = []
    real = os.open

    def spy(path, flags, *a, **k):
        calls.append((str(path), flags, "dir_fd" in k))
        return real(path, flags, *a, **k)

    monkeypatch.setattr(os, "open", spy)
    with mr._one_run_per_database(["host=y"]):
        pass
    (folder, folder_flags, _), (lock, _lock_flags, under_the_folder) = calls
    assert folder == str(mr._lock_dir()), calls
    assert folder_flags & os.O_DIRECTORY and folder_flags & os.O_NOFOLLOW, (
        "the lock folder was not opened as a folder without following a link"
    )
    assert under_the_folder and "/" not in lock, (
        f"the lock file was opened by a path, not under the opened folder: {lock}"
    )
    assert lock == _lock_name("y\n\n\n")
    assert (mr._lock_dir() / lock).is_file()


@pytest.mark.skipif(os.name == "nt", reason="POSIX owners and modes")
def test_the_lock_folder_prefers_the_runtime_folder_of_the_user_when_it_is_private(
    _real_lock_dir, monkeypatch
):
    runtime = _real_lock_dir / "run"
    runtime.mkdir(mode=0o700)
    runtime.chmod(0o700)
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(runtime))
    name = f"hadavin_mutation_locks_{os.getuid()}"
    assert mr._lock_dir() == runtime / name, (
        "a private XDG_RUNTIME_DIR of this user was not preferred"
    )
    runtime.chmod(0o755)
    assert mr._lock_dir() == _real_lock_dir / name, "a runtime folder open to others was used"
    runtime.chmod(0o700)
    monkeypatch.setenv("XDG_RUNTIME_DIR", "run")
    assert mr._lock_dir() == _real_lock_dir / name, "a relative XDG_RUNTIME_DIR was used"
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(runtime))
    monkeypatch.setattr(mr.os, "getuid", lambda: os.geteuid() + 1)
    assert mr._lock_dir().parent == _real_lock_dir, "a runtime folder of another user was used"


# ---- the output allowlist: while a passed variable has a value, only text of the caller or of Python is shown ----------------

_PW = "Zq9x" + "K4mTw"  # a made-up password, in parts


def _shown(tmp_path, *, mutants=(), classes=(), body="def test_a(v):\n    pass\n", url=""):
    """The allowlist of a call whose one test file is ``tests/test_core.py`` with ``body``, for the made-up address with the made-up password."""
    snapshot = tmp_path / "snapshot"
    (snapshot / "tests").mkdir(parents=True, exist_ok=True)
    (snapshot / CORE_TEST).write_text(body, encoding="utf-8")
    url = url or _url("svc", "Zq9x", "K4mTw", rest=f"{FAKE_HOST}/app")
    secrets = mr._secret_values((DSN_NAME,), {DSN_NAME: url})
    return mr._shown_for(secrets, list(mutants), [CORE_TEST], classes, snapshot)


def test_the_projection_shows_the_class_the_expect_word_and_the_callers_expect_only(tmp_path):
    shown = _shown(tmp_path)
    line = f"E   AssertionError: assert 'x' == 'y' at {FAKE_HOST} with {_PW}"
    assert mr._shown_line(line, shown, "assert 'x'") == "AssertionError [expect found] assert 'x'"
    assert (
        mr._shown_line(line, shown, "another text")
        == "AssertionError [expect not found] another text"
    )
    assert mr._shown_line(line, shown) == "AssertionError"
    assert mr._shown_line("", shown) == ""
    assert mr._shown_line("E   demo.fakes.KeyError: boom", shown) == "KeyError"
    assert mr._shown_line("E   Failed: DID NOT RAISE", shown) == "Failed"
    assert mr._shown_line(line, mr._Shown()) == line, "with no passed value the line was changed"


def test_a_class_name_is_shown_only_when_it_is_on_the_allowlist_of_the_call(tmp_path):
    shown = _shown(tmp_path)
    hostile = (
        _PW,
        _PW[::-1],
        _PW[1:-1],
        base64.b64encode(_PW.encode()).decode().rstrip("="),
        _PW.encode().hex(),
        codecs.encode(_PW, "rot13"),
        _PW.upper(),
        "PostgresError",
        "SomeLibraryError",
        "not an identifier",
        "",
    )
    for name in hostile:
        assert mr._shown_line(f"E   {name}: x", shown) == mr.CLASS_HIDDEN, (
            f"a class name that is not on the allowlist was shown (case {hostile.index(name)})"
        )
    crash = Mutant("c", "src/pk/core.py", "a", "b", "boom", allow_crash=True, crash_type="OwnCrash")
    assert mr._shown_line("E   OwnCrash: x", _shown(tmp_path, mutants=[crash])) == "OwnCrash", (
        "the crash_type of a mutant of this call was not shown"
    )
    assert mr._shown_line("E   OwnCrash: x", shown) == mr.CLASS_HIDDEN, (
        "a crash_type of no mutant of this call was shown"
    )
    listed = _shown(tmp_path, classes=("PostgresError",))
    assert mr._shown_line("E   lib.PostgresError: x", listed) == "PostgresError", (
        "a class the caller listed in shown_classes was not shown"
    )
    assert mr._shown_line("E   SomeLibraryError: x", listed) == mr.CLASS_HIDDEN


def test_the_address_of_ci_hides_no_ordinary_class_name_and_no_test_id_of_the_caller(tmp_path):
    # the address of CI holds no password; the old rule (no shared piece of four characters) hid ``PostgresError`` and ``test_postgres_store`` for it
    ci = "postgresql://postgres@localhost:5432/postgres"
    snapshot = tmp_path / "snapshot"
    (snapshot / "tests").mkdir(parents=True)
    tests = ["tests/test_postgres_store.py", "tests/test_other.py"]
    (snapshot / tests[0]).write_text("def test_x():\n    pass\n", encoding="utf-8")
    (snapshot / tests[1]).write_text("def test_regression():\n    pass\n", encoding="utf-8")
    secrets = mr._secret_values((DSN_NAME,), {DSN_NAME: ci})
    shown = mr._shown_for(secrets, [], tests, ("PostgresError",), snapshot)
    assert mr._shown_id("tests/test_postgres_store::test_x", shown) == (
        "tests/test_postgres_store::test_x"
    ), "a test id of the caller was hidden for the address of CI"
    assert mr._shown_id("tests/test_other::test_regression", shown) == (
        "tests/test_other::test_regression"
    )
    assert mr._shown_line("E   PostgresError: x", shown) == "PostgresError"
    assert mr._shown_line("E   AssertionError: x", shown) == "AssertionError"


def test_a_test_id_is_shown_only_when_it_is_made_of_the_callers_own_text(tmp_path):
    body = "class TestK:\n    def test_in_class(self):\n        pass\n\ndef test_a(v):\n    pass\n"
    shown = _shown(tmp_path, body=body)
    assert mr._shown_id("tests/test_core::test_a", shown) == "tests/test_core::test_a"
    cases = {
        "the file part is not one of the caller's tests": f"tests/{_PW[::-1]}::test_a",
        "a file part that only starts like a caller's test": "tests/test_core_more::test_a",
        "the function is not defined in the snapshot of that file": f"tests/test_core::{_PW[::-1]}",
        "a class that is not defined in the snapshot of that file": f"tests/test_core/{_PW[::-1]}::test_a",
        "no function part": "tests/test_core",
        "an empty function part": "tests/test_core::",
        "a collection id": "::tests.test_core",
        "an empty id": "",
    }
    for label, test_id in cases.items():
        assert mr._shown_id(test_id, shown) == mr.ID_HIDDEN, (
            f"a test id that is not the caller's own text was shown: {label}"
        )
    assert mr._shown_id("tests/test_core/TestK::test_in_class", shown) == (
        "tests/test_core/TestK::test_in_class"
    ), "a test in a class of the caller's file was hidden"
    assert mr._shown_id("tests/test_core::test_gone", shown) == mr.ID_HIDDEN
    assert mr._shown_id("tests/test_core::test_gone", shown, ("test_gone",)) == (
        "tests/test_core::test_gone"
    ), "a function the caller named on the mutant (only_test, pinned) was hidden"
    assert mr._shown_id("tests/test_core::test_a", mr._Shown()) == "tests/test_core::test_a"
    assert mr._shown_id(f"x/{_PW}::y[{_PW}]", mr._Shown()) == f"x/{_PW}::y[{_PW}]", (
        "with no passed value the id was changed"
    )


def test_the_projection_replaces_the_parameters_of_a_test_id(tmp_path):
    shown = _shown(tmp_path)
    out = mr._shown_id(f"tests/test_core::test_a[{_PW}-{FAKE_HOST}]", shown)
    assert out == "tests/test_core::test_a" + mr.PARAMETERS_HIDDEN, (
        f"the parameters of a test id were shown: {out}"
    )
    assert mr._shown_id("tests/test_core::test_a[1]", shown).endswith(mr.PARAMETERS_HIDDEN), (
        "harmless parameters were shown: the parameters are always replaced"
    )


def test_the_names_the_caller_wrote_on_a_mutant_are_its_only_test_and_its_pinned_function():
    m = Mutant(
        "m", "src/pk/core.py", "a", "b", "boom", only_test="test_one", pinned="tests/t::test_two[x]"
    )
    assert mr._own_names(m) == ("test_one", "test_two")
    assert mr._own_names(FLIP) == ()


def test_the_second_layer_masks_a_secret_that_is_also_caller_text(tmp_path):
    # a caller whose test function is named like the password: the allowlist shows it, the masker (the second layer) still hides it
    shown = _shown(tmp_path, body=f"def {_PW}():\n    pass\n", classes=(_PW,))
    assert _PW not in mr._shown_id(f"tests/test_core::{_PW}", shown), (
        "the masker did not run after the allowlist on a test id"
    )
    assert _PW not in mr._shown_line(f"E   {_PW}: x", shown), (
        "the masker did not run after the allowlist on a class name"
    )
    assert _PW not in mr._shown_line("E   AssertionError: x", shown, f"expect {_PW}"), (
        "the masker did not run on the caller's expect text"
    )


def test_the_callers_expect_text_is_printed_as_given_and_the_docstring_says_so(tmp_path):
    # the caller owns ``expect``: a piece of the password written there is shown (only a text the masker knows, the whole password, is replaced)
    shown = _shown(tmp_path)
    piece = _PW[:4]
    line = f"E   AssertionError: boom {_PW}"
    assert mr._shown_line(line, shown, piece) == f"AssertionError [expect found] {piece}", (
        "the caller's expect text was not printed as given"
    )
    doc = " ".join((mr.__doc__ or "").split())
    assert "never put a secret in ``expect``" in doc, (
        "the module docstring no longer tells the caller to keep secrets out of expect"
    )


def test_shown_classes_takes_plain_class_names_only_and_is_checked_before_anything_runs(
    tmp_path, monkeypatch
):
    root = _tree(tmp_path, {CORE_TEST: USES_GO})
    started = []
    monkeypatch.setattr(mr, "_pytest", lambda *a, **k: started.append("run") or 0)
    for bad in (("not a name",), ("a.b",), ("",), (1,), ("PostgresError", "x y")):
        _must_refuse(
            f"a shown_classes entry that is no class name was accepted (case {bad!r})",
            _run,
            root,
            [FLIP],
            shown_classes=bad,
        )
    with pytest.raises(TypeError):
        _run(root, [FLIP], shown_classes="PostgresError")
    assert started == [], f"something ran before shown_classes was refused: {started}"


_FORMS = {
    "plain": lambda t: t,
    "slice": lambda t: t[1:-1],
    "reversed": lambda t: t[::-1],
    "base64": lambda t: base64.b64encode(t.encode()).decode().rstrip("="),
    "hex": lambda t: t.encode().hex(),
    "rot13": lambda t: codecs.encode(t, "rot13"),
    "upper": lambda t: t.upper(),
    "percent": lambda t: "".join(f"%{ord(c):02X}" for c in t),
}

PICKS_A_CLASS = (
    "import pytest\nfrom pk import core\n\nNAMES = {names!r}\n\n"
    "def test_a():\n    if core.PICK:\n        raise type(NAMES[core.PICK - 1], (Exception,), {{}})('x')\n"
)


def test_a_form_of_the_password_as_a_class_name_never_reaches_first_lines_in_a_real_run(
    tmp_path, monkeypatch
):
    """The proof that fails on the runner before the allowlist: a child raises an exception whose CLASS NAME is the password reversed (and
    in five more forms). Only names both runners have are used, so this test runs on the old runner too, and fails there by showing the name."""
    dsn, word = _secret_dsn()
    monkeypatch.setenv(DSN_NAME, dsn)
    forms = {kind: form(word) for kind, form in _FORMS.items() if kind not in ("plain", "percent")}
    root = _tree(tmp_path, {CORE_TEST: PICKS_A_CLASS.format(names=list(forms.values()))})
    (root / "src" / "pk" / "core.py").write_text("PICK = 0\n", encoding="utf-8")
    mutants = [
        Mutant(kind, "src/pk/core.py", "PICK = 0", f"PICK = {n}", "assert")
        for n, kind in enumerate(forms, 1)
    ]
    lines: dict[str, str] = {}
    rows = _run(root, mutants, pass_env=(DSN_NAME,), first_lines=lines)
    assert [r[0] for r in rows] == list(forms), rows
    for kind, text in forms.items():
        assert text not in lines[kind], (
            f"the password in the form '{kind}' was shown as the class name in first_lines"
        )
        assert lines[kind] == "[class not shown] [expect not found] assert", (
            f"not the replacement text for a class name that is not allowed (form '{kind}'): shown"
        )


FUZZ_SEEDS = 60
FUZZ_OUTPUTS = 13  # per iteration: nine result rows, the baseline failure, the baseline skip message and the two canary messages
_SKIP_MESSAGE = re.compile(r"the unmutated copy skipped 1 selected test\(s\): (\[.*\])")


def _case(classname: str, name: str, inner: str) -> str:
    from xml.sax.saxutils import quoteattr

    return (
        f"<testsuites><testsuite><testcase classname={quoteattr(classname)} name={quoteattr(name)}>"
        f"{inner}</testcase></testsuite></testsuites>"
    )


def _bad(tag: str, message: str, line: str) -> str:
    from xml.sax.saxutils import escape, quoteattr

    return f"<{tag} message={quoteattr(message)}>{escape(line)}</{tag}>"


def _fuzz_outputs(folder: Path, shown, text: str, rng: _Det):
    """Every output the runner gives for one child text, from the REAL functions: ``(kind, value)`` with kind ``id`` (the test id column of a row),
    ``line`` (a ``first_lines`` entry), ``failure`` (the baseline failure message), ``skip`` (the baseline skip message) or ``canary``. Each slot
    of the child's text (class name, file, function) holds the hostile ``text`` or, half of the time, a value the allowlist shows."""
    cls = rng.choice([text, text, "KeyError", "Failed", "PostgresError", "OwnCrash"])
    file = rng.choice([f"tests.{text}", "tests.test_core"])
    function = rng.choice([text, "test_a", "test_own", "test_pinned"])
    name = f"{function}[{text}]"
    plain = Mutant("flip", "src/pk/core.py", "a", "b", "assert", only_test="test_own")
    pinned = Mutant(
        "flip", "src/pk/core.py", "a", "b", "assert", pinned="tests/test_core::test_pinned"
    )
    kill = _case(file, name, _bad("failure", text, f"E   AssertionError: assert {text}"))
    wrong = _case(file, name, _bad("failure", text, f"E   {cls}: {text}"))
    skipped = _case(file, name, f"<skipped message={text!r}/>")
    skipped_and_failed = (
        "<testsuites><testsuite>"
        + _case(file, name, f"<skipped message={text!r}/>").removeprefix("<testsuites><testsuite>")
    ).replace(
        "</testcase>",
        "</testcase>"
        + f'<testcase classname="tests.test_core" name="test_a">{_bad("failure", text, f"E   {cls}: {text}")}</testcase>',
    )
    collection = _case("", file, _bad("error", "collection failure", f"E   {cls}: {text}"))
    fixture = _case(file, name, _bad("error", f"failed on setup with {text}", f"E   {cls}: {text}"))
    runs = (
        ("kill", plain, 1, kill, False),
        ("wrong reason", plain, 1, wrong, False),
        ("other test", pinned, 1, kill, False),
        ("SKIPPED", plain, 0, skipped, True),
        ("SKIPPED with a failure", plain, 1, skipped_and_failed, True),
        ("COLLECTION ERROR", plain, 2, collection, False),
        ("FIXTURE ERROR", plain, 1, fixture, False),
        ("timeout", plain, mr.TIMED_OUT, kill, False),
        ("unusable JUnit", plain, 1, f"<testsuites><{text}", False),
    )
    junit = folder / "r.xml"
    for path, mutant, rc, xml, forbid in runs:
        junit.write_text(xml, encoding="utf-8")
        lines: dict[str, str] = {}
        row = mr._row(mutant, rc, junit, forbid, shown, lines)
        assert row[0] == "flip" and isinstance(row[1], Verdict) and isinstance(row[3], bool), row
        assert set(lines) <= {"flip"}, lines
        yield path, "id", row[2]
        if lines:
            yield path, "line", lines["flip"]
    junit.write_text(wrong, encoding="utf-8")
    yield "baseline failure", "failure", mr._baseline_failure(1, junit, shown)
    yield "canary failure", "canary", mr._canary_refusal(plain, 1, junit, True, shown)
    junit.write_text(skipped, encoding="utf-8")
    try:
        mr._refuse_skips_in_baseline(junit, shown)
        raise AssertionError("a baseline that skipped was accepted")
    except RuntimeError as exc:
        yield "baseline skip", "skip", str(exc)
    yield "canary skip", "canary", mr._canary_refusal(plain, 0, junit, True, shown)


def _fuzz_allowed(shown):
    """What an output may be, written from the caller's side only: the fixed labels of a row, test ids made of the caller's file and function
    names, and lines made of an allowlisted class name, the fixed expect words and the caller's expect text."""
    ids = {
        f"tests/test_core::{function}{end}"
        for function in ("test_a", "test_own", "test_pinned")
        for end in ("", mr.PARAMETERS_HIDDEN)
    }
    labels = {
        "TIMEOUT", "JUNIT REFUSED", "COLLECTION ERROR", "FIXTURE ERROR", "SKIPPED TESTS", "EXIT CODE 2", mr.ID_HIDDEN,
    }  # fmt: skip
    classes = sorted(shown.classes | {mr.CLASS_HIDDEN})
    lines = {
        f"{c}{word}"
        for c in classes
        for word in ("", " [expect found] assert", " [expect not found] assert")
    }
    return ids, labels, classes, lines


def _check_one_output(kind: str, value: str, shown, counts: dict[str, int]) -> None:
    ids, labels, classes, lines = _fuzz_allowed(shown)
    failure = "the unmutated copy does not pass its tests (exit code 1): "
    canary_failure = (
        "the unmutated copy no longer passes its tests after mutant 'flip' (exit code 1): the shared test database holds what the"
        " mutant left behind, so the verdicts of the later mutants would not be reliable"
    )
    if kind == "id":
        assert value in ids | labels, "a test id column is not the caller's text or a fixed label"
        counts["id shown" if value in ids else "id replaced"] += 1
    elif kind == "line" and value.startswith("skipped: "):
        assert set(value.removeprefix("skipped: ").split(", ")) <= ids | {mr.ID_HIDDEN}, (
            "the ids of a skipped-tests line are not the caller's text"
        )
    elif kind == "line":
        assert value in lines, "a first line is not an allowlisted class and the fixed words"
        counts["class replaced" if value.startswith(mr.CLASS_HIDDEN) else "class shown"] += 1
    elif kind == "failure":
        assert value.startswith(failure) and value.removeprefix(failure) in classes, (
            "the baseline failure message holds more than the run end and an allowlisted class"
        )
    elif value == canary_failure:
        pass
    else:
        skip = _SKIP_MESSAGE.fullmatch(value.removeprefix("after mutant 'flip': "))
        assert skip and (kind == "skip") != value.startswith("after mutant 'flip': "), (
            "a skip message is not the fixed text with a list of ids"
        )
        assert set(ast.literal_eval(skip.group(1))) <= ids | {mr.ID_HIDDEN}, (
            "the ids of a skip message are not the caller's text"
        )
    counts["outputs"] += 1


def _fuzz(tmp_path, seeds=range(FUZZ_SEEDS)) -> dict[str, int]:
    counts = dict.fromkeys(
        ("iterations", "outputs", "id shown", "id replaced", "class shown", "class replaced"), 0
    )
    crash = Mutant("c", "src/pk/core.py", "a", "b", "boom", allow_crash=True, crash_type="OwnCrash")
    letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    for seed in seeds:
        rng = _Det(seed)
        word = "".join(rng.choice(letters) for _ in range(rng.randint(8, 24)))
        shown = _shown(
            tmp_path,
            mutants=[crash],
            classes=("PostgresError",),
            url=f"postgresql://svc:{word}@{FAKE_HOST}:5432/app",
        )
        for form in _FORMS.values():
            text = form(rng.choice([word, f"postgresql://svc:{word}@{FAKE_HOST}:5432/app"]))
            counts["iterations"] += 1
            seen = 0
            for _path, kind, value in _fuzz_outputs(tmp_path, shown, text, rng):
                if kind != "line":  # a line belongs to the row whose id was counted just before it
                    seen += 1
                _check_one_output(kind, value, shown, counts)
            assert seen == FUZZ_OUTPUTS, f"an iteration gave {seen} outputs, not {FUZZ_OUTPUTS}"
    return counts


def test_fuzz_every_output_field_holds_only_allowlisted_classes_and_caller_ids(tmp_path):
    """Seeded: 60 secrets x 8 forms of child text (plain, slice, reversed, base64, hex, rot13, upper, percent) = 480 iterations, 13 outputs each
    (6,240), and the ``first_lines`` entry of every row that has one. Each output must be IN the set of texts built from the caller's side; no
    random piece is compared with the runner's fixed words."""
    counts = _fuzz(tmp_path)
    assert counts["iterations"] == FUZZ_SEEDS * len(_FORMS) == 480, counts
    assert (
        counts["outputs"] - counts["class shown"] - counts["class replaced"] >= 480 * FUZZ_OUTPUTS
    )
    for slot in ("id shown", "id replaced", "class shown", "class replaced"):
        assert counts[slot] > 100, f"the fuzz hardly reached the case '{slot}': {counts}"


def test_the_fuzz_check_fails_when_the_class_or_the_id_allowlist_is_switched_off(
    tmp_path, monkeypatch
):
    # the control of the fuzz: the same check on a runner that shows the child's class name, or the child's test id, must fail
    with monkeypatch.context() as off:
        off.setattr(mr, "_shown_class", lambda raw, shown: mr._leading_class(raw))
        with pytest.raises(AssertionError, match="a first line is not an allowlisted class"):
            _fuzz(tmp_path, range(3))
    with monkeypatch.context() as off:
        off.setattr(mr, "_shown_id", lambda test_id, shown, own_names=(): test_id.partition("[")[0])
        with pytest.raises(AssertionError, match="not the caller's text"):
            _fuzz(tmp_path, range(3))


def test_a_row_with_no_passed_value_shows_the_line_and_the_id_as_before(tmp_path):
    xml = tmp_path / "r.xml"
    xml.write_text(
        _junit("failure", "m", "E   KeyError: 'k'", classname="tests.test_a", name="test_x[1]"),
        encoding="utf-8",
    )
    lines: dict[str, str] = {}
    crash = Mutant(
        "c", "src/pk/core.py", "a", "b", "KeyError", allow_crash=True, crash_type="KeyError"
    )
    row = mr._row(crash, 1, xml, False, mr._Shown(), lines)
    assert row == ("c", Verdict.CRASH, "tests/test_a::test_x[1]", True), row
    assert lines == {"c": "E   KeyError: 'k'"}, lines


def test_crash_type_is_checked_against_the_raw_line_also_when_the_class_is_not_shown(tmp_path):
    # the judge and crash_type read the child's line inside the runner; what the caller sees is decided afterwards
    xml = tmp_path / "r.xml"
    xml.write_text(
        _junit(
            "failure", "m", "E   lib.OwnCrash: boom", classname="tests.test_core", name="test_a"
        ),
        encoding="utf-8",
    )
    crash = Mutant("c", "src/pk/core.py", "a", "b", "boom", allow_crash=True, crash_type="OwnCrash")
    lines: dict[str, str] = {}
    row = mr._row(crash, 1, xml, False, _shown(tmp_path, mutants=[crash]), lines)
    assert row == ("c", Verdict.CRASH, "tests/test_core::test_a", True), row
    assert lines == {"c": "OwnCrash [expect found] boom"}, lines


# ---- the address check: an exact list of hosts, one strict grammar ---------------------------------------------------------

_OK_ADDRESSES = [
    "postgresql://postgres@localhost:5432/postgres",  # the address CI passes (.github/workflows/ci.yml)
    _url("svc", "Zq9x", rest="localhost:5432/app"),
    "postgresql://127.0.0.1/any_name",
    "postgres://[::1]:5432/app",
    "host=::1 port=5432 dbname=app",
    "host=localhost port=5432 dbname=app user=svc sslmode=disable connect_timeout=3",
    "hostaddr=127.0.0.1 dbname=app",
    "host=localhost hostaddr=::1 dbname=app",
    "host=LOCALHOST dbname=app",
]
_NO_HOST = "names no host and no hostaddr"
_REFUSED_ADDRESSES = [
    ("host=db.example.org dbname=app", "host is not one of"),
    ("host=localhost hostaddr=10.0.0.5 dbname=app", "hostaddr is not one of"),
    ("hostaddr=10.0.0.5 dbname=app", "hostaddr is not one of"),
    (_url("svc", "Zq9x", rest="db.example.org/app"), "host is not one of"),
    ("postgresql://10.0.0.5/app", "host is not one of"),
    ("postgresql://localhost.example.org/app", "host is not one of"),
    ("host=0.0.0.0 dbname=app", "host is not one of"),
    # a unix socket folder is a host like any other: it is not on the default list
    ("host=/var/run/postgresql dbname=app", "host is not one of"),
    ("host=/run/pg dbname=app", "host is not one of"),
    # no host at all would be the default local socket
    ("dbname=app", _NO_HOST),
    ("user=svc", _NO_HOST),
    ("port=5432 dbname=app user=svc", _NO_HOST),
    ("host=localhost dbname=app service=prod", "not in a shape"),
    ("host=localhost dbname=app options=-c", "not in a shape"),
    ("postgresql://localhost/app?host=db.example.org", "not in a shape"),
    ("postgresql://localhost/app?hostaddr=8.8.8.8", "not in a shape"),
    ("postgresql://localhost,db.example.org/app", "not in a shape"),
    ("host=localhost,db.example.org dbname=app", "not in a shape"),
    ("host=/run/../etc dbname=app", "not in a shape"),
    ("host=[::1] dbname=app", "not in a shape"),  # brackets are for the URL form only
    ("postgresql://::1/app", "not in a shape"),  # and the URL form needs them
    ("host=localhost " + _PW_KEY + "=Zq9x dbname=app", "not in a shape"),
    (_url("svc", "a", "@b", rest="localhost/app"), "not in a shape"),
    (SENTINEL, "not in a shape"),
    ("", "not in a shape"),
    ("host=localhost dbname=app junk", "not in a shape"),
    ("mysql://localhost/app", "not in a shape"),
]
# one refused key per allowed key: a key of the database library that is close to it and that the grammar must not let through
_REFUSED_SIBLING = {
    "host": "service=prod",
    "hostaddr": "target_session_attrs=any",
    "port": "options=-cport=1",
    "dbname": "replication=database",
    "user": "passfile=/run/p",
    "sslmode": "sslrootcert=/run/ca.pem",
    "connect_timeout": "application_name=x",
}


_TMP = (
    "/" + "tmp"
)  # the socket folder of the probes, in parts (the linter reads a literal as a temp file path)
# the exact values of the independent probes of round 19, one test each: every one must be refused by the default host list
_PROBES_REFUSED = {
    "a trailing-dot host": ("postgresql://u@localhost./db", "host is not one of"),
    "a local-looking public name": ("postgresql://u@127.0.0.1.nip.io/db", "host is not one of"),
    "an IPv4 address inside an IPv6 host": (
        "postgresql://u@[::ffff:127.0.0.1]/db",
        "host is not one of",
    ),
    "the short form of 127.0.0.1": ("postgresql://u@127.1/db", "host is not one of"),
    "a decimal host": ("postgresql://u@2130706433/db", "host is not one of"),
    "a hex host": ("postgresql://u@0x7f.0.0.1/db", "host is not one of"),
    "a hostaddr outside the list": (
        "host=localhost hostaddr=10.0.0.5 dbname=x",
        "hostaddr is not one of",
    ),
    "a unix socket folder that is not listed": (f"host={_TMP} dbname=x", "host is not one of"),
    "a socket folder with a dot-dot part": (f"host={_TMP}/../etc dbname=x", "not in a shape"),
    "a host in the query": ("postgresql://u@localhost/db?host=10.0.0.5", "not in a shape"),
    "two hosts": ("postgresql://u@localhost,10.0.0.5/db", "not in a shape"),
    "a service name": ("service=prod", "not in a shape"),
    "a URL with a trailing newline": (
        "postgresql://postgres@localhost:5432/postgres\n",
        "not in a shape",
    ),
    "words with a trailing newline": ("host=localhost dbname=x\n", "not in a shape"),
}


@pytest.mark.parametrize("probe", list(_PROBES_REFUSED))
def test_each_hostile_address_of_the_probes_is_refused(probe):
    value, why = _PROBES_REFUSED[probe]
    _must_raise(
        f"a hostile address was accepted ({probe})",
        ValueError,
        mr._refuse_unsafe_address,
        DSN_NAME,
        value,
        mr.THROWAWAY_HOSTS,
        match=why,
    )


@pytest.mark.parametrize("bad", ["*", ""])
def test_a_pattern_or_an_empty_text_in_the_host_list_is_refused(bad):
    for value in (
        "postgresql://postgres@localhost:5432/postgres",
        f"host={_TMP} dbname=x",
        "dbname=x",
    ):
        with pytest.raises(ValueError):
            mr._refuse_unsafe_address(DSN_NAME, value, (bad,))
    with pytest.raises(ValueError, match="exact host names"):
        mr._refuse_unsafe_address(DSN_NAME, "postgresql://postgres@localhost:5432/postgres", (bad,))


def test_the_probes_that_are_accepted_stay_accepted_and_a_socket_folder_needs_its_exact_entry():
    mr._refuse_unsafe_address(DSN_NAME, "postgresql://u@LOCALHOST/db", mr.THROWAWAY_HOSTS)
    mr._refuse_unsafe_address(DSN_NAME, "postgresql://u@[::1]/db", mr.THROWAWAY_HOSTS)
    mr._refuse_unsafe_address(DSN_NAME, f"host={_TMP} dbname=x", (_TMP,))


def test_a_percent_encoded_at_sign_in_a_url_password_is_accepted_and_hidden_in_both_forms():
    # decided: accepted. The grammar reads the login up to the one plain ``@``; the password is searched for as written and decoded
    value = "postgresql://u:" + "Zq9x" + "%40" + "K4mTw" + "@localhost/db"
    mr._refuse_unsafe_address(DSN_NAME, value, mr.THROWAWAY_HOSTS)
    secrets = mr._secret_values((DSN_NAME,), {DSN_NAME: value})
    assert "Zq9x%40K4mTw" in secrets and "Zq9x@K4mTw" in secrets, (
        "the password with a percent-encoded at sign is not searched for in both forms"
    )
    assert mr._address_fields(value) == {"host": "localhost", "port": "", "dbname": "db"}
    _must_refuse(
        "a plain at sign in a URL password was accepted",
        mr._refuse_unsafe_address,
        DSN_NAME,
        "postgresql://u:" + "Zq9x" + "@" + "K4mTw" + "@localhost/db",
        mr.THROWAWAY_HOSTS,
    )


@pytest.mark.parametrize("value", _OK_ADDRESSES)
def test_the_address_check_accepts_a_local_address_and_the_address_of_ci(value):
    mr._refuse_unsafe_address(DSN_NAME, value, mr.THROWAWAY_HOSTS)


def _refused_by_the_address_check(why: str):
    return [value for value, text in _REFUSED_ADDRESSES if text == why]


def _every_refused(why: str, label: str) -> None:
    assert _refused_by_the_address_check(why)
    for value in _refused_by_the_address_check(why):
        _must_raise(
            f"{label} ({value!r})",
            ValueError,
            mr._refuse_unsafe_address,
            DSN_NAME,
            value,
            mr.THROWAWAY_HOSTS,
            match=why,
        )


def test_the_address_check_refuses_a_host_that_is_not_on_the_allowlist():
    _every_refused("host is not one of", "a host that is not allowed was accepted")


def test_the_address_check_refuses_a_hostaddr_that_is_not_on_the_allowlist():
    _every_refused("hostaddr is not one of", "a hostaddr that is not allowed was accepted")


def test_the_address_check_refuses_an_address_outside_the_grammar():
    _every_refused("not in a shape", "an address outside the grammar was accepted")


def test_the_address_check_refuses_an_address_with_no_host():
    _every_refused(_NO_HOST, "an address with neither host nor hostaddr was accepted")
    # also when the caller narrowed the list: the caller cannot be bypassed by leaving the host out
    _must_raise(
        "an address with no host was accepted for a narrowed host list",
        ValueError,
        mr._refuse_unsafe_address,
        DSN_NAME,
        "dbname=prod",
        ("db",),
        match=_NO_HOST,
    )


def test_a_unix_socket_folder_is_accepted_only_as_an_exact_member_of_the_host_list():
    assert not [h for h in mr.THROWAWAY_HOSTS if h.startswith("/")], (
        "the default host list holds a unix socket folder"
    )
    value = "host=/var/run/postgresql dbname=prod"
    _must_raise(
        "a unix socket folder that is not listed was accepted",
        ValueError,
        mr._refuse_unsafe_address,
        DSN_NAME,
        value,
        ("db",),
        match="host is not one of",
    )
    mr._refuse_unsafe_address(DSN_NAME, value, ("/var/run/postgresql",))
    for near in ("/var/run", "/var/run/postgresql/", "/VAR/RUN/POSTGRESQL", "/var/run/postgresql2"):
        _must_raise(
            f"a unix socket folder was accepted for another listed folder ({near})",
            ValueError,
            mr._refuse_unsafe_address,
            DSN_NAME,
            value,
            (near,),
            match="host is not one of",
        )


def test_no_key_of_a_key_value_address_may_be_written_twice():
    samples = {
        "host": "localhost",
        "hostaddr": "127.0.0.1",
        "port": "5432",
        "dbname": "app",
        "user": "svc",
        "sslmode": "disable",
        "connect_timeout": "3",
    }
    assert set(samples) == set(mr.ADDRESS_KEYS_ALLOWED), "a key of the allowlist has no sample here"
    whole = " ".join(f"{key}={token}" for key, token in samples.items())
    mr._refuse_unsafe_address(DSN_NAME, whole, mr.THROWAWAY_HOSTS)
    for key, token in samples.items():
        for twice in (f"{whole} {key}={token}", f"{whole} {key.upper()}={token}"):
            _must_raise(
                f"the key {key} written twice was accepted",
                ValueError,
                mr._refuse_unsafe_address,
                DSN_NAME,
                twice,
                mr.THROWAWAY_HOSTS,
                match="not in a shape",
            )


def test_every_allowed_key_has_a_reason_and_a_refused_sibling():
    assert set(_REFUSED_SIBLING) == set(mr.ADDRESS_KEYS_ALLOWED), (
        "the key allowlist changed: every allowed key needs a refused sibling in this test"
    )
    for key, reason in mr.ADDRESS_KEYS_ALLOWED.items():
        assert len(reason) > 20, f"the key {key} has no written reason"
    for key, sibling in _REFUSED_SIBLING.items():
        _must_raise(
            f"a key that is not on the allowlist was accepted (the sibling of {key})",
            ValueError,
            mr._refuse_unsafe_address,
            DSN_NAME,
            f"host=localhost dbname=app {sibling}",
            mr.THROWAWAY_HOSTS,
            match="not in a shape",
        )
    assert "sslrootcert" not in mr.ADDRESS_KEYS_ALLOWED
    assert "application_name" not in mr.ADDRESS_KEYS_ALLOWED


def _in_every_form(host: str) -> list[str]:
    """``host`` written in each place of an address that names a host."""
    bracket = f"[{host}]" if ":" in host else host
    return [
        f"postgresql://svc@{bracket}:5432/app",
        f"postgresql://{bracket}/app",
        f"host={host} dbname=app",
        f"hostaddr={host} dbname=app",
        f"host=localhost hostaddr={host}",
    ]


def test_property_a_host_that_is_not_exactly_in_the_list_is_refused():
    near = [
        "localhost.",  # a trailing dot
        "2130706433",  # 127.0.0.1 as one decimal number
        "0x7f000001",  # as one hex number
        "0x7f.0.0.1",
        "127.1",  # the short form
        "127.0.0.01",
        "::ffff:127.0.0.1",  # the IPv4 address inside an IPv6 one
        "0:0:0:0:0:0:0:1",  # ::1 written out
        "LocalHost.Example",  # mixed case of a name that is not listed
        "localhost-1",
        "xlocalhost",
        "localhos",
    ]
    rng = _Det(89)
    alphabet = "abcdefABCDEF0123456789.:-xyzXYZ"
    random_hosts = {
        "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 20))) for _ in range(300)
    }
    members = set(mr.THROWAWAY_HOSTS)
    checked = 0
    for host in [*near, *sorted(random_hosts)]:
        if host.lower() in members:
            continue
        for value in _in_every_form(host):
            _must_refuse(
                f"a host that is not exactly in the list was accepted ({value!r})",
                mr._refuse_unsafe_address,
                DSN_NAME,
                value,
                mr.THROWAWAY_HOSTS,
            )
            checked += 1
    assert checked >= 5 * (len(near) + 290), checked
    # a member is accepted in any letter case, because host names ignore the case of letters
    for value, hosts in (
        ("host=LocalHost dbname=app", mr.THROWAWAY_HOSTS),
        ("host=db dbname=app", ("DB",)),
        ("postgresql://svc@DB/app", ("db",)),
    ):
        try:
            mr._refuse_unsafe_address(DSN_NAME, value, hosts)
        except ValueError:
            raise AssertionError(
                f"a member written in another letter case was refused ({value!r}, {hosts!r})"
            ) from None


def test_the_address_check_takes_an_exact_allowlist_and_nothing_wider():
    hosts = ("db",)  # a container CI that reaches its database by the service name
    mr._refuse_unsafe_address(DSN_NAME, "postgresql://postgres@db:5432/postgres", hosts)
    mr._refuse_unsafe_address(DSN_NAME, "host=DB dbname=x", hosts)
    with pytest.raises(ValueError, match="host is not one of"):
        mr._refuse_unsafe_address(
            DSN_NAME, "postgresql://postgres@localhost/postgres", hosts
        )  # the default is replaced, not widened
    with pytest.raises(ValueError, match="host is not one of"):
        mr._refuse_unsafe_address(DSN_NAME, "postgresql://postgres@db2/postgres", hosts)
    for bad in (
        "*",
        "*.example.org",
        "db/x",
        "a b",
        "",
        "db\n",
        "[::1]",
        "/run/../etc",
        "/run/*",
        5,
    ):
        with pytest.raises(ValueError, match="exact host names"):
            mr._refuse_unsafe_address(DSN_NAME, "host=db dbname=x", (bad,))
    with pytest.raises(TypeError):
        mr._refuse_unsafe_address(DSN_NAME, "host=db dbname=x", "db")


def test_the_host_list_is_checked_for_every_call_also_when_no_variable_is_passed(
    tmp_path, monkeypatch
):
    monkeypatch.delenv(DSN_NAME)
    root = _tree(tmp_path, {CORE_TEST: USES_GO})
    started = []
    monkeypatch.setattr(mr, "_pytest", lambda *a, **k: started.append("run") or 0)
    for kw in ({}, {"pass_env": (DSN_NAME,)}):
        _must_raise(
            f"a host list with a pattern was accepted (keywords {sorted(kw)})",
            ValueError,
            _run,
            root,
            [FLIP],
            throwaway_hosts=("*.example.org",),
            match="exact host names",
            **kw,
        )
    assert started == [], f"something ran before the host list was refused: {started}"


def test_the_address_check_message_never_shows_the_value():
    word = "Zq9x" + "K4mTw"
    value = _url("svc", word, rest="db.internal.example.org:5432/prod")
    with pytest.raises(ValueError) as caught:
        mr._refuse_unsafe_address(DSN_NAME, value, mr.THROWAWAY_HOSTS)
    assert (
        word not in str(caught.value)
        and "internal" not in str(caught.value)
        and "svc" not in str(caught.value)
    )
    with pytest.raises(ValueError) as caught:
        mr._refuse_unsafe_address(DSN_NAME, f"dbname=prod_{word} user=svc_{word}", ("db",))
    assert word not in str(caught.value) and "prod_" not in str(caught.value)


def test_the_address_check_has_no_override_keyword_and_no_database_name_rule():
    import inspect

    names = set(inspect.signature(run_mutants).parameters)
    assert "throwaway_hosts" in names and not names & {"allow_remote_address", "db_marker"}, names
    mr._refuse_unsafe_address(
        DSN_NAME, "postgresql://postgres@localhost:5432/postgres", mr.THROWAWAY_HOSTS
    )


def test_run_mutants_refuses_an_address_before_any_folder_or_run(tmp_path, monkeypatch):
    root = _tree(tmp_path, {CORE_TEST: USES_GO})
    started = []
    real_mkdtemp = mr.tempfile.mkdtemp
    monkeypatch.setattr(
        mr.tempfile, "mkdtemp", lambda *a, **k: started.append("folder") or real_mkdtemp(*a, **k)
    )
    monkeypatch.setattr(mr, "_pytest", lambda *a, **k: started.append("run") or 0)
    real_lock_dir = mr._open_lock_dir
    monkeypatch.setattr(mr, "_open_lock_dir", lambda: started.append("lock") or real_lock_dir())
    for value, why in (
        ("host=db.example.org dbname=app", "host is not one of"),
        ("host=localhost hostaddr=10.0.0.5 dbname=a", "hostaddr"),
        ("dbname=app", _NO_HOST),
        ("x", "not in a shape"),
    ):
        monkeypatch.setenv(DSN_NAME, value)
        _must_raise(
            f"run_mutants did not refuse an address the check refuses ({why})",
            ValueError,
            run_mutants,
            root,
            [FLIP],
            [CORE_TEST],
            extra_dirs=(),
            pass_env=(DSN_NAME,),
            forbid_skips=False,  # a run that wrongly starts ends quietly, so the missing refusal is what fails
            match=why,
        )
    assert started == [], f"something started before the address was refused: {started}"


def test_run_mutants_refuses_an_address_of_another_host_unless_it_is_named_on_purpose(
    tmp_path, monkeypatch
):
    root = _tree(tmp_path, {CORE_TEST: USES_GO})
    monkeypatch.setenv(DSN_NAME, f"host={FAKE_HOST} dbname=app")
    with pytest.raises(ValueError, match="host is not one of"):
        run_mutants(root, [FLIP], [CORE_TEST], extra_dirs=(), timeout=120, pass_env=(DSN_NAME,))
    rows = run_mutants(
        root,
        [FLIP],
        [CORE_TEST],
        extra_dirs=(),
        timeout=120,
        pass_env=(DSN_NAME,),
        throwaway_hosts=FAKE_HOSTS,
    )
    assert _short(rows) == [("flip", Verdict.KILLED, True)], rows
    monkeypatch.setenv(DSN_NAME, "postgresql://postgres@localhost:5432/postgres")
    rows = run_mutants(root, [FLIP], [CORE_TEST], extra_dirs=(), timeout=120, pass_env=(DSN_NAME,))
    assert _short(rows) == [("flip", Verdict.KILLED, True)], "the address of CI was refused"


_CI_FILE = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"


@pytest.mark.skipif(
    not _CI_FILE.is_file(), reason="the workflow file is not in a mutant copy of the tree"
)
def test_the_address_of_ci_in_the_workflow_file_is_the_one_the_check_accepts():
    text = _CI_FILE.read_text(encoding="utf-8")
    values = set(re.findall(r"HADAVIN_TEST_PG_DSN:\s*(\S+)", text))
    assert values, "no address in ci.yml"
    for value in values:
        mr._refuse_unsafe_address(DSN_NAME, value, mr.THROWAWAY_HOSTS)


def test_no_name_that_is_not_set_is_checked(tmp_path, monkeypatch):
    monkeypatch.delenv(DSN_NAME, raising=False)
    root = _tree(tmp_path, {CORE_TEST: USES_GO})
    rows = run_mutants(root, [FLIP], [CORE_TEST], extra_dirs=(), timeout=120, pass_env=(DSN_NAME,))
    assert _short(rows) == [("flip", Verdict.KILLED, True)], rows


def test_the_grammar_reads_the_parts_that_the_address_check_uses():
    assert mr._address_fields("postgresql://u@Localhost:5432/app") == {
        "host": "localhost",
        "port": "5432",
        "dbname": "app",
    }
    assert mr._address_fields("hostaddr=127.0.0.1 host=H dbname=d") == {
        "hostaddr": "127.0.0.1",
        "host": "h",
        "dbname": "d",
    }, "a host name of a key=value address was not read in lower case"
    assert mr._address_fields("host=/var/Run dbname=d") == {"host": "/var/Run", "dbname": "d"}, (
        "a unix socket folder was not read as written"
    )
    assert mr._address_fields("postgres://[::1]/d") == {"host": "::1", "port": "", "dbname": "d"}
    assert mr._address_fields("host=::1 dbname=d") == {"host": "::1", "dbname": "d"}
    assert mr._address_fields("host=h dbname=d sslrootcert=x") is None
    assert mr._address_fields("") is None


# ---- the child environment: no variable of the database library but the one passed --------------------------------------------

SEES_NO_PG_VARIABLE = (
    "import os\nfrom pk.core import go\n\n"
    "def test_a():\n    assert go(True) is True\n"
    "    assert not [k for k in os.environ if k.startswith('PG')], 'the child got a PG variable'\n"
)


def test_no_variable_of_the_database_library_reaches_the_child(tmp_path, monkeypatch):
    names = (*mr.CHILD_ENV, *mr.CHILD_FIXED_ENV, *mr.PASS_ENV_ALLOWED)
    assert not [n for n in names if n.upper().startswith("PG")], (
        "a name of the child environment list starts with PG"
    )
    assert "HOME" in mr.CHILD_ENV, "HOME is no longer inherited: correct the docstring"
    for name, value in (("PGHOST", "db.example.org"), ("PGSERVICE", "prod"), ("PGPASSFILE", "/x")):
        monkeypatch.setenv(name, value)
    monkeypatch.setenv(DSN_NAME, f"host={FAKE_HOST} dbname=scratch")
    root = _tree(tmp_path, {CORE_TEST: SEES_NO_PG_VARIABLE})
    rows = _run(root, [FLIP], pass_env=(DSN_NAME,))  # a child that got one fails the baseline
    assert _short(rows) == [("flip", Verdict.KILLED, True)], rows


# ---- one run through the real address check, the real lock folder and the output allowlist -----------------------------------

RAISES_A_CLASS_OF_ITS_OWN = (
    "import os\nimport pytest\nfrom pk.core import go\n\n"
    "class LibraryError(Exception):\n    pass\n\n"
    f"@pytest.mark.parametrize('v', [os.environ[{DSN_NAME!r}]])\n"
    "def test_a(v):\n    if go(True) is not True:\n        raise LibraryError(v)\n"
)


@pytest.mark.skipif(os.name == "nt", reason="the lock folder checks are POSIX")
def test_one_run_goes_through_the_real_address_check_the_real_lock_folder_and_the_allowlist(
    _real_lock_dir, tmp_path, monkeypatch
):
    dsn, word = _secret_dsn()
    monkeypatch.setenv(DSN_NAME, dsn)
    root = _tree(tmp_path, {CORE_TEST: RAISES_A_CLASS_OF_ITS_OWN})
    checked = []
    real_check = mr._refuse_unsafe_address
    monkeypatch.setattr(
        mr, "_refuse_unsafe_address", lambda *a: checked.append(a[2]) or real_check(*a)
    )
    folder = _real_lock_dir / f"hadavin_mutation_locks_{os.getuid()}"
    during: list[list[str]] = []
    lines: dict[str, str] = {}
    crash = Mutant("flip", "src/pk/core.py", "return flag", "return not flag", "scratch")

    def run(**kw):
        return run_mutants(
            root, [crash], [CORE_TEST], extra_dirs=(), timeout=120, pass_env=(DSN_NAME,),
            first_lines=lines, on_result=lambda _row: during.append(sorted(os.listdir(folder))), **kw,
        )  # fmt: skip

    _must_raise(
        "the made-up host was accepted without being named",
        ValueError,
        run,
        match="host is not one of",
    )
    assert not folder.exists(), "a refused address still made the lock folder"
    rows = run(throwaway_hosts=FAKE_HOSTS)
    assert checked == [mr.THROWAWAY_HOSTS, FAKE_HOSTS], (
        f"the address check was not called with the caller's host list: {checked}"
    )
    assert stat.S_IMODE(folder.stat().st_mode) == 0o700, "the real lock folder is not private"
    assert during == [[_lock_name(f"{FAKE_HOST}\n\n\nscratch")]], (
        f"the lock file was not in the real lock folder while the mutant ran: {during}"
    )
    assert rows == [
        ("flip", Verdict.CRASH, "tests/test_core::test_a" + mr.PARAMETERS_HIDDEN, False)
    ]
    assert lines == {"flip": "[class not shown] [expect found] scratch"}, lines
    rows = run(throwaway_hosts=FAKE_HOSTS, shown_classes=("LibraryError",))
    assert lines == {"flip": "LibraryError [expect found] scratch"}, lines
    assert word not in str(rows) + str(lines)


# ---- what a listed name switches on: the three cases of the variable -------------------------------------------------------

# (the variable) -> (skip check on, canary run, output replaced); "refused" = a ValueError before any run
THREE_CASES = {
    "listed, variable absent": (True, False, False),
    "listed, variable present but empty": "refused",
    "listed, variable present with a value": (True, True, True),
}
SKIPS_THEN_FAILS = (
    "import pytest\nfrom pk.core import go\n\n"
    "def test_a():\n    if go(False) is not False:\n        pytest.skip('skipped under the mutant')\n\n"
    "def test_b():\n    assert go(True) is True, 'the text of the child'\n"
)


@pytest.mark.parametrize("case", list(THREE_CASES))
def test_what_a_listed_name_switches_on_in_each_case_of_the_variable(case, tmp_path, monkeypatch):
    monkeypatch.delenv(DSN_NAME)
    if "empty" in case:
        monkeypatch.setenv(DSN_NAME, "")
    if "value" in case:
        monkeypatch.setenv(DSN_NAME, _secret_dsn()[0])
    root = _tree(tmp_path, {CORE_TEST: SKIPS_THEN_FAILS})
    runs = []
    real = mr._pytest
    monkeypatch.setattr(mr, "_pytest", lambda *a, **k: runs.append(a[2].name) or real(*a, **k))
    lines: dict[str, str] = {}
    fails = Mutant("fails", "src/pk/core.py", "return flag", "return not flag", "text of")
    try:
        rows = _run(root, [fails], pass_env=(DSN_NAME,), first_lines=lines)
    except ValueError as exc:
        assert THREE_CASES[case] == "refused" and "not in a shape" in str(exc), (case, exc)
        assert runs == [], f"a run started for a refused value: {runs}"
        return
    skip_check, canary, replaced = THREE_CASES[case]
    # under the mutant test_a skips and test_b fails: with the skip check on that is an error row, not a kill
    assert (rows[0][2] == "SKIPPED TESTS") == skip_check, f"the skip check ({case}): {rows}"
    assert ("again.xml" in runs) == canary, f"the canary run ({case}): {runs}"
    assert (lines["fails"] == "AssertionError") == replaced, f"the output ({case}): {lines}"
    assert ("the text of the child" in lines["fails"]) != replaced, f"the output ({case}): {lines}"


def test_the_three_cases_are_written_in_the_module_docstring():
    doc = " ".join((mr.__doc__ or "").split())
    for words in (
        "listed, variable absent",
        "listed, variable present but empty",
        "listed, variable present with a value",
        "skip check",
        "canary run",
        "output replaced",
    ):
        assert words in doc, f"the module docstring does not hold the table words: {words}"


# ---- the order of the refusals is the order the docstring gives ---------------------------------------------------------------

# (the words of the docstring for the step, a text of its message), in the order of the code
REFUSAL_ORDER = (
    ("a name in ``pass_env`` that is not allowed", "pass_env may name only"),
    ("an entry of ``throwaway_hosts`` that is not exact", "exact host names"),
    ("an entry of ``shown_classes`` that is no class name", "shown_classes holds"),
    ("a value longer than", "longer than"),
    ("a character that a print would change", "holds a quote mark"),
    ("an address outside the grammar", "not in a shape"),
    ("an address with no host", _NO_HOST),
    ("a host that is not listed", "host is not one of"),
    ("a second runner on the same address", "another mutation run"),
)


def test_the_refusals_come_in_the_order_the_docstring_gives(tmp_path, monkeypatch):
    doc = " ".join((mr.__doc__ or "").split())
    places = [doc.find(words) for words, _message in REFUSAL_ORDER]
    assert -1 not in places and places == sorted(places), (
        f"the docstring does not list the refusals in the order of the code: {places}"
    )
    root = _tree(tmp_path, {CORE_TEST: USES_GO})
    monkeypatch.setattr(mr, "PASS_ENV_ALLOWED", (DSN_NAME, "OTHER_NAME"))
    monkeypatch.delenv("OTHER_NAME", raising=False)
    good = f"host={FAKE_HOST} dbname=scratch"
    # each step: everything that an EARLIER step refuses is put right, everything a LATER step refuses is still wrong
    wrong = {
        "pass_env": (DSN_NAME, "NOT_ALLOWED"),
        "throwaway_hosts": ("*",),
        "shown_classes": ("not a name",),
    }
    right = {"pass_env": (DSN_NAME,), "throwaway_hosts": FAKE_HOSTS, "shown_classes": ()}
    values = (
        "'" + "x" * mr.MAX_VALUE_CHARS,  # too long, and a quote mark, and no address
        "'not an address",  # a quote mark, and no address
        "not an address",
        "dbname=scratch",  # in the grammar, no host
        "host=other.invalid dbname=scratch",  # a host, not listed
        good,
    )
    monkeypatch.setenv(DSN_NAME, values[0])
    keywords = dict(wrong)
    seen = []
    for step, name in enumerate(wrong):
        with pytest.raises(ValueError) as caught:
            _run(root, [FLIP], **keywords)
        seen.append(str(caught.value))
        keywords[name] = right[name]
        assert REFUSAL_ORDER[step][1] in seen[-1], (
            f"step {step + 1} was not the refusal the docstring gives ({REFUSAL_ORDER[step][0]}): {seen[-1][:80]}"
        )
    for step, value in enumerate(values[:-1], len(wrong)):
        monkeypatch.setenv(DSN_NAME, value)
        with pytest.raises(ValueError) as caught:
            _run(root, [FLIP], **keywords)
        assert REFUSAL_ORDER[step][1] in str(caught.value), (
            f"step {step + 1} was not the refusal the docstring gives ({REFUSAL_ORDER[step][0]}): {str(caught.value)[:80]}"
        )
    monkeypatch.setenv(DSN_NAME, good)
    with mr._one_run_per_database([good]):
        _must_raise(
            "the lock was not the last refusal",
            RuntimeError,
            _run,
            root,
            [FLIP],
            match=REFUSAL_ORDER[-1][1],
            **keywords,
        )
    assert _short(_run(root, [FLIP], **keywords)) == [("flip", Verdict.KILLED, True)]
