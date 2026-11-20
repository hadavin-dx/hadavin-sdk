# INTEGRATION DRY-RUNS 2 and 3 (core-b, then core-a, then core-c; handover/ excluded)

CURRENT = "Dry-run 3" at the bottom (16:39-17:00 UTC, newest heads, PG16 on 127.0.0.1:55433, results with a real database). The "Dry-run 2" text between here and there is HISTORY: its heads, its conflict list, its 22535 count and its "PG not run / UNKNOWN" lines are superseded by dry-run 3.

# Dry-run 2 (history, superseded)

Scratch only: worktree /home/user/wt/integ, branch scratch/core-a-integration-dryrun-2 (never pushed). Nothing in any other worktree was touched.

## Heads used
core-b 463760813 (base) | core-a d1ee703ab | core-c bd7f9d978. Result commits: 283e1513f (merge core-a) and 6c89f0495 (merge core-c).

## Commands
```
cd /home/user/hadavin-sdk && git fetch -q origin && git worktree add --detach /home/user/wt/integ origin/cloud/core-b
cd /home/user/wt/integ && git checkout -q -b scratch/core-a-integration-dryrun-2
git merge --no-commit --no-ff origin/cloud/core-a      # 1 conflict, resolved below
git reset -q HEAD -- handover; git clean -fdq handover; git checkout -- handover   # no handover conflict markers appeared; 388 handover adds dropped
git commit -m "merge core-a (handover excluded)"
git merge --no-commit --no-ff origin/cloud/core-c      # 5 conflicts, resolved below
(same handover exclusion) ; git commit -m "merge core-c (handover excluded)"
uv sync --all-extras --group test ; ruff check src tests ; import hadavin_sdk ; pytest --co
```

## Step 1: merge core-a (1 conflicted file)
| File | Hunks | Sides | Resolution and why |
|---|---|---|---|
| tests/contracts/test_t1_reserve_cap.py (add/add, whole-file) | 2 | core-b 9e18334bf/41766094d (F-store T1, by a different agent, uses tests.test_stop_state_roles.World); core-a 1dec59fd3 and earlier (original T1, own fixtures) | Kept BOTH, no test dropped: core-b's file stays at this path, core-a's saved as tests/contracts/test_t1_reserve_cap_core_a.py. The two files share no helper names that matter (module-local fixtures). |

The lead-expected conflicts in CHANGELOG, defaults.py, producers.py, conftest.py did NOT occur against core-a (core-a does not touch them any more than main).

## Step 2: merge core-c (5 conflicted files)
| File | Hunks | Sides | Resolution and why |
|---|---|---|---|
| CHANGELOG.md | 1 | core-b bf093e1f4/3ceb20b63 (money block, upgrade steps) vs core-c d927df43d/d2f41b882 (textnorm, G items) | Kept both, core-b text first, core-c entries after. Pure additions; checked headings are unique. |
| src/hadavin_sdk/defaults.py | 1 | core-b ca1dc459e/14eeb5099 (TRIGGER_*, reservation, audit, money_context) vs core-c 1a0965361/fd1fb3e31 (TEXTNORM_*, G constants) | Kept both. Script check: no duplicate constant or function name after the merge. |
| src/hadavin_sdk/guard/producers.py | 1 | core-b cf2d7d006 (wording "replaces values the map holds") vs core-c aa7c5fa27 (wording "runmap.enforce_map") | Took core-c's wording: it is a description string for guard/model_gate.py, a file that only core-c has; the dict key and the set of registered callers are identical on both sides, so no check is lost. |
| tests/conftest.py | 1 | core-b 2af514d4c/969a35d16 (autouse fixtures `_migrate_takes_the_server_gate`, `_seed_caps_before_reserve`) vs core-c 939d2b38e (autouse `_pilot_builds_on_an_interpreter_with_other_unicode_data`) | Kept all three fixtures (independent autouse fixtures). |
| tests/contracts/test_t1_reserve_cap.py (add/add) | 2 | core-b version; core-c version (the "two writers" rewrite of core-a's file) | core-b's stays at the path; core-c's saved as test_t1_reserve_cap_core_c.py. Now three T1 files. |

DECISION NEEDED: the three T1 files overlap in purpose. Lead should pick one canonical file and delete or merge the others (kept all three here only because dropping a test is not mine to decide). Also core-a's and core-c's T1 variants and tests/test_grants_negative_0007.py / test_grants_negative_roles.py call migrate() without `reset_role`/`no_roles`; core-b's migrate refuses a plain migrate. They are PG-only and could not be run here (see below): expect failures there, to be adapted by their owners.

## Collection / imports
ruff check src tests: All checks passed. `import hadavin_sdk`: ok. Collection of the whole tree: 22535 tests collected, ZERO collection errors, no "cannot import name". No duplicate-basename problem (the extra T1 files have distinct names).

## Targeted runs (final tree)
- tests/test_mutants_anchors.py + tests/test_mutation_runner_exit.py (HADAVIN_REQUIRE_PG=1): 130 passed. (tests/test_mutation_runner*.py: only _exit exists.)
- tests/triggers with strict PG: NOT RUN TO COMPLETION. No PostgreSQL server is running in this box (pg_isready: no response; HADAVIN_TEST_PG_DSN unset; binaries exist under /usr/lib/postgresql/16 but I did not start a server on the shared box). The strict file test_t5_strict_mode.py gives 2 skipped without a DSN. A full tests/triggers run with -n 2 did not finish in the time available (stopped). So the "10 by-design core-b tests now pass" count is UNKNOWN: please run it with a DSN.
- Signature check: migrate() = core-b's signature (reset_role, release_role, no_roles, accept_changed_draft, reset_draft); core-a and core-c trees have the old 7-argument one; Limits.reserve(agent_id, worst_usd, *, run_id) and settle(reservation_id, actual_usd, *, agent_id) are core-b only (core-a/core-c have no Limits.reserve/settle); RedactionResult exists in core-a/core-b at redact.py:842 and core-c at :1082 (core-c's merged cleanly, a superset); bind(..., mapping=) required keyword exists only in core-c's model_gate.py and tests/test_gate_install_callers.py enforces it; Runner(max_running=) / make_app are core-a(E)-side triggers code and no call site fails at import/collection. No TypeError at import or collection anywhere; run-time TypeErrors in PG-only tests not excluded (see above).

## Final tree vs core-b (names only)
168 files differ (142 added, 26 modified, 0 under handover/); list in the scratchpad file /tmp/claude-0/-home-user/ea49ef2e-0676-59dd-b1e0-cd86ea69f123/scratchpad/files.txt. Modified: .gitattributes, .github/workflows/ci.yml, CHANGELOG.md, README.md, pyproject.toml, uv.lock, app.py, approvals/{channel,gate,slack_channel}.py, config.py, defaults.py, guard/{injection,producers,redact,runmap}.py, runtime/{agent_loop,evidence}.py, tools.py, tests/conftest.py, tests/{test_k5_producers,test_k5_round12_fuzz,test_k5_round9,test_no_hardcoded_values,test_stage_names}.py, tests/warden_port/test_redaction.py. Added: core-a's n8n/, src/hadavin_sdk/triggers/, testing/crash.py, tests/triggers/*, tests/test_trigger_config.py etc., and core-c's guard/model_gate.py, textnorm and warden_port tests.

## Versus TRIAL-INTEGRATION.md
GONE: the 7 hand-resolved conflict hunks in core-c's own files (redact.py etc.) and the defaults.py trial conflict: core-b and core-c now merge with only the five textual conflicts above, none in redact.py. The old need to take pyproject/THIRD-PARTY-NOTICES by hand is gone (they merge cleanly). The "no combined tree of the new heads" gap is closed (this is one). NEW: test_t1 add/add in three versions; CHANGELOG/defaults/producers/conftest are now conflicts (they were not in the trial). STILL OPEN: whole-suite not run here; PG-dependent results unknown; gate not yet installed in Runtime.

## Resolution plan for the lead (replayable)
1. Branch from origin/cloud/core-b. 2. `git merge --no-commit --no-ff origin/cloud/core-a`; drop handover (reset/clean/checkout); resolve test_t1_reserve_cap.py by keeping core-b's at the path and core-a's as *_core_a.py; commit. 3. Same for core-c: CHANGELOG and defaults.py keep both sides (core-b first); producers.py take core-c's model_gate line; conftest.py keep all fixtures; T1 as *_core_c.py; commit. 4. uv sync, ruff, import, `pytest --co` (expect 22535 collected, 0 errors). 5. DECISION: choose one canonical T1 file. 6. With a PG DSN: run tests/triggers (strict), tests/test_grants_negative_*.py and the three T1 files; update migrate() calls in core-a/core-c PG tests to name reset_role or pass no_roles. 7. Whole suite.

---

# Dry-run 3 (16:39 UTC, current)

Scratch worktree /home/user/wt/integ3, branch scratch/core-a-integration-dryrun-3 (never pushed). Logs: handover/core-a/raw/integ3-*.log.

## Heads
core-b 3f4ebb67e (base) | core-a bc6b400cb | core-c d53d6e7d1. Fix branches: wip/core-a-contract-fix c545aaef1, wip/core-a-t1-merge e4b0c2331, wip/core-a-door-merged 435ca8500, wip/core-a-for-grant-tests 3ffb442f1.
Commits on the scratch branch: 3abf1a2a4 merge core-a | aeafa47df merge core-c | c593cd3ab contract-fix | 1e7d2f001 t1-merge | 04cf264a0 door-merged | e1708eccd for-grant-tests | c47b08bec revert of door-merged crash_launcher.py (see below). handover/ excluded at both merges (nothing of handover committed).

## Step 1: merge core-a (1 conflict)
| File | Hunks | Resolution |
|---|---|---|
| tests/contracts/test_t1_reserve_cap.py (add/add) | 2 | core-b's version kept at the path. core-a's file holds 10 cases core-b lacks (fifty_stores_are_fifty_backends, settles_racing_the_expiry_sweep, the_cap_holds_when_the_login_defaults_to_repeatable_read, portal/reset/runtime/purge role grants, fifty_connections_settling_one_reservation, control_old_check_then_add, ...), so core-a's saved as test_t1_reserve_cap_core_a.py. (Core-b did port part of them but not these.) |

## Step 2: merge core-c (7 conflicted files; two are new since dry-run 2: README.md, SECURITY.md)
| File | Hunks | Resolution |
|---|---|---|
| CHANGELOG.md | 5 | Hunk 1: core-b's "Money status" block and all its Breaking items kept; core-c's intro paragraph (labels TESTED/MEASURED...) put on top; core-c's reworded "first stage is called demo" item (with sub-bullets) replaces core-b's one-line copy of the same item; core-c's "### Breaking changes" heading and its sentence dropped (the item now sits under core-b's "### Upgrade steps"). Hunks 2-5 (core-c renamed "K5-core" to "Read-only evidence" and split bullets; core-b renumbered the evidence migration 0006 to 0005 and rewrote 2 sentences): core-c's wording kept, `0006_evidence` replaced by `0005_evidence` everywhere, core-b's two rewritten sentences ("No ledger row needs renaming", "stop-state migration is 0006") used instead of core-c's stale ones. |
| README.md | 2 | "Limits and trust": core-c's restructured text taken; core-b's added stop-switch sentence (reset role, INSERT kill_switch_stops) and the narrowed Waiver put back as two sub-bullets under "Database roles". Last block: core-b's audit tamper-evidence sentence + core-c's Kubernetes sentence. |
| SECURITY.md | 2 | core-c restructured the file into "1. / 2.x / Words used here". Kept core-c's structure whole and added core-b's two sections intact: "## 0. What the core does and does not guarantee in pilot and prod" (before section 1) and "## 3. Spend limits (stated limits)" (end of file). DECISION NEEDED: section 0 / 3 overlap with core-c's 2.2 Spending cap, 2.3 Stop switch, 2.4 Audit record; someone must merge them by topic and renumber (no statement of either side was dropped here). |
| src/hadavin_sdk/defaults.py | 1 | both sides kept (core-b constants, then core-c TEXTNORM_*); no duplicate top-level name. |
| src/hadavin_sdk/guard/producers.py | 1 | core-c's wording ("runmap.enforce_map") for guard/model_gate.py; same dict key, no caller dropped. |
| tests/conftest.py | 1 | both sides kept (core-b autouse fixtures and core-c `_pilot_builds_on_an_interpreter_with_other_unicode_data`); no duplicate name. |
| tests/contracts/test_t1_reserve_cap.py (add/add) | 2 | core-b's at the path; core-c's saved as test_t1_reserve_cap_core_c.py (19 case names core-b lacks). |

## Fix branches applied on top
- wip/core-a-contract-fix: applied clean (tests/contracts/test_meter.py, test_store_spend_reservations.py; files identical to core-a's before, so it is a plain update).
- wip/core-a-t1-merge: core-b's T1 lacks 14 of its cases, so applied: its T1 file replaces the core-a copy (test_t1_reserve_cap_core_a.py).
- wip/core-a-door-merged: the two crash matrix files are identical to cloud/core-a (nothing to apply: door-merged-support.patch is already in). crash_launcher.py differs by one line (it drops `"conflict_events_per_minute": 10`). DOES NOT WORK on this tree: core-b's TriggerSettings requires that key; with it removed 455 failed + 15 errors in tests/triggers ("triggers.conflict_events_per_minute missing: core-b TriggerSettings required", log integ3-triggers-run1-with-door-merged-launcher.log). Reverted in c47b08bec. DECISION/OWNER core-a: the branch's launcher must keep the key (or the code side must stop requiring it).
- wip/core-a-for-grant-tests: applied clean (tests/test_grants_negative_roles.py); passes.

## Checks on the final tree (c47b08bec)
uv sync ok; ruff check src tests: All checks passed; import hadavin_sdk: ok; `pytest --co -q`: 22629 tests collected, ZERO collection errors (no name or import mismatch).

## Test results (PG16, HADAVIN_REQUIRE_PG=1)
1. tests/contracts (-n 2): 1623 passed, 21 failed, 3 skipped, 1 xfailed (4m13s).
2. tests/triggers (-n 3): 1379 passed, 4 skipped, 0 failed (3m17s) (the by-design core-b tests now run against PG and pass).
3. test_grants_negative_roles + test_grants_negative_0007 + test_mutants_anchors + test_mutation_runner_exit (-n 2): 308 passed, 11 failed (37 s); all 11 in test_grants_negative_0007.py.

## Remaining failures
| Test(s) | First error | Owner |
|---|---|---|
| tests/contracts/test_t1_reserve_cap_core_c.py, 19 ids (fifty_connections_against_a_cap_of_three[day,month], exactly_floor_of_cap_over_worst[5], month_cap_...two_days, fifty_first_connection..., fifty_connections_settle_one_reservation..., settle_above/zero/after_expiry, settles_below_the_reserve..., expired_reservations_stay_booked, fifty_sweeps_at_once, settle_racing_the_sweep, runtime_role_may_not_delete, purge_role_deletes_closed_rows...) | `TypeError: PostgresStore.settle_spend() missing 1 required keyword-only argument: 'agent_id'` (settle calls without agent_id) and `psycopg.errors.InsufficientPrivilege: permission denied for table spend_reservations` (direct SQL on the table under the runtime login; core-b revoked direct table rights) | core-c (port to core-b's settle_spend(..., agent_id=) and to the definer functions, or retire the file after folding its unique cases into core-b's T1) |
| tests/contracts/test_model_gate_contract.py::test_point4_a_failed_or_timed_out_call_is_not_settled_and_its_error_passes_unchanged[store-style-mark-on-used-up-retries] and [memory-style-...] | `AssertionError: a call of unknown cost was settled: the worst case is released` (the gate's store-style settle raises the same TypeError about agent_id) | core-c (gate must pass agent_id= to settle_spend) |
| tests/test_grants_negative_0007.py, 11 ids (identities_are_the_four_this_file_knows, grant_row_gives_each_role..[purge,runtime], grant_row_is_a_table_with_two_purge_columns, nobody_may_truncate..., pg_each_role_is_refused...[purge,runtime], pg_column_rights...[purge], pg_catalog_agrees..., pg_purge_role_deletes_by_status..., pg_store_methods_are_refused...) | `AssertionError: assert {'portal',...,'runtime'} == {...}` extra 'release' role; privilege sets come back `set()` vs {'INSERT','SELECT','UPDATE'} (core-b no longer grants the table rights directly) | core-a (update to core-b's role set incl. release role and function-based access) |
| tests/triggers: none with core-a's original crash_launcher.py | | core-a: door-merged launcher change is the only incompatibility |

## Replay plan for the lead (ordered)
1. Branch from origin/cloud/core-b (3f4ebb67e). 2. `git merge --no-commit --no-ff origin/cloud/core-a`; drop handover; keep core-b's test_t1_reserve_cap.py, save core-a's as test_t1_reserve_cap_core_a.py; commit. 3. Merge core-c the same way: resolve CHANGELOG/README/SECURITY/defaults/producers/conftest as in the table above (script: take core-c text, apply core-b's 0005 renumber and its stop-switch/audit/spend sentences; SECURITY keeps core-c structure + core-b sections 0 and 3); save core-c's T1 as *_core_c.py; commit. 4. Replace test_t1_reserve_cap_core_a.py by wip/core-a-t1-merge's T1 file; `git checkout origin/wip/core-a-contract-fix -- tests/contracts/test_meter.py tests/contracts/test_store_spend_reservations.py`; `git checkout origin/wip/core-a-for-grant-tests -- tests/test_grants_negative_roles.py`; do NOT take door-merged's crash_launcher.py (core-a must restore the conflict_events_per_minute key first). 5. uv sync, ruff, import, `pytest --co` (expect 22629, 0 errors). 6. Owners fix the remaining failures above (core-c: T1_core_c + model_gate settle agent_id; core-a: test_grants_negative_0007 role set and launcher key). 7. DECISION: one canonical T1 file (three variants: core-b, _core_a, _core_c) and a topic merge of SECURITY sections 0/3 with 2.2-2.4. 8. Whole suite (not run here).
