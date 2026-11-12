"""Fail-before rows: R5 (hostile stand-ins end to end), R6 (message grammar), R8 (HTTPError.fp), R9 (hook removal),
R10 (retry_after), R17 (traceback).

This file is copied to the base and run there: it imports only names that exist on the base and reads every new attribute with
``getattr(err, name, None)``, so a failure on the base is an ASSERTION, not an import or attribute error.
"""

from __future__ import annotations

import email.message
import hashlib
import math
import re
import traceback
import urllib.error

import pytest

from hadavin_sdk.llm import ProviderError, ProviderExhausted
from hadavin_sdk.llm.retry import with_retry
from tests.provider_wire_helpers import CANARY, run_retry

X, P = ProviderExhausted, ProviderError


def attrs(err):
    return tuple(getattr(err, n, None) for n in ("retryable", "retry_count"))


def raising(exc: BaseException):
    def hook(*_a, **_k):
        raise exc

    return hook


def err_class(**props):
    """An Exception subclass with the given class attributes; a callable value becomes a property."""
    body = {k: (property(v) if callable(v) else v) for k, v in props.items()}
    return type("Hostile", (Exception,), body)


def _boom(kind=RuntimeError):
    def getter(self):
        raise kind("x")

    return getter


class _RaisesEq(Exception):
    def __eq__(self, other):
        raise RuntimeError("eq")

    __hash__ = Exception.__hash__


class _BadBool:
    def __bool__(self):
        raise RuntimeError("bool")


def _bedrock_error(**response):
    pytest.importorskip("botocore", reason="needs extra aws")
    import botocore.exceptions as be

    exc = be.ClientError({"Error": {"Code": "ValidationException", "Message": "m"}}, "Converse")
    exc.response = response.get("response", exc.response)
    return exc


# ---- R5: decision failures (each made the base escape raw) ------------------------------------------------------------

# (id, make-error, kind, extra with_retry kwargs) -> ProviderExhausted, Attempts 1, retryable None, retry_count 1, "after 1 attempts"
DECISION = [
    ("status_code-raises", lambda: err_class(status_code=_boom())(), "std", {}),
    ("status_code-recursion", lambda: err_class(status_code=_boom(RecursionError))(), "std", {}),
    ("reason-raises", lambda: err_class(reason=_boom())(), "std", {}),
    ("reason-eq-raises", lambda: _with_reason(_RaisesEq()), "std", {}),
    (
        "hook-raises",
        lambda: err_class(status_code=429)(),
        "std",
        {"retryable": raising(RuntimeError("hook"))},
    ),
    (
        "bool-raises-BN1c",
        lambda: err_class(status_code=429)(),
        "std",
        {"retryable": lambda e: _BadBool()},
    ),
    ("class-property-raises-BN4", lambda: err_class(__class__=_boom())(), "std", {}),
    ("bedrock-response-list", lambda: _bedrock_error(response=[1, 2]), "bedrock", {}),
    (
        "bedrock-error-str",
        lambda: _bedrock_error(response={"Error": "boom", "ResponseMetadata": {}}),
        "bedrock",
        {},
    ),
    (
        "bedrock-meta-list",
        lambda: _bedrock_error(response={"Error": {"Code": "X"}, "ResponseMetadata": []}),
        "bedrock",
        {},
    ),
]


def _with_reason(reason):
    exc = err_class()()
    exc.reason = reason
    return exc


@pytest.mark.parametrize("name,make,kind,extra", DECISION, ids=[d[0] for d in DECISION])
def test_r5_a_decision_that_crashed_is_the_billed_class(name, make, kind, extra):
    sleeps: list[float] = []
    err, calls = run_retry(make, kind, sleeps=sleeps, **extra)
    assert type(err) is X  # not retried, not a raw escape
    assert calls == 1 and sleeps == []
    assert attrs(err) == (None, 1)
    assert str(err).endswith(" after 1 attempts")


def test_r5_attempt_two_hook_failure_is_billed_with_attempt_two():
    seen = []

    def hook(exc):
        seen.append(1)
        if len(seen) == 2:
            raise RuntimeError("second")
        return True

    err, calls = run_retry(lambda: err_class(status_code=429)(), "std", retryable=hook)
    assert type(err) is X and calls == 2
    assert attrs(err) == (None, 2) and str(err).endswith(" after 2 attempts")


def test_r5_bn1a_a_truthy_hook_result_is_retried_to_exhaustion():
    err, calls = run_retry(lambda: err_class()(), "std", retryable=lambda e: 1)
    assert type(err) is X and calls == 3  # class and Attempts: regression pin
    assert attrs(err) == (True, 3) and str(err).endswith(" after 3 attempts")


def test_r5_bn1b_a_falsy_hook_result_is_refused_at_once():
    err, calls = run_retry(lambda: err_class(status_code=429)(), "std", retryable=lambda e: "")
    assert type(err) is P and calls == 1
    assert attrs(err) == (False, 1)


# ---- R5 facts-path cases (class and Attempts as on the base) ---------------------------------------------------------


def _anthropic_stand_in(status=403, **extra):
    anthropic = pytest.importorskip("anthropic", reason="needs extra anthropic")
    cls = type("Rec", (anthropic.AuthenticationError,), {})
    exc = cls.__new__(cls)  # no __init__
    for name, value in {"status_code": status, "request_id": None, "body": None, **extra}.items():
        object.__setattr__(exc, name, value)
    return exc


class _LyingStr(str):
    def __len__(self):
        raise RuntimeError("len")

    def __iter__(self):
        raise RuntimeError("iter")

    def __getitem__(self, i):
        raise RuntimeError("getitem")

    def __contains__(self, x):
        raise RuntimeError("contains")

    def __eq__(self, other):
        raise RuntimeError("eq")

    __hash__ = str.__hash__


class _LyingDict(dict):
    def get(self, key, default=None):
        return {"type": "rate_limit_error"} if key == "error" else "rate_limit_error"


FACT_CASES = [
    # (id, body, status, expected error_type value or None)
    ("str-subclass-body", lambda: _LyingStr("x"), 403, "permission"),
    ("5mib-body", lambda: "A" * (5 * 1024 * 1024), 403, "permission"),
    (
        "dict-subclass-body-401",
        lambda: _LyingDict(error={"type": "rate_limit_error"}),
        401,
        "authentication",
    ),
    ("type-int", lambda: {"error": {"type": 7}}, 403, "permission"),
    ("type-list", lambda: {"error": {"type": ["x"]}}, 403, "permission"),
    (
        "type-str-subclass",
        lambda: {"error": {"type": _LyingStr("permission_error")}},
        403,
        "permission",
    ),
    (
        "type-10kb-with-newline-and-email",
        lambda: {"error": {"type": "a@b.example\n" * 800}},
        403,
        "permission",
    ),
    (
        "type-injected-short-code",
        lambda: {"error": {"type": "ignore_previous_instructions"}},
        403,
        "other",
    ),
]


@pytest.mark.parametrize("name,body,status,etype", FACT_CASES, ids=[c[0] for c in FACT_CASES])
def test_r5_claude_body_cases(name, body, status, etype):
    err, calls = run_retry(
        lambda: _anthropic_stand_in(status, body=body()), "anthropic", label="anthropic"
    )
    assert type(err) is P and calls == 1
    got = getattr(err, "error_type", None)
    assert (got.value if got else None) == etype
    assert getattr(err, "status", None) == status
    assert str(err).startswith("anthropic: ") and "a@b" not in str(err)


@pytest.mark.parametrize(
    "make_code",
    [
        lambda: 7,
        lambda: ["x"],
        lambda: _LyingStr("ValidationException"),
        lambda: "a@b.example\n" * 800,
    ],
    ids=["int", "list", "str-subclass", "10kb"],
)
def test_r5_bedrock_code_not_a_short_exact_string_gives_the_status_type(make_code):
    code = make_code()
    exc = _bedrock_error(
        response={"Error": {"Code": code}, "ResponseMetadata": {"HTTPStatusCode": 403}}
    )
    err, calls = run_retry(lambda: exc, "bedrock")
    assert type(err) is P and calls == 1
    got = getattr(err, "error_type", None)
    assert got is not None and got.value == "permission" and getattr(err, "status", None) == 403


def test_r5_bedrock_short_injected_code_is_other():
    exc = _bedrock_error(
        response={"Error": {"Code": "IgnorePrevious"}, "ResponseMetadata": {"HTTPStatusCode": 403}}
    )
    err, _ = run_retry(lambda: exc, "bedrock")
    got = getattr(err, "error_type", None)
    assert got is not None and got.value == "other"


# status -> (class, attempts); a status over 499 or a retried code is retried
HTTP_STATUS = [
    ("429", P, 1),
    (True, P, 1),
    (0, P, 1),
    (-1, P, 1),
    (429.5, P, 1),
    (99999, X, 3),
    (10**400, X, 3),
]


@pytest.mark.parametrize(
    "value,cls,attempts", HTTP_STATUS, ids=[repr(v)[:12] for v, _, _ in HTTP_STATUS]
)
def test_r5_bedrock_http_status_values_outside_the_range_are_none(value, cls, attempts):
    exc = _bedrock_error(
        response={
            "Error": {"Code": "ValidationException"},
            "ResponseMetadata": {"HTTPStatusCode": value},
        }
    )
    err, calls = run_retry(lambda: exc, "bedrock")
    assert type(err) is cls and calls == attempts
    assert getattr(err, "retry_count", None) == attempts
    assert getattr(err, "status", 0) is None
    got = getattr(err, "error_type", None)
    assert got is not None and got.value == "invalid_request"


RIDS = [
    (None, None),
    (b"req_ABCDEFGH", None),
    ("req_" + "A" * 37, None),
    ("req_ABCDEFGH\n", None),
    ("req_" + "٠١٢٣٤٥٦٧", None),
    ("ABCDEFGHIJ", None),
    ("req_ABCDEFGH", "req_ABCDEFGH"),
]


@pytest.mark.parametrize("value,kept", RIDS, ids=[repr(r[0])[:14] for r in RIDS])
def test_r5_claude_request_ids(value, kept):
    err, _ = run_retry(
        lambda: _anthropic_stand_in(401, request_id=value), "anthropic", label="anthropic"
    )
    assert getattr(err, "request_id", "unset") == kept


def test_r5_bedrock_uuid_with_trailing_newline_is_refused():
    good = "0b1c2d3e-4f50-4a6b-8c7d-9e0f1a2b3c4d"
    for value, kept in ((good, good), (good + "\n", None)):
        exc = _bedrock_error(
            response={
                "Error": {"Code": "ValidationException"},
                "ResponseMetadata": {"HTTPStatusCode": 400, "RequestId": value},
            }
        )
        err, _ = run_retry(lambda exc=exc: exc, "bedrock")
        assert getattr(err, "request_id", "unset") == kept


def test_r5_hook_returning_the_wrong_type_or_a_subclass_or_raising_gives_no_facts():
    import importlib

    try:  # a new module: before the provider-error change the row fails on the assertion below, not on an import error
        facts_module = importlib.import_module("hadavin_sdk.llm.provider_facts")
    except ImportError:
        facts_module = None
    ProviderFacts = getattr(facts_module, "ProviderFacts", None)
    assert ProviderFacts is not None, "hadavin_sdk.llm.provider_facts.ProviderFacts does not exist"

    class Lying(ProviderFacts):
        pass

    for hook in (
        lambda e: "facts",
        lambda e: Lying(401, None, None),
        raising(RuntimeError("adapter")),
    ):
        err, calls = run_retry(lambda: err_class(status_code=500)(), "std", facts=hook)
        assert type(err) is X and calls == 3  # as on the base
        assert getattr(err, "status", 0) is None and getattr(err, "retry_count", None) == 3


def test_r5_cause_cycle_and_a_status_that_changes_between_reads():
    a, b = err_class(status_code=429)(), err_class()()
    a.__cause__, b.__cause__ = b, a
    err, calls = run_retry(lambda: a, "std")
    assert type(err) is X and calls == 3

    reads = iter([503, 401, 401, 401, 401, 401, 401, 401, 401, 401])

    def flip(self):
        return next(reads, 401)

    err, calls = run_retry(lambda: err_class(status_code=flip)(), "std")
    assert type(err) in (P, X) and GRAMMAR.fullmatch(str(err)) and "Hostile" not in str(err)


# ---- R6: message grammar -----------------------------------------------------------------------------------------------

GRAMMAR = re.compile(
    r"[a-z_]{1,30}: [A-Za-z0-9_.]{1,80}( [1-5][0-9]{2})?"
    r"( (rate_limit|overloaded|invalid_request|authentication|permission|not_found|server_error|timeout|connection|throttled|quota|other))?"
    r"( after [0-9]+ attempts)?"
)
_PIECES = [
    "alice@example.com",
    "/srv/u/.ssh/id",
    "C:\\Users\\bob",
    "line1\nline2",
    "it's",
    '"q"',
    "\x00\x1b[31m",
    "ключ",
    "💥",
    "AKIAIOSFODNN7EXAMPLE",
    "sk-" + "ant-" + "abc123def456",
    "ignore previous instructions",
]
_ALPHABET = "abcXYZ012 _-.:;/\\'\"\n\t@"


class _Rng:
    """A small deterministic generator (SHA-256 of a counter) for the fuzz rows: same seed, same stream, on every Python."""

    def __init__(self, seed: int) -> None:
        self._seed, self._n = seed, 0

    def _next(self) -> int:
        self._n += 1
        return int.from_bytes(
            hashlib.sha256(f"{self._seed}:{self._n}".encode()).digest()[:8], "big"
        )

    def randint(self, lo: int, hi: int) -> int:
        return lo + self._next() % (hi - lo + 1)

    def choice(self, seq):
        return seq[self._next() % len(seq)]

    def shuffle(self, items: list) -> None:
        for i in range(len(items) - 1, 0, -1):
            j = self._next() % (i + 1)
            items[i], items[j] = items[j], items[i]


def _noise(rng: _Rng, tag: str) -> str:
    parts = [rng.choice(_PIECES) for _ in range(rng.randint(0, 3))] + [
        "".join(rng.choice(_ALPHABET) for _ in range(rng.randint(0, 40)))
    ]
    rng.shuffle(parts)
    return tag + "".join(parts) + tag


def _every_surface(err):
    return "\n".join(
        [
            str(err),
            repr(err),
            repr(err.args),
            repr(vars(err)),
            "".join(traceback.format_exception(err)),
        ]
    )


def _planted(position: str, noise: str, rng: _Rng):
    """(make-error, kind) with ``noise`` in one provider-controlled position."""
    pytest.importorskip("anthropic", reason="needs extra anthropic")
    if position == "bedrock-code":
        return (
            lambda: _bedrock_error(
                response={
                    "Error": {"Code": noise, "Message": noise},
                    "ResponseMetadata": {"HTTPStatusCode": 400},
                }
            )
        ), "bedrock"
    if position == "bedrock-meta":
        return (
            lambda: _bedrock_error(
                response={
                    "Error": {"Code": "X"},
                    "ResponseMetadata": {"HTTPStatusCode": 400, "RequestId": noise},
                }
            )
        ), "bedrock"
    if position == "claude-type":
        return (
            lambda: _anthropic_stand_in(400, body={"error": {"type": noise, "message": noise}})
        ), "anthropic"
    if position == "claude-request-id":
        return (lambda: _anthropic_stand_in(400, request_id=noise)), "anthropic"
    if position == "claude-request-id-key-shaped":
        return (
            lambda: _anthropic_stand_in(400, request_id="req_" + "sk-ant-" + "a" * 20)
        ), "anthropic"
    if position == "reason":
        return (lambda: urllib.error.URLError(noise)), "std"
    if position == "http-reason-phrase":
        return (
            lambda: urllib.error.HTTPError(
                "http://127.0.0.1:1/", 400, noise, email.message.Message(), None
            )
        ), "std"
    if position == "class-name":
        return (lambda: type("x y@z" + noise, (Exception,), {})(noise)), "std"
    if position == "status":
        return (
            lambda: err_class(status_code=rng.choice([noise, 10**30, 99, 600, True, 418.5, -1]))()
        ), "std"
    raise AssertionError(position)


POSITIONS = [
    "bedrock-code",
    "bedrock-meta",
    "claude-type",
    "claude-request-id",
    "claude-request-id-key-shaped",
    "reason",
    "http-reason-phrase",
    "class-name",
    "status",
]


def test_r6_500_random_hostile_failures_keep_the_message_grammar():
    rng = _Rng(20261106)
    for i in range(500):
        position = POSITIONS[i % len(POSITIONS)]
        noise = _noise(rng, f"ZQ{i:04d}MARK")
        make, kind = _planted(position, noise, rng)
        err, _ = run_retry(make, kind, label=kind if kind != "std" else "openai_compat")
        assert type(err) in (P, X), (i, position)
        text = str(err)
        assert GRAMMAR.fullmatch(text), (i, position, text)
        assert f"ZQ{i:04d}MARK" not in _every_surface(err), (i, position)
        rid = getattr(err, "request_id", None)
        if position == "claude-request-id-key-shaped":
            assert rid is None


# ---- R8: HTTPError.fp is closed on every failed attempt ----------------------------------------------------------------


class RecFp:
    def __init__(self, close_raises: bool = False) -> None:
        self.closed, self.close_calls, self.reads, self.close_raises = False, 0, 0, close_raises

    def close(self):
        self.close_calls += 1
        self.closed = True
        if self.close_raises:
            raise RuntimeError("close")

    def _no_read(self, *a, **k):
        self.reads += 1
        raise RuntimeError("read")

    read = readline = __iter__ = _no_read


def _http_error(code, fp, retry_after=None):
    hdrs = email.message.Message()
    if retry_after is not None:
        hdrs["Retry-After"] = retry_after
    return urllib.error.HTTPError("http://127.0.0.1:1/", code, "m", hdrs, fp)


def test_r8a_refused_at_once_closes_the_connection_without_a_read():
    fp = RecFp()
    err, calls = run_retry(lambda: _http_error(401, fp), "std")
    assert type(err) is P and calls == 1
    assert fp.closed is True and fp.reads == 0


def test_r8b_three_retried_attempts_close_all_three():
    fps, errs = (
        [],
        [],
    )  # the errors are kept alive: a garbage-collected one would close its own file and hide a missed close

    def make():
        fps.append(RecFp())
        errs.append(_http_error(503, fps[-1]))
        return errs[-1]

    err, calls = run_retry(make, "std")
    assert type(err) is X and calls == 3 and len(fps) == 3
    assert [f.closed for f in fps] == [True, True, True] and sum(f.reads for f in fps) == 0


def test_r8c_a_close_that_raises_never_replaces_the_real_error():
    fp = RecFp(close_raises=True)
    err, calls = run_retry(lambda: _http_error(401, fp), "std")
    assert type(err) is P and calls == 1 and fp.close_calls == 1
    assert isinstance(err.__context__, urllib.error.HTTPError) and err.__context__.code == 401


@pytest.mark.parametrize("header,wait", [("5", 5.0), ("100", 8.0)])
def test_r8d_retry_after_of_a_closed_error_is_still_honoured(header, wait):
    fps, sleeps = [], []

    def make():
        fps.append(RecFp())
        return _http_error(503, fps[-1], header)

    run_retry(make, "std", sleeps=sleeps)
    assert sleeps == [wait, wait] and all(f.closed for f in fps)


# ---- R9: the detail hook is gone -----------------------------------------------------------------------------------------


def test_r9_detail_hook_is_removed_everywhere():
    import inspect

    assert "detail" not in inspect.signature(with_retry).parameters, (
        "with_retry still takes a detail hook"
    )
    from hadavin_sdk.llm import bedrock
    from hadavin_sdk.llm.common import NetworkLLM

    assert not hasattr(NetworkLLM, "detail")
    assert not hasattr(bedrock, "detail") and not hasattr(bedrock.BedrockLLM, "detail")


# ---- R10: retry_after --------------------------------------------------------------------------------------------------


class _RaisingHeaders:
    def get(self, *a, **k):
        raise RuntimeError("get")


@pytest.mark.parametrize(
    "make",
    [
        lambda: _with_attr(headers=_RaisingHeaders()),
        lambda: _with_attr(headers=_boom_prop("headers")),
        lambda: _with_attr(response=_boom_prop("response")),
    ],
    ids=["headers.get-raises", "headers-property-raises", "response-property-raises"],
)
def test_r10_a_wait_computation_that_raises_is_a_decision_failure(make):
    sleeps: list[float] = []
    err, calls = run_retry(make, "std", sleeps=sleeps)
    assert type(err) is X and calls == 1 and sleeps == []
    assert attrs(err) == (None, 1) and str(err).endswith(" after 1 attempts")


def _boom_prop(name):
    return property(_boom())


def _with_attr(**attrs_):
    cls = err_class(status_code=429)
    for k, v in attrs_.items():
        setattr(cls, k, v)
    return cls()


VALUES = [
    "nan",
    "inf",
    "-inf",
    "-5",
    "1e999",
    "5, 6",
    "٥",
    "9" * 1_000_000,
    "",
    f"5 {CANARY}",
    "3",
    " 2.5 ",
]


@pytest.mark.parametrize("value", VALUES, ids=[v[:10] or "empty" for v in VALUES])
def test_r10_header_values_always_give_a_finite_wait_in_range(value):
    sleeps: list[float] = []
    err, _ = run_retry(
        lambda: _with_attr(headers={"retry-after": value}), "std", sleeps=sleeps, max_attempts=2
    )
    assert len(sleeps) == 1 and math.isfinite(sleeps[0]) and 0.0 <= sleeps[0] <= 8.0
    assert CANARY not in _every_surface(err)


# ---- R17: traceback -----------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "make,kind",
    [
        (lambda: urllib.error.URLError(OSError(CANARY)), "std"),
        (
            lambda: _bedrock_error(
                response={"Error": {"Code": "ThrottlingException", "Message": CANARY}}
            ),
            "bedrock",
        ),
    ],
    ids=["urlerror-reason", "bedrock-message"],
)
def test_r17_the_traceback_never_prints_the_original_error_text(make, kind):
    err, _ = run_retry(make, kind)
    assert err.__cause__ is None and err.__context__ is not None
    assert CANARY not in "".join(traceback.format_exception(err))
