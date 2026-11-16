"""Reserve race across processes with a start barrier (every worker is ready before any starts) and enough attempts to overlap."""

from __future__ import annotations

import os
import subprocess
import sys
import time

import pytest
from model_support import live_settings, rows, set_prices

WORKER = r"""
import sys, time
from dataclasses import replace
from pathlib import Path
from intake import budget, settings
from intake.codes import Refused

tag, barrier, attempts = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3])
s = settings.load()
s = replace(s, model=replace(s.model, overhead_tokens=0, max_tokens=99_990))  # worst = 99_990 + 10 body bytes = 100_000 micro
(barrier / ("ready-" + tag)).write_text("1")
while not (barrier / "go").exists():
    pass  # spin: all workers leave the barrier within microseconds of each other
budget.BUSY_MS = 60000  # under machine load a waiting writer must wait, not give up: only a budget refusal is allowed
ok, other = 0, 0
for i in range(attempts):
    try:
        budget.reserve(s, tag + str(i).zfill(60 - len(tag)), "read", b"0123456789")
        ok += 1
    except Refused as e:
        if e.code != "budget_total":
            other += 1  # a busy or locked refusal: it must never happen with BEGIN IMMEDIATE and a long busy timeout
print(ok, other)
"""


def _race(tmp_path, workers: int, attempts: int, cap_dollars: int = 1) -> list[int]:
    s = live_settings(tmp_path, limit=cap_dollars, sentence_total=cap_dollars)
    set_prices(s, 1_000_000, 1_000_000)
    barrier = tmp_path / "barrier"
    barrier.mkdir()
    env = {**os.environ, "HADAVIN_LOCAL": str(s.local), "INTAKE_MODEL_BACKEND": "anthropic"}
    ps = [
        subprocess.Popen([sys.executable, "-c", WORKER, f"w{n}", str(barrier), str(attempts)], env=env, stdout=subprocess.PIPE, text=True)
        for n in range(workers)
    ]
    t0 = time.time()
    while len(list(barrier.glob("ready-*"))) < workers:
        assert time.time() - t0 < 60, "workers did not become ready"
        time.sleep(0.01)
    (barrier / "go").write_text("1")
    out = [p.communicate(timeout=180)[0].split() for p in ps]
    got = [int(o[0]) for o in out]
    assert [int(o[1]) for o in out] == [0] * workers  # no process met a busy ledger
    assert rows(s, "reservations") == sum(got)
    return got


@pytest.mark.parametrize("workers", [2, 3])
def test_processes_released_together_never_pass_the_cap(tmp_path, workers):
    got = _race(tmp_path, workers, attempts=30)
    # cap US$1 = 10 reservations of 100,000 micro; every process tries 30 times, so the 60 or 90 attempts overlap heavily
    assert sum(got) == 10
