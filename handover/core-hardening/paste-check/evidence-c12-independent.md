# evidence-c12-independent (EVIDENCE RUNNER: raw outputs, no judgement). Run 2026-11-16, Linux 6.18, bash GNU bash, version 5.2.21(1)-release (x86, dash from /usr/bin/dash

## Not run / limits (first)
- NOT run: Git Bash, WSL, PowerShell, the real plan (plan-wp6-resmoke-v5.md), a real agents-register, real PROGRESS.md. Everything below ran on this Linux box with FAKE files.
- The real hbok() helper (needs Git Bash cygpath and /c/... paths) was replaced by 'return 0' in the harness, so hbok itself was not exercised.
- The plan table in the C4 harness is a FAKE I wrote (lines like '| A1 | a.sh | the word alpha | <FINAL-LINES> |'). It says nothing about how the real plan escapes table text.
- The C4/rows tests use a FAKE git repo built under the scratchpad (git init there; the project repo was not touched). Case 4 uses a really corrupted loose blob (git grep exit 128); case 4b a function wrapper that returns 2 for 'git grep' (simulated).
- Blocks were run under bash only (they use $'..' and local; the checklist says Git Bash). dash -n was syntax-only.
- Failures found by me: none in the items below (see raw output).

## (1) diff rev11 vs rev12
$ diff LEAD-CHECKLIST-v5.rev11.md LEAD-CHECKLIST-v5.md  (exit 1 = differ)
files: rev11 350 lines 98023 bytes; rev12 352 lines 100235 bytes. diff output: 73 lines; 18 hunks
hunk headers (rev11 line -> rev12 line): 1,2c1,2 8c8 63c63 69c69 119c119 136c136 225c225 247c247 249c249 266c266 283c283 285c285 287c287 289c289 297c297 331c331 341c341 347a348,349 
hunk content (each line cut to 160 chars):
    1,2c1,2
    < # LEAD CHECKLIST for the re-smoke plan v5 (revision 11, written 2026-11-16). For the lead, in Git Bash on the laptop.
    < **Words used in this file, one meaning each.** **The plan** = `plan-wp6-resmoke-v5.md`. "v5" always means the plan; the file names `LEAD-CHECKLIST-v5.md` and 
    ---
    > # LEAD CHECKLIST for the re-smoke plan v5 (revision 12, written 2026-11-16). For the lead, in Git Bash on the laptop.
    > **Words used in this file, one meaning each.** **The plan** = `plan-wp6-resmoke-v5.md`. "v5" always means the plan; the file names `LEAD-CHECKLIST-v5.md` and 
    8c8
    < - **lead** = you: the person or session at the laptop who reads this file and types the commands. **owner** = the studio owner; he only types `y`, the challen
    ---
    > - **lead** = you: the person or session at the laptop who reads this file and types the commands. **owner** = the studio owner; he only types `y`, the challen
    63c63
    < rows() { local H id f s; H=$(git -C "$WT" rev-parse HEAD) || { echo "STOP C1: git cannot read the worktree $WT. Next: if the folder does not exist, list the w
    ---
    > rows() { local H id f s g r e=0; H=$(git -C "$WT" rev-parse HEAD) || { echo "STOP C1: git cannot read the worktree $WT. Next: if the folder does not exist, li
    69c69
    <   while IFS=$'\t' read -r id f s || [ -n "$id" ]; do if git -C "$WT" cat-file -e "$PIN:scripts/$f" 2>/dev/null; then printf '%s %s %s\n' "$id" "$f" "$(git -C 
    ---
    >   while IFS=$'\t' read -r id f s || [ -n "$id" ]; do if git -C "$WT" cat-file -e "$PIN:scripts/$f" 2>/dev/null; then g=$(git -C "$WT" grep -n -F -e "$s" "$PIN
    119c119
    < A2. Check the original plan, the patches, the apply script, the edit lists, `acc5.sh` and `LEAD-FILL-list-v5.md` (the source of `P-4b.sh`): the file exists, n
    ---
    > A2. Check the original plan, the patches, the apply script, the edit lists, `acc5.sh` and `LEAD-FILL-list-v5.md` (the source of `P-4b.sh`): the file exists, n
    136c136
    < A5b4. Chain step 4, only if `CHAIN` is 4: the edit list `plan-v10-real-v5-edits.md` (29 edits) with `plan-v10-corrections-after-chain.md` (corrected edits 2, 
    ---
    > A5b4. Chain step 4, only if `CHAIN` is 4: the edit list `plan-v10-real-v5-edits.md` (29 edits) with `plan-v10-corrections-after-chain.md` (corrected edits 2, 
    225c225
    < if [ -z "${HBW:-}" ] || ! cd "$HBW/_local/scratch/wp6-smoke/pastes"; then echo "STOP C2b: HBW is not set or the pastes folder cannot be entered. Next: paste t
    ---
    > if [ -z "${HBW:-}" ] || ! cd "$HBW/_local/scratch/wp6-smoke/pastes"; then echo "STOP C2b: HBW is not set or the pastes folder cannot be entered. Next: paste t
    247c247
    < Then fill the rows in `PF`. The block refuses odd values; it counts rows it really changed and prints how many it filled (must be 20) and how many are open (m
    ---
    > Then fill the rows in `PF`. The block first refuses stale rows (line 1 of `rows.txt` must be `head=` followed by this `PIN`) and any string of `strings.txt` (
    249c249
    < hbok && { if [ "$(cat "$W/rows.rc" 2>/dev/null)" != 0 ]; then echo "STOP C4: the rows block above has not run clean in this work folder (no rows.rc proof, or 
    ---
    > hbok && { if [ "$(cat "$W/rows.rc" 2>/dev/null)" != 0 ]; then echo "STOP C4: the rows block above has not run clean in this work folder (no rows.rc proof, or 
    266c266
    < hbok && { if [ -z "$BR" ]; then echo "STOP C8: BR is empty. Next: do C2 (BR and WTN), then C8 again."; else bad=0; for g in "nlite-fix5 $WTN" "take/nlite-int-
    ---
    > hbok && { if [ -z "$BR" ]; then echo "STOP C8: BR is empty. Next: do C2 (BR and WTN), then C8 again."; else bad=0; for g in "nlite-fix5 $WTN" "take/nlite-int-
    283c283
    < if grep -qi microsoft /proc/version 2>/dev/null; then for f in "$HOME/hadavin-smoke/take-smoke-1/n8n.pid" "$HOME/hadavin-smoke/ctl/n8n.pid"; do if [ -f "$f" ]
    ---
    > if grep -qi microsoft /proc/version 2>/dev/null; then for f in "$HOME/hadavin-smoke/take-smoke-1/n8n.pid" "$HOME/hadavin-smoke/ctl/n8n.pid"; do if [ -f "$f" ]
    285c285
    < Then in Git Bash. The block refuses: a pid that is not digits, a pid below 2, a pid that differs from the one D1a printed, a pid missing from the register, a 
    ---
    > Then in Git Bash. The block refuses: a pid that is not digits, a pid below 2, a pid that differs from the one D1a printed, a pid missing from the register (ma
    287c287
    < PID=''; PIDSAYS=''; F="$EV/PROGRESS.md"; R="$HB/_local/agents-register.md"; case "$PID" in ''|*[!0-9]*) echo "STOP D1: PID must be digits. Next: write the pid
    ---
    > PID=''; PIDSAYS=''; F="$EV/PROGRESS.md"; R="$HB/_local/agents-register.md"; case "$PID" in ''|*[!0-9]*) echo "STOP D1: PID must be digits. Next: write the pid
    289c289
    < After a `kill exit=3` or `GONE-FAIL` no R2 is allowed. Next action: write nothing, tell the builder in the channel; the plan (S13, 13.4 and 13.5) goes on by i
    ---
    > After a `kill exit=3` line no R2 is allowed (a normal `GONE-FAIL` without exit 3 still allows the R2 clean-up of plan 13.1; the block does not refuse it). Nex
    297c297
    < HITPID=''; case "$HITPID" in ''|*[!0-9]*) echo "STOP D2: HITPID must be digits. Next: write the pid of one P-4b-HIT line.";; *) if grep -qi microsoft /proc/ve
    ---
    > HITPID=''; case "$HITPID" in ''|*[!0-9]*) echo "STOP D2: HITPID must be digits. Next: write the pid of one P-4b-HIT line.";; *) if grep -qi microsoft /proc/ve
    331c331
    < | C1 | git cannot read the worktree | fix `WTN`, set the variables again |
    ---
    > | C1 | git cannot read the worktree | if the folder `$WT` is missing: do not make it, ask in the channel (the round-5 builder made it); if it exists under ano
    341c341
    < | D1 | pid not digits, below 2, not the pid D1a printed, not in the register, no `NEED-LEAD` line, a `LEAD-YES` already there, or `GONE-FAIL` / `kill exit=3` 
    ---
    > | D1 | pid not digits, below 2, not the pid D1a printed, not in the register, no `NEED-LEAD` line, a `LEAD-YES` already there, or a `kill exit=3` line exists 
    347a348,349
    > Revision 12 (2026-11-16): fixes of the two reviews of revision 11 (D1 now refuses only after `kill exit=3`, not after every `GONE-FAIL`; C4 refuses stale rows
    > 

## (2) fenced bash blocks of rev 12
fence lines total: 90; opening bash fences: 45; blocks extracted: 45
bash -n failures: 0 ; dash -n failures: 0 (dash -n sanity: 'if then' file gives a syntax error rc=2, so dash -n does detect errors)

## (3a) D1 block (block 40) harness; fake EV/PROGRESS.md/register; raw output
```
--- CASE kill exit=1 + GONE-FAIL (must ALLOW) (pid=4242) rc=0
kill exit=1
LEAD-YES R2 pid=4242 2026-11-16T12:27Z
PROGRESS.md after:
NEED-LEAD R2 pid=4242
GONE-FAIL x
kill exit=1
LEAD-YES R2 pid=4242 2026-11-16T12:27Z
--- CASE kill exit=3 (must STOP) (pid=4242) rc=0
STOP D1: a kill exit=3 line exists: no R2 is allowed after exit 3. Next: write nothing, tell the builder; the plan (S13, 13.4 and 13.5) goes on by itself.
PROGRESS.md after:
NEED-LEAD R2 pid=4242
kill exit=3
--- CASE kill exit=3 end of line variant 'kill exit=3 foo' (must STOP) (pid=4242) rc=0
STOP D1: a kill exit=3 line exists: no R2 is allowed after exit 3. Next: write nothing, tell the builder; the plan (S13, 13.4 and 13.5) goes on by itself.
PROGRESS.md after:
NEED-LEAD R2 pid=4242
kill exit=3 foo
--- CASE kill exit=30 (text: not exit 3, must ALLOW) (pid=4242) rc=0
kill exit=30
LEAD-YES R2 pid=4242 2026-11-16T12:27Z
PROGRESS.md after:
NEED-LEAD R2 pid=4242
kill exit=30
LEAD-YES R2 pid=4242 2026-11-16T12:27Z
--- CASE kill exit=13 (must ALLOW) (pid=4242) rc=0
kill exit=13
LEAD-YES R2 pid=4242 2026-11-16T12:27Z
PROGRESS.md after:
NEED-LEAD R2 pid=4242
kill exit=13
LEAD-YES R2 pid=4242 2026-11-16T12:27Z
--- CASE GONE-FAIL only, no kill line (must ALLOW) (pid=4242) rc=0
GONE-FAIL
LEAD-YES R2 pid=4242 2026-11-16T12:27Z
PROGRESS.md after:
NEED-LEAD R2 pid=4242
GONE-FAIL
LEAD-YES R2 pid=4242 2026-11-16T12:27Z
--- CASE pid only inside date in register (must STOP not in register) (pid=4242) rc=0
STOP D1: the pid 4242 is not in the register $SCR/h/tmp.lT8fluSnGw/_local/agents-register.md (or the register file is missing). Next: write nothing; ask the runner for its register row of the 
PROGRESS.md after:
NEED-LEAD R2 pid=4242
--- CASE pid as date part 16 : register has 2026-11-16 only (pid=16) rc=0
STOP D1: the pid 16 is not in the register $SCR/h/tmp.bTNPL5AZdw/_local/agents-register.md (or the register file is missing). Next: write nothing; ask the runner for its register row of the ta
PROGRESS.md after:
NEED-LEAD R2 pid=16
--- CASE pid as whole word in register (must ALLOW) (pid=4242) rc=0
NEED-LEAD R2 pid=4242
LEAD-YES R2 pid=4242 2026-11-16T12:27Z
PROGRESS.md after:
NEED-LEAD R2 pid=4242
LEAD-YES R2 pid=4242 2026-11-16T12:27Z
```

## (3b) C4 fill (block 32) and rows (block 2 helper, block 31 caller); FAKE repo, FAKE plan table; raw output
```
######## CASE 1: matching case, real repo
rows rc=0
head=9d68422a66707b0166b17748d26d7a259087170b seven=9d68422 branch=main
A1 a.sh 1,3
A2 a.sh 2,3
B1 b.sh 1
fill rc=0
rows filled by this run: 3 (20 the first time; 0 on a repeat is fine if open is 0)
rows still open: 0 (must be 0)
CR count: 0
ok C4: now run: accept 6
plan after:
| A1 | a.sh | the word alpha | 1,3 |
| A2 | a.sh | the word beta | 2,3 |
| B1 | b.sh | gamma | 1 |
######## CASE 2: rows.txt wrong head line (stale pin)
rows rc=0
head=9d68422a66707b0166b17748d26d7a259087170b seven=9d68422 branch=main
A1 a.sh 1,3
A2 a.sh 2,3
B1 b.sh 1
head=0000000000000000000000000000000000000000 seven=9d68422 branch=main
fill rc=0
STOP C4: line 1 of rows.txt is not head=<this PIN>: the rows are stale or from another pin. Next: run the rows block above again with this PIN; fill nothing.
plan after:
| A1 | a.sh | the word alpha | <FINAL-LINES> |
| A2 | a.sh | the word beta | <FINAL-LINES> |
| B1 | b.sh | gamma | <FINAL-LINES> |
######## CASE 2b: rows.txt line 1 missing head= entirely
rows rc=0
head=9d68422a66707b0166b17748d26d7a259087170b seven=9d68422 branch=main
A1 a.sh 1,3
A2 a.sh 2,3
B1 b.sh 1
fill rc=0
STOP C4: line 1 of rows.txt is not head=<this PIN>: the rows are stale or from another pin. Next: run the rows block above again with this PIN; fill nothing.
plan after:
| A1 | a.sh | the word alpha | <FINAL-LINES> |
| A2 | a.sh | the word beta | <FINAL-LINES> |
| B1 | b.sh | gamma | <FINAL-LINES> |
######## CASE 3: strings.txt col3 not in plan table row
rows rc=0
head=9d68422a66707b0166b17748d26d7a259087170b seven=9d68422 branch=main
A1 a.sh 1,3
A2 a.sh 2,3
B1 b.sh 
fill rc=0
C4 mismatch: the string of row B1 (strings.txt column 3) is not in the plan table row B1
STOP C4: strings.txt does not match the plan table (rows listed above). Next: tell the builder (paste the lines); fill nothing.
plan after:
| A1 | a.sh | the word alpha | <FINAL-LINES> |
| A2 | a.sh | the word beta | <FINAL-LINES> |
| B1 | b.sh | gamma | <FINAL-LINES> |
######## CASE 3b: strings col3 matches only a different row (A2 string placed in A1 row)
rows rc=0
head=9d68422a66707b0166b17748d26d7a259087170b seven=9d68422 branch=main
A1 a.sh 2,3
fill rc=0
C4 mismatch: the string of row A1 (strings.txt column 3) is not in the plan table row A1
STOP C4: strings.txt does not match the plan table (rows listed above). Next: tell the builder (paste the lines); fill nothing.
plan after:
| A1 | a.sh | the word alpha | <FINAL-LINES> |
| A2 | a.sh | the word beta | <FINAL-LINES> |
| B1 | b.sh | gamma | <FINAL-LINES> |
######## CASE 4: rows with REAL failing git grep (corrupted blob, exit 128)
rows rc=1
head=9d68422a66707b0166b17748d26d7a259087170b seven=9d68422 branch=main
error: inflate: data stream error (incorrect header check)
error: unable to unpack 56464793a3166d51f110c13591a44e9dc9bbe61e header
fatal: loose object 56464793a3166d51f110c13591a44e9dc9bbe61e (stored in .git/objects/56/464793a3166d51f110c13591a44e9dc9bbe61e) is corrupt
STOP C4: git grep failed (exit 128) for row A1. Next: tell the builder.
A1 a.sh 
error: inflate: data stream error (incorrect header check)
error: unable to unpack 56464793a3166d51f110c13591a44e9dc9bbe61e header
fatal: loose object 56464793a3166d51f110c13591a44e9dc9bbe61e (stored in .git/objects/56/464793a3166d51f110c13591a44e9dc9bbe61e) is corrupt
STOP C4: git grep failed (exit 128) for row A2. Next: tell the builder.
A2 a.sh 
B1 b.sh 1
rows.rc file: 1
######## CASE 4b: rows with SIMULATED git grep exit 2 (git function wrapper)
rows rc=1
head=9d68422a66707b0166b17748d26d7a259087170b seven=9d68422 branch=main
STOP C4: git grep failed (exit 2) for row A1. Next: tell the builder.
A1 a.sh 
STOP C4: git grep failed (exit 2) for row A2. Next: tell the builder.
A2 a.sh 
STOP C4: git grep failed (exit 2) for row B1. Next: tell the builder.
B1 b.sh 
######## CASE 4c: block b31 as written, with failing grep (real corrupt), prints STOP hint + rc
error: inflate: data stream error (incorrect header check)
error: unable to unpack 56464793a3166d51f110c13591a44e9dc9bbe61e header
fatal: loose object 56464793a3166d51f110c13591a44e9dc9bbe61e (stored in .git/objects/56/464793a3166d51f110c13591a44e9dc9bbe61e) is corrupt
error: inflate: data stream error (incorrect header check)
error: unable to unpack 56464793a3166d51f110c13591a44e9dc9bbe61e header
fatal: loose object 56464793a3166d51f110c13591a44e9dc9bbe61e (stored in .git/objects/56/464793a3166d51f110c13591a44e9dc9bbe61e) is corrupt
head=9d68422a66707b0166b17748d26d7a259087170b seven=9d68422 branch=main
STOP C4: git grep failed (exit 128) for row A1. Next: tell the builder.
A1 a.sh 
STOP C4: git grep failed (exit 128) for row A2. Next: tell the builder.
A2 a.sh 
B1 b.sh 1
(C4 stopped: see the STOP line above)
b31 rc=0
rows.rc=1
```
exit codes shown inline as 'rows rc=' / 'fill rc=' / 'rows.rc'. Note: block 32 itself exits 0 when it prints STOP (it signals by text and by leaving the plan unfilled); the plan-after listing shows nothing was filled in cases 2, 2b, 3, 3b.

## (4) sha256
$ sha256sum LEAD-FILL-list-v5.md LEAD-CHECKLIST-v5.md
da2635db2d7c329169eca1aba285e47fd17fd734908bce20dff3a55c122ee9ca  LEAD-FILL-list-v5.md
ede7e96e2f4d6737cb6baf59720bd3108dad346f5252f0d2fa8a476c8a844849  LEAD-CHECKLIST-v5.md
claimed in v12-CHANGES.md: checklist ede7e96e2f4d6737cb6baf59720bd3108dad346f5252f0d2fa8a476c8a844849 ; fill list da2635db2d7c329169eca1aba285e47fd17fd734908bce20dff3a55c122ee9ca
checklist: MATCH
fill list: MATCH
fill list identical to rev11
