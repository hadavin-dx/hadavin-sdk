# core-c -> lead: heavy batches paused on the cloud box (12:55Z, load 7.8 on 4 cores), for the laptop

PAUSED (SIGSTOP, resumable with kill -CONT; the cloud box keeps them frozen, they are not killed):
1. G11 ticket drafter's own full-suite run: pytest master pid 10068 + 3 xdist workers, cwd /tmp/claude-0/-home-user/1ecfcb92-30a8-505b-a8c3-27491ed2aff6/scratchpad/g11t_work/full (a git archive copy of the head at ~12:30Z). It is not needed for the ticket (the drafter wanted a baseline of the whole suite). The same measurement is laptop JOB 1 below: no separate request.

KEPT RUNNING (2 heavy): (a) G4 builder: `pytest -q -n 2 -m "not live and not perf" -p no:randomly` in /tmp/core-c-g4 (branch wip-g4); (b) G9 fix builder: `python tests/redact_mutants.py` whole file (mutant runner, one pytest child) in /tmp/core-c-g9 (branch wip-g9).

HOLDING (instructed, not started): E14 builder (wip-e14) and M3 builder (wip-m3) run only targeted files until a heavy slot is free.

If you want the laptop to take heavy work instead of the cloud box, in priority order (all on base origin/cloud/core-c head e0e37b1a9; push evidence to wip/lead-c-<item>):
- JOB 1 (already requested in requests/lead-build-1.md): whole suite, non-perf and perf separately (perf only on an idle machine: a timing test at load 7.8 proves nothing), Python 3.12 and 3.13, PG17.
- JOB 4 (new, "perf-idle"): the perf-marked files on an idle laptop core set, one process at a time: uv run --all-extras --group test pytest -q -m perf -p no:randomly tests/test_redact_fold_budget.py tests/test_k5_perf.py tests/test_textnorm_perf.py tests/test_textnorm_round2.py tests/test_redact_settle_loop.py tests/test_runmap_enforce_map.py tests/test_model_gate.py (timing rows: report the ratio lines), then the same on branch wip/cloud-core-c/g9 (after its fix; E17: tests/test_redact_fold_budget.py::test_hostile_1_hostile_shapes_return_a_clean_text_or_refuse must pass) and wip/cloud-core-c/g4 (after it lands). Report: handover/core-c/evidence/LAPTOP-perf.md = per file passed/failed, every ratio, load average at start and end.
