# P1 round 4 correctness review (egm:egm-codebase-details), condensed
Target: tickets/P1.md rev 5 (b13ff07). Verdict NOT CLEAN: 0 blocker, 5 major (C1-C5), 10 minor (C6-C15), 2 nit (C16-C17). All 42 round-3 findings are mapped and fixed in text. Reviewer ran nothing (no shell): every runtime number is UNVERIFIED by the reviewer. Condensed by the lead.

| id | sev | where | problem | fix |
|---|---|---|---|---|
| C1 | Major | P1m tests, fail-before | P1m moves 14 runner/judge tests but the runner has 21 mutants; 5 more killers live in other PR #50 files (`test_pr50_fix_batch.py:343,351`, `batch2:428,454`, `batch3:401`; also `batch3:417,441`). So "each ends KILLED" cannot hold for 5 mutants and the DOCTYPE/ENTITY refusal, `MAX_JUNIT_CHARS` and `pinned=` wiring ship untested. | add the 7 tests and helpers; list all 21 mutants; replace "16, UNVERIFIED" with 21 |
| C2 | Major | P2a coupling, header, Decision 8 | P2a rev 5 still creates `testing/mutation.py`, `tools/mutation_runner.py`, moves the 21 rows and `_pk_tree`: same files as P1m. | state P2a must drop them and depend on P1m; P0e overlap table: conflict |
| C3 | Major | size rule vs P2d SEAM-1 | P2d SEAM-1 (summed NFKD length = MAX) fails under P1's weighted rule (262,144 x U+A516 has W=786,432, refused); P2d Q1 merge order (P1m, P1a, P2d, P1b) contradicts P1 header (P2d scan waits for P1b). | list as cross-ticket conflict for the lead: `* MAX_VALUE_LEN` or change SEAM-1; P1b dependency or P2d order |
| C4 | Major | header, Decision 1, P1c | LEAD-ORDERS 7(3) already drops P1c from v1; the ticket still calls it PENDING LEAD, builds the P1c section and has no v1.1 row. | mark dropped; add v1.1 row with trigger; keep P1c text as non-v1 outline |
| C5 | Major | P1m files/tests | "no suppressions" but moved code carries `noqa S603/S607/S311/S314`, `nosec B314`, `random.Random(7)` (test 764), Windows-only `mklink`/`tasklist` branches. | per item: edit, or lead-accepted exception with reason; rewrite 764 to integer arithmetic |
| C6 | Minor | size rule | ASCII shortcut is `runmap.py:145-146` not 140-141 | fix |
| C7 | Minor | P1m fail-before | "runner: failing tree kill is not caught" ends CRASH with declared type, not KILLED; main-list "runner: crash counts as good" works only via the override dict (`promoted_mutants.py:1801-1850`) | say KILLED or CRASH with declared type; carry the override dict |
| C8 | Minor | re-pointed mutants | 27 should be 28: "table: vendored data file differs from the pin" (`:1346-1352`, test 2068) | add or justify |
| C9 | Minor | Views | `view()` unknown-name error, empty-key behaviour and P1a empty set for invisible-only text undefined | define |
| C10 | Minor | FOLD_VERSION introspection | test misses `MappingProxyType`, `re.Pattern`, float, other non-callable globals; limits that change no key (`TEXTNORM_MAX_CHARS`) must not bump the fold version | extend test; keep non-key limits out of `beh` |
| C11 | Minor | caller rules | ALLOW caller rule conflicts with the lint ban on `except`; "propagating is the refusal" unsaid; line 76 old `scan` name; `ScanBudgetExceeded` never raised | fix wording; remove class or say where raised |
| C12 | Minor | P1c | `parse_stored_form` returns 5 strings for a 4-field record; unsalted verification, salt provenance and Security notes missing | fix (non-v1 outline) |
| C13 | Minor | Decision 8 | `defaults.py` ordered "P1a then P2d" but missing from overlap list; CHANGELOG order missing | add |
| C14 | Minor | Decision 4 | departures from A13(4), F4, A14(3), order 5(d) not flagged | cite them |
| C15 | Minor | evidence commands | runs a P1b-only test for every P1x; interpreter for mutant runs unnamed; `extra_dirs` for tools unstated | per-PR file list |
| C16 | Nit | tests | test 2529 "moved" by both P1m and P1a; helpers `decode`, `VECTORS`, `FIX`, `Path` not listed | fix |
| C17 | Nit | vendoring | sum 10,864 not "about 10,700"; 13.6 % not 13 %; "670 digits" unclear | state |
