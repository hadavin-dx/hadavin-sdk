# Mutation round e4b (EVIDENCE RUNNER: run and record, no judgement)

Clone: /tmp/mut2-work (from /tmp/d-tree, HEAD f1ba4ad972b115c4c279928d4483233be35fd92a). Helper: /tmp/work/run-un.sh, flags -x -q -p no:cacheprovider, timeout 100 s. Raw logs: /tmp/work/d/e4b-logs/row<N>.log. Driver: /tmp/work/d/e4b-mut.sh.
Studio folder (bible, handoff) does not exist in this container: no R-numbers cited.
Python in the venv: 3.12.3.

| row | mutation (exact one-line diff) | command | result | restored |
|---|---|---|---|---|
| 1 | desk.py `_give_back`: `-keep_age = int(last_error in BUSY_ERRORS)` / `+keep_age = 0` | `run-un.sh -x tests/test_hung_adapter_calls.py::test_busy_give_back_keeps_the_age` | FAILED: `assert ('pending','...',1700000050) == ('pending','...',1700000000)` (updated_at moved 50 s). A first attempt that edited the SQL text instead failed with a sqlite binding-count error (wrong reason), so it was discarded and redone as above. | yes (status clean) |
| 2 | desk.py `hung_workers()`: `-return dict(self._abandoned)` / `+return {("crmx" if k == "crm" else k): v for k, v in self._abandoned.items()}` | `run-un.sh -x tests/test_hung_adapter_calls.py::test_hung_workers_are_counted` | FAILED: dict comparison, "Left contains 1 more item: {'crmx': 1}" | yes |
| 3 | desk.py startup step 3: `-if not self._background:` / `+if True:` | `run-un.sh -x tests/test_desk_http_edge_cases.py::test_startup_50_pending` (run twice) | FAILED both times: `startup() took 15.5 s with 50 pending follow-ups` / `assert 15.465 < 5.0`; repeat: 15.4 s. Same value both runs (50 x 0.3 s sender delay), so not a flake. Note the failure is a time assertion, not a count assertion. | yes |
| 4 | desk.py: `-self.hooks.crash_point("D2", None)` / `+pass` | `run-un.sh -x tests/test_flow.py::test_crash_resume_each_point` | FAILED: `Failed: DID NOT RAISE SimulatedCrash` at `test_crash_resume_each_point[D2-keyed-keyed]` (1 failed, 16 passed before -x stopped). Only the D2 point was mutated. | yes |
| 5 | crm_hubspot.py `_request`: `-with _OPENER.open(req, timeout=left) as r:` / `+with urllib.request.urlopen(req, timeout=left) as r:` | `run-un.sh -x tests/test_crm_hubspot.py::test_a_redirect_to_another_host_is_never_followed_and_the_key_never_leaves` | FAILED: `assert other.calls == [] ...` Left contains `('GET', '/crm/v3/objects/contacts')` (the other host received a request). The redirect rule lives in `adapters._OPENER`; the mutation bypasses it from crm_hubspot.py. | yes |
| 6 | desk.py `_process` (~line 1353): `-except (RecursionError, TypeError, ValueError, OverflowError):` / `+except (TypeError, ValueError, OverflowError):` | `run-un.sh -x tests/test_input_edge_cases.py::test_deeply_nested_json_is_bad_envelope` | PASSED = NOT CAUGHT (1 passed). | yes |
| 6x (extra, same test) | server.py line 971: `-except (ValueError, RecursionError):` / `+except ValueError:` | same test | PASSED = NOT CAUGHT (1 passed). | yes |
| 7 | server.py `_take_slot`: `-victim = next((s for s in self._slots if s.reading and s.last_progress <= idle_before), None)` / `+victim = next((s for s in self._slots if s.reading), None)` | `run-un.sh -x tests/test_stall_eviction.py::test_dripping_crowd_is_not_evicted_live` | FAILED: `assert (200, {...}) == (503, {'error': 'busy','reason': 'busy'})` (a steadily sending client was evicted). | yes |
| 8 | run_real_check.py end of main: `-return 0 if result["ok"] and not left else EXIT_FAILED` / `+return EXIT_FAILED` | `run-un.sh -x tests/test_real_check_dry.py::test_dry_fakes_run_end_to_end` | FAILED: `assert code == 0, out[-3000:]` (the printed script output follows the assertion). | yes |

Notes
- Row 6, what the test asserts instead: it posts a body with `"payload":` followed by 5000 nested `[`. On this Python (3.12.3) `json.loads` parses depth 5000 without raising RecursionError (checked directly: "parsed ok"). The payload is then a list, and the server rejects it with 400 bad_envelope because the payload is not an object. So the test gets its 400 from that check, and neither RecursionError handler (desk.py `_process`, server.py 971) is reached. The docs cite this test as proof of the depth guard; it does not exercise it. Nothing was changed in the repo to fix this (runner does not judge).
- Row 7: the brief's grep ("steadily|early") found no matching test name in tests/test_stall_eviction.py. I used `test_dripping_crowd_is_not_evicted_live` (connections sending a byte every 0.1 s are not evicted). I did not mutate the `EVICT_MIN_IDLE_SECONDS` constant, because the test sets it itself by monkeypatch; I mutated the idle test in server.py instead.
- Row 4 mutated one hook point (D2) only; the other 4 points and the hooks module were not mutated.
- Row 3: the test's time limit was 5 s; the mutated start-up took about 15.4 s.
- Not checked: no lint, no whole-file runs, no other points or siblings, no unmutated baseline run of each test in this round.
- Cleanup: `git status` clean after every row and at the end; all __pycache__ directories deleted from /tmp/mut2-work. No processes of mine left running (the pytest processes visible in pgrep belong to the other suites; not touched).

Counts: caught 7 (rows 1, 2, 3, 4, 5, 7, 8), not caught 1 (row 6; the extra 6x also not caught), skipped 0.
