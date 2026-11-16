# evidence-c13 (raw outputs, harness runs against rev 13; made-up data; scratch dirs)

Syntax sweep of final file (bash -n and dash -n on 45 blocks): 0 failures.
sha256:
33f50ab7b781b965b86c090106230597c4d80445536878eecfa4fb4b622b73b6  LEAD-CHECKLIST-v5.md
da2635db2d7c329169eca1aba285e47fd17fd734908bce20dff3a55c122ee9ca  LEAD-FILL-list-v5.md
4ee334309b17375df29209610bc0094c504286b7a0781410c2a5be54113626e9  acc5.sh

## neg1.txt
```
##### N1 C9: proof-c8.txt removed
--- b37
STOP C9: C8 has not printed ok for this PF (no proof-c8.txt, or PF changed after C8). Next: run C7 and C8 again.
rc=1
PROGRESS.md lines: 1
##### N2 C9: PF changed after C8 (one comment line appended)
--- b37
STOP C9: C8 has not printed ok for this PF (no proof-c8.txt, or PF changed after C8). Next: run C7 and C8 again.
rc=1
PROGRESS.md lines: 1
##### N3 C9: PROGRESS.md is a symlink to an outside file
--- b37
STOP LINK: PROGRESS.md is a symbolic link or not a plain file: nothing is written through it. Next: tell the builder.
rc=1
outside file: outside-original
##### N4 C9: PROGRESS.md immutable (write fails)
--- b37
$S/h/blk.20640/x.sh: line 1: /q/r4/egm/duplicate-proof-lead-desk/wp6/evidence-2/PROGRESS.md: Operation not permitted
STOP C9: the line could not be written (read-only file or no space?). Next: nothing was released; check that you may write PROGRESS.md; tell the builder.
rc=1
PROGRESS.md: P-3a done 2026-11-16T10:00Z
##### N5 C9: PROGRESS.md is a directory
--- b37
STOP LINK: PROGRESS.md is a symbolic link or not a plain file: nothing is written through it. Next: tell the builder.
rc=1
##### N6 C9: standin-gone.txt is a symlink
--- b37
STOP C9: the stand-in is not proven gone for the current control file. Next: run WSL-4 (C2b step 4).
rc=1
--- b36
dash syntax ok
P-4b files ok
STOP LINK: standin-gone.txt is a symbolic link. Next: write nothing; tell the builder.
rc=1
##### N7 C9 and C8b: control file is a symlink
--- b37
STOP C9: the P-4b files do not pass C2c. Next: run C2c and fix.
rc=1
--- b36
STOP LINK: /q/r4/_local/scratch/wp6-smoke/pastes/P-4b.control.txt is a symbolic link; it must be a plain file. Next: write nothing; tell the builder, then aside "/q/r4/_local/scratch/wp6-smoke/pastes/P-4b.control.txt" and make the file again with the
ok C8b: stand-in gone for the current control file
rc=1
--- b27
STOP LINK: /q/r4/_local/scratch/wp6-smoke/pastes/P-4b.control.txt is a symbolic link; it must be a plain file. Next: write nothing; tell the builder, then aside "/q/r4/_local/scratch/wp6-smoke/pastes/P-4b.control.txt" and make the file again with the
rc=1
##### N8 C7 and C8: PF missing
--- b34
STOP PF: the plan file PF (/q/r4/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md) does not exist or is a symbolic link (a link could send a change to another file). Next: do A8 (copy the patched plan); if PF is a link, tell the builder, then
rc=1
--- b35
STOP PF: the plan file PF (/q/r4/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md) does not exist or is a symbolic link (a link could send a change to another file). Next: do A8 (copy the patched plan); if PF is a link, tell the builder, then
rc=1
--- b37
STOP C9: C7 is not clean. Next: run C7.
rc=1
##### N9 C7 and C8 and C2 and B2 and flip: PF is a symlink
--- b34
STOP PF: the plan file PF (/q/r4/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md) does not exist or is a symbolic link (a link could send a change to another file). Next: do A8 (copy the patched plan); if PF is a link, tell the builder, then
rc=1
--- b35
STOP PF: the plan file PF (/q/r4/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md) does not exist or is a symbolic link (a link could send a change to another file). Next: do A8 (copy the patched plan); if PF is a link, tell the builder, then
rc=1
--- b18
STOP PF: the plan file PF (/q/r4/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md) does not exist or is a symbolic link (a link could send a change to another file). Next: do A8 (copy the patched plan); if PF is a link, tell the builder, then
rc=1
--- b16
STOP PF: the plan file PF (/q/r4/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md) does not exist or is a symbolic link (a link could send a change to another file). Next: do A8 (copy the patched plan); if PF is a link, tell the builder, then
rc=1
--- b15
STOP PF: the plan file PF (/q/r4/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md) does not exist or is a symbolic link (a link could send a change to another file). Next: do A8 (copy the patched plan); if PF is a link, tell the builder, then
rc=1
--- acc6.sh
STOP PF: the plan file PF (/q/r4/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md) does not exist or is a symbolic link (a link could send a change to another file). Next: do A8 (copy the patched plan); if PF is a link, tell the builder, then
rc=1
--- b14
STOP PF: the plan file PF (/q/r4/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md) does not exist or is a symbolic link (a link could send a change to another file). Next: do A8 (copy the patched plan); if PF is a link, tell the builder, then
rc=1
##### N10 C4 fill: PF missing
--- b31
STOP PF: the plan file PF (/q/r4/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md) does not exist or is a symbolic link (a link could send a change to another file). Next: do A8 (copy the patched plan); if PF is a link, tell the builder, then
rc=1
##### N11 positive again after all restores: C7 C8 C9
--- b34
counts 0 0 2 1 (must be 0 0 2 1); CR=0 (0); first 3 bytes in hex=232057 (BOM if efbbbf); distinct 40-character shas: 1 (1, and equal to PIN)
ok C7
rc=0
--- b35
names in PF (count, name):
      3 nlite-fix3
      1 nlite-fix4
     15 nlite-fix5
      1 nlite-int
      1 nlite-int-r5
      1 take/n8n.lock
      1 take/n8n.pid
      2 take/nlite-int-r3
      1 take/nlite-int-r4
      9 take/nlite-int-r5
ok C8
rc=0
--- b37
P-3a done 2026-11-16T10:00Z
LEAD-GO RE-PIN 2026-11-16T12:40Z pin=8b6f83f36ba38f7141ed3b5a9b23a1e488d98154 plan=3e764722f7baa29c
rc=0
```

## neg2.txt
```
##### C5/C6 OLD=[f66c4ed]
--- b32
known
== n8n_start.sh
== n8n_kill.py
-    sys.exit(0)
+    print("refused: unreadable")
+    sys.exit(3)
== end
rc=0
##### C5/C6 OLD=[1f4dfc2]
--- b32
unknown
== n8n_start.sh
== n8n_kill.py
-    sys.exit(1)
+    print("refused: unreadable")
+    sys.exit(3)
== end
rc=0
##### C5/C6 OLD=[-h]
--- b32
STOP C5: OLD is [-h], not 7 to 40 lowercase hex characters (a commit sha). An empty value, a name such as HEAD or a value that starts with - is refused, so it can never reach git as an option or as a name that moves. Next: write the old pin of line 3 of the pl
rc=1
##### C5/C6 OLD=[--all]
--- b32
STOP C5: OLD is [--all], not 7 to 40 lowercase hex characters (a commit sha). An empty value, a name such as HEAD or a value that starts with - is refused, so it can never reach git as an option or as a name that moves. Next: write the old pin of line 3 of the
rc=1
##### C5/C6 OLD=[HEAD]
--- b32
STOP C5: OLD is [HEAD], not 7 to 40 lowercase hex characters (a commit sha). An empty value, a name such as HEAD or a value that starts with - is refused, so it can never reach git as an option or as a name that moves. Next: write the old pin of line 3 of the 
rc=1
##### C5/C6 OLD=[]
--- b32
STOP C5: the old commit eec6ba4 is neither in /q/r4/_local/scratch/wt/nlite-fix5 nor in the round-3 worktree /q/r4/_local/scratch/wt/nlite-fix3. Next: check W3N and OLD against line 3 of the plan; tell the builder.
rc=1
##### C5/C6 OLD=[zzzzzzz]
--- b32
STOP C5: OLD is [zzzzzzz], not 7 to 40 lowercase hex characters (a commit sha). An empty value, a name such as HEAD or a value that starts with - is refused, so it can never reach git as an option or as a name that moves. Next: write the old pin of line 3 of t
rc=1
##### C5/C6 OLD=[ABCDEF1]
--- b32
STOP C5: OLD is [ABCDEF1], not 7 to 40 lowercase hex characters (a commit sha). An empty value, a name such as HEAD or a value that starts with - is refused, so it can never reach git as an option or as a name that moves. Next: write the old pin of line 3 of t
rc=1
##### C5/C6 OLD=[8b6f83f]
--- b32
STOP C5: OLD is the same commit as PIN, so the diff would be empty. Next: check OLD against line 3 of the plan; tell the builder.
rc=1
##### C5/C6 OLD=[8b6f83f36ba38f7141ed3b5a9b23a1e488d98154]
--- b32
STOP C5: OLD is the same commit as PIN, so the diff would be empty. Next: check OLD against line 3 of the plan; tell the builder.
rc=1
##### C5/C6 OLD=[0000000]
--- b32
STOP C5: the old commit 0000000 is neither in /q/r4/_local/scratch/wt/nlite-fix5 nor in the round-3 worktree /q/r4/_local/scratch/wt/nlite-fix3. Next: check W3N and OLD against line 3 of the plan; tell the builder.
rc=1
##### C5/C6 OLD=[f66c4ed;id]
--- b32
known
== n8n_start.sh
== n8n_kill.py
-    sys.exit(0)
+    print("refused: unreadable")
+    sys.exit(3)
== end
rc=0
##### C5/C6 OLD=[-f66c4ed]
--- b32
STOP C5: OLD is [-f66c4ed], not 7 to 40 lowercase hex characters (a commit sha). An empty value, a name such as HEAD or a value that starts with - is refused, so it can never reach git as an option or as a name that moves. Next: write the old pin of line 3 of 
rc=1
##### C6 OLD=[1f4dfc2] (round-3 route, acc5)
--- b33
ACCEPT
---- the n8n_kill.py part, read it:
== n8n_kill.py
-    sys.exit(1)
+    print("refused: unreadable")
+    sys.exit(3)
== end
rc=0
##### C6 OLD=[HEAD]
--- b33
STOP C5: OLD is [HEAD], not 7 to 40 lowercase hex characters (a commit sha). An empty value, a name such as HEAD or a value that starts with - is refused, so it can never reach git as an option or as 
STOP C6: the diff could not be made (see above). Next: do not write the release line; send /q/r4/_local/scratch/lead-plan-work/out-c6.txt to the builder.
rc=1
ls: cannot access '$S/qroot/r4/_local/scratch/lead-plan-work/proof-c6.txt': No such file or directory
```

## neg3.txt
```
##### N20 OLD empty (no value)
--- b32
STOP C5: OLD is [], not 7 to 40 lowercase hex characters (a commit sha). An empty value, a name such as HEAD or a value that starts with - is refused, so it can never reach git as an option or as a na
rc=1
##### N21 A3 and A4 with no patch program on PATH (fresh root)
--- b03
ok A1: made /q/r6/_local/scratch/lead-plan-work
rc=0
--- b04
ok original checksum
ok original no CR
ok A2: every file checked, proof file written
rc=0
--- b05
STOP A3: the program patch is not installed (command -v patch finds nothing in this shell). Next: nothing was changed. Install patch (Git for Windows has it under usr/bin; check PATH), open a new Git Bash window, set the variables, run this block again. There is no git apply fallback any more.
rc=1
--- b06
STOP A4: the plan in the work folder does not start from the checksum this step expects (it is 67a0a195537de875). If you are repeating a step you already did, go to A6: it names the state. Next: nothing was changed; move aside and start at A1 only if A6 also says STOP.
rc=1
```

## neg4.txt
```
##### A2: a file of PC is a symlink (copy folder ch2)
STOP A2: acc5.sh in /q/ch2/paste-check is a symbolic link. Next: get the file again as a plain file from the repository (section 0b).
A2 is not clean: A3 to A5b4 refuse to run until it is.
rc=1
##### A2 after: restore for r7
ok A2: every file checked, proof file written
rc=0
##### A8 repeat (PF equals PT)
--- b12
ok A8 (PF already equals the untouched patched plan; nothing changed): go on to A9
rc=0
##### A8 PF differs
--- b12
STOP A8: PF exists and differs from the patched plan: it holds your edits. Next: do not copy over it. If the line below shows run lines, a run has begun: do NOT touch PF, tell the builder. Otherwise, only if you want to redo all e
rc=1
##### A8 PF symlink
--- b12
STOP PF: PF (/q/r7/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md) is a symbolic link. Next: tell the builder; aside "$PF" and run A8 again.
rc=1
##### A8 stray .orig
--- b12
STOP A5c: a .orig or .rej file is in /q/r7/_local/scratch/lead-plan-work/inputs; A8 refuses. Next: aside "/q/r7/_local/scratch/lead-plan-work", start at A1.
rc=1
##### A8 with PF missing: copy
--- b12
ok A8 copied
rc=0
same
##### C2 BR=-x
--- b18
STOP C2: BR has unsafe characters, starts with -, or is empty. Next: write BR in section 1.
rc=1
##### C2 BR=take/nlite-int-r5 PIN ok -> ok; then C2 repeat
ok C2
rc=0
ok C2
rc=0
##### C2 FINAL5=no
--- b18
STOP C2: FINAL5 or NAMES_OK is not yes: nothing changed. Next: wait for the round-5 builder's final message in the channel, then write both in section 1.
rc=1
##### C2 PIN=HEAD
--- b18
STOP C2: PIN is not 40 hex characters. Next: write PIN in section 1.
rc=1
##### C2 PIN=-h
--- b18
STOP C2: PIN is not 40 hex characters. Next: write PIN in section 1.
rc=1
##### C2 PF missing
--- b18
STOP PF: the plan file PF (/q/r7/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md) does not exist or is a symbolic link (a link could send a change to another file). Next: do A8 (copy the patched plan); if PF is a link, te
rc=1
```

## neg5.txt
```
##### P-4b.sh save: first (exists?)
--- b20
syntax ok
CR count: 0 (must be 0)
non-ASCII bytes: 0 (must be 0)
word scan:
(end: nothing above is right)
rc=0
##### P-4b.sh save again (refuses)
--- b20
STOP C2b: /q/r7/_local/scratch/wp6-smoke/pastes/P-4b.sh already exists (a file you may have changed). Next: keep it and go to step (3); or, to start from the proposal again: aside "/q/r7/_local/scratch/wp6-smoke/pastes/P-4b.sh" and run this
rc=1
##### C2b step 2 with banned word in the fill list copy
--- b20
syntax ok
CR count: 0 (must be 0)
non-ASCII bytes: 0 (must be 0)
word scan:
6:# a kill word
(end: nothing above is right)
STOP C2b: the word kill or env.sh is in P-4b.sh (lines above). Next: aside "/q/r7/_local/scratch/wp6-smoke/pastes/P-4b.sh" and run this block again; tell the builder.
rc=0
##### SP note: normal, symlink, immutable
--- sp.sh
NOTE lead stand-in pid=777 2026-11-16T12:41Z
rc=0
--- sp.sh
STOP LINK: /q/r7/egm/duplicate-proof-lead-desk/wp6/evidence-2/PROGRESS.md is a symbolic link or not a plain file. Next: write nothing; tell the builder.
rc=1
outside: orig
--- sp.sh
$S/h/blk.23904/x.sh: line 1: /q/r7/egm/duplicate-proof-lead-desk/wp6/evidence-2/PROGRESS.md: Operation not permitted
STOP C2b: the note could not be written (read-only file?). Next: nothing was noted; tell the builder.
rc=1
##### SP not digits
--- sp0.sh
STOP C2b: SP must be digits. Next: write the pid printed by WSL-2 and run again.
rc=1
##### D1: PROGRESS symlink
--- d1.sh
STOP LINK: PROGRESS.md is a symbolic link or not a plain file: nothing is written through it. Next: write nothing; tell the builder.
rc=1
##### D1: normal
--- d1.sh
NEED-LEAD R2 pid=555 t
LEAD-YES R2 pid=555 2026-11-16T12:41Z
rc=0
--- D1 again (second LEAD-YES refused)
--- d1.sh
STOP D1: a LEAD-YES line for pid 555 is already there. Next: tell the builder.
rc=1
##### D1: immutable
--- d1.sh
$S/h/blk.24004/x.sh: line 1: /q/r7/egm/duplicate-proof-lead-desk/wp6/evidence-2/PROGRESS.md: Operation not permitted
STOP D1: the line could not be written (read-only file?). Next: no permission was given; tell the builder.
rc=1
##### D1: kill exit=3 line
--- d1.sh
STOP D1: a kill exit=3 line exists: no R2 is allowed after exit 3. Next: write nothing, tell the builder; the plan (S13, 13.4 and 13.5) goes on by itself.
rc=1
##### C3b: no runner line, then lines
--- b29
runner lines in PROGRESS.md: 0 (must be 1 or more)
NOTE lead x
STOP C3b: no runner line in PROGRESS.md. Next: ask the runner (see below).
strings.txt exists
rc=1
--- b29
runner lines in PROGRESS.md: 1 (must be 1 or more)
NOTE lead x
P-3a done t
strings.txt exists
rc=0
##### C3b: strings.txt missing
--- b29
runner lines in PROGRESS.md: 1 (must be 1 or more)
NOTE lead x
P-3a done t
STOP C3b: strings.txt is missing. Next: ask the runner (see below).
rc=1
```

## neg6.txt
```
##### C2b step 2 banned word
--- b20
syntax ok
CR count: 0 (must be 0)
non-ASCII bytes: 0 (must be 0)
word scan:
6:# a kill word
(end: nothing above is right)
STOP C2b: the word kill or env.sh is in P-4b.sh (lines above). Next: aside "/q/r7/_local/scratch/wp6-smoke/pastes/P-4b.sh" and run this block again; tell the builder.
rc=1
##### step 2 normal
--- b20
syntax ok
CR count: 0 (must be 0)
non-ASCII bytes: 0 (must be 0)
word scan:
(end: nothing above is right)
rc=0
##### step 2 list file without 'exit 0' end
ln: '/dev/null' and '/dev/null' are the same file
--- b20
/q/r7/_local/scratch/wp6-smoke/pastes/P-4b.sh: line 29: unexpected EOF while looking for matching ``'
STOP C2b: the saved P-4b.sh does not end with the line exit 0 (the list file is damaged, for example by CR). Next: run A2; then aside "/q/r7/_local/scratch/wp6-smoke/pastes/P-4b.sh" and run this block
rc=1
```

## neg7.txt
```
##### WSL-3 real P-4b.sh as root (no hit expected)
--- b24
exit=0
STOP C2b: the exit code is not 0, or there is no hit line (the stand-in was not seen), or an output line has the wrong shape. Next: tell the builder; paste the lines printed here:
rc=1
##### WSL-3 stub P-4b.sh with a hit
--- b24
exit=0
P-4b.sh sha256 4843532b8e2a365cdafdcb82211bcbd012e90b3e201139582d60d4cd531ec967
P-4b-HIT pid=99
rc=0
P-4b.sh sha256 4843532b8e2a365cdafdcb82211bcbd012e90b3e20113
P-4b-HIT pid=99
##### WSL-3 control file is a symlink
--- b24
STOP LINK: P-4b.sh or P-4b.control.txt is a symbolic link. Next: write nothing; tell the builder.
rc=1
##### WSL-4 normal
--- b26
gone
rc=0
gone control=f330935816f6366a
##### WSL-4 standin-gone.txt symlink
--- b26
STOP LINK: P-4b.control.txt or standin-gone.txt is a symbolic link. Next: write nothing; tell the builder.
rc=1
##### WSL-4 control missing
--- b26
STOP C2b: P-4b.control.txt is missing or empty. Next: run WSL-3 first (a stand-in you started ends by itself after 10 minutes, or end it with kill "" if SPID is set in this window).
rc=1
##### WSL-1 wrong folder
--- b22
$S/h/blk.25919/x.sh: line 1: cd: /q/nowhere/_local/scratch/wp6-smoke/pastes: No such file or directory
STOP C2b: wrong folder, root user, or dash -n failed. Next: fix it (HBW line, user, P-4b.sh), run WSL-1 again.
rc=1
```

## neg8.txt
```
##### A6 CHAIN=3 on chain-2 plan
--- b10
ok A6 counts 24 10 2 1
STOP A6: the plan checksum is 39af84aec78b650f, not the one of CHAIN=3 (515cf4704ebba5bd). Next: repeat the chain step blocks of A3 to A5b4 for your CHAIN (finished ones print ok already); if one prints STOP, follow it.
rc=1
##### A7 CHAIN=4
586:LEAD-FILL 1
STOP A7: marker lines are 2,3,4,125,258,275,433,434,585,586, expected 2,3,4,137,270,287,509,510,774,775. Next: tell the builder.
rc=1
##### A5c with .orig
--- b09
plan-wp6-resmoke-v5.md
y.rej
STOP A5c: a .orig or .rej file is there. Next: aside "/q/r7/_local/scratch/lead-plan-work", start at A1.
rc=1
##### A6 CHAIN empty
--- b10
STOP CHAIN: CHAIN is ''. Next: decide 2, 3 or 4 in A0, write it in section 1, set the variables again.
rc=1
##### C6 acc5 prints STOP
--- b33
STOP C5: the old commit eec6ba4 is neither in /q/r7/_local/scratch/wt/nlite-fix5 nor in the round-3 worktree /q/r7/_local/scratch/wt/nlite-fix3. Next: check W3N and OLD against line 3 of the plan; tel
STOP C6: the diff could not be made (see above). Next: do not write the release line; send /q/r7/_local/scratch/lead-plan-work/out-c6.txt to the builder.
rc=1
ls: cannot access '/tmp/claude-0/-home-user/957f9d59-4d7f-59
##### C8 with a different confirmed branch name
STOP C8: the plan still names its guess take/nlite-int-r5 in 9 places, but you confirmed take/nlite-int-r6. Next: edit those places in PF to take/nlite-int-r6, then C7 and C8 again.
STOP C8: the confirmed name take/nlite-int-r6 is not in PF. Next: do C2 and C7, then C8 again.
STOP C8: see the lines above. Next: fix them, then C7 and C8 again.
rc=1
ls: cannot access '/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e8
##### D1a D2(1) D2(2) D2(2b) D2-check D2-delete in a non-WSL shell
--- b38
STOP D1: this is not the WSL Ubuntu shell (no 'microsoft' in /proc/version). Next: run D1a in the WSL window.
rc=1
--- b40
STOP D2: this is not the WSL Ubuntu shell, or EV/p.log does not exist. Next: run it in the WSL window with HBW and EV set (D2 text above).
rc=1
--- b41
STOP D2: HITPID must be digits. Next: write the pid of one P-4b-HIT line.
rc=1
--- b42
rc=0
--- b43
STOP D2: this is not the WSL Ubuntu shell. Next: run it in the WSL window. Nothing was scanned.
rc=1
--- b44
STOP D2: this is not the WSL Ubuntu shell (no microsoft in /proc/version). Next: run it in the WSL window. Nothing was scanned or deleted.
rc=1
##### B1 accept 3 4 8 then accept 5 then accept 1
rc=0
STOP B1: question 5 is answered only by its own block (5 and 7 by C2, 9 by A9). Next: do that block. Nothing changed.
rc=1
STOP B1: unknown question '99'. Next: use only 3 4 8 (2, 1, 1b, 6 after their own checks); check the number you typed. Nothing changed.
rc=1
##### A1 with HB not a folder (STOP VARS)
```

## neg9.txt
```
##### C6 acc5 prints STOP (fake acc5 in copy folder)
--- b33
STOP (fake)
STOP C6: STOP (fake). Next: do not write the release line; send /q/r7/_local/scratch/lead-plan-work/out-c6.txt and this line to the builder and wait.
---- the n8n_kill.py part, read it:
== n8n_kill.py
-    sys.exit(0)
+    print("refused: unreadable")
+    sys.exit(3)
== end
rc=1
ls: cannot access '/tmp/claude-0/-home-u
##### C6 with the real acc5 (ACCEPT) leaves proof
--- b33
ACCEPT
/tmp/claude-0/-home-
##### A1 with HB that does not exist (STOP VARS)
--- b03
STOP VARS: HB ('/q/nonexist') is not a folder here (wrong shell? use Git Bash only; or the variables are not set). Next: write HB and CH in section 1 and set the variables again. Nothing was written.
rc=1
##### A2 without work folder
--- b04
STOP A2: the work folder does not exist. Next: do A1 first.
rc=1
##### acc5.sh fed the three forms of observation 2 and the plan-exact one
print("exit 3") -> ACCEPT
EXIT 3 -> ACCEPT
os._exit(3) -> ACCEPT
sys.exit(3) -> ACCEPT
case: comment return 3 only -> STOP (no exit 3 or return 3 in kill block)
cases ok=18 bad=0
STOP (block missing)
(above: no == end line, expect STOP (block missing))
```
