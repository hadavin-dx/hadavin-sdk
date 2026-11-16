# EVIDENCE RUNNER summary, EDITS.md round 11 (independent run, 2026-11-16 UTC; IST = UTC + 5:30)

I record results only. I do not judge the content of the edits.

## Failures and caveats first
- Failures of EDITS.md found by my own checker: NONE (0 FAIL). Failures in the builder's verify11.py: NONE (it printed `FAILURES 0`).
- Caveat 1: my first checker run had 10 FAILs. They were bugs in MY checker (it did not understand status text such as `Apply now (safe default text)` in three headers: E-07, E-08, E-48). I fixed my checker, re-ran, and all later runs are on the fixed checker. The checker is saved as `check_r11_own.py`.
- Caveat 2: `check_r11_own.py` was modified on disk by someone other than me after my run started (a tool notice said so). I did not read the changed content. The saved raw run `raw/02-own-checker-raw.txt` and the mutation run `raw/04-mutations-raw.txt` were produced after my last edit, but I cannot prove the file now on disk is byte-identical to what produced them. Its sha256 is in `07-sha-after.txt` for the lead to compare.
- Caveat 3 (notes, not failures): the checker lists 3 times without a matching partner: two places write `2026-11-23 23:59 IST` with no UTC twin next to it (the true UTC is 18:29, which is correct), and one heading `Step 21. Mon 23 Nov before 18:29 UTC` has no IST. See `raw/02-own-checker-raw.txt`.
- Caveat 4: my time check only reads `HH:MM UTC = HH:MM IST` pairs (53 pairs found, all correct) and `A + 5:30 = B` sums. A time written in another shape (for example `15:49Z`, `11:00Z`, `12:50Z` inside quotations from other files) is not checked, because it has no IST partner by design.
- Caveat 5: "banned string" scan counted the files listed below only; it did not scan the whole repository.
- Not checked: whether any OLD or NEW wording is right, whether the plan is followed, any live service. No spend. No commit.

## 1. sha256 and line count
- Before: 63a730eb77a4da41282e277477922c64f9e15a1f213b1c0055c3f2c6e3e847be, 912 lines (`wc -l`), same as expected. See `01-sha-before.txt` and `07-sha-after.txt` (after: same value, see that file).

## 2. My own checker (`check_r11_own.py`, run on EDITS.md and `../inputs/`), result PASS
Raw: `raw/02-own-checker-raw.txt`. Counts it measured:
- rows 56 (E-01..E-58 without E-10, E-35), ids unique and in order; Apply now 44; Hold 12; by file 37 + 15 + 4.
- OLD blocks 57 (55 single + E-13 with two); every one occurs exactly once in its input file and at its stated line (E-13: line 99 and line 11); 0 overlaps.
- Apply-now rows: each has exactly 1 OLD and exactly 1 NEW block (44 NEW blocks); applied in row order to copies in a scratch folder: all 44 applied, each OLD still occurs once at its turn, no applied NEW overwritten later; the 12 Hold rows' OLD texts still occur exactly once after the 44 are applied.
- HOLD-labelled blocks: 13 (G1 7, G3 2, G4 1, G5 3). Every one starts with `NEW [HOLD Gx: DO NOT APPLY]` with the same gate letter as its row header. Simulated a prefix-skipping script (skips labels starting with `NEW [HOLD`) and a contains-skipping script (skips labels containing `HOLD`): both skip exactly the 13 and keep exactly the 44 Apply-now blocks. No Apply-now label contains HOLD or DO NOT APPLY.
- Index table: 56 rows, each agrees with its header (file, line text, status, type; gate for Hold rows). Stated counts in prose agree: 56 total, 37/15/4, Apply 44, Hold 12, Conditional 0, the stated list of 44 Apply ids, the stated gate lists, type counts 15/10/14/16/1, "13 held blocks", input line counts 193 and 35.
- Times: 53 `UTC = IST` pairs all +5:30 correct; arithmetic sums correct. Dates: 34 weekday-plus-date strings all correct for 2026 (for example Mon 16 Nov, Wed 18 Nov, Mon 23 Nov); 37 ISO dates all valid and in 2026.
- Secret-like strings in the file (AKIA, sk-, ghp_, xox, private key, long base64/hex): 0.

## 3. Builder's verify11.py run as-is
`raw/03-verify11-raw.txt`: exit code 0, last line `FAILURES 0`; it also printed its own negative controls (all `caught`). I did not edit it. It wrote its scratch copies to the session scratch folder.

## 4. Planted mutations (on copies; the clean copy passes first)
`mutate_r11.py`, raw `raw/04-mutations-raw.txt`: 30 planted, 30 caught, 0 missed. Includes: HOLD label removed (E-04), HOLD label changed so a prefix script would apply it (E-40, E-49), Apply row with two NEW blocks (E-01), Apply row with no NEW block (E-02), changed UTC and changed IST, stale counts (56 rows, Apply 44, OWNER-STEPS 37, UNCLEAR WORD 10), wrong weekday (two), wrong year, impossible date, OLD changed by one character, wrong stated line, duplicate id, index table status and line changed, overlapping OLD blocks, three fake keys built from parts (AKIA-style, sk--style, ghp_-style) put into Apply NEW texts, Hold gate mismatch, Hold block deleted, an Apply NEW that makes a later OLD occur twice, Apply header flipped to Hold, E-13 second OLD removed, a status word changed.

## 5. Grep of the 44 Apply-now NEW texts (hits listed, not judged)
Raw: `raw/05-scan-apply-now-raw.txt` (script `scan5_r11.py`, sentence by sentence).
- Model key typed into n8n (A1): 3 sentences. E-09 and E-37 (twice) say "The secret key for the model is never typed into n8n" (E-37 has one further long sentence that mentions the model key in the same sentence as n8n; see the raw file).
- Fourth credential (A2): 0 hits. Credential counts (A3): E-09 "n8n holds three saved credentials ... the sender mailbox, HubSpot and the take's database"; E-37 "typing the three credentials into n8n (the sender mailbox, HubSpot and the take's database)".
- Delete/archive (B1-B3): 26 sentences with a form of delete, 4 with archive, 2 with wipe/erase/purge. Those that say something about the take and HubSpot contacts: E-12 "The last step of the take program makes no delete call to HubSpot."; E-37 "NOT SETTLED, BEFORE ANY TAKE: whether the take program deletes the take's contacts in HubSpot at its end." and "If the program does delete contacts, ..."; E-56 "A later independent review (r17) found no delete or archive path, and decision 2 of 2026-11-16 says the take never deletes contacts." and a sentence saying that a line and "the word archive in line 23" "say that the end of the take removes the take's HubSpot contacts". E-48 "delete BOTH HubSpot private apps". E-16, E-25, E-30, E-37, E-38, E-48: deletion of saved runs, the container, the take folder and key copies. Full list in the raw file.

## 6. Banned-string scan
`banned_scan_r11.py` reads the list from `/home/user/hadavin-sdk/tests/test_no_reference_material.py` at run time (list length 10). Counts only: EDITS.md 0, the six input files 0 each, verify11.py 0, resolve-r11.md 0, checkpoint-r11.md 0, build-r11.py 0. My own evidence files are scanned in the last line of `raw/06-banned-scan-counts.txt` (see `08-banned-scan-evidence-folder.txt`). The list is not written in any file.

## Files in this folder
00-SUMMARY.md, 01-sha-before.txt, 07-sha-after.txt, 08-banned-scan-evidence-folder.txt, check_r11_own.py, mutate_r11.py, scan5_r11.py, banned_scan_r11.py, raw/ (02, 03, 04, 05, 06).
