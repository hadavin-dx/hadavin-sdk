"""D2 probe (PR H rev 3): overlapping known values. Runs on main (2a8c2aac) from the clean worktree.

(a) main's `_keep_earlier_masks` with partial overlap, equal length, nested short-first, mixed spelling domains;
(b) main's redactor sweep of known values (`redact(text, mapping=run_map)`) with the same overlaps;
(c) main's `redact_text` with a run map that holds two partially overlapping values;
(d) the rev-3 reference rule `mask_spans` (union of every match span, one pass) on the same inputs.
Verdict per row: LEAKED when a piece of 4+ characters of any value that stands in the input stays readable."""

from __future__ import annotations

import re
import sys

from hadavin_sdk.guard import runmap
from hadavin_sdk.guard.redact import redact

print("hadavin_sdk loaded from", sys.modules["hadavin_sdk"].__file__)

A = "Qz7" + "kPQRSTmn"  # 10 chars; its tail PQRSTmn is the head of B
B = "PQRSTmn" + "w4Xy9"  # 12 chars
C = "Hh2" + "PQRSTmn"  # equal length to A (10), shares the 7-char overlap with B's head
INNER = "PQRSTmn"  # nested inside A and B


def leaked(out: str, values: list[str]) -> list[str]:
    bad = []
    for v in values:
        for i in range(len(v) - 3):
            if v[i : i + 4] in out:
                bad.append(v[i : i + 4])
                break
    return bad


def mask_spans(view: str, pairs: list[tuple[str, str]]) -> str:
    """Rev-3 rule: every occurrence of every spelling (overlaps included) is a span; touching or overlapping spans
    merge; each merged span is replaced by the placeholders of the spellings that start in it, in start order."""
    spans = []
    for ph, sp in pairs:
        for m in re.finditer("(?=" + re.escape(sp) + ")", view):
            spans.append((m.start(), m.start() + len(sp), ph))
    if not spans:
        return view
    spans.sort()
    out, pos, i = [], 0, 0
    while i < len(spans):
        s, e, ph = spans[i]
        phs = [ph]
        j = i + 1
        while j < len(spans) and spans[j][0] < e:
            e = max(e, spans[j][1])
            if spans[j][2] not in phs:
                phs.append(spans[j][2])
            j += 1
        out.append(view[pos:s])
        out.append("".join(phs))
        pos, i = e, j
    out.append(view[pos:])
    return "".join(out)


ROWS = [
    ("partial overlap, A listed first", "id " + A + B[7:] + " end", [("<SECRET_1>", A), ("<SECRET_2>", B)]),
    ("partial overlap, B listed first", "id " + A + B[7:] + " end", [("<SECRET_2>", B), ("<SECRET_1>", A)]),
    ("equal length overlap C|B", "id " + C + B[7:] + " end", [("<SECRET_1>", C), ("<SECRET_2>", B)]),
    ("nested, short first", "id " + A + " end", [("<SECRET_3>", INNER), ("<SECRET_1>", A)]),
    ("mixed domains: escaped short vs raw long", "id " + "x%3Dy" + A + " end", [("<SECRET_3>", "x%3Dy" + A[:3]), ("<SECRET_1>", A)]),
]

print("== (a) main _keep_earlier_masks  |  (d) rev-3 mask_spans")
for name, text, pairs in ROWS:
    values = [v for _, v in pairs]
    a = runmap._keep_earlier_masks(text, pairs)
    d = mask_spans(text, pairs)
    print(f"{name} | main: {'LEAKED ' + str(leaked(a, values)) if leaked(a, values) else 'MASKED'} {a!r} | rev3: {'LEAKED ' + str(leaked(d, values)) if leaked(d, values) else 'MASKED'} {d!r}")

print("== (b) main redact() sweep of known values (run map pre-filled)")
for name, text, pairs in ROWS:
    values = [v for _, v in pairs]
    out = redact(text, mapping=dict(pairs)).text
    print(f"{name} | {'LEAKED ' + str(leaked(out, values)) if leaked(out, values) else 'MASKED'} | {out!r}")

print("== (c) main redact_text / redact_untrusted with the run map")
for name, text, pairs in ROWS[:3]:
    values = [v for _, v in pairs]
    for label, fn in (("redact_text", runmap.redact_text), ("redact_untrusted", runmap.redact_untrusted)):
        m = dict(pairs)
        out = fn(text, m)
        print(f"{name} | {label} | {'LEAKED ' + str(leaked(out, values)) if leaked(out, values) else 'MASKED'} | {out!r}")
