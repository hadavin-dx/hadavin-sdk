"""The closed lists of ``codes.py``: the frozen code set, the fact tables and the table of this package's own exception classes."""

from __future__ import annotations

import ast
import builtins
import importlib
from pathlib import Path

import pytest

from hadavin_sdk import codes
from hadavin_sdk.codes import OWN_CODES, RESERVED_FOR, Code, FactKey
from hadavin_sdk.guard.diagnostic import diagnose, render

SRC = Path(__file__).resolve().parents[1] / "src" / "hadavin_sdk"
FROZEN = [
    "config_invalid",
    "store_unavailable",
    "store_conflict",
    "provider_http",
    "provider_timeout",
    "provider_rate_limit",
    "provider_invalid_request",
    "provider_auth",
    "provider_exhausted",
    "audit_unavailable",
    "egress_refused",
    "unqualified",
    "validation_failed",
    "scan_failed",
    "timeout",
    "os_error",
    "db_error",
    "internal_bug",
    "foreign_exception",
    "session_closed",
    "tool_refused",
]


def test_code_set_is_the_frozen_list() -> None:
    assert [c.value for c in Code] == FROZEN
    assert len(Code) == 21


def test_fact_priority_equals_fact_key_members() -> None:
    assert list(codes.FACT_PRIORITY) == list(FactKey)
    assert len(set(codes.FACT_PRIORITY)) == len(FactKey) == 20


D9_FACT_ORDER = (
    "type",
    "key",
    "http_status",
    "sqlstate",
    "phase",
    "cause_kind",
    "provider_error_type",
    "request_id",
    "retryable",
    "errno",
    "winerror",
    "gai",
    "count",
    "position",
    "line",
    "column",
    "field",
    "retry_count",
    "attempt",
    "duration_ms",
)


def test_fact_priority_order_is_the_d9_literal() -> None:
    """The 20 names of design D9, in order, written out here as one literal. The test above compares ``FACT_PRIORITY`` with ``FactKey``,
    so swapping two names in both would pass it; this one pins the order itself (BN-17)."""
    assert len(D9_FACT_ORDER) == 20 and len(set(D9_FACT_ORDER)) == 20
    assert tuple(k.value for k in codes.FACT_PRIORITY) == D9_FACT_ORDER, (
        "FACT_PRIORITY differs from the D9 literal order"
    )
    assert tuple(k.value for k in FactKey) == D9_FACT_ORDER, "FactKey differs from the D9 literal"


def test_fact_bounds_cover_the_number_keys() -> None:
    numbers = {
        "http_status",
        "retry_count",
        "attempt",
        "errno",
        "winerror",
        "gai",
        "count",
        "position",
        "line",
        "column",
        "duration_ms",
    }
    assert {k.value for k in codes.FACT_BOUNDS} == numbers
    assert len(numbers) == 11
    assert all(lo <= hi for lo, hi in codes.FACT_BOUNDS.values())


def test_tick_steps_match_tick_module() -> None:
    from hadavin_sdk.runtime import tick

    in_tick, in_codes = sorted(s.name for s in tick.STEPS), sorted(codes.TICK_STEPS)
    assert in_tick == in_codes, f"TICK_STEPS differ: tick has {in_tick}, codes has {in_codes}"


def test_codes_module_imports_only_the_standard_library() -> None:
    tree = ast.parse((SRC / "codes.py").read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, "a relative import"
            names.add((node.module or "").split(".")[0])
    import sys

    assert names <= set(sys.stdlib_module_names), sorted(names - set(sys.stdlib_module_names))


def test_every_code_member_is_reachable_or_reserved() -> None:
    reachable = set(OWN_CODES.values()) | {
        Code.validation_failed, Code.os_error, Code.db_error, Code.internal_bug, Code.foreign_exception, Code.timeout,
    }  # fmt: skip
    for code in Code:
        assert code in reachable or code.value in RESERVED_FOR, code
    for name in RESERVED_FOR:
        assert Code(name) not in set(OWN_CODES.values()), f"{name} is reserved but reachable"


def _visit(body: list[ast.stmt], prefix: str, module: str, found: dict[str, list[str]]) -> None:
    for node in body:
        if isinstance(node, ast.ClassDef):
            bases = [
                b.id if isinstance(b, ast.Name) else b.attr
                for b in node.bases
                if isinstance(b, (ast.Name, ast.Attribute))
            ]
            found[f"{module}:{prefix}{node.name}"] = bases
            _visit(node.body, f"{prefix}{node.name}.", module, found)


def _exception_classes() -> dict[str, list[str]]:
    """``module:Qualname`` -> simple base names, for every class under src whose bases lead to a built-in exception."""
    found: dict[str, list[str]] = {}
    for path in sorted(SRC.rglob("*.py")):
        rel = path.relative_to(SRC.parent).with_suffix("")
        module = ".".join(rel.parts).removesuffix(".__init__")

        _visit(ast.parse(path.read_text(encoding="utf-8")).body, "", module, found)
    simple = {k.split(":")[1].split(".")[-1]: v for k, v in found.items()}

    def is_exc(name: str, seen: frozenset[str] = frozenset()) -> bool:
        if name in seen:
            return False
        obj = getattr(builtins, name, None)
        if isinstance(obj, type):
            return issubclass(obj, BaseException)
        return any(is_exc(b, seen | {name}) for b in simple.get(name, []))

    return {k: v for k, v in found.items() if any(is_exc(b) for b in v)}


def test_every_own_exception_class_resolves_to_a_code() -> None:
    table_names = {k.split(":")[1].split(".")[-1] for k in OWN_CODES}
    classes = _exception_classes()
    assert len(classes) >= 20, classes
    missing = []
    for key, bases in classes.items():
        simple = key.split(":")[1].split(".")[-1]

        def resolved(name: str, seen: frozenset[str] = frozenset()) -> bool:
            if name in table_names:
                return True
            if name in seen:
                return False
            bases_of = [
                b for k, bs in classes.items() if k.split(":")[1].split(".")[-1] == name for b in bs
            ]
            return any(resolved(b, seen | {name}) for b in bases_of)

        if key not in OWN_CODES and not any(resolved(b) for b in bases):
            missing.append((key, bases, simple))
    assert not missing, missing


PINNED = {
    "hadavin_sdk.errors:ConfigError": "config_invalid",
    "hadavin_sdk.config:_RenamedStage": "config_invalid",
    "hadavin_sdk.k1b.bundle:BundleError": "config_invalid",
    "hadavin_sdk.llm.fake:UnknownRecording": "config_invalid",
    "hadavin_sdk.store.protocol:StoreUnavailable": "store_unavailable",
    "hadavin_sdk.store.protocol:StaleState": "store_conflict",
    "hadavin_sdk.store.protocol:NotFound": "store_conflict",
    "hadavin_sdk.runtime.runs:IllegalTransition": "store_conflict",
    "hadavin_sdk.audit.protocol:DuplicateEvent": "store_conflict",
    "hadavin_sdk.audit.anchors:AnchorConflict": "store_conflict",
    "hadavin_sdk.llm.protocol:ProviderError": "provider_http",
    "hadavin_sdk.approvals.slack_channel:SlackError": "provider_http",
    "hadavin_sdk.sources:SourceError": "provider_http",
    "hadavin_sdk.actions.secrets_vault:VaultError": "provider_http",
    "hadavin_sdk.llm.protocol:ProviderExhausted": "provider_exhausted",
    "hadavin_sdk.audit.protocol:AuditUnavailable": "audit_unavailable",
    "hadavin_sdk.guard.egress:EgressRefused": "egress_refused",
    "hadavin_sdk.runtime.agent_loop:Unqualified": "unqualified",
    "hadavin_sdk.runtime.agent_loop:InvalidRunId": "config_invalid",
    "hadavin_sdk.store.migration_numbers:SqlReadError": "internal_bug",
    "hadavin_sdk.k1b.loop:CallTimeout": "timeout",
    "hadavin_sdk.tools:ToolRefused": "tool_refused",
    "hadavin_sdk.guard.runmap:RedactionError": "scan_failed",
    "hadavin_sdk.guard.runmap:InputTooLarge": "scan_failed",
    "hadavin_sdk.guard.runmap:TooDeep": "scan_failed",
    "hadavin_sdk.guard.textnorm:TextnormError": "scan_failed",
}


def test_pinned_code_per_class() -> None:
    assert {k: v.value for k, v in OWN_CODES.items()} == PINNED, (
        "the table differs from the pinned rows"
    )
    wrong = []
    for key in sorted(PINNED):
        module, qual = key.split(":")
        cls = getattr(importlib.import_module(module), qual)
        exc = cls.__new__(cls)  # no constructor: some classes need arguments
        line = render(diagnose(exc, step=codes.Where.other))
        if f"code={PINNED[key]} " not in line:
            wrong.append((key, line))
    assert not wrong, f"a class does not give its pinned code: {wrong}"


def test_spoofed_class_gets_no_own_code() -> None:
    spoof = type("ConfigError", (Exception,), {"__module__": "hadavin_sdk.errors"})
    assert "code=foreign_exception " in render(diagnose(spoof("x"), step=codes.Where.other))


def test_instance_and_class_attribute_named_code_is_ignored() -> None:
    class E(Exception):
        code = "config_invalid"

    e = E("x")
    e.code = "config_invalid"  # type: ignore[attr-defined]
    assert "code=foreign_exception " in render(diagnose(e, step=codes.Where.other))


def test_textnorm_error_family_maps_to_scan_failed() -> None:
    from hadavin_sdk.guard.textnorm import TextnormError

    assert "code=scan_failed " in render(diagnose(TextnormError("x"), step=codes.Where.scan))


def test_step_token_is_closed_and_final() -> None:
    tok = codes.StepToken.of("sweep")
    assert isinstance(tok, codes.StepToken) and tok.value == "sweep"
    assert codes.StepToken.of("jane_doe") is codes.Where.other
    assert codes.StepToken.of("sweep\n") is codes.Where.other
    assert codes.StepToken.of(3) is codes.Where.other
    assert codes.StepToken.of("extract") is codes.Where.other, (
        "a Where name as text was accepted as a step token"
    )

    class Sub(str):
        pass

    assert codes.StepToken.of(Sub("sweep")) is codes.Where.other
    with pytest.raises(TypeError):
        type("X", (codes.StepToken,), {})


# --- tests the ticket lists (BN-9, BN-10 cut one) ------------------------------------------------------------------------------
def test_every_row_key_is_found_by_the_scan() -> None:
    """A rename of a class without a change of its row fails loudly: every row key is a class the AST scan finds (no exemption list)."""
    found = set(_exception_classes())
    lost = [key for key in OWN_CODES if key not in found]
    assert not lost, f"rows whose class the scan does not find: {lost}"


def test_phase_is_the_frozen_list() -> None:
    assert [p.value for p in codes.Phase] == ["auth", "connect", "query", "unknown"]


FROZEN_VALIDATION_TYPES = frozenset(
    {
        "missing", "extra_forbidden", "literal_error", "int_parsing", "float_parsing", "bool_parsing", "string_type", "int_type",
        "dict_type", "list_type", "too_short", "too_long", "greater_than", "less_than", "string_too_short", "string_too_long",
        "decimal_parsing", "date_parsing", "datetime_parsing", "enum", "url_parsing", "json_invalid", "model_type",
        "union_tag_invalid", "value_error", "assertion_error",
    }
)  # fmt: skip


def test_validation_types_are_the_frozen_list() -> None:
    assert len(FROZEN_VALIDATION_TYPES) == 26
    assert codes.VALIDATION_TYPES == FROZEN_VALIDATION_TYPES, (
        "the closed list of validation types changed"
    )
    assert (
        codes.VALIDATION_OTHER == "other" and codes.VALIDATION_OTHER not in codes.VALIDATION_TYPES
    )


def test_reserved_codes_name_their_package() -> None:
    assert dict(RESERVED_FOR) == {
        "session_closed": "P5c",
        "provider_rate_limit": "P5b1",
        "provider_auth": "P5b1",
        "provider_invalid_request": "P5b1",
        "provider_timeout": "P5b1",
    }
    for name in RESERVED_FOR:
        assert Code(name).value == name


def test_builtin_ancestry_never_beats_the_row() -> None:
    """A class with a row gets its row's code even when its built-in base (``PermissionError``, ``KeyError``) would give another."""
    from hadavin_sdk.guard.egress import EgressRefused
    from hadavin_sdk.llm.fake import UnknownRecording
    from hadavin_sdk.store.protocol import NotFound

    assert issubclass(EgressRefused, PermissionError)
    assert issubclass(NotFound, KeyError) and issubclass(UnknownRecording, KeyError)
    for cls, code in (
        (EgressRefused, "egress_refused"),
        (NotFound, "store_conflict"),
        (UnknownRecording, "config_invalid"),
    ):
        line = render(diagnose(cls.__new__(cls), step=codes.Where.other))
        assert f"code={code} " in line, line


def test_fact_bounds_values_are_pinned() -> None:
    from hadavin_sdk.codes import FACT_BOUNDS, FactKey

    got = {k.value: v for k, v in FACT_BOUNDS.items()}
    assert got == {
        "http_status": (100, 599),
        "retry_count": (0, 1000),
        "attempt": (0, 1000),
        "errno": (0, 20000),
        "winerror": (0, 20000),
        "gai": (-20000, 20000),
        "count": (0, 10**6),
        "position": (0, 10**9),
        "line": (0, 10**9),
        "column": (0, 10**9),
        "duration_ms": (0, 10**9),
    }, f"fact bounds changed: {got}"
    assert FactKey.count in FACT_BOUNDS
