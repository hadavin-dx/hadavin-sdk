"""``guard/diagnostic.py``: Grammar A, the closed facts, the code rules, the locator and the golden lines."""

from __future__ import annotations

import asyncio
import random
import re
import socket
import sys
import types

import pytest

from hadavin_sdk import defaults, stats
from hadavin_sdk.codes import FACT_BOUNDS, FactKey, Phase, ProviderErrorType, Where
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.guard.diagnostic import (
    FALLBACK_FP,
    Diagnostic,
    SafeToken,
    class_name_of,
    diagnose,
    render,
)
from tests.data import c18a_hostile_corpus as corpus
from tests.data.c18a_oracle import grammar_ok

STEP = Where.extract


def line_of(exc: BaseException, **kw: object) -> str:
    return render(diagnose(exc, step=kw.pop("step", STEP), **kw))  # type: ignore[arg-type]


def test_grammar_a_shape_and_cap_boundary() -> None:
    d = diagnose(ValueError("x"), step=STEP)
    assert grammar_ok(render(d))
    base = Diagnostic("K", d.code, "extract", "-", (), "0" * 8)
    start = len(render(base)) + len(" key=") + 120 + len(" cause_kind=") + 120
    for total, kept in ((399, True), (400, True), (401, False)):
        n = total - start - len(" field=")
        text = "f" * n
        facts = (
            (FactKey.key, SafeToken.of("a" * 120, frozenset({"a" * 120}))),
            (FactKey.cause_kind, SafeToken.of("a" * 120, frozenset({"a" * 120}))),
            (FactKey.field, SafeToken.of(text, frozenset({text}))),
        )
        out = render(Diagnostic("K", d.code, "extract", "-", facts, "0" * 8))
        assert (" field=" in out) is kept, f"cap boundary at {total}: {len(out)}"
        assert len(out) <= defaults.DIAG_LINE_CHARS and " key=" in out and " fp=00000000" in out


def test_cap_drops_trailing_facts_and_keeps_the_head() -> None:
    d = diagnose(ValueError("x"), step=STEP)
    token = SafeToken.of("c" * 120, frozenset({"c" * 120}))
    facts = tuple(
        (k, token)
        for k in (FactKey.type, FactKey.key, FactKey.cause_kind, FactKey.field, FactKey.request_id)
    )
    out = render(Diagnostic("K", d.code, "extract", "-", facts, "0" * 8))
    assert len(out) <= defaults.DIAG_LINE_CHARS
    assert out.startswith("K: diag_v=1 code=") and " fp=00000000" in out
    assert out.count("=c") < 5


def test_diagnose_never_raises_on_exception() -> None:
    for row in (
        r
        for r in corpus.ROWS
        if r.status == "active" and r.kind == "exception" and r.expect != "propagates"
    ):
        import contextlib

        ctx = (
            corpus.CONTEXTS[row.spec["ctx"]]() if row.spec.get("ctx") else contextlib.nullcontext()
        )  # type: ignore[index]
        with ctx:
            diagnose(corpus.build_exception(row.spec), step=STEP)
    rng = random.Random(5)  # noqa: S311 - seeded test data, not security
    for _ in range(300):
        text = "".join(chr(rng.randrange(0, 0x3000)) for _ in range(rng.randrange(0, 40)))
        n = rng.randrange(0, 3)
        e = [ValueError, OSError, KeyError][n](text)
        assert grammar_ok(line_of(e))


def _hostile_errno(exc_type: type[BaseException]) -> OSError:
    class E(OSError):
        @property
        def errno(self) -> int:  # type: ignore[override]
            raise exc_type()

    return E(2, "x")


def test_baseexception_from_hostile_getattr_propagates() -> None:
    for exc_type in (asyncio.CancelledError, GeneratorExit, KeyboardInterrupt):
        with pytest.raises(exc_type):
            diagnose(_hostile_errno(exc_type), step=STEP)

    class F(OSError):
        @property
        def errno(self) -> int:  # type: ignore[override]
            raise RuntimeError("x")

    assert diagnose(F(2, "x"), step=STEP).fp == FALLBACK_FP


def test_non_exception_baseexception_passed_in_is_foreign() -> None:
    out = line_of(KeyboardInterrupt("x"))
    assert out.startswith("KeyboardInterrupt: ") and "code=foreign_exception" in out


def test_fallback_fp_is_pinned() -> None:
    assert FALLBACK_FP == "2a1e659d", "the fallback fp changed"
    out = render(
        diagnose(corpus.build_exception({"factory": "getattr_raises", "args": ("x",)}), step=STEP)
    )
    assert out == "unknown: diag_v=1 code=foreign_exception step=extract at=- fp=2a1e659d"


def test_str_repr_args_getitem_notes_are_never_called() -> None:
    reads: list[str] = []
    names = (
        "args",
        "__notes__",
        "__cause__",
        "__context__",
        "filename",
        "filename2",
        "strerror",
        "doc",
        "msg",
        "message",
    )

    class Spy(OSError):
        def __getattribute__(self, name: str) -> object:
            if name in names:
                reads.append(name)
            return super().__getattribute__(name)

        def __str__(self) -> str:
            reads.append("__str__")
            return "x"

        def __repr__(self) -> str:
            reads.append("__repr__")
            return "x"

    e = Spy(2, "Quentin")
    diagnose(e, step=STEP)
    assert reads == [], f"the exception was read: {reads}"


def test_facts_bounds_table() -> None:
    for key, (lo, hi) in FACT_BOUNDS.items():
        for value, kept in ((lo - 1, False), (lo, True), (hi, True), (hi + 1, False)):
            out = line_of(ValueError("x"), facts={key: value})
            assert (f" {key.value}={value}" in out) is kept, (
                f"{'kept' if kept else 'dropped'} {key.value}={value}: {out}"
            )
        assert f" {key.value}=" not in line_of(ValueError("x"), facts={key: True}), (
            f"a bool was printed as the number {key.value}"
        )
        assert f" {key.value}=" not in line_of(ValueError("x"), facts={key: "5"})  # type: ignore[dict-item]


def test_fact_patterns_use_fullmatch() -> None:
    assert SafeToken.sqlstate("28P01\n") is None, "a sqlstate with a trailing newline was accepted"
    assert SafeToken.sqlstate("28P01") is not None
    assert SafeToken.of("a\n", frozenset({"a\n"})) is None


def test_safe_token_lying_str_subclass() -> None:
    class Liar(str):
        def __eq__(self, other: object) -> bool:
            return True

        def __hash__(self) -> int:
            return 1

    assert SafeToken.of(Liar("x"), frozenset({"abc"})) is None
    with pytest.raises(TypeError):
        SafeToken("x")


def test_more_than_12_facts_keeps_priority_12() -> None:
    facts = {k: lo for k, (lo, _hi) in FACT_BOUNDS.items()}
    facts[FactKey.retryable] = True  # type: ignore[assignment]
    facts[FactKey.provider_error_type] = ProviderErrorType.timeout  # type: ignore[assignment]
    d = diagnose(ValueError("x"), step=STEP, facts=facts)  # type: ignore[arg-type]
    assert len(d.facts) == 12
    order = [k for k, _ in d.facts]
    assert order == sorted(order, key=list(FactKey).index)
    assert FactKey.duration_ms not in order and FactKey.http_status in order


def test_facts_read_from_exc_only() -> None:
    inner = OSError(5, "x")
    try:
        try:
            raise inner
        except OSError as e:
            raise ConfigError("x") from e
    except ConfigError as outer:
        out = line_of(outer)
    assert "code=config_invalid" in out and "errno" not in out
    # an exception that is no OSError takes no fact from the OSError it was raised from
    try:
        try:
            raise OSError(5, "x")
        except OSError as e:
            raise RuntimeError("x") from e
    except RuntimeError as outer:
        out = line_of(outer)
    assert out.startswith("RuntimeError: ") and "errno" not in out, f"facts from the cause: {out}"


def test_exception_group_takes_first_member_code() -> None:
    for kind, code in (
        ("timeout_first", "timeout"),
        ("nested", "foreign_exception"),
        ("raises", "foreign_exception"),
    ):
        out = line_of(corpus.build_exception({"factory": "group", "args": (kind, "Quentin")}))
        assert f"code={code} " in out and "Quentin" not in out, f"group {kind}: {out}"
    assert "code=foreign_exception" in line_of(ExceptionGroup("x", [ValueError("y")])), (
        "a group of a built-in error took a member code"
    )


def test_step_token_closed_to_tick_steps() -> None:
    from hadavin_sdk.codes import StepToken

    assert "step=sweep " in render(diagnose(ValueError("x"), step=StepToken.of("sweep")))
    for bad in ("jane_doe", "Sweep", "sweep\n", 3, None):
        assert "step=other " in render(diagnose(ValueError("x"), step=StepToken.of(bad)))
    assert "step=other " in render(diagnose(ValueError("x"), step="sweep"))  # type: ignore[arg-type]


def test_kind_identity_rule() -> None:
    assert class_name_of(ValueError("x")) == "ValueError"
    assert class_name_of(socket.gaierror(-2, "x")) == "socket.gaierror"
    assert class_name_of(type("Jane", (ValueError,), {})("x")) == "dynamic_class", (
        "a class not found under its own name was printed"
    )
    assert (
        class_name_of(type("N" * 81, (ValueError,), {"__module__": "builtins"})("x"))
        == "dynamic_class"
    )

    class Inner(Exception):
        pass

    assert class_name_of(Inner("x")) == "dynamic_class"  # a <locals> class
    assert class_name_of(ConfigError("x")) == "ConfigError"
    import pydantic

    assert class_name_of(pydantic.create_model("Jane_Doe")) == "dynamic_class"


def test_safe_token_holds_the_member_of_the_allowed_set_not_the_callers_object() -> None:
    member = "ab" + "c" * 2
    allowed = frozenset({member})
    value = b"abcc".decode()  # equal to the member, a different object
    assert value == member and value is not member
    token = SafeToken.of(value, allowed)
    assert token is not None and token.value is next(iter(allowed)), (
        "the token holds the caller's object"
    )


def test_locator_and_fp() -> None:
    def run() -> str:
        try:
            stats.upper_error_bound(5, 3)
        except ValueError as e:
            return line_of(e)
        raise AssertionError

    out = run()
    assert (
        out
        == f"ValueError: diag_v=1 code=internal_bug step=extract at=stats.py:{re.search(r'stats.py:(\d+)', out).group(1)} fp=ed342ffb"
    )  # type: ignore[union-attr]
    assert "at=-" in line_of(corpus._f_compiled("made_up.py", "x", None))


def _raised_in_stats(source: str, inner: str | None = None, **names: object) -> BaseException:
    """Run ``source`` as a function ``_p5a_probe`` in the real namespace of ``stats`` (own code by every frame rule) and return what it raises.
    ``inner`` is compiled under a made-up file name (frame rule c: not counted) and defines ``_p5a_inner``, for ``source`` to call."""
    d = vars(stats)
    d.update(names)
    try:
        if inner is not None:
            exec(compile(inner, "p5a_made_up.py", "exec"), d)  # noqa: S102
        exec(compile(source, stats.__file__, "exec"), d)  # noqa: S102
        with pytest.raises(Exception) as caught:
            d["_p5a_probe"]()
        return caught.value
    finally:
        d.pop("_p5a_probe", None)
        d.pop("_p5a_inner", None)
        for n in names:
            d.pop(n, None)


def test_internal_bug_is_decided_on_the_raise_frame() -> None:
    out = line_of(corpus._f_in_stats("same", "x"))
    assert "code=internal_bug" in out and "at=stats.py:" in out, f"own raise: {out}"
    # deterministic (no frozen-module detail): an own frame calls a frame compiled under a made-up file name, which is not counted
    deep = _raised_in_stats(
        "def _p5a_probe():\n    return _p5a_inner()\n",
        inner="def _p5a_inner():\n    return {}['x']\n",
    )
    assert "code=foreign_exception" in line_of(deep), f"uncounted inner frame: {line_of(deep)}"
    env = _raised_in_stats(
        "def _p5a_probe():\n    import os\n    return os.environ['P5A_NOT_SET_ANYWHERE']\n"
    )
    assert "code=foreign_exception" in line_of(env), f"os.environ from own code: {line_of(env)}"
    assert "code=foreign_exception" in line_of(corpus._f_in_stats("other_file_in_package", "x"))
    look = type("KeyError", (Exception,), {})
    fake = _raised_in_stats("def _p5a_probe():\n    raise P5A_LOOK('x')\n", P5A_LOOK=look)
    assert "code=foreign_exception" in line_of(fake), f"look-alike class: {line_of(fake)}"


def test_family_order_timeout_before_os_error() -> None:
    assert "code=timeout " in line_of(TimeoutError("x"))
    assert "code=os_error " in line_of(ConnectionRefusedError("x"))


def test_gaierror_gives_gai_not_errno() -> None:
    out = line_of(socket.gaierror(-2, "x"))
    assert out.startswith("socket.gaierror: diag_v=1 code=os_error step=extract at=- fp="), (
        f"gaierror head: {out}"
    )
    assert out.endswith(" gai=-2"), f"gaierror facts: {out}"


def test_psycopg_phase_is_sqlstate_class_only() -> None:
    errors = pytest.importorskip("psycopg.errors")
    for cls, sqlstate, phase in (
        (errors.InvalidPassword, "28P01", Phase.auth),
        (errors.UndefinedTable, "42P01", Phase.query),
        (errors.ConnectionFailure, "08006", Phase.connect),
    ):
        out = line_of(cls("x"))
        assert "code=db_error step=extract at=- fp=" in out and out.endswith(
            f" sqlstate={sqlstate} phase={phase.value}"
        ), out
        assert out.startswith(f"psycopg.errors.{cls.__name__}: ")


def test_psycopg_claimed_module_name_is_not_trusted() -> None:
    pytest.importorskip("psycopg")  # the check only runs when the driver is loaded
    fake = type(
        "OperationalError", (Exception,), {"__module__": "psycopg.errors", "sqlstate": "28P01"}
    )
    out = line_of(fake("x"))
    assert "code=db_error" not in out and "sqlstate" not in out, (
        f"a class that only claims the psycopg module name was trusted: {out}"
    )


def test_golden_lines_json_position_kept_and_dropped() -> None:
    head = r"json\.decoder\.JSONDecodeError: diag_v=1 code=validation_failed step=extract at=- fp=[0-9a-f]{8}"
    assert re.fullmatch(head + " position=3", line_of(corpus._f_json("m", "d", 3)))
    assert re.fullmatch(head, line_of(corpus._f_json("m", "d", 10**12))), (
        "an out-of-bounds position is dropped"
    )


# ---- R18: the provider read side. Instances are built with plain assignment so these rows run on the base too. ----------

_GOOD_REQ = "req_AbCd1234Ef56Gh78"


def _provider(cls=None, **attrs):
    from hadavin_sdk.llm import ProviderError

    err = (cls or ProviderError)("x")
    for name, value in attrs.items():
        setattr(err, name, value)
    return err


def _view(err) -> tuple[str, str]:
    text = render(diagnose(err, step=Where.model_call))
    code = re.search(r"code=([a-z_]+)", text)
    return (code.group(1) if code else ""), text


def test_provider_attributes_are_read_with_exact_types():
    good = {
        "status": 403,
        "error_type": ProviderErrorType.permission,
        "request_id": _GOOD_REQ,
        "retryable": False,
        "retry_count": 1,
    }
    code, text = _view(_provider(**good))
    assert code == "provider_auth"
    for line in (
        "http_status=403",
        "provider_error_type=permission",
        f"request_id={_GOOD_REQ}",
        "retryable=false",
        "retry_count=1",
    ):
        assert line in text, text
    bad = {
        "status": [True, 99, 600, "429"],
        "error_type": ["permission"],
        "request_id": ["r" * 41, _GOOD_REQ + "\n", "A" * 40, "a-b_c" * 8],
        "retryable": [1],
        "retry_count": [-1, 1001, True, "3"],
    }
    fact_name = {
        "status": "http_status",
        "error_type": "provider_error_type",
        "request_id": "request_id",
        "retryable": "retryable",
        "retry_count": "retry_count",
    }
    for field, values in bad.items():
        for value in values:
            _, text = _view(_provider(**{**good, field: value}))
            assert f"{fact_name[field]}=" not in text, (
                field,
                value,
                text,
            )  # the bad one is dropped
            for other, name in fact_name.items():
                if other != field:
                    assert f"{name}=" in text, (
                        field,
                        value,
                        other,
                        text,
                    )  # the valid ones are kept


def test_provider_codes_follow_status_then_type():
    from hadavin_sdk.llm import ProviderExhausted

    assert _view(_provider(status=429))[0] == "provider_rate_limit"  # (i) one attribute alone
    assert _view(_provider(error_type=ProviderErrorType.timeout))[0] == "provider_timeout"
    for status, want in (
        (401, "provider_auth"),
        (403, "provider_auth"),
        (400, "provider_invalid_request"),
        (404, "provider_invalid_request"),
        (422, "provider_invalid_request"),
        (500, "provider_http"),
        (408, "provider_http"),
    ):
        assert _view(_provider(status=status))[0] == want, status
    code, text = _view(
        _provider(
            ProviderExhausted,
            status=429,
            error_type=ProviderErrorType.rate_limit,
            request_id=_GOOD_REQ,
            retry_count=3,
        )
    )  # (iii)
    assert code == "provider_exhausted"
    assert all(
        x in text
        for x in (
            "http_status=429",
            "provider_error_type=rate_limit",
            f"request_id={_GOOD_REQ}",
            "retry_count=3",
        )
    ), text
    for status in (302, 418):  # (iv)
        assert (
            _view(_provider(status=status, error_type=ProviderErrorType.authentication))[0]
            == "provider_http"
        )
    want_by_type = {  # (v) no status, all 12 types, written out here
        "rate_limit": "provider_rate_limit",
        "throttled": "provider_rate_limit",
        "quota": "provider_rate_limit",
        "authentication": "provider_auth",
        "permission": "provider_auth",
        "invalid_request": "provider_invalid_request",
        "not_found": "provider_invalid_request",
        "timeout": "provider_timeout",
        "overloaded": "provider_http",
        "server_error": "provider_http",
        "connection": "provider_http",
        "other": "provider_http",
    }
    assert len(want_by_type) == len(ProviderErrorType) == 12
    for word, want in want_by_type.items():
        assert _view(_provider(error_type=ProviderErrorType(word)))[0] == want, word
    # a coded status beats the type, and the type is the fallback
    assert (
        _view(_provider(status=429, error_type=ProviderErrorType.authentication))[0]
        == "provider_rate_limit"
    )
    assert (
        _view(_provider(status=500, error_type=ProviderErrorType.authentication))[0]
        == "provider_http"
    )


def _row(cls: str, n: int) -> corpus.Row:
    return next(r for r in corpus.ROWS if r.id == f"HC-{cls}-{n:02d}")


def _golden(row: corpus.Row) -> None:
    import contextlib

    ctx = corpus.CONTEXTS[row.spec["ctx"]]() if row.spec.get("ctx") else contextlib.nullcontext()  # type: ignore[index]
    with ctx:
        out = line_of(corpus.build_exception(row.spec))
    assert re.fullmatch(str(row.spec["golden"]), out), f"frame rule: {out}"


def test_frame_rule_a_name_must_be_exactly_str() -> None:
    _golden(_row("locator_frames", 7))


def test_frame_rule_b_globals_must_be_the_module_namespace() -> None:
    _golden(_row("locator_frames", 8))


def test_frame_rule_c_filename_must_be_the_module_file() -> None:
    _golden(_row("locator_frames", 6))


def test_frame_check_that_raises_means_not_counted() -> None:
    _golden(_row("locator_frames", 10))
    _golden(_row("locator_frames", 9))


def test_long_traceback_is_foreign() -> None:
    import sys

    d = vars(stats)
    src = "def _p5a_probe_deep(n):\n    if n == 0:\n        raise KeyError('x')\n    return _p5a_probe_deep(n - 1)\n"
    old = sys.getrecursionlimit()
    sys.setrecursionlimit(6000)
    got: dict[int, str] = {}
    try:
        exec(compile(src, stats.__file__, "exec"), d)  # noqa: S102
        for depth in (20, defaults.DIAG_TB_STEPS + 50):
            try:
                d["_p5a_probe_deep"](depth)
            except KeyError as e:
                got[depth] = line_of(e)
    finally:
        d.pop("_p5a_probe_deep", None)
        sys.setrecursionlimit(old)
    assert "code=internal_bug " in got[20], f"short traceback: {got[20]}"
    assert "code=foreign_exception " in got[defaults.DIAG_TB_STEPS + 50], (
        f"long traceback: {got[defaults.DIAG_TB_STEPS + 50]}"
    )


def test_off_list_foreign_class_prints_foreign_class() -> None:
    row = _row("foreign_name", 1)
    with corpus.CONTEXTS["vendor_module"]():
        assert class_name_of(corpus.build_exception(row.spec)) == "foreign_class", (
            f"an off-list package class was printed ({row.id})"
        )


# --- golden T7: a secret that Vault does not hold (a 404) ---------------------------------------------------------------------
def _vault_error(status: int, name: str) -> BaseException:
    from hadavin_sdk.actions.secrets_vault import VaultProvider

    provider = VaultProvider("http://127.0.0.1:9", lambda _p: "t", path_prefix="app/")
    provider.authed = lambda *_a, **_k: (status, {})  # type: ignore[method-assign]  # the reader's one network call, stubbed
    with pytest.raises(Exception) as info:
        provider._fetch(name)
    return info.value


def _line_of_source(module_file: str, wanted: str) -> int:
    from pathlib import Path

    lines = Path(module_file).read_text(encoding="utf-8").splitlines()
    return 1 + next(i for i, text in enumerate(lines) if text.strip() == wanted)


def test_t7_a_vault_404_is_a_config_error_with_its_own_line_and_no_free_text() -> None:
    from hadavin_sdk.actions import secrets_vault

    secret_name = "pay-" + "quentin-abernathy"  # made up
    exc = _vault_error(404, secret_name)
    assert type(exc) is ConfigError
    line = _line_of_source(
        secrets_vault.__file__, 'raise ConfigError(f"secret {name!r} not found in Vault")'
    )
    out = line_of(exc, step=Where.extract)
    assert re.fullmatch(
        rf"ConfigError: diag_v=1 code=config_invalid step=extract at=actions/secrets_vault\.py:{line} fp=[0-9a-f]{{8}}",
        out,
    ), out
    assert secret_name not in out and "Vault" not in out and "not found" not in out
    assert grammar_ok(out)


def test_t7_a_vault_server_answer_is_a_vault_error_with_code_provider_http() -> None:
    from hadavin_sdk.actions import secrets_vault

    exc = _vault_error(500, "pay-" + "quentin-abernathy")
    assert type(exc) is secrets_vault.VaultError
    out = line_of(exc, step=Where.extract)
    assert re.fullmatch(
        r"VaultError: diag_v=1 code=provider_http step=extract at=actions/secrets_vault\.py:[0-9]{1,5} fp=[0-9a-f]{8}",
        out,
    ), out


# --- BN-3: a BaseException from a hostile attribute leaves ``diagnose`` --------------------------------------------------------
def _oserror_with_errno_that_raises(error: BaseException) -> OSError:
    class Hostile(OSError):
        @property
        def errno(self) -> int:  # type: ignore[override]
            raise error

    return Hostile("x")


def test_a_valueerror_in_errno_gives_the_fallback_and_every_propagating_row_propagates() -> None:
    """The ``BaseException`` case of a hostile ``errno`` is ``test_baseexception_from_hostile_getattr_propagates`` above; this adds the
    ``ValueError`` case (a line, not a crash) and every row in ``PROPAGATES_ROWS``."""
    out = line_of(_oserror_with_errno_that_raises(ValueError("x")))
    assert grammar_ok(out) and f"fp={FALLBACK_FP}" in out, f"not the fallback: {out}"
    by_id = {r.id: r for r in corpus.ROWS}
    for row_id in corpus.PROPAGATES_ROWS:
        with pytest.raises(BaseException) as info:
            diagnose(corpus.build_exception(by_id[row_id].spec), step=STEP)
        assert not isinstance(info.value, Exception)


# --- one read of the class names (a hostile metaclass cannot answer differently the second time) ---------------------------
def test_class_name_reads_the_module_name_once() -> None:
    reads: list[str] = []

    class Meta(type):
        @property
        def __module__(cls) -> str:  # type: ignore[override]
            reads.append("module")
            return "builtins" if len(reads) % 2 else "hadavin_sdk.errors"

    hostile = Meta("Hostile", (Exception,), {})
    out = class_name_of(hostile)
    assert reads.count("module") == 1, f"__module__ was read {len(reads)} times"
    assert out == "dynamic_class", out


def test_a_group_gives_the_code_of_its_first_member_and_no_member_facts() -> None:
    """``ExceptionGroup("x", [OSError(5, "x")])`` is ``os_error``, with no errno fact, and the member's ``errno`` is never read."""
    reads: list[str] = []

    class Member(OSError):
        @property
        def errno(self) -> int:  # type: ignore[override]
            reads.append("errno")
            return 5

    d = diagnose(ExceptionGroup("x", [Member(5, "x")]), step=STEP)
    assert d.code.value == "os_error", d.code
    assert FactKey.errno not in dict(d.facts), d.facts
    assert reads == [], "the group's member had its errno read"
    plain = diagnose(ExceptionGroup("x", [OSError(5, "x")]), step=STEP)
    assert plain.code.value == "os_error" and FactKey.errno not in dict(plain.facts)


def _traceback_of(n: int) -> types.TracebackType:
    frame = sys._getframe()
    tb = None
    for _ in range(n):
        tb = types.TracebackType(tb, frame, 0, 1)
    return tb  # type: ignore[return-value]


def test_links_keep_the_innermost_frames_only_up_to_the_step_cap() -> None:
    """BN-18: a hand-built traceback of 1 to ``DIAG_TB_STEPS`` links keeps at most ``DIAG_MAX_FRAMES`` of them and is not too long."""
    from hadavin_sdk.guard import diagnostic as dg

    for links in (1, 32, 33, 500, 2000):
        exc = ValueError("x").with_traceback(_traceback_of(links))
        kept, too_long = dg._links(exc)
        assert not too_long and len(kept) == min(links, defaults.DIAG_MAX_FRAMES), (
            f"{links} links: kept {len(kept)}, the frame cap is {defaults.DIAG_MAX_FRAMES}"
        )


def test_links_flag_a_traceback_over_the_step_cap_and_keep_nothing() -> None:
    from hadavin_sdk.guard import diagnostic as dg

    exc = ValueError("x").with_traceback(_traceback_of(defaults.DIAG_TB_STEPS + 1))
    assert dg._links(exc) == ([], True), "a traceback over the step cap was walked"
    d = diagnose(exc, step=STEP)
    assert d.code.value == "foreign_exception" and d.locator == "-"


def test_a_long_class_name_prints_a_fixed_word_not_the_name() -> None:
    """A class reachable under its own name but longer than ``DIAG_KIND_CHARS`` prints ``foreign_class`` (built-in) or ``dynamic_class`` (own)."""
    import builtins

    n = "L" * (defaults.DIAG_KIND_CHARS + 20)
    built = type(n, (Exception,), {"__module__": "builtins"})
    own = type(n, (Exception,), {"__module__": "hadavin_sdk.stats"})
    setattr(builtins, n, built)
    setattr(stats, n, own)
    try:
        got_built, got_own = class_name_of(built), class_name_of(own)
        assert got_built == "foreign_class", f"long built-in name printed (length {len(got_built)})"
        assert got_own == "dynamic_class", f"long own name printed (length {len(got_own)})"
    finally:
        delattr(builtins, n)
        delattr(stats, n)


def test_phase_of_each_class_of_sqlstate() -> None:
    from hadavin_sdk.guard.diagnostic import _phase_of

    assert _phase_of(None) is Phase.unknown, "no sqlstate"
    assert _phase_of(SafeToken.sqlstate("28P01")) is Phase.auth
    assert _phase_of(SafeToken.sqlstate("08006")) is Phase.connect
    assert _phase_of(SafeToken.sqlstate("42P01")) is Phase.query, "any other sqlstate is a query"


def test_own_code_reads_the_class_names_once() -> None:
    from hadavin_sdk.guard.diagnostic import _own_code

    reads: list[str] = []

    class Meta(type):
        @property
        def __module__(cls) -> str:  # type: ignore[override]
            reads.append("module")
            return "hadavin_sdk.errors" if len(reads) % 2 else "builtins"

    hostile = Meta("ConfigError", (Exception,), {})
    assert _own_code(hostile) is None, "a class that answers differently the second time is not own"
    assert reads.count("module") == 1, f"__module__ was read {reads.count('module')} times"


def test_render_stops_at_the_first_fact_that_does_not_fit() -> None:
    """Trailing facts are dropped from the first one that overflows: a later, shorter fact is not squeezed in after it."""
    d = diagnose(ValueError("x"), step=STEP)
    base = Diagnostic("K", d.code, "extract", "-", (), "0" * 8)
    start = len(render(base)) + len(" key=") + 120 + len(" cause_kind=") + 120
    n = defaults.DIAG_LINE_CHARS + 1 - start - len(" field=")
    big = "f" * n
    facts = (
        (FactKey.key, SafeToken.of("a" * 120, frozenset({"a" * 120}))),
        (FactKey.cause_kind, SafeToken.of("a" * 120, frozenset({"a" * 120}))),
        (FactKey.field, SafeToken.of(big, frozenset({big}))),
        (FactKey.request_id, SafeToken.of("r", frozenset({"r"}))),
    )
    out = render(Diagnostic("K", d.code, "extract", "-", facts, "0" * 8))
    assert " field=" not in out and " request_id=" not in out, f"a later fact after the cut: {out}"


def test_a_frame_of_this_package_without_a_locator_hands_over_to_the_next_own_frame() -> None:
    """``_locate`` skips an own frame that gives no locator (no line number) and takes the next outer own frame."""
    from hadavin_sdk.guard.diagnostic import _locate

    frame = sys._getframe()  # a frame of this test file: not an own frame
    own = vars(stats)["upper_error_bound"]
    own_frame = types.SimpleNamespace(f_globals=vars(stats), f_code=own.__code__)
    assert "stats.py" in own.__code__.co_filename
    outer = (own_frame, 7)
    inner = (own_frame, None)
    assert _locate([outer, inner])[0] == "stats.py:7", (
        "the inner frame has no line: the outer own frame is used"
    )
    assert _locate([inner]) == ("-", "-", "-")
    assert _locate([(frame, 1)]) == ("-", "-", "-")


def test_a_class_of_the_entry_script_prints_a_fixed_word() -> None:
    """``__main__`` is not in the list of printable packages: a class of the application's entry script is never printed by name."""
    main = sys.modules["__main__"]
    cls = type("EntryScriptError", (Exception,), {"__module__": "__main__"})
    main.EntryScriptError = cls  # type: ignore[attr-defined]
    try:
        got = class_name_of(cls)
    finally:
        del main.EntryScriptError  # type: ignore[attr-defined]
    assert got == "foreign_class", f"entry script class printed as {got}"


def test_the_psycopg_extra_is_installed_where_ci_runs() -> None:
    """``test_psycopg_claimed_module_name_is_not_trusted`` skips without the ``pg`` extra; CI installs every extra, so there it must not skip."""
    import os

    if os.environ.get("CI") == "true":
        import psycopg  # noqa: F401
