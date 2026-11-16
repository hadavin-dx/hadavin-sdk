# evidence-c3g (raw, 2026-11-16). Builder output, no verdicts. Test copies live in the scratchpad (/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/v4); the real inputs/ file was not edited. Stub tests only: plain bash/dash on this Linux container, not Git Bash, not PowerShell, not WSL.
## 1 patch apply order, fresh copy of inputs/ (patch -p1)
$ patch -p1 --dry-run < plan-v5-fixes.patch
checking file inputs/plan-wp6-resmoke-v5.md
rc=0
$ real apply fixes
patching file inputs/plan-wp6-resmoke-v5.md
rc=0
$ patch -p1 --dry-run < plan-v5-repin-v4.patch
checking file inputs/plan-wp6-resmoke-v5.md
rc=0
$ real apply v4
patching file inputs/plan-wp6-resmoke-v5.md
rc=0
$ cmp result vs build copy
cmp rc=0
$ patch residue files (.orig/.rej)
plan-wp6-resmoke-v5.md
$ order check: v4 dry-run on the ORIGINAL plan (fixes not applied), expected to fail
Hunk #14 succeeded at 509 (offset -2 lines).
Hunk #15 FAILED at 559.
5 out of 15 hunks FAILED
rc=1
$ order check: v4 dry-run on a plan that already has v3 (two re-pin patches), expected to fail
Hunk #14 FAILED at 508.
Hunk #15 FAILED at 556.
15 out of 15 hunks FAILED
rc=1
$ sha256 (first 16) of the real inputs/ file and of the untouched copy (must be equal)
67a0a195537de875
67a0a195537de875
## 2 placeholder and marker counts on the patched plan (grep -c counts LINES)
FINAL lines (expect 24): 24
LEAD-FILL lines (expect 10): 10
$ marker places (grep -n -o)
2:LEAD-FILL 7 3:LEAD-FILL 5 3:LEAD-FILL 6 3:LEAD-FILL 9 3:LEAD-FILL 7 4:LEAD-FILL 8 4:LEAD-FILL 3 110:LEAD-FILL 4 243:LEAD-FILL 1 243:LEAD-FILL 1b 243:LEAD-FILL 2 243:LEAD-FILL 1b 258:LEAD-FILL 6 416:LEAD-FILL 4 417:LEAD-FILL 4 566:LEAD-FILL 7 567:LEAD-FILL 1
marker texts: 17
$ Grep-tool style, line numbers of hits before any fill: FINAL then LEAD-FILL
2 121 236 517 519 520 521 522 523 524 525 526 527 528 529 530 531 532 533 534 535 536 537 538
2 3 4 110 243 258 416 417 566 567
$ simulated fill of every placeholder and flip of every marker: must go to 0 and 0
0
0
$ partial flip, all markers except 1b: the list command and the count still show it
243:LEAD-FILL 1b
243:LEAD-FILL 1b
1
$ last-check and names-check commands as printed in the plan (PF value swapped to the test copy)
24
10
2:nlite-fix5
2:nlite-int-r5
2:nlite-fix5
2:nlite-int-r5
3:nlite-fix5
3:nlite-fix5
3:nlite-fix5
3:nlite-fix5
3:nlite-fix5
3:nlite-int-r5
77:nlite-fix5
77:nlite-int-r5
121:nlite-fix5
236:nlite-fix5
495:nlite-fix5
515:nlite-fix5
515:nlite-int-r5
563:nlite-fix5
563:nlite-int-r5
566:nlite-fix5
566:nlite-int-r5
568:nlite-fix5
$ stray things: lines holding @@ (pre-existing in the original plan, 2 lines), blank line check not repeated (unchanged since v3)
2
## 3 shell syntax of the new or changed spans (extracted from the PATCHED plan)
bash -n P-3b rc=0
dash -n P-3b rc=0
bash -n fill rc=0
dash -n fill rc=0
bash -n diff-known rc=0
dash -n diff-known rc=0
bash -n diff-unknown rc=0
/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/v4/ex/diff-unknown.sh: 1: Syntax error: "(" unexpected
dash -n diff-unknown rc=2
bash -n last rc=0
dash -n last rc=0
bash -n names rc=0
dash -n names rc=0
bash -n gone rc=0
dash -n gone rc=0
bash -n P-4b-proposal rc=0
dash -n P-4b-proposal rc=0
## 4 P-3b span (extracted from the patched plan, cd line swapped to a stub folder). Expected literal log of a good run: -- scan / scan exit=1 / compile exit=0 / syntax end / P-4b files ok / strings bad lines: 0 / strings lines: 20 (run.sh adds the == and exit= lines; not part of this stub)
--- A good
   -- scan
   scan exit=1
   compile exit=0
   syntax end
   P-4b files ok
   strings bad lines: 0
   strings lines: 20
--- B CR in P-4b.sh (expect a hit line, scan exit=0, P-4b files STOP)
   -- scan
   pastes/P-4b.sh:1:#!/bin/bash^M
   pastes/P-4b.sh:2:exit 0^M
   scan exit=0
   compile exit=0
   syntax end
   P-4b files STOP
   strings bad lines: 0
   strings lines: 20
--- C CR in the control file only
   -- scan
   pastes/P-4b.control.txt:1:P-4b.sh sha256 a396b74778517c2cbdca0243a1cd5a151c1a514e0a00eb287dfee6c9fa9490da^M
   pastes/P-4b.control.txt:2:P-4b-HIT pid=123^M
   scan exit=0
   compile exit=0
   syntax end
   P-4b files STOP
   strings bad lines: 0
   strings lines: 20
--- D P-4b.sh missing
   -- scan
   scan exit=1
   compile exit=0
   syntax end
   P-4b files STOP
   strings bad lines: 0
   strings lines: 20
--- E control missing
   -- scan
   grep: pastes/P-4b.control.txt: No such file or directory
   scan exit=2
   compile exit=0
   syntax end
   P-4b files STOP
   strings bad lines: 0
   strings lines: 20
--- F both missing
   -- scan
   grep: pastes/P-4b.control.txt: No such file or directory
   scan exit=2
   compile exit=0
   syntax end
   P-4b files STOP
   strings bad lines: 0
   strings lines: 20
--- G wrong hash
   -- scan
   scan exit=1
   compile exit=0
   syntax end
   P-4b files STOP
   strings bad lines: 0
   strings lines: 20
--- H hash inside a longer first line (the old unanchored grep -qF would pass)
   -- scan
   scan exit=1
   compile exit=0
   syntax end
   P-4b files STOP
   strings bad lines: 0
   strings lines: 20
--- I later control line has the wrong shape
   -- scan
   scan exit=1
   compile exit=0
   syntax end
   P-4b files STOP
   strings bad lines: 0
   strings lines: 20
--- J control holds the hash line only
   -- scan
   scan exit=1
   compile exit=0
   syntax end
   P-4b files STOP
   strings bad lines: 0
   strings lines: 20
--- K comment-only P-4b.sh with a matching hand-written control
   -- scan
   scan exit=1
   compile exit=0
   syntax end
   P-4b files STOP
   strings bad lines: 0
   strings lines: 20
--- L bad strings line
   -- scan
   scan exit=1
   compile exit=0
   syntax end
   P-4b files ok
   strings bad lines: 1
   strings lines: 21
--- M empty P-4b.sh
   -- scan
   scan exit=1
   compile exit=0
   syntax end
   P-4b files STOP
   strings bad lines: 0
   strings lines: 20
--- N non-ASCII byte in another file
   -- scan
   env-resmoke.sh:1:cafM-CM-)
   scan exit=0
   compile exit=0
   syntax end
   P-4b files ok
   strings bad lines: 0
   strings lines: 20
--- O shell syntax error in a paste
   -- scan
   scan exit=1
   compile exit=0
   pastes/P-1.sh: line 1: syntax error near unexpected token `then'
   pastes/P-1.sh: line 1: `if then'
   syntax: pastes/P-1.sh
   syntax end
   P-4b files ok
   strings bad lines: 0
   strings lines: 20
## 5 fill command, diff commands and acceptance rule against stub git repos (round-3 stub repo wt3, round-5 stub repo g; strings.txt stub with 5 rows)
--- fill command, strings.txt present (H1: file not in scripts/ -> FILE-MISSING; H2 present; X1 string absent -> empty field)
full=aa965c8f00bf4c81ba5f20f44316f81608b8d560 seven=aa965c8 branch=master
S1 n8n_start.sh 3
K4 n8n_kill.py 1
H1 run_real_check_n8n.py FILE-MISSING
H2 other.py 1
X1 n8n_kill.py 
--- fill command, strings.txt absent
full=aa965c8f00bf4c81ba5f20f44316f81608b8d560 seven=aa965c8 branch=master
strings.txt not written yet (run this paste again after P-3a)
--- fill command, strings.txt with CRLF
full=aa965c8f00bf4c81ba5f20f44316f81608b8d560 seven=aa965c8 branch=master
strings.txt holds a CR (CRLF): STOP
--- cat-file test: eec6ba4 is not in the stub, the stub round-3 commit is
unknown
known
--- diff (known case, eec6ba4 replaced by the stub round-3 sha), then the acceptance rule applied mechanically
-print("confirmed gone")
+print("), confirmed gone")
+sys.exit(3)
ACCEPT
--- diff --no-index variant (unknown case), then the acceptance rule
-print("confirmed gone")
+print("), confirmed gone")
+sys.exit(3)
ACCEPT
--- acceptance rule on made-up outputs
input: +sys.exit(main())
+sys.exit(3)
STOP (other exit lines=1, literal 3 lines=1)
input: +print("x")
+EXIT_CODE = 3
STOP (other exit lines=1, literal 3 lines=0)
input: +    EXIT 4
+sys.exit(3)
STOP (other exit lines=1, literal 3 lines=1)
input: +die() { exit 2; }
STOP (other exit lines=0, literal 3 lines=0)
input: -sys.exit(1)
+sys.exit(3)
+die() { exit 2; }
beh.sh: line 35: printf: -s: invalid option
printf: usage: printf [-v var] format [arguments]
STOP (other exit lines=0, literal 3 lines=0)
## 6 gone() (unchanged code, rerun) with a fake n8n_kill.py; ss is not installed here, so the port-wait loop sees no listener
--- fake exits 0, confirmed gone printed: yes
), confirmed gone
kill exit=0
ports free after 0s; groups of 99999 left: 0
GONE-OK
gone-rc=0
--- fake exits 3, confirmed gone printed: yes
), confirmed gone
kill exit=3
ports free after 0s; groups of 99999 left: 0
GONE-FAIL: kill exit=3, expected 0 only (3 = an unreadable n8n-shaped process of this user exists, per lead): STOP (R1: no fallback kill)
gone-rc=1
--- fake exits 1, confirmed gone printed: yes
), confirmed gone
kill exit=1
ports free after 0s; groups of 99999 left: 0
GONE-FAIL: kill exit=1, expected 0 only (3 = an unreadable n8n-shaped process of this user exists, per lead): STOP (R1: no fallback kill)
gone-rc=1
--- fake exits 2, confirmed gone printed: yes
), confirmed gone
kill exit=2
ports free after 0s; groups of 99999 left: 0
GONE-FAIL: kill exit=2, expected 0 only (3 = an unreadable n8n-shaped process of this user exists, per lead): STOP (R1: no fallback kill)
gone-rc=1
--- fake exits 0, confirmed gone printed: no

kill exit=0
ports free after 0s; groups of 99999 left: 0
GONE-FAIL: STOP (R1: no fallback kill)
gone-rc=1
## 7 proposed P-4b.sh (LEAD-FILL-list.md), end to end with P-3b. Stub process: python as uid 65534, command line holds n8n-stub, not dumpable (environ unreadable); P-4b.sh run as uid 65534 with setpriv
--- negative control (no stub process)
exit=0
--- positive control, stub pid 24307
P-4b-HIT pid=24307
exit=0
stub processes left: 0
--- control file made as the list says (sha256sum pastes/P-4b.sh), then P-3b span
P-4b.sh sha256 6f102c5dc44b153
P-4b-HIT pid=20696
done
P-4b files STOP
(the line above: P-4b.sh edited after the control was made)
-- scan
scan exit=1
compile exit=0
syntax end
P-4b files ok
strings bad lines: 0
strings lines: 20
