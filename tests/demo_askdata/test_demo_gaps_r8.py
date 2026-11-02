"""Round 8: identical-set refusal, lost-folder forgery, relabelled copies, failed move-aside, key rotation, report-lost
guards, byte-priced reservations, idempotent settle, per-config isolation, roles.sql limits."""

from __future__ import annotations

import json
import os
import re
import shutil
import threading
from decimal import Decimal

import pytest
from askdata import evalcli, evalset, sealed
from askdata.evalcli import cmd_run
from askdata.evalset import LockError, lock_path
from askdata.fixtures import ROUTE, Step
from askdata.meter import Meter, worst_case_usd
from askdata.sealed import RECOVERY_MARKER, SealedGate, key_from

from hadavin_sdk.actions.secrets import FakeSecretProvider

from .conftest import DEMO
from .kit import COUNT_ORDERS, Kit
from .test_demo_gaps_r3 import KEY, gate_for, renew
from .test_demo_gaps_r7 import REASON, RUN1, _recorded_run
from .test_eval_harness import cli_env  # noqa: F401 - a fixture reused here

KEY2 = ("n3w-" * 6).encode()


# ============================================================ M1: a new set must differ from every earlier set
def test_a_new_set_with_files_identical_to_an_earlier_set_is_refused(tmp_path):
    g = gate_for(tmp_path)
    with pytest.raises(LockError, match="IDENTICAL"):
        g.create(["a.jsonl"], new_set_reason=REASON)
    renew(g)
    g.create(["a.jsonl"], new_set_reason=REASON)  # different files: fine
    (g.eval_dir / "a.jsonl").write_text("x\n", encoding="utf-8")  # back to the FIRST set's bytes
    with pytest.raises(LockError, match="IDENTICAL"):
        g.create(["a.jsonl"], new_set_reason=REASON + " again")


# ============================================================ M2 / M3: report vouching
def _sealed_run_dir(cfg, factory):
    cmd_run(cfg, "test", 1, None, harness_factory=factory)
    return next(p for p in cfg.paths.runs_dir.iterdir() if p.name.endswith("-sealed"))


def test_a_forged_report_in_a_lost_run_folder_prints_nothing_and_exits_4(cli_env, capsys):  # noqa: F811
    cfg, factory = cli_env
    run_dir = _sealed_run_dir(cfg, factory)
    shutil.rmtree(run_dir)
    evalcli._gate(cfg).mark_report_lost(run_dir.name, "pruned runs/ to free the disk")
    run_dir.mkdir()
    (run_dir / "report.json").write_text(
        json.dumps({"split": "test", "label": "sealed", "verdict": "FORGED-GREEN"}),
        encoding="utf-8",
    )
    capsys.readouterr()
    assert evalcli.cmd_report(run_dir, "md", None, cfg) == 4
    shown = capsys.readouterr().out
    assert "marked lost" in shown and "FORGED-GREEN" not in shown


def test_a_byte_copy_of_a_recorded_report_in_any_folder_is_not_silently_shown(
    cli_env,  # noqa: F811
    capsys,
    tmp_path,
):
    cfg, factory = cli_env
    run_dir = _sealed_run_dir(cfg, factory)
    copy = tmp_path / "pretty-name"
    copy.mkdir()
    shutil.copyfile(run_dir / "report.json", copy / "report.json")
    capsys.readouterr()
    assert evalcli.cmd_report(copy, "md", None, cfg) == 4
    assert "NOT VOUCHED" in capsys.readouterr().out


def test_a_folder_named_like_a_sealed_run_is_checked_even_when_its_report_says_dev(
    cli_env,  # noqa: F811
    capsys,
    tmp_path,
):
    cfg, _ = cli_env
    fake = tmp_path / "20261101T000000000009Z-sealed"
    fake.mkdir()
    (fake / "report.json").write_text(
        json.dumps({"split": "dev", "label": "dev"}), encoding="utf-8"
    )
    assert evalcli._looks_sealed(fake)
    assert evalcli.cmd_report(fake, "md", None, cfg) == 4
    assert "NOT VOUCHED" in capsys.readouterr().out


# ============================================================ M6: a failed move-aside leaves nothing to recover
def test_a_failed_move_of_the_old_lock_leaves_no_marker_and_no_changes(tmp_path, monkeypatch):
    g = gate_for(tmp_path, KEY)
    renew(g)
    entries_before = g.chain.path.read_bytes()
    real = os.replace

    def failing(src, dst, *a, **k):
        if ".prev-" in str(dst):
            raise OSError("disk says no")
        return real(src, dst, *a, **k)

    monkeypatch.setattr(os, "replace", failing)
    with pytest.raises(OSError, match="disk says no"):
        g.create(["a.jsonl"], new_set_reason=REASON)
    monkeypatch.setattr(os, "replace", real)
    assert not (g.eval_dir / RECOVERY_MARKER).exists()
    assert g.chain.path.read_bytes() == entries_before
    assert lock_path(g.eval_dir).exists()


# ============================================================ m1 / m2: report-lost guards
def test_report_lost_on_an_intact_run_is_refused(tmp_path):
    g = gate_for(tmp_path, KEY)
    _recorded_run(g, RUN1)
    with pytest.raises(LockError, match="intact"):
        g.mark_report_lost(RUN1, "this run is perfectly healthy but I want to hide it")


def test_report_lost_on_a_keyed_set_needs_the_key(tmp_path):
    g = gate_for(tmp_path, KEY)
    _recorded_run(g, RUN1)
    shutil.rmtree(g.runs_dir / RUN1)
    keyless = SealedGate(g.eval_dir, g.chain.path, g.runs_dir, None, g.anchors)
    with pytest.raises(LockError, match="downgrade"):
        keyless.mark_report_lost(RUN1, "pruned runs/ to free the disk")
    assert not any(e["kind"] == "report_lost" for e in g.chain.entries())


# ============================================================ m4: a run whose results vanished is never "complete"
def test_a_run_finished_without_any_results_on_disk_is_unverified(tmp_path):
    g = gate_for(tmp_path, KEY)
    g.begin(g.load(), "r1")
    g.finish("r1", "complete")
    assert g.load().last_test_status == "unverified"


# ============================================================ m6: Windows-style PermissionError on replace is retried
def _flaky_replace(monkeypatch, failures):
    calls = {"n": 0}
    real = os.replace

    def flaky(src, dst, *a, **k):
        calls["n"] += 1
        if calls["n"] <= failures:
            raise PermissionError("held open by a reader")
        return real(src, dst, *a, **k)

    monkeypatch.setattr(os, "replace", flaky)
    monkeypatch.setattr(evalset.time, "sleep", lambda _s: None)
    return calls


def test_the_chain_rewrite_and_the_json_writes_retry_a_permission_error_and_leak_no_temp(
    tmp_path, monkeypatch
):
    g = gate_for(tmp_path, KEY)
    lines = g.chain.path.read_text(encoding="utf-8").splitlines()
    calls = _flaky_replace(monkeypatch, 2)
    g.chain._rewrite(lines)
    assert calls["n"] == 3
    calls = _flaky_replace(monkeypatch, 2)
    target = tmp_path / "audit" / "x.json"
    sealed._write_json(target, {"a": 1})
    assert json.loads(target.read_text(encoding="utf-8")) == {"a": 1} and calls["n"] == 3
    _flaky_replace(monkeypatch, 10**6)  # never succeeds
    with pytest.raises(PermissionError):
        sealed._write_json(target, {"a": 2})
    with pytest.raises(PermissionError):
        g.chain._rewrite(lines)
    assert not list((tmp_path / "audit").glob("*.tmp*")) and not list(
        (tmp_path / "audit").glob("*.new*")
    )


# ============================================================ m9: key rotation
def test_rotate_key_round_trip_and_the_ways_it_is_refused(tmp_path):
    g = gate_for(tmp_path, KEY)
    _recorded_run(g, RUN1)
    new = SealedGate(g.eval_dir, g.chain.path, g.runs_dir, KEY2, g.anchors, (KEY,))
    with pytest.raises(LockError):  # a lock sealed under the old key is not accepted as the new one
        new.begin(new.load(), "r2")
    new.rotate_key()
    assert new.load().test_runs == 1  # the counter is untouched
    assert any(e["kind"] == "rekey" for e in new.chain.entries())
    new.begin(new.load(), "r2")
    assert new.load().test_runs == 2
    old_only = SealedGate(g.eval_dir, g.chain.path, g.runs_dir, KEY, g.anchors)
    with pytest.raises(LockError):
        old_only.load()
    new_alone = SealedGate(g.eval_dir, g.chain.path, g.runs_dir, KEY2, g.anchors)
    with pytest.raises(LockError):
        new_alone.load()
    with pytest.raises(LockError, match="previous key"):
        SealedGate(g.eval_dir, g.chain.path, g.runs_dir, KEY2, g.anchors).rotate_key()


def test_a_trailing_newline_in_a_secret_does_not_change_the_key():
    assert key_from(FakeSecretProvider({"k": KEY.decode() + "\n"}), "k") == KEY


# ============================================================ M7: reservations are priced in bytes
def test_worst_case_prices_bytes_so_cjk_is_not_undercounted():
    question = "注文" * 200  # 400 characters, 1200 UTF-8 bytes
    assert worst_case_usd(ROUTE, len(question.encode())) > worst_case_usd(ROUTE, len(question))


def test_the_pipeline_reserves_for_the_bytes_of_a_cjk_question(tmp_path):
    from askdata import llm_io
    from askdata.pipeline import _SCHEMA_BYTES

    q = "注文は何件ありますか" * 10
    k = Kit(tmp_path)
    k.script(q, Step(sql=COUNT_ORDERS))
    reserved = []
    real = k.meter.reserve
    k.meter.reserve = lambda amount, live=True: (reserved.append(amount), real(amount, live=live))[
        1
    ]
    k.pipeline.ask(q)
    content = llm_io.build_messages(k.pipeline.prompt.text, q, None, None)[0]["content"]
    n = len(llm_io.SYSTEM.encode()) + len(content.encode()) + _SCHEMA_BYTES
    assert n > len(llm_io.SYSTEM) + len(content) + _SCHEMA_BYTES
    assert reserved[0] / k.pipeline.s.llm_max_attempts >= worst_case_usd(ROUTE, n)


# ============================================================ R368-R370: no lost or double-billed call, per-config isolation
def _meter(path, cap="100.00"):
    Meter.create(path, total_cap=cap, reserve="1.00", demo_cap="90.00")
    return Meter(path)


def test_a_second_settle_of_the_same_reservation_changes_nothing(tmp_path):
    m = _meter(tmp_path / "m.json")
    rid = m.reserve(Decimal("0.50"), live=False)
    m.settle(Decimal("0.50"), Decimal("0.10"), rid)
    once = m.snapshot()["askdata_spent"]
    m.settle(Decimal("0.50"), Decimal("0.10"), rid)  # a retried or duplicated settle
    assert m.snapshot()["askdata_spent"] == once == Decimal("0.10")
    assert m.snapshot()["open"] == 0


def test_concurrent_reserve_and_settle_lose_and_double_bill_nothing(tmp_path):
    m = _meter(tmp_path / "m.json")
    errors = []

    def work(i):
        try:
            mm = Meter(m.path)
            rid = mm.reserve(Decimal("0.20"), live=False)
            mm.settle(Decimal("0.20"), Decimal("0.01") * (i + 1), rid)
        except Exception as err:  # noqa: BLE001
            errors.append(err)

    threads = [threading.Thread(target=work, args=(i,)) for i in range(12)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    snap = m.snapshot()
    assert snap["askdata_spent"] == sum(Decimal("0.01") * (i + 1) for i in range(12))
    assert snap["open"] == 0


def test_two_configs_never_see_each_others_spend(tmp_path):
    for name in ("a", "b"):
        (tmp_path / name).mkdir()
    a, b = _meter(tmp_path / "a" / "m.json"), _meter(tmp_path / "b" / "m.json")
    rid = a.reserve(Decimal("0.30"), live=False)
    a.settle(Decimal("0.30"), Decimal("0.25"), rid)
    assert a.snapshot()["askdata_spent"] == Decimal("0.25")
    assert b.snapshot()["askdata_spent"] == Decimal(0)


# ============================================================ m10: roles.sql limits (text; the live run was done by hand)
def test_roles_sql_caps_the_timeouts_and_checks_the_role_name_and_the_password():
    text = "\n".join(
        ln
        for ln in (DEMO / "db" / "roles.sql").read_text(encoding="utf-8").splitlines()
        if not ln.lstrip().startswith("--")
    )
    assert "'^[1-9][0-9]{0,2}s$'" in text and "{0,4}s" not in text  # at most 999s
    assert "'^[a-z_][a-z0-9_]{0,62}$'" in text
    assert re.search(r"length\(:'ro_password'\) >= 12", text)
    assert text.index("ok_role") < text.index("CREATE ROLE")
    assert text.index("ok_pw") < text.index("CREATE ROLE")


def test_the_runtime_timeouts_the_cli_passes_cannot_exceed_the_sql_cap():
    from askdata.settings import Runtime

    with pytest.raises(ValueError):
        Runtime(role_statement_timeout_s=1000)
