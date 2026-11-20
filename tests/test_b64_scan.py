"""G4 (ticket G4, sections 10.2 and 10.3): the base64 view of `runmap.redact_text` and the kind ENCODED.

Private names are reached INSIDE each test (`runmap.<name>`, `redact_mod.<name>`; no module-level import of a G4 name). Every
assertion message starts with its TB id and one space (`"TB-2.3 ..."`): tests/b64_mutants.py uses it as the mutant's `expect`.
A killer that expects a raise asserts an OUTCOME string, so its failure line still starts with the id.
"""

from __future__ import annotations

import base64
import hashlib
import importlib
import json
import random
import re
import textwrap
import time

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.approvals import cards, channel
from hadavin_sdk.guard import runmap
from hadavin_sdk.models import RunState
from tests import p1c_cases as pc

redact_mod = importlib.import_module("hadavin_sdk.guard.redact")

X = "QUJD" + "REVG" + "R0hJ"
S12 = "Zq9" + "xW4" + "mT7" + "pL2"


def _outcome(fn):
    """The result of `fn()`, or `Type(message)` when it raises a RedactionError (the id then stays on the failure line)."""
    try:
        return fn()
    except runmap.RedactionError as exc:
        return f"{type(exc).__name__}({exc})"


# ---------------------------------------------------------------------------------------------------------------------
# Phase 2: the kind ENCODED (G4b)
# ---------------------------------------------------------------------------------------------------------------------
def test_encoded_kind_is_a_secret_label_never_stored():
    assert "ENCODED" in redact_mod._LABELS, "TB-2.1 ENCODED is not a label"
    assert "ENCODED" in redact_mod.SECRET_KINDS, "TB-2.1 ENCODED is not a secret kind"
    assert "ENCODED" not in defaults.STORED_KINDS, "TB-2.1 ENCODED is a stored kind"
    assert "ENCODED" not in runmap._GRAMMAR, "TB-2.1 ENCODED has a grammar"
    assert redact_mod._sweep("<ENCODED_1>", "abcd") is redact_mod._EVERY_COPY, (
        "TB-2.1 ENCODED is not swept in every copy"
    )


def test_encoded_kind_after_a_key():
    """Own output after E9: a genuine placeholder stays; the escaped look-alike and a cut-off opening are masked as SECRET."""
    got = [
        redact_mod.redact(t)
        for t in ("password=<ENCODED_1>", "password=‹ENCODED_1›", "password=<ENC")
    ]
    out = [(r.text, r.mapping) for r in got]
    assert out[0] == ("password=<ENCODED_1>", {}), (
        "TB-2.2 a genuine ENCODED placeholder after a key"
    )
    assert out[1] == ("password=<SECRET_1>", {"<SECRET_1>": "‹ENCODED_1›"}), (
        "TB-2.2 the escaped look-alike"
    )
    assert out[2] == ("password=<SECRET_1>", {"<SECRET_1>": "<ENC"}), "TB-2.2 a cut-off opening"


def test_place_encoded_numbering():
    m = {"<ENCODED_5>": "a" * 12}
    assert redact_mod.place_encoded(m, ["b" * 12]) == ["<ENCODED_6>"], "TB-2.3 after 5"
    assert len(m) == 2, "TB-2.3 the map grows by the new run"
    m = {"<ENCODED_5>": "a" * 12, "<ENCODED_2>": "c" * 12}
    assert redact_mod.place_encoded(m, ["b" * 12]) == ["<ENCODED_7>"], "TB-2.3 after 5 and 2"
    assert len(m) == 3, "TB-2.3 the map grows by the new run (two entries before)"
    m = {}
    assert redact_mod.place_encoded(m, ["a" * 12, "b" * 12]) == ["<ENCODED_1>", "<ENCODED_2>"], (
        "TB-2.3 from empty"
    )
    assert len(m) == 2, "TB-2.3 two new runs, two entries"


def test_place_encoded_numbering_is_the_redactor_counter():
    for before, runs in (
        ({"<ENCODED_5>": "a" * 12}, ["b" * 12]),
        ({"<ENCODED_5>": "a" * 12, "<ENCODED_2>": "c" * 12}, ["b" * 12]),
        ({}, ["a" * 12, "b" * 12]),
    ):
        m = dict(before)
        used = redact_mod.place_encoded(m, runs)
        first = redact_mod._Redactor(dict(before)).counters["ENCODED"] + 1
        assert used[0] == f"<ENCODED_{first}>", (
            "TB-2.4 the number is the redactor's counter plus one"
        )


def test_place_encoded_identifier_original_gets_a_new_entry():
    m = {"<TENANT_1>": X}
    assert redact_mod.place_encoded(m, [X]) == ["<ENCODED_1>"], "TB-2.5 placeholder"
    assert m == {"<TENANT_1>": X, "<ENCODED_1>": X}, "TB-2.5 map"


def test_place_encoded_reuses_an_encoded_original():
    m = {"<ENCODED_3>": X}
    assert redact_mod.place_encoded(m, [X]) == ["<ENCODED_3>"], "TB-2.6 reuse"
    assert len(m) == 1, "TB-2.6 no new entry"


def test_tie_break_same_original_secret_rule_first():
    mapping = {"<TENANT_1>": X, "<ENCODED_1>": X}
    out = redact_mod.redact("pre" + X + "post and " + X + " alone", mapping=mapping).text
    assert out == "pre<ENCODED_1>post and <ENCODED_1> alone", (
        "TB-2.7 the secret kind's rule governs the original"
    )


def test_tie_break_keeps_the_order_of_different_originals():
    text = "x ab-cd-ef y"
    # Re-pinned on the merged G9 + G4 tree (E20): G9's sweep masks an overlap with the placeholders already held
    # (no secret value stays readable; the G4 base text kept a half of the other value), so the output is the two
    # placeholders in text order in every map; the order follows the position in the text, not the map order.
    maps = [
        ({"<TENANT_1>": "cd-ef", "<SECRET_1>": "ab-cd"}, "x <SECRET_1><TENANT_1> y"),
        ({"<SECRET_1>": "ab-cd", "<TENANT_1>": "cd-ef"}, "x <SECRET_1><TENANT_1> y"),
        ({"<TENANT_1>": "ab-cd", "<SECRET_1>": "cd-ef"}, "x <TENANT_1><SECRET_1> y"),
        ({"<SECRET_1>": "cd-ef", "<TENANT_1>": "ab-cd"}, "x <TENANT_1><SECRET_1> y"),
    ]
    for i, (m, want) in enumerate(maps, start=1):
        got = _outcome(lambda m=m: runmap.enforce_map(text, dict(m)))
        assert got == want, f"TB-2.8 map {i}"
    fifth = {"<TENANT_1>": "cd-ef", "<SECRET_1>": "ab-cd", "<SECRET_2>": "cd-ef"}
    got = _outcome(lambda: runmap._Redactor(dict(fifth), None).sweep(text))
    assert got == "x <SECRET_1><SECRET_2> y", "TB-2.8 fifth map, the redactor's own sweep"
    got = _outcome(lambda: runmap.enforce_map(text, dict(fifth)))
    assert got == "x <SECRET_1><SECRET_2> y", "TB-2.8 fifth map, enforce_map"
    # sixth map (MIX builder, E20): two DIFFERENT originals of the SAME length, one of an identifier kind (EMAIL) and one of a secret kind
    # (SECRET), written glued together. The tie-break of `_build` is per ORIGINAL (`_rules[original]`: the secret kind's rule wins when two
    # placeholders share one original); it does not order two different originals. Their order is the stable sort of `-len(original)`, so
    # the map's order stands and EMAIL (first) comes first: its rule, an identifier swept only at a boundary, does not fire on `abcd`
    # glued to `efgh`, the SECRET rule masks `efgh`, and the output is `abcd<SECRET_1>`. With a sort key that puts the secret kind first
    # (gate mutant "b64 tie-break as v3's sort key") the order flips and the bare sweep gives `<EMAIL_1><SECRET_1>`. G9's read-back masks
    # the shared overlaps of TB-2.8's maps 1-5 whatever the order, so only this map, which the read-back does not touch, tells the two
    # orders apart.
    sixth = {"<EMAIL_1>": "abcd", "<SECRET_1>": "efgh"}
    got = _outcome(lambda: runmap._Redactor(dict(sixth), None).sweep("abcdefgh"))
    assert got == "abcd<SECRET_1>", "TB-2.8 sixth map, the redactor's own sweep"


def test_encoded_is_never_restored_or_stored():
    sb = "cGFzc3dvcmQ9" + "WnE5eFc0bVQ3cEwy"
    m = {"<ENCODED_1>": sb}
    assert runmap.restore_text("x <ENCODED_1>", m) == "x <ENCODED_1>", "TB-2.9 restore"
    assert (
        runmap.restore_text("x <ENCODED_1>", m, kinds=frozenset({"ENCODED"})) == "x <ENCODED_1>"
    ), "TB-2.9 restore with kinds"
    assert runmap.storable(m) == {}, "TB-2.9 storable"
    assert runmap.storable(m, frozenset({"ENCODED"})) == {}, "TB-2.9 storable with kinds"


def test_assignment_kinds_hold_encoded():
    assert "ENCODED" in channel._ASSIGNMENT_KINDS, "TB-2.10 ENCODED is not an assignment kind"


# ---------------------------------------------------------------------------------------------------------------------
# Phase 3: the base64 view (G4a)
# ---------------------------------------------------------------------------------------------------------------------
def b64(data) -> str:
    return base64.b64encode(data.encode() if isinstance(data, str) else data).decode()


PW = "Kp7" + "rTq" + "2W"
SB = b64("password=" + S12)  # cGFzc3dvcmQ9WnE5eFc0bVQ3cEwy (28)
B1 = b64("this is just a status message")
B2 = b64("ok status 200")
IP = b64("10.20.30.40")
BL = b64(
    "2026-11-20 deploy db_password="
    + S12
    + " applied to the cluster after the review of the change set"
)
NO_RUN = re.compile(r"(?!)")


def _step_off(monkeypatch):
    monkeypatch.setattr(runmap, "_B64_RUN", NO_RUN)


def _both(text, mapping=None):
    """(redact_text, redact_untrusted) outputs and maps, each with a fresh map."""
    res = []
    for fn in (runmap.redact_text, runmap.redact_untrusted):
        m = {} if mapping is None else dict(mapping)
        res.append((fn(text, m), m))
    return res


class _Spy:
    """Counts the calls of `runmap._b64_text`."""

    def __init__(self, monkeypatch):
        self.n = 0
        real = runmap._b64_text

        def spy(joined):
            self.n += 1
            return real(joined)

        monkeypatch.setattr(runmap, "_b64_text", spy)


def test_b64_text_rules():
    t = runmap._b64_text
    got = [
        t(b64("status ok here")),
        t(b64(bytes(range(256)))),
        t("QUJD+REVG_R0hJ"),
        t("QUJDREVGR0hJS"),
        t(b64("10.20.30.40".encode("utf-16-le"))),
        t(b64("10.20.30.40".encode("utf-16-be"))),
        t(b64(b"\xff\xfe" + "ok".encode("utf-16-le"))),
        t(b64("unpadded!!").rstrip("=")),
    ]
    want = ["status ok here", None, None, None, "10.20.30.40", "10.20.30.40", "ok", "unpadded!!"]
    for i, (g, w) in enumerate(zip(got, want, strict=True), start=1):
        assert g == w, f"TB-3.1 rule {i}"
    assert b64("10.20.30.40".encode("utf-16-be")) == "ADEAMAAuADIAMAAuADMAMAAuADQAMA==", (
        "TB-3.1 the UTF-16-BE blob"
    )
    assert t("Pz8/Pz8_") is None, "TB-3.1 a mixed alphabet run that would decode to text"


A16, A15, A18 = "QUJDREVGR0hJSktM", "QUJDREVGR0hJSkt", "QUJDREVGR0hJSktMTU"
B4, B8, B10, B15 = "TU5P", "TU5PUFFS", "TU5PUFFSU1", "TU5PUFFSU1RVVld"
B16, B18, B20 = "TU5PUFFSU1RVVldY", "5PUFFSU1RVVldYWVph", "TU5PUFFSU1RVVldYWVph"
C16, C20, D4 = "WVphYmNkZWZnaGlq", "WVphYmNkZWZnaGlqa2xt", "bm9w"
UNIT_ROWS = [
    ([A16, B10], [(0, 27, "b")], [[(0, 16)]]),
    ([A16, B16, C16], [(0, 50, "b")], [[(0, 16), (17, 33), (34, 50)]]),
    ([A16, B10, C16], [(0, 27, "b"), (28, 44, "r")], [[(0, 16)]]),
    ([A16, B20], [(0, 16, "r"), (17, 37, "r")], []),
    ([A15, B15], [(0, 15, "r"), (16, 31, "r")], []),
    ([A16, B15 + "=", C16], [(0, 33, "b"), (34, 50, "r")], [[(0, 16), (17, 33)]]),
    ([A16, B8, C20, D4], [(0, 25, "b"), (26, 51, "b")], [[(0, 16)], [(26, 46)]]),
    (["  " + A16 + "\r", B4], [(2, 24, "b")], [[(2, 18)]]),
    ([A18, B18], [(0, 37, "b")], [[(0, 18), (19, 37)]]),
    ([A18, B10], [(0, 29, "b")], [[(0, 18)]]),
]


def test_b64_units_wrapped_block_table():
    for n, (row, units, parts) in enumerate(UNIT_ROWS, start=1):
        text = "\n".join(row)
        stripped, got = runmap._b64_units(text)
        assert stripped == text, f"TB-3.2 row {n} text"
        assert [(u.start, u.end) for u in got] == [(a, b) for a, b, _ in units], (
            f"TB-3.2 row {n} units"
        )
        assert all(u.written == text[u.start : u.end] for u in got), f"TB-3.2 row {n} written"
        blocks = [u for u in got if u.parts]
        got_parts = [[(p.start, p.end) for p in u.parts] for u in blocks]
        assert got_parts == parts, f"TB-3.2 row {n} parts"
        assert all(p.written == text[p.start : p.end] for u in got for p in u.parts), (
            f"TB-3.2 row {n} part text"
        )


def test_b64_units_placeholders_are_never_runs(monkeypatch):
    texts = [
        "x <HIGHENTROPY_7> y",
        "card <CREDITCARD_12> ok",
        "<SECRET_REDACTED>",
        "\u2039HIGHENTROPY_7\u203a",
        "<GCPRESOURCE_1>",
        "<AZURERESOURCE_12>",
        "<SECRET_REDACTED> " * 20_000,
    ]
    for t in texts:
        assert runmap._b64_units(t)[1] == [], "TB-3.3 a placeholder or marker is a run"

    def run_all():
        out = []
        for t in texts:
            for fn in (runmap.redact_text, runmap.redact_untrusted):
                m: dict[str, str] = {}
                out.append((_outcome(lambda t=t, fn=fn, m=m: fn(t, m)), m))
        return out

    mine = run_all()
    _step_off(monkeypatch)
    off = run_all()
    assert mine == off, "TB-3.3 output and map differ from the step-off build"


def test_marker_shaped_blobs_are_blanked():
    for t in ("<cGFzc3dvcmQ_12>", "<ABCDEFGHIJKLMNOP>", "\u2039ABCDEFGHIJKLMNOP\u203a"):
        assert runmap._b64_units(t)[1] == [], f"TB-3.3b {t}"
    assert [u.written for u in runmap._b64_units("<" + SB + ">")[1]] == [SB], "TB-3.3b control"


def test_no_run_no_extra_work(monkeypatch):
    rnd = random.Random(7)  # noqa: S311 - a seeded test generator, not a secret
    prose = ("the quick brown fox jumps over the lazy dog and keeps going. " * 2000)[:100_000]
    blob48 = "".join(
        rnd.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        for _ in range(48)
    )
    texts = [
        "pw=ab%41 here",
        "pw=ab%41 x A",
        prose,
        blob48,
        "x <HIGHENTROPY_7> y",
        "card <CREDITCARD_12> ok",
        "<SECRET_REDACTED>",
    ]

    def run():
        calls = {"redact": 0, "clock": 0}
        real_redact, real_clock = runmap.redact, time.thread_time

        def redact(*a, **k):
            calls["redact"] += 1
            return real_redact(*a, **k)

        def clock():
            calls["clock"] += 1
            return real_clock()

        work, outs = [], []
        for t in texts:
            for fn in (runmap.redact_text, runmap.redact_untrusted):
                calls["redact"] = calls["clock"] = 0
                m: dict[str, str] = {}
                with monkeypatch.context() as mp:
                    mp.setattr(runmap, "redact", redact)
                    mp.setattr(runmap.time, "thread_time", clock)
                    out = fn(t, m)
                work.append((calls["redact"], calls["clock"]))
                outs.append((out, m))
        return work, outs

    on = run()
    with monkeypatch.context() as mp:
        _step_off(mp)
        off = run()
    assert on == off, "TB-3.4 the step does extra work on a text with no run"

    # The real check: the work of a text with no run is that of the base commit's pass one, which is `redact` alone. No literal count
    # (the clock reads of the pattern table change with every pattern edit: 154, 156, 160 in turn): the reference replaces `_pass_one`
    # by that one call, so a clock read or a `redact` call the step adds BEFORE its gate (the mutant "b64 clock read before the gate")
    # is a difference whatever the table holds. `_step_off` alone cannot see it: the read stays in the off build too.
    def base_pass_one(text, mapping, cache, budget, depth):
        return runmap.redact(
            text, mapping=mapping, _cache=cache, _deadline=budget.started + defaults.REDACT_BUDGET_S
        )

    with monkeypatch.context() as mp:
        mp.setattr(runmap, "_pass_one", base_pass_one)
        base = run()
    assert on == base, "TB-3.4 the work of a text with no run is not the base commit's"
    assert any(n > 1 for _, n in on[0]), "TB-3.4 the counts are vacuous (no clock read at all)"


def test_short_blob_alone_is_encoded():
    for out, m in _both(SB):
        assert out == "<ENCODED_1>", "TB-3.5 output"
        assert m == {"<SECRET_1>": S12, "<ENCODED_1>": SB}, "TB-3.5 map"


def test_decoded_secret_entry_kept_and_a_plain_copy_swept():
    out, _ = _both(SB + " and later " + S12 + " alone")[0]
    assert out == "<ENCODED_1> and later <SECRET_1> alone", (
        "TB-3.6 a plain copy of the decoded secret"
    )


def test_four_levels_one_entry():
    blob = b64(b64(b64(b64("status ok"))))
    assert blob == "V1hwT1UyRkhVa2xXYm5CS1VucHNlUT09", "TB-3.7 the recipe"
    m: dict[str, str] = {}
    assert runmap.redact_text("x " + blob, m) == "x <ENCODED_1>", "TB-3.7 output"
    assert list(m) == ["<ENCODED_1>"], "TB-3.7 one entry"


def test_three_levels_read():
    blob = b64(b64(b64("pwd=Zq9xW4m")))
    assert blob == "WTBoa2ExQldjSGhQV0doWVRrY3dQUT09", "TB-3.8 the recipe"
    out = runmap.redact_text(blob, {})
    assert out == "<ENCODED_1>", "TB-3.8 output"
    assert pc.leak_of("Zq9xW4m", out)[0] == "no", "TB-3.8 leak"


def test_utf16_be_short():
    blob = "ADEAMAAuADIAMAAuADMAMAAuADQAMA=="
    m: dict[str, str] = {}
    assert runmap.redact_text(blob, m) == "<ENCODED_1>", "TB-3.9 output"
    assert m == {"<ENCODED_1>": blob}, "TB-3.9 map (IPV4 is a stored kind: no entry)"


def test_too_deep_inside_a_decoded_view_is_masked_unread():
    blob = b64("%" + "25" * 9 + "41")
    assert blob == "JTI1MjUyNTI1MjUyNTI1MjUyNTQx", "TB-3.10 the recipe"
    assert _outcome(lambda: runmap.redact_text(blob, {})) == "<ENCODED_1>", "TB-3.10 output"


def test_tenant_held_blob_becomes_encoded():
    blob = b64("pwd=Kp7rTq2W")
    assert blob == "cHdkPUtwN3JUcTJX", "TB-3.11 the recipe"
    m: dict[str, str] = {}
    assert runmap.redact_text("org_id=" + blob, m) == "org_id=<ENCODED_1>", "TB-3.11 output"
    assert m == {"<SECRET_1>": "Kp7rTq2W", "<ENCODED_1>": blob}, "TB-3.11 map"


def test_blob_after_an_ansi_escape():
    assert runmap.redact_text("\x1b[1m" + SB + "\x1b[0m", {}) == "<ENCODED_1>", "TB-3.12 ansi"


def test_percent_padding():
    t = "data=" + b64("password=Zq9xW4mT7pL")[:-1] + "%3D"
    assert t == "data=cGFzc3dvcmQ9WnE5eFc0bVQ3cEw%3D", "TB-3.13 the recipe"
    m: dict[str, str] = {}
    assert runmap.redact_text(t, m) == "data=<ENCODED_1>%3D", "TB-3.13 percent padding"
    assert m == {"<SECRET_1>": "Zq9xW4mT7pL", "<ENCODED_1>": "cGFzc3dvcmQ9WnE5eFc0bVQ3cEw"}, (
        "TB-3.13 map"
    )


def test_json_escaped_slashes():
    rnd = random.Random(20261120)  # noqa: S311 - a seeded test generator, not a secret
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789?~"
    blob = ""
    for _ in range(100_000):
        blob = b64("pwd=" + "".join(rnd.choice(alphabet) for _ in range(8)))
        if "/" in blob:
            break
    assert "/" in blob, "TB-3.14 no blob with a slash drawn"
    t = json.dumps({"data": blob}).replace("/", "\\/")
    assert runmap.redact_text(t, {}) == '{"data": "<ENCODED_1>"}', "TB-3.14 output"


def test_known_value_seen_in_base64():
    m = {"<SECRET_1>": S12}
    assert runmap.redact_text("x " + b64("note " + S12), m) == "x <ENCODED_1>", "TB-3.15 output"


def test_caps_fail_closed(monkeypatch):
    unit = runmap._B64Unit(0, 28, SB, SB, (SB,))
    blobs = [b64(f"pwd=Zq9xW4m{i}") for i in range(4)]
    # (a) four distinct blobs, three allowed
    with monkeypatch.context() as mp:
        mp.setattr(defaults, "B64_MAX_UNITS", 3)
        m: dict[str, str] = {}
        assert (
            _outcome(lambda: runmap.redact_text(" ".join(blobs), m))
            == "InputTooLarge(InputTooLarge)"
        ), "TB-3.16 (a)"
        assert m == {}, "TB-3.16 (a) map"
    # (b) ten decoded characters allowed
    with monkeypatch.context() as mp:
        mp.setattr(defaults, "B64_MAX_DECODED_CHARS", 10)
        m = {}
        assert _outcome(lambda: runmap.redact_text(SB, m)) == "InputTooLarge(InputTooLarge)", (
            "TB-3.16 (b)"
        )
        assert m == {}, "TB-3.16 (b) map"
    # (c) a spent deadline stops before any decode
    with monkeypatch.context() as mp:
        spy = _Spy(mp)
        got = _outcome(lambda: runmap._b64_hits([unit], {}, runmap._ScanBudget(started=-1e9), 0))
        assert got == "InputTooLarge(InputTooLarge)", "TB-3.16 (c)"
        assert spy.n == 0, "TB-3.16 (c) a decode ran"
    # (d) the dedupe counts one unit
    with monkeypatch.context() as mp:
        mp.setattr(defaults, "B64_MAX_UNITS", 1)
        got = _outcome(lambda: runmap.redact_text(" ".join([SB] * 4), {}))
        assert got == "<ENCODED_1> <ENCODED_1> <ENCODED_1> <ENCODED_1>", "TB-3.16 (d)"
    # (e) a decoded join over the cap: every unit a hit, unread
    with monkeypatch.context() as mp:
        mp.setattr(defaults, "MAX_REDACT_CHARS", 20)
        got = _outcome(
            lambda: runmap._b64_hits([unit], {}, runmap._ScanBudget(time.thread_time()), 0)
        )
        assert got == ([True], []), "TB-3.16 (e)"
    # (f) a backstop: the characters of the lines tried alone have a count of their own
    with monkeypatch.context() as mp:
        mp.setattr(defaults, "B64_MAX_DECODED_CHARS", 30)
        budget2 = runmap._ScanBudget(time.thread_time())
        budget2.take(20, True)
        try:
            budget2.take(20, True)
            got = "no raise"
        except runmap.InputTooLarge as exc:
            got = f"InputTooLarge({exc})"
        assert got == "InputTooLarge(InputTooLarge)", "TB-3.16 (f)"
        assert budget2.units == 0, "TB-3.16 (f) the lines counted as units"
    # (g) the lines of a block are not units
    a = b64("pwd=" + S12 + "abcd").rstrip("=")
    b = b64("pwd=" + S12[::-1] + "wxyz").rstrip("=")
    with monkeypatch.context() as mp:
        mp.setattr(defaults, "B64_MAX_UNITS", 1)
        got = _outcome(lambda: runmap.redact_text(a + "\n" + b, {}))
        assert got == "<ENCODED_1>\n<ENCODED_2>", "TB-3.16 (g)"


def test_separator_fallback():
    def hits(pieces):
        units = [runmap._B64Unit(0, 0, x, x, (x,)) for x in map(b64, pieces)]
        return runmap._b64_hits(units, {}, runmap._ScanBudget(time.thread_time()), 0)[0]

    assert hits(['secret="', 'plain words" here', "x" * 12]) == [True, True, True], (
        "TB-3.17 lost separator"
    )
    assert hits(['secret="', "plain words here", "x" * 12]) == [False, False, False], (
        "TB-3.17 control"
    )


def test_separator_survives_every_neutralise():
    pieces = ["status ok", "hello world", "x"]
    joined = runmap._B64_SEP.join(pieces)
    for name, hook in (
        ("untrusted", runmap.neutralise_untrusted),
        ("none", lambda t: t),
        ("card", channel._neutralise),
    ):
        assert hook(joined).split(runmap._B64_SEP) == pieces, f"TB-3.18 {name}"


def test_settle_chain_beside_a_blob():
    from tests.test_redact_idempotent_property import CONSTRUCTED

    for sep in (" ", ",", "\n"):
        m = runmap.RunMap()
        out = runmap.redact_text(CONSTRUCTED[0] + sep + SB, m)
        want = (
            "password=<SECRET_2>\nBSB: <BANKCODE_1><SECRET_2>\npaid <BANKCODE_1>/<BANKACCT_1>"
            + sep
            + "<ENCODED_1>"
        )
        assert out == want, f"TB-3.19 output for {sep!r}"
        assert sorted(m) == [
            "<BANKACCT_1>",
            "<BANKCODE_1>",
            "<ENCODED_1>",
            "<SECRET_1>",
            "<SECRET_2>",
        ], "TB-3.19 keys"
        assert m["<SECRET_1>"] == S12, "TB-3.19 the kept decoded secret"


def test_wrapped_chain_settles_inside_the_view():
    from tests.test_redact_idempotent_property import CONSTRUCTED

    t = "\n".join(textwrap.wrap(b64(CONSTRUCTED[0]), 64))
    assert runmap.redact_text(t, {}) == "<ENCODED_1>", "TB-3.20 wrapped chain"


def test_fold_scan_runs_in_both_passes():
    assert runmap.redact_text("caf\u00e9 " + SB, {}) == "caf\u00e9 <ENCODED_1>", (
        "TB-3.21 fold, first"
    )
    got = runmap.redact_text("\u13aalice@example.com " + SB, {})
    assert got == "[line withheld: look-alike text hid a protected value] <EMAIL_1>", (
        "TB-3.21 fold, second"
    )


def _second_call_raises(exc):
    """A `runmap.redact` stand-in that raises `exc` on its second call."""
    real = runmap.redact
    calls = {"n": 0}

    def broken(*a, **k):
        calls["n"] += 1
        if calls["n"] == 2:
            raise exc
        return real(*a, **k)

    return broken


def test_errors_of_the_second_pass_propagate(monkeypatch):
    for exc in (runmap.RedactionError("NotSettled"), runmap.InputTooLarge("InputTooLarge")):
        m = runmap.RunMap()
        with monkeypatch.context() as mp:
            mp.setattr(runmap, "redact", _second_call_raises(exc))
            got = _outcome(lambda m=m: runmap.redact_text(SB, m))
        assert got == f"{type(exc).__name__}({exc})", "TB-3.22 the error is kept as raised"
        assert dict(m) == {}, "TB-3.22 the map was written"


def _count_redact(mp, only_encoded=None):
    """Patch `runmap.redact` with a call counter (and `_only_encoded` when given); returns the counter."""
    calls = {"n": 0}
    real = runmap.redact

    def counted(*a, **k):
        calls["n"] += 1
        return real(*a, **k)

    mp.setattr(runmap, "redact", counted)
    if only_encoded is not None:
        mp.setattr(runmap, "_only_encoded", lambda t2, base: only_encoded)
    return calls


def test_only_encoded_shortcut_is_taken_and_exact(monkeypatch):
    """E22: a t2 that is only `<ENCODED_n>` over an all-ASCII map skips step 9's `redact`; the result is the one `redact` gives."""
    for text in (SB, W):
        with monkeypatch.context() as mp:
            calls = _count_redact(mp)
            on = _outcome(lambda text=text: _both(text))
            n_on = calls["n"]
        with monkeypatch.context() as mp:
            calls = _count_redact(mp, only_encoded=False)
            off = _outcome(lambda text=text: _both(text))
            n_off = calls["n"]
        assert on == off, "TB-3.44 the shortcut's output or map differs from step 9's"
        assert n_off > n_on, "TB-3.44 the shortcut did not skip step 9's redact"
    with monkeypatch.context() as mp:
        calls = _count_redact(mp)
        runmap.redact_text(SB, {})
        assert calls["n"] == 2, "TB-3.44 expected pass one and the decoded view's pass one only"


def test_only_encoded_shortcut_guards(monkeypatch):
    """A non-ASCII stored value, or a stored value that occurs in t2, must NOT take the shortcut: step 9's `redact` runs."""
    for name, held in (
        ("non-ASCII value", {"<TENANT_1>": "caf\u00e9-unique-tenant"}),
        ("value inside t2", {"<TENANT_1>": "ENCODED_1"}),
    ):
        with monkeypatch.context() as mp:
            calls = _count_redact(mp)
            runmap.redact_text(SB, dict(held))
            n_on = calls["n"]
        with monkeypatch.context() as mp:
            calls = _count_redact(mp, only_encoded=False)
            runmap.redact_text(SB, dict(held))
            n_off = calls["n"]
        assert n_on == n_off, f"TB-3.45 {name}: step 9's redact was skipped"
    direct = [
        ("<ENCODED_1>", {"<ENCODED_1>": SB}, True),
        ("<ENCODED_1>", {"<ENCODED_1>": SB, "<TENANT_1>": "caf\u00e9"}, False),
        ("<ENCODED_1>", {"<ENCODED_1>": SB, "<TENANT_1>": "ENCODED_1"}, False),
        ("<ENCODED_1>", {"<ENCODED_1>": SB, "<TENANT_1>": "<ENCODED_1>"}, False),
        ("x <ENCODED_1>", {"<ENCODED_1>": SB}, False),
    ]
    for t2, base, want in direct:
        assert runmap._only_encoded(t2, base) is want, (
            f"TB-3.45 _only_encoded({t2!r}, {sorted(base)})"
        )


def test_unit_over_the_char_cap_is_masked_unread(monkeypatch):
    """`B64_MAX_UNIT_CHARS`: a longer unit that pass one did not hold is masked unread (no decode); one at the cap is decoded."""
    with monkeypatch.context() as mp:
        mp.setattr(defaults, "B64_MAX_UNIT_CHARS", len(SB) - 1)
        spy = _Spy(mp)
        m: dict[str, str] = {}
        out = runmap.redact_text(SB, m)
        assert out == "<ENCODED_1>" and m == {"<ENCODED_1>": SB}, (
            "TB-3.46 over the cap: output or map"
        )
        assert spy.n == 0, "TB-3.46 a unit over the cap was decoded"
        spy = _Spy(mp)
        mp.setattr(defaults, "B64_MAX_UNIT_CHARS", len(B2) - 1)
        assert runmap.redact_text(B2, {}) == "<ENCODED_1>", (
            "TB-3.46 a benign unit over the cap is masked too"
        )
        assert spy.n == 0, "TB-3.46 a benign unit over the cap was decoded"
    with monkeypatch.context() as mp:
        mp.setattr(defaults, "B64_MAX_UNIT_CHARS", len(SB))
        spy = _Spy(mp)
        m = {}
        out = runmap.redact_text(SB, m)
        assert out == "<ENCODED_1>" and m == {"<SECRET_1>": S12, "<ENCODED_1>": SB}, (
            "TB-3.46 at the cap: output or map"
        )
        assert spy.n >= 1, "TB-3.46 a unit at the cap was not decoded"


def test_errors_of_step_nine_propagate(monkeypatch):
    """I21 (ticket 2.5 step 9): an error raised by the final `redact` over T2 propagates; the text is not shown unscanned."""
    t = "x " + SB
    assert runmap.redact_text(t, {}) == "x <ENCODED_1>", "TB-3.47 control"
    for exc in (runmap.RedactionError("NotSettled"), runmap.InputTooLarge("InputTooLarge")):
        real = runmap.redact

        def broken(text, *a, exc=exc, real=real, **k):
            if text == "x <ENCODED_1>":  # T2: the only call whose text is the placeholder text
                raise exc
            return real(text, *a, **k)

        m = runmap.RunMap()
        with monkeypatch.context() as mp:
            mp.setattr(runmap, "redact", broken)
            got = _outcome(lambda m=m: runmap.redact_text(t, m))
        assert got == f"{type(exc).__name__}({exc})", "TB-3.47 the step 9 error is kept as raised"
        assert dict(m) == {}, "TB-3.47 the map was written"


def test_views_are_of_the_input():
    out = runmap.redact_untrusted(SB + " password%3D" + S12, {})
    assert "<ENCODED_1>" in out and "<SECRET_" in out and "\u2039ENCODED" not in out, (
        "TB-3.23 views"
    )


def test_card_two_benign_runs_and_one_secret():
    got = channel.clean(f"note {B1} then {B2} and {SB} end")
    assert got == f"note {B1} then {B2} and <ENCODED_1> end", "TB-3.24 card"


def test_card_cap_refusal_is_a_raise(monkeypatch):
    monkeypatch.setattr(defaults, "B64_MAX_UNITS", 1)
    refused = "InputTooLarge(InputTooLarge)"
    assert _outcome(lambda: channel.clean(f"a {B1} b {B2}")) == refused, "TB-3.25 channel.clean"
    got = _outcome(lambda: cards.render_abstain("r", "x", [f"{B1} {B2}"]))
    assert got == refused, "TB-3.25 cards.render_abstain"


def test_card_tag_split_blob():
    assert channel.clean(IP[:8] + "<i> </i>" + IP[8:]) == "<ENCODED_1>", "TB-3.26 tag split"


W = "\n".join(textwrap.wrap(b64("2026-11-20 deploy db_password=" + S12 + " applied"), 32))


def test_encoded_through_enforce_map_and_snapshot():
    m = runmap.RunMap({"<ENCODED_1>": W})
    t = "x " + W + " y"
    assert runmap.enforce_map(t, m) == "x <ENCODED_1> y", "TB-3.27 enforce_map"
    snap = runmap.snapshot(m)
    assert runmap.held_value_left("x <ENCODED_1> y", snap) is False, "TB-3.27 placeholder text"
    assert runmap.held_value_left(t, runmap.snapshot(m)) is True, "TB-3.27 raw text"


def test_map_ceiling(tmp_path):
    from tests.k5_support import ScriptLLM, build_runtime, handle, k5_cfg

    rnd = random.Random(5)  # noqa: S311 - a seeded test generator, not a secret

    def doc(n):
        words = [
            "".join(rnd.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(12))
            for _ in range(n)
        ]
        return " ".join(b64("password=" + w) for w in words).encode()

    cfg = k5_cfg(tmp_path, config={"evidence": {"max_map_entries": 40}})
    rt, _ = build_runtime(cfg, ScriptLLM([{"noaction": True}]))
    run = handle(rt, document=doc(15))
    assert run.reason_code != "document_too_complex", "TB-3.28 15 blobs stop the run"
    cfg2 = k5_cfg(tmp_path / "b", config={"evidence": {"max_map_entries": 40}})
    rt2, _ = build_runtime(cfg2, ScriptLLM([{"noaction": True}]))
    run2 = handle(rt2, document=doc(25))
    assert (run2.state, run2.reason_code) == (RunState.NEEDS_PERSON, "document_too_complex"), (
        "TB-3.28 25 blobs"
    )


def test_held_wrapped_original_is_not_decoded_again(monkeypatch):
    m = runmap.RunMap()
    first = runmap.redact_text(W, m)
    spy = _Spy(monkeypatch)
    second = runmap.redact_text(W, m)
    assert first == second == "<ENCODED_1>", "TB-3.29 output"
    assert spy.n == 0, "TB-3.29 the held block was decoded again"


def test_held_block_of_any_width_is_not_decoded_again(monkeypatch):
    t = "\n".join(textwrap.wrap(BL, 30))
    m = runmap.RunMap()
    spy = _Spy(monkeypatch)
    assert runmap.redact_text(t, m) == "<ENCODED_1>", "TB-3.29b first call"
    assert spy.n == 1, "TB-3.29b first call decodes the join once"
    before = dict(m)
    spy.n = 0
    assert runmap.redact_text(t, m) == "<ENCODED_1>", "TB-3.29b second call"
    assert spy.n == 0, "TB-3.29b the held block was decoded again"
    assert dict(m) == before, "TB-3.29b the map changed"


def test_card_url_credential_blob():
    assert channel.clean(f"see {b64('http://u:' + PW + '@h.io')} now") == "see <ENCODED_1> now", (
        "TB-3.31 card"
    )


def test_card_curl_credential_blob():
    assert channel.clean(f"see {b64('curl -u user:' + PW)} now") == "see <ENCODED_1> now", (
        "TB-3.32 card"
    )


def test_spelled_work_through_a_decoded_blob(monkeypatch):
    t = "password=ab!" + SB + "\n" + " ".join([SB] * 3000)
    m = runmap.RunMap({"<IPV4_1>": "10.0.0.1"})
    before = dict(m)
    runmap.redact_text(t, runmap.RunMap({"<IPV4_1>": "10.0.0.1"}))  # no raise without the patch
    monkeypatch.setattr(defaults, "SPELLED_MAX_WORK", 1000)
    got = _outcome(lambda: runmap.redact_text(t, m))
    assert got == "InputTooLarge(SpelledWorkTooMuch)", "TB-3.33 refusal"
    assert dict(m) == before, "TB-3.33 the map was written"


def test_url_credential_blob_kept_entry():
    blob = b64("http://u:" + PW + "@h.io")
    m: dict[str, str] = {}
    assert runmap.redact_text(blob, m) == "<ENCODED_1>", "TB-3.34 output"
    assert m == {"<URLCRED_1>": PW, "<ENCODED_1>": blob}, "TB-3.34 map"


def test_decoded_text_is_neutralised():
    blob = b64("password=<FOO_1>")
    assert runmap.redact_text(blob, runmap.RunMap()) == "<ENCODED_1>", "TB-3.35 redact_text"
    assert runmap.redact_untrusted(blob, runmap.RunMap()) == "<ENCODED_1>", (
        "TB-3.35 redact_untrusted"
    )
    # a benign decoded text that merely holds a placeholder look-alike is NOT a hit (the look-alike is escaped before the scan)
    benign = b64("status <FOO_1> is ok here")
    m: dict[str, str] = {}
    assert runmap.redact_text(benign, m) == benign and m == {}, (
        "TB-3.35 a look-alike in decoded text is no hit"
    )


def test_decoded_text_gets_its_views():
    m: dict[str, str] = {}
    assert runmap.redact_text(b64("password%3D" + S12), m) == "<ENCODED_1>", "TB-3.36 output"
    assert m["<SECRET_1>"] == S12, "TB-3.36 the secret of the view"


def test_wrapped_at_any_width(monkeypatch):
    spy = _Spy(monkeypatch)
    for w in (18, 30, 34, 38, 50):
        t = "\n".join(textwrap.wrap(BL, w))
        for fn in (runmap.redact_text, runmap.redact_untrusted):
            m = runmap.RunMap()
            spy.n = 0
            assert fn(t, m) == "<ENCODED_1>", f"TB-3.37 width {w} output"
            assert sorted(m) == ["<ENCODED_1>", "<SECRET_1>"], f"TB-3.37 width {w} keys"
            assert m["<SECRET_1>"] == S12 and m["<ENCODED_1>"] == t, f"TB-3.37 width {w} values"
            assert spy.n == 1, f"TB-3.37 width {w} decodes"
    for w in (70, 90):
        t = "\n".join(textwrap.wrap(BL, w))
        for fn in (runmap.redact_text, runmap.redact_untrusted):
            m = runmap.RunMap()
            spy.n = 0
            assert fn(t, m) == "<HIGHENTROPY_1>\n<HIGHENTROPY_2>", f"TB-3.37 held width {w} output"
            assert spy.n == 0, f"TB-3.37 held width {w} decodes"
            assert not any("ENCODED" in k for k in m), f"TB-3.37 held width {w} ENCODED key"


def test_loose_block_falls_back_to_its_lines(monkeypatch):
    a = b64("pwd=" + S12 + "abcd").rstrip("=")
    b = b64("pwd=" + S12[::-1] + "wxyz").rstrip("=")
    spy = _Spy(monkeypatch)
    for fn in (runmap.redact_text, runmap.redact_untrusted):
        m = runmap.RunMap()
        spy.n = 0
        assert fn(a + "\n" + b, m) == "<ENCODED_1>\n<ENCODED_2>", "TB-3.38 output"
        want = {
            "<SECRET_1>": S12 + "abcd",
            "<SECRET_2>": S12[::-1] + "wxyz",
            "<ENCODED_1>": a,
            "<ENCODED_2>": b,
        }
        assert dict(m) == want, "TB-3.38 map"
        assert spy.n == 3, "TB-3.38 decodes"


H = hashlib.sha256(b"g4 v8").hexdigest()[:32]


def test_a_line_that_is_no_blob_does_not_hide_the_blob():
    cases = [
        (SB + "\nThanks", "<ENCODED_1>\nThanks"),
        ("here it is:\n" + SB + "\nThanks\nBob", "here it is:\n<ENCODED_1>\nThanks\nBob"),
        (H + "\n" + SB, H + "\n<ENCODED_1>"),
    ]
    for i, (t, want) in enumerate(cases):
        for out, m in _both(t):
            assert out == want, f"TB-3.39 case {i}"
            assert m == {"<SECRET_1>": S12, "<ENCODED_1>": SB}, f"TB-3.39 case {i} map"


def test_parts_follow_the_held_rule(monkeypatch):
    rnd = random.Random(20261120)  # noqa: S311 - a seeded test generator, not a secret
    r50 = "\n".join(textwrap.wrap(b64(bytes(rnd.randrange(256) for _ in range(102))), 50))
    m_on: dict[str, str] = {}
    spy = _Spy(monkeypatch)
    out = runmap.redact_text(r50, m_on)
    calls = spy.n
    with monkeypatch.context() as mp:
        _step_off(mp)
        m_off: dict[str, str] = {}
        off = runmap.redact_text(r50, m_off)
    assert (out, m_on) == (off, m_off), "TB-3.40 output and map differ from the step-off build"
    assert calls == 3, "TB-3.40 decodes (the join, the lines without the first, the last line)"


def test_a_long_block_is_one_unit(monkeypatch):
    rnd = random.Random(20261120)  # noqa: S311 - a seeded test generator, not a secret
    raw = b64(bytes(rnd.randrange(256) for _ in range(94000)))
    big = raw[: 2499 * 50 + 20]
    t = "\n".join(big[i : i + 50] for i in range(0, len(big), 50))
    spy = _Spy(monkeypatch)
    m: dict[str, str] = {}
    got = _outcome(lambda: runmap.redact_text(t, m))
    assert got == "<ENCODED_1>", "TB-3.41 output"
    assert m == {"<ENCODED_1>": t}, "TB-3.41 map"
    assert spy.n == 0, "TB-3.41 decodes"


def _straddling(width: int, lines: int) -> str:
    """A blob of `lines` full lines of `width` characters (a multiple of 4) whose secret straddles the first line break."""
    nbytes = width * 3 // 4 * lines
    text = "deploy db_password=" + S12
    text += " " * (nbytes - len(text))
    return b64(text)


def test_a_closing_line_does_not_hide_a_secret_across_a_line_break():
    """TB-3.42. A blob of full lines followed by a short alphabet-only line is one block whose join is junk; the secret across the
    first line break is found in the join WITHOUT the closing line (or without an odd first line)."""
    for width in (36, 32, 28):
        blob = _straddling(width, 2)
        lines = [blob[i : i + width] for i in range(0, len(blob), width)]
        assert len(lines) == 2 and len(lines[0]) == width, f"TB-3.42 recipe at {width}"
        for closing in ("Thanks", "EOF", "Regards"):
            t = "\n".join([*lines, closing])
            for fn in (runmap.redact_text, runmap.redact_untrusted):
                m = runmap.RunMap()
                out = fn(t, m)
                assert out == "<ENCODED_1>\n" + closing, (
                    f"TB-3.42 width {width} closing {closing}: {out!r}"
                )
                assert m["<SECRET_1>"] == S12, f"TB-3.42 width {width} secret"
    blob = _straddling(32, 2)
    lines = [blob[:32], blob[32:]]
    t = "\n".join([H, *lines])
    out = runmap.redact_text(t, m := runmap.RunMap())
    assert out == H + "\n<ENCODED_1>", "TB-3.42 odd first line"
    assert m["<SECRET_1>"] == S12, "TB-3.42 odd first line secret"


def test_kept_entries_of_the_block_scan_and_the_line_scan_do_not_collide():
    """TB-3.43. The scan of the units and the scan of the lines of a loose block each number their kept entries from the same
    start: kept as (kind, original) pairs, neither is lost, and a later plain copy of each value is swept."""
    t1, t2 = "Zq9xW4mT7pL2", "Kp7rTq2WmN5v"
    a = b64("pwd=" + t1 + "abcd").rstrip("=")
    b = b64("pwd=" + t2 + "wxyz").rstrip("=")
    t = (
        SB
        + " ok\n"
        + a
        + "\n"
        + b
        + "\nlater "
        + S12
        + " and "
        + t1
        + "abcd and "
        + t2
        + "wxyz end"
    )
    m = runmap.RunMap()
    out = runmap.redact_text(t, m)
    values = set(m.values())
    assert {S12, t1 + "abcd", t2 + "wxyz"} <= values, "TB-3.43 a kept entry was lost"
    for v in (S12, t1, t2):
        assert v not in out, "TB-3.43 a plain copy was left readable"
    assert len({k for k in m if k.startswith("<SECRET_")}) == 3, "TB-3.43 three kept secrets"


# strict xfails: the stated limits (the base64 view is not an adversary-proof gate)
@pytest.mark.xfail(strict=True, reason="L-B1: a blob glued to other base64 characters")
def test_limit_glued_prefix():
    out = runmap.redact_text("/v1/blob/" + SB, {})
    assert pc.leak_of(S12, out)[0] == "no", "TB-3.L-B1 glued prefix"


@pytest.mark.xfail(strict=True, reason="L-B4: a blob split across JSON fields")
def test_limit_split_fields():
    out = runmap.redact_text(json.dumps({"a": SB[:14], "b": SB[14:]}), {})
    assert pc.leak_of(S12, out)[0] == "no", "TB-3.L-B4 split fields"


@pytest.mark.xfail(strict=True, reason="L-B5: a wrapped blob with a log prefix on every line")
def test_limit_log_prefixed_lines():
    blob = b64("2026-11-20 deploy db_password=" + S12 + " applied")
    t = "\n".join("2026-11-20 INFO " + w for w in textwrap.wrap(blob, 16))
    assert pc.leak_of(S12, runmap.redact_text(t, {}))[0] == "no", "TB-3.L-B5 log prefix"


@pytest.mark.xfail(strict=True, reason="L-B2: base32 and hex are not decoded")
def test_limit_base32_hex():
    b = base64.b32encode(("password=" + S12).encode()).decode()
    h = ("password=" + S12).encode().hex()
    out = runmap.redact_text(b + " " + h, {})
    assert b not in out and h not in out, "TB-3.L-B2 base32 and hex"


@pytest.mark.xfail(
    strict=True,
    reason="L-B8: a decoded text with 10 % or more non-printable characters is not read",
)
def test_limit_padded_blob():
    """L-B8 (design result review 1, M2): `_printable_text` returns None for a decoded text where fewer than `B64_PRINTABLE_SHARE`
    of the characters are printable (`str.isprintable()` is False for NBSP and U+3000 too, and a binary container is such a text),
    so the unit is not decoded and stays readable beside pass one's misses. Three NBSP after `password=` + 12 characters are 3 of 24.
    A control (two NBSP, under the share) is read and masked. No fallback is built (a lead decision)."""
    pad = "\u00a0" * 3
    assert runmap._b64_text(b64("password=" + S12 + pad[:2])) is not None, "TB-3.L-B8 control"
    out = runmap.redact_text(b64("password=" + S12 + pad), {})
    assert pc.leak_of(S12, out)[0] == "no", "TB-3.L-B8 padded blob"


def test_jwt_segment_copy_is_masked_by_pass_one():
    """L-B7 (3.3), MEASURED in Phase 3: the ticket predicted a leak (a lone segment is held, so not decoded, and under 40 characters);
    pass one masks the copy as a piece of the JWT (`<JWT_3>`), so there is no leak and no strict xfail. Pinned as the plain string."""
    jwt = pc._jwt('{"pwd":"' + S12 + '"}')
    t = jwt + " and later " + jwt.split(".")[1]
    assert runmap.redact_text(t, {}) == "<JWT_1> and later <JWT_3>", "TB-3.L-B7 segment copy"


# ---------------------------------------------------------------------------------------------------------------------
# I16: what the step costs on texts with many runs that are not base64 (13.4). Run serially: pytest -m perf -p no:xdist
# ---------------------------------------------------------------------------------------------------------------------
WORDS = [
    "get",
    "user",
    "by",
    "id",
    "request",
    "handler",
    "config",
    "value",
    "retry",
    "count",
    "max",
    "timeout",
    "session",
    "token",
    "cache",
    "lookup",
    "table",
    "index",
    "build",
    "deploy",
    "service",
    "worker",
    "queue",
]
PLAIN_RATIO, PROSE_RATIO, PLANTED_RATIO, FLOOR_S = 1.15, 1.10, 1.15, 0.005


def _snake_text(planted: bool = False) -> str:
    rnd = random.Random(20261120)  # noqa: S311 - a seeded test generator, not a secret
    items: list[str] = []
    size = 0
    while size < 100_000:
        roll = rnd.random()
        if roll < 0.5:
            item = "_".join(rnd.choice(WORDS) for _ in range(rnd.randint(2, 5)))
        elif roll < 0.8:
            segs = [
                "_".join(rnd.choice(WORDS) for _ in range(rnd.randint(1, 3)))
                for _ in range(rnd.randint(2, 6))
            ]
            item = "/" + "/".join(segs) + ".py"
        else:
            item = rnd.choice(WORDS)
        items.append(item + rnd.choice([" ", "\\n", ", "]))
        size += len(items[-1])
    text = "".join(items)[:100_000]
    if planted:
        text = text[:50_000] + " password=" + S12 + " " + text[50_000:]
    return text


def _best_ratio(text: str, monkeypatch) -> tuple[float, float]:
    """(step on, step off) best-of-3 thread time of `redact_text`, interleaved, a fresh map per call."""
    on = off = float("inf")
    for _ in range(3):
        t0 = time.thread_time()
        runmap.redact_text(text, runmap.RunMap())
        on = min(on, time.thread_time() - t0)
        with monkeypatch.context() as mp:
            _step_off(mp)
            t0 = time.thread_time()
            runmap.redact_text(text, runmap.RunMap())
            off = min(off, time.thread_time() - t0)
    return on, off


@pytest.mark.perf
def test_perf_step_overhead(monkeypatch):
    prose = ("the quick brown fox jumps over the lazy dog and keeps going. " * 2000)[:100_000]
    for name, text, ratio in (
        ("plain", _snake_text(), PLAIN_RATIO),
        ("prose", prose, PROSE_RATIO),
        ("planted", _snake_text(planted=True), PLANTED_RATIO),
    ):
        on, off = _best_ratio(text, monkeypatch)
        assert on <= max(off * ratio, FLOOR_S), f"TB-3.30 {name}: {on:.3f}s on, {off:.3f}s off"
    rnd = random.Random(20261120)  # noqa: S311 - a seeded test generator, not a secret
    words = {
        "".join(rnd.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(12))
        for _ in range(defaults.B64_MAX_UNITS)
    }
    text = " ".join(b64("password=" + w) for w in sorted(words))
    t0 = time.thread_time()
    runmap.redact_text(text, runmap.RunMap())
    assert time.thread_time() - t0 < defaults.REDACT_BUDGET_S, "TB-3.30 the cap ceiling"
