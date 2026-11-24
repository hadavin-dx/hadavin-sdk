"""The mark `refused_before_response` (llm/retry.py): True only when it is certain that the provider did no work.

Written by a different agent than the builders of the mark. `with_retry` runs with a fake call and a fake sleep
(no waiting, no network); the two adapter checks use a scripted `post_json` and a fake Bedrock client.
"""

import socket
import urllib.error
from decimal import Decimal
from types import SimpleNamespace

import pytest

from hadavin_sdk.llm import openai_compat
from hadavin_sdk.llm.protocol import ProviderError, ProviderExhausted
from hadavin_sdk.llm.retry import with_retry

ATTEMPTS = 3


class _Status(Exception):
    """An SDK error that carries an HTTP status the way most SDKs do."""

    def __init__(self, code):
        super().__init__(f"status {code}")
        self.status_code = code


def _refused():
    return urllib.error.URLError(ConnectionRefusedError(111, "refused"))


def _no_name():
    return urllib.error.URLError(socket.gaierror(socket.EAI_NONAME, "no such host"))


def _timeout():
    return urllib.error.URLError(TimeoutError("timed out"))


def _run(errors, max_attempts=ATTEMPTS, throttled_unbilled=True, **kw):
    """Run `with_retry` over a call that raises `errors` in order; return (the error, calls made, sleeps)."""
    left, sleeps, calls = list(errors), [], []

    def call():
        calls.append(1)
        raise left.pop(0)

    with pytest.raises(ProviderError) as caught:
        with_retry(
            call,
            label="t",
            max_attempts=max_attempts,
            sleep=sleeps.append,
            throttled_unbilled=throttled_unbilled,
            **kw,
        )
    assert not left, "the table row lists more errors than attempts were made"
    return caught.value, len(calls), sleeps


# (name, the error of each attempt, the class of the final error)
MARKED = [
    *[
        (f"{code} at once", [_Status(code)], ProviderError)
        for code in (400, 401, 403, 404, 413, 422)
    ],
    ("urllib 401 at once", [urllib.error.HTTPError("u", 401, "no", {}, None)], ProviderError),
    ("refused then 401", [_refused(), _Status(401)], ProviderError),
    ("refused, no name, then 400", [_refused(), _no_name(), _Status(400)], ProviderError),
    ("refused every time", [_refused(), _refused(), _refused()], ProviderExhausted),
    (
        "bare refused every time",
        [ConnectionRefusedError(), ConnectionRefusedError(), ConnectionRefusedError()],
        ProviderExhausted,
    ),
    ("no name every time", [_no_name(), _no_name(), _no_name()], ProviderExhausted),
    ("refused and no name mixed", [_refused(), _no_name(), _refused()], ProviderExhausted),
    ("429 every time", [_Status(429), _Status(429), _Status(429)], ProviderExhausted),
    (
        "urllib 429 every time",
        [urllib.error.HTTPError("u", 429, "slow", {}, None) for _ in range(ATTEMPTS)],
        ProviderExhausted,
    ),
    ("429, refused, 429", [_Status(429), _refused(), _Status(429)], ProviderExhausted),
    ("refused, 429, no name", [_refused(), _Status(429), _no_name()], ProviderExhausted),
    ("429, 429, refused", [_Status(429), _Status(429), _refused()], ProviderExhausted),
]

UNMARKED = [
    *[
        (f"{code} exhausted", [_Status(code)] * ATTEMPTS, ProviderExhausted)
        for code in (408, 500, 502, 503)
    ],
    *[(f"{code} at once", [_Status(code)], ProviderError) for code in (409, 418)],
    ("500 then 400", [_Status(500), _Status(400)], ProviderError),
    ("refused, timeout, refused", [_refused(), _timeout(), _refused()], ProviderExhausted),
    ("timeout every time", [_timeout(), _timeout(), _timeout()], ProviderExhausted),
    (
        "bare timeout every time",
        [TimeoutError(), TimeoutError(), TimeoutError()],
        ProviderExhausted,
    ),
    ("timeout then 401", [_timeout(), _Status(401)], ProviderError),
    (
        "reset every time",
        [ConnectionResetError(104, "reset") for _ in range(ATTEMPTS)],
        ProviderExhausted,
    ),
    (
        "refused, reset, refused",
        [_refused(), ConnectionResetError(), _refused()],
        ProviderExhausted,
    ),
    ("429 then 500 then 429", [_Status(429), _Status(500), _Status(429)], ProviderExhausted),
    ("429, 429, 500", [_Status(429), _Status(429), _Status(500)], ProviderExhausted),
    ("500 then 429 twice", [_Status(500), _Status(429), _Status(429)], ProviderExhausted),
    ("429, timeout, 429", [_Status(429), _timeout(), _Status(429)], ProviderExhausted),
    ("429, 408, 429", [_Status(429), _Status(408), _Status(429)], ProviderExhausted),
    ("an unknown error", [KeyError("choices")], ProviderError),
]


@pytest.mark.parametrize(("errors", "final"), [r[1:] for r in MARKED], ids=[r[0] for r in MARKED])
def test_marked_when_no_attempt_can_have_been_billed(errors, final):
    error, calls, sleeps = _run(errors)
    assert type(error) is final
    assert error.refused_before_response is True
    assert calls == len(errors)
    assert len(sleeps) == len(errors) - 1  # one fake sleep between attempts, none after the last


@pytest.mark.parametrize(
    ("errors", "final"), [r[1:] for r in UNMARKED], ids=[r[0] for r in UNMARKED]
)
def test_unmarked_when_any_attempt_may_have_been_answered(errors, final):
    error, calls, sleeps = _run(errors)
    assert type(error) is final
    assert error.refused_before_response is False
    assert calls == len(errors)
    assert len(sleeps) == len(errors) - 1


def test_a_single_attempt_that_is_throttled_or_refused_is_marked():
    for exc in (_Status(429), _refused(), _no_name()):
        error, calls, sleeps = _run([exc], max_attempts=1)
        assert type(error) is ProviderExhausted
        assert error.refused_before_response is True
        assert (calls, sleeps) == (1, [])


def test_a_reply_that_failed_to_parse_passes_through_unmarked():
    """The call raises ProviderError itself once the answer arrived: the same object, no retry, no mark."""
    raised = ProviderError("openai_compat: KeyError")
    error, calls, sleeps = _run([raised])
    assert error is raised
    assert error.refused_before_response is False
    assert (calls, sleeps) == (1, [])
    # also after attempts that were never sent
    raised = ProviderError("openai_compat: KeyError")
    error, calls, _ = _run([_refused(), raised])
    assert error is raised and calls == 2
    assert error.refused_before_response is False


def test_the_default_is_unmarked_and_the_mark_is_per_instance():
    assert ProviderError("x").refused_before_response is False
    assert ProviderExhausted("x").refused_before_response is False
    marked, _, _ = _run([_Status(401)])
    assert marked.refused_before_response is True
    assert ProviderError.refused_before_response is False  # setting one error never marks the class
    assert ProviderExhausted.refused_before_response is False
    assert ProviderError("y").refused_before_response is False


def test_the_kind_status_feeds_the_mark_but_not_the_retry_decision():
    class Sdk(Exception):
        """Keeps its status where the generic rule does not look."""

        def __init__(self, code):
            super().__init__("sdk")
            self.where = code

    def run(errors, retryable=None):
        left, sleeps = list(errors), []

        def call():
            raise left.pop(0)

        with pytest.raises(ProviderError) as caught:
            with_retry(
                call,
                label="t",
                max_attempts=ATTEMPTS,
                sleep=sleeps.append,
                retryable=retryable,
                throttled_unbilled=True,
                http_status=lambda exc: getattr(exc, "where", None),
            )
        return caught.value, len(sleeps)

    error, slept = run([Sdk(403)])
    assert type(error) is ProviderError and error.refused_before_response is True
    error, slept = run([Sdk(500)])  # a 5xx the kind does not retry: one attempt, unmarked
    assert type(error) is ProviderError and slept == 0
    assert error.refused_before_response is False
    error, slept = run([Sdk(429)] * ATTEMPTS, retryable=lambda exc: True)
    assert type(error) is ProviderExhausted and slept == ATTEMPTS - 1
    assert error.refused_before_response is True
    error, slept = run([Sdk(429), Sdk(503), Sdk(429)], retryable=lambda exc: True)
    assert type(error) is ProviderExhausted and error.refused_before_response is False


# --- openai_compat: the second request ---------------------------------------------------------------------

ROUTE = SimpleNamespace(
    model_id="m-2026-01-01",
    max_tokens=16,
    input_usd_per_mtok=Decimal(1),
    output_usd_per_mtok=Decimal(1),
)
SCHEMA = {"type": "object", "properties": {"n": {"type": "integer"}}, "required": ["n"]}
# An answer in plain text that is not JSON: with a forced answer the adapter sends one more request.
NOT_JSON = {
    "choices": [{"message": {"content": "no json here"}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 3, "completion_tokens": 2},
}


def _http(code):
    return urllib.error.HTTPError("u", code, "x", {}, None)


def _openai(monkeypatch, script):
    """The adapter over a scripted `post_json`: each item is returned, or raised when it is an exception."""
    left, sent = list(script), []

    def fake_post(url, body, headers, timeout_s):
        sent.append(body)
        item = left.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item

    monkeypatch.setattr(openai_compat, "post_json", fake_post)
    llm = openai_compat.OpenAICompatLLM(
        "https://x.example/v1", None, {"r": ROUTE}, 1.0, ATTEMPTS, sleep=lambda s: None
    )
    return llm, sent


def _chat(llm):
    return llm.chat([{"role": "user", "content": "q"}], system="s", route="r", output_schema=SCHEMA)


@pytest.mark.parametrize(
    ("script", "final"),
    [
        ([_http(401)], ProviderError),
        ([_refused(), _http(403)], ProviderError),
        ([_refused(), _refused(), _refused()], ProviderExhausted),
    ],
    ids=["401", "refused then 403", "refused every time"],
)
def test_openai_compat_first_request_keeps_the_mark(monkeypatch, script, final):
    llm, sent = _openai(monkeypatch, script)
    with pytest.raises(ProviderError) as caught:
        _chat(llm)
    assert type(caught.value) is final
    assert caught.value.refused_before_response is True
    assert len(sent) == len(script)


@pytest.mark.parametrize(
    ("script", "final"),
    [
        ([NOT_JSON, _http(401)], ProviderError),
        ([NOT_JSON, _http(400)], ProviderError),
        ([NOT_JSON, _refused(), _refused(), _refused()], ProviderExhausted),
        ([NOT_JSON, _http(429), _http(429), _http(429)], ProviderExhausted),
        ([NOT_JSON, _refused(), _http(403)], ProviderError),
    ],
    ids=["401", "400", "refused every time", "429 every time", "refused then 403"],
)
def test_openai_compat_clears_the_mark_on_its_second_request(monkeypatch, script, final):
    """The first request was answered (and billed), so a refusal of the second one is not "refused before"."""
    llm, sent = _openai(monkeypatch, script)
    with pytest.raises(ProviderError) as caught:
        _chat(llm)
    assert type(caught.value) is final
    assert caught.value.refused_before_response is False
    assert len(sent) == len(script)  # the first request, then every attempt of the second


def test_openai_compat_sends_no_second_request_without_a_forced_answer(monkeypatch):
    llm, sent = _openai(monkeypatch, [NOT_JSON])
    got = llm.chat([{"role": "user", "content": "q"}], system="s", route="r")
    assert got.text == "no json here"
    assert len(sent) == 1


# --- bedrock: the status lives in response["ResponseMetadata"] -------------------------------------------------


class _AwsError(Exception):
    """Shaped like a botocore error (a `response` dict), without botocore and without any AWS call."""

    def __init__(self, response):
        super().__init__("aws")
        self.response = response


def _meta(code, name="ValidationException"):
    return {"ResponseMetadata": {"HTTPStatusCode": code}, "Error": {"Code": name}}


@pytest.fixture
def bedrock():
    pytest.importorskip("boto3")
    from hadavin_sdk.llm import bedrock as module

    return module


def _converse(bedrock, errors):
    left, calls = list(errors), []

    class Client:
        def converse(self, **request):
            calls.append(request)
            raise left.pop(0)

    route = SimpleNamespace(**{**vars(ROUTE), "model_id": "anthropic.m-v1:0"})
    llm = bedrock.BedrockLLM(Client(), {"r": route}, ATTEMPTS, sleep=lambda s: None)
    with pytest.raises(ProviderError) as caught:
        llm.chat([{"role": "user", "content": "q"}], system="s", route="r")
    assert not left
    return caught.value, len(calls)


def test_bedrock_http_status_reads_response_metadata(bedrock):
    assert bedrock.http_status(_AwsError(_meta(400))) == 400
    assert bedrock.http_status(_AwsError(_meta(429))) == 429
    for response in (
        {},
        {"ResponseMetadata": {}},
        {"Error": {"Code": "400"}},
        {"ResponseMetadata": {"HTTPStatusCode": "400"}},
        {"ResponseMetadata": {"HTTPStatusCode": True}},
        {"ResponseMetadata": {"HTTPStatusCode": None}},
        None,
        "400",
    ):
        assert bedrock.http_status(_AwsError(response)) is None
    assert bedrock.http_status(ValueError("no response at all")) is None


@pytest.mark.parametrize("code", [400, 401, 403, 404, 413, 422])
def test_bedrock_marks_a_refusal_from_response_metadata(bedrock, code):
    error, calls = _converse(bedrock, [_AwsError(_meta(code))])
    assert type(error) is ProviderError
    assert error.refused_before_response is True
    assert calls == 1


def test_bedrock_leaves_other_answers_unmarked(bedrock):
    for response in (_meta(409), _meta(418), {"Error": {"Code": "ValidationException"}}):
        error, calls = _converse(bedrock, [_AwsError(response)])
        assert type(error) is ProviderError
        assert error.refused_before_response is False
        assert calls == 1


def test_bedrock_client_errors_through_the_retry(bedrock):
    from botocore.exceptions import ClientError  # built by hand: no AWS call

    def client_error(code, name):
        return ClientError(_meta(code, name), "Converse")

    error, calls = _converse(bedrock, [client_error(400, "ValidationException")])
    assert type(error) is ProviderError and calls == 1
    assert error.refused_before_response is True

    throttled = [client_error(429, "ThrottlingException") for _ in range(ATTEMPTS)]
    error, calls = _converse(bedrock, throttled)
    assert type(error) is ProviderExhausted and calls == ATTEMPTS
    assert error.refused_before_response is True

    broken = [client_error(500, "InternalServerException") for _ in range(ATTEMPTS)]
    error, calls = _converse(bedrock, broken)
    assert type(error) is ProviderExhausted and calls == ATTEMPTS
    assert error.refused_before_response is False

    mixed = [
        client_error(429, "ThrottlingException"),
        client_error(503, "ServiceUnavailableException"),
        client_error(429, "ThrottlingException"),
    ]
    error, calls = _converse(bedrock, mixed)
    assert type(error) is ProviderExhausted and calls == ATTEMPTS
    assert error.refused_before_response is False

    after_a_5xx = [
        client_error(500, "InternalServerException"),
        client_error(403, "AccessDeniedException"),
    ]
    error, calls = _converse(bedrock, after_a_5xx)
    assert type(error) is ProviderError and calls == 2
    assert error.refused_before_response is False


# === Provider mark fix round 1 (ticket F-provider-mark RESOLUTION M1, M2, N3, N5, N7) ==============================
# Added by a different agent than the builders. Existing tests above are unchanged.

import itertools

from hadavin_sdk.llm import retry as retry_mod
from hadavin_sdk.llm.common import NetworkLLM
from hadavin_sdk.llm.retry import REFUSED_STATUSES, never_sent

ALL_REFUSED = (400, 401, 403, 404, 413, 422)
ROUTER_REFUSED = (401, 403, 404)
ROUTER_NOT_REFUSED = (400, 413, 422)


class _Generic(NetworkLLM):
    """The generic kind: no override of the status list. Its `_chat` raises the scripted errors in order."""

    label = "generic"

    def __init__(self, errors, max_attempts=ATTEMPTS):
        super().__init__({}, max_attempts, sleep=lambda s: None)
        self.left = list(errors)

    def _chat(self, route, system, turns, specs, forced, output_schema):
        def call():
            raise self.left.pop(0)

        return self._retry(call)


def _generic_error(errors, max_attempts=ATTEMPTS):
    llm = _Generic(errors, max_attempts)
    llm.routes = {"r": ROUTE}
    with pytest.raises(ProviderError) as caught:
        llm.chat([{"role": "user", "content": "q"}], system="s", route="r")
    return caught.value


@pytest.mark.parametrize("code", ALL_REFUSED + (429,))
def test_generic_kind_keeps_the_full_status_list(code):
    assert _Generic.refused_statuses == REFUSED_STATUSES == frozenset(ALL_REFUSED)
    error = _generic_error([_Status(code)], max_attempts=1)
    assert error.refused_before_response is (code != 429)  # no override: a 429 is never unbilled


@pytest.mark.parametrize("code", ROUTER_REFUSED)
def test_openai_compat_marks_401_403_404(monkeypatch, code):
    assert openai_compat.OpenAICompatLLM.refused_statuses == frozenset(ROUTER_REFUSED)
    llm, sent = _openai(monkeypatch, [_http(code)])
    with pytest.raises(ProviderError) as caught:
        _chat(llm)
    assert type(caught.value) is ProviderError
    assert caught.value.refused_before_response is True
    assert len(sent) == 1


@pytest.mark.parametrize("code", ROUTER_NOT_REFUSED)
def test_openai_compat_does_not_mark_400_413_422(monkeypatch, code):
    """A router behind base_url may answer these after the upstream model consumed tokens."""
    llm, sent = _openai(monkeypatch, [_http(code)])
    with pytest.raises(ProviderError) as caught:
        _chat(llm)
    assert type(caught.value) is ProviderError
    assert caught.value.refused_before_response is False
    assert len(sent) == 1


@pytest.mark.parametrize("code", ROUTER_NOT_REFUSED)
def test_openai_compat_refused_connection_then_router_status_is_unmarked(monkeypatch, code):
    llm, _ = _openai(monkeypatch, [_refused(), _http(code)])
    with pytest.raises(ProviderError) as caught:
        _chat(llm)
    assert caught.value.refused_before_response is False


@pytest.mark.parametrize("code", ALL_REFUSED)
def test_another_kind_still_marks_all_six_statuses(code):
    error = _generic_error([_Status(code)], max_attempts=1)
    assert error.refused_before_response is True


def test_every_kind_but_openai_compat_keeps_the_default_list():
    """The per-kind list is a class attribute: only the router-fronted kind narrows it."""
    kinds = {"openai_compat": openai_compat.OpenAICompatLLM}
    for name in ("anthropic", "gemini", "bedrock"):
        try:
            module = __import__(f"hadavin_sdk.llm.{name}", fromlist=["x"])
        except ImportError:  # the extra is not installed
            continue
        kinds[name] = next(
            v
            for v in vars(module).values()
            if isinstance(v, type) and issubclass(v, NetworkLLM) and v is not NetworkLLM
        )
    for name, kind in kinds.items():
        narrow = name in (
            "openai_compat",
            "anthropic",
        )  # anthropic: widened per instance for the direct API
        expected = frozenset(ROUTER_REFUSED) if narrow else REFUSED_STATUSES
        assert kind.refused_statuses == expected, name


def test_a_429_then_a_400_stays_unmarked():
    error, calls, _ = _run([_Status(429), _Status(400)])
    assert type(error) is ProviderError and calls == 2
    assert error.refused_before_response is False
    error, _, _ = _run([_Status(429), _Status(429), _Status(400)])
    assert error.refused_before_response is False


def test_a_429_a_kind_chose_not_to_retry_stays_unmarked():
    """No built kind declines to retry a 429 (anthropic, gemini, openai_compat use the generic rule; bedrock
    retries it by status). The hook is exercised with a double."""
    sleeps = []

    def call():
        raise _Status(429)

    with pytest.raises(ProviderError) as caught:
        with_retry(
            call,
            label="t",
            max_attempts=ATTEMPTS,
            sleep=sleeps.append,
            retryable=lambda exc: False,
        )
    assert type(caught.value) is ProviderError
    assert caught.value.refused_before_response is False
    assert sleeps == []
    # also after a refused connection
    left = [_refused(), _Status(429)]

    def call2():
        raise left.pop(0)

    with pytest.raises(ProviderError) as caught:
        with_retry(
            call2,
            label="t",
            max_attempts=ATTEMPTS,
            sleep=sleeps.append,
            retryable=lambda exc: status_of(exc) != 429,
        )
    assert caught.value.refused_before_response is False


def status_of(exc):
    return retry_mod.status(exc)


def test_a_tls_error_stays_unmarked():
    import ssl

    for exc in (
        ssl.SSLCertVerificationError("bad cert"),
        urllib.error.URLError(ssl.SSLError("handshake")),
    ):
        error, calls, sleeps = _run([exc])
        assert type(error) is ProviderError
        assert error.refused_before_response is False
        assert (calls, sleeps) == (1, [])
    error, _, _ = _run([_refused(), ssl.SSLCertVerificationError("bad cert")])
    assert error.refused_before_response is False


def _linked(kinds):
    """An error chain: kinds[0] is the outer error, each next one its `__cause__`."""
    errors = [k if isinstance(k, BaseException) else k() for k in kinds]
    for outer, inner in itertools.pairwise(errors):
        outer.__cause__ = inner
    return errors[0]


def _plain():
    return OSError("wrapper")


def test_a_cause_chain_longer_than_the_walk_limit_is_not_never_sent():
    # 10 errors: a refused connection at depth 3, a timeout at depth 9 (past the limit of 8)
    kinds = [_plain] * 10
    kinds[2], kinds[8] = ConnectionRefusedError, TimeoutError
    assert never_sent(_linked(kinds)) is False
    # a refused connection and nothing else, but the chain is cut: still not never-sent
    kinds = [_plain] * 10
    kinds[2] = ConnectionRefusedError
    assert never_sent(_linked(kinds)) is False
    # 9 errors is one past the limit
    kinds = [_plain] * 9
    kinds[2] = ConnectionRefusedError
    assert never_sent(_linked(kinds)) is False


def test_a_cause_chain_of_exactly_the_walk_limit_is_checked_whole():
    kinds = [_plain] * 8
    kinds[2] = ConnectionRefusedError
    assert never_sent(_linked(kinds)) is True
    kinds[7] = TimeoutError  # the last error of the chain is still seen
    assert never_sent(_linked(kinds)) is False


def test_a_truncated_chain_is_not_marked_through_with_retry():
    kinds = [_plain] * 10
    kinds[2], kinds[8] = ConnectionRefusedError, TimeoutError
    error, _, _ = _run([_linked(kinds)], max_attempts=1)
    assert error.refused_before_response is False
    kinds = [_plain] * 8
    kinds[2] = ConnectionRefusedError
    error, _, _ = _run([_linked(kinds)], max_attempts=1)
    assert (
        type(error) is ProviderExhausted
    )  # a bare chain ending in a refused connection is retried
    assert error.refused_before_response is True


@pytest.mark.parametrize("combo", list(itertools.product("RTSX", repeat=3)), ids="".join)
def test_exhausted_is_marked_iff_every_attempt_was_never_sent_or_429(combo):
    """R refused, T 429, S 500, X timeout. Rule (2) of the module docstring."""
    make = {"R": _refused, "T": lambda: _Status(429), "S": lambda: _Status(500), "X": _timeout}
    error, calls, _ = _run([make[c]() for c in combo])
    assert type(error) is ProviderExhausted and calls == ATTEMPTS
    assert error.refused_before_response is all(c in "RT" for c in combo)


def test_a_provider_error_raised_by_the_adapters_own_call_passes_through_unmarked():
    """N5 (corrected after the test writer's finding): `except ProviderError: raise` in with_retry is kept; a
    ProviderError the adapter's own call raises passes through UNCHANGED and unmarked, whatever it carries
    (the safe direction: the worst case stays booked). No built adapter raises one."""
    raised = ProviderError("openai_compat: KeyError")
    error, calls, _ = _run([raised])
    assert error is raised
    assert error.refused_before_response is False
    assert calls == 1
    # after a never-sent attempt: still the same object, still unmarked
    raised = ProviderError("openai_compat: KeyError")
    error, calls, _ = _run([_refused(), raised])
    assert error is raised and calls == 2
    assert error.refused_before_response is False
    # even one that carries a refused status passes through unmarked (it is not with_retry's own error)
    raised = ProviderError("x")
    raised.status_code = 401
    error, _, _ = _run([raised])
    assert error is raised
    assert error.refused_before_response is False


class _AnthropicClient:
    """Stands in for the SDK client: `messages.create` raises the scripted error."""

    def __init__(self, code):
        self.code = code
        self.messages = self

    def create(self, **_):
        raise _Status(self.code)


def _anthropic_error(code, **kw):
    pytest.importorskip("anthropic")
    from hadavin_sdk.llm.anthropic import AnthropicLLM

    llm = AnthropicLLM(_AnthropicClient(code), {"r": ROUTE}, 1, sleep=lambda s: None, **kw)
    with pytest.raises(ProviderError) as caught:
        llm.chat([{"role": "user", "content": "q"}], system="s", route="r")
    return caught.value


@pytest.mark.parametrize("code", ALL_REFUSED)
def test_anthropic_direct_api_marks_all_six_statuses(code):
    assert _anthropic_error(code, direct_api=True).refused_before_response is True


@pytest.mark.parametrize("code", ROUTER_REFUSED)
def test_anthropic_behind_a_gateway_marks_only_401_403_404(code):
    assert _anthropic_error(code).refused_before_response is True


@pytest.mark.parametrize("code", ROUTER_NOT_REFUSED)
def test_anthropic_behind_a_gateway_does_not_mark_400_413_422(code):
    """Vertex and Foundry (and an unknown platform) may answer these after the model started."""
    assert _anthropic_error(code).refused_before_response is False


@pytest.mark.parametrize(
    ("platform", "direct"),
    [
        ("vertex", False),
        ("foundry", False),
        ("api", True),
        ("bedrock", False),
        ("API", False),
        ("apii", False),
        ("", False),
        (None, False),
    ],
)
def test_make_wide_list_only_for_the_exact_api_platform(monkeypatch, platform, direct):
    pytest.importorskip("anthropic")
    from types import SimpleNamespace

    from hadavin_sdk.llm import anthropic as mod

    monkeypatch.setattr(mod, "client", lambda settings, key: object())
    settings = SimpleNamespace(platform=platform, api_key_secret_name="k", max_attempts=1)  # noqa: S106
    llm = mod.make(settings, SimpleNamespace(routes={}, resolve=lambda n: "x"))
    assert (llm.refused_statuses == REFUSED_STATUSES) is direct


# throttled_unbilled (M1 of D-config-and-mark-rereview-1): a router's / gateway's 429 can follow upstream work, so
# the gate must not settle it at 0 ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "script",
    [
        [_http(429)] * 3,
        [_refused(), _http(429), _http(429)],
        [_http(429), _refused(), _http(429)],
    ],
    ids=["429 x3", "refused, 429, 429", "429, refused, 429"],
)
def test_openai_compat_429_exhausted_is_not_marked(monkeypatch, script):
    assert openai_compat.OpenAICompatLLM.throttled_unbilled is False
    llm, sent = _openai(monkeypatch, script)
    with pytest.raises(ProviderExhausted) as caught:
        _chat(llm)
    assert caught.value.refused_before_response is False
    assert len(sent) == len(script)


def test_openai_compat_never_sent_every_time_is_still_marked(monkeypatch):
    llm, _ = _openai(monkeypatch, [_refused(), _no_name(), _refused()])
    with pytest.raises(ProviderExhausted) as caught:
        _chat(llm)
    assert caught.value.refused_before_response is True


@pytest.mark.parametrize("combo", list(itertools.product("RTSX", repeat=3)), ids="".join)
def test_exhausted_with_throttled_unbilled_is_marked_iff_every_attempt_was_never_sent_or_429(combo):
    make = {"R": _refused, "T": lambda: _Status(429), "S": lambda: _Status(500), "X": _timeout}
    error, calls, _ = _run([make[c]() for c in combo], throttled_unbilled=True)
    assert type(error) is ProviderExhausted and calls == ATTEMPTS
    assert error.refused_before_response is all(c in "RT" for c in combo)


@pytest.mark.parametrize("combo", list(itertools.product("RTSX", repeat=3)), ids="".join)
def test_exhausted_without_throttled_unbilled_is_marked_iff_every_attempt_was_never_sent(combo):
    make = {"R": _refused, "T": lambda: _Status(429), "S": lambda: _Status(500), "X": _timeout}
    error, calls, _ = _run([make[c]() for c in combo], throttled_unbilled=False)
    assert type(error) is ProviderExhausted and calls == ATTEMPTS
    assert error.refused_before_response is all(c == "R" for c in combo)


def test_a_single_429_attempt_is_unmarked_without_throttled_unbilled():
    error, _, _ = _run([_Status(429)], max_attempts=1, throttled_unbilled=False)
    assert type(error) is ProviderExhausted
    assert error.refused_before_response is False
    error, _, _ = _run(
        [_Status(429)], max_attempts=1, throttled_unbilled=True
    )  # the direct API case
    assert error.refused_before_response is True


def test_with_retry_and_a_new_kind_default_to_never_unbilled_429():
    """Fail closed: a hypothetical kind with no setting, and with_retry called without the flag."""
    assert NetworkLLM.throttled_unbilled is False and _Generic.throttled_unbilled is False
    assert _generic_error([_Status(429)] * 3).refused_before_response is False
    assert (
        _generic_error([_refused()] * 3).refused_before_response is True
    )  # never sent still counts
    left = [_Status(429)] * 3

    def call():
        raise left.pop(0)

    with pytest.raises(ProviderExhausted) as caught:
        with_retry(call, label="t", max_attempts=3, sleep=lambda s: None)
    assert caught.value.refused_before_response is False


def test_only_the_direct_kinds_set_throttled_unbilled():
    from hadavin_sdk.llm import bedrock, gemini

    assert bedrock.BedrockLLM.throttled_unbilled is True
    assert gemini.GeminiLLM.throttled_unbilled is True
    assert openai_compat.OpenAICompatLLM.throttled_unbilled is False


def _anthropic_exhausted(code, direct_api):
    pytest.importorskip("anthropic")
    from hadavin_sdk.llm.anthropic import AnthropicLLM

    llm = AnthropicLLM(
        _AnthropicClient(code), {"r": ROUTE}, ATTEMPTS, sleep=lambda s: None, direct_api=direct_api
    )
    with pytest.raises(ProviderExhausted) as caught:
        llm.chat([{"role": "user", "content": "q"}], system="s", route="r")
    return caught.value


@pytest.mark.parametrize("platform", ["vertex", "foundry", "bedrock", "API", "", "unknown", None])
def test_anthropic_other_platform_429_is_not_marked(monkeypatch, platform):
    pytest.importorskip("anthropic")
    from hadavin_sdk.llm import anthropic as mod

    monkeypatch.setattr(mod, "client", lambda settings, key: object())
    settings = SimpleNamespace(platform=platform, api_key_secret_name="k", max_attempts=3)  # noqa: S106
    llm = mod.make(settings, SimpleNamespace(routes={}, resolve=lambda n: "x"))
    assert llm.throttled_unbilled is False
    assert _anthropic_exhausted(429, direct_api=False).refused_before_response is False


def test_anthropic_direct_api_429_exhausted_is_marked(monkeypatch):
    pytest.importorskip("anthropic")
    from hadavin_sdk.llm import anthropic as mod

    monkeypatch.setattr(mod, "client", lambda settings, key: object())
    settings = SimpleNamespace(platform="api", api_key_secret_name="k", max_attempts=3)  # noqa: S106
    llm = mod.make(settings, SimpleNamespace(routes={}, resolve=lambda n: "x"))
    assert llm.throttled_unbilled is True
    assert _anthropic_exhausted(429, direct_api=True).refused_before_response is True


@pytest.mark.parametrize("code", [401, 403, 404])
def test_anthropic_direct_api_refused_statuses_stay_marked(code):
    assert _anthropic_error(code, direct_api=True).refused_before_response is True


class _Scripted:
    def __init__(self, errors):
        self.errors, self.messages = errors, self

    def create(self, **_):
        raise self.errors.pop(0)


def test_anthropic_direct_api_mixed_attempts():
    pytest.importorskip("anthropic")
    from hadavin_sdk.llm.anthropic import AnthropicLLM

    for script, marked in (
        ([429, 429, 401], False),
        ([429, 500, 429], False),
        ([429, 429, 429], True),
    ):
        client = _Scripted([_Status(c) for c in script])
        llm = AnthropicLLM(client, {"r": ROUTE}, 3, sleep=lambda s: None, direct_api=True)
        with pytest.raises(ProviderError) as caught:
            llm.chat([{"role": "user", "content": "q"}], system="s", route="r")
        assert caught.value.refused_before_response is marked, script
