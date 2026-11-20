# INTEGRATION DRY-RUN 2 (core-b, then core-a, then core-c; handover/ excluded)

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
