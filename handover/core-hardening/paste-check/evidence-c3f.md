# evidence-c3f (raw, 2026-11-16). Builder output, no verdicts. Test copies live in the scratchpad; the real inputs/ file was not edited.
## 1 patch apply order, fresh copy of inputs/ (patch -p1)
$ patch -p1 --dry-run < paste-check/plan-v5-fixes.patch
checking file inputs/plan-wp6-resmoke-v5.md
rc=0
$ real apply fixes
patching file inputs/plan-wp6-resmoke-v5.md
rc=0
$ patch -p1 --dry-run < paste-check/plan-v5-repin-v3.patch
checking file inputs/plan-wp6-resmoke-v5.md
rc=0
$ real apply v3
patching file inputs/plan-wp6-resmoke-v5.md
rc=0
$ cmp result vs build copy v3
cmp rc=0
$ order check: v3 dry-run on the ORIGINAL plan (fixes not applied), expected to fail
Hunk #14 succeeded at 509 (offset -2 lines).
Hunk #15 FAILED at 559.
5 out of 15 hunks FAILED
rc=1
$ sha256 of the real inputs/ file and of the untouched copy (must be equal)
67a0a195537de875
67a0a195537de875
## 2 placeholder counts on the patched plan (grep -c counts LINES)
FINAL lines (expect 24): 24
LEAD-FILL lines (expect 10): 10
$ lines holding FINAL placeholders
      3 2;      3 121;      3 236;      1 517;      1 519;      1 520;      1 521;      1 522;      1 523;      1 524;      1 525;      1 526;      1 527;      1 528;      1 529;      1 530;      1 531;      1 532;      1 533;      1 534;      1 535;      1 536;      1 537;      1 538;
$ simulate the lead filling every placeholder and answering every marker: counts must go to 0 and 0
FINAL: 0
LEAD-FILL: 0
$ stray blank line between UNVERIFIED 11 and 12 (expect item 11 line directly above item 12)
563-11. Round 5 (`nlite-fix5`, branch `t
564:12. That the installed Docker CLI ac
$ blank lines in the file (line numbers), v2-applied vs v3
8 40 75 83 99 105 107 115 131 165 174 191 213 222 224 226 229 245 263 273 281 299 310 314 319 323 327 335 343 347 405 412 429 451 468 493 496 509 513 551 
$ names check (lines holding nlite-fix5 or nlite-int-r5)
2 3 77 121 236 495 515 563 566 568 
$ other numbers: floor lines
23:171 min clean is a floor (HISTORY: section 5 now says 172 min = 2 h 52 min) 
73:172 min = 2 h 52 min) 
448:172 min = 2 h 52 min** 
$ run the last-check commands of the RE-PIN line on the patched plan (P path swapped to the test copy)
24
rc=0
## 3 shell syntax of the new or changed spans (extracted from the PATCHED plan)
bash -n gone.sh rc=0
dash -n gone.sh rc=0
bash -n P-3b.sh rc=0
dash -n P-3b.sh rc=0
bash -n repin0.sh rc=0
dash -n repin0.sh rc=0
bash -n repin1.sh rc=0
dash -n repin1.sh rc=0
bash -n repin2.sh rc=0
dash -n repin2.sh rc=0
bash -n repin3.sh rc=0
repin3.sh: 1: Syntax error: "(" unexpected
dash -n repin3.sh rc=2
bash -n repin4.sh rc=0
dash -n repin4.sh rc=0

## 4 behaviour with STUBS (plain bash on this Linux container; NOT Git Bash, NOT PowerShell, NOT WSL; stub repos and fake scripts, no real nlite worktree)
### 4.1 gone() with a fake n8n_kill.py (note: 'ss' is not installed in this container, so the port-wait loop sees no listener; pgrep is real)
--- fake exits 0, prints confirmed gone
kill exit=0
GONE-OK
gone rc=0
--- fake exits 3, prints confirmed gone
kill exit=3
GONE-FAIL: kill exit=3, expected 0 only (3 = an unreadable n8n-shaped process of this user exists, per lead): STOP (R1: no fallback kill)
gone rc=1
--- fake exits 1, prints confirmed gone
kill exit=1
GONE-FAIL: kill exit=1, expected 0 only (3 = an unreadable n8n-shaped process of this user exists, per lead): STOP (R1: no fallback kill)
gone rc=1
--- fake exits 2, prints confirmed gone
kill exit=2
GONE-FAIL: kill exit=2, expected 0 only (3 = an unreadable n8n-shaped process of this user exists, per lead): STOP (R1: no fallback kill)
gone rc=1
--- fake exits 0 without 'confirmed gone'
x
kill exit=0
GONE-FAIL: STOP (R1: no fallback kill)
gone rc=1
### 4.2 fill command and diff commands against stub git repos
--- fill command, strings.txt present
full=060caa8912a5a24b57dced1caedd6dc39f0e280c seven=060caa8 branch=take/r5
S1 n8n_start.sh 3
S5 n8n_start.sh 2
K4 n8n_kill.py 1
H1 run_real_check_n8n.py 
rc=0
--- fill command, strings.txt absent
full=060caa8912a5a24b57dced1caedd6dc39f0e280c seven=060caa8 branch=take/r5
strings.txt not written yet (run this paste again after P-3a)
--- cat-file test, round-3 commit known to the fix5 stub
known
--- cat-file test, round-3 commit NOT known (other repo)
unknown
--- diff + grep, known case
-print("confirmed gone")
+print("), confirmed gone")
+    sys.exit(3)
--- diff --no-index variant, unknown case (round-3 worktree w3 read separately)
-print("confirmed gone")
+print("), confirmed gone")
+    sys.exit(3)
### 4.3 P-3b span with P-4b variants (cd line swapped to a stub folder)
--- A good P-4b.sh + control with hash line and one hit line (expect only the count 20)
20
--- B comment-only P-4b.sh
P-4b.sh has no command line: STOP
20
--- C control file missing
P-4b.control.txt missing or has fewer than 2 non-empty lines: STOP
P-4b.control.txt first line does not hold the sha256 of P-4b.sh: STOP
20
--- D control first line has another sha256
P-4b.control.txt first line does not hold the sha256 of P-4b.sh: STOP
20
--- E empty P-4b.sh
P-4b.sh missing or empty: STOP
P-4b.sh has no command line: STOP
20
--- F both missing
P-4b.sh missing or empty: STOP
grep: pastes/P-4b.sh: No such file or directory
P-4b.sh has no command line: STOP
P-4b.control.txt missing or has fewer than 2 non-empty lines: STOP
../p3b-stub.sh: line 1: pastes/P-4b.sh: No such file or directory
P-4b.control.txt first line does not hold the sha256 of P-4b.sh: STOP
20
--- G control has the hash line only (no hit line)
P-4b.control.txt missing or has fewer than 2 non-empty lines: STOP
20
### 4.4 PROPOSED P-4b.sh body (paste-check/LEAD-FILL-list.md), stub test as uid 65534 (nobody) with a process that is not dumpable, so its environ is unreadable to that uid
bash -n rc=0
dash -n rc=0
--- as root, no n8n-named process
exit=0
--- as nobody, no stub process (negative control)
exit=0
--- as nobody, stub process pid 3477 running (positive control)
P-4b-HIT pid=3477
exit=0
stub processes left: 0
