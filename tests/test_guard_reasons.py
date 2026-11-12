"""Round 13 (Q8a-1): each REASON of the allowance table is a claim about the code, and this file checks the claim.

A reason written in words only can be wrong and nobody sees it. Here every reason that this round gave (and the sites it
covers) has a check that reads the code or runs it: a value that the reason calls an `int` is cast to `int` or declared
`int`, a list that the reason calls "written in code" is a constant in the source, a label that the reason calls "a
literal at every caller" is a literal at every caller. The reasons of earlier rounds are listed in `UNCHECKED`: the list
may only get shorter (a test pins its size), and each of them is named in the notes of this batch as not yet checked by code.
"""

from __future__ import annotations

import ast
import re
import typing
from pathlib import Path

import pytest

from tests._guard_allowances import NEW_ALLOWED, REASONS

SRC = Path(__file__).resolve().parent.parent / "src" / "hadavin_sdk"

# Reasons of rounds 11 and 12 that have no check by code yet. The size may only go down.
UNCHECKED = {
    "PROC", "CARD", "LLMREQ", "NUM", "STOREID", "URL", "BUNDLE", "KIND", "PKGERR", "MODELTEXT", "REDACTED", "NUMFIELD",
}  # fmt: skip


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
        "blocked", "reply", "result", "now_d", "failed", "reason", "why", "disabled", "cfg", "name",
        "sources", "tools_mod", "shown_name", "sorted", "a", "p", "ToolRefused",
    }  # fmt: skip
    for m, k in _rows("WORDS"):
        extra = _names(k) - allowed - {"_LOG"}
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
        ("config.py", "_anchor_refusals", "refused"),
    ):
        try:
            fn = _fn(rel, name)
        except AssertionError:
            continue
        for n in ast.walk(fn):
            if (
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and n.func.attr == "append"
                and isinstance(n.func.value, ast.Name)
                and n.func.value.id == var
            ):
                arg = n.args[0]
                if not isinstance(arg, ast.JoinedStr | ast.Constant | ast.Call):
                    bad.append(f"{rel}:{n.lineno}: {var}.append of {ast.unparse(arg)[:50]}")
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
    place = _fn("backends/platform_secrets.py", "_place")
    for n in ast.walk(place):
        if (
            isinstance(n, ast.FormattedValue)
            and isinstance(n.value, ast.Name)
            and n.value.id == "name"
        ):
            bad.append("_place formats the secret name")
    return bad


def check_label() -> list[str]:
    """A label is a literal at every call of the functions that take one."""
    bad = []
    takes = {"read_configured": 1, "list_configured": 1, "unreadable": 0, "_yaml": 1}
    for p in SRC.rglob("*.py"):
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if not (
                isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in takes
            ):
                continue
            if len(n.args) <= takes[n.func.id]:
                continue
            arg = n.args[takes[n.func.id]]
            fixed = isinstance(arg, ast.Constant) or (
                isinstance(arg, ast.JoinedStr)
                and "shown_name" not in ast.unparse(arg)
                or isinstance(arg, ast.Name)
            )
            if isinstance(arg, ast.Name) and arg.id not in {"what", "label", "name"}:
                fixed = False
            if not fixed:
                bad.append(f"{p.name}:{n.lineno}: {n.func.id} gets {ast.unparse(arg)[:40]}")
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

    class Odd(Exception):
        status_code = "https://x.example/?key=1"

    if describe(Odd("t")) != "Odd":
        bad.append("describe shows a status that is not an int")
    return bad


def check_objects() -> list[str]:
    fn = _fn("llm/retry.py", "_chain")
    return [
        "_chain makes text"
        for n in ast.walk(fn)
        if isinstance(n, ast.JoinedStr | ast.FormattedValue)
    ]


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
    keys_ok = {
        "bundle_set_sha256", "cases_with_masking", "cause_fault_types_sha256", "cause_services_sha256",
        "config_hash", "model_id", "scheme", "sdk_version", "usd",
    }  # fmt: skip
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

    bad = [
        f"state {m!r} is not a fixed upper-case word"
        for m in RunState
        if not re.fullmatch(r"[A-Z_]+", m.value)
    ]
    fn = _fn("runtime/runs.py", "check")
    notes = {a.arg: ast.unparse(a.annotation) for a in fn.args.args}  # type: ignore[attr-defined]
    if notes != {"frm": "RunState", "to": "RunState"}:
        bad.append(f"runs.check parameters are not both RunState: {notes}")
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


def check_time() -> list[str]:
    bad = []
    ok = re.compile(
        r"timedelta\(|\.ttl_s\b|\.retain\b|clock\(\)|monotonic\(\)|^now$|^at$|timeout_s"
    )
    for (mod, site), node in zip(_rows("TIME"), _row_asts("TIME"), strict=True):
        if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)):
            bad.append(f"{mod}: {site} is not a sum")
        elif not (ok.search(ast.unparse(node.left)) and ok.search(ast.unparse(node.right))):
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
    for mod, site in _rows("CLASSNAMES"):
        text = site
        if "str(exc)" in text or "safe_head" in text or "exc.args" in text:
            bad.append(f"{mod}: {site}: prints the text of an error")
        if mod != "config.py" or "exc.title" not in text or "len(errors)" not in text:
            bad.append(f"{mod}: {site}: not the pydantic count-and-title line")
    return bad


def check_seq() -> list[str]:
    bad = []
    src = (SRC / "audit/chain.py").read_text(encoding="utf-8")
    m = re.search(r"type\(seq\) is not int", src)
    if not m:
        bad.append(
            "chain.py no longer checks `type(seq) is not int` refusal before the message with seq"
        )
    elif src.index("holds seq") < m.start():
        bad.append("the seq message comes before the integer check")
    return bad


def check_built() -> list[str]:
    fn = _fn("audit/local_dir.py", "write_intent")
    src = ast.unparse(fn)
    bad = []
    if (
        "failure = None" not in src
        or "failure = f'intent {event.event_id}: {exc.__class__.__name__}'" not in src
    ):
        bad.append("`failure` is no longer built from the event id and the class name")
    raise_after_handler = False
    for n in ast.walk(fn):
        if isinstance(n, ast.Try):
            raise_after_handler = raise_after_handler or any(
                isinstance(x, ast.Raise) and ast.unparse(x) == "raise AuditUnavailable(failure)"
                for x in ast.iter_child_nodes(fn)
            )
    if "raise AuditUnavailable(failure)" not in src:
        bad.append("AuditUnavailable(failure) is gone")
    # the raise is not inside any handler: no cause, no context
    for n in ast.walk(fn):
        if isinstance(n, ast.ExceptHandler):
            for x in ast.walk(n):
                if isinstance(x, ast.Raise) and "AuditUnavailable(failure)" in ast.unparse(x):
                    bad.append(
                        "AuditUnavailable(failure) is raised inside an except block (it would carry a cause)"
                    )
    return bad


def check_keyver() -> list[str]:
    bad = []
    src = (SRC / "audit/signer_vault.py").read_text(encoding="utf-8")
    if "key_version: int" not in src:
        bad.append("key_version is not declared int in the signer")
    if (
        not re.search(r"status_text|isinstance\(status, int\)", src)
        and "Vault answered {status}" in src
    ):
        bad.append("the Vault status is printed without a number check")
    for call in re.findall(r"self\._call\(\s*\w+,\s*(\S+?),", src):
        if not re.match(r"[\"'f](keys|sign)", call):
            bad.append(f"a request path that does not start with keys or sign: {call}")
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


CHECKS = {
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
    "BUILT": check_built,
    "KEYVER": check_keyver,
    "MIGNAMES": check_mignames,
    "FIELDS": check_fields,
    "ARG": check_arg,
}


def test_every_reason_has_a_check_or_is_in_the_pinned_unchecked_list():
    used = set(NEW_ALLOWED.values())
    assert used <= set(REASONS), used - set(REASONS)
    unchecked = {r for r in REASONS if r not in CHECKS}
    assert unchecked == UNCHECKED, unchecked ^ UNCHECKED
    assert len(UNCHECKED) <= 12  # round 13, second pass: may only go down


@pytest.mark.parametrize("reason", sorted(CHECKS))
def test_the_claim_of_each_reason_holds_in_the_code(reason):
    assert _rows(reason), f"no row uses {reason}: the reason is not needed"
    problems = CHECKS[reason]()
    assert not problems, "\n".join(problems)
