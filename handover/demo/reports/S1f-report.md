# S1f report: flaky test_mutant_no_claim

Result: a test race, not a desk race. Fixed in tests/test_mutants.py only (src untouched). EGM review: lead runs it.

## Cause
Before the fix: 7 failures in 40 runs ("DID NOT RAISE AssertionError": the weak claim sent 1 email, not 2).
The real claim (desk.py `_claim`) is one SQL UPDATE with a state precondition inside a write transaction, so only one
Retry can win; the real test test_retry_twice_concurrent passed 100/100 and the scenario cannot double or lose a send.
The race is in the weakened stand-in: it UPDATEs `attempts+1` and returns True; the caller then reads its ownership
token with `_take_token` (current attempts value). If thread A reads before thread B's update, A holds token N+1,
B moves the row to N+2, A's first `_touch` fails ("no longer ours") and A sends nothing. Only when both updates land
before either read do both send. That ordering depended on thread timing.

## Fix
The stand-in waits on `threading.Barrier(2, timeout=20)` after its UPDATE and before returning, so both callers
always hold the same token and both send. No sleeps. Guard strength: it still requires AssertionError matching
"emails == 1" and "got 2", and `applied` must be non-empty.

## Evidence (raw counts)
- test_mutant_no_claim (weak claim must be caught): 0 failures in 100 runs (before: 7/40).
- test_retry_twice_concurrent (real claim must pass): 0 failures in 100 runs.
- tests/test_mutants.py whole file, final head: 0 failures in 100 runs.
- Sibling loop, each file run 50 times, failing test ids collected: test_mutants.py, test_hardening_cloud_d.py,
  test_stall_eviction.py, test_reaper_start_stop.py, test_slow_sender.py, test_http.py, test_server_hardening.py:
  0 failures each (350 file runs). Other mutation guard in the file (test_mutant_no_unique_key) is in the 100 runs.
- Not run in a loop: test_hardening_cloud.py, _cloud_b.py, test_portal_api.py (they use sleeps; not ordering
  between two threads per grep, but not looped, so not verified flake-free). Full suite not run (another process uses
  a4r4). Other claim-using tests listed by grep: only retry_twice_body uses the mutant (test_flow.py, test_mutants.py).
- Not done: I did not run the old-code "weak claim fails every time" against an unfixed barrier-free variant beyond the
  7/40 failure before the fix; 100/100 pass after.
- ruff check . : All checks passed. ruff format --check . : 54 files already formatted.
- Hygiene: test names unchanged (test_mutant_no_claim, 21 chars); no IP-like or token-like literals added.

## Files
- /home/user/build/S1f.diff (diff -ruN, a/ b/, one file: tests/test_mutants.py, 32 lines). Apply-check on a fresh copy
  of /tmp/dpld-a4r4: patch -p1 --dry-run and real apply OK, result identical to /tmp/dpld-s6.
- Working tree: /tmp/dpld-s6. Background loop script /tmp/s6loop.sh has finished; no processes left running by me.
