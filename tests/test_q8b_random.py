"""Q8b, seeded random tests of the two masking paths (made-up data; fixed seeds; no clock in an assertion).

P1: a value under a credential key, or an entry of a Kubernetes Secret, in an incident case. P2 and N9: the text of an
approval card. The generators and the oracles are the ticket's (appendix C). The oracle for a bare domain is a plain
token scan that shares no pattern with ``approvals/gate.py``.
"""

from __future__ import annotations

import random
import re
from datetime import UTC, datetime
from functools import cache

import pytest

from hadavin_sdk.approvals import channel as C
from hadavin_sdk.approvals import gate
from hadavin_sdk.approvals.channel import clean
from hadavin_sdk.guard import runmap
from hadavin_sdk.k1b import redaction as R
from hadavin_sdk.k1b.bundle import Bundle


class SeededData(random.Random):
    """A seeded generator of made-up test data, so every run draws the same cases. Never used for a secret."""


PW = "pass" + "word"
ONE = "hunter2" + "secretXYZ"
ONLY_PLACEHOLDERS = re.compile(rf"(?:{runmap.PLACEHOLDER.pattern})+")

# --- P1 (seed 20261111, 3,000 cases)
SEED, CASES = 20261111, 3000
ALPHA = "qxzjkwvy"
SPACE = [chr(c) for c in range(0x3000) if chr(c).isspace()]
BREAK = list(";&,\"'")
ODD = [
    "\x1b[0m", "\x08", "\x7f", "%20", "%3B", "\\u0041", "\\n", "&#59;", "<", ">", "=", ":", "|", "/", "@",
    "\uff41\uff42", "\uff02", "\uff07", "\u200b", "\u200d", "<SECRET_1>",
]  # fmt: skip
COMPOSITE = [
    "bob.smith@example.com",
    "db01.corp.internal",
    "AKIA" + "IOSFODNN7EXAMPLE",
    "10.20.30.40",
]
KEYS = [
    PW, "api_key", "clientSecret", "accessToken", "PG" + PW.upper(), "pwd", "authorization", "private_key",
    "bearer", "passphrase", "refresh_tokens", "session", PW + "_for_the_primary_database_replica",
]  # fmt: skip
ENDS = set(SPACE) | set(BREAK)


def word(rng):
    return "".join(rng.choice(ALPHA + "0123456789") for _ in range(rng.randint(4, 9)))


def value(rng):
    target = rng.randint(256, 300) if rng.random() < 0.06 else rng.randint(1, 255)
    out = ""
    while len(out) < target:
        r = rng.random()
        out += (
            word(rng)
            if r < 0.55
            else rng.choice(SPACE)
            if r < 0.75
            else rng.choice(BREAK)
            if r < 0.85
            else rng.choice(ODD)
            if r < 0.97
            else rng.choice(COMPOSITE)
        )
    return out[:target]


def runs(v):
    """The runs of 4 or more characters between white space and break characters that are made only of the rare
    alphabet: what must not be readable."""
    out, cur = [], ""
    for ch in v:
        if ch in ENDS:
            if len(cur) >= 4:
                out.append(cur)
            cur = ""
        else:
            cur += ch
    if len(cur) >= 4:
        out.append(cur)
    return [r for r in out if all(c in ALPHA + "0123456789" for c in r)]


def shown(*records):
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
    return list(R.redact_bundle(bundle)[0].deploys)


def _visible(v: str) -> bool:
    return all(0x21 <= ord(ch) <= 0x7E or ch.isspace() for ch in v)


@cache
def p1_results():
    """One run of the generator for the three P1 tests: counts and the first examples of each failure."""
    rng = SeededData(SEED)
    res = {
        "run": 0,
        "over_255": 0,
        "a": [],
        "b": [],
        "c": [],
        "c_checked": 0,
        "x9": [],
        "x9_checked": 0,
    }
    for _ in range(CASES):
        v = value(rng)
        key = rng.choice(KEYS)
        in_secret = rng.random() < 0.25
        res["over_255"] += len(v) > 255
        under = ("cfg" if rng.random() < 0.5 else key) if in_secret else key
        record = {"kind": "Secret", "stringData": {under: v}} if in_secret else {key: v}
        try:
            first, second = shown(record, {"message": "saw " + v + " there"})
        except runmap.RedactionError:
            continue
        res["run"] += 1
        got = (first.get("stringData") or first)[under]
        if not (isinstance(got, str) and (got == R.MASKED or ONLY_PLACEHOLDERS.fullmatch(got))):
            res["a"].append((under, v[:60], got))
        if any(r in got for r in runs(v)):
            res["b"].append((under, v[:60], got))
        try:
            unchanged = runmap.redact_text(v, runmap.RunMap()) == v
        except runmap.RedactionError:
            unchanged = False
        eight = under != "cfg" or (
            len(v) >= 8 and not v.isdigit() and not (v.isascii() and v.isalpha() and v.islower())
        )
        if not (4 <= len(v) <= 255 and not ('"' in v and "'" in v) and unchanged and eight):
            continue
        bucket = ("c", "c_checked") if _visible(v) else ("x9", "x9_checked")
        res[bucket[1]] += 1
        if any(r in second["message"] for r in runs(v)):
            res[bucket[0]].append((under, v[:60], second["message"][:90]))
    return res


def test_p1_the_shown_value_is_only_placeholders_or_the_fixed_mask():
    res = p1_results()
    assert res["run"] == CASES and res["over_255"] >= CASES * 0.05, (res["run"], res["over_255"])
    assert not res["a"], (
        f"part of the value is readable: {len(res['a'])} cases, first {res['a'][:3]!r}"
    )


def test_p1_no_run_of_the_value_is_readable_under_its_key():
    res = p1_results()
    assert not res["b"], (
        f"part of the value is readable: {len(res['b'])} cases, first {res['b'][:3]!r}"
    )


def test_p1_a_plain_value_is_masked_where_it_is_repeated():
    res = p1_results()
    assert res["c_checked"] >= 100, res["c_checked"]
    assert not res["c"], (
        f"readable in the log line: {len(res['c'])} of {res['c_checked']} cases, first {res['c'][:3]!r}"
    )


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="Q8d: sweep of registered secrets before the patterns",
)
def test_x9_a_value_with_special_characters_is_masked_where_it_is_repeated():
    assert not p1_results()["x9"]


def test_x9_has_cases_to_check():
    assert p1_results()["x9_checked"] >= 100, p1_results()["x9_checked"]


# --- "outside code" and the link oracle (a plain token scan; the exemptions E1-E3 are NOT used: call with exempt=False)
def outside_code(text):
    code = set()
    for start, last, ch in gate._closed_fences(text):
        if ch == "`":
            code.update(range(start + 1, last))
    out = []
    for i, line in enumerate(text.split("\n")):
        if i in code:
            continue
        segs = [line] if "``" in line else gate._INLINE_CODE.split(line)
        out += [seg for k, seg in enumerate(segs) if k % 2 == 0]
    return out


def bare_domain_tokens(text, exempt=True):
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


# --- P2 (seed 8, 4,000 cases)
P2_SEED, P2_CASES = 8, 4000
IDS = [
    "bob.smith@example.com", "a.b-c@mail.corp.example.org", "db01.corp.internal", "pay-api.prod.svc.cluster.local",
    "10.20.30.40", "wiki.corp.internal", "priya.nair@example.co.in",
]  # fmt: skip
NOISE = [
    "contact", "restart", "\t\t", " ", "\n", "```\n", "\n```\n", "`", "~~~\n", "<b>", "</b>", "@here", "**", "> ",
    "# ", "- ", PW + "=", "see", "(", ")", "[x]", "<", ">", "&lt;", "%40", "\u3002", ",", ";", ":", "/", "evil.com",
    "http://",
]  # fmt: skip


def p2_text(rng):
    parts = [rng.choice(IDS if rng.random() < 0.4 else NOISE) for _ in range(rng.randint(1, 9))]
    return "".join(p if rng.random() < 0.5 else " " + p + " " for p in parts)


def _standalone(original: str, flat: str) -> bool:
    return (
        re.search(r"(?<![A-Za-z0-9])" + re.escape(original) + r"(?![A-Za-z0-9])", flat) is not None
    )


@cache
def p2_results():
    rng = SeededData(P2_SEED)
    res = {"run": 0, "leak": [], "bare": [], "twice": []}
    for _ in range(P2_CASES):
        text = p2_text(rng)
        try:
            found = runmap.RunMap()
            runmap.redact_text(text, found)
            out = clean(text)
        except runmap.RedactionError:
            continue
        res["run"] += 1
        flat = out.replace("[.]", ".")
        leaked = [o for o in found.values() if o in IDS and _standalone(o, flat)]
        if leaked:
            res["leak"].append((text, out, leaked))
        bad = bare_domain_tokens(out, exempt=False)
        if bad:
            res["bare"].append((text, out, bad))
        if clean(out) != out:
            res["twice"].append((text, out, clean(out)))
    return res


def test_p2_every_identifier_the_redactor_masks_is_masked_on_the_card():
    res = p2_results()
    assert res["run"] >= P2_CASES * 0.9, res["run"]
    assert not res["leak"], (
        f"an identifier is readable on the card: {len(res['leak'])} texts, first {res['leak'][:2]!r}"
    )


def test_p2_no_bare_domain_is_outside_code():
    res = p2_results()
    assert not res["bare"], (
        f"a bare domain is outside code: {len(res['bare'])} texts, first {res['bare'][:2]!r}"
    )


def test_p2_cleaning_a_cleaned_text_changes_nothing():
    res = p2_results()
    assert not res["twice"], f"{len(res['twice'])} texts, first {res['twice'][:2]!r}"


# --- N9 (seed 9, 3,000 cases)
N9_SEED, N9_CASES = 9, 3000
N9_IDS = ["bob.smith@example.com", "db01.corp.internal", "10.20.30.40", "wiki.corp.internal"]
N9_SEC = [ONE, "Zx9" + "tailpart77"]
N9_BITS = [
    "<b>", "</b>", "<i></i>", "<span x>", " ", "\n", PW + "=", PW + "%", "3D", "token: ", "note", ";", "<br/> ",
]  # fmt: skip


def n9_text(rng):
    return "".join(
        rng.choice(N9_IDS + N9_SEC if rng.random() < 0.45 else N9_BITS)
        for _ in range(rng.randint(2, 10))
    )


def n9_readable(text):
    """The originals of the first view's map (seed entries and entries under 4 characters left out) that are readable
    as a standalone word in the text `clean` returns."""
    m1 = C._seeded(text.replace("\x00", ""))
    runmap.redact_text(text, m1, neutralise=C._neutralise)
    flat = clean(text).replace("[.]", ".")
    return [
        o
        for o in m1.values()
        if not o.startswith("\0seed") and len(o) >= 4 and _standalone(o, flat)
    ]


def test_n9_nothing_the_first_view_masked_is_readable_in_the_returned_text():
    rng = SeededData(N9_SEED)
    run, bad = 0, []
    for _ in range(N9_CASES):
        text = n9_text(rng)
        try:
            left = n9_readable(text)
        except runmap.RedactionError:
            continue
        run += 1
        if left:
            bad.append((text, left))
    assert run >= N9_CASES * 0.9, run
    assert not bad, f"readable in the returned text: {len(bad)} texts, first {bad[:2]!r}"
