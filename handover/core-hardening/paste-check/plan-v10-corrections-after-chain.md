# Corrections to plan-v10-real-v5-edits.md when the edits are applied AFTER the patch chain (2026-11-16, chain builder)
The old file `plan-v10-real-v5-edits.md` is NOT edited. It was written against the unpatched plan (input sha256 starts `67a0a195537de875`). After the chain `plan-v5-fixes.patch`, `plan-v5-repin-v6.patch`, `plan-v5-gate-rows-v3.patch` (see `PLAN-CHAIN.md`) five of its 29 edits (2, 18, 19, 20, 21) find no old text, and edits 5 and 6 still apply but write wrong numbers. This file replaces those SEVEN edits. Use the other 22 edits of the old file unchanged and in their old order.
Arithmetic (chain end: 154 steps, 174 min = 2 h 54 min, 77 unrun files, section 7 heading "(23 rows)"; v10 adds 2.1b = 2 steps, 2 minutes, 1 unrun file, 1 row CS): 156 steps, 176 min = 2 h 56 min, 78 unrun files, 24 rows. The "+1 unrun file" and "+1 row" are taken from v10 (edits 6 and 21); they were not re-counted by hand against the chained plan.
Edit 5 and edit 6 old texts occur once in the original AND in the chained plan (they sit in the CHANGES table and in section 2), so they apply; only their NEW text changes here.

## Edit 2 (corrected): plan line 6 after the chain (RIGHT-SIZE, floor time)
~~~~old
Floor about 2 h 54 min clean
~~~~
~~~~new
Floor about 2 h 56 min clean
~~~~

## Edit 5 (corrected new text): CHANGES FROM v4 table, estimate row
~~~~old
171 min clean is a floor
~~~~
~~~~new
176 min clean is a floor (174 before the real-v5 edit)
~~~~

## Edit 6 (corrected new text): section 2 `code` row
~~~~old
2 h 51 min is a floor: about 76 files are unrun
~~~~
~~~~new
2 h 56 min is a floor: about 78 files are unrun
~~~~

## Edit 18 (corrected): section 5, steps total
~~~~old
| **steps** | | **154** |
~~~~
~~~~new
| **steps** | | **156** |
~~~~

## Edit 19 (corrected): section 5, clean total
~~~~old
| **clean total (a FLOOR, not a quote)** | | **174 min = 2 h 54 min** |
~~~~
~~~~new
| **clean total (a FLOOR, not a quote)** | | **176 min = 2 h 56 min** |
~~~~

## Edit 20 (corrected): section 5, quote sentence
~~~~old
2 h 54 min is a floor: about 77 files are unrun
~~~~
~~~~new
2 h 56 min is a floor: about 78 files are unrun
~~~~

## Edit 21 (corrected): section 7 heading
~~~~old
## 7. PASS/FAIL table to fill in `evidence-2\INDEX.md` (23 rows)
~~~~
~~~~new
## 7. PASS/FAIL table to fill in `evidence-2\INDEX.md` (24 rows)
~~~~
