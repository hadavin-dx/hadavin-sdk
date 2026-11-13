#!/usr/bin/env python3
"""Q2 evidence runner: seeded fuzz of lead_desk identity (email key) and the receipt/claim logic.

Run (from the repo copy, TMPDIR private):
  cd /home/user/work/q2-base; TMPDIR=/home/user/work/q2-tmp PYTHONPATH=src:.:tests \
    /home/user/work/final-venv/bin/python q2-fuzz.py --campaign a|b|c --seed N --out FILE.json
Only stdlib `random` with the fixed seed given; no network; no spend. Records, never judges the product code:
it prints counts and verbatim counterexamples (ascii() of each input, so invisible characters stay visible).
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import tempfile
import time
import unicodedata
from pathlib import Path

sys.path[:0] = [p for p in ("src", ".", "tests") if os.path.isdir(p)]
from lead_desk import identity  # noqa: E402
from support import build_rig, call  # noqa: E402

MAX_CE = 50
SRC = ("form", "webhook")
NAME = "Test Person"
DOC_RULE = "README.md:28 + identity.py:44-46 (trim, lower-case, nothing more)"
DOC_PLUS = "docs/limits.md:24 (plus-tag and dots are different leads) + README.md:28"
DOC_REJECT = (
    "identity.py:97 (any Unicode C* character in the email) / identity.py:115-116 (control char) / "
    "identity.py:20 (no whitespace inside)"
)
UND_CASE = "UNDOCUMENTED (docs say 'lower-cased'; str.lower is not case folding)"

LOC_SYL = ["an", "ka", "mi", "to", "re", "lu", "sa", "vi", "ne", "do", "ha", "po", "ju", "be", "ro", "zi"]
LOC_ACC = ["josé", "müller", "zoë", "françois", "łukasz", "åse", "björn",
           "émile", "anaïs", "núñez"]
LOC_SPECIAL = ["straße", "οδυσσεύς", "σοφίας",
               "ıstanbul", "ǆana", "æsir"]
DOMAINS = ["example.test", "example.com", "mail.example.test", "sub.example.com", "corp-x.example.test",
           "a1.example.com"]
UPAD = [" ", " ", "　", " ", " ", " ", " ", " "]
ZW = ["​", "‌", "‍", "﻿", "⁠"]
BIDI = ["‮", "‭", "‪", "‫", "‬", "⁦", "⁧", "⁨", "⁩", "‎",
        "‏", "؜"]
HOMO = {"a": "а", "e": "е", "o": "о", "p": "р", "c": "с", "x": "х", "i": "і",
        "j": "ј"}


def A(s: object) -> str:
    return ascii(s)


def key_of(s: str) -> tuple[str, str | None]:
    """(verdict, key) from the real identity.check_payload."""
    c = identity.check_payload({"name": NAME, "email": s})
    return c.kind, c.email_key


class Sink:
    def __init__(self) -> None:
        self.ce: list[dict] = []
        self.n_ce_total = 0
        self.samples: dict[str, list[dict]] = {}
        self.tally: dict[str, dict[str, int]] = {}
        self.labels: dict[str, int] = {}

    def add(self, cls: str, outcome: str) -> None:
        t = self.tally.setdefault(cls, {})
        t[outcome] = t.get(outcome, 0) + 1

    def counterexample(self, d: dict) -> None:
        self.n_ce_total += 1
        lab = str(d.get("label"))
        self.labels[lab] = self.labels.get(lab, 0) + 1
        if len(self.ce) < MAX_CE:
            self.ce.append(d)

    def sample(self, cls: str, d: dict, k: int = 3) -> None:
        s = self.samples.setdefault(cls, [])
        if len(s) < k:
            s.append(d)


def rand_local(rng: random.Random) -> str:
    kind = rng.random()
    if kind < 0.60:
        loc = "".join(rng.choice(LOC_SYL) for _ in range(rng.randint(2, 4)))
    elif kind < 0.90:
        loc = rng.choice(LOC_ACC) + rng.choice(LOC_SYL)
    else:
        loc = rng.choice(LOC_SPECIAL)
    if rng.random() < 0.25 and len(loc) > 2:
        loc = loc[: len(loc) // 2] + "." + loc[len(loc) // 2 :]
    if rng.random() < 0.15:
        loc += "+" + rng.choice(["sales", "news", "x1", "tag"])
    return loc + str(rng.randint(0, 99999))


def make_base(rng: random.Random, i: int) -> str:
    return f"{rand_local(rng)}x{i}@{rng.choice(DOMAINS)}".lower()


def rand_case(rng: random.Random, s: str) -> str:
    return "".join(c.upper() if rng.random() < 0.5 else c.lower() for c in s)


def fullwidth(s: str) -> str:
    return "".join(chr(ord(c) - 0x20 + 0xFF00) if (c.isascii() and c.isalnum()) else c for c in s)


def variants(rng: random.Random, b: str) -> list[tuple[str, str, str | None]]:
    """(variant, class, doc-if-different)."""
    loc, _, dom = b.partition("@")
    out: list[tuple[str, str, str | None]] = []
    out += [(b.upper(), "case:upper", UND_CASE), (b.capitalize(), "case:capitalize", UND_CASE),
            (b.swapcase(), "case:swapcase", UND_CASE), (b.title(), "case:title", UND_CASE)]
    for _ in range(3):
        out.append((rand_case(rng, b), "case:random", UND_CASE))
    out.append((loc + "@" + dom.upper(), "case:domain-upper", UND_CASE))
    for _ in range(3):
        out.append((" " * rng.randint(1, 5) + b + " " * rng.randint(0, 5), "pad:ascii-space", None))
    for _ in range(5):
        l = "".join(rng.choice(UPAD + [" "]) for _ in range(rng.randint(0, 3)))
        r = "".join(rng.choice(UPAD + [" "]) for _ in range(rng.randint(0, 3)))
        out.append((l + b + r, "pad:unicode-space", None))
    for _ in range(12):
        l = "".join(rng.choice(UPAD + [" "]) for _ in range(rng.randint(0, 3)))
        r = "".join(rng.choice(UPAD + [" "]) for _ in range(rng.randint(0, 3)))
        out.append((l + rand_case(rng, b) + r, "case+pad", UND_CASE))
    for nf in ("NFC", "NFD", "NFKC", "NFKD"):
        out.append((unicodedata.normalize(nf, b), "unicode:" + nf, DOC_RULE))
    out.append((unicodedata.normalize("NFD", b.upper()), "unicode:NFD+upper", DOC_RULE))
    out.append((fullwidth(b), "fullwidth", DOC_RULE))
    for _ in range(2):
        z = rng.choice(ZW)
        p = rng.randint(0, len(loc))
        out.append((loc[:p] + z + loc[p:] + "@" + dom, "zero-width", DOC_REJECT))
    base_loc = loc.split("+")[0]
    out.append((base_loc + "+" + rng.choice(["a", "b", "c"]) + "@" + dom, "plus:add/replace", DOC_PLUS))
    out.append((base_loc + "@" + dom, "plus:remove", DOC_PLUS))
    p = rng.randint(1, max(1, len(loc) - 1))
    out.append((loc[:p] + "." + loc[p:] + "@" + dom, "dot:insert", DOC_PLUS))
    out.append((loc.replace(".", "") + "@" + dom, "dot:remove", DOC_PLUS))
    p = rng.randint(1, max(1, len(loc) - 1))
    out.append((loc[:p] + " " + loc[p:] + "@" + dom, "inner-space", DOC_REJECT))
    out.append((b.replace("@", " @ ", 1), "space-around-at", DOC_REJECT))
    h = "".join(HOMO.get(c, c) for c in loc[:6]) + loc[6:]
    out.append((h + "@" + dom, "homoglyph", DOC_RULE))
    out.append(("\t" + b + "\n", "pad:tab-newline", DOC_REJECT))
    return out


def campaign_a(seed: int, n_bases: int, out: dict) -> None:
    rng = random.Random(seed)
    sink = Sink()
    tp = Path(tempfile.mkdtemp(dir=os.environ["TMPDIR"], prefix="a-"))
    t0 = time.time()
    sent = 0
    n_viol = 0
    rig = build_rig(tp)
    desk = rig.desk
    bases = [make_base(rng, i) for i in range(n_bases)]
    assert len(set(bases)) == n_bases
    try:
        for i, b in enumerate(bases):
            r0 = desk.process("webhook", f"b{i}", {"name": NAME, "email": b})
            sent += 1
            if r0.body.get("verdict") != "new":
                sink.counterexample({"label": "VIOLATION base not new", "input": A(b), "reply": r0.body})
                n_viol += 1
                continue
            lead0 = r0.body["lead_id"]
            for j, (v, cls, doc) in enumerate(variants(rng, b)):
                r = desk.process("form", f"v{i}-{j}", {"name": NAME, "email": v})
                sent += 1
                verdict = r.body.get("verdict")
                lead = r.body.get("lead_id")
                kv, kk = key_of(v)
                same = lead == lead0 and verdict == "duplicate"
                if kv == "ok" and kk != v.strip().lower():
                    n_viol += 1
                    sink.counterexample({"label": "VIOLATION key != strip().lower()", "input": A(v), "key": A(kk)})
                outcome = "review" if verdict == "review" else ("same-identity" if same else "different-identity")
                sink.add(cls, outcome)
                lower_same = v.strip().lower() == b
                if (kv == "review") != (verdict == "review"):
                    n_viol += 1
                    sink.counterexample({"label": "VIOLATION desk verdict disagrees with check_payload", "variant": A(v),
                                         "check": kv, "verdict": verdict})
                if verdict == "review":
                    if cls in ("pad:tab-newline", "zero-width", "inner-space", "space-around-at"):
                        sink.sample(cls, {"label": "documented as rejected at " + str(doc), "base": A(b), "variant": A(v)})
                    else:
                        n_viol += 1
                        sink.counterexample({"label": "VIOLATION valid-by-construction variant went to review",
                                             "class": cls, "base": A(b), "variant": A(v)})
                    continue
                if lower_same:  # strip().lower() equals the base: the documented rule says ONE identity
                    if not same:
                        n_viol += 1
                        sink.counterexample({"label": "VIOLATION (documented as merged)", "class": cls, "base": A(b),
                                             "variant": A(v), "outcome": outcome, "lead_id": lead,
                                             "base_lead_id": lead0})
                    continue
                if same:  # strip().lower() differs from the base but the desk merged them
                    n_viol += 1
                    sink.counterexample({"label": "MERGE OF DOCUMENTED-DIFFERENT", "class": cls, "base": A(b),
                                         "variant": A(v), "outcome": outcome})
                    continue
                if cls.startswith("case"):
                    sink.counterexample({"label": UND_CASE, "class": cls, "base": A(b), "variant": A(v),
                                         "variant_key": A(v.strip().lower()), "outcome": outcome,
                                         "lead_id": lead, "base_lead_id": lead0})
                    continue
                sink.sample(cls, {"label": "documented as different at " + str(doc), "base": A(b), "variant": A(v),
                                  "outcome": outcome, "key": A(kk)})
        out["db_leads"] = rig.leads()
        out["db_receipts"] = rig.query("SELECT count(*) FROM receipts")[0][0]
    finally:
        desk.close()
    out.update(
        campaign="a", seed=seed, bases=n_bases, variants_sent=sent - n_bases, requests_sent=sent,
        wall_s=round(time.time() - t0, 1), violations=n_viol, counterexamples_total=sink.n_ce_total,
        counterexamples_listed=len(sink.ce), label_counts=sink.labels, counterexamples=sink.ce, tally=sink.tally,
        doc_samples=sink.samples,
    )


# ---------------------------------------------------------------- campaign b
def rv_local(rng: random.Random, n: int | None = None) -> str:
    n = n or rng.randint(3, 14)
    return "".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(n))


def gen_pair(rng: random.Random) -> tuple[str, str, str, bool]:
    """(a, b, type, valid_expected_both). Different persons by construction unless type starts with 'same'."""
    t = rng.choice(["sub1", "ins", "del", "swapadj", "domain1", "tld", "homoglyph", "dots", "plus", "plus2", "namesw",
                    "long", "long-end", "empty", "ws-only", "nul", "ctrl", "bidi", "same-case", "same-pad", "nf",
                    "unrelated", "kelvin", "fullwidth"])
    loc = rv_local(rng)
    d = rng.choice(DOMAINS)
    e = f"{loc}@{d}"
    if t == "sub1":
        p = rng.randrange(len(loc))
        c = rng.choice([x for x in "abcdefghijklmnopqrstuvwxyz0123456789" if x != loc[p]])
        return e, loc[:p] + c + loc[p + 1 :] + "@" + d, t, True
    if t == "ins":
        p = rng.randrange(len(loc) + 1)
        return e, loc[:p] + rng.choice("abz09") + loc[p:] + "@" + d, t, True
    if t == "del":
        p = rng.randrange(len(loc))
        return e, loc[:p] + loc[p + 1 :] + "@" + d, t, len(loc) > 1
    if t == "swapadj":
        p = rng.randrange(len(loc) - 1)
        return e, loc[:p] + loc[p + 1] + loc[p] + loc[p + 2 :] + "@" + d, t, True
    if t == "domain1":
        dd = rv_local(rng, 5)
        return f"{loc}@{dd}.example.test", f"{loc}@{dd[:-1]}x.example.test", t, True
    if t == "tld":
        return f"{loc}@example.com", f"{loc}@example.co", t, True
    if t == "homoglyph":
        loc = "pa" + loc
        idx = [k for k, c in enumerate(loc) if c in HOMO]
        k = rng.choice(idx)
        h = rng.choice([HOMO[loc[k]], chr(ord(loc[k]) - 0x20 + 0xFF00), "ı" if loc[k] == "i" else HOMO[loc[k]]])
        return f"{loc}@{d}", loc[:k] + h + loc[k + 1 :] + "@" + d, t, True
    if t == "dots":
        loc2 = loc[:3] + "." + loc[3:] if len(loc) > 4 else loc + ".x"
        i0 = loc2.index(".")
        v = rng.choice([(loc2, loc2.replace(".", "")), (loc2, loc2.replace(".", "..")), (loc2 + ".", loc2),
                        ("." + loc2, loc2), (loc2, loc2[: i0 + 2] + "." + loc2[i0 + 2 :])])
        return v[0] + "@" + d, v[1] + "@" + d, t, True
    if t == "plus":
        return f"{loc}+a@{d}", f"{loc}@{d}", t, True
    if t == "plus2":
        return f"{loc}+a@{d}", f"{loc}+b@{d}", t, True
    if t == "namesw":
        f, l = rv_local(rng, 5), rv_local(rng, 6)
        sep = rng.choice([".", "_", "-", ""])
        return f"{f}{sep}{l}@{d}", f"{l}{sep}{f}@{d}", t, True
    if t == "long":
        n = rng.choice([60, 64, 100, 200, 230, 240])
        base = rv_local(rng, n)
        k = rng.choice([0, n // 2, n - 1])
        c = "b" if base[k] != "b" else "c"
        return base + "@e.test", base[:k] + c + base[k + 1 :] + "@e.test", t, True
    if t == "long-end":
        tot = rng.choice([250, 252, 253, 254, 255, 256, 300, 1000, 20000])
        dom = "@example.test"
        base = rv_local(rng, tot - len(dom))
        other = base[:-1] + ("b" if base[-1] != "b" else "c")
        return base + dom, other + dom, t, False
    if t == "empty":
        return rng.choice(["", e]), (rng.choice(["", e]) if rng.random() < 0.5 else ""), t, False
    if t == "ws-only":
        return rng.choice([" ", "   ", " ", "　　", "\t", "\n"]), e, t, False
    if t == "nul":
        p = rng.randrange(len(loc) + 1)
        return loc[:p] + "\x00" + loc[p:] + "@" + d, (e if rng.random() < 0.5 else loc[:p] + loc[p:] + "@" + d), t, False
    if t == "ctrl":
        c = rng.choice(["\x01", "\x07", "\x08", "\x1b", "\x7f", "\x85", "\x1f", "\r", "\n", "\t", "\x0b", "\x0c"])
        p = rng.randrange(len(loc) + 1)
        return loc[:p] + c + loc[p:] + "@" + d, e, t, False
    if t == "bidi":
        c = rng.choice(BIDI)
        p = rng.randrange(len(loc) + 1)
        return loc[:p] + c + loc[p:] + "@" + d, e, t, False
    if t == "same-case":
        return e, rand_case(rng, e), t, True
    if t == "same-pad":
        return e, " " * rng.randint(0, 3) + e.upper() + " " * rng.randint(0, 3), t, True
    if t == "nf":
        e2 = f"{rng.choice(LOC_ACC)}{rv_local(rng, 4)}@{d}"
        return e2, unicodedata.normalize("NFD", e2), t, True
    if t == "unrelated":
        return e, f"{rv_local(rng)}@{rng.choice(DOMAINS)}", t, True
    if t == "kelvin":
        return f"{loc}k@{d}", f"{loc}K@{d}", t, True
    if t == "fullwidth":
        return e, fullwidth(e), t, True
    raise AssertionError(t)


NO_REVIEW_EXPECTED_EXCLUDE = ("empty", "ws-only", "nul", "ctrl", "bidi", "long-end", "kelvin")


def campaign_b(seed: int, n_pairs: int, out: dict, chunk: int = 10000) -> None:
    rng = random.Random(seed)
    sink = Sink()
    t0 = time.time()
    n_viol = 0
    types: dict[str, int] = {}
    ok_ok = reviews = sent = unexpected_review = done = 0
    while done < n_pairs:
        tp = Path(tempfile.mkdtemp(dir=os.environ["TMPDIR"], prefix="b-"))
        rig = build_rig(tp)
        desk = rig.desk
        okey_to_lead: dict[str, str] = {}
        lead_to_okey: dict[str, str] = {}
        try:
            for _ in range(min(chunk, n_pairs - done)):
                a, b, t, valid_exp = gen_pair(rng)
                done += 1
                types[t] = types.get(t, 0) + 1
                res = []
                for side, s in (("A", a), ("B", b)):
                    r = desk.process("webhook", f"p{done}{side}", {"name": NAME, "email": s})
                    sent += 1
                    res.append(r.body)
                kA, kB = key_of(a), key_of(b)
                for s, body in ((a, res[0]), (b, res[1])):
                    if body.get("verdict") == "review":
                        reviews += 1
                        if valid_exp and t not in NO_REVIEW_EXPECTED_EXCLUDE:
                            unexpected_review += 1
                            sink.counterexample({"label": "UNEXPECTED REVIEW for a well-formed address", "type": t,
                                                 "input": A(s)[:300], "reply": body})
                        continue
                    ok = s.strip().lower()
                    lead = body["lead_id"]
                    if ok in okey_to_lead:
                        if okey_to_lead[ok] != lead:
                            n_viol += 1
                            sink.counterexample({"label": "VIOLATION false split", "type": t, "input": A(s)[:300],
                                                 "lead": lead, "expected_lead": okey_to_lead[ok]})
                    else:
                        okey_to_lead[ok] = lead
                    if lead in lead_to_okey and lead_to_okey[lead] != ok:
                        n_viol += 1
                        sink.counterexample({"label": "VIOLATION FALSE MERGE", "type": t, "input": A(s)[:300],
                                             "merged_with": A(lead_to_okey[lead])[:300], "lead": lead})
                    lead_to_okey.setdefault(lead, ok)
                if kA[0] == "ok" and kB[0] == "ok":
                    ok_ok += 1
                    oracle_same = a.strip().lower() == b.strip().lower()
                    if (kA[1] == kB[1]) != oracle_same:
                        n_viol += 1
                        sink.counterexample({"label": "VIOLATION key equality != oracle", "type": t, "a": A(a)[:300],
                                             "b": A(b)[:300], "key_a": A(kA[1])[:300], "key_b": A(kB[1])[:300]})
                    sink.add(t, "ok-merged-as-documented" if oracle_same else "ok-kept-apart")
                    if not oracle_same and t in ("nf", "dots", "plus", "plus2", "homoglyph", "fullwidth", "namesw"):
                        sink.sample(t, {"a": A(a), "b": A(b), "key_a": A(kA[1]), "key_b": A(kB[1]),
                                        "doc": DOC_PLUS if t in ("dots", "plus", "plus2") else DOC_RULE})
                else:
                    sink.add(t, "a side is review (no identity, cannot merge)")
                    if t in ("bidi", "nul", "ctrl", "empty", "ws-only", "kelvin", "long-end"):
                        sink.sample(t + ":review", {"a": A(a)[:120], "b": A(b)[:120], "verdicts": [kA[0], kB[0]]})
        finally:
            desk.close()
    out.update(
        campaign="b", seed=seed, pairs=n_pairs, requests_sent=sent, wall_s=round(time.time() - t0, 1),
        violations=n_viol, counterexamples_total=sink.n_ce_total, counterexamples_listed=len(sink.ce),
        label_counts=sink.labels, counterexamples=sink.ce, pair_types=types, both_sides_ok=ok_ok,
        side_reviews=reviews, unexpected_reviews=unexpected_review, tally=sink.tally, doc_samples=sink.samples,
    )


# ---------------------------------------------------------------- campaign c
def shuffled_json(rng: random.Random, obj: dict) -> str:
    """Same content, re-ordered keys at every level, random extra whitespace between tokens."""

    def ws() -> str:
        return "".join(rng.choice([" ", "\t", "\n", "\r\n", ""]) for _ in range(rng.randint(0, 3)))

    def enc(o: object) -> str:
        if isinstance(o, dict):
            items = list(o.items())
            rng.shuffle(items)
            body = ("," + ws()).join(
                json.dumps(k, ensure_ascii=rng.random() < 0.5) + ws() + ":" + ws() + enc(v) for k, v in items
            )
            return "{" + ws() + body + ws() + "}"
        return json.dumps(o, ensure_ascii=rng.random() < 0.5)

    return ws() + enc(obj) + ws()


def campaign_c(seed: int, n_replays: int, out: dict) -> None:
    rng = random.Random(seed)
    from lead_desk.server import serve_in_thread

    sink = Sink()
    tp = Path(tempfile.mkdtemp(dir=os.environ["TMPDIR"], prefix="c-"))
    rig = build_rig(tp)
    desk = rig.desk
    base_url, stop = serve_in_thread(desk)
    t0 = time.time()
    n_viol = 0
    kinds = {"same-object": 0, "reordered-json-process": 0, "same-id-other-body": 0, "http-reordered-ws": 0}
    n_first = 0
    try:
        for i in range(n_replays):
            src = rng.choice(SRC)
            ref = f"R{i}-" + "".join(rng.choice("abcdefXYZ09 -_é") for _ in range(rng.randint(0, 40)))
            email = f"{rv_local(rng, 8)}n{i}@{rng.choice(DOMAINS)}"
            payload = {"name": rng.choice(["Ada Lovelace", "Zoë Müller", "Test Person", "O'Neil"]),
                       "email": rng.choice([email, email.upper()]),
                       "phone": rng.choice([None, "+441234567890", "555 0100"]),
                       "company": rng.choice([None, "Example Ltd"]),
                       "message": rng.choice([None, "Hello\nthere", "café é"])}
            payload = {k: v for k, v in payload.items() if v is not None}
            r1 = desk.process(src, ref, payload)
            if r1.body.get("verdict") != "new":
                n_viol += 1
                sink.counterexample({"label": "VIOLATION first send not new", "src": src, "ref": A(ref), "reply": r1.body})
                continue
            n_first += 1
            kind = rng.choices(list(kinds), weights=[40, 30, 10, 20])[0]
            kinds[kind] += 1
            if kind == "same-object":
                r = desk.process(src, ref, dict(payload))
                st, body = r.status, r.body
            elif kind == "reordered-json-process":
                r = desk.process(src, ref, json.loads(shuffled_json(rng, payload)))
                st, body = r.status, r.body
            elif kind == "same-id-other-body":
                r = desk.process(src, ref, dict(payload, name="Someone Else", email=payload["email"].swapcase()))
                st, body = r.status, r.body
            else:
                raw = shuffled_json(rng, {"source": src, "source_ref": ref, "payload": payload}).encode()
                st, body = call(base_url, "POST", "/leads", raw=raw)
            exp_match = kind != "same-id-other-body"
            bad = (st != 201 or body.get("verdict") != "new" or body.get("lead_id") != r1.body["lead_id"]
                   or body.get("receipt_id") != r1.body["receipt_id"] or body.get("replayed") is not True
                   or body.get("payload_matches") is not exp_match)
            sink.add(kind, "bad" if bad else "ok")
            if bad:
                n_viol += 1
                sink.counterexample({"label": "VIOLATION replay answered differently", "kind": kind, "src": src,
                                     "ref": A(ref), "status": st, "reply": body, "first_reply": r1.body,
                                     "payload": A(payload)})
        rows_l = rig.leads()
        rows_r = rig.query("SELECT count(*) FROM receipts")[0][0]
        rows_f = rig.query("SELECT count(*) FROM followups")[0][0]
        distinct_keys = rig.query("SELECT count(DISTINCT email_key) FROM leads")[0][0]
        out["rows"] = {"leads": rows_l, "receipts": rows_r, "followups": rows_f, "distinct_email_keys": distinct_keys,
                       "expected_unique": n_first}
        if not (rows_l == rows_r == rows_f == distinct_keys == n_first):
            n_viol += 1
            sink.counterexample({"label": "VIOLATION row counts", **out["rows"]})
    finally:
        try:
            stop()
        finally:
            desk.close()
    out.update(
        campaign="c", seed=seed, replays=sum(kinds.values()), first_sends=n_first, wall_s=round(time.time() - t0, 1),
        violations=n_viol, counterexamples_total=sink.n_ce_total, counterexamples_listed=len(sink.ce),
        label_counts=sink.labels, counterexamples=sink.ce, kinds=kinds, tally=sink.tally,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True, choices=["a", "b", "c"])
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--n", type=int, default=0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out: dict = {}
    if a.campaign == "a":
        campaign_a(a.seed, a.n or 2400, out)
    elif a.campaign == "b":
        campaign_b(a.seed, a.n or 200000, out)
    else:
        campaign_c(a.seed, a.n or 20000, out)
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=True), encoding="utf-8")
    keys = ("campaign", "seed", "wall_s", "violations", "counterexamples_total", "requests_sent", "variants_sent",
            "pairs", "replays", "label_counts")
    print(json.dumps({k: v for k, v in out.items() if k in keys}))


if __name__ == "__main__":
    main()
