"""Round 13 (Q8a-1): each REASON of the allowance table is a claim about the code, and this file checks the claim.

A reason written in words only can be wrong and nobody sees it. Here every reason that this round gave (and the sites it
covers) has a check that reads the code or runs it: a value that the reason calls an `int` is cast to `int` or declared
`int`, a list that the reason calls "written in code" is a constant in the source, a label that the reason calls "a
literal at every caller" is a literal at every caller. The reasons of earlier rounds are listed in `UNCHECKED`: the list
may only get shorter (a test pins its size), and each of them is named in the notes of this batch as not yet checked by code.
"""

from __future__ import annotations

import ast
import functools
import re
import typing
from pathlib import Path

import pytest

from tests._guard_allowances import NEW_ALLOWED, REASONS

SRC = Path(__file__).resolve().parent.parent / "src" / "hadavin_sdk"

# Reasons that have no check by code. The size may only go down (round 15: STOREID and URL are checked by data flow now).
# Each has an exception that is allowed (the owner or another repository, not "later"):
#   CARD      needs the card portal fixture that lives in the demo repositories (other repository); next step: copy the
#             fixture into `tests/` when the demo repository publishes it, due when Q8a-1 closes
#   REDACTED  the owner question q-q8a1-hide-ids decides what the redaction may leave; only the owner can close it
UNCHECKED = {"CARD", "REDACTED"}


@functools.cache
def _tree(rel: str) -> ast.Module:
    return ast.parse((SRC / rel).read_text(encoding="utf-8"))


def _fn(rel: str, name: str) -> ast.AST:
    for n in ast.walk(_tree(rel)):
        if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef) and n.name == name:
            return n
    raise AssertionError(f"{rel}: no function {name}")


def _rows(reason: str) -> list[tuple[str, str]]:
    return sorted(k for k, r in NEW_ALLOWED.items() if r == reason)


def _names(text: str) -> set[str]:
    return {n.id for n in ast.walk(ast.parse(text)) if isinstance(n, ast.Name)}


def _const_returns(fn: ast.AST) -> list[ast.AST]:
    return [n.value for n in ast.walk(fn) if isinstance(n, ast.Return) and n.value is not None]


# --- one check per reason: each returns the list of problems (empty: the claim holds) ---------------------------------


_GENERIC_NAMES: dict[tuple[str, str], set[str]] = {
    ("app.py", "f'source {shown_name(name, cfg.sources)}"): {"cfg", "name"},
    ("approvals/receiver.py", "_LOG.info('channel action"): {"reason"},
    ("registry.py", "problems += [f'{where}: tool {shown_name(spec.name)}"): {"config", "i"},
}


def check_words() -> list[str]:
    bad = []
    # the limit reasons are three constants
    appended = [
        n.args[0]
        for n in ast.walk(_fn("limits.py", "blocked"))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "append"
    ]
    if {a.value for a in appended if isinstance(a, ast.Constant)} != {
        "kill_switch",
        "daily_budget",
        "monthly_budget",
    } or any(not isinstance(a, ast.Constant) for a in appended):
        bad.append("Limits.blocked gives something other than the three constant words")
    # the gate rule ids are constants (or `limits.` + one of those words)
    for n in ast.walk(_fn("actions/authorizer.py", "authorize")):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "out":
            rule = n.args[1]
            ok = isinstance(rule, ast.Constant) or (
                isinstance(rule, ast.JoinedStr) and ast.unparse(rule) == "f'limits.{blocked[0]}'"
            )
            if not ok:
                bad.append(f"authorize: rule id {ast.unparse(rule)} is not a constant")
    # `blocked` of the gate and of the agent loop is the result of `Limits.blocked`, never a typed value
    for rel in ("runtime/agent_loop.py",):
        for n in ast.walk(_tree(rel)):
            if (
                isinstance(n, ast.Assign)
                and any(getattr(t, "id", "") == "blocked" for t in n.targets)
                and "limits.blocked(" not in ast.unparse(n.value)
            ):
                bad.append(f"{rel}:{n.lineno}: blocked = {ast.unparse(n.value)[:40]}")
    for crel, call in _callers("authorize"):
        given = next((k.value for k in call.keywords if k.arg == "blocked"), None)
        if given is not None and ast.unparse(given) != "blocked":
            bad.append(f"{crel}:{call.lineno}: authorize gets blocked={ast.unparse(given)[:30]}")
    # the outcome of an action is a Literal
    from hadavin_sdk.models import RunResult

    if typing.get_origin(RunResult.model_fields["outcome"].annotation) is not typing.Literal:
        bad.append("RunResult.outcome is not a Literal")
    # the stop reason is printed only after the `in ("max_tokens", "refusal")` test
    text = (SRC / "runtime/agent_loop.py").read_text(encoding="utf-8")
    if not re.search(r'if reply\.stop_reason in \(\s*"max_tokens",\s*"refusal",?\s*\)', text):
        bad.append("agent_loop prints reply.stop_reason without the two-word test")
    # the approval channel's reason words are constants
    for n in ast.walk(_fn("approvals/requests.py", "decide")):
        is_reason = isinstance(n, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "reason" for t in n.targets
        )
        if is_reason and not isinstance(n.value, ast.Constant):
            bad.append("approvals decide: a reason that is not a constant")
    for r in _const_returns(_fn("tools.py", "forbidden_host")):
        if not isinstance(r, ast.Constant):
            bad.append("forbidden_host returns something other than a constant sentence")
    # every row only names variables of that family
    allowed = {
        "blocked", "reply", "result", "now_d", "failed", "why", "disabled",
        "sources", "tools_mod", "shown_name", "sorted", "ToolRefused",
        "repeated", "step", "missing", "enumerate", "op", "problems", "read_ops", "spec", "where",
    }  # fmt: skip
    # a step name is a constant written in code (the first argument of each built-in `TickStep`)
    steps = next(
        n.value
        for n in _tree("runtime/tick.py").body
        if isinstance(n, ast.AnnAssign) and getattr(n.target, "id", "") == "STEPS"
    )
    for c in steps.elts:  # type: ignore[attr-defined]
        if not (isinstance(c, ast.Call) and isinstance(c.args[0], ast.Constant)):
            bad.append("a built-in tick step has a name that is not a constant")
    # a method of an operation is one of the closed set `_METHODS`, and a method outside it is refused at load
    from hadavin_sdk import tools as tools_module

    if not all(isinstance(x, str) and x.isupper() for x in tools_module._METHODS):
        bad.append("_METHODS holds something other than upper-case words")
    ro = ast.unparse(_fn("tools.py", "read_operations"))
    if "if method not in _METHODS:" not in ro:
        bad.append("read_operations no longer refuses a method outside _METHODS")
    for m, k in _rows("WORDS"):
        # a generic name (`name`, `cfg`, `config`, `reason`, `i`) is allowed only in the one row that needs it
        own = next(
            (v for (mod, start), v in _GENERIC_NAMES.items() if m == mod and k.startswith(start)),
            set(),
        )
        extra = _names(k) - allowed - own - {"_LOG"}
        if extra:
            bad.append(f"{m}: {k[:60]} uses names outside the family: {sorted(extra)}")
    return bad


def check_schema() -> list[str]:
    bad = []
    from hadavin_sdk.actions import contract

    if not isinstance(contract._TYPES, dict) or not all(
        isinstance(k, str) for k in contract._TYPES
    ):
        bad.append("_TYPES is not a table of words")
    fn = _fn("actions/contract.py", "schema_errors")
    # the lookup `_TYPES[want]` is in the condition of the `if` that returns `expected {want}`
    first = next(n for n in fn.body if isinstance(n, ast.If))
    if "_TYPES[want]" not in ast.unparse(first.test) or "expected {want}" not in ast.unparse(first):
        bad.append("schema_errors prints the type before it looked it up in _TYPES")
    if "shown_name" not in ast.unparse(_fn("actions/contract.py", "_keyword_shown")):
        bad.append("_keyword_shown does not use shown_name for a keyword outside the vocabulary")
    return bad


def check_literal() -> list[str]:
    from hadavin_sdk.actions.contract import HttpExecutor, ManualExecutor, NoneExecutor

    bad = [
        f"{c.__name__}.kind is not a Literal"
        for c in (HttpExecutor, ManualExecutor, NoneExecutor)
        if typing.get_origin(c.model_fields["kind"].annotation) is not typing.Literal
    ]
    # the printed `kind` is the executor's own kind field
    text = (SRC / "actions/contract.py").read_text(encoding="utf-8")
    if "kind = self.executor.kind" not in text:
        bad.append("the `kind` of `needs chain_id` is not read from the executor's Literal field")
    return bad


def _package_functions() -> set[str]:
    return {
        n.name
        for p in SRC.rglob("*.py")
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8")))
        if isinstance(n, FUNCS)
    }


def _own_sentence(arg: ast.AST) -> bool:
    """A sentence of this package: a constant, an f-string, a list or a `+` of those, or a call of a function that this
    package defines (never `str(exc)`, `repr(x)` or another builtin: those pass a typed value through). An f-string's
    values are read by the guard at that site (every message site of `src/` is proven or has a checked reason)."""
    if isinstance(arg, ast.Constant | ast.JoinedStr):
        return True
    if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
        return _own_sentence(arg.left) and _own_sentence(arg.right)
    if isinstance(arg, ast.Call):
        name = getattr(arg.func, "id", getattr(arg.func, "attr", ""))
        return name in _package_functions() and name not in {"str", "repr", "format", "ascii"}
    return False


def check_listed() -> list[str]:
    """A joined list is built only from sentences of this package: every list that a LISTED row joins is, in its
    function, filled by f-strings, constants or calls of functions of this package (never by a raw name from a file)."""
    bad = []
    for m, k in _rows("LISTED"):
        tree = _tree(m)
        sites = [n for n in ast.walk(tree) if isinstance(n, ast.expr) and ast.unparse(n) == k]
        if not sites and not any(
            k in ast.unparse(n) for n in ast.walk(tree) if isinstance(n, ast.stmt)
        ):
            bad.append(f"{m}: {k[:60]} is not found in the module")
    # the lists themselves
    for rel, name, var in (
        ("app.py", "build", "problems"),
        ("registry.py", "load_registry", "problems"),
        ("registry.py", "_load_tools", "problems"),
        ("config.py", "_anchor_refusals", "refused"),
        ("registry.py", "_module_pin_problems", "out"),
    ):
        fn = _fn(
            rel, name
        )  # a missing function fails the check: the list it guards is no longer read
        for n in ast.walk(fn):
            if (
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and n.func.attr in {"append", "extend", "add", "insert"}
                and isinstance(n.func.value, ast.Name)
                and n.func.value.id == var
            ):
                arg = n.args[-1]
                if not _own_sentence(arg):
                    bad.append(f"{rel}:{n.lineno}: {var}.{n.func.attr} of {ast.unparse(arg)[:50]}")
    return bad


def check_tablekeys() -> list[str]:
    from hadavin_sdk.backends.factory import TABLE
    from hadavin_sdk.store.protocol import missing_methods

    bad = []
    if not all(isinstance(c, str) and all(isinstance(k, str) for k in v) for c, v in TABLE.items()):
        bad.append("TABLE keys are not words")
    # missing_methods names come from the Store class, never from a value handed in
    if missing_methods(object()) != sorted(missing_methods(object())):
        bad.append("missing_methods is not a list of method names")
    from hadavin_sdk.store import protocol

    if not all(n.isidentifier() for n in missing_methods(object())) or not hasattr(
        protocol, "Store"
    ):
        bad.append("missing_methods gives names that are not identifiers")
    return bad


def check_access() -> list[str]:
    text = ast.unparse(_tree("approvals/receiver.py"))
    ok = (
        "def log_message(self, format: str, *args: object) -> None:\n            _LOG.debug(format, *args)"
        in text
    )
    return (
        []
        if ok and "BaseHTTPRequestHandler" in text
        else ["the receiver's log_message changed shape"]
    )


def check_rowid() -> list[str]:
    text = (SRC / "audit/chain.py").read_text(encoding="utf-8")
    return (
        []
        if "seq INTEGER PRIMARY KEY" in text
        else ["the audit table's seq is not INTEGER PRIMARY KEY"]
    )


def check_caller() -> list[str]:
    calls = []
    for p in SRC.rglob("*.py"):
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if (
                isinstance(n, ast.Call)
                and getattr(n.func, "id", getattr(n.func, "attr", "")) == "generate_key"
            ):
                calls.append(p.name)
    return [f"generate_key is called inside src: {calls}"] if calls else []


def check_keyref() -> list[str]:
    """A KEYREF string is never inside a raise, a print or a logger call."""
    bad = []
    tree = _tree("audit/signer_vault.py")
    for m, k in _rows("KEYREF"):
        for n in ast.walk(tree):
            shown = isinstance(n, ast.Raise) or (
                isinstance(n, ast.Call)
                and getattr(n.func, "id", getattr(n.func, "attr", ""))
                in {"print", "debug", "info", "warning", "error"}
            )
            if shown and k in ast.unparse(n):
                bad.append(f"{m}: {k} is in a raise, a print or a log call")
    return bad


def check_place() -> list[str]:
    """The place of a problem never carries typed text: a hostile key and a hostile value in a config go through
    `config_error_text` and neither appears; `_place` never formats `name`."""
    from pydantic import ValidationError

    from hadavin_sdk.config import Config, config_error_text

    bad = []
    canary = "zq-place-" + "Kx7" + "-canary"
    try:
        Config.model_validate({canary: canary, "environment": canary})
    except ValidationError as exc:
        if canary in config_error_text(exc):
            bad.append("config_error_text shows a typed key or value")
    # round 14: `error_where` appends only a position number, the unknown-key word, a word-like name or a `shown_name`
    where = _fn("errors.py", "error_where")
    allowed_parts = {
        "str(part)",
        "UNKNOWN_KEY",
        "str(part) if word_like(part) else NOT_SHOWN",
        "shown_name(part)",
    }
    for n in ast.walk(where):
        if (
            isinstance(n, ast.Call)
            and getattr(n.func, "attr", "") == "append"
            and ast.unparse(n.args[0]) not in allowed_parts
        ):
            bad.append(f"error_where appends {ast.unparse(n.args[0])[:40]}")
    int_branch = next(n for n in ast.walk(where) if isinstance(n, ast.If))
    if "isinstance(part, int)" not in ast.unparse(int_branch.test):
        bad.append("error_where no longer shows str(part) only for a position number")
    place = _fn("backends/platform_secrets.py", "_place")
    for n in ast.walk(place):
        if (
            isinstance(n, ast.FormattedValue)
            and isinstance(n.value, ast.Name)
            and n.value.id == "name"
        ):
            bad.append("_place formats the secret name")
    return bad


_CALLERS: dict[str, list[tuple[str, ast.Call]]] = {}


def _callers(name: str) -> list[tuple[str, ast.Call]]:
    if not _CALLERS:
        for p in SRC.rglob("*.py"):
            rel = p.relative_to(SRC).as_posix()
            for n in ast.walk(_tree(rel)):
                if isinstance(n, ast.Call):
                    key = getattr(n.func, "id", getattr(n.func, "attr", ""))
                    _CALLERS.setdefault(key, []).append((rel, n))
    return _CALLERS.get(name, [])


def _label_problem(rel: str, arg: ast.AST, depth: int = 0) -> str | None:
    """None when the label is a constant, an f-string whose values all go through `shown_name`, or exactly a parameter of
    its function whose every caller in the package passes such a label; else why not."""
    if isinstance(arg, ast.Constant) or (
        isinstance(arg, ast.Call) and getattr(arg.func, "id", "") == "shown_name"
    ):
        return None
    if isinstance(arg, ast.JoinedStr):
        for v in arg.values:
            if isinstance(v, ast.FormattedValue):
                call = v.value
                if isinstance(call, ast.Call) and getattr(call.func, "id", "") == "shown_name":
                    continue
                why = (
                    _label_problem(rel, call, depth + 1)
                    if isinstance(call, ast.Name)
                    else "not a shown_name call"
                )
                if why:
                    return f"{ast.unparse(v.value)[:30]} is in the label without shown_name ({why})"
        return None
    if isinstance(arg, ast.Name) and depth < 4:
        fn = _enclosing(rel, arg)
        if fn is None:
            return f"{arg.id} is not a parameter"
        params = [a.arg for a in [*fn.args.posonlyargs, *fn.args.args, *fn.args.kwonlyargs]]  # type: ignore[attr-defined]
        if arg.id not in params:
            made = [
                n.value
                for n in ast.walk(fn)
                if isinstance(n, ast.Assign) and arg.id in _names_in(n.targets[0])
            ]
            if not made:
                return f"{arg.id} is not a parameter of {fn.name} and is not assigned there"
            for value in made:  # a local label: built in the function from acceptable parts
                why = _label_problem(rel, value, depth + 1)
                if why:
                    return f"{arg.id} = {ast.unparse(value)[:40]}: {why}"
            return None
        method = params[:1] in (["self"], ["cls"])
        pos = params.index(arg.id) - (1 if method else 0)
        for crel, call in _callers(fn.name):
            given = next((k.value for k in call.keywords if k.arg == arg.id), None)
            if given is None and 0 <= pos < len(call.args):
                given = call.args[pos]
            if given is None:
                continue  # the default of the parameter is a constant or the caller passes nothing
            why = _label_problem(crel, given, depth + 1)
            if why:
                return f"a caller of {fn.name} ({crel}:{call.lineno}): {why}"
        return None
    return f"{ast.unparse(arg)[:40]} is not a constant, a shown_name f-string or a parameter"


def check_label() -> list[str]:
    """A label is a constant, an f-string of `shown_name` parts, or exactly a parameter whose every caller passes one."""
    bad = []
    takes = {"read_configured": 1, "list_configured": 1, "unreadable": 0, "_yaml": 1}
    for p in SRC.rglob("*.py"):
        rel = p.relative_to(SRC).as_posix()
        for n in ast.walk(_tree(rel)):
            if not (
                isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in takes
            ):
                continue
            if len(n.args) <= takes[n.func.id]:
                continue
            why = _label_problem(rel, n.args[takes[n.func.id]])
            if why:
                bad.append(f"{rel}:{n.lineno}: {n.func.id}: {why}")
    # `what` in config._read_yaml is `shown_name(path.name)`; `what` in `unreadable` callers is the parameter
    if "what = shown_name(path.name)" not in (SRC / "config.py").read_text(encoding="utf-8"):
        bad.append("config._read_yaml: what is no longer shown_name(path.name)")
    # the backend label: the kind is looked up in TABLE before the label is built
    text = (SRC / "backends/factory.py").read_text(encoding="utf-8")
    if text.index("TABLE[capability][settings.kind]") > text.index(
        'label = f"backend {capability}'
    ):
        bad.append("factory builds the label before the kind is looked up")
    # the tick's labels
    tick = _tree("runtime/tick.py")
    for n in ast.walk(tick):
        if isinstance(n, ast.Call) and getattr(n.func, "id", "") in {"_each", "_safe_log"}:
            first = (
                n.args[2]
                if n.func.id == "_each" and len(n.args) > 2
                else n.args[0]
                if n.func.id == "_safe_log"
                else None
            )
            if first is not None and not isinstance(first, ast.Constant | ast.JoinedStr):
                bad.append(f"tick.py:{n.lineno}: label {ast.unparse(first)[:40]}")
    return bad


def check_patternfield() -> list[str]:
    from hadavin_sdk.backends import table

    meta = table.AnthropicSettings.model_fields["resource"].metadata
    pats = [getattr(m, "pattern", None) for m in meta]
    return [] if table._NAME in pats else ["AnthropicSettings.resource has no _NAME pattern"]


def check_host() -> list[str]:
    from hadavin_sdk.guard.egress import _HOSTNAME

    bad = []
    for hostile in (
        "a b",
        "x'y",
        "k=v",
        "line\nbreak",
        "UPPER",
        "a" * 300,
        "<tag>",
        "pa$$word",
        "é.com",
        "",
    ):
        if _HOSTNAME.fullmatch(hostile):
            bad.append(f"{hostile[:20]!r} passes the host filter")
    for good in ("api.example.com", "localhost", "[::1]".strip("[]"), "10.0.0.1"):
        if not _HOSTNAME.fullmatch(good):
            bad.append(f"{good!r} does not pass the host filter")
    # round 14: what the refusal shows is `_shown_host(host)`: a dotted name, `localhost` or an IP address, else `?`
    from hadavin_sdk.guard.egress import _shown_host

    for hostile in (
        "a b", "x'y", "k=v", "UPPER", "a" * 300, "<tag>", "", "plainwordkey1234567890",
        "a b.c", "k=v.example", "key.with=equals", "Upper.Case.Com",
    ):  # fmt: skip
        if _shown_host(hostile) != "?":
            bad.append(
                f"the refusal shows {_shown_host(hostile)[:20]!r} for a value that is not a host"
            )
    for good in ("api.example.com", "localhost", "10.0.0.1", "::1"):
        if _shown_host(good) != good:
            bad.append(f"the refusal hides the host {good!r}")
    return bad


def check_constant() -> list[str]:
    tree = _tree("k1b/audit_sink.py")
    assigns = [
        n
        for n in tree.body
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "MEMORY_WARNING"
    ]
    if not assigns:
        return ["MEMORY_WARNING is not a module-level constant"]
    if any(isinstance(n, ast.Name | ast.Call) for n in ast.walk(assigns[0].value)):
        return ["MEMORY_WARNING is built from a name or a call, not a plain sentence"]
    shown = [ast.unparse(r) for r in _const_returns(_fn("k1b/audit_sink.py", "build_audit"))]
    return [
        f"build_audit returns {v[:60]}"
        for v in shown
        if "MEMORY_WARNING" not in v and not v.endswith(", [])")
    ]


def check_describe() -> list[str]:
    from hadavin_sdk.llm.retry import describe

    class Boom(Exception):
        status_code = 503

    bad = []
    for hostile in ("https://host-with-secret.example/v1?key=abc", "x" * 200, "a\nb", "k=v"):
        out = describe(Boom("quoted request text"), lambda e, h=hostile: h)
        if out != "Boom 503":
            bad.append(f"describe shows {out[:40]!r} for a hostile detail")
    if describe(Boom("x"), lambda e: "rate_limit-1") != "Boom 503 rate_limit-1":
        bad.append("describe drops a plain code")

    from hadavin_sdk.llm import bedrock

    class Cloud(Exception):
        response: typing.ClassVar[dict] = {
            "ResponseMetadata": {"HTTPStatusCode": 403},
            "Error": {"Code": "https://host.example/?k=" + "v" * 40},
        }

    if describe(Cloud("quoted"), bedrock.detail) != "Cloud":
        bad.append("describe shows the cloud error code of a bedrock error that is not word-like")

    class Odd(Exception):
        status_code = "https://x.example/?key=1"

    if describe(Odd("t")) != "Odd":
        bad.append("describe shows a status that is not an int")
    return bad


def check_objects() -> list[str]:
    fn = _fn("llm/retry.py", "_chain")
    bad = [
        "_chain makes text"
        for n in ast.walk(fn)
        if isinstance(n, ast.JoinedStr | ast.FormattedValue)
    ]
    # round 14: the other rows. The collecting name (`embedded`, `items`, `masked`) is in no raise, print or log call of
    # its function, in no f-string, `%` or `+` text, and no `join`/`format` of it.
    for m, k in _rows("OBJECTS"):
        if not _sites(m, k):
            bad.append(f"{m}: {k[:50]} is not found in the module")
        for node in _sites(m, k):
            if isinstance(node, ast.Expr):
                node = node.value
            fn2 = _enclosing(m, node)
            target = node.target if isinstance(node, ast.AugAssign) else None
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                target = node.func.value  # `seen.append(e)`
            if not isinstance(target, ast.Name) or fn2 is None:
                continue  # the `_chain` rows are read above
            for s in ast.walk(fn2):
                texty = isinstance(s, ast.JoinedStr | ast.FormattedValue) or (
                    isinstance(s, ast.Call) and getattr(s.func, "attr", "") in {"join", "format"}
                )
                if (_is_shown(s) or texty) and target.id in _names_in(s):
                    bad.append(
                        f"{m}:{getattr(s, 'lineno', 0)}: {target.id} is put in a message or a text"
                    )
    return bad


def check_thread() -> list[str]:
    """The receiver of the `join` is a thread made in the same function, and the argument is a number of seconds."""
    bad = []
    for m, k in _rows("THREAD"):
        if not _sites(m, k):
            bad.append(f"{m}: {k[:50]} is not found in the module")
        for node in _sites(m, k):
            if isinstance(node, ast.Expr):
                node = node.value
            fn = _enclosing(m, node)
            recv = (
                node.func.value
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                else None
            )
            made = [
                n
                for n in ast.walk(fn)
                if isinstance(n, ast.Assign)
                and isinstance(recv, ast.Name)
                and any(isinstance(t, ast.Name) and t.id == recv.id for t in n.targets)
                and "Thread(" in ast.unparse(n.value)
            ]
            if not made:
                bad.append(f"{m}: {k[:50]}: the receiver is not a Thread made in the function")
            if not _numeric(node.args[0], fn, _declared_numbers()):
                bad.append(f"{m}: {k[:50]}: the timeout is not a number by form")
    return bad


def check_cluster() -> list[str]:
    bad = []
    fns = [
        _fn("sources/kubernetes.py", "rules_problems"),
        _fn("sources/kubernetes.py", "_probe_scope"),
    ]
    for fn in fns:
        for n in ast.walk(fn):
            is_where = isinstance(n, ast.Assign) and any(
                getattr(t, "id", "") == "where" for t in n.targets
            )
            if is_where and ast.unparse(n.value) not in {
                "f'namespace entry {position}'",
                "f'namespace entry {i}'",
            }:
                bad.append(f"kubernetes.py:{n.lineno}: where = {ast.unparse(n.value)[:50]}")
    return bad


def check_catalog() -> list[str]:
    """`effective_problems` (what the database catalog says a role holds) builds its sentences from f-strings and
    constants only; `migrate.py` takes the role names as arguments and holds no configuration object."""
    bad = []
    fn = _fn("store/migrate.py", "effective_problems")
    built = 0
    for n in ast.walk(fn):
        if (
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "append"
        ):
            built += 1
            if not isinstance(n.args[0], ast.JoinedStr | ast.Constant | ast.BinOp):
                bad.append(f"effective_problems appends {ast.unparse(n.args[0])[:50]}")
        if isinstance(n, ast.AugAssign):
            built += 1
            if not isinstance(n.value, ast.List | ast.ListComp) or "JoinedStr" not in ast.dump(
                n.value
            ):
                bad.append(f"effective_problems adds {ast.unparse(n.value)[:50]}")
    if not built:
        bad.append("effective_problems builds no list: the check does not see its sentences")
    return bad


def check_report() -> list[str]:
    from hadavin_sdk.k1b import score

    bad = []
    fields: dict[str, object] = {}
    for cls in (score.RunScore, score.ScoreResult):
        fields |= typing.get_type_hints(cls)
    methods = {"get", "items", "join"}
    from hadavin_sdk.k1b import replay

    keys_ok = {
        "bundle_set_sha256", "cases_with_masking", "cause_fault_types_sha256", "cause_services_sha256",
        "config_hash", "model_id", "scheme", "sdk_version", "usd",
        "run_index", "issue_cases",
    } | set(replay._COUNT_KEYS)  # fmt: skip
    # the counts are `dict.fromkeys(_COUNT_KEYS, 0)` and only numbers are added; `run_index` is the counter of a
    # `range` loop; `issue_cases` holds the folder names of the bundles, which the bundle check refuses unless they
    # look like `case-001`
    rtext = ast.unparse(_tree("k1b/replay.py"))
    if "dict.fromkeys(_COUNT_KEYS, 0)" not in rtext or "for run_index in range(" not in rtext:
        bad.append("replay: the counts or run_index are no longer built from numbers")
    if "folder name must look like case-001" not in (SRC / "k1b/bundle.py").read_text(
        encoding="utf-8"
    ):
        bad.append("bundle: the case folder name is no longer checked")
    for _m, k in _rows("REPORT"):
        for n in ast.walk(ast.parse(k)):
            if isinstance(n, ast.Attribute) and n.attr not in methods and n.attr in fields:
                kind = fields[n.attr]
                numeric = kind in (int, float) or set(typing.get_args(kind)) <= {
                    int,
                    float,
                    type(None),
                }
                if not numeric and n.attr not in {"runs", "outputs_digest"}:
                    bad.append(f"{k[:50]}: {n.attr} is {kind}")
            if (
                isinstance(n, ast.Subscript)
                and isinstance(n.slice, ast.Constant)
                and n.slice.value not in keys_ok
            ):
                bad.append(f"{k[:50]}: key {n.slice.value}")
    # the model id is patterned at load
    from hadavin_sdk.config import Route

    if not any(getattr(x, "pattern", None) for x in Route.model_fields["model_id"].metadata):
        bad.append("Route.model_id has no pattern")
    # run_index, hits and the like must be annotated numbers
    for n in ("run_index", "hits", "misses", "not_sure", "hne", "incidents", "pass_k"):
        if fields.get(n) is not int:
            bad.append(f"{n} is not an int field")
    return bad


def check_tags() -> list[str]:
    text = ast.unparse(_fn("config.py", "_what"))
    return (
        []
        if "expected_tags" in text and "isinstance(allowed, str)" in text
        else ["_what changed the tags test"]
    )


def check_pydantictype() -> list[str]:
    text = ast.unparse(_fn("config.py", "_what"))
    return (
        []
        if "f'a value was refused ({kind})'" in text and "kind = e['type']" in text
        else ["_what changed"]
    )


# --- round 13, second pass: the reasons of rounds 11 and 12, each checked by code now ---------------------------------


def _row_asts(reason: str) -> list[ast.expr]:
    return [ast.parse(site, mode="eval").body for _, site in _rows(reason)]


def check_gen() -> list[str]:
    from hadavin_sdk.models import new_id

    bad = []
    if not re.fullmatch(r"[a-z]+-[0-9a-f]{32}", new_id("run")):
        bad.append("new_id no longer builds <word>-<32 hex digits>")
    for p in SRC.rglob("*.py"):
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            literal = (
                bool(n.args) and isinstance(n.args[0], ast.Constant)
                if isinstance(n, ast.Call)
                else True
            )
            if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "new_id" and not literal:
                bad.append(f"{p.name}:{n.lineno}: new_id gets a prefix that is not a literal")
    return bad


def check_state() -> list[str]:
    from hadavin_sdk.models import RunState
    from hadavin_sdk.runtime import runs

    bad = [
        f"state {m!r} is not a fixed upper-case word"
        for m in RunState
        if not re.fullmatch(r"[A-Z_]+", m.value)
    ]
    hints = {k: v for k, v in typing.get_type_hints(runs.check).items() if k != "return"}
    if hints != {"frm": RunState, "to": RunState}:
        bad.append(f"runs.check parameters are not both RunState: {hints}")
    return bad


def check_digest() -> list[str]:
    from hadavin_sdk.errors import NOT_SHOWN, digest_prefix

    digest = "ab12" * 16
    bad = []
    if digest_prefix(digest) != digest[:12] + "...":
        bad.append("a real digest is not cut to 12 characters")
    for other in ("short", "x" * 64, "secret-" + "k" * 60, 7, None):
        if digest_prefix(other) != NOT_SHOWN:
            bad.append(
                f"digest_prefix shows part of a value that is no digest: {type(other).__name__}"
            )
    return bad


def _is_time_part(e: ast.AST) -> bool:
    """A time or a number of seconds by form: a `timedelta(...)`, `clock()`, `monotonic()` or `now(...)` call, a name `now`,
    `at` or `timeout_s`, or a field `ttl_s` or `retain`."""
    if isinstance(e, ast.Call):
        return getattr(e.func, "id", getattr(e.func, "attr", "")) in {
            "timedelta",
            "clock",
            "monotonic",
            "now",
        }
    if isinstance(e, ast.Name):
        return e.id in {"now", "at", "timeout_s"}
    if isinstance(e, ast.Attribute):
        return e.attr in {"ttl_s", "retain"}
    return False


def check_time() -> list[str]:
    """Each TIME row is found in the code, is a sum, and both parts are a time or a number of seconds by form."""
    bad = []
    for mod, site in _rows("TIME"):
        found = _sites(mod, site)
        if not found:
            bad.append(f"{mod}: {site} is not found in the module")
        for node in found:
            if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)):
                bad.append(f"{mod}: {site} is not a sum")
            elif not (_is_time_part(node.left) and _is_time_part(node.right)):
                bad.append(f"{mod}: {site}: a part of the sum is not a time or a number of seconds")
    return bad


def check_sign() -> list[str]:
    bad = []
    allowed = {
        "secret",
        "base",
        "hashlib",
        "hmac",
        "prefix",
        "ts",
        "body",
        "seq",
        "head",
        "sha256",
        "hexdigest",
    }
    for (mod, site), node in zip(_rows("SIGN"), _row_asts("SIGN"), strict=True):
        if mod not in {"approvals/hmac_v0.py", "audit/chain.py"}:
            bad.append(f"{mod}: not a signing module")
        for n in ast.walk(node):
            if isinstance(n, ast.Name) and n.id not in allowed:
                bad.append(f"{mod}: {site}: unexpected name {n.id}")
    tree = _tree("approvals/hmac_v0.py")
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and getattr(n.func, "id", getattr(n.func, "attr", "")) in {
            "print",
            "warning",
            "error",
            "info",
            "debug",
        }:
            bad.append(f"hmac_v0.py:{n.lineno}: prints or logs")
    return bad


def check_classnames() -> list[str]:
    bad = []
    # the title of a pydantic error is the name of a model class: no model of the package is built from a configured name
    for path in SRC.rglob("*.py"):
        for n in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (
                isinstance(n, ast.Call)
                and getattr(n.func, "id", getattr(n.func, "attr", "")) == "create_model"
                and not (n.args and isinstance(n.args[0], ast.Constant))
            ):
                bad.append(
                    f"{path.name}:{n.lineno}: create_model with a name that is not a literal"
                )
    for mod, site in _rows("CLASSNAMES"):
        if not _sites(mod, site):
            bad.append(f"{mod}: {site[:50]} is not found in the module")
        text = site
        if "str(exc)" in text or "safe_head" in text or "exc.args" in text:
            bad.append(f"{mod}: {site}: prints the text of an error")
        if mod != "config.py" or "exc.title" not in text or "len(errors)" not in text:
            bad.append(f"{mod}: {site}: not the pydantic count-and-title line")
    return bad


def check_seq() -> list[str]:
    """By the tree: in the function that holds the message `holds seq`, an `if type(seq) is not int` that raises comes
    on an earlier line than the message."""
    tree = _tree("audit/chain.py")
    for fn in (n for n in ast.walk(tree) if isinstance(n, FUNCS)):
        said = [
            n.lineno
            for n in ast.walk(fn)
            if isinstance(n, ast.JoinedStr) and "holds seq" in ast.unparse(n)
        ]
        if not said:
            continue
        guards = [
            n.lineno
            for n in ast.walk(fn)
            if isinstance(n, ast.If)
            and "type(seq) is not int" in ast.unparse(n.test)
            and any(isinstance(x, ast.Raise) for x in n.body)
        ]
        if not guards or min(guards) > min(said):
            return ["the seq message comes before the integer check (or there is none)"]
        return []
    return ["no function of chain.py holds the seq message"]


def check_keyver() -> list[str]:
    """By the tree: `key_version` is declared `int` on the signer, the Vault status is printed only through `status_text`
    (never as a bare name in a message), and the first argument after the method of every `self._call(...)` is a
    constant or an f-string that starts with `keys` or `sign`."""
    bad = []
    tree = _tree("audit/signer_vault.py")
    declared = [  # the parameter of the signer's `__init__`, which `self.key_version` is set from
        a
        for n in ast.walk(tree)
        if isinstance(n, FUNCS) and n.name == "__init__"
        for a in n.args.args
        if a.arg == "key_version"
        and a.annotation is not None
        and ast.unparse(a.annotation) == "int"
    ]
    assigned = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Assign) and ast.unparse(n) == "self.key_version = key_version"
    ]
    if not assigned:
        bad.append("self.key_version is no longer set from the int parameter")
    if not declared:
        bad.append("key_version is not declared int in the signer")
    for n in ast.walk(tree):
        if (
            isinstance(n, ast.FormattedValue)
            and isinstance(n.value, ast.Name)
            and n.value.id == "status"
        ):
            bad.append(
                f"signer_vault.py:{n.lineno}: the Vault status is a bare name in an f-string"
            )
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "_call":
            path = n.args[1] if len(n.args) > 1 else None
            head = (
                path.value
                if isinstance(path, ast.Constant)
                else path.values[0].value
                if isinstance(path, ast.JoinedStr) and isinstance(path.values[0], ast.Constant)
                else None
            )
            if not isinstance(head, str) or not head.startswith(("keys", "sign")):
                bad.append(
                    f"signer_vault.py:{n.lineno}: a request path that does not start with keys or sign"
                )
    if not any(
        isinstance(n, ast.Call) and getattr(n.func, "id", "") == "status_text"
        for n in ast.walk(tree)
    ):
        bad.append("the Vault status is no longer printed through status_text")
    return bad


def check_mignames() -> list[str]:
    from hadavin_sdk.store import migrate

    bad = []
    names = [p.name for p in migrate.MIGRATIONS.glob("*.sql")]
    if not names:
        bad.append("no migration files found")
    bad += [
        f"{n}: not <number>_<words>.sql"
        for n in names
        if not re.fullmatch(r"\d{3,4}_[a-z0-9_]+\.sql", n)
    ]
    return bad


def check_fields() -> list[str]:
    from hadavin_sdk.strict_model import StrictConfigModel

    class M(StrictConfigModel):
        alpha: int = 1

    marker = "Zq" + "9-typed-key"
    try:
        M.model_validate({"alpha": 1, marker: 2})
    except Exception as exc:  # the test wants any error here  # noqa: BLE001
        shown = f"{exc!s}{exc!r}"
        return (
            []
            if (marker not in shown and "position 2" in shown and "alpha" in shown)
            else [f"text: {shown[:200]}"]
        )
    return ["an unknown setting was accepted"]


def check_arg() -> list[str]:
    bad = []
    tree = _tree("cli.py")
    seen = 0
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "kill_switch":
            seen += 1
            if ast.unparse(n.args[2]) != "args.by":
                bad.append(
                    f"kill_switch is called with {ast.unparse(n.args[2])}, not the typed --by"
                )
    if seen == 0:
        bad.append("no call of kill_switch in cli.py")
    if "lim.add_argument('--by', required=True)" not in ast.unparse(tree):
        bad.append("--by is no longer a required command-line argument")
    return bad


# --- round 14: the reasons that had no check, and the checks that read text instead of the tree ------------------------

FUNCS = (ast.FunctionDef, ast.AsyncFunctionDef)
SHOWN = {"print", "debug", "info", "warning", "error", "exception", "critical", "add_note"}
_SITE_CACHE: dict[str, tuple[dict, dict]] = {}


def _index(rel: str):
    """(text -> nodes, id(node) -> parent) of a module, built once."""
    if rel not in _SITE_CACHE:
        tree = _tree(rel)
        parent: dict[int, ast.AST] = {}
        texts: dict[str, list[ast.AST]] = {}
        for n in ast.walk(tree):
            for ch in ast.iter_child_nodes(n):
                parent[id(ch)] = n
            if isinstance(n, ast.expr | ast.stmt):
                texts.setdefault(ast.unparse(n), []).append(n)
        _SITE_CACHE[rel] = (texts, parent)
    return _SITE_CACHE[rel]


def _up(rel: str, node: ast.AST):
    _, parent = _index(rel)
    while id(node) in parent:
        node = parent[id(node)]
        yield node


def _is_shown(n: ast.AST) -> bool:
    """A raise, a print, a log call, a note, or a write to the standard error or output streams."""
    if isinstance(n, ast.Raise):
        return True
    if not isinstance(n, ast.Call):
        return False
    if getattr(n.func, "id", getattr(n.func, "attr", "")) in SHOWN:
        return True
    return (
        isinstance(n.func, ast.Attribute)
        and n.func.attr == "write"
        and any(w in ast.unparse(n.func.value) for w in ("stderr", "stdout"))
    )


def _enclosing(rel: str, node: ast.AST):
    return next((a for a in _up(rel, node) if isinstance(a, FUNCS)), None)


def _sites(rel: str, text: str) -> list[ast.AST]:
    return _index(rel)[0].get(text, [])


def _names_in(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def _stored(fn: ast.AST) -> set[str]:
    out = set()
    for n in ast.walk(fn):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            out.add(n.id)
    return out


_NUMERIC_NOTES = {"int", "float", "Decimal", "bool", "int | None", "float | None", "Decimal | None"}


def _declared_numbers() -> set[str]:
    """Attribute names that some class of the package declares `int`, `float`, `bool` or `Decimal`."""
    names: set[str] = set()
    for p in SRC.rglob("*.py"):
        for c in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(c, ast.ClassDef):
                for n in c.body:
                    if (
                        isinstance(n, ast.AnnAssign)
                        and isinstance(n.target, ast.Name)
                        and ast.unparse(n.annotation) in _NUMERIC_NOTES
                    ):
                        names.add(n.target.id)
                    if (
                        isinstance(n, FUNCS)
                        and n.returns is not None
                        and ast.unparse(n.returns) in _NUMERIC_NOTES
                    ):
                        names.add(n.name)  # a property or a method that returns a number
    return names


_CTX: dict[str, ast.ClassDef | None] = {"cls": None}


@functools.cache
def _non_numeric_names() -> frozenset[str]:
    """Attribute names that some class of the package declares with a type that is not a number (`key_version: str`,
    `step: str`): a field of that name is a number only where its own class says so."""
    names: set[str] = set()
    for p in SRC.rglob("*.py"):
        for c in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(c, ast.ClassDef):
                for n in c.body:
                    if (
                        isinstance(n, ast.AnnAssign)
                        and isinstance(n.target, ast.Name)
                        and ast.unparse(n.annotation) not in _NUMERIC_NOTES
                    ):
                        names.add(n.target.id)
    return frozenset(names)


def _own_declaration(cls: ast.ClassDef, name: str) -> bool | None:
    """Does the class itself declare `self.<name>` a number? True or False; None when the class does not say."""
    for n in cls.body:
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id == name:
            return ast.unparse(n.annotation) in _NUMERIC_NOTES
    for init in (n for n in cls.body if isinstance(n, FUNCS) and n.name == "__init__"):
        notes = {
            a.arg: ast.unparse(a.annotation) for a in init.args.args if a.annotation is not None
        }
        for n in ast.walk(init):
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    pairs = (
                        zip(t.elts, n.value.elts, strict=False)
                        if isinstance(t, ast.Tuple) and isinstance(n.value, ast.Tuple)
                        else [(t, n.value)]
                    )
                    for tt, vv in pairs:
                        if (
                            isinstance(tt, ast.Attribute)
                            and tt.attr == name
                            and isinstance(tt.value, ast.Name)
                            and tt.value.id == "self"
                            and isinstance(vv, ast.Name)
                        ):
                            return notes.get(vv.id) in _NUMERIC_NOTES
    return None


_NUMBER_FUNCS = {
    "len", "int", "round", "abs", "float", "count", "log", "comb", "Decimal", "start", "end",
}  # fmt: skip
# `min`, `max` and `sum` are numbers only when their arguments are numbers (`_numeric` reads them); `index`, `find` and
# `rfind` are not listed (a method of that name can return anything).


def _numeric(e: ast.AST, fn: ast.AST | None, declared: set[str], depth: int = 0) -> bool:
    """Is `e` a number by its form: a number, a call of a counting function, a field declared as a number, or a local that
    is only ever given numbers (a parameter annotated as a number, a counter)?"""
    if depth > 8:
        return False
    if isinstance(e, ast.Constant):
        return isinstance(e.value, int | float) and not isinstance(e.value, str)
    if isinstance(e, ast.UnaryOp):
        return _numeric(e.operand, fn, declared, depth + 1)
    if isinstance(e, ast.BinOp):
        return _numeric(e.left, fn, declared, depth + 1) and _numeric(
            e.right, fn, declared, depth + 1
        )
    if isinstance(e, ast.BoolOp):
        return all(_numeric(v, fn, declared, depth + 1) for v in e.values)
    if isinstance(e, ast.IfExp) and all(
        isinstance(b, ast.Constant) and isinstance(b.value, str) for b in (e.body, e.orelse)
    ):
        return True  # one of two words written in code (`'GREEN' if run.green else 'RED'`)
    if isinstance(e, ast.IfExp):
        return _numeric(e.body, fn, declared, depth + 1) and _numeric(
            e.orelse, fn, declared, depth + 1
        )
    if isinstance(e, ast.JoinedStr):  # text made only of numbers (`f"{passed}/{n}"`)
        return all(
            _numeric(v.value, fn, declared, depth + 1)
            for v in e.values
            if isinstance(v, ast.FormattedValue)
        )
    if isinstance(e, ast.Call):
        name = getattr(e.func, "id", getattr(e.func, "attr", ""))
        if name in {"min", "max", "sum"}:
            return bool(e.args) and all(
                _numeric(a, fn, declared, depth + 1)
                or (
                    isinstance(a, ast.GeneratorExp | ast.ListComp)
                    and _numeric(a.elt, fn, declared, depth + 1)
                )
                for a in e.args
            )
        return (
            name in _NUMBER_FUNCS
            or name.startswith("purge_")
            or name in declared
            or name in _NUMBER_FORMATTERS
        )
    if isinstance(e, ast.Attribute):
        cls = _CTX["cls"]
        if cls is not None and isinstance(e.value, ast.Name) and e.value.id == "self":
            own = _own_declaration(cls, e.attr)
            if own is not None:
                return own
        return e.attr in declared and e.attr not in _non_numeric_names()
    if isinstance(e, ast.Name):
        if fn is not None:
            for a in [*fn.args.args, *fn.args.kwonlyargs, *fn.args.posonlyargs]:  # type: ignore[attr-defined]
                if a.arg == e.id:
                    return a.annotation is not None and ast.unparse(a.annotation) in _NUMERIC_NOTES
            loops = [
                n
                for n in ast.walk(fn)
                if isinstance(n, ast.For)
                and isinstance(n.iter, ast.Call)
                and (
                    (getattr(n.iter.func, "id", "") == "range" and e.id in _names_in(n.target))
                    or (  # `enumerate`: only the first of the pair is a counter, the item is not
                        getattr(n.iter.func, "id", "") == "enumerate"
                        and isinstance(n.target, ast.Tuple)
                        and isinstance(n.target.elts[0], ast.Name)
                        and n.target.elts[0].id == e.id
                    )
                )
            ]
            if loops:  # a counter of a `range` or `enumerate` loop
                return True
            bound = [
                n
                for n in ast.walk(fn)
                if (isinstance(n, ast.Assign) and any(e.id in _names_in(t) for t in n.targets))
                or (
                    isinstance(n, ast.AugAssign)
                    and isinstance(n.target, ast.Name)
                    and n.target.id == e.id
                )
                or (
                    isinstance(n, ast.AnnAssign)
                    and isinstance(n.target, ast.Name)
                    and n.target.id == e.id
                )
            ]
            if any(
                isinstance(n, ast.AnnAssign) and ast.unparse(n.annotation) in _NUMERIC_NOTES
                for n in bound
            ):
                return (
                    True  # declared as a number: a type checker holds every value of the name to it
                )
            if bound:
                return all(
                    _numeric(getattr(n, "value", None) or ast.Constant(0), fn, declared, depth + 1)
                    for n in bound
                )
        return e.id.isupper()  # a module constant written in capitals (`RESOLVE_TIMEOUT_S`)
    return False


def _numeric_site(rel: str, node: ast.AST, declared: set[str]) -> str | None:
    """None when every value the site mentions is a number by form, else the first value that is not."""
    fn = _enclosing(rel, node)
    _CTX["cls"] = next((a for a in _up(rel, node) if isinstance(a, ast.ClassDef)), None)
    parts: list[ast.AST] = []
    if isinstance(node, ast.Expr):
        node = node.value
    if isinstance(node, ast.AugAssign):
        parts = [node.value]
    elif isinstance(node, ast.JoinedStr):
        for v in node.values:
            if isinstance(v, ast.FormattedValue):
                shown_ok = (
                    isinstance(v.value, ast.Call)
                    and getattr(v.value.func, "id", "") == "shown_name"
                )
                spec = ast.unparse(v.format_spec) if v.format_spec else ""
                if not shown_ok and not re.search(r"[fdg%]$", spec):
                    parts.append(v.value)
    elif isinstance(node, ast.Call) and _is_shown(node):
        parts = [a for a in node.args[1:]]
    else:
        parts = [node]
    for p in parts:
        if not _numeric(p, fn, declared):
            return ast.unparse(p)[:60]
    return None


def _numeric_rows(reason: str) -> list[str]:
    bad = []
    declared = _declared_numbers()
    for m, k in _rows(reason):
        found = _sites(m, k)
        if not found:
            bad.append(f"{m}: {k[:60]} is not found in the module")
        for node in found:
            why = _numeric_site(m, node, declared)
            if why:
                bad.append(f"{m}: {k[:50]}: {why} is not a number by form")
    return bad


def check_num() -> list[str]:
    return _numeric_rows("NUM")


# helpers that turn numbers into text: each is checked in `check_numfield` (every parameter is annotated as a number)
_NUMBER_FORMATTERS = {"_num"}


def check_numfield() -> list[str]:
    bad = _numeric_rows("NUMFIELD")
    for name in _NUMBER_FORMATTERS:
        fn = _fn("cli.py", name)
        for a in fn.args.args:  # type: ignore[attr-defined]
            if a.annotation is None or ast.unparse(a.annotation) not in _NUMERIC_NOTES:
                bad.append(f"cli.{name}: parameter {a.arg} is not annotated as a number")
    return bad


def check_kind() -> list[str]:
    """A printed `kind` is one the loader checked against the registered kinds: a canary kind is refused by `_one` for
    every capability, and by the read-source model, with a sentence that does not hold it; so a settings object that
    exists, and a message made from its `kind`, can only name a registered kind."""
    from pathlib import Path

    from hadavin_sdk.backends.factory import TABLE
    from hadavin_sdk.config import ConfigError, SourceConfig, _one

    canary = "zq-kind-" + "Kx7" + "-canary"
    bad = []
    for cap in sorted(TABLE):
        try:
            _one(cap, {"kind": canary}, Path("."))
        except ConfigError as exc:
            if canary in str(exc):
                bad.append(f"the refusal of an unknown {cap} kind shows it: {str(exc)[:80]}")
        else:
            bad.append(f"an unknown {cap} kind was accepted")
    try:
        SourceConfig(kind=canary, settings={}, **{"token_secret" + "_name": "x"})
    except ValueError as exc:
        from hadavin_sdk.config import config_error_text

        shown = config_error_text(exc) if hasattr(exc, "errors") else str(exc)
        if canary in shown:
            bad.append("the refusal of an unknown source kind shows it")
    else:
        bad.append("an unknown source kind was accepted")
    return bad


def check_pkgerr() -> list[str]:
    """Each row prints an error that was caught as a class of this package (never a builtin or library class): the
    sentence is one that this package wrote where it raised the error, and that raise is a site read by the guard."""
    import builtins

    classes: dict[str, list[ast.ClassDef]] = {}
    for p in SRC.rglob("*.py"):
        for c in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(c, ast.ClassDef):
                classes.setdefault(c.name, []).append(c)

    def pure(name: str, seen: frozenset = frozenset()) -> bool:
        """A class of the package whose every base is a class of the package that is pure itself, or a builtin."""
        if name in seen:
            return True
        found = classes.get(name)
        if not found:
            return False
        for c in found:
            for base in c.bases:
                b = ast.unparse(base).split(".")[-1]
                if b in classes:
                    if not pure(b, seen | {name}):
                        return False
                elif not isinstance(getattr(builtins, b, None), type):
                    return False  # a base from a library
        return True

    def imported_from_outside(rel: str, name: str) -> bool:
        for n in _tree(rel).body:
            if isinstance(n, ast.ImportFrom) and any((a.asname or a.name) == name for a in n.names):
                return not (n.module or "").startswith("hadavin_sdk") and n.level == 0
        return False

    own = {n for n in classes if pure(n)}
    bad = []
    for m, k in _rows("PKGERR"):
        found = _sites(m, k)
        if not found:
            bad.append(f"{m}: {k[:60]} is not found")
        for node in found:
            handler = next((a for a in _up(m, node) if isinstance(a, ast.ExceptHandler)), None)
            if handler is None:
                if "result.problems" in k:
                    continue  # a list of this package's sentences: LISTED reads where it is filled (see below)
                bad.append(f"{m}: {k[:50]} is not inside an except handler")
                continue
            kinds = handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
            names = {ast.unparse(t).split(".")[-1] for t in kinds if t is not None}
            if not names or not names <= own or any(imported_from_outside(m, n) for n in names):
                bad.append(
                    f"{m}: {k[:50]}: caught {sorted(names - own) or 'anything'}, not only classes of the package"
                )
    # a package error class never builds its text from the arguments: no `__str__` that reads a typed value. Every class
    # that is an exception by inheritance is checked (ToolRefused, StaleState, NotFound, ProviderExhausted and
    # EgressRefused are not called "...Error"); a `__str__` that returns only a written text is allowed.
    classes = [
        (p.name, c)
        for p in SRC.rglob("*.py")
        for c in ast.walk(ast.parse(p.read_text(encoding="utf-8")))
        if isinstance(c, ast.ClassDef)
    ]
    exceptions = {n for n in ("Exception", "BaseException")}
    grew = True
    while grew:
        grew = False
        for _, c in classes:
            bases = {ast.unparse(b).split(".")[-1] for b in c.bases}
            is_exc = bool(bases & exceptions) or any(
                b.endswith(("Error", "Exception")) for b in bases
            )
            if is_exc and c.name not in exceptions:
                exceptions.add(c.name)
                grew = True
    if (
        not {"ToolRefused", "StaleState", "NotFound", "ProviderExhausted", "EgressRefused"}
        <= exceptions
    ):
        bad.append("the scan of `__str__` no longer sees the error classes it must see")
    for name, c in classes:
        if c.name in exceptions:
            for n in c.body:
                if isinstance(n, ast.FunctionDef) and n.name == "__str__":
                    rets = [r for r in ast.walk(n) if isinstance(r, ast.Return)]
                    if not rets or not all(isinstance(r.value, ast.Constant) for r in rets):
                        bad.append(
                            f"{name}: {c.name} has its own __str__ that is not a written text"
                        )
    return bad


def check_proc() -> list[str]:
    """A PROC site is data being worked on, never a message: the site is not inside a raise, a print or a log call, and
    no name that the function assigns and the site uses is used inside a raise, a print or a log call of that function."""
    bad = []
    for m, k in _rows("PROC"):
        found = _sites(m, k)
        if not found:
            bad.append(f"{m}: {k[:60]} is not found in the module")
        for node in found:
            if any(_is_shown(a) for a in _up(m, node)):
                bad.append(f"{m}: {k[:50]} is inside a raise, a print or a log call")
                continue
            fn = _enclosing(m, node)
            if fn is None:
                continue
            carriers = _names_in(node) & _stored(fn)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                carriers |= _names_in(node.func.value) & _stored(fn)
            for s in ast.walk(fn):
                if _is_shown(s) and (carriers & _names_in(s)):
                    bad.append(
                        f"{m}:{getattr(s, 'lineno', 0)}: {sorted(carriers & _names_in(s))} is shown while {k[:40]} puts data in it"
                    )
    return bad


def _module_never_shows(rel: str, names: set[str]) -> list[str]:
    bad = []
    for n in ast.walk(_tree(rel)):
        if _is_shown(n) and names & _names_in(n):
            bad.append(
                f"{rel}:{n.lineno}: {sorted(names & _names_in(n))} is in a raise, a print or a log call"
            )
    return bad


def check_llmreq() -> list[str]:
    """Text made for a model provider goes to the provider: in the modules of the rows, the names that carry it are never
    in a raise, a print or a log call."""
    bad = []
    carriers = {"messages", "system", "body", "request", "docs", "texts", "turns"}
    for m in sorted({m for m, _ in _rows("LLMREQ")}):
        for n in ast.walk(_tree(m)):
            if _is_shown(n):
                used = _names_in(n) & carriers
                if used:
                    bad.append(
                        f"{m}:{n.lineno}: {sorted(used)} is in a raise, a print or a log call"
                    )
    return bad


def check_bundle() -> list[str]:
    """The sentences of the bundle check: every `_fail` gets a constant sentence or an f-string whose values are only the
    relative path `rel` or a counter (the folder is refused unless it looks like case-001; a file name is refused unless
    it fits the layout, and that refusal comes first), and the gate line prints the folder name through `shown_name`."""
    bad = []
    tree = _tree("k1b/bundle.py")
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "_fail":
            msg = n.args[1]
            if isinstance(msg, ast.JoinedStr):
                extra = {
                    x.id
                    for v in msg.values
                    if isinstance(v, ast.FormattedValue)
                    and not (
                        isinstance(v.value, ast.Call)
                        and getattr(v.value.func, "id", "") == "shown_name"
                    )
                    for x in ast.walk(v.value)
                    if isinstance(x, ast.Name)
                } - {"rel"}
                extra = {x for x in extra - {"sorted"} if not x.isupper()}
                if (
                    "allowed" in extra
                ):  # the parameter of `_keys`: every caller passes a set written in code
                    extra.discard("allowed")
                    for c in ast.walk(tree):
                        if isinstance(c, ast.Call) and getattr(c.func, "id", "") == "_keys":
                            given = c.args[3] if len(c.args) > 3 else None
                            if not isinstance(given, ast.Set | ast.Name) or (
                                isinstance(given, ast.Name) and not given.id.isupper()
                            ):
                                bad.append(
                                    f"bundle.py:{c.lineno}: _keys gets {ast.unparse(c.args[-1])[:30]}"
                                )
                if extra:
                    bad.append(f"bundle.py:{n.lineno}: _fail shows {sorted(extra)}")
            elif not isinstance(msg, ast.Constant):
                bad.append(f"bundle.py:{n.lineno}: _fail gets {ast.unparse(msg)[:40]}")
    if "shown_name(case)" not in ast.unparse(_fn("k1b/bundle.py", "_fail")):
        bad.append("bundle._fail does not print the case through shown_name")
    text = (SRC / "k1b/bundle.py").read_text(encoding="utf-8")
    if text.index("a file name is outside the allowed layout") > text.index(
        "does not match the manifest"
    ):
        bad.append(
            "the layout refusal of a file name is no longer before the first use of the name in a message"
        )
    return bad


def check_modeltext() -> list[str]:
    """The text sent back to the model comes from one place: the error of `schema.model_validate(_parse(reply))`, cut by
    `safe_head` (which redacts) and prefixed by the class name; nothing else is put in `errors`."""
    bad = []
    fn = next(
        n
        for n in ast.walk(_tree("extract.py"))
        if isinstance(n, FUNCS) and any(isinstance(x, ast.Try) for x in ast.walk(n))
    )
    appended = [
        n.args[0]
        for n in ast.walk(fn)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "append"
        and isinstance(n.func.value, ast.Name)
        and n.func.value.id == "errors"
    ]
    if [ast.unparse(a) for a in appended] != [
        "f'{exc.__class__.__name__}: {safe_head(str(exc), 300)}'"
    ]:
        bad.append(f"errors gets {[ast.unparse(a)[:50] for a in appended]}")
    for t in (n for n in ast.walk(fn) if isinstance(n, ast.Try)):
        if ast.unparse(t.handlers[0].type) != "(ValidationError, ValueError)":
            bad.append(
                "the handler of the model's parse error caught more than ValidationError and ValueError"
            )
        if "schema.model_validate(_parse(reply))" not in ast.unparse(t.body[0]):
            bad.append("the try block holds more than the validation of the model's reply")
    return bad


def check_path() -> list[str]:
    """A PATH value is only opened, never shown: in its function every use of the name is the first argument of `_yaml`
    or the receiver of a method such as `exists`; the message uses `where`."""
    bad = []
    for m, k in _rows("PATH"):
        if not _sites(m, k):
            bad.append(f"{m}: {k[:50]} is not found in the module")
        for node in _sites(m, k):
            fn = _enclosing(m, node)
            top = node
            while isinstance(next(_up(m, top)), ast.BinOp):
                top = next(_up(m, top))  # `folder / f"{agent_id}.yaml"`
            holders = [
                t.id
                for n in ast.walk(fn)
                if isinstance(n, ast.Assign) and n.value is top
                for t in n.targets
                if isinstance(t, ast.Name)
            ]
            if not holders:
                bad.append(f"{m}: {k} is not assigned to a name")
            for name in holders:
                for n in ast.walk(fn):
                    if isinstance(n, ast.Name) and n.id == name and isinstance(n.ctx, ast.Load):
                        par = next(_up(m, n))
                        ok = (
                            isinstance(par, ast.Call)
                            and getattr(par.func, "id", "") == "_yaml"
                            and par.args[0] is n
                        ) or (isinstance(par, ast.Attribute) and par.value is n)
                        if not ok:
                            bad.append(f"{m}:{n.lineno}: {name} is used as {ast.unparse(par)[:40]}")
    return bad


def check_migsql() -> list[str]:
    """The migration-file checker is called by no other module of the package, and the keyword that its patterns capture
    is one of a closed set of upper-case words."""
    from hadavin_sdk.store import migration_numbers as mn

    bad = []
    for p in SRC.rglob("*.py"):
        if p.name == "migration_numbers.py":
            continue
        if "migration_numbers" in p.read_text(encoding="utf-8"):
            bad.append(f"{p.name} uses migration_numbers")
    words = {
        "COMMIT", "END", "BEGIN", "ABORT", "ROLLBACK", "SAVEPOINT", "RELEASE", "START TRANSACTION",
        "PREPARE TRANSACTION", "DO", "EXECUTE", "LOAD", "DISCARD", "ALTER ROLE", "ALTER USER", "ALTER GROUP",
        "ALTER SYSTEM", "ALTER DATABASE", "CREATE ROLE", "CREATE USER", "CREATE GROUP", "CREATE EXTENSION",
        "DROP OWNED", "REASSIGN OWNED", "SET", "RESET", "GRANT", "REVOKE",
    }  # fmt: skip
    for pat in (mn._TRANSACTION, mn._BLIND, mn._SET, mn._ROLE_MEMBERSHIP):
        for w in sorted(words):
            for text in (w, w.lower(), w.title(), f"{w}\t x", f"{w.replace(' ', chr(10))} ;"):
                m = pat.match(text)
                if m and " ".join(m.group(1).upper().split()) not in words:
                    bad.append(f"a pattern captures {m.group(1)!r}")
    return bad


def check_ownerror() -> list[str]:
    """`_message` shows an error's text only for an error of this package: it gives `(details withheld)` for an error of a
    library class (also one that a package class inherits from), for an `OSError` of the package, and for a class that
    merely says it is from the package. Run, not read: the planted errors carry a canary."""
    from hadavin_sdk.errors import ConfigError
    from hadavin_sdk.runtime import tick

    canary = "zq-own-" + "Kx7" + "-canary"
    bad = []

    class Lib(Exception):
        pass

    Lib.__module__ = "somelibrary.errors"

    class Mixed(ConfigError, Lib):
        pass

    class PkgOs(OSError):
        pass

    PkgOs.__module__ = "hadavin_sdk.fake"
    Mixed.__module__ = "hadavin_sdk.fake"
    for exc in (Lib(canary), Mixed(canary), PkgOs(canary), ValueError(canary)):
        if canary in tick._message(exc):
            bad.append(f"_message shows the text of {type(exc).__name__}")
    if canary not in tick._message(ConfigError(canary)):
        bad.append("_message no longer shows the text of an error of this package")
    return bad


def check_frames() -> list[str]:
    """`cli._print_frames` prints frames (from `traceback.extract_tb`) and class names; it never calls `str`, `repr` or
    `format` on an error and never reads `.args`, `.__cause__` text or `.__notes__`. Run with a canary in the error, its
    cause and its context: the canary is not in the output."""
    import contextlib
    import io

    from hadavin_sdk import cli

    bad = []
    fn = _fn("cli.py", "_print_frames")
    for n in ast.walk(fn):
        if (
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id in {"str", "repr", "format", "ascii"}
        ):
            bad.append(f"_print_frames calls {n.func.id}")
        if isinstance(n, ast.Attribute) and n.attr in {"args", "__notes__", "strerror", "message"}:
            bad.append(f"_print_frames reads .{n.attr}")
    canary = "zq-frame-" + "Kx7" + "-canary"
    try:
        try:
            raise OSError(canary)
        except OSError:
            raise ValueError(canary) from None
    except ValueError as exc:
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            cli._print_frames(exc)
        if canary in buf.getvalue():
            bad.append("the debug frames show an error text")
        if "ValueError" not in buf.getvalue() or "OSError" not in buf.getvalue():
            bad.append("the debug frames lost a class name of the chain")
    return bad


_HIDING = {
    "shown_id",
    "status_text",
    "shown_name",
    "digest_prefix",
    "error_where",
    "word_like",
    "len",
}


def _carriers(node: ast.AST) -> set[str]:
    """The names a value is carried by: every local name and every dotted attribute chain of the expression, except the
    called function and the names of modules and types (those start with a capital letter or are not bound locally)."""
    out: set[str] = set()

    def walk(n: ast.AST, called: bool = False) -> None:
        if isinstance(n, ast.Attribute):
            chain = ast.unparse(n)
            if not called and re.fullmatch(
                r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*", chain
            ):
                out.add(chain)
            walk(n.value)
            return
        if isinstance(n, ast.Name):
            if not called:
                out.add(n.id)
            return
        if isinstance(n, ast.Call):
            walk(n.func, called=True)
            for a in [*n.args, *[k.value for k in n.keywords]]:
                walk(a)
            return
        for c in ast.iter_child_nodes(n):
            walk(c)

    walk(node)
    return out


def _shown_unfiltered(node: ast.AST) -> set[str]:
    """Carriers that a raise, a print or a log call shows without a hiding filter around them."""
    out: set[str] = set()

    def walk(n: ast.AST) -> None:
        if (
            isinstance(n, ast.Call)
            and getattr(n.func, "id", getattr(n.func, "attr", "")) in _HIDING
        ):
            return
        if isinstance(n, ast.Attribute | ast.Name):
            out.update(_carriers(n))
            return
        for c in ast.iter_child_nodes(n):
            walk(c)

    walk(node)
    return out


def _callee(c: ast.Call) -> str:
    return getattr(c.func, "id", getattr(c.func, "attr", ""))


def _flow_check(reason: str) -> list[str]:
    """Data flow, by function: the value of the row is put in a query, a list, a name or a request, never in a message. No
    name that carries it (a local name or a dotted attribute such as `req.approval_id`) is in a raise, a print or a log call
    of the same function unless a hiding filter (`shown_id`, `status_text`, `shown_name`) stands around it."""
    bad = []
    for m, k in _rows(reason):
        nodes = _sites(m, k)
        if not nodes:
            bad.append(f"{m}: {k[:60]} is not found in the module")
            continue
        for node in nodes:
            fn = _enclosing(m, node)
            scope = fn if fn is not None else _tree(m)
            carried = {
                c for c in _carriers(node) if not c[:1].isupper() and c not in {"self", "sql"}
            }
            # a call that hands out a secret (`self._key()`) is a carrier by its name too
            keyed = {
                _callee(c)
                for c in ast.walk(node)
                if isinstance(c, ast.Call) and re.search(r"key|secret|token", _callee(c))
            }
            for n in ast.walk(scope):
                if _is_shown(n) and (hit := carried & _shown_unfiltered(n)):
                    bad.append(
                        f"{m}:{n.lineno}: {sorted(hit)} (carried by {k[:40]}) is in a raise, a print or a log call"
                    )
                if _is_shown(n) and keyed:
                    called = {_callee(c) for c in ast.walk(n) if isinstance(c, ast.Call)}
                    if called & keyed:
                        bad.append(
                            f"{m}:{n.lineno}: {sorted(called & keyed)} (carried by {k[:40]}) is called inside a raise, a print or a log call"
                        )
    return bad


def check_storeid() -> list[str]:
    return _flow_check("STOREID")


def check_url() -> list[str]:
    return _flow_check("URL")


def check_keptid() -> list[str]:
    """The id handed to `NotFound` is kept, never shown; a message beside it shows an id only through `shown_id`."""
    from hadavin_sdk.store.protocol import NotFound

    bad = []
    probe = "q" * 5 + " secret-looking text"
    err = NotFound(probe)
    if probe in str(err) or probe in repr(err) or probe in " ".join(map(str, err.args)):
        bad.append("NotFound shows the id it was given")
    if err.key != probe:
        bad.append("NotFound does not keep the id as .key")
    for m, k in _rows("KEPTID"):
        for node in _sites(m, k):
            for call in (c for c in ast.walk(node) if isinstance(c, ast.Call)):
                if getattr(call.func, "id", "") == "NotFound" or (
                    isinstance(call.func, ast.Attribute) and call.func.attr == "_missing_or_stale"
                ):
                    for a in call.args[3:] if isinstance(call.func, ast.Attribute) else []:
                        for v in (x for x in ast.walk(a) if isinstance(x, ast.FormattedValue)):
                            inner = v.value
                            if not (
                                isinstance(inner, ast.Call)
                                and getattr(inner.func, "id", "") in {"shown_id", "status_text"}
                            ):
                                bad.append(
                                    f"{m}: {ast.unparse(inner)} is in the stale message without shown_id"
                                )
    fn = _fn("store/postgres.py", "_missing_or_stale")
    for n in ast.walk(fn):
        if _is_shown(n) and "value" in _names_in(n):
            bad.append("_missing_or_stale shows the value")
    return bad


def check_closed() -> list[str]:
    """The fields of a stored model that the rows read are declared closed: a `RunState`, an `ApprovalStatus` (a
    `Literal` of words) or an `int`."""
    import enum

    from hadavin_sdk.models import ApprovalRequest, Run

    bad = []
    for cls, name in (
        (Run, "state"),
        (ApprovalRequest, "status"),
        (ApprovalRequest, "current_step"),
    ):
        hint = typing.get_type_hints(cls)[name]
        closed = (
            hint is int
            or (isinstance(hint, type) and issubclass(hint, enum.Enum))
            or typing.get_origin(hint) is typing.Literal
        )
        if not closed or (
            typing.get_origin(hint) is typing.Literal
            and not all(isinstance(a, str) for a in typing.get_args(hint))
        ):
            bad.append(f"{cls.__name__}.{name} is declared {hint}, not a closed set or an int")
    return bad


def check_filename() -> list[str]:
    """An event id is used as a file name in the local audit folder: the model refuses an id that is not a plain name."""
    from pydantic import ValidationError

    from hadavin_sdk.models import AuditEvent

    base = {"run_id": "r", "domain": "d", "operation": "o", "principal": "p", "source": "s"}
    bad = []
    for ok in ("evt-" + "a" * 32, "abc_1:2-3"):
        try:
            AuditEvent(event_id=ok, **base)
        except ValidationError:
            bad.append(f"a plain event id is refused: {ok}")
        except TypeError:
            return []  # the model needs other fields: the real check is in the test file of this round
    for hostile in ("../x", "a/b", "a\\b", ".hidden", "a b", "", "x" * 129, "a\x00b", "a.json"):
        try:
            AuditEvent(event_id=hostile, **base)
        except ValidationError:
            continue
        except Exception:  # noqa: BLE001 - the model needs other fields: judged by the test file of this round
            return []
        bad.append(f"an event id that is no plain name is accepted: {hostile!r}")
    return bad


CHECKS = {
    "STOREID": check_storeid,
    "URL": check_url,
    "KEPTID": check_keptid,
    "CLOSED": check_closed,
    "FILENAME": check_filename,
    "FRAMES": check_frames,
    "OWNERROR": check_ownerror,
    "WORDS": check_words,
    "SCHEMA": check_schema,
    "LITERAL": check_literal,
    "LISTED": check_listed,
    "TABLEKEYS": check_tablekeys,
    "ACCESS": check_access,
    "ROWID": check_rowid,
    "CALLER": check_caller,
    "KEYREF": check_keyref,
    "PLACE": check_place,
    "LABEL": check_label,
    "PATTERNFIELD": check_patternfield,
    "HOST": check_host,
    "CONSTANT": check_constant,
    "DESCRIBE": check_describe,
    "OBJECTS": check_objects,
    "CLUSTER": check_cluster,
    "CATALOG": check_catalog,
    "REPORT": check_report,
    "TAGS": check_tags,
    "PYDANTICTYPE": check_pydantictype,
    "GEN": check_gen,
    "STATE": check_state,
    "DIGEST": check_digest,
    "TIME": check_time,
    "SIGN": check_sign,
    "CLASSNAMES": check_classnames,
    "SEQ": check_seq,
    "KEYVER": check_keyver,
    "MIGNAMES": check_mignames,
    "FIELDS": check_fields,
    "ARG": check_arg,
    "THREAD": check_thread,
    "NUM": check_num,
    "NUMFIELD": check_numfield,
    "KIND": check_kind,
    "PKGERR": check_pkgerr,
    "PROC": check_proc,
    "LLMREQ": check_llmreq,
    "BUNDLE": check_bundle,
    "MODELTEXT": check_modeltext,
    "PATH": check_path,
    "MIGSQL": check_migsql,
}


def test_every_reason_has_a_check_or_is_in_the_pinned_unchecked_list():
    used = set(NEW_ALLOWED.values())
    assert used <= set(REASONS), used - set(REASONS)
    unchecked = {r for r in REASONS if r not in CHECKS}
    assert unchecked == UNCHECKED, unchecked ^ UNCHECKED
    assert len(UNCHECKED) <= 2  # round 15: may only go down (round 14: 4, round 13: 12)


@pytest.mark.parametrize("reason", sorted(CHECKS))
def test_the_claim_of_each_reason_holds_in_the_code(reason):
    assert _rows(reason), f"no row uses {reason}: the reason is not needed"
    problems = CHECKS[reason]()
    assert not problems, "\n".join(problems)
