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
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pytest
import yaml
from tools import policy_page as pp

from hadavin_sdk.backends import table
from hadavin_sdk.sources import kinds as source_kinds
from hadavin_sdk.sources import kubernetes as k8s
from tests.test_lockin_guard import TODAY, Pending

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "tests" / "fixtures" / "policy_sources_2026-11-11.txt"
DECIDED = date(2026, 11, 11)

# ------------------------------------------------------------------------------------- kinds: who is covered

_PR2 = ("the permission names of this kind are not all checked yet", "Q8c PR 2", date(2026, 12, 11))
_SLICE2 = ("slice 2 of Q8c: names not checked, owner questions O2 and O3 open", "Q8c slice 2")
# A kind that signs in to an outside system and has no POLICY yet. Overdue and stale entries fail.
PENDING_KINDS: dict[str, Pending] = {
    "secrets/aws_secrets_manager": Pending(_PR2[0], _PR2[1], DECIDED, _PR2[2]),
    "signer/aws_kms": Pending(_PR2[0], _PR2[1], DECIDED, _PR2[2]),
    "anchor/s3_object_lock": Pending(_PR2[0], _PR2[1], DECIDED, _PR2[2]),
    "store/postgres": Pending(_PR2[0], _PR2[1], DECIDED, _PR2[2]),
    "llm/bedrock": Pending(_PR2[0], _PR2[1], DECIDED, _PR2[2]),
    "detector/bedrock_guardrail": Pending(_PR2[0], _PR2[1], DECIDED, _PR2[2]),
    "channel/slack": Pending(
        "no Slack page could be read, so no scope name is checked", _PR2[1], DECIDED, _PR2[2]
    ),
    "secrets/azure_key_vault": Pending(*_SLICE2, DECIDED, date(2027, 1, 31)),
    "secrets/gcp_secret_manager": Pending(*_SLICE2, DECIDED, date(2027, 1, 31)),
    "signer/azure_key_vault_key": Pending(*_SLICE2, DECIDED, date(2027, 1, 31)),
    "signer/gcp_kms": Pending(*_SLICE2, DECIDED, date(2027, 1, 31)),
    "anchor/azure_immutable_blob": Pending(*_SLICE2, DECIDED, date(2027, 1, 31)),
    "anchor/gcs_retention_lock": Pending(*_SLICE2, DECIDED, date(2027, 1, 31)),
    "llm/anthropic": Pending(*_SLICE2, DECIDED, date(2027, 1, 31)),
    "llm/openai_compat": Pending(*_SLICE2, DECIDED, date(2027, 1, 31)),
    "llm/gemini": Pending(*_SLICE2, DECIDED, date(2027, 1, 31)),
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
# (kind, grant id) -> a grant whose name is not yet found in a vendor source. Empty: all six are found.
PENDING_NAMES: dict[tuple[str, str], Pending] = {}


def all_kinds() -> set[str]:
    out = {f"{family}/{name}" for family, entries in table.TABLE.items() for name in entries}
    return out | {f"source/{name}" for name in source_kinds.KINDS}


def _pending_problems(label: str, pending: dict, live: set, today: date) -> list[str]:
    out = [
        f"{label} {key} is fixed or gone: delete the entry" for key in pending if key not in live
    ]
    return out + [
        f"{label} {key} is overdue (review_by {p.review_by}): {p.fix_ref}"
        for key, p in pending.items()
        if key in live and today > p.review_by
    ]


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
    return out + _pending_problems("PENDING_KINDS", pending, kinds - declared, today)


def same(found: object, expected: object) -> None:
    """`found == expected`, with both written out in full in the failure message (pytest shortens a long
    list in the first line, and the mutant runner reads that line)."""
    assert found == expected, f"reported {found!r}, expected {expected!r}"


def _policies() -> dict[str, pp.Policy]:
    loaded = pp.load_all(ROOT)
    missing = [pp.KIND_MODULES[k] for k, p in loaded.items() if p is None]
    assert not missing, "no POLICY in " + ", ".join(missing)
    return {k: p for k, p in loaded.items() if p is not None}


def test_every_kind_is_declared_pending_or_holds_no_identity():
    declared = {k for k, p in pp.load_all(ROOT).items() if p is not None}
    problems = kind_problems(all_kinds(), declared, PENDING_KINDS, NO_IDENTITY, TODAY)
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
        DECIDED,
    )
    same(
        problems,
        ["kind secrets/new_cloud has no POLICY and is on no list: declare it or add a dated entry"],
    )


def test_plant_a_declared_kind_left_on_the_pending_list_is_caught():
    pending = {**PENDING_KINDS, "secrets/vault": Pending("r", "t", DECIDED, date(2026, 12, 11))}
    problems = kind_problems(all_kinds(), set(pp.KIND_MODULES), pending, NO_IDENTITY, DECIDED)
    same(
        problems,
        [
            "kind secrets/vault is on more than one list",
            "PENDING_KINDS secrets/vault is fixed or gone: delete the entry",
        ],
    )


def test_plant_an_overdue_pending_kind_is_caught():
    problems = kind_problems(
        all_kinds(), set(pp.KIND_MODULES), PENDING_KINDS, NO_IDENTITY, date(2026, 12, 12)
    )
    assert len(problems) == 7 and all("is overdue (review_by 2026-12-11)" in p for p in problems)


# ----------------------------------------------------------------------------------------------- A1: calls


@dataclass(frozen=True)
class Shape:
    """How one kind module writes its requests.

    `sinks`: the method names whose call sends (or passes on) a request, each with the position of the
    operation argument (None: keyword only). For Vault the verb sits one position before the path.
    `wrappers`: (enclosing function, line, sink called there). Each asserts that at that line, inside that
    function, there is a call to that sink whose operation argument is a parameter of the enclosing function
    (the function passes on what it was given). An entry with no such call there is stale and fails.
    `raw_http`: the only functions that may build a raw HTTP request.
    """

    platform: str
    sinks: dict[str, int | None]
    wrappers: frozenset[tuple[str, int, str]]
    raw_http: frozenset[str] = frozenset()


SHAPES: dict[str, Shape] = {
    "src/hadavin_sdk/actions/secrets_vault.py": Shape(
        "vault",
        {"call": 1, "authed": 1},
        frozenset({("authed", 101, "call"), ("authed", 104, "call")}),
        frozenset({"__init__", "call"}),
    ),
    # The sign-in call of this kind lives in the imported module actions/secrets_vault.py and is declared there.
    "src/hadavin_sdk/audit/signer_vault.py": Shape(
        "vault", {"call": 1, "authed": 1, "_call": 1}, frozenset({("_call", 40, "authed")})
    ),
    "src/hadavin_sdk/sources/kubernetes.py": Shape(
        "kubernetes_rbac",
        {"_fetch": None, "_call": 1, "_get": 1, "_items": 1},
        frozenset({("_call", 168, "_fetch"), ("_get", 184, "_call"), ("_items", 203, "_get")}),
    ),
}
BANNED_NAMES = {"_make_api_call", "get_waiter", "methodcaller", "__getattribute__"}
RAW_HTTP = {"Request", "urlopen", "build_opener", "HTTPConnection", "HTTPSConnection"}
_HOLE = "\x00"  # stands for the wrapper's own path parameter inside its template


def _template(node: ast.AST | None) -> str | None:
    """A path written as a literal or an f-string, folded to a template: a formatted `self.X` / `obj.X` gives
    `{X}`, a formatted bare name gives `{name}`. Anything else (a call, a conversion, a format spec, a literal
    brace) is not foldable: None."""
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
                out += "{" + value.attr + "}"
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
    for _func, node in walk.loads:
        if node.attr in shape.sinks and id(node) not in walk.called:
            out.append(
                f"{rel}:{node.lineno}: `.{node.attr}` is taken as a value, not called: the request it "
                "would send cannot be read"
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
                "parameter of that function"
            )
    problems += [
        f"{rel}: stale allowlist entry ({func}, line {line}, .{sink}): no call to `.{sink}` that passes "
        f"on a parameter of `{func}` is at that line"
        for func, line, sink in sorted(shape.wrappers - seen)
    ]
    found: dict[tuple[str, ...], list[int]] = {}
    for _func, call, sink in literal_calls:
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
            ("GET", "{mount}/data/{path_prefix}{name}"),
            ("POST", "auth/{auth_mount}/login"),
        },
        "src/hadavin_sdk/audit/signer_vault.py": {
            ("POST", "{mount}/sign/{key_name}"),
            ("GET", "{mount}/keys/{key_name}"),
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
                f"{VAULT}:{line}: request ('LIST', '{{mount}}/metadata/{{path_prefix}}') has no grant and no "
                "free entry in POLICY"
            )
        ],
    )


def test_plant_a_grant_whose_request_was_deleted_is_caught():
    problems = _planted(TRANSIT, 'self._call("GET", f"keys/{self.key_name}")', "dict(self.cached)")
    same(
        problems,
        [
            (
                f"{TRANSIT}: POLICY declares request ('GET', '{{mount}}/keys/{{key_name}}') but the module "
                "makes no such call"
            )
        ],
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
    )


def test_plant_a_stale_allowlist_line_is_caught():
    """One line added above the wrapper moves it: the entry no longer points at a call that passes its
    parameter on, and the moved call is read as a request that is not a literal."""
    problems = _planted(TRANSIT, "import base64\n", "import base64\nimport binascii\n")
    same(
        problems[:2],
        [
            (
                f"{TRANSIT}: stale allowlist entry (_call, line 40, .authed): no call to `.authed` that passes on "
                "a parameter of `_call` is at that line"
            ),
            (
                f"{TRANSIT}:41: call to `.authed` whose request is not a literal, outside the allowlisted lines: "
                "it cannot be compared with the declared list"
            ),
        ],
    )
    # with the wrapper no longer recognised, its `{mount}/` is not added, so no request matches either
    assert len(problems) == 6 and all("('POST', 'sign/{key_name}')" not in p for p in problems[:2])


def test_plant_an_allowlisted_line_that_stops_passing_its_parameter_is_caught():
    problems = _planted(
        TRANSIT,
        'self._vault.authed(method, f"{self.mount}/{path}", body)',
        'self._vault.authed(method, f"{self.mount}/keys/x", body)',
    )
    assert (
        f"{TRANSIT}:40: allowlisted call to `.authed` in `_call` does not pass on a parameter of that function"
        in problems
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
        fold('f"{self.mount}/data/{self.path_prefix}{name}"') == "{mount}/data/{path_prefix}{name}"
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
    )


def test_plant_d1_a_wildcard_resource_with_no_bound_is_caught():
    same(
        _grant_changed("secrets/vault", bound=" "),
        [
            (
                "grant R17: resource '{mount}/data/{path_prefix}*' holds a wildcard, so `bound` must say what "
                "limits it"
            )
        ],
    )
    same(
        _grant_changed("signer/vault_transit", resource="{transit_mount}/sign/?"),
        [
            "grant R18: resource '{transit_mount}/sign/?' holds a wildcard, so `bound` must say what limits it"
        ],
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
    )


def test_plant_d3_an_empty_reason_is_caught():
    same(_grant_changed("source/kubernetes", reason="  "), ["grant R20: reason is empty"])
    raw = _raw("secrets/vault")
    raw["never"] = ({**raw["never"][0], "reason": ""},)
    same(pp.problems(raw), ["never entry 0: reason is empty"])


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
    )


def test_plant_a_grant_id_used_by_two_kinds_is_caught():
    policies = _policies()
    raw = _raw("signer/vault_transit")
    raw["grants"] = ({**raw["grants"][0], "id": "R17"}, raw["grants"][1])
    policies["signer/vault_transit"] = pp.parse(f"POLICY = {raw!r}")
    same(
        pp.cross_problems(policies),
        ["grant id R17 is used by secrets/vault and by signer/vault_transit"],
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
    same(pp.problems({**raw, "deny": ()}), ["POLICY: unknown key 'deny'"])
    same(pp.problems({**raw, "platform": "aws_iam"}), ["POLICY: unknown platform 'aws_iam'"])
    same(_grant_changed("secrets/vault", no_wire="x"), ["grant R17: unknown key 'no_wire'"])
    never = ({**raw["never"][0], "type": "deny"},)
    same(pp.problems({**raw, "never": never}), ["never entry 0: unknown never type 'deny'"])
    with pytest.raises(pp.PolicyError, match="unknown key 'deny'"):
        pp.parse(f"POLICY = { ({**raw, 'deny': ()})!r}", "planted.py")
    with pytest.raises(pp.PolicyError, match="exactly once"):
        pp.parse(f"POLICY = {raw!r}\nPOLICY = {raw!r}\n", "planted.py")


def test_a_module_with_no_policy_loads_as_none(tmp_path):
    (tmp_path / "x.py").write_text('"""POLICY = {}"""\nimport os\n', encoding="utf-8")
    assert pp.load(tmp_path / "x.py") is None


# ------------------------------------------------------------------------- A4: verified names and sources


def source_ids() -> dict[str, tuple[str, str, str, str]]:
    out = {}
    for line in SOURCES.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = [p.strip() for p in line.split(" | ")]
        assert len(parts) == 5, line
        assert parts[0] not in out, parts[0]
        assert parts[1].startswith("https://") and re.fullmatch(r"[0-9a-f]{64}", parts[3]), line
        assert parts[2], line
        out[parts[0]] = (parts[1], parts[2], parts[3], parts[4])
    return out


def _all_verified(policy: pp.Policy):
    yield from ((f"grant {g.id}", g.verified) for g in policy.grants)
    yield from ((f"free entry {i}", f.verified) for i, f in enumerate(policy.free))
    yield from ((f"never {n.name}", n.verified) for n in policy.never)


def name_problems(
    policies: dict[str, pp.Policy],
    pending: dict[tuple[str, str], Pending],
    known: set[str],
    today: date,
) -> list[str]:
    """ONE rule, no time dimension: a grant with `verified = None` fails unless its (kind, id) is pending.
    Every source id must resolve in the sources file."""
    unverified = {(k, g.id) for k, p in policies.items() for g in p.grants if g.verified is None}
    out = [
        f"{kind} {gid}: the name is not found in a vendor source (verified is None) and has no "
        "PENDING_NAMES entry"
        for kind, gid in sorted(unverified - set(pending))
    ]
    out += _pending_problems("PENDING_NAMES", pending, unverified, today)
    for kind, policy in policies.items():
        for where, verified in _all_verified(policy):
            out += [
                f"{kind} {where}: source id {s} is not in the sources file"
                for s in (verified or ())[1:]
                if s not in known
            ]
    return out


def test_every_grant_name_is_verified_or_pending_and_every_source_id_resolves():
    assert name_problems(_policies(), PENDING_NAMES, set(source_ids()), TODAY) == []


def test_pr1_grants_are_all_verified_with_no_unverified_claim():
    grants = {g.id: g for p in _policies().values() for g in p.grants}
    same(sorted(grants), ["R17", "R18", "R19", "R20", "R21", "R22"])
    for g in grants.values():
        assert g.verified is not None and g.verified[0] == "2026-11-11", g.id
        assert g.claims_unverified == () and g.confirmed_live is None, g.id


def _with_grant(kind: str, **changes) -> dict[str, pp.Policy]:
    policies = _policies()
    raw = _raw(kind)
    raw["grants"] = ({**raw["grants"][0], **changes}, *raw["grants"][1:])
    policies[kind] = pp.parse(f"POLICY = {raw!r}")
    return policies


def test_plant_an_unverified_grant_with_no_pending_entry_is_caught():
    policies = _with_grant("secrets/vault", verified=None)
    same(
        name_problems(policies, {}, set(source_ids()), DECIDED),
        [
            (
                "secrets/vault R17: the name is not found in a vendor source (verified is None) and has no "
                "PENDING_NAMES entry"
            )
        ],
    )
    entry = {("secrets/vault", "R17"): Pending("r", "t", DECIDED, date(2026, 12, 11))}
    assert name_problems(policies, entry, set(source_ids()), DECIDED) == []
    overdue = name_problems(policies, entry, set(source_ids()), date(2026, 12, 12))
    assert len(overdue) == 1 and "is overdue" in overdue[0]
    stale = name_problems(_policies(), entry, set(source_ids()), DECIDED)
    same(stale, ["PENDING_NAMES ('secrets/vault', 'R17') is fixed or gone: delete the entry"])


def test_plant_a_source_id_that_does_not_resolve_is_caught():
    policies = _with_grant("secrets/vault", verified=("2026-11-11", "V-NOPE"))
    same(
        name_problems(policies, {}, set(source_ids()), DECIDED),
        ["secrets/vault grant R17: source id V-NOPE is not in the sources file"],
    )


@pytest.mark.parametrize(
    "source", ["https://developer.hashicorp.com/vault", "developer.hashicorp.com", "v-kv", ""]
)
def test_plant_a_url_or_host_in_verified_is_refused(source):
    problems = _grant_changed("secrets/vault", verified=("2026-11-11", source))
    assert len(problems) == 1 and "is not a source id" in problems[0]


def test_plant_no_copy_ready_text_for_a_kind_with_an_unverified_grant_or_claim():
    policy = _policies()["secrets/vault"]
    assert pp.copy_ready(policy)
    for changes in ({"verified": None}, {"claims_unverified": ("the bound",)}):
        changed = _with_grant("secrets/vault", **changes)["secrets/vault"]
        assert not pp.copy_ready(changed), (
            "copy-ready text is offered for a kind with an unchecked grant"
        )
        section = "\n".join(pp._kind_section("secrets/vault", VAULT, changed))
        assert "```" not in section and "No copy-ready text" in section
    section = "\n".join(
        pp._kind_section(
            "secrets/vault", VAULT, _with_grant("secrets/vault", verified=None)["secrets/vault"]
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
        "# R17: reads one named secret\n"
        'path "{mount}/data/{path_prefix}*" {\n  capabilities = ["read"]\n}\n'
    )
    assert pp.render_vault(policies["secrets/vault"], VAULT_VALUES) == (
        "# R17: reads one named secret\n"
        'path "secret/data/hadavin/acme/*" {\n  capabilities = ["read"]\n}\n'
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


def test_an_empty_vault_prefix_is_refused_and_the_page_says_so_first():
    policy = _policies()["secrets/vault"]
    with pytest.raises(
        ValueError, match="'path_prefix' is empty: an empty prefix means the whole mount"
    ):
        pp.render_vault(policy, {**VAULT_VALUES, "path_prefix": ""})
    section = pp._kind_section("secrets/vault", VAULT, policy)
    assert section[2] == pp.WHOLE_MOUNT and "every secret in the mount" in pp.WHOLE_MOUNT


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
    assert pp.main(["--check"]) == 0


def test_the_page_states_its_limits_and_offers_text_for_the_three_kinds():
    text = pp.page(ROOT)
    assert text.count("```hcl") == 2 and text.count("```yaml") == 1
    for words in (
        "No test shows that a permission NAME is right",
        "No policy on this page has been confirmed on a real account",
        "a real Vault server, in CI only",
        "no cluster in any test",
        "OpenBao was never run",
        "These 16 kinds sign in to an outside system and have no declared permission",
    ):
        assert words in text, words
    assert "smallest" not in text.lower() and "Deny" not in text


def test_plant_a_page_that_differs_from_the_data_fails_the_check(tmp_path, monkeypatch, capsys):
    (tmp_path / "docs").mkdir()
    (tmp_path / pp.PAGE).write_text(pp.page(ROOT) + "edited by hand\n", encoding="utf-8")
    real = pp.page
    monkeypatch.setattr(pp, "page", lambda: real(ROOT))
    monkeypatch.setattr(pp, "ROOT", tmp_path)
    assert pp.main(["--check"]) == 1
    assert "differs from the data" in capsys.readouterr().err
    assert pp.main(["--write"]) == 0 and pp.main(["--check"]) == 0
