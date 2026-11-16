# EVIDENCE RUNNER: evidence-chain-r1 (raw output, no judgement)
Run date 2026-11-16. GNU patch on Linux, python3 -I. All work on scratch copies under the session scratchpad; `inputs/` and patch files untouched (input sha256 before and after: `67a0a195537de875...`, see below).

## Read first: what went wrong in my own run, and what I did not run
1. In my first script I called `apply-v10.py` with a path as argument 1 for a "step 3" test. That script's argument 1 is an OUTPUT path (it always reads the original plan), so it overwrote my scratch `step3.md` with "old edit list on the original" (716 lines, sha 3e605f4d...). Every result in Part A below that is labelled "INVALID" was produced from that wrong file. I regenerated step 3 and re-ran those tests in Part C (valid).
2. The script `apply-v10.py` cannot take a plan as input; so "old edit list on step N" tests in Part C use my own scratch script (`oldonly.py`, same regex as `apply-v10-after-chain.py` but without the corrections table).
3. Not run: the plan itself, any paste in it, n8n, Git Bash, `git apply`, `patch --fuzz=0`. I did not recompute section 5 totals from rows. The `LEAD-CHECKLIST-v5.md` A3-A5b run of the older `plan-v5-gate-rows.patch` was only done as an extra (Part A, "alt"). I ran the A6 grep commands exactly as in LEAD-CHECKLIST-v5.md line 60 (counted with `grep -c`, file name substituted).
4. PLAN-CHAIN.md says "wrong order, gate-rows first fails 7 of 8 hunks; repin-v6 on the original 5 of 15 hunks fail": reproduced (Part A).
5. Two things differ from or add to PLAN-CHAIN.md / LEAD-CHECKLIST-v5.md (facts, not judgement): (a) the checklist names `plan-v5-gate-rows.patch` (sha 4b985424... result) while PLAN-CHAIN.md names `plan-v5-gate-rows-v3.patch` (result 515cf470...): both apply, both give 622 lines and A6 counts 24 10 2 1, results differ in sha; (b) the order "fixes, gate-rows-v3, repin-v6" fails at gate-rows-v3 (5 of 8 hunks) but the later repin-v6 dry run succeeded on that already-damaged file (rc 0) in my run; exit codes shown below.

## Part A: raw output of the first script (steps 0-4, alt, wrong orders). Contains INVALID sections, marked below
Sections of this part that are INVALID: "edit list (v10 old script) on original, then fixes" (cp failed: no v10.md written, so the three dry runs ran on the ORIGINAL plan... they are shown failing because of leftover state; ignore) and "old edit list (apply-v10.py) on step3" (overwrote step3.md; ignore). Valid redo in Part C.
```
== inputs sha before
67a0a195537de8754ef80bd3bd8d8a4d78a507ca8418bec8f835a0e99abb41f1  /home/user/hadavin-sdk/handover/core-hardening/inputs/plan-wp6-resmoke-v5.md
--- state: 0 original
sha256: 67a0a195537de8754ef80bd3bd8d8a4d78a507ca8418bec8f835a0e99abb41f1
wc -l: 558
A6 FINAL: 0
A6 LEAD-FILL: 0
A6 HEAD_PIN: 2
A6 RE-PIN: 0
floor lines:
5:**RIGHT-SIZE (R455):** a MANUAL one-off run: loopback only, made-up data, throwaway stub services, US$0, inside the owner's WP6 smoke yes of 2026-11-15 (loopback, US$0; no real mailbox, HubSpot, Gmail, model call, DNS 
22:| design owner estimate + lead ruling (a) | 2 h 50 min is a floor | section 5 and header: quote the owner 3.5 to 4.5 hours realistic; 171 min clean is a floor |
443:| **clean total (a FLOOR, not a quote)** | | **171 min = 2 h 51 min** |
445:**Quote the owner 3.5 to 4.5 hours realistic** (design round 3, lead ruling a; 2 h 51 min is a floor: about 76 files are unrun, P-3a is tight, glue fixes cost 2 to 4 x 15 min, and the S11 waits run toward their bound

=== STEP 1 plan-v5-fixes.patch
9e8d06ddb5bb5b57e6a81c0493e2a449a918cfc2dfc13e988f82d32ce96584b8  /home/user/hadavin-sdk/handover/core-hardening/paste-check/plan-v5-fixes.patch
checking file inputs/plan-wp6-resmoke-v5.md
dry rc=0
patching file inputs/plan-wp6-resmoke-v5.md
apply rc=0
--- state: 1 after plan-v5-fixes
sha256: 53f1670383a2c728c4bdbb560f5444766aa0df773ac6f85a4c6496aca1bb1c2a
wc -l: 561
A6 FINAL: 0
A6 LEAD-FILL: 0
A6 HEAD_PIN: 2
A6 RE-PIN: 0
floor lines:
5:**RIGHT-SIZE (R455):** a MANUAL one-off run: loopback only, made-up data, throwaway stub services, US$0, inside the owner's WP6 smoke yes of 2026-11-15 (loopback, US$0; no real mailbox, HubSpot, Gmail, model call, DNS 
22:| design owner estimate + lead ruling (a) | 2 h 50 min is a floor | section 5 and header: quote the owner 3.5 to 4.5 hours realistic; 171 min clean is a floor |
445:| **clean total (a FLOOR, not a quote)** | | **171 min = 2 h 51 min** |
447:**Quote the owner 3.5 to 4.5 hours realistic** (design round 3, lead ruling a; 2 h 51 min is a floor: about 76 files are unrun, P-3a is tight, glue fixes cost 2 to 4 x 15 min, and the S11 waits run toward their bound

=== STEP 2 plan-v5-repin-v6.patch
8a83abaa5c10db10ec84adabc82a855b087ff67286a44cec1611b812c90011d2  /home/user/hadavin-sdk/handover/core-hardening/paste-check/plan-v5-repin-v6.patch
checking file inputs/plan-wp6-resmoke-v5.md
dry rc=0
patching file inputs/plan-wp6-resmoke-v5.md
apply rc=0
--- state: 2 after plan-v5-repin-v6
sha256: 39af84aec78b650f287d20013cdfa2d45dde8b75632e6d6729660bbc21ce3f5b
wc -l: 587
A6 FINAL: 24
A6 LEAD-FILL: 10
A6 HEAD_PIN: 2
A6 RE-PIN: 1
floor lines:
6:**RIGHT-SIZE (R455):** a MANUAL one-off run: loopback only, made-up data, throwaway stub services, US$0, inside the owner's WP6 smoke yes of 2026-11-15 (loopback, US$0; no real mailbox, HubSpot, Gmail, model call, DNS 
23:| design owner estimate + lead ruling (a) | 2 h 50 min is a floor | section 5 and header: quote the owner 3.5 to 4.5 hours realistic; 171 min clean is a floor (HISTORY: section 5 now says 172 min = 2 h 52 min) |
465:| **clean total (a FLOOR, not a quote)** | | **172 min = 2 h 52 min** |
467:**Quote the owner 3.5 to 4.5 hours realistic** (design round 3, lead ruling a; 2 h 52 min is a floor: about 77 files are unrun, P-3a is tight, glue fixes cost 2 to 4 x 15 min, and the S11 waits run toward their bound

=== STEP 3 plan-v5-gate-rows-v3.patch
498c1e5f4b3debc9b7f1ae977e6b4c9c364c8cb3cefe62398202eb4b36779477  /home/user/hadavin-sdk/handover/core-hardening/paste-check/plan-v5-gate-rows-v3.patch
checking file inputs/plan-wp6-resmoke-v5.md
Hunk #1 succeeded at 3 with fuzz 2.
dry rc=0
patching file inputs/plan-wp6-resmoke-v5.md
Hunk #1 succeeded at 3 with fuzz 2.
apply rc=0
--- state: 3 after plan-v5-gate-rows-v3
sha256: 515cf4704ebba5bdc00e3c2ab9fdce7f65a2a7b8467ceec0bf0942b7e21a7e45
wc -l: 622
A6 FINAL: 24
A6 LEAD-FILL: 10
A6 HEAD_PIN: 2
A6 RE-PIN: 1
floor lines:
6:**RIGHT-SIZE (R455):** a MANUAL one-off run: loopback only, made-up data, throwaway stub services, US$0, inside the owner's WP6 smoke yes of 2026-11-15 (loopback, US$0; no real mailbox, HubSpot, Gmail, model call, DNS 
23:| design owner estimate + lead ruling (a) | 2 h 50 min is a floor | section 5 and header: quote the owner 3.5 to 4.5 hours realistic; 171 min clean is a floor (HISTORY: the re-pin patch made section 5 say 172 min = 2 
498:| **clean total (a FLOOR, not a quote)** | | **174 min = 2 h 54 min** |
500:**Quote the owner 3.5 to 4.5 hours realistic** (design round 3, lead ruling a; 2 h 54 min is a floor: about 77 files are unrun, P-3a is tight, glue fixes cost 2 to 4 x 15 min, and the S11 waits run toward their bound

=== STEP 4 apply-v10-after-chain.py
29 ['2', '5', '18', '19', '20', '21']
failing []
rc=0
--- state: 4 after v10
sha256: b0caeb84c5a28a9438d242d8ce1dbe442418dcf96e3c18659c39b05a37d56f99
wc -l: 779
A6 FINAL: 24
A6 LEAD-FILL: 10
A6 HEAD_PIN: 2
A6 RE-PIN: 1
floor lines:
6:**RIGHT-SIZE (R455):** a MANUAL one-off run: loopback only, made-up data, throwaway stub services, US$0, inside the owner's WP6 smoke yes of 2026-11-15 (loopback, US$0; no real mailbox, HubSpot, Gmail, model call, DNS 
18:| time | 2.1b adds a step | S2 12 to 14 min, steps 151 to 153, clean floor 171 to 173 min = 2 h 53 min (2.1b = 2 min, a builder estimate, not measured) |
35:| design owner estimate + lead ruling (a) | 2 h 50 min is a floor | section 5 and header: quote the owner 3.5 to 4.5 hours realistic; 176 min clean is a floor (174 before the real-v5 edit) (HISTORY: the re-pin patch m
541:| **clean total (a FLOOR, not a quote)** | | **176 min = 2 h 56 min** |
543:**Quote the owner 3.5 to 4.5 hours realistic** (design round 3, lead ruling a; 2 h 56 min is a floor: about 78 files are unrun, P-3a is tight, glue fixes cost 2 to 4 x 15 min, and the S11 waits run toward their bound
plan-wp6-resmoke-v5.md

=== also checklist-named gate-rows.patch (non -v3) on step 2
ee29f955c632fbde812beeb8a808ca685df2dc6595b135748baf3b17ca7169d0  /home/user/hadavin-sdk/handover/core-hardening/paste-check/plan-v5-gate-rows.patch
checking file inputs/plan-wp6-resmoke-v5.md
Hunk #1 succeeded at 3 with fuzz 2.
dry rc=0
patching file inputs/plan-wp6-resmoke-v5.md
Hunk #1 succeeded at 3 with fuzz 2.
apply rc=0
--- state: alt step3 with plan-v5-gate-rows.patch
sha256: 4b985424af9993f2cf5e17f17c5e61e61cbced14247957f8cb81ab04808082b4
wc -l: 622
A6 FINAL: 24
A6 LEAD-FILL: 10
A6 HEAD_PIN: 2
A6 RE-PIN: 1
floor lines:
6:**RIGHT-SIZE (R455):** a MANUAL one-off run: loopback only, made-up data, throwaway stub services, US$0, inside the owner's WP6 smoke yes of 2026-11-15 (loopback, US$0; no real mailbox, HubSpot, Gmail, model call, DNS 
23:| design owner estimate + lead ruling (a) | 2 h 50 min is a floor | section 5 and header: quote the owner 3.5 to 4.5 hours realistic; 171 min clean is a floor (HISTORY: the re-pin patch made section 5 say 172 min = 2 
498:| **clean total (a FLOOR, not a quote)** | | **174 min = 2 h 54 min** |
500:**Quote the owner 3.5 to 4.5 hours realistic** (design round 3, lead ruling a; 2 h 54 min is a floor: about 77 files are unrun, P-3a is tight, glue fixes cost 2 to 4 x 15 min, and the S11 waits run toward their bound

=== WRONG ORDERS (scratch copies)
## gate-rows-v3 first
-- plan-v5-gate-rows-v3.patch
dry rc=1
Hunk #7 FAILED at 483.
Hunk #8 succeeded at 471 (offset -23 lines).
7 out of 8 hunks FAILED
apply rc=1
plan-wp6-resmoke-v5.md
plan-wp6-resmoke-v5.md.rej
## repin-v6 on original
-- plan-v5-repin-v6.patch
dry rc=1
Hunk #14 succeeded at 503 (offset -2 lines).
Hunk #15 FAILED at 561.
5 out of 15 hunks FAILED
apply rc=1
plan-wp6-resmoke-v5.md
plan-wp6-resmoke-v5.md.rej
## repin-v6 then fixes
-- plan-v5-repin-v6.patch
dry rc=1
Hunk #14 succeeded at 503 (offset -2 lines).
Hunk #15 FAILED at 561.
5 out of 15 hunks FAILED
apply rc=1
-- plan-v5-fixes.patch
dry rc=0
Hunk #6 succeeded at 412 (offset 2 lines).
Hunk #7 succeeded at 552 (offset 5 lines).
Hunk #8 succeeded at 563 (offset 5 lines).
apply rc=0
plan-wp6-resmoke-v5.md
plan-wp6-resmoke-v5.md.rej
## fixes, gate-rows-v3, repin-v6
-- plan-v5-fixes.patch
dry rc=0
checking file inputs/plan-wp6-resmoke-v5.md
apply rc=0
-- plan-v5-gate-rows-v3.patch
dry rc=1
Hunk #7 FAILED at 516.
Hunk #8 succeeded at 506 (offset -21 lines).
5 out of 8 hunks FAILED
apply rc=1
-- plan-v5-repin-v6.patch
dry rc=0
Hunk #13 succeeded at 544 (offset 35 lines).
Hunk #14 succeeded at 558 (offset 35 lines).
Hunk #15 succeeded at 614 (offset 35 lines).
apply rc=0
plan-wp6-resmoke-v5.md
plan-wp6-resmoke-v5.md.rej
## edit list (v10 old script) on original, then fixes
plan list sha256 ec922309d8e937507f69ed9b2e6fc4da006b30f13f865df98dc0444a35e0f8db
input sha256 prefix before 67a0a195537de875
header says 29 parsed 29
edit 1 occurs in original 1 in current 1 order ok True OK
edit 2 occurs in original 1 in current 1 order ok True OK
edit 3 occurs in original 1 in current 1 order ok True OK
edit 4 occurs in original 1 in current 1 order ok True OK
edit 5 occurs in original 1 in current 1 order ok True OK
edit 6 occurs in original 1 in current 1 order ok True OK
edit 7 occurs in original 1 in current 1 order ok True OK
edit 8 occurs in original 1 in current 1 order ok True OK
edit 9 occurs in original 1 in current 1 order ok True OK
edit 10 occurs in original 1 in current 1 order ok True OK
edit 11 occurs in original 1 in current 1 order ok True OK
edit 12 occurs in original 1 in current 1 order ok True OK
edit 13 occurs in original 1 in current 1 order ok True OK
edit 14 occurs in original 1 in current 1 order ok True OK
edit 15 occurs in original 1 in current 1 order ok True OK
edit 16 occurs in original 1 in current 1 order ok True OK
edit 17 occurs in original 1 in current 1 order ok True OK
edit 18 occurs in original 1 in current 1 order ok True OK
edit 19 occurs in original 1 in current 1 order ok True OK
edit 20 occurs in original 1 in current 1 order ok True OK
edit 21 occurs in original 1 in current 1 order ok True OK
edit 22 occurs in original 1 in current 1 order ok True OK
edit 23 occurs in original 1 in current 1 order ok True OK
edit 24 occurs in original 1 in current 1 order ok True OK
edit 25 occurs in original 1 in current 1 order ok True OK
edit 26 occurs in original 1 in current 1 order ok True OK
edit 27 occurs in original 1 in current 1 order ok True OK
edit 28 occurs in original 1 in current 1 order ok True OK
edit 29 occurs in original 1 in current 1 order ok True OK
lines before 558 after 716 fails 0
input sha256 prefix after 67a0a195537de875
apply-v10 rc=0
cp: cannot stat '/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/w/wo_e/v10.md': No such file or directory
-- plan-v5-fixes
dry rc=1
Hunk #8 FAILED at 558.
2 out of 8 hunks FAILED
-- plan-v5-repin-v6
dry rc=1
Hunk #15 FAILED at 557.
13 out of 15 hunks FAILED
-- plan-v5-gate-rows-v3
dry rc=1
Hunk #8 FAILED at 494.
8 out of 8 hunks FAILED
## old edit list (apply-v10.py) on step3
plan list sha256 ec922309d8e937507f69ed9b2e6fc4da006b30f13f865df98dc0444a35e0f8db
input sha256 prefix before 67a0a195537de875
header says 29 parsed 29
edit 1 occurs in original 1 in current 1 order ok True OK
edit 2 occurs in original 1 in current 1 order ok True OK
edit 3 occurs in original 1 in current 1 order ok True OK
edit 4 occurs in original 1 in current 1 order ok True OK
edit 5 occurs in original 1 in current 1 order ok True OK
edit 6 occurs in original 1 in current 1 order ok True OK
edit 7 occurs in original 1 in current 1 order ok True OK
edit 8 occurs in original 1 in current 1 order ok True OK
edit 9 occurs in original 1 in current 1 order ok True OK
edit 10 occurs in original 1 in current 1 order ok True OK
edit 11 occurs in original 1 in current 1 order ok True OK
edit 12 occurs in original 1 in current 1 order ok True OK
edit 13 occurs in original 1 in current 1 order ok True OK
edit 14 occurs in original 1 in current 1 order ok True OK
edit 15 occurs in original 1 in current 1 order ok True OK
edit 16 occurs in original 1 in current 1 order ok True OK
edit 17 occurs in original 1 in current 1 order ok True OK
edit 18 occurs in original 1 in current 1 order ok True OK
edit 19 occurs in original 1 in current 1 order ok True OK
edit 20 occurs in original 1 in current 1 order ok True OK
edit 21 occurs in original 1 in current 1 order ok True OK
edit 22 occurs in original 1 in current 1 order ok True OK
edit 23 occurs in original 1 in current 1 order ok True OK
edit 24 occurs in original 1 in current 1 order ok True OK
edit 25 occurs in original 1 in current 1 order ok True OK
edit 26 occurs in original 1 in current 1 order ok True OK
edit 27 occurs in original 1 in current 1 order ok True OK
edit 28 occurs in original 1 in current 1 order ok True OK
edit 29 occurs in original 1 in current 1 order ok True OK
lines before 558 after 716 fails 0
input sha256 prefix after 67a0a195537de875
rc=0
## after-chain script on step 2
29 ['2', '5', '18', '19', '20', '21']
failing [('2', 0), ('18', 0), ('19', 0), ('20', 0), ('21', 0)]
rc=0
## input sha after
67a0a195537de8754ef80bd3bd8d8a4d78a507ca8418bec8f835a0e99abb41f1  /home/user/hadavin-sdk/handover/core-hardening/inputs/plan-wp6-resmoke-v5.md
```
## Part B: extra raw output (old edit list only, on each state; second script). The "on step3" line here is INVALID (used the overwritten step3.md); valid line in Part C.
```
-- on step1   29 failing []            rc=0
-- on step2   29 failing [('2', 0), ('18', 0), ('19', 0), ('20', 0), ('21', 0)]   rc=0
-- on step3   INVALID (22 failures, wrong file)
-- on original 29 failing []  rc=0 ; result sha 3e605f4d33bf540a, 716 lines
edit list FIRST (apply-v10.py -> v10.md, 716 lines), THEN patches: fixes dry rc=1 (Hunk #8 FAILED at 558, 2 of 8 hunks failed); repin-v6 dry rc=1 (13 of 15 hunks failed); gate-rows-v3 dry rc=1 (8 of 8 hunks failed)
fixes, THEN old edit list (29 of 29 found), THEN: repin-v6 dry rc=1 (10 of 15 hunks failed); gate-rows-v3 dry rc=1 (7 of 8 hunks failed)
```
## Part C: valid redo of step 3 and everything that used it
```
step3.md regenerated: step2 output + plan-v5-gate-rows-v3.patch: patch rc=0 ("Hunk #1 succeeded at 3 with fuzz 2")
sha256 515cf4704ebba5bdc00e3c2ab9fdce7f65a2a7b8467ceec0bf0942b7e21a7e45   wc -l 622   (equals the chain step 3 of Part A)
old edit list only (no corrections), independent counts on step3: failing [('2', 0), ('18', 0), ('19', 0), ('20', 0), ('21', 0)]  (edit 5 applies, count 1)
old edit list only, sequential, on step3: 29 failing [2, 18, 19, 20, 21]
apply-v10-after-chain.py on step3.md: 29 [2, 5, 18, 19, 20, 21]; failing []; result sha256 b0caeb84c5a28a9438d242d8ce1dbe442418dcf96e3c18659c39b05a37d56f99
(same result sha as step 4 of Part A; repeated run is stable)
apply-v10-after-chain.py on step2.md: failing [('2', 0), ('18', 0), ('19', 0), ('20', 0), ('21', 0)]  (rc=0, the script does not fail on missing text; it prints the list)
```
## Part D: sha256sum -c of patches-ready/v3, v4, v5 SHA256SUMS.txt (each run inside its folder)
```
v3: C-01.patch OK, A-01.patch OK, G5-wording.patch OK      rc=0
v4: README.md, REPORT-v4.md, checkpoint.md, G5-wording.patch, C-01-MINIMAL.patch, DEAD-MAN-CHECK.md, DEFERRED-A-01.patch, CUT-C-01-FULL-NOT-FOR-THE-TAKE.patch: all OK   rc=0
v5: README.md, REPORT-v5.md, checkpoint.md, G5-wording.patch, C-01-MINIMAL.patch, DEAD-MAN-CHECK.md, DEFERRED-A-01.patch, CUT-C-01-FULL-NOT-FOR-THE-TAKE.patch: all OK   rc=0
```
## Part E: banned-word counts (list read from tests/test_no_reference_material.py BANNED at run time, 10 entries; words not printed; counts per entry index 0-9)
All counts 0 for: PLAN-CHAIN.md, plan-v10-corrections-after-chain.md, apply-v10-after-chain.py, plan-v5-fixes.patch, plan-v5-repin-v6.patch, plan-v5-gate-rows-v3.patch, plan-v5-gate-rows.patch, plan-v10-real-v5-edits.md, LEAD-CHECKLIST-v5.md, scratch step1/step2/step3 plans, scratch real-v5-plan.md (step 4 result), and the Part A raw output. rc=0.
(Exact substring match as in the test, `s in text`; the test also scans file types and names, which I did not run.)

## Part F (fix pass 2, builder run, NOT independent evidence: the evidence runner must re-run it): apply-v10-after-chain.py tests on scratch copies
Command: `bash test-apply-v10-after-chain.sh <plan after gate-rows-v3>`. Raw output:
```
515cf4704ebba5bd
## T1 good input
29 old edits; corrected or added: ['2', '4', '5', '18', '19', '20', '21', '29', '30']
failing []
written /tmp/tmp.ZKtnFhuozL/out1.md 28f92c5d1211207c 780 lines
rc=0 out_exists=yes sha=28f92c5d1211207c
## T2 wrong input sha (one byte appended)
REFUSED: input sha256 is a908e9862ea369c9, expected 515cf4704ebba5bd (the plan after fixes, repin-v6 and gate-rows-v3)
rc=1 out_exists=no
## T3 wrong input: the unpatched-shaped file (first 100 lines)
REFUSED: input sha256 is 82dbe0f86a00b3a2, expected 515cf4704ebba5bd (the plan after fixes, repin-v6 and gate-rows-v3)
rc=1 out_exists=no
## T4 equal paths
REFUSED: input and output are the same path
rc=1 sha_after=515cf4704ebba5bd
## T5 same file by another name (symlink)
REFUSED: input and output are the same path
rc=1 sha_after=515cf4704ebba5bd
## T6 output already exists
REFUSED: output file already exists (this script never overwrites)
rc=1 content=keep
## T7 failed edit (old text of edit 3 damaged in a scratch copy of the edit list)
damaged edit 3 old text
REFUSED: 1 edit(s) did not find their old text exactly once; nothing written
29 old edits; corrected or added: ['2', '4', '5', '18', '19', '20', '21', '29', '30']
failing [('3', 0)]
rc=1 out_exists=no
## T8 missing output folder
REFUSED: output folder does not exist
rc=1
## T9 wrong argument count
REFUSED: usage: apply-v10-after-chain.py <chained plan> <new output file>
rc=1
scratch folder: /tmp/tmp.ZKtnFhuozL (left in place; nothing in the repository was changed)
```
Fresh chain re-run (fix pass 2): fixes, repin-v6, gate-rows-v3 each dry run then apply, rc 0 each, shas 53f1670383a2c728, 39af84aec78b650f, 515cf4704ebba5bd; then apply-v10-after-chain.py: 'failing []', rc 0, sha256 28f92c5d1211207cce0222c87bb7a6e6dc8e39a21a659624a1a7fe9cc32992ce, 780 lines; A6 counts 24 10 2 1; UNVERIFIED numbers 1 to 20, 0 duplicates; input plan sha unchanged (67a0a195537de875). Tested repin patches on the plan after fixes: repin 4 0 2 0, repin-v2 24 0 2 1 (wrong), repin-v3 to v5 24 10 2 1 with other shas, v6 24 10 2 1 (39af84aec78b650f). Banned-word list (10 entries, read from tests/test_no_reference_material.py): 0 hits in the changed files and the final plan.

## Part G (fix pass 3, builder run, NOT independent evidence): hardened apply-v10-after-chain.py, 17 cases
Command: `bash test-apply-v10-after-chain.sh <plan after gate-rows-v3>` (plan rebuilt from the original by the three patches, sha 515cf4704ebba5bd). Decisions: a RENUMBER with `to=15` is accepted (same sha 28f92c5d, T14); `shift = 4` with spaces, `shift=x`, a deleted line, `shift=0` and an edit list without 27 are refused. Raw output, rc of the script shown below the block:
```
515cf4704ebba5bd
## T1 good input
29 old edits; corrected or added: ['2', '4', '5', '18', '19', '20', '21', '29', '30']
failing []
written /tmp/tmp.09o5QykTbG/out1.md 28f92c5d1211207c 780 lines
rc=0 out_exists=yes sha=28f92c5d1211207c
T1 full sha equals expected: YES lines=780
## T2 wrong input sha (one byte appended)
REFUSED: input sha256 is a908e9862ea369c9, expected 515cf4704ebba5bd (the plan after fixes, repin-v6 and gate-rows-v3)
rc=1 out_exists=no
## T3 wrong input: only the first 100 lines of the chained plan
REFUSED: input sha256 is 82dbe0f86a00b3a2, expected 515cf4704ebba5bd (the plan after fixes, repin-v6 and gate-rows-v3)
rc=1 out_exists=no
## T4 equal paths
REFUSED: input and output are the same path
rc=1 sha_after=515cf4704ebba5bd
## T5 same file by another name (symlink)
REFUSED: input and output are the same path
rc=1 sha_after=515cf4704ebba5bd
## T6 output already exists
REFUSED: output path already exists or is a symlink (this script never overwrites and never follows a link)
rc=1 content=keep
## T7 failed edit (old text of edit 3 damaged in a scratch copy of the edit list)
damaged edit 3 old text
REFUSED: 1 edit(s) did not find their old text exactly once; nothing written
29 old edits; corrected or added: ['2', '4', '5', '18', '19', '20', '21', '29', '30']
failing [('3', 0)]
rc=1 out_exists=no
## T8 missing output folder
REFUSED: output folder does not exist
rc=1
## T9 wrong argument count
REFUSED: usage: apply-v10-after-chain.py <chained plan> <new output file>
rc=1
## T10 RENUMBER line deleted (must refuse)
REFUSED: corrections file must hold exactly one RENUMBER line, found 0
rc=1 out_exists=no sha=
## T11 shift=0 (must refuse: edits 8, 13, 27 would not change)
REFUSED: RENUMBER changed nothing in edit(s) ['8', '13', '27'] (shift 0 or from/to range wrong); nothing written
29 old edits; corrected or added: ['2', '4', '5', '18', '19', '20', '21', '29', '30']
failing []
rc=1 out_exists=no sha=
## T12 'shift = 4' with spaces (malformed, must refuse)
REFUSED: RENUMBER line is malformed: 'RENUMBER edits=8,13,27 from=13 to=16 shift = 4'
rc=1 out_exists=no sha=
## T13 shift=4 text with a non-integer shift=x (must refuse)
REFUSED: RENUMBER line is malformed: 'RENUMBER edits=8,13,27 from=13 to=16 shift=x'
rc=1 out_exists=no sha=
## T14 to=15 (decision: accepted, item 16 is not referenced by edits 8, 13, 27, so the sha must stay 28f92c5d)
29 old edits; corrected or added: ['2', '4', '5', '18', '19', '20', '21', '29', '30']
failing []
written /tmp/tmp.09o5QykTbG/rn-to15/out.md 28f92c5d1211207c 780 lines
rc=0 out_exists=yes sha=28f92c5d1211207c
## T15 shift=4 but edit list reduced to 8,13 (must refuse: 27 missing)
REFUSED: RENUMBER must list edits 8, 13 and 27
rc=1 out_exists=no sha=
## T16 dangling symlink as output (must refuse, nothing created at the target)
REFUSED: output path already exists or is a symlink (this script never overwrites and never follows a link)
rc=1 target_exists=no
## T17 symlink to an existing file as output (must refuse, file untouched)
REFUSED: output path already exists or is a symlink (this script never overwrites and never follows a link)
rc=1 content=keep2
scratch folder: /tmp/tmp.09o5QykTbG (left in place; nothing in the repository was changed)
```
Script exit code of the test run: 0 (the test script itself always ends 0; the per-case rc= lines above are the results).
