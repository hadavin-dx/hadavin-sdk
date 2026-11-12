"""Round 18 groups 1 to 5: the refusal for a failed cloud sign-in (and for a refused connection) carries none of the error it
was made from.

Bug class: an error built INSIDE an `except` block keeps the handled error on `__context__`; `raise ... from None` only hides
it from the printed traceback (`__suppress_context__`), so a log handler that walks `__context__` (or `__cause__`) records
the SDK's or the driver's own words, which can hold an account name, a role name, a host or a user. Standard: Python
language reference, "The raise statement" (implicit chaining and `from None`). Fix at the choke point: the three places that
turn such an error into a refusal hold only the NAME of the error class, leave the `except` block, and raise from outside it
(`store/auth_aws.py`, `store/postgres.py` `connect` and `build`, `store/migrate.py` `_connected_before_commit`).

What the AST test below cannot see: an error raised by a helper that an `except` block calls, a logger of the SDK itself
that records the text before our code sees it, and the values held by the stack frames of the traceback. The behaviour
tests (a chain walk over every error the refusal keeps) cover the first of these.
"""

from __future__ import annotations

import ast
import json
import traceback
from pathlib import Path
from types import SimpleNamespace

import psycopg
import pytest

from hadavin_sdk import errors
from hadavin_sdk.store import postgres as pg
from hadavin_sdk.store.protocol import StoreUnavailable
from tests.test_migration_verify import _a_cloud_sdk_whose_token_request_fails

# Made-up words that stand for an account name (not secret-shaped).
WORDS = "made-up-account-words"
ROOT = Path(__file__).resolve().parents[1]


def everything_kept(err: BaseException) -> list[BaseException]:
    """`err` and every error reachable from it through `__cause__` and `__context__` (what a log handler could walk)."""
    seen: list[BaseException] = []
    todo = [err]
    while todo:
        e = todo.pop()
        if e is None or any(e is s for s in seen):
            continue
        seen.append(e)
        todo += [e.__cause__, e.__context__]
    return seen


def assert_no_channel(err: BaseException, *words: str) -> None:
    """The refusal holds no other error on any channel, and none of `words` is in anything it keeps or prints."""
    assert err.__cause__ is None, "the refusal keeps the error it was made from (`from <error>`)"
    assert err.__context__ is None, (
        "the refusal was raised inside an `except` block (`__context__` is set)"
    )
    assert err.__suppress_context__ is False, (
        "`from None` hides the error from the printed traceback only"
    )
    assert everything_kept(err) == [err]
    shown = "".join(traceback.format_exception(err)) + "".join(str(e) for e in everything_kept(err))
    for word in words:
        assert word not in shown, shown


def raised(call, kind: type[BaseException] = Exception) -> BaseException:
    """The error `call` raises (any `kind`), so that a test can say what it was with an `assert`; an error of another type
    that comes out raw is then a failed assertion with its type named, not a bare crash."""
    try:
        call()
    except kind as e:
        return e
    pytest.fail("nothing was raised")


DSN = "host=made-up.example dbname=made-up user=made-up"
TLS = {"sslmode": "verify-full", "sslrootcert": "/made/up/ca.pem"}


def no_connection(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("a connection was tried after the sign-in failed")

    monkeypatch.setattr(pg.psycopg, "connect", refuse)


ERRORS = {
    "runtime-error": lambda: RuntimeError(WORDS),
    "os-error": lambda: OSError(2, WORDS),
    "json-error": lambda: json.JSONDecodeError(WORDS, "{}", 0),
    "client-error": lambda: __import__("botocore.exceptions", fromlist=["ClientError"]).ClientError(
        {"Error": {"Code": "AccessDenied", "Message": WORDS}}, "GenerateDbAuthToken"
    ),
    "botocore-error": lambda: __import__(
        "botocore.exceptions", fromlist=["EndpointConnectionError"]
    ).EndpointConnectionError(endpoint_url=WORDS),
    "boto3-error": lambda: __import__("boto3.exceptions", fromlist=["Boto3Error"]).Boto3Error(
        WORDS
    ),
}


@pytest.mark.parametrize("step", ["client-is-built", "token-is-asked-for"])
@pytest.mark.parametrize("which", sorted(ERRORS))
def test_a_failed_sign_in_of_any_kind_leaves_no_trace_of_the_sdk_error(monkeypatch, which, step):
    """Round 18 groups 1 and 2: any error of either step of the sign-in (not two library types) becomes `SignInError`, a
    `ConfigError`, naming only the class, with no other error on `__context__` or `__cause__`, and no connection is tried.
    On aac26d60 the library types were converted but kept on `__context__`, and the other types came out raw (exit 3)."""
    error = ERRORS[which]()
    if step == "token-is-asked-for":
        _a_cloud_sdk_whose_token_request_fails(monkeypatch, error)
    else:
        import boto3

        def client(service, **kwargs):
            raise error

        monkeypatch.setattr(boto3, "client", client)
    no_connection(monkeypatch)
    err = raised(lambda: pg.connect(DSN, iam_auth=True, region="r", **TLS))
    assert isinstance(err, errors.SignInError), f"came out as {type(err).__name__}"
    assert isinstance(err, errors.ConfigError)
    assert type(error).__name__ in str(err), str(err)
    assert_no_channel(err, WORDS)


@pytest.mark.parametrize("step", ["client-is-built", "token-is-asked-for"])
@pytest.mark.parametrize("signal", [KeyboardInterrupt, SystemExit])
def test_an_interrupt_during_the_sign_in_is_not_turned_into_a_refusal(monkeypatch, signal, step):
    """Round 18 group 2: the conversion takes `Exception`, never `BaseException` (a Ctrl-C or an exit must still stop the
    process as itself). Control for the catch: passes on aac26d60 too (it caught two library types only)."""
    if step == "token-is-asked-for":
        _a_cloud_sdk_whose_token_request_fails(monkeypatch, signal())
    else:
        import boto3

        def client(service, **kwargs):
            raise signal()

        monkeypatch.setattr(boto3, "client", client)
    no_connection(monkeypatch)
    err = raised(lambda: pg.connect(DSN, iam_auth=True, region="r", **TLS), BaseException)
    assert type(err) is signal, f"came out as {type(err).__name__}"


def _a_password_source_that_is_recorded(monkeypatch):
    asked: list[tuple] = []
    monkeypatch.setattr(
        pg,
        "password_source",
        lambda iam, region: lambda host, port, user: asked.append((host, port, user)) or "made-up",
    )
    return asked


BAD_ADDRESSES = [
    ("host=made-up.example dbname=made-up", "no user"),
    ("dbname=made-up user=made-up", "no host"),
    ("host=made-up.example user=made-up port=abc", "a port that is not one number from 1 to 65535"),
    ("host=made-up.example user=made-up port=5432,5433", "a port that is not one number"),
    ("host=made-up.example user=made-up port=0", "a port that is not one number"),
    ("host=made-up.example user=made-up port=65536", "a port that is not one number"),
    ("host=made-up.example user=made-up port=+5432", "a port that is not one number"),
    ("host=made-up.example user=made-up port=1_000", "a port that is not one number"),
    (
        "host=made-up.example user=made-up port=٥٤٣٢",
        "a port that is not one number",
    ),  # digits of another script
    ("host=made-up.example,made-up.example user=made-up", "more than one host"),
]


@pytest.mark.parametrize(
    ("dsn", "named"),
    BAD_ADDRESSES,
    ids=[
        "no-user",
        "no-host",
        "port-abc",
        "port-list",
        "port-0",
        "port-65536",
        "port-sign",
        "port-underscore",
        "port-other-script",
        "two-hosts",
    ],
)
def test_an_iam_address_the_sign_in_cannot_be_asked_for_is_refused_by_name_before_any_connection(
    monkeypatch, dsn, named
):
    """Round 18 groups 3, 4, 5: the part that is wrong is named in plain words (no Python exception name), the sentence ends
    with a full stop, nothing is caught (so no other error is kept), the sign-in is not asked and no connection is tried.
    On aac26d60 a port that is not a number or a list of ports gave `ValueError` text and a missing part gave `KeyError`."""
    asked = _a_password_source_that_is_recorded(monkeypatch)
    no_connection(monkeypatch)
    err = raised(lambda: pg.connect(dsn, iam_auth=True, region="r", **TLS))
    assert isinstance(err, errors.SignInError), f"came out as {type(err).__name__}"
    text = str(err)
    assert named in text and text.endswith("."), text
    assert "Error" not in text, text
    assert asked == [], "the sign-in was asked for although the address cannot be signed in for"
    assert_no_channel(err)


@pytest.mark.parametrize(
    ("dsn", "asked_for"),
    [
        ("host=made-up.example user=made-up", ("made-up.example", 5432, "made-up")),
        ("host=made-up.example user=made-up port=1", ("made-up.example", 1, "made-up")),
        ("host=made-up.example user=made-up port=65535", ("made-up.example", 65535, "made-up")),
    ],
    ids=["default-port", "port-1", "port-65535"],
)
def test_an_iam_address_with_a_host_a_user_and_a_plain_port_asks_for_the_sign_in(
    monkeypatch, dsn, asked_for
):
    """Control for the allow list of the port (the ends of the range and the default): the sign-in is asked for with the
    numbers read from the address. Passes on aac26d60 (the same behaviour for good addresses)."""
    asked = _a_password_source_that_is_recorded(monkeypatch)

    class Conn:
        def execute(self, *args, **kwargs):
            return None

    monkeypatch.setattr(pg.psycopg, "connect", lambda *a, **k: Conn())
    pg.connect(dsn, iam_auth=True, region="r", **TLS)
    assert asked == [asked_for]


@pytest.mark.parametrize(
    "close_error", [psycopg.OperationalError, OSError, BrokenPipeError, RuntimeError]
)
def test_a_close_that_fails_with_any_error_does_not_hide_the_first_error(monkeypatch, close_error):
    """Round 18 group 4: the close of a half-made connection ignores any error, not only the driver's. On aac26d60 an
    `OSError` of `close` replaced the first error. Killed by V135."""
    tries = []

    class Broken:
        def execute(self, statement, *args, **kwargs):
            raise psycopg.OperationalError("made-up: the setup statement failed")

        def close(self):
            tries.append(1)
            raise close_error("made-up: the close failed too")

    monkeypatch.setattr(pg.psycopg, "connect", lambda *args, **kwargs: Broken())
    err = raised(lambda: pg.connect("host=made-up dbname=made-up", sslmode="disable"))
    assert isinstance(err, psycopg.OperationalError), f"came out as {type(err).__name__}"
    assert "the setup statement failed" in str(err), str(err)
    assert tries == [1]


def test_a_store_that_cannot_connect_names_only_the_class_and_keeps_no_driver_error(monkeypatch):
    """Round 18 group 1 (the sibling in `postgres.build`, same class): `StoreUnavailable` was raised `from None` inside the
    `except` block, so the driver error (which can hold the host and the user) stayed on `__context__`."""
    named = {"dsn_secret_name": "made-up"}  # a name of a stored value, not a value
    settings = SimpleNamespace(
        iam_auth=False,
        region=None,
        sslmode=None,
        sslrootcert=None,
        sslrootcert_secret_name=None,
        **named,
    )
    deps = SimpleNamespace(resolve=lambda name: DSN)

    def refuse(*args, **kwargs):
        raise psycopg.OperationalError(WORDS)

    monkeypatch.setattr(pg, "connect", refuse)
    err = raised(lambda: pg.build(settings, deps))
    assert isinstance(err, StoreUnavailable), f"came out as {type(err).__name__}"
    assert "OperationalError" in str(err) and WORDS not in str(err)
    assert_no_channel(err, WORDS)


def test_a_failed_sign_in_while_the_store_is_built_is_the_sign_in_refusal_and_not_store_unavailable(
    monkeypatch,
):
    """Round 18 group 5 (the runtime build path, `postgres.build`): the sign-in refusal is a `ConfigError` that passes through
    (a login or a region that is wrong is a configuration fault, not an unavailable store), with no channel and no
    connection tried. On aac26d60 the sign-in error stayed on `__context__` of the refusal."""
    named = {"dsn_secret_name": "made-up"}  # a name of a stored value, not a value
    settings = SimpleNamespace(
        iam_auth=True,
        region="r",
        sslmode="verify-full",
        sslrootcert="/made/up/ca.pem",
        sslrootcert_secret_name=None,
        **named,
    )
    deps = SimpleNamespace(resolve=lambda name: DSN)
    _a_cloud_sdk_whose_token_request_fails(monkeypatch, RuntimeError(WORDS))
    no_connection(monkeypatch)
    err = raised(lambda: pg.build(settings, deps))
    assert isinstance(err, errors.SignInError), f"came out as {type(err).__name__}"
    assert not isinstance(err, StoreUnavailable)
    assert_no_channel(err, WORDS)


# --- what an AST scan can see: no new error is raised inside an `except` block of the three choke points ----------------
CHOKE_POINTS = {
    "src/hadavin_sdk/store/auth_aws.py": {"rds_iam", "password", "_refused"},
    "src/hadavin_sdk/store/postgres.py": {"connect", "build", "_plain_port"},
    "src/hadavin_sdk/store/migrate.py": {"_connected_before_commit"},
}


def raises_inside_handlers(source: str, functions: set[str]) -> list[str]:
    """`file:line` of every `raise <something>` inside an `except` block of the named functions (a bare `raise`, which
    passes the same error on, is not a new error)."""
    found = []
    tree = ast.parse(source)
    for fn in ast.walk(tree):
        if isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef) and fn.name in functions:
            for handler in (n for n in ast.walk(fn) if isinstance(n, ast.ExceptHandler)):
                found += [
                    f"{fn.name}:{n.lineno}"
                    for n in ast.walk(handler)
                    if isinstance(n, ast.Raise) and n.exc is not None
                ]
    return found


@pytest.mark.parametrize("path", sorted(CHOKE_POINTS))
def test_the_choke_points_raise_no_new_error_inside_an_except_block(path):
    """Round 18 group 1: the structure that keeps `__context__` empty, checked in the source. A `raise` of a new error inside
    an `except` block of these functions fails here. Killed by V130, V131 and V134 (a raise put back inside the block)."""
    text = (ROOT / path).read_text(encoding="utf-8")
    assert raises_inside_handlers(text, CHOKE_POINTS[path]) == []


def test_the_ast_scan_finds_a_raise_inside_a_handler_and_ignores_a_bare_raise():
    """The scan itself (a planted source): finds `raise E from None` in a handler, ignores `raise` alone."""
    source = (
        "def f():\n    try:\n        pass\n    except Exception:\n        raise ValueError('x') from None\n"
        "def g():\n    try:\n        pass\n    except Exception:\n        raise\n"
    )
    assert raises_inside_handlers(source, {"f", "g"}) == ["f:5"]
