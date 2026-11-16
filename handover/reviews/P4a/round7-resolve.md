Status: resolved (fixes applied to the ticket text as revision 8; not yet re-reviewed)

# P4a BN-17 to BN-19, plan review round 7: resolve (egm-resolve, headless, ordered mode)

Written 2026-11-09 09:09 UTC (14:39 IST) by the resolver (Opus 5.5). Money path: no round cap.
Targets: `handover/tickets/P4a.md` (revision 7 -> 8: build notes BN-17 to BN-19, plus the revision log on line 3) and `handover/tickets/P4b1.md` (BN-35 on line 531 only, as a list of superseded lines).
Findings: `reviews/P4a/round7-design.md` (0 Blockers, 3 Majors M1-M3, 5 Nits N1-N5) and `reviews/P4a/round7-readiness.md` (0 Blockers, 4 Majors M1-M4, 6 Nits). Below, design findings are `D-`, readiness findings `R-`. Readiness nits are numbered R-N1 to R-N6 in the order the reviewer wrote them.
Lead rulings applied as binding (ORDER 189/193): FB-4 stays "book R, raise `UsageMissing`, do not return the reply"; N7-1 reading confirmed (both config-read loaders refuse a paid model module and every module below it, even when allow-listed; operator tool modules outside `hadavin_sdk` stay loadable); PR78 is one pull request; the migration is found by its name ending, expected 0008; the 0008 entry on P3a-2's allow list is yes.

**Nothing was built, run or tested.** I ran only read-only commands: `sed`, `grep`, `awk`, `cat`, `ls`, `date -u`, and `git show`, `git log` and `git ls-tree` against `origin/*` refs in the existing worktree `/home/user/build/B-P3a-2` (one `git fetch -q origin` there). No commit, no push. The ticket edits were applied by one `python3 -I` script of exact-string replacements, each asserted to match exactly once. The counts were then recounted by a second `python3 -I` script (read-only).

## Facts I checked for this resolve (read, not run)

- F1. 78 `models.py`: `Reply.input_tokens` and `output_tokens` are `int = 0`; `Reply.usage` returns `Usage(...)`, whose `__post_init__` raises a plain `ValueError` for a non-int, negative or too-large count. 78 `llm/protocol.py` `checked_count(value, field)`: `None` gives `UsageMissing("absent", field)`; a non-int (a `bool` included), a negative or a count above `MAX_USAGE_TOKENS_PER_CLASS` gives `"invalid"`. 78 `llm/pricing.py` `check_input_plausible(usage, route)` refuses input 0 only when `route.input_usd_per_mtok > 0`; `check_output_plausible(usage, text, calls)` refuses output 0 only when there is text or a tool call. So design M1 is right on every point: a wrapper that reads `Reply.usage` turns a bad count into `ValueError` (row FB-3, wrong class), and a blanket zero refusal would refuse a valid empty reply. `absent` IS reachable, but only through `Reply.model_construct(input_tokens=None)` or a stub without the attribute; I defined it rather than dropping it.
- F2. 79 `meter.py` `Meter._settled`: every row that is not `released` gets status `"settled"` and `charged = settled_usd`. An `expired` row has `settled_usd = reserved_usd` (79 `store/memory.py` sweep), so a refused settle of an `expired` row returns `Settled(id, "settled", R, applied=False, overshoot=0)`. 79 `Hold.record(None, measured=False)` cannot raise (both arguments accepted); a new `Hold` already plans "settle at R" (`_actual = None`, `_release = False`).
- F3. `origin/core/P3a-2` head is 6f2493a (also the newest commit in `/home/user/build/B-P3a-2`). Its `store/migrate.py` `_check_read_back` (lines 459-517) compares every trigger that existed before a file (enabled state, definition, function text, security mode, settings) and refuses any change; a trigger the file creates is checked only for `D` or `R`. There is NO allow list on that head (ORDER 186 was given at 08:22 UTC; the build note BN-P3a-2-g does not exist in `tickets/P3a.md` yet). The snapshot `/home/user/build/snap/P3a-2-2b0941b` is older and has neither the trigger check nor an allow list. ORDER 186 (LEAD-ORDERS.md line 1216) keys an entry by "migration stem + TRIGGER name + one-line reason"; the ticket wrote the FUNCTION name.
- F4. 79 `0006_spend_reservations.sql`: function `hadavin_spend_reservations_update()` (line 41) is used by trigger `spend_reservations_update` (line 66). 0006 and PR76's 0007 (`origin/core/P2a-1`, lines 47-75) each create every trigger and trigger function they touch in the same file; none of 0001-0005 creates a trigger on `spend_reservations` or `kill_switch`. So by F3 neither file needs an entry, and 0008 does (its `CREATE OR REPLACE FUNCTION` changes the function text of a trigger that existed before the file, on a fresh database and on an upgrade alike). Separately, P2a-1's `migrate()` rewrites the trigger function `hadavin_kill_switch_guard()` on every run (`origin/core/P2a-1` `store/migrate.py` `_GUARD_FN`, line 150); whether P3a-2's read-back spans that step is UNVERIFIED and is P2a-1's matter (ORDER 186: "P2a's ... file gets its own allow-list entry when P2a lands").
- F5. 78 `tests/contracts/kinds/store_postgres.py` `pg_schema(migrated, runtime)`: `migrated=False` skips only the first, role-less `migrate`; with `runtime=True` it creates three logins and runs `migrate(scoped, runtime_role=..., purge_role=..., reset_role=RESET_GROUP)` regardless (lines 46-58), and records `OWNER_DSN[runtime_dsn]` and `PURGE_DSN[runtime_dsn]`. 78 `store/migrate.py` `migrate` calls the module-level `_migration_files()` at line 519 and returns the list of stems it applied (line 614). So patching `_migration_files` BEFORE the fixture shortens the fixture's own run too: readiness M1's runtime-role leg is buildable with `pg_schema(migrated=False, runtime=True)`.
- F6. 79 `tests/contracts/kinds/store_postgres.py` `_open_split` (lines 85-86) builds a postgres store with `make("store", PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn"), FakeSecretProvider({"pg-dsn": dsn}))`; 79 `tests/contracts/test_store_reserve.py` `_run` makes the run row with `create_run(Run(agent_id=..., principal_id="p", trigger_kind="event", trigger_ref="t"))` and `_reserve` calls `reserve_spend(rid, agent, utc_today(store), Decimal(amount), day_cap=..., month_cap=..., run_id=..., run_cap=...)`.
- F7. 78 `tools.py`: `_LOADERS` (lines 279-295) and the name walk inline in `_reach_problems` (lines 312-342; stops at the first hit; `re.compile` allowed). No shared function exists today.
- F8. Rule attribution for the SG-T11 self-tests, by reading the rules as written: cases 2 (`importlib.import_module("<paid name>")`) and 9 (`__import__("<paid name>")`) are reported by BOTH (a') (the string) and (c') (the loader name). So SG-M18 (a' ignores strings) survives case 2, and SG-M20 (c' not applied) survives case 9, unless the self-test asserts the exact rule set. Readiness M4 is right.
- F9. `grep -rnwE 'pickle|marshal|ctypes|ImportString|dictConfig|fileConfig|logging\.config|unittest|mock|shelve|dill|cloudpickle|cffi'` over 78 and 79 `src/hadavin_sdk/`: no hit. So a source-only extra loader list costs no existing code.
- F10. 78 `actions/executor.py` `resolve`: its first statement is `module, _, name = ref.partition(":")`; the `check_modules` test and `importlib.import_module` follow. 78 `tools.py` `load_tool_module`: the first statement after the docstring is the `pin` lookup; nothing is read or imported before it.
- F11. 79 `store/memory.py` `_close` line 331 already returns `applied=False` for a `settled` or `released` row, so FB-M6 (a replay applies a lower amount) is killed by P4d's code today.
- F12. 78 `tests/test_k5_fixes2.py` lines 261-286: the names 0005 to 0008 there are made-up renamed files written into `tmp_path` from the real 0005 to 0007; none is the new file. `_REAL[:4]` keeps 0001-0004 whatever is added.
- F13. `P4b1.md` lines 48, 103, 142, 364 and 400 each still say a settle of an `expired` row is allowed "in either direction" or "from `open` or `expired`" (read). Line 287 (B4) still lists "zero" as a garbage form.

## Findings, in severity order (merged groups)

### Group A: row FB-4 cannot be built as worded (D-M1, Major)
- AI Suggestion: **PROPOSE FIX** (F1). Lead ruling kept: book R, raise `UsageMissing`, never return the reply.
- Edit applied: row FB-4's "books" cell states the derivation: (a) raw `input_tokens` and `output_tokens` through `checked_count` (`getattr(reply, ..., None)`), never `Reply.usage`; (b) `check_input_plausible(u, route)` and `check_output_plausible(u, reply.text, reply.tool_calls)`; (c) a zero those accept is not refused (empty reply with output 0; input 0 on a route whose input price is 0); the first failure in the order input count, output count, input check, output check is raised; `absent` is DEFINED (attribute missing or `None`); `unpriced_class` is never raised by the wrapper. FB-T4 lists the exact forms (each field: `None`, `-1`, `True`, `1.0`, `"5"`, cap + 1; two zero forms; a non-`Reply` stub) and two passing sub-rows (empty reply books exactly 12,000; input 0 on a zero-input-price route books exactly 150). New mutants FB-M4c (blanket zero refusal; killed by the empty-reply passing row), FB-M4d (reads `reply.usage`; killed by the reason and `error_class` assertions), FB-M4e (output check skipped; killed by the `"hi"` sub-row). `P4b1.md` BN-35: line 287's form list superseded.

### Group B: stale expired-row lines in P4b1.md and the planned-below-R repair (D-M2, Major; D-N4, Nit)
- AI Suggestion: **PROPOSE FIX** (F2, F13).
- Edit applied: BN-35 names lines 48, 103, 142 (T1.24), 364 and 400 superseded (106 already was), with the replacement rule (at or above R applied, below R refused) and what T1.24 now asserts. Row FB-5 gains the case "planned below R after the row went `expired`": the repair is refused by FB-6, `Meter.settle` returns `Settled(id, "settled", R, applied=False, overshoot=0)`, the row stays at R (safe side); before P4b2-a nothing sweeps, so the repair still applies. FB-T6b asserts that exact `Settled`. D-N4: row FB-2 and BN-35 say `UsageMissing`, `UnpricedUsage` and every class raised after `chat()` was entered are never a releasable "non-billing" error; only a new row of the table could make one.

### Group C: the P3a-2 allow-list entry and its test (D-M3, Major; R-M2, Major; R-N5, Nit)
- AI Suggestion: **PROPOSE FIX** (F3, F4, F12), with one correction the reviewers did not raise: the entry names the TRIGGER `spend_reservations_update` (ORDER 186), not the function.
- Edit applied (row FB-6): the entry is data written at the PR79 rebase with the number taken then; tests derive the stem (`new[0].stem`) and assert exactly one entry for that stem and trigger, no entry for a stem missing from the real list, a fresh `pg_schema()` passing P3a-2's check, and a copy under another stem refused. 0006 and 0007 need no entry from this ticket (F4); P2a-1's own `migrate()` rewrite is P2a's entry per ORDER 186 (stated, not built here). R-M2: P3a-2's allow-list interface does not exist on any branch today (F3), so the sub-row is written against it at build time: a numbered build step (read BN-P3a-2-g and the allow-list file and checker on main at the PR79 rebase, paste path, entry shape and function name into the evidence); if main has no allow list, P4b1-a does not merge and the builder reports. R-N5: the `test_k5_fixes2.py` sentence now says those names are made-up renames in a temporary folder and the builder runs the file; `late_files` has its own tests in P3a.

### Group D: FB-T6b upgrade recipe cannot run the runtime-role leg (R-M1, Major)
- AI Suggestion: **PROPOSE FIX** (F5, F6).
- Edit applied: the recipe patches `_migration_files` FIRST, then `pg_schema(migrated=False, runtime=True)` (its own role-giving `migrate` runs over the shortened list); the reservation is made through a postgres store on the runtime DSN with a run row (`_open_split`, `_run`, `_reserve` patterns); the upgrade `migrate` runs on `OWNER_DSN[rt]` with the same role arguments a deployment passes (user names from `conninfo_to_dict`); the refusals run on both connections. Both legs run.

### Group E: worker-thread and guard sub-rows sit under the wrong test row (R-M3, Major)
- AI Suggestion: **PROPOSE FIX**. The worker-thread sub-rows and the AST guard sub-row are labelled FB-T9b (P4a-2, a `NetworkLLM` test subclass, no meter); FB-T9b now says it kills FB-M9e, FB-M9f, FB-M9g and FB-M9j inside P4a-2; the real-counter sub-row is labelled P4b1-b; the garbage sub-rows are labelled FB-T9 again.

### Group F: the shared loader walk and self-test attribution (R-M4, Major; D-N1, Nit)
- AI Suggestion: **PROPOSE FIX** (F7, F8, F9).
- Edit applied: one named function `hadavin_sdk.tools.loader_name_hits(tree, extra=frozenset()) -> list[tuple[int, str]]` (78 `tools.py` lines 312-342 moved, returns every hit); `_reach_problems` calls it unchanged in effect; SG-T11 passes a source-only `extra` list (`pickle`, `marshal`, `shelve`, `ctypes`, `cffi`, `dictConfig`, `fileConfig`, `ImportString`, `mock`; none in `src/` today, F9). The guard returns `(rule, line)` pairs; each of the now 19 self-tests asserts the EXACT rule set (1, 7, 8, 10: a'; 2, 9: a' and c'; 3-6, 11, 12, 15-17: b'; 13, 14, 18, 19: c'). SG-M17 is re-attributed to 1, 7, 8; SG-M18 to 10 (plus 2 and 9 by exact set); SG-M20 to 13, 14, 18, 19 (plus 2 and 9). New SG-M28 (the `extra` list not passed; killed by 19). D-N1: the text now says rule (c') is a best-effort tripwire and names what stops a paid call when it misses (the `make` refusal, SG-T13, SG-T7, code review). I extended the list rather than only stating the limit because F9 shows it costs nothing.

### D-N2 [egm-design] Nit: SG-T7's `isinstance` passes a wrapper
- AI Suggestion: **PROPOSE FIX**. `app.build` follows the `inner` attribute chain (at most 8 levels; longer is refused) and refuses when it reaches a `NetworkLLM`; P4b1-b's wrapper keeps its inner llm in `inner`. SG-T7 wrapper sub-row (P4a-2); SG-T6d sub-row with the real wrapper (P4b1-b); new mutant SG-M27.

### D-N3 [egm-design] Nit: alert after an FB-5 exit failure; `h.record` raising inside `except`
- AI Suggestion: **PROPOSE FIX** (F2). "The failure alert" states `booked == R` is right in every exit (the row stays open at R when the exit settle fails, and the alert follows `on_settle_failed`), that `h.record(None, measured=False)` cannot raise, and that a hold's default plan already books R.

### D-N5 [egm-design] Nit: counts not re-derived
- AI Suggestion: **PROPOSE FIX**. Recounted by script after the edits (see "Counts after editing").

### R-N1 [egm-implementation-readiness] Nit: FB-M6 leaves the fail-before decision to the builder
- AI Suggestion: **PROPOSE FIX** (F11). Decided: FB-T6 is a regression pin of P4d behaviour (no fail-before), FB-M6 is planted in 79 `store/memory.py` `_close` line 331 and must still be killed; "Who builds what" lists FB-T6 among the pins.

### R-N2 [egm-implementation-readiness] Nit: W fixture depends on how an empty system prompt is framed
- AI Suggestion: **PROPOSE FIX**. FB-T2 first asserts `prompt_bytes([that message], system="") == 4000` as a literal, so a build that frames the system prompt fails there, before 27,360 is used.

### R-N3 [egm-implementation-readiness] Nit: no per-sub-ticket file table
- AI Suggestion: **PROPOSE FIX**. A short table "Files per sub-ticket" follows "Who builds what" (P4a-2, P4b1-a, P4b1-b, P4c-2; new names placed).

### R-N4 [egm-implementation-readiness] Nit: `late_files` untested here; `test_k5_fixes2` hard-codes 0005-0008
- Merged into Group C (F12).

### R-N5 [egm-implementation-readiness] Nit: `executor.resolve` "first statement"
- AI Suggestion: **PROPOSE FIX** (F10). SG-T13 (1) now reads "right after `ref.partition(":")`, before the `check_modules` test and `importlib.import_module`". `load_tool_module`'s "first statement" stays (true, F10).

### R-N6 [egm-implementation-readiness] Nit: recipes otherwise sound
- No action (a statement, not a defect).

## Tally
PROPOSE FIX 16 (7 Majors in 6 groups, 9 Nits; R-N4 merged into Group C), CONTEST 0, DECLINE 0, no action 1 (R-N6), NEEDS LEAD 0. Remaining unaddressed: 0.

## Counts after editing (recounted by a read-only `python3 -I` script over the edited `P4a.md`)
- BN-17 test row ids: 17, unchanged (revision 8 adds sub-rows only).
- BN-17 mutant ids: 39 + FB-M4c, FB-M4d, FB-M4e = 42; 2 renamed, so 40 new. P4b1-b 27 (25 new), P4b1-a 7, P4a-2 8. 27 + 7 + 8 = 42.
- BN-18: 16 test rows (unchanged; SG-T7 and SG-T6d gain sub-rows), 28 mutants (SG-M27 and SG-M28 added; P4a-2 holds 26, P4c-2 SG-M8, P4b1-b SG-M13). SG-T11 self-tests: 19.
- P4a-2 test rows from BN-17 and BN-18: 6 + 14 = 20 (unchanged). P4a-1/P4a-2 body mutant count stays 94, plus 26 BN-18 mutants built in P4a-2.
- `P4b1.md` BN-35 "new in this ticket": -b 26 (revision 7's 23 + FB-M4c, FB-M4d, FB-M4e) + -a 7 = 33.

## NEEDS LEAD (new)
None. Every question was answered by the rulings or by the code. Two items are stated in the tickets rather than escalated, because each has a safe default that needs no decision: (1) P3a-2's allow list does not exist on any branch yet (F3): default written into row FB-6, P4b1-a does not merge until main holds it, and the builder keeps building; (2) P2a-1's `migrate()` rewrite of `hadavin_kill_switch_guard()` against P3a-2's check (F4) is P2a's own allow-list entry under ORDER 186, not this ticket's; the lead may wish to relay it to the P2a-1 and P3a-2 builders.

## What I did not check
- P3a-2's final allow-list code and BN-P3a-2-g text (they do not exist yet); whether P3a-2's read-back spans P2a-1's in-`migrate()` function writes.
- Any run: no test, no Postgres, no `ast` script this round (round 6's `ast` result for rule (c') is carried, not redone; the extra list was checked by `grep -w` only).
- P1m and P4d-c migration numbers (no branch holds them).
- `P4a.md` lines 1-605 and `P4b1.md` outside lines 48, 103, 106, 142, 261, 287, 364, 400 and 531.
