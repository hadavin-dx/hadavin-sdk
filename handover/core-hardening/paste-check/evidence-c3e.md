# evidence-c3e.md (raw, 2026-11-16). Builder output, no verdicts. Test copies live in the scratchpad; the real inputs/ file was not edited.

## 1 patch apply order (apply.txt)
$ cd <folder holding inputs/>; patch -p1 --dry-run < paste-check/plan-v5-fixes.patch
checking file inputs/plan-wp6-resmoke-v5.md
rc=0
$ real apply of fixes
patching file inputs/plan-wp6-resmoke-v5.md
rc=0
$ patch -p1 --dry-run < paste-check/plan-v5-repin-v2.patch
checking file inputs/plan-wp6-resmoke-v5.md
rc=0
$ real apply of v2
patching file inputs/plan-wp6-resmoke-v5.md
rc=0
$ cmp result vs build copy
cmp rc=0
$ order check: v2 dry-run on the ORIGINAL plan (no fixes first), must fail
checking file inputs/plan-wp6-resmoke-v5.md
Hunk #4 FAILED at 107.
Hunk #7 FAILED at 225.
Hunk #8 FAILED at 412.
Hunk #9 succeeded at 427 (offset -2 lines).
Hunk #10 succeeded at 440 (offset -2 lines).
Hunk #11 succeeded at 463 (offset -2 lines).
Hunk #12 succeeded at 489 (offset -2 lines).
Hunk #13 succeeded at 509 (offset -2 lines).
Hunk #14 FAILED at 559.
4 out of 14 hunks FAILED
rc=1
$ untouched input unchanged:
cmp rc=0

## 2 shell syntax (syntax.txt)
$ bash -n env-resmoke.sh (plan section 3 block, plan-v2 lines 135-162)
rc=0
$ dash -n env-resmoke.sh
rc=0
$ bash -n gone.sh (gone() only)
rc=0
$ dash -n gone.sh
rc=0
$ bash -n P-3b.sh (P-3b span, with the new test -s)
rc=0
$ dash -n P-3b.sh
rc=0
$ bash -n RE-PIN loop and diff span (test copy)
rc=0
rc=0

## 3 behaviour with stubs (functional.txt)
--- gone() with a fake n8n_kill.py that prints "confirmed gone" and exits 3
n8n 1 confirmed gone
kill exit=3
ports free after 0s; groups of 4242 left: 1
GONE-FAIL: kill exit=3 (per lead: an unreadable n8n-shaped process of this user exists): STOP (R1: no fallback kill)
gone rc=1
--- same with exit 0 (must still pass)
n8n 1 confirmed gone
kill exit=0
ports free after 0s; groups of 4242 left: 1
GONE-FAIL: STOP (R1: no fallback kill)
gone rc=1
--- run.sh form with an empty-output P-4b.sh (copy of run.sh, EV and paste path changed to temp)
== P-4b 2026-11-16T09:35:50Z
exit=0
--- P-3b test -s: missing / empty / ok
P-4b.sh missing or empty: STOP
P-4b.sh missing or empty: STOP
(third case printed nothing: ok)
--- (re-run with a pgrep stub that prints nothing; the first run counted its stub line as a live group)
n8n 1 confirmed gone
kill exit=0
ports free after 0s; groups of 4242 left: 0
GONE-OK
gone rc=0
n8n 1 confirmed gone
kill exit=3
ports free after 0s; groups of 4242 left: 0
GONE-FAIL: kill exit=3 (per lead: an unreadable n8n-shaped process of this user exists): STOP (R1: no fallback kill)
gone rc=1

## 4 RE-PIN loop and diff span run on a made-up git repo (Linux bash; paths replaced by temp paths)
$ bash loop.sh  (strings.txt: S1 present at line 3, K1 at line 2, H1 absent)
S1 n8n_start.sh 3
K1 n8n_kill.py 2
H1 n8n_start.sh 
rc=0
$ bash diff.sh  (new text: return 5)
+return 5
rc=0

## 5 placeholder count in the patched plan (pattern that does not match itself)
grep -c '<FINAL[-]' plan: 24  (expected 24 = lines 2, 121, 236, header 517, 20 cells)
2 121 236 517 519 520 521 522 523 524 525 526 527 528 529 530 531 532 533 534 535 536 537 538 

## 6 repo guard BANNED strings in the patch: none found (test_no_reference_material.py list)

## 7 Builder notes (REPORT-repin-v2.md could not be written: the Write tool refused report files for sub-agents; these notes stand in)
FAILURES FIRST
- v1 slip, fixed: plan-v5-repin.patch deleted plan items 12 and 13 of "UNVERIFIED in this plan" (hunk 559,561c561). v2 restores both verbatim (patched plan lines 565-566).
- Needs the lead: pastes\P-4b.sh (command unknown; run stops at P-3a without it); the four placeholder places; confirm folder nlite-fix5 and branch take/nlite-int-r5 (UNVERIFIED 14); eec6ba4 existing in that worktree is unchecked.
- Not run: PowerShell, wsl.exe, Git Bash, real n8n scripts. Loop, gone(), run.sh, P-3b test -s ran on Linux with a made-up repo and stubs (sections 3, 4).
- S9 "round 1" / "B2 round" are defined as restart rounds in the WORDS line, not renamed.
CHANGES (plan lines after both patches): WORDS 4, R5 exceptions 113, RE-PIN 3 (four places, F/WT/SF defined, return in grep, final check grep -c '<FINAL[-]' = 0), section 11 515-538 (phrase "final-head column", cells FINAL-LINES), P-4b 243 (+ 228, 230, 231, 241), section 5 now 172 min = 2 h 52 min (433, 448), row U1 476 (21 rows), exit 3 "per lead" 153, R2 no-op clause 110 (+13.1, 13.3), MUST-NOT 495, items 14 and 15 (567-568), history rows 20 and 26 marked HISTORY.
APPLY (folder holding inputs/): cd /home/user/hadavin-sdk/handover/core-hardening && patch -p1 < paste-check/plan-v5-fixes.patch && patch -p1 < paste-check/plan-v5-repin-v2.patch   (not together with the old repin patch)
