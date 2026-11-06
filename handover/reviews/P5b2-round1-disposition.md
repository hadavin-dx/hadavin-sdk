# P5b2 round 1 disposition (revision 1 -> revision 2)

- Applies `reviews/P5b2-round1-resolve.md` (13 decisions, all PROPOSE FIX; C5 partly by cut) to `tickets/P5b2.md`. Source findings: `reviews/P5b2-round1-reviewer.md`. I read the reviewer file only to check the resolve was applied faithfully.
- Result: 13 of 13 applied. Not applied: none. Where I went beyond or differed from the resolve text, it is listed under "Differences" below.
- Ticket: 130 lines -> 163 lines. Template fields: 17, unchanged. Mutant rows: 18 -> 29 (recounted from the table: M1-M13 = 13, M14a, M14b = 2, M15-M18 = 4, M19-M23 = 5, M24a-d = 4, M25 = 1; total 29).
- Nothing was run against the repository (no tests, no generator). All counts are arithmetic on the resolve's figures; they are marked UNVERIFIED in the ticket where they are not grep results.

## Where each decision landed in the ticket

| id | applied how | places in the ticket |
|---|---|---|
| C1 | `class=LITERAL` if and only if `auto_class=LITERAL`; `wrong_literal` defined as XOR; unit (9) case per direction; mutant M19 | Locked rows; `compare` list; unit (9); mutation table |
| C2 | `-I` kept; repo root passed as `argv[1]`; `sys.path.insert` before import; `cwd=` repo root; marker `STDLIB-ONLY-OK`; exit 0 AND marker asserted; M17 killed by the static half | CI test on the real tree; M17 row |
| C3 | `HASH_TRANSPARENT_CALLS = ("t1",)` constant; `t1(X)` replaced by `X` before hashing; unit (5) case; M20; P5b3 requirement; `--carry-from` not built | Constants; column 5; unit (5); P5b3 section; PENDING LEAD 9 |
| C4 | factories detected by rule (returns or raises a site that interpolates its own parameter); each call is a site; `kind` = built class; auto columns over bound arguments; own construction stays a row; factory-through-factory raises `SitesError`; hostile `_fail2` case; M21; Counts | scan (d); hostile inputs; mutation table; Size section; Counts |
| C5 | M22, M23, M24a-d, M25 added with killers; the `os.replace` temporary-file promise deleted from `write()`, from "Existing core code reused" and from the security note | `write()`; mutation table; reused-code and security bullets |
| C6 | taint through any assignment form to a fixed point; `tools.py:120` becomes locked FOREIGN (17 -> at least 18); case added to unit (3) | column 7; facts; unit (3) |
| C7 | hash input is the tokens of the construction's own `Call` node in any context; bare `raise A` hashes `A`; factory call hashes the call; then C3 stripping | column 5; unit (5) |
| C8 | `kind` is the canonical class name; hash keeps the text as written; unit (4) fixes file names `a_sub.py` (`class B(A)`) and `z_base.py` (`class A(ConfigError)`) | column 4; unit (4) |
| C9 | M14 split into M14a (reads non-source files) and M14b (skips subfolders) with their killers | mutation table |
| C10 | `missing_code` renamed `code_mismatch` (FOREIGN with no `code`, OR non-FOREIGN with a `code`); still seven lists | `compare` list; unit (9) |
| C11 | runner puts `Path(__file__).resolve().parents[1]` first on `sys.path` and runs each mutant's pytest in a subprocess with `cwd=` the temporary tree; evidence 3 note on blank `class` and what `cmp` compares | Files (mutants file); evidence 3 and 4 |
| C12 | reworded as the resolve states | column 1 |
| C13 | all six files listed against memo-5 (3 listed there); PENDING LEAD 8 | Files; PENDING LEAD 8 |

## Counts requested by the resolve

- Site counts from revision 1 are kept and labelled "on ce70eb5" (237 lines, 171 constructions in 37 files, 42 / 114 / 15, 17, 112, per-file table).
- New section "Known changes before P5b2 merges" holds the table of changes from earlier packages (P4a-2, P4a zero-price check, P4d, P3a, P4b2, P5a/P5b1) and says that the builder's generator count at the merge base wins, with every difference from ce70eb5 explained in the evidence. PENDING LEAD 5 was extended to say the same.
- Expected table on ce70eb5 after the rule changes (recomputed): 171 + 29 = 200 rows; LITERAL 42; locked FOREIGN at least 18 (17 + `tools.py:120`); human decisions 200 - 42 - 18 = 140 (111 constructions + 29 calls). The resolve says "at most 140"; the same figure. After P4a-2: 202 rows, LITERAL 44, locked 18, human 140. P3a and P4b2 deltas: UNVERIFIED.
- Mutants: 29 (was 18). New PENDING LEAD items: 3 (numbers 8, 9, 10).

## Couplings from the resolve

1. P5a -> P5b2 (`t1` owner after P5a's cut): written as PENDING LEAD 9, recommendation P5b3.
2. P5a ledger rows 005 and 033: added to the appended `tests/test_diagnostics_hostile.py` change in "Files". Note: the resolve cites `tickets/P5a.md:92-93`, but those lines hold P5a's mutation plan and evidence; the rows are named in P5a's Appendix (the "classification 005, 033 (owner R3a, P5b2)" line near line 150) and in line 90. I cite the P5a ticket without a line number. The exact assertion shape stays PENDING P5a.
3. P5b3 inputs (C3 requirement, the 29 `_fail` rows): written into "How P5b3 keeps the table in step".

## Differences from the resolve text (small, all within its intent)

- Unit (3) wording changed from "the first nine" to "every listed form except the last", because the list grew with the derived-value cases.
- The hostile-input list also covers "factory through another factory raises `SitesError`" (stated in the resolve under C4) in the same hostile bullet, with M21 as the killer.
- "Existing core code reused" and the security note lost their `os.replace` / temporary-file sentences, which the resolve's cut implies but does not name.
- Evidence 8 (counts) and the Done line now say the merge-base count is compared with 200 plus the known changes; the FOREIGN > 30 stop reading now says up to 158 rows may start as FOREIGN before review (129 + 29).
- The resolve's own claim "the ticket's 171 / 42 / 114 / 15 / 17 / 112 figures are not re-derived" is carried into the ticket's UNVERIFIED list; I did not re-derive them either.

## Checks I made

- Re-read the resolve table against the ticket after editing: every id has a landing place above (grep for the new names: `HASH_TRANSPARENT_CALLS`, `code_mismatch`, `wrong_literal`, `STDLIB-ONLY-OK` all present; `missing_code` appears only in the revision log as the old name).
- Recounted mutant rows from the table (29) and report lists (seven).
- No model ids, owner names, studio paths or real-looking values were added; the ticket is ASCII.
- Other tickets untouched.
