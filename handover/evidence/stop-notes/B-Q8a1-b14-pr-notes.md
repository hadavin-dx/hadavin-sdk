# Q8a-1 batch 14: PR notes (builder). Security path, no round cap.

Base 918c0345, branch core/q8a1-b14, pushed to wip/cloud-q8a1-b14 (plain push). No spend, no live call.

## What is NOT verified by the builder (lead / evidence runner own these)
- EGM result review: not run (lead).
- Independent evidence runner: not run (lead).
- Four guard reasons are still UNCHECKED by code: CARD, STOREID, URL, REDACTED. Next steps are in the comment above `UNCHECKED` in tests/test_guard_reasons.py. REDACTED waits for the owner (q-q8a1-hide-ids: may an error reason be shown).
- The guard cannot see: an appended dict, tuple or call result that is only returned and never reaches text in the tree; `PROC` and `PKGERR` checks are bounded to the function or handler; `_shown_host` shows any dotted token; a model id cut into short pieces by separators passes.
- `raise ... from None` inside an `except` hides the old error from printed tracebacks but `__context__` stays set (errors.py states this). The class-only helpers (`call_class_only`) raise after the block and leave neither.
- Executor `http_{int(status)}` has no fix mutant (no test in b14 file targets it); it is a hardening, not a leak.
- signer_vault `status_text`: hardening, not a real leak (corrects the earlier wording).
- Known flake test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in not touched.

## Fail-before (918c0345 detached worktree, only new tests copied in)
- tests/test_q8a1_b14_fixes.py: 22 failed, 88 passed (the 88 are regression pins for behaviour that held already). Log: /home/user/build/checkpoints/B-Q8a1-b14-failbefore-a.log
- guard tests (test_guard_reasons.py, test_stage_names.py with the new _text_guard.py and _guard_allowances.py): 3 failed, 516 passed: BUNDLE, HOST reason checks and test_no_config_derived_name_is_put_in_a_message_outside_the_one_filter. Log: ...failbefore-b.log
- Mutants: Z65-Z83 reason checks, Z84-Z89 guard branches, Z90-Z98 fixes (one per fix), see tests/stage_mutants.py.

## 54 `noqa: BLE001` handlers in src (not 45)
Per-site list printed by /tmp/claude-0/ble.py. 46 print the class only or fixed text. Those that use the error beyond its class: audit/chain.py:532 `is_connectivity_error(exc)`; cli.py:395 and :408 `_kill_switch_store_down`; guard/http.py:131, k1b/loop.py:95, tools.py:1146 (stored in a box, re-raised by the caller); runtime/agent_loop.py:312 and tools.py:1224 `error_reason` (the REDACTED owner question); sources/kubernetes.py:205 `getattr(exc, "too_large")`.

## Tests by issue (tests/test_q8a1_b14_fixes.py unless named)
1 injection and Bedrock class-only logging, no cause/context. 2 tick: AST no broad handler, no suppression comment, `# why:` above each swallow site, library errors of azure/google/hvac/botocore (and a subclass) withheld, CAS-loser debug line. 5 sslmode from the DSN. 8 `_DETAIL`, `_shown_host`, vault text status, `status_text` int subclass, strict-model unknown keys, bundle folder name, model id pattern. 3 and 4 reason checks in tests/test_guard_reasons.py (44 checked). 6 guard: tests/test_stage_names.py (R14b to R14f planted faults, two clean forms, resolution by real definition).

## Gates on the final head (command and result)
- ruff check: all passed. ruff format --check src tests demos tools: 329 files already formatted. bandit -ll -r src: rc 0, 0 issues. tools/scan_repo.py: rc 0.
- gitleaks: NOT RUN (binary is not installed on this box).
- Full tests/stage_mutants.py at the final head: 281 mutants, 281 good (one run gave 280 of 281; the one SNIPPET NOT FOUND, Z89, was a format change of the guard file and was re-run alone: KILLED).
- Full pytest (own Postgres 16 on port 56414, `-m "not live and not perf"`), 294 s: 11379 passed, 1 skipped, 2 failed.
  - tests/test_k5_round5.py::test_r1_hold_run_ids_is_wired_by_build_and_a_raising_hook_halts_purging: a real consequence of Issue 2 (a plain RuntimeError is no longer shown by the tick). Test updated to expect the class and no text; file re-run: 78 passed.
  - tests/demo_askdata/test_validate_harm.py::...[dblink-connect]: fails the same way on base 918c0345 (the database server cannot reach its default socket in this box); not caused by this change, not fixed here.
  - The full run was made before the one-line update of test_k5_round5.py; the changed file and the three guard/b14 files were re-run alone (all green). The full suite was NOT re-run after that edit.
