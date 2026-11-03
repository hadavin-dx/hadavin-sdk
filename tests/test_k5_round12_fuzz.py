"""Round 12: a class-level property test for the area every review round found a new hole in: a secret VALUE written in
an encoding, with a value-ending character in it, behind junk, must leave no fragment (every suffix of length 3 or more
of each of its parts) in the output of `clean()` and of the producers. Seeded and time-bounded."""

from __future__ import annotations

import random
import re
import time

from hadavin_sdk import tools as tools_mod
from hadavin_sdk.approvals import channel as channel_mod
from hadavin_sdk.guard import runmap
from hadavin_sdk.runtime import tick as tick_mod

BS = chr(92)
_TAGS = re.compile(r"<[^<>]{0,200}>")
ALPHA = "qxzjkwvy"  # lower-case letters no placeholder, key word or tag in the generated text contains in a row
KEYS = ["password", "secret", "api_key", "passwd"]
# value-ending characters: the redactor's value pattern stops at white space, `;`, `&`, `,` and quotes
ENDS = [" ", "\t", ";", "&", ",", '"', "'", "\r", "\x0b", "\x0c", " ", "\x1c", "\x85", " ", "\n"]
SEED = 20261104
CASES = 1800
BUDGET_S = 55


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


def _word(rng: random.Random, lo: int, hi: int) -> str:
    return "".join(rng.choice(ALPHA) for _ in range(rng.randint(lo, hi)))


def _case(rng: random.Random):
    """(text, parts): the text holds `key=part1 END part2` with END encoded, plus junk; parts are the secret's pieces."""
    key = rng.choice(KEYS)
    long = rng.random() < 0.02
    part1 = _word(rng, 4200, 4300) if long else _word(rng, 4, 14)
    part2 = _word(rng, 4, 14)
    end = rng.choice(ENDS)
    sep = rng.choice(["=", "%3D", "&#61;", BS + "x3d"])
    value = part1 + _encode_char(rng, end) + part2
    secret = f"{key}{sep}{value}"
    tagged = False
    if rng.random() < 0.4:  # a markup split: only a CARD path (sanitise) can join what a tag splits
        tagged = True
        if rng.random() < 0.5:
            # a tag that becomes a real space only splits the KEY/SEPARATOR region (`password%<i> </i>3Dx`): a space inside the
            # value would end the value for any redactor
            i = len(key) + rng.randint(0, len(sep))
            tag = "<i> </i>"
        else:
            i = (
                rng.randint(len(key), len(secret) - 1)
                if not long
                else rng.randint(len(key), len(key) + 5)
            )
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
    pieces = junk[: len(junk) // 2] + [secret] + junk[len(junk) // 2 :]
    text = rng.choice([" ", "\n", " , "]).join(["note"] + pieces + ["end"])
    return text, [part1, part2], sep == "=", tagged


def _fragments(parts):
    out = set()
    for p in parts:
        # every suffix of length >= 3, but not the whole long value (checked by its tail)
        tails = [p[i:] for i in range(max(0, len(p) - 40), len(p) - 2)]
        out.update(tails)
    return out


def _slack(text):
    from types import SimpleNamespace

    from hadavin_sdk.approvals.slack_channel import SlackChannel

    ch = SlackChannel.__new__(SlackChannel)
    ch.max_card_chars = 10**6
    req = SimpleNamespace(
        summary=text, current_step=0, steps=[1], approval_id="a", status="PENDING"
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
    started = time.monotonic()
    failures = []
    names = sorted(PRODUCERS)
    done = 0
    for i in range(CASES):
        if time.monotonic() - started > BUDGET_S:
            break
        text, parts, strict, tagged = _case(rng)
        frags = _fragments(parts)
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
    assert done >= 1200, f"only {done} cases ran inside the time bound"
