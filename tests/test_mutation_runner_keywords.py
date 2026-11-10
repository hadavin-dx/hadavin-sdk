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
import json
import os
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
    assert mr._masked("E   x == 'abc...def'", ("abcdefghijkl",)) == "E   x == 'abc...def'", (
        "a fragment shorter than the minimum was masked"
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


def test_a_fragment_of_exactly_the_minimum_length_is_masked_and_a_shorter_one_is_not():
    secret = "Qw7xK2mTp9" + "Zr4Vb8Nc3L"  # built from parts
    head6 = mr._masked(f"E x == '{secret[:6]}...zzz'", (secret,))
    assert secret[:6] not in head6, f"a 6-character head next to the dots was not masked: {head6}"
    tail6 = mr._masked(f"E x == 'zzz...{secret[-6:]}'", (secret,))
    assert secret[-6:] not in tail6, f"a 6-character tail next to the dots was not masked: {tail6}"
    short = mr._masked(f"E x == '{secret[:5]}...zzz'", (secret,))
    assert secret[:5] in short, f"a 5-character head was masked, below the minimum: {short}"


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
    "host=db.invalid user=svc password=" + 'Ab3"' + chr(233) + "Xy9Zq1"
)  # both a quote and a non-ASCII letter


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
    # found by the property test: cutting the short secret out first changed the text, and the tail of the long one no longer matched
    secret = "Hq4Zr8Wm2Tx5Lb" + "ZZZZZ" + "Kd7tavnQe3Rj9"
    shown = f"E   assert '{secret[:12]}...{secret[-13:]}' == 'other'"
    out = mr._masked(shown, (secret, "ta"))
    assert "vnQe3Rj9" not in out and "Hq4Zr8" not in out, (
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
    assert took < 5, f"the check of a hostile line took {took:.1f} seconds"
    assert mr._masked("E   x == 'abc...def'", secrets) == "E   x == 'abc...def'", (
        "an honest line with dots was replaced"
    )


def test_the_fragment_scan_agrees_with_the_plain_definition():
    """The scan was rewritten to be fast; it must still return the spans of the plain definition (every length from the largest down)."""
    rng = _Det(7)
    for _ in range(300):
        secret = "".join(rng.choice("abcd") for _ in range(rng.randint(7, 20)))
        text = "".join(rng.choice("abcd.") for _ in range(rng.randint(0, 60)))
        plain: list[tuple[int, int]] = []
        for at in range(len(text) - 2):
            if text[at : at + 3] != "...":
                continue
            start, end, top = at, at + 3, len(secret) - 1
            for k in range(min(top, start), 5, -1):
                if text[start - k : start] == secret[:k]:
                    plain.append((start - k, start))
                    break
            for k in range(min(top, len(text) - end), 5, -1):
                if text[end : end + k] == secret[-k:]:
                    plain.append((end, end + k))
                    break
        assert sorted(mr._fragment_spans(text, secret)) == sorted(plain), (
            f"the fast scan found other spans than the plain definition: {text!r} {secret!r}"
        )
    # the largest head and tail (one character short of the whole secret) at every length, which random text almost never hits
    for size in range(7, 21):
        secret = "".join("pqrstuvwxyz"[(i * 3 + size) % 11] for i in range(size))
        top = size - 1
        text = secret[:top] + "..." + secret[-top:]
        assert sorted(mr._fragment_spans(text, secret)) == [(0, top), (top + 3, len(text))], (
            f"the largest head and tail of a {size}-character secret were not both found: {text!r}"
        )


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


def test_a_lock_file_that_cannot_be_opened_is_a_clear_refusal(tmp_path):
    (
        tmp_path / _lock_name("x")
    ).mkdir()  # a folder in the place of the file: the open fails like a file of another user does
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
    with mr._one_run_per_database(["y"]):
        pass
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
    except (RuntimeError, OSError) as exc:
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
