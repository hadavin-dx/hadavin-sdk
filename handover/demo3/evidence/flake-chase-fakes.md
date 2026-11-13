# Q10 flake chase: tests/test_fakes_body_before_answer.py (evidence only, no judgement)

STOPPED EARLY on the lane lead's order (CPU shortage, 13:16Z / 18:46 IST). INCOMPLETE vs the brief:
- PR #12 tree (8d655773): 0 runs (never started). requirements-dev.txt is identical in both commits, so final-venv would have served both.
- Main tree (f3c39cf8): 60 staggered runs + 12 lockstep runs (4 batches of 3 started in the same second); brief asked 20 lockstep.
- CPU hog: PID 27139 ran 13:05-13:15Z (its own 600 s timeout), covering the 60 staggered runs and part of the lockstep ones; second hog (PID 17877) was killed by me within 2 minutes of starting. Lockstep runs ran mostly without the hog.
- Not checked: the PR #12 tree; any run with heavier load than 3 parallel pytests + 1 hog on a shared 4-core machine.

## Summary
| tree | runs | errors | failures | duration min / median / max (s) |
|---|---|---|---|---|
| main f3c39cf8, staggered 1.7 s | 60 | 0 | 0 | 23.07 / 23.44 / 24.47 |
| main f3c39cf8, lockstep | 12 | 0 | 0 | 23.00 / 23.31 / 23.84 |
| PR #12 8d655773 | 0 | not run | not run | not run |

Every run: exit 0, "17 passed". No ERROR or FAILED mark in any of 72 logs. Because no error appeared, step 4 (10 reproductions) had nothing to reproduce.

## Errors verbatim
None.

## What the "Exception occurred during processing of request" lines are
Present in all 72 main-tree logs, 825 in total (11 or 12 per run), always `BrokenPipeError: [Errno 32]`, raised at demo_only/fake_hubspot.py:224 (`_send`, wfile.write) via `_gate` :243 (401), do_POST :320/:327, do_PATCH :285/:290. They are stderr noise from socketserver.handle_error, not test results. Likely cause (inference, not proven): the test's `early_answer` probe sends only the head and closes after 0.3 s; the fake then writes its answer to a closed socket. Constant count per run means it does not depend on load. Logs: handover/demo3/evidence/raw/q10/ (main-*.log, summary-*.txt).

## Risk list (read from the code; none of these was seen to fire)
Ports: none fixed. Fakes, model, hubspot and the desk all bind port 0 (tests/test_fakes_body_before_answer.py fixtures; demo_only/fakes_server.py:221, fake_hubspot.py:384, fake_model_server.py:238). Config fakes_port 8766 is only used by the command line main.
Shared files: none in this test file (desk tests use pytest tmp_path via env; --basetemp confinement).
Threads: server thread per fixture, daemon, stopped by shutdown/server_close/join(5) (fixtures hubspot, model, fakes: a join timeout there does not raise).
Possible ERROR (fixture error, not assertion): tests/conftest.py:84-93 autouse `_stuck_servers_fail_the_test` raises ServerDidNotStop at teardown when a desk server does not stop within 2 x REQUEST_TIMEOUT_SECONDS (tests/support.py:490 stop_within). That affects only the 2 desk tests using `env` (test_the_desks_early_replies..., test_the_desks_busy_reply...). The ids in the old log mapping (hubspot/fakes) use fixtures that cannot raise this, which fits "the mapping is unreliable". The busy-reply test sets MAX_HANDLER_THREADS=1 and holds a stalled socket; stop() joins the thread for REQUEST_TIMEOUT_SECONDS. Most plausible ERROR source under heavy load, but not reproduced.
Timing assumptions (would give FAILURE, not error): PAUSE 0.3 s sleeps; `early_answer` treats 0.3 s without bytes as "no early answer" (a slow server gives a false pass); `late_body` recv timeout 2 s (slower answer counts as reset); busy-reply test assumes the stalled connection owns the only handler thread after 0.3 s (under load the second connection could win it and the 503 expectation fails).
