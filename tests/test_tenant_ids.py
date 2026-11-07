"""A tenant id may not be spelled like a stage (order 126, q269 item b): refused where tenant ids are validated, so the
log value `tenant_id=prod` can only mean the stage and the redactor needs no mask for common words.

No tenant is created or stored anywhere on this branch (no tenant field in the config, the store, the CLI or a
backend), so the check sits in `hadavin_sdk.stages.check_tenant_id` and in the config type `TenantId`; the source-walk
test at the end fails when a field named like a tenant is added that does not use it.
"""

import ast
import re
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from hadavin_sdk.config import TenantId
from hadavin_sdk.guard.runmap import canonical
from hadavin_sdk.stages import STAGES, check_tenant_id, fold_name, is_stage_name

# Built from parts: the stage scan reads this file too.
OLD = "d" + "ev"
SRC = Path(__file__).resolve().parents[1] / "src" / "hadavin_sdk"


def fullwidth(word: str) -> str:
    return "".join(chr(0xFF00 + ord(c) - 0x20) for c in word)


REFUSED = [
    "demo",
    "pilot",
    "prod",
    "Demo",
    "PILOT",
    "Prod",
    "dEmO",
    "PROD",
    fullwidth("demo"),
    fullwidth("PILOT"),
    fullwidth("Prod"),
    chr(0x217E) + "emo",  # small roman numeral five hundred: NFKC gives d
    "demo" + chr(0x00A0),  # no-break space: NFKC gives a plain space, then cut
    " pilot ",
    chr(0x200B) + "prod",  # zero-width space (category Cf)
    "pi" + chr(0xAD) + "lot",  # soft hyphen (category Cf)
    "pro" + chr(0x2060) + "d",  # word joiner (category Cf)
]

ACCEPTED = [
    "acme",
    "acmecorp",
    "prod-1",
    "prod_eu",
    "demos",
    "demo-co",
    "pilots",
    "pilot1",
    "prod" + "uction",
    "preprod",
    OLD,  # the old stage name is not a stage now; it is an ordinary word
    "test",
    "p",
    "Ünïcode-Tenant",
    fullwidth("acme"),
]


def test_a_tenant_id_spelled_like_a_stage_is_refused():
    for value in REFUSED:
        assert is_stage_name(value), f"{value!a} was not read as a stage name"
        try:
            check_tenant_id(value)
        except ValueError as exc:
            assert "stage name" in str(exc), (
                f"{value!a} was refused without the stage-name sentence"
            )
        else:
            raise AssertionError(f"{value!a} was accepted as a tenant id")


def test_a_tenant_id_that_is_not_a_stage_name_is_accepted_unchanged():
    for value in ACCEPTED:
        assert not is_stage_name(value), f"{value!a} was read as a stage name"
        assert check_tenant_id(value) == value, f"{value!a} was changed or refused"


def test_a_tenant_id_that_is_not_a_string_is_refused():
    for value in [None, 5, b"demo", ["demo"]]:
        assert not is_stage_name(value), f"{value!a} was read as a stage name"
        try:
            check_tenant_id(value)
        except TypeError as exc:
            assert "must be a string" in str(exc), f"{value!a} was refused with another sentence"
        else:
            raise AssertionError(
                f"{value!a} was accepted as a tenant id although it is not a string"
            )


def test_the_refusal_names_the_three_stages_and_the_fold_and_does_not_echo_the_value():
    secretish = "PILOT" + chr(0x200B)
    with pytest.raises(ValueError) as caught:
        check_tenant_id(secretish)
    message = str(caught.value)
    for stage in STAGES:
        assert stage in message, f"the refusal does not name {stage}"
    assert "NFKC" in message and "case folding" in message
    assert "PILOT" not in message and chr(0x200B) not in message, "the refusal echoes the value"


def test_the_fold_is_the_redactors_canonical_form_then_casefolded():
    """The same NFKC and format-character removal the redactor (`runmap.canonical`) applies, so a spelling the redactor
    reads as a stage word is a stage word here."""
    for value in [*REFUSED, *ACCEPTED]:
        want = canonical(value).casefold().strip()
        assert fold_name(value) == want, (
            f"{value!a}: the fold differs from the redactor's canonical form"
        )


class _Tenant(BaseModel):
    tenant_id: TenantId


def test_the_config_type_refuses_a_stage_spelling_with_a_validation_error():
    for value in REFUSED:
        try:
            _Tenant(tenant_id=value)
        except ValidationError as exc:
            assert "stage name" in str(exc), (
                f"{value!a} was refused without the stage-name sentence"
            )
        else:
            raise AssertionError(f"the config type accepted {value!a}")


def test_the_config_type_accepts_an_ordinary_tenant_id():
    assert _Tenant(tenant_id="acmecorp").tenant_id == "acmecorp"


# --- the walk: no model may hold a tenant id outside the checked type --------------------------------------------


def unchecked_tenant_fields(source: str, name: str) -> list[str]:
    """Every field or parameter in `source` whose name holds `tenant` and that does not go through the check: a class
    field must be annotated `TenantId`; a function parameter needs a call to `check_tenant_id` in the function."""
    problems = []
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and re.search("tenant", node.target.id, re.IGNORECASE)
            and "TenantId" not in ast.unparse(node.annotation)
        ):
            problems.append(f"{name}:{node.lineno} field {node.target.id} is not a TenantId")
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args
            for arg in [*args.posonlyargs, *args.args, *args.kwonlyargs, args.vararg, args.kwarg]:
                if arg is not None and re.search("tenant", arg.arg, re.IGNORECASE):
                    body = "\n".join(ast.unparse(n) for n in node.body)
                    if "check_tenant_id" not in body:
                        problems.append(f"{name}:{node.lineno} parameter {arg.arg} is not checked")
    return problems


def test_the_walk_sees_a_tenant_field_that_skips_the_check():
    """Sensitivity control: the walk is not vacuously empty."""
    bad = "class M(BaseModel):\n    tenant_id: str\n    other: TenantId\n"
    assert len(unchecked_tenant_fields(bad, "x.py")) == 1, (
        "the walk missed a field of the wrong type"
    )
    bad_fn = "def make(tenant_id):\n    return tenant_id\n"
    assert len(unchecked_tenant_fields(bad_fn, "x.py")) == 1, (
        "the walk missed an unchecked parameter"
    )
    good = "class M(BaseModel):\n    tenant_id: TenantId\n    tenant_ids: list[TenantId]\n"
    assert unchecked_tenant_fields(good, "x.py") == [], "the walk flagged a TenantId field"
    good_fn = "def make(tenant_id):\n    return check_tenant_id(tenant_id)\n"
    assert unchecked_tenant_fields(good_fn, "x.py") == [], "the walk flagged a checked parameter"


def test_every_tenant_field_in_the_package_goes_through_the_check():
    problems = []
    files = sorted(SRC.rglob("*.py"))
    assert files, "no source files found"
    for path in files:
        problems += unchecked_tenant_fields(
            path.read_text(encoding="utf-8"), str(path.relative_to(SRC))
        )
    assert not problems, "\n".join(problems)
