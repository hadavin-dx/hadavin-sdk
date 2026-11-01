"""Round 6: the security re-review (core hash recorded in the chain, report deletion, cross-process run lock,
reset and rollback edge cases, run ids) and the roles.sql variables."""

from __future__ import annotations

import json
import subprocess
import sys
import time

import pytest
from askdata import cli, evalcli, evalrun, sealed
from askdata.cli import _roles_input
from askdata.evalcli import cmd_run
from askdata.evalset import Lock, LockError, lock_path, read_lock, write_lock
from askdata.sealed import Chain, SealedGate, core_hash_of, files_sha_of
from askdata.settings import RUNTIME

from .conftest import DEMO
from .test_demo_gaps_r3 import KEY, gate_for, renew
from .test_demo_gaps_r4 import _run
from .test_demo_gaps_r5 import DEFECT
from .test_eval_harness import cli_env  # noqa: F401 - a fixture reused here


def _begin_only(g: SealedGate, rid: str) -> None:
    g.begin(g.load(), rid)


# ====================================================== M1: the core hash is in the CHAIN, not only in lock.json
def test_every_chain_entry_carries_the_core_and_files_hashes(tmp_path):
    g = gate_for(tmp_path, KEY)
    _run(g, "r1")
    g.record_smoke("k:v")
    for e in g.chain.entries():
        assert len(e["data"]["core_hash"]) == 64 and len(e["data"]["files_sha"]) == 64, e["kind"]
    head = read_lock(g.eval_dir)
    last = next(e for e in g.chain.entries() if e["sha"] == head.chain_head)
    assert last["data"]["core_hash"] == core_hash_of(head) and last["data"][
        "files_sha"
    ] == files_sha_of(head)


def test_reseal_refuses_a_lock_rewritten_together_with_its_own_core_hash(tmp_path):
    """The real attack: swap the frozen set, rewrite lock.files AND recompute core_hash, then ask for a reseal."""
    import hashlib

    g = gate_for(tmp_path, KEY)
    _run(g, "r1")
    (g.eval_dir / "a.jsonl").write_text("swapped gold", encoding="utf-8")
    digest = hashlib.sha256(b"swapped gold").hexdigest()
    raw = json.loads(lock_path(g.eval_dir).read_text(encoding="utf-8"))
    raw["files"]["a.jsonl"] = digest
    raw.update(DEFECT)
    forged = Lock.model_validate(raw)
    raw["core_hash"] = core_hash_of(
        forged
    )  # the attacker keeps the stored core_hash consistent with the new files
    lock_path(g.eval_dir).write_text(json.dumps(raw, indent=2, sort_keys=True), encoding="utf-8")
    assert (
        core_hash_of(read_lock(g.eval_dir)) == read_lock(g.eval_dir).core_hash
    )  # self-consistent on its own
    with pytest.raises(LockError, match="reseal refused"):
        g.reseal()  # but the CHAIN recorded another value


def test_even_a_keyless_load_notices_a_lock_edited_together_with_its_core_hash(tmp_path):
    g = gate_for(tmp_path, None)
    _run(g, "r1")
    raw = json.loads(lock_path(g.eval_dir).read_text(encoding="utf-8"))
    raw["max_second_looks"] = 99
    raw["core_hash"] = core_hash_of(Lock.model_validate(raw))
    lock_path(g.eval_dir).write_text(json.dumps(raw, indent=2, sort_keys=True), encoding="utf-8")
    with pytest.raises(LockError, match="differs from what the sealed-run chain recorded"):
        g.load()


# ====================================================== M2: a recorded report cannot be deleted or replaced
def test_a_deleted_recorded_report_is_refused_not_judged_aborted(tmp_path):
    g = gate_for(tmp_path, KEY)
    _begin_only(g, "r1")
    rep = g.runs_dir / "r1" / "report.json"
    rep.parent.mkdir(parents=True, exist_ok=True)
    rep.write_text(json.dumps({"aborted": False}), encoding="utf-8")
    g.record_report("r1")  # ...and the process is killed here, before `finish`
    rep.unlink()
    with pytest.raises(LockError, match="was deleted after its hash was recorded"):
        g.load()


def test_a_replaced_report_is_refused_even_after_the_run_finished(tmp_path):
    g = gate_for(tmp_path, KEY)
    _begin_only(g, "r1")
    rep = g.runs_dir / "r1" / "report.json"
    rep.parent.mkdir(parents=True, exist_ok=True)
    rep.write_text(json.dumps({"aborted": False}), encoding="utf-8")
    g.record_report("r1")
    g.finish("r1", "complete")
    assert g.load().last_test_status == "complete"
    rep.write_text(
        json.dumps({"aborted": True}), encoding="utf-8"
    )  # a sealed_done exists: it used to be unchecked
    with pytest.raises(LockError, match="differs from the hash recorded"):
        g.load()


@pytest.mark.parametrize("name", ["results.jsonl", "report.md", "report.json"])
def test_any_results_evidence_without_a_chain_record_is_unverified_not_aborted(tmp_path, name):
    g = gate_for(tmp_path, KEY)
    _begin_only(g, "r1")
    (g.runs_dir / "r1").mkdir(parents=True, exist_ok=True)
    (g.runs_dir / "r1" / name).write_text("{}", encoding="utf-8")
    assert g.load().last_test_status == "unverified"
    with pytest.raises(LockError, match="did not abort"):
        evalrun.sealed_gate(g.load(), 5, split="test", second_look="aborted")


def test_a_run_killed_after_begin_and_before_the_run_lock_with_no_results_is_aborted(tmp_path):
    g = gate_for(tmp_path, KEY)
    _begin_only(g, "r1")  # no acquire_run, no files: nothing was seen
    assert g.load().last_test_status == "aborted"
    evalrun.sealed_gate(g.load(), 5, split="test", second_look="aborted")


HOLDER = """
import json, sys
sys.path[:] = json.loads(sys.argv[1])
from pathlib import Path
from askdata.sealed import SealedGate
g = SealedGate(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]), None, [])
h = g.acquire_run()
print("READY", flush=True)
sys.stdin.readline()
"""


def test_the_run_lock_works_across_processes_and_dies_with_the_process(tmp_path):
    g = gate_for(tmp_path, KEY)
    _begin_only(g, "r1")
    cmd = [
        sys.executable,
        "-c",
        HOLDER,
        json.dumps(sys.path),
        str(g.eval_dir),
        str(g.chain.path),
        str(g.runs_dir),
    ]
    child = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)  # noqa: S603
    try:
        assert child.stdout.readline().strip() == "READY"
        assert g.running() and g.load().last_test_status == "running"  # another PROCESS holds it
        with pytest.raises(LockError, match="still running"):
            evalrun.sealed_gate(g.load(), 5, split="test", second_look="aborted")
        child.kill()  # the holder dies without releasing anything
        child.wait(timeout=30)
        deadline = time.monotonic() + 10
        while g.running() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert not g.running() and g.load().last_test_status == "aborted"
    finally:
        child.kill()
        child.wait(timeout=30)


def test_report_and_compare_check_the_report_against_the_chain(cli_env, capsys):  # noqa: F811
    cfg, factory = cli_env
    cmd_run(cfg, "test", 1, None, harness_factory=factory)
    run_dir = next(p for p in cfg.paths.runs_dir.iterdir() if p.name.endswith("-sealed"))
    path = str(cfg.paths.eval_dir.parent / "askdata.yaml")
    assert cli.main(["eval", "--config", path, "report", str(run_dir)]) == 0
    assert cli.main(["eval", "--config", path, "compare", str(run_dir), str(run_dir)]) in (0, 11, 4)
    rep = run_dir / "report.json"
    data = json.loads(rep.read_text(encoding="utf-8"))
    data["verdict"] = "green"
    rep.write_text(json.dumps(data), encoding="utf-8")
    capsys.readouterr()
    assert cli.main(["eval", "--config", path, "report", str(run_dir)]) == 4
    assert "differs from the hash recorded" in capsys.readouterr().out
    assert cli.main(["eval", "--config", path, "compare", str(run_dir), str(run_dir)]) == 4
    rep.unlink()
    assert cli.main(["eval", "--config", path, "report", str(run_dir)]) == 4
    assert (
        evalcli.verify_run_report([], run_dir) == "unrecorded"
    )  # an empty chain vouches for nothing


# ====================================================== m2 / m3: reset and rollback edge cases
def test_new_set_with_an_anchor_but_no_chain_needs_an_explicit_discard_count(tmp_path):
    g = gate_for(tmp_path, KEY)
    renew(g)
    _run(g, "r1")
    g.chain.path.unlink()
    lock_path(g.eval_dir).unlink()
    reason = "the chain file was lost in a restore"
    with pytest.raises(LockError, match="NO chain"):
        g.create(["a.jsonl"], new_set_reason=reason)
    g.create(["a.jsonl"], new_set_reason=reason, discard_count=1)
    assert g.chain.entries()[-1]["data"]["discarded_runs"] == 1  # logged as claimed
    assert g.load().test_runs == 0


def test_a_failed_anchor_write_removes_the_new_lock_even_when_there_was_no_old_one(
    tmp_path, monkeypatch
):
    g = gate_for(tmp_path, KEY)
    renew(g)
    g.chain.path.unlink()
    lock_path(g.eval_dir).unlink()  # anchors remain: only --new-set can freeze again
    monkeypatch.setattr(
        sealed, "_write_json", lambda *a, **k: (_ for _ in ()).throw(OSError("disk full"))
    )
    with pytest.raises(OSError):
        g.create(["a.jsonl"], new_set_reason="a replacement for a lost chain", discard_count=0)
    assert not lock_path(g.eval_dir).exists() and not g.chain.path.exists()


def test_no_backup_files_leak_when_the_chain_append_itself_fails(tmp_path, monkeypatch):
    g = gate_for(tmp_path, KEY)
    renew(g)
    _run(g, "r1")
    monkeypatch.setattr(
        Chain, "append", lambda *a, **k: (_ for _ in ()).throw(OSError("fsync failed"))
    )
    with pytest.raises(OSError):
        g.create(["a.jsonl"], new_set_reason="the client replaced the questions", discard_count=1)
    leftovers = [p.name for d in (g.eval_dir, g.chain.path.parent) for p in d.glob("*.bak")]
    assert leftovers == []
    monkeypatch.undo()
    assert g.load().test_runs == 1


# ====================================================== nits
def test_run_ids_are_ascii_only_and_a_defect_must_name_a_chained_sealed_run(cli_env, capsys):  # noqa: F811
    arabic = "٢٠٢٦١١٠١T٠٩٢٨٤٧٦٧٩١٩٤Z-sealed"
    assert not evalcli.RUN_ID.fullmatch(arabic)
    cfg, factory = cli_env
    cmd_run(cfg, "dev", 1, None, harness_factory=factory)
    dev_run = next(p.name for p in cfg.paths.runs_dir.iterdir() if p.name.endswith("-dev"))
    cmd_run(cfg, "test", 1, None, harness_factory=factory)
    item = json.loads((cfg.paths.eval_dir / "gold.test.jsonl").read_text().splitlines()[0])["id"]
    fake_sealed = "20261101T000000000000Z-sealed"
    (cfg.paths.runs_dir / fake_sealed).mkdir()
    (cfg.paths.runs_dir / fake_sealed / "report.json").write_text("{}", encoding="utf-8")
    for bad in (dev_run, fake_sealed):  # a dev run, and a folder the chain never recorded
        write_lock(
            cfg.paths.eval_dir,
            read_lock(cfg.paths.eval_dir).model_copy(
                update={
                    "harness_defect_reason": "gold query is wrong",
                    "harness_defect_run": bad,
                    "harness_defect_item": item,
                }
            ),
        )
        capsys.readouterr()
        assert cmd_run(cfg, "test", 1, "harness_defect", harness_factory=factory) == 14
        out_text = capsys.readouterr().out
        # a dev run is refused as a defect run; a results folder the chain never recorded is refused at load
        assert (
            "sealed run of the current set" in out_text
            or "hold results that the chain has no sealed run" in out_text
        )


# ====================================================== roles.sql has no numbers of its own
def test_roles_sql_takes_its_numbers_from_variables_set_from_runtime():
    text = (DEMO / "db" / "roles.sql").read_text(encoding="utf-8")
    import re

    code = "\n".join(ln for ln in text.splitlines() if not ln.lstrip().startswith("--"))
    assert not re.search(r"CONNECTION LIMIT\s+\d|'\d+s'", code)
    for var in (
        "ro_connection_limit",
        "ro_statement_timeout",
        "ro_lock_timeout",
        "ro_idle_timeout",
    ):
        assert f":{var}" in text or f":'{var}'" in text
    sent = _roles_input("pw")
    assert f"set ro_connection_limit '{RUNTIME.role_connection_limit}'" in sent
    assert f"set ro_statement_timeout '{RUNTIME.role_statement_timeout_s}s'" in sent
    assert sent.index("set ro_connection_limit") < sent.index("i roles.sql")


@pytest.mark.parametrize(
    "mutate",
    [
        lambda raw: raw.update(max_second_looks=99),
        lambda raw: raw["thresholds"].update(green_max_upper="0.99"),
        lambda raw: raw.update(sealed_min_remaining_usd="0"),
    ],
)
def test_reseal_compares_the_core_with_the_chain_even_when_the_files_are_untouched(
    tmp_path, mutate
):
    g = gate_for(tmp_path, KEY)
    _run(g, "r1")
    raw = json.loads(lock_path(g.eval_dir).read_text(encoding="utf-8"))
    mutate(raw)
    raw.update(DEFECT)
    raw["core_hash"] = core_hash_of(
        Lock.model_validate(raw)
    )  # kept self-consistent by the attacker
    lock_path(g.eval_dir).write_text(json.dumps(raw, indent=2, sort_keys=True), encoding="utf-8")
    with pytest.raises(LockError, match="reseal refused"):
        g.reseal()
