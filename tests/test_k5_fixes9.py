"""Review 5 of PR #42 (3fd024d): "a handed-out secret (or its front) reaches the model through a cut, an unscrubbed
slice, or an undecoded spelling".

M-1 an exception message was cut BEFORE the scrub; M-2 a front spelled in NFKC-compatible characters was never
recognised; M-3 a cut made by `_fit` inside the scrub loop could be turned unreadable by a later decoded-view swap;
M-4 a cut inside a base64 token that wraps a secret; M-5 `\\/` (and the other JSON escapes) were not undone; plus the
constants in validated config and a counted-steps bound on the strip.

Cuts use the `raw_cap=4096` route (same `_cut` and boundary rule as the window cut, cheap). Where a cut inside the
scrub loop is needed the redactor's cap is lowered with monkeypatch (every size check reads it at call time)."""

from __future__ import annotations

import base64

import pytest
from pydantic import ValidationError

from hadavin_sdk import defaults
from hadavin_sdk import tools as tools_mod
from hadavin_sdk.config import EvidenceSettings, ScrubSettings
from hadavin_sdk.guard import runmap
from tests.k5_support import TOOL

CAP = defaults.MAX_REDACT_CHARS
RAW_CAP = 4096
BS = chr(92)
TRUNC = tools_mod.TRUNCATED
OTHER = "Hy8@" + "Rt4nWs6d"  # fakes, built from parts
ALNUM = "Zk39qWdRt5"
KEY = "Qm7xT2vLp9" + "Wn4Zc8Rb1Hd5Ke3Ys6Ga0Fj2Uo7Ti9Mn4"  # 40 characters


def _cut_body(
    spelled: str,
    off: int,
    secrets: list[str],
    other_spelled: str = "",
    scrub: ScrubSettings | None = None,
) -> str:
    """The text before the marker when the cut falls after `off` characters of `spelled`; `other_spelled` (another
    handed-out secret) stands whole earlier. Lengths are in BYTES: `_cut` counts bytes."""
    tail = (scrub or ScrubSettings()).tail_window
    head = spelled[:off]
    pad = "." * (
        RAW_CAP
        - tail
        - len(head.encode())
        - len(other_spelled.encode())
        - (10 if other_spelled else 0)
    )
    raw = (
        pad + other_spelled + ("." * 10 if other_spelled else "") + head + spelled[off:] + "." * 600
    )
    kwargs = {"scrub": scrub} if scrub is not None else {}
    out = tools_mod.prepare_output(raw, {}, CAP, secrets, raw_cap=RAW_CAP, **kwargs)
    assert out.endswith(TRUNC), "the text was not cut: the test does not test the cut"
    return out[: -len(TRUNC)]


# ---- M-1: an exception message is scrubbed before it is cut --------------------------------------------------------------


@pytest.mark.parametrize("prefix", [100, 130, 150, 159])
def test_m1_error_reason_scrubs_the_whole_message_before_the_cut(prefix):
    message = "upstream rejected key " + "x" * (prefix - 22) + KEY
    out = tools_mod.error_reason(RuntimeError(message), [KEY])
    assert KEY[:3] not in out and KEY[-3:] not in out
    assert len(out) <= len("RuntimeError: ") + 160


def test_m1_a_refusal_message_is_scrubbed_before_its_200_character_cut():
    out = tools_mod.error_reason(tools_mod.ToolRefused("bad " + "x" * 180 + KEY), [KEY])
    assert KEY[:3] not in out and len(out) <= 200


def test_m1_an_encoded_secret_in_a_huge_message_is_scrubbed_too():
    pct = "".join(f"%{b:02X}" for b in KEY.encode())
    out = tools_mod.error_reason(RuntimeError("y" * 300_000 + " " + pct), [KEY])
    assert KEY[:3] not in out and "%51" not in out


def test_m1_end_to_end_through_the_toolbox_the_model_never_sees_a_front_of_the_secret():
    spec = tools_mod.ToolSpec(**{**TOOL, "secret_names": ["tool-key"]})

    def fn(args, ctx):
        key = ctx.secret("tool-key")
        raise RuntimeError("upstream rejected key " + "x" * 130 + " " + key)

    box = tools_mod.ToolBox(
        {"read_logs": spec},
        {"read_logs": fn},
        timeout_s=2,
        secret_resolver_for=lambda s: lambda name: KEY,
    )
    out = box.invoke("read_logs", {"name": "x"}, {})
    assert out.error and "RuntimeError" in out.text
    assert KEY[:3] not in out.text


# ---- M-2: a front spelled in NFKC-compatible characters -----------------------------------------------------------------


def _map(s: str, f) -> str:
    return "".join(f(c) for c in s)


def _fullwidth(c: str) -> str:
    return chr(ord(c) + 0xFEE0) if 0x21 <= ord(c) <= 0x7E else c


def _mathbold(c: str) -> str:
    if c.isascii() and c.isupper():
        return chr(0x1D400 + ord(c) - 65)
    if c.isascii() and c.islower():
        return chr(0x1D41A + ord(c) - 97)
    if c.isdigit():
        return chr(0x1D7CE + int(c))
    return c


def _circled(c: str) -> str:
    if c.isascii() and c.isupper():
        return chr(0x24B6 + ord(c) - 65)
    if c.isascii() and c.islower():
        return chr(0x24D0 + ord(c) - 97)
    if c.isdigit():
        return chr(0x2460 + int(c) - 1) if c != "0" else chr(0x24EA)
    return c


def _super(c: str) -> str:
    return {"0": "⁰", "1": "¹", "2": "²", "3": "³"}.get(c) or (
        chr(0x2070 + int(c)) if c.isdigit() else c
    )


COMPAT = {
    "fullwidth": _fullwidth,
    "mathbold": _mathbold,
    "circled": _circled,
    "superscript": _super,
}


@pytest.mark.parametrize("name", list(COMPAT))
def test_m2_the_compat_spelling_reads_as_the_secret(name):
    assert tools_mod._decoded(_map(ALNUM, COMPAT[name])) == ALNUM


def _compat_cases():
    for name, f in COMPAT.items():
        for off in range(1, len(_map(ALNUM, f).encode()) + 1):
            yield pytest.param(name, off, id=f"{name}-{off}")


@pytest.mark.parametrize(("name", "off"), list(_compat_cases()))
@pytest.mark.parametrize("other_whole", [False, True], ids=["alone", "other-whole"])
def test_m2_a_cut_at_every_offset_of_a_compat_spelling_leaves_no_front(name, off, other_whole):
    spelled = _map(ALNUM, COMPAT[name])
    off = min(off, len(spelled) - 1)
    other = _map(OTHER, COMPAT[name]) if other_whole else ""
    body = _cut_body(spelled, off, [ALNUM, OTHER], other)
    assert body.endswith("." * 10 if other else "."), (name, off, ascii(body[-12:]))
    assert tools_mod._decoded(body[-12:])[-3:] != ALNUM[:3]
    assert not any(ch in body[-8:] for ch in _map(ALNUM[:2], COMPAT[name]))


# ---- M-3: a cut by `_fit` inside the loop, then a decoded-view swap ---------------------------------------------------


def _pct(s: str) -> str:
    return "".join(f"%{b:02X}" for b in s.encode())


def _ent(s: str) -> str:
    return "".join(f"&#{ord(c)};" for c in s)


def _jsn(s: str) -> str:
    out = []
    for c in s:
        n = ord(c)
        if n >= 0x10000:
            n -= 0x10000
            out.append(f"{BS}u{0xD800 + (n >> 10):04x}{BS}u{0xDC00 + (n & 0x3FF):04x}")
        else:
            out.append(f"{BS}u{n:04x}")
    return "".join(out)


M3_SECRET = {"entity": OTHER, "percent": chr(0xE9) + "Tn2Kq8x", "json": chr(0x1F600) + "Lm4Qa7"}


def _m3_cases():
    for shape, spell in (("entity", _ent), ("percent", _pct), ("json", _jsn)):
        for off in range(1, len(spell(M3_SECRET[shape]))):
            yield pytest.param(shape, off, id=f"{shape}-{off}")


@pytest.mark.parametrize(("shape", "off"), list(_m3_cases()))
def test_m3_a_fit_cut_then_a_decoded_swap_leaves_no_front_of_the_cut_secret(
    monkeypatch, shape, off
):
    spell = {"entity": _ent, "percent": _pct, "json": _jsn}[shape]
    cap = 20_000
    monkeypatch.setattr(defaults, "MAX_REDACT_CHARS", cap)
    a = "Zx9Qw" + "+"  # grows 6 -> 17 characters when scrubbed: that is what triggers `_fit`
    c = (
        "Lp3" + "Vn8Xd2"
    )  # spelled in percent, whole, before the cut: needs the decoded view (the swap)
    b = M3_SECRET[shape]  # spelled in `shape` and cut
    at = cap - len(tools_mod.TRUNCATED) - tools_mod.TAIL_WINDOW  # where `_fit` really cuts
    head = spell(b)[:off]
    copies = 800
    c_spelled = _pct(c)
    n1 = at - copies * 18 - len(c_spelled) - 10 - len(head.encode())
    assert n1 > 300
    raw = (
        (a + " ") * copies
        + "." * n1
        + c_spelled
        + "." * 10
        + head
        + spell(b)[off:]
        + "." * (cap - at + 300)
    )
    out = tools_mod.prepare_output(raw, {}, cap, [a, c, b], raw_cap=10 * cap)
    assert out.endswith(TRUNC), "the _fit cut did not happen: the test does not test it"
    # the whole text before the marker: nothing of `b` (its first characters) is left anywhere near the cut
    body = out.removesuffix(TRUNC)
    assert body.endswith("." * 10), ascii(
        body[-16:]
    )  # the cut front is gone, not turned into U+FFFD or a tab
    assert b[:2] not in body[-40:]
    assert spell(b)[:6] not in body[-60:]


# ---- M-4: a cut inside a base64 token that wraps a secret --------------------------------------------------------------


def _b64_cases():
    blob = ('{"user":"svc-admin","note":"??>>","password":"' + ALNUM + '","n":1}').encode()
    for alphabet, enc in (
        ("standard", base64.b64encode(blob).decode()),
        ("urlsafe", base64.urlsafe_b64encode(blob).decode()),
    ):
        for off in range(8, len(enc)):
            yield pytest.param(enc, off, id=f"{alphabet}-{off}")


def _tail_decoded(body: str) -> bytes:
    i = len(body)
    while i and body[i - 1] in tools_mod._B64_CHARS:
        i -= 1
    t = body[i:].replace("-", "+").replace("_", "/").rstrip("=")
    if len(t) % 4 == 1:
        t = t[:-1]
    return base64.b64decode(t + "=" * (-len(t) % 4)) if t else b""


@pytest.mark.parametrize(("enc", "off"), list(_b64_cases()))
def test_m4_a_cut_inside_a_base64_token_that_wraps_a_secret_leaves_no_front_of_it(enc, off):
    body = _cut_body(enc, off, [ALNUM])
    dec = _tail_decoded(body)
    secret = ALNUM.encode()
    for p in range(len(dec)):
        assert not (len(dec) - p >= 2 and secret.startswith(dec[p:])), (off, dec[p:])


# ---- M-5: JSON escapes beyond \\uXXXX, and layers nested the other way --------------------------------------------------


AWS = "wJalrXUtnFEMI/K7MDENG/bPxRfiCY"


def test_m5_a_slash_written_as_backslash_slash_is_undone():
    echoed = AWS.replace("/", BS + "/")
    out = tools_mod.prepare_output("body " + echoed + " end", {}, 16_384, [AWS])
    assert "wJalr" not in out and "<SECRET_REDACTED>" in out


def test_m5_escaped_slashes_mixed_with_a_u_escape_are_scrubbed_whole():
    echoed = AWS.replace("/", BS + "/").replace("F", BS + "u0046")
    out = tools_mod.prepare_output("body " + echoed + " end", {}, 16_384, [AWS])
    assert "wJalr" not in out and "K7MDENG" not in out


@pytest.mark.parametrize(
    ("secret", "echoed"),
    [
        ('Ab"9Qz7Kp', "Ab" + BS + '"9Qz7Kp'),
        ("Ab" + BS + "9Qz7Kp", "Ab" + BS + BS + "9Qz7Kp"),
        ("Ab9\tQz7Kp", "Ab9" + BS + "tQz7Kp"),
        ("Ab9" + chr(10) + "Qz7Kp", "Ab9" + BS + "nQz7Kp"),
    ],
    ids=["quote", "backslash", "tab", "newline"],
)
def test_m5_the_other_json_escapes_are_undone(secret, echoed):
    out = tools_mod.prepare_output("x " + echoed + " y", {}, 16_384, [secret])
    assert "Qz7Kp" not in out and "<SECRET_REDACTED>" in out


def test_m5_the_decode_repeats_so_a_double_backslash_is_read_twice_but_the_pass_itself_reads_json():
    assert runmap.json_unescape(BS + BS + "u0041") == BS + "u0041"  # one pass, as JSON is read
    assert tools_mod._decoded(BS + "u0041") == "A"
    assert (
        tools_mod._decoded(BS + BS + "u0041") == "A"
    )  # nested layers: the view is deliberately generous


def test_m1_layers_nested_either_way_are_undone():
    sec = "Ab9Qz7Kp"
    for echoed in (
        "&#37;41b9Qz7Kp",
        "%26%2365;b9Qz7Kp",
    ):  # percent written as an entity; an entity percent-encoded
        out = tools_mod.prepare_output("x " + echoed + " y", {}, 16_384, [sec])
        assert "b9Qz7Kp" not in out, echoed


def test_m1_hex_is_read_in_any_case():
    sec = "Ab9Qz7KpWd"
    hexed = sec.encode().hex()
    mixed = "".join(c.upper() if i % 3 == 0 else c for i, c in enumerate(hexed))
    out = tools_mod.prepare_output("x " + mixed + " y", {}, 16_384, [sec])
    assert mixed not in out and "<SECRET_REDACTED>" in out


def test_m1_a_hex_front_in_mixed_case_is_stripped_at_a_cut():
    sec = "Ab9Qz7KpWd"
    hexed = sec.encode().hex()
    mixed = "".join(c.upper() if i % 3 == 0 else c for i, c in enumerate(hexed))
    body = _cut_body(mixed, 8, [sec])
    assert body.endswith(".")


# ---- the strip does bounded work --------------------------------------------------------------------------------------


def test_m3_the_strip_makes_at_most_fragment_scan_decode_calls(monkeypatch):
    calls = []
    real = tools_mod._decoded
    monkeypatch.setattr(tools_mod, "_decoded", lambda t: (calls.append(1), real(t))[1])
    real_clean = tools_mod._decoded_clean
    monkeypatch.setattr(
        tools_mod, "_decoded_clean", lambda t, *w: (calls.append(1), real_clean(t, *w))[1]
    )
    tools_mod._first_decoded.cache_clear()
    forms = sorted(tools_mod._secret_forms("Zk39qWdRt5"))
    adversarial = "Z" * 6000 + TRUNC  # every position reads as the first character of a form
    tools_mod._strip_fragment(adversarial, forms)
    assert len(calls) <= ScrubSettings().fragment_scan + 3
    calls.clear()
    small = ScrubSettings(fragment_scan=64)
    tools_mod._strip_fragment(adversarial, forms, small)
    assert len(calls) <= 64 + 3


# ---- the constants are validated configuration ----------------------------------------------------------------------


def test_the_scrub_constants_are_validated_config_with_one_set_of_defaults():
    s = EvidenceSettings().scrub
    assert (s.tail_window, s.min_redaction_window, s.min_secret) == (256, 4096, 6)
    assert (s.fragment_scan, s.fragment_min, s.partial_end) == (4096, 1, 10)
    assert s.tail_window == tools_mod.TAIL_WINDOW and s.min_secret == tools_mod.MIN_SCRUBBED_SECRET
    for bad in (
        {"tail_window": 1},
        {"min_secret": 1},
        {"fragment_min": 0},
        {"fragment_scan": 10**7},
    ):
        with pytest.raises(ValidationError):
            ScrubSettings(**bad)


def test_the_scrub_settings_reach_the_scrub():
    wide = "." * 10_000
    out_default = tools_mod.prepare_output(wide, {}, CAP, ["Zk39qWdRt5"], raw_cap=RAW_CAP)
    out_small = tools_mod.prepare_output(
        wide, {}, CAP, ["Zk39qWdRt5"], raw_cap=RAW_CAP, scrub=ScrubSettings(tail_window=64)
    )
    assert len(out_small) - len(out_default) == 256 - 64
    seven = "Ab9Qz7K"
    kept = tools_mod.prepare_output(
        "x " + seven + " y", {}, 16_384, [seven], scrub=ScrubSettings(min_secret=8)
    )
    assert seven in kept  # below the configured minimum: not scrubbed
    assert seven not in tools_mod.prepare_output("x " + seven + " y", {}, 16_384, [seven])


# ---- the sibling in guard/runmap ------------------------------------------------------------------------------------------


def test_the_runmap_json_unescape_joins_pairs_and_reads_slashes():
    assert runmap.json_unescape(BS + "ud83d" + BS + "ude00") == chr(0x1F600)
    assert runmap.json_unescape(BS + "ud83d") == chr(0xFFFD)
    assert runmap.json_unescape("a" + BS + "/b") == "a/b"
    assert runmap.json_unescape("a" + BS + "nb", simple="/") == "a" + BS + "nb"
    assert runmap.json_unescape(BS + BS + "u0041") == BS + "u0041"


def test_the_redactors_second_pass_reads_a_slash_written_as_backslash_slash():
    gcp = "projects/my-proj-123/zones/z1"
    out = runmap.redact_text("see " + gcp.replace("/", BS + "/") + " now", {})
    assert "my-proj-123" not in out


# ---- layered percent-encoding: the doubly and triply encoded unicode secret (evidence-13: 96 leaks at 3fd024d) ----------


def _pct2(s: str) -> str:
    return _pct(_pct(s))


def _pct3(s: str) -> str:
    return _pct(_pct(_pct(s)))


LAYERED = {"percent2": _pct2, "percent3": _pct3}
UNICODE_KEY = (
    "abZq" + chr(0xE9) + "Tn2" + chr(0x4E2D) + "Kq8"
)  # ASCII front, then 2- and 3-byte characters


@pytest.mark.parametrize("name", list(LAYERED))
def test_layered_percent_encoding_of_a_unicode_secret_is_scrubbed_whole(name):
    out = tools_mod.prepare_output(
        "x " + LAYERED[name](UNICODE_KEY) + " y", {}, 16_384, [UNICODE_KEY]
    )
    assert "<SECRET_REDACTED>" in out and "abZq" not in out and "%25" not in out


def _layered_cases():
    for name, f in LAYERED.items():
        for off in range(1, len(f(UNICODE_KEY))):
            for other in (False, True):
                yield pytest.param(
                    name, off, other, id=f"{name}-{off}-{'other' if other else 'alone'}"
                )


@pytest.mark.parametrize(("name", "off", "other"), list(_layered_cases()))
def test_a_cut_at_every_offset_of_a_layered_percent_spelling_leaves_no_front(name, off, other):
    f = LAYERED[name]
    body = _cut_body(f(UNICODE_KEY), off, [UNICODE_KEY, OTHER], f(OTHER) if other else "")
    assert "abZq" not in body[-40:] and body.endswith("." * 10 if other else "."), (
        name,
        off,
        ascii(body[-16:]),
    )
    assert "%25" not in body[-12:] and "%C3" not in body[-12:]


def test_the_decode_reads_layered_percent_encoding_to_a_fixed_point_in_four_rounds():
    assert tools_mod._decoded(_pct3(UNICODE_KEY)) == UNICODE_KEY
    assert tools_mod._decoded(_pct2("Ab9")) == "Ab9"


# ---- stacked half-written escapes: every one is removed, then the front before them ---------------------------------------


@pytest.mark.parametrize(
    "tail",
    ["&#9&#1", "%C3%A%C3", "&#9%C3&#1", BS + "u00" + "&#9", "%25C3%25&#9", "&#x4&#9"],
    ids=["entities", "percents", "mixed", "json-entity", "layered-entity", "hex-entity"],
)
def test_stacked_half_written_escapes_are_all_removed_with_the_front_before_them(tail):
    forms = sorted(tools_mod._secret_forms(ALNUM))
    out = tools_mod._strip_fragment("pad ..........Zk3" + tail + TRUNC, forms)
    assert out == "pad .........." + TRUNC, ascii(out[-24:])


# ---- hex in mixed case: a letter-first hex (the secret starts with a two-byte character) -------------------------------------


def test_a_mixed_case_hex_front_that_starts_with_a_letter_is_stripped():
    sec = chr(0xE9) + "Tn2Kq8x"
    hexed = sec.encode().hex()  # c3a9...
    mixed = "".join(c.upper() if i % 3 == 0 else c for i, c in enumerate(hexed))
    assert mixed[0].isupper()
    for off in range(3, len(mixed) - 1, 2):
        body = _cut_body(mixed, off, [sec])
        assert body.endswith("."), (off, ascii(body[-12:]))


# ---- a base64 token with the secret near its start: tokens of 8 or more characters are examined ------------------------


def test_a_short_base64_token_with_the_secret_near_its_start_is_cut_back():
    enc = base64.b64encode(b"svc:" + ALNUM.encode() + b":x").decode()
    for off in range(8, len(enc)):
        dec = _tail_decoded(_cut_body(enc, off, [ALNUM]))
        secret = ALNUM.encode()
        assert not any(len(dec) - p >= 2 and secret.startswith(dec[p:]) for p in range(len(dec))), (
            off,
            dec,
        )
