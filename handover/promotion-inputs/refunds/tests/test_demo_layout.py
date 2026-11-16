"""Tests that need the demo folder (the ingest spec model reads its seeded plan; the data bytes policy lives next to the generated data). With the demo folder deleted
(the cut test) this module is left out of collection by conftest; everything else must stay green."""

from pathlib import Path

import ingest_model as im
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _msg(mid, body):
    base = {
        k: False
        for k in ("crash_on_receive", "crash_before_effect", "crash_after_effect", "timeout", "throttle_429", "poison", "invalid")
    }
    return {**base, "msg_id": mid, "duplicates": 0, "outcome_hint": "processed", "body_sha256": body}


def test_an_id_reused_with_a_different_body_is_its_own_rejected_row():
    p = im.Pipeline()
    assert p.receive(_msg("m1", "a" * 64), 0) and p.receive(_msg("m1", "b" * 64), 0)
    assert p.ledger["m1"] == "received", "the first message keeps its own state"
    reuse = [k for k in p.ledger if k.startswith("m1#id_reuse-")]
    assert len(reuse) == 1 and p.ledger[reuse[0]] == "rejected"


def test_a_redelivery_with_the_same_body_changes_nothing():
    p = im.Pipeline()
    for _ in range(3):
        assert p.receive(_msg("m1", "a" * 64), 0)
    assert list(p.ledger) == ["m1"]


def test_reused_id_with_a_different_body_is_rejected_and_the_effect_is_applied_once():
    """Drive the whole path: all deliveries are received, the caller enqueues the id each time, the worker drains. The effect (the fake payment) is
    applied exactly once, for the first body; the conflicting delivery has its own rejected row and never reaches the effect."""
    first, second = _msg("m1", "a" * 64), _msg("m1", "b" * 64)
    p = im.Pipeline()
    msgs = {"m1": first}
    for m in (first, second, first):  # first body, a conflicting body, a redelivery of the first
        assert p.receive(m, 0)
        assert p.enqueue("m1")
    p.drain(msgs)
    assert p.effects == {"effect-m1": 1}, p.effects
    assert p.ledger["m1"] == "processed"
    rejected = {k: v for k, v in p.ledger.items() if "#id_reuse-" in k}
    assert list(rejected.values()) == ["rejected"] and len(rejected) == 1
    assert len(p.ledger) == 2, p.ledger


def test_without_the_reuse_check_the_second_body_is_silently_merged():
    p = im.Pipeline(id_reuse_check=False)
    p.receive(_msg("m1", "a" * 64), 0)
    p.receive(_msg("m1", "b" * 64), 0)
    assert list(p.ledger) == ["m1"], "the check is what separates them (the switch proves the test can fail)"


def test_the_repo_forces_lf_and_leaves_data_bytes_alone():
    lines = (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
    assert "* text=auto eol=lf" in lines
    data_attrs = (ROOT / "demo_only" / "data" / ".gitattributes").read_text(encoding="utf-8").splitlines()
    assert "* -text" in data_attrs, "the generated data keeps its exact bytes"


def _m(mid, body):
    base = {
        k: False
        for k in ("crash_on_receive", "crash_before_effect", "crash_after_effect", "timeout", "throttle_429", "poison", "invalid")
    }
    m = {**base, "msg_id": mid, "duplicates": 0, "outcome_hint": "processed"}
    if body is not None:
        m["body_sha256"] = body
    return m


@pytest.mark.parametrize("body", [None, "", "short", "G" * 64, "A" * 64, 5])
def test_a_delivery_without_a_valid_body_hash_is_rejected_not_skipped(body):
    p = im.Pipeline()
    m = _m("m1", None) if body is None else {**_m("m1", None), "body_sha256": body}
    assert p.receive(m, 0)
    assert p.ledger == {"m1#no_body": "rejected"}, p.ledger
    assert "m1" not in p.ledger, "a body-less first delivery must not claim the id either"


def test_the_first_body_is_the_one_the_worker_acts_on_even_if_the_conflicting_one_is_offered_by_id():
    first, second = _m("m1", "a" * 64), _m("m1", "b" * 64)
    p = im.Pipeline()
    for m in (first, second):
        assert p.receive(m, 0) and p.enqueue("m1")
    p.drain({"m1": second})  # a caller that looks the message up by id and finds the CONFLICTING one
    assert p.acted_body == {"m1": "a" * 64}, p.acted_body
    assert p.effects == {"effect-m1": 1}


def test_two_bodies_sharing_a_prefix_keep_separate_rejected_rows():
    p = im.Pipeline()
    p.receive(_m("m1", "a" * 64), 0)
    p.receive(_m("m1", "b" * 12 + "0" * 52), 0)
    p.receive(_m("m1", "b" * 12 + "1" * 52), 0)
    rows = [k for k in p.ledger if "#id_reuse-" in k]
    assert len(rows) == 2 and all(len(k.split("#id_reuse-")[1]) == 64 for k in rows)


def test_the_seeded_plan_now_carries_a_body_hash_on_every_delivery():
    r = im.run(100)
    assert (r["missing"], r["duplicated_effects"], r["non_terminal"], r["reconciliation_gap"]) == (0, 0, 0, 0), r
    r2 = im.run(100, id_reuse_check=False)
    assert r2["received"] == r["received"]


def test_reconciliation_stays_zero_when_conflicting_bodies_arrive_in_the_seeded_run():
    base = im.run(100)
    r = im.run(100, conflicts=10)
    assert r["conflict_rows"] == 10 and base["conflict_rows"] == 0
    assert (r["missing"], r["duplicated_effects"], r["non_terminal"], r["reconciliation_gap"]) == (0, 0, 0, 0), r
    for k in ("received", "processed", "abstained", "dead_lettered", "rejected"):
        assert r[k] == base[k], (k, r[k], base[k])  # the first bodies are what was processed: nothing changed for the source ids


def test_the_demo_source_loads_only_through_the_data_source_door(monkeypatch):
    from refunds import data_source

    monkeypatch.setenv("REFUNDS_DEMO_SOURCE", "refunds_demo_source")
    monkeypatch.setenv("REFUNDS_PATH", str(ROOT / "demo_only"))
    s = data_source.load("demo")
    assert isinstance(s.world(), dict) and len(s.cases()) == 75
