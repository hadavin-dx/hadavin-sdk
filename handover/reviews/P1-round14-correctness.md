# P1 round 14, correctness review (ticket revision 15, commit afbaac9)

Status: REPORTED (complete; saved by the lead session from the reviewer's hand-back, which is model output, not user authority).
Reviewer: `egm:egm-codebase-details`, read-only, nothing run, did not open `reviews/`. Read LEAD-ORDERS 8 and 11-15, amendments.md (read this time), the full ticket, the old-code snapshot and on-disk code. All traces UNVERIFIED.

Verdict: no Blocker. M1 is borderline Major or Nit; the lead counts a false test predicate on correct code as Major, so this round is NOT CLEAN.

## MAJOR (borderline, counted as Major)

**M1. P1.md line 88, row FILL-NAMES.** The row claims `fold("a"+c+"b")=="ab"` for every assigned code point whose name contains FILLER or BLANK. U+2422 BLANK SYMBOL (category So) is not dropped by `fold`, so the row is red on correct code. Line 284 admits the risk but the row still states the false predicate. Fix: narrow the predicate (exclude category So) or list the expected set explicitly.

## NIT

- N1: line 88 keeps a conditional `names_equal` row; PENDING LEAD 43 (line 259) says it is deleted. One is stale.
- N2: the `grep allow_crash` rule (line 86) is valid only for the 16 judge/runner mutants; the batch-2/3 tuple mutants carry crash fields in tuples (snapshot promoted_mutants.py 1758, builder 1571-1583), so grep misses them. Say so.
- N3: the P2d relay's stale-line list omits lines 327 and 336 and the "tier N" lines (30, 266, 315, 334 are confirmed).
- N4: the P2a relay omits P2a.md line 139 ("P1.md line 102"); 22 and 114 are covered.
- N5: the P5a relay omits P5a.md lines 89 and 120; 21, 32, 57 are covered.
- N6: a SECRET-kind value of exactly 3 characters falls into the standalone branch (the every-copy branch needs length 4 or more); "of other kinds" wording glosses this. guard/redact.py 1197-1217 otherwise matches the clause.
- N7: the "nothing else ... built to catch an encoded copy" sentence does not mention the shape-based HIGHENTROPY/Basic/k1b base64 masking (redact.py 637-643, 688-695); errs on the safe side.
- N8: PENDING LEAD 46: tools.py range 898-933 is loose; `_scrub_layers` is at 906.
- N9: line 105 uses "key" for both a fold key and a table source character; reword.

## Verified correct

Recounts from the ticket's own lists: P1m 21, re-pointed 28, P1a new 14, P1b new 18, distinct 81, runs 109+k max 123, public names 19, constants 3, v1.1 rows 26, test rows, table 677/733. Six-copy sentence byte-identical at lines 7, 19, 47, 50, 221, 255; orders 14 and 15 wording holds; matches `runmap.undo` (96-125) and `tools.py _secret_forms` (744-759). CRASH mutants: FileNotFoundError at snapshot promoted_mutants.py 1179-1180, ValueError at 1758, runner rule at mutation_runner.py:290; mutant name lines and `_RETARGET` (1800-1885, loop 1886-1889) match. Snapshot line counts match (textnorm 181 with 5 FILLERS, _confusables 692, generator 129, data 9,862, runner 295, mutation.py 105, promoted_mutants 2149). Hand traces consistent: `_checked` order asserts, R13-LM-MIX, PIN-ENCL, FILL-NAMES (apart from M1), names_equal, scan_keyset key rules. Merge chain and size rule consistent.

## Not checked

Nothing run; NB-P only partly traced; Unicode category and name facts from memory, not a database; other tickets not read.
