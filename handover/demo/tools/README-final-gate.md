# final_gate.sh: one command that records the evidence for a demo tarball

It runs on a fresh unpacked copy of a demo tarball and writes a report with the tools' own output, word for word.
It gives no pass/fail verdict of its own. The tarballs are private test copies: this script unpacks them into a
temporary folder and never copies them anywhere else.

## Use

    handover/demo/tools/final_gate.sh handover/demo/dpld-fix7-00e30c5.tar.gz              # full run
    handover/demo/tools/final_gate.sh <tarball> --quick                                    # small run (about 10 minutes)
    handover/demo/tools/final_gate.sh <tarball> --only 1                                   # one stage (or --only 2,3)
    handover/demo/tools/final_gate.sh <tarball> --workdir /tmp/x                           # resume: stages already finished there are skipped
    options: --force (repeat finished stages), --out-dir DIR (default handover/demo/reports)

Report: `handover/demo/reports/final-gate-<shortsha>.md` (`-quick` is added to the name in quick mode), plus a folder
`final-gate-<shortsha>[-quick]-raw/` with every raw output file. The report header says which folder the run used.

## What it does (in this order, one thing at a time, every step has a time limit)

| Stage | What | Full | `--quick` |
|---|---|---|---|
| 0 | Unpack into a new temp folder; make an own virtual environment (packages from the tarball's `requirements-dev.txt`, hashes checked; if the download fails it falls back to the packages of `/tmp/dpld-venv` and says so in the header); apply the 3 documented `server.py` hook edits to the unpacked copy only | yes | yes |
| 1 | `ruff check`, `ruff format --check`, `mypy --platform linux`, `bandit -q -ll -r src tools -c pyproject.toml`, `scripts/check_schema.py` | yes | yes |
| 2 | Full `pytest -q -rf -p no:cacheprovider` | 3 runs | 1 run |
| 3 | The four concurrency tests (`test_concurrent_same_source_ref`, `test_retry_twice_concurrent`, `test_ten_parallel`, `test_reconcile_counts`, picked with `-k`) | 50 runs each | 3 runs each |
| 4 | Hostile matrix with one runner (`hostile_run.py`: classes B to H, which include 1000 parallel different ids, concurrent resolve and kill -9 with restart; then class A through `final_gate/runA.py`) | yes | not run |
| 5 | Load, for the keyed and the blind sender: same lead 10/100/500/1000, different leads 100/1000; then kill -9 rounds 1 to 5 (200 requests each) per mode | yes | same 10/100, different 100, kill round 1 |

Each step records: the command, the folder it ran in, the exit code (124 = this script stopped it at its time limit),
the seconds and the raw file path (`stages.jsonl` in the work folder holds the same as JSON lines).

## The server.py edits

The tarball's `server.py` may lack the lead's hook edits (CONTRACT-DELTA.md, "server.py hooks"): catch `LockHeldError`
and `OSError` separately, `start_background()` before `startup()`, `stop_background()` first in `finally`. Stage 0
applies them with `final_gate/patch_hooks.py` to the unpacked copy. It stops with exit 72 if the text it replaces is not
found exactly once, and does nothing (prints ALREADY-PATCHED) if the hooks are present. The report header repeats the result.
Hook 3 (listen queue) is not edited: the script only prints the tree's `LISTEN_QUEUE` value.

## Safety

- One runner: a lock file (`/tmp/final-gate.lock`) refuses a second gate (exit 75). Free ports are picked at the start of every step.
- Every desk or fake server it starts is stopped by the load/hostile script that started it; a step that hits its time limit
  has only its own process group stopped. It never touches other processes.
- All data is made up (`example.test` addresses). No model call, no network use except the package download in stage 0.
- Do not run it while another heavy job (for example your own full pytest) is running: the timing numbers would be mixed.

## Files in `final_gate/`

`step.py` (run one command with a time limit, record it), `conc.py` (repeat one test selection), `patch_hooks.py`,
`prep_hostile.py` (points a copy of `../hostile_run.py` at this run's Python and ports), `runA.py`, `load.py` (stdlib load
script: root, Python and ports come from environment variables), `freeport.py`, `report.py`.
