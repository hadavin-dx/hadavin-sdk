## What this adds (AK-G2-a: the inbound message ledger, without the dispatcher)

A message that arrives from outside (a webhook call, an e-mail) is written down once, before anything else happens to it. It can then be taken by exactly one worker at a time, finished once, and never lost or applied twice (bible R368). Each tenant's messages stay apart (R369). The part that starts agent runs (dispatch, classify, StartRun) is NOT in this PR: it needs the AK1-a pieces, which are not on main (see "What waits for AK1-a").

Parts of this change that deal with the receipt, the claim and the retry count are promoted from the public demo repo duplicate-proof-lead-desk-n8n at 43110e7 (the original is read-only; the code here is rewritten against the ticket, with demo names and demo fields removed).

- Migration `0006_inbound.sql`: receipts, bodies, key checks, a login-less re-run owner role, database triggers that refuse every illegal state move, and the grants for six database roles.
- `InboundStore` (11 methods) in memory and in Postgres, with one shared contract test file that runs both.
- `triggers/ledger.py`: the keys (HMAC based), the sender-id check, `Inbox.receive`.
- `migrate` and the command line: three new options for the inbound roles; a role that does not exist now stops with a plain `ConfigError` naming it (before, the database gave a raw error).

## Rung table (R448, CODE-LAST)

| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| receipt, dedupe, claim, lease, finish | no lost and no double-applied message | already in a demo (reuse, rung 1); queue library pgmq (rung 5), ticket section 12, 2026-11-06 | ticket section 12: no dedupe key, no tenant columns | keyed dedupe, tenant columns, grants and triggers | KEEP-CODE |
| re-run guard trigger and login-less owner role | only a person re-runs a stopped message | none higher: it is an approval guarantee | n/a | approver separate from the agent | KEEP-CODE |
| retry with back-off | demo had a per-key wait | the ticket wins (lines 18, 328, 330, 395: a try is counted only on lease expiry or a step error; no wait; the end state is `needs_person attempts_exhausted`) | ticket | n/a | CUT (the claim and lease already cover it) |

## Tests that fail on the old code

Raw output: `PD-AKG2a-failbefore.txt` and `PD-AKG2a-failbefore-b2.txt` (the new test files run against base 2a8c2aac fail to import or fail on every row, because the tables, roles and triggers do not exist there). The migrate role-existence fix has its own test (`test_l26_a_partial_role_set_is_refused_and_a_real_database_is_left_untouched`, `test_l26_a_partial_set_of_inbound_roles_is_refused_before_connecting`).

Real Postgres 16 tests (`tests/test_inbound_postgres.py`): L5 (8 processes claim 500 receipts, each exactly once), L14, L15 a-h (immutable columns, even for the migrator), L21, L24 (the exact rights of all six roles, refused inserts), L25 (8 processes), L26 and L28 with real roles. They need `HADAVIN_TEST_PG_DSN`; without it they skip.

## Mutants

`tests/inbound_ledger_mutants.py`: 69 mutants, one per code item of the ledger (keys, memory store, Postgres store, migration SQL, grants and migrate). Each names the one test that must kill it and the text of the failure it must give; `tests/test_inbound_ledger_mutants_guard.py` checks that every mutant text still applies exactly once. Result of the final run through `heavy.sh` on head aba26c69: **69 of 69 good, problems: [], exit code 0**. (An earlier exploratory run gave 62 of 69; five of the seven problems were wrong failure-text or test-id pins in the mutants file, one needed an allowed crash type, and one, P11, was a real test gap, now killed by `test_l25_v_a_changed_key_is_refused_by_the_read_before_any_insert_is_tried`.)

Note: the runner on main has no way to pass `HADAVIN_TEST_PG_DSN` to the child test process (the runner PR R1 is not merged). The script adds it itself and exits 2 when it is missing.

## What waits for AK1-a (not built, nothing stubbed to look finished)

Missing on main: `tenant_key`, `TENANT_PATTERN`, `Readers`, `Step`, `StepInput`, `run_step`, `REASONS`. Stand-ins now in `triggers/ledger.py`: `tenant_key` and `INBOUND_NAME`.

| ticket rows | waits for | replace the stand-in with |
|---|---|---|
| F1 to F3, B1, B2 (with dispatch) | Step, run_step | the AK1-a runner |
| L8, L10 (spy-step part), L17, L20 (iii) to (vii) | Step and StepInput | `Step`, `StepInput`, `run_step` |
| D1 to D15, D15 guard, ticket rule 8a | dispatch, `_classify`, `StartRun` | the AK1-a `Readers` type and `REASONS` |
| mutants M-a8, 16-18, 20-24, 26, 36, 39, 44-46, 48-50, 58-60, 62-64, 66, 68, 70, 75-77, 81, 87, 88, 90, 94 | the same | added with the dispatch part |
| tenant key | AK1-a `tenant_key` | the AK1-a function (same signature; golden test L19 will show any drift) |

B3 (opt-in 1-million-row load test) is not built; it does not need dispatch.

## Checks run (head aba26c69; every number is a real exit code)

| command | result |
|---|---|
| `ruff check` | exit 0, all checks passed |
| `ruff format --check src tests demos tools` | exit 0, 325 files formatted |
| `bandit -q -r src demos tools -ll` (no pipe) | exit 0 |
| `python tools/scan_repo.py` | exit 0 |
| `python tests/stage_mutants.py` | exit 0, 37 of 37 good |
| `python tests/inbound_ledger_mutants.py` via `heavy.sh` | exit 0, 69 of 69 good |
| full `pytest -m "not live and not perf"` via `heavy.sh`, own Postgres 16 | exit 1: 10752 passed, 2 skipped, 2 failed (below) |

The 2 failures: (1) `test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]`, the known environment failure; (2) `test_the_runner_children_see_an_allowlisted_environment_only`, which failed in the full run (its baseline child run did not pass inside the shared test folder) but passes alone and with the whole `tests/test_mutation_runner.py` file (59 passed). I did not find the cause; it touches no file in this change (NOT confirmed as unrelated on the base commit). `test_the_timing_harness_flags_a_quadratic_stand_in` failed in an earlier full run and passed in this one (known flaky).

An earlier full run on the previous head found three real regressions caused by migration 0006 (the runtime-grant test, the renamed-migration test, the migration-list test); they are fixed in this head.

No paid or live model call was made. EGM review of the result has NOT been run by the builder; the lead runs it. Rules cited: R368, R369, R370, R448, R449.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_014pRo36xK6rXQgBKwtTHfac
