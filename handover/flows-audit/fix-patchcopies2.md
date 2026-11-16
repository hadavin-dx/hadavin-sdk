# fix-patchcopies2: fixer log for patchcopies-readiness-r2 (B1, M1-M6, nits)
Date 2026-11-16. Security path fixer. Edited only: `reviews-of-core-patches/patch-copies/README.md`, `DEAD-MAN-CHECK.md`, `A-01.patch`, `C-01.patch`. Nothing committed or pushed. EGM skipped for the fixer step: the lead runs the result review.

## Not done, uncertain, not checked (first)
- STATIC order kept: no database started. Every database behaviour is UNVERIFIED except what `fix-patchcopies1.md` saw once on a throwaway Postgres (not the real store). The new DEAD-MAN statements (REVOKE FROM PUBLIC, default_transaction_read_only, CONNECTION LIMIT, statement_timeout, password step) were NOT run. Needs the lead: a test database with the real migrations; next step is the "Negative test" section of DEAD-MAN-CHECK.md.
- Full suite ran in an archive folder (not a git checkout); `perf` tests not run.
- Decision needed from the studio head (not code): `openai_compat` with a keyless loopback address (a local model) legitimately costs 0; C-01 refuses that. Options (a) state a small price, (b) exempt that case. Also the 200_000 ceiling is marked default pending the studio head's yes.
- Which login the tick runs under: not stated in the patches; REVIEW.md X-6 says one runtime login serves agent, tick and approval receiver. Whether a deployment splits them: the lead answers.
- Sandbox environment holds cloud variables; all test runs used `env -i` (PATH, HOME, PYTHONPATH only). None of them was used or printed.
- Slip of mine: my first full-suite start did not clear the environment; I killed it within seconds and re-ran under `env -i`.

## Changes made (class: "tests that pass or fail for the wrong reason" and "recipe that cannot be run as written")
- B1: README pass criterion rewritten: baseline measured on the unpatched archive (exact command, exit, counts, the 2 named failures), rule "exactly these named failures and no others, passed = baseline + 32", marker form `-m "not live and not perf"` (markers from pyproject.toml, CI at ci.yml:88/94), gate commands through `uv run` (worked offline from the cache), bandit run in the CI form.
- M1: C-01 tests use the literals 200_001 / 200_000 (no `defaults` import). A-01 tests now drive the real `run_tick` with the list cut to `audit_reconcile` against a small fake store, so on old code they fail for behaviour (see below).
- M2: `match="less than or equal to 200000"` and `match="greater than 0"` added.
- M3: recipe: `mktemp -d`, absolute `P`, no G5 patch step, real commands with `echo exit=`, "unpatched copy" and "patched copy" defined, expected exit 1 on the old tree stated. G5 wording drop written as a prose list of exact old and new sentences (no handle, no e-mail; old lines read with git show b4cce5b; none of the quoted lines carry a handle). No G5 patch file recreated.
- M4/M5: DEAD-MAN-CHECK identity table: REVOKE ... FROM PUBLIC (with the warning about other roles), password step through the secrets kind (no password text; `\password` prompt), default_transaction_read_only, CONNECTION LIMIT, statement_timeout; named human with a separate login; psql exit codes corrected (2 cannot connect, 3 script error); table-in-public assumption stated.
- M6: DEAD-MAN-CHECK states: audit-write-failure log lines are read by nothing (no alert kind in src); green means the step ran. Code change in A-01 beyond the review text (my decision, say if you disagree): a kind without `reconcile` now FAILS the step instead of recording a quiet success (closes the false-green at the shared step). K1bAudit has no reconcile but is built only for k1b commands (cli.py:213), not as `app.audit` (app.py:161). Other no-spend llm kinds: only `fake` (backends/table.py:512-540: fake, anthropic, bedrock, openai_compat, gemini); demos hold no llm config.

## Raw results (scratch copies of b4cce5b under the scratchpad, `mktemp -d`)
git apply --check on a fresh archive (final files): `check C-01 rc=0`, `check A-01 rc=0`, apply both `rc=0`.
`ruff format --check` on the touched python (8 files, scratch): `8 files already formatted`, rc 0 (first version of the files; the final run used `uv run --all-extras --group test ruff format --check`: `301 files already formatted`, rc 0).
`uv run --all-extras --group test ruff check`: `All checks passed!` rc 0. `bandit -q -r src demos -ll`: rc 0, no issue.
Fail-on-old-code (unpatched archive + the two new test files; `env -i PATH=/usr/bin:/bin HOME=<scratch> PYTHONPATH=src python -m pytest -q -p no:cacheprovider tests/test_a01_audit_reconcile.py tests/test_c01_route_limits.py -rf`): exit 1, `13 failed, 19 passed in 0.49s`. Failure reasons: 7 x `DID NOT RAISE ConfigError` (6 price + max_tokens 200_001); `assert 'audit_reconcile' in [sweep, reconcile, stuck, checkpoint, purge_evidence, reprobe_sources]`; `'audit_reconcile drained=1' in 'INFO ... tick ok=True failed=-'`; `assert 0 == 1` (no step ran); three empty-log assertions (`'OSError' in ''`, `'held in memory only' in ''`, `'goes to the outbox' in ''`).
Patched copy, new tests plus tick tests: `47 passed` (a01 + p7_tick) and `73 passed` (a01 + c01 + p7_tick) on the two versions.
Baseline, unpatched archive full run: `2 failed, 9364 passed, 454 skipped, 26 deselected in 225.52s`, exit 1; failed: tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked, tests/test_repo_rules.py::test_licences_are_proprietary.
patched full run (final patch files): `2 failed, 9396 passed, 454 skipped, 26 deselected in 247.81s`, exit 1; the same two names; 9396 = 9364 + 32.
Personal-handle and e-mail scan of the four files (pattern search): no match.

## Cleanup
No background process or container left. Scratch folders are under the scratchpad only.
