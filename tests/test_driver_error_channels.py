"""Round 19 groups 2, 3 and 8: which refusal may keep the error it was made from, a sign-in failure that a second try can
cure, and a DSN that cannot be read. No server is needed here (the real-server halves are in
`tests/test_migration_verify_pg.py`).

Bug classes and standards:
- Group 2: a refusal raised inside an `except` block keeps the handled error on `__context__`, and `raise ... from e` keeps it
  on `__cause__` (Python language reference, "The raise statement"). The driver's text can hold a DETAIL line with a row value
  and the connection words. The rule is written once (CHANGELOG, "Which refusals may keep the error they were made from") and
  enforced at the one exit of `migrate` (`_keeps_no_driver_error`); the AST scan below lists every `raise ... from` of
  `migrate.py`, so a new one is a decision and not an accident.
- Group 3: a retryable fault must stay retryable (exit 4, "run again"), not become "the configuration is wrong" (exit 2).
- Group 8: the driver's error for a DSN that cannot be read QUOTES a word of the DSN (libpq `PQconninfoParse`).

What the AST scan cannot see: a `raise` in a helper that a handler calls, a logger that records the text before our code sees
it, the values held by the stack frames of a traceback, and a refusal built from `str(e)` by hand (the behaviour tests walk
the chains of the errors that come out; they do not read the log of another library).
"""

from __future__ import annotations

import ast
import traceback
from pathlib import Path
from types import SimpleNamespace

import psycopg
import pytest
from psycopg import errors as pge

from hadavin_sdk import cli, errors
from hadavin_sdk.errors import AppliedNotVerifiedError, ConfigError, SignInError
from hadavin_sdk.store import auth_aws
from hadavin_sdk.store import migrate as mig
from hadavin_sdk.store import postgres as pg
from hadavin_sdk.store.protocol import StoreUnavailable
from tests.fixtures.channels import assert_no_channel, everything_kept
from tests.fixtures.cloud_sdk import a_cloud_sdk_whose_token_request_fails

WORDS = "made-up-detail-words"  # stands for a row value or a host name (not secret-shaped)
ROOT = Path(__file__).resolve().parents[1]


# --- group 2: the one exit of `migrate` -------------------------------------------------------------------------------
def _driver_errors():
    return {
        "operational": lambda: psycopg.OperationalError(WORDS),
        "interface": lambda: psycopg.InterfaceError(WORDS),
        "programming": lambda: psycopg.ProgrammingError(WORDS),
        "unique-violation": lambda: pge.UniqueViolation(WORDS),
        "check-violation": lambda: pge.CheckViolation(WORDS),
        "lost-connection": lambda: pge.AdminShutdown(WORDS),
    }


def _refusals():
    """The ways the code of `migrate` turns an error into another one: `from e`, a raise inside the handler with no `from`,
    and a refusal made from a refusal that was made from the driver error."""

    def explicit(e, make):
        try:
            raise e
        except psycopg.Error as caught:
            raise make() from caught

    def implicit(e, make):
        try:
            raise e
        except psycopg.Error:
            raise make()  # noqa: B904 - the point of the test: the implicit chain

    def nested(e, make):
        try:
            try:
                raise e
            except psycopg.Error as caught:
                raise ConfigError("the inner refusal") from caught
        except ConfigError as inner:
            raise make() from inner

    return {"from-e": explicit, "implicit": implicit, "nested": nested}


MAKERS = {
    "config": lambda: ConfigError(
        "migrate stopped and kept nothing: made-up words of the refusal."
    ),
    "applied-not-verified": lambda: AppliedNotVerifiedError("the files are applied", applied=[]),
}


@pytest.mark.parametrize("maker", sorted(MAKERS))
@pytest.mark.parametrize("how", sorted(_refusals()))
@pytest.mark.parametrize("which", sorted(_driver_errors()))
def test_a_refusal_made_from_a_driver_error_keeps_it_on_no_channel(which, how, maker):
    """Round 19 group 2: whatever way a refusal was made from a driver error (`from e`, inside the handler, through another
    refusal), what `migrate` raises holds no driver error on `__cause__` or `__context__`, and neither the traceback nor
    anything it keeps holds the driver's words. On 6a25ae5d the driver error was kept on both channels."""

    @mig._keeps_no_driver_error
    def run():
        _refusals()[how](_driver_errors()[which](), MAKERS[maker])

    with pytest.raises(Exception) as seen:
        run()
    assert type(seen.value).__name__ in {"ConfigError", "AppliedNotVerifiedError"}, type(seen.value)
    assert_no_channel(seen.value, WORDS)
    assert everything_kept(seen.value) == [seen.value]


@pytest.mark.parametrize("limit", [pge.LockNotAvailable, pge.QueryCanceled])
def test_a_lock_wait_or_a_statement_limit_is_still_kept_as_the_cause(limit):
    """The one error the rule keeps: its words hold no row value, and `tests/test_migration_postgres.py` pins it (a person who
    debugs a refused run wants to see which limit it was). The test fails if the rule drops everything."""

    @mig._keeps_no_driver_error
    def run():
        try:
            raise limit("made-up: the limit was reached")
        except psycopg.Error as e:
            raise ConfigError("migrate stopped: a limit was reached") from e

    with pytest.raises(ConfigError) as seen:
        run()
    assert isinstance(seen.value.__cause__, limit)


def test_an_error_that_is_not_a_driver_error_keeps_its_cause():
    """A cause that is not a driver error (the unreadable list of released files: an `OSError` whose text is already in the
    message) is not touched; the rule is about driver words."""

    @mig._keeps_no_driver_error
    def run():
        try:
            raise OSError(2, "made-up: no such file")
        except OSError as e:
            raise ConfigError(f"the list cannot be read: {e}") from e

    with pytest.raises(ConfigError) as seen:
        run()
    assert isinstance(seen.value.__cause__, OSError)


def test_a_chain_that_holds_a_limit_error_and_another_driver_error_keeps_neither():
    """A refusal that has a lock-wait error on one channel and a row-value error behind it loses both (the row value must
    not travel because a harmless error sits next to it)."""

    @mig._keeps_no_driver_error
    def run():
        try:
            try:
                raise pge.UniqueViolation(WORDS)
            except psycopg.Error:
                raise pge.LockNotAvailable("made-up: waited too long")  # noqa: B904
        except psycopg.Error as e:
            raise ConfigError("migrate stopped") from e

    with pytest.raises(ConfigError) as seen:
        run()
    assert_no_channel(seen.value, WORDS)


def test_a_raw_driver_error_of_a_migration_file_passes_through_unchanged():
    """A file's own failure is passed on as it is (its own text is the message, on purpose; `migrate` raises it with a bare
    `raise`), and so is an interrupt."""
    first = pge.UniqueViolation(WORDS)

    @mig._keeps_no_driver_error
    def run():
        raise first

    with pytest.raises(pge.UniqueViolation) as seen:
        run()
    assert seen.value is first

    @mig._keeps_no_driver_error
    def chained():
        try:
            raise pge.OperationalError("made-up: the first")
        except psycopg.Error as e:
            raise pge.UniqueViolation(WORDS) from e

    with pytest.raises(pge.UniqueViolation) as chain_seen:
        chained()
    assert isinstance(chain_seen.value.__cause__, pge.OperationalError), (
        "the driver's own error is passed on as it is, with what it holds"
    )

    @mig._keeps_no_driver_error
    def stop():
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        stop()


def test_migrate_is_wrapped_and_keeps_its_signature_and_its_text():
    """The public function is the guarded one; the unguarded body is `__wrapped__` (the per-site tests call that one, so
    that the guard cannot hide a site that has gone back to chaining)."""
    assert hasattr(mig.migrate, "__wrapped__")
    assert mig.migrate.__name__ == "migrate" and "Apply pending migrations" in (
        mig.migrate.__doc__ or ""
    )


# --- group 2: every `raise ... from` of migrate.py is a decision ---------------------------------------------------------
# (function, the text of the raised expression up to its first bracket) -> why that site may name a cause. A site whose
# cause can be a driver error is allowed ONLY because `_keeps_no_driver_error` drops that error at the one exit; a limit
# error is the one driver error that stays.
ALLOWED_FROM = {
    (
        "_released_manifest",
        "ConfigError",
    ): "the cause is an unreadable file (`OSError`/`ValueError`); its text is in the message",
    ("_trigger_changes", "ConfigError"): "same: an unreadable list of allowed trigger changes",
    (
        "_recheck_roles",
        "ConfigError",
    ): "the cause is a refusal of the runner itself, not a driver error",
}


def raises_with_cause(source: str) -> list[tuple[str, str, int]]:
    """(function, expression head, line) of every `raise X from <name>` in `source` (a `from None` is a different thing and
    is not listed: it keeps `__context__`, which the exit also clears, and it is not a decision about a cause)."""
    found = []
    tree = ast.parse(source)
    for fn in ast.walk(tree):
        if not isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        for node in ast.walk(fn):
            if isinstance(node, ast.Raise) and node.exc is not None and node.cause is not None:
                if isinstance(node.cause, ast.Constant) and node.cause.value is None:
                    continue
                head = node.exc
                if isinstance(head, ast.Call):
                    head = head.func
                found.append((fn.name, ast.unparse(head), node.lineno))
    return found


def test_the_scan_of_raise_from_finds_a_planted_site_and_skips_from_none():
    source = (
        "def f():\n    try:\n        pass\n    except Exception as e:\n        raise ValueError('x') from e\n"
        "def g():\n    try:\n        pass\n    except Exception:\n        raise ValueError('x') from None\n"
    )
    assert raises_with_cause(source) == [("f", "ValueError", 5)]


def test_every_raise_from_of_migrate_is_on_the_written_list_or_is_one_of_the_guarded_driver_sites():
    """Round 19 group 2: the sites that chain a cause are listed with a reason, so a new `raise ... from e` is a decision
    (written in the CHANGELOG list) and not an accident. The driver-error sites of `migrate()` are all behind
    `_keeps_no_driver_error`; they are counted here by function, so a site added to another function fails this test."""
    text = (ROOT / "src/hadavin_sdk/store/migrate.py").read_text(encoding="utf-8")
    sites = raises_with_cause(text)
    by_function: dict[str, list[str]] = {}
    for fn, head, _line in sites:
        by_function.setdefault(fn, []).append(head)
    # the guarded driver sites: everything inside the body of `migrate` and the two statement-time helpers it calls
    guarded = {"migrate": 8, "_check_could_not_run": 2}
    unlisted = {
        fn: heads
        for fn, heads in by_function.items()
        if fn not in guarded and not any(fn == f for (f, _h) in ALLOWED_FROM)
    }
    assert unlisted == {}, f"a raise ... from that is not on the written list: {unlisted}"
    for fn, n in guarded.items():
        assert len(by_function.get(fn, [])) == n, (fn, by_function.get(fn))


def test_the_text_of_the_written_rule_is_in_the_changelog():
    """The rule is written once (r19 group 2). The words are the ones this file and `_keeps_no_driver_error` use."""
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "Which refusals may keep the error they were made from" in changelog
    assert "_keeps_no_driver_error" in changelog


# --- group 3: a sign-in failure that a second try can cure -----------------------------------------------------------------
def _client_error(code):
    from botocore.exceptions import ClientError

    return ClientError({"Error": {"Code": code, "Message": WORDS}}, "GenerateDbAuthToken")


TRANSIENT = {
    "os-error": lambda: OSError(2, WORDS),
    "timeout": lambda: TimeoutError(WORDS),
    "connection-reset": lambda: ConnectionResetError(WORDS),
    "throttled": lambda: _client_error("ThrottlingException"),
    "throttling-short": lambda: _client_error("Throttling"),
    "request-limit": lambda: _client_error("RequestLimitExceeded"),
    "endpoint": lambda: __import__("botocore.exceptions", fromlist=["x"]).EndpointConnectionError(
        endpoint_url=WORDS
    ),
    "connect-timeout": lambda: __import__(
        "botocore.exceptions", fromlist=["x"]
    ).ConnectTimeoutError(endpoint_url=WORDS),
    "read-timeout": lambda: __import__("botocore.exceptions", fromlist=["x"]).ReadTimeoutError(
        endpoint_url=WORDS
    ),
    "metadata": lambda: __import__("botocore.exceptions", fromlist=["x"]).MetadataRetrievalError(
        error_msg=WORDS
    ),
}
PERMANENT = {
    "runtime-error": lambda: RuntimeError(WORDS),
    "no-credentials": lambda: __import__(
        "botocore.exceptions", fromlist=["x"]
    ).NoCredentialsError(),
    "access-denied": lambda: _client_error("AccessDenied"),
    "unknown-code": lambda: _client_error("MadeUpCode"),
    "no-code": lambda: __import__("botocore.exceptions", fromlist=["x"]).ClientError({}, "Op"),
    "json": lambda: ValueError(WORDS),
}


@pytest.mark.parametrize("which", sorted(TRANSIENT))
def test_the_classifier_calls_a_timeout_a_lost_network_or_a_throttle_transient(which):
    assert auth_aws.is_transient(TRANSIENT[which]()) is True


@pytest.mark.parametrize("which", sorted(PERMANENT))
def test_the_classifier_does_not_call_a_missing_login_or_a_refusal_transient(which):
    assert auth_aws.is_transient(PERMANENT[which]()) is False


def _iam_settings():
    named = {"dsn_secret_name": "made-up"}  # a name of a stored value, not a value
    return SimpleNamespace(
        iam_auth=True,
        region="r",
        sslmode="verify-full",
        sslrootcert="/made/up/ca.pem",
        sslrootcert_secret_name=None,
        **named,
    )


DSN = "host=made-up.example dbname=made-up user=made-up"
DEPS = SimpleNamespace(resolve=lambda name: DSN)


@pytest.mark.parametrize("which", sorted(TRANSIENT))
def test_a_transient_sign_in_failure_while_the_store_is_built_is_store_unavailable_by_class_name(
    monkeypatch, which
):
    """Round 19 group 3: a timeout, a lost network or a throttled request in the token request is `StoreUnavailable` (the
    store cannot be reached: exit 4, run again), naming only the class, with no channel and no connection tried. On 6a25ae5d
    it was a `SignInError`, a `ConfigError` (exit 2)."""
    error = TRANSIENT[which]()
    a_cloud_sdk_whose_token_request_fails(monkeypatch, error)

    def no_connection(*args, **kwargs):
        raise AssertionError("a connection was tried after the sign-in failed")

    monkeypatch.setattr(pg.psycopg, "connect", no_connection)
    with pytest.raises(Exception) as seen:
        pg.build(_iam_settings(), DEPS)
    assert isinstance(seen.value, StoreUnavailable), f"came out as {type(seen.value).__name__}"
    assert str(seen.value) == f"store postgres: cannot connect ({type(error).__name__})"
    assert_no_channel(seen.value, WORDS)


@pytest.mark.parametrize("which", sorted(PERMANENT))
def test_a_sign_in_failure_that_a_second_try_cannot_cure_stays_the_refusal_of_exit_2(
    monkeypatch, which
):
    """The other half: a missing login, a refused request and an unknown error stay `SignInError` (a `ConfigError`), not
    `StoreUnavailable`, so that "run again" is not said for a wrong configuration."""
    a_cloud_sdk_whose_token_request_fails(monkeypatch, PERMANENT[which]())
    with pytest.raises(Exception) as seen:
        pg.build(_iam_settings(), DEPS)
    assert isinstance(seen.value, SignInError), f"came out as {type(seen.value).__name__}"
    assert not isinstance(seen.value, StoreUnavailable)
    assert_no_channel(seen.value, WORDS)


def test_a_sign_in_error_built_by_hand_is_not_transient_unless_it_says_so():
    assert SignInError("x").transient is False and SignInError("x").kind == ""
    assert errors.SignInError("x", kind="K", transient=True).transient is True


def _use_iam_store(cfg_dir):
    import yaml

    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["backends"]["store"] = {
        "kind": "postgres",
        "dsn_secret_name": "pg-dsn",
        "iam_auth": True,
        "region": "r",
        "sslmode": "verify-full",
        "sslrootcert": "/made/up/ca.pem",
    }
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def _fake_dsn_secret(monkeypatch):
    from hadavin_sdk.actions.secrets import FakeSecretProvider

    monkeypatch.setattr(
        "hadavin_sdk.backends.builtin.fake_secrets",
        lambda settings, deps: FakeSecretProvider({"pg-dsn": DSN}),
    )


@pytest.mark.parametrize("action", ["stop", "reset"])
@pytest.mark.parametrize("which", ["os-error", "throttled", "metadata"])
def test_the_kill_switch_says_not_set_run_again_exit_4_for_a_transient_sign_in_failure(
    cfg_dir, monkeypatch, capsys, action, which
):
    """Round 19 group 3, the kill switch path of `cli.py`: "kill switch NOT set ... Nothing was changed ... run the same
    command again" and exit 4 (on 6a25ae5d: `refused`, exit 2)."""
    _use_iam_store(cfg_dir)
    _fake_dsn_secret(monkeypatch)
    a_cloud_sdk_whose_token_request_fails(monkeypatch, TRANSIENT[which]())
    assert cli.main(["--config", str(cfg_dir), "limits", action, "--by", "user:a"]) == 4
    err = capsys.readouterr().err
    assert "kill switch NOT" in err and "Nothing was changed" in err, err
    assert WORDS not in err


@pytest.mark.parametrize("action", ["stop", "reset"])
def test_the_kill_switch_keeps_exit_2_for_a_sign_in_failure_that_is_not_transient(
    cfg_dir, monkeypatch, capsys, action
):
    _use_iam_store(cfg_dir)
    _fake_dsn_secret(monkeypatch)
    a_cloud_sdk_whose_token_request_fails(monkeypatch, RuntimeError(WORDS))
    assert cli.main(["--config", str(cfg_dir), "limits", action, "--by", "user:a"]) == 2
    err = capsys.readouterr().err
    assert "kill switch NOT" not in err and WORDS not in err, err


# --- group 8: a DSN that cannot be read ------------------------------------------------------------------------------------
BAD_DSNS = {
    "word-without-equals": f"host=made-up.example user=made-up {WORDS}",
    "unterminated-quote": f"host=made-up.example password='{WORDS}",
    "empty-option": f"host=made-up.example =x {WORDS}",
    "option-without-value": f"host=made-up.example {WORDS}",
}


@pytest.mark.parametrize("which", sorted(BAD_DSNS))
def test_the_driver_does_quote_a_word_of_a_dsn_it_cannot_read(which):
    """The reason for the fix, measured: the driver's own error for these DSNs holds a word of the DSN. A control (this test
    passes on the old code too: it tests the driver, not our code); at least one of the four must quote the words, or the
    class would not exist."""
    from psycopg.conninfo import conninfo_to_dict

    try:
        conninfo_to_dict(BAD_DSNS[which])
    except Exception as e:  # noqa: BLE001 - the driver's own error, read for its text
        quoted = WORDS in str(e)
    else:
        pytest.fail("the driver read a DSN that this test says it cannot")
    if which in {"word-without-equals", "option-without-value"}:
        assert quoted, "the driver no longer quotes the word: re-check the class"


@pytest.mark.parametrize("which", sorted(BAD_DSNS))
def test_a_dsn_that_cannot_be_read_is_a_plain_refusal_by_class_name_on_every_path(
    monkeypatch, which
):
    """Round 19 group 8: `dsn_parts`, `tls_mode`, `connect` and `build` (iam and not) refuse it with a `ConfigError` that
    names the class only and keeps no error on any channel; no connection is tried. On 6a25ae5d the driver's error came out
    raw with a word of the DSN in its text."""

    def no_connection(*args, **kwargs):
        raise AssertionError("a connection was tried with a DSN that cannot be read")

    monkeypatch.setattr(pg.psycopg, "connect", no_connection)
    dsn = BAD_DSNS[which]
    calls = {
        "tls_mode": lambda: pg.tls_mode(dsn),
        "connect": lambda: pg.connect(dsn),
        "connect-iam": lambda: pg.connect(
            dsn, iam_auth=True, region="r", sslmode="verify-full", sslrootcert="/made/up/ca.pem"
        ),
        "build": lambda: pg.build(
            SimpleNamespace(**{**vars(_iam_settings()), "iam_auth": False}),
            SimpleNamespace(resolve=lambda name: dsn),
        ),
        "build-iam": lambda: pg.build(_iam_settings(), SimpleNamespace(resolve=lambda name: dsn)),
        "dsn_parts": lambda: pg.dsn_parts(dsn),
    }
    for name, call in calls.items():
        with pytest.raises(Exception) as seen:
            call()
        assert isinstance(seen.value, ConfigError), (
            f"{name}: came out as {type(seen.value).__name__}"
        )
        assert "ProgrammingError" in str(seen.value) and WORDS not in str(seen.value), (
            name,
            str(seen.value),
        )
        assert_no_channel(seen.value, WORDS)
        assert WORDS not in "".join(traceback.format_exception(seen.value)), name


def test_a_dsn_that_can_be_read_is_returned_as_the_driver_reads_it():
    """The control: a good DSN gives the driver's own parts (nothing is changed for it)."""
    assert pg.dsn_parts("host=a port=5433 user=b") == {"host": "a", "port": "5433", "user": "b"}
