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
