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
