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


def mask_spans(view: str, pairs: list[tuple[str, str]], minted: dict[str, str] | None = None) -> str:
    """Rev-3 rule (W0): every occurrence of every spelling is a span (overlaps included); a span inside another
    is dropped; a chain of partially overlapping spans is ONE merged span. A merged span of one span gets that
    span's placeholder; of two or more, ONE new placeholder (here `<MERGED_n>`; the build mints it with the
    redactor's own numbering, kind of the longest span) whose value is the merged text, so restore is exact."""
    minted = {} if minted is None else minted
    spans = []
    for ph, sp in pairs:
        for m in re.finditer("(?=" + re.escape(sp) + ")", view):
            spans.append((m.start(), m.start() + len(sp), ph))
    spans.sort(key=lambda t: (t[0], -t[1]))
    kept = []
    for s_, e_, ph in spans:
        if kept and e_ <= max(k[1] for k in kept) and s_ >= min(k[0] for k in kept if k[1] >= e_):
            if any(k[0] <= s_ and e_ <= k[1] for k in kept):
                continue
        kept.append((s_, e_, ph))
    out, pos, i = [], 0, 0
    while i < len(kept):
        s_, e_, ph = kept[i]
        members = [kept[i]]
        j = i + 1
        while j < len(kept) and kept[j][0] < e_:
            e_ = max(e_, kept[j][1])
            members.append(kept[j])
            j += 1
        out.append(view[pos:s_])
        if len(members) == 1:
            out.append(ph)
        else:
            merged = view[s_:e_]
            name = next((k for k, v in minted.items() if v == merged), None)
            if name is None:
                name = f"<MERGED_{len(minted) + 1}>"
                minted[name] = merged
            out.append(name)
        pos, i = e_, j
    out.append(view[pos:])
    return "".join(out)


ROWS = [
    ("partial overlap, A listed first", "id " + A + B[7:] + " end", [("<SECRET_1>", A), ("<SECRET_2>", B)]),
    ("partial overlap, B listed first", "id " + A + B[7:] + " end", [("<SECRET_2>", B), ("<SECRET_1>", A)]),
    ("equal length overlap C|B", "id " + C + B[7:] + " end", [("<SECRET_1>", C), ("<SECRET_2>", B)]),
    ("nested, short first", "id " + A + " end", [("<SECRET_3>", INNER), ("<SECRET_1>", A)]),
    ("three-chain overlap", "id " + A + B[7:] + "Zr8" + " end", [("<SECRET_1>", A), ("<SECRET_2>", B), ("<SECRET_4>", "w4Xy9Zr8")]),
    ("same start, equal length", "id " + A + " end", [("<SECRET_1>", A), ("<SECRET_5>", A[:-1] + "n")]),
    ("mixed domains: escaped short vs raw long", "id " + "x%3Dy" + A + " end", [("<SECRET_3>", "x%3Dy" + A[:3]), ("<SECRET_1>", A)]),
]

print("== (a) main _keep_earlier_masks  |  (d) rev-3 mask_spans")
for name, text, pairs in ROWS:
    values = [v for _, v in pairs]
    a = runmap._keep_earlier_masks(text, pairs)
    minted: dict[str, str] = {}
    d = mask_spans(text, pairs, minted)
    restored = d
    for k, v in {**dict(pairs), **minted}.items():
        restored = restored.replace(k, v)
    print(f"{name} | main: {'LEAKED ' + str(leaked(a, values)) if leaked(a, values) else 'MASKED'} {a!r} | rev3: {'LEAKED ' + str(leaked(d, values)) if leaked(d, values) else 'MASKED'} {d!r} restore-exact={restored == text}")

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
