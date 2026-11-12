"""Seeded property tests of the fold scan through the live path (P2d-1): moved from core PR #50 (748849c)."""

import importlib
import random

from hadavin_sdk.guard import textnorm

redact_mod = importlib.import_module("hadavin_sdk.guard.redact")
redact = redact_mod.redact
_Redactor = redact_mod._Redactor
FOLD_NOTE = getattr(redact_mod, "FOLD_NOTE", "<no FOLD_NOTE on this head>")


_FW = str.maketrans(
    {c: chr(ord(c) + 0xFEE0) for c in "<>!@:/`abcdefghijklmnopqrstuvwxyz"}
)  # full-width forms: live ASCII after the fold


_LIVE = ("<!", "@here", "@channel", "://", "```", "kubectl delete", "<http", "](")


def _is_live(text: str) -> list[str]:
    """Live syntax in the text as written, or (not a fence: the sanitiser breaks fences with an invisible character on purpose) after the fold."""
    folded = textnorm.fold(text).lower()
    return [p for p in _LIVE if p in text.lower() or (p != "```" and p in folded)]


def test_the_live_secret_path_masks_a_key_hidden_behind_look_alikes():
    # the REAL entry point of approval and channel text: channel.clean = redact -> sanitise -> redact (the G5 re-scan)
    from hadavin_sdk.approvals.channel import clean

    spoofed = "key AK" + chr(0x406) + "A" + chr(0x406) + "OSFODNN7EXAMPLE end"
    assert "AKIAIOSFODNN7EXAMPLE" not in clean(spoofed)
    assert chr(0x406) not in clean(spoofed)


def test_text_changed_after_the_mask_is_masked_again_whatever_look_alikes_hide_the_key():
    # class lesson of PR #42: anything transformed AFTER the redact step must be re-checked. Seeded fuzz through the real entry point.
    from hadavin_sdk.approvals.channel import clean

    key = "AKIA" + "IOSFODNN7EXAMPLE"
    alike = {
        "A": chr(0x410),
        "I": chr(0x406),
        "O": chr(0x41E),
        "S": chr(0x405),
        "E": chr(0x415),
        "P": chr(0x420),
    }
    rng = random.Random(50)  # noqa: S311  # a seeded test fuzz, not a secret
    for _ in range(300):
        text = "".join(
            alike[c]
            if c in alike and rng.random() < 0.5
            else c + (chr(0x200B) if rng.random() < 0.15 else "")
            for c in key
        )
        out = clean(f"the key {text} was pasted")
        assert key not in out and textnorm.fold(out).count(key) == 0, (text, out)


def test_a_fold_on_hit_rewrite_never_emits_folded_text_so_nothing_goes_live_after_the_neutralising():
    # class lesson of PR #42 INSIDE the redactor: the second redact of channel.clean runs after sanitise and withhold; its fold-on-hit rewrite
    # used to emit the FOLDED line, turning full-width text into live mentions, links, commands and fences nobody had neutralised.
    from hadavin_sdk.approvals.channel import clean
    from hadavin_sdk.guard.redact import redact

    key = chr(0x410) + "KIA" + "IOSFODNN7EXAMPLE"
    payload = "<!channel> @here kubectl delete pods https://evil.example/x ```".translate(_FW)
    for text in (
        f"{key} {payload}",
        f"{chr(0x410)}KIA<b>IOSFODNN7EXAMPLE {payload}",
        f"{payload} {key}",
    ):
        out = clean(text)
        assert "AKIAIOSFODNN7EXAMPLE" not in textnorm.fold(out), (text, out)
        assert _is_live(out) == [], (text, out, _is_live(out))
        # redact() alone neutralises nothing, but its own rewrite must add no live ASCII: no live syntax as written in its output
        raw = redact(text).text
        assert [p for p in _LIVE if p in raw.lower()] == [], (text, raw)
    assert "<APIKEY_1>" in clean(
        f"{key} {payload}"
    )  # the hit is still reported, by its placeholder


def test_the_look_alike_fuzz_keeps_both_the_key_and_live_syntax_out():
    from hadavin_sdk.approvals.channel import clean

    key = "AKIA" + "IOSFODNN7EXAMPLE"
    alike = {
        "A": chr(0x410),
        "I": chr(0x406),
        "O": chr(0x41E),
        "S": chr(0x405),
        "E": chr(0x415),
        "P": chr(0x420),
    }
    payloads = [
        "<!channel>", "<!here>", "@here", "@channel", "kubectl delete pods", "https://evil.example/x", "```", "[x](http://e.example)",
    ]  # fmt: skip
    rng = random.Random(51)  # noqa: S311  # a seeded test fuzz, not a secret
    for _ in range(300):
        text = "".join(
            alike[c]
            if c in alike and rng.random() < 0.5
            else c + (chr(0x200B) if rng.random() < 0.15 else "")
            for c in key
        )
        if (
            rng.random() < 0.5
        ):  # a tag INSIDE the key: redact finds no key until the sanitiser has removed the tag
            at = rng.randrange(1, len(text) - 1)
            text = text[:at] + "<b>" + text[at:]
        live = rng.choice(payloads)
        live = live.translate(_FW) if rng.random() < 0.7 else live
        line = rng.choice([f"the key {text} {live} end", f"{live} {text}", f"{text}<b>{live}"])
        out = clean(line)
        assert key not in textnorm.fold(out), (line, out)
        assert _is_live(out) == [], (line, out, _is_live(out))
