# Q1 xdist proof (evidence only, no verdict)

Base: public main f3c39cf89ec989f032ea48a23cfd824b88da9c68 (worktree /home/user/work/q1-base). Python 3.12.3.

## Failures first
Under `-n 3`, 2 tests FAIL in both xdist runs; both PASS serial (and pass alone, in either venv, in a serial run of the file):
- tests/test_reset_scripts.py::test_reset_sh_refuses_when_the_desk_does_not_stop (expected exit 5, got 6)
- tests/test_reset_scripts.py::test_reset_sh_waits_for_a_desk_that_needs_a_few_seconds_to_stop (expected 0, got 6)
Both: `refused: pid N in .../desk.pid is not the desk or the demo server`.
Reproduced on a small run: `-p xdist -n 1` and `-n 3` on tests/test_reset_scripts.py alone fail the same 2 (43 pass); serial passes all 45.
Cause (guess, NOT confirmed): scripts/reset.sh line 34 reads the child's command line with `ps -p PID -o args=` and matches `*lead_desk.server*`. The marker is the LAST argument, after a long `-c` code string. Where `ps` cuts the line to 80 columns the marker is lost and the script exits 6. A probe test (throwaway, /home/user/work/q1-probe) showed this cut happens inside a pytest test that captures output, even serial, so what differs under xdist workers (their standard input/output are pipes set up by execnet) is unproven. Not a shared port / file / order issue as far as seen: failure is deterministic in both runs and with -n 1.

## 1. Results
| run | passed | failed | skipped | errors | wall | exit |
|---|---|---|---|---|---|---|
| serial (final-venv) | 3683 | 0 | 200 | 0 | 1295.23s (21:35) | 0 |
| xdist -n 3 run 1 | 3681 | 2 | 200 | 0 | 428.41s (7:08) | 1 |
| xdist -n 3 run 2 | 3681 | 2 | 200 | 0 | 478.79s (7:58) | 1 |

loadavg (1/5/15 min) before -> after: serial 0.00 0.16 0.48 at 12:31Z (before the pytest start, see progress file) -> 5.05 7.19 6.09; xdist1 4.55 6.63 5.97 -> 7.45 7.67 6.66; xdist2 4.73 6.90 6.44 -> 15.87 13.44 9.48. Other agents were running; every run is NOISY. Q4 had written END (12:54:41Z) before xdist 1 started (12:54:42Z); xdist 1 did not need the 40-minute cap.
Serial wall time was measured under load 3.5-7.6 (other agents), so the speed-up is indicative only.

## 2. Node-id comparison (script: handover/demo3/tools/q1_compare.py)
Totals: 3883 ids in each run (3683+200 serial; 3683+200 xdist counting the 2 failures). The script's parser read 3880/3883/3883 ids; the gaps are lines where a test printed to stderr in the middle of a status line (e.g. `test_fakes_body_before_answer...[POST /fake/nothing-{}]`, `[POST /fake/outbox-[1]]`, `test_hygiene_scan_public`, `test_measure_burst`). I resolved those by hand with grep: same outcome in both runs (PASSED, PASSED, SKIPPED, SKIPPED).
- ids only in serial: 0. ids only in xdist: 0 (after the manual check).
- ids with a different outcome serial vs xdist1: 2 (the two above, PASSED -> FAILED).
- xdist1 vs xdist2: 0 different outcomes, same ids; same 2 failures (so no flake seen, 2 runs).
Skipped sets match (200): no gitleaks (28), no playwright (about 166), etc.

## 3. Fails only under xdist: last 15 lines
See raw/q1-xdist1.log, section "FAILURES". Both end with:
`AssertionError: ('', 'refused: pid 21030 in /home/user/work/q1-base/data/reset-guard-lbjr6mdz/desk.pid is not the desk or the demo server; nothing was stopped or deleted (delete the pid file yourself if it is stale)\n')` / `assert 6 == 5` (first) and `assert 6 == 0` (second).

## 4. Commands and versions
- worktree: `git -C /home/user/work/src worktree add --detach /home/user/work/q1-base f3c39cf89ec989f032ea48a23cfd824b88da9c68`
- serial: `TMPDIR=/home/user/work/q1-tmp-serial timeout 2400 /home/user/work/final-venv/bin/python -m pytest -v -rs -p no:cacheprovider -o faulthandler_timeout=120 --basetemp=$TMPDIR/bt`
- xdist: same plus `-p xdist -n 3`, venv /home/user/work/q1-xdist-venv (python3.12 venv, `pip install --require-hashes -r requirements-dev.txt`, then `pip install pytest-xdist`), TMPDIR=/home/user/work/q1-tmp-xdist1 / q1-tmp-xdist2.
- versions in the xdist venv: pytest 9.2.0, pytest-xdist 3.8.0, execnet 2.1.2 (the only packages added: pytest-xdist and execnet, taken from the xdist install; nothing entered the repo).
- Raw logs: raw/q1-serial.log, q1-xdist1.log, q1-xdist2.log; timings: raw/progress-Q1.txt.
