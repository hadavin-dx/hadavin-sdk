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


def _run(errors, max_attempts=ATTEMPTS):
    """Run `with_retry` over a call that raises `errors` in order; return (the error, calls made, sleeps)."""
    left, sleeps, calls = list(errors), [], []

    def call():
        calls.append(1)
        raise left.pop(0)

    with pytest.raises(ProviderError) as caught:
        with_retry(call, label="t", max_attempts=max_attempts, sleep=sleeps.append)
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
        ([_http(429), _http(429), _http(429)], ProviderExhausted),
        ([_refused(), _refused(), _refused()], ProviderExhausted),
    ],
    ids=["401", "refused then 403", "429 every time", "refused every time"],
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
