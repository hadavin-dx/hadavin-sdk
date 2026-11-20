"""ORDER 013 item 2: ONE property over the repo's existing hostile and fuzz corpora, to make a whole class visible.

For every input x of the corpora below, through `runmap.redact_text` with one run map:
  (a) a second pass changes nothing: `redact_text(redact_text(x, m), m)` is the first result and `m` is the same;
  (b) no original value of the map occurs raw in the output, by the redactor's own rule for copies (`redact._sweep`):
      a value of a secret kind of 4 characters or more, nowhere outside a placeholder; any other value, nowhere as a
      token of its own (no ASCII letter or digit touching it). Values the rule never sweeps (under 3 characters,
      all digits under 6, a common word such as `prod`) are not checked: that is the redactor's stated rule, not a
      finding of this test.
An input the redactor REFUSES (InputTooLarge, TooDeep: nothing is returned) satisfies both vacuously and is counted.

The corpora (nothing is dropped from any of them; `test_the_corpus_is_what_this_file_says` pins the counts):
  privacy        tests/warden_port/privacy_corpus.py              MASKED (every class) and KEPT
  bank           tests/warden_port/test_redaction_bank.py         POSITIVE, NEGATIVE, PINNED
  review2        tests/warden_port/test_redaction_review2.py      LEAKS, FALSE_POSITIVES
  cookies        tests/warden_port/test_redaction_review9.py      COOKIES, each with the file's session value
  own-shapes     tests/warden_port/test_redaction.py              OWN_SHAPES
  spellings      tests/test_k5_round8.py                          SPELLINGS (the layered spellings round 8 and 9 drive)
  round12-fuzz   tests/test_k5_round12_fuzz.py                    `_case`, its seed, its 1,200 cases
  round-trip     tests/redact_corpus_support.py                   `random_text`, its seed, 300 texts; LOOKALIKES
  p1c            tests/p1c_builders.py                            gap1_values (short and long), gap2_cases, gap3_cases
  g7             tests/test_redact_context_after_sweep.py         SHAPES, MUST_KEEP, E5 (the shapes G7 was built on)
  constructed    this file                                        CONSTRUCTED: built to find what one extra pass misses
Measured 2026-11-20 (fix round 3, settle as a real fixed point): 1,835 inputs, 0 refused (asserted), 0 fail. With settle
switched off, 9 fail (5 g7 shapes, 3 g7 E5, `constructed:0`); with ONE extra pass (the round 1 design) only `constructed:0` fails;
no input of the older corpora fails with or without it. The generated compositions aimed at the class (4 to 8 lines of key=V,
glued bank codes, short Bearer/Basic/authorization/sig/auth with V glued, account after code, copies, half of them from a
pre-seeded run map) are in tests/test_redact_settle_loop.py, against a reference fixed-point loop.
Not used, because they are not inputs of the redactor: tests/demo_askdata/fuzzgen.py (SQL for the demo's validator),
tests/test_peel_run_id.py HOSTILE (run ids), tests/fixtures/textnorm_corpus.json (name pairs for the fold).

Property (c) is a raw-copy check that does NOT call the production sweep: no 4-character piece of an original of a secret
kind may stand outside a placeholder in the output. (b) stays, by the redactor's own rule, for the other kinds.
A chain that needs more rounds than the cap is a refusal (RedactionError), never a silent leak: the real corpora must
not refuse (`test_no_input_of_the_corpora_is_refused`).
"""

from __future__ import annotations

import importlib
import importlib.util
import pathlib
import random
import sys

import pytest

from hadavin_sdk.guard import runmap
from tests import p1c_builders as p1c
from tests import redact_corpus_support as round_trip
from tests import test_k5_round8 as round8
from tests import test_k5_round12_fuzz as round12
from tests import test_redact_context_after_sweep as g7
from tests.warden_port import privacy_corpus
from tests.warden_port import test_redaction as port
from tests.warden_port import test_redaction_bank as bank
from tests.warden_port import test_redaction_review2 as review2
from tests.warden_port import test_redaction_review9 as review9

importlib.import_module("hadavin_sdk.guard.redact")
R = sys.modules["hadavin_sdk.guard.redact"]

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_P1C = (
    _ROOT / "handover" / "core-c" / "evidence" / "p1c_probe.py"
)  # the evidence file the builders came from: read by the parity test only


# Built for this file while looking for what ONE extra pass cannot settle (the corpora above had no such input).
_V = "abcd" + "9x"
CONSTRUCTED = [
    # 0: a chain of three. Pass 1 finds the password; its sweep frees the bank code from the letters glued to it;
    # round 1 finds the code; the second sweep writes the code's placeholder before the account; round 2 reads the
    # account; round 3 changes nothing and ends the loop (a fixed point; see `_Redactor.settle`).
    f"password={_V}\nBSB: {g7.BSB}{_V}\npaid {g7.BSB}/{g7.ACCOUNT}",
]


def _build() -> list[tuple[str, str]]:
    """(id, text) for every input, in a fixed order. Ids are `corpus:index` and never hold a value."""
    rows: list[tuple[str, str]] = []

    def add(corpus: str, texts) -> None:
        rows.extend((f"{corpus}:{i}", text) for i, text in enumerate(texts))

    add("privacy-masked", [t for texts in privacy_corpus.MASKED.values() for t in texts])
    add("privacy-kept", privacy_corpus.KEPT)
    add("bank-positive", [row[1] for row in bank.POSITIVE])
    add("bank-negative", [row[1] if isinstance(row, tuple) else row for row in bank.NEGATIVE])
    add("bank-pinned", [row[1] if isinstance(row, tuple) else row for row in bank.PINNED])
    add("review2-leaks", [text for text, _ in review2.LEAKS])
    add("review2-kept", review2.FALSE_POSITIVES)
    add("cookies", [form % review9.S for form in review9.COOKIES])
    add("own-shapes", [text for _, text, _ in port.OWN_SHAPES])
    add("spellings", list(round8.SPELLINGS.values()))
    rng = random.Random(round12.SEED)  # noqa: S311 - a test fixture generator, not a secret
    add("round12-fuzz", [round12._case(rng)[0] for _ in range(round12.CASES)])
    rng = random.Random(20261120)  # noqa: S311 - the seed the round-trip corpus was built with
    add("round-trip", [round_trip.random_text(rng) for _ in range(300)])
    add("lookalikes", round_trip.LOOKALIKES)
    p1c.reseed()  # the probe's own seed, so the built values are the same on every run
    values = p1c.gap1_values()
    add("p1c-gap1", [v[k] for v in values for k in ("short", "long")])
    add("p1c-gap2", [text for _, _, text in p1c.gap2_cases()])
    add("p1c-gap3", [text for _, _, text in p1c.gap3_cases()])
    add("g7-shapes", [g7.SHAPES[k] for k in sorted(g7.SHAPES)])
    add("g7-must-keep", g7.MUST_KEEP)
    add("g7-e5", [g7.E5[k][0] for k in sorted(g7.E5)])
    add("constructed", CONSTRUCTED)
    return rows


CORPUS = _build()


def _free_text(out: str) -> str:
    """The output without its placeholder tokens (a value such as `SECRET` or `1` occurs inside every token)."""
    return "\x00".join(R._PLACEHOLDER.split(out)[0::2])


def raw_copies(out: str, mapping: dict[str, str]) -> list[str]:
    """The placeholders whose original still stands raw in `out`, by the redactor's rule for copies."""
    free, found = _free_text(out), []
    for placeholder, original in mapping.items():
        rule = R._sweep(placeholder, original)
        if rule is None or original not in free:
            continue
        if rule is R._EVERY_COPY or R._replace_standalone(free, original, "\x00") != free:
            found.append(placeholder)
    return found


def piece_leaks(text: str, out: str, mapping: dict[str, str]) -> list[str]:
    """(c) A check that does NOT call the production sweep or its rules: the placeholders of a secret kind with a 4-character
    piece that stands MORE often outside a placeholder in `out` than in the input once every original of the map is cut
    out of it (a piece such as `ecre` of `Cl5ecretV` is also in the word `secret` of the text: that is not a copy)."""
    rest = text
    for original in sorted(mapping.values(), key=len, reverse=True):
        rest = rest.replace(original, "\x00")
    free, found = _free_text(out), []
    for placeholder, original in mapping.items():
        if R.kind_of(placeholder) in R.SECRET_KINDS and any(
            free.count(piece) > rest.count(piece)
            for piece in {original[i : i + 4] for i in range(len(original) - 3)}
        ):
            found.append(placeholder)
    return found


def check(text: str) -> tuple[str, list[str]]:
    """("refused" | "ok" | "fails", what failed). Never returns a value: kinds and placeholder names only."""
    mapping = runmap.RunMap()
    try:
        once = runmap.redact_text(text, mapping)
    except runmap.RedactionError:
        return "refused", []
    held = dict(mapping)
    why = []
    try:
        twice = runmap.redact_text(once, mapping)
    except runmap.RedactionError as exc:
        return "fails", [f"the second pass refused the first pass's output ({exc})"]
    if twice != once:
        why.append("a second pass changed the text")
    if dict(mapping) != held:
        new = sorted({R.kind_of(p) for p in mapping if p not in held})
        why.append(f"a second pass grew the map by {len(mapping) - len(held)} ({', '.join(new)})")
    raw = raw_copies(once, held)
    if raw:
        why.append(f"raw copy of {sorted({R.kind_of(p) for p in raw})} in the output")
    pieces = piece_leaks(text, once, held)
    if pieces:
        why.append(f"a 4-character piece of {sorted({R.kind_of(p) for p in pieces})} in the output")
    return ("fails" if why else "ok"), why


def _params():
    for case_id, text in CORPUS:
        yield pytest.param(text, id=case_id)


@pytest.mark.parametrize("text", list(_params()))
def test_one_pass_is_a_fixed_point_and_leaves_no_raw_copy(text):
    state, why = check(text)
    assert state != "fails", "; ".join(why)


def test_the_corpus_is_what_this_file_says():
    """Nothing dropped: every corpus is there with its full count, and every listed limit is a real input."""
    counts: dict[str, int] = {}
    for case_id, _ in CORPUS:
        counts[case_id.split(":")[0]] = counts.get(case_id.split(":")[0], 0) + 1
    assert counts["privacy-masked"] == sum(len(v) for v in privacy_corpus.MASKED.values())
    assert counts["privacy-kept"] == len(privacy_corpus.KEPT)
    assert counts["bank-positive"] == len(bank.POSITIVE)
    assert counts["bank-negative"] == len(bank.NEGATIVE)
    assert counts["bank-pinned"] == len(bank.PINNED)
    assert counts["review2-leaks"] == len(review2.LEAKS)
    assert counts["cookies"] == len(review9.COOKIES)
    assert counts["own-shapes"] == len(port.OWN_SHAPES)
    assert counts["round12-fuzz"] == round12.CASES == 1200
    assert counts["round-trip"] == 300
    assert counts["p1c-gap1"] == 16
    assert len(CORPUS) == sum(counts.values()) == EXPECTED_INPUTS
    assert len({case_id for case_id, _ in CORPUS}) == len(CORPUS)
    assert counts["p1c-gap2"] == P1C_GAP2 and counts["p1c-gap3"] == P1C_GAP3


def test_the_piece_check_sees_a_tail_and_ignores_a_word_of_the_text():
    mapping = {"<SECRET_1>": "ab9x", "<BEARER_1>": "ab9xqrstu"}
    assert piece_leaks("password=ab9x Bearer ab9xqrstu", "x <SECRET_1>qrstu y", mapping) == [
        "<BEARER_1>"
    ]
    assert piece_leaks("password=ab9x Bearer ab9xqrstu", "x <BEARER_1> y", mapping) == []
    # a piece of the secret that is also a word of the text is not a copy
    assert (
        piece_leaks("secret and Cl5ecretV", "secret and <SECRET_1>", {"<SECRET_1>": "Cl5ecretV"})
        == []
    )


def test_the_check_itself_sees_a_raw_copy_and_a_second_pass_that_changes():
    """The property is not vacuous: the two failures it is for are seen on made-up outputs."""
    secret = "hun" + "ter" + "2" + "zz"
    assert raw_copies(f"x {secret} y", {"<SECRET_1>": secret}) == ["<SECRET_1>"]
    assert raw_copies(f"x{secret}y", {"<SECRET_1>": secret}) == [
        "<SECRET_1>"
    ]  # a secret: every copy
    ip = "10." + "1.2.3"
    assert raw_copies(f"at {ip} now", {"<IPV4_1>": ip}) == ["<IPV4_1>"]
    assert (
        raw_copies(f"v{ip}9", {"<IPV4_1>": ip}) == []
    )  # an identifier inside a longer token: not a copy
    assert raw_copies("status 500", {"<TENANT_1>": "500"}) == []  # the rule never sweeps it
    assert (
        raw_copies("see <SECRET_1>", {"<SECRET_1>": "SECRET"}) == []
    )  # inside a placeholder token
    # the old one-pass result of the bank shape is exactly what (a) is for
    old = f"BSB: <BANKCODE_1>\npaid <BANKCODE_1>/{g7.ACCOUNT}"
    mapping = runmap.RunMap({"<BANKCODE_1>": g7.BSB})
    assert runmap.redact_text(old, mapping) != old


def test_the_tail_of_a_compound_value_found_late_is_swept_from_its_other_copies():
    """Was a stated limit (the first sweep cut the other copy to `<SECRET_1>tail` before V+tail existed); fixed by sweeping the
    placeholder-spelled form of a compound entry as a literal (ORDER 020 dz-2)."""
    short = "ab" + "9x"
    tail = "qrs" + "tu"
    text = f"password={short}\nBearer {short}{tail}\nnote {short}{tail}vw end"
    mapping = runmap.RunMap()
    out = runmap.redact_text(text, mapping)
    assert mapping["<BEARER_1>"] == short + tail  # found by the second pass, stored whole
    assert tail not in out


def test_no_input_of_the_corpora_is_refused():
    """The ticket says 0 refused; nothing asserted it (a refusal passes (a) and (b) vacuously)."""
    refused = [case_id for case_id, text in CORPUS if check(text)[0] == "refused"]
    assert refused == []


def test_the_constructed_chain_is_one_call_and_check_reports_a_refusal_as_refused(monkeypatch):
    """The chain of three is masked in one call at the real cap. `check` must report a refusal as "refused", not "ok" or "fails":
    a cap of 1 is patched in here ONLY to drive that path (the cap's real boundary is tested, unpatched, in
    tests/test_redact_settle_loop.py)."""
    mapping = runmap.RunMap()
    out = runmap.redact_text(CONSTRUCTED[0], mapping)
    assert g7.ACCOUNT not in out
    monkeypatch.setattr(R, "_SETTLE_ROUNDS", 1)
    assert check(CONSTRUCTED[0])[0] == "refused"  # never a silent leak


@pytest.mark.skipif(not _P1C.exists(), reason="the evidence probe file is not in this checkout")
def test_the_moved_builders_give_the_rows_of_the_evidence_probe():
    """Codebase M4: the three builders live in tests/p1c_builders.py now. When the evidence probe is still there, both give the same rows
    from the same seed, called in the order the corpus uses (this test, and only this one, loads the probe file: its builders only, its
    `main()` runs under `__main__`; it never reads the probe's output). Skipped, and only this test, when the file is gone."""
    spec = importlib.util.spec_from_file_location("g7_p1c_probe_parity", _P1C)
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    probe.RNG.seed(p1c.SEED)
    want = (probe.gap1_values(), probe.gap2_cases(), probe.gap3_cases())
    p1c.reseed()
    got = (p1c.gap1_values(), p1c.gap2_cases(), p1c.gap3_cases())
    assert got == want
    assert [len(x) for x in got] == [8, P1C_GAP2, P1C_GAP3]


EXPECTED_INPUTS = 1835
P1C_GAP2 = 44  # the p1c probe's gap2 and gap3 cases, pinned: a probe that shrinks must be looked at
P1C_GAP3 = 43  # measured 2026-11-20: a corpus that grows or shrinks must be looked at
