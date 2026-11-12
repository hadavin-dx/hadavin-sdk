"""Guard "code equals declaration" for the declared permission sets (ticket Q8c, PR 1; owner rule least privilege).

Three backend kinds carry a `POLICY` literal: `vault` (secrets), `vault_transit` (signer), `kubernetes` (source).
These tests compare OUR code with OUR list. They do not show that a permission name is right, and no server
reads anything here (the Vault server tests are in tests/test_policy_engine.py).

  A1 calls: the requests written in a kind module, by the call shapes listed in `SHAPES`, EQUAL the requests its
     POLICY declares. A request with no grant fails; a grant whose request is gone fails.
  A2 data rules: checked by `tools.policy_page.problems` (wildcards, reasons, long-lived credentials, pure literal).
  A3 the committed page equals what the data gives.
  A4 a grant whose name was not found in a vendor source needs a dated `PENDING_NAMES` entry; every source id
     resolves in tests/fixtures/policy_sources_2026-11-11.txt.
  A5 Kubernetes: the generated Role passes the kind's own read-only rule, and a planted write does not.
  Kinds: every kind is declared, on the dated pending list, or listed as holding no identity of its own.
Each rule has a plant test: a violation planted in a copy must be reported.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import os
import re
import runpy
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
import yaml
from tools import policy_page as pp

from hadavin_sdk.backends import table
from hadavin_sdk.sources import kinds as source_kinds
from hadavin_sdk.sources import kubernetes as k8s
from tests.test_lockin_guard import Pending

ROOT = Path(__file__).resolve().parents[1]
DECIDED = pp.DECIDED
# The longest time a dated entry may stand before it is looked at again. An entry can only be kept alive
# by a new decision (a new `decided` day) with a new `review_by` at most this many days after it. The number
# lives in the tool (one place); a test below checks this file does not hold a second one.
MAX_PENDING_DAYS = pp.MAX_PENDING_DAYS

# ------------------------------------------------------------------------------------- kinds: who is covered

# The day the 16 kinds below were put on the pending list. A literal of its own, NOT `pp.DECIDED`: the tool's
# date is the day of the last decision about the names and claims, and renewing that must not silently renew
# these kinds as well (the 92-day cap compares `review_by` with `decided`, so a shared date could dodge it).
KINDS_DECIDED = date(2026, 11, 11)
# The latest decision day of the dated lists: the day a clock must show for every list to exist (a renewal of the
# kinds alone moves the kinds past the names and claims, and the other way round).
LATEST_DAY = max(DECIDED, KINDS_DECIDED)
_PR2 = ("the permission names of this kind are not all checked yet", "Q8c PR 2", date(2026, 12, 11))
_SLICE2 = ("slice 2 of Q8c: names not checked, owner questions O2 and O3 open", "Q8c slice 2")
# A kind that signs in to an outside system and has no POLICY yet. Overdue and stale entries fail.
PENDING_KINDS: dict[str, Pending] = {
    "secrets/aws_secrets_manager": Pending(_PR2[0], _PR2[1], KINDS_DECIDED, _PR2[2]),
    "signer/aws_kms": Pending(_PR2[0], _PR2[1], KINDS_DECIDED, _PR2[2]),
    "anchor/s3_object_lock": Pending(_PR2[0], _PR2[1], KINDS_DECIDED, _PR2[2]),
    "store/postgres": Pending(_PR2[0], _PR2[1], KINDS_DECIDED, _PR2[2]),
    "llm/bedrock": Pending(_PR2[0], _PR2[1], KINDS_DECIDED, _PR2[2]),
    "detector/bedrock_guardrail": Pending(_PR2[0], _PR2[1], KINDS_DECIDED, _PR2[2]),
    "channel/slack": Pending(
        "no Slack page could be read, so no scope name is checked", _PR2[1], KINDS_DECIDED, _PR2[2]
    ),
    "secrets/azure_key_vault": Pending(*_SLICE2, KINDS_DECIDED, date(2027, 1, 31)),
    "secrets/gcp_secret_manager": Pending(*_SLICE2, KINDS_DECIDED, date(2027, 1, 31)),
    "signer/azure_key_vault_key": Pending(*_SLICE2, KINDS_DECIDED, date(2027, 1, 31)),
    "signer/gcp_kms": Pending(*_SLICE2, KINDS_DECIDED, date(2027, 1, 31)),
    "anchor/azure_immutable_blob": Pending(*_SLICE2, KINDS_DECIDED, date(2027, 1, 31)),
    "anchor/gcs_retention_lock": Pending(*_SLICE2, KINDS_DECIDED, date(2027, 1, 31)),
    "llm/anthropic": Pending(*_SLICE2, KINDS_DECIDED, date(2027, 1, 31)),
    "llm/openai_compat": Pending(*_SLICE2, KINDS_DECIDED, date(2027, 1, 31)),
    "llm/gemini": Pending(*_SLICE2, KINDS_DECIDED, date(2027, 1, 31)),
}
# A kind that holds no identity at an outside system, and why. A new kind must be put in one of the three lists.
NO_IDENTITY: dict[str, str] = {
    "secrets/fake": "in-memory test kind",
    "secrets/env": "reads this process's own environment",
    "secrets/mounted_file": "reads files the platform mounted; the file rights are the platform's",
    "signer/none": "signs nothing",
    "signer/ed25519_local": "a key file on this machine",
    "anchor/none": "anchors nothing",
    "store/memory": "in-memory",
    "audit/local_dir": "a folder on this machine",
    "audit/chain": "uses the signer, anchor and store kinds; holds no credential of its own",
    "llm/fake": "in-memory test kind",
    "detector/regex": "runs in this process",
    "detector/llm_judge": "calls through the llm kind; holds no credential of its own",
    "channel/fake": "in-memory test kind",
}
# The dated lists of names and claims live in the tool (`pp.PENDING_NAMES`, `pp.PENDING_CLAIMS`), so that
# `python tools/policy_page.py --check` runs their rules too; the tests below read the same objects.
PENDING_NAMES = pp.PENDING_NAMES
PENDING_CLAIMS = pp.PENDING_CLAIMS


def all_kinds() -> set[str]:
    out = {f"{family}/{name}" for family, entries in table.TABLE.items() for name in entries}
    return out | {f"source/{name}" for name in source_kinds.KINDS}


_pending_problems = pp.pending_problems  # one rule for every dated list, in the tool


def kind_problems(
    kinds: set[str],
    declared: set[str],
    pending: dict[str, Pending],
    no_identity: dict[str, str],
    today: date,
) -> list[str]:
    out = []
    for kind in sorted(kinds):
        homes = [kind in declared, kind in pending, kind in no_identity]
        if sum(homes) == 0:
            out.append(
                f"kind {kind} has no POLICY and is on no list: declare it or add a dated entry"
            )
        if sum(homes) > 1:
            out.append(f"kind {kind} is on more than one list")
    out += [f"declared kind {k} is not a kind of the tables" for k in sorted(declared - kinds)]
    out += [
        f"NO_IDENTITY {k} is not a kind of the tables" for k in sorted(set(no_identity) - kinds)
    ]
    return out + _pending_problems(
        "PENDING_KINDS",
        pending,
        kinds - declared,
        today,
        rule=pp.KINDS_RENEWAL_RULE,
        steps=pp.KINDS_RENEWAL_STEPS,
    )


def same(found: object, expected: object, what: str = "") -> None:
    """`found == expected`, with both written out in full in the failure message (pytest shortens a long
    list in the first line, and the mutant runner reads that line). `what` names the check in words and
    starts the message: a test with several `same()` calls gives each its own, so that the line the mutant
    runner reads says WHICH call failed (the expected text alone is the same in two calls that look alike)."""
    assert found == expected, (
        f"{what + ': ' if what else ''}reported {found!r}, expected {expected!r}"
    )


def _refused_with(call, exc: type[BaseException], text: str) -> bool:
    """True when `call()` raises `exc` and the message holds `text`. The caller's `assert` then carries its own words
    (pytest's "DID NOT RAISE" names no call, so the mutant runner could not tell which refusal was lost)."""
    try:
        call()
    except exc as found:
        return text in str(found)
    return False


def _marks_for(policy: pp.Policy) -> pp.Marks:
    """The real marks, plus the nobody-read mark for every claim of `policy` that the sources file does not list
    (a planted claim), so that a planted policy can be rendered."""
    marks = pp.read_marks(ROOT)
    extra = tuple(
        c
        for e in (*policy.grants, *policy.free, *policy.never)
        for c in e.claims_unverified
        if c not in (*marks.builder_read, *marks.nobody_read)
    )
    return dataclasses.replace(marks, nobody_read=(*marks.nobody_read, *extra))


def _policies() -> dict[str, pp.Policy]:
    loaded = pp.load_all(ROOT)
    missing = [pp.KIND_MODULES[k] for k, p in loaded.items() if p is None]
    assert not missing, "no POLICY in " + ", ".join(missing)
    return {k: p for k, p in loaded.items() if p is not None}


def _today() -> date:
    """The ONE source of "today" for every date guard of this file: the tool's own clock (`pp.datetime`), which the
    fixture `_fixed_day_of_the_run` fixes when a mutant run was given a day. A guard test never reads the real clock
    by another way (a module-level day taken at import was the slip of batch 9: a fixed day then reached the tool
    but not these tests)."""
    return pp.datetime.now(pp.UTC).date()


def _names_claims_day() -> date | None:
    """The review day of the names and claims lists together (each from its own entries), None when both are empty."""
    return pp.review_day(PENDING_NAMES, PENDING_CLAIMS)


def _overdue_pair() -> tuple[date, date] | None:
    """(the review day, the day after it): the last green day and the first overdue day of the names and claims
    lists; None when both are empty (nothing can be overdue: the end state, run by its own test)."""
    day = _names_claims_day()
    return None if day is None else (day, day + timedelta(days=1))


def _kinds_problems_today() -> list[str]:
    declared = {k for k, p in pp.load_all(ROOT).items() if p is not None}
    return kind_problems(all_kinds(), declared, PENDING_KINDS, NO_IDENTITY, _today())


def test_every_kind_is_declared_pending_or_holds_no_identity():
    declared = {k for k, p in pp.load_all(ROOT).items() if p is not None}
    problems = _kinds_problems_today()
    assert problems == []
    assert set(PENDING_KINDS) == set(pp.NOT_YET_DECLARED), (
        "the page's list differs from PENDING_KINDS"
    )
    assert len(PENDING_KINDS) == 16 and len(declared) == 3


def test_plant_a_new_kind_on_no_list_is_caught():
    problems = kind_problems(
        all_kinds() | {"secrets/new_cloud"},
        set(pp.KIND_MODULES),
        PENDING_KINDS,
        NO_IDENTITY,
        LATEST_DAY,
    )
    same(
        problems,
        ["kind secrets/new_cloud has no POLICY and is on no list: declare it or add a dated entry"],
        what="the check reports: is on no list",
    )


def test_plant_a_declared_kind_left_on_the_pending_list_is_caught():
    pending = {
        **PENDING_KINDS,
        "secrets/vault": Pending("r", "t", DECIDED, DECIDED + timedelta(days=30)),
    }
    problems = kind_problems(all_kinds(), set(pp.KIND_MODULES), pending, NO_IDENTITY, LATEST_DAY)
    same(
        problems,
        [
            "kind secrets/vault is on more than one list",
            "PENDING_KINDS secrets/vault is fixed or gone: delete the entry",
        ],
    )


def test_plant_an_overdue_pending_kind_is_caught():
    first = pp.review_day(PENDING_KINDS)
    if first is None:  # every kind is declared: an empty list reports nothing overdue, on any day
        late = DECIDED + timedelta(days=800)
        declared = all_kinds() - set(NO_IDENTITY)
        assert kind_problems(all_kinds(), declared, {}, NO_IDENTITY, late) == [], (
            "an empty pending-kinds list reports an overdue kind"
        )
        return
    problems = kind_problems(
        all_kinds(), set(pp.KIND_MODULES), PENDING_KINDS, NO_IDENTITY, first + timedelta(days=1)
    )
    due = sum(1 for p in PENDING_KINDS.values() if p.review_by == first)
    assert len(problems) == due and all(f"is overdue (review_by {first})" in p for p in problems), (
        f"the kinds that fall due the day after {first} are not reported as overdue, one line each: {problems}"
    )


# ----------------------------------------------------------------------------------------------- A1: calls


@dataclass(frozen=True)
class Shape:
    """How one kind module writes its requests.

    `sinks`: the method names whose call sends (or passes on) a request, each with the position of the
    operation argument (None: keyword only). For Vault the verb sits one position before the path.
    `wrappers`: (enclosing function, line, sink called there). Each asserts that at that line, inside that
    function, there is a call to that sink whose operation argument is a parameter of the enclosing function
    (the function passes on what it was given). An entry with no such call there is stale and fails.
    `raw_http`: the only functions that may build a raw HTTP request or touch the HTTP opener.
    `imports`: every import the module may hold (`module` or `module:name`). A new import (another HTTP
    library, `operator`, `functools`, `importlib`) fails until a person adds it here.
    `getattr_ok`: the only literal names that may be read with `getattr`.
    `settings`: Vault only. The object attribute a request path is built from -> the setting it holds. Written
    by hand from the kind's `build` function; no test follows the value from the setting to the attribute.
    """

    platform: str
    sinks: dict[str, int | None]
    wrappers: frozenset[tuple[str, int, str]]
    raw_http: frozenset[str] = frozenset()
    imports: frozenset[str] = frozenset()
    getattr_ok: frozenset[str] = frozenset()
    settings: tuple[tuple[str, str], ...] = ()


_SDK = "hadavin_sdk"
SHAPES: dict[str, Shape] = {
    "src/hadavin_sdk/actions/secrets_vault.py": Shape(
        "vault",
        {"call": 1, "authed": 1},
        frozenset({("authed", 102, "call"), ("authed", 105, "call")}),
        frozenset({"__init__", "call"}),
        frozenset(
            {
                "__future__:annotations",
                "json",
                "os",
                "re",
                "ssl",
                "time",
                "urllib.error",
                "urllib.parse",
                "urllib.request",
                "collections.abc:Callable",
                "pathlib:Path",
                "typing:Any",
                f"{_SDK}.actions.secrets_cache:CachedSecrets",
                f"{_SDK}.backends.table:VAULT_EMPTY_PREFIX",
                f"{_SDK}.errors:ConfigError",
                f"{_SDK}.guard.http:NoRedirect",
            }
        ),
        settings=(("self.mount", "mount"), ("self.path_prefix", "path_prefix")),
    ),
    # The sign-in call of this kind lives in the imported module actions/secrets_vault.py and is declared there.
    "src/hadavin_sdk/audit/signer_vault.py": Shape(
        "vault",
        {"call": 1, "authed": 1, "_call": 1},
        frozenset({("_call", 40, "authed")}),
        imports=frozenset(
            {
                "__future__:annotations",
                "base64",
                "threading",
                "typing:Any",
                "typing:Literal",
                f"{_SDK}.actions.secrets_vault:VaultError",
                f"{_SDK}.actions.secrets_vault:connect",
                f"{_SDK}.audit.signer:probe",
                f"{_SDK}.errors:ConfigError",
            }
        ),
        settings=(("self.mount", "transit_mount"), ("self.key_name", "key_name")),
    ),
    "src/hadavin_sdk/sources/kubernetes.py": Shape(
        "kubernetes_rbac",
        {"_fetch": None, "_call": 1, "_get": 1, "_items": 1},
        frozenset({("_call", 171, "_fetch"), ("_get", 187, "_call"), ("_items", 206, "_get")}),
        imports=frozenset(
            {
                "__future__:annotations",
                "json",
                "collections.abc:Callable",
                "datetime:UTC",
                "datetime:datetime",
                "typing:Any",
                "urllib.parse:quote",
                "pydantic:BaseModel",
                "pydantic:ConfigDict",
                "pydantic:Field",
                f"{_SDK}:defaults",
                f"{_SDK}.sources:Record",
                f"{_SDK}.sources:SourceError",
            }
        ),
        getattr_ok=frozenset({"too_large"}),
    ),
}
# Names that reach a method or a module without writing its name as a plain call. Refused wherever they
# appear in a declared module: as a name, an attribute, an imported name or an alias.
BANNED_NAMES = {
    "_make_api_call",
    "get_waiter",
    "methodcaller",
    "attrgetter",
    "__getattribute__",
    "__getattr__",
    "__dict__",
    "__import__",
    "import_module",
    "eval",
    "exec",
    "globals",
    "locals",
    "vars",
    "setattr",
    "partial",
    "partialmethod",
}
RAW_HTTP = {
    "Request",
    "urlopen",
    "urlretrieve",
    "build_opener",
    "open",
    "HTTPConnection",
    "HTTPSConnection",
    "create_connection",
    "socket",
    "getresponse",
}
OPENER = "_opener"  # the attribute that holds the HTTP opener of the Vault client
_HOLE = "\x00"  # stands for the wrapper's own path parameter inside its template
# Kubernetes: the query parameters a request written in the module may carry, per operation id. None of them
# changes the verb the request needs (`watch=true` would need the verb `watch`; it is refused, like any name
# not listed). PAGING is what the list wrapper `_items` adds to both list requests.
QUERY_OK: dict[str, frozenset[str]] = {
    "k8s.pod_log": frozenset({"timestamps", "sinceTime", "limitBytes"})
}
PAGING = frozenset({"limit", "continue"})
# A query parameter name in any text: `?name=`, `&name=`, and a bare `&name` or `?name` (Kubernetes reads a bare
# `watch` as true).
QUERY_NAME = r"[?&]([A-Za-z_]\w*)(?==|&|$)"
# The only text pieces the query of `_items` may be built from (what PAGING lists, nothing else).
_PAGING_TEXT = frozenset({"?limit=", "&continue=", ""})
# Vault: the capability each HTTP verb of a declared request needs (source V-POL).
VERB_CAPABILITY = {"GET": "read", "POST": "update"}


def _template(node: ast.AST | None) -> str | None:
    """A path written as a literal or an f-string, folded to a template: a formatted `self.X` / `obj.X` gives
    `{self.X}` / `{obj.X}` (the object's name is kept, so a local variable named like a setting is not taken
    for the setting), a formatted bare name gives `{name}`. Anything else (a call, a conversion, a format
    spec, a literal brace) is not foldable: None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return None if "{" in node.value or "}" in node.value else node.value
    if not isinstance(node, ast.JoinedStr):
        return None
    out = ""
    for part in node.values:
        if isinstance(part, ast.Constant) and isinstance(part.value, str):
            if "{" in part.value or "}" in part.value:
                return None
            out += part.value
        elif (
            isinstance(part, ast.FormattedValue)
            and part.conversion == -1
            and part.format_spec is None
        ):
            value = part.value
            if isinstance(value, ast.Name):
                out += "{" + value.id + "}"
            elif isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name):
                out += "{" + value.value.id + "." + value.attr + "}"
            else:
                return None
        else:
            return None
    return out


def _params(func: ast.AST | None) -> list[str]:
    if not isinstance(func, ast.FunctionDef | ast.AsyncFunctionDef):
        return []
    a = func.args
    names = [x.arg for x in (*a.posonlyargs, *a.args, *a.kwonlyargs)]
    return [n for n in names if n not in ("self", "cls")]


def _argument(call: ast.Call, position: int | None, keyword: str) -> ast.AST | None:
    """The argument at `position` or named `keyword`; None when it is absent or hidden behind * or **."""
    if any(isinstance(a, ast.Starred) for a in call.args) or any(
        k.arg is None for k in call.keywords
    ):
        return None
    for k in call.keywords:
        if k.arg == keyword:
            return k.value
    if position is not None and len(call.args) > position:
        return call.args[position]
    return None


class _Walk(ast.NodeVisitor):
    """Every call and every attribute read, each with its innermost enclosing function."""

    def __init__(self) -> None:
        self.stack: list[ast.AST] = []
        self.calls: list[tuple[ast.AST | None, ast.Call]] = []
        self.loads: list[tuple[ast.AST | None, ast.Attribute]] = []
        self.called: set[int] = set()

    def _function(self, node: ast.AST) -> None:
        self.stack.append(node)
        self.generic_visit(node)
        self.stack.pop()

    visit_FunctionDef = _function
    visit_AsyncFunctionDef = _function

    def visit_Call(self, node: ast.Call) -> None:
        self.calls.append((self.stack[-1] if self.stack else None, node))
        self.called.add(id(node.func))
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if isinstance(node.ctx, ast.Load):
            self.loads.append((self.stack[-1] if self.stack else None, node))
        self.generic_visit(node)


def _name_of(func: ast.AST | None) -> str:
    return getattr(func, "name", "<module>")


def _banned(rel: str, shape: Shape, tree: ast.AST, walk: _Walk) -> list[str]:
    out = []
    for node in ast.walk(tree):
        line = getattr(node, "lineno", 0)
        name = node.attr if isinstance(node, ast.Attribute) else getattr(node, "id", None)
        if name in BANNED_NAMES:
            out.append(f"{rel}:{line}: banned indirect call `{name}`")
        if isinstance(node, ast.alias):
            for part in (*node.name.split("."), node.asname):
                if part in BANNED_NAMES:
                    out.append(f"{rel}:{line}: banned indirect call `{part}` (imported)")
        if isinstance(node, ast.Import | ast.ImportFrom):
            module = "." * getattr(node, "level", 0) + (getattr(node, "module", None) or "")
            for alias in node.names:
                entry = f"{module}:{alias.name}" if isinstance(node, ast.ImportFrom) else alias.name
                if entry not in shape.imports:
                    out.append(
                        f"{rel}:{line}: import `{entry}` is not on this module's import list: a new way "
                        "to send a request must be looked at by a person first"
                    )
                elif alias.asname is not None:
                    out.append(f"{rel}:{line}: import `{entry}` is renamed to `{alias.asname}`")
        if (
            isinstance(node, ast.Attribute)
            and node.attr == "client"
            and isinstance(node.value, ast.Attribute)
            and node.value.attr == "meta"
        ):
            out.append(f"{rel}:{line}: banned indirect call `.meta.client`")
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "getattr"
        ):
            literal = len(node.args) > 1 and isinstance(node.args[1], ast.Constant)
            if not literal:
                out.append(f"{rel}:{line}: banned `getattr` with a name that is not a literal")
            elif node.args[1].value not in shape.getattr_ok:
                out.append(
                    f"{rel}:{line}: banned `getattr` of `{node.args[1].value}`: only "
                    f"{sorted(shape.getattr_ok) or 'no name'} may be read this way in this module"
                )
    for func, node in walk.loads:
        if node.attr in shape.sinks and id(node) not in walk.called:
            out.append(
                f"{rel}:{node.lineno}: `.{node.attr}` is taken as a value, not called: the request it "
                "would send cannot be read"
            )
        if node.attr == OPENER and _name_of(func) not in shape.raw_http:
            out.append(
                f"{rel}:{node.lineno}: the HTTP opener `.{OPENER}` is used outside "
                f"{sorted(shape.raw_http) or 'any allowed function'}"
            )
    for func, call in walk.calls:
        f = call.func
        name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
        if name in RAW_HTTP and _name_of(func) not in shape.raw_http:
            out.append(
                f"{rel}:{call.lineno}: raw HTTP call `{name}` outside "
                f"{sorted(shape.raw_http) or 'any allowed function'}"
            )
    return out


def _bound_once(func: ast.AST | None, node: ast.AST | None) -> ast.AST | None:
    """`node` itself, or, when it is a local name bound exactly once in `func` by a plain assignment, the
    value it was given. None when the name is bound in any other way or more than once."""
    if not isinstance(node, ast.Name):
        return node
    if func is None:
        return None
    stores = [
        n
        for n in ast.walk(func)
        if isinstance(n, ast.Name) and n.id == node.id and isinstance(n.ctx, ast.Store)
    ]
    values = [
        n.value
        for n in ast.walk(func)
        if isinstance(n, ast.Assign)
        and len(n.targets) == 1
        and isinstance(n.targets[0], ast.Name)
        and n.targets[0].id == node.id
    ]
    return values[0] if len(stores) == 1 and len(values) == 1 else None


def _quoted_or_setting(func: ast.AST | None, value: ast.AST) -> bool:
    """May this formatted value stand in a Kubernetes request path? Only `quote(<name>, safe="")` (so it can
    add no `/`, `?` or `&`), a local name bound once to such a call, or a setting `self._cfg.<field>`."""
    value = _bound_once(func, value)
    if (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id == "quote"
        and len(value.args) == 1
        and isinstance(value.args[0], ast.Name)
        and [(k.arg, getattr(k.value, "value", None)) for k in value.keywords] == [("safe", "")]
    ):
        return True
    return (
        isinstance(value, ast.Attribute)
        and isinstance(value.value, ast.Attribute)
        and value.value.attr == "_cfg"
        and isinstance(value.value.value, ast.Name)
        and value.value.value.id == "self"
    )


def kubernetes_path_problems(
    rel: str, func: ast.AST | None, call: ast.Call, operation: str
) -> list[str]:
    """The path a Kubernetes request is written with must fit the path bound to its operation id, and its
    query string may hold only the parameter names listed for that id. This is what ties the declared verb
    to the request: `?watch=true` on a list path needs the verb `watch`, which no grant declares."""
    where = f"{rel}:{call.lineno}"
    if operation not in k8s.READ_OPERATIONS:
        return []  # reported as a request with no grant
    node = _bound_once(func, _argument(call, 0, "path"))
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        parts: list[ast.AST] = [node]
    elif isinstance(node, ast.JoinedStr):
        parts = list(node.values)
    else:
        return [f"{where}: the path of `{operation}` is not a literal, so its query cannot be read"]
    text = ""
    for part in parts:
        if isinstance(part, ast.Constant) and isinstance(part.value, str):
            text += part.value
        elif (
            isinstance(part, ast.FormattedValue)
            and part.conversion == -1
            and part.format_spec is None
            and _quoted_or_setting(func, part.value)
        ):
            text += _HOLE
        else:
            return [
                (
                    f"{where}: the path of `{operation}` holds a value that is neither `quote(name, safe='')` "
                    "nor a setting, so what it adds to the request cannot be read"
                )
            ]
    path, mark, query = text.partition("?")
    out = []
    if any(_HOLE in s and s != _HOLE for s in path.split("/")) or not re.fullmatch(
        k8s.READ_OPERATIONS[operation][1], path.replace(_HOLE, "x")
    ):
        out.append(f"{where}: the path does not fit the one bound to `{operation}`")
    allowed = QUERY_OK.get(operation, frozenset())
    for pair in query.split("&") if mark else []:
        name, equals, value = pair.partition("=")
        if not equals or name not in allowed or (_HOLE in value and value != _HOLE):
            out.append(
                f"{where}: query parameter `{name.replace(_HOLE, '?')}` is not one that `{operation}` may "
                f"carry ({sorted(allowed) or 'none'}): it could change the verb the request needs"
            )
    return out


def query_name_problems(rel: str, tree: ast.AST) -> list[str]:
    """Kubernetes, module-wide: every query parameter name written in any text of the module is on a list."""
    allowed = PAGING.union(*QUERY_OK.values())
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            for name in re.findall(QUERY_NAME, node.value):
                if name not in allowed:
                    out.append(
                        f"{rel}:{node.lineno}: query parameter `{name}` is written in the module and is "
                        f"not on the list {sorted(allowed)}"
                    )
    return out


def _call_name(call: ast.Call) -> str | None:
    f = call.func
    return f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)


def _function(tree: ast.AST, name: str) -> list[ast.FunctionDef]:
    return [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name]


def items_query_problems(rel: str, tree: ast.AST) -> list[str]:
    """Kubernetes: the paging wrapper `_items` builds the query that both list requests carry. It is built
    in ONE assignment out of the pieces `_PAGING_TEXT`, the names `limit` and `token`, and `quote(token,
    safe="")`; any other part (a literal or not) is reported, and every `_get` call in `_items` passes
    `path + query` and nothing else. This closes the wrapper line that rule A1 allowlists."""
    funcs = _function(tree, "_items")
    if len(funcs) != 1:
        return [f"{rel}: expected exactly one function `_items`, found {len(funcs)}"]
    func, out = funcs[0], []
    assigns = [
        n
        for n in ast.walk(func)
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "query" for t in n.targets)
    ]
    if len(assigns) != 1:
        return [f"{rel}: `_items` must assign `query` exactly once (found {len(assigns)})"]
    ok_types = (
        ast.JoinedStr,
        ast.FormattedValue,
        ast.IfExp,
        ast.BinOp,
        ast.Add,
        ast.Load,
        ast.keyword,
    )
    for node in ast.walk(assigns[0].value):
        line = getattr(node, "lineno", assigns[0].lineno)
        if isinstance(node, ast.Constant):
            if node.value not in _PAGING_TEXT:
                out.append(
                    f"{rel}:{line}: the query of `_items` holds the text {node.value!r}, which is not "
                    f"one of {sorted(_PAGING_TEXT)}"
                )
        elif isinstance(node, ast.Name):
            if node.id not in {"limit", "token", "quote"}:
                out.append(f"{rel}:{line}: the query of `_items` holds the name `{node.id}`")
        elif isinstance(node, ast.Call):
            good = (
                isinstance(node.func, ast.Name)
                and node.func.id == "quote"
                and len(node.args) == 1
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id == "token"
                and [(k.arg, getattr(k.value, "value", None)) for k in node.keywords]
                == [("safe", "")]
            )
            if not good:
                out.append(
                    f"{rel}:{line}: the query of `_items` holds a call other than `quote(token, safe='')`"
                )
        elif not isinstance(node, ok_types):
            out.append(f"{rel}:{line}: the query of `_items` holds a {type(node).__name__}")
    for call in (n for n in ast.walk(func) if isinstance(n, ast.Call) and _call_name(n) == "_get"):
        arg = call.args[0] if call.args else None
        if not (
            isinstance(arg, ast.BinOp)
            and isinstance(arg.op, ast.Add)
            and isinstance(arg.left, ast.Name)
            and arg.left.id in _params(func)
            and isinstance(arg.right, ast.Name)
            and arg.right.id == "query"
        ):
            out.append(
                f"{rel}:{call.lineno}: `_items` calls `_get` with something other than `path + query`"
            )
    return out


def sender_problems(rel: str, shape: Shape, tree: ast.AST) -> list[str]:
    """Vault: the one sending function `call` holds exactly one request construction, with the address and
    path of the declared shape (`<address>/v1/<path>`) and the method it was given, and exactly one send
    through the opener. A second request, a changed address or a changed method inside it is reported."""
    if "call" not in shape.raw_http:
        return []
    funcs = _function(tree, "call")
    if len(funcs) != 1:
        return [f"{rel}: expected exactly one function `call`, found {len(funcs)}"]
    calls = [n for n in ast.walk(funcs[0]) if isinstance(n, ast.Call)]
    requests = [c for c in calls if _call_name(c) == "Request"]
    sends = [c for c in calls if _call_name(c) == "open"]
    out = []
    if len(requests) != 1 or len(sends) != 1:
        return [
            f"{rel}: `call` must hold exactly one `Request` and one `open` (found {len(requests)} and {len(sends)})"
        ]
    req, send = requests[0], sends[0]
    if _template(_argument(req, 0, "url")) != "{self.address}/v1/{path}":
        out.append(
            f"{rel}:{req.lineno}: the request of `call` is not sent to `<address>/v1/<path>`"
        )
    method = next((k.value for k in req.keywords if k.arg == "method"), None)
    if not (isinstance(method, ast.Name) and method.id == "method"):
        out.append(
            f"{rel}:{req.lineno}: the request of `call` does not use the method it was given"
        )
    if {k.arg for k in req.keywords} != {"data", "headers", "method"} or len(req.args) != 1:
        out.append(
            f"{rel}:{req.lineno}: the request of `call` has arguments other than url, data, headers, method"
        )
    target = _argument(send, 0, "req")
    if not (
        isinstance(target, ast.Name)
        and isinstance(send.func, ast.Attribute)
        and isinstance(send.func.value, ast.Attribute)
        and send.func.value.attr == OPENER
    ):
        out.append(
            f"{rel}:{send.lineno}: `call` sends something other than its one request through the opener"
        )
    return out


def settings_flow_problems(rel: str, tree: ast.AST, shape: Shape, cls: str) -> list[str]:
    """Vault: each (object attribute -> setting) of `shape.settings` is real. `build` hands the setting to
    the class `cls` (as a keyword or by position, directly or through `connect(**kw)`), and the class
    `__init__` stores that parameter under the attribute's name."""
    builds = [
        f
        for f in tree.body
        if isinstance(f, ast.FunctionDef) and f.name == "build"  # type: ignore[attr-defined]
    ]
    classes = [c for c in ast.walk(tree) if isinstance(c, ast.ClassDef) and c.name == cls]
    if len(builds) != 1 or len(classes) != 1:
        return [f"{rel}: expected one `build` and one class `{cls}`"]
    inits = _function(classes[0], "__init__")
    if len(inits) != 1:
        return [f"{rel}: class `{cls}` must have one `__init__`"]
    params = _params(inits[0])
    stored: dict[str, str] = {}
    for node in ast.walk(inits[0]):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target, value = node.targets[0], node.value
            pairs = (
                list(zip(target.elts, value.elts, strict=False))
                if isinstance(target, ast.Tuple) and isinstance(value, ast.Tuple)
                else [(target, value)]
            )
            for tgt, val in pairs:
                if (
                    isinstance(tgt, ast.Attribute)
                    and isinstance(tgt.value, ast.Name)
                    and tgt.value.id == "self"
                    and isinstance(val, ast.Name)
                    and val.id in params
                ):
                    stored[tgt.attr] = val.id
    out = []
    for attr, setting in shape.settings:
        name = attr.removeprefix("self.")
        passed: set[str] = set()
        for call in (n for n in ast.walk(builds[0]) if isinstance(n, ast.Call)):
            for k in call.keywords:
                if k.arg and _is_setting(k.value, setting):
                    passed.add(k.arg)
            if _call_name(call) == cls:
                for i, a in enumerate(call.args):
                    if _is_setting(a, setting) and i < len(params):
                        passed.add(params[i])
        if name not in stored:
            out.append(f"{rel}: `{cls}.__init__` does not store a parameter as `{attr}`")
        elif stored[name] not in passed:
            out.append(
                f"{rel}: `build` does not hand the setting `{setting}` to the parameter `{stored[name]}` "
                f"that `{cls}` stores as `{attr}`"
            )
    return out


def _is_setting(node: ast.AST, setting: str) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == setting
        and isinstance(node.value, ast.Name)
        and node.value.id == "settings"
    )


def binding_problems(rel: str, shape: Shape, policy: pp.Policy) -> list[str]:
    """Vault: each grant IS its one request. The resource must equal the request's path with every object
    attribute replaced by its setting and every bare parameter (one caller-chosen path part) replaced by
    the one-part wildcard `+`; the capability must be the one the request's verb needs."""
    settings, out = dict(shape.settings), []
    for g in policy.grants:
        if len(g.operations) != 1:
            out.append(f"{rel} {g.id}: a Vault grant serves exactly one request")
            continue
        verb, template = g.operations[0]
        names = re.findall(r"\{([^{}]*)\}", template)
        unknown = sorted(n for n in names if "." in n and n not in settings)
        if unknown:
            out.append(f"{rel} {g.id}: `{unknown[0]}` in the request path is not a known setting")
            continue
        want = re.sub(
            r"\{([^{}]*)\}",
            lambda m: "{" + settings[m.group(1)] + "}" if "." in m.group(1) else "+",
            template,
        )
        if g.resource != want:
            out.append(
                f"{rel} {g.id}: resource {g.resource!r} is not the path of the request it serves ({want!r})"
            )
        if g.name != VERB_CAPABILITY.get(verb):
            out.append(
                f"{rel} {g.id}: capability {g.name!r} is not the one a {verb} request needs "
                f"({VERB_CAPABILITY.get(verb)!r})"
            )
    return out


def extract(
    rel: str, text: str, shape: Shape
) -> tuple[dict[tuple[str, ...], list[int]], list[str]]:
    """(the requests written in the module -> their lines, problems). Reads `ast.Call` nodes only, so a
    docstring or a comment never counts."""
    tree = ast.parse(text)
    walk = _Walk()
    walk.visit(tree)
    problems = _banned(rel, shape, tree, walk)
    vault = shape.platform == "vault"
    if not vault:
        problems += query_name_problems(rel, tree)
        if "_items" in shape.sinks:
            problems += items_query_problems(rel, tree)
    else:
        problems += sender_problems(rel, shape, tree)
    sink_calls = [
        (func, call, call.func.attr)
        for func, call in walk.calls
        if isinstance(call.func, ast.Attribute) and call.func.attr in shape.sinks
    ]
    templates: dict[
        str, str
    ] = {}  # wrapper function -> its path template, _HOLE for its own parameter
    seen: set[tuple[str, int, str]] = set()
    literal_calls = []
    for func, call, sink in sink_calls:
        key = (_name_of(func), call.lineno, sink)
        if key not in shape.wrappers:
            literal_calls.append((func, call, sink))
            continue
        params = _params(func)
        position = shape.sinks[sink]
        operation = _argument(call, position, "path" if vault else "operation")
        passes = False
        if vault:
            verb = _argument(call, 0, "method")
            folded = _template(operation)
            if isinstance(operation, ast.Name):
                folded = "{" + operation.id + "}"
            if (
                len(params) >= 2
                and isinstance(verb, ast.Name)
                and verb.id == params[0]
                and folded is not None
                and folded.count("{" + params[1] + "}") == 1
                and not any(("{" + p + "}") in folded for p in params if p != params[1])
            ):
                passes = True
                templates[_name_of(func)] = folded.replace("{" + params[1] + "}", _HOLE)
        else:
            passes = isinstance(operation, ast.Name) and operation.id in params
        if passes:
            seen.add(key)
        else:
            problems.append(
                f"{rel}:{call.lineno}: allowlisted call to `.{sink}` in `{key[0]}` does not pass on a "
                "parameter of that function. What to do: the code at that line changed; move or remove "
                "the entry in SHAPES (`wrappers`) of tests/test_policy_guard.py"
            )
    problems += [
        f"{rel}: stale allowlist entry ({func}, line {line}, .{sink}): no call to `.{sink}` that passes "
        f"on a parameter of `{func}` is at that line. What to do: the call moved; set the new line "
        "number of the entry in SHAPES (`wrappers`) of tests/test_policy_guard.py"
        for func, line, sink in sorted(shape.wrappers - seen)
    ]
    found: dict[tuple[str, ...], list[int]] = {}
    for func, call, sink in literal_calls:
        position = shape.sinks[sink]
        operation = _argument(call, position, "path" if vault else "operation")
        pair: tuple[str, ...] | None = None
        if vault:
            verb = _argument(call, 0, "method")
            folded = _template(operation)
            if (
                isinstance(verb, ast.Constant)
                and isinstance(verb.value, str)
                and folded is not None
            ):
                pair = (verb.value, templates.get(sink, _HOLE).replace(_HOLE, folded))
        elif isinstance(operation, ast.Constant) and isinstance(operation.value, str):
            pair = (operation.value,)
            problems += kubernetes_path_problems(rel, func, call, operation.value)
        if pair is None:
            problems.append(
                f"{rel}:{call.lineno}: call to `.{sink}` whose request is not a literal, outside the "
                "allowlisted lines: it cannot be compared with the declared list"
            )
        else:
            found.setdefault(pair, []).append(call.lineno)
    return found, sorted(problems)


def call_problems(rel: str, text: str, shape: Shape) -> list[str]:
    """Rule A1 for one module: the extracted requests EQUAL the requests its POLICY declares."""
    found, problems = extract(rel, text, shape)
    policy = pp.parse(text, rel)
    if policy is None:
        return [*problems, f"no POLICY in {rel}"]
    declared = policy.operations()
    if shape.platform == "vault":
        problems += binding_problems(rel, shape, policy)
    for pair in sorted(set(found) - declared):
        lines = ", ".join(str(n) for n in found[pair])
        problems.append(f"{rel}:{lines}: request {pair} has no grant and no free entry in POLICY")
    for pair in sorted(declared - set(found)):
        problems.append(f"{rel}: POLICY declares request {pair} but the module makes no such call")
    return problems


def _text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


@pytest.mark.parametrize("rel", sorted(SHAPES))
def test_the_calls_written_in_the_module_equal_the_declared_list(rel):
    assert call_problems(rel, _text(rel), SHAPES[rel]) == []


def test_every_declared_kind_module_has_a_call_shape():
    assert set(SHAPES) == set(pp.KIND_MODULES.values())


def test_the_extracted_requests_are_the_ones_the_ticket_lists():
    """The pairs found on main by the ticket author (section 4.3), so a silent change of the reader shows."""
    found = {rel: set(extract(rel, _text(rel), SHAPES[rel])[0]) for rel in SHAPES}
    assert found == {
        "src/hadavin_sdk/actions/secrets_vault.py": {
            ("GET", "{self.mount}/data/{self.path_prefix}{name}"),
            ("POST", "auth/{auth_mount}/login"),
        },
        "src/hadavin_sdk/audit/signer_vault.py": {
            ("POST", "{self.mount}/sign/{self.key_name}"),
            ("GET", "{self.mount}/keys/{self.key_name}"),
        },
        "src/hadavin_sdk/sources/kubernetes.py": {
            ("k8s.list_deployments",),
            ("k8s.list_events",),
            ("k8s.pod_log",),
            ("k8s.rules_review",),
        },
    }


VAULT = "src/hadavin_sdk/actions/secrets_vault.py"
TRANSIT = "src/hadavin_sdk/audit/signer_vault.py"
KUBE = "src/hadavin_sdk/sources/kubernetes.py"


def _planted(rel: str, old: str, new: str) -> list[str]:
    """Rule A1 on a copy of the real module with one piece of text replaced (the copy is never written
    into src/)."""
    text = _text(rel)
    assert text.count(old) == 1, (rel, old, text.count(old))
    return call_problems(rel, text.replace(old, new), SHAPES[rel])


_NEW_METHOD = """

def _planted(provider):
    return provider.authed("LIST", f"{provider.mount}/metadata/{provider.path_prefix}")
"""


def test_plant_a_new_request_with_no_grant_is_caught():
    text = _text(VAULT) + _NEW_METHOD
    line = text.count("\n")
    same(
        call_problems(VAULT, text, SHAPES[VAULT]),
        [
            (
                f"{VAULT}:{line}: request ('LIST', '{{provider.mount}}/metadata/{{provider.path_prefix}}') "
                "has no grant and no free entry in POLICY"
            )
        ],
        what="the check reports: has no grant and no",
    )


def test_plant_a_grant_whose_request_was_deleted_is_caught():
    problems = _planted(TRANSIT, 'self._call("GET", f"keys/{self.key_name}")', "dict(self.cached)")
    same(
        problems,
        [
            (
                f"{TRANSIT}: POLICY declares request ('GET', '{{self.mount}}/keys/{{self.key_name}}') but "
                "the module makes no such call"
            )
        ],
        what="the check reports: makes no such call",
    )


def test_plant_a_request_that_is_not_a_literal_is_caught():
    text = (
        _text(VAULT)
        + "\n\ndef _planted(provider, verb, path):\n    return provider.authed(verb, path)\n"
    )
    line = text.count("\n")
    same(
        call_problems(VAULT, text, SHAPES[VAULT]),
        [
            (
                f"{VAULT}:{line}: call to `.authed` whose request is not a literal, outside the allowlisted "
                "lines: it cannot be compared with the declared list"
            )
        ],
    )


def test_plant_a_path_built_by_a_call_is_not_foldable_and_is_caught():
    text = (
        _text(VAULT)
        + '\n\ndef _planted(p):\n    return p.authed("GET", "/".join([p.mount, "x"]))\n'
    )
    problems = call_problems(VAULT, text, SHAPES[VAULT])
    assert len(problems) == 1 and "whose request is not a literal" in problems[0]


@pytest.mark.parametrize(
    ("code", "message"),
    [
        (
            "getattr(p, name)('GET', 'sys/mounts')",
            "banned `getattr` with a name that is not a literal",
        ),
        (
            "operator.methodcaller('authed', 'GET', 'sys/mounts')(p)",
            "banned indirect call `methodcaller`",
        ),
        ("p.__getattribute__('authed')", "banned indirect call `__getattribute__`"),
        ("p.meta.client.get_waiter('x')", "banned indirect call `.meta.client`"),
        ("p._make_api_call('GetSecretValue', {})", "banned indirect call `_make_api_call`"),
    ],
)
def test_plant_a_banned_indirect_call_is_caught(code, message):
    text = _text(VAULT) + f"\n\ndef _planted(p, name):\n    return {code}\n"
    line = text.count("\n")
    assert f"{VAULT}:{line}: {message}" in call_problems(VAULT, text, SHAPES[VAULT])


def test_plant_a_sink_taken_as_a_value_is_caught():
    text = _text(VAULT) + "\n\ndef _planted(p):\n    send = p.authed\n    return send\n"
    line = text.count("\n") - 1
    same(
        call_problems(VAULT, text, SHAPES[VAULT]),
        [
            f"{VAULT}:{line}: `.authed` is taken as a value, not called: the request it would send cannot be read"
        ],
    )


def test_plant_a_raw_http_request_outside_the_one_sender_is_caught():
    text = _text(TRANSIT) + "\n\ndef _planted(url):\n    return urllib.request.Request(url)\n"
    line = text.count("\n")
    same(
        call_problems(TRANSIT, text, SHAPES[TRANSIT]),
        [f"{TRANSIT}:{line}: raw HTTP call `Request` outside any allowed function"],
        what="the check reports: raw HTTP call",
    )


def test_plant_a_stale_allowlist_line_is_caught():
    """One line added above the wrapper moves it: the entry no longer points at a call that passes its
    parameter on, and the moved call is read as a request that is not a literal."""
    problems = _planted(TRANSIT, "import base64\n", "import base64\n\n")
    same(
        problems[:2],
        [
            (
                f"{TRANSIT}: stale allowlist entry (_call, line 40, .authed): no call to `.authed` that passes on "
                "a parameter of `_call` is at that line. What to do: the call moved; set the new line number of the "
                "entry in SHAPES (`wrappers`) of tests/test_policy_guard.py"
            ),
            (
                f"{TRANSIT}:41: call to `.authed` whose request is not a literal, outside the allowlisted lines: "
                "it cannot be compared with the declared list"
            ),
        ],
        what="the check reports: stale allowlist entry",
    )
    # with the wrapper no longer recognised, its `{mount}/` is not added, so no request matches either
    assert len(problems) == 6 and all(
        "('POST', 'sign/{self.key_name}')" not in p for p in problems[:2]
    )


def test_plant_an_allowlisted_line_that_stops_passing_its_parameter_is_caught():
    problems = _planted(
        TRANSIT,
        'self._vault.authed(method, f"{self.mount}/{path}", body)',
        'self._vault.authed(method, f"{self.mount}/keys/x", body)',
    )
    assert (
        f"{TRANSIT}:40: allowlisted call to `.authed` in `_call` does not pass on a parameter of that function. "
        "What to do: the code at that line changed; move or remove the entry in SHAPES (`wrappers`) of "
        "tests/test_policy_guard.py" in problems
    ), (
        f"an allowlisted call that stops passing its parameter gives no hint to move or remove the entry in SHAPES: {problems}"
    )


def test_a_request_named_only_in_a_docstring_changes_nothing():
    text = _text(VAULT) + '\n\ndef _planted():\n    """self.authed("DELETE", "sys/mounts/x")"""\n'
    assert call_problems(VAULT, text, SHAPES[VAULT]) == []


def test_plant_a_new_kubernetes_operation_is_caught():
    text = (
        _text(KUBE)
        + '\n\ndef _planted(source):\n    return source._get("/api/v1/secrets", "k8s.list_secrets")\n'
    )
    line = text.count("\n")
    same(
        call_problems(KUBE, text, SHAPES[KUBE]),
        [f"{KUBE}:{line}: request ('k8s.list_secrets',) has no grant and no free entry in POLICY"],
    )


def test_template_folds_only_names_and_attributes():
    def fold(code: str) -> str | None:
        return _template(ast.parse(code, mode="eval").body)

    assert (
        fold('f"{self.mount}/data/{self.path_prefix}{name}"')
        == "{self.mount}/data/{self.path_prefix}{name}"
    )
    assert fold('"sys/mounts"') == "sys/mounts"
    for code in (
        'f"{a.b.c}"',
        'f"{name!r}"',
        'f"{name:>4}"',
        'f"{f()}"',
        '"a{b}"',
        "name",
        'f"{{x}}"',
    ):
        assert fold(code) is None, code


# ------------------------------------------------------------------------------------- Kubernetes bindings


def _derived(operation: str) -> tuple[str, str, str]:
    """(API group, resource, verb) from the path pattern bound to an operation id in READ_OPERATIONS: a
    collection path gives `list`, an object or subresource path gives `get`."""
    method, pattern = k8s.READ_OPERATIONS[operation]
    assert method == "GET", operation
    parts = pattern.replace(k8s._NS, "{}").strip("/").split("/")
    group = "core" if parts[0] == "api" else parts[1]
    rest = parts[2:] if parts[0] == "api" else parts[3:]
    assert rest[:2] == ["namespaces", "{}"], pattern
    rest = rest[2:]
    if len(rest) == 1:
        return group, rest[0], "list"
    assert rest[1] == "{}" and len(rest) <= 3, pattern
    return group, "/".join([rest[0], *rest[2:]]), "get"


def test_kubernetes_declared_operations_equal_the_bound_operation_ids():
    policy = _policies()["source/kubernetes"]
    assert policy.operations() == {(op,) for op in k8s.READ_OPERATIONS}
    assert set(extract(KUBE, _text(KUBE), SHAPES[KUBE])[0]) == {(op,) for op in k8s.READ_OPERATIONS}


def test_each_kubernetes_grant_is_the_verb_and_resource_of_its_path():
    for grant in _policies()["source/kubernetes"].grants:
        assert len(grant.operations) == 1, grant.id
        group, resource, verb = _derived(grant.operations[0][0])
        assert grant.resource == f"{group}/{resource} in {{namespaces}}", grant.id
        assert grant.name == verb, grant.id


def test_the_kubernetes_never_list_equals_what_the_code_refuses_at_start_up():
    never = _policies()["source/kubernetes"].never
    assert {n.name for n in never if n.type == "action"} == set(k8s._WRITE_VERBS)
    assert {n.name for n in never if n.type == "resource"} == set(k8s._SHELL_RESOURCES) | {
        "secrets"
    }
    assert "watch" not in {n.name for n in never}  # the code does not refuse `watch`: not claimed


def _role_rules(text: str) -> list[list[dict]]:
    docs = list(yaml.safe_load_all(text))
    assert {d["kind"] for d in docs} == {"Role", "RoleBinding"}  # never a ClusterRole
    return [d["rules"] for d in docs if d["kind"] == "Role"]


K8S_VALUES = {
    "namespaces": "shop,payments",
    "ROLE_NAME": "hadavin-read",
    "SERVICE_ACCOUNT": "hadavin-agent",
    "SERVICE_ACCOUNT_NAMESPACE": "hadavin",
}


def test_the_generated_role_passes_the_kinds_own_read_only_rule():
    policy = _policies()["source/kubernetes"]
    text = pp.render_kubernetes(policy, K8S_VALUES)
    docs = list(yaml.safe_load_all(text))
    same(
        [(d["kind"], d["metadata"]["namespace"]) for d in docs],
        [
            ("Role", "shop"),
            ("RoleBinding", "shop"),
            ("Role", "payments"),
            ("RoleBinding", "payments"),
        ],
    )
    for rules in _role_rules(text):
        assert rules == pp.kubernetes_rules(policy)
        assert k8s.rules_problems("shop", rules) == []
    binding = docs[1]
    assert binding["roleRef"] == {
        "apiGroup": "rbac.authorization.k8s.io",
        "kind": "Role",
        "name": "hadavin-read",
    }
    same(
        binding["subjects"],
        [{"kind": "ServiceAccount", "name": "hadavin-agent", "namespace": "hadavin"}],
    )


@pytest.mark.parametrize(
    ("extra", "word"),
    [
        (
            {"apiGroups": ["apps"], "resources": ["deployments"], "verbs": ["patch"]},
            "write verb patch",
        ),
        ({"apiGroups": [""], "resources": ["pods/exec"], "verbs": ["get"]}, "access to pods/exec"),
        (
            {"apiGroups": [""], "resources": ["secrets"], "verbs": ["list"]},
            "read access to secrets",
        ),
    ],
)
def test_plant_a_widened_role_fails_the_kinds_own_read_only_rule(extra, word):
    rules = [*pp.kubernetes_rules(_policies()["source/kubernetes"]), extra]
    problems = k8s.rules_problems("shop", rules)
    assert len(problems) == 1 and word in problems[0], problems


# ------------------------------------------------------------------------------------------ A2: data rules


def _raw(kind: str) -> dict:
    raw = pp.literal(_text(pp.KIND_MODULES[kind]))
    assert isinstance(raw, dict), f"no POLICY in {pp.KIND_MODULES[kind]}"
    return copy.deepcopy(raw)


def _grant_changed(kind: str, **changes) -> list[str]:
    raw = _raw(kind)
    raw["grants"] = ({**raw["grants"][0], **changes}, *raw["grants"][1:])
    return pp.problems(raw)


def test_the_three_literals_break_no_data_rule():
    for kind in pp.KIND_MODULES:
        assert pp.problems(_raw(kind)) == [], kind
    assert pp.cross_problems(_policies()) == []


def test_plant_d1_a_wildcard_in_a_permission_name_is_caught():
    same(
        _grant_changed("secrets/vault", name="re*d"),
        [
            "grant R17: name 're*d' must be one permission name with no * or ?",
            "grant R17: 're*d' is not a Vault capability a grant may hold",
        ],
        what="the check reports: must be one permission name",
    )


def test_plant_d1_a_wildcard_resource_with_no_bound_is_caught():
    same(
        _grant_changed("secrets/vault", bound=" "),
        [
            (
                "grant R17: resource '{mount}/data/{path_prefix}+' holds a wildcard, so `bound` must say what "
                "limits it"
            )
        ],
        "a blank `bound` on the wildcard resource of the Vault secrets grant is not reported",
    )
    same(
        _grant_changed("signer/vault_transit", resource="{transit_mount}/sign/?"),
        [
            "grant R18: resource '{transit_mount}/sign/?' holds a wildcard, so `bound` must say what limits it"
        ],
        "a wildcard resource with no bound on the Transit signing grant is not reported",
    )


SETTINGS = {
    "secrets/vault": table.VaultSettings,
    "signer/vault_transit": table.VaultTransitSettings,
    "source/kubernetes": k8s.KubernetesSettings,
}


def field_problems(kind: str, policy: pp.Policy, settings: type) -> list[str]:
    """D2: every `{field}` of a resource is a setting of the kind."""
    return [
        f"{kind} {g.id}: {{{name}}} is not a setting of {settings.__name__}"
        for g in policy.grants
        for name in pp._FIELD.findall(g.resource)
        if name not in settings.model_fields
    ]


def test_d2_every_field_of_a_resource_is_a_setting_of_the_kind():
    assert set(SETTINGS) == set(pp.KIND_MODULES)
    for kind, policy in _policies().items():
        assert field_problems(kind, policy, SETTINGS[kind]) == []


def test_plant_d2_a_field_that_is_no_setting_is_caught():
    raw = _raw("signer/vault_transit")
    raw["grants"] = ({**raw["grants"][0], "resource": "{mount}/sign/{key_name}"}, raw["grants"][1])
    policy = pp.parse(f"POLICY = {raw!r}")
    same(
        field_problems("signer/vault_transit", policy, table.VaultTransitSettings),
        ["signer/vault_transit R18: {mount} is not a setting of VaultTransitSettings"],
        what="the check reports: is not a setting of",
    )


def test_plant_d3_an_empty_reason_is_caught():
    same(
        _grant_changed("source/kubernetes", reason="  "),
        ["grant R20: reason is empty"],
        "a blank reason on the Kubernetes grant is not reported",
    )
    raw = _raw("secrets/vault")
    raw["never"] = ({**raw["never"][0], "reason": ""},)
    same(
        pp.problems(raw),
        ["never entry 0: reason is empty"],
        "an empty reason on a never-list line is not reported",
    )


def test_plant_d4_a_grant_that_names_no_call_is_caught():
    problems = _grant_changed("signer/vault_transit", operations=())
    assert len(problems) == 1 and problems[0].startswith(
        "grant R18: operations must be a non-empty"
    )
    problems = _grant_changed("signer/vault_transit", operations=(("POST",),))
    assert len(problems) == 1 and "2-part tuples" in problems[0]


def test_plant_d5_a_never_action_that_another_kind_needs_is_caught():
    policies = _policies()
    raw = _raw("source/kubernetes")
    raw["never"] = (
        *raw["never"],
        {"type": "action", "name": "list", "reason": "r", "verified": None},
    )
    policies["source/kubernetes"] = pp.parse(f"POLICY = {raw!r}")
    same(
        pp.cross_problems(policies),
        [
            "source/kubernetes: never-list action 'list' is a permission that source/kubernetes needs"
        ],
        what="the check reports: never-list action",
    )


def test_plant_a_grant_id_used_by_two_kinds_is_caught():
    policies = _policies()
    raw = _raw("signer/vault_transit")
    raw["grants"] = ({**raw["grants"][0], "id": "R17"}, raw["grants"][1])
    policies["signer/vault_transit"] = pp.parse(f"POLICY = {raw!r}")
    same(
        pp.cross_problems(policies),
        ["grant id R17 is used by secrets/vault and by signer/vault_transit"],
        what="the check reports: is used by",
    )
    raw["grants"] = ({**raw["grants"][0], "id": "R19"}, raw["grants"][1])
    same(pp.problems(raw), ["grant id R19 is used twice"])


def test_plant_d6_a_long_lived_credential_with_no_exception_is_caught():
    raw = _raw("secrets/vault")
    assert raw["credential"]["lifetime"] == "long"
    raw["credential"] = {**raw["credential"], "exception": ""}
    same(
        pp.problems(raw),
        ["credential: a long-lived credential needs `exception`: why, and what removes it"],
        what="the check reports: long-lived credential",
    )


@pytest.mark.parametrize(
    "value",
    ["POLICY = dict(platform='vault')", "POLICY = {'platform': PLATFORM}", "POLICY = {**BASE}"],
)
def test_plant_d7_a_policy_that_is_not_a_pure_literal_is_refused_and_never_run(value):
    with pytest.raises(pp.PolicyError, match="not a pure literal"):
        pp.parse(f"import os\nBASE = PLATFORM = os.sep\n{value}\n", "planted.py")


def test_plant_d7_unknown_keys_platform_and_never_type_are_refused():
    raw = _raw("secrets/vault")
    same(
        pp.problems({**raw, "deny": ()}),
        ["POLICY: unknown key 'deny'"],
        "an extra top-level key `deny` of the policy is not reported",
    )
    same(
        pp.problems({**raw, "platform": "aws_iam"}),
        ["POLICY: unknown platform 'aws_iam'"],
        "a platform name outside the list is not reported",
    )
    same(
        _grant_changed("secrets/vault", no_wire="x"),
        ["grant R17: unknown key 'no_wire'"],
        "an extra key `no_wire` on a grant is not reported",
    )
    never = ({**raw["never"][0], "type": "deny"},)
    same(
        pp.problems({**raw, "never": never}),
        ["never entry 0: unknown never type 'deny'"],
        "a never-list type outside the list is not reported",
    )
    with pytest.raises(pp.PolicyError, match="unknown key 'deny'"):
        pp.parse(f"POLICY = { ({**raw, 'deny': ()})!r}", "planted.py")
    with pytest.raises(pp.PolicyError, match="exactly once"):
        pp.parse(f"POLICY = {raw!r}\nPOLICY = {raw!r}\n", "planted.py")


def test_a_module_with_no_policy_loads_as_none(tmp_path):
    (tmp_path / "x.py").write_text('"""POLICY = {}"""\nimport os\n', encoding="utf-8")
    assert pp.load(tmp_path / "x.py") is None


# ------------------------------------------------------------------------- A4: verified names and sources


def source_ids() -> dict[str, tuple[str, str, str, str]]:
    return pp.source_ids(ROOT)


def _unverified(policies: dict[str, pp.Policy]) -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    for kind, p in policies.items():
        out |= {(kind, g.id) for g in p.grants if g.verified is None}
        out |= {(kind, f"free:{i}") for i, f in enumerate(p.free) if f.verified is None}
        out |= {(kind, f"never:{n.name}") for n in p.never if n.verified is None}
    return out


def name_problems(
    policies: dict[str, pp.Policy],
    pending: dict[tuple[str, str], Pending],
    known: set[str],
    today: date,
) -> list[str]:
    """The rule of `pp.name_pending_problems` and every source id resolving in the sources file."""
    return pp.name_pending_problems(policies, pending, today) + pp.source_problems(policies, known)


def _names_problems_today() -> list[str]:
    return name_problems(_policies(), PENDING_NAMES, set(source_ids()), _today())


def test_every_grant_name_is_verified_or_pending_and_every_source_id_resolves():
    assert _names_problems_today() == []


claim_problems = pp.claim_pending_problems


def _claims_problems_today() -> list[str]:
    return claim_problems(_policies(), PENDING_CLAIMS, _today())


def _claims_date_body(policies: dict[str, pp.Policy], pending: dict) -> None:
    """The body of the claims date test, for any policies and list: the end state runs it as its own plant."""
    first = pp.review_day(pending)
    if first is None:  # the end state: no claim is waiting, so nothing can be overdue
        assert claim_problems(policies, pending, DECIDED + timedelta(days=800)) == [], (
            "an empty claims list reports an overdue claim"
        )
        return
    overdue = claim_problems(policies, pending, first + timedelta(days=1))
    due = sum(1 for p in pending.values() if p.review_by == first)
    assert len(overdue) == due and all("is overdue" in p for p in overdue), (
        f"the claims that fall due the day after {first} are not reported as overdue: {overdue}"
    )


def test_every_unchecked_claim_has_a_dated_entry_and_the_suite_goes_red_when_it_is_overdue():
    assert _claims_problems_today() == []
    _claims_date_body(_policies(), PENDING_CLAIMS)


def test_plant_an_unchecked_claim_with_no_pending_entry_is_caught():
    same(
        claim_problems(_policies(), {}, DECIDED),
        [
            f"{kind} {gid}: has an unchecked claim (claims_unverified) and no PENDING_CLAIMS entry"
            for kind, gid in sorted(PENDING_CLAIMS)
        ],
        what="the check reports: has an unchecked claim",
    )
    stale = {**PENDING_CLAIMS, ("secrets/vault", "R99"): PENDING_CLAIMS[("secrets/vault", "R17")]}
    same(
        claim_problems(_policies(), stale, DECIDED),
        ["PENDING_CLAIMS ('secrets/vault', 'R99') is fixed or gone: delete the entry"],
    )


R17_CLAIM = (
    "the + matches exactly one whole path part, nothing deeper",
    "a `read` on a secret's path also serves a request for an older version of that secret",
)
CLAIMED_GRANTS = {"R17", "R18", "R20", "R21", "R22"}


def test_pr1_grants_are_all_named_in_a_source_and_the_grants_with_an_unchecked_claim_are_listed():
    grants = {g.id: g for p in _policies().values() for g in p.grants}
    same(sorted(grants), ["R17", "R18", "R19", "R20", "R21", "R22"])
    for g in grants.values():
        assert g.verified is not None and g.verified[0] == "2026-11-11", g.id
        assert g.confirmed_live is None, g.id
        assert bool(g.claims_unverified) == (g.id in CLAIMED_GRANTS), g.id
    same(grants["R17"].claims_unverified, R17_CLAIM)


def test_the_builder_only_claims_are_not_shown_as_checked_and_no_kind_has_copy_ready_text():
    """Fix batches 2 and 3: the claims in `claims_unverified` and three never-list paths were read by the
    builder only or by nobody (fixture header), so no kind offers copy-ready text."""
    policies = _policies()
    same(
        {k: pp.copy_ready(p) for k, p in policies.items()},
        {"secrets/vault": False, "signer/vault_transit": False, "source/kubernetes": False},
    )
    text = pp.page()
    section = text[text.index("## vault (secrets)") : text.index("## vault_transit (signer)")]
    assert "No copy-ready text" in section and "```" not in section
    assert "nothing deeper (builder read the passage); a `read`" in section
    for kind, name in (
        ("secrets/vault", "{mount}/undelete/*"),
        ("secrets/vault", "{mount}/subkeys/*"),
        ("signer/vault_transit", "{transit_mount}/byok-export/*"),
    ):
        entry = next(n for n in policies[kind].never if n.name == name)
        assert entry.verified is None, name
        assert (kind, f"never:{name}") in PENDING_NAMES, name
        assert f"| `{name}` | " in text and "not yet checked |" in text


def test_a_builder_only_source_is_marked_wherever_the_page_lists_it():
    marks = pp.read_marks(ROOT)
    assert set(marks.builder_only) <= set(source_ids())
    text = pp.page()
    for sid in marks.builder_only:
        assert sid in text, sid
        unmarked = re.findall(rf"\b{sid}\b(?! \(builder only\))", text)
        assert unmarked == [], f"the page lists {sid} without the mark (builder only)"
    cell = pp._checked_cell(("2026-11-11", "V-KV", "V-ACL", "B-ACL"))
    assert cell == "2026-11-11, sources V-KV, V-ACL (builder only), B-ACL (builder only)", (
        f"a builder-only source id is not marked in the checked cell: {cell}"
    )
    assert pp._checked_cell(("2026-11-11", "V-KV")) == "2026-11-11, sources V-KV"


def _with_grant(kind: str, **changes) -> dict[str, pp.Policy]:
    policies = _policies()
    raw = _raw(kind)
    raw["grants"] = ({**raw["grants"][0], **changes}, *raw["grants"][1:])
    policies[kind] = pp.parse(f"POLICY = {raw!r}")
    return policies


def test_plant_an_unverified_grant_with_no_pending_entry_is_caught():
    policies = _with_grant("secrets/vault", verified=None)
    same(
        name_problems(policies, PENDING_NAMES, set(source_ids()), DECIDED),
        [
            (
                "secrets/vault R17: the name is not found in a vendor source (verified is None) and has no "
                "PENDING_NAMES entry"
            )
        ],
        what="the check reports: is not found in a vendor source",
    )
    entry = {
        **PENDING_NAMES,
        ("secrets/vault", "R17"): Pending("r", "t", DECIDED, DECIDED + timedelta(days=29)),
    }
    assert name_problems(policies, entry, set(source_ids()), DECIDED) == []
    overdue = name_problems(policies, entry, set(source_ids()), DECIDED + timedelta(days=30))
    assert len(overdue) == 1 and "is overdue" in overdue[0]
    stale = name_problems(_policies(), entry, set(source_ids()), DECIDED)
    same(stale, ["PENDING_NAMES ('secrets/vault', 'R17') is fixed or gone: delete the entry"])


def test_plant_a_source_id_that_does_not_resolve_is_caught():
    policies = _with_grant("secrets/vault", verified=("2026-11-11", "V-NOPE"))
    same(
        name_problems(policies, PENDING_NAMES, set(source_ids()), DECIDED),
        ["secrets/vault grant R17: source id V-NOPE is not in the sources file"],
        what="the check reports: is not in the sources file",
    )


@pytest.mark.parametrize(
    "source", ["https://developer.hashicorp.com/vault", "developer.hashicorp.com", "v-kv", ""]
)
def test_plant_a_url_or_host_in_verified_is_refused(source):
    problems = _grant_changed("secrets/vault", verified=("2026-11-11", source))
    assert len(problems) == 1 and "is not a source id" in problems[0]


def test_plant_no_copy_ready_text_for_a_kind_with_an_unverified_grant_or_claim():
    base = _with_grant("signer/vault_transit", claims_unverified=())["signer/vault_transit"]
    assert pp.copy_ready(base), "a transit policy with no unchecked claim is not copy-ready"
    assert not pp.copy_ready(_policies()["signer/vault_transit"]), (
        "copy-ready text is offered for a kind with an unchecked grant"
    )
    for changes in (
        {"verified": None},
        {"claims_unverified": ("the exact path R18 does not also allow (planted)",)},
    ):
        changed = _with_grant("signer/vault_transit", **changes)["signer/vault_transit"]
        assert not pp.copy_ready(changed), (
            "copy-ready text is offered for a kind with an unchecked grant"
        )
        section = "\n".join(
            pp._kind_section("signer/vault_transit", TRANSIT, changed, _marks_for(changed))
        )
        assert "```" not in section and "No copy-ready text" in section
    section = "\n".join(
        pp._kind_section(
            "signer/vault_transit",
            TRANSIT,
            _with_grant("signer/vault_transit", verified=None)["signer/vault_transit"],
            pp.read_marks(ROOT),
        )
    )
    assert "| not yet checked |" in section


# ------------------------------------------------------------------------------------- rendering, grammar


def _pattern(model: type, field: str) -> str:
    return next(
        m.pattern for m in model.model_fields[field].metadata if getattr(m, "pattern", None)
    )


def test_each_grammar_is_the_settings_own_pattern():
    assert "^" + pp.GRAMMAR["mount"] + "$" == table._PATH == _pattern(table.VaultSettings, "mount")
    assert "^" + pp.GRAMMAR["transit_mount"] + "$" == _pattern(
        table.VaultTransitSettings, "transit_mount"
    )
    assert "^" + pp.GRAMMAR["key_name"] + "$" == _pattern(table.VaultTransitSettings, "key_name")
    # the setting allows an empty prefix (`*`); the page grammar is the same pattern with one or more (`+`)
    setting = _pattern(table.VaultSettings, "path_prefix")
    assert setting.endswith(")*$") and "^" + pp.GRAMMAR["path_prefix"] + "$" == setting[:-3] + ")+$"
    assert pp.GRAMMAR["namespaces"] == k8s._NS


VAULT_VALUES = {"mount": "secret", "path_prefix": "hadavin/acme/"}
TRANSIT_VALUES = {"transit_mount": "transit", "key_name": "audit-key"}


def test_vault_text_in_page_mode_and_with_values():
    policies = _policies()
    assert pp.render_vault(policies["secrets/vault"]) == (
        "# R17: reads one named secret; the right also covers every secret directly under the prefix; it may also cover every older version of each (not yet checked against the vendor, see the claims cell)\n"
        'path "{mount}/data/{path_prefix}+" {\n  capabilities = ["read"]\n}\n'
    )
    assert pp.render_vault(policies["secrets/vault"], VAULT_VALUES) == (
        "# R17: reads one named secret; the right also covers every secret directly under the prefix; it may also cover every older version of each (not yet checked against the vendor, see the claims cell)\n"
        'path "secret/data/hadavin/acme/+" {\n  capabilities = ["read"]\n}\n'
    )
    text = pp.render_vault(policies["signer/vault_transit"], TRANSIT_VALUES)
    same(
        re.findall(r'path "([^"]+)" \{\n  capabilities = \["(\w+)"\]\n\}', text),
        [
            ("transit/sign/audit-key", "update"),
            ("transit/keys/audit-key", "read"),
        ],
    )
    assert "*" not in text  # the Transit policy has no wildcard at all


def test_the_page_says_that_the_kubernetes_start_up_check_does_not_refuse_an_over_broad_read():
    """The limit is real: a rule that reads configmaps, pods and nodes gives no problem, and the page must say so."""
    assert (
        k8s.rules_problems(
            "ns",
            [
                {
                    "verbs": ["get", "list"],
                    "resources": ["configmaps", "pods", "nodes"],
                    "apiGroups": [""],
                }
            ],
        )
        == []
    ), "the start-up check now refuses an over-broad read: change the sentence"
    section = pp._kind_section(
        "source/kubernetes", KUBE, _policies()["source/kubernetes"], pp.read_marks(ROOT)
    )
    assert pp.KUBE_PROBE_LIMIT in section, (
        "the page does not say what the start-up check does not see"
    )
    assert "configmaps" in pp.KUBE_PROBE_LIMIT and "does not refuse a read" in pp.KUBE_PROBE_LIMIT


def test_an_empty_vault_prefix_is_refused_and_the_page_says_so_first():
    policy = _policies()["secrets/vault"]
    assert _refused_with(
        lambda: pp.render_vault(policy, {**VAULT_VALUES, "path_prefix": ""}),
        ValueError,
        "'path_prefix' is empty: an empty prefix means the whole mount",
    ), "an empty path_prefix is accepted into the text"
    section = pp._kind_section("secrets/vault", VAULT, policy, pp.read_marks(ROOT))
    assert section[2] == pp.WHOLE_MOUNT
    assert "every secret at the top level of the mount" in pp.WHOLE_MOUNT


@pytest.mark.parametrize(
    "bad", ["*", "a*", "{mount}", "a b", " a", "a\n", "", "..", "a/../b", "a/"]
)
def test_each_vault_grammar_refuses_what_is_not_a_plain_name(bad):
    policies = _policies()
    with pytest.raises(ValueError, match="'mount'"):
        pp.render_vault(policies["secrets/vault"], {**VAULT_VALUES, "mount": bad})
    for key in TRANSIT_VALUES:
        with pytest.raises(ValueError, match=f"'{key}'"):
            pp.render_vault(policies["signer/vault_transit"], {**TRANSIT_VALUES, key: bad})
    if bad != "a/":  # one segment and a slash is a valid prefix
        with pytest.raises(ValueError, match="'path_prefix'"):
            pp.render_vault(policies["secrets/vault"], {**VAULT_VALUES, "path_prefix": bad})


@pytest.mark.parametrize("bad", ["*", "Shop", "a b", "{namespaces}", "shop,", "-a", "a_b", ""])
def test_the_kubernetes_grammar_refuses_what_is_not_a_plain_name(bad):
    policy = _policies()["source/kubernetes"]
    for key in K8S_VALUES:
        with pytest.raises(ValueError, match=f"'{key}'"):
            pp.render_kubernetes(policy, {**K8S_VALUES, key: bad})


def test_a_missing_an_unused_and_a_non_text_value_are_refused():
    policies = _policies()
    with pytest.raises(ValueError, match="'path_prefix' is missing"):
        pp.render_vault(policies["secrets/vault"], {"mount": "secret"})
    with pytest.raises(ValueError, match="'key_name' is not used by this kind"):
        pp.render_vault(policies["secrets/vault"], {**VAULT_VALUES, "key_name": "k"})
    with pytest.raises(ValueError, match="'mount' does not match its grammar"):
        pp.render_vault(policies["secrets/vault"], {**VAULT_VALUES, "mount": 7})
    with pytest.raises(ValueError, match="platform vault"):
        pp.render_vault(policies["source/kubernetes"])
    with pytest.raises(ValueError, match="platform kubernetes_rbac"):
        pp.render_kubernetes(policies["secrets/vault"])


def test_kubernetes_page_mode_keeps_the_placeholders():
    text = pp.render_kubernetes(_policies()["source/kubernetes"])
    assert 'namespace: "{namespaces}"' in text and 'name: "<ROLE_NAME>"' in text
    assert "ClusterRole" not in text and len(_role_rules(text)) == 1


# ------------------------------------------------------------------------------------------------ A3: page


def test_the_committed_page_equals_what_the_data_gives():
    page = ROOT / pp.PAGE
    assert page.is_file(), f"{pp.PAGE} is missing: run `python tools/policy_page.py --write`"
    assert page.read_text(encoding="utf-8") == pp.page(ROOT), (
        f"{pp.PAGE} differs from the data: run `python tools/policy_page.py --write` and commit"
    )
    assert pp.main(["--check"], today=DECIDED) == 0


def test_the_page_states_its_limits_and_offers_text_for_the_three_kinds():
    text = pp.page(ROOT)
    # no kind has copy-ready text while a claim of it is unchecked (fix batches 2 and 3)
    assert text.count("```hcl") == 0 and text.count("```yaml") == 0
    assert text.count("No copy-ready text: at least one permission or claim") == 3
    assert "These tests have not run yet" in text, (
        "the page claims a run that is on record: it does not say these tests have not run yet"
    )
    for words in (
        "No test shows that a permission NAME is right",
        "No policy on this page has been confirmed on a real account",
        "a real Vault server in CI only",
        "These tests have not run yet",
        "no cluster in any test",
        "OpenBao (not yet run)",
        "does not represent sign-in through an",
        "These 16 kinds sign in to an outside system and have no declared permission",
    ):
        assert words in text, words
    assert "smallest" not in text.lower() and "Deny" not in text


def test_plant_a_page_that_differs_from_the_data_fails_the_check(tmp_path, monkeypatch, capsys):
    (tmp_path / "docs").mkdir()
    (tmp_path / pp.PAGE).write_text(pp.page(ROOT) + "edited by hand\n", encoding="utf-8")
    monkeypatch.setattr(pp, "ROOT", tmp_path)
    assert pp.main(["--check"], today=DECIDED) == 1
    assert "differs from the data" in capsys.readouterr().err
    assert pp.main(["--write"], today=DECIDED) == 0 and pp.main(["--check"], today=DECIDED) == 0


# ============================================================ fix batch 1 (result review round 1 of 7af13809)

# ------------------------------------------- M3: indirect or renamed access to a request sink (class plants)

_FETCH_LINE = (
    '        status, body = self.authed("GET", f"{self.mount}/data/{self.path_prefix}{name}")\n'
)
_EVENTS_LINE = (
    '        events, more_e = self._items(f"/api/v1/namespaces/{ns}/events", "k8s.list_events")\n'
)


def test_plant_p04b_an_added_request_through_getattr_with_a_literal_name_is_caught():
    """The independent plant P04b, exactly: an ADDED Vault LIST request sent through `getattr(self, "authed")`."""
    planted = (
        '        getattr(self, "authed")("LIST", f"{self.mount}/metadata/{self.path_prefix}")\n'
        + _FETCH_LINE
    )
    problems = _planted(VAULT, _FETCH_LINE, planted)
    same(
        problems,
        [
            f"{VAULT}:118: banned `getattr` of `authed`: only no name may be read this way in this module"
        ],
        what="the check reports: banned `getattr` of `authed`",
    )


def test_plant_p09a_a_kubernetes_request_with_watch_in_its_query_is_caught():
    """The independent plant P09a, exactly: `?watch=true` sent under the declared id `k8s.list_events`."""
    planted = (
        '        self._get(f"/api/v1/namespaces/{ns}/events?watch=true", "k8s.list_events")\n'
        + _EVENTS_LINE
    )
    problems = _planted(KUBE, _EVENTS_LINE, planted)
    carried, listed = (
        [p for p in problems if "may carry" in p],
        [p for p in problems if "is written in the module" in p],
    )
    same(
        carried,
        [
            (
                f"{KUBE}:250: query parameter `watch` is not one that `k8s.list_events` may carry (none): it "
                "could change the verb the request needs"
            )
        ],
        what="the check reports: may carry",
    )
    same(
        listed,
        [
            (
                f"{KUBE}:250: query parameter `watch` is written in the module and is not on the list "
                "['continue', 'limit', 'limitBytes', 'sinceTime', 'timestamps']"
            )
        ],
        what="the check reports: is written in the module",
    )
    assert len(problems) == 2, f"the planted request gives other lines than these two: {problems}"


@pytest.mark.parametrize(
    ("code", "message"),
    [
        ("getattr(p, 'authed')('GET', 'sys/mounts')", "banned `getattr` of `authed`"),
        ("getattr(p, '_opener').open('https://x')", "banned `getattr` of `_opener`"),
        (
            "__import__('operator').methodcaller('authed', 'GET', 'sys/mounts')(p)",
            "banned indirect call `__import__`",
        ),
        (
            "operator.attrgetter('authed')(p)('GET', 'sys/mounts')",
            "banned indirect call `attrgetter`",
        ),
        ("functools.partial(p.authed, 'GET')('sys/mounts')", "banned indirect call `partial`"),
        ("vars(p)['authed']('GET', 'sys/mounts')", "banned indirect call `vars`"),
        ("p.__dict__['_opener']", "banned indirect call `__dict__`"),
        ("p._opener.open('https://x/v1/sys/mounts')", "raw HTTP call `open` outside"),
        ("p._opener", "the HTTP opener `._opener` is used outside"),
        ("urllib.request.urlretrieve('https://x')", "raw HTTP call `urlretrieve` outside"),
    ],
)
def test_plant_each_indirect_way_to_a_request_is_caught(code, message):
    text = _text(VAULT) + f"\n\ndef _planted(p, name):\n    return {code}\n"
    line = text.count("\n")
    problems = call_problems(VAULT, text, SHAPES[VAULT])
    assert any(p.startswith(f"{VAULT}:{line}: {message}") for p in problems), problems


@pytest.mark.parametrize(
    ("statement", "message"),
    [
        (
            "from operator import methodcaller as mc",
            "banned indirect call `methodcaller` (imported)",
        ),
        ("from operator import attrgetter", "banned indirect call `attrgetter` (imported)"),
        ("import httpx", "import `httpx` is not on this module's import list"),
        ("import socket", "import `socket` is not on this module's import list"),
        ("from http import client", "import `http:client` is not on this module's import list"),
        ("from typing import Any as A", "import `typing:Any` is renamed to `A`"),
    ],
)
@pytest.mark.parametrize("rel", sorted(SHAPES))
def test_plant_a_new_or_renamed_import_in_a_declared_module_is_caught(rel, statement, message):
    """A new HTTP library, or a name that arrives only through an import alias, in any declared module."""
    text = _text(rel) + f"\n\ndef _planted():\n    {statement}\n"
    line = text.count("\n")
    problems = call_problems(rel, text, SHAPES[rel])
    assert any(p.startswith(f"{rel}:{line}: {message}") for p in problems), problems


def test_every_import_of_a_declared_module_is_on_its_list_and_no_entry_is_stale():
    for rel, shape in SHAPES.items():
        found = set()
        for node in ast.walk(ast.parse(_text(rel))):
            if isinstance(node, ast.Import):
                found |= {a.name for a in node.names}
            if isinstance(node, ast.ImportFrom):
                found |= {f"{node.module}:{a.name}" for a in node.names}
        same(sorted(found), sorted(shape.imports))


def test_plant_a_local_variable_named_like_a_setting_is_not_taken_for_the_setting():
    """`self.` is kept when a path is folded: a path built from local names does not equal the declared one."""
    code = (
        "\n\ndef _planted(p, name):\n    mount, path_prefix = 'sys', ''\n"
        "    return p.authed('GET', f'{mount}/data/{path_prefix}{name}')\n"
    )
    text = _text(VAULT) + code
    line = text.count("\n")
    same(
        call_problems(VAULT, text, SHAPES[VAULT]),
        [
            (
                f"{VAULT}:{line}: request ('GET', '{{mount}}/data/{{path_prefix}}{{name}}') has no grant and "
                "no free entry in POLICY"
            )
        ],
        what="the check reports: has no grant",
    )


# Who may use the Vault client outside its own module: module -> the names it may import from it.
VAULT_CLIENT = "hadavin_sdk.actions.secrets_vault"
VAULT_CLIENT_USERS = {TRANSIT: {"VaultError", "connect"}}
# The one place that names the module in a text (the kinds table loads `build` by name).
VAULT_CLIENT_NAMED_IN_TEXT = {"src/hadavin_sdk/backends/table.py"}
VAULT_CLASSES = {"VaultProvider", "VaultTransitSigner"}
# (file, name of the object) pairs whose `.call` is not the Vault client's: `snap.call` of the replay loop
# and `checked.call`, a field of a checked tool call. Neither sends an HTTP request.
CALL_NOT_VAULT = {
    ("src/hadavin_sdk/k1b/loop.py", "snap"),
    ("src/hadavin_sdk/runtime/agent_loop.py", "checked"),
}


def client_user_problems(files: dict[str, str]) -> list[str]:
    """Class: another module, or a subclass, sends requests with the Vault client, where rule A1 does not
    look. Outside the declared modules nothing may import the client (beyond the listed names), name its
    module in a text, subclass its classes or use `.authed`."""
    out = []
    for rel, text in sorted(files.items()):
        if rel == VAULT:
            continue
        allowed = VAULT_CLIENT_USERS.get(rel, set())
        for node in ast.walk(ast.parse(text)):
            line = getattr(node, "lineno", 0)
            names: set[str] = set()
            if isinstance(node, ast.ImportFrom) and node.module == VAULT_CLIENT:
                names = {a.name for a in node.names}
            elif (
                isinstance(node, ast.ImportFrom) and node.module == VAULT_CLIENT.rpartition(".")[0]
            ):
                names = (
                    {"<the module>"}
                    if any(a.name == "secrets_vault" for a in node.names)
                    else set()
                )
            elif isinstance(node, ast.Import):
                names = (
                    {"<the module>"} if any(a.name == VAULT_CLIENT for a in node.names) else set()
                )
            if names - allowed:
                out.append(
                    f"{rel}:{line}: imports {sorted(names - allowed)} from the Vault client module; only "
                    "the declared kind modules may, with the listed names"
                )
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and "secrets_vault" in node.value
                and "\n" not in node.value
                and " " not in node.value
                and rel not in VAULT_CLIENT_NAMED_IN_TEXT
            ):
                out.append(
                    f"{rel}:{line}: names the Vault client module in a text (a load by name)"
                )
            if isinstance(node, ast.ClassDef) and rel not in SHAPES:
                bases = {getattr(b, "attr", getattr(b, "id", None)) for b in node.bases}
                if bases & VAULT_CLASSES:
                    out.append(f"{rel}:{line}: class {node.name} extends a Vault client class")
            if isinstance(node, ast.Attribute) and node.attr == "authed" and rel not in SHAPES:
                out.append(
                    f"{rel}:{line}: uses `.authed` of the Vault client outside a declared module"
                )
            if (
                isinstance(node, ast.Attribute)
                and node.attr == "call"
                and rel not in SHAPES
                and not (
                    isinstance(node.value, ast.Name) and (rel, node.value.id) in CALL_NOT_VAULT
                )
            ):
                out.append(
                    f"{rel}:{line}: uses `.call` of the Vault client outside a declared module (or add the "
                    "file to CALL_NOT_VAULT if its `.call` is another object's)"
                )
    return out


def _src_files() -> dict[str, str]:
    return {
        p.relative_to(ROOT).as_posix(): p.read_text(encoding="utf-8")
        for p in sorted((ROOT / "src").rglob("*.py"))
    }


def test_only_the_declared_modules_use_the_vault_client():
    assert client_user_problems(_src_files()) == []


@pytest.mark.parametrize(
    ("code", "message"),
    [
        (
            "from hadavin_sdk.actions.secrets_vault import connect\n",
            "imports ['connect'] from the Vault client module",
        ),
        (
            "from hadavin_sdk.actions import secrets_vault\n",
            "imports ['<the module>'] from the Vault client module",
        ),
        (
            "import hadavin_sdk.actions.secrets_vault\n",
            "imports ['<the module>'] from the Vault client module",
        ),
        (
            "import importlib\nm = importlib.import_module('hadavin_sdk.actions.secrets_vault')\n",
            "names the Vault client module in a text",
        ),
        ("class Wide(VaultProvider):\n    pass\n", "class Wide extends a Vault client class"),
        (
            "def f(c):\n    return c.authed('LIST', 'sys/mounts')\n",
            "uses `.authed` of the Vault client outside a declared module",
        ),
        (
            "def f(c):\n    return c.call('GET', 'sys/mounts')\n",
            "uses `.call` of the Vault client outside a declared module",
        ),
    ],
)
def test_plant_another_module_or_a_subclass_using_the_vault_client_is_caught(code, message):
    files = {**_src_files(), "src/hadavin_sdk/planted.py": code}
    problems = client_user_problems(files)
    assert len(problems) == 1 and problems[0].startswith("src/hadavin_sdk/planted.py:"), problems
    assert message in problems[0]
    widened = {
        **_src_files(),
        TRANSIT: _text(TRANSIT).replace(
            "VaultError, connect", "VaultError, connect, VaultProvider"
        ),
    }
    same(
        client_user_problems(widened),
        [
            (
                f"{TRANSIT}:21: imports ['VaultProvider'] from the Vault client module; only the declared kind "
                "modules may, with the listed names"
            )
        ],
    )


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (
            'self._call(f"/api/v1/namespaces/{ns}/pods/{ns}/log?follow=true", "k8s.pod_log")',
            "query parameter `follow` is not one that `k8s.pod_log` may carry",
        ),
        (
            'self._get(f"/api/v1/namespaces/{ns}/events?limit=5", "k8s.list_events")',
            "query parameter `limit` is not one that `k8s.list_events` may carry",
        ),
        (
            'self._get(f"/api/v1/namespaces/{ns}/events?", "k8s.list_events")',
            "query parameter `` is not one that `k8s.list_events` may carry",
        ),
        (
            'self._get(f"/api/v1/namespaces/{ns}/events" + "?watch=1", "k8s.list_events")',
            "the path of `k8s.list_events` is not a literal",
        ),
        (
            'self._get(f"/api/v1/namespaces/{scope}/events", "k8s.list_events")',
            "holds a value that is neither `quote(name, safe='')` nor a setting",
        ),
        (
            'self._get(f"/api/v1/namespaces/{ns}/secrets", "k8s.list_events")',
            "the path does not fit the one bound to `k8s.list_events`",
        ),
        (
            'self._get(f"/api/v1/namespaces/{ns}x/events", "k8s.list_events")',
            "the path does not fit the one bound to `k8s.list_events`",
        ),
    ],
)
def test_plant_a_kubernetes_path_or_query_that_changes_the_request_is_caught(call, message):
    problems = _planted(KUBE, _EVENTS_LINE, f"        {call}\n" + _EVENTS_LINE)
    assert any(p.startswith(f"{KUBE}:250: ") and message in p for p in problems), problems


def test_the_query_parameters_the_kubernetes_module_writes_are_exactly_the_listed_ones():
    """What the code can send today: paging on the two lists (the wrapper `_items`), three log parameters."""
    tree = ast.parse(_text(KUBE))
    by_function: dict[str, set[str]] = {}
    for func in ast.walk(tree):
        if isinstance(func, ast.FunctionDef):
            for node in ast.walk(func):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    names = set(re.findall(QUERY_NAME, node.value))
                    if names:
                        by_function.setdefault(func.name, set()).update(names)
    same(by_function, {"_items": set(PAGING), "query_logs": set(QUERY_OK["k8s.pod_log"])})
    assert query_name_problems(KUBE, tree) == []


# ------------------------------------------ fix batch 2: query of `_items`, the sender, the settings flow


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        (
            'query = f"?limit={limit}" + (f"&continue={quote(token, safe=\'\')}" if token else "")',
            'query = f"?limit={limit}&watch" + (f"&continue={quote(token, safe=\'\')}" if token else "")',
            "holds the text '&watch'",
        ),
        (
            'query = f"?limit={limit}" + (f"&continue={quote(token, safe=\'\')}" if token else "")',
            'query = f"?limit={limit}" + (f"&continue={quote(token, safe=\'\')}" if token else "") + "&watch=true"',
            "holds the text '&watch=true'",
        ),
        (
            'query = f"?limit={limit}" + (f"&continue={quote(token, safe=\'\')}" if token else "")',
            'query = f"?limit={limit}" + (f"&{token}=1" if token else "")',
            "holds the text '&'",
        ),
        (
            "page = self._get(path + query, operation)",
            'page = self._get(path + query + "&watch=true", operation)',
            "calls `_get` with something other than `path + query`",
        ),
    ],
)
def test_plant_a_query_the_paging_wrapper_could_send_beyond_paging_is_caught(old, new, message):
    text = _text(KUBE)
    assert text.count(old) == 1, old
    problems = items_query_problems(KUBE, ast.parse(text.replace(old, new)))
    assert any(message in p for p in problems), problems


def test_plant_a_continue_token_quoted_in_another_way_is_caught():
    text = _text(KUBE)
    old = "f\"&continue={quote(token, safe='')}\""
    assert text.count(old) == 1
    for new in ('f"&continue={quote(token)}"', 'f"&continue={token.lower()}"'):
        problems = items_query_problems(KUBE, ast.parse(text.replace(old, new)))
        assert any("holds a call other than" in p for p in problems), (new, problems)
    assert items_query_problems(KUBE, ast.parse(text)) == []


def test_the_bare_query_name_regex_sees_a_name_with_no_equals_sign():
    for text, names in (
        ("?limit=5&watch", ["limit", "watch"]),
        ("&watch", ["watch"]),
        ("/a/b?watch&x=1", ["watch", "x"]),
        ("?limit=5", ["limit"]),
        ("plain text", []),
    ):
        same(re.findall(QUERY_NAME, text), names)


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        (
            'f"{self.address}/v1/{path}"',
            'f"{self.address}/v1/{path}?list=true"',
            "is not sent to `<address>/v1/<path>`",
        ),
        (
            "headers=headers, method=method",
            'headers=headers, method="LIST"',
            "does not use the method it was given",
        ),
        (
            "            with self._opener.open(req, timeout=self.timeout_s) as r:",
            (
                "            self._opener.open(req, timeout=self.timeout_s)\n"
                "            with self._opener.open(req, timeout=self.timeout_s) as r:"
            ),
            "must hold exactly one `Request` and one `open` (found 1 and 2)",
        ),
        (
            "with self._opener.open(req, timeout=self.timeout_s) as r:",
            "with self._opener.open(urllib.request.Request(self.address), timeout=self.timeout_s) as r:",
            "must hold exactly one `Request` and one `open` (found 2 and 1)",
        ),
    ],
)
def test_plant_a_change_inside_the_one_sending_function_is_caught(old, new, message):
    problems = _planted(VAULT, old, new)
    assert any(message in p for p in problems), problems


@pytest.mark.parametrize(
    ("rel", "old", "new", "message"),
    [
        (
            VAULT,
            "path_prefix=settings.path_prefix,",
            "path_prefix=settings.field,",
            "`build` does not hand the setting `path_prefix` to the parameter `path_prefix`",
        ),
        (
            VAULT,
            "mount=settings.mount,",
            "mount=settings.field,",
            "`build` does not hand the setting `mount`",
        ),
        (
            TRANSIT,
            "VaultTransitSigner(client, settings.transit_mount, settings.key_name, version)",
            "VaultTransitSigner(client, settings.key_name, settings.key_name, version)",
            "`build` does not hand the setting `transit_mount`",
        ),
        (
            VAULT,
            "self.mount, self.path_prefix, self.field = mount, path_prefix, field",
            "self.mount, self.path_prefix, self.field = mount, field, path_prefix",
            "`build` does not hand the setting `path_prefix`",
        ),
    ],
)
def test_plant_a_setting_that_reaches_the_request_through_another_attribute_is_caught(
    rel, old, new, message
):
    text = _text(rel)
    assert text.count(old) == 1, old
    cls = "VaultProvider" if rel == VAULT else "VaultTransitSigner"
    problems = settings_flow_problems(rel, ast.parse(text.replace(old, new)), SHAPES[rel], cls)
    assert any(message in p for p in problems), problems


@pytest.mark.parametrize("rel", [VAULT, TRANSIT])
def test_each_mapped_setting_reaches_its_attribute_through_build(rel):
    cls = "VaultProvider" if rel == VAULT else "VaultTransitSigner"
    assert settings_flow_problems(rel, ast.parse(_text(rel)), SHAPES[rel], cls) == []


# One plain plant per new rule, with its own message: the mutant runner reads that message (a `same()` message
# holds the expected text whatever fails, so it cannot tell which assertion failed).
def test_plant_a_second_send_in_the_sending_function_is_the_class_caught():
    problems = _planted(
        VAULT,
        "            with self._opener.open(req, timeout=self.timeout_s) as r:",
        "            self._opener.open(req, timeout=self.timeout_s)\n"
        "            with self._opener.open(req, timeout=self.timeout_s) as r:",
    )
    assert any("must hold exactly one `Request` and one `open`" in p for p in problems), (
        "a second send inside `call` is not reported"
    )


def test_plant_a_bare_watch_in_the_paging_query_is_the_class_caught():
    text = _text(KUBE)
    old = 'query = f"?limit={limit}" +'
    assert text.count(old) == 1
    problems = items_query_problems(
        KUBE, ast.parse(text.replace(old, 'query = f"?limit={limit}&watch" +'))
    )
    assert any("the query of `_items` holds the text" in p for p in problems), (
        "a bare `watch` in the paging query is not reported"
    )


def test_plant_a_setting_handed_to_the_wrong_parameter_is_the_class_caught():
    text = _text(VAULT)
    old = "path_prefix=settings.path_prefix,"
    assert text.count(old) == 1
    problems = settings_flow_problems(
        VAULT,
        ast.parse(text.replace(old, "path_prefix=settings.field,")),
        SHAPES[VAULT],
        "VaultProvider",
    )
    assert any("`build` does not hand the setting" in p for p in problems), (
        "a setting stored in the wrong attribute is not reported"
    )


def test_plant_a_call_of_the_vault_client_in_another_module_is_the_class_caught():
    files = {
        **_src_files(),
        "src/hadavin_sdk/planted.py": "def f(c):\n    return c.call('GET', 'x')\n",
    }
    assert any("uses `.call` of the Vault client" in p for p in client_user_problems(files)), (
        "a `.call` outside the declared modules is not reported"
    )


def namespace_check_problems(rel: str, tree: ast.AST) -> list[str]:
    """A request for a namespace that is not configured is refused in code: both public readers hold an `if`
    whose test starts with `scope not in self.namespaces`. (The namespaced Role would refuse it on a server
    anyway; this keeps the code from asking.)"""
    out = []
    for name in ("_recent_changes", "query_logs"):
        funcs = _function(tree, name)
        tests = [ast.unparse(n.test) for f in funcs for n in ast.walk(f) if isinstance(n, ast.If)]
        if len(funcs) != 1 or not any(x.startswith("scope not in self.namespaces") for x in tests):
            out.append(f"{rel}: `{name}` has no `if scope not in self.namespaces` check")
    return out


def test_the_kubernetes_namespace_check_is_present_in_both_readers():
    assert namespace_check_problems(KUBE, ast.parse(_text(KUBE))) == []


@pytest.mark.parametrize("name", ["_recent_changes", "query_logs"])
def test_plant_removing_the_namespace_check_is_caught(name):
    text = _text(KUBE)
    old = "if scope not in self.namespaces" + (":" if name == "_recent_changes" else " or not pod")
    assert text.count(old) == 1, old
    new = "if False" + (":" if name == "_recent_changes" else " or not pod")
    problems = namespace_check_problems(KUBE, ast.parse(text.replace(old, new)))
    same(problems, [f"{KUBE}: `{name}` has no `if scope not in self.namespaces` check"])


def test_page_with_no_argument_reads_the_data_root_set_at_call_time(tmp_path, monkeypatch):
    """`page()` and `load_all()` resolve their default inside, so a changed `DATA_ROOT` is followed (a default
    argument is fixed when the function is defined). An empty root has no kind module: an error, not the page."""
    assert pp.page() == pp.page(ROOT)
    monkeypatch.setattr(pp, "DATA_ROOT", tmp_path)
    with pytest.raises(pp.PolicyError):
        pp.page()
    with pytest.raises(pp.PolicyError):
        pp.load_all()


# ------------------------------- M2 and the Vault binding: the grant is the request, no wider and no other


def test_each_vault_grant_is_the_path_and_capability_of_its_one_request():
    for rel in (VAULT, TRANSIT):
        policy = pp.parse(_text(rel), rel)
        assert binding_problems(rel, SHAPES[rel], policy) == []
    r17 = _policies()["secrets/vault"].grants[0]
    # the code reads exactly one path part below the prefix, and the grant covers exactly one
    assert r17.resource == "{mount}/data/{path_prefix}+" and "*" not in r17.resource


@pytest.mark.parametrize(
    ("rel", "kind", "changes", "message"),
    [
        (
            VAULT,
            "secrets/vault",
            {"resource": "{mount}/data/{path_prefix}*"},
            (
                "R17: resource '{mount}/data/{path_prefix}*' is not the path of the request it serves "
                "('{mount}/data/{path_prefix}+')"
            ),
        ),
        (
            TRANSIT,
            "signer/vault_transit",
            {"resource": "{transit_mount}/sign/*", "bound": "every key of the mount"},
            (
                "R18: resource '{transit_mount}/sign/*' is not the path of the request it serves "
                "('{transit_mount}/sign/{key_name}')"
            ),
        ),
        (
            TRANSIT,
            "signer/vault_transit",
            {"name": "read"},
            "R18: capability 'read' is not the one a POST request needs ('update')",
        ),
        (
            TRANSIT,
            "signer/vault_transit",
            {"operations": (("POST", "{self.mount}/sign/{self.other}"),)},
            "R18: `self.other` in the request path is not a known setting",
        ),
    ],
)
def test_plant_a_vault_grant_wider_than_or_other_than_its_request_is_caught(
    rel, kind, changes, message
):
    raw = _raw(kind)
    raw["grants"] = ({**raw["grants"][0], **changes}, *raw["grants"][1:])
    policy = pp.parse(f"POLICY = {raw!r}")
    same(binding_problems(rel, SHAPES[rel], policy), [f"{rel} {message}"])


def test_the_secret_name_is_one_path_part_checked_before_any_request():
    """The grant's `+` stands for the secret name. The code refuses a name with a `/` before it sends."""
    from hadavin_sdk.actions.secrets_vault import VaultProvider
    from hadavin_sdk.errors import ConfigError

    sent = []
    provider = VaultProvider("http://127.0.0.1:9", lambda p: sent.append("login") or "t")
    for name in ("a/b", "a/b/c", "..", ""):
        with pytest.raises(ConfigError, match="Vault names here are"):
            provider._fetch(name)
    assert sent == []


def _refusal(call) -> str | None:
    """The text of the refusal `call` raises for an empty Vault prefix, or None when it raised nothing."""
    from hadavin_sdk.errors import ConfigError

    try:
        call()
    except (ConfigError, ValueError) as exc:
        return str(exc)
    except OSError:  # the request was tried: nothing refused it
        return None
    return None


EMPTY_PREFIX_WORDS = "path_prefix must not be empty: an empty prefix would let this kind read every secret directly under the mount"


def test_vault_settings_with_an_empty_path_prefix_are_refused_and_a_named_one_is_taken():
    """Class: a setting that widens a grant to the whole mount by being left out. Refused where the settings are made."""
    from hadavin_sdk.backends.table import VaultSettings

    text = _refusal(lambda: VaultSettings(kind="vault", address="https://vault.example"))
    assert text is not None, "the settings with an empty prefix were taken"
    assert EMPTY_PREFIX_WORDS in text, "the refusal of the empty prefix is not the plain sentence"
    named = VaultSettings(kind="vault", address="https://vault.example", path_prefix="a/")
    assert named.path_prefix == "a/", "a named prefix was not kept"


def test_building_the_vault_kind_from_settings_that_skipped_their_checks_refuses_an_empty_prefix():
    from hadavin_sdk.backends.factory import make
    from hadavin_sdk.backends.table import VaultSettings

    skipped = VaultSettings.model_construct(
        kind="vault", address="https://vault.example", path_prefix=""
    )
    text = _refusal(lambda: make("secrets", skipped))
    assert text is not None, "the start-up built the kind with an empty prefix"
    assert EMPTY_PREFIX_WORDS in text, "the refusal at start-up is not the plain sentence"


def test_a_vault_read_with_an_empty_prefix_is_refused_before_any_request_and_a_bad_name_is_refused_first():
    from hadavin_sdk.actions.secrets_vault import VaultProvider

    sent = []
    provider = VaultProvider("http://127.0.0.1:9", lambda p: sent.append("login") or "t")
    text = _refusal(lambda: provider._fetch("pg_dsn"))
    assert text is not None, "a read with an empty prefix was tried"
    assert EMPTY_PREFIX_WORDS in text, "the refusal of the read is not the plain sentence"
    assert sent == [], "a sign-in was sent before the empty prefix was refused"
    bad = _refusal(lambda: provider._fetch("a/b"))
    assert bad is not None and "Vault names here are" in bad, "a bad name was not refused first"


@pytest.mark.parametrize(
    "name",
    ["a%b", "a?b", "a#b", "a+b", "a*b", "a b", "a\nb", "a%2Fb", "a%2fb", "%", "+", "*", "?"],
)
def test_a_secret_name_with_a_character_that_could_leave_the_one_path_part_is_refused(name):
    """The grant's `+` is one whole path part only while `_NAME` admits none of `%` (an encoded slash), `?`,
    `#`, `+`, `*`, a space or a newline: each of these must be refused before any request."""
    from hadavin_sdk.actions.secrets_vault import VaultProvider
    from hadavin_sdk.errors import ConfigError

    sent = []
    provider = VaultProvider("http://127.0.0.1:9", lambda p: sent.append("login") or "t")
    with pytest.raises(ConfigError, match="Vault names here are"):
        provider._fetch(name)
    assert sent == []


@pytest.mark.parametrize(
    ("resource", "message"),
    [
        ("{mount}/data/x+", "`+` must be one whole path segment"),
        ("{mount}/data/+x/y", "`+` must be one whole path segment"),
        ("{mount}/{key_name}+", "`+` must be one whole path segment"),
        ("{mount}/da*ta/x", "`*` is a Vault wildcard only as the last character"),
        ("{mount}/data/+*", "Vault refuses `+*`"),
    ],
)
def test_plant_a_vault_wildcard_in_a_form_the_server_does_not_read_is_caught(resource, message):
    problems = _grant_changed("secrets/vault", resource=resource)
    assert any(message in p for p in problems), problems


def test_plant_d1_a_plus_wildcard_with_no_bound_is_caught():
    same(
        _grant_changed("signer/vault_transit", resource="{transit_mount}/sign/+"),
        [
            "grant R18: resource '{transit_mount}/sign/+' holds a wildcard, so `bound` must say what limits it"
        ],
        what="the check reports: holds a wildcard",
    )
    # for Kubernetes `+` is no wildcard and a plain resource needs no bound
    assert _grant_changed("source/kubernetes", bound="") == []


def test_a_filled_vault_path_with_a_misplaced_wildcard_is_refused():
    policy = _policies()["secrets/vault"]
    import dataclasses

    grant = dataclasses.replace(policy.grants[0], resource="{mount}/data/{path_prefix}x+")
    with pytest.raises(
        ValueError, match="holds a wildcard in a place where Vault does not read one"
    ):
        pp.render_vault(dataclasses.replace(policy, grants=(grant,)), VAULT_VALUES)


# ------------------------------------------------------- data rules added in fix batch 1 (m6, m7, m9, m15)


def test_plant_m6_a_key_written_twice_in_the_policy_literal_is_refused():
    text = _text(VAULT).replace(
        '            "resource": "{mount}/data/{path_prefix}+",\n',
        '            "resource": "{mount}/data/{path_prefix}+",\n            "resource": "{mount}/data/*",\n',
    )
    assert _refused_with(
        lambda: pp.parse(text, "planted.py"),
        pp.PolicyError,
        "key 'resource' is written twice in one dict of POLICY",
    ), "a key written twice in the policy literal is accepted"


@pytest.mark.parametrize("key", ["id", "name", "resource", "reason", "bound", "applies_when"])
@pytest.mark.parametrize("bad", ["\n", "\r", "\t", "\x00", "\x1b", "\x7f", "\u2028", "\x85"])
def test_plant_m7_a_control_character_in_a_text_of_a_grant_is_refused(key, bad):
    value = "x" + bad + 'path "sys/*" {'
    same(
        _grant_changed("secrets/vault", **{key: value}),
        [
            (
                f"POLICY.grants[0].{key}: holds a control or other non-printing character (a newline, a tab); "
                "it would be copied into the rendered policy text"
            )
        ],
    )


def test_plant_m7_a_control_character_anywhere_else_in_the_literal_is_refused():
    raw = _raw("secrets/vault")
    raw["never"] = ({**raw["never"][0], "name": "sys/*\n"}, *raw["never"][1:])
    raw["notes"] = ("a\nb",)
    raw["credential"] = {**raw["credential"], "how": "x\ty"}
    problems = pp.problems(raw)
    assert len(problems) == 3 and all("non-printing character" in p for p in problems), problems


@pytest.mark.parametrize(
    "resource", ["{mount}/data/{prefix2}x", "{mount}/data/<name>", "{mount}/}"]
)
def test_plant_m9_a_brace_that_is_no_placeholder_is_refused_in_the_literal(resource):
    problems = _grant_changed("signer/vault_transit", resource=resource)
    assert len(problems) == 1 and "would stay in the rendered text unfilled" in problems[0], (
        problems
    )


def test_plant_m9_a_placeholder_left_after_filling_is_refused():
    import dataclasses

    policy = _policies()["signer/vault_transit"]
    grant = dataclasses.replace(policy.grants[0], resource="{transit_mount}/sign/{key_name}{Odd9}")
    assert _refused_with(
        lambda: pp.render_vault(
            dataclasses.replace(policy, grants=(grant, policy.grants[1])), TRANSIT_VALUES
        ),
        ValueError,
        "a placeholder is left unfilled",
    ), "a placeholder left after filling is accepted into the text"
    same(
        _grant_changed("signer/vault_transit", resource="{transit_mount}/sign/{nosuch}"),
        ["grant R18: placeholder 'nosuch' in the resource has no grammar, so it is refused"],
    )


def test_plant_m15_small_validation_gaps_are_closed():
    problems = _grant_changed("secrets/vault", verified=("9999-99-99", "V-KV"))
    same(problems, ["grant R17: verified must start with a real date such as 2026-11-11"])
    raw = _raw("secrets/vault")
    never = next(n for n in raw["never"] if n.get("capabilities"))
    raw["never"] = ({**never, "capabilities": ("create", "wipe")},)
    same(pp.problems(raw), ["never entry 0: 'wipe' is not a Vault capability"])
    policies = _policies()
    with pytest.raises(ValueError, match="'namespaces' names the same namespace twice"):
        pp.render_kubernetes(
            policies["source/kubernetes"], {**K8S_VALUES, "namespaces": "shop,shop"}
        )
    with pytest.raises(ValueError, match="'path_prefix' does not match its grammar"):
        pp.render_vault(policies["secrets/vault"], {**VAULT_VALUES, "path_prefix": 7})
    raw = _raw("signer/vault_transit")
    raw["grants"] = (
        raw["grants"][0],
        {**raw["grants"][1], "operations": raw["grants"][0]["operations"]},
    )
    assert any("is claimed twice" in p for p in pp.problems(raw))


# -------------------------------- evidence item (b): a well-formed value that names a reserved thing


@pytest.mark.parametrize(
    ("kind", "key", "value", "message"),
    [
        ("secrets/vault", "mount", "sys", "starts with Vault's own path 'sys'"),
        ("secrets/vault", "mount", "auth", "starts with Vault's own path 'auth'"),
        ("secrets/vault", "mount", "identity", "starts with Vault's own path 'identity'"),
        ("secrets/vault", "mount", "cubbyhole", "starts with Vault's own path 'cubbyhole'"),
        ("secrets/vault", "mount", "sys/kv", "starts with Vault's own path 'sys'"),
        ("signer/vault_transit", "transit_mount", "sys", "starts with Vault's own path 'sys'"),
        ("signer/vault_transit", "transit_mount", "auth/t", "starts with Vault's own path 'auth'"),
        ("source/kubernetes", "namespaces", "kube-system", "one of the cluster's own namespaces"),
        (
            "source/kubernetes",
            "namespaces",
            "shop,kube-public",
            "one of the cluster's own namespaces",
        ),
        (
            "source/kubernetes",
            "namespaces",
            "kube-node-lease",
            "one of the cluster's own namespaces",
        ),
        (
            "source/kubernetes",
            "SERVICE_ACCOUNT_NAMESPACE",
            "kube-system",
            "the cluster's own namespaces",
        ),
        ("source/kubernetes", "ROLE_NAME", "cluster-admin", "a built-in role name"),
        ("source/kubernetes", "ROLE_NAME", "admin", "a built-in role name"),
        ("source/kubernetes", "ROLE_NAME", "edit", "a built-in role name"),
        ("source/kubernetes", "ROLE_NAME", "view", "a built-in role name"),
        ("source/kubernetes", "ROLE_NAME", "system-node", "a built-in role name"),
        ("source/kubernetes", "ROLE_NAME", "system.basic-user", "a built-in role name"),
        ("source/kubernetes", "SERVICE_ACCOUNT", "default", "every pod gets by default"),
    ],
)
def test_a_well_formed_value_that_names_a_reserved_thing_is_refused(kind, key, value, message):
    policy = _policies()[kind]
    base = {"secrets/vault": VAULT_VALUES, "signer/vault_transit": TRANSIT_VALUES}.get(
        kind, K8S_VALUES
    )
    render = pp.RENDERERS[policy.platform][1]
    with pytest.raises(ValueError, match=f"'{key}' is refused") as caught:
        render(policy, {**base, key: value})
    assert message in str(caught.value)


def test_a_nested_mount_is_accepted_and_a_role_name_with_a_colon_never_passes_the_grammar():
    policies = _policies()
    text = pp.render_vault(policies["secrets/vault"], {**VAULT_VALUES, "mount": "team/kv"})
    assert 'path "team/kv/data/hadavin/acme/+"' in text
    with pytest.raises(ValueError, match="'ROLE_NAME' does not match its grammar"):
        pp.render_kubernetes(
            policies["source/kubernetes"], {**K8S_VALUES, "ROLE_NAME": "system:node"}
        )


@pytest.mark.parametrize(
    ("kind", "key"),
    [
        ("secrets/vault", "mount"),
        ("secrets/vault", "path_prefix"),
        ("signer/vault_transit", "transit_mount"),
        ("signer/vault_transit", "key_name"),
        ("source/kubernetes", "namespaces"),
        ("source/kubernetes", "ROLE_NAME"),
        ("source/kubernetes", "SERVICE_ACCOUNT"),
        ("source/kubernetes", "SERVICE_ACCOUNT_NAMESPACE"),
    ],
)
def test_a_value_longer_than_its_limit_is_refused_and_one_at_the_limit_is_not(kind, key):
    policy = _policies()[kind]
    base = {"secrets/vault": VAULT_VALUES, "signer/vault_transit": TRANSIT_VALUES}.get(
        kind, K8S_VALUES
    )
    render = pp.RENDERERS[policy.platform][1]
    limit = pp.MAX_LENGTH[key]
    tail = "/" if key == "path_prefix" else ""
    assert render(policy, {**base, key: "a" * (limit - len(tail)) + tail})
    with pytest.raises(ValueError, match=f"'{key}' is longer than {limit} characters"):
        render(policy, {**base, key: "a" * (limit + 1 - len(tail)) + tail})
    assert set(pp.MAX_LENGTH) == set(pp.GRAMMAR)


# ---------------------------------------------- m10: the command line runs the data checks, one line each


def _tree(tmp_path: Path) -> Path:
    for rel in (*pp.KIND_MODULES.values(), pp.SOURCES):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(_text(rel), encoding="utf-8")
    return tmp_path


def _check(monkeypatch, capsys, root: Path) -> tuple[int, list[str]]:
    monkeypatch.setattr(pp, "DATA_ROOT", root)
    code = pp.main(["--check"], today=DECIDED)
    return code, capsys.readouterr().err.splitlines()


def test_the_data_of_this_repository_breaks_no_rule_the_command_line_checks():
    assert pp.data_problems(ROOT, today=DECIDED) == []


def test_plant_m10_check_reports_each_data_problem_in_one_line_with_exit_code_1(
    tmp_path, monkeypatch, capsys
):
    root = _tree(tmp_path)
    assert pp.data_problems(root, today=DECIDED) == []
    transit = root / TRANSIT
    transit.write_text(_text(TRANSIT).replace('"id": "R18"', '"id": "R17"'), encoding="utf-8")
    code, lines = _check(monkeypatch, capsys, root)
    same(
        (code, lines),
        (
            1,
            [
                "policy page: grant id R17 is used by secrets/vault and by signer/vault_transit",
                # the renamed grant has a claim and no dated entry, and the entry of the old id is stale
                "policy page: signer/vault_transit R17: has an unchecked claim (claims_unverified) and no PENDING_CLAIMS entry",
                "policy page: PENDING_CLAIMS ('signer/vault_transit', 'R18') is fixed or gone: delete the entry",
            ],
        ),
        what="the check reports: is used by secrets/vault and by",
    )
    transit.write_text("def broken(:\n", encoding="utf-8")
    same(
        _check(monkeypatch, capsys, root),
        (1, ["policy page: signer_vault.py: is not valid Python (line 1)"]),
    )
    transit.write_text("POLICY = None\n", encoding="utf-8")
    same(
        _check(monkeypatch, capsys, root),
        (1, ["policy page: signer_vault.py: POLICY must be a dict (found NoneType)"]),
    )
    transit.unlink()
    same(
        _check(monkeypatch, capsys, root),
        (1, ["policy page: signer_vault.py: cannot be read (FileNotFoundError)"]),
    )
    transit.write_text(_text(TRANSIT), encoding="utf-8")
    stray = root / "src/hadavin_sdk/actions/secrets_new.py"
    stray.write_text('POLICY = {"platform": "vault"}\n', encoding="utf-8")
    same(
        _check(monkeypatch, capsys, root),
        (
            1,
            [
                (
                    "policy page: src/hadavin_sdk/actions/secrets_new.py: holds a POLICY but is not in "
                    "KIND_MODULES, so no check reads it"
                )
            ],
        ),
    )
    stray.unlink()
    (root / VAULT).write_text(_text(VAULT).replace('"V-PARSE"', '"V-NOPE"'), encoding="utf-8")
    code, lines = _check(monkeypatch, capsys, root)
    same(
        (code, lines),
        (1, ["policy page: secrets/vault grant R17: source id V-NOPE is not in the sources file"]),
    )


def test_m10_write_makes_a_missing_docs_folder_and_check_then_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(pp, "ROOT", tmp_path)
    assert not (tmp_path / "docs").exists()
    assert pp.main(["--write"], today=DECIDED) == 0 and pp.main(["--check"], today=DECIDED) == 0


# ------------------------------------------------------------------------- m12: sources are pinned and used


def test_plant_a_source_row_that_names_a_branch_is_refused(tmp_path):
    (tmp_path / pp.SOURCES).parent.mkdir(parents=True)
    row = (
        "K-X | https://raw.githubusercontent.com/kubernetes/website/main/a.md | {} | "
        + "0" * 64
        + " | n\n"
    )
    for commit in ("main", "branch main at 18f8e9f", "18f8e9f"):
        (tmp_path / pp.SOURCES).write_text(row.format(commit), encoding="utf-8")
        with pytest.raises(pp.PolicyError, match="K-X is not pinned"):
            pp.source_ids(tmp_path)


def test_every_source_row_is_pinned_and_is_used():
    rows = source_ids()
    listed = [
        line.split(" | ")[0].strip()
        for line in (ROOT / pp.SOURCES).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    same(sorted(rows), sorted(listed))
    assert len(listed) == len(set(listed))
    header = re.search(r"(\d+) rows\.", (ROOT / pp.SOURCES).read_text(encoding="utf-8"))
    assert header and int(header.group(1)) == len(listed), (
        "the fixture header names a different row count"
    )
    for key, (url, commit, _digest, _note) in rows.items():
        assert f"/blob/{commit}/" in url, key
    used = {
        s
        for p in _policies().values()
        for _w, v in (
            [(g.id, g.verified) for g in p.grants]
            + [("free", f.verified) for f in p.free]
            + [(n.name, n.verified) for n in p.never]
        )
        for s in (v or ())[1:]
    }
    engine_text = (ROOT / "tests/test_policy_engine.py").read_text(encoding="utf-8")
    unused = sorted(k for k in rows if k not in used and f"source id {k} " not in engine_text)
    same(unused, [])


def test_the_page_and_the_fixture_agree_on_which_rows_are_abbreviated_and_what_is_unpinned():
    rows = source_ids()
    short = sorted(k for k, (_u, commit, _d, _n) in rows.items() if len(commit) < 40)
    same(short, sorted(["V-API", "V-APPROLE", "V-K8S", "V-KV", "V-POL", "V-TOK", "V-TR"]))
    head = " ".join(pp.head().split())
    assert (
        "Seven of the rows (the Vault documentation) carry a 7-character abbreviated commit id"
        in head
    )
    assert len(short) == 7 and all(k.startswith("V-") and rows[k][1] == "82e7167" for k in short)
    assert "OpenBao claims are not tied to one release" in head


# -------------------------------------------------------------------- m5, m16: dated entries, what to do


def test_plant_an_overdue_entry_says_what_to_do_and_a_date_cannot_be_moved_far():
    # the list as it is; with every kind declared (the end state) a made-up entry stands in, so that the wording
    # of the overdue line is still shown
    base = PENDING_KINDS or {
        "channel/slack": Pending("r", "t", DECIDED, DECIDED + timedelta(days=30))
    }
    problems = kind_problems(
        all_kinds(),
        set(pp.KIND_MODULES) - set(base),
        base,
        NO_IDENTITY,
        pp.review_day(base) + timedelta(days=1),
    )
    assert problems, "no overdue entry is reported"
    assert all("What to do: finish that work and delete the entry; or" in p for p in problems)
    assert all("decide again" in p and "at most 92 days" in p for p in problems)
    moved = {
        **base,
        "channel/slack": Pending("r", "t", DECIDED, DECIDED + timedelta(days=93)),
    }
    same(
        kind_problems(
            all_kinds(), set(pp.KIND_MODULES) - set(moved), moved, NO_IDENTITY, LATEST_DAY
        ),
        [
            (
                f"PENDING_KINDS channel/slack: review_by {DECIDED + timedelta(days=93)} is more than 92 days after "
                f"the decision of {DECIDED}: a date may not be moved further than that"
            )
        ],
        what="the check reports: a date may not be moved further",
    )
    ahead = {
        **base,
        "channel/slack": Pending(
            "r", "t", DECIDED + timedelta(days=200), DECIDED + timedelta(days=230)
        ),
    }
    same(
        kind_problems(
            all_kinds(), set(pp.KIND_MODULES) - set(ahead), ahead, NO_IDENTITY, LATEST_DAY
        ),
        [f"PENDING_KINDS channel/slack: decided {DECIDED + timedelta(days=200)} is in the future"],
    )


def test_plant_m16_an_unverified_never_list_name_needs_a_dated_entry():
    same(
        name_problems(_policies(), {}, set(source_ids()), DECIDED),
        [
            f"{kind} never:{name}: the name is not found in a vendor source (verified is None) "
            "and has no PENDING_NAMES entry"
            for kind, name in (
                ("secrets/vault", "{mount}/subkeys/*"),
                ("secrets/vault", "{mount}/undelete/*"),
                ("signer/vault_transit", "{transit_mount}/byok-export/*"),
                ("source/kubernetes", "admin"),
                ("source/kubernetes", "cluster-admin"),
                ("source/kubernetes", "edit"),
            )
        ],
    )
    assert sorted(_unverified(_policies())) == sorted(PENDING_NAMES)


# ------------------------------------------------ a never-list line must not cover a grant (fix batch 3)


def _with_never(kind: str, **entry) -> dict[str, pp.Policy]:
    policies = _policies()
    raw = _raw(kind)
    raw["never"] = (
        *raw["never"],
        {"type": "path", "reason": "planted", "verified": None, **entry},
    )
    policies[kind] = pp.parse(f"POLICY = {raw!r}")
    return policies


def _covers_problems(policies: dict[str, pp.Policy]) -> list[str]:
    return [p for p in pp.cross_problems(policies) if "covers the resource and capability" in p]


def test_no_never_list_line_of_the_three_kinds_covers_a_grant():
    for kind, policy in _policies().items():
        assert pp.never_covers_grant_problems(kind, policy) == [], kind


def test_plant_a_vault_never_path_over_a_grant_is_caught_and_a_capability_that_differs_is_not():
    vault, transit = "secrets/vault", "signer/vault_transit"
    clean = [
        (vault, {"name": "{mount}/data/*", "capabilities": ("create", "update")}),
        (vault, {"name": "{mount}/metadata/*"}),
        (vault, {"name": "other/data/*"}),
        (transit, {"name": "{transit_mount}/keys/{key_name}", "capabilities": ("delete",)}),
        (transit, {"name": "{transit_mount}/sign/{key_name}/sha2-256"}),
    ]
    for kind, entry in clean:
        found = _covers_problems(_with_never(kind, **entry))
        assert found == [], f"a never path {entry} that covers no grant is reported: {found}"
    caught = [
        (vault, {"name": "{mount}/data/*", "capabilities": ("read",)}, "R17"),
        (vault, {"name": "{mount}/data/*"}, "R17"),  # no capabilities: all of them
        (vault, {"name": "{mount}/data/{path_prefix}+", "capabilities": ("read", "list")}, "R17"),
        (
            vault,
            {"name": "{mount}/data/{path_prefix}secret1"},
            "R17",
        ),  # narrower: the grant covers it
        (transit, {"name": "{transit_mount}/sign/{key_name}"}, "R18"),
        (transit, {"name": "{transit_mount}/sign/*", "capabilities": ("update",)}, "R18"),
        (transit, {"name": "{transit_mount}/keys/{key_name}", "capabilities": ("read",)}, "R19"),
    ]
    for kind, entry, grant in caught:
        found = _covers_problems(_with_never(kind, **entry))
        assert any(
            f"never-list path {entry['name']!r}" in f and f"grant {grant} " in f for f in found
        ), f"a never path {entry} that covers grant {grant} is not reported: {found}"
        assert len(found) == 1, f"a never path {entry} is reported more than once: {found}"


def test_a_never_path_over_a_grant_is_also_refused_by_the_check_command(tmp_path, monkeypatch):
    policies = _with_never("secrets/vault", name="{mount}/data/*")
    assert any(
        "covers the resource and capability of grant R17" in p for p in pp.cross_problems(policies)
    )
    raw = _raw("secrets/vault")
    raw["never"] = (
        *raw["never"],
        {"type": "path", "name": "{mount}/data/*", "reason": "x", "verified": None},
    )
    for kind, rel in pp.KIND_MODULES.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        body = raw if kind == "secrets/vault" else _raw(kind)
        (tmp_path / rel).write_text(f"POLICY = {body!r}\n", encoding="utf-8")
    (tmp_path / pp.SOURCES).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / pp.SOURCES).write_text(
        (ROOT / pp.SOURCES).read_text(encoding="utf-8"), encoding="utf-8"
    )
    assert any(
        "covers the resource and capability" in p for p in pp.data_problems(tmp_path, today=DECIDED)
    )


def test_plant_a_kubernetes_never_resource_that_a_grant_names_is_caught():
    kube = "source/kubernetes"
    for name, grant in (("pods/log", "R22"), ("events", "R21"), ("deployments", "R20")):
        found = _covers_problems(_with_never(kube, type="resource", name=name))
        assert len(found) == 1 and f"grant {grant} " in found[0], (
            f"a never resource {name!r} that a grant names is not reported: {found}"
        )
    found = _covers_problems(_with_never(kube, type="resource", name="pods/exec"))
    assert found == [], f"a never resource that no grant names is reported: {found}"


def test_plant_the_check_across_kinds_calls_the_cover_rule():
    problems = pp.cross_problems(_with_never("secrets/vault", name="{mount}/data/*"))
    assert problems, "cross_problems does not call the never-list cover rule"


# --------------------------------- every behaviour claim in a note has a source or an unchecked-claim entry
# The classes are in the tool (`pp.NOTE_CLASSES`), because the page prints the source ids of a `sources` note. A
# note with no class fails. The class is a label a person chooses: this test cannot know that a `sources` note
# is true, only that its ids exist and, on the page, are printed after the note and in the source list.
NOTE_CLASSES = pp.NOTE_CLASSES


# The rule itself is in the tool, so that the check command (`pp.data_problems`) runs it too.
note_problems = pp.note_problems


def test_every_note_of_a_kind_is_classed_and_every_claim_has_a_source_or_an_unchecked_entry():
    same(note_problems(_policies(), NOTE_CLASSES, set(source_ids())), [])


def _with_note(kind: str, note: str) -> dict[str, pp.Policy]:
    policies = _policies()
    raw = _raw(kind)
    raw["notes"] = (*raw["notes"], note)
    policies[kind] = pp.parse(f"POLICY = {raw!r}")
    return policies


def test_plant_a_new_note_with_no_class_a_claim_that_is_not_listed_and_an_unknown_source_are_caught():
    known = set(source_ids())
    found = note_problems(
        _with_note("source/kubernetes", "The server never retries."), NOTE_CLASSES, known
    )
    assert any("has 0 classes" in p for p in found), "a note with no class is not reported"
    claimless = {
        **NOTE_CLASSES,
        ("source/kubernetes", "The server never"): ("claim", "no such claim text"),
    }
    found = note_problems(
        _with_note("source/kubernetes", "The server never retries."), claimless, known
    )
    assert any("is a claim, but no claims_unverified holds" in p for p in found), (
        "a claim note whose text is in no claims_unverified is not reported"
    )
    badsrc = {**NOTE_CLASSES, ("source/kubernetes", "The server never"): ("sources", ("K-NOPE",))}
    found = note_problems(
        _with_note("source/kubernetes", "The server never retries."), badsrc, known
    )
    assert any("K-NOPE, which is not in the sources file" in p for p in found), (
        "a note that names an unknown source id is not reported"
    )
    stale = {**NOTE_CLASSES, ("secrets/vault", "No such note"): ("code",)}
    assert any("matches no note" in p for p in note_problems(_policies(), stale, known)), (
        "a stale class entry is not reported"
    )


# ----------------------------------------------------- fix batch 4: the review of round 4, items 1 to 5 and 7


def _free_entry_changed(kind: str, **changes) -> list[str]:
    raw = _raw(kind)
    raw["free"] = ({**raw["free"][0], **changes}, *raw["free"][1:])
    return pp.problems(raw)


def test_a_free_or_never_reason_that_says_it_is_unchecked_must_list_the_claim():
    # Class: a statement shown as checked next to the same page denying it (Issue 1). Free and never entries
    # now carry `claims_unverified` as grants do; the wording rule is in `pp.problems`.
    kube = "source/kubernetes"
    said = "that it writes nothing was not found in a vendor source"
    found = _free_entry_changed(kube, reason=said, claims_unverified=())
    assert any("must be listed in claims_unverified" in p for p in found), (
        f"a free reason that says it is unchecked, with no claim listed, is not refused: {found}"
    )
    assert _free_entry_changed(kube, reason=said, claims_unverified=("it writes nothing",)) == [], (
        "a free reason that says it is unchecked is refused although the claim is listed"
    )
    raw = _raw(kube)
    raw["never"] = (
        *raw["never"],
        {"type": "role", "name": "x", "reason": "nobody has checked this", "verified": None},
    )
    found = pp.problems(raw)
    assert any("must be listed in claims_unverified" in p for p in found), (
        f"a never reason that says it is unchecked, with no claim listed, is not refused: {found}"
    )


def test_the_self_review_create_is_an_unchecked_claim_on_the_page_not_a_checked_fact():
    policy = _policies()["source/kubernetes"]
    free = next(f for f in policy.free if f.operations == (("k8s.rules_review",),))
    assert "creates nothing" not in free.reason and free.claims_unverified, free
    never = next(n for n in policy.never if n.name == "create")
    assert never.claims_unverified, never
    text = pp.page(ROOT)
    assert "Claims not checked: a `create` on `selfsubjectrulesreviews` changes nothing" in text, (
        "the free request does not show its unchecked claim on the page"
    )
    assert "creates nothing" not in text


def test_the_pending_claims_of_a_free_and_a_never_entry_are_watched_like_a_grant_claim():
    found = claim_problems(_policies(), {}, DECIDED)
    missing = {
        entry
        for entry in ("free:0", "never:create")
        if not any(f"source/kubernetes {entry}: has an unchecked claim" in p for p in found)
    }
    assert "free:0" not in missing, (
        f"an unchecked claim of a free request: the entry free:0 needs no PENDING_CLAIMS entry: {found}"
    )
    assert "never:create" not in missing, (
        f"an unchecked claim of a never line: the entry never:create needs no PENDING_CLAIMS entry: {found}"
    )


def _never_over(kind: str, name: str, capabilities: tuple[str, ...] = ()) -> list[str]:
    return _covers_problems(_with_never(kind, name=name, capabilities=capabilities))


def test_a_never_path_of_two_or_more_parts_over_the_one_prefix_grant_is_caught():
    # Class: the cover check treated `{path_prefix}` as one word with no slash (Issue 2). R17 is
    # `{mount}/data/{path_prefix}+`; the prefix has one or more parts, each ending in `/`.
    vault = "secrets/vault"
    for name in (
        "{mount}/data/+/+",  # a one-part prefix
        "{mount}/data/+/+/+",  # a two-part prefix
        "{mount}/data/+/+/+/+/+",  # a four-part prefix
        "{mount}/data/team/+",  # a literal first part: the prefix may be `team/`
        "{mount}/+/{path_prefix}foo",  # a wildcard on both sides, in different places
        "{mount}/data/*",
    ):
        found = _never_over(vault, name, ("read",))
        assert len(found) == 1 and "grant R17 " in found[0], (
            f"a never path {name!r} that the grant R17 covers is not reported once: {found}"
        )
    for name in (
        "{mount}/data/{path_prefix}",  # no secret name: the grant needs one more part
        "{mount}/data/+",  # one part: the prefix has at least one part, so R17 reaches two or more
        "{mount}/metadata/+/+",
        "other/data/+/+",
    ):
        found = _never_over(vault, name, ("read",))
        assert found == [], (
            f"a never path {name!r} that the grant R17 does not cover is reported: {found}"
        )


def _matches(path: str, candidates: list[str]) -> frozenset[str]:
    """The candidate paths one pattern allows (`+` is one or more characters that are not `/`, a last `*` is any
    ending): the reference answer the automaton is compared with."""
    body = re.escape(path.removesuffix("*")).replace(r"\+", "[^/]+")
    regex = re.compile(body + (".*" if path.endswith("*") else ""))
    return frozenset(c for c in candidates if regex.fullmatch(c))


def test_the_path_overlap_automaton_agrees_with_a_brute_force_search_on_every_small_pattern_pair():
    import itertools

    # Every path over {a, b, /} of up to 7 characters. A pattern is up to 3 parts of `a`, `b` or `+` (at least one
    # character each), with or without a last `*`. Two patterns that overlap share a path of at most 5
    # characters, so the search is complete, and every pair of the generated patterns is compared (no random choice).
    candidates = ["".join(c) for n in range(8) for c in itertools.product("ab/", repeat=n)]
    patterns = [
        "/".join(parts) + star
        for n in (1, 2, 3)
        for parts in itertools.product(("a", "b", "+"), repeat=n)
        for star in ("", "*")
        if not (star and parts[-1] == "+")  # Vault refuses `+*`
    ]
    assert len(patterns) == sum(2 * 3**n - 3 ** (n - 1) for n in (1, 2, 3)), len(patterns)
    allowed = {p: _matches(p, candidates) for p in patterns}
    seen = set()
    for first, second in itertools.product(patterns, repeat=2):
        answer = bool(allowed[first] & allowed[second])
        seen.add(answer)
        assert pp.vault_paths_overlap(first, second) == answer, (
            f"overlap of {first!r} and {second!r} differs from the brute-force answer {answer}"
        )
    assert seen == {True, False}, "the patterns did not hold both an overlap and none"


def test_the_path_prefix_setting_is_read_as_one_or_more_parts_each_ending_in_a_slash():
    assert pp.vault_paths_overlap("m/+", "m/abc") is True, (
        "a `+` is read as one character, so m/+ and m/abc are not reported as overlapping"
    )
    same(pp.vault_paths_overlap("m/{path_prefix}x", "m/a/x"), True)
    same(pp.vault_paths_overlap("m/{path_prefix}x", "m/a/b/c/x"), True)
    same(pp.vault_paths_overlap("m/{path_prefix}x", "m/x"), False)
    same(pp.vault_paths_overlap("m/{path_prefix}x", "m/a/y"), False)
    same(pp.vault_paths_overlap("m/{path_prefix}+", "m/+/+/+"), True)
    same(
        pp.vault_paths_overlap("m/+", "m/abc"), True
    )  # a `+` is one part of any length, not one character
    same(pp.vault_paths_overlap("m/{path_prefix}x", "m/abc/de/x"), True)


def test_a_never_type_that_does_not_fit_the_platform_is_refused():
    # Class: a never line no cover rule reads is still printed (Issue 3).
    vault, kube = _raw("secrets/vault"), _raw("source/kubernetes")
    for raw, bad in (
        (vault, {"type": "resource", "name": "{mount}/data/*"}),
        (vault, {"type": "action", "name": "delete"}),
        (vault, {"type": "prose", "name": "{mount}/data/*"}),
        (kube, {"type": "path", "name": "secrets"}),
        (kube, {"type": "prose", "name": "secrets"}),
    ):
        planted = {**raw, "never": (*raw["never"], {"reason": "planted", "verified": None, **bad})}
        found = pp.problems(planted)
        assert any("does not fit platform" in p for p in found), (
            f"a never line {bad} on platform {raw['platform']} is not refused: {found}"
        )
    for raw, ok in (
        (vault, {"type": "path", "name": "{mount}/zzz/*"}),
        (vault, {"type": "role", "name": "root"}),
        (kube, {"type": "resource", "name": "pods/zzz"}),
        (kube, {"type": "action", "name": "zzz"}),
    ):
        planted = {**raw, "never": (*raw["never"], {"reason": "planted", "verified": None, **ok})}
        assert pp.problems(planted) == [], f"a fitting never line {ok} is refused"


def test_every_note_with_a_sources_class_shows_its_source_ids_after_the_note_and_in_the_source_list():
    text = pp.page(ROOT)
    marks = pp.read_marks(ROOT)
    listed = text.split("## Sources named on this page", 1)[1]
    for (kind, start), cls in pp.NOTE_CLASSES.items():
        if cls[0] != "sources" or start.startswith("reason:"):
            continue  # a reason names the source ids of its own entry, printed in the checked cell
        note = next(
            n
            for n in (*_policies()[kind].notes, *(f"free:{f.note}" for f in _policies()[kind].free))
            if n.startswith(start)
        )
        shown = note.removeprefix("free:")
        suffix = ", ".join(
            s + (" (builder only)" if s in marks.builder_only else "") for s in cls[1]
        )
        assert f"{shown} (sources: {suffix})" in text, (
            f"the note {shown[:40]!r} does not show its source ids"
        )
        for sid in cls[1]:
            mark = " (builder only)" if sid in marks.builder_only else ""
            assert f"\n- {sid}{mark}: " in listed, (
                f"{sid} (named by a note) is not in the source list"
            )
    assert "\n- V-TOK: " in listed, "V-TOK, named by two notes, is printed nowhere"


def test_a_sources_note_whose_free_entry_does_not_list_the_id_is_caught():
    classes = {
        **NOTE_CLASSES,
        ("source/kubernetes", "free:a default cluster gives every"): (
            "sources",
            ("K-RBAC", "K-SRC", "K-SSRR", "K-KUBELET"),
        ),
    }
    found = note_problems(_policies(), classes, set(source_ids()))
    assert any("not in `verified` of the same entry" in p and "K-KUBELET" in p for p in found), (
        f"a free-entry note that names a source its entry does not list is not reported: {found}"
    )


def test_the_builder_only_marks_are_read_from_the_head_of_the_sources_file_and_match_its_list():
    text = _text(pp.SOURCES)
    marks = pp.read_marks(ROOT)
    assert marks.builder_only == ("V-ACL", "V-PARSE", "B-ACL"), (
        f"the builder-only ids read from the head are not 'V-ACL', 'V-PARSE', 'B-ACL': {marks.builder_only}"
    )
    listed = text.split("# WHAT A LATER EVIDENCE RUNNER MUST RE-READ", 1)[1].split(
        "# After that run", 1
    )[0]
    named = set(re.findall(r"\b[VBK]-[A-Z]+\b", listed))
    marked = set(marks.builder_only) | set(marks.partly_builder_only)
    assert marked == named | set(marks.builder_only), (
        f"the marked ids {sorted(marked)} differ from the ids the head says a later runner must re-read "
        f"{sorted(named)}"
    )
    assert not set(marks.builder_only) & set(marks.partly_builder_only)


def test_the_builder_marks_refuse_a_missing_line_an_unknown_id_and_a_second_line(tmp_path):
    base = _text(pp.SOURCES)
    cases = {
        "a missing line": base.replace("# BUILDER-ONLY:", "# X:"),
        "an unknown id": base.replace("# BUILDER-ONLY: V-ACL", "# BUILDER-ONLY: V-NOPE, V-ACL"),
        "a second line": base + "\n# BUILDER-ONLY: V-ACL\n",
    }
    accepted = set()
    for name, body in cases.items():
        (tmp_path / pp.SOURCES).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / pp.SOURCES).write_text(body, encoding="utf-8")
        if not _refused_with(lambda: pp.read_marks(tmp_path), pp.PolicyError, ""):
            accepted.add(name)
    assert "a missing line" not in accepted, "a sources file with no builder-only line is accepted"
    assert "an unknown id" not in accepted, (
        "a builder-only id that is no row of the sources file is accepted"
    )
    assert "a second line" not in accepted, (
        "a second builder-only line in the sources file is accepted"
    )


_PASSAGE_MARK = "(the passage behind the claim: see claims)"


def test_a_source_of_which_only_a_passage_was_read_is_marked_on_a_row_with_a_claim_only():
    claimed = pp._checked_cell(("2026-11-11", "V-POL", "V-KV"), True)
    assert claimed == f"2026-11-11, sources V-POL {_PASSAGE_MARK}, V-KV {_PASSAGE_MARK}", (
        f"a row with a claim does not mark a partly read source: {claimed}"
    )
    plain = pp._checked_cell(("2026-11-11", "V-POL", "V-KV"), False)
    assert plain == "2026-11-11, sources V-POL, V-KV", (
        f"a row with no claim marks a source as partly builder only: {plain}"
    )
    text = pp.page(ROOT)
    row = next(ln for ln in text.splitlines() if ln.startswith("| R17 "))
    assert f"V-POL {_PASSAGE_MARK}" in row and f"B-KV {_PASSAGE_MARK}" in row, row


# A hand list, not a derived one: a person decides which grants allow more than their reason says. Two tests pin
# it to the data and to the page: every id named here has the sentence in its `bound` and in its page row, and no
# other grant has it, so a grant added to or dropped from the list alone fails.
BROADER_THAN_REASON = {"R17", "R20", "R21", "R22"}
BROADER_START = "Allows more than the reason says"


def test_the_grants_broader_than_their_reason_say_so_in_the_cell_a_reader_checks():
    grants = {g.id: g for p in _policies().values() for g in p.grants}
    for gid in BROADER_THAN_REASON:
        assert BROADER_START in grants[gid].bound, (
            f"{gid} does not say it allows more than its reason"
        )
    for gid in sorted(set(grants) - BROADER_THAN_REASON):
        assert BROADER_START not in grants[gid].bound, gid
    text = pp.page(ROOT)
    for gid in BROADER_THAN_REASON:
        row = next(ln for ln in text.splitlines() if ln.startswith(f"| {gid} "))
        assert BROADER_START in row, row


def test_the_limit_of_a_dated_entry_is_one_number_in_the_tool():
    assert pp.MAX_PENDING_DAYS == 92, (
        f"the limit of a dated entry is {pp.MAX_PENDING_DAYS}, not 92 days"
    )
    assert MAX_PENDING_DAYS == pp.MAX_PENDING_DAYS, "this file reads another limit than the tool"
    tree = ast.parse(_text("tests/test_policy_guard.py"))
    own = [
        n.lineno
        for n in ast.walk(tree)
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "MAX_PENDING_DAYS" for t in n.targets)
        and isinstance(n.value, ast.Constant)
    ]
    assert own == [], (
        f"tests/test_policy_guard.py holds its own MAX_PENDING_DAYS number (line {own})"
    )


# ------------------------------------------------------------- M1 and the page: no claim without a run


def test_m1_the_page_names_the_run_once_one_is_on_record(monkeypatch):
    monkeypatch.setattr(pp, "ENGINE_RUN", ("2026-11-12", "CI run 1 of pull request 91"))
    text = pp.page(ROOT)
    assert "have not run yet" not in text
    assert text.count("Last recorded run: 2026-11-12, CI run 1 of pull request 91.") == 3


# ------------------------------------- one plain plant per rule, named by tests/policy_mutants.py as killer


def _appended(rel: str, body: str) -> tuple[list[str], int]:
    text = _text(rel) + f"\n\ndef _planted(p, name):\n    {body}\n"
    return call_problems(rel, text, SHAPES[rel]), text.count("\n")


def test_plant_an_import_of_another_http_library_is_caught():
    problems, line = _appended(TRANSIT, "import httpx")
    same(
        problems,
        [
            (
                f"{TRANSIT}:{line}: import `httpx` is not on this module's import list: a new way to send a "
                "request must be looked at by a person first"
            )
        ],
        what="the check reports: is not on this module's import list",
    )


def test_plant_a_banned_name_that_arrives_through_an_import_alias_is_caught():
    problems, line = _appended(VAULT, "from operator import methodcaller as mc")
    same(
        problems,
        [
            f"{VAULT}:{line}: banned indirect call `methodcaller` (imported)",
            (
                f"{VAULT}:{line}: import `operator:methodcaller` is not on this module's import list: a new "
                "way to send a request must be looked at by a person first"
            ),
        ],
        what="the check reports: (imported)",
    )


def test_plant_attrgetter_on_a_sink_is_caught():
    problems, line = _appended(VAULT, "return json.attrgetter('authed')(p)('GET', 'sys/mounts')")
    same(
        problems,
        [f"{VAULT}:{line}: banned indirect call `attrgetter`"],
        what="the check reports: banned indirect call `attrgetter`",
    )


def test_plant_the_http_opener_used_outside_the_one_sender_is_caught():
    problems, line = _appended(VAULT, "return p._opener")
    same(
        problems,
        [f"{VAULT}:{line}: the HTTP opener `._opener` is used outside ['__init__', 'call']"],
        what="the check reports: the HTTP opener",
    )


def test_plant_the_old_star_form_of_the_vault_secrets_grant_is_caught():
    """Result review Major 2 on head 7af13809: `<prefix>*` covers more than the one path part the code reads."""
    text = _text(VAULT).replace(
        '"resource": "{mount}/data/{path_prefix}+"', '"resource": "{mount}/data/{path_prefix}*"'
    )
    assert text != _text(VAULT)
    same(
        call_problems(VAULT, text, SHAPES[VAULT]),
        [
            (
                f"{VAULT} R17: resource '{{mount}}/data/{{path_prefix}}*' is not the path of the request it "
                "serves ('{mount}/data/{path_prefix}+')"
            )
        ],
        what="the check reports: is not the path of the request",
    )


def test_plant_a_vault_capability_that_is_not_the_verbs_own_is_caught():
    text = _text(TRANSIT).replace('"name": "update"', '"name": "read"')
    assert text != _text(TRANSIT)
    same(
        call_problems(TRANSIT, text, SHAPES[TRANSIT]),
        [f"{TRANSIT} R18: capability 'read' is not the one a POST request needs ('update')"],
        what="the check reports: is not the one a POST request needs",
    )


def test_plant_a_kubernetes_path_that_is_not_the_bound_one_is_caught():
    planted = (
        '        self._get(f"/api/v1/namespaces/{ns}/secrets", "k8s.list_events")\n' + _EVENTS_LINE
    )
    same(
        _planted(KUBE, _EVENTS_LINE, planted),
        [f"{KUBE}:250: the path does not fit the one bound to `k8s.list_events`"],
        what="the check reports: the path does not fit",
    )


def test_plant_a_newline_in_a_reason_is_caught():
    same(
        _grant_changed("secrets/vault", reason='reads one named secret\npath "sys/*" {'),
        [
            (
                "POLICY.grants[0].reason: holds a control or other non-printing character (a newline, a tab); "
                "it would be copied into the rendered policy text"
            )
        ],
        what="the check reports: non-printing character",
    )


def test_plant_a_grant_that_names_no_call_is_caught_with_its_message():
    same(
        _grant_changed("signer/vault_transit", operations=()),
        [
            (
                "grant R18: operations must be a non-empty tuple of 2-part tuples of text: every grant names "
                "the call it serves"
            )
        ],
        what="the check reports: operations must be a non-empty",
    )


def test_plant_a_url_in_verified_is_caught_with_its_message():
    same(
        _grant_changed(
            "secrets/vault", verified=("2026-11-11", "https://developer.hashicorp.com/vault")
        ),
        [
            (
                "grant R17: verified source 'https://developer.hashicorp.com/vault' is not a source id (a URL "
                "or host is never written here)"
            )
        ],
        what="the check reports: is not a source id",
    )


def test_plant_the_mount_sys_is_refused():
    assert _refused_with(
        lambda: pp.render_vault(_policies()["secrets/vault"], {**VAULT_VALUES, "mount": "sys"}),
        ValueError,
        "'mount' is refused: 'sys' starts with Vault's own path",
    ), "a reserved value (the mount sys) is put into the text"


def test_plant_a_300_character_value_is_refused():
    assert _refused_with(
        lambda: pp.render_vault(
            _policies()["signer/vault_transit"], {**TRANSIT_VALUES, "key_name": "k" * 300}
        ),
        ValueError,
        "'key_name' is longer than 255 characters",
    ), "a value longer than its limit is put into the text"


def test_plant_another_module_importing_the_vault_client_is_caught():
    files = {
        **_src_files(),
        "src/hadavin_sdk/planted.py": "from hadavin_sdk.actions.secrets_vault import connect\n",
    }
    same(
        client_user_problems(files),
        [
            (
                "src/hadavin_sdk/planted.py:1: imports ['connect'] from the Vault client module; only the "
                "declared kind modules may, with the listed names"
            )
        ],
        what="the check reports: from the Vault client module",
    )


# ------------------------------------------------ fix batch 5: the review of round 5 and the evidence run (items a to d)


def _planted_policies(kind: str, change) -> dict[str, pp.Policy]:
    """The real policies with the raw literal of `kind` changed by `change(raw)`."""
    policies = _policies()
    raw = _raw(kind)
    change(raw)
    policies[kind] = pp.parse(f"POLICY = {raw!r}")
    return policies


def _free_reason(kind: str, reason: str, claims: tuple[str, ...] | None = None):
    def change(raw):
        entry = {**raw["free"][0], "reason": reason}
        if claims is not None:
            entry["claims_unverified"] = claims
        raw["free"] = (entry, *raw["free"][1:])

    return _planted_policies(kind, change)


def _problems_of(policies: dict[str, pp.Policy]) -> list[str]:
    return note_problems(policies, NOTE_CLASSES, set(source_ids()))


# ---- C1: two marks, read from the head of the sources file


def _claim_rows(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if ln.startswith("| R")]


def test_every_claim_has_one_of_two_marks_taken_from_the_head_of_the_sources_file():
    marks = pp.read_marks(ROOT)
    claims = [
        (g.id, c) for p in _policies().values() for g in p.grants for c in g.claims_unverified
    ]
    builder = [(gid, c) for gid, c in claims if pp.claim_mark(c, marks) == pp.MARK_BUILDER_READ]
    assert [gid for gid, _ in builder] == ["R17"] and builder[0][1] == R17_CLAIM[0], (
        f"the claims with the builder mark are not exactly the + claim of R17: {builder}"
    )
    same(pp.claim_mark_problems(_policies(), marks), [])
    for gid, c in claims:
        if (gid, c) not in builder:
            assert pp.claim_mark(c, marks) == pp.MARK_NOBODY_READ, (gid, c)
    assert pp.MARK_BUILDER_READ != pp.MARK_NOBODY_READ


def test_the_page_shows_the_builder_mark_on_the_plus_claim_of_r17_and_the_nobody_mark_on_every_other_claim():
    text = pp.page(ROOT)
    rows = {ln.split(" | ")[0].removeprefix("| "): ln for ln in _claim_rows(text)}
    r17 = rows["R17"]
    assert f"nothing deeper ({pp.MARK_BUILDER_READ})" in r17, (
        f"the claims cell shows no mark after nothing deeper: {r17}"
    )
    assert f"older version of that secret ({pp.MARK_NOBODY_READ})" in r17, (
        f"the claims cell shows no mark after the older version of that secret: {r17}"
    )
    for gid in ("R18", "R20", "R21", "R22"):
        assert pp.MARK_NOBODY_READ in rows[gid] and pp.MARK_BUILDER_READ not in rows[gid], rows[gid]
    free = next(ln for ln in text.splitlines() if ln.startswith("- `k8s.rules_review`"))
    assert "Claims not checked: a `create` on `selfsubjectrulesreviews` changes nothing" in free
    assert free.endswith(f"{pp.MARK_NOBODY_READ}).") and pp.MARK_BUILDER_READ not in free, free
    never = next(ln for ln in text.splitlines() if ln.startswith("| action | `create` |"))
    assert never.endswith(f"({pp.MARK_NOBODY_READ}) |") and pp.MARK_BUILDER_READ not in never, never
    # the only claim on the page that says "builder read" is the `+` claim of R17
    marked = [
        ln
        for ln in text.splitlines()
        if ln.startswith(("| ", "- `")) and pp.MARK_BUILDER_READ in ln
    ]
    assert marked == [r17], marked


def test_a_claim_with_no_mark_two_marks_or_a_stale_text_is_a_problem_and_a_bad_line_is_refused(
    tmp_path,
):
    policies = _policies()
    marks = pp.read_marks(ROOT)
    found = pp.claim_mark_problems(policies, dataclasses.replace(marks, nobody_read=("zzz",)))
    assert any("has 0 marks" in p for p in found), found
    assert any("'zzz' matches no claim" in p for p in found), (
        f"a stale text is not reported: {found}"
    )
    r18 = next(c for c in marks.nobody_read if c.startswith("the exact path R18"))
    both = dataclasses.replace(marks, builder_read=(*marks.builder_read, r18))
    assert any("has 2 marks" in p for p in pp.claim_mark_problems(policies, both)), "two marks pass"
    body = _text(pp.SOURCES)
    accepted = set()
    for name, text in {
        "missing": body.replace("# CLAIM-READ-BY-NOBODY:", "# X:"),
        "second": body + "\n# CLAIM-READ-BY-BUILDER: x\n",
        "empty text": body.replace(
            "# CLAIM-READ-BY-BUILDER: the +", "# CLAIM-READ-BY-BUILDER: ;; the +"
        ),
    }.items():
        (tmp_path / pp.SOURCES).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / pp.SOURCES).write_text(text, encoding="utf-8")
        why = "holds an empty claim text" if name == "empty text" else "needs exactly one line"
        if not _refused_with(lambda: pp.read_marks(tmp_path), pp.PolicyError, why):
            accepted.add(name)
    assert "missing" not in accepted, "a sources file with no claim line is accepted"
    assert "second" not in accepted, "a second claim line in the sources file is accepted"
    assert "empty text" not in accepted, (
        "an empty claim text in the head of the sources file is accepted"
    )


# ---- C3: free and never rows carry the mark too


def test_a_free_or_never_row_with_a_claim_marks_its_partly_read_sources():
    text = pp.page(ROOT)
    free = next(ln for ln in text.splitlines() if ln.startswith("- `k8s.rules_review`"))
    assert f"K-SSRR {_PASSAGE_MARK}" in free and f"K-RBAC {_PASSAGE_MARK}" in free, (
        f"a free request with a claim (k8s.rules_review) shows its partly read source as a plain claim: {free}"
    )
    assert f"K-SRC {_PASSAGE_MARK}" not in free, free
    never = next(ln for ln in text.splitlines() if ln.startswith("| action | `create` |"))
    assert f"K-AUTHZ {_PASSAGE_MARK}" in never, (
        f"a never line with a claim (| action | `create` |) shows its partly read source as a plain claim: {never}"
    )
    update = next(ln for ln in text.splitlines() if ln.startswith("| action | `update` |"))
    assert _PASSAGE_MARK not in update, update  # no claim: no mark


# ---- C2 and the evidence probes P1a to P1c: every reason has a class


def test_a_free_reason_that_says_it_creates_nothing_or_changes_nothing_has_no_class_and_is_refused():
    kube = "source/kubernetes"
    real = _policies()[kube].free[0].reason
    same(_problems_of(_policies()), [])
    for said in (
        "asks the cluster what this identity may do and creates nothing in the cluster",
        "it is read-only and changes nothing",
        "it only reads",
    ):
        for claims in (None, ()):
            found = _problems_of(_free_reason(kube, said, claims))
            assert any("has 0 classes in NOTE_CLASSES" in p and "reason:" in p for p in found), (
                f"the free reason {said!r} (claims {claims}) needs no class: it has 0 classes in NOTE_CLASSES "
                f"and is not refused: {found}"
            )
    # a reason that starts like the real one and goes on: refused as well (a reason matches its exact text)
    found = _problems_of(_free_reason(kube, real + " It creates nothing in the cluster."))
    assert any("has 0 classes in NOTE_CLASSES" in p for p in found), found


def test_a_reason_is_matched_by_its_exact_text_even_when_a_class_key_is_its_unique_prefix():
    # Planted on its own data, so it does not depend on which real reason is the prefix of another: the key is
    # a prefix no real reason has, the reason goes on after it, so the reason has no class.
    kube = "source/kubernetes"
    key = "reason:zq planted reason with no look-alike in the data"
    classes = {**NOTE_CLASSES, (kube, key): ("code",)}
    for tail in (" and goes on", " "):
        policies = _free_reason(kube, key.removeprefix("reason:") + tail)
        found = note_problems(policies, classes, set(source_ids()))
        assert any(
            "has 0 classes in NOTE_CLASSES" in p and "zq planted reason" in p for p in found
        ), (
            f"a reason that goes on after its unique prefix is read as the class of that prefix: {found}"
        )
    exact = _free_reason(kube, key.removeprefix("reason:"))
    found = note_problems(exact, classes, set(source_ids()))
    assert not any("zq planted reason" in p and "has 0 classes" in p for p in found), found


def test_a_grant_or_never_reason_with_no_class_is_refused_and_a_wrong_class_is_caught():
    vault, kube = "secrets/vault", "source/kubernetes"

    def grant(raw):
        raw["grants"] = ({**raw["grants"][0], "reason": "reads one named secret and nothing else"},)

    def never(raw):
        raw["never"] = (
            *raw["never"],
            {"type": "role", "name": "x", "reason": "it only reads", "verified": None},
        )

    for kind, change in ((vault, grant), (kube, never)):
        found = _problems_of(_planted_policies(kind, change))
        assert any("has 0 classes" in p for p in found), found
    wrong = {
        # `sources` on a reason whose entry names no source
        (vault, "reason:brings deleted versions of a secret back"): ("sources",),
        # `pending` on a reason whose entry has `verified` set
        (vault, "reason:marks versions of a secret as deleted"): ("pending",),
    }
    classes = {**NOTE_CLASSES, **wrong}
    found = note_problems(_policies(), classes, set(source_ids()))
    assert any("is class sources, but its entry names no source" in p for p in found), (
        f"a sources class on an entry with no source is not reported: {found}"
    )
    assert any("is class pending, but its entry has `verified` set" in p for p in found), (
        f"a pending class on an entry with a source is not reported: {found}"
    )
    claimless = {
        **NOTE_CLASSES,
        (kube, "reason:reads deployments, their rollout revision and images"): (
            "claim",
            "no such text",
        ),
    }
    assert any(
        "is a claim, but no claims_unverified holds" in p
        for p in note_problems(_policies(), claimless, set(source_ids()))
    ), "a claim class whose text is in no claim of its entry is accepted"


# ---- (b) the check command reports a bad class table, never a KeyError


def test_a_note_class_with_an_unknown_source_id_is_a_problem_of_the_check_and_the_page_raises_policy_error(
    monkeypatch,
):
    key = ("source/kubernetes", "free:a default cluster gives every")
    monkeypatch.setitem(pp.NOTE_CLASSES, key, ("sources", ("K-NOPE",)))
    found = pp.data_problems(ROOT, today=DECIDED)
    assert any("K-NOPE, which is not in the sources file" in p for p in found), (
        f"the check command does not report an unknown source id of a note class: {found}"
    )
    raised: Exception | None = None
    try:
        pp.page(ROOT)
    except (pp.PolicyError, KeyError, IndexError, TypeError, ValueError) as exc:
        raised = exc
    assert raised is not None, "the page accepts a note class with an unknown source id"
    assert isinstance(raised, pp.PolicyError), (
        f"the page raises {type(raised).__name__}, not PolicyError: {raised}"
    )  # the old code raised a KeyError here
    assert "K-NOPE" in str(raised), (
        "the PolicyError of the page does not name the unknown id K-NOPE"
    )


def test_a_free_note_class_that_lists_a_source_its_entry_does_not_name_is_a_problem_of_the_check(
    monkeypatch, tmp_path
):
    key = ("source/kubernetes", "free:a default cluster gives every")
    monkeypatch.setitem(pp.NOTE_CLASSES, key, ("sources", ("K-RBAC", "K-SRC", "V-TOK")))
    found = pp.data_problems(ROOT, today=DECIDED)
    assert any("V-TOK, which is not in `verified` of the same entry" in p for p in found), (
        f"the check command does not report a class source that is not in `verified`: {found}"
    )
    monkeypatch.setitem(pp.NOTE_CLASSES, key, ("sources", ("K-RBAC", "K-SRC", "K-SSRR")))
    root = _tree(tmp_path)
    kube = root / pp.KIND_MODULES["source/kubernetes"]
    old = '"verified": ("2026-11-11", "K-RBAC", "K-SRC", "K-SSRR"),'
    assert old in kube.read_text(encoding="utf-8")
    kube.write_text(
        kube.read_text(encoding="utf-8").replace(
            old, '"verified": ("2026-11-11", "K-RBAC", "K-SRC"),'
        ),
        encoding="utf-8",
    )
    found = pp.data_problems(root, today=DECIDED)
    assert any("K-SSRR, which is not in `verified` of the same entry" in p for p in found), (
        f"the check command does not report a source dropped from `verified`: {found}"
    )


def test_the_check_command_reports_a_claim_with_no_mark_in_the_sources_file(tmp_path):
    root = _tree(tmp_path)
    head = root / pp.SOURCES
    head.write_text(
        _text(pp.SOURCES).replace("the exact path R18 does not also allow", "no such claim"),
        encoding="utf-8",
    )
    found = pp.data_problems(root, today=DECIDED)
    assert any("has 0 marks" in p for p in found) and any("matches no claim" in p for p in found), (
        f"the check command does not report a claim with no mark: {found}"
    )


# ---- C4: the head sentence and the R17 cell say the same


R17_HEDGED = "it may also cover every older version of each (not yet checked against the vendor, see the claims cell)"
R17_FLAT = "each with every older version"


def test_the_page_head_and_the_r17_cell_and_reason_state_the_same_hedged_scope():
    text = pp.page(ROOT)
    head = text.split("## vault (secrets)", 1)[0].replace("\n  ", " ")
    r17_row = next(ln for ln in text.splitlines() if ln.startswith("| R17 "))
    r17 = _policies()["secrets/vault"].grants[0]
    assert "every secret directly under the prefix" in head, (
        "the page head does not say the prefix scope"
    )
    for where, said in (
        ("the page head", head),
        ("the R17 cell", r17_row),
        ("the reason", r17.reason),
    ):
        assert "every secret directly under the prefix" in said, (
            f"{where} does not say the prefix scope"
        )
        assert "may also" in said and "every older version of each" in said, (
            f"{where} does not say the older versions are only possible"
        )
        assert "not yet checked against the vendor" in said, (
            f"{where} does not hedge the older versions"
        )
    assert R17_HEDGED in r17.reason, r17.reason
    assert "also serves a request for an older version" in r17.bound, (
        "the bound does not name the claim"
    )
    assert "second claim" not in r17.bound, (
        "the bound points at a claim by its place, not in its own words"
    )
    assert "reads one named secret" not in head.replace("not only the one secret it names", "")
    docs = (ROOT / "docs/declared-permissions.md").read_text(encoding="utf-8")
    for where, said in (
        ("the page head", head),
        ("the R17 cell", r17_row),
        ("the reason", r17.reason),
        ("the bound", r17.bound),
        ("docs/declared-permissions.md", docs),
        ("the secrets_vault.py source", _text(pp.KIND_MODULES["secrets/vault"])),
        ("the rendered Vault policy", pp.render_vault(_policies()["secrets/vault"])),
    ):
        assert R17_FLAT not in said and "and every older version of each" not in said, (
            f"{where} still says flatly that R17 covers every older version"
        )


# ---- (a) a never path that is deeper than the grant does not cover it


def test_a_never_path_deeper_than_the_prefix_grant_is_not_reported_as_covering_it():
    # R17 is `{mount}/data/{path_prefix}+`; the setting has ONE value in a deployment, so a never line that
    # writes `{path_prefix}` once and then two more parts is two parts longer than R17 for every value.
    vault = "secrets/vault"
    same(
        _never_over(
            vault, "{mount}/data/{path_prefix}+/deeper/+", ("read",)
        ),  # the evidence probe P3e
        [],
        "{mount}/data/{path_prefix}+/deeper/+ is reported as covering the prefix grant R17",
    )
    same(
        _never_over(vault, "{mount}/data/{path_prefix}+/+", ("read",)),  # the evidence probe P3b
        [],
        "{mount}/data/{path_prefix}+/+ is reported as covering the prefix grant R17",
    )
    same(
        _never_over(vault, "{mount}/data/{path_prefix}deeper/+/+", ("read",)),
        [],
        "{mount}/data/{path_prefix}deeper/+/+ is reported as covering the prefix grant R17",
    )
    for name in ("{mount}/data/{path_prefix}+", "{mount}/data/{path_prefix}*"):
        found = _never_over(vault, name, ("read",))
        assert len(found) == 1 and "grant R17 " in found[0], (name, found)


def test_the_path_overlap_with_a_prefix_setting_agrees_with_a_brute_force_search_over_its_values():
    import itertools

    # Patterns start with `{path_prefix}` (so the one value sits at the same place in both) and go on with up to
    # two parts of `a`, `b` or `+`, with or without a last `*`. The reference answer: for every value of the
    # setting (1 or 2 parts, each `a/` or `b/`) put the value in both patterns, then ask whether ONE path fits both.
    candidates = ["".join(c) for n in range(8) for c in itertools.product("ab/", repeat=n)]
    values = ["".join(parts) for k in (1, 2) for parts in itertools.product(("a/", "b/"), repeat=k)]
    tails = [
        "",
        *("/".join(t) for n in (1, 2) for t in itertools.product(("a", "b", "+"), repeat=n)),
    ]
    patterns = [
        "{path_prefix}" + tail + star
        for tail in tails
        for star in ("", "*")
        if not (star and tail.endswith("+"))
    ]
    allowed = {
        (p, v): _matches(p.replace("{path_prefix}", v), candidates)
        for p in patterns
        for v in values
    }
    seen = set()
    for first, second in itertools.product(patterns, repeat=2):
        answer = any(allowed[first, v] & allowed[second, v] for v in values)
        seen.add(answer)
        assert pp.vault_paths_overlap(first, second) == answer, (
            f"overlap of {first!r} and {second!r} differs from the brute-force answer {answer}"
        )
    assert seen == {True, False}


# ------------------------------------------------ fix batch 6: the review of round 6 and the evidence run


PLUS_CLAIM = R17_CLAIM[0]
OLDER_CLAIM = R17_CLAIM[1]
R18_CLAIM = "the exact path R18 does not also allow Vault's longer sign path that ends in a hash algorithm name"


def _edit(root: Path, rel: str, old: str, new: str) -> None:
    text = (root / rel).read_text(encoding="utf-8")
    assert text.count(old) == 1, (rel, old)
    (root / rel).write_text(text.replace(old, new), encoding="utf-8")


def _head(root: Path) -> str:
    return (root / pp.SOURCES).read_text(encoding="utf-8")


# ---- 1: a claim carries a mark by its FULL text, one reader for the three parsers


_MORE = ", and so does every other path"


def test_a_clause_appended_to_a_claim_is_no_longer_the_listed_claim(tmp_path):
    # the end of the R18 claim is written in two strings in the module, so the clause goes after `algorithm name"`
    for rel, old in ((VAULT, PLUS_CLAIM), (VAULT, OLDER_CLAIM), (TRANSIT, 'algorithm name"')):
        root = _tree(tmp_path / rel.replace("/", "_"))
        _edit(root, rel, old, old.removesuffix('"') + _MORE + ('"' if old.endswith('"') else ""))
        found = pp.data_problems(root, today=DECIDED)
        assert any("has 0 marks" in p for p in found), f"the longer claim still has a mark: {found}"
        assert any("matches no claim" in p for p in found), f"the listed text is not stale: {found}"


def test_the_marks_of_r17_and_r18_swapped_in_the_sources_file_are_reported_by_the_check(tmp_path):
    root = _tree(tmp_path)
    text = _head(root)
    text = text.replace(
        f"# CLAIM-READ-BY-BUILDER: {PLUS_CLAIM}\n", f"# CLAIM-READ-BY-BUILDER: {R18_CLAIM}\n"
    )
    assert f" ;; {R18_CLAIM}" in text
    (root / pp.SOURCES).write_text(
        text.replace(f" ;; {R18_CLAIM}", f" ;; {PLUS_CLAIM}"), encoding="utf-8"
    )
    found = pp.data_problems(root, today=DECIDED)
    assert any(
        p.startswith("signer/vault_transit R18") and "marked 'builder read the passage'" in p
        for p in found
    ), f"a builder-read mark on R18 is not reported: {found}"
    assert any(
        p.startswith("secrets/vault R17") and "none of its claims is marked" in p for p in found
    ), f"R17 with no builder-read claim is not reported: {found}"


def test_a_claim_text_under_both_marks_is_refused(tmp_path):
    root = _tree(tmp_path)
    (root / pp.SOURCES).write_text(
        _head(root).replace(
            "# CLAIM-READ-BY-NOBODY: ", f"# CLAIM-READ-BY-NOBODY: {PLUS_CLAIM} ;; ", 1
        ),
        encoding="utf-8",
    )
    assert any("is under both marks" in p for p in pp.data_problems(root, today=DECIDED)), (
        "a text under both marks is not reported"
    )
    with pytest.raises(pp.PolicyError, match="is under both marks"):
        pp.read_marks(root)


def test_a_claim_text_that_ends_in_two_semicolons_or_repeats_is_refused(tmp_path):
    root = _tree(tmp_path)
    nobody = next(ln for ln in _head(root).splitlines() if ln.startswith("# CLAIM-READ-BY-NOBODY:"))
    for name, line, why in (
        ("a trailing ` ;;`", nobody + " ;;", "holds `;;` inside a claim text"),
        ("a text twice", nobody + f" ;; {OLDER_CLAIM}", "holds a claim text twice"),
    ):
        (root / pp.SOURCES).write_text(
            _head(_tree(tmp_path)).replace(nobody, line), encoding="utf-8"
        )
        assert any(why in p for p in pp.data_problems(root, today=DECIDED)), (
            f"{name} is not refused"
        )
        with pytest.raises(pp.PolicyError, match=why):
            pp.read_marks(root)


def test_a_byte_order_mark_is_read_the_same_by_the_row_the_id_and_the_claim_parsers(tmp_path):
    for first in ("# BUILDER-ONLY:", "# CLAIM-READ-BY-BUILDER:", "V-POL | "):
        root = _tree(tmp_path / first[:6].strip("#| "))
        plain_rows = pp.source_ids(root)
        lines = _head(root).split("\n")
        moved = next(ln for ln in lines if ln.startswith(first))
        lines.remove(moved)
        (root / pp.SOURCES).write_bytes("\n".join([moved, *lines]).encode("utf-8-sig"))
        assert (root / pp.SOURCES).read_bytes().startswith(b"\xef\xbb\xbf")
        assert pp.data_problems(root, today=DECIDED) == [], (
            f"a file with a byte-order mark before `{first}` is refused somewhere"
        )
        assert pp.source_ids(root) == plain_rows
        assert pp.read_marks(root) == pp.read_marks(ROOT)


# ---- 2: R17 says "it may also cover every older version" only as a hedge (test above: ..._same_hedged_scope)


# ---- 3: the dated lists are run by `--check`


def test_the_check_command_reports_a_name_or_claim_with_no_dated_entry_and_a_stale_or_overdue_entry(
    monkeypatch, capsys
):
    monkeypatch.setattr(pp, "PENDING_NAMES", {})
    code, lines = _check(monkeypatch, capsys, ROOT)
    assert code == 1 and len(lines) == len(PENDING_NAMES), lines
    assert all("no PENDING_NAMES entry" in ln for ln in lines), lines
    monkeypatch.setattr(pp, "PENDING_NAMES", PENDING_NAMES)
    monkeypatch.setattr(pp, "PENDING_CLAIMS", {})
    code, lines = _check(monkeypatch, capsys, ROOT)
    assert code == 1 and len(lines) == len(PENDING_CLAIMS), lines
    assert all("no PENDING_CLAIMS entry" in ln for ln in lines), lines
    stale = {**PENDING_CLAIMS, ("secrets/vault", "R99"): PENDING_CLAIMS[("secrets/vault", "R17")]}
    monkeypatch.setattr(pp, "PENDING_CLAIMS", stale)
    code, lines = _check(monkeypatch, capsys, ROOT)
    same(
        (code, lines),
        (
            1,
            [
                "policy page: PENDING_CLAIMS ('secrets/vault', 'R99') is fixed or gone: delete the entry"
            ],
        ),
    )
    monkeypatch.setattr(pp, "PENDING_CLAIMS", PENDING_CLAIMS)
    pair = _overdue_pair()
    if pair is None:  # the end state: nothing can be overdue; its own test runs the real commands
        assert pp.data_problems(ROOT, today=DECIDED + timedelta(days=800)) == []
        return
    day, after = pair
    overdue = pp.data_problems(ROOT, today=after)
    due = sum(1 for p in (*PENDING_NAMES.values(), *PENDING_CLAIMS.values()) if p.review_by == day)
    assert len(overdue) == due, (
        f"the entries due the day after the review day are not each reported once: {overdue}"
    )
    assert all(f"is overdue (review_by {day})" in p for p in overdue), (
        f"an entry due the day after the review day is not reported as overdue: {overdue}"
    )
    assert pp.data_problems(ROOT, today=day) == [], "an entry is reported overdue on its review day"


def test_from_the_review_date_the_write_command_stops_and_writes_nothing(
    tmp_path, monkeypatch, capsys
):
    # The dated entries are overdue the day after `review_by`: `--write` then refuses with the overdue lines
    # (the red signal that the dates must be renewed); the day before it passes. Every call gives `today`, so no
    # result here depends on the real date.
    root = _tree(tmp_path)
    monkeypatch.setattr(pp, "ROOT", root)
    monkeypatch.setattr(pp, "DATA_ROOT", root)
    pair = _overdue_pair()
    if pair is None:  # the end state: no date to go red on; the commands stay green on any day
        late = DECIDED + timedelta(days=800)
        assert pp.main(["--write"], today=late) == 0 and pp.main(["--check"], today=late) == 0, (
            "with both dated lists empty the commands stop on a late day"
        )
        return
    day_before, day_of = pair
    assert pp.main(["--write"], today=day_before) == 0 and (root / pp.PAGE).is_file(), (
        "the write command did not write the page the day before the review date"
    )
    capsys.readouterr()
    (root / pp.PAGE).unlink()
    assert pp.main(["--write"], today=day_of) == 1, (
        "the write command did not stop on the review date it was given"
    )
    assert not (root / pp.PAGE).exists(), (
        "`--write` wrote the page although the dated entries are overdue"
    )
    err = capsys.readouterr().err
    assert f"is overdue (review_by {day_before})" in err, err


def test_from_the_review_date_the_check_command_stops(tmp_path, monkeypatch, capsys):
    root = _tree(tmp_path)
    monkeypatch.setattr(pp, "ROOT", root)
    monkeypatch.setattr(pp, "DATA_ROOT", root)
    pair = _overdue_pair()
    if pair is None:  # the end state: no date to go red on; the commands stay green on any day
        late = DECIDED + timedelta(days=800)
        assert pp.main(["--write"], today=late) == 0 and pp.main(["--check"], today=late) == 0, (
            "with both dated lists empty the commands stop on a late day"
        )
        return
    day_before, day_of = pair
    assert pp.main(["--write"], today=day_before) == 0
    assert pp.main(["--check"], today=day_before) == 0, (
        "the check command stopped the day before the review date"
    )
    capsys.readouterr()
    assert pp.main(["--check"], today=day_of) == 1, (
        "the check command did not stop on the review date it was given"
    )
    err = capsys.readouterr().err
    assert f"is overdue (review_by {day_before})" in err, err


def test_a_grant_whose_name_is_unchecked_with_no_pending_row_is_reported_by_the_check(tmp_path):
    root = _tree(tmp_path)
    text = (root / VAULT).read_text(encoding="utf-8")
    planted, n = re.subn(
        r'"verified": \(\s*"2026-11-11",\s*"V-KV",.*?\),\n',
        '"verified": None,\n',
        text,
        count=1,
        flags=re.DOTALL,
    )
    assert n == 1
    (root / VAULT).write_text(planted, encoding="utf-8")
    found = pp.data_problems(root, today=DECIDED)
    assert any(
        p.startswith("secrets/vault R17: the name is not found in a vendor source")
        and "no PENDING_NAMES entry" in p
        for p in found
    ), f"a name with no dated entry is not reported by the check: {found}"


def test_a_new_unchecked_claim_with_no_pending_row_is_reported_by_the_check(tmp_path):
    root = _tree(tmp_path)
    text = (root / TRANSIT).read_text(encoding="utf-8")
    head, tail = text.split('"id": "R19"', 1)
    assert tail.count('"claims_unverified": (),') == 1
    (root / TRANSIT).write_text(
        head
        + '"id": "R19"'
        + tail.replace(
            '"claims_unverified": (),', '"claims_unverified": ("a planted statement",),'
        ),
        encoding="utf-8",
    )
    found = pp.data_problems(root, today=DECIDED)
    assert any(
        p.startswith("signer/vault_transit R19: has an unchecked claim")
        and "no PENDING_CLAIMS entry" in p
        for p in found
    ), f"a claim with no dated entry is not reported by the check: {found}"


# ---- 4: the marks are read from `root`; a bad class table is one problem line


@pytest.mark.parametrize(
    "tag",
    [
        "# BUILDER-ONLY:",
        "# PARTLY-BUILDER-ONLY:",
        "# CLAIM-READ-BY-BUILDER:",
        "# CLAIM-READ-BY-NOBODY:",
    ],
)
def test_a_missing_marks_line_in_the_head_is_one_problem_of_the_check_not_a_traceback(
    tmp_path, monkeypatch, capsys, tag
):
    root = _tree(tmp_path)
    assert _head(root).count(tag) == 1
    (root / pp.SOURCES).write_text(_head(root).replace(tag, "# X:"), encoding="utf-8")
    code, lines = _check(monkeypatch, capsys, root)
    assert code == 1 and len(lines) == 1, lines
    assert f"needs exactly one line starting `{tag}`" in lines[0], lines


def test_the_page_takes_its_marks_from_the_root_it_is_given(tmp_path):
    root = _tree(tmp_path)
    (root / pp.SOURCES).write_text(
        _head(root).replace("# BUILDER-ONLY: V-ACL, ", "# BUILDER-ONLY: V-KV, V-ACL, "),
        encoding="utf-8",
    )
    r17 = next(ln for ln in pp.page(root).splitlines() if ln.startswith("| R17 "))
    assert "V-KV (builder only)" in r17, (
        f"the page does not take its marks from the root it is given: {r17}"
    )
    r17 = next(ln for ln in pp.page(ROOT).splitlines() if ln.startswith("| R17 "))
    assert "V-KV (builder only)" not in r17, r17


_KEY = ("signer/vault_transit", "In the call column")
BAD_CLASSES = {
    "an empty tuple": ((), "its class is not a non-empty tuple"),
    "a bare text": ("code", "its class is not a non-empty tuple"),
    "a claim with a number": (("claim", 5), "its class claim needs exactly one non-empty text"),
    "a claim with an empty text": (
        ("claim", ""),
        "its class claim needs exactly one non-empty text",
    ),
    "a claim with no text": (("claim",), "its class claim needs exactly one non-empty text"),
    "a source list holding a number": (("sources", ("V-KV", 5)), "its class sources needs"),
    "a source list as bare text": (("sources", "V-KV"), "its class sources needs"),
    "an unknown class": (("weird",), "is not one of code, sources, claim, pending"),
    "code with an extra item": (("code", "x"), "its class code takes nothing"),
    "pending with an extra item": (("pending", ("x",)), "its class pending takes nothing"),
}


def _check_or_fail(monkeypatch, capsys):
    try:
        return _check(monkeypatch, capsys, ROOT)
    except (AttributeError, IndexError, KeyError, TypeError, ValueError) as exc:
        # the check must report, never raise: the assertion that follows shows this
        return -1, [f"the check raised {type(exc).__name__} instead of one problem line"]


def test_a_malformed_note_class_is_one_problem_line_of_the_check_and_no_traceback(
    monkeypatch, capsys
):
    for name in sorted(BAD_CLASSES):
        cls, why = BAD_CLASSES[name]
        with monkeypatch.context() as m:
            m.setitem(pp.NOTE_CLASSES, _KEY, cls)
            code, lines = _check_or_fail(m, capsys)
        assert code == 1 and len(lines) == 1, (
            f"a malformed class is not one problem line ({name}): {lines}"
        )
        assert "NOTE_CLASSES entry" in lines[0] and why in lines[0], (
            f"the problem line does not name the class shape ({name}): {lines}"
        )


def test_a_malformed_note_class_key_is_one_problem_line_of_the_check_and_no_traceback(
    monkeypatch, capsys
):
    for key in (("secrets/vault",), (1, "x"), "secrets/vault", ("a", "b", "c")):
        with monkeypatch.context() as m:
            m.setitem(pp.NOTE_CLASSES, key, ("code",))
            code, lines = _check_or_fail(m, capsys)
        assert code == 1 and len(lines) == 1, (
            f"a malformed key is not one problem line (the check raised IndexError, or printed more): {lines}"
        )
        assert "its key is not a tuple of two texts" in lines[0], lines


# ---- 5: head prose about which claim has which mark is built from the sources file


def test_the_page_head_lists_the_claims_of_each_mark_from_the_sources_file_not_from_prose():
    marks = pp.read_marks(ROOT)
    planted = dataclasses.replace(
        marks, builder_read=("planted builder text",), nobody_read=("planted other text",)
    )
    head = pp.head(planted)
    assert '"planted builder text"' in head and '"planted other text"' in head, (
        f"the page head does not list the claims of each mark from the lists it is given: {head}"
    )
    assert PLUS_CLAIM not in head
    real = pp.head(marks)
    for text in (*marks.builder_read, *marks.nobody_read):
        assert f'"{text}"' in real, text
    assert "Only one claim has the first mark" not in real


def test_the_fixture_head_names_the_builder_read_claims_as_they_are():
    head = _head(ROOT)
    marks = pp.read_marks(ROOT)
    assert len(marks.builder_read) == 1 and marks.builder_read[0] == PLUS_CLAIM
    assert "only V-POL and B-POL have a builder-read passage" in " ".join(
        ln.removeprefix("#").strip() for ln in head.splitlines()
    ), "the fixture head does not say which sources have a builder-read passage"
    assert "the other 7" in " ".join(ln.removeprefix("#").strip() for ln in head.splitlines())
    assert len(marks.partly_builder_only) == 9
    assert "(6 different texts)" in " ".join(
        ln.removeprefix("#").strip() for ln in head.splitlines()
    )
    assert len(set(marks.nobody_read)) == len(marks.nobody_read) == 6


def test_a_kind_whose_module_could_not_be_read_adds_no_stale_class_line():
    # The note classes of a kind that is not among the loaded policies are not reported as stale: that kind has
    # its own problem line, and its notes were never looked at.
    kube = "source/kubernetes"
    policies = {k: v for k, v in _policies().items() if k != kube}
    found = pp.note_problems(policies, pp.NOTE_CLASSES, set(pp.source_ids(ROOT)))
    assert not [p for p in found if kube in p], (
        f"a kind that was not loaded is reported as stale class lines: {found}"
    )


def test_the_sixteen_kinds_keep_a_decision_day_of_their_own_not_the_tools_date():
    assert {p.decided for p in PENDING_KINDS.values()} == {date(2026, 11, 11)}, (
        "the pending kinds do not all stand on the literal day 2026-11-11"
    )
    assert len(PENDING_KINDS) == 16, "the number of pending kinds is not 16"
    # the 92-day cap compares `review_by` with `decided` (moved here from the changelog test file, where no
    # mutant could reach it)
    assert max((p.review_by - p.decided).days for p in PENDING_KINDS.values()) <= 92, (
        "a pending kind is more than 92 days from its decision to its review day"
    )


def test_the_tool_docstring_holds_no_date_that_is_not_in_the_dated_lists():
    dated = (*pp.PENDING_NAMES.values(), *pp.PENDING_CLAIMS.values())
    allowed = {str(d) for p in dated for d in (p.decided, p.review_by)}
    stray = set(re.findall(r"\d{4}-\d{2}-\d{2}", pp.__doc__)) - allowed
    assert not stray, f"the tool docstring holds a date that is in no dated list: {sorted(stray)}"


def test_the_tool_docstring_holds_no_literal_date():
    # A day written in the docstring would stay after a renewal and could be another entry's day; the tool's
    # docstring names the rule (the day after the earliest `review_by`), never a day.
    stray = stray_days(pp.__doc__)
    assert not stray, f"the tool docstring holds a literal date: {stray}"


def test_the_decision_day_of_the_16_kinds_does_not_follow_the_tools_decision_day(monkeypatch):
    # Behaviour, not syntax: this file is run again with the tool's decision day moved, and its 16 kinds must keep
    # the day they were decided (a name that takes the tool's day would move them and the 92-day cap with them).
    monkeypatch.setattr(pp, "DECIDED", pp.DECIDED + timedelta(days=30))
    again = runpy.run_path(__file__, run_name="b10_kinds_copy")
    same(
        {p.decided for p in again["PENDING_KINDS"].values()},
        {KINDS_DECIDED},
        "the 16 kinds follow the tool's decision day when it moves (the decision days of the 16 kinds)",
    )


def _fixed_clock(day: date):
    """A `datetime` look-alike for `pp.datetime`: its `now()` is `day` at noon UTC (as the evidence plugin does)."""
    fixed = datetime(day.year, day.month, day.day, 12, tzinfo=UTC)

    class Fixed(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed if tz is None else fixed.astimezone(tz)

    return Fixed


def test_the_check_command_uses_the_tools_own_clock_when_no_day_is_given(
    tmp_path, monkeypatch, capsys
):
    # `python tools/policy_page.py --check` passes no `today`: every other test gives one, so a default fixed to
    # a day would keep the command green after the review date and no test would notice.
    root = _tree(tmp_path)
    monkeypatch.setattr(pp, "ROOT", root)
    monkeypatch.setattr(pp, "DATA_ROOT", root)
    pair = _overdue_pair()
    if pair is None:  # the end state: no date to go red on; the commands stay green on any day
        late = DECIDED + timedelta(days=800)
        assert pp.main(["--write"], today=late) == 0 and pp.main(["--check"], today=late) == 0, (
            "with both dated lists empty the commands stop on a late day"
        )
        return
    day_before, day_of = pair
    assert pp.main(["--write"], today=day_before) == 0
    capsys.readouterr()
    monkeypatch.setattr(pp, "datetime", _fixed_clock(day_before))
    assert pp.main(["--check"]) == 0, f"the check command stopped on {day_before} by its own clock"
    monkeypatch.setattr(pp, "datetime", _fixed_clock(day_of))
    assert pp.main(["--check"]) == 1, (
        f"the check command did not stop on {day_of} by its own clock (no day given)"
    )
    assert f"is overdue (review_by {day_before})" in capsys.readouterr().err


def test_the_kinds_decision_day_is_a_literal_date_call_not_a_name_of_the_tools_date():
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    value = next(
        n.value
        for n in tree.body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "KINDS_DECIDED" for t in n.targets)
    )
    assert (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id == "date"
        and all(isinstance(a, ast.Constant) for a in value.args)
    ), "KINDS_DECIDED is not a literal date(...) call: the 16 kinds would follow the tools date"


def test_the_tools_decision_day_is_the_day_the_names_and_claims_were_decided():
    # `pp.DECIDED` is the decision day of the two dated lists of the tool. It is pinned here apart from the
    # kinds (their own literal above): a renewal moves this day and the `review_by` days together, on purpose,
    # in the tool and in this test, and never moves the 16 kinds with it.
    assert pp.DECIDED == date(2026, 11, 11), "the tool's decision day moved without this test"
    left_behind = _left_behind(
        {"PENDING_NAMES": pp.PENDING_NAMES, "PENDING_CLAIMS": pp.PENDING_CLAIMS}, pp.DECIDED
    )
    assert not left_behind, (
        "renew all or none: every entry of the names and claims lists has the tool's decision day, and "
        f"these were not renewed with it: {left_behind}"
    )


def _left_behind(lists: dict[str, dict], decided: date) -> list[str]:
    """The entries (list name, kind, name) of the dated lists whose `decided` day is not `decided`: what a
    renewal of only some entries leaves behind."""
    return sorted(
        f"{name} {key[0]} {key[1]}"
        for name, lst in lists.items()
        for key, p in lst.items()
        if p.decided != decided
    )


def test_plant_a_renewal_of_only_some_entries_names_the_entry_that_was_not_renewed():
    late = DECIDED + timedelta(days=40)
    names = {
        ("secrets/vault", "kept"): pp.Pending("r", "t", DECIDED, DECIDED + timedelta(days=30)),
        ("secrets/vault", "renewed"): pp.Pending("r", "t", late, late + timedelta(days=30)),
    }
    claims = {
        ("secrets/vault", "claim kept"): pp.Pending("r", "t", DECIDED, DECIDED + timedelta(days=30))
    }
    same(
        _left_behind({"PENDING_NAMES": names, "PENDING_CLAIMS": claims}, late),
        ["PENDING_CLAIMS secrets/vault claim kept", "PENDING_NAMES secrets/vault kept"],
        "the entries left behind when only one name was renewed",
    )
    same(
        _left_behind({"PENDING_NAMES": {}, "PENDING_CLAIMS": {}}, late),
        [],
        "the entries left behind by two empty lists",
    )


def _dated(*days: date) -> dict[tuple[str, str], pp.Pending]:
    """A made-up dated list: one entry per day given, keyed apart, decided on the tool's decision day."""
    return {
        ("secrets/vault", f"made-up:{i}"): pp.Pending("r", "t", pp.DECIDED, d)
        for i, d in enumerate(days)
    }


def _review_day_page_body(marks: pp.Marks) -> None:
    """The body of the review-day page test, read from the tool's own lists (so that a plant can empty them)."""
    expected = min(
        (p.review_by for p in (*pp.PENDING_NAMES.values(), *pp.PENDING_CLAIMS.values())),
        default=None,
    )
    assert pp.review_date() == expected, (
        f"review_date() is {pp.review_date()}, the earliest day of the two lists is {expected}"
    )
    head = pp.head(marks)
    if expected is None:
        assert "no review date applies now" in head, "an empty state: the page does not say so"
    else:
        assert head.count(str(expected)) == 2, (
            f"the page head does not name the review day {expected} twice"
        )


def test_the_page_names_the_review_day_read_from_the_lists_and_not_a_day_written_in_the_test():
    _review_day_page_body(pp.read_marks(ROOT))


def test_the_page_names_the_review_day_of_the_dated_lists_and_follows_a_renewal(monkeypatch):
    # State: only the names and claims lists are renewed (made-up lists; the kinds list is not touched).
    marks = pp.read_marks(ROOT)
    old_day = pp.DECIDED + timedelta(days=30)
    monkeypatch.setattr(pp, "PENDING_NAMES", _dated(old_day))
    monkeypatch.setattr(pp, "PENDING_CLAIMS", _dated(old_day))
    before = pp.head(marks)
    assert before.count(str(old_day)) == 2, "the page head does not name the review day twice"
    new_day = pp.DECIDED + timedelta(days=60)
    monkeypatch.setattr(pp, "PENDING_NAMES", _dated(new_day))
    monkeypatch.setattr(pp, "PENDING_CLAIMS", _dated(new_day))
    after = pp.head(marks)
    assert str(old_day) not in after, (
        "the page head still names the review day from before the renewal"
    )
    assert after.count(str(new_day)) == 2, (
        "the page head does not name the renewed review day twice"
    )
    # the earliest day of the two lists is named, not the latest
    early = pp.DECIDED + timedelta(days=45)
    monkeypatch.setattr(pp, "PENDING_CLAIMS", _dated(new_day, early))
    assert pp.head(marks).count(str(early)) == 2, (
        "the page head does not name the earliest review day"
    )


def _docs_review_body(page_text: str) -> None:
    """The body of the docs-page test, for any page text (the end state gives the page it wrote)."""
    docs = " ".join(page_text.split())
    day = pp.review_date()
    if day is None:  # the end state: the page says no date applies and names no day
        assert "no review date applies now" in docs and "whichever comes first" not in docs, (
            "the docs page does not say that no review date applies"
        )
        return
    assert f"or the review date {day}, whichever comes first" in docs, (
        f"the docs page does not name the review date {day} in the trigger sentence"
    )
    assert f"(review by {day})" in docs, (
        f"the docs page does not name the review date {day} in the claims sentence"
    )
    assert docs.count(str(day)) >= 2


def test_the_docs_page_names_the_review_day_of_the_dated_lists_only():
    _docs_review_body((ROOT / "docs/declared-permissions.md").read_text(encoding="utf-8"))


def _decided_plus(days: int) -> str:
    """A day written YYYY-MM-DD, `days` after the day the dated lists were decided: the runner tests take their
    days from here, so a renewal (a new decision day) moves them with it and no test holds a day as text."""
    return (LATEST_DAY + timedelta(days=days)).isoformat()


FIXED_DAY_VAR = "HADAVIN_POLICY_FIXED_DAY"
MUTANT_RUN_VAR = "HADAVIN_POLICY_MUTANT_RUN"


def _run_day(env) -> date | None:
    """The day a mutant run fixed for this pytest run, or None. The day variable is honoured only together with the
    marker that only `tests/policy_mutants.py` sets: a developer or CI environment that holds the day variable alone
    must not switch off the date reminder, so that case is refused (the session stops with one line)."""
    day = env.get(FIXED_DAY_VAR)
    if day is None:
        return None
    if env.get(MUTANT_RUN_VAR) != "1":
        raise RuntimeError(
            f"{FIXED_DAY_VAR} is set but this is not a mutant run ({MUTANT_RUN_VAR} is not 1): unset it, "
            "only tests/policy_mutants.py --day sets it"
        )
    return date.fromisoformat(day)


@pytest.fixture(autouse=True, scope="session")
def _fixed_day_needs_the_mutant_run_marker():
    try:
        _run_day(os.environ)
    except RuntimeError as exc:
        pytest.exit(str(exc), returncode=2)


@pytest.fixture(autouse=True)
def _fixed_day_of_the_run(monkeypatch):
    """When a mutant run was given a fixed day, the tool's clock (and so `_today()`) shows it. Unset: the real clock."""
    day = _run_day(os.environ)
    if day:
        monkeypatch.setattr(pp, "datetime", _fixed_clock(day))


def test_the_day_the_tool_sees_is_the_fixed_day_the_run_was_given():
    given = _run_day(os.environ)
    seen = _today()
    if given:
        assert seen == given, (
            f"the fixed day {given} did not reach the tool's clock: it shows {seen}"
        )
    else:
        real = datetime.now(UTC).date()
        assert abs((seen - real).days) <= 1, (
            f"the tool's clock shows {seen}, the real day is {real}"
        )


def test_the_fixed_day_is_honoured_only_with_the_marker_of_the_mutant_run():
    assert _run_day({}) is None, "no day variable: the real clock"
    fixed = _decided_plus(31)
    assert _run_day({FIXED_DAY_VAR: fixed, MUTANT_RUN_VAR: "1"}) == date.fromisoformat(fixed), (
        "day and marker: the fixed day"
    )
    assert _refused_with(
        lambda: _run_day({FIXED_DAY_VAR: fixed}), RuntimeError, "not a mutant run"
    ), "a day variable without the marker was honoured"
    assert _refused_with(
        lambda: _run_day({FIXED_DAY_VAR: fixed, MUTANT_RUN_VAR: "0"}),
        RuntimeError,
        "not a mutant run",
    ), "a day variable with a marker that is not 1 was honoured"


def _date_test_problems(name: str, helper, entries: dict, monkeypatch) -> list[str]:
    """What is wrong with the date test `name` whose list is `entries` and whose problems come from `helper()`: the
    review day is the earliest day of THAT list (`pp.review_day`); on it the helper reports nothing, the day after
    it reports "overdue". A list with no entry has no review day: its helper then reports no overdue line on any
    day. The clock is set here, so a `_today()` that reads the real day is found on every run."""
    review = pp.review_day(entries)
    if review is None:
        monkeypatch.setattr(pp, "datetime", _fixed_clock(DECIDED + timedelta(days=800)))
        if any("is overdue" in p for p in helper()):
            return [f"the {name} date test reports an overdue line although its list is empty"]
        return []
    monkeypatch.setattr(pp, "datetime", _fixed_clock(review))
    found = helper()
    if found:
        return [
            f"the {name} date test reports a problem on the review day of its own list: {found}"
        ]
    monkeypatch.setattr(pp, "datetime", _fixed_clock(review + timedelta(days=1)))
    found = helper()
    if not (found and all("is overdue" in p for p in found)):
        return [
            f"the {name} date test does not go red the day after the review day of its list: it reads another clock"
        ]
    return []


def test_the_three_date_tests_read_the_clock_function_and_go_red_after_the_review_day(monkeypatch):
    # The consumers of `_today()` are the three date tests; each is checked by `_date_test_problems` against its
    # own list. Independent of the day the run was given (the clock is set inside).
    helpers = {
        "kinds": (_kinds_problems_today, PENDING_KINDS),
        "names": (_names_problems_today, PENDING_NAMES),
        "claims": (_claims_problems_today, PENDING_CLAIMS),
    }
    for name, (helper, entries) in helpers.items():
        found = _date_test_problems(name, helper, entries, monkeypatch)
        assert found == [], (
            f"{found} (the date tests do not read the clock function, or a list is wrong)"
        )


def test_the_date_test_rule_finds_an_empty_list_that_reports_and_a_list_that_never_goes_red(
    monkeypatch,
):
    # Plants for `_date_test_problems` with made-up lists and stand-in helpers (the real lists are never empty
    # today, so these branches are shown here).
    day = pp.DECIDED + timedelta(days=30)

    def overdue_from(review: date):
        return lambda: ["X is overdue (review_by)"] if _today() > review else []

    assert _date_test_problems("n", overdue_from(day), _dated(day), monkeypatch) == [], (
        "a helper that is quiet on the review day and overdue after it was refused"
    )
    assert _date_test_problems("n", lambda: ["X is overdue"], {}, monkeypatch), (
        "an empty list whose helper reports an overdue line was accepted"
    )
    assert _date_test_problems("n", list, {}, monkeypatch) == [], (
        "an empty list whose helper reports nothing was refused"
    )
    assert _date_test_problems("n", list, _dated(day), monkeypatch), (
        "a list with an entry whose helper never goes red was accepted"
    )
    assert _date_test_problems("n", lambda: ["X is overdue"], _dated(day), monkeypatch), (
        "a helper that is red on the review day itself was accepted"
    )
    assert _date_test_problems("n", lambda: ["another problem"], _dated(day), monkeypatch), (
        "a helper that reports a problem which is not an overdue line was accepted"
    )
    assert _date_test_problems(
        "n", lambda: ["another problem"] if _today() > day else [], _dated(day), monkeypatch
    ), (
        "a helper that is quiet on the review day and then reports a problem that is not an overdue line was accepted"
    )


def test_the_review_day_helper_takes_each_list_from_its_own_entries_and_has_none_for_an_empty_one():
    early, late = DECIDED + timedelta(days=20), DECIDED + timedelta(days=50)
    one, two = _dated(late), _dated(early, late)
    same(pp.review_day({}), None, "the review day of an empty list")
    same(pp.review_day({}, {}), None, "the review day of two empty lists")
    same(pp.review_day(one), late, "the review day of the one list")
    same(pp.review_day(two), early, "the earliest day of a list with two days")
    same(pp.review_day(two, latest=True), late, "the latest day of a list with two days")
    same(pp.review_day(one, two), early, "the earliest day over two lists")
    same(pp.review_day({}, one), late, "an empty list ignored beside a list with a day")


# ------------------------------------------------------------------ the runner's own rules (batch 10)


def _runner():
    from tests import policy_mutants

    return policy_mutants


def test_the_runner_refuses_a_day_argument_that_is_missing_or_not_a_day():
    runner = _runner()
    for argv in (
        ["--day"],
        ["x", "--day"],
        ["--day", ""],
        ["--day", "tomorrow"],
        ["--day", "2026-13-01"],
        ["--day", "2026-12-1"],
        ["--day", "2026-02-30"],
        ["--day", "20261212"],
        ["--day", "2026-W50-5"],
    ):
        try:
            runner.parse_args(argv)
            raised = None
        except (runner.ArgumentProblem, KeyError, IndexError, TypeError, ValueError) as exc:
            raised = exc
        assert type(raised) is runner.ArgumentProblem, (
            f"the runner takes the argument list {argv} (a --day with no real day) or fails with {raised!r} "
            "instead of one plain line"
        )
    good = _decided_plus(31)
    same(runner.parse_args(["--day", good, "D1"]), (good, ["D1"]), "a good --day")
    same(runner.parse_args(["B9"]), (None, ["B9"]), "no --day")


def test_the_probe_day_is_never_the_real_day_and_is_never_after_the_review_day():
    runner = _runner()
    review = DECIDED + timedelta(days=30)
    for offset in range(-400, 400):
        today = review + timedelta(days=offset)
        canary = runner.canary_day(today, review, DECIDED)
        assert canary != today, (
            f"the probe day is the real day {today}: a dropped clock hook would hide"
        )
        assert canary < review, f"the probe day {canary} is not before the review day {review}"


def test_the_floor_of_a_fixed_day_is_the_latest_decision_day_of_the_lists_and_the_probe_day_keeps_to_it():
    runner = _runner()
    renewed = DECIDED + timedelta(
        days=60
    )  # the kinds list alone was decided again, later than the tool's day
    kinds_only = ({"k": Pending("r", "t", renewed, renewed + timedelta(days=30))}, {}, {})
    assert runner.decided_floor(kinds_only) == renewed, (
        "the floor ignores a kinds list that was renewed alone"
    )
    assert runner.decided_floor(({}, {}, {})) == DECIDED, (
        "the floor of three empty lists is not the tool's decision day"
    )
    day_between = (
        DECIDED + timedelta(days=30)
    ).isoformat()  # after the tool's day, before the kinds decision
    raised = _parse_problem(runner, ["--day", day_between], renewed)
    assert type(raised) is runner.ArgumentProblem, (
        "a --day before the kinds decision day was taken (a day on which the kinds entry did not exist)"
    )
    assert runner.parse_args(["--day", renewed.isoformat()], renewed)[0] == renewed.isoformat(), (
        "the floor day itself was refused"
    )
    review = renewed + timedelta(days=30)
    for floor in (DECIDED, renewed, review - timedelta(days=1)):
        for offset in range(-200, 400):
            today = DECIDED + timedelta(days=offset)
            canary = runner.canary_day(today, review, floor)
            assert canary >= floor, (
                f"the probe day is before the floor {floor}: {canary} (today {today})"
            )
            assert canary != today or canary == floor == review, (
                f"the probe day is the real day {today}: a dropped clock hook would hide"
            )
            assert canary <= review, f"the probe day {canary} is after the review day {review}"
    assert runner.canary_day(DECIDED + timedelta(days=500), renewed, renewed) == renewed, (
        "the probe day is before the floor when the day before the review day is before it"
    )
    assert runner.canary_day(renewed + timedelta(days=1), None, renewed) >= renewed, (
        "with no review day the probe day is before the floor"
    )


def test_the_clock_readers_of_the_guard_file_include_the_three_date_tests():
    runner = _runner()
    readers = runner.clock_readers()
    assert set(runner.DATE_TESTS) <= readers, (
        f"a date test does not read the clock function `_today` (directly or through a helper): "
        f"{sorted(set(runner.DATE_TESTS) - readers)}"
    )


def test_the_message_scan_counts_only_assert_messages_match_and_what_texts():
    runner = _runner()
    source = (
        "def killer():\n"
        "    # needle in a comment\n"
        "    for word in ('needle in a loop literal',):\n"
        "        assert any('needle in a predicate' in p for p in []) or True\n"
        "    assert 1 == 1, 'needle in a message'\n"
        "    same(1, 1, 'needle in a what')\n"
        "    with pytest.raises(ValueError, match='needle in a match'):\n"
        "        pass\n"
    )
    found = runner.message_texts_of(source)["killer"]
    same(
        sorted(found),
        ["needle in a match", "needle in a message", "needle in a what"],
        "the texts the scan counts",
    )


# `May` is the one month name that is also an ordinary word ("7 may be"): it counts only with a capital M (or in
# capitals), or with a year after it (the extra form below)
_MONTH_NAMES = "January|Jan|February|Feb|March|Mar|April|Apr|(?-i:May|MAY)|June|Jun|July|Jul|August|Aug|September|Sept|Sep|October|Oct|November|Nov|December|Dec"
# whole month names and their short forms only: "Decision 12", "Mark 12", "Marker 5" and "Mayor 3" are not days
_MONTHS = r"\b(?:" + _MONTH_NAMES + r")\b\.?"
_ONES = "one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen"
_ORDINALS = "first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|eighteenth|nineteenth|twentieth|twenty-first|twenty-second|twenty-third|twenty-fourth|twenty-fifth|twenty-sixth|twenty-seventh|twenty-eighth|twenty-ninth|thirtieth|thirty-first"
_SPELLED = (
    r"\b(?:"
    + _ORDINALS
    + "|"
    + _ONES
    + r"|twenty(?:-(?:one|two|three|four|five|six|seven|eight|nine))?|thirty(?:-one)?)"
)
DAY_FORMS = (
    r"(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)",  # 2026-12-12
    r"(?<!\d)\d{4}/\d{2}/\d{2}(?!\d)",  # 2026/12/12
    r"(?<!\d)\d{4}\.\d{2}\.\d{2}(?!\d)",  # 2026.12.12
    r"(?<!\d)(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])(?!\d)",  # 20261212
    r"(?<!\d)\d{1,2}[/.-]\d{1,2}[/.-]\d{4}(?!\d)",  # 12/12/2026, 12.12.2026, 12-12-2026
    r"(?<!\d)\d{1,2}/\d{1,2}/\d{2}(?!\d)",  # 12/12/26 (a two-digit year with slashes only: 12.12.12 is a version)
    r"(?<!\d)\d{1,2}-\d{1,2}-\d{2}(?!\d)",  # 12-12-26 (hyphens too; a version has dots)
    r"(?<!\d)\d{1,2} \d{1,2} (?:19|20)\d{2}(?!\d)",  # 12 12 2026 (spaces)
    r"(?<!\d)\d{1,2}(?:st|nd|rd|th)?(?: of)? may(?: of)? \d{4}(?!\d)",  # 12 may 2026 (a lowercase may needs a year)
    _SPELLED + r"(?: of)? " + _MONTHS,  # twelfth of December, twelve December
    _MONTHS + r" (?:the )?" + _SPELLED + r"\b",  # December twelfth
    r"(?<!\d)\d{1,2}-" + _MONTHS + r"-\d{4}(?!\d)",  # 12-Dec-2026
    r"(?<!\d)\d{1,2}(?:st|nd|rd|th)?(?: of)? "
    + _MONTHS
    + r"(?: \d{4})?",  # 12 December, 12th of December, 12 Dec 2026
    _MONTHS
    + r" \d{1,2}(?!\d)(?:st|nd|rd|th)?\b(?:,? \d{4})?",  # Dec 12, Dec. 12, December 12th, December 12, 2026
)
DAY_PATTERN = re.compile("|".join(f"(?:{f})" for f in DAY_FORMS), re.IGNORECASE)


def stray_days(text: str, allowed: str = "") -> list[str]:
    """Every written day of `text` once the one `allowed` sentence is cut out, in any of the forms of `DAY_FORMS`
    (ISO, with slashes or dots, day-first or month-first with a month name in full or short, with or without the
    year, in any letter case): a day written as text stays wrong after a renewal."""
    flat = " ".join(text.split())
    return DAY_PATTERN.findall(flat.replace(allowed, "") if allowed else flat)


END_STATE_SOURCE = (
    "V-POL"  # a real source id of the sources file: the page then lists a real source
)


def _cleared_policy(policy: pp.Policy | None) -> pp.Policy | None:
    """One policy of the END state: every name checked, no claim left unchecked (what the person who empties the
    lists writes into the kind module)."""
    if policy is None:
        return None

    def clear(e):
        changes = {}
        if e.verified is None:
            changes["verified"] = (
                DECIDED.isoformat(),
                END_STATE_SOURCE,
            )  # a day and a source id, as the loader needs
        if e.claims_unverified:
            changes["claims_unverified"] = ()
        return dataclasses.replace(e, **changes) if changes else e

    return dataclasses.replace(
        policy,
        grants=tuple(clear(g) for g in policy.grants),
        free=tuple(clear(f) for f in policy.free),
        never=tuple(clear(n) for n in policy.never),
    )


LIST_LINES = (
    "BUILDER-ONLY",
    "PARTLY-BUILDER-ONLY",
    "CLAIM-READ-BY-BUILDER",
    "CLAIM-READ-BY-NOBODY",
)


def _head_with(text: str, **lists: str) -> str:
    """The sources file text with the value of each named list line replaced. A keyword is the name of the line
    with `_` for `-` (`CLAIM_READ_BY_BUILDER="x"`)."""
    out = []
    for ln in text.splitlines():
        tag = next((t for t in LIST_LINES if ln.startswith(f"# {t}:")), None)
        key = tag.replace("-", "_") if tag else None
        out.append(f"# {tag}: {lists[key]}" if key in lists else ln)
    return "\n".join(out) + "\n"


def _end_state(monkeypatch, root: Path) -> None:
    """The END state, written as the person who empties the lists would write it, and checked by the REAL rules:
    both dated lists empty; the four lists at the head of the sources file written as the empty marker (in the tmp
    copy `root`); every name checked and no claim left (the kind modules are read through `_cleared_policy`: the
    kind modules of today still hold unchecked entries, that is what the dated lists are for); and the notes of
    class claim or pending, whose claim or pending name is gone, moved to class code. `read_marks`,
    `claim_mark_problems`, `note_problems`, `name_pending_problems`, `claim_pending_problems`, `--check` and
    `--write` all run for real on that data. What IS replaced (six things, each by `monkeypatch`): `pp.ROOT` and
    `pp.DATA_ROOT` point at the temporary copy; `pp.PENDING_NAMES` and `pp.PENDING_CLAIMS` are empty; `pp.NOTE_CLASSES`
    has the claim and pending classes moved to code; `pp.load` (the sixth) calls the real loader first, so the
    loader reads each kind module of today and runs its own checks on it, and only then returns the policy through
    `_cleared_policy` (a `verified` made of a day and the real source id `END_STATE_SOURCE`, no unchecked claim): the
    loader's checks of `verified` therefore run on the entries as the kind modules hold them today, not on the
    cleared ones. The sources file of the copy is rewritten on disk (the four lists written as the empty
    marker), not replaced by `monkeypatch`."""
    classes = {
        k: ("code",) if v and v[0] in ("claim", "pending") else v
        for k, v in pp.NOTE_CLASSES.items()
    }
    sources = root / pp.SOURCES
    marker = pp.EMPTY_MARKER
    sources.write_text(
        _head_with(
            sources.read_text(encoding="utf-8"),
            BUILDER_ONLY=marker,
            PARTLY_BUILDER_ONLY=marker,
            CLAIM_READ_BY_BUILDER=marker,
            CLAIM_READ_BY_NOBODY=marker,
        ),
        encoding="utf-8",
    )
    real_load = pp.load
    monkeypatch.setattr(pp, "ROOT", root)
    monkeypatch.setattr(pp, "DATA_ROOT", root)
    monkeypatch.setattr(pp, "PENDING_NAMES", {})
    monkeypatch.setattr(pp, "PENDING_CLAIMS", {})
    monkeypatch.setattr(pp, "load", lambda path: _cleared_policy(real_load(path)))
    monkeypatch.setattr(pp, "NOTE_CLASSES", classes)


def test_with_both_dated_lists_empty_the_page_names_no_day_and_the_commands_still_report(
    tmp_path, monkeypatch, capsys
):
    # The end state of the ticket: nothing is waiting for a check. `review_date()` has no day then, and the page,
    # `--write` and `--check` must work and say so (a `min()` of nothing raised ValueError before). Two parts:
    # (1) with the kind modules of today (they still hold unchecked names and claims) both commands REFUSE, one
    # line per unchecked entry: that is the rule working, not a fault; (2) with the dated-list rules given the
    # policies of the end state (`_end_state`), everything else real, both commands pass on any day.
    unchecked = {(k, lab) for k, lab, e in pp.entries(_policies()) if e.verified is None}
    claimed = {(k, lab) for k, lab, e in pp.entries(_policies()) if e.claims_unverified}
    root = _tree(tmp_path)
    monkeypatch.setattr(pp, "ROOT", root)
    monkeypatch.setattr(pp, "DATA_ROOT", root)
    monkeypatch.setattr(pp, "PENDING_NAMES", {})
    monkeypatch.setattr(pp, "PENDING_CLAIMS", {})
    assert pp.main(["--write"], today=DECIDED) == 1 and not (root / pp.PAGE).exists(), (
        "--write wrote the page with both dated lists empty although the kind modules hold unchecked entries"
    )
    refused = capsys.readouterr().err.splitlines()
    assert len(refused) == len(unchecked) + len(claimed), refused
    assert all(
        "no PENDING_NAMES entry" in ln or "no PENDING_CLAIMS entry" in ln for ln in refused
    ), refused
    assert pp.main(["--check"], today=DECIDED) == 1, (
        "--check passed with both dated lists empty although the kind modules hold unchecked entries"
    )
    capsys.readouterr()
    monkeypatch.undo()
    _end_state(monkeypatch, root)
    assert pp.data_problems(root, today=DECIDED) == [], (
        "the REAL rules refuse the end state (empty marker lines, cleared policies, notes moved to class code)"
    )
    marks = pp.read_marks(root)
    assert marks == pp.Marks((), (), (), ()), f"the four lists with the marker read as {marks}"
    try:
        day = pp.review_date()
    except ValueError as exc:
        day = f"raised {exc}"
    assert day is None, f"review_date() has no answer with both dated lists empty: {day}"
    head = pp.head(marks)
    flat = " ".join(head.split())
    assert not stray_days(re.sub(r"policy_sources_[\w.-]*\.txt", "", head)), (
        "the page head names a day with both dated lists empty"
    )
    assert "a deployment chooses OpenBao; no review date applies now" in flat, (
        "the page head does not state the OpenBao trigger on its own with both dated lists empty"
    )
    assert "whichever comes first" not in head, "the page head still offers a date trigger"
    assert "No claim on this page is waiting for a check" in head, (
        "the page head does not say that no claim is waiting, with the claim marks lists empty"
    )
    assert "Some claims are weaker than that" not in head, (
        "the page head still describes unchecked claims with the claim marks lists empty"
    )
    assert "No permission name or claim is waiting" not in head, (
        "the page head keeps a sentence about a dated entry with no date to name"
    )
    assert "Each of these has a dated entry" not in head, (
        "the page head keeps the sentence about a dated entry with no date to name"
    )
    # the same two lists, but a head that still describes unchecked claims (the claim marks of today): the review
    # sentences are part of that text, so a day or a dated-entry sentence there is seen only here
    with_claims = pp.head(pp.read_marks(ROOT))
    assert "Each of these has a dated entry" not in with_claims, (
        "the page head keeps the sentence about a dated entry with no date to name (claims still listed)"
    )
    assert not stray_days(re.sub(r"policy_sources_[\w.-]*\.txt", "", with_claims)), (
        "the page head names a day with both dated lists empty (claims still listed)"
    )
    for today in (DECIDED, DECIDED + timedelta(days=800)):
        assert pp.main(["--write"], today=today) == 0, (
            f"--write stops with both dated lists empty on {today}"
        )
        assert pp.main(["--check"], today=today) == 0, (
            f"--check stops with both dated lists empty on {today}"
        )
    written = (root / pp.PAGE).read_text(encoding="utf-8")
    assert "no review date applies now" in written, (
        "the written page does not say that no review date applies"
    )
    assert "is not yet checked against the vendor's own sources" not in written, (
        "the written page withholds the copy-ready text of a kind whose names are all checked and has no claim"
    )
    capsys.readouterr()


def test_the_date_tests_branches_for_an_empty_list_run_in_the_end_state(tmp_path, monkeypatch):
    # The "no entry" branches of the date tests run on no day today (both lists hold entries): a typo in one would
    # first show on the day the lists are emptied. Each body is run once here, on the end state of `_end_state`.
    root = _tree(tmp_path)
    _end_state(monkeypatch, root)
    cleared = {k: p for k, p in pp.load_all(root).items() if p is not None}
    _claims_date_body(cleared, {})
    _review_day_page_body(pp.read_marks(root))
    _docs_review_body(pp.page(root))
    late = DECIDED + timedelta(days=800)
    declared = all_kinds() - set(NO_IDENTITY)
    same(
        kind_problems(all_kinds(), declared, {}, NO_IDENTITY, late),
        [],
        what="the pending-kinds list is empty and every kind is declared: nothing is overdue",
    )


def test_each_of_the_four_lists_may_be_the_word_none_and_an_empty_line_or_a_mixed_one_is_refused(
    tmp_path,
):
    body = _text(pp.SOURCES)
    real = pp.read_marks(ROOT)
    (tmp_path / pp.SOURCES).parent.mkdir(parents=True, exist_ok=True)

    def read(**lists: str) -> pp.Marks:
        (tmp_path / pp.SOURCES).write_text(_head_with(body, **lists), encoding="utf-8")
        return pp.read_marks(tmp_path)

    for key, attr in (
        ("BUILDER_ONLY", "builder_only"),
        ("PARTLY_BUILDER_ONLY", "partly_builder_only"),
        ("CLAIM_READ_BY_BUILDER", "builder_read"),
        ("CLAIM_READ_BY_NOBODY", "nobody_read"),
    ):
        try:
            got = read(**{key: pp.EMPTY_MARKER})
        except pp.PolicyError as exc:
            raise AssertionError(
                f"the list {key} written as the word none reads as an error: {exc}"
            ) from None
        same(getattr(got, attr), (), what=f"the list {key} written as the word none reads as")
        same(
            [a for a in vars(got) if getattr(got, a) != getattr(real, a)],
            [attr],
            what=f"the lists that differ from the real ones when only {key} is the marker",
        )
    ids = ("BUILDER_ONLY", "PARTLY_BUILDER_ONLY")
    for key in ids:
        for value, why in (
            ("", "must list source ids"),
            ("none, V-ACL", "must list source ids"),
            ("None", "must list source ids"),
        ):
            assert _refused_with(
                lambda key=key, value=value: read(**{key: value}), pp.PolicyError, why
            ), f"the source id line {key} with the value {value!r} is not refused with {why!r}"
    for key in ("CLAIM_READ_BY_BUILDER", "CLAIM_READ_BY_NOBODY"):
        assert _refused_with(
            lambda key=key: read(**{key: ""}), pp.PolicyError, "holds an empty claim text"
        ), (
            f"the claim line {key} with nothing after the colon is accepted: the word none is the only empty form"
        )
        assert _refused_with(
            lambda key=key: read(**{key: "none ;; a text"}), pp.PolicyError, "mixes the word `none`"
        ), f"the claim line {key} mixing the word none with a text is accepted"
        assert _refused_with(
            lambda key=key: read(**{key: "a text ;; none"}), pp.PolicyError, "mixes the word `none`"
        ), f"the claim line {key} ending in the word none after a text is accepted"


def test_the_empty_marker_hides_no_claim_and_a_listed_text_with_no_claim_is_stale():
    real_marks = pp.read_marks(ROOT)
    none = pp.Marks((), (), (), ())
    real = _policies()
    cleared = {k: _cleared_policy(p) for k, p in real.items()}
    claims = sum(
        len(e.claims_unverified) for p in real.values() for e in (*p.grants, *p.free, *p.never)
    )
    found = pp.claim_mark_problems(real, none)
    assert len(found) == claims and all("has 0 marks" in f for f in found), (
        f"the marker alone (no text listed) does not leave every one of the {claims} claims with no mark: {found}"
    )
    same(
        pp.claim_mark_problems(cleared, none),
        [],
        what="the marker on policies with no claim reports",
    )
    texts = len(real_marks.builder_read) + len(real_marks.nobody_read)
    stale = pp.claim_mark_problems(cleared, real_marks)
    assert len(stale) == texts and all("matches no claim: delete it" in f for f in stale), (
        f"texts listed after every claim is checked are not each reported as stale ({texts} expected): {stale}"
    )


def test_the_page_head_describes_unchecked_claims_only_while_a_claim_mark_is_listed():
    real = pp.head(pp.read_marks(ROOT))
    assert "Some claims are weaker than that" in real and "No claim on this page" not in real, (
        "with claims listed the head does not describe the unchecked claims"
    )
    none = pp.head(pp.Marks((), (), (), ()))
    assert "No claim on this page is waiting for a check" in none, (
        "with no claim listed the head does not say that no claim is waiting"
    )
    assert "Some claims are weaker than that" not in none and "CLAIM_MARKS_TEXT" not in none, (
        "with no claim listed the head keeps the description of unchecked claims"
    )
    only_nobody = pp.head(pp.Marks((), (), (), ("a text",)))
    assert "Some claims are weaker than that" in only_nobody, (
        "one list with a text and the other the marker: the head drops the description of unchecked claims"
    )


def test_the_overdue_message_says_renew_all_or_none_and_lists_everything_a_renewal_or_an_emptying_touches():
    pending = {("secrets/vault", "x"): pp.Pending("r", "t", DECIDED, DECIDED + timedelta(days=30))}
    lines = pp.pending_problems(
        "PENDING_NAMES", pending, {("secrets/vault", "x")}, DECIDED + timedelta(days=31)
    )
    assert len(lines) == 1 and "Renew all or none" in lines[0], (
        f"the overdue message does not say to renew all or none: {lines}"
    )
    assert pp.RENEWAL_STEPS in lines[0], (
        "the overdue message does not print the list of what a renewal touches"
    )
    # every file and test the list names exists, and the list names each thing the files hold
    guard = Path(__file__).read_text(encoding="utf-8")
    tool = (ROOT / "tools/policy_page.py").read_text(encoding="utf-8")
    for path in ("tools/policy_page.py", "tests/test_policy_guard.py"):
        assert path in pp.RENEWAL_STEPS and (ROOT / path).is_file(), (
            f"the renewal list names {path}"
        )
    # (the changelog file is not in the copy the mutant runner tests; tests/test_policy_changelog.py reads it)
    assert "CHANGELOG.md" in pp.RENEWAL_STEPS, "the renewal list does not name the changelog"
    pin = "test_the_tools_decision_day_is_the_day_the_names_and_claims_were_decided"
    assert pin in pp.RENEWAL_STEPS and f"def {pin}(" in guard, (
        "the renewal list names a pin test that is not there"
    )
    for token in (
        "`DECIDED`",
        "NOTE_CLASSES",
        "`_HEAD`",
        "claims_unverified",
        "`verified`",
        f"`{pp.EMPTY_MARKER}`",
        "--write",
        "notes_lines_check",
    ):
        assert token in pp.RENEWAL_STEPS, f"the renewal list does not name {token}"
    for name in ("DECIDED =", "NOTE_CLASSES", "_HEAD ="):
        assert name in tool, f"{name} is not in the tool the renewal list sends a person to"
    assert "Renew all or none" in (pp.__doc__ or ""), (
        "the tool docstring does not say renew all or none"
    )


def test_the_overdue_message_of_the_kinds_has_its_own_rule_and_steps_and_names_only_things_that_exist():
    # the 16 kinds renew on their own day (`KINDS_DECIDED`), apart from the names and claims: a message that sent a
    # person to the names and claims lists would send them to the wrong place on the first overdue day
    kind = next(iter(PENDING_KINDS))
    late = max(p.review_by for p in PENDING_KINDS.values()) + timedelta(days=1)
    lines = kind_problems(
        all_kinds(), {k for k in all_kinds() if k not in PENDING_KINDS}, PENDING_KINDS, {}, late
    )
    overdue = [ln for ln in lines if "is overdue" in ln]
    assert overdue, f"no kind is reported overdue on {late}: {lines}"
    for line in overdue:
        assert pp.KINDS_RENEWAL_RULE in line and pp.KINDS_RENEWAL_STEPS in line, (
            f"the overdue message of a kind does not carry the rule and the steps of the kinds list: {line}"
        )
        assert pp.RENEWAL_STEPS not in line and "PENDING_NAMES" not in line, (
            f"the overdue message of a kind sends a person to the names and claims lists: {line}"
        )
    assert kind in " ".join(overdue), "the kind is not named in its overdue message"
    # every thing the steps name exists where they send a person (a name that is not in the file is a wrong step)
    guard = Path(__file__).read_text(encoding="utf-8")
    pin_file = (ROOT / "tests/test_policy_changelog.py").read_text(encoding="utf-8")
    for name in ("KINDS_DECIDED", "_PR2", "PENDING_KINDS"):
        assert name in pp.KINDS_RENEWAL_STEPS or name in pp.KINDS_RENEWAL_RULE, (
            f"the kinds steps do not name {name}"
        )
        assert f"{name} =" in guard or f"{name}:" in guard, f"{name} is not in the guard file"
    for name in ("KINDS_LITERAL", "KINDS_GROUPS"):
        assert name in pp.KINDS_RENEWAL_STEPS and f"{name} =" in pin_file, (
            f"{name} is named by the kinds steps but is not in tests/test_policy_changelog.py"
        )
    pin = "test_the_sixteen_kinds_keep_a_decision_day_of_their_own_not_the_tools_date"
    assert pin in pp.KINDS_RENEWAL_STEPS and f"def {pin}(" in guard, (
        "the kinds steps name a test that is not there"
    )
    for path in ("tests/policy_mutants.py", "tests/test_policy_changelog.py", "CHANGELOG.md"):
        assert path in pp.KINDS_RENEWAL_STEPS, f"the kinds steps do not name {path}"
    assert (
        "`python tests/policy_mutants.py`" in pp.RENEWAL_STEPS and "`--day`" in pp.RENEWAL_STEPS
    ), "the renewal steps of the names and claims do not name the mutant file"
    assert (ROOT / "tests/policy_mutants.py").is_file(), (
        "the mutant file named by the steps is gone"
    )


def test_the_kinds_pin_refuses_a_moved_kind_another_built_sentence_and_an_entry_without_it():
    # the pin of the days the kinds start to fail lives in tests/test_policy_changelog.py (it reads the changelog,
    # which is not in the copy the mutant runner tests); its three refusals are shown here, on made-up input only,
    # so that a mutant of the pin has a test in this file to be killed by
    from dataclasses import replace

    from tests.test_policy_changelog import KINDS_LITERAL, _kinds_pin_problem

    entry = f"text {KINDS_LITERAL} text"
    same(
        _kinds_pin_problem(PENDING_KINDS, KINDS_LITERAL, entry), "", what="the right list and text"
    )
    first = next(iter(PENDING_KINDS))
    earliest = min(p.review_by for p in PENDING_KINDS.values())
    moved = {
        **PENDING_KINDS,
        first: replace(PENDING_KINDS[first], review_by=earliest - timedelta(days=1)),
    }
    assert "no longer holds" in _kinds_pin_problem(moved, KINDS_LITERAL, entry), (
        "a kind moved to another day was accepted by the kinds pin"
    )
    assert "not the one written in this pin" in _kinds_pin_problem(
        PENDING_KINDS, KINDS_LITERAL[:-1] + "2", entry
    ), "a built sentence with another day was accepted by the kinds pin"
    assert "does not give the days" in _kinds_pin_problem(
        PENDING_KINDS, KINDS_LITERAL, "text with no sentence"
    ), "an entry without the sentence was accepted by the kinds pin"


def test_with_one_dated_list_empty_the_page_names_the_review_day_of_the_other(monkeypatch):
    marks = pp.read_marks(ROOT)
    day = pp.DECIDED + timedelta(days=50)
    monkeypatch.setattr(pp, "PENDING_NAMES", {})
    monkeypatch.setattr(pp, "PENDING_CLAIMS", _dated(day))
    assert pp.review_date() == day, "review_date() ignores the one list that has entries"
    head = pp.head(marks)
    assert head.count(str(day)) == 2, "the page head does not name the day of the one list twice"
    monkeypatch.setattr(pp, "PENDING_NAMES", _dated(day))
    monkeypatch.setattr(pp, "PENDING_CLAIMS", {})
    assert pp.head(marks).count(str(day)) == 2, (
        "the page head does not name the day of the names list when the claims list is empty"
    )


ENTRY_START = "- **Declared permissions for three backend kinds**"


def kinds_sentence(pending: dict | None = None) -> str:
    """The one sentence of the changelog that may hold days: how many kinds start to fail from which day, built from
    the dated list itself (the day a kind fails is the day after its `review_by`), for any number of day groups:
    none ("none of them"), one ("all 16 of them from D"), two (the form the changelog holds today) or more."""
    pending = PENDING_KINDS if pending is None else pending
    groups = sorted(Counter(p.review_by for p in pending.values()).items())
    shown = [f"{n} of them from {d + timedelta(days=1)}" for d, n in groups]
    if not groups:
        return "none of them"
    if len(groups) == 1:
        return f"all {shown[0]}"
    last_n, last_d = groups[-1][1], groups[-1][0] + timedelta(days=1)
    return ", ".join(shown[:-1]) + f" and the other {last_n} from {last_d}"


def changelog_entry(text: str | None = None) -> str:
    """The entry for this work, whitespace folded: from its heading line to the next TOP-LEVEL bullet of any kind
    (a line that starts with `- `, `* `, `+ ` or a number and a point or bracket at the left edge, bold or not), the
    next heading (a line that starts with `#`) or a horizontal rule; an indented bullet inside the entry does not
    end it, and the last entry of the file ends at the end of the file. The one cut used by
    every changelog test of this folder (tests/test_policy_docs.py imports it)."""
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8") if text is None else text
    start = text.index(ENTRY_START)
    stop = re.search(
        r"\n(?:[-*+] |\d+[.)] |#|(?:-{3,}|\*{3,}|_{3,})[ \t]*(?:\n|$))", text[start + 1 :]
    )  # the next top-level bullet of any kind (also a numbered one), a heading or a horizontal rule
    end = start + 1 + stop.start() if stop else len(text)
    return " ".join(text[start:end].split())


def test_the_kinds_sentence_is_built_for_any_number_of_day_groups():
    day = DECIDED + timedelta(days=30)

    def kinds(*days: date) -> dict:
        return {f"k{i}": Pending("r", "t", DECIDED, d) for i, d in enumerate(days)}

    def nxt(n: int) -> date:
        return day + timedelta(days=n + 1)  # the day a kind fails

    assert kinds_sentence(kinds()) == "none of them", "an empty list"
    assert kinds_sentence(kinds(day, day)) == f"all 2 of them from {nxt(0)}", "one group of days"
    assert kinds_sentence(kinds(day, day, day + timedelta(days=9))) == (
        f"2 of them from {nxt(0)} and the other 1 from {nxt(9)}"
    ), "two groups of days (the form of the changelog)"
    # a renewal of some kinds only: three groups of days
    assert kinds_sentence(
        kinds(day, day + timedelta(days=9), day + timedelta(days=9), day + timedelta(days=40))
    ) == (f"1 of them from {nxt(0)}, 2 of them from {nxt(9)} and the other 1 from {nxt(40)}"), (
        "three groups of days after a renewal of some kinds"
    )


def test_a_renewal_of_some_kinds_leaves_the_changelog_rules_working():
    # State: some kinds are renewed, so the list holds three groups of days. The sentence is built from the list
    # and is the one allowed place for days; a day anywhere else is still refused.
    base = DECIDED + timedelta(days=30)
    renewed = {
        **PENDING_KINDS,
        "secrets/aws_secrets_manager": Pending("r", "t", DECIDED, base + timedelta(days=5)),
        "signer/aws_kms": Pending("r", "t", DECIDED, base + timedelta(days=9)),
    }
    sentence = kinds_sentence(renewed)
    assert len(sentence.split(" of them from ")) >= 3, f"three groups were not written: {sentence}"
    good = f"fails for {sentence}, unless renewed"
    assert stray_days(good, sentence) == [], "the allowed sentence of three groups is flagged"
    assert stray_days(good + " (review date 2026-12-11)", sentence), "a stray day was not flagged"


def test_the_entry_cut_ends_at_a_top_level_bullet_only():
    text = (
        f"{ENTRY_START} first line\n  - **a nested bold bullet** with 2026-12-11 inside\n  more text\n"
        "- **Another entry** with 2027-01-01\n"
    )
    cut = changelog_entry(text)
    assert "a nested bold bullet" in cut and "more text" in cut, (
        f"a nested bold bullet ended the entry early: {cut}"
    )
    assert "Another entry" not in cut, f"the entry runs into the next top-level bullet: {cut}"


def test_the_entry_cut_ends_at_a_plain_bullet_a_star_bullet_a_heading_and_the_end_of_the_file():
    body = f"{ENTRY_START} first line\n  - nested plain bullet\n  more text\n"
    plain = changelog_entry(body + "- A plain bullet with 2027-01-01\n")
    assert "nested plain bullet" in plain and "more text" in plain, (
        f"an indented plain bullet ended the entry early: {plain}"
    )
    assert "2027-01-01" not in plain, f"the entry runs on into a plain bullet: {plain}"
    star = changelog_entry(body + "* A star bullet with 2027-01-01\n")
    assert "2027-01-01" not in star, f"the entry runs on into a star bullet: {star}"
    heading = changelog_entry(body + "### A heading with 2027-01-01\n")
    assert "2027-01-01" not in heading, f"the entry runs on into a heading: {heading}"
    last = changelog_entry(body)
    assert last.endswith("more text"), f"the last entry of the file lost its last line: {last}"
    assert "nested plain bullet" in last, f"the last entry of the file is cut short: {last}"


# ------------------------------------------------------------------ the runner's own rules (batch 11)


def _parse_problem(runner, argv, floor=None):
    """The exception the runner raises for `argv`, or None when it takes it."""
    try:
        runner.parse_args(argv, floor)
    except (runner.ArgumentProblem, KeyError, IndexError, TypeError, ValueError) as exc:
        return exc
    return None


def test_the_runner_takes_day_in_both_written_forms_once_and_not_before_the_decision_day():
    runner = _runner()
    day, other = _decided_plus(31), _decided_plus(32)
    same(
        runner.parse_args([f"--day={day}", "D1"]),
        (day, ["D1"]),
        "the --day=VALUE form",
    )
    same(
        runner.parse_args(["D1", "--day", day]),
        (day, ["D1"]),
        "--day after a name",
    )
    same(
        runner.parse_args(["--day", LATEST_DAY.isoformat()]),
        (LATEST_DAY.isoformat(), []),
        "the decision day itself",
    )
    before = (LATEST_DAY - timedelta(days=1)).isoformat()
    raised = _parse_problem(runner, ["--day", before])
    assert type(raised) is runner.ArgumentProblem, (
        f"the runner takes a --day before the decision day ({before}) or fails with {raised!r} instead of one plain line"
    )
    raised = _parse_problem(runner, [f"--day={before}"])
    assert type(raised) is runner.ArgumentProblem, (
        f"the runner takes a --day=VALUE before the decision day ({before}) or fails with {raised!r} instead of one plain line"
    )
    raised = _parse_problem(runner, ["--day", day, f"--day={other}"])
    assert type(raised) is runner.ArgumentProblem, (
        f"the runner takes --day twice (the second written --day=VALUE) or fails with {raised!r} instead of one plain line"
    )
    raised = _parse_problem(runner, [f"--day={day}", "--day", other])
    assert type(raised) is runner.ArgumentProblem, (
        f"the runner takes --day twice (the first written --day=VALUE) or fails with {raised!r} instead of one plain line"
    )
    raised = _parse_problem(runner, ["--day="])
    assert type(raised) is runner.ArgumentProblem, (
        f"the runner takes an empty --day= value or fails with {raised!r} instead of one plain line"
    )
    raised = _parse_problem(runner, ["--day=tomorrow"])
    assert type(raised) is runner.ArgumentProblem, (
        f"the runner takes --day=tomorrow or fails with {raised!r} instead of one plain line"
    )


def test_the_runner_reads_the_failures_the_overdue_text_and_the_error_lines_of_a_pytest_run():
    runner = _runner()
    path = runner.TEST
    out = (
        f"____ test_a ____\nE   AssertionError: X is overdue (review_by {_decided_plus(30)})\n"
        "____ test_b ____\nE   AssertionError: another problem\n"
        "==== short test summary info ====\n"
        f"FAILED {path}::test_a - AssertionError: X is overdue\n"
        f"FAILED {path}::test_b - AssertionError: another problem\n"
        f"ERROR {path} - boom\n"
        "2 failed, 1 error in 0.1s\n"
    )
    got = runner.read_run(out)
    same(got.failed, {"test_a", "test_b"}, "the failed tests of the run")
    same(
        got.not_overdue,
        {"test_b"},
        "the failed tests with no overdue text (the last test must not borrow the text of the summary)",
    )
    same(got.errors, 1, "the number of ERROR lines of the run")
    same(got.last, "2 failed, 1 error in 0.1s", "the last line of the run")
    clean = runner.read_run("1 passed in 0.1s\n")
    same((clean.failed, clean.not_overdue, clean.errors), (set(), set(), 0), "a clean run")


def test_the_runner_expects_red_only_for_lists_with_entries_and_exits_1_for_a_weak_mutant():
    runner = _runner()
    kinds, names, claims = runner.date_lists()
    expect = {t for t, e in zip(runner.DATE_TESTS, (kinds, names, claims), strict=True) if e}
    same(runner.expected_red(), expect, "the date tests that must be red after the review day")
    one, none = _dated(DECIDED), {}
    same(
        runner.expected_red((one, none, one)),
        {runner.DATE_TESTS[0], runner.DATE_TESTS[2]},
        "the date tests that must be red when the names list is empty",
    )
    same(
        runner.expected_red((none, none, none)),
        set(),
        "the date tests that must be red with every list empty",
    )
    same(runner.exit_code([], []), 0, "the exit code of a run with no problem")
    same(runner.exit_code(["m"], []), 1, "the exit code with a mutant that is not good")
    same(runner.exit_code([], [("m", "e", "k")]), 1, "the exit code with a weak mutant")
    # every day here is built from the decision day and the floor is given, so that a renewal (a later decision day,
    # a later latest decision day in the lists) cannot move the answer
    today = DECIDED + timedelta(days=30)
    assert runner.canary_day(today, None, DECIDED) < today, (
        "with no review day the probe day is not before today"
    )
    same(
        runner.canary_day(today, today + timedelta(days=1), DECIDED),
        today - timedelta(days=1),
        "a day that is not today",
    )


# The functions that keep a day written on purpose, each with the reason (every other function of the policy
# test files must build a day from `DECIDED`; `test_no_test_writes_a_day_as_a_literal_inside_a_function`):
_PIN_VERIFIED = "a fixed past day on which the sources were read (data of the sources file, never a renewal day)"
_PIN_ENGINE = "a made-up day of a sample run record, not a renewal day"
_PIN_RENEWAL = "the pin of a decision day: a renewal step names it (steps of RENEWAL_STEPS and KINDS_RENEWAL_STEPS)"
_PIN_SAMPLE = "a day inside a made-up text that only has to differ from the text around it"
LITERAL_DAY_PINS = {
    (
        "tests/test_policy_guard.py",
        "test_pr1_grants_are_all_named_in_a_source_and_the_grants_with_an_unchecked_claim_are_listed",
    ): _PIN_VERIFIED,
    (
        "tests/test_policy_guard.py",
        "test_a_builder_only_source_is_marked_wherever_the_page_lists_it",
    ): _PIN_VERIFIED,
    (
        "tests/test_policy_guard.py",
        "test_plant_a_source_id_that_does_not_resolve_is_caught",
    ): _PIN_VERIFIED,
    (
        "tests/test_policy_guard.py",
        "test_plant_a_url_or_host_in_verified_is_refused",
    ): _PIN_VERIFIED,
    (
        "tests/test_policy_guard.py",
        "test_a_source_of_which_only_a_passage_was_read_is_marked_on_a_row_with_a_claim_only",
    ): _PIN_VERIFIED,
    (
        "tests/test_policy_guard.py",
        "test_plant_a_url_in_verified_is_caught_with_its_message",
    ): _PIN_VERIFIED,
    (
        "tests/test_policy_guard.py",
        "test_m1_the_page_names_the_run_once_one_is_on_record",
    ): _PIN_ENGINE,
    (
        "tests/test_policy_guard.py",
        "test_the_sixteen_kinds_keep_a_decision_day_of_their_own_not_the_tools_date",
    ): _PIN_RENEWAL,
    (
        "tests/test_policy_guard.py",
        "test_the_tools_decision_day_is_the_day_the_names_and_claims_were_decided",
    ): _PIN_RENEWAL,
    (
        "tests/test_policy_guard.py",
        "test_the_entry_cut_ends_at_a_plain_bullet_a_star_bullet_a_heading_and_the_end_of_the_file",
    ): _PIN_SAMPLE,
}


def _constant_int(node: ast.AST) -> int | None:
    """The whole number an expression of constants stands for (`12`, `10 + 1`, `-1 + 13`), else None."""
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        value = None
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult)):
        left, right = _constant_int(node.left), _constant_int(node.right)
        if left is not None and right is not None:
            return {ast.Add: left + right, ast.Sub: left - right, ast.Mult: left * right}[
                type(node.op)
            ]
    return None


def _written_day(call: ast.Call) -> date | None:
    """The day a call writes with constants: `date(2026, 12, 11)`, `date(2026, 12, 10 + 1)`,
    `date(year=2026, month=12, day=11)`, `datetime(2026, 12, 11, ...)`, `date.fromisoformat("2026-12-11")`,
    `datetime.fromisoformat(...)`; None when any part is not a constant or the call is another call."""
    name = call.func.attr if isinstance(call.func, ast.Attribute) else getattr(call.func, "id", "")
    try:
        if name in ("date", "datetime"):
            parts = [_constant_int(a) for a in call.args[:3]]
            named = {k.arg: _constant_int(k.value) for k in call.keywords if k.arg}
            for position, key in enumerate(("year", "month", "day")):
                if position >= len(call.args) and key in named:
                    parts.append(named[key])
            if len(parts) == 3 and None not in parts:
                return date(*parts)
        elif name == "fromisoformat" and len(call.args) == 1:
            text = ast.literal_eval(call.args[0])
            if isinstance(text, str):
                return datetime.fromisoformat(text).date()
    except (TypeError, ValueError, SyntaxError, MemoryError, RecursionError):
        return None
    return None


_BARE_ISO_DAY = re.compile(r"\d{4}-\d{2}-\d{2}")


def literal_day_problems(source: str, rel: str, pins: dict | None = None) -> list[str]:
    """Every day written as a literal INSIDE a function (a test or a helper) of `source`, wherever it lies
    against the decision day: a call of `date`, `datetime` or `fromisoformat` made of constants (positions or
    keywords, `10 + 1` too) and a text that is exactly one ISO day (`"2026-12-11"`). A day before the decision
    day is as wrong as one after it: after a renewal the old window is behind it and nothing tells why. A
    literal at the top level of a file is data (the kinds list, `KINDS_DECIDED`) and is named by the renewal
    steps. `pins` names the functions that keep a day on purpose, as `{(rel, function): reason}`; every such
    function is named with its reason in this file. What it does not see: a day built from text pieces
    (`"2026-" + "12-11"`), a day read from a file, a day inside a bigger text (`"on 2026-12-11 it"`, that is
    `stray_days`' job for the changelog), a day behind a name (`D = 11` then `date(2026, 12, D)`)."""
    pins = pins or {}
    out = []

    def visit(node: ast.AST, fn: str | None) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fn = node.name  # the innermost function names the day
        day = None
        if fn is not None and isinstance(node, ast.Call):
            day = _written_day(node)
        elif (
            fn is not None
            and isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and _BARE_ISO_DAY.fullmatch(node.value)
        ):
            try:
                day = date.fromisoformat(node.value)
            except ValueError:
                day = None
        if day is not None and (rel, fn) not in pins:
            out.append(f"{rel}:{node.lineno}: the day {day} is written in `{fn}`")
        for child in ast.iter_child_nodes(node):
            visit(child, fn)

    visit(ast.parse(source), None)
    return sorted(set(out))


def test_no_test_writes_a_day_of_the_renewal_window_as_a_literal_inside_a_function():
    files = sorted(
        p.relative_to(ROOT).as_posix() for p in (ROOT / "tests").glob("test_policy_*.py")
    )
    assert files, "no policy test file was found to scan"
    assert {
        "tests/test_policy_guard.py",
        "tests/test_policy_changelog.py",
        "tests/test_policy_docs.py",
        "tests/test_policy_engine.py",
    } <= set(files), "a policy test file is missing from the day scan"
    found = [
        line
        for rel in files
        for line in literal_day_problems(
            (ROOT / rel).read_text(encoding="utf-8"), rel, LITERAL_DAY_PINS
        )
    ]
    assert not found, (
        "a day is written in a function; build it from the decision day (`DECIDED + timedelta(days=...)`) "
        f"or name the function with its reason in LITERAL_DAY_PINS: {found}"
    )


def test_plant_a_written_day_in_a_function_is_found_and_a_derived_day_a_top_level_day_and_the_pin_are_not():
    d = DECIDED
    w = d + timedelta(days=20)
    before = d - timedelta(days=20)

    def body(expr: str) -> str:
        return f"def test_x():\n    assert f({expr})\n"

    def found(source: str, pins: dict | None = None) -> list[str]:
        return literal_day_problems(source, "f.py", pins)

    assert found(body(f"date({w.year}, {w.month}, {w.day})")), "a day of the window was not found"
    assert found(body(f"date({before.year}, {before.month}, {before.day})")), (
        "a day before the decision day was not found (an old literal after a renewal)"
    )
    assert found(body(f"date({d.year + 5}, 1, 1)")), "a day far outside the window was not found"
    assert found(body(f"date({w.year}, {w.month}, {w.day - 1} + 1)")), (
        "a day written as a sum of constants was not found"
    )
    assert found(body(f"date(year={w.year}, month={w.month}, day={w.day})")), (
        "a day written with keywords was not found"
    )
    assert found(body(f"datetime({w.year}, {w.month}, {w.day}, 12, 0)")), (
        "a datetime written with constants was not found"
    )
    assert found(body(f"date.fromisoformat('{w.isoformat()}')")), (
        "a day written as an ISO text for `fromisoformat` was not found"
    )
    assert found(body(f"datetime.fromisoformat('{w.isoformat()} 10:00')")), (
        "a day with a time written as an ISO text for `fromisoformat` was not found"
    )
    assert found(body(f"'{w.isoformat()}'")), "a bare ISO day text was not found"
    assert found(f"def outer():\n    def inner():\n        return '{w.isoformat()}'\n"), (
        "a day inside a nested function was not found"
    )
    assert not found(f"X = date({w.year}, {w.month}, {w.day})\nY = '{w.isoformat()}'\n"), (
        "a day written at the top level was flagged"
    )
    assert not found(body("DECIDED + timedelta(days=20)")), "a derived day was flagged"
    assert not found(body("date(2026, 13, 40)")), "an impossible day was flagged"
    pin = body(f"date({d.year}, {d.month}, {d.day})")
    assert found(pin), "a pin that is not named was accepted"
    assert not found(pin, {("f.py", "test_x"): "a pin"}), "a named pin was flagged"
    assert not found(body("'on 2026-12-11 it'")) and not found(body(f"'{w.isoformat()} it'")), (
        "a day inside a bigger text was flagged"
    )


def test_the_message_scan_counts_the_messages_of_a_helper_the_killer_calls_and_only_that():
    runner = _runner()
    source = (
        "def helper():\n"
        "    assert 1 == 1, 'needle in a helper'\n"
        "    inner()\n"
        "def inner():\n"
        "    assert 1 == 1, 'needle in an inner helper'\n"
        "def killer():\n"
        "    helper()\n"
        "    assert 1 == 1, 'needle in the killer'\n"
        "def other():\n"
        "    assert 1 == 1, 'needle in another test'\n"
        "def loop_a():\n"
        "    loop_b()\n"
        "def loop_b():\n"
        "    loop_a()\n"
        "    assert 1 == 1, 'needle in a loop'\n"
    )
    found = runner.message_texts_of(source)
    same(
        sorted(found["killer"]),
        ["needle in a helper", "needle in an inner helper", "needle in the killer"],
        "the texts the scan counts for a killer that calls a helper",
    )
    same(found["other"], ["needle in another test"], "a test that calls no helper")
    same(
        sorted(found["loop_a"]),
        ["needle in a loop"],
        "two helpers that call each other (the scan must end)",
    )


DAYS_IN_EVERY_FORM = (
    "2026-12-12",
    "2026/12/12",
    "2026.12.12",
    "12/12/2026",
    "12.12.2026",
    "12-Dec-2026",
    "12 December 2026",
    "12th Dec 2026",
    "12 December",
    "the 12th of December",
    "12 Dec",
    "Dec 12",
    "Dec. 12",
    "December 12th",
    "December 12, 2026",
    "DECEMBER 12",
    "12 DEC",
    "dec 12",
)


def test_a_day_in_any_written_form_is_found_outside_the_one_allowed_sentence():
    allowed = "all 16 of them from 2027-01-01"
    for said in DAYS_IN_EVERY_FORM:
        found = stray_days(f"text {said} text")
        assert found, f"the day written `{said}` was not found"
        assert stray_days(f"text {allowed} text {said}", allowed), (
            f"the day written `{said}` beside the allowed sentence was not found"
        )
    assert stray_days(f"text {allowed} text", allowed) == [], (
        "the allowed sentence alone is flagged"
    )
    assert stray_days("no day written here, only 16 kinds and 3 groups") == [], (
        "a text with no day is flagged"
    )


def test_each_form_of_a_written_day_is_found_and_each_miss_names_its_form():
    # one assert and one fixed message for each form: a form that stops being read is named by the failing line
    assert stray_days("on 2026-12-12 it"), "the day form year-month-day with hyphens is not found"
    assert stray_days("on 2026/12/12 it"), "the day form year-month-day with slashes is not found"
    assert stray_days("on 2026.12.12 it"), "the day form year-month-day with dots is not found"
    assert stray_days("on 12/12/2026 it"), "the day form day-month-year with slashes is not found"
    assert stray_days("on 12.12.2026 it"), "the day form day-month-year with dots is not found"
    assert stray_days("on 12-Dec-2026 it"), (
        "the day form with hyphens and a month name is not found"
    )
    assert stray_days("on 12 December 2026 it"), (
        "the day form day first with a month name and a year is not found"
    )
    assert stray_days("on 12 December it"), (
        "the day form day first with a month name and no year is not found"
    )
    assert stray_days("on the 12th of December it"), (
        "the day form with an ordinal and the word of is not found"
    )
    assert stray_days("on Dec 12 it"), "the day form month first is not found"
    assert stray_days("on Dec. 12 it"), (
        "the day form month first with a point after the month is not found"
    )
    assert stray_days("on DECEMBER 12 it"), "the day form written in capital letters is not found"
    assert stray_days("on dec 12 it"), "the day form written in small letters is not found"


def test_more_written_forms_of_a_day_are_found_and_an_ordinary_word_is_not_a_day():
    # one assert and one fixed message for each form (batch 13)
    assert stray_days("on 12-12-2026 it"), "the day form day-month-year with hyphens is not found"
    assert stray_days("on 20261212 it"), "the day form of eight digits is not found"
    assert stray_days("on 12/12/26 it"), (
        "the day form with a two-digit year and slashes is not found"
    )
    assert stray_days("on twelfth of December it"), (
        "the day form with a spelled ordinal is not found"
    )
    assert stray_days("on December the twelfth it"), (
        "the day form month first with a spelled ordinal is not found"
    )
    assert stray_days("on twelve December it"), "the day form with a spelled number is not found"
    assert stray_days("on twenty-first of March it"), (
        "the day form with a spelled compound ordinal is not found"
    )
    assert stray_days("on 12 may 2026 it"), (
        "the day form with a lowercase may and a year is not found"
    )
    assert stray_days("on 12 May it"), "the day form with May written with a capital is not found"
    assert stray_days("on May 12 it"), "the day form month first with May is not found"
    assert stray_days("on 12 MAY it"), "the day form with MAY in capitals is not found"
    for plain in (
        "7 may be",
        "this may be",
        "it may 12 times",
        "version 12.12.12",
        "id 20261399",
        "number 123456789",
    ):
        assert stray_days(f"text {plain} text") == [], (
            f"an ordinary word or number was found as a written day: {plain}"
        )


def test_a_two_digit_year_with_hyphens_and_a_day_with_spaces_are_found_and_a_version_is_not():
    assert stray_days("on 12-12-26 it"), (
        "the day form with a two-digit year and hyphens is not found"
    )
    assert stray_days("on 1-2-26 it"), "the day form with one-digit parts and hyphens is not found"
    assert stray_days("on 12 12 2026 it"), "the day form with spaces is not found"
    assert stray_days("on 3 4 1999 it"), "the day form with spaces and one-digit parts is not found"
    for plain in (
        "version 12.12.12",
        "range 12-12-261",
        "16 12 kinds",
        "page 12 12 3026",
        "12 12 20261",
    ):
        assert stray_days(f"text {plain} text") == [], (
            f"an ordinary number was found as a written day: {plain}"
        )


def test_the_changelog_entry_ends_at_a_numbered_item_and_at_a_horizontal_rule():
    body = f"{ENTRY_START} first line\n  second line\n"
    assert changelog_entry(body + "1. a numbered item\n") == changelog_entry(body), (
        "a numbered item at the left edge does not end the entry"
    )
    assert changelog_entry(body + "---\nnext\n") == changelog_entry(body), (
        "a horizontal rule at the left edge does not end the entry"
    )
    assert "second line" in changelog_entry(body + "1) item\n"), "the entry lost its own lines"
    assert "text" in changelog_entry(body + "  1. nested numbered\n  text\n"), (
        "an indented numbered item ended the entry"
    )


def test_a_word_that_only_starts_like_a_month_is_not_a_day():
    for word in (
        "Decision 12",
        "Mark 12",
        "Marker 5",
        "Mayor 3",
        "Decimal 4",
        "Augment 9",
        "version 12.12.12 of it",
        "16 kinds and 3 groups",
        "item 2026-12-123",
    ):
        assert stray_days(f"text {word} text") == [], (
            f"a word that only starts like a month was found as a written day: {word}"
        )
