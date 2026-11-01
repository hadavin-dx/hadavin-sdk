"""Round 7: rollback that never deletes what it did not create, atomic chain rewrites, an audited way out when a
recorded run folder is gone, rolled-back lock detection, report vouching, and roles.sql validation."""

from __future__ import annotations

import json
import re
import shutil

import pytest
from askdata import cli, evalcli, sealed
from askdata.evalcli import cmd_run
from askdata.evalset import Lock, LockError, lock_path, read_lock, write_lock
from askdata.sealed import RECOVERY_MARKER, Chain, SealedGate, report_state

from .conftest import DEMO
from .test_demo_gaps_r3 import KEY, gate_for
from .test_eval_harness import cli_env  # noqa: F401 - a fixture reused here

RUN1 = "20261101T000000000001Z-sealed"
RUN2 = "20261101T000000000002Z-sealed"
REASON = "the client replaced the test questions"


def _recorded_run(g: SealedGate, rid: str, aborted: bool = False) -> None:
    """begin -> results on disk -> report hash recorded -> finished (what a real sealed run leaves)."""
    g.begin(g.load(), rid)
    folder = g.runs_dir / rid
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "report.json").write_text(json.dumps({"aborted": aborted}), encoding="utf-8")
    (folder / "results.jsonl").write_text('{"x": 1}\n', encoding="utf-8")
    g.record_report(rid)
    g.finish(rid, "aborted" if aborted else "complete")


# ====================================================== M1: a failed freeze deletes only what it created
@pytest.mark.parametrize("fail_at", [1, 2])
def test_a_failed_backup_copy_never_deletes_an_anchor_that_already_existed(
    tmp_path, monkeypatch, fail_at
):
    g = gate_for(tmp_path, KEY)
    before = {a: a.read_bytes() for a in g.anchors}
    chain_before = g.chain.path.read_bytes()
    real, calls = shutil.copyfile, {"n": 0}

    def flaky(src, dst, **kw):
        calls["n"] += 1
        if calls["n"] == fail_at:
            raise PermissionError("disk full or locked")
        return real(src, dst, **kw)

    monkeypatch.setattr(sealed.shutil, "copyfile", flaky)
    with pytest.raises(PermissionError):
        g.create(["a.jsonl"], new_set_reason=REASON, discard_count=0)
    monkeypatch.undo()
    assert {
        a: a.read_bytes() for a in g.anchors
    } == before  # BOTH originals are still there, unchanged
    assert g.chain.path.read_bytes() == chain_before and g.load().test_runs == 0
    assert not list(g.eval_dir.glob("*.bak")) and not list(g.chain.path.parent.glob("*.bak"))


def test_a_rollback_that_itself_fails_is_surfaced_and_leaves_a_recovery_marker(
    tmp_path, monkeypatch
):
    g = gate_for(tmp_path, KEY)
    _recorded_run(g, RUN1)
    real_replace = sealed.os.replace

    def replace(src, dst, *a, **kw):
        if "lock.json.prev-" in str(src):  # the move of the old lock back into place fails
            raise PermissionError("antivirus has the file")
        return real_replace(src, dst, *a, **kw)

    monkeypatch.setattr(sealed.os, "replace", replace)
    monkeypatch.setattr(
        sealed, "_write_json", lambda *a, **k: (_ for _ in ()).throw(OSError("disk full"))
    )
    with pytest.raises(LockError, match="rollback is incomplete") as err:
        g.create(["a.jsonl"], new_set_reason=REASON, discard_count=1)
    assert isinstance(err.value.__cause__, OSError)  # the ORIGINAL error is chained, not masked
    monkeypatch.undo()
    assert (g.eval_dir / RECOVERY_MARKER).exists()
    with pytest.raises(LockError, match=RECOVERY_MARKER):
        g.load()  # nothing runs on a half-restored state


# ====================================================== M2: chain rewrites are atomic
def test_a_crash_while_repairing_a_torn_chain_leaves_the_old_file_untouched(tmp_path, monkeypatch):
    g = gate_for(tmp_path, KEY)
    with open(g.chain.path, "a", encoding="utf-8") as f:
        f.write('{"seq":9,"kind":"sealed_ru')  # a torn tail
    before = g.chain.path.read_bytes()

    def crash(*a, **kw):
        raise OSError("power loss")

    monkeypatch.setattr(sealed.os, "replace", crash)
    with pytest.raises(OSError):
        g.chain.repair()
    monkeypatch.undo()
    assert (
        g.chain.path.read_bytes() == before
    )  # not empty, not half-written: the old bytes, torn tail and all
    assert not list(g.chain.path.parent.glob("*.tmp"))
    assert g.load().test_runs == 0  # and the next load repairs it properly


def test_a_crash_during_rollback_truncation_keeps_the_whole_chain(tmp_path, monkeypatch):
    g = gate_for(tmp_path, KEY)
    _recorded_run(g, RUN1)
    before = g.chain.path.read_bytes()
    monkeypatch.setattr(
        sealed.os, "replace", lambda *a, **k: (_ for _ in ()).throw(OSError("power loss"))
    )
    with pytest.raises(OSError):
        g.chain.truncate_to(1)
    monkeypatch.undo()
    assert g.chain.path.read_bytes() == before


# ====================================================== 7: a complete last line without its newline
def test_a_valid_last_line_without_a_newline_is_not_glued_to_the_next_entry(tmp_path):
    g = gate_for(tmp_path, KEY)
    g.chain.path.write_text(g.chain.path.read_text(encoding="utf-8").rstrip("\n"), encoding="utf-8")
    assert not g.chain.torn
    g.begin(g.load(), RUN1)  # used to append onto the same line and break the chain
    assert [e["kind"] for e in g.chain.entries()] == ["genesis", "sealed_run"]
    assert g.chain.path.read_text(encoding="utf-8").endswith("\n")


# ====================================================== M3: the audited way out when run folders are gone
def test_a_pruned_run_folder_has_an_audited_non_reset_way_out(tmp_path):
    g = gate_for(tmp_path, KEY)
    _recorded_run(g, RUN1)
    shutil.rmtree(
        g.runs_dir / RUN1
    )  # an operator tidies runs/, or restores the audit folder on a fresh machine
    with pytest.raises(LockError, match="report-lost"):
        g.load()
    with pytest.raises(LockError, match="at least 20"):
        g.mark_report_lost(RUN1, "tidied")
    g.mark_report_lost(RUN1, "runs/ was pruned to free disk space")
    lock = g.load()
    assert lock.test_runs == 1  # the counter is untouched: this is not a reset
    assert (
        lock.last_test_status == "complete"
    )  # sealed_done is on record; a later unfinished run would be unverified
    last = g.chain.entries()[-1]
    assert last["kind"] == "report_lost" and last["data"]["found"] == "deleted"
    with pytest.raises(LockError, match="already marked lost"):
        g.mark_report_lost(RUN1, "marking it a second time is pointless")


def test_a_lost_report_never_grants_an_aborted_second_look(tmp_path):
    g = gate_for(tmp_path, KEY)
    g.begin(g.load(), RUN1)
    (g.runs_dir / RUN1).mkdir(parents=True)
    (g.runs_dir / RUN1 / "report.json").write_text(json.dumps({"aborted": True}), encoding="utf-8")
    g.record_report(RUN1)  # killed before `finish`
    shutil.rmtree(g.runs_dir / RUN1)
    g.mark_report_lost(RUN1, "the run folder was moved to another disk")
    assert g.load().last_test_status == "unverified"
    assert report_state(g.chain.entries(), g.runs_dir, RUN1) == "lost"


def test_report_lost_through_the_cli_and_the_report_banner(cli_env, capsys):  # noqa: F811
    cfg, factory = cli_env
    cmd_run(cfg, "test", 1, None, harness_factory=factory)
    run_dir = next(p for p in cfg.paths.runs_dir.iterdir() if p.name.endswith("-sealed"))
    path = str(cfg.paths.eval_dir.parent / "askdata.yaml")
    shutil.rmtree(run_dir)
    assert (
        cmd_run(cfg, "test", 1, "aborted", harness_factory=factory) == 14
    )  # refused: evidence is gone
    capsys.readouterr()
    assert (
        cli.main(["eval", "--config", path, "report-lost", run_dir.name, "--reason", "short"]) == 14
    )
    assert (
        cli.main(["eval", "--config", path, "report-lost", "not-a-run", "--reason", "x" * 25]) == 1
    )
    assert (
        cli.main(
            [
                "eval",
                "--config",
                path,
                "report-lost",
                run_dir.name,
                "--reason",
                "pruned runs/ to free the disk",
            ]
        )
        == 0
    )
    assert read_lock(cfg.paths.eval_dir).test_runs == 1


# ====================================================== 5: a rolled-back lock+chain with the run folders still there
def test_a_lock_and_chain_rolled_back_to_an_older_state_are_noticed_by_the_run_folders(tmp_path):
    g = gate_for(tmp_path, KEY)
    _recorded_run(g, RUN1)
    old_lock, old_chain = lock_path(g.eval_dir).read_bytes(), g.chain.path.read_bytes()
    _recorded_run(g, RUN2)
    lock_path(g.eval_dir).write_bytes(
        old_lock
    )  # restore both files from an earlier backup: a perfectly valid pair
    g.chain.path.write_bytes(old_chain)
    with pytest.raises(LockError, match="look rolled back"):
        g.load()


def test_stray_empty_run_folders_and_dev_runs_do_not_trigger_the_rollback_check(tmp_path):
    g = gate_for(tmp_path, KEY)
    (g.runs_dir / RUN2).mkdir(parents=True)  # a failed start left an empty folder
    (g.runs_dir / "20261101T000000000003Z-dev").mkdir()
    (g.runs_dir / "20261101T000000000003Z-dev" / "report.json").write_text("{}", encoding="utf-8")
    assert g.load().test_runs == 0


# ====================================================== 6: eval report / compare do not give false comfort
def _sealed_report(folder, **fields):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "report.json").write_text(
        json.dumps({"split": "test", "label": "sealed", "verdict": "green", **fields}),
        encoding="utf-8",
    )


def test_a_forged_sealed_looking_report_is_not_vouched_whatever_the_folder_is_called(
    cli_env,  # noqa: F811
    capsys,
    tmp_path,
):
    cfg, _ = cli_env
    path = str(cfg.paths.eval_dir.parent / "askdata.yaml")
    forged = tmp_path / "pretty-name"
    _sealed_report(forged)
    assert cli.main(["eval", "--config", path, "report", str(forged)]) == 4
    assert "NOT VOUCHED" in capsys.readouterr().out
    assert cli.main(["eval", "--config", path, "compare", str(forged), str(forged)]) == 4
    capsys.readouterr()
    assert cli.main(["eval", "report", str(forged)]) in (
        0,
        4,
    )  # no config: nothing can be checked...
    assert "NOT checked against the chain" in capsys.readouterr().out  # ...and it says so loudly
    dev = tmp_path / "a-dev-run"
    dev.mkdir()
    (dev / "report.json").write_text(json.dumps({"split": "dev", "label": "dev"}), encoding="utf-8")
    assert evalcli._looks_sealed(forged) and not evalcli._looks_sealed(dev)


def test_a_config_that_was_asked_for_and_cannot_be_read_is_an_error_not_no_config(tmp_path, capsys):
    forged = tmp_path / "x"
    _sealed_report(forged)
    assert (
        cli.main(["eval", "--config", str(tmp_path / "missing.yaml"), "report", str(forged)]) == 4
    )
    assert "startup" in capsys.readouterr().out


def test_the_recorded_hash_covers_results_jsonl_and_report_md(tmp_path):
    g = gate_for(tmp_path, KEY)
    _recorded_run(g, RUN1)
    (g.runs_dir / RUN1 / "results.jsonl").write_text('{"x": 2}\n', encoding="utf-8")
    with pytest.raises(LockError, match="differs from the hash recorded"):
        g.load()


# ====================================================== 8: --new-set also accounts for lock.json's own counter
def test_new_set_with_a_lock_but_no_chain_must_discard_exactly_the_locks_count(tmp_path):
    g = gate_for(tmp_path, KEY)
    _recorded_run(g, RUN1)
    g.chain.path.unlink()
    with pytest.raises(LockError, match="--discard-count 1"):
        g.create(["a.jsonl"], new_set_reason=REASON, discard_count=0)
    g.create(["a.jsonl"], new_set_reason=REASON, discard_count=1)
    assert g.chain.entries()[-1]["data"]["lock_test_runs"] == 1


# ====================================================== 9: a defect must cite a recorded, verified, current-set run
def test_defect_run_ok_needs_a_recorded_verified_run_of_the_current_set(tmp_path):
    g = gate_for(tmp_path, KEY)
    _recorded_run(g, RUN1)
    assert g.defect_run_ok(RUN1)
    assert not g.defect_run_ok(RUN2)  # never recorded
    g.begin(g.load(), RUN2)
    (g.runs_dir / RUN2).mkdir(parents=True)
    (g.runs_dir / RUN2 / "report.json").write_text(
        "{}", encoding="utf-8"
    )  # results exist, no recorded hash
    assert not g.defect_run_ok(RUN2)
    g.create(["a.jsonl"], new_set_reason=REASON, discard_count=2) if False else None
    shutil.rmtree(g.runs_dir / RUN2)
    g.finish(RUN2, "aborted")
    g.create(["a.jsonl"], new_set_reason=REASON, discard_count=2)
    assert not g.defect_run_ok(RUN1)  # a run of the PREVIOUS set


# ====================================================== 10: verification happens before anything is written
def test_load_verifies_the_reports_before_it_rewrites_anything(tmp_path, monkeypatch):
    g = gate_for(tmp_path, KEY)
    g.begin(g.load(), RUN1)
    (g.runs_dir / RUN1).mkdir(parents=True)
    (g.runs_dir / RUN1 / "report.json").write_text(json.dumps({"aborted": False}), encoding="utf-8")
    g.record_report(RUN1)
    monkeypatch.setattr(
        sealed, "write_lock", lambda *a, **k: (_ for _ in ()).throw(OSError("crash"))
    )
    with pytest.raises(OSError):
        g.finish(
            RUN1, "complete"
        )  # the chain has sealed_done, lock.json is behind: recovery is pending
    monkeypatch.undo()
    shutil.rmtree(g.runs_dir / RUN1)
    lock_bytes, chain_bytes = lock_path(g.eval_dir).read_bytes(), g.chain.path.read_bytes()
    with pytest.raises(LockError, match="deleted"):
        g.load()
    assert (
        lock_path(g.eval_dir).read_bytes() == lock_bytes
    )  # nothing was re-sealed over the broken evidence
    assert g.chain.path.read_bytes() == chain_bytes  # and no `reconcile` entry was appended


def test_a_keyed_chain_entry_without_a_core_hash_is_an_error(tmp_path):
    g = gate_for(tmp_path, KEY)
    entry = g.chain.append("reconcile", {"replayed": []})  # an entry that lacks core_hash
    forged = g._sealed(read_lock(g.eval_dir).model_copy(update={"chain_head": entry["sha"]}))
    write_lock(g.eval_dir, forged)
    with pytest.raises(LockError, match="no core_hash"):
        g.load()
    keyless = gate_for(tmp_path / "k", None)
    entry = keyless.chain.append("reconcile", {"replayed": []})
    write_lock(
        keyless.eval_dir,
        read_lock(keyless.eval_dir).model_copy(update={"chain_head": entry["sha"]}),
    )
    assert keyless.load().test_runs == 0  # a keyless gate tolerates it (older chains)


# ====================================================== roles.sql: validated, and what the role can do
def test_roles_sql_validates_what_it_is_given_and_grants_exactly_the_documented_rights():
    text = "\n".join(
        line
        for line in (DEMO / "db" / "roles.sql").read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith("--")
    )
    assert "CONNECTION LIMIT :cl;" in text and ":ro_connection_limit;" not in text
    assert "'^[0-9]{1,3}$'" in text and "BETWEEN 1 AND 999" in text
    assert (
        text.count("'^[1-9][0-9]{0,4}s$'") == 3
    )  # statement, lock and idle timeouts: positive, so never '0s'
    grants = re.findall(r"^GRANT .*?;", text, flags=re.MULTILINE | re.DOTALL)
    assert len(grants) == 3
    assert any("CONNECT ON DATABASE" in g for g in grants)
    assert any("USAGE ON SCHEMA analytics" in g for g in grants)
    assert any(
        "SELECT ON analytics.customers_v, analytics.products_v, analytics.orders_v, analytics.order_items_v"
        in g.replace("\n", " ").replace("    ", " ")
        for g in grants
    )
    assert not re.search(r"GRANT\s+(ALL|INSERT|UPDATE|DELETE|TRUNCATE|CREATE|EXECUTE)", text)


def test_unused_imports_kept():
    assert Lock and Chain and cmd_run and evalcli
