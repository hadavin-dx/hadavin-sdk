"""P1c: base64, whole host names and bare numbers through the PUBLIC redaction functions (ticket G4, section 10.1).

Public names only: `runmap.redact_text` and `runmap.redact_untrusted`. The rows are the probe's (tests/p1c_cases.py); a row that must
keep the base commit's output is compared by digest with tests/fixtures/p1c_base_digests.json (made on the base by
tests/fixtures/make_p1c_base_digests.py: digests, so no fake secret value is written).

`OPEN_ROWS` holds the rows a later phase of G4 closes; each is a STRICT xfail until then, so the branch is green at every commit
and `pytest --runxfail` on the base shows exactly those failures (FAIL-BEFORE). Every assertion message starts with `TG-I<n> `:
the mutants of tests/b64_mutants.py use it as their `expect`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hadavin_sdk.guard import runmap
from tests import p1c_cases as pc
from tests.warden_port import privacy_corpus

BASE = json.loads((Path(__file__).parent / "fixtures" / "p1c_base_digests.json").read_text())[
    "rows"
]

# Row ids this ticket closes: 57 base64 ids (G4a: 52 leaks and 5 kind changes) and 19 host ids (G4c). Phase 3 deletes the G4a keys,
# Phase 4 the G4c keys, Phase 5 this dict.
_LEAK_1B = (
    list(range(1, 6))
    + [7, 8]
    + list(range(33, 38))
    + [39, 40]
    + list(range(49, 54))
    + [56]
    + list(range(65, 73))
    + list(range(81, 89))
    + list(range(97, 102))
    + [104]
    + list(range(113, 118))
    + [120]
)
LEAK_IDS = [f"b64-1b-{n:03d}" for n in _LEAK_1B] + [f"b64-1c-{n:02d}" for n in (1, 2, 5, 9)]
KIND_CHANGE_IDS = [f"b64-1c-{n:02d}" for n in (3, 6, 7, 10, 11)]
HOST_CLOSED_IDS = [
    f"host-{n:02d}"
    for n in (1, 2, 17, 19, 21, 24, 26, 29, 32, 33, 34, 35, 36, 37, 38, 39, 40, 43, 44)
]
OPEN_ROWS: dict[str, str] = {
    **dict.fromkeys(LEAK_IDS + KIND_CHANGE_IDS, "G4a"),
    **dict.fromkeys(HOST_CLOSED_IDS, "G4c"),
}

CASES = pc.build()
FUNCTIONS = {"text": runmap.redact_text, "untrusted": runmap.redact_untrusted}


def _params(rows, fn=lambda row: row):
    out = []
    for row in rows:
        marks = []
        if row[0] in OPEN_ROWS:
            marks.append(pytest.mark.xfail(strict=True, reason=f"closed by {OPEN_ROWS[row[0]]}"))
        out.append(pytest.param(fn(row), id=row[0], marks=marks))
    return out


def _run(fn, text):
    mapping: dict[str, str] = {}
    out = fn(text, mapping)
    return out, mapping


def _digest_of(fn, text):
    out, mapping = _run(fn, text)
    return pc.digest(out, mapping)


# ---------------------------------------------------------------------------------------------------------------------
# I1, I2, I3: the 142 base64 rows
# ---------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("row", _params(CASES.b64))
def test_base64_row(row):
    row_id, protected, text = row
    for which, fn in FUNCTIONS.items():
        out, mapping = _run(fn, text)
        if row_id in LEAK_IDS:  # I1: the 52 leak rows
            assert pc.leak_of(protected, out)[0] == "no", f"TG-I1 leak in {row_id} ({which})"
            assert "<ENCODED_" in out, f"TG-I1 no ENCODED in {row_id} ({which})"
        elif row_id in KIND_CHANGE_IDS:  # I3: the 5 kind-change rows
            assert out == "<ENCODED_1>", f"TG-I3 output of {row_id} ({which})"
            kinds = {k.split("_")[0].lstrip("<") for k in mapping}
            assert "HIGHENTROPY" not in kinds, f"TG-I3 HIGHENTROPY entry in {row_id} ({which})"
        else:  # I2: the 85 rows that must stay as at the base
            assert pc.digest(out, mapping) == BASE[f"{row_id}/{which}"], (
                f"TG-I2 digest of {row_id} ({which})"
            )


# ---------------------------------------------------------------------------------------------------------------------
# I4: what must keep its output (17 base64 look-alikes, 60 privacy rows)
# ---------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("row", [pytest.param(r, id=r[0]) for r in pc.MUST_KEEP_B64])
def test_must_keep_b64(row):
    k, text = row
    for which, fn in FUNCTIONS.items():
        assert _digest_of(fn, text) == BASE[f"mustkeep-b64-{k}/{which}"], (
            f"TG-I4 digest of mustkeep-b64-{k} ({which})"
        )


def _privacy():
    rows = [t for texts in privacy_corpus.MASKED.values() for t in texts]
    named = [(f"masked-{k:02d}", t) for k, t in enumerate(rows, start=1)]
    named += [(f"kept-{k:02d}", t) for k, t in enumerate(privacy_corpus.KEPT, start=1)]
    # the two HOSTNAME rows at lines 36 and 37 of the corpus change under G4c: I12b (TB-4.9) owns them
    return [r for r in named if r[0] not in ("masked-27", "masked-28")]


@pytest.mark.parametrize("row", [pytest.param(r, id=r[0]) for r in _privacy()])
def test_must_keep_corpus(row):
    row_id, text = row
    for which, fn in FUNCTIONS.items():
        assert _digest_of(fn, text) == BASE[f"{row_id}/{which}"], (
            f"TG-I4 digest of {row_id} ({which})"
        )


# ---------------------------------------------------------------------------------------------------------------------
# I9: a second pass changes nothing, over the 229 probe inputs
# ---------------------------------------------------------------------------------------------------------------------
_ALL = (
    [(i, t) for i, _p, t in CASES.b64]
    + [(i, t) for i, _n, t in CASES.hosts]
    + [(i, t) for i, _n, t in CASES.numbers]
)


@pytest.mark.parametrize("row", [pytest.param(r, id=r[0]) for r in _ALL])
def test_idempotent(row):
    row_id, text = row
    mapping: dict[str, str] = {}
    out = runmap.redact_text(text, mapping)
    before = dict(mapping)
    again = runmap.redact_text(out, mapping)
    assert again == out, f"TG-I9 second pass changed {row_id}"
    assert mapping == before, f"TG-I9 the map grew on the second pass of {row_id}"


# ---------------------------------------------------------------------------------------------------------------------
# I10: redact_untrusted agrees with redact_text
# ---------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("row", [pytest.param(r, id=r[0]) for r in CASES.b64])
def test_parity_base64(row):
    row_id, protected, text = row
    a = pc.leak_of(protected, runmap.redact_text(text, {}))[0] == "no"
    b = pc.leak_of(protected, runmap.redact_untrusted(text, {}))[0] == "no"
    assert a == b, f"TG-I10 the two functions disagree on {row_id}"


@pytest.mark.parametrize("row", [pytest.param(r, id=r[0]) for r in CASES.hosts + CASES.numbers])
def test_parity_text(row):
    row_id, _name, text = row
    assert runmap.redact_text(text, {}) == runmap.redact_untrusted(text, {}), (
        f"TG-I10 outputs differ on {row_id}"
    )


# ---------------------------------------------------------------------------------------------------------------------
# I11, I12: host names
# ---------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("row", [pytest.param(r, id=f"hostkeep-{r[0]}") for r in pc.HOST_MUST_KEEP])
def test_host_must_keep(row):
    k, text = row
    for which, fn in FUNCTIONS.items():
        assert _digest_of(fn, text) == BASE[f"hostkeep-{k}/{which}"], (
            f"TG-I11 digest of hostkeep-{k} ({which})"
        )


@pytest.mark.parametrize("row", _params(CASES.hosts))
def test_host_row(row):
    row_id, name, text = row
    out = runmap.redact_text(text, {})
    if row_id in HOST_CLOSED_IDS:  # the 19 closed rows: no label of the name is left readable
        assert pc.host_kept_labels(name, text, out) == [], f"TG-I12 label kept in {row_id}"
    else:  # the other 25 rows keep the base commit's output
        for which, fn in FUNCTIONS.items():
            assert _digest_of(fn, text) == BASE[f"{row_id}/{which}"], (
                f"TG-I12 digest of {row_id} ({which})"
            )


# ---------------------------------------------------------------------------------------------------------------------
# I18: bare numbers, written down and pinned by class (section 6)
# ---------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("row", [pytest.param(r, id=r[0]) for r in CASES.numbers])
def test_number_row(row):
    row_id, number, text = row
    want = pc.NUMBER_CLASS[int(row_id.split("-")[1]) - 1]
    assert pc.number_class(number, runmap.redact_text(text, {})) == want, (
        f"TG-I18 class of {row_id}"
    )


# ---------------------------------------------------------------------------------------------------------------------
# I25: the inputs are the probe's inputs
# ---------------------------------------------------------------------------------------------------------------------
def test_inputs_are_the_probe_inputs():
    assert pc.inputs_sha() == pc.I25_SHA, "TG-I25 the probe inputs moved"
    assert (len(CASES.b64), len(CASES.hosts), len(CASES.numbers)) == (142, 44, 43), (
        "TG-I25 row counts"
    )
    assert len(OPEN_ROWS) == 76, "TG-I25 open rows"
