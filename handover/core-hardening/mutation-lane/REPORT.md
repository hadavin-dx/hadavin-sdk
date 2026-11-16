# Mutation lane report, round 2 (C8b), run 2026-11-16 UTC. Evidence runner: runs and records, does not judge.

> **SCOPE: v1 patches only; v2 rerun pending (C8c).** Every number below was measured on the v1 patches (`patches-ready/C-01.patch`, `A-01.patch`). The v2 patches that will merge (`patches-ready/v2/`) change the code (new function names, new checks) and were NOT run through this lane. Nothing here is merge evidence for v2. The mutant plan for v2 is `MUTANTS-V2-PLAN.md`.
> Corrected after review 2 (`review-2.md`): the 46 vs 104 explanation (section 2), the stale m08/m09 line, the one-file proof baseline, the suppression comments in the proof test, and `run.py` (backups no longer written into this folder; crash safety added; see section 5).

## 1. What survived or could not run (read this first)
Base: commit `b4cce5b6ae80b45125604b8295ebb35bd2ea1c2c` plus one patch each (`patches-ready/C-01.patch`, `A-01.patch`), in scratch copies `/tmp/c8/wC` and `/tmp/c8/wA` (byte-identical to a fresh `git archive` + `patch -p1`, checked with `diff -rq`, no output). The real repository source was not touched.

**Real mutants killed / survived with the patches' own tests (counts exclude no-op controls):**
- C-01: 20 real mutants, 13 killed, **7 SURVIVED** (m11, m12, m13, m14, m18, m19, m21). Control m16 survives as it must.
- A-01: 27 real mutants, 15 killed, **12 SURVIVED** (m08, m09, m17, m18, m19, m21, m22, m23, m24, m25, m26, m29). Controls m01 and m10 survive as they must.
- Every survivor now has a kill test, proven below (section 4): passes on unmutated code, fails on the mutant. After adding them, 0 of the 19 survivors remain. The extra tests are NOT applied to the repo: they are in `proof-tests/` (and the assertions are shown in section 3). Someone must decide to add them to the patches.

**Could not run or not checked:**
- Full suite, ruff, bandit, G5-wording patch: not run (another agent runs the full suite; G5 is text only).
- Mutants of the test files themselves, `reprobe_sources` / K1bAudit paths, other audit kinds: not covered. The mutant lists are hand-made, not exhaustive.
- C-01 mutants were run against `tests/test_c01_route_limits.py` only (10 tests). A kill by some other test elsewhere in the repo is not looked for.
- Reordered `except` clauses in `write_outcome` (review-1 M4 "reordered"): not run; only "removed" and "returns None" variants were run.
- A-01 survivors m08 and m09: proven by `raw-proof/A-01-proof-m08.txt` and `raw-proof/A-01-proof-m09.txt`; m09 (interval 3600) fails two tests there (the list-entry test and the two-ticks test), so both are shown to kill it. m08 also fails in its proof file.
- Slips by me: (a) I ran two short pytest processes (proof checks) while the A-01 mutation loop was running, against the "one pytest process at a time" rule; they used different scratch trees and ran under 10 s, so the loop results are not affected, but it was a slip. (b) `run.py` first wrote `.restore-copy` into this folder and it was picked up as a tracked file by git; I removed it. FIXED in C8c prep: the saved original now lives in `$TMPDIR/hadavin-mutation-lane/`, outside the repository, and is deleted after every mutant (proof: `raw/run-py-safety-tests.txt`).
- v1 correction: in v1 the A-01 row 14 (memory-only ERROR to DEBUG) was reported KILLED, but the first planting used text that does not exist in the file (COULD-NOT-PLANT, matches=0); the kill came from a separate rerun with corrected text. In this round the corrected text is in the list and m14 is KILLED in one run.
- v1 also ran with Python bytecode caches left on; a stale `.pyc` with the same size and same second could in theory hide a change. This round deletes `__pycache__` before every run and sets `PYTHONDONTWRITEBYTECODE=1`.

## 2. Baseline (answers review-1 M2: "46 vs 104"; corrected after review 2)
Run in the unmutated patched copies, clean environment (`env -i`), one process, exit code 0 each time (raw: `raw/C-01-baseline.txt`, `raw/A-01-baseline.txt`):
- C-01 command `.venv/bin/python -m pytest -q -p no:cacheprovider --tb=line -rf tests/test_c01_route_limits.py` -> **10 passed** (6 price cases = 2 fields x 3 prices, plus 4 other tests).
- A-01, two different sets, not one:
  - `tests/test_a01_audit_reconcile.py` alone -> 5 passed.
  - plus `tests/test_p7_tick.py` -> **46 passed** (this was the v1 REPORT number: the new tests and the tick tests).
  - plus `tests/test_s2_audit.py` and `tests/test_p3b_neutral_audit.py` -> **104 passed** (4-file set).
  - Which set ran where (corrected; the earlier text said the 4-file set ran in every v1 A-01 run, which was wrong): in v1 the kill runs used `-x` and only the new test file `tests/test_a01_audit_reconcile.py`; only the v1 survivors were then run against the 104-test set (source: review 2 and the v1 run notes; the v1 raw files in `raw-v1/` have no command line, so this cannot be re-checked from them). "46" and "104" were therefore never one number that mismatched: they are the sizes of two test sets used for two purposes. In this round-2 loop (`raw/`) all 29 A-01 raw files (27 real mutants + 2 controls) record the same 4-file command (104 tests) without `-x` (grep over `raw/A-01-m*.txt`; the baseline `raw/A-01-baseline.txt` says 104 passed).
- With the extra proof tests added (scratch only): C-01 13 passed (10 + 3 new), A-01 proof file 10 passed.
- The proof baseline is ONE file per lane (`raw-proof/C-01-proof-baseline.txt`, `raw-proof/A-01-proof-baseline.txt`), taken once before that lane's 7 and 12 proof kills; it is not repeated per mutant. The kill files each record their own rc and failing tests.
- Suppressions removed: `proof-tests/test_a01_extra_proof.py` had two `# noqa: F811` comments and one `# noqa: F401`. The file now registers the existing tick fixtures with `pytest_plugins = ["tests.test_p7_tick"]`, so no name is imported and nothing is suppressed. `grep -c noqa proof-tests/*.py` gives 0; `ruff check` and `ruff format --check` on both proof files pass and the A-01 proof file passes 10 tests (`raw-proof/ruff-proof-tests.txt`, `raw-proof/A-01-proof-noqa-removed-pytest.txt`). Note: the proof tests of this report still describe the v1 messages; they must be re-based on v2.

## 3. Assertions that kill each survivor (test text is in `proof-tests/`, not applied)
- C-01 m11 (`gt=0` to `gt=1`): `assert _load(cfg_dir, max_tokens=1).routes["default"].max_tokens == 1`.
- C-01 m12, m13, m14 (ceiling constant 200_001 / 199_999 / 2_000_000): literals, not the constant: `_load(max_tokens=200_000)` loads; `_load(max_tokens=200_001)` raises ConfigError; `_load(max_tokens=2_000_000)` raises ConfigError (review-1 minor: boundary literals).
- C-01 m18, m21 (only the first / only the "default" route checked) and m19 (route names dropped from the message): add a second route `zcheap` with input price "0" under a live model (route name sorts after `default`, because `yaml.safe_dump` sorts keys, otherwise "first route" would be the bad one); `with pytest.raises(ConfigError, match=r"zero or negative price: \['zcheap'\]")`.
- A-01 m08, m09 (wrong function; interval 3600): corrected form per review-1 M1: `step = next(s for s in tick.STEPS if s.name == "audit_reconcile"); assert step.fn is tick.audit_reconcile; assert step.every_s == 0 and step.interval is None`. A two-tick run test with a counting stub also exists (two ticks one second apart both call `reconcile`).
- A-01 m17, m18, m19 (`LocalDirSink.write_outcome` warning removed / leaks error text / DEBUG): force `sink._write` to raise `OSError("secret-looking detail")`; with caplog at WARNING on `hadavin_sdk.audit.local_dir`, `write_outcome(ev) is None`; exactly one WARNING record; text has `OSError` and `ev.event_id`; no `secret-looking detail`, no `run-4`.
- A-01 m21, m22 (chain `write_outcome` duplicate: except removed / returns None): `assert log.write_outcome(ev) == ev.event_id` twice; `audit_outbox` stays empty.
- A-01 m23 (local_dir duplicate except removed): second `write_outcome(ev) == f"{ev.event_id}.json"` and no outbox file.
- A-01 m24, m25 (chain `reconcile` never drains `_pending` / never removes the event): make `_append` and `_db.run` raise, `write_outcome` leaves 1 event in `_pending`; restore both; `reconcile() == 1`, `_pending == []`, a second `reconcile() == 0`, and the event is in `audit_entries`.
- A-01 m26 (local_dir `reconcile` never drains `_pending`): same shape with an unusable outbox (a file where the folder should be); `reconcile() == 1`, `_pending == []`, `sink.events()` holds the event.
- A-01 m29 (`_drain` reports success after a failed append): `_append` raises; the event sits in `audit_outbox`; `reconcile() == 0` and the outbox row is still there.
- Killed by existing tests already (review-1 M4 items): C-01 `kind` inversion (m17), `<= 0` to `< 0` full expression (m20); A-01 result ignored (m20), step isolation removed (m27), raising step not recorded (m28).

## 4. Proof that each extra test is real (raw: `raw-proof/`)
Unmutated scratch copy with the extra file: C-01 `13 passed`, A-01 proof file `10 passed` (rc 0; `raw-proof/C-01-proof-baseline.txt`, `A-01-proof-baseline.txt`). Each of the 19 survivors was then planted again with the same text and run with the extra tests: all 19 KILLED (rc 1). Proof copies are `/tmp/c8b/kC` and `/tmp/c8b/kA` (the venv `.pth` points at the old trees, so `run.py --pythonpath` points at the copy's `src`; the kills show the mutation took effect). A first proof run left C-01 m18 SURVIVED because `default` sorted after the test route `cheap`; the route was renamed `zcheap` and re-run; the table shows the second run.

## 5. Method and files
- `run.py` (this folder; rewritten in C8c prep, see below): one mutant or a JSON list; per mutant it writes `raw/<tag>-<id>.txt` with verdict, description, base sha, root, command, rc, restore check (`diff` of the saved original against the file after restore, rc 0 means identical; the script aborts if not), pytest summary line, first and all failing tests (no `-x`), full old and new text, full pytest output. Verdict by exit code only: 0 survived, 1 killed, other = ERROR (none occurred).
- Mutant lists: `mutants-C-01.json`, `mutants-A-01.json` (same list as v1 with ids m01..; new ones M4 are C m17..m21 and A m20..m29). v1 files are in `raw-v1/` (unchanged). v1 old report text is replaced by this file.
- Not committed or pushed.

## 5b. run.py safety changes (C8c prep, after review 2 M2 and M3)
- Backups: outside the repository (`$TMPDIR/hadavin-mutation-lane/<root key>.backup`), removed after each mutant. Nothing is written into the lane folder except `raw/`.
- Hash baseline: the original bytes of every target file come from a fresh `git archive <sha>` extract plus the `--patch` files, never from the file on disk. Before the loop the whole scratch tree is compared with that reference; any difference means REFUSED (a planted change from a killed run cannot be read as the original).
- `--root` that is, contains or lies inside the real repository (the repository work tree), or is any git work tree, is REFUSED. A lock per root refuses a second run.
- A marker is written before each planting. After SIGKILL the file stays mutated, the next run refuses and prints `run.py --root R --restore`; with the marker lost the tree comparison still refuses. SIGTERM and SIGINT restore the file, stop the test process group, remove the marker and exit 143 / 130.
- After the loop `raw/<prefix>-tree-diff.txt` holds `diff -rq` against a fresh archive extract. For the finished round-2 loops it was run once by hand on the unchanged scratch trees: `raw/C-01-tree-diff.txt` and `raw/A-01-tree-diff.txt`, both rc 0 (no differences). This is a check taken after the loop, not during it; the old claim "byte-identical, checked with `diff -rq`, no output" had no raw file until now.
- Test of all of this on a toy repository with made-up files (not on the real code): `raw/run-py-safety-tests.txt` (T1 real repo refused, T2 SIGKILL, T3 refusal text, T4 marker lost, T5 `--restore`, T6 SIGTERM, T7 SIGINT, T8 lock, T9 clean run). Not tested: Windows (the lock uses `fcntl`, Linux and macOS only); a SIGKILL of the test process alone (the timeout path is unchanged, 600 s).
- Not done in this prep: the full v1 loops were NOT rerun with the new `run.py` (they are superseded by the v2 rerun). The old v1/round-2 raw files were produced by the old script.

## 6. Full result tables

### C-01

| id | file | mutation | verdict (rc) | first killing test / failing count | with the extra test |
|---|---|---|---|---|---|
| C-01-m01 | config.py | price check <= 0 -> < 0 (price 0 allowed) | KILLED (rc=1) | tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[0-input_usd_per_mtok] [4 failing] |  |
| C-01-m02 | config.py | min -> max (only both-zero refused) | KILLED (rc=1) | tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[0-input_usd_per_mtok] [6 failing] |  |
| C-01-m03 | config.py | output price no longer checked | KILLED (rc=1) | tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[0-output_usd_per_mtok] [3 failing] |  |
| C-01-m04 | config.py | input price no longer checked | KILLED (rc=1) | tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[0-input_usd_per_mtok] [3 failing] |  |
| C-01-m05 | config.py | live-kind price check removed entirely | KILLED (rc=1) | tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[0-input_usd_per_mtok] [6 failing] |  |
| C-01-m06 | config.py | price check also applied to fake kind (over-broad) | KILLED (rc=1) | tests/test_c01_route_limits.py::test_the_fake_model_may_cost_nothing [1 failing] |  |
| C-01-m07 | config.py | refusal never raised | KILLED (rc=1) | tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[0-input_usd_per_mtok] [6 failing] |  |
| C-01-m08 | config.py | max_tokens ceiling dropped | KILLED (rc=1) | tests/test_c01_route_limits.py::test_max_tokens_above_the_ceiling_is_refused [1 failing] |  |
| C-01-m09 | config.py | max_tokens gt=0 -> ge=0 (0 allowed) | KILLED (rc=1) | tests/test_c01_route_limits.py::test_max_tokens_at_the_ceiling_loads_and_zero_is_still_refused [1 failing] |  |
| C-01-m10 | config.py | ceiling le -> lt (off-by-one at ceiling) | KILLED (rc=1) | tests/test_c01_route_limits.py::test_max_tokens_at_the_ceiling_loads_and_zero_is_still_refused [1 failing] |  |
| C-01-m11 | config.py | max_tokens gt=0 -> gt=1 (1 refused) | SURVIVED (rc=0) |  | KILLED: tests/test_c01_extra_proof.py::test_max_tokens_one_loads |
| C-01-m12 | defaults.py | ceiling constant +1 | SURVIVED (rc=0) |  | KILLED: tests/test_c01_extra_proof.py::test_the_ceiling_is_exactly_200_000 |
| C-01-m13 | defaults.py | ceiling constant -1 | SURVIVED (rc=0) |  | KILLED: tests/test_c01_extra_proof.py::test_the_ceiling_is_exactly_200_000 |
| C-01-m14 | defaults.py | ceiling constant x10 (the typo it guards) | SURVIVED (rc=0) |  | KILLED: tests/test_c01_extra_proof.py::test_the_ceiling_is_exactly_200_000 |
| C-01-m15 | defaults.py | ceiling constant lowered to 100 (would break 1024 fixtures) | KILLED (rc=1) | tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[0-input_usd_per_mtok] [8 failing] |  |
| C-01-m16 | config.py | (no-op control: identical text) | SURVIVED (no-op control, not counted) (rc=0) |  |  |
| C-01-m17 | config.py | M4: kind != "fake" inverted to == "fake" | KILLED (rc=1) | tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[0-input_usd_per_mtok] [7 failing] |  |
| C-01-m18 | config.py | M4: only the first route is checked | SURVIVED (rc=0) |  | KILLED: tests/test_c01_extra_proof.py::test_every_route_is_checked_and_the_message_names_the_free_one |
| C-01-m19 | config.py | M4: route names dropped from the message (count only) | SURVIVED (rc=0) |  | KILLED: tests/test_c01_extra_proof.py::test_every_route_is_checked_and_the_message_names_the_free_one |
| C-01-m20 | config.py | M4: min(...) <= 0 changed to < 0 (full-expression form) | KILLED (rc=1) | tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[0-input_usd_per_mtok] [4 failing] |  |
| C-01-m21 | config.py | M4: only the route named default is checked | SURVIVED (rc=0) |  | KILLED: tests/test_c01_extra_proof.py::test_every_route_is_checked_and_the_message_names_the_free_one |

### A-01

| id | file | mutation | verdict (rc) | first killing test / failing count | with the extra test |
|---|---|---|---|---|---|
| A-01-m01 | tick.py | (no-op control) | SURVIVED (no-op control, not counted) (rc=0) |  |  |
| A-01-m02 | tick.py | drain count logged as 0 and reconcile never called | KILLED (rc=1) | tests/test_a01_audit_reconcile.py::test_the_step_drains_the_outbox_and_logs_the_count [1 failing] |  |
| A-01-m03 | tick.py | drain runs but no log line | KILLED (rc=1) | tests/test_a01_audit_reconcile.py::test_the_step_drains_the_outbox_and_logs_the_count [1 failing] |  |
| A-01-m04 | tick.py | early return: step never drains | KILLED (rc=1) | tests/test_a01_audit_reconcile.py::test_the_step_drains_the_outbox_and_logs_the_count [1 failing] |  |
| A-01-m05 | tick.py | missing-reconcile guard removed (kind without reconcile crashes) | KILLED (rc=1) | tests/test_a01_audit_reconcile.py::test_a_kind_without_reconcile_is_skipped [1 failing] |  |
| A-01-m06 | tick.py | logged count off by one | KILLED (rc=1) | tests/test_a01_audit_reconcile.py::test_the_step_drains_the_outbox_and_logs_the_count [1 failing] |  |
| A-01-m07 | tick.py | step removed from STEPS | KILLED (rc=1) | tests/test_a01_audit_reconcile.py::test_the_step_is_in_the_tick_list [2 failing] |  |
| A-01-m08 | tick.py | STEPS entry points at the wrong function | SURVIVED (rc=0) |  | KILLED: tests/test_a01_extra_proof.py::test_the_list_entry_runs_audit_reconcile_every_tick |
| A-01-m09 | tick.py | step interval 0 -> 3600 (not every tick) | SURVIVED (rc=0) |  | KILLED: tests/test_a01_extra_proof.py::test_the_list_entry_runs_audit_reconcile_every_tick |
| A-01-m10 | chain.py | (no-op control) | SURVIVED (no-op control, not counted) (rc=0) |  |  |
| A-01-m11 | chain.py | chain outbox WARNING removed | KILLED (rc=1) | tests/test_a01_audit_reconcile.py::test_a_failed_outcome_write_logs_type_and_id_but_never_the_body [1 failing] |  |
| A-01-m12 | chain.py | chain WARNING leaks the error text (redaction regression) | KILLED (rc=1) | tests/test_a01_audit_reconcile.py::test_a_failed_outcome_write_logs_type_and_id_but_never_the_body [1 failing] |  |
| A-01-m13 | chain.py | chain WARNING logs run id instead of event id | KILLED (rc=1) | tests/test_a01_audit_reconcile.py::test_a_failed_outcome_write_logs_type_and_id_but_never_the_body [1 failing] |  |
| A-01-m14 | chain.py | memory-only ERROR downgraded to DEBUG | KILLED (rc=1) | tests/test_a01_audit_reconcile.py::test_when_the_outbox_table_also_fails_an_error_line_is_logged [1 failing] |  |
| A-01-m15 | chain.py | memory-only ERROR line removed | KILLED (rc=1) | tests/test_a01_audit_reconcile.py::test_when_the_outbox_table_also_fails_an_error_line_is_logged [1 failing] |  |
| A-01-m16 | chain.py | event no longer kept in memory when outbox fails (audit loss) | KILLED (rc=1) | tests/test_a01_audit_reconcile.py::test_when_the_outbox_table_also_fails_an_error_line_is_logged [1 failing] |  |
| A-01-m17 | local_dir.py | local_dir outbox WARNING removed | SURVIVED (rc=0) |  | KILLED: tests/test_a01_extra_proof.py::test_local_dir_failed_outcome_logs_a_warning_with_type_and_id_only |
| A-01-m18 | local_dir.py | local_dir WARNING leaks the error text | SURVIVED (rc=0) |  | KILLED: tests/test_a01_extra_proof.py::test_local_dir_failed_outcome_logs_a_warning_with_type_and_id_only |
| A-01-m19 | local_dir.py | local_dir WARNING downgraded to DEBUG | SURVIVED (rc=0) |  | KILLED: tests/test_a01_extra_proof.py::test_local_dir_failed_outcome_logs_a_warning_with_type_and_id_only |
| A-01-m20 | tick.py | M4: reconcile called but its result ignored (logs 0) | KILLED (rc=1) | tests/test_a01_audit_reconcile.py::test_the_step_drains_the_outbox_and_logs_the_count [1 failing] |  |
| A-01-m21 | chain.py | M4: chain write_outcome DuplicateEvent except removed (duplicate goes to outbox) | SURVIVED (rc=0) |  | KILLED: tests/test_a01_extra_proof.py::test_chain_duplicate_outcome_is_not_an_outage |
| A-01-m22 | chain.py | M4: chain write_outcome returns None for a duplicate instead of the event id | SURVIVED (rc=0) |  | KILLED: tests/test_a01_extra_proof.py::test_chain_duplicate_outcome_is_not_an_outage |
| A-01-m23 | local_dir.py | M4: local_dir write_outcome DuplicateEvent except removed | SURVIVED (rc=0) |  | KILLED: tests/test_a01_extra_proof.py::test_local_dir_duplicate_outcome_is_not_an_outage |
| A-01-m24 | chain.py | M4: chain reconcile never drains _pending | SURVIVED (rc=0) |  | KILLED: tests/test_a01_extra_proof.py::test_chain_reconcile_drains_memory_only_events_once |
| A-01-m25 | chain.py | M4: chain reconcile drains _pending but never removes the event (re-counted every run) | SURVIVED (rc=0) |  | KILLED: tests/test_a01_extra_proof.py::test_chain_reconcile_drains_memory_only_events_once |
| A-01-m26 | local_dir.py | M4: local_dir reconcile never drains _pending | SURVIVED (rc=0) |  | KILLED: tests/test_a01_extra_proof.py::test_local_dir_reconcile_drains_memory_only_events_once |
| A-01-m27 | tick.py | M4: run_tick step isolation removed (a raising step propagates) | KILLED (rc=1) | tests/test_p7_tick.py::test_one_failing_step_lets_the_others_run_and_exits_1 [6 failing] |  |
| A-01-m28 | tick.py | M4: a raising step is no longer recorded as failed | KILLED (rc=1) | tests/test_p7_tick.py::test_one_failing_step_lets_the_others_run_and_exits_1 [6 failing] |  |
| A-01-m29 | chain.py | M4: _drain reports success when the append failed (event dropped from the outbox) | SURVIVED (rc=0) |  | KILLED: tests/test_a01_extra_proof.py::test_chain_reconcile_keeps_an_event_whose_append_still_fails |
