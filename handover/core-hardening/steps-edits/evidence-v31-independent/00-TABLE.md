# Evidence v31, independent runner (raw results; the runner does not judge)
Run 2026-11-16 17:47 to about 18:05 UTC (23:17 to 23:35 IST). No commit, no push, no spend, no secrets. Work on copies in `base/` (a copy of the v31 inputs taken 17:47 UTC; the originals were byte-identical to it when I finished). Own scripts: `indep31.py` (my own checker, shares no code with check-v31.py or newchecks-v31.py), `hostile31.py` (mutation driver). Raw outputs: `out-*.txt`.

## Failures and deviations first
1. **check-v31.py does NOT end at 0 failures.** It prints 9 failures, all C19 ("pointer not in the verified list"), all in `v31-CHANGES.md` (pointers like `Open 102`, `Q27`, `7.11`, `5.1`, `card step 5`, `5.5`). `pointers-v31.txt` was written 17:33 UTC; `v31-CHANGES.md` was edited 17:46 UTC afterwards. Same 9 lines on the original folder (out-check-v31-original-folder.txt) and on my copy (out-check-v31.txt). Needs a person to read the new pointers, then `ACCEPT_POINTERS=1`.
2. **mut31.py: 230 plants, 228 caught by the meant check, 1 anchor-not-found (M48, "CHANGES table pointer 6.7 to 6.9", the text no longer exists in v31-CHANGES.md), negative control ok.** Expected 229 caught; 228 is what ran. v31-CHANGES.md line 23 says "229 caught, 0 anchor-not-found" and "Baseline failures 0": both do not match this run.
3. **check-v31.py misses 12 of my 57 source-level hostile mutations**, my checker misses 18; **6 are missed by both** (list below). Real gaps in check-v31.py: H09 warning beside default A removed from the lead note; H18 absolute path in an owner sheet; H20 `ORD:` and H21 `DEC:` in an owner sheet; H25 "for one letter only" rule shortened; H33 7-day date computed from 160 h instead of 168 h (page then shows 18:30 UTC = 00:00 IST, pair and weekday still consistent); H37 label L5 renamed L4; H38 UNVERIFIED removed from a section heading; H50 film pause 10 changed to 12 in one place; H51 call ceiling 3 changed to 4 in one place; H53 run length 15 changed to 12 in one place; H54 a new wording of the H06 idea (`the lead sends you "cancel the older key" and you cancel it`). Single-copy number drift (H50, H51, H53) is the biggest class: a number typed once in a source, not tied to the facts file, is not compared.
4. Earlier misses (v30 evidence items): H06 exact text caught (C213, H26); but my variant H54 is NOT caught (H55 other phrasing is caught). H09 caught (C224, H45 and H57). H15 (unused fact) caught (C225, H56). Item 4 of v30 (pair 18:00 UTC = 23:30 IST absent): the brief names 18:00, no v31 page uses it either; 18:04 = 23:34, 18:09 = 23:39, 18:19 = 23:49, 18:29 = 23:59 are present and right (owner pages hold 18:29, 18:19, 18:09; 18:04 is in the appendix A/B and lead note). Brief said "7 earlier misses"; the v30 evidence lists 3 misses (H06, H09, H15) plus 4 other items, so I tested those 3 and the pair item.
5. 4 of my mutations never applied (anchor not found, so not counted): H43/H46/P12 were fixed and re-run; P05 (film page weekday) still has no anchor ("Mon 23 Nov" not on the film page) and was not re-run.
6. My checker's first run had false findings (email at example.com, `[LEAD FILLS ...` explanatory text, money numbers that live only in the lead note, seconds written on one side only). I fixed my script; the final output is what is saved.
7. Not mine: other agents run python and mutation jobs on this machine (load about 4); the git tree has many modified files outside my folder. A backgrounded `cp` from the builder was not seen.

## Results
| # | Step | Result | Raw file |
|---|---|---|---|
| 1a | build-v31.py on copy | rc 0; 9 files built; sha256 of all 44 copied files identical before and after | out-build-v31.txt, hashes-before.txt |
| 1b | check-v31.py on copy | rc 1, 9 failures, all C19 in v31-CHANGES.md (deviation 1) | out-check-v31.txt |
| 1c | v31-fail-proof.py | rc 0; Part 8 has 18 checks (C210 to C227); 17 fail on built v30; C224 is listed as unable to fail on v30; none fail on v31 | out-fail-proof.txt |
| 1d | mut31.py | 230 plants, 228 caught, 0 missed, 1 anchor-not-found (M48), negative control ok (deviation 2) | out-mut31.txt |
| 2 | my own checker indep31.py on built v31 | 0 findings after my own fixes (checks I01 to I11: word counts, UTC/IST pairs with seconds, weekday-date, pointers, absolute paths, internal codes, secrets, banned counts, emails, content anchors, numbers) | out-indep31.txt |
| 2a | word counts (split on spaces) | sheet A 6287 (cap 6300), sheet B 6087, card A 1959, card B 1876, appendix A 4458, appendix B 4389, film page 519, lead note 13032, open list 7679 | out-wordcounts.txt |
| 2b | UTC/IST pairs | every pair in 9 pages recomputed with +5:30: 0 wrong; required pairs 18:29=23:59, 18:19=23:49, 18:09=23:39, 15:00=20:30 in both owner packages; 18:04=23:34 and 18:14:40=23:44:40 present | indep31 I02 |
| 2c | weekday-date | Mon 16, Wed 18, Sun 22, Mon 23, Wed 25 Nov 2026 present in both packages and correct; every other "Weekday D Mon" mention correct | I03 |
| 2d | owner pages: absolute paths 0, internal codes (Q-number, ORD:, DEC:, C-number, L-23NOV style) 0, secret shapes 0 (incl. hyphenated sk- style), email-shaped text other than masked or example.com 0, banned strings 0 hits (10+ entries read at run time, counts only) | | I05 to I09 |
| 3 | hostile mutations | 69 applied (57 source+rebuild, 12 built-page edits); see below | out-hostile31.txt, -b, -c |

### Mutation catch counts
| Group | Applied | check-v31 caught | my checker caught | both missed | only check-v31 | only mine |
|---|---|---|---|---|---|---|
| Source or facts edited, rebuilt (H01 to H57) | 57 | 45 | 39 | 6 | 12 | 6 |
| Built pages edited, no rebuild (P01 to P13) | 12 | 12 (but 5 only by C01, the rebuild comparison; 7 by a second code) | 7 | 0 | 5 | 0 |

Missed by neither: H33 (7-day date from 160 h), H37 (L5 renamed L4), H38 (UNVERIFIED removed from section 6 heading), H50 (film pause 12 in one place), H51 (call ceiling 4 in one place), H53 (run length 12 in one place).
Missed by check-v31 only: H09, H18, H20, H21, H25, H54 (my checker catches these).
Missed by my checker only (check-v31 catches): H05, H23, H24, H28, H32, H35, H36, H40, H46, H52, H55, H56 and page edits P02, P06, P11, P12, P13 (my checker has no check for them).
Where each mutation and its codes are listed: out-hostile31.txt (H01-P12), out-hostile31b.txt (re-run of H43, H46, P05, P12 and new P13, H49-H53), out-hostile31c.txt (H54-H57).

## Step 5
`git status --short inputs src tests` = 0 lines. No process of mine left (all runs finished, foreground or finished background). `__pycache__`: 0 (all runs used -B). Scratch folders in the session scratchpad removed. `base/` (44 copied files, small) kept so hostile31.py can be re-run: `python3 -B -I hostile31.py base <scratch folder>`.

## Not checked
Whether the sheets are understandable or correct for a real person; the sheet claims marked UNVERIFIED; any text outside the 9 pages and listed scripts; the repo CI gates (ruff, pytest, bandit, CodeQL); whether the 7-day and other rules are right (only that wording and numbers stay consistent).
