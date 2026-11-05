"""Cross-process tests of the queue (spec 7): the service is one process but ``intake purge`` and a second start are separate processes, and the
database guards must hold between them. Workers are real subprocesses started together at one wall-clock instant."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from queue_helpers import approve, assertive_all, new_item, sha

from conftest import settings_for_tests
from intake import queue_schema, workqueue
from intake.content_code import content_code

WORKER = Path(__file__).with_name("queue_worker.py")


def run_together(s, jobs: list[list[str]], lead_s: float = 4.0) -> list[str]:
    """Start every job as its own process, all released at the same instant; return each one's printed word."""
    env = {**os.environ, "HADAVIN_LOCAL": str(s.local), "INTAKE_MODEL_BACKEND": "fake"}
    start = str(time.time() + lead_s)
    procs = [
        subprocess.Popen([sys.executable, str(WORKER), start, *job], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)  # noqa: S603
        for job in jobs
    ]
    out = []
    for p in procs:
        so, se = p.communicate(timeout=180)
        assert p.returncode in (0, 9), se[-400:]
        out.append(so.strip().splitlines()[-1] if so.strip() else se[-200:])
    return out


def test_first_open_race_four_processes_create_one_consistent_schema(tmp_path):
    s = settings_for_tests(tmp_path)
    assert not workqueue.queue_path(s).exists()
    assert run_together(s, [["connect"]] * 4) == ["ok"] * 4
    with workqueue.opened(s) as c:
        have = {
            r["name"]: queue_schema.normalise_sql(r["sql"]) for r in c.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger'")
        }
    assert have == {k: queue_schema.normalise_sql(v) for k, v in queue_schema.trigger_sql().items()}


def test_the_same_file_dropped_in_four_processes_is_one_item_and_three_duplicates(tmp_path):
    s = settings_for_tests(tmp_path)
    workqueue.connect(s).close()
    res = run_together(s, [["insert", sha("same"), "same"]] * 4)
    assert sorted(res) == ["dup", "dup", "dup", "item"], res
    assert len(workqueue.list_items(s)) == 1


def test_four_processes_deciding_one_item_exactly_one_wins(tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s)
    code = content_code(it)
    res = run_together(s, [["decide", it.id, d, code, str(it.version)] for d in ("approve", "reject", "approve", "reject")])
    assert sorted(res) == ["already_decided"] * 3 + ["ok"], res
    with workqueue.opened(s) as c:
        assert c.execute("SELECT COUNT(*) FROM decisions").fetchone()[0] == 1


@pytest.mark.parametrize("round_", range(3))
def test_purge_and_decide_in_two_processes_never_both_succeed(round_, tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s, f"r{round_}")
    res = run_together(s, [["decide", it.id, "approve", content_code(it), str(it.version)], ["purge", it.id]], lead_s=3.0)
    decide_res, purge_res = res
    assert (decide_res, purge_res) in (("ok", "purge_refused"), ("not_found", "ok")), res
    got = workqueue.get(s, it.id)
    with workqueue.opened(s) as c:
        n_dec = c.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
        n_purge = c.execute("SELECT COUNT(*) FROM purges").fetchone()[0]
    if decide_res == "ok":
        assert got.state == "APPROVED" and n_dec == 1 and n_purge == 0
    else:
        assert got is None and n_dec == 0 and n_purge == 1


def test_a_process_killed_in_the_middle_of_a_transaction_leaves_nothing_behind(tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s)
    assert run_together(s, [["die_in_transaction", str(it.uid)]], lead_s=2.0) == ["in_transaction"]
    assert workqueue.get(s, it.id).state == "READY" and workqueue.get(s, it.id).version == it.version
    with workqueue.opened(s) as c:
        assert c.execute("SELECT COUNT(*) FROM decisions").fetchone()[0] == 0
    assert approve(s, workqueue.get(s, it.id)).decision == "approve"  # the lock died with the process: the next writer is not blocked


assertive_all(globals())
