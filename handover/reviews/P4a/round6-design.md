# P4a rev 6 plan review, round 6, design (egm-design, sonnet)
Verdict: not clean. 0 Blockers, 4 Majors, 8 Nits. Read-only reviewer; ran nothing. Round-5 fixes SG-T11 allowlist, retry counter fail-closed, migration 0008 mechanics hold; FailureBooked fix and merge-order paragraph each introduce a defect.

MAJOR
- M1. FB-4 (usage zero/negative/bool/string, reply returned, h.record(None, measured=False)) has no exception, yet P4a ~662 builds FailureBooked(error_class=type(exc).__name__) and "re-raises the same exception" for FB-2/3/4, and ~630 asserts an alert for FB-T4. Pick: FB-4 sends no alert (say so, as FB-1d), or sends the event with a closed error_class such as "UnusableUsage", returns the reply, FB-T4 asserts that. Add a mutant.
- M2. Garbage unknown_attempts: FB-T9 books exactly R; P4b1.md:268 (_unknown_attempts clamp) and :282 (R4d-2 garbage = answered + max x W) say otherwise; BN-35 (531) supersedes only part. Name 268's clamp helper and 282's garbage clause as superseded by FB-9/FB-T9 (not proven => max(R, answered)), or delete the garbage sub-row from R4d-2.
- M3. SG-T11 rules (a')/(b') still bypassed by: importlib.import_module with concatenated/f-string/variable arg; reading TABLE[...].factory elsewhere; `from ... import make as m`; `import factory as f; f.make`; getattr(factory,"make"). Add a third allowlist rule: outside backends/factory.py, actions/executor.py, tools.py (executor.py:37, tools.py:365, factory.py:39) import_module/__import__ are not called; `.factory` of a table entry read only in factory.py; alias forms of make count as make. Add self-tests and mutants.
- M4. The "ONE list" merge order (P4a ~610) omits line-213 prerequisites (P1m, P3a, five P4d PRs incl. P4d-c). Then the "if P4b1-a merges first" branch in FB-6 is dead, P3a-2 allow-list entry (ORDER 186 G73-2(c)) becomes mandatory, "0008 is fixed" is false (P3a/P4d-c may add migrations), and FB-T6b hard-codes the 0008 name. Put the full dependency list in the one list, derive the file name from the real file list in the test, remove the dead branch.

NITS
- N1. No sub-row asserts failure_booked spy has 0 calls for FB-1 causes / no mutant "alert fires on a refusal"; wrapper try must separate reserve failure (no h) from body failure; KeyboardInterrupt during reserve.
- N2. SG-M17 wording is revision-5 text; SG-T11 self-test has six plants (resolve said five); no self-test for relative import, `from pkg import module`, __import__, `:name` suffix, `.environment` on a fake.
- N3. Move SDK-retry-off pin (anthropic max_retries 0, bedrock total_max_attempts 1) from P4b1-b FB-T2 to FB-T9b (counter built in P4a-2).
- N4. 0008 changes a trigger function: mark non-revertible in rollback line; old code on migrated DB fails loudly (migrate.py:320-326), write it down and test.
- N5. P4b1.md:106 ("one real settle correct an expired row once, either direction") conflicts with FB-6 refusing a lower settle; BN-35 does not supersede it.
- N6. After P4b2-a sweep, a healthy slow call can be expired (tick.py:109 bound exceeds orphan_age_s ~605 s at max_attempts 10, call_timeout_s 60); FB-6 books R (safe side). State in "What this costs".
- N7. SG-T7 tests NetworkLLM refusal in pilot only; line 690 silent on demo stage.
- N8. FB-T6b: say the check asserts session_replication_role='origin'.

VERIFIED: retry counter fail-closed (callers, with_retry tests keep working, Reply model_copy), migration mechanics (migrate returns stems, _migration_files seam), arithmetic (W 27,360, R 164,160; 30 failures = US$4.9248; counts 15 causes/17 rows/35 mutants), _STUCK allowlist two release calls, make takes **available.
NOT CHECKED: 78/79 files not on this branch (meter.py, limits.py, metered.py, migrations 0006/0007, late_files, k1b/loop.py), P4a lines 1-605 beyond 3 and 213 (BN-19 list unchecked), P4b1 body outside 1-126/256-283/531, P3a-2 mechanism, git facts; nothing run.
