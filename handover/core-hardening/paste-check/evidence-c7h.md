# evidence-c7h.md - raw output of the revision 10 test runs (checklist and fill list)

Run on 2026-11-16T11:54Z, Linux, bash GNU bash, version 5.2.21(1)-release (x86. NOT run: Git Bash on Windows, WSL, PowerShell, the real laptop, the real plan folders. cygpath is a stub that maps the scratch tree to a Windows-looking path. Scratch tree, made-up data, no secrets, nothing outside /tmp touched. User name in paths masked.

## 1. Syntax of every code block

Command: `bash -n` and `dash -n` on each of the 42 extracted blocks (no output means pass).
Result: bash -n passed 42 of 42; dash -n passed 42 of 42.

## 2.2 Full walk of the blocks A1 to D2, CHAIN=2 (raw)
```
## block 01 (variables, CHAIN=2)
STOP VARS form: HB is '/tmp/v10t/hb', not in Git Bash form /c/Users/... Next: write it in that form in section 1.
STOP VARS form: CH is '/tmp/v10t/ch', not in Git Bash form /c/Users/... Next: write it in that form in section 1.
PF=/tmp/v10t/hb/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md
EV=/tmp/v10t/hb/egm/duplicate-proof-lead-desk/wp6/evidence-2
PASTES=/tmp/v10t/hb/_local/scratch/wp6-smoke/pastes
[rc=0]

## block 02 (step)
ok A1: made /tmp/v10t/hb/_local/scratch/lead-plan-work
[rc=0]

## block 03 (step)
ok plan-v5-fixes.patch no CR
ok plan-v5-repin-v6.patch no CR
ok plan-v5-gate-rows-v3.patch no CR
ok apply-v10-after-chain.py no CR
ok plan-v10-real-v5-edits.md no CR
ok plan-v10-corrections-after-chain.md no CR
ok acc5.sh no CR
ok LEAD-FILL-list-v5.md no CR
ok plan-v5-fixes.patch checksum
ok plan-v5-repin-v6.patch checksum
ok plan-v5-gate-rows-v3.patch checksum
ok original checksum
ok original no CR
[rc=0]

## block 04 (step)
ok A3
[rc=0]

## block 05 (step)
ok A4
[rc=0]

## block 06 (step)
CHAIN=2: chain step 3 skipped
[rc=0]

## block 07 (step)
CHAIN=2: chain step 4 skipped
[rc=0]

## block 08 (step)
plan-wp6-resmoke-v5.md
ok A5c
[rc=0]

## block 09 (step)
ok A6 counts 24 10 2 1
ok A6 plan checksum for CHAIN=2 (39af84aec78b650f)
[rc=0]

## block 10 (step)
2:LEAD-FILL 7
3:LEAD-FILL 5
3:LEAD-FILL 6
3:LEAD-FILL 9
3:LEAD-FILL 7
4:LEAD-FILL 8
4:LEAD-FILL 3
125:LEAD-FILL 4
258:LEAD-FILL 1
258:LEAD-FILL 1b
258:LEAD-FILL 2
258:LEAD-FILL 1b
275:LEAD-FILL 6
433:LEAD-FILL 4
434:LEAD-FILL 4
585:LEAD-FILL 7
586:LEAD-FILL 1
ok A7 marker lines are 2,3,4,125,258,275,433,434,585,586
[rc=0]

## block 04 (A3 re-run)
ok A3 (already done: the plan in the work folder is further along, at a later chain step; nothing changed. A6 checks it against your CHAIN)
[rc=0]

## block 05 (A4 re-run)
ok A4 (already applied: the plan in the work folder is the result of this step; nothing changed)
[rc=0]

## block 06 (A5b re-run)
CHAIN=2: chain step 3 skipped
[rc=0]

## block 07 (A5b4 re-run)
CHAIN=2: chain step 4 skipped
[rc=0]

## block 11 (A8)
ok A8 copied
[rc=0]

## block 11 (A8 re-run)
ok A8 (PF already equals the untouched patched plan; nothing changed): go on to A9
[rc=0]

## block 12 (A9 check (expect not 1/2/..))
windows form: C:\Users\USER\Downloads\Hadavin\egm\duplicate-proof-lead-desk\wp6\plan-wp6-resmoke-v5.md
mixed form (drive letter, forward slashes; the form the plan writes after PF=): C:/Users/USER/Downloads/Hadavin/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md
string (1) found: 1 (must be 1)
strings (2) and (3) found: 2 (must be 2)
evidence folder named in plan: 1 (must be 1 or more)
pastes folder named in plan: 1 (must be 1 or more)
[rc=0]

## block 12 (A9 check after line 3 fix)
windows form: C:\Users\USER\Downloads\Hadavin\egm\duplicate-proof-lead-desk\wp6\plan-wp6-resmoke-v5.md
mixed form (drive letter, forward slashes; the form the plan writes after PF=): C:/Users/USER/Downloads/Hadavin/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md
string (1) found: 1 (must be 1)
strings (2) and (3) found: 2 (must be 2)
evidence folder named in plan: 1 (must be 1 or more)
pastes folder named in plan: 1 (must be 1 or more)
[rc=0]

## block 13 (A9 flip (PF_CONFIRMED=no))
STOP A9: not confirmed (PF_CONFIRMED), no drive letter, or the counts are not 1 and 2: nothing changed. Next: fix line 3 of PF or PF_CONFIRMED, then run this block again.
[rc=0]

## block 13 (A9 flip yes)
ok A9: marker 9 flipped; left:
(end of list)
[rc=0]

## block 14 (B1 accept 3 4 8)
2:LEAD-FILL 7
3:LEAD-FILL 5
3:LEAD-FILL 6
3:LEAD-FILL 7
258:LEAD-FILL 1
258:LEAD-FILL 1b
258:LEAD-FILL 2
258:LEAD-FILL 1b
275:LEAD-FILL 6
585:LEAD-FILL 7
586:LEAD-FILL 1
(end of list; CR count in PF: 0, must be 0)
[rc=0]
accept 2:
STOP B1: question 2 is an open ruling (L1). Next: get the ruling, write L1_RULED=yes in section 1 (see the row of question 2 in LEAD-FILL-list-v5.md). Nothing changed.
accept 5:
STOP B1: question 5 is answered only by its own block (5 and 7 by C2, 9 by A9). Next: do that block. Nothing changed.
accept 1:
STOP C2b: question 1 is answered only when the check C2c prints 'P-4b files ok'. Next: run C2c and fix what it says. Nothing changed.
## C1 rows with PIN empty

## block 15 (C1)
head=5861a9726cc48d873367878b2e9584d9b1c3189d seven=5861a97 branch=take/nlite-int-r5
PIN empty: first run, read only (nothing changed)
[rc=0]

## block 16 (C2)
ok C2
3:LEAD-FILL 6
258:LEAD-FILL 1
258:LEAD-FILL 1b
258:LEAD-FILL 2
258:LEAD-FILL 1b
275:LEAD-FILL 6
586:LEAD-FILL 1
(end of list; CR count in PF: 0, must be 0)
left placeholders (sha/branch must be 0): 0; table rows still open: 20 (must be 20 until C4)
[rc=0]

## block 16 (C2 re-run)
ok C2
3:LEAD-FILL 6
258:LEAD-FILL 1
258:LEAD-FILL 1b
258:LEAD-FILL 2
258:LEAD-FILL 1b
275:LEAD-FILL 6
586:LEAD-FILL 1
(end of list; CR count in PF: 0, must be 0)
left placeholders (sha/branch must be 0): 0; table rows still open: 20 (must be 20 until C4)
[rc=0]

## block 17 (C2b(1))
11:    return 3  # unreadable process
[rc=0]

## block 18 (C2b(2))
syntax ok
CR count: 0 (must be 0)
non-ASCII bytes: 0 (must be 0)
word scan:
(end: nothing above is right)
[rc=0]

## block 18 (C2b(2) re-run (must refuse))
STOP C2b: /tmp/v10t/hb/_local/scratch/wp6-smoke/pastes/P-4b.sh already exists (a file you may have changed). Next: keep it and go to step (3); or, to start from the proposal again: mv "/tmp/v10t/hb/_local/scratch/wp6-smoke/pastes/P-4b.sh" "/tmp/v10t/hb/_local/scratch/wp6-smoke/pastes/P-4b.sh.old" (i
[rc=0]
## wsl form

## block 19 (HBW)
HBW='/mnt/tmp/v10t/hb'
[rc=0]
## C2c before control exists

## block 25 (C2c)
STOP C2c: missing or empty: /tmp/v10t/hb/_local/scratch/wp6-smoke/pastes/P-4b.control.txt. Next: make it (C2b).
[rc=1]

######## PART 2: WSL blocks as uid 65534
## WSL block 20
/tmp/v10t/hb/_local/scratch/wp6-smoke/pastes
user: nobody uid=65534 (must not be 0)
dash -n ok
[rc=0]
## WSL block 21
Could not find platform dependent libraries <exec_prefix>
stand-in pid=15674
me=65534
65534 /proc/15674
0 /proc/15674/environ
status-uid=65534
/tmp/v10t/blocks/21.sh: line 1: /proc/15674/environ: Permission denied
[rc=0]
## WSL block 22
exit=0
P-4b.sh sha256 21d00f1c69cbc5bc5ef29772e351ea972c5754d556bd77e292615adbc2d3497c
P-4b-HIT pid=15674
[rc=0]
## WSL block 24
gone
[rc=0]
## WSL-4 alone, stand-in alive in another window (expect ALIVE and STOP)
Could not find platform dependent libraries <exec_prefix>
ALIVE pid=16092
STOP C2b: a stand-in is still alive. Next: wait up to 10 minutes (it ends by itself), or, if it is yours, end it by its exact pid typed by you; run WSL-4 again.
[rc=0]
ls: cannot access 'standin-gone.txt': No such file or directory
## WSL-4 after it ended by itself
gone
gone control=23d45ac6cc4eb384
## WSL-1 as root (must refuse)
user: root uid=0 (must not be 0)
STOP C2b: wrong folder, root user, or dash -n failed. Next: fix it (HBW line, user, P-4b.sh), run WSL-1 again.
total 12
-rw-r--r-- 1 nobody nogroup  99 Nov 16 11:53 P-4b.control.txt
-rw-rw-rw- 1 root   root    719 Nov 16 11:53 P-4b.sh
-rw-r--r-- 1 nobody nogroup  30 Nov 16 11:53 standin-gone.txt
P-4b.sh sha256 21d00f1c69cbc5bc5ef29772e351ea972c5754d556bd77e292615adbc2d3497c
P-4b-HIT pid=15674

## block 23 (SP=<pid>)
/tmp/v10t/b23.sh: line 1: syntax error near unexpected token `;'
/tmp/v10t/b23.sh: line 1: `SP=<pid>; F="$EV/PROGRESS.md"; case "$SP" in ''|*[!0-9]*) echo "STOP C2b: SP must be digits. Next: write the pid printed by WSL-2 and run again.";; *) if evok; then if [ -s "$F" ] && [ -n "$(tail -c 1 "$F")" ]; then printf '\n' >> "$F"; fi; printf 'NOTE lead stand-in pid=%
[rc=2]

## block 23 (SP=)
STOP C2b: SP must be digits. Next: write the pid printed by WSL-2 and run again.
[rc=0]

## block 23 (SP=abc)
STOP C2b: SP must be digits. Next: write the pid printed by WSL-2 and run again.
[rc=0]

## block 23 (SP=15674)
NOTE lead stand-in pid=15674 2026-11-16T11:53Z
[rc=0]

## block 23 (SP=15674)
NOTE lead stand-in pid=15674 2026-11-16T11:53Z
NOTE lead stand-in pid=15674 2026-11-16T11:53Z
[rc=0]
NOTE lead stand-in pid=15674 2026-11-16T11:53Z
NOTE lead stand-in pid=15674 2026-11-16T11:53Z

## block 25 (C2c (expect P-4b files ok))
dash syntax ok
P-4b files ok
[rc=0]
## C2c with dash missing
NOTE C2c: dash is not installed in Git Bash, so dash -n was NOT run here (this is not a STOP). It is run in WSL in C2b step (3), block WSL-1.
P-4b files ok
## C2c negative: CR in P-4b.sh
STOP C2c: CR in /tmp/v10t/hb/_local/scratch/wp6-smoke/pastes/P-4b.sh. Next: make the file again in WSL (C2b step 4).
STOP C2c: a byte that is not plain ASCII in /tmp/v10t/hb/_local/scratch/wp6-smoke/pastes/P-4b.sh. Next: make the file again (C2b).
## C2c negative: word kill
STOP C2c: the word kill or env.sh is in P-4b.sh. Next: remove it, make the control file again (C2b).
dash syntax ok
STOP C2c: the first line of the control file does not hold the checksum of P-4b.sh. Next: make the control file again (C2b step 4).
## C2c negative: edited P-4b.sh (control hash mismatch)
dash syntax ok
STOP C2c: the first line of the control file does not hold the checksum of P-4b.sh. Next: make the control file again (C2b step 4).
## C2c negative: bad control line
dash syntax ok
STOP C2c: a control line has the wrong shape. Next: make the control file again (C2b step 4).
## C2c negative: non-ASCII
STOP C2c: a byte that is not plain ASCII in /tmp/v10t/hb/_local/scratch/wp6-smoke/pastes/P-4b.sh. Next: make the file again (C2b).
dash syntax ok
P-4b files ok
## accept 1 1b
258:LEAD-FILL 2
275:LEAD-FILL 6
(end of list; CR count in PF: 0, must be 0)

## block 26 (C3 brief)
STUDIO-PREAMBLE v1
You are working for Hadavin (solo AI studio, owner the owner). These rules bind you; the studio folder is <studio>/.

You are the RUNNER of the re-smoke plan. Read your steps only from this file: C:\Users\USER\Downloads\Hadavin\egm\duplicate-proof-lead-desk\wp6\plan-wp6-resmoke-v5.md (a different copy = STOP). Run plan step P-3a only (write the glue, the paste files and strings.txt with the Write tool; do NOT write
ok C3: brief saved in /tmp/v10t/hb/_local/scratch/lead-plan-work/runner-brief.txt (no placeholder to fill)
[rc=0]
STUDIO-PREAMBLE v1
You are the RUNNER of the re-smoke plan. Read your steps only from this file: C:\Users\USER\Downloads\Hadavin\egm\duplicate-proof-lead-desk\wp6\plan-wp6-resmoke-v5.md (a different copy = STOP). Run p
5
## C3 with bad BP
STOP C3: BP (/nonexistent) is not the studio preamble (first line STUDIO-PREAMBLE v1, containing EGM-GATE v1). Next: write BP in section 1 (file handover/BRIEF-PREAMBLE.md of the repository), set the variables.

## block 27 (C3b (no runner line yet))
runner lines in PROGRESS.md: 0 (must be 1 or more)
NOTE lead stand-in pid=15674 2026-11-16T11:53Z
NOTE lead stand-in pid=15674 2026-11-16T11:53Z
strings.txt exists
[rc=0]
## C9 now (no runner line) expect STOP

## block 35 (C9-early)
STOP C9: C7 is not clean. Next: run C7.
[rc=0]

## block 27 (C3b with runner line)
runner lines in PROGRESS.md: 1 (must be 1 or more)
NOTE lead stand-in pid=15674 2026-11-16T11:53Z
NOTE lead stand-in pid=15674 2026-11-16T11:53Z
P-3a done 2026-11-16T12:00Z
strings.txt exists
[rc=0]
## C4 rows

## block 28 (C4 rows)
head=5861a9726cc48d873367878b2e9584d9b1c3189d seven=5861a97 branch=take/nlite-int-r5
S1 n8n_start.sh 2
S2 n8n_start.sh 4
S3 n8n_start.sh 6
S4 n8n_start.sh 8
S5 n8n_start.sh 10
S6 n8n_start.sh 12
S7 n8n_start.sh 14
S8 n8n_start.sh 16
K1 n8n_kill.py 2
K2 n8n_kill.py 4
K3 n8n_kill.py 6
K4 n8n_kill.py 8
D1 n8n_drive.py 2
D2 n8n_drive.py 4
D3 n8n_drive.py 6
D4 n8n_drive.py 8
D5 n8n_drive.py 10
D6 n8n_drive.py 12
H1 run_real_check_n8n.py 2
H2 real-run-n8n.env.example 2
[rc=0]
head=5861a9726cc48d873367878b2e9584d9b1c3189d seven=5861a97 branch=take/nlite-int-r5
S1 n8n_start.sh 2
S2 n8n_start.sh 4

## block 29 (C4 fill)
rows filled by this run: 20 (20 the first time; 0 on a repeat is fine if open is 0)
rows still open: 0 (must be 0)
CR count: 0
ok C4: now run: accept 6
[rc=0]
258:LEAD-FILL 2
(end of list; CR count in PF: 0, must be 0)

## block 30 (C5 known)
known
== n8n_start.sh
+die() { echo "refused: $1" >&2; exit 2; }
== n8n_kill.py
+    return 3  # unreadable process
+    print("confirmed gone")
+sys.exit(main())
== end
[rc=0]
## C5 unknown path

## block 30 (C5 unknown)
unknown
== n8n_start.sh
+die() { echo "refused: $1" >&2; exit 2; }
== n8n_kill.py
+    return 3  # unreadable process
+    print("confirmed gone")
+sys.exit(main())
== end
[rc=0]

## block 31 (C6 unknown)
ACCEPT
---- the n8n_kill.py part, read it:
== n8n_kill.py
+    return 3  # unreadable process
+    print("confirmed gone")
+sys.exit(main())
== end
[rc=0]
## C5 W3 missing

## block 30 (C5 W3 missing)
STOP C5: the old commit f419fd2 is neither in /tmp/v10t/hb/_local/scratch/wt/nlite-fix5 nor in the round-3 worktree /tmp/v10t/nonexist. Next: check W3N and OLD against line 3 of the plan; tell the builder.
[rc=1]
## C5 old commit nowhere

## block 30 (C5 OLD nowhere)
STOP C5: the old commit 1234567 is neither in /tmp/v10t/hb/_local/scratch/wt/nlite-fix5 nor in the round-3 worktree /tmp/v10t/hb/_local/scratch/wt/nlite-fix3. Next: check W3N and OLD against line 3 of the plan; tell the builder.
[rc=1]

## block 31 (C6 known)
ACCEPT
---- the n8n_kill.py part, read it:
== n8n_kill.py
+    return 3  # unreadable process
+    print("confirmed gone")
+sys.exit(main())
== end
[rc=0]
proof-c6: 5861a9726cc48d873367878b2e9584d9b1c3189d
## C6 acc5 STOP case: out file with bad exit
STOP (other exit text: +    sys.exit(9)|)
## C7 with marker 2 left

## block 32 (C7)
counts 0 1 2 1 (must be 0 0 2 1); CR=0 (0); first 3 bytes in hex=232057 (BOM if efbbbf); distinct 40-character shas: 1 (1, and equal to PIN)
STOP C7: 1 lines still hold a LEAD-FILL marker. Next: answer it (B1, A9, C2, C2b, C4); list: left
[rc=1]
(end of list; CR count in PF: 0, must be 0)

## block 32 (C7 after accept 2)
counts 0 0 2 1 (must be 0 0 2 1); CR=0 (0); first 3 bytes in hex=232057 (BOM if efbbbf); distinct 40-character shas: 1 (1, and equal to PIN)
ok C7
[rc=0]
## C7 negative: CR, BOM, extra sha
counts 0 0 2 1 (must be 0 0 2 1); CR=1 (0); first 3 bytes in hex=232057 (BOM if efbbbf); distinct 40-character shas: 1 (1, and equal to PIN)
STOP C7: PF holds 1 carriage returns. Next: close the editor, run: sed -i 's/\r$//' "$PF" , then C7 again.
counts 0 0 2 1 (must be 0 0 2 1); CR=0 (0); first 3 bytes in hex=efbbbf (BOM if efbbbf); distinct 40-character shas: 1 (1, and equal to PIN)
STOP C7: PF starts with a byte-order mark. Next: close the editor, run: sed -i '1s/^\xEF\xBB\xBF//' "$PF" , then C7 again.
counts 0 0 2 1 (must be 0 0 2 1); CR=0 (0); first 3 bytes in hex=232057 (BOM if efbbbf); distinct 40-character shas: 2 (1, and equal to PIN)
STOP C7: the 40-character shas in PF are [0123456789abcdef0123456789abcdef01234567,5861a9726cc48d873367878b2e9584d9b1c3189d] and PIN is [5861a9726cc48d873367878b2e9584d9b1c3189d]; exactly one sha, equal to PIN, is allowed. Next: edit the odd place in PF to PIN, or fix PIN; then C7 again.
counts 0 0 1 1 (must be 0 0 2 1); CR=0 (0); first 3 bytes in hex=232057 (BOM if efbbbf); distinct 40-character shas: 1 (1, and equal to PIN)
STOP C7: HEAD_PIN lines are 1, must be 2: PF is damaged or is not the patched plan. Next: tell the builder.

## block 32 (C7 restored)
counts 0 0 2 1 (must be 0 0 2 1); CR=0 (0); first 3 bytes in hex=232057 (BOM if efbbbf); distinct 40-character shas: 1 (1, and equal to PIN)
ok C7
[rc=0]

## block 33 (C8)
2:take/nlite-int-r5
2:nlite-fix5
2:take/nlite-int-r5
2:nlite-fix5
2:take/nlite-int-r5
3:nlite-fix5
3:nlite-fix5
3:nlite-fix5
3:nlite-fix5
3:nlite-fix5
77:nlite-fix5
77:take/nlite-int-r5
136:take/nlite-int-r5
136:nlite-fix5
251:take/nlite-int-r5
251:nlite-fix5
512:nlite-fix5
534:nlite-fix5
534:take/nlite-int-r5
582:nlite-fix5
582:take/nlite-int-r5
585:nlite-fix5
585:take/nlite-int-r5
587:nlite-fix5
[rc=0]
STOP C8: BR is empty or nothing was found. Next: do C2 (BR and WTN), then C8 again.

## block 34 (C8b (stand-in gone file from WSL-4))
dash syntax ok
P-4b files ok
ok C8b: stand-in gone for the current control file
[rc=0]

## block 33 (C8 with BR set)
[rc=0]
(grep lines: 24)

## block 34 (C8b)
dash syntax ok
P-4b files ok
ok C8b: stand-in gone for the current control file
[rc=0]
## C9 variants (each in a subshell, proof file saved and restored)
STOP C9: PIN is empty or not a commit of /tmp/v10t/hb/_local/scratch/wt/nlite-fix5. Next: C2.
STOP C9: C6 has not printed ACCEPT for this PIN. Next: do C6.
STOP C9: the stand-in is not proven gone for the current control file. Next: run WSL-4 (C2b step 4).
STOP C9: C7 is not clean. Next: run C7.
STOP C9: the last runner line is not 'P-3a done ...'. Next: C3b; wait for the runner's message.
STOP C9: PIN is not the tip of branch take/nlite-int-r5. Next: ask the builder for the final head; do C2 again.
## C9 success path

## block 35 (C9 release)
P-3a done 2026-11-16T12:00Z
LEAD-GO RE-PIN 2026-11-16T11:53Z pin=5861a9726cc48d873367878b2e9584d9b1c3189d plan=2776582ba6f44c55
[rc=0]
## C9 second time (must refuse: a release line exists)

## block 35 (C9 second)
STOP C9: a LEAD-GO RE-PIN line is already there. Next: tell the builder if you did not write it; if you did, the run may be released already: read the last lines of PROGRESS.md.
[rc=0]
4:LEAD-GO RE-PIN 2026-11-16T11:53Z pin=5861a9726cc48d873367878b2e9584d9b1c3189d plan=2776582ba6f44c55
P-3a done 2026-11-16T12:00Z
LEAD-GO RE-PIN 2026-11-16T11:53Z pin=5861a9726cc48d873367878b2e9584d9b1c3189d plan=2776582ba6f44c55
## D1

## block 36 (PID=4242) D1 ok
NEED-LEAD R2 pid=4242 x
LEAD-YES R2 pid=4242 2026-11-16T11:53Z
[rc=0]

## block 36 (PID=4242) D1 second time
STOP D1: a LEAD-YES line for pid 4242 is already there. Next: tell the builder.
[rc=0]

## block 36 (PID=999) D1 pid without a NEED line
STOP D1: no NEED-LEAD R2 line for pid 999 in PROGRESS.md. Next: check the pid with the runner.
[rc=0]

## block 36 (PID=abc) D1 bad
STOP D1: PID must be digits. Next: write the pid of the NEED-LEAD line.
[rc=0]

## block 36 (PID=777) D1 after kill exit=3
STOP D1: a kill exit=3 line exists: no R2 is allowed after it, ever. Next: write nothing, tell the builder; the plan (S13, 13.4 and 13.5) goes on by itself.
[rc=0]
1
## D2

## block 37 (D2(1))
== P-4b
P-4b-HIT pid=1
exit=0
[rc=0]

## block 38 (HITPID=1) D2(2) pid 1
/process_api --firecracker-init --addr 0.0.0.0:2024 --max-ws-buffer-size 32768 --block-local-connections --log-vsock-port 5002 --control-vsock-port 5001 --listen-vsock-port 2024 --tcp-readiness-only 
[rc=0]

## block 38 (HITPID=abc) D2(2) bad
STOP D2: HITPID must be digits. Next: write the pid of one P-4b-HIT line.
[rc=0]

## block 39 (D2(2b))
NOTE lead stand-in pid=15674 2026-11-16T11:53Z
[rc=0]

## block 40 (D2 check)
nothing alive
[rc=0]

## block 41 (D2 delete DEL=no)
STOP D2: DEL is not yes. Next: nothing deleted.
[rc=0]
## D2 delete with DEL=yes while a fake process is alive (must refuse)
STOP D2: something of the run is alive; nothing deleted. Next: run D2-check, ask the builder in the channel.
/tmp/v10t/home/hadavin-smoke
## D2 delete DEL=yes, nothing alive
deleted
ls: cannot access '/tmp/v10t/home/hadavin-smoke': No such file or directory
```

## 2.3 Full walk of the blocks A1 to D2, CHAIN=3 (raw)
```
## block 01 (variables, CHAIN=3)
STOP VARS form: HB is '/tmp/v10t/hb', not in Git Bash form /c/Users/... Next: write it in that form in section 1.
STOP VARS form: CH is '/tmp/v10t/ch', not in Git Bash form /c/Users/... Next: write it in that form in section 1.
PF=/tmp/v10t/hb/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md
EV=/tmp/v10t/hb/egm/duplicate-proof-lead-desk/wp6/evidence-2
PASTES=/tmp/v10t/hb/_local/scratch/wp6-smoke/pastes
[rc=0]

## block 02 (step)
ok A1: made /tmp/v10t/hb/_local/scratch/lead-plan-work
[rc=0]

## block 03 (step)
ok plan-v5-fixes.patch no CR
ok plan-v5-repin-v6.patch no CR
ok plan-v5-gate-rows-v3.patch no CR
ok apply-v10-after-chain.py no CR
ok plan-v10-real-v5-edits.md no CR
ok plan-v10-corrections-after-chain.md no CR
ok acc5.sh no CR
ok LEAD-FILL-list-v5.md no CR
ok plan-v5-fixes.patch checksum
ok plan-v5-repin-v6.patch checksum
ok plan-v5-gate-rows-v3.patch checksum
ok original checksum
ok original no CR
[rc=0]

## block 04 (step)
ok A3
[rc=0]

## block 05 (step)
ok A4
[rc=0]

## block 06 (step)
ok A5b
[rc=0]

## block 07 (step)
CHAIN=3: chain step 4 skipped
[rc=0]

## block 08 (step)
plan-wp6-resmoke-v5.md
ok A5c
[rc=0]

## block 09 (step)
ok A6 counts 24 10 2 1
ok A6 plan checksum for CHAIN=3 (515cf4704ebba5bd)
[rc=0]

## block 10 (step)
2:LEAD-FILL 7
3:LEAD-FILL 5
3:LEAD-FILL 6
3:LEAD-FILL 9
3:LEAD-FILL 7
4:LEAD-FILL 8
4:LEAD-FILL 3
125:LEAD-FILL 4
258:LEAD-FILL 1
258:LEAD-FILL 1b
258:LEAD-FILL 2
258:LEAD-FILL 1b
275:LEAD-FILL 6
466:LEAD-FILL 4
467:LEAD-FILL 4
620:LEAD-FILL 7
621:LEAD-FILL 1
ok A7 marker lines are 2,3,4,125,258,275,466,467,620,621
[rc=0]

## block 04 (A3 re-run)
ok A3 (already done: the plan in the work folder is further along, at a later chain step; nothing changed. A6 checks it against your CHAIN)
[rc=0]

## block 05 (A4 re-run)
ok A4 (already done: the plan in the work folder is further along, at a later chain step; nothing changed. A6 checks it against your CHAIN)
[rc=0]

## block 06 (A5b re-run)
ok A5b (already applied: the plan in the work folder is the result of this step; nothing changed)
[rc=0]

## block 07 (A5b4 re-run)
CHAIN=3: chain step 4 skipped
[rc=0]

## block 11 (A8)
ok A8 copied
[rc=0]

## block 11 (A8 re-run)
ok A8 (PF already equals the untouched patched plan; nothing changed): go on to A9
[rc=0]

## block 12 (A9 check (expect not 1/2/..))
windows form: C:\Users\USER\Downloads\Hadavin\egm\duplicate-proof-lead-desk\wp6\plan-wp6-resmoke-v5.md
mixed form (drive letter, forward slashes; the form the plan writes after PF=): C:/Users/USER/Downloads/Hadavin/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md
string (1) found: 1 (must be 1)
strings (2) and (3) found: 2 (must be 2)
evidence folder named in plan: 1 (must be 1 or more)
pastes folder named in plan: 1 (must be 1 or more)
[rc=0]

## block 12 (A9 check after line 3 fix)
windows form: C:\Users\USER\Downloads\Hadavin\egm\duplicate-proof-lead-desk\wp6\plan-wp6-resmoke-v5.md
mixed form (drive letter, forward slashes; the form the plan writes after PF=): C:/Users/USER/Downloads/Hadavin/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md
string (1) found: 1 (must be 1)
strings (2) and (3) found: 2 (must be 2)
evidence folder named in plan: 1 (must be 1 or more)
pastes folder named in plan: 1 (must be 1 or more)
[rc=0]

## block 13 (A9 flip (PF_CONFIRMED=no))
STOP A9: not confirmed (PF_CONFIRMED), no drive letter, or the counts are not 1 and 2: nothing changed. Next: fix line 3 of PF or PF_CONFIRMED, then run this block again.
[rc=0]

## block 13 (A9 flip yes)
ok A9: marker 9 flipped; left:
(end of list)
[rc=0]

## block 14 (B1 accept 3 4 8)
2:LEAD-FILL 7
3:LEAD-FILL 5
3:LEAD-FILL 6
3:LEAD-FILL 7
258:LEAD-FILL 1
258:LEAD-FILL 1b
258:LEAD-FILL 2
258:LEAD-FILL 1b
275:LEAD-FILL 6
620:LEAD-FILL 7
621:LEAD-FILL 1
(end of list; CR count in PF: 0, must be 0)
[rc=0]
accept 2:
STOP B1: question 2 is an open ruling (L1). Next: get the ruling, write L1_RULED=yes in section 1 (see the row of question 2 in LEAD-FILL-list-v5.md). Nothing changed.
accept 5:
STOP B1: question 5 is answered only by its own block (5 and 7 by C2, 9 by A9). Next: do that block. Nothing changed.
accept 1:
STOP C2b: question 1 is answered only when the check C2c prints 'P-4b files ok'. Next: run C2c and fix what it says. Nothing changed.
## C1 rows with PIN empty

## block 15 (C1)
head=c3f9cbc82b9f0443e4e83ea836715fb456303aa1 seven=c3f9cbc branch=take/nlite-int-r5
PIN empty: first run, read only (nothing changed)
[rc=0]

## block 16 (C2)
ok C2
3:LEAD-FILL 6
258:LEAD-FILL 1
258:LEAD-FILL 1b
258:LEAD-FILL 2
258:LEAD-FILL 1b
275:LEAD-FILL 6
621:LEAD-FILL 1
(end of list; CR count in PF: 0, must be 0)
left placeholders (sha/branch must be 0): 0; table rows still open: 20 (must be 20 until C4)
[rc=0]

## block 16 (C2 re-run)
ok C2
3:LEAD-FILL 6
258:LEAD-FILL 1
258:LEAD-FILL 1b
258:LEAD-FILL 2
258:LEAD-FILL 1b
275:LEAD-FILL 6
621:LEAD-FILL 1
(end of list; CR count in PF: 0, must be 0)
left placeholders (sha/branch must be 0): 0; table rows still open: 20 (must be 20 until C4)
[rc=0]

## block 17 (C2b(1))
11:    return 3  # unreadable process
[rc=0]

## block 18 (C2b(2))
syntax ok
CR count: 0 (must be 0)
non-ASCII bytes: 0 (must be 0)
word scan:
(end: nothing above is right)
[rc=0]

## block 18 (C2b(2) re-run (must refuse))
STOP C2b: /tmp/v10t/hb/_local/scratch/wp6-smoke/pastes/P-4b.sh already exists (a file you may have changed). Next: keep it and go to step (3); or, to start from the proposal again: mv "/tmp/v10t/hb/_local/scratch/wp6-smoke/pastes/P-4b.sh" "/tmp/v10t/hb/_local/scratch/wp6-smoke/pastes/P-4b.sh.old" (i
[rc=0]
## wsl form

## block 19 (HBW)
HBW='/mnt/tmp/v10t/hb'
[rc=0]
## C2c before control exists

## block 25 (C2c)
STOP C2c: missing or empty: /tmp/v10t/hb/_local/scratch/wp6-smoke/pastes/P-4b.control.txt. Next: make it (C2b).
[rc=1]

######## PART 2: WSL blocks as uid 65534
## WSL block 20
/tmp/v10t/hb/_local/scratch/wp6-smoke/pastes
user: nobody uid=65534 (must not be 0)
dash -n ok
[rc=0]
## WSL block 21
Could not find platform dependent libraries <exec_prefix>
stand-in pid=18627
me=65534
65534 /proc/18627
0 /proc/18627/environ
status-uid=65534
/tmp/v10t/blocks/21.sh: line 1: /proc/18627/environ: Permission denied
[rc=0]
## WSL block 22
exit=0
P-4b.sh sha256 21d00f1c69cbc5bc5ef29772e351ea972c5754d556bd77e292615adbc2d3497c
P-4b-HIT pid=18627
[rc=0]
## WSL block 24
gone
[rc=0]
## WSL-4 alone, stand-in alive in another window (expect ALIVE and STOP)
Could not find platform dependent libraries <exec_prefix>
ALIVE pid=19259
STOP C2b: a stand-in is still alive. Next: wait up to 10 minutes (it ends by itself), or, if it is yours, end it by its exact pid typed by you; run WSL-4 again.
[rc=0]
ls: cannot access 'standin-gone.txt': No such file or directory
## WSL-4 after it ended by itself
gone
gone control=770a429d04cafb21
## WSL-1 as root (must refuse)
user: root uid=0 (must not be 0)
STOP C2b: wrong folder, root user, or dash -n failed. Next: fix it (HBW line, user, P-4b.sh), run WSL-1 again.
total 12
-rw-r--r-- 1 nobody nogroup  99 Nov 16 11:53 P-4b.control.txt
-rw-rw-rw- 1 root   root    719 Nov 16 11:53 P-4b.sh
-rw-r--r-- 1 nobody nogroup  30 Nov 16 11:53 standin-gone.txt
P-4b.sh sha256 21d00f1c69cbc5bc5ef29772e351ea972c5754d556bd77e292615adbc2d3497c
P-4b-HIT pid=18627

## block 23 (SP=<pid>)
/tmp/v10t/b23.sh: line 1: syntax error near unexpected token `;'
/tmp/v10t/b23.sh: line 1: `SP=<pid>; F="$EV/PROGRESS.md"; case "$SP" in ''|*[!0-9]*) echo "STOP C2b: SP must be digits. Next: write the pid printed by WSL-2 and run again.";; *) if evok; then if [ -s "$F" ] && [ -n "$(tail -c 1 "$F")" ]; then printf '\n' >> "$F"; fi; printf 'NOTE lead stand-in pid=%
[rc=2]

## block 23 (SP=)
STOP C2b: SP must be digits. Next: write the pid printed by WSL-2 and run again.
[rc=0]

## block 23 (SP=abc)
STOP C2b: SP must be digits. Next: write the pid printed by WSL-2 and run again.
[rc=0]

## block 23 (SP=18627)
NOTE lead stand-in pid=18627 2026-11-16T11:53Z
[rc=0]

## block 23 (SP=18627)
NOTE lead stand-in pid=18627 2026-11-16T11:53Z
NOTE lead stand-in pid=18627 2026-11-16T11:53Z
[rc=0]
NOTE lead stand-in pid=18627 2026-11-16T11:53Z
NOTE lead stand-in pid=18627 2026-11-16T11:53Z

## block 25 (C2c (expect P-4b files ok))
dash syntax ok
P-4b files ok
[rc=0]
## C2c with dash missing
NOTE C2c: dash is not installed in Git Bash, so dash -n was NOT run here (this is not a STOP). It is run in WSL in C2b step (3), block WSL-1.
P-4b files ok
## C2c negative: CR in P-4b.sh
STOP C2c: CR in /tmp/v10t/hb/_local/scratch/wp6-smoke/pastes/P-4b.sh. Next: make the file again in WSL (C2b step 4).
STOP C2c: a byte that is not plain ASCII in /tmp/v10t/hb/_local/scratch/wp6-smoke/pastes/P-4b.sh. Next: make the file again (C2b).
## C2c negative: word kill
STOP C2c: the word kill or env.sh is in P-4b.sh. Next: remove it, make the control file again (C2b).
dash syntax ok
STOP C2c: the first line of the control file does not hold the checksum of P-4b.sh. Next: make the control file again (C2b step 4).
## C2c negative: edited P-4b.sh (control hash mismatch)
dash syntax ok
STOP C2c: the first line of the control file does not hold the checksum of P-4b.sh. Next: make the control file again (C2b step 4).
## C2c negative: bad control line
dash syntax ok
STOP C2c: a control line has the wrong shape. Next: make the control file again (C2b step 4).
## C2c negative: non-ASCII
STOP C2c: a byte that is not plain ASCII in /tmp/v10t/hb/_local/scratch/wp6-smoke/pastes/P-4b.sh. Next: make the file again (C2b).
dash syntax ok
P-4b files ok
## accept 1 1b
258:LEAD-FILL 2
275:LEAD-FILL 6
(end of list; CR count in PF: 0, must be 0)

## block 26 (C3 brief)
STUDIO-PREAMBLE v1
You are working for Hadavin (solo AI studio, owner the owner). These rules bind you; the studio folder is <studio>/.

You are the RUNNER of the re-smoke plan. Read your steps only from this file: C:\Users\USER\Downloads\Hadavin\egm\duplicate-proof-lead-desk\wp6\plan-wp6-resmoke-v5.md (a different copy = STOP). Run plan step P-3a only (write the glue, the paste files and strings.txt with the Write tool; do NOT write
ok C3: brief saved in /tmp/v10t/hb/_local/scratch/lead-plan-work/runner-brief.txt (no placeholder to fill)
[rc=0]
STUDIO-PREAMBLE v1
You are the RUNNER of the re-smoke plan. Read your steps only from this file: C:\Users\USER\Downloads\Hadavin\egm\duplicate-proof-lead-desk\wp6\plan-wp6-resmoke-v5.md (a different copy = STOP). Run p
5
## C3 with bad BP
STOP C3: BP (/nonexistent) is not the studio preamble (first line STUDIO-PREAMBLE v1, containing EGM-GATE v1). Next: write BP in section 1 (file handover/BRIEF-PREAMBLE.md of the repository), set the variables.

## block 27 (C3b (no runner line yet))
runner lines in PROGRESS.md: 0 (must be 1 or more)
NOTE lead stand-in pid=18627 2026-11-16T11:53Z
NOTE lead stand-in pid=18627 2026-11-16T11:53Z
strings.txt exists
[rc=0]
## C9 now (no runner line) expect STOP

## block 35 (C9-early)
STOP C9: C7 is not clean. Next: run C7.
[rc=0]

## block 27 (C3b with runner line)
runner lines in PROGRESS.md: 1 (must be 1 or more)
NOTE lead stand-in pid=18627 2026-11-16T11:53Z
NOTE lead stand-in pid=18627 2026-11-16T11:53Z
P-3a done 2026-11-16T12:00Z
strings.txt exists
[rc=0]
## C4 rows

## block 28 (C4 rows)
head=c3f9cbc82b9f0443e4e83ea836715fb456303aa1 seven=c3f9cbc branch=take/nlite-int-r5
S1 n8n_start.sh 2
S2 n8n_start.sh 4
S3 n8n_start.sh 6
S4 n8n_start.sh 8
S5 n8n_start.sh 10
S6 n8n_start.sh 12
S7 n8n_start.sh 14
S8 n8n_start.sh 16
K1 n8n_kill.py 2
K2 n8n_kill.py 4
K3 n8n_kill.py 6
K4 n8n_kill.py 8
D1 n8n_drive.py 2
D2 n8n_drive.py 4
D3 n8n_drive.py 6
D4 n8n_drive.py 8
D5 n8n_drive.py 10
D6 n8n_drive.py 12
H1 run_real_check_n8n.py 2
H2 real-run-n8n.env.example 2
[rc=0]
head=c3f9cbc82b9f0443e4e83ea836715fb456303aa1 seven=c3f9cbc branch=take/nlite-int-r5
S1 n8n_start.sh 2
S2 n8n_start.sh 4

## block 29 (C4 fill)
rows filled by this run: 20 (20 the first time; 0 on a repeat is fine if open is 0)
rows still open: 0 (must be 0)
CR count: 0
ok C4: now run: accept 6
[rc=0]
258:LEAD-FILL 2
(end of list; CR count in PF: 0, must be 0)

## block 30 (C5 known)
known
== n8n_start.sh
+die() { echo "refused: $1" >&2; exit 2; }
== n8n_kill.py
+    return 3  # unreadable process
+    print("confirmed gone")
+sys.exit(main())
== end
[rc=0]
## C5 unknown path

## block 30 (C5 unknown)
unknown
== n8n_start.sh
+die() { echo "refused: $1" >&2; exit 2; }
== n8n_kill.py
+    return 3  # unreadable process
+    print("confirmed gone")
+sys.exit(main())
== end
[rc=0]

## block 31 (C6 unknown)
ACCEPT
---- the n8n_kill.py part, read it:
== n8n_kill.py
+    return 3  # unreadable process
+    print("confirmed gone")
+sys.exit(main())
== end
[rc=0]
## C5 W3 missing

## block 30 (C5 W3 missing)
STOP C5: the old commit fc2e9e9 is neither in /tmp/v10t/hb/_local/scratch/wt/nlite-fix5 nor in the round-3 worktree /tmp/v10t/nonexist. Next: check W3N and OLD against line 3 of the plan; tell the builder.
[rc=1]
## C5 old commit nowhere

## block 30 (C5 OLD nowhere)
STOP C5: the old commit 1234567 is neither in /tmp/v10t/hb/_local/scratch/wt/nlite-fix5 nor in the round-3 worktree /tmp/v10t/hb/_local/scratch/wt/nlite-fix3. Next: check W3N and OLD against line 3 of the plan; tell the builder.
[rc=1]

## block 31 (C6 known)
ACCEPT
---- the n8n_kill.py part, read it:
== n8n_kill.py
+    return 3  # unreadable process
+    print("confirmed gone")
+sys.exit(main())
== end
[rc=0]
proof-c6: c3f9cbc82b9f0443e4e83ea836715fb456303aa1
## C6 acc5 STOP case: out file with bad exit
STOP (other exit text: +    sys.exit(9)|)
## C7 with marker 2 left

## block 32 (C7)
counts 0 1 2 1 (must be 0 0 2 1); CR=0 (0); first 3 bytes in hex=232057 (BOM if efbbbf); distinct 40-character shas: 1 (1, and equal to PIN)
STOP C7: 1 lines still hold a LEAD-FILL marker. Next: answer it (B1, A9, C2, C2b, C4); list: left
[rc=1]
(end of list; CR count in PF: 0, must be 0)

## block 32 (C7 after accept 2)
counts 0 0 2 1 (must be 0 0 2 1); CR=0 (0); first 3 bytes in hex=232057 (BOM if efbbbf); distinct 40-character shas: 1 (1, and equal to PIN)
ok C7
[rc=0]
## C7 negative: CR, BOM, extra sha
counts 0 0 2 1 (must be 0 0 2 1); CR=1 (0); first 3 bytes in hex=232057 (BOM if efbbbf); distinct 40-character shas: 1 (1, and equal to PIN)
STOP C7: PF holds 1 carriage returns. Next: close the editor, run: sed -i 's/\r$//' "$PF" , then C7 again.
counts 0 0 2 1 (must be 0 0 2 1); CR=0 (0); first 3 bytes in hex=efbbbf (BOM if efbbbf); distinct 40-character shas: 1 (1, and equal to PIN)
STOP C7: PF starts with a byte-order mark. Next: close the editor, run: sed -i '1s/^\xEF\xBB\xBF//' "$PF" , then C7 again.
counts 0 0 2 1 (must be 0 0 2 1); CR=0 (0); first 3 bytes in hex=232057 (BOM if efbbbf); distinct 40-character shas: 2 (1, and equal to PIN)
STOP C7: the 40-character shas in PF are [0123456789abcdef0123456789abcdef01234567,c3f9cbc82b9f0443e4e83ea836715fb456303aa1] and PIN is [c3f9cbc82b9f0443e4e83ea836715fb456303aa1]; exactly one sha, equal to PIN, is allowed. Next: edit the odd place in PF to PIN, or fix PIN; then C7 again.
counts 0 0 1 1 (must be 0 0 2 1); CR=0 (0); first 3 bytes in hex=232057 (BOM if efbbbf); distinct 40-character shas: 1 (1, and equal to PIN)
STOP C7: HEAD_PIN lines are 1, must be 2: PF is damaged or is not the patched plan. Next: tell the builder.

## block 32 (C7 restored)
counts 0 0 2 1 (must be 0 0 2 1); CR=0 (0); first 3 bytes in hex=232057 (BOM if efbbbf); distinct 40-character shas: 1 (1, and equal to PIN)
ok C7
[rc=0]

## block 33 (C8)
2:take/nlite-int-r5
2:nlite-fix5
2:take/nlite-int-r5
2:nlite-fix5
2:take/nlite-int-r5
3:nlite-fix5
3:nlite-fix5
3:nlite-fix5
3:nlite-fix5
3:nlite-fix5
77:nlite-fix5
77:take/nlite-int-r5
136:take/nlite-int-r5
136:nlite-fix5
251:take/nlite-int-r5
251:nlite-fix5
547:nlite-fix5
569:nlite-fix5
569:take/nlite-int-r5
617:nlite-fix5
617:take/nlite-int-r5
620:nlite-fix5
620:take/nlite-int-r5
622:nlite-fix5
[rc=0]
STOP C8: BR is empty or nothing was found. Next: do C2 (BR and WTN), then C8 again.

## block 34 (C8b (stand-in gone file from WSL-4))
dash syntax ok
P-4b files ok
ok C8b: stand-in gone for the current control file
[rc=0]

## block 33 (C8 with BR set)
[rc=0]
(grep lines: 24)

## block 34 (C8b)
dash syntax ok
P-4b files ok
ok C8b: stand-in gone for the current control file
[rc=0]
## C9 variants (each in a subshell, proof file saved and restored)
STOP C9: PIN is empty or not a commit of /tmp/v10t/hb/_local/scratch/wt/nlite-fix5. Next: C2.
STOP C9: C6 has not printed ACCEPT for this PIN. Next: do C6.
STOP C9: the stand-in is not proven gone for the current control file. Next: run WSL-4 (C2b step 4).
STOP C9: C7 is not clean. Next: run C7.
STOP C9: the last runner line is not 'P-3a done ...'. Next: C3b; wait for the runner's message.
STOP C9: PIN is not the tip of branch take/nlite-int-r5. Next: ask the builder for the final head; do C2 again.
## C9 success path

## block 35 (C9 release)
P-3a done 2026-11-16T12:00Z
LEAD-GO RE-PIN 2026-11-16T11:53Z pin=c3f9cbc82b9f0443e4e83ea836715fb456303aa1 plan=7f03243d8189163d
[rc=0]
## C9 second time (must refuse: a release line exists)

## block 35 (C9 second)
STOP C9: a LEAD-GO RE-PIN line is already there. Next: tell the builder if you did not write it; if you did, the run may be released already: read the last lines of PROGRESS.md.
[rc=0]
4:LEAD-GO RE-PIN 2026-11-16T11:53Z pin=c3f9cbc82b9f0443e4e83ea836715fb456303aa1 plan=7f03243d8189163d
P-3a done 2026-11-16T12:00Z
LEAD-GO RE-PIN 2026-11-16T11:53Z pin=c3f9cbc82b9f0443e4e83ea836715fb456303aa1 plan=7f03243d8189163d
## D1

## block 36 (PID=4242) D1 ok
NEED-LEAD R2 pid=4242 x
LEAD-YES R2 pid=4242 2026-11-16T11:53Z
[rc=0]

## block 36 (PID=4242) D1 second time
STOP D1: a LEAD-YES line for pid 4242 is already there. Next: tell the builder.
[rc=0]

## block 36 (PID=999) D1 pid without a NEED line
STOP D1: no NEED-LEAD R2 line for pid 999 in PROGRESS.md. Next: check the pid with the runner.
[rc=0]

## block 36 (PID=abc) D1 bad
STOP D1: PID must be digits. Next: write the pid of the NEED-LEAD line.
[rc=0]

## block 36 (PID=777) D1 after kill exit=3
STOP D1: a kill exit=3 line exists: no R2 is allowed after it, ever. Next: write nothing, tell the builder; the plan (S13, 13.4 and 13.5) goes on by itself.
[rc=0]
1
## D2

## block 37 (D2(1))
== P-4b
P-4b-HIT pid=1
exit=0
[rc=0]

## block 38 (HITPID=1) D2(2) pid 1
/process_api --firecracker-init --addr 0.0.0.0:2024 --max-ws-buffer-size 32768 --block-local-connections --log-vsock-port 5002 --control-vsock-port 5001 --listen-vsock-port 2024 --tcp-readiness-only 
[rc=0]

## block 38 (HITPID=abc) D2(2) bad
STOP D2: HITPID must be digits. Next: write the pid of one P-4b-HIT line.
[rc=0]

## block 39 (D2(2b))
NOTE lead stand-in pid=18627 2026-11-16T11:53Z
[rc=0]

## block 40 (D2 check)
nothing alive
[rc=0]

## block 41 (D2 delete DEL=no)
STOP D2: DEL is not yes. Next: nothing deleted.
[rc=0]
## D2 delete with DEL=yes while a fake process is alive (must refuse)
STOP D2: something of the run is alive; nothing deleted. Next: run D2-check, ask the builder in the channel.
/tmp/v10t/home/hadavin-smoke
## D2 delete DEL=yes, nothing alive
deleted
ls: cannot access '/tmp/v10t/home/hadavin-smoke': No such file or directory
```

## 2.4 Full walk of the blocks A1 to D2, CHAIN=4 (raw)
```
## block 01 (variables, CHAIN=4)
STOP VARS form: HB is '/tmp/v10t/hb', not in Git Bash form /c/Users/... Next: write it in that form in section 1.
STOP VARS form: CH is '/tmp/v10t/ch', not in Git Bash form /c/Users/... Next: write it in that form in section 1.
PF=/tmp/v10t/hb/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md
EV=/tmp/v10t/hb/egm/duplicate-proof-lead-desk/wp6/evidence-2
PASTES=/tmp/v10t/hb/_local/scratch/wp6-smoke/pastes
[rc=0]

## block 02 (step)
ok A1: made /tmp/v10t/hb/_local/scratch/lead-plan-work
[rc=0]

## block 03 (step)
ok plan-v5-fixes.patch no CR
ok plan-v5-repin-v6.patch no CR
ok plan-v5-gate-rows-v3.patch no CR
ok apply-v10-after-chain.py no CR
ok plan-v10-real-v5-edits.md no CR
ok plan-v10-corrections-after-chain.md no CR
ok acc5.sh no CR
ok LEAD-FILL-list-v5.md no CR
ok plan-v5-fixes.patch checksum
ok plan-v5-repin-v6.patch checksum
ok plan-v5-gate-rows-v3.patch checksum
ok original checksum
ok original no CR
[rc=0]

## block 04 (step)
ok A3
[rc=0]

## block 05 (step)
ok A4
[rc=0]

## block 06 (step)
ok A5b
[rc=0]

## block 07 (step)
29 old edits; corrected or added: ['2', '4', '5', '18', '19', '20', '21', '29', '30']
failing []
written /tmp/v10t/hb/_local/scratch/lead-plan-work/real-v5-plan.md 28f92c5d1211207c 780 lines
ok A5b4
[rc=0]

## block 08 (step)
plan-wp6-resmoke-v5.md
plan-wp6-resmoke-v5.md.step3
ok A5c
[rc=0]

## block 09 (step)
ok A6 counts 24 10 2 1
ok A6 plan checksum for CHAIN=4 (28f92c5d1211207c)
[rc=0]

## block 10 (step)
2:LEAD-FILL 7
3:LEAD-FILL 5
3:LEAD-FILL 6
3:LEAD-FILL 9
3:LEAD-FILL 7
4:LEAD-FILL 8
4:LEAD-FILL 3
137:LEAD-FILL 4
270:LEAD-FILL 1
270:LEAD-FILL 1b
270:LEAD-FILL 2
270:LEAD-FILL 1b
287:LEAD-FILL 6
509:LEAD-FILL 4
510:LEAD-FILL 4
774:LEAD-FILL 7
775:LEAD-FILL 1
ok A7 marker lines are 2,3,4,137,270,287,509,510,774,775
[rc=0]

## block 04 (A3 re-run)
ok A3 (already done: the plan in the work folder is further along, at a later chain step; nothing changed. A6 checks it against your CHAIN)
[rc=0]

## block 05 (A4 re-run)
ok A4 (already done: the plan in the work folder is further along, at a later chain step; nothing changed. A6 checks it against your CHAIN)
[rc=0]

## block 06 (A5b re-run)
ok A5b (already done: the plan in the work folder is further along, at a later chain step; nothing changed. A6 checks it against your CHAIN)
[rc=0]

## block 07 (A5b4 re-run)
ok A5b4 (already applied: nothing changed)
[rc=0]

## block 11 (A8)
ok A8 copied
[rc=0]

## block 11 (A8 re-run)
ok A8 (PF already equals the untouched patched plan; nothing changed): go on to A9
[rc=0]

## block 12 (A9 check (expect not 1/2/..))
windows form: C:\Users\USER\Downloads\Hadavin\egm\duplicate-proof-lead-desk\wp6\plan-wp6-resmoke-v5.md
mixed form (drive letter, forward slashes; the form the plan writes after PF=): C:/Users/USER/Downloads/Hadavin/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md
string (1) found: 1 (must be 1)
strings (2) and (3) found: 2 (must be 2)
evidence folder named in plan: 1 (must be 1 or more)
pastes folder named in plan: 1 (must be 1 or more)
[rc=0]

## block 12 (A9 check after line 3 fix)
windows form: C:\Users\USER\Downloads\Hadavin\egm\duplicate-proof-lead-desk\wp6\plan-wp6-resmoke-v5.md
mixed form (drive letter, forward slashes; the form the plan writes after PF=): C:/Users/USER/Downloads/Hadavin/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md
string (1) found: 1 (must be 1)
strings (2) and (3) found: 2 (must be 2)
evidence folder named in plan: 1 (must be 1 or more)
pastes folder named in plan: 1 (must be 1 or more)
[rc=0]

## block 13 (A9 flip (PF_CONFIRMED=no))
STOP A9: not confirmed (PF_CONFIRMED), no drive letter, or the counts are not 1 and 2: nothing changed. Next: fix line 3 of PF or PF_CONFIRMED, then run this block again.
[rc=0]

## block 13 (A9 flip yes)
ok A9: marker 9 flipped; left:
(end of list)
[rc=0]

## block 14 (B1 accept 3 4 8)
2:LEAD-FILL 7
3:LEAD-FILL 5
3:LEAD-FILL 6
3:LEAD-FILL 7
270:LEAD-FILL 1
270:LEAD-FILL 1b
270:LEAD-FILL 2
270:LEAD-FILL 1b
287:LEAD-FILL 6
774:LEAD-FILL 7
775:LEAD-FILL 1
(end of list; CR count in PF: 0, must be 0)
[rc=0]
accept 2:
STOP B1: question 2 is an open ruling (L1). Next: get the ruling, write L1_RULED=yes in section 1 (see the row of question 2 in LEAD-FILL-list-v5.md). Nothing changed.
accept 5:
STOP B1: question 5 is answered only by its own block (5 and 7 by C2, 9 by A9). Next: do that block. Nothing changed.
accept 1:
STOP C2b: question 1 is answered only when the check C2c prints 'P-4b files ok'. Next: run C2c and fix what it says. Nothing changed.
## C1 rows with PIN empty

## block 15 (C1)
head=31c1a2cb1566fb9fd8b0b7765404e6fa7997b0b2 seven=31c1a2c branch=take/nlite-int-r5
PIN empty: first run, read only (nothing changed)
[rc=0]

## block 16 (C2)
ok C2
3:LEAD-FILL 6
270:LEAD-FILL 1
270:LEAD-FILL 1b
270:LEAD-FILL 2
270:LEAD-FILL 1b
287:LEAD-FILL 6
775:LEAD-FILL 1
(end of list; CR count in PF: 0, must be 0)
left placeholders (sha/branch must be 0): 0; table rows still open: 20 (must be 20 until C4)
[rc=0]

## block 16 (C2 re-run)
ok C2
3:LEAD-FILL 6
270:LEAD-FILL 1
270:LEAD-FILL 1b
270:LEAD-FILL 2
270:LEAD-FILL 1b
287:LEAD-FILL 6
775:LEAD-FILL 1
(end of list; CR count in PF: 0, must be 0)
left placeholders (sha/branch must be 0): 0; table rows still open: 20 (must be 20 until C4)
[rc=0]

## block 17 (C2b(1))
11:    return 3  # unreadable process
[rc=0]

## block 18 (C2b(2))
syntax ok
CR count: 0 (must be 0)
non-ASCII bytes: 0 (must be 0)
word scan:
(end: nothing above is right)
[rc=0]

## block 18 (C2b(2) re-run (must refuse))
STOP C2b: /tmp/v10t/hb/_local/scratch/wp6-smoke/pastes/P-4b.sh already exists (a file you may have changed). Next: keep it and go to step (3); or, to start from the proposal again: mv "/tmp/v10t/hb/_local/scratch/wp6-smoke/pastes/P-4b.sh" "/tmp/v10t/hb/_local/scratch/wp6-smoke/pastes/P-4b.sh.old" (i
[rc=0]
## wsl form

## block 19 (HBW)
HBW='/mnt/tmp/v10t/hb'
[rc=0]
## C2c before control exists

## block 25 (C2c)
STOP C2c: missing or empty: /tmp/v10t/hb/_local/scratch/wp6-smoke/pastes/P-4b.control.txt. Next: make it (C2b).
[rc=1]

######## PART 2: WSL blocks as uid 65534
## WSL block 20
/tmp/v10t/hb/_local/scratch/wp6-smoke/pastes
user: nobody uid=65534 (must not be 0)
dash -n ok
[rc=0]
## WSL block 21
Could not find platform dependent libraries <exec_prefix>
stand-in pid=21868
me=65534
65534 /proc/21868
0 /proc/21868/environ
status-uid=65534
/tmp/v10t/blocks/21.sh: line 1: /proc/21868/environ: Permission denied
[rc=0]
## WSL block 22
exit=0
P-4b.sh sha256 21d00f1c69cbc5bc5ef29772e351ea972c5754d556bd77e292615adbc2d3497c
P-4b-HIT pid=21868
[rc=0]
## WSL block 24
gone
[rc=0]
## WSL-4 alone, stand-in alive in another window (expect ALIVE and STOP)
Could not find platform dependent libraries <exec_prefix>
ALIVE pid=22313
STOP C2b: a stand-in is still alive. Next: wait up to 10 minutes (it ends by itself), or, if it is yours, end it by its exact pid typed by you; run WSL-4 again.
[rc=0]
ls: cannot access 'standin-gone.txt': No such file or directory
## WSL-4 after it ended by itself
gone
gone control=d50ed03227c3650e
## WSL-1 as root (must refuse)
user: root uid=0 (must not be 0)
STOP C2b: wrong folder, root user, or dash -n failed. Next: fix it (HBW line, user, P-4b.sh), run WSL-1 again.
total 12
-rw-r--r-- 1 nobody nogroup  99 Nov 16 11:53 P-4b.control.txt
-rw-rw-rw- 1 root   root    719 Nov 16 11:53 P-4b.sh
-rw-r--r-- 1 nobody nogroup  30 Nov 16 11:53 standin-gone.txt
P-4b.sh sha256 21d00f1c69cbc5bc5ef29772e351ea972c5754d556bd77e292615adbc2d3497c
P-4b-HIT pid=21868

## block 23 (SP=<pid>)
/tmp/v10t/b23.sh: line 1: syntax error near unexpected token `;'
/tmp/v10t/b23.sh: line 1: `SP=<pid>; F="$EV/PROGRESS.md"; case "$SP" in ''|*[!0-9]*) echo "STOP C2b: SP must be digits. Next: write the pid printed by WSL-2 and run again.";; *) if evok; then if [ -s "$F" ] && [ -n "$(tail -c 1 "$F")" ]; then printf '\n' >> "$F"; fi; printf 'NOTE lead stand-in pid=%
[rc=2]

## block 23 (SP=)
STOP C2b: SP must be digits. Next: write the pid printed by WSL-2 and run again.
[rc=0]

## block 23 (SP=abc)
STOP C2b: SP must be digits. Next: write the pid printed by WSL-2 and run again.
[rc=0]

## block 23 (SP=21868)
NOTE lead stand-in pid=21868 2026-11-16T11:53Z
[rc=0]

## block 23 (SP=21868)
NOTE lead stand-in pid=21868 2026-11-16T11:53Z
NOTE lead stand-in pid=21868 2026-11-16T11:53Z
[rc=0]
NOTE lead stand-in pid=21868 2026-11-16T11:53Z
NOTE lead stand-in pid=21868 2026-11-16T11:53Z

## block 25 (C2c (expect P-4b files ok))
dash syntax ok
P-4b files ok
[rc=0]
## C2c with dash missing
NOTE C2c: dash is not installed in Git Bash, so dash -n was NOT run here (this is not a STOP). It is run in WSL in C2b step (3), block WSL-1.
P-4b files ok
## C2c negative: CR in P-4b.sh
STOP C2c: CR in /tmp/v10t/hb/_local/scratch/wp6-smoke/pastes/P-4b.sh. Next: make the file again in WSL (C2b step 4).
STOP C2c: a byte that is not plain ASCII in /tmp/v10t/hb/_local/scratch/wp6-smoke/pastes/P-4b.sh. Next: make the file again (C2b).
## C2c negative: word kill
STOP C2c: the word kill or env.sh is in P-4b.sh. Next: remove it, make the control file again (C2b).
dash syntax ok
STOP C2c: the first line of the control file does not hold the checksum of P-4b.sh. Next: make the control file again (C2b step 4).
## C2c negative: edited P-4b.sh (control hash mismatch)
dash syntax ok
STOP C2c: the first line of the control file does not hold the checksum of P-4b.sh. Next: make the control file again (C2b step 4).
## C2c negative: bad control line
dash syntax ok
STOP C2c: a control line has the wrong shape. Next: make the control file again (C2b step 4).
## C2c negative: non-ASCII
STOP C2c: a byte that is not plain ASCII in /tmp/v10t/hb/_local/scratch/wp6-smoke/pastes/P-4b.sh. Next: make the file again (C2b).
dash syntax ok
P-4b files ok
## accept 1 1b
270:LEAD-FILL 2
287:LEAD-FILL 6
(end of list; CR count in PF: 0, must be 0)

## block 26 (C3 brief)
STUDIO-PREAMBLE v1
You are working for Hadavin (solo AI studio, owner the owner). These rules bind you; the studio folder is <studio>/.

You are the RUNNER of the re-smoke plan. Read your steps only from this file: C:\Users\USER\Downloads\Hadavin\egm\duplicate-proof-lead-desk\wp6\plan-wp6-resmoke-v5.md (a different copy = STOP). Run plan step P-3a only (write the glue, the paste files and strings.txt with the Write tool; do NOT write
ok C3: brief saved in /tmp/v10t/hb/_local/scratch/lead-plan-work/runner-brief.txt (no placeholder to fill)
[rc=0]
STUDIO-PREAMBLE v1
You are the RUNNER of the re-smoke plan. Read your steps only from this file: C:\Users\USER\Downloads\Hadavin\egm\duplicate-proof-lead-desk\wp6\plan-wp6-resmoke-v5.md (a different copy = STOP). Run p
5
## C3 with bad BP
STOP C3: BP (/nonexistent) is not the studio preamble (first line STUDIO-PREAMBLE v1, containing EGM-GATE v1). Next: write BP in section 1 (file handover/BRIEF-PREAMBLE.md of the repository), set the variables.

## block 27 (C3b (no runner line yet))
runner lines in PROGRESS.md: 0 (must be 1 or more)
NOTE lead stand-in pid=21868 2026-11-16T11:53Z
NOTE lead stand-in pid=21868 2026-11-16T11:53Z
strings.txt exists
[rc=0]
## C9 now (no runner line) expect STOP

## block 35 (C9-early)
STOP C9: C7 is not clean. Next: run C7.
[rc=0]

## block 27 (C3b with runner line)
runner lines in PROGRESS.md: 1 (must be 1 or more)
NOTE lead stand-in pid=21868 2026-11-16T11:53Z
NOTE lead stand-in pid=21868 2026-11-16T11:53Z
P-3a done 2026-11-16T12:00Z
strings.txt exists
[rc=0]
## C4 rows

## block 28 (C4 rows)
head=31c1a2cb1566fb9fd8b0b7765404e6fa7997b0b2 seven=31c1a2c branch=take/nlite-int-r5
S1 n8n_start.sh 2
S2 n8n_start.sh 4
S3 n8n_start.sh 6
S4 n8n_start.sh 8
S5 n8n_start.sh 10
S6 n8n_start.sh 12
S7 n8n_start.sh 14
S8 n8n_start.sh 16
K1 n8n_kill.py 2
K2 n8n_kill.py 4
K3 n8n_kill.py 6
K4 n8n_kill.py 8
D1 n8n_drive.py 2
D2 n8n_drive.py 4
D3 n8n_drive.py 6
D4 n8n_drive.py 8
D5 n8n_drive.py 10
D6 n8n_drive.py 12
H1 run_real_check_n8n.py 2
H2 real-run-n8n.env.example 2
[rc=0]
head=31c1a2cb1566fb9fd8b0b7765404e6fa7997b0b2 seven=31c1a2c branch=take/nlite-int-r5
S1 n8n_start.sh 2
S2 n8n_start.sh 4

## block 29 (C4 fill)
rows filled by this run: 20 (20 the first time; 0 on a repeat is fine if open is 0)
rows still open: 0 (must be 0)
CR count: 0
ok C4: now run: accept 6
[rc=0]
270:LEAD-FILL 2
(end of list; CR count in PF: 0, must be 0)

## block 30 (C5 known)
known
== n8n_start.sh
+die() { echo "refused: $1" >&2; exit 2; }
== n8n_kill.py
+    return 3  # unreadable process
+    print("confirmed gone")
+sys.exit(main())
== end
[rc=0]
## C5 unknown path

## block 30 (C5 unknown)
unknown
== n8n_start.sh
+die() { echo "refused: $1" >&2; exit 2; }
== n8n_kill.py
+    return 3  # unreadable process
+    print("confirmed gone")
+sys.exit(main())
== end
[rc=0]

## block 31 (C6 unknown)
ACCEPT
---- the n8n_kill.py part, read it:
== n8n_kill.py
+    return 3  # unreadable process
+    print("confirmed gone")
+sys.exit(main())
== end
[rc=0]
## C5 W3 missing

## block 30 (C5 W3 missing)
STOP C5: the old commit aea4458 is neither in /tmp/v10t/hb/_local/scratch/wt/nlite-fix5 nor in the round-3 worktree /tmp/v10t/nonexist. Next: check W3N and OLD against line 3 of the plan; tell the builder.
[rc=1]
## C5 old commit nowhere

## block 30 (C5 OLD nowhere)
STOP C5: the old commit 1234567 is neither in /tmp/v10t/hb/_local/scratch/wt/nlite-fix5 nor in the round-3 worktree /tmp/v10t/hb/_local/scratch/wt/nlite-fix3. Next: check W3N and OLD against line 3 of the plan; tell the builder.
[rc=1]

## block 31 (C6 known)
ACCEPT
---- the n8n_kill.py part, read it:
== n8n_kill.py
+    return 3  # unreadable process
+    print("confirmed gone")
+sys.exit(main())
== end
[rc=0]
proof-c6: 31c1a2cb1566fb9fd8b0b7765404e6fa7997b0b2
## C6 acc5 STOP case: out file with bad exit
STOP (other exit text: +    sys.exit(9)|)
## C7 with marker 2 left

## block 32 (C7)
counts 0 1 2 1 (must be 0 0 2 1); CR=0 (0); first 3 bytes in hex=232057 (BOM if efbbbf); distinct 40-character shas: 1 (1, and equal to PIN)
STOP C7: 1 lines still hold a LEAD-FILL marker. Next: answer it (B1, A9, C2, C2b, C4); list: left
[rc=1]
(end of list; CR count in PF: 0, must be 0)

## block 32 (C7 after accept 2)
counts 0 0 2 1 (must be 0 0 2 1); CR=0 (0); first 3 bytes in hex=232057 (BOM if efbbbf); distinct 40-character shas: 1 (1, and equal to PIN)
ok C7
[rc=0]
## C7 negative: CR, BOM, extra sha
counts 0 0 2 1 (must be 0 0 2 1); CR=1 (0); first 3 bytes in hex=232057 (BOM if efbbbf); distinct 40-character shas: 1 (1, and equal to PIN)
STOP C7: PF holds 1 carriage returns. Next: close the editor, run: sed -i 's/\r$//' "$PF" , then C7 again.
counts 0 0 2 1 (must be 0 0 2 1); CR=0 (0); first 3 bytes in hex=efbbbf (BOM if efbbbf); distinct 40-character shas: 1 (1, and equal to PIN)
STOP C7: PF starts with a byte-order mark. Next: close the editor, run: sed -i '1s/^\xEF\xBB\xBF//' "$PF" , then C7 again.
counts 0 0 2 1 (must be 0 0 2 1); CR=0 (0); first 3 bytes in hex=232057 (BOM if efbbbf); distinct 40-character shas: 2 (1, and equal to PIN)
STOP C7: the 40-character shas in PF are [0123456789abcdef0123456789abcdef01234567,31c1a2cb1566fb9fd8b0b7765404e6fa7997b0b2] and PIN is [31c1a2cb1566fb9fd8b0b7765404e6fa7997b0b2]; exactly one sha, equal to PIN, is allowed. Next: edit the odd place in PF to PIN, or fix PIN; then C7 again.
counts 0 0 1 1 (must be 0 0 2 1); CR=0 (0); first 3 bytes in hex=232057 (BOM if efbbbf); distinct 40-character shas: 1 (1, and equal to PIN)
STOP C7: HEAD_PIN lines are 1, must be 2: PF is damaged or is not the patched plan. Next: tell the builder.

## block 32 (C7 restored)
counts 0 0 2 1 (must be 0 0 2 1); CR=0 (0); first 3 bytes in hex=232057 (BOM if efbbbf); distinct 40-character shas: 1 (1, and equal to PIN)
ok C7
[rc=0]

## block 33 (C8)
2:take/nlite-int-r5
2:nlite-fix5
2:take/nlite-int-r5
2:nlite-fix5
2:take/nlite-int-r5
3:nlite-fix5
3:nlite-fix5
3:nlite-fix5
3:nlite-fix5
3:nlite-fix5
89:nlite-fix5
89:take/nlite-int-r5
148:take/nlite-int-r5
148:nlite-fix5
263:take/nlite-int-r5
263:nlite-fix5
592:nlite-fix5
723:nlite-fix5
723:take/nlite-int-r5
771:nlite-fix5
771:take/nlite-int-r5
774:nlite-fix5
774:take/nlite-int-r5
776:nlite-fix5
[rc=0]
STOP C8: BR is empty or nothing was found. Next: do C2 (BR and WTN), then C8 again.

## block 34 (C8b (stand-in gone file from WSL-4))
dash syntax ok
P-4b files ok
ok C8b: stand-in gone for the current control file
[rc=0]

## block 33 (C8 with BR set)
[rc=0]
(grep lines: 24)

## block 34 (C8b)
dash syntax ok
P-4b files ok
ok C8b: stand-in gone for the current control file
[rc=0]
## C9 variants (each in a subshell, proof file saved and restored)
STOP C9: PIN is empty or not a commit of /tmp/v10t/hb/_local/scratch/wt/nlite-fix5. Next: C2.
STOP C9: C6 has not printed ACCEPT for this PIN. Next: do C6.
STOP C9: the stand-in is not proven gone for the current control file. Next: run WSL-4 (C2b step 4).
STOP C9: C7 is not clean. Next: run C7.
STOP C9: the last runner line is not 'P-3a done ...'. Next: C3b; wait for the runner's message.
STOP C9: PIN is not the tip of branch take/nlite-int-r5. Next: ask the builder for the final head; do C2 again.
## C9 success path

## block 35 (C9 release)
P-3a done 2026-11-16T12:00Z
LEAD-GO RE-PIN 2026-11-16T11:53Z pin=31c1a2cb1566fb9fd8b0b7765404e6fa7997b0b2 plan=1d76dd3087154fa8
[rc=0]
## C9 second time (must refuse: a release line exists)

## block 35 (C9 second)
STOP C9: a LEAD-GO RE-PIN line is already there. Next: tell the builder if you did not write it; if you did, the run may be released already: read the last lines of PROGRESS.md.
[rc=0]
4:LEAD-GO RE-PIN 2026-11-16T11:53Z pin=31c1a2cb1566fb9fd8b0b7765404e6fa7997b0b2 plan=1d76dd3087154fa8
P-3a done 2026-11-16T12:00Z
LEAD-GO RE-PIN 2026-11-16T11:53Z pin=31c1a2cb1566fb9fd8b0b7765404e6fa7997b0b2 plan=1d76dd3087154fa8
## D1

## block 36 (PID=4242) D1 ok
NEED-LEAD R2 pid=4242 x
LEAD-YES R2 pid=4242 2026-11-16T11:53Z
[rc=0]

## block 36 (PID=4242) D1 second time
STOP D1: a LEAD-YES line for pid 4242 is already there. Next: tell the builder.
[rc=0]

## block 36 (PID=999) D1 pid without a NEED line
STOP D1: no NEED-LEAD R2 line for pid 999 in PROGRESS.md. Next: check the pid with the runner.
[rc=0]

## block 36 (PID=abc) D1 bad
STOP D1: PID must be digits. Next: write the pid of the NEED-LEAD line.
[rc=0]

## block 36 (PID=777) D1 after kill exit=3
STOP D1: a kill exit=3 line exists: no R2 is allowed after it, ever. Next: write nothing, tell the builder; the plan (S13, 13.4 and 13.5) goes on by itself.
[rc=0]
1
## D2

## block 37 (D2(1))
== P-4b
P-4b-HIT pid=1
exit=0
[rc=0]

## block 38 (HITPID=1) D2(2) pid 1
/process_api --firecracker-init --addr 0.0.0.0:2024 --max-ws-buffer-size 32768 --block-local-connections --log-vsock-port 5002 --control-vsock-port 5001 --listen-vsock-port 2024 --tcp-readiness-only 
[rc=0]

## block 38 (HITPID=abc) D2(2) bad
STOP D2: HITPID must be digits. Next: write the pid of one P-4b-HIT line.
[rc=0]

## block 39 (D2(2b))
NOTE lead stand-in pid=21868 2026-11-16T11:53Z
[rc=0]

## block 40 (D2 check)
nothing alive
[rc=0]

## block 41 (D2 delete DEL=no)
STOP D2: DEL is not yes. Next: nothing deleted.
[rc=0]
## D2 delete with DEL=yes while a fake process is alive (must refuse)
STOP D2: something of the run is alive; nothing deleted. Next: run D2-check, ask the builder in the channel.
/tmp/v10t/home/hadavin-smoke
## D2 delete DEL=yes, nothing alive
deleted
ls: cannot access '/tmp/v10t/home/hadavin-smoke': No such file or directory
```

## 3. Negative cases for the chain steps (raw): empty CHAIN, CHAIN=7, no patch tool, CR in a patch, damaged plan, existing output, no Python
```
######## N1 CHAIN empty

## block 03 (A3 with CHAIN empty)
ok plan-v5-fixes.patch checksum
ok plan-v5-repin-v6.patch checksum
ok plan-v5-gate-rows-v3.patch checksum
ok original checksum
[rc=0]

## block 07 (A5b4 CHAIN empty)
STOP CHAIN: CHAIN is ''. Next: decide 2, 3 or 4 in A0, write it in section 1, set the variables again.
[rc=1]
######## N2 CHAIN=7

## block 03 (A3 CHAIN=7)
ok plan-v5-fixes.patch checksum
ok plan-v5-repin-v6.patch checksum
ok plan-v5-gate-rows-v3.patch checksum
ok original checksum
[rc=0]
######## N3 CHAIN=2 with no GNU patch on PATH (git apply fallback)

## block 02 (A1)
ok A1: made /tmp/v10t/hb/_local/scratch/lead-plan-work
[rc=0]

## block 03 (A2)
ok plan-v5-fixes.patch checksum
ok plan-v5-repin-v6.patch checksum
ok plan-v5-gate-rows-v3.patch checksum
ok original checksum
[rc=0]
(no patch on PATH)
ok A3
[rc=0]
ok A4
[rc=0]
######## N4 CHAIN=3 with no GNU patch (must STOP, no fallback for step 3)

## block 02 (A1)
ok A1: made /tmp/v10t/hb/_local/scratch/lead-plan-work
[rc=0]

## block 03 (A2)
ok plan-v5-fixes.patch checksum
ok plan-v5-repin-v6.patch checksum
ok plan-v5-gate-rows-v3.patch checksum
ok original checksum
[rc=0]
ok A3
ok A4
STOP A5b: the program patch is not installed and this chain step cannot use git apply. Next: set CHAIN=2 in section 1, set the variables, mv "/tmp/v10t/hb/_local/scratch/lead-plan-work" "/tmp/v10t/hb/_local/scratch/lead-plan-work.old" (if .old exists use .old2), start at A1.
[rc=1]
######## N5 CHAIN=4 existing real-v5-plan.md before A5b4 / output exists

## block 02 (A1)
ok A1: made /tmp/v10t/hb/_local/scratch/lead-plan-work
[rc=0]

## block 03 (A2)
ok plan-v5-fixes.patch checksum
ok plan-v5-repin-v6.patch checksum
ok plan-v5-gate-rows-v3.patch checksum
ok original checksum
[rc=0]

## block 04 (A3)
ok A3
[rc=0]

## block 05 (A4)
ok A4
[rc=0]

## block 06 (A5b)
ok A5b
[rc=0]

## block 07 (A5b4 output exists)
29 old edits; corrected or added: ['2', '4', '5', '18', '19', '20', '21', '29', '30']
failing []
written /tmp/v10t/hb/_local/scratch/lead-plan-work/real-v5-plan.md 28f92c5d1211207c 780 lines
ok A5b4
[rc=0]
######## N6 CHAIN=4 no python

## block 07 (A5b4 no python)
ok A5b4 (already applied: nothing changed)
[rc=0]
######## N7 CR in a patch file

## block 03 (A2 CR in patch)
STOP A2: plan-v5-fixes.patch has CR. Next: do section 0b (autocrlf false), get the file again: git -C "$PC" checkout -- plan-v5-fixes.patch , then run A2 again.
STOP A2: plan-v5-fixes.patch is not the expected file (checksum). Next: get it again from the repository.
ok plan-v5-repin-v6.patch checksum
ok plan-v5-gate-rows-v3.patch checksum
ok original checksum
[rc=0]
######## N8 damaged plan (extra line) before A3

## block 02 (A1)
ok A1: made /tmp/v10t/hb/_local/scratch/lead-plan-work
[rc=0]

## block 03 (A2)
ok plan-v5-fixes.patch checksum
ok plan-v5-repin-v6.patch checksum
ok plan-v5-gate-rows-v3.patch checksum
ok original checksum
[rc=0]

## block 04 (A3 on damaged plan)
STOP A3: the plan in the work folder does not start from the checksum this step expects (it is 57317bf229ab9667). If you are repeating a step you already did, go to A6: it names the state. Next: nothing was changed; move aside and start at A1 only if A6 also says STOP.
[rc=1]
--- second run (corrected cases N5 to N8) ---
######## N2b CHAIN=7 A3 and A5b4

## block 02 (A1)
ok A1: made /tmp/v10t/hb/_local/scratch/lead-plan-work
[rc=0]

## block 03 (A2)
ok plan-v5-fixes.patch checksum
ok plan-v5-repin-v6.patch checksum
ok plan-v5-gate-rows-v3.patch checksum
ok original checksum
[rc=0]

## block 04 (A3)
ok A3
[rc=0]

## block 07 (A5b4)
STOP CHAIN: CHAIN is '7'. Next: decide 2, 3 or 4 in A0, write it in section 1, set the variables again.
[rc=1]
######## N5 CHAIN=4 junk real-v5-plan.md in W

## block 02 (A1)
ok A1: made /tmp/v10t/hb/_local/scratch/lead-plan-work
[rc=0]

## block 03 (A2)
ok plan-v5-fixes.patch checksum
ok plan-v5-repin-v6.patch checksum
ok plan-v5-gate-rows-v3.patch checksum
ok original checksum
[rc=0]

## block 04 (A3)
ok A3
[rc=0]

## block 05 (A4)
ok A4
[rc=0]

## block 06 (A5b)
ok A5b
[rc=0]

## block 07 (A5b4 output exists (different content))
STOP A5b4: /tmp/v10t/hb/_local/scratch/lead-plan-work/real-v5-plan.md already exists; the script refuses to overwrite, so this step cannot run twice. Next: mv "/tmp/v10t/hb/_local/scratch/lead-plan-work/real-v5-plan.md" "/tmp/v10t/hb/_local/scratch/lead-plan-work/real-v5-plan.md.old" (if .old exists
[rc=1]
junk

######## N5b existing output with the right checksum

## block 07 (A5b4 first)
29 old edits; corrected or added: ['2', '4', '5', '18', '19', '20', '21', '29', '30']
failing []
written /tmp/v10t/hb/_local/scratch/lead-plan-work/real-v5-plan.md 28f92c5d1211207c 780 lines
ok A5b4
[rc=0]

## block 07 (A5b4 second)
ok A5b4 (already applied: nothing changed)
[rc=0]
######## N6 CHAIN=4 no python

## block 02 (A1)
ok A1: made /tmp/v10t/hb/_local/scratch/lead-plan-work
[rc=0]

## block 03 (A2)
ok plan-v5-fixes.patch checksum
ok plan-v5-repin-v6.patch checksum
ok plan-v5-gate-rows-v3.patch checksum
ok original checksum
[rc=0]

## block 04 (A3)
ok A3
[rc=0]

## block 05 (A4)
ok A4
[rc=0]

## block 06 (A5b)
ok A5b
[rc=0]
(no python on PATH)
STOP A5b4: no working Python 3.6 or newer in Git Bash. Next: set CHAIN=3 in section 1 (or install Python), set the variables.
[rc=1]
######## N7 CR in a patch file

## block 03 (A2 CR in patch)
STOP A2: plan-v5-fixes.patch has CR. Next: do section 0b (autocrlf false), get the file again: git -C "$PC" checkout -- plan-v5-fixes.patch , then run A2 again.
STOP A2: plan-v5-fixes.patch is not the expected file (checksum). Next: get it again from the repository.
ok plan-v5-repin-v6.patch checksum
ok plan-v5-gate-rows-v3.patch checksum
ok original checksum
[rc=0]
######## N8 damaged plan

## block 02 (A1)
ok A1: made /tmp/v10t/hb/_local/scratch/lead-plan-work
[rc=0]

## block 03 (A2)
ok plan-v5-fixes.patch checksum
ok plan-v5-repin-v6.patch checksum
ok plan-v5-gate-rows-v3.patch checksum
ok original checksum
[rc=0]

## block 04 (A3 on damaged plan)
STOP A3: the plan in the work folder does not start from the checksum this step expects (it is 57317bf229ab9667). If you are repeating a step you already did, go to A6: it names the state. Next: nothing was changed; move aside and start at A1 only if A6 also says STOP.
[rc=1]
```

## 4. Not run, stated honestly
- Git Bash, WSL and PowerShell were never started. Anything that depends on them (cygpath real output, the HB form on a real C: path, a real dash in Git Bash, autocrlf behaviour of git on Windows, files arriving on the laptop with CR) was only simulated or not tested.
- HB/HBW check: only the norm function and the stub path form were exercised, not a real /c/Users path.
- The stand-in process was tested as user 65534 on Linux (unreadable environ proven by the Permission denied line); a real n8n process, a real WSL /proc and real Windows process lists were not.
- C6 "the reader actually reads the lines" is a human step; only acc5.sh's judgement of a made-up diff was run (ACCEPT on the stub diff; STOP on a diff with an exit 9 line).
- The apply script's own defects F3 and F4 were not fixed (not mine to edit); see v10-OPEN-FOR-LEAD.md.
- No test used the real plan folders, real keys or a live model.
- Test-harness artefact: the D2 process scan matches any process whose command line contains the words n8n or hadavin-smoke, including the test harness's own parent shell when it was started with a long command text; on the laptop a normal terminal does not carry those words.
- With CHAIN=7, blocks A1 to A4 still print ok (they do not read CHAIN); A5b4 then refuses. Harmless, not changed.
