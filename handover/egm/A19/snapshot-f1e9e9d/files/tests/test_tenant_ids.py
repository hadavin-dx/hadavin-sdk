"""An id may not be spelled like a stage word or be a common word the redactor does not sweep. Refused where ids are validated: `stages.check_id`, and the `config` types `TenantId`, `OrgId`,
`CustomerId`, `AccountId` and `UserId` that call it.

Why, in plain words. The redactor's labelled rule (`tenant_id=...`, also org, organisation, organization, customer,
account and user) masks the value after the label whatever the value is: `tenant_id=prod` becomes `tenant_id=<TENANT_1>`
even for a tenant named prod. What the redactor does not do is sweep OTHER copies of a value that is on its common-word
list (`hadavin_sdk.commonwords.COMMON_WORDS`, shared with `guard/redact.py`): a bare `prod` or `default` elsewhere in
the text stays readable, because `HTTP 500 in prod` must. So an id that is one of those words would keep every
unlabelled copy in clear. Refusing those words, and the three further stage words (`stages.STAGE_WORDS`), as ids
closes that; the WARDEN pin that `HTTP 500 in prod` stays readable is untouched.

The comparison is made after three steps, so a disguised spelling is read as the word: NFKC (Unicode compatibility
form: a full-width `prod` or a roman-numeral letter becomes plain letters), removal of the invisible format characters
(Unicode category Cf: zero-width space, soft hyphen, word joiner), then case folding and cutting surrounding white
space. The first two are the redactor's own `runmap.canonical`; the last two are added in `stages.fold_name`.

No id is created or stored anywhere on this branch, so the check guards no live path yet. The walk at the end of this
file fails when a field or parameter named like such an id is added without the check. Each pin test names the stage
mutant (tests/stage_mutants.py) that it kills.
"""

import ast
import importlib
import re
import unicodedata
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from hadavin_sdk import commonwords
from hadavin_sdk.commonwords import SWEEP_MIN_DIGITS, SWEEP_MIN_LENGTH
from hadavin_sdk.config import AccountId, CustomerId, OrgId, TenantId, UserId, _Strict
from hadavin_sdk.guard.redact import redact
from hadavin_sdk.guard.runmap import canonical, redact_text
from hadavin_sdk.stages import (
    _READABLE_ID,
    REFUSED_ID_WORDS,
    STAGE_WORDS,
    STAGES,
    check_id,
    check_tenant_id,
    fold_name,
)
from tests.fixtures.stage_words import NEW_WORDS, is_stage_name

redact_mod = importlib.import_module(
    "hadavin_sdk.guard.redact"
)  # `guard.redact` the name is the function

# Built from parts: the stage scan reads this file too.
OLD = "d" + "ev"
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "hadavin_sdk"


def fullwidth(word: str) -> str:
    return "".join(chr(0xFF00 + ord(c) - 0x20) for c in word)


# Spellings of demo, pilot and prod (after NFKC, removal of Cf characters, case folding and cutting white space).
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

# The three further stage words, and spellings of them.
REFUSED_STAGE_WORDS = [
    NEW_WORDS[0],
    NEW_WORDS[1].capitalize(),
    NEW_WORDS[2].upper(),
    fullwidth(NEW_WORDS[0]),
    NEW_WORDS[1][:5] + chr(0x200B) + NEW_WORDS[1][5:],
    f" {NEW_WORDS[2]} ",
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
    "preprod",
    "productions",
    "tester",
    "testing",
    "devops",
    "abc",
    "acme-7_b",
    "123456",
    "Acme-Corp_7",
]


def _refusal(check, value) -> str | None:
    """The text of the ValueError `check(value)` raises, None when it raises nothing. The assertions are made by the
    caller, outside the except block, so a failure shows one line and not a chained traceback."""
    try:
        check(value)
    except ValueError as exc:
        return str(exc)
    return None


def test_an_id_spelled_like_a_stage_is_refused():
    """Kills T1-T5 (each part of the fold, pilot), T6 (the stage-word sentence is lost) and T6b (nothing is refused)."""
    for value in REFUSED:
        assert is_stage_name(value), f"{value!a} was not read as a stage name"
        message = _refusal(check_tenant_id, value)
        assert message is not None, f"{value!a} was accepted as a tenant id"
        assert "stage word" in message, f"{value!a} was refused without the stage-word sentence"


def test_the_further_stage_words_are_refused_as_ids():
    """Kills T19 (a further stage word dropped from STAGE_WORDS; they are not all on the common-word list:
    development is not)."""
    for value in REFUSED_STAGE_WORDS:
        message = _refusal(check_tenant_id, value)
        assert message is not None, f"{value!a} was accepted as a tenant id"
        assert "stage word" in message, f"{value!a} was refused without the stage-word sentence"


def test_every_common_word_is_refused_as_an_id_in_every_spelling():
    """Kills T17 (the check ignores the common-word list). Before this change only demo, pilot and prod were refused."""
    assert commonwords.COMMON_WORDS, "the common-word list is empty"
    for word in sorted(commonwords.COMMON_WORDS):
        for value in (
            word,
            word.upper(),
            word.capitalize(),
            f" {word} ",
            word[:1] + chr(0x200B) + word[1:],
        ):
            for check in (check_tenant_id, check_id):
                try:
                    check(value)
                except ValueError as exc:
                    assert "may not be a" in str(exc), f"{value!a}: another sentence"
                else:
                    raise AssertionError(f"{value!a} was accepted as an id")


def test_an_id_that_is_not_a_refused_word_is_accepted_unchanged():
    """Kills T7 (a word that merely contains a stage word is read as one) and T7b (a word that merely contains a
    refused word is refused)."""
    for value in ACCEPTED:
        assert not is_stage_name(value), f"{value!a} was read as a stage name"
        assert value.strip().casefold() not in REFUSED_ID_WORDS
        try:
            got = check_tenant_id(value)
        except ValueError:
            raise AssertionError(
                f"{value!a} was refused as an id although it is an ordinary word"
            ) from None
        assert got == value, f"{value!a} was changed"
        assert check_id(value, "a user id") == value


def test_an_id_that_is_not_a_string_is_refused_with_a_value_error():
    """Kills T8 (a non-string is accepted) and T15 (is_stage_name loses its isinstance test and raises on a
    non-string). ValueError, so a pydantic AfterValidator turns it into a validation error (a TypeError would escape
    pydantic as itself)."""
    for value in [None, 5, b"demo", ["demo"]]:
        try:
            flagged = is_stage_name(value)
        except TypeError:
            raise AssertionError(f"{value!a}: is_stage_name raises on a non-string") from None
        assert not flagged, f"{value!a} was read as a stage name"
        try:
            check_tenant_id(value)
        except ValueError as exc:
            assert "must be a string" in str(exc), f"{value!a} was refused with another sentence"
        else:
            raise AssertionError(
                f"{value!a} was accepted as a tenant id although it is not a string"
            )


def test_the_refusal_names_the_stage_words_and_the_fold_and_does_not_echo_the_value():
    """Kills T9 (the refusal echoes the value), T18 (the common-word refusal echoes it)."""
    for secretish, words in (
        ("PILOT" + chr(0x200B), STAGE_WORDS),
        ("DEFAULT" + chr(0x200B), ()),
    ):
        with pytest.raises(ValueError) as caught:
            check_tenant_id(secretish)
        message = str(caught.value)
        for stage in words:
            assert stage in message, f"the refusal does not name {stage}"
        assert "NFKC" in message and "case folding" in message
        assert secretish[:-1] not in message and chr(0x200B) not in message, (
            "the refusal echoes the value"
        )


def test_the_fold_is_the_spelling_the_redactor_leaves_bare():
    """Against the redactor's real behaviour (not a copy of the fold's own formula): next to a label every spelling of
    a stage word is masked, and (for a word on the common-word list) the bare folded word elsewhere in the text stays
    readable, because the redactor does not sweep that word. So `fold_name` of a spelling is the word the redactor would leave in clear, which is why the check
    compares it. Kills T1-T4 and T11."""
    for value in [*REFUSED, *REFUSED_STAGE_WORDS]:
        folded = fold_name(value)
        assert folded in REFUSED_ID_WORDS, f"{value!a}: the fold {folded!a} is not a refused word"
        out = redact_text(f"tenant_id={value} then {folded} later", {})
        assert "<TENANT_" in out, f"{value!a}: the labelled copy was not masked: {out!a}"
        if folded in commonwords.COMMON_WORDS:  # the words the redactor does not sweep
            assert f" then {folded} later" in out, (
                f"{value!a}: the redactor masked the bare folded word {folded!a}: {out!a}"
            )
    for value in ACCEPTED:
        assert fold_name(value) not in REFUSED_ID_WORDS or _refusal(check_id, value) is not None


# --- the shared list ------------------------------------------------------------------------------------------


def test_the_redactor_and_the_id_check_use_one_word_list():
    """Kills T16 (redact.py gets its own copy of the list)."""
    assert redact_mod._COMMON is commonwords.COMMON_WORDS, "the redactor has a list of its own"
    assert REFUSED_ID_WORDS == frozenset(STAGE_WORDS) | commonwords.COMMON_WORDS


def test_the_stage_words_are_the_stages_and_the_words_the_stage_scan_looks_for():
    """Kills T19 (a stage word dropped) and T20 (a word added that the scan does not know)."""
    assert STAGE_WORDS == (*STAGES, *NEW_WORDS), (
        "the stage words differ from the stage scan's words"
    )
    assert len(set(STAGE_WORDS)) == 6, "a stage word is listed twice or missing"


def test_every_word_the_redactor_does_not_sweep_is_refused_and_the_leak_is_real():
    """For every common word: the labelled copy is masked, the bare copy stays readable (that is the leak a tenant
    with this id would have), and the check refuses the word. Kills T17."""
    for word in sorted(commonwords.COMMON_WORDS):
        with pytest.raises(ValueError):
            check_id(word)
        if len(word) < 3:  # too short for the label rule and for the sweep: nothing to leak or mask
            continue
        text = f"tenant_id={word} then {word} later"
        masked = redact(text).text
        assert masked == f"tenant_id=<TENANT_1> then {word} later", f"{word}: {masked!a}"


def test_an_ordinary_id_is_masked_in_every_copy_so_it_needs_no_refusal():
    assert redact("tenant_id=acmeco then acmeco later").text == (
        "tenant_id=<TENANT_1> then <TENANT_1> later"
    )


def test_the_id_types_cover_the_labels_of_the_redactors_tenant_rule():
    """The redactor reads tenant, org, organisation, organization, customer, account and user before `_id`; each of
    them has a type in `config`. Fails when the redactor gains a label that has no type here."""
    rule = next(rx for name, rx in redact_mod.PATTERNS if name == "TENANT")
    group = re.search(r"\(\?:([a-z|]+)\)\[_\\-\]\?id", rule.pattern)
    assert group, "the TENANT pattern has another shape"
    labels = set(group.group(1).split("|"))
    assert labels == {
        "tenant",
        "org",
        "organisation",
        "organization",
        "customer",
        "account",
        "user",
    }


# --- through the config types ------------------------------------------------------------------------------------


class _Tenant(_Strict):
    tenant_id: TenantId


class _Plain(BaseModel):
    tenant_id: TenantId


def test_the_config_type_refuses_a_stage_word_with_a_validation_error():
    """Kills T10 (the config type does not call the check)."""
    for value in [*REFUSED, *REFUSED_STAGE_WORDS]:
        try:
            _Tenant(tenant_id=value)
        except ValidationError as exc:
            assert "stage word" in str(exc), (
                f"{value!a} was refused without the stage-word sentence"
            )
        else:
            raise AssertionError(f"the config type accepted {value!a}")


def test_the_config_type_accepts_an_ordinary_tenant_id():
    assert _Tenant(tenant_id="acmecorp").tenant_id == "acmecorp"


def test_each_other_id_type_refuses_a_common_word_and_a_stage_word():
    """Kills T10b (an other id type does not call the check) and T21 (an other id type carries the wrong label)."""
    for kind, label in (
        (OrgId, "an org id"),
        (CustomerId, "a customer id"),
        (AccountId, "an account id"),
        (UserId, "a user id"),
    ):
        model = type("Holder", (_Strict,), {"__annotations__": {"value": kind}})
        for value in ("default", "Prod", NEW_WORDS[2], NEW_WORDS[0].upper(), "admin"):
            with pytest.raises(ValidationError) as caught:
                model(value=value)
            assert label in str(caught.value), f"{value}: the error does not start with {label!r}"
        assert model(value="acmeco-7").value == "acmeco-7"


def test_a_refused_value_is_absent_from_the_error_text_of_a_strict_model():
    """The no-echo promise holds inside a `_Strict` model (hide_input_in_errors), checked through the model and not
    only through the function. A message that echoes the value is killed here too (T9, T18)."""
    for value in ("PILOT" + chr(0x200B), "DEFAULT" + chr(0x200B), "Admin"):
        with pytest.raises(ValidationError) as caught:
            _Tenant(tenant_id=value)
        text = str(caught.value)
        assert value not in text and value.strip(chr(0x200B)) not in text, f"{value!a} is echoed"
        assert "input_value" not in text, "the error prints the input"


def test_a_plain_model_does_echo_the_value_so_the_type_belongs_in_a_strict_model():
    """The control for the test above: without `hide_input_in_errors` pydantic prints `input_value=`. This is why the
    walk requires a `_Strict` base for a class that holds an id (and why `check_id` documents it)."""
    with pytest.raises(ValidationError) as caught:
        _Plain(tenant_id="ADMIN")
    assert "ADMIN" in str(caught.value), "pydantic no longer prints the input: the control is void"


def test_a_non_string_through_the_config_type_is_a_validation_error():
    with pytest.raises(ValidationError):
        _Tenant(tenant_id=5)


# --- the walk: no model may hold an id outside the checked types -------------------------------------------------

# The labels the redactor's rule reads (pinned above). tenant is matched anywhere in a name; the others only as
# `<label>_id` or `<label>id` (plural allowed), so `customers_v` or `user_name` are not ids.
ID_NAME = re.compile(
    r"tenant|(?:org(?:ani[sz]ation)?|customer|account|user)[_\-]?ids?(?![a-z])", re.IGNORECASE
)
# Names that mean a switch or a count, not an id (`multi_tenant: bool`).
FLAG_NAME = re.compile(
    r"^(?:multi|single)_tenant$|^(?:is|has|n|num)_.*tenant|tenants?_(?:count|enabled|mode)$|^n_tenants$",
    re.IGNORECASE,
)
ID_TYPES = frozenset({"TenantId", "OrgId", "CustomerId", "AccountId", "UserId"})
CHECKS = frozenset({"check_tenant_id", "check_id"})
CONTAINERS = frozenset({"list", "set", "frozenset", "tuple", "Sequence", "Optional", "List", "Set"})


def _last_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def is_id_type(ann: ast.AST | None) -> bool:
    """True when the annotation is exactly one of the id types, alone, in `X | None`, `Optional[X]`, or as the element
    of a list, set, frozenset or tuple. Not a substring: `NotTenantId`, a string annotation, `dict[str, TenantId]`
    and `Annotated[...]` are not."""
    if ann is None:
        return False
    if isinstance(ann, (ast.Name, ast.Attribute)):
        return _last_name(ann) in ID_TYPES
    if isinstance(ann, ast.BinOp) and isinstance(ann.op, ast.BitOr):
        sides = [ann.left, ann.right]
        none = [s for s in sides if isinstance(s, ast.Constant) and s.value is None]
        rest = [s for s in sides if s not in none]
        return len(none) <= 1 and all(is_id_type(s) for s in rest) and bool(rest)
    if isinstance(ann, ast.Subscript) and _last_name(ann.value) in CONTAINERS:
        inner = ann.slice
        items = inner.elts if isinstance(inner, ast.Tuple) else [inner]
        items = [i for i in items if not (isinstance(i, ast.Constant) and i.value is Ellipsis)]
        return bool(items) and all(is_id_type(i) for i in items)
    return False


def _is_check_call(node: ast.AST | None) -> bool:
    return isinstance(node, ast.Call) and _last_name(node.func) in CHECKS


def calls_check_on(scope: ast.AST, param: str) -> bool:
    """True when `scope` contains a call to a check whose argument is THAT parameter (positional or keyword)."""
    for node in ast.walk(scope):
        if _is_check_call(node):
            args = [*node.args, *(k.value for k in node.keywords)]
            if any(isinstance(a, ast.Name) and a.id == param for a in args):
                return True
    return False


def _is_id_name(name: str) -> bool:
    return bool(ID_NAME.search(name)) and not FLAG_NAME.search(name)


def _plain_type(ann: ast.AST | None) -> bool:
    return isinstance(ann, ast.Name) and ann.id in {"bool", "int"}


def _targets(node: ast.AST) -> list[ast.AST]:
    out = []
    for t in node.targets if isinstance(node, ast.Assign) else [node.target]:
        out += t.elts if isinstance(t, ast.Tuple) else [t]
    return out


def unchecked_id_fields(source: str, name: str, defines_types: bool = False) -> list[str]:
    """Every id-named field, attribute or parameter in `source` that does not go through the check:
    - an annotated name (class field or module name) must carry exactly an id type;
    - a class-level or module-level assignment of such a name needs the check call as its value (an unannotated
      `tenant_id = Field(...)` is a field with no type);
    - an attribute (`self.tenant_id = ...`) needs the check call as its value;
    - a function or lambda parameter needs a call to a check on THAT parameter in the function;
    - the id types themselves may only be defined in config.py (`defines_types`) and only imported from
      hadavin_sdk.config.
    Limits: a local variable assigned inside a function is not checked (it comes from a parameter or field that is);
    a dict key or setattr is not seen; only pydantic models validate, so a dataclass or TypedDict field with an id
    type is accepted by the walk and not validated at run time."""
    problems = []
    tree = ast.parse(source)

    def flag(node: ast.AST, what: str) -> None:
        problems.append(f"{name}:{node.lineno} {what}")

    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign):
            target = node.target
            ident = _last_name(target)
            if ident and _is_id_name(ident) and not _plain_type(node.annotation):
                if isinstance(target, ast.Attribute):
                    if not _is_check_call(node.value):
                        flag(node, f"attribute {ident} is not set through a check")
                elif not is_id_type(node.annotation):
                    flag(node, f"field {ident} is not an id type")
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            args = node.args
            for arg in [*args.posonlyargs, *args.args, *args.kwonlyargs, args.vararg, args.kwarg]:
                if (
                    arg
                    and _is_id_name(arg.arg)
                    and not _plain_type(arg.annotation)
                    and not calls_check_on(node, arg.arg)
                ):
                    flag(node, f"parameter {arg.arg} is not checked")
        if isinstance(node, ast.Assign):
            for target in _targets(node):
                ident = _last_name(target)
                if ident in ID_TYPES and not defines_types:
                    flag(node, f"{ident} is defined outside config.py")
                if (
                    ident
                    and _is_id_name(ident)
                    and isinstance(target, ast.Attribute)
                    and not _is_check_call(node.value)
                ):
                    flag(node, f"attribute {ident} is not set through a check")
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name in ID_TYPES and (node.module or "") not in {
                    "hadavin_sdk.config",
                    "config",
                }:
                    flag(
                        node, f"{alias.name} is imported from {node.module}, not hadavin_sdk.config"
                    )
        if isinstance(node, ast.ClassDef) and node.name in ID_TYPES:
            flag(node, f"{node.name} is defined as a class")
    # class-level and module-level assignments (not inside a function)
    containers = [tree] + [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    for container in containers:
        for stmt in container.body:
            if isinstance(stmt, ast.Assign):
                for target in _targets(stmt):
                    if (
                        isinstance(target, ast.Name)
                        and _is_id_name(target.id)
                        and target.id not in ID_TYPES
                        and not _is_check_call(stmt.value)
                    ):
                        flag(stmt, f"field {target.id} has no id type")
    # a class that holds an id field must hide the input in errors: it derives from _Strict
    for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
        holds = any(
            isinstance(s, ast.AnnAssign)
            and isinstance(s.target, ast.Name)
            and is_id_type(s.annotation)
            and _is_id_name(s.target.id)
            for s in cls.body
        )
        if holds and "_Strict" not in {_last_name(b) for b in cls.bases}:
            flag(cls, f"class {cls.name} holds an id but does not derive from _Strict")
    return problems


def test_the_walk_sees_each_kind_of_unchecked_id():
    """Sensitivity controls: each rule of the walk is shown on a planted source. Kills T12 (any type accepted), T13
    (parameters ignored), T15b (the annotation is matched as a substring), T23 (any parameter counts as checked), T24
    (attribute targets ignored), T25 (plain assignments ignored), T26 (the _Strict base is not required)."""
    wrong_type = "class M(_Strict):\n    tenant_id: str\n    other: TenantId\n"
    assert len(unchecked_id_fields(wrong_type, "x.py")) == 1, (
        "the walk missed a field of the wrong type"
    )
    for ann in ("NotTenantId", "dict[str, TenantId]", "'TenantId'", "Annotated[str, TenantId]"):
        src = f"class M(_Strict):\n    tenant_id: {ann}\n"
        assert len(unchecked_id_fields(src, "x.py")) == 1, f"the walk accepted the annotation {ann}"
    for ann in (
        "TenantId",
        "config.TenantId",
        "TenantId | None",
        "Optional[TenantId]",
        "list[TenantId]",
    ):
        src = f"class M(_Strict):\n    tenant_id: {ann}\n"
        assert unchecked_id_fields(src, "x.py") == [], f"the walk flagged the annotation {ann}"
    other_label = "class M(_Strict):\n    customer_id: str\n"
    assert len(unchecked_id_fields(other_label, "x.py")) == 1, "the walk missed a customer id"
    unchecked_param = "def make(tenant_id):\n    return tenant_id\n"
    assert len(unchecked_id_fields(unchecked_param, "x.py")) == 1, (
        "the walk missed an unchecked parameter"
    )
    wrong_param = "def make(tenant_id, other):\n    return check_tenant_id(other)\n"
    assert len(unchecked_id_fields(wrong_param, "x.py")) == 1, (
        "the walk accepted a check on another parameter"
    )
    mention = "def make(tenant_id):\n    return 'check_tenant_id'\n"
    assert len(unchecked_id_fields(mention, "x.py")) == 1, "the walk accepted the text of a check"
    lam = "f = lambda tenant_id: tenant_id\n"
    assert len(unchecked_id_fields(lam, "x.py")) == 1, "the walk missed a lambda parameter"
    assign = "class M(_Strict):\n    tenant_id = Field(...)\n"
    assert len(unchecked_id_fields(assign, "x.py")) == 1, "the walk missed an assigned field"
    attr = "class M:\n    def __init__(self, v):\n        self.tenant_id: str = v\n"
    assert len(unchecked_id_fields(attr, "x.py")) == 1, "the walk missed an annotated attribute"
    attr2 = "class M:\n    def __init__(self, v):\n        self.org_id = v\n"
    assert len(unchecked_id_fields(attr2, "x.py")) == 1, "the walk missed an attribute assignment"
    plain = "class M(BaseModel):\n    tenant_id: TenantId\n"
    assert len(unchecked_id_fields(plain, "x.py")) == 1, (
        "the walk accepted a model that echoes input"
    )
    shadow = "TenantId = str\nclass M(_Strict):\n    tenant_id: TenantId\n"
    assert len(unchecked_id_fields(shadow, "x.py")) == 1, "the walk accepted a shadowed TenantId"
    foreign = "from elsewhere import TenantId\n"
    assert len(unchecked_id_fields(foreign, "x.py")) == 1, (
        "the walk accepted a TenantId from elsewhere"
    )


def test_the_walk_accepts_checked_ids_and_leaves_flags_and_other_names_alone():
    good = (
        "class M(_Strict):\n    tenant_id: TenantId\n    tenant_ids: list[TenantId]\n"
        "    multi_tenant: bool\n    customer_id: CustomerId\n    customers_v: str\n    user_name: str\n"
    )
    assert unchecked_id_fields(good, "x.py") == [], "the walk flagged a checked or unrelated field"
    for src in (
        "def make(tenant_id):\n    return check_tenant_id(tenant_id)\n",
        "def make(*, org_id):\n    return check_id(value=org_id, label='x')\n",
        "f = lambda tenant_id: check_tenant_id(tenant_id)\n",
        "def f(is_multi_tenant: bool):\n    return is_multi_tenant\n",
    ):
        assert unchecked_id_fields(src, "x.py") == [], f"the walk flagged: {src!r}"
    config_src = "TenantId = Annotated[str, AfterValidator(check_tenant_id)]\n"
    assert unchecked_id_fields(config_src, "config.py", defines_types=True) == []


WALKED = ("src", "demos", "tools")


def walk_tree(root: Path) -> list[str]:
    """Every unchecked id field, attribute or parameter in the Python files below `root`/src, demos and tools.
    What the walk skips, stated: a local variable assigned inside a function (it comes from a parameter or field that
    is checked); a parameter or field annotated plain `bool` or `int` (a switch or a count); a dict key or `setattr`;
    a dataclass or TypedDict field (only pydantic models validate at run time)."""
    problems = []
    files = sorted(
        p
        for folder in WALKED
        for p in (root / folder).rglob("*.py")
        if "__pycache__" not in p.parts
    )
    for path in files:
        problems += unchecked_id_fields(
            path.read_text(encoding="utf-8"),
            str(path.relative_to(root)),
            defines_types=path == root / "src" / "hadavin_sdk" / "config.py",
        )
    return problems


def test_every_id_field_in_the_package_goes_through_the_check():
    """Walks src, demos and tools of this repository. No field uses the id types yet (the trigger is named in the
    docstring of config.py), so the walk also fails any id-named field typed as a plain str."""
    assert any((ROOT / "src" / "hadavin_sdk").rglob("*.py")), "no source files found"
    problems = walk_tree(ROOT)
    assert not problems, "\n".join(problems)


def test_a_tenant_field_planted_in_a_fixture_tree_is_found_in_each_walked_folder(tmp_path):
    """Kills T14 (a walked folder is dropped, or the walk of a tree finds nothing). The planted source is a string
    written here, so the test depends on no file of the package."""
    planted = "class Holder(_Strict):\n    tenant_id: str = ''\n"
    for folder in WALKED:
        tree = tmp_path / folder
        tree.mkdir()
        (tree / "plant.py").write_text(planted, encoding="utf-8")
    found = walk_tree(tmp_path)
    assert len(found) == len(WALKED), f"the walk found {found}"
    for folder in WALKED:
        assert any(f.startswith(f"{folder}/plant.py") for f in found), f"{folder} was not walked"


def test_the_refused_words_are_exactly_these_twenty_nine():
    """A literal list, written out here and not read from the code: a word dropped from or added to commonwords.py or
    STAGE_WORDS is seen (the other tests walk the code's own lists, so they cannot see it). Kills T28, T28b, T28c.
    Words the stage scan looks for are built from parts."""
    expected = {
        "admin", "api", "app", "db", "debug", "default", "error", "false", "info", "local", "main",
        "master", "none", "null", "public", "root", "sta" + "ge", "sta" + "ging", "true", "user", "users", "web",
        "d" + "ev", "de" + "mo", "pi" + "lot", "pr" + "od", *NEW_WORDS,
    }  # fmt: skip
    assert len(expected) == 29
    assert set(REFUSED_ID_WORDS) == expected, (
        f"the refused words differ from the expected list: {sorted(set(REFUSED_ID_WORDS) ^ expected)}"
    )


# --- G1: an id the redactor cannot sweep is refused where it enters ------------------------------------------------
# The redactor's label rule reads `[a-z0-9_-]{3,}` after tenant_id, org_id, ... and its sweep copies only values of 3 or
# more characters, and all-digit values of 6 or more (guard/redact.py, `_sweep`). An id outside that is masked in part
# or not at all, and its other copies stay in clear. These tests run the candidates through the redactor itself.


TOO_SHORT = ["", "a", "xy", "p", "7", "42", " ab ", "a" + chr(0x200B) + "b", fullwidth("ab")]
ODD_IDS = [
    "ac\x00me",  # NUL
    "ac\x07me",  # bell
    "ac\tme",  # tab
    "ac me",  # a space inside
    "ac" + chr(0xA0) + "me",  # no-break space
    "ac.me",  # a dot
    "acme" + chr(0x2028) + "x",  # line separator
    "\u0430cme",  # Cyrillic a that looks Latin
    "acm" + chr(0x0435),  # Cyrillic ie that looks Latin
    "Ünïcode-Tenant",  # accented letters: the label rule reads only ASCII letters
    chr(0x131) + "d123",  # dotless i
    # Review A19 round 2, B1: the case fold turns these into ASCII, the redactor does not fold, so only the part before
    # them is masked.
    "acme" + chr(0xDF) + "corp7",  # sharp s (folds to ss)
    chr(0xDF) + "corp-tenant9",  # sharp s first
    "acme" + chr(0x1E9E) + "corp7",  # capital sharp s (folds to ss)
    "acme" + chr(0x17F) + "corp7",  # long s (Unicode ignore-case would match s)
    "acme" + chr(0x212A) + "corp7",  # Kelvin sign (folds to k)
    # An invisible format character (Cf) inside a long id: the id is not what the redactor reads.
    "tenant-abcdefgh" + chr(0x200B) + "ijklmnop99",
    "tenant-abcd" + chr(0xAD) + "efgh99",
    "tenant-abcd" + chr(0x2060) + "efgh99",
    "tenant-abcd" + chr(0xFEFF) + "efgh99",
    fullwidth("acmecorp"),  # NFKC turns it into ASCII; the id as written is not
    "acme" + chr(0xFF10) + "corp",  # full-width digit zero
    "acme\n",  # trailing newline
]


def _masked_shape(out: str, template: str) -> bool:
    """True when `out` is `template` with every {} replaced by one placeholder of any kind and nothing else changed:
    no part of the id is left in clear."""
    pattern = re.escape(template).replace(re.escape("{}"), r"<[A-Z0-9_]+>")
    return re.fullmatch(pattern, out) is not None


# Positions: the id beside its label, a bare copy after it, a bare copy before it, a copy in quotes, a copy after
# punctuation.
LEAK_TEMPLATES = [
    "customer_id={} then {} later",
    "{} first, then customer_id={}",
    "customer_id={}\n{}",
    '{"user_id": "{}", "note": "{}"}',
    "customer_id={} ({}) and [{}]",
]


def _fill(template: str, value: str) -> str:
    return template.replace("{}", value)


def _leaks(value: str) -> bool:
    """True when any part of `value` survives redact_text in any of the positions above. The test is the shape of the
    output: only placeholders may stand where the id stood (a partial mask, `<TENANT_1>` followed by the tail of the id,
    fails it too)."""
    return any(
        not _masked_shape(redact_text(_fill(template, value), {}), template)
        for template in LEAK_TEMPLATES
    )


def test_an_id_shorter_than_the_redactors_minimum_is_refused():
    """Kills T30 (the length refusal is off)."""
    for value in TOO_SHORT:
        message = _refusal(check_id, value)
        assert message is not None, f"{value!a} was accepted as an id"
        assert "too short" in message, f"{value!a}: another sentence: {message}"
        assert _refusal(check_tenant_id, value) is not None


@pytest.mark.parametrize("n", [SWEEP_MIN_LENGTH - 1, SWEEP_MIN_LENGTH, SWEEP_MIN_LENGTH + 1])
def test_the_length_limit_is_the_redactors_own_number(n):
    value = "q" * n
    refused = _refusal(check_id, value) is not None
    assert refused == (n < SWEEP_MIN_LENGTH), f"length {n}: refused={refused}"
    if not refused:
        assert not _leaks(value), f"{value!a} is accepted and leaks"


def test_all_digit_ids_are_refused_below_the_redactors_digit_minimum():
    """Kills T31 (the digit refusal is off)."""
    for n in (SWEEP_MIN_DIGITS - 1, SWEEP_MIN_DIGITS, SWEEP_MIN_DIGITS + 1):
        value = "7" * n
        refused = _refusal(check_id, value) is not None
        assert refused == (n < SWEEP_MIN_DIGITS), f"{n} digits: refused={refused}"
        if not refused:
            assert not _leaks(value), f"{value!a} is accepted and leaks"
        # Full-width digits are refused at every length: the id is read as written, and the redactor reads ASCII digits.
        assert _refusal(check_id, fullwidth(value)) is not None, f"{n} full-width digits accepted"


def test_the_redactor_really_leaks_a_short_digit_id_the_control():
    """The reason for the limit: a bare 5-digit id next to its label stays readable elsewhere."""
    assert _leaks("1" * (SWEEP_MIN_DIGITS - 1)), (
        "the redactor no longer leaks it: the limit is void"
    )


@pytest.mark.parametrize("value", ODD_IDS)
def test_a_control_character_or_look_alike_id_is_refused_or_swept(value):
    """Either check_id refuses the id, or the redactor masks every copy of it. Never accepted and leaking."""
    refused = _refusal(check_id, value) is not None
    assert refused or not _leaks(value), f"{value!a} is accepted and a copy stays in clear"


def test_the_odd_ids_are_in_fact_refused():
    """Kills T32 (the character refusal is off), T32b (the check reads the fold) and T34 (the ASCII-only flag is lost)."""
    for value in ODD_IDS:
        message = _refusal(check_id, value)
        assert message is not None, f"{value!a} was accepted"
        assert value not in message, "the refusal echoes the value"


@pytest.mark.parametrize("value", ACCEPTED)
def test_every_accepted_id_is_swept_in_every_copy(value):
    assert not _leaks(value), f"{value!a} is accepted by check_id and still leaks"


def test_the_label_rule_class_is_the_one_the_check_allows():
    """The class body of the redactor's TENANT rule and the one in `stages._READABLE_ID` are equal (not a substring
    check), and the check reads it as ASCII with the case ignored, like the rule's `(?i)`. Kills T34."""
    rule = next(rx for name, rx in redact_mod.PATTERNS if name == "TENANT")
    found = re.findall(r"\[a-z0-9_\\-\]\{" + str(SWEEP_MIN_LENGTH) + r",\}", rule.pattern)
    assert len(found) == 1, f"the TENANT rule holds {len(found)} value classes"
    rule_class = found[0].split("{")[0]
    assert _READABLE_ID.pattern == rule_class + "+", (
        f"the id class {_READABLE_ID.pattern!r} differs from the rule's {rule_class!r}"
    )
    assert _READABLE_ID.flags & re.ASCII and _READABLE_ID.flags & re.IGNORECASE
    assert rule.flags & re.IGNORECASE


def _wide_candidates():
    """Every code point whose NFKC form, case fold or Cf-stripped form is plain ASCII letters, digits, hyphen or
    underscore, or empty (a Cf character): the characters a fold-based check could let in. The ASCII class itself is
    included."""
    ok = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
    out = []
    for cp in range(0x110000):
        if 0xD800 <= cp <= 0xDFFF:
            continue
        c = chr(cp)
        forms = {
            c.casefold(),
            canonical(c),
            canonical(c).casefold(),
            unicodedata.normalize("NFKC", c),
        }
        if any(f == "" or set(f) <= ok for f in forms):
            out.append(c)
    return out


def test_no_accepted_id_leaks_over_a_sweep_of_every_code_point_the_fold_could_read_as_ascii():
    """Class: the check validated a form (the fold) other than the one it returns and the redactor reads. For every
    code point whose casefold, NFKC form or Cf-stripped form is ASCII (or empty), in the middle, at the start and at
    the end of an id and inside a long id: if check_id accepts the id, it is ASCII and every copy of it is masked in
    every position (`_leaks`). Kills T32b (the check reads the fold)."""
    candidates = _wide_candidates()
    non_ascii = [c for c in candidates if not c.isascii()]
    assert len(non_ascii) > 1000, f"the sweep is too small: {len(non_ascii)} non-ASCII code points"
    for needed in (0xDF, 0x1E9E, 0x17F, 0x212A, 0x200B, 0xAD, 0xFF41):
        assert chr(needed) in non_ascii, f"U+{needed:04X} is missing from the sweep"
    accepted_non_ascii = []
    accepted = []
    for c in candidates:
        for value in (
            "acme" + c + "corp7",
            c + "corp-tenant9",
            "tenant-corp9" + c,
            "tenant-abcdefgh" + c + "ijklmnop99",
        ):
            if _refusal(check_id, value) is None:
                accepted.append(value)
                if not value.isascii():
                    accepted_non_ascii.append(value)
    assert not accepted_non_ascii, (
        f"{len(accepted_non_ascii)} non-ASCII ids accepted, first {accepted_non_ascii[0]!a}"
    )
    leaking = [v for v in accepted if _leaks(v)]
    assert not leaking, f"{len(leaking)} accepted ids leak, first {leaking[0]!a}"


@pytest.mark.parametrize("value", ["---", "___", "-_-", "----", "______", "_-_-_-"])
def test_an_id_of_punctuation_only_is_masked_in_every_position(value):
    """Review A19 round 2, M2: the redactor's class holds hyphen and underscore, so such an id is accepted. Run through
    the same helper as every other id: every copy beside a label is masked and no part stays in clear. (Over-masking a
    separator such as `-----` in other text is the redactor's standing behaviour for every id; a tenant that picks such
    an id accepts it.)"""
    assert _refusal(check_id, value) is None
    assert not _leaks(value), f"{value!a} is accepted and a copy stays in clear"


def test_stages_py_imports_only_the_leaf_modules():
    """Class: a module every guard imports at the top of its file must stay a leaf. An AST walk of src/hadavin_sdk/
    stages.py: the only imports are `re` and `__future__` from the standard library and the two leaf modules
    `hadavin_sdk.commonwords` and `hadavin_sdk.textfold`, and those two import nothing of the package. Kills T35."""
    leaf_modules = {"hadavin_sdk.commonwords", "hadavin_sdk.textfold"}

    def imports(path: Path) -> set[str]:
        found: set[str] = set()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                found.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert node.level == 0, f"{path.name}: a relative import"
                found.add(node.module or "")
        return found

    assert imports(SRC / "stages.py") == {"__future__", "re", *leaf_modules}, (
        "stages.py imports something besides the leaf modules"
    )
    for leaf in ("commonwords.py", "textfold.py"):
        package = {m for m in imports(SRC / leaf) if m.split(".")[0] == "hadavin_sdk"}
        assert not package, f"{leaf} is not a leaf: it imports {sorted(package)}"


def test_the_redactor_sweep_uses_the_shared_limits():
    import inspect

    source = inspect.getsource(redact_mod._sweep)
    for name in ("SWEEP_MIN_LENGTH", "SWEEP_MIN_DIGITS"):
        assert name in source, f"_sweep does not read {name}: a second copy of the limit"
    assert redact_mod._sweep("<TENANT_1>", "q" * (SWEEP_MIN_LENGTH - 1)) is None
    assert redact_mod._sweep("<TENANT_1>", "q" * SWEEP_MIN_LENGTH) is not None
    assert redact_mod._sweep("<TENANT_1>", "7" * (SWEEP_MIN_DIGITS - 1)) is None
    assert redact_mod._sweep("<TENANT_1>", "7" * SWEEP_MIN_DIGITS) is not None
