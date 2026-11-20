# TRIAL INTEGRATION of core-b, core-c and core-a on main (ORDER 014 item 1)

Written by the trial integrator of core-a, 2026-11-20. Nothing was fixed in anyone's code and nothing was pushed.
The combined tree exists only in a scratch folder (section 2). Words used: "combined tree" = main plus the code of
all three sessions; "old heads" = the branch heads this tree was built from; "new heads" = what the sessions pushed
while the trial ran. S = `/tmp/claude-0/-home-user/ea49ef2e-0676-59dd-b1e0-cd86ea69f123/scratchpad`.

## 1. What was NOT done or not run (read this first)
- **The whole suite ran on the OLD heads only** (core-b 44d691b24, core-c c73b55238). While the trial ran, core-b
  pushed 6 more code commits (now f390b7d6e: trigger-config fix round 1, F-store fix round 1, the
  refused-before-response mark, more stop-state tests) and core-c pushed 2 (now 93f7f24e4). ONE whole-suite run was
  allowed, so the new heads got only targeted checks: our four contract files and the worker start, on a tree
  "core-b f390b7d6e + core-a files" (no core-c). **No combined tree of the new heads was built or run.**
- core-c's new head 93f7f24e4 was not combined at all (read with git only: it fixes failure 15 of section 6 and
  changes `guard/redact.py` again, so the conflicts of section 3 will come back in the same places).
- The combined tree holds MY trial resolutions of 9 conflict hunks in core-c's own files (section 3). They made the
  tree run; they are not reviewed and are not a proposal for the final text.
- Not run: tests marked `live` and `perf` (deselected, 70 tests), any mutant script, PostgreSQL 17 (CI uses 17.10;
  this run used 16.15), the demos, the n8n template against a real n8n, a live model call.
- The gate is not installed in `Runtime` on any branch (step F install is not built), so "gate works with core-b's
  meter" was checked by a direct probe and by the contract tests, not through a real run.
- `handover/` was never brought in, so one core-c test that reads a handover file still skips
  (tests/test_model_gate.py:702).
- The skip list of the whole-suite run (25 skipped) was not broken down by reason (the run printed failures only).
- The clock of the machine moved only about 8 minutes during the whole trial; times in the logs are as printed.

## 2. Heads used and commands (repeatable)
| What | Head used | Head when the report was written |
|---|---|---|
| main (base) | 51c9fc4fb | same |
| origin/cloud/core-b | 44d691b24 | f390b7d6e |
| origin/cloud/core-c | c73b55238 | 93f7f24e4 |
| origin/wip/cloud-core-c/g1-fold | 8e4d2349e (is inside g3; not brought in on its own) | same |
| origin/wip/cloud-core-c/g2-p1d-a | 22d2e0dab | same |
| origin/wip/cloud-core-c/g3-p2d-port | ef09bf52c | same |
| origin/cloud/core-a | 7129afc9b (code paths) | f52944ddc (only n8n/*.json changed since) |

Combined tree: worktree `S/trial`, local branch `trial/combined`, head 96768f66d, 11 commits on main (one per step).
Commands (scripts copied to raw/TRIAL-bring.sh.txt and raw/TRIAL-resolve.py.txt; per-file actions in
raw/TRIAL-build-steps.log):
```
cd /home/user/hadavin-sdk && git fetch origin
git worktree add --detach S/trial 51c9fc4fb && cd S/trial && git checkout -b trial/combined
P="src tests tools n8n pyproject.toml uv.lock"
bring.sh origin/cloud/core-b 51c9fc4fb core-b $P                 ; commit   # 33 files, all plain checkout
bring.sh origin/cloud/core-c 51c9fc4fb core-c $P                 ; resolve defaults.py ; commit
bring.sh origin/wip/cloud-core-c/g3-p2d-port origin/wip/cloud-core-c/g1-fold core-c-g3 $P ; resolve ; commit
bring.sh origin/wip/cloud-core-c/g2-p1d-a 51c9fc4fb core-c-g2 $P ; resolve redact.py ; commit
bring.sh origin/cloud/core-a 51c9fc4fb core-a $P                 ; commit   # 24 files, all plain checkout
# then the same four branches again for: .gitattributes .github CHANGELOG.md README.md SECURITY.md THIRD-PARTY-NOTICES.md docs
uv sync --all-extras --group test
```
`bring.sh <branch> <base> <label> <paths>`: for every file the branch changed against the base, if the trial tree
still has the base version the branch's file is taken whole (`git checkout <branch> -- file`), else a three-way
merge (`git merge-file`, base as given). g3 was merged against g1-fold because cloud/core-c already holds the G1
commits (re-committed, same content) and g3 is "g1 plus the port".
Files outside the code paths, and whether I took them: `pyproject.toml` (core-c: license file list, ruff banned-API
rows) TAKEN, the build needs it; `THIRD-PARTY-NOTICES.md` (core-c) TAKEN, pyproject names it as a license file so
the package does not build without it; `.gitattributes`, `.github/workflows/ci.yml` (core-c), `CHANGELOG.md`,
`README.md` (core-b and core-c), `SECURITY.md`, `docs/stop-state-runbook.md` (core-b) TAKEN because tests read
them. `uv.lock`: no session changed it. Migrations: 0006 and 0007, both core-b, no number used twice.

## 3. Conflicts (9 files touched by more than one side; 4 with real conflicts)
| File | Sides | What each side did | Suggested resolution | Who |
|---|---|---|---|---|
| src/hadavin_sdk/defaults.py | core-b x core-c | both add a block at the same place (end of the K8S block): core-b the price cap, TRIGGER_*, RESERVATION_EXPIRE_S; core-c the TEXTNORM_* block | keep both blocks, core-b's first (done in the trial; ruff clean) | whoever merges second (core-c), 1 hunk |
| CHANGELOG.md | core-b x core-c x g3 x g2 | every side adds entries at the top of the same list | keep all entries; agree an order (the trial kept arrival order) | the integrator |
| src/hadavin_sdk/app.py, README.md | core-b x core-c | different places | merged clean, nothing to do | nobody |
| src/hadavin_sdk/guard/redact.py | cloud/core-c (G7) x g3 (fold scan port) | G7: `redact()` ends with `r.settle([r.sweep(out)])[0]` and adds `_find_context`/`settle`; g3: same line becomes `r.sweep(out)` with `actions=r.actions`, adds `_over_budget`, `_fold_scan` and more at the same place (2 hunks) | trial: `settle` kept AND `actions` kept; both method groups kept. core-c must decide whether `settle` runs under g3's deadline | core-c (inside its own session) |
| src/hadavin_sdk/guard/redact.py | the above x g2 (P1d-a) | g2 adds `_NOT_ADDRESS`, `_GLUED_WINDOW`, `_sub_glued` where g3 added its blocks (2 hunks) | keep both (done; this is the one file `ruff format` wants reformatted, section 7) | core-c |
| src/hadavin_sdk/guard/runmap.py | cloud/core-c (G0 `is_masked`, `enforce_map`, `_scan`) x g3 | G0 moved the body of `redact_text` into `_scan` and imports `_Redactor`; g3 changed the same body to CPU time with a deadline handed to `redact` and imports `without_spacing_marks` (3 hunks) | trial: both imports; `_scan` uses `time.thread_time()` and passes `_deadline` to both `redact` calls. core-c must confirm that `is_masked` should share the budget | core-c |

Also for the lead, no text conflict but an ownership point: g2 edits `approvals/channel.py`, a file the plan gives
to SPINE (core-b); its own commit message says so. core-b did not touch the file, so it merged without a conflict.
Still 3 unmerged lines of work inside core-c: cloud/core-c, g3 (contains g1) and g2 have never been put together
by core-c itself; all 9 hunks above except defaults.py and CHANGELOG are between core-c's own branches.

## 4. Name and import mismatches between sessions
| What | Where on each side | Effect | Suggested owner |
|---|---|---|---|
| **The secret reader has three names.** Our worker asks for `App.trigger_resolve`; core-b old head built `App.secrets` (the whole store); core-b new head removed `App.secrets` and built `App.trigger_secret` (limited to sender names) | ours: src/hadavin_sdk/triggers/worker.py:292; core-b old: app.py:59; core-b new (f390b7d6e): app.py:59 and 339-348 | **The worker refuses to start on both core-b heads**: `ConfigError: App.trigger_resolve is not available` (raw/TRIAL-worker-probe.log, raw/TRIAL-worker-probe-newb.log). With that ONE name supplied the worker builds its WSGI app on both heads | core-a: read `trigger_secret` (one line, ORDER 014 item 3); or the lead picks one name |
| `host`, `port`, `allow_non_loopback`, `poll_s` do not exist in core-b's TriggerSettings (old and new head) | ours: worker.py:305-307, 396-398 (getattr with fallbacks); core-b: config.py:358-372 | works: the worker uses its own literals (127.0.0.1, 8081, false, 0.05); 20 of our config tests skip for these fields | lead: either core-b adds the fields or core-a deletes the reads and the 20 tests |
| `max_running` default: ours 1 ("parallel runs can pass a budget"), core-b 4 | worker.py:62 and its module text line 26; core-b defaults.py TRIGGER_MAX_RUNNING | a config without the field gets 4 parallel loops from core-b's default, against the worker's own stated reason for 1 | lead decides; then one side changes |
| Literals defined on both sides | ours endpoint.py:35 `ID_RE`, :39 `MAX_SECRETS_PER_SENDER = 2`, worker.py:63 `ACK_WAIT_S = 5.0`; core-b config.py:344 `_TRIGGER_ID`, :353 `max_length=2`, defaults TRIGGER_ACK_WAIT_S | same values today; two places to change later. `MAX_SENDERS = 8` and `MIN_SECRET_CHARS = 32` exist only on our side (endpoint.py:37-38), core-b has no sender limit | core-a: read core-b's defaults where one exists |
| `senders` is a map id -> sender, no `id` field, `secret_names` a tuple | core-b config.py:353-363; ours endpoint.py:204-209, worker.py:219-225 | no effect: our code accepts both shapes (checked by the probe) | nobody |
| Spend store amounts: more than 12 decimal places are refused (ValueError) | core-b store/protocol.py:61-79 (`check_spend_amount`); ours tests/contracts/test_store_spend_reservations.py:213-220 expects a 21-decimal amount to be stored unrounded | 2 test failures (memory, postgres), section 6 | lead: which is the interface; then core-a changes the test or core-b the rule |
| Settle after expiry with a lower real cost: `settled_usd` is the larger of actual and reserved (1.00) | core-b store/protocol.py:232-234 (new head text), memory.py:329; ours test file :409-420 expects `settled_usd` = 0.40 | 2 test failures, section 6 | same as the row above |
| Spend names: `SpendCapExceeded` in store/protocol.py:50, `SpendRefused` and `Meter` in limits.py:17, 26; store methods `reserve_spend`, `settle_spend`, `expire_spend_reservations`, `purge_spend_reservations` | ours look the names up at run time in exactly these modules | match: 98 of 102 spend contract tests pass | nobody |
| Gate x meter | gate: guard/model_gate.py:76-79 (its own `Meter` Protocol), :240 `reserve(agent_id, worst, run_id=...)`, :283 `settle(id, usd)`, :117 SPEND_REASONS; core-b: limits.py:26-35, 60, 92 | signatures and the five refusal reasons are identical; probe: one call booked 0.002, an over-cap call raised `SpendRefused("daily_budget")` and the model client was not called (raw/TRIAL-gate-probe.log) | nobody for function; core-c could import `limits.Meter` instead of keeping a second copy, and its comment at model_gate.py:50-53 ("SpendRefused is not in limits.py yet") is out of date |
| `refused_before_response` mark | gate reads it at model_gate.py:139; core-b sets it only on the NEW head (llm/protocol.py, llm/retry.py, commit 2c3074830) | on the old heads no error is ever settled at 0 (the gate's own text says so); names match on the new head (read, not run) | nobody; re-run after rebase |
| Worst-case cost function | gate takes it as a parameter (model_gate.py:182); `llm.common.worst_case_usd` does not exist on any head (only `k1b/loop.py:115`, another signature) | nothing to install the gate with yet; our contract test for point 10 skips (test_model_gate_contract.py:883) | core-b (install ticket) |
| core-c's grant tests pin main's grants | core-c tests/test_grants_negative_roles.py; core-b migrations 0006, 0007 and store/migrate.py | 8 failures, section 6 (expected by the file's own header) | core-c, after core-b's B and F-store land |
| `TEXTNORM_PINNED_PYTHON` is defined twice with the same value | core-c defaults.py:141 and 146 (inside core-c alone) | none today | core-c |
| Helper names used in more than one new file (`Sink`, `_Recorder`, `_as`, `_load`, `_run`, `build`, `main`, `mutant`, `refused`) | all private to their own test or tool file | none: no shared module, collection has no error (13716 tests collected) | nobody |
| Mutant scripts | core-b already has tests/audit_drain_mutants.py and tests/price_mutants.py (44d691b24) | ORDER 014 item 2 says to skip the ones that exist | lead |

## 5. Tests that only skipped on single branches and now run
| File | On core-a alone | In the combined tree (old heads) |
|---|---|---|
| tests/test_trigger_config.py | whole file skipped (1) | 129 tests: 93 passed, 16 expected-failures, 20 skipped (fields not built) |
| tests/contracts/test_model_gate_contract.py | whole file skipped (1) | 202 tests: 201 passed, 1 skipped (no worst-case helper) |
| tests/contracts/test_store_spend_reservations.py | 94 skipped | 94 run: 90 passed, 4 failed |
| tests/contracts/test_t1_reserve_cap.py | 8 skipped | 8 passed (50 connections, PostgreSQL 16) |
| tests/test_grants_negative_roles.py (core-c) | on core-c alone: 2 strict expected-failures "step B not built" | both now pass, which a strict marker reports as a failure |

Our 16 strict expected-failures in tests/test_trigger_config.py: on the OLD core-b head all 16 still fail as
expected (no finding fixed there). On the NEW core-b head (f390b7d6e) **all 16 now pass and so fail the run as
XPASS(strict)**: F2 (1), F3 (1), F4a (1), F4b (1), F5 (8), F7 (1), F8 (3): every finding of
FINDINGS-core-b-trigger-config.md is fixed. One more test fails there because core-b changed a message:
`test_a_sender_secret_name_that_is_an_action_secret_fails_the_start` expects "secret names used by both", the new
text is "triggers.senders.s1.secret_names: a name is also used by another part of the config ...". So on the new
head our file gives 17 failed, 92 passed, 20 skipped: core-a must remove 16 markers and update 1 match.
(raw/TRIAL-newly-running.log)

## 6. Whole-suite result (combined tree, old heads, PostgreSQL 16.15, 3 workers)
`15 failed, 13655 passed, 25 skipped, 21 xfailed in 309.24s (0:05:09)`; 70 deselected (live, perf).
Logs: raw/TRIAL-whole-suite-pg16.log (last 200 lines), raw/TRIAL-whole-suite-failures.log (every traceback),
raw/TRIAL-classify.log (the 15 ids run again on main, core-b, core-c, core-a and the combined tree; all 15 fail
again combined, so none is a one-off).
Classes: INHERITED 1, SINGLE-BRANCH 1, COMBINATION 13 (4 core-a x core-b, 8 core-b x core-c, 1 inside core-c).
| # | Test | Class | First failing line | Reading |
|---|---|---|---|---|
| 1 | tests/demo_askdata/test_validate_harm.py::...[dblink-connect] | INHERITED (fails the same on main, core-a, core-b, core-c) | `connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed` | the attack `dblink_connect('dbname=postgres')` looks for a server on the default socket; the test server listens on port 55432. A matter of this machine's set-up, NOT of version 16 |
| 2-3 | tests/contracts/test_store_spend_reservations.py::test_nothing_is_rounded[memory], [postgres] | COMBINATION core-a x core-b (skips on core-a, file absent on core-b) | `ValueError: spend amount must be a finite Decimal ... at most 12 decimal places` | the contract test books 0.000000123456789012345; core-b's store refuses more than 12 places. Interface question, not a crash |
| 4-5 | same file::test_settle_after_expiry_with_a_lower_actual_moves_nothing_down[memory], [postgres] | COMBINATION core-a x core-b | `At index 1 diff: Decimal('1.00') != Decimal('0.40')` | after expiry core-b keeps the larger amount in `settled_usd`; the test expects the real cost there. Interface question |
| 6 | tests/test_grants_negative_roles.py::test_the_identities_are_the_ones_this_file_knows | COMBINATION core-b x core-c (passes on core-c) | `Extra items in the left set: 'reset_role'` | core-b's step B adds the reset role; core-c's pin lists three roles |
| 7 | ...::test_every_write_privilege_is_on_the_reviewed_list | COMBINATION core-b x core-c | purge now holds DELETE on `spend_reservations`; runtime grants differ | pins of main's grant map; 0006 and 0007 changed it |
| 8 | ...::test_only_the_runtime_role_holds_anything_on_the_stop_table | COMBINATION core-b x core-c | `{'runtime': {'SELECT'}} != {'runtime': {'INSERT', 'SELECT', 'UPDATE'}}` | step B took the write rights away: the wanted result, old pin |
| 9-10 | ...::test_delete_is_held_only_on_the_outbox_and_the_purged_evidence, ::test_the_purge_role_holds_delete_only_and_no_whole_table_read | COMBINATION core-b x core-c | `Extra items in the left set: 'spend_reservations'` | F-store gives the purge role DELETE on the new table |
| 11 | ...::test_pg_the_runtime_role_can_switch_the_stop_on | COMBINATION core-b x core-c | `InsufficientPrivilege: permission denied for table kill_switch` | the test switches the stop on by UPDATE; after step B a stop is a row in `kill_switch_stops` |
| 12-13 | ...::test_step_b_the_grant_map_gives_the_runtime_role_no_way_to_switch_the_stop_off, ::test_pg_step_b_the_runtime_role_cannot_switch_the_stop_off | COMBINATION core-b x core-c | `[XPASS(strict)] step B not built` | good news: step B does what core-c's target tests ask. Markers to remove |
| 14 | tests/test_redact_context_after_sweep.py::test_public_signatures_are_unchanged | COMBINATION inside core-c (passes on cloud/core-c; fails once g3 is added) | `+ ..., _deadline: 'float | None' = None) -> 'RedactionResult'` | G7's test pins the signature of `redact`; g3 adds the `_deadline` parameter. Not caused by my resolutions |
| 15 | tests/test_stage_names.py::test_the_old_stage_word_is_gone | SINGLE-BRANCH core-c (fails on c73b55238 alone, passes on main and core-b) | `tests/test_runmap_enforce_map.py:231 [quoted literal] ({"<SECRET_1>": "dev"}, "x dev y")` | a test value trips the stage-word guard. Already changed to "web" on core-c's new head 93f7f24e4 (read, not run) |

No failure was about PostgreSQL 16 as a version (no INHERITED-PG16). No failure in core-a's trigger files
(tests/triggers/, tests/test_testing_crash.py) and none in core-b's own new test files.

## 7. Lint (combined tree)
- `ruff check src tests demos tools`: **All checks passed** (raw/TRIAL-ruff-check.log).
- `ruff format --check src tests demos tools`: **1 file would be reformatted, 394 already formatted**:
  src/hadavin_sdk/guard/redact.py, three blank-line places where I joined both sides of a conflict (lines 1059,
  1151, 1489). An artefact of the trial merge, not of any session's code (raw/TRIAL-ruff-format.log).

## 8. To integrate for real, in this order
1. core-c first puts its own three lines together (cloud/core-c + g3 + g2) on its branch: 7 hunks in
   guard/redact.py and guard/runmap.py, the signature pin of failure 14, and it decides how `settle` and
   `is_masked` share g3's time budget. Until then no one else can merge core-c cleanly.
2. Land core-b as planned (A, B, C, D-config, F-store): 33 files at the old head, no conflict with main.
   Everyone rebases on that.
3. Lead rules on the two spend-interface questions (12 decimal places; `settled_usd` after expiry). core-a or
   core-b then changes 4 tests or 2 rules.
4. core-a, after rebasing on core-b's NEW head: read `App.trigger_secret` in worker.py:292 (the worker cannot
   start until then); remove the 16 strict markers and update 1 message match in tests/test_trigger_config.py;
   decide with the lead on `max_running` 1 or 4 and on the four fields core-b did not build (20 skipped tests).
5. core-c, after rebasing on core-b: one hunk in defaults.py (keep both blocks), CHANGELOG entries in agreed
   order, rewrite tests/test_grants_negative_roles.py for the grants after 0006 and 0007 (6 pins, 2 markers), drop
   the duplicate `TEXTNORM_PINNED_PYTHON`.
6. Then core-a's files (all new, no conflict). The 331 tests of section 5 that only skipped now run in CI.
7. Run the whole suite again on the combined NEW heads on PostgreSQL 17 (not done here), then step F install
   (gate into Runtime, worst-case function), which nothing above covers.

## Where things are
Worktrees, all under S, left in place, about 465 MB together: `trial` (combined, 300M), `trial-main` (24M),
`trial-core-a` (45M), `trial-core-b` (26M, at 44d691b24), `trial-core-c` (27M, at c73b55238), `trial-newb`
(43M, branch trial/newb-plus-a = core-b f390b7d6e + core-a files). Local branches `trial/combined` and
`trial/newb-plus-a` and tag `trial-raw-with-markers` exist only in the local repository; none was pushed. Remove
with `git worktree remove <path>` and `git branch -D`. The PostgreSQL 16 test server (port 55432) was started for
the run and is stopped; the other server on port 55433 (core-a-shared) is not mine and was left running.
