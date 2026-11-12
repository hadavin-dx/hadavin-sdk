"""The hostile corpus of the diagnostics redesign: test inputs built to get personal data past a safety check.

ASCII only: every hostile code point is a ``\\u....`` or ``\\U........`` escape (a meta-test fails on any other byte). Canaries are made-up
and built from parts. Each ``Row`` is one input; ``status`` says whether a test asserts on it today (``active``), waits for a later
package (``later``) or has nothing to test (``not_applicable``). Later packages append rows and bump ``CORPUS_STEP``.
"""

from __future__ import annotations

import contextlib
import json
import os
import sys
import types
import uuid
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel, ValidationError, field_validator

from hadavin_sdk import stats
from hadavin_sdk.codes import Code
from hadavin_sdk.errors import ConfigError

CORPUS_STEP: Final = "R3a"  # last redesign step merged; each P5b pull request bumps it
STEPS: Final = (
    "R1",
    "R1P",
    "R3a",
    "R3c",
    "R3b",
    "R2",
    "R5",
)  # in order: provider errors (R1P), config-error site table (R3a), writers and code scan (R3c, R3b), logging layer (R2), last step (R5)
CLASSES: Final = (
    "pii_plain", "pii_obfuscated", "pii_encoded", "ansi_c1", "email_unicode", "secret_shapes", "foreign_driver",
    "builtin_text", "pydantic_input", "json_decode", "hostile_class", "field_forging", "size_time", "config_detail",
    "locator_frames", "group", "own_class_spoof", "foreign_name", "ast_taint", "logging_layer", "writer_wiring",
    "classification", "provider_attrs", "process_findings",
)  # fmt: skip
# Minimum rows per class: active classes, later classes, not applicable.
MINIMUMS: Final[Mapping[str, int]] = {
    "pii_plain": 6, "pii_obfuscated": 10, "pii_encoded": 9, "ansi_c1": 7, "email_unicode": 6, "secret_shapes": 6,
    "foreign_driver": 8, "builtin_text": 10, "pydantic_input": 12, "json_decode": 4, "hostile_class": 16,
    "field_forging": 9, "size_time": 5, "config_detail": 4, "locator_frames": 10, "group": 3, "own_class_spoof": 7,
    "foreign_name": 3, "ast_taint": 6, "logging_layer": 5, "writer_wiring": 3, "classification": 2,
    "provider_attrs": 8, "process_findings": 2,
}  # fmt: skip
LEDGER_IDS: Final = tuple(f"BL-core-c18a-{n:03d}" for n in range(1, 52))


def _p(*parts: str) -> str:
    return "".join(parts)


# --- canaries (made up; built from parts) -------------------------------------------------------------------------------
NAME: Final = _p("Quentin", " ", "Abernathy")
EMAIL: Final = _p("quentin.abernathy", "@", "example", ".", "invalid")
IBAN: Final = _p("DE00", "1234", "5678", "9012", "3456", "78")
CARD: Final = _p("4929", "0000", "1111", "2222")
PHONE: Final = _p("+49 30 ", "5550142")
ADDRESS: Final = _p("17 Hollow", " Brook", " Lane")
HOST: Final = _p("db-quentin-abernathy", ".example", ".invalid")
USER: Final = _p("quentin", "_abernathy")
AWS: Final = _p("AKIA", "IOSFODNN7EXAMPLE")
SKKEY: Final = _p("sk-", "Zq" * 12)
JWT: Final = _p(
    "eyJ", "hbGciOiJIUzI1NiJ9", ".", "eyJzdWIiOiJ6enoifQ", ".", "p5aSignature0123456789"
)
PEM_BODY: Final = _p("ZZZFAKEPEM", "BODYp5a0123")
PEM: Final = _p(
    "-----BEGIN ", "PRIVATE", " KEY-----\n", PEM_BODY, "\n-----END ", "PRIVATE", " KEY-----"
)
PWPHRASE: Final = _p("correct horse", " battery")
GHTOKEN: Final = _p("gh", "p_", "Zz" * 18)
INVOICE: Final = _p("Total EUR 1,234.00 ", "Abernathy Textiles GmbH")
BIG: Final = 1 << 20


@dataclass(frozen=True, slots=True)
class Row:
    id: str
    cls: str
    ledger: tuple[str, ...]
    kind: Literal["exception", "validation", "source", "scenario"]
    status: Literal["active", "later", "not_applicable"]
    owner_step: str
    spec: Mapping[str, object]
    canaries: tuple[str, ...]
    expect: Literal["no_canary", "grammar", "bounded", "golden", "propagates"]
    expect_code: Code | None
    why: str
    reason: str = ""


# --- factories: every hostile object is built here ----------------------------------------------------------------------
class _StrSub(str):
    pass


class _Counting(Exception):
    """A chain link that counts every read of the names a diagnostic must never read."""

    reads: list[str] = []  # noqa: RUF012 - shared on purpose: one counter for the whole chain

    def __getattribute__(self, name: str) -> object:
        if name in ("args", "__cause__", "__context__", "__notes__", "__traceback__"):
            _Counting.reads.append(name)
        return super().__getattribute__(name)


def _chain(depth: int, text: str) -> BaseException:
    _Counting.reads.clear()
    head: BaseException = _Counting(text)
    for _ in range(depth):
        nxt = _Counting(text)
        nxt.__cause__ = head
        head = nxt
    _Counting.reads.clear()
    return head


class _MetaRaise(type):
    @property
    def __module__(cls) -> str:  # type: ignore[override]
        raise RuntimeError("module")


class _MetaName(type):
    @property
    def __name__(cls) -> str:  # type: ignore[override]
        raise RuntimeError("name")


class _MetaEq(type):
    def __eq__(cls, other: object) -> bool:
        raise RuntimeError("eq")

    def __hash__(cls) -> int:
        raise RuntimeError("hash")


class _MetaMro(type):
    @property
    def __mro__(cls) -> tuple[type, ...]:  # type: ignore[override]
        raise RuntimeError("mro")


class _RaisesErrno(OSError):
    @property
    def errno(self) -> int:  # type: ignore[override]
        raise KeyboardInterrupt


class _RaisesGetattr(OSError):
    def __getattr__(self, name: str) -> object:
        raise RuntimeError("getattr")


def _f_str_raises(text: str) -> BaseException:
    class E(Exception):
        def __str__(self) -> str:
            raise RuntimeError(text)

    return E(text)


def _f_repr_raises(text: str) -> BaseException:
    class E(Exception):
        def __repr__(self) -> str:
            raise RuntimeError(text)

    return E(text)


def _f_str_recursion(text: str) -> BaseException:
    class E(Exception):
        def __str__(self) -> str:
            return str(self)

    return E(text)


def _f_meta(meta: type, text: str) -> BaseException:
    return meta("E", (Exception,), {})(text)


def _f_dynamic(name: str, text: str) -> BaseException:
    return type(name, (ValueError,), {})(text)


def _f_dynamic_module(name: str, module: object, base: type, text: str) -> BaseException:
    return type(name, (base,), {"__module__": module})(text)


def _f_attrs_everywhere(text: str) -> BaseException:
    e = OSError(2, text, text)
    e.filename2 = text
    e.__notes__ = [text]
    e.doc = text  # type: ignore[attr-defined]
    e.msg = text  # type: ignore[attr-defined]
    e.message = text  # type: ignore[attr-defined]
    e.__cause__ = ValueError(text)
    e.__context__ = ValueError(text)
    return e


def _f_os(errno: int, text: str, filename: str) -> BaseException:
    return OSError(errno, text, filename)


def _f_json(msg: str, doc: str, pos: int) -> BaseException:
    return json.JSONDecodeError(msg, doc, pos)


def _f_json_real(doc: str) -> BaseException:
    try:
        json.loads(doc)
    except json.JSONDecodeError as e:
        return e
    raise AssertionError("the document parsed")


def _f_unicode_encode(text: str) -> BaseException:
    return UnicodeEncodeError("ascii", text + "\u00e9", 0, 1, "ordinal not in range for " + text)


def _f_deep() -> BaseException:
    try:
        json.loads("[" * 100000)
    except (RecursionError, json.JSONDecodeError) as e:
        return e
    raise AssertionError("parsed")


def _f_group(kind: str, text: str) -> BaseException:
    if kind == "timeout_first":
        return ExceptionGroup(text, [TimeoutError(text), ValueError(text)])
    if kind == "nested":
        return ExceptionGroup(text, [ExceptionGroup(text, [TimeoutError(text)])])

    class G(ExceptionGroup):
        @property
        def exceptions(self) -> tuple[BaseException, ...]:  # type: ignore[override]
            raise RuntimeError(text)

    return G(text, [ValueError(text)])


def _f_config_wrapped(inner: str) -> BaseException:
    return ConfigError(f"backends.records (fixture): {inner}")


def _f_provider(attr: str, value: object) -> BaseException:
    from hadavin_sdk.llm.protocol import ProviderError

    e = ProviderError(
        f"{value} {NAME}"
    )  # the name is the canary: a writer that prints the message leaks it
    setattr(e, attr, value)
    return e


def _retried(
    make: Callable[[], BaseException],
    label: str = "openai_compat",
    kind: str = "std",
    **hooks: object,
) -> BaseException:
    """The error ``with_retry`` raises when ``make()`` is raised from ``call`` (the provider-error rows run the real retry loop)."""
    import inspect

    from hadavin_sdk.llm.protocol import ProviderError
    from hadavin_sdk.llm.retry import with_retry
    from tests.provider_wire_helpers import kind_hooks

    def call() -> None:
        raise make()

    # A hook the loop does not take (``facts`` on the code before the provider-facts change) is left out, so a row fails on an assertion, never on a TypeError.
    accepted = inspect.signature(with_retry).parameters
    given = {k: v for k, v in (kind_hooks(kind) | hooks).items() if k in accepted}
    try:
        with_retry(call, label=label, max_attempts=3, sleep=lambda _s: None, **given)  # type: ignore[arg-type]
    except ProviderError as e:
        return e
    raise RuntimeError("the call did not fail")


def _f_retried_class(name: str) -> BaseException:
    return _retried(lambda: type(name, (Exception,), {})("boom"))


def _f_retried_meta() -> BaseException:
    return _retried(lambda: _MetaRaise("E", (Exception,), {})("boom"))


def _raw_bedrock(code: str, status: int, text: str) -> BaseException:
    """The Amazon error as the client library raises it, before the retry loop turns it into a checked provider error."""
    from botocore.exceptions import ClientError

    response = {
        "Error": {"Code": code, "Message": text},
        "ResponseMetadata": {"HTTPStatusCode": status},
    }
    return ClientError(response, "Converse")  # type: ignore[arg-type]


def _f_retried_bedrock(code: str, status: int, text: str) -> BaseException:
    return _retried(lambda: _raw_bedrock(code, status, text), label="bedrock", kind="bedrock")


# Rows whose factory runs the real retry loop hand ``diagnose`` an already checked error (its message has no free text), so the leaky
# subjects of the teeth test would never show the canary. For the rows listed here the teeth test reads the error BEFORE the loop.
RAW_FACTORIES: Final = {"retried_bedrock": _raw_bedrock}


def build_raw_exception(spec: Mapping[str, object]) -> BaseException | None:
    """The unchecked error of a row that runs through the retry loop, or None when the row has no such form."""
    raw = RAW_FACTORIES.get(spec["factory"])  # type: ignore[arg-type]
    return None if raw is None else raw(*spec["args"])  # type: ignore[operator]


def _f_retried_hook(variant: str) -> BaseException:
    import importlib

    try:  # the module did not exist before the provider-facts change: the row then runs without a facts class and fails on its assertions
        pf = importlib.import_module("hadavin_sdk.llm.provider_facts")
    except ImportError:
        pf = None
    facts_cls = getattr(pf, "ProviderFacts", None)
    sub = type("Sub", (facts_cls,), {}) if facts_cls is not None else object

    def raising(_e: BaseException) -> object:
        raise RuntimeError("adapter bug")

    hooks = {
        "raises": raising,
        "wrong_type": lambda _e: {"status": 429},
        "subclass": lambda _e: sub(429, None, None),
    }
    return _retried(lambda: ValueError("boom"), facts=hooks[variant])


def _f_retried_parse(variant: str) -> BaseException:
    make = {
        "value": lambda: ValueError("gemini answered with no candidates"),
        "key": lambda: KeyError("choices"),
    }[variant]
    return _retried(make, label="gemini")


def _f_system_exit(text: str) -> BaseException:
    return SystemExit(text)


def _f_driver(which: str) -> BaseException:
    text = f"connection to server at {HOST} failed: password authentication failed for user {USER}"
    if which == "psycopg":
        import psycopg

        return psycopg.errors.OperationalError(text)
    if which == "urllib3":
        import urllib3

        return urllib3.exceptions.NewConnectionError(None, text)  # type: ignore[arg-type]
    if which == "botocore":
        import botocore.exceptions as be

        return be.EndpointConnectionError(endpoint_url=f"https://{HOST}")
    if which == "anthropic":
        import anthropic

        return anthropic.APIConnectionError(message=text, request=None)  # type: ignore[arg-type]
    if which == "pydantic_core":
        return _validation(_Invoice, json.dumps({"total": USER, "vendor": HOST}))
    return type("Error", (Exception,), {"__module__": which})(text)  # the hand-built three


def _validation(model: type[BaseModel], document: str) -> BaseException:
    try:
        model.model_validate_json(document)
    except ValidationError as e:
        return e
    raise AssertionError("the document validated")


# --- the code-running factories of the locator rows. They run code in the real namespace of ``hadavin_sdk.stats`` and leave
# only names that start with ``_p5a_probe_``, deleted in ``finally`` --------------------------------------------------
_RAISE = "def _p5a_probe_raise():\n    raise KeyError({text!r})\n"
_OUTER = "def _p5a_probe_outer(fn):\n    return fn()\n"


def _f_compiled(filename: str, text: str, namespace_name: str | None) -> BaseException:
    ns: dict[str, object] = {} if namespace_name is None else {"__name__": namespace_name}
    try:
        exec(compile(f"raise KeyError({text!r})", filename, "exec"), ns)  # noqa: S102
    except KeyError as e:
        return e
    raise AssertionError("no raise")


def _f_string_code(text: str) -> BaseException:
    try:
        exec(f"raise KeyError({text!r})", {})  # noqa: S102
    except KeyError as e:
        return e
    raise AssertionError("no raise")


def _f_in_stats(filename_kind: str, text: str) -> BaseException:
    d = vars(stats)
    filename = stats.__file__
    if filename_kind == "other_file_in_package":
        filename = os.path.join(os.path.dirname(stats.__file__), "p5a_probe_made_up.py")
    try:
        exec(compile(_RAISE.format(text=text), filename, "exec"), d)  # noqa: S102
        d["_p5a_probe_raise"]()
    except KeyError as e:
        return e
    finally:
        d.pop("_p5a_probe_raise", None)
    raise AssertionError("no raise")


def _f_foreign_namespace(text: str) -> BaseException:
    ns: dict[str, object] = {"__name__": stats.__name__}
    try:
        exec(compile(_RAISE.format(text=text), stats.__file__, "exec"), ns)  # noqa: S102
        ns["_p5a_probe_raise"]()  # type: ignore[operator]
    except KeyError as e:
        return e
    raise AssertionError("no raise")


def _f_outer_own(inner_module_name: str, text: str) -> BaseException:
    d = vars(stats)
    inner_ns: dict[str, object] = {"__name__": inner_module_name}
    exec(compile(_RAISE.format(text=text), "<p5a>", "exec"), inner_ns)  # noqa: S102
    try:
        exec(compile(_OUTER, stats.__file__, "exec"), d)  # noqa: S102
        d["_p5a_probe_outer"](inner_ns["_p5a_probe_raise"])
    except KeyError as e:
        return e
    finally:
        d.pop("_p5a_probe_outer", None)
    raise AssertionError("no raise")


def _f_swapped_name(text: str) -> BaseException:
    d = vars(stats)
    try:
        exec(compile(_RAISE.format(text=text), stats.__file__, "exec"), d)  # noqa: S102
        d["_p5a_probe_raise"]()
    except KeyError as e:
        return e
    finally:
        d.pop("_p5a_probe_raise", None)
    raise AssertionError("no raise")


def _f_vendor_class(text: str) -> BaseException:
    mod = sys.modules["vendorx_p5a"]
    return mod.Jane_Doe_Err(text)  # type: ignore[attr-defined]


@contextlib.contextmanager
def _ctx_swap_stats_name() -> Iterator[None]:
    d = vars(stats)
    real = d["__name__"]
    d["__name__"] = _StrSub(real)
    try:
        yield
    finally:
        d["__name__"] = real


@contextlib.contextmanager
def _ctx_novars_module() -> Iterator[None]:
    sys.modules["p5a_probe_novars"] = object()  # type: ignore[assignment]
    try:
        yield
    finally:
        sys.modules.pop("p5a_probe_novars", None)


@contextlib.contextmanager
def _ctx_vendor_module() -> Iterator[None]:
    mod = types.ModuleType("vendorx_p5a")
    mod.Jane_Doe_Err = type("Jane_Doe_Err", (ValueError,), {"__module__": "vendorx_p5a"})  # type: ignore[attr-defined]
    sys.modules["vendorx_p5a"] = mod
    try:
        yield
    finally:
        sys.modules.pop("vendorx_p5a", None)


@contextlib.contextmanager
def _ctx_main_class() -> Iterator[None]:
    main = sys.modules["__main__"]
    had = hasattr(main, "Jane_Doe_Main")
    main.Jane_Doe_Main = type("Jane_Doe_Main", (ValueError,), {"__module__": "__main__"})  # type: ignore[attr-defined]
    try:
        yield
    finally:
        if not had:
            del main.Jane_Doe_Main  # type: ignore[attr-defined]


def _f_main_class(text: str) -> BaseException:
    return sys.modules["__main__"].Jane_Doe_Main(text)  # type: ignore[attr-defined]


CONTEXTS: Final[Mapping[str, Callable[[], contextlib.AbstractContextManager[None]]]] = {
    "swap_stats_name": _ctx_swap_stats_name,
    "novars_module": _ctx_novars_module,
    "vendor_module": _ctx_vendor_module,
    "main_class": _ctx_main_class,
}


FACTORIES: Final[Mapping[str, Callable[..., BaseException]]] = {
    "value_error": ValueError,
    "key_error": KeyError,
    "runtime_error": RuntimeError,
    "type_error": TypeError,
    "attribute_error": AttributeError,
    "index_error": IndexError,
    "assertion_error": AssertionError,
    "import_error": ImportError,
    "os_error": _f_os,
    "config_error": ConfigError,
    "config_wrapped": _f_config_wrapped,
    "json_error": _f_json,
    "json_real": _f_json_real,
    "unicode_encode": _f_unicode_encode,
    "deep_json": _f_deep,
    "group": _f_group,
    "provider": _f_provider,
    "retried_class": _f_retried_class,
    "retried_meta": _f_retried_meta,
    "retried_bedrock": _f_retried_bedrock,
    "retried_hook": _f_retried_hook,
    "retried_parse": _f_retried_parse,
    "system_exit": _f_system_exit,
    "driver": _f_driver,
    "str_raises": _f_str_raises,
    "repr_raises": _f_repr_raises,
    "str_recursion": _f_str_recursion,
    "dynamic": _f_dynamic,
    "dynamic_module": _f_dynamic_module,
    "attrs_everywhere": _f_attrs_everywhere,
    "meta_module": lambda t: _f_meta(_MetaRaise, t),
    "meta_name": lambda t: _f_meta(_MetaName, t),
    "meta_eq": lambda t: _f_meta(_MetaEq, t),
    "meta_mro": lambda t: _f_meta(_MetaMro, t),
    "getattr_raises": lambda t: _RaisesGetattr(2, t),
    "errno_keyboard_interrupt": lambda t: _RaisesErrno(2, t),
    "str_sub_args": lambda t: ValueError(_StrSub(t)),
    "exc_in_args": lambda t: ValueError(ValueError(t)),
    "big_args": lambda t: ValueError(t + "x" * BIG),
    "zero_width": lambda t: ValueError(t + "\u200b" * 100000),
    "fdfa": lambda t: ValueError(t + "\ufdfa" * 19200),
    "big_message": lambda t: ValueError(t + "y" * BIG),
    "chain": lambda t: _chain(5000, t),
    "compiled": _f_compiled,
    "string_code": _f_string_code,
    "in_stats": _f_in_stats,
    "foreign_namespace": _f_foreign_namespace,
    "outer_own": _f_outer_own,
    "swapped_name": _f_swapped_name,
    "vendor_class": _f_vendor_class,
    "main_class": _f_main_class,
}  # fmt: skip


# --- models for the validation rows --------------------------------------------------------------------------------------
class _Invoice(BaseModel):
    model_config = ConfigDict(extra="forbid")
    total: int
    vendor: str


class _Lit(BaseModel):
    pick: Literal["a", "b"]


class _Cat(BaseModel):
    kind: Literal["cat"]
    name: str


class _Dog(BaseModel):
    kind: Literal["dog"]
    name: str


class _Pet(BaseModel):
    pet: Annotated[_Cat | _Dog, Field(discriminator="kind")]


class _Dict(RootModel[dict[str, int]]):
    pass


class _Uuid(BaseModel):
    ident: uuid.UUID


class _Custom(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def _check(cls, v: str) -> str:
        raise ValueError(f"bad value {v}")


class _Asserting(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def _check(cls, v: str) -> str:
        assert v == "ok", v
        return v


class _Many(BaseModel):
    a: int
    b: int
    c: int
    d: int
    e: int
    f: int
    g: int


class _Short(BaseModel):
    name: Annotated[str, Field(max_length=3)]


class _Color(Enum):
    red = "red"


class _Enumerated(BaseModel):
    color: _Color


MODELS: Final[Mapping[str, type[BaseModel]]] = {
    "invoice": _Invoice, "lit": _Lit, "pet": _Pet, "dict": _Dict, "uuid": _Uuid, "custom": _Custom,
    "asserting": _Asserting, "many": _Many, "short": _Short, "enumerated": _Enumerated,
}  # fmt: skip


def build_exception(spec: Mapping[str, object]) -> BaseException:
    """The exception of an ``exception`` row (the caller enters the row's context first, if it has one)."""
    return FACTORIES[spec["factory"]](*spec["args"])  # type: ignore[index, operator]


def build_validation_error(spec: Mapping[str, object]) -> BaseException:
    return _validation(MODELS[spec["model"]], spec["document"])  # type: ignore[index, arg-type]


# --- rows ---------------------------------------------------------------------------------------------------------------
_ROWS: list[Row] = []
_SEQ: dict[str, int] = {}


def _add(cls: str, kind: str, status: str, owner: str, spec: dict[str, object], canaries: tuple[str, ...], expect: str,
         code: Code | None, why: str, ledger: tuple[str, ...] = (), reason: str = "", rid: str | None = None) -> None:  # fmt: skip
    if rid is None:
        _SEQ[cls] = _SEQ.get(cls, 0) + 1
        rid = f"HC-{cls}-{_SEQ[cls]:02d}"
    _ROWS.append(
        Row(rid, cls, ledger, kind, status, owner, spec, canaries, expect, code, why, reason)
    )  # type: ignore[arg-type]


def exc(cls: str, factory: str, args: tuple[object, ...], canaries: tuple[str, ...], why: str, *, ledger: tuple[str, ...] = (),
        expect: str = "no_canary", code: Code | None = None, step: str = "extract", golden: str | None = None,
        ctx: str | None = None, owner: str = "R1", rid: str | None = None, variants: tuple[str, ...] = ()) -> None:  # fmt: skip
    spec: dict[str, object] = {"factory": factory, "args": args, "step": step}
    if variants:
        spec["variants"] = variants
    if golden is not None:
        spec["golden"] = golden
        expect = "golden"
    if ctx is not None:
        spec["ctx"] = ctx
    _add(cls, "exception", "active", owner, spec, canaries, expect, code, why, ledger, rid=rid)


def val(
    cls: str,
    model: str,
    document: str,
    canaries: tuple[str, ...],
    why: str,
    *,
    ledger: tuple[str, ...] = (),
) -> None:
    _add(
        cls,
        "validation",
        "active",
        "R1",
        {"model": model, "document": document},
        canaries,
        "no_canary",
        None,
        why,
        ledger,
    )


def later(cls: str, kind: str, owner: str, spec: dict[str, object], why: str, reason: str, *, ledger: tuple[str, ...] = (),
          canaries: tuple[str, ...] = ()) -> None:  # fmt: skip
    _add(cls, kind, "later", owner, spec, canaries, "no_canary", None, why, ledger, reason)


def L(n: int) -> tuple[str, ...]:
    return (f"BL-core-c18a-{n:03d}",)


E_, N_ = (EMAIL,), (NAME,)
GOLD_FALLBACK = r"unknown: diag_v=1 code=foreign_exception step=extract at=- fp=2a1e659d"

# pii_plain (6)
exc(
    "pii_plain",
    "value_error",
    (f"cannot send to {EMAIL}",),
    E_,
    "an e-mail address in args[0]",
    ledger=L(1),
)
exc("pii_plain", "value_error", (f"IBAN {IBAN} rejected",), (IBAN,), "an IBAN in args[0]")
exc("pii_plain", "runtime_error", (f"card {CARD} declined",), (CARD,), "a card number in args[0]")
exc("pii_plain", "value_error", (f"unknown payee {NAME}",), N_, "a person's name in args[0]")
exc("pii_plain", "type_error", (f"call back on {PHONE}",), (PHONE,), "a phone number in args[0]")
exc(
    "pii_plain",
    "value_error",
    (f"deliver to {ADDRESS}",),
    (ADDRESS,),
    "a street address in args[0]",
)

# pii_obfuscated (10): spellings the fold reads through
_IBAN_SPACED = " ".join(IBAN[i : i + 4] for i in range(0, len(IBAN), 4))
exc(
    "pii_obfuscated",
    "value_error",
    (f"IBAN {_IBAN_SPACED} rejected",),
    (IBAN,),
    "a spaced IBAN",
    ledger=L(11),
)
exc(
    "pii_obfuscated",
    "value_error",
    (f"mail {EMAIL.replace('@', chr(0x200B) + '@')}",),
    E_,
    "zero-width space inside an e-mail",
    ledger=L(23),
)
exc(
    "pii_obfuscated",
    "value_error",
    (f"mail {EMAIL.replace('@', chr(0xFF20))}",),
    E_,
    "a fullwidth at sign",
    ledger=L(28),
)
exc(
    "pii_obfuscated",
    "value_error",
    (f"mail {EMAIL.replace('a', chr(0x0430))}",),
    E_,
    "Cyrillic a for Latin a",
    ledger=L(39),
)
exc(
    "pii_obfuscated",
    "value_error",
    (f"mail {EMAIL.upper()}",),
    E_,
    "upper-case e-mail",
    ledger=L(44),
)
exc("pii_obfuscated", "value_error", (f"payee {NAME.upper()}",), N_, "an upper-case name")
exc(
    "pii_obfuscated",
    "value_error",
    (f"payee {NAME.replace('e', chr(0x0435))}",),
    N_,
    "Cyrillic e for Latin e in a name",
)
exc(
    "pii_obfuscated",
    "value_error",
    (f"mail {''.join(c + chr(0x0301) for c in EMAIL[:6])}{EMAIL[6:]}",),
    E_,
    "combining marks inside an e-mail",
)
exc(
    "pii_obfuscated",
    "value_error",
    (f"payee {NAME.replace(' ', chr(0xE0020) + ' ')}",),
    N_,
    "a tag character inside a name",
)
exc(
    "pii_obfuscated",
    "value_error",
    (f"card {CARD[:4]}-{CARD[4:8]}.{CARD[8:12]} {CARD[12:]}",),
    (CARD,),
    "a card number with mixed separators",
)

# pii_encoded (9): the oracle decodes these views
exc(
    "pii_encoded",
    "value_error",
    (f"mail {EMAIL.replace('@', '&commat;')}",),
    E_,
    "HTML entity with a semicolon",
    ledger=L(40),
)
exc(
    "pii_encoded",
    "value_error",
    (f"mail {EMAIL.replace('@', '&#64')}",),
    E_,
    "numeric HTML entity without a semicolon",
)
exc(
    "pii_encoded",
    "value_error",
    (f"mail {EMAIL.replace('@', '&#0000064;')}",),
    E_,
    "numeric HTML entity with padding",
)
exc(
    "pii_encoded",
    "value_error",
    (f"mail {EMAIL.replace('@', '%40')}",),
    E_,
    "percent-encoded at sign",
)
exc(
    "pii_encoded",
    "value_error",
    (f"mail {EMAIL.replace('@', '%2540')}",),
    E_,
    "double percent-encoded at sign",
)
exc(
    "pii_encoded",
    "value_error",
    (f"mail {EMAIL.replace('@', chr(92) + 'x40')}",),
    E_,
    "backslash x40",
    ledger=L(50),
)
exc(
    "pii_encoded",
    "value_error",
    (f"mail {EMAIL.replace('@', '&#64;')}",),
    E_,
    "numeric HTML entity with a semicolon",
)
exc(
    "pii_encoded",
    "value_error",
    (f"mail {EMAIL.replace('@', '=40')}",),
    E_,
    "quoted-printable at sign",
)
exc(
    "pii_encoded", "value_error", (f"mail {EMAIL.replace('@', '%u0040')}",), E_, "percent-u at sign"
)

# ansi_c1 (7)
_A, _B = EMAIL[:9], EMAIL[9:]
exc(
    "ansi_c1",
    "value_error",
    (f"mail {_A}\x1b{_B}",),
    E_,
    "a lone ESC inside an e-mail",
    ledger=L(13),
)
exc(
    "ansi_c1",
    "value_error",
    (f"key \x1b{AWS}",),
    (AWS,),
    "ESC and a capital letter before a key",
    ledger=L(27),
)
exc(
    "ansi_c1",
    "value_error",
    (f"mail {_A}\x1b[1;31m{_B}",),
    E_,
    "a CSI sequence with parameters inside an e-mail",
    ledger=L(36),
)
exc(
    "ansi_c1",
    "value_error",
    (f"card \x1b[{CARD[:4]}-{CARD[4:8]}-{CARD[8:12]}-{CARD[12:]}",),
    (CARD,),
    "ESC [ before digits",
    ledger=L(43),
)
exc(
    "ansi_c1",
    "value_error",
    (f"mail {_A}\u009b31m{_B}",),
    E_,
    "U+009B before a letter run",
    ledger=L(37),
)
exc(
    "ansi_c1",
    "value_error",
    (f"mail {_A}\u009d0;title\u0007{_B}",),
    E_,
    "U+009D (OSC) inside an e-mail",
)
exc(
    "ansi_c1",
    "value_error",
    (f"mail {_A}\x1b]0;x\x07{_B}",),
    E_,
    "an OSC sequence inside an e-mail",
)

# email_unicode (6)
exc(
    "email_unicode",
    "value_error",
    (f"mail {EMAIL.replace('quentin', 'quent' + chr(0x0456) + 'n')}",),
    E_,
    "Cyrillic i in the local part",
    ledger=L(14),
)
exc(
    "email_unicode",
    "value_error",
    (f"mail {EMAIL.replace('abernathy', 'abernathy' + chr(0x17B4))}",),
    E_,
    "an invisible Khmer vowel",
    ledger=L(20),
)
exc(
    "email_unicode",
    "value_error",
    (f"mail {EMAIL.replace('.', chr(0x3002))}",),
    E_,
    "ideographic full stops",
    ledger=L(35),
)
exc(
    "email_unicode",
    "value_error",
    (f"mail {EMAIL.replace('@', chr(0xFF20)).replace('.', chr(0xFF0E))}",),
    E_,
    "fullwidth at sign and dots",
    ledger=L(49),
)
exc(
    "email_unicode",
    "value_error",
    ("mail jos\u00e9.abernathy@example.invalid",),
    ("jos\u00e9.abernathy@example.invalid",),
    "an accented local part",
)
exc(
    "email_unicode",
    "value_error",
    (f"mail {EMAIL.replace('example', 'ex' + chr(0x0430) + 'mple')}",),
    E_,
    "Cyrillic a in the domain",
)

# secret_shapes (6)
exc("secret_shapes", "value_error", (f"key {AWS}",), (AWS,), "the AWS example key", ledger=L(24))
exc("secret_shapes", "value_error", (f"key {SKKEY}",), (SKKEY,), "an sk- shaped key")
exc("secret_shapes", "value_error", (f"token {JWT}",), (JWT,), "a JWT shaped token")
exc("secret_shapes", "value_error", (f"key {PEM}",), (PEM_BODY,), "a PEM block")
exc(
    "secret_shapes",
    "value_error",
    (_p("pass", "word", '="', PWPHRASE),),
    (PWPHRASE,),
    "an unterminated quote after a password assignment",
)
exc(
    "secret_shapes", "value_error", (f"token {GHTOKEN}",), (GHTOKEN,), "a GitHub token shaped value"
)

# foreign_driver (8): 5 real classes, 3 hand-built (not the real class)
_DRV = (HOST, USER)
for _d in ("psycopg", "urllib3", "botocore", "anthropic", "pydantic_core"):
    exc(
        "foreign_driver",
        "driver",
        (_d,),
        _DRV,
        f"the real {_d} error with a host and a user",
        ledger=L(2) if _d == "psycopg" else (),
    )
for _d in ("httpx", "openai", "sqlalchemy.exc"):
    exc("foreign_driver", "driver", (_d,), _DRV, f"not the real class: a hand-built error claiming module {_d}", expect="golden",
        golden=r"dynamic_class: diag_v=1 code=foreign_exception step=extract at=- fp=[0-9a-f]{8}")  # fmt: skip

# builtin_text (10)
exc(
    "builtin_text",
    "value_error",
    (f"could not convert string to float: {INVOICE!r}",),
    (INVOICE,),
    "a ValueError quoting an invoice line",
    ledger=L(22),
)
exc("builtin_text", "key_error", (NAME,), N_, "a KeyError holding a document field")
exc("builtin_text", "unicode_encode", (f"{NAME} ",), N_, "a UnicodeEncodeError over a name")
exc(
    "builtin_text",
    "import_error",
    (f"cannot import name {NAME!r}",),
    N_,
    "an ImportError with a name",
)
exc(
    "builtin_text",
    "attribute_error",
    (f"'dict' object has no attribute {NAME!r}",),
    N_,
    "an AttributeError with a name",
)
exc(
    "builtin_text",
    "index_error",
    (f"row for {EMAIL} out of range",),
    E_,
    "an IndexError with an e-mail",
)
exc(
    "builtin_text",
    "type_error",
    (f"unsupported operand for {INVOICE!r}",),
    (INVOICE,),
    "a TypeError with an invoice line",
)
exc("builtin_text", "assertion_error", (f"expected {NAME}",), N_, "an AssertionError with a name")
exc(
    "builtin_text",
    "os_error",
    (2, "No such file", f"/data/{NAME.replace(' ', '_')}.pdf"),
    (NAME.replace(" ", "_"),),
    "an OSError with a file name",
)
exc(
    "builtin_text",
    "system_exit",
    (f"stopping for {NAME}",),
    N_,
    "a SystemExit passed in (not an Exception)",
    ledger=L(51),
    expect="grammar",
    code=Code.foreign_exception,
)

# pydantic_input (12)
val(
    "pydantic_input",
    "invoice",
    json.dumps({"total": f"{NAME} units", "vendor": "x"}),
    N_,
    "int_parsing quoting the input",
    ledger=L(21),
)
val(
    "pydantic_input",
    "invoice",
    json.dumps({"total": 1, "vendor": "x", NAME: 1}),
    N_,
    "extra_forbidden with the stray key",
    ledger=L(29),
)
val("pydantic_input", "lit", json.dumps({"pick": EMAIL}), E_, "literal_error quoting the input")
val(
    "pydantic_input",
    "pet",
    json.dumps({"pet": {"kind": NAME}}),
    N_,
    "discriminated union with a wrong tag",
    ledger=L(38),
)
val(
    "pydantic_input", "dict", json.dumps({NAME: "not a number"}), N_, "a RootModel[dict] key in loc"
)
val("pydantic_input", "uuid", json.dumps({"ident": NAME}), N_, "uuid_parsing quoting the input")
val(
    "pydantic_input",
    "custom",
    json.dumps({"name": NAME}),
    N_,
    "a custom validator error with the value",
)
val(
    "pydantic_input",
    "asserting",
    json.dumps({"name": NAME}),
    N_,
    "an assertion error with the value",
)
val(
    "pydantic_input",
    "many",
    json.dumps({"a": NAME}),
    N_,
    "seven errors: the first quotes the input",
)
val("pydantic_input", "invoice", f"{{{EMAIL} garbage", E_, "json_invalid quoting the text")
val("pydantic_input", "short", json.dumps({"name": NAME}), N_, "string_too_long quoting the input")
val(
    "pydantic_input",
    "enumerated",
    json.dumps({"color": EMAIL}),
    E_,
    "an enum error quoting the input",
)

# json_decode (4)
exc(
    "json_decode",
    "json_error",
    (EMAIL, NAME, 5),
    (EMAIL, NAME),
    "msg and doc carry canaries",
    ledger=L(42),
    code=Code.validation_failed,
)
exc(
    "json_decode",
    "json_real",
    (json.dumps({"n": NAME})[:-1] + ' "x"}',),
    N_,
    "a real parse error over a document with a name",
    code=Code.validation_failed,
)
exc("json_decode", "json_error", (EMAIL, NAME, 10**12), (EMAIL, NAME), "a position out of bounds is dropped", golden=r"json\.decoder\.JSONDecodeError: diag_v=1 code=validation_failed step=extract at=- fp=[0-9a-f]{8}")  # fmt: skip
exc(
    "json_decode",
    "json_error",
    (EMAIL.replace("@", "%40"), NAME.upper(), 0),
    (EMAIL, NAME),
    "msg and doc in encoded spellings",
    code=Code.validation_failed,
)

# hostile_class (16)
exc(
    "hostile_class",
    "dynamic",
    (NAME.replace(" ", "_"), "x"),
    (NAME.replace(" ", "_"),),
    "a dynamic class named like personal data",
    ledger=L(3),
)
exc("hostile_class", "meta_module", (NAME,), N_, "a class whose __module__ raises", ledger=L(19))
exc("hostile_class", "meta_name", (NAME,), N_, "a class whose __name__ raises")
exc("hostile_class", "str_raises", (NAME,), N_, "__str__ raises")
exc("hostile_class", "repr_raises", (NAME,), N_, "__repr__ raises")
exc("hostile_class", "meta_eq", (NAME,), N_, "a metaclass whose __eq__ and __hash__ raise")
exc(
    "hostile_class",
    "getattr_raises",
    (NAME,),
    N_,
    "an OSError whose __getattr__ raises",
    golden=GOLD_FALLBACK,
)
exc(
    "hostile_class",
    "meta_mro",
    (NAME,),
    N_,
    "a metaclass whose __mro__ raises",
    golden=GOLD_FALLBACK,
)
exc("hostile_class", "str_sub_args", (NAME,), N_, "args holding a str subclass")
exc("hostile_class", "exc_in_args", (NAME,), N_, "args holding another exception")
exc("hostile_class", "str_recursion", (NAME,), N_, "__str__ recurses without end")
exc("hostile_class", "big_args", (NAME,), N_, "a 1 MiB args[0]", expect="bounded")
exc("hostile_class", "attrs_everywhere", (NAME,), N_, "a canary in every attribute")
exc(
    "hostile_class",
    "dynamic_module",
    ("Err", [], ValueError, NAME),
    N_,
    "a __module__ that is a list",
)
exc(
    "hostile_class",
    "dynamic_module",
    ("Err", None, ValueError, NAME),
    N_,
    "a __module__ that is None",
)
exc(
    "hostile_class",
    "errno_keyboard_interrupt",
    (NAME,),
    N_,
    "errno raises KeyboardInterrupt: it must propagate",
    expect="propagates",
)

# field_forging (9)
_NL = f"{NAME.replace(' ', '_')}\ncode=config_invalid"
exc(
    "field_forging",
    "dynamic",
    (_NL, "x"),
    (NAME.replace(" ", "_"),),
    "a class name with a newline and a forged field",
    ledger=L(12),
)
exc(
    "field_forging",
    "dynamic",
    ("\x1b[31m" + NAME.replace(" ", "_"), "x"),
    (NAME.replace(" ", "_"),),
    "a class name with an ANSI colour",
    ledger=L(25),
)
exc(
    "field_forging",
    "dynamic",
    ("Err step=sweep fp=00000000 " + NAME.replace(" ", "_"), "x"),
    (NAME.replace(" ", "_"),),
    "a class name with forged step and fp",
    ledger=L(34),
)
exc("field_forging", "value_error", ("jane_doe",), ("jane_doe",), "a name-shaped step", step="jane_doe", golden=r"ValueError: diag_v=1 code=foreign_exception step=other at=- fp=[0-9a-f]{8}")  # fmt: skip
exc(
    "field_forging",
    "value_error",
    (NAME,),
    N_,
    "a step with a newline and a forged fp",
    step="sweep\nfp=00000000",
)
exc(
    "field_forging",
    "value_error",
    (NAME,),
    N_,
    "a step in the wrong case (variant_of=HC-field_forging-05)",
    step="Sweep",
)
exc(
    "field_forging",
    "dynamic",
    (NAME.replace(" ", "_") + "." * 3 + "a b", "x"),
    (NAME.replace(" ", "_"),),
    "a class name with dots and a space",
)
exc(
    "field_forging",
    "dynamic",
    ("N" * 81 + NAME.replace(" ", "_"), "x"),
    (NAME.replace(" ", "_"),),
    "an 81 character class name",
)
exc(
    "field_forging",
    "dynamic_module",
    ("Err", "a b\nc", ValueError, NAME),
    N_,
    "a module name with a space and a newline",
)

# size_time (5): algorithmic bounds only
exc("size_time", "big_message", (NAME,), N_, "a 1 MiB message", expect="bounded")
exc("size_time", "zero_width", (NAME,), N_, "100000 zero-width characters", expect="bounded")
exc("size_time", "fdfa", (NAME,), N_, "19200 U+FDFA characters", expect="bounded")
exc("size_time", "deep_json", (), (), "100000 nested brackets", expect="bounded")
_add("size_time", "exception", "active", "R1", {"factory": "chain", "args": (NAME,), "step": "extract", "reads_zero": True}, N_, "bounded", None, "a 5000 link cause chain whose links count their own reads", (L(16)))  # fmt: skip

# config_detail (4)
exc(
    "config_detail",
    "config_wrapped",
    (f"Value error, {NAME} at line 3",),
    N_,
    "a ConfigError wrapping text with a name",
    ledger=L(8),
    code=Code.config_invalid,
)
exc(
    "config_detail",
    "config_wrapped",
    (f"input_value={EMAIL}",),
    E_,
    "a ConfigError wrapping an input value",
    code=Code.config_invalid,
)
exc(
    "config_detail",
    "config_wrapped",
    (f"yaml: could not parse {INVOICE}",),
    (INVOICE,),
    "a ConfigError wrapping a yaml sentence",
    code=Code.config_invalid,
)
exc(
    "config_detail",
    "config_error",
    (f"bad key {NAME}",),
    N_,
    "a plain ConfigError with a name",
    code=Code.config_invalid,
)

# locator_frames (10)
_LP = NAME.replace(" ", "_")
_NF = r"KeyError: diag_v=1 code=foreign_exception step=extract at=- fp=[0-9a-f]{8}"
_OWN = r"KeyError: diag_v=1 code=foreign_exception step=extract at=stats\.py:2 fp=[0-9a-f]{8}"
exc(
    "locator_frames",
    "compiled",
    ("made_up_p5a_file.py", NAME, None),
    N_,
    "compile() with a made-up file name",
    ledger=L(41),
    golden=_NF,
)
exc("locator_frames", "string_code", (NAME,), N_, "code run from a string (<string>)", golden=_NF)
exc(
    "locator_frames",
    "compiled",
    (f"{_LP}.py", NAME, "p5a_probe_nowhere"),
    N_,
    "a file name that is a person's name",
    golden=_NF,
)
exc(
    "locator_frames",
    "compiled",
    ("a" * 300 + ".py", NAME, "p5a_probe_nowhere"),
    N_,
    "a very long path",
    golden=_NF,
)
exc(
    "locator_frames",
    "compiled",
    ("\u00e9\u00e8_p5a.py", NAME, "p5a_probe_nowhere"),
    N_,
    "a non-ASCII path",
    golden=_NF,
)
exc(
    "locator_frames",
    "in_stats",
    ("other_file_in_package", NAME),
    N_,
    "the real namespace under another file inside the package folder (rule c)",
    golden=_NF,
)
exc(
    "locator_frames",
    "swapped_name",
    (NAME,),
    N_,
    "__name__ is a str subclass equal to the real name (rule a)",
    golden=_NF,
    ctx="swap_stats_name",
)
exc(
    "locator_frames",
    "foreign_namespace",
    (NAME,),
    N_,
    "the real module name and file in a different namespace dict (rule b)",
    golden=_NF,
)
exc(
    "locator_frames",
    "outer_own",
    ("p5a_probe_nowhere", NAME),
    N_,
    "an inner frame whose __name__ names no module: the next own frame outward",
    golden=_OWN,
)
exc("locator_frames", "outer_own", ("p5a_probe_novars", NAME), N_, "an inner frame whose module entry has no vars(): the next own frame outward", golden=_OWN, ctx="novars_module")  # fmt: skip

# group (3)
exc(
    "group",
    "group",
    ("timeout_first", NAME),
    N_,
    "the first member's code is used",
    expect="grammar",
    code=Code.timeout,
)
exc(
    "group",
    "group",
    ("nested", NAME),
    N_,
    "a nested group is foreign_exception",
    expect="grammar",
    code=Code.foreign_exception,
)
exc(
    "group",
    "group",
    ("raises", NAME),
    N_,
    "a member list that raises is foreign_exception",
    expect="grammar",
    code=Code.foreign_exception,
)

# own_class_spoof (7)
exc("own_class_spoof", "dynamic_module", ("ConfigError", "hadavin_sdk.errors", Exception, NAME), N_, "a class named ConfigError claiming the real module", golden=r"dynamic_class: diag_v=1 code=foreign_exception step=extract at=- fp=[0-9a-f]{8}")  # fmt: skip
exc("own_class_spoof", "dynamic_module", ("Err", [], OSError, NAME), N_, "an OSError subclass whose __module__ is a list", expect="golden", golden=r"dynamic_class: diag_v=1 code=os_error step=extract at=- fp=[0-9a-f]{8}")  # fmt: skip
exc("own_class_spoof", "dynamic_module", ("Err", "psycopg.errors", Exception, NAME), N_, "a class claiming the psycopg module", golden=r"dynamic_class: diag_v=1 code=foreign_exception step=extract at=- fp=[0-9a-f]{8}")  # fmt: skip
exc("own_class_spoof", "dynamic_module", ("Err", "hadavin_sdk.nowhere", ValueError, NAME), N_, "a class claiming an own module that holds nothing", golden=r"dynamic_class: diag_v=1 code=foreign_exception step=extract at=- fp=[0-9a-f]{8}")  # fmt: skip
exc("own_class_spoof", "dynamic_module", ("Jane_Doe_Record", "hadavin_sdk.errors", ConfigError, NAME), N_, "an own-module subclass made on the fly keeps its base's code but prints dynamic_class", golden=r"dynamic_class: diag_v=1 code=config_invalid step=other at=- fp=[0-9a-f]{8}", step="other")  # fmt: skip
exc("own_class_spoof", "dynamic_module", ("Err", "builtins", ValueError, NAME), N_, "a class claiming the builtins module", golden=r"dynamic_class: diag_v=1 code=foreign_exception step=extract at=- fp=[0-9a-f]{8}")  # fmt: skip
exc("own_class_spoof", "dynamic_module", ("Err", "hadavin_sdk.errors", ValueError, NAME), N_, "an own-module class that is not in the table", golden=r"dynamic_class: diag_v=1 code=foreign_exception step=extract at=- fp=[0-9a-f]{8}")  # fmt: skip

# foreign_name (3)
exc("foreign_name", "vendor_class", (NAME,), N_, "a real class from a module off the allow-list", golden=r"foreign_class: diag_v=1 code=foreign_exception step=extract at=- fp=[0-9a-f]{8}", ctx="vendor_module")  # fmt: skip
exc("foreign_name", "dynamic_module", ("Jane_Doe", "json.decoder", ValueError, NAME), N_, "a dynamic class claiming an allow-listed module", golden=r"dynamic_class: diag_v=1 code=foreign_exception step=extract at=- fp=[0-9a-f]{8}")  # fmt: skip
exc("foreign_name", "main_class", (NAME,), N_, "a class from __main__ prints foreign_class", golden=r"foreign_class: diag_v=1 code=foreign_exception step=extract at=- fp=[0-9a-f]{8}", ctx="main_class")  # fmt: skip

# --- later rows: the input is recorded, the owning package adds the assertion -------------------------------------------
_LATER_AST = "ast_taint"
for _n, _src in (
    (4, "log.error('x', exc_info=True)"), (10, "_safe_log('x', str(exc))"), (15, "return str(e)"),
    (31, "self.last_error = str(e)"), (32, "_LOG.warning('x', e.errno)"), (48, "audit.emit_outcome('x', error=str(exc))"),
):  # fmt: skip
    later("ast_taint", "source", "R3c", {"code": _src, "verdict": "flag" if _n != 32 else "clean", "sink": "log"},
          f"the code scan must judge `{_src}`", "the code scan arrives with the code-scan step (R3c)", ledger=L(_n))  # fmt: skip
for _n, _what in ((26, "root handler formats exc_info"), (30, "root NullHandler hides records"), (45, "handleError prints raw record"),
                  (46, "third-party record text reaches stderr"), (47, "library warning prints raw")):  # fmt: skip
    later("logging_layer", "scenario", "R2", {"argv": ("tick",), "script": _what, "channel": "stderr", "env": {}},
          f"the logging layer must not print foreign text: {_what}", "the logging layer arrives with the logging-layer step (R2)", ledger=L(_n), canaries=N_)  # fmt: skip
for _n, _what in (
    (6, "tick writes last_error and log from one place"),
    (9, "extract writes DeadLetter.errors"),
    (17, "cli prints"),
):
    later("writer_wiring", "scenario", "R3c", {"argv": (), "script": _what, "channel": "store", "env": {}},
          f"the writers must use render(): {_what}", "the writers are wired in the writer step (R3c)", ledger=L(_n), canaries=N_)  # fmt: skip
for _n, _what in ((5, "sweep table gap"), (33, "ConfigError(f'...{exc}') site")):
    # Active since the corpus step R3a: the rows are driven by the site-table tests of the owning step (the config-error site table), not by ``diagnose``.
    _add("classification", "source", "active", "R3a", {"code": _what, "verdict": "classify", "sink": "any", "driver": "p5b2_sites"}, (),
         "no_canary", None, f"the site table must list: {_what}", L(_n))  # fmt: skip
# Step R1P: the eight provider_attrs rows run on the real attribute names. Each value is checked; the mapping to the design's cases
# is: status 429 = R18(i); status 99 = R18(ii); a plain-string error_type = R5/R18(ii); a request_id that is not a closed shape
# (underscored name, e-mail address) = R10/R18(ii); retryable True = R18(i); retryable "yes" = R3 (dropped).
_PROV = (("status", 429, "provider_rate_limit", N_), ("status", 99, "provider_http", N_),
         ("error_type", "rate_limit", "provider_http", N_), ("request_id", "req_" + NAME.replace(" ", "_"), "provider_http", N_),
         ("retryable", True, "provider_http", N_), ("retryable", "yes", "provider_http", N_),
         ("error_type", NAME, "provider_http", N_), ("request_id", EMAIL, "provider_http", E_))  # fmt: skip
for _attr, _val, _code, _can in _PROV:
    exc("provider_attrs", "provider", (_attr, _val), _can, f"a provider error with attribute {_attr}", code=Code(_code),
        step="model_call", owner="R1P")  # fmt: skip

for _n in (7, 18):
    _add("process_findings", "scenario", "not_applicable", "R1", {"argv": (), "script": "none", "channel": "none", "env": {}}, (), "no_canary",
         None, "a finding about the old branch's own evidence and tests", L(_n),
         "the new package's equivalents are the mutation plan and test_every_active_row_has_teeth")  # fmt: skip

# --- Step R1P rows 61-69: the hostile input is raised from ``call`` through the real retry loop ----------------------------------
_LONG_NAME = (NAME.replace(" ", "_") + "z" * 100)[:100]
_CODE63 = _p("AccessDenied", "Exception")
_GOLD63 = r"ProviderError: diag_v=1 code=provider_auth step=model_call at=llm/retry\.py:\d+ fp=[0-9a-f]{8} http_status=403 provider_error_type=permission retryable=false retry_count=1"
_P5 = {"owner": "R1P", "step": "model_call"}
exc("hostile_class", "retried_class", ("x y@z.example",), ("y@z.example",), "a dynamic class named with a space and an at sign", rid="HC-hostile_class-61",
    code=Code.provider_http, expect="grammar", **_P5)  # fmt: skip
exc("hostile_class", "retried_class", (_LONG_NAME,), (_LONG_NAME, NAME.replace(" ", "_")), "a legal identifier of 100 characters (the 100-character name)",
    rid="HC-hostile_class-62", code=Code.provider_http, expect="grammar", **_P5)  # fmt: skip
exc("hostile_class", "retried_bedrock", (_CODE63, 403, f"not allowed for {NAME}"), (NAME, _CODE63), "a modelled Amazon access-denied error",
    rid="HC-hostile_class-63", code=Code.provider_auth, golden=_GOLD63, **_P5)  # fmt: skip
exc("hostile_class", "retried_meta", (), N_, "a class whose module name raises when read", rid="HC-hostile_class-64",
    code=Code.provider_http, expect="grammar", **_P5)  # fmt: skip
exc("provider_attrs", "retried_hook", ("raises",), N_, "an adapter that raises; a hook returning the wrong type; a facts subclass",
    rid="HC-provider_attrs-68", code=Code.provider_http, expect="grammar", variants=("raises", "wrong_type", "subclass"), **_P5)  # fmt: skip
exc("hostile_class", "retried_parse", ("value",), N_, "Gemini parser errors from a malformed 200 reply", rid="HC-hostile_class-69",
    code=Code.provider_http, expect="grammar", variants=("value", "key"), **_P5)  # fmt: skip
for _rid, _cls, _case, _expect, _why in (
    ("HC-provider_attrs-65", "provider_attrs", "status_777", "no_canary", "a raw reply 'HTTP/1.1 777 IGNORE <canary>'"),
    ("HC-size_time-66", "size_time", "body_6mib", "bounded", "a 6 MiB 500 body holding the canary and an injected instruction"),
    ("HC-size_time-67", "size_time", "header_70000", "grammar", "a 70,000-byte header line"),
):  # fmt: skip
    _add(_cls, "scenario", "active", "R1P", {"driver": "p5b1_raw", "case": _case, "argv": (), "script": _why, "channel": "error", "env": {}},
         (NAME,), _expect, Code.provider_http if _expect == "grammar" else None, _why, rid=_rid)  # fmt: skip

ROWS: Final[tuple[Row, ...]] = tuple(_ROWS)
PROPAGATES_ROWS: Final = tuple(r.id for r in ROWS if r.expect == "propagates")
NO_OLD_WRITER_PATH: Final = frozenset[
    str
]()  # validation rows the real extraction model accepts (filled by the evidence run)
