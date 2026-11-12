"""Shared helpers of the Q8b tests: the link oracle (a plain scan of the text that reads code fences and inline code with
its OWN small reader, not the functions of ``approvals/gate.py`` under test) and the placeholder pattern of the code."""

from __future__ import annotations

import re

from hadavin_sdk.guard import runmap

# One or more placeholders and nothing else. Built from the public `runmap.PLACEHOLDER` (present on main too), not from the
# private `R._ONLY_PLACEHOLDERS`, so these tests are collected on code that predates that name.
ONLY_PLACEHOLDERS = re.compile(rf"(?:{runmap.PLACEHOLDER.pattern})+")

_FENCE_OPEN = re.compile(r"^ {0,3}(`{3,})[^`]*$")


def code_lines(text: str) -> set[int]:
    """The line numbers inside the body of a CLOSED backtick fence (CommonMark: an opening run of three or more
    backticks with no backtick in its info string, closed by a line of at least as many and nothing else)."""
    lines = text.split("\n")
    inside: set[int] = set()
    i = 0
    while i < len(lines):
        m = _FENCE_OPEN.match(lines[i])
        if not m:
            i += 1
            continue
        n = len(m.group(1))
        close = next(
            (
                j
                for j in range(i + 1, len(lines))
                if re.fullmatch(rf" {{0,3}}`{{{n},}}[ \t]*", lines[j])
            ),
            None,
        )
        if close is None:
            i += 1
            continue
        inside.update(range(i + 1, close))
        i = close + 1
    return inside


def outside_code(text: str) -> list[str]:
    """The parts of the text that are not a fence body and not inline code (a line with a double backtick is all
    outside: its code spans are ambiguous)."""
    code = code_lines(text)
    out: list[str] = []
    for i, line in enumerate(text.split("\n")):
        if i in code:
            continue
        if "``" in line:
            out.append(line)
            continue
        parts = line.split("`")
        paired = (
            len(parts) if len(parts) % 2 == 1 else len(parts) - 1
        )  # an unclosed last span is not code
        out += [p for k, p in enumerate(parts) if k % 2 == 0 or k >= paired]
    return out


def bare_domain_tokens(text: str, exempt: bool = True) -> list[str]:
    """A token (split at white space, outside code) fails when, with every `[.]` read as `|`, it still holds
    letter-or-digit-or-`>` then `.` then two or more letters. Three exemptions, each the older code's own stated rule:
    E1 the dot is in the part before an `@` (an e-mail's local part); E2 the letters after the dot are directly followed
    by a digit, `_`, `-` or `@` (not the shape of a top-level domain); E3 the label starts right after `/` and the token
    holds no placeholder. The tests call it with ``exempt=False``."""
    bad = []
    for seg in outside_code(text):
        for tok in seg.split():
            t = tok.replace("[.]", "|")
            for i, ch in enumerate(t):
                if ch != "." or i == 0 or not (t[i - 1].isalnum() or t[i - 1] == ">"):
                    continue
                j = i + 1
                while j < len(t) and t[j].isalpha():
                    j += 1
                if j - (i + 1) < 2:
                    continue
                if exempt:
                    if "@" in t[i:]:
                        continue  # E1
                    if j < len(t) and (t[j].isdigit() or t[j] in "_-@"):
                        continue  # E2
                    k = i
                    while k > 0 and (t[k - 1].isalnum() or t[k - 1] in "-_"):
                        k -= 1
                    if k > 0 and t[k - 1] == "/" and "<" not in t:
                        continue  # E3
                bad.append(tok)
                break
    return bad


def shown_records(*records):
    """The records as `redact_bundle` shows them (two passes, one map), as a list."""
    from datetime import UTC, datetime

    from hadavin_sdk.k1b.bundle import Bundle
    from hadavin_sdk.k1b.redaction import redact_bundle

    bundle = Bundle(
        case_id="case-q8b",
        alert_time=datetime(2026, 1, 1, 10, tzinfo=UTC),
        alert_time_text="2026-01-01T10:00:00Z",
        alert={},
        metrics=(),
        logs=(),
        deploys=tuple(records),
        k8s=(),
        runbooks=(),
        ids=frozenset(),
        manifest_sha256="0" * 64,
    )
    return list(redact_bundle(bundle)[0].deploys)


_ORDINARY_LOOKBEHIND = re.compile(r"\(\?<!\(\?<!\[\\w\.\]\)\(\?<!\[\\w\.\]-\)[a-z]+\)")
_LOOKAHEAD = re.compile(r"\(\?=[^()]*\)")


def strip_look_arounds(fragment: str) -> str:
    """A fragment of `redact.KEY_ALTERNATIVES` without its look-arounds: the look-ahead after a bare word (`pass(?=...)`) and the
    look-behinds that keep the bare word out of an ordinary word (`(?<!(?<![a-z0-9])by)pass`). What is left is the key word."""
    return _LOOKAHEAD.sub("", _ORDINARY_LOOKBEHIND.sub("", fragment))


def _spellings(fragment: str) -> list[str]:
    """Every way a fragment of `redact.KEY_ALTERNATIVES` can be written: `[_\\-]?` as nothing, `_` and `-`, `(?:ificate)?` with
    and without its letters, `\\.` as a dot, and a look-ahead (`pass(?=["']?\\s*[:=])`) as the word before it."""
    out = [strip_look_arounds(fragment).replace("\\.", ".")]
    for pat, subs in (
        ("[_\\-]?", ["", "_", "-"]),
        ("(?:[0-9]*[_.\\-])?", ["", "_", "-", "."]),  # a pair: glued or with a separator (round 11)
    ):
        out = [o.replace(pat, s) for o in out for s in subs]
    more = []
    for o in out:
        m = re.search(r"\(\?:([a-z]+)\)\?", o)
        if m:
            more += [o.replace(m.group(0), ""), o.replace(m.group(0), m.group(1))]
        else:
            more.append(o)
    return more


def key_spellings() -> list[str]:
    """Every spelling of every key of `redact.KEY_ALTERNATIVES`, derived from the regex fragments (so a key added there is
    tested without a second list here)."""
    import importlib

    redact = importlib.import_module(
        "hadavin_sdk.guard.redact"
    )  # the module (the package exports a function of that name)
    keys = {k for frag in redact.KEY_ALTERNATIVES for k in _spellings(frag)}
    bad = [k for k in keys if not re.fullmatch(r"[A-Za-z_.\-]+", k)]
    assert not bad, f"a fragment of KEY_ALTERNATIVES was not expanded: {bad}"
    assert len(keys) > 30, keys
    return sorted(keys)


def slack_notice(text: str) -> str:
    """What the REAL Slack channel would post for `notify(principal, text)` (its HTTP call replaced by a recorder)."""
    from hadavin_sdk.approvals.slack_channel import SlackChannel

    posted: list[dict] = []
    ch = SlackChannel.__new__(SlackChannel)
    ch.channel_id = "C0000000"
    ch._call = lambda method, body: posted.append(body) or {}  # type: ignore[method-assign]
    ch.notify("U0000000", text)
    return posted[0]["text"]


# ---- every path a credential key can take (round 4) ---------------------------------------------------------------------

P1, P2, P3 = "Zq7" + "xV", "Kp9" + "wT", "Hn4" + "bL"  # made-up pieces of a value, built from parts
VALUE_STYLES = {  # style -> (the text after the sign, the raw value written under the key in a record)
    "dq": (f'"{P1};{P2} {P3}"', f"{P1};{P2} {P3}"),
    "sq": (f"'{P1} {P2} {P3}'", f"{P1} {P2} {P3}"),
    "semicolon": (f"{P1};{P2}{P3}", f"{P1};{P2}{P3}"),
    "plain": (f"{P1}{P2}{P3}", f"{P1}{P2}{P3}"),
}


def _case_bundle(**records):
    from datetime import UTC, datetime

    from hadavin_sdk.k1b.bundle import Bundle

    base = {
        "case_id": "case-q8b",
        "alert_time": datetime(2026, 1, 1, 10, tzinfo=UTC),
        "alert_time_text": "2026-01-01T10:00:00Z",
        "alert": {},
        "metrics": (),
        "logs": (),
        "deploys": (),
        "k8s": (),
        "runbooks": (),
        "ids": frozenset(),
        "manifest_sha256": "0" * 64,
    }
    base.update(records)
    return Bundle(**base)


def path_outputs(key: str, style: str) -> dict[str, str]:
    """What the four paths show for `key` with a value of `style`: the card (`key=v` and `key: v`), a tool result (as
    text and as JSON), a log record of a case bundle, and a record key of a case bundle (nested too)."""
    import json

    from hadavin_sdk.approvals.channel import clean
    from hadavin_sdk.k1b.redaction import redact_bundle
    from hadavin_sdk.tools import redact_layered

    text, raw = VALUE_STYLES[style]
    logs = (
        (
            "app.log",
            ({"ts": "2026-01-01T09:00:00Z", "msg": f"{key}={text} end"},),
        ),
    )
    out = redact_bundle(_case_bundle(logs=logs))[0]
    rec = redact_bundle(_case_bundle(deploys=({key: raw, "n": {key: raw}},), alert={key: [raw]}))[0]
    return {
        "card": clean(f"set {key}={text} now") + "\n" + clean(f"{key}: {text}"),
        "tool": redact_layered(f"{key}={text} tail", {})
        + "\n"
        + redact_layered(json.dumps({key: raw}), {}),
        "log": json.dumps(out.logs, default=str, ensure_ascii=False),
        "walk": json.dumps(rec.deploys, default=str) + json.dumps(rec.alert, default=str),
    }


def text_paths(text: str) -> dict[str, str]:
    """What the text paths show for `text`: a card, a tool result, an untrusted text of a run and a log line of a case bundle."""
    import json

    from hadavin_sdk.approvals.channel import clean
    from hadavin_sdk.k1b.redaction import redact_bundle
    from hadavin_sdk.tools import redact_layered

    logs = (("app.log", ({"ts": "2026-01-01T09:00:00Z", "msg": text},)),)
    out = redact_bundle(_case_bundle(logs=logs))[0]
    return {
        "card": clean(text),
        "tool": redact_layered(text, {}),
        "run": runmap.redact_untrusted(text, runmap.RunMap()),
        "log": json.dumps(out.logs, default=str, ensure_ascii=False),
    }


def readable_pieces(out: str, within: str | None = None) -> list[str]:
    """The made-up pieces (`P1`, `P2`, `P3`) readable in `out`; with `within`, only those that are part of that text."""
    return [p for p in (P1, P2, P3) if p in out and (within is None or p in within)]


# ---- the scan for a second list of credential keys (used by `tests/test_q8b_batch2.py` and its self-test in batch 4) --------------

KEY_LIST_WORDS = {
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "passphrase",
    "credential",
    "apikey",
}


def _letters(text: str) -> str:
    return re.sub(r"[^a-z]", "", text.lower())


def _string_of(node) -> str | None:
    """The text of a string constant, or of a `+` chain of string constants (`"a|" + "b"`); None for anything else."""
    import ast

    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _string_of(node.left), _string_of(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def key_list_words(node) -> set[str]:
    """The credential words (`KEY_LIST_WORDS`, compared by their letters only: `api_key` is `apikey`) that this ONE node lists:
    a tuple, list or set of strings; a `"a b c".split()`; or a text with `|` (a regex alternation, joined by `+` too)."""
    import ast

    if isinstance(node, ast.Tuple | ast.List | ast.Set):
        pieces = [
            e.value for e in node.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)
        ]
    elif (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "split"
        and _string_of(node.func.value) is not None
    ):
        pieces = re.split(r"[|,\s]+", _string_of(node.func.value) or "")
    elif (text := _string_of(node)) is not None and "|" in text:
        pieces = text.split("|")
    else:
        return set()
    return {_letters(p) for p in pieces} & KEY_LIST_WORDS


def second_key_lists(tree, allowed: set[str]) -> list[tuple[int, list[str]]]:
    """Every node of `tree` that lists three or more credential words, outside the assignments named in `allowed`."""
    import ast

    skip: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign | ast.AnnAssign):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(target, ast.Name) and target.id in allowed:
                skip.update(id(c) for c in ast.walk(node))
    found = []
    for node in ast.walk(tree):
        if id(node) not in skip and len(hits := key_list_words(node)) >= 3:
            found.append((node.lineno, sorted(hits)))
    return found
