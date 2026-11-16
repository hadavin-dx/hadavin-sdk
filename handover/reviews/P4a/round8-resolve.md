Status: resolved (fixes applied to the ticket text as revision 9; not yet re-reviewed)

# P4a BN-17 to BN-19, plan review round 8: resolve (egm-resolve, headless, ordered mode)

Written 2026-11-09 09:26 UTC (14:56 IST) by the resolver (Opus 5.5). Money path: no round cap.
Targets: `handover/tickets/P4a.md` (revision 8 -> 9: build notes BN-17 to BN-19, the revision log on line 3, words added to line 1 and to BN-14 on line 592) and `handover/tickets/P4b1.md` (lines 5, 262, 265-268, 274, 282, 287, 326, 328, 341, 355, 413, 419 and BN-35 on line 531).
Findings: `reviews/P4a/round8-design.md` (0 Blockers, 6 Majors R8-1 to R8-6, 9 Nits R8-7 to R8-15) and `reviews/P4a/round8-readiness.md` (0 Blockers, 5 Majors R8-1 to R8-5, 7 Nits R8-6 to R8-12). Below, design findings are `D-R8-n`, readiness findings `R-R8-n`.
Binding decisions from the lead's brief, applied: a build-step branch for "main has no function-text check" with a stated outcome (P4b1-a does not merge, the builder reports) and a named owner; ONE fix for the `defaults.py` conflict, with self-tests and mutants; the FB-6 upgrade list is a PREFIX of the real files below N; one mutant per FB-6 guard behaviour; FB-5's planned amount per FB-9 branch; rung rows (UNVERIFIED allowed, each with a verdict); every stale `P4b1.md` line of R-R8-3 edited to a pointer.

**Nothing was built, run or tested.** Read-only commands only: `sed`, `grep`, `awk`, `cat`, `ls`, `wc`, `date -u`, and `git show`, `git log`, `git ls-tree`, `git merge-base`, `git for-each-ref` against `origin/*` refs already present in the worktree `/home/user/build/B-P3a-2` (no fetch). No commit, no push, no process left running. The edits were applied by one `python3 -I` script of exact-string replacements (each old string asserted to occur exactly once; line-level edits of `P4b1.md` asserted on the line's opening words), plus one more single replacement; the revision 8 files are kept in the scratchpad (`rev8/P4a.md`, `rev8/P4b1.md`). Counts were recounted by a second, read-only `python3 -I` script.

## Facts I checked for this resolve (read, not run)

- F1. `origin/core/P3a-2` in `/home/user/build/B-P3a-2` points at c727453 (committed 2026-11-09 08:48:56 UTC, "trigger read-back with a reviewed allow list"), not 6f2493a as round 7's F3 said. I did not fetch: the ref was already there. Round 7's statement "that head has no allow list" is therefore stale. On c727453: `store/migration_numbers.py` line 77 `TRIGGER_CHANGES = MIGRATIONS.parent / "migrations_trigger_changes.json"` (file content `[]`); `store/migrate.py` `_trigger_changes()` (line 421) reads a JSON list whose entries have exactly the keys `migration` (stem), `trigger`, `reason` (one line) and refuses any other shape; `_check_read_back(db, saved, file_name, allowed_triggers)` (line 512) compares every trigger that existed before a file on enabled state, definition, md5 of the function text, security mode, owner and settings (`_READBACK_TRIGGERS_SQL`, lines 401-407), allows a change only when the trigger NAME is listed for that file's stem (line 534, `key[2] in allowed_triggers`; line 711), and its refusal text names the trigger and says "changed a trigger ... changed: function text". `migrate()` refuses a superuser or CREATEROLE/CREATEDB/BYPASSRLS migration role (`_ROLE_FLAGS`, line 383); tests run it through `tests/fixtures/migration_role.py` as a plain role. The commit message says `SET LOCAL lock_timeout/statement_timeout` is refused by the text scan.
- F2. `git merge-base --is-ancestor origin/core/P3a-2 origin/main` is false; `origin/main` (2a8c2aa, 08:56 UTC) holds migrations 0001-0005 and no P3a-2 code. `P3a.md` on disk still says the opposite of F1: limit (b) ("a file that replaces a trigger FUNCTION ... is not caught") and v1.1 row V-g (line 197); it has build notes BN-P3a-2-a to -e only, no -g. So readiness R8-2 is right: the contradiction exists, between `P3a.md` and P3a-2's code.
- F3. `P3a`'s `released_problems(MIGRATIONS, ...)` (c727453 `migration_numbers.py` line 334) reads the folder on disk, not the patched `_migration_files` list, so a copy in `tmp_path` and a shortened list do not trip it.
- F4. 79 `0006_spend_reservations.sql`: `closed_at` line 15, `expired_at` line 16, CHECKs lines 18-21; the function header line 41 has no `SECURITY DEFINER` and no `SET`; the open-to-expired rule is lines 50-53; the expired branch lines 56-59 allows `settled` and `released`; every refusal is `RAISE EXCEPTION 'spend_reservations: change refused'` (lines 31, 48, 52, 58, 61); line 3 is `SET LOCAL lock_timeout = '10s';`.
- F5. 79 `store/postgres.py` `_close` (lines 615-660): the claim is one `UPDATE ... WHERE reservation_id = %s AND status IN ('open', 'expired') RETURNING *`; zero rows read the stored row (line 626) and return `applied=False`. 79 `store/memory.py` `_close` line 331 refuses only `settled`/`released`, under the store's lock.
- F6. 78 `store/migrate.py`: `reset_role` is required (lines 479, 522-524), `runtime_role` optional; the "applied migrations have no file in this release" check (lines 547-553) runs before any role check (line 569). So the old-code sub-row's call is valid (D-R8-12).
- F7. `origin/core/P2a-1` `store/migrate.py` `_install_kill_switch` re-issues `_STOP_FN`, `_RESET_FN`, `_GUARD_FN` in a loop (line 195): a Python step. On c727453 the read-back runs only after each file inside the apply loop (lines 704-712). Whether P2a-1's step lands outside that loop on main: UNVERIFIED.
- F8. `run_mutants` on `origin/main` `tools/mutation_runner.py` (line 365) has no `conftest`, `pass_env` or `forbid_skips`; branch `origin/core/mutation-runner-keywords` (08:48 UTC) has all three (`forbid_skips: bool = False`).
- F9. 78 `defaults.py` and `scrub_settings.py` docstring: `tools.py` must not import `config.py` (and through it the kind table), pinned by a repo test. So the readiness/design R8-4 conflict is real: SG-T13 puts the paid names in `defaults.py`, rule (a') forbids those strings outside `backends/table.py`.
- F10. 78 `pyproject.toml`: ruff `extend-select` holds `TID`, `ban-relative-imports = "all"`; no `banned-api` list; `tenacity` is not a dependency (and no hit in `src/`).
- F11. `grep` of 78 `tests/` and `demos/`: no `Mock`/`MagicMock` llm passed to `app.build` (D-R8-9).

## Findings, in merged groups (severity order)

### Group 1: `defaults.PAID_KIND_MODULES` against rule (a') (D-R8-4 Major, R-R8-1 Major; same defect)
- AI Suggestion: **PROPOSE FIX** (F9). One fix chosen: an exact EXEMPTION in rule (a') for the one module-level assignment `PAID_KIND_MODULES = frozenset({...})` in `defaults.py` (a `frozenset` call over one set or tuple display of string constants); every other paid-module string in `defaults.py`, and the same assignment in any other module, is still reported. Rejected: building the names from parts (it hides them from the very rule (a') exists for) and deriving from the kind table (`tools.py` may not import it, F9).
- Edits applied: rule (a') text; SG-T13 note; SG-T11 self-tests (20) exempt shape not reported, (21) a second paid string in `defaults.py` reported [a'], (22) the exempt assignment in `tools.py` reported [a']; the guard takes each made-up module with a path; mutants SG-M29 (exemption covers all of `defaults.py`; killed by 21) and SG-M30 (exemption keyed on the target name in any module; killed by 22).

### Group 2: FB-T6b upgrade and allow-list recipes; the P3a-2 contradiction (D-R8-1 Major, D-R8-2 Major, R-R8-2 Major)
- AI Suggestion: **PROPOSE FIX** (F1, F2, F3) and one **NEEDS LEAD** item (PENDING LEAD 80).
- Edits applied ("FB-T6b recipes" below the table, items 4-7): the shortened list is `old = [p for p in real if int(p.name[:4]) < n]`, a PREFIX, so no gap whatever lands after the new file; step (6) returns exactly `rest` (the new stem and every later one); the old-code sub-row uses the same prefix and expects every stem of `rest` named. The allow-list copy is written at the SAME number N under another name (`NNNN_copy_of_expired_guard.sql`) and run with `old + [copy]`; the test asserts the refusal names `spend_reservations_update` and says the trigger changed, and names no number, gap or missing file. Build step (item 7) states what c727453 holds (file, entry shape, loader and checker names, the exact entry this ticket adds) and three branches with outcomes: (i) check and allow list on main: write entry and sub-row; (ii) check without allow list: P4b1-a does not merge, builder reports; (iii) NO function-text check on main (what `P3a.md` says): P4b1-a does not merge, builder reports. Owner of the contradiction: the lead (ORDER 186); P3a-2's builder writes BN-P3a-2-g. Row FB-6's "head 6f2493a, no allow list" sentence is corrected to c727453.

### Group 3: FB-5 planned amount per FB-9 branch; silent refusal of a slow healthy call (D-R8-3 Major, D-R8-14 Nit)
- AI Suggestion: **PROPOSE FIX**.
- Edits applied: row FB-5 states `planned` per row and branch (None for FB-2/3/4 and FB-9 not proven with answered <= R; `answered` for not proven with answered > R; `answered + u x W` for proven, below, at or above R; `answered` for attempts == 1); "never below R" is limited to ambiguous calls; the expired-row paragraph adds attempts == 1. New FB-T5c third variant (proven answered below R, `CounterDamaged`, repair applies and the counters fall by exactly `R - answered`) and mutant FB-M5d (planned below R raised to R). D-R8-14: the slow-call refusal's signal is named (the store's FB-6 WARNING by `hadavin_sdk.store` with the reservation id, asserted by FB-T6b, and `Settled.applied == False`; no alert, it is not a failure). No new code for the signal.

### Group 4: missing mutants (D-R8-5 Major, R-R8-5 Major, R-R8-6 Nit)
- AI Suggestion: **PROPOSE FIX**.
- Edits applied: one mutant per FB-6 guard behaviour, each tied to an FB-T6b assertion: FB-M6b (memory lower settle, existing), FB-M6e (memory release), FB-M6f (postgres `_close` lower settle), FB-M6g (postgres `_close` release), FB-M6c (trigger lower settle, existing), FB-M6h (trigger release), FB-M6i (allow-list entry missing or naming the function), FB-M6j (postgres guard read before the `UPDATE`; Group 6). FB-M10 (reserve does not raise the counters; FB-T10). FB-M9k (`started == retried + answered` dropped; the FB-T9b swallowed-failure sub-row now makes two `_retry` calls so `answered == 1`). FB-M2i (`failure_booked` does not catch the callback's exception; FB-T2 raising-spy sub-row).

### Group 5: rung table gap (D-R8-6 Major, R-R8-4 Major)
- AI Suggestion: **PROPOSE FIX** (F10).
- Edit applied: "Rung table for BN-17 and BN-18" at the end of BN-18, pointed to from BN-14: rows for the P4b1-b wrapper, `reserved_factor`, the retry counter, the stage gate, SG-T11's import half and its other rules, the FB-T5b guard, the FB-6 store guard and migration, the failure alert and `loader_name_hits`. Verdicts: KEEP-CODE throughout except the alert's delivery (CUT-TO-CONFIG+GLUE, in P4c-2) and `loader_name_hits` (KEEP, moved). The ruff `TID251` option for the import half is recorded with its evidence UNVERIFIED and rejected for a stated reason (a second, static copy of the paid set; the import half is one of three rules). If the lead disagrees with any verdict, the row is where to change it.

### Group 6: migration and store-guard detail (D-R8-7, D-R8-8, D-R8-11, D-R8-12 Nits; R-R8-8, R-R8-9, R-R8-10 Nits)
- AI Suggestion: **PROPOSE FIX** (F4-F8), plus **NEEDS LEAD** relay 81 for R-R8-10.
- Edits applied ("FB-T6b recipes" items 1-3, 5, 8, 10): transition table of the new function against 0006; header unchanged (no `SECURITY DEFINER`, no `SET`), owner kept, no `SET LOCAL` line, same error text and SQLSTATE `P0001`; the builder runs P3a's checks on the file first (D-R8-8). Postgres `_close` guard inside the claiming `UPDATE`'s `WHERE`, with a two-connection race sub-row (D-R8-7) and FB-M6j. Test placement: both-store rows in `tests/contracts/test_store_reserve.py`, the race in `tests/contracts/test_store_reserve_pg.py`, trigger/upgrade/allow-list rows in a new `tests/test_spend_expired_guard_postgres.py` (D-R8-11). Columns cited from 0006 (D-R8-12); the old-code call confirmed valid (F6); the upgrade sub-row also asserts `proowner`, `prosecdef`, `proconfig` unchanged. Exact pytest command, raw-output paths, and the `run_mutants(..., pass_env=..., forbid_skips=True)` syntax with a fallback if the keywords are not on main (R-R8-9, F8). P2a-1's in-`migrate()` rewrite: owner P2a-1's builder, with a two-run test (R-R8-10, F7).

### Group 7: stale `P4b1.md` lines (R-R8-3 Major)
- AI Suggestion: **PROPOSE FIX**.
- Edits applied: lines 266, 267, 268, 282 and 287 are now pointers to FB-9, FB-4 and FB-T9/FB-T4; line 265 says the wrapper reads raw counts through `checked_count`, never `Reply.usage`; line 262 drops "P4a's `Price`"; lines 274, 355, 413 and 419 name P4a-2 as the builder of `Reply.unknown_attempts: int | None = None`; W19 (line 328) and W17 (line 326, same cause: R4d-2 is now a pointer) name FB-T9 as the killer; line 341 counts the W ids and the 27 new -b mutants; line 5 now says truthfully which lines were edited and which are superseded by BN-35 only (27, 48, 52, 76, 103, 106, 142, 260, 269, 273, 278, 364, 400); BN-35 updated (revision 9, mutant lists, 27 + 15 = 42 new, PENDING LEAD 69/80/81).

### D-R8-9 [egm-design] Nit: `Mock` has an endless `inner`
- AI Suggestion: **PROPOSE FIX** (F11). SG-T7 states the refusal is intended, the grep result, and the rule that every future llm wrapper keeps its inner in `inner` (SG-M27 covers only P4b1-b's).

### D-R8-10 [egm-design] Nit: FB-T4 companions, `AttributeError` path, FB-M4e description
- AI Suggestion: **PROPOSE FIX**. Companion counts named; a FB-T3 sub-row pins a stub without `text`/`tool_calls` (row FB-3, R, alert `error_class == "AttributeError"`); FB-M4e's description corrected (books R through FB-9 and returns the reply; killed by the `UsageMissing` assertion).

### D-R8-13 [egm-design] Nit: more guard mutants, message pin, stated intent
- AI Suggestion: **PROPOSE FIX**. SG-M31 (`**` accepted, self-test 6), SG-M32 (factory-attribute half of (c'), self-test 18), SG-M33 (`re.compile` exception dropped, real-tree run); `_reach_problems` message pinned as a literal; "a `SRC_EXTRA_LOADERS` name in `src/` fails hard" stated as intended.

### D-R8-15 [egm-design] Nit: table cells too long
- AI Suggestion: **PROPOSE FIX for row FB-6** (the longest cell, about 11,400 characters, whose recipes I rewrote anyway: moved to "FB-T6b recipes"); **CONTEST for rows FB-1, FB-2 and FB-9**: moving their text changes no meaning, the reviewers recounted them as correct, and a mechanical move of thousands of words in a money ticket in round 8 risks dropping a clause; the lead may order the move as a separate edit with a before/after word diff.

### R-R8-7 [egm-implementation-readiness] Nit: file-table rows for `limits.py` and `llm/fake.py`
- AI Suggestion: **PROPOSE FIX**. Two rows added (P4a-2 / PR78).

### R-R8-11 [egm-implementation-readiness] Nit: title says 83
- AI Suggestion: **PROPOSE FIX**. Line 1 says the 83 is history and where the current counts are.

### R-R8-12 [egm-implementation-readiness] Nit: FB-8 mutant cell reads as covered
- AI Suggestion: **PROPOSE FIX**. The cell says the SG mutants guard pilot and prod only and the demo-stage gap has no mutant on purpose.

## Tally
27 findings (design 15, readiness 12) in 7 merged groups plus 7 single items. PROPOSE FIX 27 (D-R8-15 only partly: FB-6 moved), CONTEST 1 part (D-R8-15 for FB-1, FB-2, FB-9), DECLINE 0. NEEDS LEAD (new, lead actions with safe defaults): 2 (PENDING LEAD 80 and 81). Remaining unaddressed: 0.

## Counts after editing (recounted by a read-only `python3 -I` script over the edited `P4a.md`)
- BN-17 test row ids: 17 (FB-T1 to FB-T10, FB-T5b, FB-T5c, FB-T6b, FB-T7b, FB-T7c, FB-T7d, FB-T9b), unchanged; revision 9 adds sub-rows only.
- BN-17 mutant ids: 52 (42 + FB-M2i, FB-M5d, FB-M6e to FB-M6j, FB-M9k, FB-M10); 2 renamed (FB-M2a, FB-M2b), so 50 new. Per package: P4b1-b 28 (26 new), P4b1-a 15, P4a-2 9; 28 + 15 + 9 = 52. Per row, by script: FB-1 7, FB-2 9, FB-3 1, FB-4 5, FB-5 4, FB-6 10, FB-7 4, FB-9 11, FB-10 1.
- BN-18: 16 test rows (unchanged), 33 mutants (SG-M1 to SG-M33; P4a-2 31, P4c-2 SG-M8, P4b1-b SG-M13); 22 SG-T11 self-tests.
- P4a-1/P4a-2 body mutant count: 95 (94 + FB-M9k), plus 31 BN-18 mutants built in P4a-2. P4a-2 test rows from BN-17 and BN-18: 6 + 14 = 20 (unchanged).
- FB-T1 cause table: 15 cause lines, 17 sub-rows (unchanged).
- `P4b1.md` BN-35 "new in this ticket": -b 27 (26 + FB-M2i) + -a 15 = 42.
- Line positions: `P4a.md` lines 1-605 keep their count (only lines 1, 3 and 592 gained words); the file grew from 773 to 826 lines, all inside BN-17 to BN-19 and at the end. `P4b1.md` keeps 531 lines.

## NEEDS LEAD (new; each blocks a merge, not the building)
1. **PENDING LEAD 80: `P3a.md` against P3a-2's code on trigger-function changes.** `P3a.md` says such a change is not caught (limit (b), row V-g); c727453 refuses it unless allow-listed. Owner: the lead; P3a-2's builder writes BN-P3a-2-g before P3a-2 merges. Safe default: P4b1-a does not merge until main's P3a-2 holds a function-text check AND an allow list and `P3a.md` says so; the builder keeps building.
2. **PENDING LEAD 81: relay to P2a-1 (PR76).** Run P2a-1's `migrate()` twice on one fresh database with P3a-2's check on; if refused, P2a-1 adds its own allow-list entry. Safe default: PR76 does not merge with a refused second run.

## What I did not check
- Anything by running: no test, no Postgres, no ruff, no `ast` script. The PostgreSQL facts that `CREATE OR REPLACE FUNCTION` needs the owner and keeps it, and that READ COMMITTED re-checks an `UPDATE`'s `WHERE` after a lock wait, are from the documentation as I remember it (UNVERIFIED; the race and upgrade sub-rows test both).
- Whether ruff `TID251` reports `from hadavin_sdk.llm import anthropic`; litellm's budget code; `tenacity`'s cross-thread statistics (rung rows say UNVERIFIED).
- Whether c727453 is what P3a-2 merges; whether `migrate()` on main will still call the module-level `_migration_files()` (78 does).
- 78's `_reach_problems` tests and the exact message text (the sub-row copies it at build).
- `P4a.md` lines 1-605 beyond lines 1, 3, 580-604; `P4b1.md` outside the lines edited; `P4b2.md`, `P4c.md` (not edited).
