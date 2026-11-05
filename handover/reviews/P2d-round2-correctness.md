# P2d round 2, correctness (egm:egm-codebase-details), head d6be4de. Condensed. Verdict: NOT CLEAN. 4 MAJOR, 8 MINOR, 5 NIT. Reviewer ran nothing (no shell/git); probe figures, numstat, merge-base UNVERIFIED. All 29 round-1 applications checked present (caveats D1 COR-C11 premise differs, D2 `perf` not `slow`, D3 R2 not killed).
| id | sev | problem | fix |
|---|---|---|---|
| R2-C1 | MAJOR | GAP-1 and P1B-1 decide "still leaked" by checking the key visible after `fold` of the output; `fold` drops tag chars and unassigned points, so the row passes vacuously and P2d-2 fail-before has nothing to fail on. | Decide on the RAW output (no tag-char run for the key remains, substituted point gone); add control that plain key is masked. |
| R2-C2 | MAJOR | Mutant R2 (check after pass one, line 496) survives BUDGET-1: loop check at 509 fires with the same exception. "Every mutant KILLED" unmet. | Spy that `_decoded_masks`/neutralise is NOT run when budget already spent, or declare R2 equivalent. |
| R2-C3 | MAJOR | Moved test 14 ends `assert value in r.mapping.values()` with FOLDED spellings; with L1 (written slice stored) 8 of 10 rows fail; L5 sentence "does not pin the folded spelling" false; mutant 10 affected. | List the edit to test 14 (expected = written slice); fix L5 and `_folded_line` docstring (1162). |
| R2-C4 | MAJOR | Guarantee sentence "ASCII-only line takes the old path" is per TEXT in code: `bank_near` from whole folded text (1056-1059) and multi-line withhold from an ASCII start line (1070-1076). | Reword "ASCII-only TEXT"; state both behaviours; rows. (= ADV-R2-2) |
| R2-C5 | MINOR | BUDGET-2 label R should be A; text must be ASCII with an escape; `runmap.time` and `redact_mod.time` same module. | Relabel; state. |
| R2-C6 | MINOR | ALIGN-1 near tautology except U+2044; Class B "Fixed by ALIGN-1" overstated; `perf`-marked so unit step skips it. | Sequence row (base letters, every Mn, Hangul jamo, ZWJ); reword. |
| R2-C7 | MINOR | Evidence step 2 old tree is a no-op (P1a touches neither file; drops P2a/P4d). | Use P2d-1 parent, revert only P2d-1 hunks. |
| R2-C8 | MINOR | "budget plus one pass" mixes meanings; true worst case = budget + direct pass + sweep. | Define; HOSTILE-1 measures whole call. (= ADV-R2-4) |
| R2-C9 | MINOR | `_place`/`_mask_ex` already exist at 748849c; dedupe by written spelling needs deferred registration; several differently written occurrences share one placeholder. | Describe restructure; row. |
| R2-C10 | MINOR | `_decoded_masks` unbudgeted for non-ASCII originals after L1. | Measurement row. (= ADV-R2-1b) |
| R2-C11 | MINOR | No placement table for new rows. | Add. |
| R2-C12 | MINOR | P2d-2 mutants have no killers. | Provisional killers or mark blocked on P1b. |
| R2-C13..C17 | NIT | "4 to 17 times" vs 5.0x/3.3x; defaults.py lines 45-48; head not named for runmap lines (ce70eb5: EMAIL 170, storable 218-226); mutants 5 and 7 only re-pointed; `has_hidden_channel` is P1a (P1.md:37). | Fix. |
Cross-ticket: no P1.md text acknowledges P1b running ALIGN-1 and `tests/test_redact*.py` (P2d claims it only). Stop rule: not met.
