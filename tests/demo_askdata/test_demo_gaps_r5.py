"""Round 5: the reviewer's probes n_* as regression tests (run lock, narrow reseal, report hash, anchors, reset
guard, rollback, key id), the literal and numeric scans over the whole demo tree, and the small nits."""

from __future__ import annotations

import json

import pytest
from askdata import evalcli, evalrun, sealed
from askdata.evalset import Lock, LockError, lock_path, read_lock, write_lock
from askdata.sealed import HAND_FIELDS, SealedGate, report_state
from askdata.settings import RUNTIME

from .conftest import DEMO
from .test_demo_gaps_r3 import KEY, gate_for, renew
from .test_demo_gaps_r4 import _edit_lock, _run
from .test_eval_harness import cli_env  # noqa: F401 - a fixture reused here

DEFECT = {
    "harness_defect_reason": "gold g7 fails on database A",
    "harness_defect_run": "20261101T000000000000Z-sealed",
    "harness_defect_item": "g7",
}


def _begin_only(g: SealedGate, rid: str) -> None:
    g.begin(g.load(), rid)


# ====================================================== (1) a run in progress is not "aborted"
def test_a_run_still_running_is_not_aborted_and_blocks_a_second_look(tmp_path):
    g = gate_for(tmp_path, KEY)
    _begin_only(g, "r1")
    handle = g.acquire_run()  # the process of run 1 is alive and holds the run lock
    try:
        lock = g.load()
        assert lock.last_test_status == "running"
        with pytest.raises(LockError, match="still running"):
            evalrun.sealed_gate(lock, 5, split="test", second_look="aborted")
        with pytest.raises(LockError, match="still running"):
            evalrun.sealed_gate(lock, 5, split="test", second_look="harness_defect")
        with pytest.raises(LockError, match="still running"):
            g.acquire_run()  # and a second run cannot take the lock either
    finally:
        g.release_run(handle)
    assert g.load().last_test_status == "aborted"  # the process is gone: now it is aborted
    evalrun.sealed_gate(g.load(), 5, split="test", second_look="aborted")


# ====================================================== (2) reseal blesses ONLY the hand-written fields
@pytest.mark.parametrize(
    "mutate",
    [
        lambda l: l["thresholds"].update(green_max_upper="0.99"),
        lambda l: l.update(max_second_looks=99),
        lambda l: l.update(sealed_min_remaining_usd="0"),
        lambda l: l.update(second_look_min_remaining_usd="0"),
        lambda l: l["files"].update({"a.jsonl": "0" * 64}),
    ],
)
def test_reseal_refuses_any_change_outside_the_hand_written_fields(tmp_path, mutate):
    g = gate_for(tmp_path, KEY)
    _run(g, "r1")
    _edit_lock(g, lambda l: l.update(DEFECT))
    _edit_lock(g, mutate)
    with pytest.raises(LockError, match="something other than the hand-written"):
        g.reseal()


def test_reseal_refuses_to_swap_the_frozen_set_with_rehashed_files(tmp_path):
    import hashlib

    g = gate_for(tmp_path, KEY)
    (g.eval_dir / "a.jsonl").write_text("swapped", encoding="utf-8")
    digest = hashlib.sha256(b"swapped").hexdigest()
    _edit_lock(g, lambda l: (l.update(DEFECT), l["files"].update({"a.jsonl": digest})))
    with pytest.raises(LockError, match="something other than the hand-written"):
        g.reseal()


def test_reseal_needs_a_hand_field_and_accepts_exactly_that(tmp_path):
    g = gate_for(tmp_path, KEY)
    with pytest.raises(LockError, match="nothing to bless"):
        g.reseal()
    _edit_lock(g, lambda l: l.update(DEFECT))
    assert g.reseal() == list(HAND_FIELDS)
    assert g.load().harness_defect_item == "g7"


# ====================================================== (3) a crashed run is judged by a report whose hash was recorded
def test_a_report_the_chain_does_not_vouch_for_is_unverified_and_a_changed_one_is_refused(tmp_path):
    g = gate_for(tmp_path, KEY)
    _begin_only(g, "r1")
    rep = g.runs_dir / "r1" / "report.json"
    rep.parent.mkdir(parents=True, exist_ok=True)
    rep.write_text(
        json.dumps({"aborted": True}), encoding="utf-8"
    )  # a planted report, nobody recorded its hash
    assert g.load().last_test_status == "unverified"
    with pytest.raises(LockError, match="did not abort|aborted"):
        evalrun.sealed_gate(g.load(), 5, split="test", second_look="aborted")
    rep.write_text(json.dumps({"aborted": False}), encoding="utf-8")
    g.record_report("r1")
    assert g.load().last_test_status == "complete"
    rep.write_text(
        json.dumps({"aborted": True}), encoding="utf-8"
    )  # edited after the hash was recorded
    with pytest.raises(LockError, match="differs from the hash recorded"):
        g.load()
    assert report_state(g.chain.entries(), g.runs_dir, "nope") is None


# ====================================================== (4) deleting one anchor is noticed
@pytest.mark.parametrize("which", [0, 1])
def test_deleting_any_configured_anchor_is_refused(tmp_path, which):
    g = gate_for(tmp_path, KEY)
    g.anchors[which].unlink()
    with pytest.raises(LockError, match="anchor .* is missing"):
        g.load()


# ====================================================== (5) the counter reset is deliberate and logged
def test_a_new_set_needs_a_real_reason_and_the_count_to_discard(tmp_path):
    g = gate_for(tmp_path, KEY)
    renew(g)
    _run(g, "r1")
    _run(g, "r2")
    with pytest.raises(LockError, match="at least 20 characters"):
        g.create(["a.jsonl"], new_set_reason="x")
    reason = "the client replaced the test questions"
    with pytest.raises(LockError, match="RESETS the sealed counter and 2 sealed run"):
        g.create(["a.jsonl"], new_set_reason=reason)
    with pytest.raises(LockError, match="--discard-count 2"):
        g.create(["a.jsonl"], new_set_reason=reason, discard_count=1)
    assert g.load().test_runs == 2  # nothing happened
    g.create(["a.jsonl"], new_set_reason=reason, discard_count=2)
    last = g.chain.entries()[-1]
    assert (
        last["kind"] == "new_set"
        and last["data"]["discarded_runs"] == 2
        and last["data"]["reason"] == reason
    )
    assert g.load().test_runs == 0


# ====================================================== (6) a failed freeze leaves nothing behind
def test_a_failed_first_freeze_rolls_everything_back_including_the_anchors(tmp_path, monkeypatch):
    ev = tmp_path / "ev"
    ev.mkdir()
    (ev / "a.jsonl").write_text("x", encoding="utf-8")
    anchors = [tmp_path / "audit" / "sealed-anchor.json", ev / "anchor.json"]
    g = SealedGate(ev, tmp_path / "audit" / "chain.jsonl", tmp_path / "runs", KEY, anchors)
    real, calls = sealed._write_json, {"n": 0}

    def second_fails(path, obj):
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("disk full")
        real(path, obj)

    with monkeypatch.context() as m:
        m.setattr(sealed, "_write_json", second_fails)
        with pytest.raises(OSError):
            g.create(["a.jsonl"])
    assert calls["n"] == 2  # the first anchor WAS written before the second failed
    assert (
        not lock_path(ev).exists()
        and not g.chain.path.exists()
        and not any(a.exists() for a in anchors)
    )
    assert g.create(["a.jsonl"]).test_runs == 0  # and a plain freeze works afterwards, not "stuck"


def test_a_failed_new_set_restores_the_old_lock_and_the_chain(tmp_path, monkeypatch):
    g = gate_for(tmp_path, KEY)
    renew(g)
    _run(g, "r1")
    before_chain, before_lock = g.chain.path.read_bytes(), lock_path(g.eval_dir).read_bytes()
    reason = "the client replaced the test questions"
    with monkeypatch.context() as m:
        m.setattr(
            sealed.Chain, "append", lambda *a, **k: (_ for _ in ()).throw(OSError("fsync failed"))
        )
        with pytest.raises(OSError):
            g.create(["a.jsonl"], new_set_reason=reason, discard_count=1)
    assert (
        lock_path(g.eval_dir).read_bytes() == before_lock
        and g.chain.path.read_bytes() == before_chain
    )
    assert not list(g.eval_dir.glob("lock.json.prev-*"))
    # and when the failure comes AFTER the old lock was moved aside (the anchor write), it is moved back
    with monkeypatch.context() as m:
        m.setattr(
            sealed, "_write_json", lambda *a, **k: (_ for _ in ()).throw(OSError("disk full"))
        )
        with pytest.raises(OSError):
            g.create(["a.jsonl"], new_set_reason=reason, discard_count=1)
    assert (
        lock_path(g.eval_dir).read_bytes() == before_lock
        and g.chain.path.read_bytes() == before_chain
    )
    assert g.load().test_runs == 1


# ====================================================== (7) key id; the full downgrade is a documented limit
def test_an_anchor_that_names_another_key_id_is_refused(tmp_path):
    g = gate_for(tmp_path, KEY)
    assert json.loads(g.anchors[0].read_text(encoding="utf-8"))["key_id"] == g._key_id()
    assert g.chain.entries()[0]["data"]["key_id"] == g._key_id()
    for a in g.anchors:
        body = json.loads(a.read_text(encoding="utf-8"))
        body["key_id"] = "0" * 16
        a.write_text(json.dumps(body), encoding="utf-8")
    with pytest.raises(LockError, match="key id mismatch"):
        g.load()


def test_a_full_rewrite_of_every_file_as_a_keyless_set_succeeds_and_the_readme_says_so(tmp_path):
    """Pinned limit: every guard is a plain file, so a writer of ALL of them can re-create the set unkeyed."""
    g = gate_for(tmp_path, KEY)
    _run(g, "r1")
    for p in (g.chain.path, lock_path(g.eval_dir), *g.anchors):
        p.unlink()
    keyless = SealedGate(g.eval_dir, g.chain.path, g.runs_dir, None, g.anchors)
    keyless.create(["a.jsonl"])
    assert keyless.load().test_runs == 0
    readme = (DEMO / "README.md").read_text(encoding="utf-8")
    assert "only as strong as where it is anchored" in readme and "signed checkpoints" in readme


# ====================================================== (11) run ids
@pytest.mark.parametrize("bad", ["", ".", "..", "r1", "../x", "20261101T000000000000Z-other"])
def test_a_harness_defect_run_must_look_like_a_run_id(bad):
    assert not evalcli.RUN_ID.fullmatch(bad)
    assert evalcli.RUN_ID.fullmatch("20261101T092847679194Z-second-look")


def test_the_runtime_block_is_the_one_home_of_the_moved_defaults():
    assert (
        RUNTIME.statement_timeout_s,
        RUNTIME.max_rows,
        RUNTIME.max_bytes,
        RUNTIME.fetch_batch,
    ) == (10.0, 1000, 1_000_000, 200)
    from askdata.pgsource import Limits
    from askdata.pipeline import Settings

    assert Limits() == Limits(
        statement_timeout_s=RUNTIME.statement_timeout_s, max_rows=RUNTIME.max_rows,
        max_bytes=RUNTIME.max_bytes, batch=RUNTIME.fetch_batch,
    )  # fmt: skip
    assert Settings().injection_threshold == RUNTIME.injection_threshold
    assert Settings().transient_backoff_s == RUNTIME.transient_backoff_s
    assert evalrun.Config().max_duration_ms == RUNTIME.max_duration_ms


def test_lock_dataclass_import_kept():
    assert Lock and read_lock and write_lock


def test_during_a_real_sealed_run_the_status_is_running_and_afterwards_it_is_not(cli_env):  # noqa: F811
    from askdata.evalcli import cmd_run

    cfg, factory = cli_env
    seen = []

    def spy(*a, **k):
        harness, meter, meta = factory(*a, **k)
        real = harness.run_gold

        def run_gold(items):
            seen.append(evalcli._gate(cfg).load().last_test_status)
            return real(items)

        harness.run_gold = run_gold
        return harness, meter, meta

    cmd_run(cfg, "test", 1, None, harness_factory=spy)
    assert seen == ["running"]
    assert evalcli._gate(cfg).load().last_test_status == "complete"


def test_the_report_hash_is_recorded_by_a_real_sealed_run(cli_env):  # noqa: F811
    from askdata.evalcli import cmd_run

    cfg, factory = cli_env
    cmd_run(cfg, "test", 1, None, harness_factory=factory)
    kinds = [e["kind"] for e in evalcli._gate(cfg).chain.entries()]
    assert kinds == ["genesis", "sealed_run", "report", "sealed_done"]
