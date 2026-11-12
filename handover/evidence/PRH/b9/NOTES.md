# PR H batch 9 (round 8 resolve) builder notes

Branch core/prh-b9 from b8fbf659, pushed to wip/cloud-prh-b9. Failures and not-run items are in the lead report first. Words: a SPACED-OUT secret is a secret written with a gap between its characters. A MUTANT is a planted fault in the code that a test must catch.

## What changed, per group (round-8 report)
| Group | Fix | Tests (tests/test_prh_b9.py unless named) | Mutants |
|---|---|---|---|
| 1 | one built killer per survivor (54, 59, 84, 93, 111); final-head run found two more whose random-corpus killers no longer reached them (31, 114): built killers too | g1_* tests, `test_b9_g1_mutant_31_*`, `test_b9_g1_mutant_114_*` | 31, 54, 59, 84, 93, 111, 114, 116 |
| 2 | the (fj, fs) fold kept and pinned; docstring states the reason | g1_g2_* | 116 |
| 3 | `check_only` narrowed: a value only inside an unterminated string body is masked, not withheld; front before the opener still withholds | g3_* | 127, 128 |
| 4 | rules written down and rows added (alphabet, digit table, boundary five against six different characters, repeated letter, ordinary text with single-character tokens, exact output for `"x " * 400`) | g4_* | 115, 125, 126 |
| 5 | any whitespace or invisible gap, key word glued, text around a spaced key, known values of 12 or more characters read; a value of no pattern shape is NOT read and SECURITY says so, pinned by a test | g5_*, test_prh_b9_docs.py | 110, 132 |
| 6 | every wrong sentence corrected; docs test reads each documented number against the live constant or the evidence file | test_prh_b9_docs.py | none |
| 7 | cap of 32 runs per text with a withhold (never a skip), linear index search | g7_* | 121, 122, 123, 124 |
| 8 | a short value in a soft conflict now withholds (final guard on values of 4 or more characters) | g8_* | 117 |
| 9 | a dropped view that alone found a new value raises the limit (withheld) | g9_* | 119, 120 |
| 10 | one seeded generator (`tests/seeded.py`), one allowance for S311 | tests | none |
| 11 | real counts below; withheld-share bound tightened to the measured values | b8 i6 test | none |
Evidence leak groups found by the independent runner: backslash-e spelling of ESC (fixed, e1), a front left by an unterminated string opener (fixed, e2), whitespace gaps (fixed, e3).

## Not fixed (exception reasons and next steps) - also in SECURITY.md and CHANGELOG
* Split texts (261 of 4691 in the evidence fuzz): needs the owner decision `q-prh-piece-masking` (masking a piece of a value is a product choice).
* A key spelled with a backslash-e ESC plus a raw BEL title row: next step is to build the decoded views also from the text with its hidden items intact.
* 3 multi-cut `rand` texts: next step is a gap pattern that allows ESC plus one optional letter.
* Hyphen as a gap: not read (would change ordinary hyphenated text).
* Unknown spaced values of no pattern shape (40): by design, stated in SECURITY.
* Hostile texts that reach the run cap are refused, never shown.

## Fail-before on ea6dbdaf
`failbefore-ea6dbdaf.txt`: clean detached worktree at ea6dbdaf, new and changed test files copied in, 5 test files run: 33 failed, 2046 passed, no collection error. `passing-on-old-ea6dbdaf.txt` lists every test of b7, b8 and b9 that passes on the old code (170 lines). Reasons per group:
* b9 g1 (10 rows) and g1_g2 (3): killers of mutants 31, 54, 59, 84, 93, 111, 114, 116 - the guards exist on the old code, the tests fail only when the guard is planted away (mutant gate, 129 of 129).
* b9 g3 front, g4 (9), g7 index search and distinct-count: boundary or regression pins of behaviour that must not change; mutants 115, 124, 125, 126, 128 plant the change.
* b9 g5 (two: any-separator row and the no-pattern-shape statement) and e1 lone backslash-e: pins of behaviour that stays; mutant 132 and the e1 rows of the failing group.
* b8 (46 rows): rows built in b8 for guards that exist at ea6dbdaf and are killed by mutants 102 to 114 of the b8 set (gate), plus 20 runner rows that are regression pins of the independent runner's own corpus (0 leaks on both trees).
* b7 (95 rows): regression tests of b7; the mutants 59 to 100 range kills them.
