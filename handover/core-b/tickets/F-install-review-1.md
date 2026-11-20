# EGM review round 1 of 1: tickets/F-install.md (egm:egm-review-loop through the Skill tool; direct dispatch; model fable)
When: 2026-11-20 06:09 to 06:17 UTC. Reviewers: egm:egm-implementation-readiness = completed; egm:egm-codebase-details = completed. Nothing run by either. Read against core-c's gate copy (notes/core-c-model_gate-copy.md) and the built meter.
Round result: NOT CLEAN. Blockers 4 (one shared), Majors 19 (several shared), Nits 17. Verdict of both: not ready to build as written.
Resolution: ticket section "RESOLUTION of review round 1" (V1 to V12). Five of the answers are design decisions the lead must confirm before GO BUILD F-install: ESCALATIONS.md E3. No round 2 by order.

| id | severity | finding (short) | answered in |
|---|---|---|---|
| ir-1 / cb-B1 / cb-M7 | Blocker | the worst-case callable is not specified, does not match the gate's six-argument call (output_schema missing), and a route the registry does not hold (the judge double's route "screen") makes two "stay green" tests fail | V1 |
| ir-2 / cb-M8 / cb-N6 | Blocker | the in-memory Budget meter's refusal, its amount check, late settle and the whole evals path (how the cap arrives, what a cap hit does, the audit sink) are undefined | V2, V3 |
| cb-B2 / ir-10 | Blocker | every agent_loop.py line number is stale by 3 lines and my "CHECKED" line certified them; deleting by number would remove the wrong lines | V10 |
| ir-3 / cb-M6 | Major | the test plan (H1, H2, H5, E6, M5, invariants 3, 7, 9) still describes the gate before the update | V8 |
| ir-4 / cb-M1 | Major | gate audit rows in the replay sink break pinned tests (tests/test_k1b_replay.py:114-121, 444) | V3 |
| ir-5 / cb-M5 / cb-M12 | Major | consequences of "no settle on failure" not carried through: holds that never close in the Budget, forfeit before reserve, every provider error now books a worst case, duplicate failure rows | V4, V5 |
| ir-6 / cb-M2 | Major | the refusal mapping contradicts the loop's existing stop conventions (kill switch is STOPPED with no card today) | V6 |
| ir-7 / cb-M3 | Major | no final code for the helper and wrap callables; a BoundGate in rt.llm or a closure fault strands the run in WORKING | V6, V7 |
| cb-M4 | Major | a meter refusal inside a judge call is swallowed by injection_check as an injection flag (wrong end state in the run, a false warning on the card, wrong counts in replay, a false red judge in evals) | V7 |
| ir-8 | Major | open questions the material already answers (replay has no map object; acknowledge flag in pilot and prod) | V9 |
| ir-9 | Major | no exact file list | V11 |
| cb-M9 | Major | day spend and run cost diverge for unsettled holds; a reply with unusable cost never counts toward the run cap | V5 |
| cb-M10 | Major | the gate module and runmap.enforce_map are not in the tree; commit ids differ | V12 |
| cb-M11 | Major | the landed producers text says the gate refuses unmasked input (false after the lead's decision) | fixed now, commit "code F: producers text" |
| nits | Nit | stale cli.py and app.py numbers; extract fixtures (three recorded files, regenerate with tests.fixtures.record); exact usd strings; message-list aliasing; name clash limits.Budget against registry.Budget; renamed test; docstrings | V10, V11, V12 |
Verified correct by the reviewers: the list of .chat( call sites and charge sites is complete; no double charge remains if all listed lines go; the run loop holds ONE live run-map object (agent_loop.py:400) that can be passed by reference; every test double accepts the gate's call; the meter facts match the built limits.py.
