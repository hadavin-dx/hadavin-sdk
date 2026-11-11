<!-- full hand-back report of sub-agent ae9691ed, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

Q8a-1 fix batch 4 is pushed as head ecd5dba1 (fast-forward from 0b97d55a) on core/q8a-1-live-override-refusals, but the one full suite did not finish green: 1 failed, 10752 passed, 1 skipped. I did not rerun the whole suite at the final head.

Summary: M1, m2, m3, m4, m5 and m6 are done, and the direct-store-purge item is stated plainly in the limit text and written as an open question (no small safe fix).

**What failed or is uncertain**
- Full suite via heavy.sh (own Postgres 16 on port 56050, `-m "not live and not perf"`): rc=1, 285 s.
  - The one failure is `tests/demo_askdata/test_validate_harm.py::...[dblink-connect]`. My server was started without PGPORT/PGHOST in its own environment, so dblink looked for port 5432. This is a problem with my setup, not the code.
  - After restarting my server with those variables set, `test_validate_harm.py` gave 253 passed.
  - I did not rerun the full suite after that, and I did not rerun the whole suite after one small final edit (removing a `# pragma: no cover` from a new test). After that edit I reran ruff check, ruff format --check and the two touched test files (326 passed) plus the M13 mutants (14 good). The first full run was therefore at the tree just before that edit.
  - The flaky `test_migration_numbers` timing test did not fail.
- The 28 `perf` tests were not run (deselected by the CI marker).
- No live Vault or network service was contacted.
- Not run: the lock-in guard of the sibling branch, and the independent evidence runner and fresh reviewers (the lead's step).

**What I did per item**
- **M1 (Major):** outside DEMO, `_now` now checks `type(ctx) is not TickContext` instead of `isinstance`. `TickContext.__init_subclass__` raises TypeError, so it cannot be subclassed. `src/hadavin_sdk/runtime/tick.py` is the only source file for this fix. The checks inside `__post_init__` and `_now` are the choke point.
  - A spec'd Mock and an object with a `__class__` property both pass `isinstance`; the new tests confirm that, and both are refused.
  - Subclassing is refused.
- **m2:** outside DEMO, `run_tick` now refuses a STEPS list with a name used twice ("a tick step name is used twice: <names>"), checked after the missing-step check.
  - The limit texts now say that a built-in name with a huge `every_s` or `interval` is also a replacement.
  - Also named as still not covered: reordered STEPS, a same-name no-op `purge_evidence`, and a rebound `_BUILT_IN`.
- **m3:** ERRATA rev 7 is added to `/home/user/hadavin-sdk/handover/tickets/Q8a-live-override-refusals.md`. It records the 0.001 timeout lower bound and the frozen optional-time TickContext, plus all of this batch's changes.
- **m4:** config errors no longer show the refused value (no `input_value=`, no link), and the layout is otherwise unchanged. The change is `_value_free_text` in `src/hadavin_sdk/config.py`. A first global rewrite broke an existing test that pins pydantic's layout, so I rebuilt pydantic's layout without the value.
- **m5:** the CHANGELOG says the config is read with YAML 1.1 rules (0x10 is 16, 1:30 is 90). It also says plainly that `Decimal('2.5')` by keyword is refused while `2.5` from the config is accepted. The config cannot carry a Decimal, so I made no code change there.
- **m6 and evidence facts:** the CHANGELOG, `app.py` docstring, `run_tick` docstring, TickContext docstring and the test-module docstring now state what is NOT covered. That list covers:
  - `object.__setattr__` on a real context;
  - an object built without its constructor;
  - a wrapped app that reports demo;
  - a reordered STEPS, or a same-name no-op replacement of a step;
  - a rebound `_BUILT_IN`;
  - the store's purge methods called directly with a made-up time.
  - The CHANGELOG and docstrings now also say that calling the store's purge methods directly on a pilot or prod app with a time 500 days ahead deleted all 3 planted rows with no refusal.
- **Direct store purge:** no small safe fix exists. The store knows no stage or trusted clock, and demo tests use made-up times. It is stated plainly in the limit text and written as `Q-2026-11-11-Q8a1-direct-store-purge` in `/home/user/hadavin-sdk/handover/questions-for-lead.md`. The safe default taken was no change. A proposed separate ticket is in that entry.
- `/home/user/build/B-Q8a1-pr-notes.md` is updated.

**Fail-before (new and changed tests against the 0b97d55a source):** 27 failed, 299 passed across `tests/test_q8a_live_overrides.py` and `tests/test_stage_names.py`.

| Failing tests | Count |
|---|---|
| Mock(spec) and `__class__` lie, 3 steps x 7 stages | 21 |
| Subclassing refused | 1 |
| Duplicate step name refused | 2 |
| Config error free of the value | 1 |
| Extended killer tests in `test_stage_names.py` (one stand-in/Mock/subclass, one built-in-step/duplicate) | 2 |

I did not run the new tests against main separately.

**Counts and exit codes at this head**
- Own Postgres: the two positive pilot tests (`test_k3_pilot_app_has_no_executor`, `test_the_app_deletes_evidence_only_through_the_purge_identity`) ran non-skipped: 2 passed, rc 0.
- `tests/stage_mutants.py` via heavy.sh: 75 of 75 good, rc 0.
  - I added four mutants: M13k (isinstance again), M13l (subclass allowed again), M13m and M13n (duplicate-name check switched off or finding nothing).
  - The M13i string was updated for the new check.
- ruff check: 0. ruff format --check: 0 (323 files). `bandit -ll -r src tools`: 0, no issues (Low 12, Medium 0, High 0). `scan_repo.py`: 0.
- gitleaks (`/home/user/build/bin/gitleaks`), `origin/main..HEAD`: 0, 5 commits, no leaks. I ran it before the push and again after the final amend.
- Suppressions: my first commit had one `# pragma: no cover`. I removed it and amended the commit before pushing.

**Rules cited:** the bible is not present in this cloud session. I used the repo rules fix-dont-defer-be-honest, class-level-fixes, least-privilege-hard-rule, no-single-dependency, verify-tests-and-evals and core-modules-one-source-of-truth.

**Files changed (commit ecd5dba1):**
- `CHANGELOG.md`
- `src/hadavin_sdk/app.py`
- `src/hadavin_sdk/config.py`
- `src/hadavin_sdk/runtime/tick.py`
- `tests/stage_mutants.py`
- `tests/test_q8a_live_overrides.py`
- `tests/test_stage_names.py`

Edited outside the worktree: the ticket errata and `questions-for-lead.md` under `/home/user/hadavin-sdk/handover/`, and the PR notes under `/home/user/build/`. Logs are in `/home/user/build/B-Q8a1-evidence/r5-*.log`.

**Cleanup:** my Postgres is stopped and its data dir deleted; nothing of mine is running. I started no sub-agents and merged nothing.
