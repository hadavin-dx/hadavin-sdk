# P3a round 7: disposition (ticket revision 9)

Written 2026-11-05 20:00 UTC = 2026-11-06 01:30 IST by the drafting agent (times in UTC and IST). It answers `handover/reviews/P3a-round7-resolve.md` row by row. The lead runs the EGM review of revision 9; I did not review my own work.

## What was and was not run

- Run: read-only commands (`grep`, `sed -n`, `awk`, `wc`, `diff`, `git diff --stat ce70eb5 HEAD -- src tests .github`, `git tag`) and one Python script in the scratchpad that edited `tickets/P3a.md` and checked counts. Nothing else.
- NOT run: no SQL, no repository code, no pytest, no repository script, no mutation run. `psycopg` is not installed in this session, so `check_grants` and `migrate()` were NOT run, and nothing in revision 9 about their behaviour is a test result.
- Code is read-only at core `ce70eb5` (`git diff --stat ce70eb5 HEAD -- src tests .github` was empty; `git tag` is empty).
- Edited files: `handover/tickets/P3a.md` and this file. Nothing else.

## Counts (printed arithmetic)

- Finding ids: 15 (ADV-R7-1 to 15) + 12 (COR-R7-1 to 12) = 27.
- Resolve table rows: 27 ids - 8 ids merged into other rows = 19 rows. The merges: ADV-R7-4 + COR-R7-1 (1 saved), ADV-R7-5 + COR-R7-2 (1), ADV-R7-7 + COR-R7-6 (1), ADV-R7-10 + COR-R7-8 + COR-R7-9 + COR-R7-10 + COR-R7-12 (4 saved), ADV-R7-13 + COR-R7-11 (1): 1 + 1 + 1 + 4 + 1 = 8 saved. 27 - 8 = 19. The resolve file itself says "table rows 21" and "PROPOSE FIX 20"; its table has 19 rows (I counted them), and 20 matches neither 17 rows nor 25 ids. I follow the table, not the sentence.
- By row: 18 applied, 0 contested, 1 declined (ADV-R7-6; the resolve calls it "CONTEST in part" and decides DECLINE). COR-R7-7 sits in the table as MOOT; it is counted as applied (its cause, the `U&"` rule, is cut). Two rows are applied "narrowed" (ADV-R7-2, ADV-R7-7/COR-R7-6) and three are applied as cuts (ADV-R7-8, ADV-R7-15, and the two rules inside ADV-R7-2).
- By id: 26 applied (including COR-R7-7 applied as moot), 0 contested, 1 declined (ADV-R7-6) = 27.
- Mutants: 111 distinct mutants under 79 ids (ticket count table: 96 - 11 + 26 = 111; ids 10 + 15 + 6 + 11 + 8 + 11 + 3 + 15 = 79; 111 - 79 = 32 = 12 + 8 + 12 for M25, M26, M27). The earlier plan in my notes said 115 and then 113; COR-R7-3 retires two more (row count, relation existence), and I recounted from the final text by script: 111. Revision 8's 96 were distinct mutants under 56 ids (script on the revision 8 file).
- Tests: 9 FAIL-BEFORE items (1 to 7 as before, 8 and 9 new), 10 test functions (item 4 has two, 4a and 4b). The resolve says "eleven tests"; that does not match, I use 10. Postgres tests H1 to H12 (H11 and H12 new).
- Layer 1: 10 kinds, not the resolve's 9 (13 listed kinds minus rules, enum and domain types, comments = 10; sequence settings were part of the relations kind). M27 has 13 sub-mutants (19 - 4 cut - 2 equivalent).

## One row per finding id

| id | status | where in the ticket (revision 9) |
|---|---|---|
| ADV-R7-1 | applied | Interface, `hand_recipe` (first generated line `\set ON_ERROR_STOP on`, constants `RECIPE_COMMAND`, `RECIPE_FIRST_LINE`); Interface, refusal message text; Tests, recipe tests (`test_recipe_order_and_command`, `test_recipe_first_line`); H4 row 3 (no `-X`, `PSQLRC` set); Rollback, runbook rule for every hand step; mutants M78, M79 |
| ADV-R7-2 | applied, narrowed (two text rules cut) | Interface, `migrate()` (read-back of `current_user`, `session_user`, `session_replication_role`, `search_path`, lock, after each file); Interface, lexer rule (d) (cut of the `set_config` and `U&"` rules); Security notes; Tests, `test_readback_stub_connection` and H11; mutants M61 to M67, M70, M71; v1.1 rows V-a, V-e |
| ADV-R7-3 | applied now | Interface, `migrate()` / `_scan` on `statement_text(text, keep_identifiers=True)`; FAIL-BEFORE 8 and 9; mutants M68, M69; Files, existing tests (re-run unchanged); Open point 7 closed |
| ADV-R7-4 | applied (merged with COR-R7-1) | First paragraph (evidence labels SAVED, R6-UNSAVED, UNVERIFIED; the ticket now cites the probe files); lexer and rule (d) text; every old "run on 16.15" claim carries a label; `x[1:n]` marked summary-only and UNVERIFIED until command 7h |
| ADV-R7-5 | applied (merged with COR-R7-2) | Tests, `test_e_string_and_dollar_cases` and the exact output form of `statement_text`; the three NOT-refused cases; mutants M72, M73 (and M26(d)) |
| ADV-R7-6 | declined (resolve: contest in part, decline the differential test) | Interface, last lexer bullet (why `pglast` is not used, not even as a test); v1.1 row V-c. Reason: the lexer rests on the real server, a stronger oracle; the library would add a test dependency. The resolve's remark that the library is the PostgreSQL 17 parser is carried as UNVERIFIED by me |
| ADV-R7-7 | applied, narrowed (merged with COR-R7-6) | Interface, rule (e) (`ALTER TABLE` plus `DISABLE TRIGGER` / `ENABLE REPLICA TRIGGER`; `ENABLE ALWAYS` stays allowed); layer 1 compares `tgenabled`; planted case; mutants M75, M76, M77 |
| ADV-R7-8 | applied (cut) | Interface, rule (c) (no `BEGIN ATOMIC` rule, reasoning stated as not run); M25 13; v1.1 row V-f |
| ADV-R7-9 | applied | Mutation plan wording ("mutant ids" and "distinct mutants"), retired ids M5, M30, M39, M40, M53, M54, M58, M34b renamed M74, count table with printed arithmetic, "nine FAIL-BEFORE items, ten test functions" |
| ADV-R7-10 | applied (merged with COR-R7-8, 9, 10, 12) | Hot files item; `ACCEPTED_CHANGES` item (key `(object_name, package_id)`, value `{reason, test}`); coupling table (P4d, P2a-1, P4b2-b, P4c-1, P5a rows); Open points 16, 17; other tickets cited by item name |
| ADV-R7-11 | applied | Interface, `hand_recipe` case 2 (`RECIPE begins` / `RECIPE ends`, control characters); `test_recipe_refuses_markers_and_control_characters`; M80, M81 |
| ADV-R7-12 | applied | Tests, `test_gone_message_names_escaped`; M60. Note: "one line per orphan" in the resolve is one line per case in the real message |
| ADV-R7-13 | applied (merged with COR-R7-11) | `hand_recipe` case 1 (stem against `STEM`) and case 3 (`:{`, `:'`, `:"`, letter, underscore, non-ASCII); tests; M82, M83 |
| ADV-R7-14 | applied, narrowed | Tests, `test_lexer_is_linear` (ratio harness of `tests/test_k5_perf.py`, marked `perf`); evidence command 3b; M86 |
| ADV-R7-15 | applied (cut) | Layer 1 item (10 kinds), planted cases, M27 13 sub-mutants; Open point 15; v1.1 row V-d |
| COR-R7-1 | applied (merged into ADV-R7-4) | as ADV-R7-4 |
| COR-R7-2 | applied (merged into ADV-R7-5) | as ADV-R7-5 |
| COR-R7-3 | applied | Layer 1 mutant item: 13 sub-mutants, one isolating plant each (column plant `runs.reason_code`, UNVERIFIED that it isolates); "row count" and "relation existence" retired as equivalent |
| COR-R7-4 | applied | `hand_recipe` (line feed before each `INSERT`, `;` separator only for an unterminated last statement, probe P4); `test_recipe_trailing_comment`, `test_recipe_unterminated_last_statement`, H12; M84, M85 |
| COR-R7-5 | applied | Layer 1 item: structural kinds A to U and U to F; seeded rows only in U against the seed values |
| COR-R7-6 | applied, narrowed (merged into ADV-R7-7) | as ADV-R7-7 |
| COR-R7-7 | applied as moot | The `U&"` rule is cut (rule (d) text); no quoted-spelling rule remains |
| COR-R7-8 | applied (merged into ADV-R7-10) | Hot files item and `ACCEPTED_CHANGES` item cite P2a/P4b2 by item name |
| COR-R7-9 | applied (merged into ADV-R7-10) | Hot files item (overlap 2), coupling table, Open point 17: two builders, not stated as agreed |
| COR-R7-10 | applied (merged into ADV-R7-10) | Coupling table rows for P4c-1, P4b2-b, P5a; Open points 16 and 17. The P4b2 `cli.py: P3a` claim and the P2a Python-step order are the resolve's statements; I did not locate them (UNVERIFIED) |
| COR-R7-11 | applied (merged into ADV-R7-13) | as ADV-R7-13; name characters in scope are stated, the digit and non-ASCII claims are the reviewer's (UNVERIFIED) |
| COR-R7-12 | applied (merged into ADV-R7-10) | `test_k2_migrations.py:29-33` (read); the P4b1 sentence replaced by a cite to `P4d.md` item "Hot files" |

Check: 15 + 12 = 27 rows above; applied 26 + declined 1 = 27.

## New and changed PENDING LEAD items

- 15: layer 1 compares 10 kinds (the resolve says 9); cut decided under order 6(g), recommend accept.
- 16: order of the pull requests that edit `store/migrate.py` (P2a.md and P4b2.md disagree).
- 17: one schema builder or two (P3a and P4d-a1); also the P4c downgrade-read gap and the P5a `config_invalid` claim.
- Open point 7 is closed (no longer a PENDING LEAD). Items 8 to 14 stand.
- v1.1 rows added with triggers: V-a, V-b, V-c, V-d, V-e, V-f. The row "`_scan` switched to `statement_text`" is removed because that fix is in the package.

## Where I disagree with, or could not follow, the resolve

1. Row and id arithmetic: the resolve says 21 rows and "PROPOSE FIX 20"; its table has 19 rows and 27 ids. Its severity split for the adversarial review (6 major, 8 minor in the text) also differs from the adversarial report's own table (8 major, 7 minor, as I read it). I did not restate either.
2. "13 kinds become 9": it is 10 by my count (see Counts).
3. "Eleven tests": 10 test functions in 9 items.
4. "One line per orphan" (ADV-R7-12): the real `gone_message` prints one line per case, not per orphan.
5. `config_invalid` (COR-R7-10 (vi)): no such error class exists in `src/` (`grep -rn config_invalid src` finds nothing); I did not write it into the ticket and put the question in Open point 17.
6. COR-R7-3 retires two M27 sub-mutants, so the mutant count is 111, not the roughly flat count the resolve expected.
7. A lock-release mutant for the read-back (my own first idea) is not listed: a transaction-level advisory lock is probably not released by `pg_advisory_unlock`; not probed (UNVERIFIED). The stub-connection case (no lock row) is the killer.
8. The abort-probe file `evidence/P3a-abort-commit-probe.md` holds output only (its SQL, `/tmp/r67.sql`, is missing). The resolve says the file is "amended"; I may edit only two files, so I did not touch it. The lead adds the SQL, or evidence command 7g repeats the probe with its SQL saved.
9. `tests/test_migrate_regex_linear.py` uses an absolute bound (1.0 s on 60,000 characters), while the comment in `ci.yml` before the perf step describes a ratio. For `test_lexer_is_linear` I follow the ratio harness of `tests/test_k5_perf.py` (64 and 256 KiB, ratio 12, floor 0.06 s, minimum small run 0.004 s). Which style the lead wants is a small open choice.

## UNVERIFIED (short; the full list is the last section of the ticket)

`check_grants` and `migrate()` were not run (no `psycopg`); the existing grant-scan tests staying green after `_scan` moves to the lexer; every server result on 17.10; the lock key split (`classid`, `objid`, `objsubid`); that H11 plant 3 changes `current_user`; `x[1:n]` with `n` unset; that the `runs.reason_code` plant isolates the column comparer; the resolve's statements about P2a, P4b2 and `pglast` that I could not locate.
