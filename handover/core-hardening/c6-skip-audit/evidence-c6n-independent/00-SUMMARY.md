# c6n independent evidence runner (condensed copy of the inline report), 2026-11-16
Runner only records; no verdict. Originals unchanged (sha256 before == after). No secrets, no spend.

## Failures and gaps (first)
1. verify-c6n.py never fails: no exit/raise/assert, so exit code 0 for every input; all 17 negative controls exited 0. Detection exists only as printed text.
2. Not detected even in text: 60.1 -> 61.1 in glossary row (V2a) and in new text of row 39 plus prose line 71 (V2d); one IST time changed 23:59 -> 23:58 at line 42 (V4a). Changing all 23:59 IST lines flips one line to False but exit stays 0 (V4b). No check that the figure itself is right.
3. Detected in text only: altered old quote (rows 1 and 40); one VOID label removed next to "18 runs"; IST broken in a new text (row 6); fake key-shaped strings built from parts.
4. Closing card: four spoken lines hold 144 words (52+35+34+23), about 58 s at 150 words a minute, against a 30 s budget (report line 64 says NOT TESTED). Open item.
5. static-checks.sh differs from stored output only by live-folder drift (file count 520 vs 502; three newer files).
6. UTC without IST within 80 characters: 6 of 43 mentions (lines 42, 165, 298, 300, 494; quotes or other cells). Z-times without IST: lines 294 and 318 (old-text quotes).

## Results
Rebuild on a scratch copy: same sha as the original, empty diff, 72 rows, ready 35 / default 34 / check-wait 3. verify on original and scratch: identical, 72 of 72 old texts once, 0 mismatches, banned none, secrets none. void-check: 128 rows, 18 kept (K1 5, K2 5, K3 5, K6 3), kill to final 60.1-61.9 s, 2 VOID rows. Own recount: 'two stores' 4 occurrences (lines 63, 163 twice, 523); '18 runs' on lines 71, 74, 293, 331 each with both VOID labels. 72 of 72 old texts occur once on stated lines; 8 tree files identical to the branch. Banned scan 0 hits.

## Not run
C-3, C-4, C-5, C-6, C-8, C-9 part 2, C-10b, C-10c part 2 (need n8n or absent files); take and probe scripts and HB reports are not on disk; correctness of the 72 new texts not judged.
Raw files: this folder (01- to 08-).
