"""G4 (ticket G4, sections 10.2 and 10.3): the base64 view of `runmap.redact_text` and the kind ENCODED.

Private names are reached INSIDE each test (`runmap.<name>`, `redact_mod.<name>`; no module-level import of a G4 name). Every
assertion message starts with its TB id and one space (`"TB-2.3 ..."`): tests/b64_mutants.py uses it as the mutant's `expect`.
A killer that expects a raise asserts an OUTCOME string, so its failure line still starts with the id.
"""

from __future__ import annotations

import importlib

from hadavin_sdk import defaults
from hadavin_sdk.approvals import channel
from hadavin_sdk.guard import runmap

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
    maps = [
        ({"<TENANT_1>": "cd-ef", "<SECRET_1>": "ab-cd"}, "x ab-<TENANT_1> y"),
        ({"<SECRET_1>": "ab-cd", "<TENANT_1>": "cd-ef"}, "x <SECRET_1>-ef y"),
        ({"<TENANT_1>": "ab-cd", "<SECRET_1>": "cd-ef"}, "x <TENANT_1>-ef y"),
        ({"<SECRET_1>": "cd-ef", "<TENANT_1>": "ab-cd"}, "x ab-<SECRET_1> y"),
    ]
    for i, (m, want) in enumerate(maps, start=1):
        got = _outcome(lambda m=m: runmap.enforce_map(text, dict(m)))
        assert got == want, f"TB-2.8 map {i}"
    fifth = {"<TENANT_1>": "cd-ef", "<SECRET_1>": "ab-cd", "<SECRET_2>": "cd-ef"}
    got = _outcome(lambda: runmap._Redactor(dict(fifth), None).sweep(text))
    assert got == "x <SECRET_1>-ef y", "TB-2.8 fifth map, the redactor's own sweep"
    got = _outcome(lambda: runmap.enforce_map(text, dict(fifth)))
    assert got == "x <SECRET_1>-ef y", "TB-2.8 fifth map, enforce_map"


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
