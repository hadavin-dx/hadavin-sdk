"""A secret's front survived LAYERED encodings. `pct(entity(secret))` cut inside the token
leaked at 7 of 451 cut points. Class: any ordered stack of the supported encodings (percent, HTML entity decimal and
hex, backslash-u, backslash-slash, NFKC full-width, a base64 token front) of any depth up to the cap must not let a
fragment of a registered secret survive the scrub, whatever the cut. Root cause: the decoder applied percent-decoding
AND entity-decoding in one step, so a half entity (`&#10`) that percent-decoding exposed became a newline before the
half-escape strip could see it.

The harness is seeded; `test_the_harness_sees_a_leak` proves it can fail."""

from __future__ import annotations

import base64
import contextlib
import random
import urllib.parse as up

import pytest

from hadavin_sdk import defaults
from hadavin_sdk import tools as tools_mod
from hadavin_sdk.guard import runmap
from hadavin_sdk.guard.runmap import RedactionError
from hadavin_sdk.scrub_settings import ScrubSettings
from hadavin_sdk.tools import MARKER, TRUNCATED, prepare_output
from tests.fixtures import timing

SECRET = "Zk3#9qWd" + "Xv7/pL2m" + "Qa5@Rt8$" + "Yu4%Bn6^" + "Hc1~Jd0*"  # fake, built from parts
SHORT = "Zk3#9qWd" + "Xv7/"  # 12 characters: layers of it stay small
GRAM = 4
SMALL = ScrubSettings(min_redaction_window=1024)
DEFAULT = ScrubSettings()


def _full(c: str) -> str:
    return chr(ord(c) + 0xFEE0) if 0x21 <= ord(c) <= 0x7E else c


ENCODERS = {
    "pct": lambda s: up.quote(s, safe=""),
    "ent": lambda s: "".join(f"&#{ord(c)};" for c in s),
    "enthex": lambda s: "".join(f"&#x{ord(c):X};" for c in s),
    "u": lambda s: "".join(f"\\u{ord(c):04x}" for c in s),
    "bs": lambda s: s.replace("/", "\\/"),
    "nfkc": lambda s: "".join(_full(c) for c in s),
}


def stack(secret: str, names: list[str]) -> str:
    """`names[0]` is applied first (innermost); `b64` wraps `user:secret` and is only ever innermost."""
    out = secret
    for n in names:
        out = base64.b64encode(f"user:{out}".encode()).decode() if n == "b64" else ENCODERS[n](out)
    return out


def build(enc: str, k: int, win: int, secret: str) -> str:
    """A text whose look-back window cut lands `k` bytes into the (whitespace-free) token `enc`. Before the token
    come whole entity-encoded copies of the secret, so the scrub swaps to the decoded view (the swap is what put
    the fragment on screen) and the final byte cut does not hide the fragment."""
    cut = win - 256
    eb = enc.encode()
    k = max(1, min(k, len(eb), cut - 2))
    start = cut - k
    unit = ENCODERS["ent"](secret) + " "
    pre = " " + unit * ((start - 1) // len(unit))
    pre += " " * (start - len(pre.encode()))
    return pre + enc + "." * max(win + 600 - start - len(eb), 600)


def survivors(out: str, secret: str) -> list[str]:
    o = out.replace(MARKER, "").replace(TRUNCATED, "")
    views = {o}
    with contextlib.suppress(RedactionError):  # a view that cannot be built is no leak
        views.add(tools_mod._decoded(o))
    return sorted(
        {
            secret[i : i + GRAM]
            for i in range(len(secret) - GRAM + 1)
            if any(secret[i : i + GRAM] in v for v in views)
        }
    )


def run(
    secret: str, names: list[str], k: int, scrub: ScrubSettings, handed: bool = True
) -> list[str]:
    win = scrub.min_redaction_window
    mb = 500 if win == 1024 else 2000
    out = prepare_output(
        build(stack(secret, names), k, win, secret), {}, mb, [secret] if handed else [], scrub=scrub
    )
    return survivors(out, secret)


# ---- the recorded failing cases, every cut point of the layered spellings ------------------------------


@pytest.mark.parametrize(
    "names",
    [
        ["ent", "pct"],
        ["pct", "ent"],
        ["u", "pct"],
        ["pct", "pct"],
        ["nfkc", "pct"],
        ["ent", "ent"],
        ["pct", "u"],
        ["enthex", "pct"],
        ["pct", "enthex"],
    ],
)
def test_every_cut_point_of_a_layered_secret_leaves_no_fragment(names):
    n = len(stack(SHORT, names).encode())
    leaks = {k: s for k in range(1, n + 1) if (s := run(SHORT, names, k, SMALL))}
    assert not leaks, leaks


@pytest.mark.parametrize("k", [87, 178, 200])
def test_evidence_14_pct_of_entity_at_its_recorded_cut_points(k):
    assert run(SECRET, ["ent", "pct"], k, SMALL) == []
    assert run(SECRET, ["ent", "pct"], k, DEFAULT) == []


def test_the_half_entity_percent_decoding_exposes_is_not_read_as_a_newline():
    """The root cause, directly: the tail of `%26%2310` is half of `&#10`."""
    assert tools_mod._decoded_clean("Zk3%26%2310") == "Zk3"
    assert tools_mod._decoded_clean("Zk3%2526%252310") == "Zk3"


def test_the_harness_sees_a_leak():
    """Sensitivity control: with no secret handed over nothing is scrubbed, and the harness must report it."""
    assert run(SECRET, ["ent", "pct"], 87, SMALL, handed=False) != []


# ---- seeded fuzz over arbitrary orderings and depths -----------------------------------------------------------


def _case(rnd: random.Random) -> tuple[list[str], int]:
    depth = rnd.choice([1, 2, 2, 3, 3, 4])
    names = [rnd.choice(list(ENCODERS)) for _ in range(depth)]
    if rnd.random() < 0.15:
        names[0] = "b64"
    return names, rnd.randint(1, 100000)


def _fuzz(seed: int, cases: int, scrub: ScrubSettings) -> list[tuple[list[str], int, list[str]]]:
    rnd = random.Random(seed)  # noqa: S311 - a seeded test generator, not a secret
    bad = []
    for _ in range(cases):
        names, kraw = _case(rnd)
        n = len(stack(SHORT, names).encode())
        k = 1 + kraw % n
        if s := run(SHORT, names, k, scrub):
            bad.append((names, k, s))
    return bad


def test_fuzz_small_window_19700_cases():
    bad = _fuzz(20261103, 19700, SMALL)
    assert not bad, bad[:5]


def test_fuzz_default_window_300_cases():
    bad = _fuzz(20261104, 300, DEFAULT)
    assert not bad, bad[:5]


# ---- the depth cap fails closed ------------------------------------------------------------------------------


def test_a_text_nested_past_the_cap_is_refused_not_shown():
    deep = SHORT
    for _ in range(defaults.SCRUB_MAX_LAYERS + 2):
        deep = up.quote(deep, safe="")
    with pytest.raises(tools_mod.TooDeep):
        tools_mod._decoded(deep)
    out = prepare_output(" " + deep, {}, 500, [SHORT], scrub=SMALL)
    assert SHORT[:GRAM] not in out and out.startswith(MARKER)


def test_a_text_nested_to_the_cap_is_still_read():
    deep = SHORT
    for _ in range(defaults.SCRUB_MAX_LAYERS):
        deep = up.quote(deep, safe="")
    out = prepare_output("x " + deep + " y", {}, 500, [SHORT], scrub=SMALL)
    assert MARKER in out and SHORT[:GRAM] not in out


# ---- siblings: error_reason cuts after the scrub, including a layered secret --------------------------------


@pytest.mark.parametrize(
    "names", [["ent", "pct"], ["pct", "ent"], ["u", "pct"], ["pct", "pct", "pct"]]
)
@pytest.mark.parametrize("pad", [0, 40, 100, 120, 130, 150])
def test_error_reason_leaves_no_fragment_of_a_layered_secret(names, pad):
    msg = "x" * pad + stack(SHORT, names) + " tail"
    out = tools_mod.error_reason(RuntimeError(msg), [SHORT], scrub=SMALL)
    assert survivors(out, SHORT) == []


# ---- timing (perf step only; no wall clock in the default run) -----------------------------------------------


@pytest.mark.perf
@pytest.mark.parametrize("names", [["ent", "pct"], ["pct"] * 4, ["u", "pct", "ent"]])
def test_100kb_adversarial_layered_input_is_bounded(names):
    enc = stack(SHORT, names)
    big = (enc + " ") * (100_000 // (len(enc) + 1))
    soup = "%26%2310" * 12_500
    for text in (big, soup, "%25" * 33_000 + "41"):
        t = timing.CLOCK()
        prepare_output(text, {}, 2000, [SHORT])
        assert timing.CLOCK() - t < 20


def test_ascii_shortcut_in_nfkc_equals_the_full_canonical_form_for_every_ascii_character():
    """The shortcut is only sound if NFKC plus invisible-removal is the identity on ASCII: checked for all 128."""
    for cp in range(128):
        assert tools_mod.nfkc(chr(cp)) == runmap.canonical(chr(cp))


def test_ascii_text_never_reaches_the_normaliser(monkeypatch):
    """The percent-encoded expanding text is ASCII: the refusal must come from the decoded text, not the raw one."""
    calls = []
    monkeypatch.setattr(runmap, "fits_after_nfkc", lambda t: calls.append(t) or t)
    tools_mod.nfkc("%EF%B7%BA" * 10)
    assert calls == []


# --- round 6: pattern-shaped secrets behind layers, and the cut after the redaction ----------------------------------------------------
@pytest.mark.parametrize(
    "spelling",
    [
        "%41KIA" + "IOSFODNN7EXAMPLE",
        "&#65;KIA" + "IOSFODNN7EXAMPLE",
        "password%3Dhunter2",
        "&#x70;assword=hunter2",
    ],
)
def test_a_pattern_shaped_secret_behind_a_layer_is_masked_in_every_tool_result_without_a_handed_out_secret(
    spelling,
):
    out = prepare_output(f"line {spelling} end", {}, 16384, [])
    assert "IOSFODNN7EXAMPLE" not in out and "hunter2" not in out


def test_a_text_nested_past_the_cap_with_no_secret_handed_out_is_not_shown():
    deep = "%41KIA" + "IOSFODNN7EXAMPLE"
    for _ in range(defaults.SCRUB_MAX_LAYERS + 2):
        deep = up.quote(deep, safe="")
    assert prepare_output(deep, {}, 16384, []).startswith(MARKER)


def test_error_reason_redacts_a_jwt_before_the_160_character_cut():
    jwt = (
        "eyJhbGciOiJIUzI1NiJ9."
        + "eyJzdWIiOiJhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhIn0."
        + "c2lnbmF0dXJlc2lnbmF0dXJl"
    )
    msg = (
        "failed with " * 10 + jwt
    )  # words, so only the token is a secret; a cut at 150 or 160 lands inside it
    reason = tools_mod.error_reason(ValueError(msg), [])
    assert "eyJzdWIi" not in reason and "eyJhbGci" not in reason


def test_error_reason_with_an_expanding_message_and_a_handed_out_secret_is_refused():
    with pytest.raises(RedactionError):
        tools_mod.error_reason(ValueError("ﷺ" * 87000), [SECRET])


def test_a_mime_wrapped_base64_of_a_handed_out_secret_is_masked():
    # 50 bytes of padding: the secret straddles the first wrap, so no single line decodes to the whole secret
    body = base64.b64encode(("p" * 50 + SECRET + " " * 60).encode()).decode()
    wrapped = "\n".join(body[i : i + 76] for i in range(0, len(body), 76))
    assert "\n" in wrapped
    for text in (wrapped, wrapped.replace("\n", "\r\n")):
        out = prepare_output("attachment:\n" + text + "\nend", {}, 16384, [SECRET])
        assert SECRET not in out and body[:30] not in out and body[-30:] not in out


def test_a_base64_of_a_quoted_or_hex_spelling_of_a_handed_out_secret_is_masked():
    for spelling in (
        up.quote(SECRET, safe=""),
        SECRET.encode().hex(),
        SECRET.encode().hex().upper(),
    ):
        tok = base64.b64encode(("x=" + spelling).encode()).decode()
        out = prepare_output(f"blob {tok} end", {}, 16384, [SECRET])
        assert tok not in out, spelling
