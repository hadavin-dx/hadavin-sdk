"""An id may not be spelled like a stage word or be a common word the redactor does not sweep (order 126 and order 132,
q269 item b and F4). Refused where ids are validated: `stages.check_id`, and the `config` types `TenantId`, `OrgId`,
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
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from hadavin_sdk import commonwords
from hadavin_sdk.config import AccountId, CustomerId, OrgId, TenantId, UserId, _Strict
from hadavin_sdk.guard.redact import redact
from hadavin_sdk.guard.runmap import canonical
from hadavin_sdk.stages import (
    REFUSED_ID_WORDS,
    STAGE_WORDS,
    STAGES,
    check_id,
    check_tenant_id,
    fold_name,
    is_stage_name,
)
from tests.test_stage_names import NEW_WORDS

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
    "p",
    "Ünïcode-Tenant",
    fullwidth("acme"),
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


def test_the_fold_is_the_redactors_canonical_form_then_casefolded_then_cut():
    """The redactor's `runmap.canonical` (NFKC, then Cf characters removed) is the first half of the fold; the case
    fold and the cut of white space are added by `stages.fold_name`. Kills T11 (the Cf step differs from the
    redactor's)."""
    for value in [*REFUSED, *REFUSED_STAGE_WORDS, *ACCEPTED]:
        want = canonical(value).casefold().strip()
        assert fold_name(value) == want, (
            f"{value!a}: the fold differs from the redactor's canonical form"
        )


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


def test_every_id_field_in_the_package_goes_through_the_check():
    """Kills T14 (a tenant field planted in src escapes the walk). Walks src, demos and tools."""
    problems = []
    files = sorted(
        p
        for folder in ("src", "demos", "tools")
        for p in (ROOT / folder).rglob("*.py")
        if "__pycache__" not in p.parts
    )
    assert any(f.is_relative_to(SRC) for f in files), "no source files found"
    for path in files:
        problems += unchecked_id_fields(
            path.read_text(encoding="utf-8"),
            str(path.relative_to(ROOT)),
            defines_types=path == SRC / "config.py",
        )
    assert not problems, "\n".join(problems)


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
