"""Round 12: a class-level property test for the area every review round found a new hole in: a secret VALUE written in
an encoding, with a value-ending character in it, behind junk, must leave no fragment (every suffix of length 3 or more
of each of its parts) in the output of `clean()` and of the producers. Seeded and time-bounded."""

from __future__ import annotations

import random
import re

import pytest

from hadavin_sdk import tools as tools_mod
from hadavin_sdk.approvals import channel as channel_mod
from hadavin_sdk.guard import runmap
from hadavin_sdk.runtime import tick as tick_mod

BS = chr(92)
_TAGS = re.compile(r"<[^<>]{0,200}>")
ALPHA = "qxzjkwvy"
WIDE = ALPHA + "QXZJ0123456789-._+/"  # digits, upper case and URL-safe punctuation
# lower-case letters no placeholder, key word or tag in the generated text contains in a row
KEYS = ["password", "secret", "api_key", "passwd"]
# value-ending characters: the redactor's value pattern stops at white space, `;`, `&`, `,` and quotes
ENDS = [" ", "\t", ";", "&", ",", '"', "'", "\r", "\x0b", "\x0c", " ", "\x1c", "\x85", " ", "\n"]
SEED = 20261104
CASES = 1200


def _encode_char(rng: random.Random, ch: str) -> str:
    kind = rng.choice(["percent", "entity", "hex", "u", "U"])
    cp = ord(ch)
    if kind == "percent":
        return "".join(f"%{b:02X}" for b in ch.encode("utf-8"))
    if kind == "entity":
        return f"&#{cp};" if rng.random() < 0.5 else f"&#x{cp:X};"
    if kind == "hex" and cp < 256:
        return BS + "x" + format(cp, "02x")
    if kind == "u" and cp < 0x10000:
        return BS + "u" + format(cp, "04x")
    return BS + "U" + format(cp, "08x")


def _word(rng: random.Random, lo: int, hi: int, wide: bool = False) -> str:
    return "".join(rng.choice(WIDE if wide else ALPHA) for _ in range(rng.randint(lo, hi)))


def _case(rng: random.Random):
    """(text, parts, strict, tagged, base): the text holds a secret whose value is `part1 END part2` with END encoded, plus
    junk. Kinds: `key=value`, a flag `--key=value`, a URL credential `scheme://user:value@host`. `base` is the text without
    the secret (a fragment that also occurs there is not a leak)."""
    kind = rng.choice(["assign", "assign", "flag", "url"])
    key = rng.choice(KEYS)
    wide = rng.random() < 0.5
    long = rng.random() < 0.02
    part1 = _word(rng, 4200, 4300) if long else _word(rng, 4, 14, wide)
    part2 = _word(rng, 4, 14, wide)
    end = rng.choice(ENDS if kind != "url" else [" ", ";", ",", '"', "'", "\t"])
    sep = rng.choice(["=", "%3D", "&#61;", BS + "x3d"]) if kind != "url" else "="
    value = part1 + _encode_char(rng, end) + part2
    head = {"assign": key, "flag": "--" + key, "url": "postgres://admin:"}[kind]
    secret = f"{head}{sep if kind != 'url' else ''}{value}" + (
        "@db.example/x" if kind == "url" else ""
    )
    tagged = False
    if rng.random() < 0.4:  # a markup split: only a CARD path (sanitise) can join what a tag splits
        tagged = True
        lo = 1  # a tag may start inside the key
        if kind != "url" and rng.random() < 0.5:
            # a tag that becomes a real space only splits the KEY/SEPARATOR region (`password%<i> </i>3Dx`): a space inside the
            # value would end the value for any redactor
            i = rng.randint(lo, len(head) + len(sep))
            tag = "<i> </i>"
        else:
            i = rng.randint(lo, len(secret) - 1) if not long else rng.randint(lo, len(head) + 5)
            tag = rng.choice(["<b></b>", "<span></span>", "<!-- x -->"])
        secret = secret[:i] + tag + secret[i:]
    junk = []
    for _ in range(rng.choice([0, 0, 3, 40, 120])):
        junk.append(f"<IPV4_{rng.randint(1, 400)}>")
    if rng.random() < 0.5:
        junk.append(
            "and " + "%41KIA" + "IOSFODNN7EXAMPLE"
        )  # a decode-only secret: it makes the decoded view the result
    if rng.random() < 0.3:
        junk.append(f"api_key=AAAA{rng.randint(1000, 9999)}")
    rng.shuffle(junk)
    joiner = rng.choice([" ", "\n", " , "])
    mid = len(junk) // 2
    text = joiner.join(["note"] + junk[:mid] + [secret] + junk[mid:] + ["end"])
    base = joiner.join(["note"] + junk[:mid] + junk[mid:] + ["end"])
    # a flag or url secret has a plain key part that is not secret; the parts are what must not appear
    return text, [part1, part2], sep == "=" or kind == "url", tagged, base


def _fragments(parts, base):
    out = set()
    for p in parts:
        # every suffix of length >= 3 (>= 5 in the wide alphabet, whose short windows can occur in a placeholder), but not
        # the whole long value (checked by its tail); a fragment that also occurs in the text without the secret is not a leak
        tails = [p[i:] for i in range(max(0, len(p) - 40), len(p) - 2)]
        out.update(
            t for t in tails if (len(t) >= 5 or t.islower() and t.isalpha()) and t not in base
        )
    return out


def _slack(text):
    """The Slack block gets `req.summary`, which `summary()` built with `clean()`: the real flow is clean, then the block."""
    from types import SimpleNamespace

    from hadavin_sdk.approvals.slack_channel import SlackChannel

    ch = SlackChannel.__new__(SlackChannel)
    ch.max_card_chars = 10**6
    req = SimpleNamespace(
        summary=channel_mod.clean(text),
        current_step=0,
        steps=[1],
        approval_id="a",
        status="PENDING",
    )
    return ch._blocks(req, None)[0]["text"]["text"]


PRODUCERS = {
    "clean": channel_mod.clean,
    "redact_text": lambda t: runmap.redact_text(t, {}),
    "redact_untrusted": lambda t: runmap.redact_untrusted(t, {}),
    "safe_head": lambda t: runmap.safe_head(t, 10**6),
    "prepare_output": lambda t: tools_mod.prepare_output(t, {}, 262144, []),
    "error_reason": lambda t: tools_mod.error_reason(ValueError(t), []),
    "tick": lambda t: tick_mod._message(ValueError(t)).replace("\n", " "),
    "slack": _slack,
}


def test_no_fragment_of_an_encoded_secret_value_survives_any_producer():
    rng = random.Random(SEED)  # noqa: S311 - a seeded test generator
    failures = []
    names = sorted(PRODUCERS)
    done = 0
    for i in range(CASES):
        text, parts, strict, tagged, base = _case(rng)
        frags = _fragments(parts, base)
        pool = [n for n in names if n in {"clean", "slack"}] if tagged else names
        for name in rng.sample(pool, 1) + ["clean"]:
            try:
                out = PRODUCERS[name](text)
            except runmap.RedactionError:
                continue  # refused: nothing shown (fail closed)
            leaked = [f for f in frags if f in out]
            if leaked and not strict:
                # an encoded `=`: pass one cannot read the key, so the protection is that of the PLAIN spelling of the same
                # text (the decoded text, tags deleted): an encoding must not leave more than the plain form leaves
                plain = PRODUCERS[name](runmap.undo(_TAGS.sub("", text)))
                leaked = [f for f in leaked if f not in plain]
            if leaked:
                failures.append(
                    (
                        i,
                        name,
                        max(leaked, key=len)[:12],
                        text[:160].encode("unicode_escape").decode(),
                    )
                )
        done += 1
    assert not failures, f"{len(failures)} leaks, first: {failures[:6]}"
    assert done == CASES


def test_a_tag_longer_than_200_characters_splitting_an_encoded_separator_leaves_nothing():
    tag = "<span " + "a" * 260 + "></span>"
    out = channel_mod.clean("note password%" + tag + "3Dxyz9abc end")
    assert "xyz9abc" not in out, out


def test_a_zero_width_and_a_spaced_tag_inside_a_plain_value_are_joined_and_masked():
    for text in ("password=ab<i> </i>cdz9q end", "password=ab<b></b>cdz9q end"):
        out = channel_mod.clean("note " + text)
        assert "cdz9q" not in out and "abcdz9q" not in out, (text, out)


def test_the_summary_fallback_fails_closed_when_the_expected_outcome_alone_holds_too_many_pairable_values():
    from hadavin_sdk.approvals.requests import summary
    from hadavin_sdk.models import Plan, Target

    expected = " ".join(f"password=ab%3Bzz{i}" for i in range(300))
    plan = Plan(
        run_id="run-1",
        agent_id="test-agent",
        action_id="create_draft_record",
        action_version=1,
        risk_class="reversible",
        inputs={"title": "x"},
        target=Target(system="fixture-records", ref=None),
        idempotency_key="run-1:create_draft_record",
        expected_outcome=expected,
    )
    text = summary(plan)  # must not raise
    assert "zz1" not in text and "too large to show" in text


def test_a_masked_value_nested_deeper_than_the_cap_refuses_the_text_instead_of_skipping_its_pairing():
    import urllib.parse as up

    deep = "ab cd"
    for _ in range(tools_mod.defaults.SCRUB_MAX_LAYERS + 2):
        deep = up.quote(deep, safe="")
    with pytest.raises(runmap.RedactionError):
        runmap.redact_text(f"password={deep} and %41KIA" + "IOSFODNN7EXAMPLE", {})


def test_a_fold_on_hit_line_stays_note_only_through_every_producer_and_view():
    # a key hidden behind Cyrillic look-alikes (with or without a tag split) next to full-width live syntax: the redactor's fold-on-hit
    # rewrite must emit the fixed note and placeholders only, never folded text, so no mention, link, command or fence goes live
    import importlib

    from hadavin_sdk.guard import textnorm

    FOLD_NOTE = getattr(
        importlib.import_module("hadavin_sdk.guard.redact"),
        "FOLD_NOTE",
        "<no FOLD_NOTE on this head>",
    )

    fw = str.maketrans({c: chr(ord(c) + 0xFEE0) for c in "<>!@:/`abcdefghijklmnopqrstuvwxyz"})
    payloads = [
        "<!channel>", "<!here>", "@here", "@channel", "kubectl delete pods", "https://evil.example/x", "```", "[x](http://e.example)",
    ]  # fmt: skip
    live = ("<!", "@here", "@channel", "://", "kubectl delete", "](")
    alike = {"A": chr(0x410), "I": chr(0x406), "O": chr(0x41E), "S": chr(0x405), "E": chr(0x415)}
    key = "AKIA" + "IOSFODNN7EXAMPLE"
    rng = random.Random(SEED + 1)  # noqa: S311 - a seeded test generator
    names = sorted(PRODUCERS)
    for _ in range(300):
        text = "".join(alike[c] if c in alike and rng.random() < 0.5 else c for c in key)
        if rng.random() < 0.5:  # a tag inside the key: no hit until the tag is gone
            at = rng.randrange(1, len(text) - 1)
            text = text[:at] + "<b>" + text[at:]
        pay = rng.choice(payloads)
        pay = pay.translate(fw) if rng.random() < 0.7 else pay
        line = rng.choice([f"the key {text} {pay} end", f"{pay} {text}", f"{text} {pay}"])
        tagged = "<b>" in text
        # producers that neutralise text a person reads (clean, slack) get every case; the others only the untagged ones
        pool = [n for n in names if n in {"clean", "slack"}] if tagged else names
        for name in rng.sample(pool, 1) + ["clean"]:
            try:
                out = PRODUCERS[name](line)
            except runmap.RedactionError:
                continue  # refused: nothing shown (fail closed)
            low, folded = out.lower(), textnorm.fold(out).lower()
            assert key not in textnorm.fold(out), (name, line, out)
            if name in {"clean", "slack"}:
                assert [p for p in live if p in low or p in folded] == [], (name, line, out)
            if (
                FOLD_NOTE in out
            ):  # from the note to the end of its line: only the note and placeholders
                tail = next(ln for ln in out.splitlines() if FOLD_NOTE in ln)
                tail = tail[tail.index(FOLD_NOTE) :]
                assert re.fullmatch(
                    re.escape(FOLD_NOTE) + r"(?: <[A-Z0-9]+_\d+>)*", tail.strip()
                ), (name, out)
