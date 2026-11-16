# claims-B (lane B)
(Saved by the session: the builder's Write of this file was refused by the harness, so this is the builder's returned report extracted VERBATIM by script from its transcript, not edited. Verdicts are the builder's proposals; not yet spot-checked by a reviewer. Audited sha b4cce5b.)

## claims-B (not saved to disk; status SUPPORTED, UNSUPPORTED or UNVERIFIED). Format: claim | file:line | code | test and what its body asserts | status.
1. "Concurrent ticks are safe: every state change is a compare-and-set, and a loser skips." | tick.py:22 | tick.py:57-70, runs.py:36-39, postgres.py:257-268 | tests/test_p7_tick.py:150 asserts SUCCEEDED, one external create, and codes [0,0] | SUPPORTED for state and side effect; the audit still gets a second intent (B-03).
2. "A failed re-probe switches off every tool that names the source until a probe passes." | README.md:35 | tick.py:221-240 (in-process set) | tests/test_k5_round9b.py:295-314 asserts the set on one object | UNVERIFIED across processes; B-01.
3. "An EXECUTING run is never re-executed (outcome_unknown)." | tick.py:116 | STUCK map, no execute call in tick stuck | tests/test_p7_tick.py:221 asserts the reason code | SUPPORTED.
4. "Gate decision once per run, a second raises StaleState." | store/protocol.py:57-60 | memory.py:109-112, postgres.py:299-303 (UniqueViolation) | tests/contracts/test_store.py (names it), test_p7_store.py:136 (append-only grants) | SUPPORTED by code; the Postgres test needs a database, not run.
5. "record_decision: both the decision and the request change, or neither." | protocol.py:62-69 | postgres.py:337-373 (transaction, Rollback) | tests/contracts/test_store.py:227 `test_record_decision_is_atomic` | SUPPORTED by code and test name; not run.
6. "A missing or unreadable kill switch row reads as ON." | protocol.py:107-108 | postgres.py:444-451 | tests/test_p7_store.py:166-171 asserts `on is True` and `by == "system:kill_switch_row_missing"` | SUPPORTED for a missing row. Memory store has no missing-row case. An unreadable (exception) case propagates and stops the run.
7. "The runtime role has no DELETE or TRUNCATE; only the purge role deletes evidence." | README.md:33 | migrate.py:62-65, 340-353 | tests/test_p2_postgres.py:173-192 asserts no DELETE or TRUNCATE on `runs`; test_k2_migrations.py:230 for audit | SUPPORTED for the grant; the same runtime role holds approval and kill-switch writes (B-06).
8. "migrate applies each file once under an advisory lock." | migrate.py:3-4 | migrate.py:314 | tests/test_p2_postgres.py:157 `test_two_concurrent_migrate_runs_apply_once` | SUPPORTED by name; not run.
9. "A tool call or redaction map older than 400 days is purged whatever any hold says." | tick.py:184-203 | tick.py:197-203 | tests/test_k5_review.py:511-514 | SUPPORTED by code; not run.
10. "Redaction map is never returned, written, sent to the audit sink or logged." | k1b/redaction.py:6-8 | redaction.py:172-195 | tests/test_k1b_redaction.py (names only) | UNVERIFIED (body not opened).
11. "If replay dies after the output folder exists, FAILED.txt is written." | k1b/replay.py:267-277 | replay.py:269-277 | tests/test_k1b_replay.py:473-482 asserts text starts "replay did not finish: RuntimeError" | SUPPORTED by test body; not run.
12. "A crash leaves a *.tmp, never a torn file." | k1b/atomic.py:1 | atomic.py:12-17 | tests/test_k1b_cli.py:207 only replaces the function | UNVERIFIED; B-15.
13. "K1b audit: write_intent before the side effect." | audit_sink.py:32 | replay.py:162 vs 260 | tests/test_k1b_replay.py (no ordering test) | UNSUPPORTED for replay; B-02.
14. "A chain over the memory store keeps events only until exit (warns)." | audit_sink.py:3-4 | audit_sink.py:72 | tests/test_k1b_cli.py (names only) | SUPPORTED by code.
15. "Tick external heartbeat is PENDING (K7): nothing sends it today." | tick.py:10-11 | none | none | SUPPORTED (self-stated gap); B-22.
16. "The regex value is never compiled into a pattern." | runtime/evidence.py:60-62 | evidence.py:81-109 | tests/test_k5_classes.py, test_k5_round10.py (names only) | SUPPORTED by code reading.
17. "Postgres store: compare-and-set holds across processes." | postgres.py:1-2 | postgres.py:262-268 `WHERE run_id = %s AND state = %s` | tests/contracts/kinds/store_postgres.py | SUPPORTED by code; not run.
18. "Runtime, approvals and llm never import platform_secrets." | backends/platform_secrets.py:5 | grep of src (lane A/C also) | tests/test_repo_rules.py:141 | UNVERIFIED (test body not opened).
19. "A torn qualified.jsonl line is skipped, not fatal." | agent_loop.py:107-115 | agent_loop.py:106-124 | tests/test_k1a_pass_k.py:144 | SUPPORTED by code; test not opened.
20. "Hosts list suggested egress; enforcement is network-level (S11)." | factory.py:109-115 | factory.py:112-115 | none | UNVERIFIED (S11 is outside this repo).

## Lessons for the checklist, preamble and plan
- The evidence runner's string-exclusion list should include every file with `"module:function"` strings (here `backends/table.py`).
- Check each docstring claim against README.md and CHANGELOG.md before filing; two of my first findings were already enforced (app.py:84-89).
- A test on an in-memory flag proves nothing across processes.
- `Write` of a findings file inside a lane was refused for me although the brief names it; the lane brief should say how findings travel when the tool refuses.

## Files written
- `/home/user/hadavin-sdk/handover/core-hardening/parts/checkpoint-B.md` (about 20 lines)
- `/home/user/hadavin-sdk/handover/core-hardening/parts/map-B.md` (about 130 lines)
- NOT written, content above: `findings-B.md`, `claims-B.md`, `walk-B.md`.

Head sha audited: b4cce5b (disk: 1c50990). Processes started: none.
