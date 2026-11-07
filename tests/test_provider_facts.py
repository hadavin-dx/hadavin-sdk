"""New-feature rows: the checked facts and their tables (R3, R4, R15, R19) and the neutral module's imports.

Not copied to the fail-before worktree: every row here needs a name that does not exist on the base.
"""

from __future__ import annotations

import copy
import multiprocessing
import pickle
import sys
import urllib.error

import pytest

from hadavin_sdk import codes
from hadavin_sdk.codes import (
    CODED_STATUSES,
    ERROR_TYPE_CODE,
    REQUEST_ID_SHAPES,
    STATUS_ERROR_TYPE,
    Code,
)
from hadavin_sdk.codes import ProviderErrorType as T
from hadavin_sdk.llm import ProviderError, ProviderExhausted, protocol, retry
from hadavin_sdk.llm import anthropic as anth
from hadavin_sdk.llm import bedrock as bed
from hadavin_sdk.llm.provider_facts import (
    NO_FACTS,
    TYPE_NAME_MAX,
    ProviderFacts,
    clean_count,
    clean_error_type,
    clean_flag,
    clean_request_id,
    clean_status,
    safe_facts,
    status_error_type,
)
from tests.import_order_child import import_in_order

GOOD_UUID = "0b1c2d3e-4f50-4a6b-8c7d-9e0f1a2b3c4d"
GOOD_REQ = "req_AbCd1234Ef56Gh78"

# ---- R3: constructor ----------------------------------------------------------------------------------------------------

BAD_VALUES = {
    "status": [True, 0, 99, 600, "429", 429.0, None],
    "error_type": ["rate_limit", 7, None],
    "request_id": ["req_" + "A" * 37, GOOD_REQ + "\n", "A" * 40, "a-b_c" * 8, "x" * 41, 41, None],
    "retryable": [1, 0, "yes", None],
    "retry_count": [-1, 1001, True, "3", 2.0, None],
}


@pytest.mark.parametrize("cls", [ProviderError, ProviderExhausted])
def test_r3_plain_text_construction_still_works_and_subclasses_pass_only_text(cls):
    err = cls("x")
    assert str(err) == "x" and err.args == ("x",)
    assert (err.status, err.error_type, err.request_id, err.retryable, err.retry_count) == (
        None,
    ) * 5

    class Sub(cls):
        def __init__(self, text):
            super().__init__(text)

    assert Sub("y").status is None and str(Sub("y")) == "y"


@pytest.mark.parametrize(
    "field,value", [(f, v) for f, vs in BAD_VALUES.items() for v in vs if v is not None]
)
def test_r3_a_wrong_type_or_range_becomes_none_and_never_raises(field, value):
    err = ProviderError("x", **{field: value})
    assert getattr(err, field) is None
    assert vars(err)[field] is None


def test_r3_valid_values_are_kept_and_the_others_stay_independent():
    err = ProviderError(
        "x",
        status=429,
        error_type=T.rate_limit,
        request_id=GOOD_UUID,
        retryable=True,
        retry_count=3,
    )
    assert (err.status, err.error_type, err.request_id, err.retryable, err.retry_count) == (
        429,
        T.rate_limit,
        GOOD_UUID,
        True,
        3,
    )
    for n in (0, 1, 1000):
        assert ProviderError("x", retry_count=n).retry_count == n
    for n in (-1, 1001):
        assert ProviderError("x", retry_count=n).retry_count is None
    assert (
        ProviderError("x", status=True, retry_count=2).retry_count == 2
    )  # one bad value drops only itself
    assert ProviderError("x", request_id=GOOD_REQ).request_id == GOOD_REQ
    assert ProviderError("x", retryable=False).retryable is False


def test_r3_extra_positional_arguments_stay_text_arguments_not_facts():
    err = ProviderError("x", 429)
    assert err.args == ("x", 429) and err.status is None


def test_r3_direct_provider_facts_drops_the_same_values_without_raising():
    for field, values in (
        ("status", BAD_VALUES["status"]),
        ("error_type", BAD_VALUES["error_type"]),
        ("request_id", BAD_VALUES["request_id"]),
    ):
        for v in values:
            kw = {"status": None, "error_type": None, "request_id": None} | {field: v}
            assert getattr(ProviderFacts(**kw), field) is None
    ok = ProviderFacts(503, T.server_error, GOOD_REQ)
    assert (ok.status, ok.error_type, ok.request_id) == (503, T.server_error, GOOD_REQ)
    assert NO_FACTS == ProviderFacts(None, None, None)
    with pytest.raises(AttributeError):
        ok.status = 1  # frozen


def _rebuilt(obj):
    """What unpickling does, step by step: the object must pickle, and its ``__reduce_ex__`` result must rebuild an equal object.

    ``pickle.loads`` itself is not called in a test of our own objects; the rebuild below is the same call ``loads`` would make
    (class called with the stored arguments, then the stored attributes set)."""
    pickle.dumps(obj)  # it must be picklable at all
    reduced = obj.__reduce_ex__(pickle.HIGHEST_PROTOCOL)
    func, args = reduced[0], reduced[1]
    state = reduced[2] if len(reduced) > 2 else None
    clone = func(*args)
    clone.__dict__.update(state or {})
    return clone


@pytest.mark.parametrize("cls", [ProviderError, ProviderExhausted])
def test_r3_pickle_and_copy_keep_the_attributes(cls):
    err = cls(
        "x", status=429, error_type=T.throttled, request_id=GOOD_UUID, retryable=True, retry_count=3
    )
    for clone in (_rebuilt(err), copy.copy(err), copy.deepcopy(err)):
        assert type(clone) is cls and str(clone) == "x"
        assert (
            clone.status,
            clone.error_type,
            clone.request_id,
            clone.retryable,
            clone.retry_count,
        ) == (429, T.throttled, GOOD_UUID, True, 3)


def test_r3_p4a_subclasses_keep_their_fields_through_pickle_and_copy():
    """UsageMissing / UnpricedUsage live on core/P4a, not on this branch (BLOCKED on P4a; no stand-in is invented here)."""
    usage_missing = getattr(protocol, "UsageMissing", None)
    unpriced = getattr(protocol, "UnpricedUsage", None)
    if usage_missing is None or unpriced is None:
        pytest.skip(
            "BLOCKED: UsageMissing and UnpricedUsage are not on this branch (they live on core/P4a); rerun after P4a merges"
        )
    for e in (usage_missing("absent", "usage"), unpriced("speed")):
        for name, value in (
            ("status", 429),
            ("error_type", T.throttled),
            ("request_id", GOOD_UUID),
            ("retryable", False),
            ("retry_count", 2),
        ):
            setattr(e, name, value)
        for clone in (_rebuilt(e), copy.copy(e)):
            assert type(clone) is type(e) and str(clone) == str(e)
            assert (clone.reason, clone.field) == (e.reason, e.field)
            assert (
                clone.status,
                clone.error_type,
                clone.request_id,
                clone.retryable,
                clone.retry_count,
            ) == (429, T.throttled, GOOD_UUID, False, 2)


# ---- clean_* and safe_facts ---------------------------------------------------------------------------------------------


def test_clean_functions_are_exact_type_checks():
    class S(str):
        pass

    class I(int):
        pass

    assert clean_status(I(429)) is None and clean_count(I(3)) is None and clean_flag(1) is None
    assert clean_error_type("rate_limit") is None and clean_error_type(T.rate_limit) is T.rate_limit
    assert clean_request_id(S(GOOD_REQ)) is None and clean_request_id(GOOD_REQ) == GOOD_REQ
    assert (
        clean_request_id(GOOD_UUID, "prefixed") is None
        and clean_request_id(GOOD_REQ, "uuid") is None
    )
    assert clean_request_id(GOOD_REQ, "no-such-shape") is None
    assert (
        clean_status(100) == 100
        and clean_status(599) == 599
        and clean_status(99) is None
        and clean_status(600) is None
    )


def test_safe_facts_accepts_only_exactly_provider_facts():
    class Sub(ProviderFacts):
        pass

    exc = ValueError("x")
    assert safe_facts(lambda e: Sub(401, None, None), exc) is NO_FACTS
    assert safe_facts(lambda e: "facts", exc) is NO_FACTS
    assert safe_facts(lambda e: (_ for _ in ()).throw(RuntimeError("adapter")), exc) is NO_FACTS
    good = ProviderFacts(401, T.authentication, None)
    assert safe_facts(lambda e: good, exc) is good

    class Stop(BaseException):
        pass

    with pytest.raises(Stop):
        safe_facts(lambda e: (_ for _ in ()).throw(Stop()), exc)


# ---- R4: read recorder ---------------------------------------------------------------------------------------------------

ALLOWED = {
    "default": {"status_code", "code", "reason", "__cause__", "__context__", "__class__"},
}
ALLOWED["anthropic"] = ALLOWED["default"] | {"request_id", "body"}
ALLOWED["bedrock"] = ALLOWED["default"] | {"response"}
ADAPTERS = {"default": retry.default_facts, "anthropic": anth.facts, "bedrock": bed.facts}


class Forbidden(BaseException):
    pass


def recorder_class(base=Exception, *, flag=None, allowed=frozenset(), log=None, attrs=None):
    """A class whose attribute reads (and ``__str__`` / ``__repr__``) are recorded; with ``flag`` it raises on a forbidden read."""
    log = [] if log is None else log

    def getattribute(self, name):
        log.append(name)
        if flag is not None and flag["on"] and name not in allowed:
            raise Forbidden(name)
        return object.__getattribute__(self, name)

    def as_str(self):
        log.append("__str__")
        if flag is not None and flag["on"]:
            raise Forbidden("__str__")
        return "S"

    def as_repr(self):
        log.append("__repr__")
        if flag is not None and flag["on"]:
            raise Forbidden("__repr__")
        return "R"

    cls = type(
        "Rec", (base,), {"__getattribute__": getattribute, "__str__": as_str, "__repr__": as_repr}
    )
    return cls, log


def _with_attrs(cls, **attrs):
    exc = cls.__new__(cls)
    for k, v in attrs.items():
        object.__setattr__(exc, k, v)
    return exc


@pytest.mark.parametrize("name", ["default", "anthropic", "bedrock"])
def test_r4a_direct_adapter_reads_only_its_allow_list(name):
    cls, log = recorder_class()

    class Reason(OSError):  # the text of a reason is never read, only its type is tested
        def __str__(self):
            log.append("reason.__str__")
            return "r"

        __repr__ = __str__

    exc = _with_attrs(
        cls,
        status_code=None,
        code=None,
        response={
            "Error": {"Code": "X", "Message": "m"},
            "ResponseMetadata": {"HTTPStatusCode": 400, "RequestId": GOOD_UUID},
        },
        body={"error": {"type": "x", "message": "m"}},
        request_id=GOOD_REQ,
        reason=Reason("r"),
    )
    ADAPTERS[name](exc)
    assert set(log) <= ALLOWED[name], set(log) - ALLOWED[name]
    assert log, "the recorder saw nothing"


@pytest.mark.parametrize("name", ["default", "anthropic", "bedrock"])
def test_r4b_through_with_retry_the_adapter_reads_only_its_allow_list(name):
    flag = {"on": False}
    cls, _ = recorder_class(flag=flag, allowed=ALLOWED[name])
    exc = _with_attrs(
        cls,
        status_code=403,
        code=None,
        response={
            "Error": {"Code": "AccessDeniedException"},
            "ResponseMetadata": {"HTTPStatusCode": 403},
        },
        body={"error": {"type": "permission_error"}},
        request_id=GOOD_REQ,
        reason=OSError("r"),
    )

    def wrapper(e):
        flag["on"] = True
        try:
            return ADAPTERS[name](e)
        finally:
            flag["on"] = False

    with pytest.raises(ProviderError) as got:
        retry.with_retry(
            lambda: (_ for _ in ()).throw(exc),
            label="k",
            max_attempts=2,
            sleep=lambda s: None,
            facts=wrapper,
        )
    assert got.value.status == 403


def test_r4d_a_str_body_is_never_read_or_measured():
    log: list[str] = []

    class Body(str):
        def __len__(self):
            log.append("len")
            return str.__len__(self)

        def __bool__(self):
            log.append("bool")
            return True

        def __iter__(self):
            log.append("iter")
            return str.__iter__(self)

        def __getitem__(self, item):
            log.append("getitem")
            return str.__getitem__(self, item)

        def __contains__(self, item):
            log.append("contains")
            return str.__contains__(self, item)

    for body in (Body("plain text " * 50), "x" * 5000):
        exc = _with_attrs(
            type("Plain", (Exception,), {}),
            status_code=403,
            code=None,
            body=body,
            request_id=GOOD_REQ,
        )
        got = anth.facts(exc)
        assert (got.status, got.error_type) == (403, T.permission)
    assert log == [], log


def test_r4c_claude_library_class_with_a_recording_getattribute():
    anthropic = pytest.importorskip("anthropic", reason="needs extra anthropic")
    import httpx2

    log: list[str] = []

    def getattribute(self, name):
        log.append(name)
        return object.__getattribute__(self, name)

    Rec = type("Rec", (anthropic.AuthenticationError,), {"__getattribute__": getattribute})
    resp = httpx2.Response(
        401, request=httpx2.Request("POST", "http://127.0.0.1:1/"), headers={"request-id": GOOD_REQ}
    )
    try:
        exc = Rec(
            "invalid key",
            response=resp,
            body={"error": {"type": "authentication_error", "message": "m"}},
        )
    except (TypeError, AttributeError, ValueError):  # fallback: no __init__
        exc = Rec.__new__(Rec)
        for k, v in (
            ("status_code", 401),
            ("request_id", GOOD_REQ),
            ("body", {"error": {"type": "authentication_error"}}),
        ):
            object.__setattr__(exc, k, v)
    del log[:]
    got = anth.facts(exc)
    assert (got.status, got.error_type) == (401, T.authentication)
    assert set(log) <= ALLOWED["anthropic"], set(log) - ALLOWED["anthropic"]


# ---- R15: one table test per table -------------------------------------------------------------------------------------

T_S = {
    429: T.rate_limit,
    401: T.authentication,
    403: T.permission,
    400: T.invalid_request,
    404: T.invalid_request,
    422: T.invalid_request,
    408: T.timeout,
} | {n: T.server_error for n in range(500, 600)}


def test_t_s_status_table_both_directions():
    assert dict(STATUS_ERROR_TYPE) == T_S
    for n in (99, 100, 399, 499, 600):
        assert status_error_type(n) is None
    assert [status_error_type(n) for n in (400, 401, 403, 404, 408, 422, 429, 500, 599)] == [
        T.invalid_request,
        T.authentication,
        T.permission,
        T.invalid_request,
        T.timeout,
        T.invalid_request,
        T.rate_limit,
        T.server_error,
        T.server_error,
    ]
    assert status_error_type(True) is None
    assert CODED_STATUSES == frozenset({400, 401, 403, 404, 422, 429})
    assert dict(ERROR_TYPE_CODE) == {
        T.rate_limit: Code.provider_rate_limit,
        T.throttled: Code.provider_rate_limit,
        T.quota: Code.provider_rate_limit,
        T.authentication: Code.provider_auth,
        T.permission: Code.provider_auth,
        T.invalid_request: Code.provider_invalid_request,
        T.not_found: Code.provider_invalid_request,
        T.timeout: Code.provider_timeout,
        T.overloaded: Code.provider_http,
        T.server_error: Code.provider_http,
        T.connection: Code.provider_http,
        T.other: Code.provider_http,
    }
    assert set(ERROR_TYPE_CODE) == set(T) and len(T) == 12
    assert dict(REQUEST_ID_SHAPES) == {
        "prefixed": r"req_[A-Za-z0-9]{8,36}",
        "uuid": r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
    }


T_C = {
    "rate_limit_error": T.rate_limit,
    "overloaded_error": T.overloaded,
    "invalid_request_error": T.invalid_request,
    "authentication_error": T.authentication,
    "permission_error": T.permission,
    "not_found_error": T.not_found,
    "api_error": T.server_error,
    "timeout_error": T.timeout,
    "billing_error": T.quota,
}
T_B = {
    "ThrottlingException": T.throttled,
    "ModelTimeoutException": T.timeout,
    "ServiceUnavailableException": T.server_error,
    "ValidationException": T.invalid_request,
    "AccessDeniedException": T.permission,
    "InternalServerException": T.server_error,
    "ModelErrorException": T.server_error,
    "ModelNotReadyException": T.throttled,
    "ResourceNotFoundException": T.not_found,
    "ServiceQuotaExceededException": T.quota,
}


def _claude(word, status=400):
    anthropic = pytest.importorskip("anthropic", reason="needs extra anthropic")
    cls = type("Rec", (anthropic.APIStatusError,), {})
    return _with_attrs(cls, status_code=status, request_id=None, body={"error": {"type": word}})


def _amazon(code, status=400):
    return _with_attrs(
        type("Rec", (Exception,), {}),
        response={"Error": {"Code": code}, "ResponseMetadata": {"HTTPStatusCode": status}},
    )


def test_t_c_claude_table_both_directions():
    pytest.importorskip("anthropic", reason="needs extra anthropic")
    assert dict(anth._TYPE) == T_C
    for word, want in T_C.items():
        assert anth.facts(_claude(word)).error_type is want
    assert anth.facts(_claude("something_new")).error_type is T.other


def test_t_b_amazon_table_both_directions():
    assert dict(bed._CODE_TYPE) == T_B
    for code, want in T_B.items():
        assert bed.facts(_amazon(code)).error_type is want
    assert bed.facts(_amazon("SomethingNew")).error_type is T.other


def test_t_n_amazon_classes_timeout_before_connection():
    import botocore.exceptions as be

    assert bed._TIMEOUT_CLASSES == (be.ConnectTimeoutError, be.ReadTimeoutError)
    assert bed._CONNECTION_CLASSES == (be.EndpointConnectionError, be.ConnectionClosedError)
    assert bed._CREDENTIAL_CLASSES == (be.NoCredentialsError, be.PartialCredentialsError)
    # ConnectTimeoutError derives from a connection error: the timeout test must win.
    assert (
        bed.facts(be.ConnectTimeoutError(endpoint_url="http://127.0.0.1:1")).error_type is T.timeout
    )
    assert bed.facts(be.ReadTimeoutError(endpoint_url="http://127.0.0.1:1")).error_type is T.timeout
    assert (
        bed.facts(be.EndpointConnectionError(endpoint_url="http://127.0.0.1:1")).error_type
        is T.connection
    )
    assert (
        bed.facts(be.ConnectionClosedError(endpoint_url="http://127.0.0.1:1")).error_type
        is T.connection
    )
    assert bed.facts(be.NoCredentialsError()).error_type is T.authentication
    assert (
        bed.facts(be.PartialCredentialsError(provider="p", cred_var="v")).error_type
        is T.authentication
    )


def test_t_l_a_65_character_key_is_never_looked_up(monkeypatch):
    """TYPE_NAME_MAX is part of the rule. Ticket R15 T-L says the key "is still ``other``"; the shared rule (ii) sends a longer
    string on to the class and status rules, so the assertion here is: the patched table entry is NOT used."""
    pytest.importorskip("anthropic", reason="needs extra anthropic")
    key = "k" * (TYPE_NAME_MAX + 1)
    monkeypatch.setitem(anth._TYPE, key, T.quota)
    monkeypatch.setitem(bed._CODE_TYPE, key, T.quota)
    assert anth.facts(_claude(key, 403)).error_type is T.permission
    assert bed.facts(_amazon(key, 403)).error_type is T.permission
    ok = "k" * TYPE_NAME_MAX
    monkeypatch.setitem(anth._TYPE, ok, T.quota)
    assert anth.facts(_claude(ok, 403)).error_type is T.quota  # exactly the bound is looked up
    assert TYPE_NAME_MAX == 64


# ---- R19: direct adapter calls --------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "adapter", [retry.default_facts, anth.facts, bed.facts], ids=["default", "anthropic", "bedrock"]
)
def test_r19_bare_exceptions_give_the_class_based_types(adapter):
    for exc, want in (
        (TimeoutError(), T.timeout),
        (urllib.error.URLError(TimeoutError()), T.timeout),
        (OSError(), T.connection),
        (ValueError(), None),
    ):
        got = adapter(exc)
        assert (got.status, got.error_type, got.request_id) == (None, want, None), (adapter, exc)


def test_r19_each_kind_accepts_only_its_own_request_id_shape():
    pytest.importorskip("anthropic", reason="needs extra anthropic")
    assert (
        anth.facts(
            _with_attrs(type("R", (Exception,), {}), status_code=401, request_id="ABCDEFGHIJ")
        ).request_id
        is None
    )
    assert (
        anth.facts(
            _with_attrs(type("R", (Exception,), {}), status_code=401, request_id=GOOD_REQ)
        ).request_id
        == GOOD_REQ
    )
    assert (
        anth.facts(
            _with_attrs(type("R", (Exception,), {}), status_code=401, request_id=GOOD_UUID)
        ).request_id
        is None
    )
    assert bed.facts(_amazon("ValidationException")).request_id is None

    def with_id(rid):
        return _with_attrs(
            type("R", (Exception,), {}),
            response={
                "Error": {"Code": "X"},
                "ResponseMetadata": {"HTTPStatusCode": 400, "RequestId": rid},
            },
        )

    assert bed.facts(with_id(GOOD_UUID)).request_id == GOOD_UUID
    assert bed.facts(with_id(GOOD_UUID + "\n")).request_id is None
    assert bed.facts(with_id(GOOD_REQ)).request_id is None


# ---- the neutral module and the other imports --------------------------------------------------------------------------------


def test_provider_facts_imports_only_the_standard_library_and_codes():
    import ast
    import pathlib

    tree = ast.parse(
        pathlib.Path(
            __import__("hadavin_sdk.llm.provider_facts", fromlist=["x"]).__file__
        ).read_text(encoding="utf-8")
    )
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            names.add(node.module or "")
    own = {n for n in names if n.split(".")[0] == "hadavin_sdk"}
    assert own == {"hadavin_sdk.codes", "hadavin_sdk.neverraise"}, own
    assert all(
        n.split(".")[0] in sys.stdlib_module_names | {"hadavin_sdk", "__future__"} for n in names
    ), names


def test_the_llm_and_diagnostic_modules_import_on_a_clean_interpreter_without_a_cycle():
    import pathlib

    ctx = multiprocessing.get_context(
        "spawn"
    )  # a fresh interpreter per order: nothing imported yet
    src = str(pathlib.Path(codes.__file__).parents[1])
    for order in (
        "hadavin_sdk.llm.protocol, hadavin_sdk.guard.diagnostic, hadavin_sdk.llm.retry",
        "hadavin_sdk.llm.retry, hadavin_sdk.guard.diagnostic, hadavin_sdk.llm.protocol",
        "hadavin_sdk.guard.diagnostic, hadavin_sdk.llm.provider_facts",
        "hadavin_sdk.llm.provider_facts",
    ):
        child = ctx.Process(
            target=import_in_order, args=(tuple(m.strip() for m in order.split(",")),)
        )
        child.start()
        child.join(timeout=60)
        assert child.exitcode == 0, (order, child.exitcode)
    # the diagnostic module never IMPORTS the llm package (its keys are strings)
    import ast

    tree = ast.parse(
        pathlib.Path(src, "hadavin_sdk", "guard", "diagnostic.py").read_text(encoding="utf-8")
    )
    imported = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)] + [
        a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names
    ]
    assert not [m for m in imported if m.startswith("hadavin_sdk.llm")], imported
