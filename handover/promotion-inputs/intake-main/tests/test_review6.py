"""Review round 6: live-run gate, PO grammar agreement, Policy immutability, egress fold and exact matching,
mutation judge classes, core-copy pins, line endings. Every test here fails on the code before this round."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

import pytest

from intake import rules
from intake.egress import check_egress
from intake.tools import normalise_po

ROOT = Path(__file__).resolve().parents[1]
POL = rules.load_policy()
RAW = json.loads((ROOT / "config" / "policy.json").read_text(encoding="utf-8"))
TODAY = date(2026, 11, 2)


def _live(**over):
    block = {
        "allowed": True,
        "provider_no_training_setting": "zero data retention on the API organisation",
        "training_use": False,
        "setting_checked_on": "2026-11-01",
        "setting_max_age_days": 90,
        "region": "us",
        "owner_yes_quote": "yes, USD 0.58",
    }
    block.update(over)
    return {"live_run": block}


def test_live_run_gate_accepts_the_complete_block_and_never_raises_on_a_malformed_one():
    assert rules.live_run_allowed(_live(), TODAY) is True
    assert rules.live_run_allowed(RAW, TODAY) is False  # the shipped policy: nothing checked
    for bad in ({"live_run": None}, {"live_run": []}, {"live_run": "yes"}, {"live_run": 1}, {}, None, [], "x"):
        try:
            got = rules.live_run_allowed(bad, TODAY)
        except Exception as exc:  # noqa: BLE001
            got = f"RAISED {type(exc).__name__}"  # old code: AttributeError on None and []
        assert got is False, (bad, got)


@pytest.mark.parametrize(
    "over",
    [
        {"training_use": None},
        {"training_use": True},
        {"training_use": "false"},  # not the boolean
        {"training_use": 0},
        {"allowed": "yes"},  # truthy but not the boolean true
        {"allowed": 1},
        {"setting_checked_on": "2026-12-01"},  # in the future
        {"setting_checked_on": "2026-02-01"},  # 274 days old: stale
        {"setting_checked_on": "2026-W44-1"},
        {"setting_checked_on": "20261101"},
        {"setting_checked_on": "2026-11-01\n"},
        {"setting_checked_on": "not a date"},
        {"setting_checked_on": 20261101},
        {"setting_max_age_days": None},
        {"setting_max_age_days": True},
        {"setting_max_age_days": -1},
        {"setting_max_age_days": "90"},
        {"region": "  "},
        {"region": 5},
        {"owner_yes_quote": ""},
        {"provider_no_training_setting": ["zero retention"]},
    ],
)
def test_live_run_gate_refuses_every_field_that_is_set_but_not_valid(over):
    assert rules.live_run_allowed(_live(**over), TODAY) is False, over


def test_live_run_gate_date_window_is_inclusive_and_uses_the_real_clock_by_default():
    assert rules.live_run_allowed(_live(setting_checked_on="2026-08-04"), TODAY) is True  # exactly 90 days
    assert rules.live_run_allowed(_live(setting_checked_on="2026-08-03"), TODAY) is False  # 91 days
    assert rules.live_run_allowed(_live(setting_checked_on="2026-11-02"), TODAY) is True  # today
    assert rules.live_run_allowed(_live(setting_checked_on="2026-11-03"), TODAY) is False  # tomorrow
    # a date that is always valid whatever the real clock: far future is refused, far past is refused
    assert rules.live_run_allowed(_live(setting_checked_on="2099-01-01")) is False
    assert rules.live_run_allowed(_live(setting_checked_on="2000-01-01")) is False


def test_the_shipped_policy_carries_the_new_live_run_keys_with_the_gate_closed():
    lr = RAW["live_run"]
    assert lr["allowed"] is False and lr["training_use"] is None and lr["setting_max_age_days"] == 90
    assert rules.live_run_allowed(RAW) is False


# --- PO grammar: normalise_po and po_valid agree --------------------------------------------------------------------------------


def test_normalise_po_key_is_pinned_and_documented_as_the_specified_fold():
    # R-INTAKE-017: the letter O reads as 0 and a leading 0 of a digit run is stripped, so 'PO-48211' keys as 'P48211' (not a bug)
    assert normalise_po("PO-48211") == "P48211"
    assert normalise_po("PO-0048211") == normalise_po("po 48211") == normalise_po("PO48211") == "P48211"
    assert "R-INTAKE-017" in (ROOT / "gate_rules.md").read_text(encoding="utf-8")
    assert "'P48211'" in normalise_po.__doc__


@pytest.mark.parametrize(
    "bad", ["PO-1\n", "PO-1\r\n", "\nPO-1", "PO\t1", "PO-1\x00", "PO-1\x1b[0m", "PO#1", "PO-1;x", "=HYPERLINK(1)", "PO 1", "PO -1"]
)
def test_normalise_po_refuses_what_po_valid_refuses_for_characters(bad):
    with pytest.raises(ValueError):
        normalise_po(bad)  # old code: 'PO-1\n' normalised to 'P1' while po_valid refused it
    assert not rules.po_valid(bad, POL)


def test_po_valid_implies_normalise_po_succeeds_and_the_character_sets_are_the_same():
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ./_-")
    for ch in map(chr, range(0, 0x250)):
        try:
            normalise_po("PO-" + ch + "1")
            ok = True
        except ValueError:
            ok = False
        assert ok == (ch in allowed), repr(ch)
        if rules.po_valid("PO-" + ch + "1", POL):
            assert ok, repr(ch)  # valid => normalisable
    for good in ("PO-48211", "po 48211", "A/12.7_x", "X" * 30, "a b c"):
        assert rules.po_valid(good, POL)
        normalise_po(good)
    import re as _re

    assert (
        set(c for c in allowed if _re.fullmatch(POL.po_pattern, "a" + c + "b")) == allowed
    )  # the policy pattern allows the same characters


# --- Policy immutability ---------------------------------------------------------------------------------------------------------


def test_policy_cannot_be_changed_by_assignment_by_dict_write_or_by_editing_its_tables():
    with pytest.raises(dataclasses.FrozenInstanceError):
        POL.confidence_floor = 0.0  # type: ignore[misc]
    with pytest.raises(AttributeError):
        POL.__dict__["confidence_floor"] = (
            0.0  # old code: a frozen dataclass still had a writable __dict__ and this succeeded  # noqa: B003
        )
    for table in (POL.four_eyes_minor, POL.unit_synonyms, POL.currency_symbols):
        k = next(iter(table))
        before = table[k]
        with pytest.raises(TypeError):
            table[k] = 1  # type: ignore[index]
        with pytest.raises(TypeError):
            del table[k]  # type: ignore[attr-defined]
        assert table[k] == before
    assert rules.tier_for(set(), rules.Money("1", "USD"), POL) == "human"  # still works on a read-only mapping


def test_policy_documents_its_honest_limit():
    assert "object.__setattr__" in rules.Policy.__doc__ and "NOT guaranteed" in rules.Policy.__doc__
    p = rules.load_policy()
    object.__setattr__(p, "confidence_floor", 0.0)  # the limit is real: in-process code can still do this; the docstring says so
    assert p.confidence_floor == 0.0
    assert rules.load_policy().confidence_floor == RAW["confidence_floor"]  # a fresh load is unaffected


# --- egress: look-alike fold and exact matching -------------------------------------------------------------------------------------


def test_egress_folds_look_alike_letters_so_a_cyrillic_host_is_still_an_unlisted_host():
    base = {"recipient": "orders@harborlane.example.com", "verified_sender": "orders@harborlane.example.com"}
    cyr = "".join(map(chr, (0x441, 0x43E, 0x440, 0x440, 0x435, 0x441, 0x440, 0x43E, 0x43D, 0x434)))  # 'correspond'-like, all look-alikes
    host = "".join(map(chr, (0x430, 0x440, 0x440, 0x435, 0x430, 0x435)))  # Cyrillic a p p e a e: folds to Latin letters
    body = f"please pay at {host}.{cyr[:3]}"
    assert any("unlisted link or host" in p for p in check_egress(**base, body=body)), check_egress(**base, body=body)


def test_egress_does_not_let_a_link_through_because_it_contains_the_verified_address():
    sender = "orders@harborlane.example.com"
    base = {"recipient": sender, "verified_sender": sender}
    for body in (
        f"see http://evil.example.net/?r={sender}",
        f"see evil.example.net/{sender}",
        "see https://harborlane.example.com.evil.example.net/x",
    ):
        assert any("unlisted link or host" in p for p in check_egress(**base, body=body)), (
            body
        )  # old code: substring match let the first two pass
    assert check_egress(**base, body=f"Your address {sender} is on file.") == []


# --- tools/mutate_src.py judge --------------------------------------------------------------------------------------------------------


def _load_mutate():
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import mutate_src  # noqa: PLC0415

        return mutate_src
    finally:
        sys.path.pop(0)


JUNIT_FAIL = '<testsuite><testcase classname="t" name="a"><failure message="{msg}">x</failure></testcase></testsuite>'
JUNIT_ERR = '<testsuite><testcase classname="t" name="a"><error message="{msg}">x</error></testcase></testsuite>'


@pytest.mark.parametrize(
    "rc,xml,expected",
    [
        (0, "<testsuite/>", "SURVIVED"),
        (1, JUNIT_FAIL.format(msg="assert 1 == 2"), "KILLED"),
        (1, JUNIT_FAIL.format(msg="AssertionError: nope"), "KILLED"),
        (1, JUNIT_FAIL.format(msg="Failed: DID NOT RAISE &lt;class ValueError&gt;"), "KILLED"),
        (1, JUNIT_FAIL.format(msg="AttributeError: 'NoneType' object has no attribute x"), "CRASH"),
        (1, JUNIT_ERR.format(msg="collection failure"), "CRASH"),
        (2, "", "CRASH"),  # interrupted / collection error / import error
        (3, "", "CRASH"),
        (4, "", "CRASH"),
        (5, "", "CRASH"),  # no tests collected
        (1, "", "CRASH"),  # failed run with no readable report: not a proven kill
        (1, "<not xml", "CRASH"),
    ],
)
def test_mutation_judge_separates_assertion_kills_from_crashes(rc, xml, expected):
    assert _load_mutate().judge(rc, xml) == expected  # old code: every non-zero exit code was a KILL


def test_mutation_source_file_has_lf_line_endings_so_patterns_with_newlines_match_on_any_checkout():
    for p in (ROOT / "src" / "intake").rglob("*.py"):
        assert b"\r\n" not in p.read_bytes(), p


# --- line endings and core copies ---------------------------------------------------------------------------------------------------


def test_gitattributes_force_lf_for_source():
    first = (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()[0]
    assert first == "* text=auto eol=lf"


def test_core_copies_json_pins_every_copied_file_and_lists_every_local_generic():
    t = json.loads((ROOT / "core_copies.json").read_text(encoding="utf-8"))
    for rel, meta in t["files"].items():
        data = (ROOT / rel).read_bytes()
        assert b"\r\n" not in data
        text = data.decode("utf-8")
        for pair in meta.get("import_rewrite", []):
            text = text.replace(pair[1], pair[0])  # reverse the import rewrite to get the core bytes back
        assert hashlib.sha256(text.encode("utf-8")).hexdigest() == meta["core_sha256"], rel
    for rel, meta in t["allowed_local"].items():
        assert meta["reason"].strip() and meta["expires"], rel
        assert (ROOT / rel).exists(), rel
    md = (ROOT / "CORE_COPIES.md").read_text(encoding="utf-8")
    for rel in list(t["files"]) + list(t["allowed_local"]):
        assert rel in md, rel
    assert "awaiting core PR #50" in md or "core PR #50" in md


def test_safe_text_is_the_byte_copy_of_the_core_module_not_a_hand_edit():
    t = json.loads((ROOT / "core_copies.json").read_text(encoding="utf-8"))
    meta = t["files"]["src/intake/safe_text.py"]
    assert hashlib.sha256((ROOT / "src/intake/safe_text.py").read_bytes()).hexdigest() == meta["core_sha256"]


def test_the_confusable_fold_is_reached_only_through_the_local_seam():
    import ast  # noqa: PLC0415

    offenders = []
    for p in (ROOT / "src" / "intake").rglob("*.py"):
        if "core_copy" in p.parts or p.name == "textfold.py":
            continue
        for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            mods = (
                [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else [a.name for a in node.names]
                if isinstance(node, ast.Import)
                else []
            )
            offenders += [(p.name, m) for m in mods if "core_copy" in m or m.startswith("hadavin_sdk")]
    assert not offenders, offenders
    from intake.textfold import fold_text  # noqa: PLC0415

    assert fold_text("аpple") == "apple"  # the API shape of core PR #50 fold
