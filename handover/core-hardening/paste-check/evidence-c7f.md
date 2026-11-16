# evidence-c7f (raw, 2026-11-16). Evidence runner output, no verdicts. Builder tests on this Linux container only (plain bash and dash; not Git Bash, not PowerShell, not WSL). Scratch plan copies lived in paste-check/scratch-v5/ (deleted afterwards); stub folders live in the session scratchpad.
## 0 start: sha256 of the three patches and of the real inputs plan (the real inputs file is never edited)
9e8d06ddb5bb5b57  plan-v5-fixes.patch
f65f2dbae2e50775  plan-v5-repin-v4.patch
8a142d2e062d10bc  plan-v5-repin-v5.patch
67a0a195537de875
## 1 apply order (patch -p1 from core-hardening/ on a pristine copy of inputs/plan-wp6-resmoke-v5.md)
$ patch -p1 --dry-run < plan-v5-fixes.patch
checking file inputs/plan-wp6-resmoke-v5.md
rc=0
$ patch -p1 < plan-v5-fixes.patch
patching file inputs/plan-wp6-resmoke-v5.md
rc=0
$ patch -p1 --dry-run < plan-v5-repin-v5.patch
checking file inputs/plan-wp6-resmoke-v5.md
rc=0
$ patch -p1 < plan-v5-repin-v5.patch
patching file inputs/plan-wp6-resmoke-v5.md
rc=0
$ cmp result vs build copy
cmp rc=0
$ residue (.orig/.rej)
plan-wp6-resmoke-v5.md
$ re-extract spans from the final patched plan
ex rc=0
$ order check 1: v5 dry-run on the ORIGINAL plan (fixes not applied), expected to fail
Hunk #15 FAILED at 561.
5 out of 15 hunks FAILED
rc=1
$ order check 2: v5 dry-run on fixes + v4 (v4 already applied), expected to fail
Hunk #15 FAILED at 556.
15 out of 15 hunks FAILED
rc=1
$ real inputs file untouched (sha256 first 16, must equal the line in section 0)
67a0a195537de875
## 2 leftover-marker counts on the patched plan (grep -c counts LINES)
FINAL lines (expect 24): 24
LEAD-FILL lines (plan says 10): 10
control lines (expect 2): 2
$ marker places
2:LEAD-FILL 7 3:LEAD-FILL 5 3:LEAD-FILL 6 3:LEAD-FILL 9 3:LEAD-FILL 7 4:LEAD-FILL 8 4:LEAD-FILL 3 123:LEAD-FILL 4 256:LEAD-FILL 1 256:LEAD-FILL 1b 256:LEAD-FILL 2 256:LEAD-FILL 1b 273:LEAD-FILL 6 431:LEAD-FILL 4 432:LEAD-FILL 4 583:LEAD-FILL 7 584:LEAD-FILL 1
marker texts: 17
$ lines of each pattern (Grep-tool style)
2 134 249 534 536 537 538 539 540 541 542 543 544 545 546 547 548 549 550 551 552 553 554 555
2 3 4 123 256 273 431 432 583 584
2:**HEAD_PIN = <FINAL-SH
249:$HEAD_PIN = '<FINAL-
$ simulated fill and flip: must go to 0, 0, control still 2
0
0
2
$ partial flip, all markers except 1b
256:LEAD-FILL 1b
256:LEAD-FILL 1b
1
$ last-check command as printed (PF swapped): patched plan | filled+flipped copy | wrong path | copy without HEAD_PIN lines
24 10 2
0 0 2
grep: /nonexistent/x.md: No such file or directory grep: /nonexistent/x.md: No such file or directory grep: /nonexistent/x.md: No such file or directory
0 0 0
$ names check as printed (PF swapped)
2:nlite-fix5 2:nlite-int-r5 2:nlite-fix5 2:nlite-int-r5 3:nlite-fix5 3:nlite-fix5 3:nlite-fix5 3:nlite-fix5 3:nlite-fix5 3:nlite-int-r5 77:nlite-fix5 77:nlite-int-r5 134:nlite-fix5 249:nlite-fix5 510:nlite-fix5 532:nlite-fix5 532:nlite-int-r5 580:nlite-fix5 580:nlite-int-r5 583:nlite-fix5 583:nlite-int-r5 585:nlite-fix5
$ line numbers of the sections named in the names check list (nlite-fix5 lines -> section heading above)
2 -> |3 -> |77 -> ## COULD NOT RESOLVE without a|134 -> ## 2. Pinned values|249 -> ## 4. Steps|510 -> ## 8. MUST-NOT (run)|532 -> ## 11. Quoted strings and thei|580 -> ## UNVERIFIED in this plan (re|583 -> ## UNVERIFIED in this plan (re|585 -> ## UNVERIFIED in this plan (re
## 3 syntax (bash -n and dash -n)
$ fenced blocks of the patched plan (blocks.py of c7e, sh/bash blocks only; powershell and python blocks not checked)
fenced blocks total: 15 langs: ['bash', 'powershell', 'python', 'sh']
line 111 lang=sh lines=9: bash -n rc=0; dash -n rc=0
line 147 lang=sh lines=28: bash -n rc=0; dash -n rc=0
line 180 lang=sh lines=5: bash -n rc=0; dash -n rc=0
line 189 lang=sh lines=13: bash -n rc=0; dash -n rc=0
line 228 lang=bash lines=5: bash -n rc=0; dash -n rc=0
line 263 lang=sh lines=8: bash -n rc=0; dash -n rc=0
line 300 lang=sh lines=2: bash -n rc=0; dash -n rc=0
line 306 lang=sh lines=5: bash -n rc=0; dash -n rc=0
line 346 lang=sh lines=1: bash -n rc=0; dash -n rc=0
line 367 lang=sh lines=4: bash -n rc=0; dash -n rc=0
line 375 lang=sh lines=15: bash -n rc=0; dash -n rc=0
line 400 lang=sh lines=15: bash -n rc=0; dash -n rc=0
line 434 lang=sh lines=1: bash -n rc=0; dash -n rc=0
$ new or changed command spans extracted from the patched plan (P-3b, fill, diff command, last check, names check, R2.sh block, gone)
P-3b: bash -n rc=0 dash -n rc=0
fill: bash -n rc=0 dash -n rc=0
diff: bash -n rc=0 dash -n rc=0
last: bash -n rc=0 dash -n rc=0
names: bash -n rc=0 dash -n rc=0
R2: bash -n rc=0 dash -n rc=0
gone: bash -n rc=0 dash -n rc=0
$ inline-span extractor of c3 (extract_spans.py, S13 line number made a variable): rows failing bash -n or dash -n raw, and after placeholders are replaced, old v4 plan vs new plan
after-v4: spans 252; raw fail 29; fail after placeholders 4
work: spans 289; raw fail 30; fail after placeholders 4
## 4 fill command against stub git repos (round-5 stub repo g; strings.txt stub with 5 rows)
--- fill, PIN = PIN empty
head=aa965c8f00bf4c81ba5f20f44316f81608b8d560 seven=aa965c8 branch=master
PIN empty: first run, read only
--- fill, PIN = full HEAD
head=aa965c8f00bf4c81ba5f20f44316f81608b8d560 seven=aa965c8 branch=master
S1 n8n_start.sh 3
K4 n8n_kill.py 1
H1 run_real_check_n8n.py FILE-MISSING
H2 other.py 1
X1 n8n_kill.py 
--- fill, PIN = parent (head differs)
head=aa965c8f00bf4c81ba5f20f44316f81608b8d560 seven=aa965c8 branch=master
MISMATCH: head differs from PIN, the lines below are read at PIN
S1 n8n_start.sh 2
K4 n8n_kill.py 
H1 run_real_check_n8n.py FILE-MISSING
H2 other.py FILE-MISSING
X1 n8n_kill.py 
--- fill, PIN = 7 characters
head=aa965c8f00bf4c81ba5f20f44316f81608b8d560 seven=aa965c8 branch=master
PIN is not the full 40-character sha of a commit in this worktree: STOP
--- fill, PIN = garbage
head=aa965c8f00bf4c81ba5f20f44316f81608b8d560 seven=aa965c8 branch=master
PIN is not the full 40-character sha of a commit in this worktree: STOP
--- fill, no strings.txt
head=aa965c8f00bf4c81ba5f20f44316f81608b8d560 seven=aa965c8 branch=master
strings.txt not written yet (run this paste again after P-3a)
--- fill, CRLF
head=aa965c8f00bf4c81ba5f20f44316f81608b8d560 seven=aa965c8 branch=master
strings.txt holds a CR (CRLF): STOP
--- fill, last row without newline
head=aa965c8f00bf4c81ba5f20f44316f81608b8d560 seven=aa965c8 branch=master
K4 n8n_kill.py 1
## 5 wording-diff command and acceptance rule (stub round-3 repo wt3, stub round-5 repo g; eec6ba4 replaced by the stub sha)
--- known case, PIN=''
PIN empty: STOP
== end
STOP (block missing)
--- known case, PIN='aa965c8'
known
== n8n_start.sh
== n8n_kill.py
-print("confirmed gone")
+print("), confirmed gone")
+sys.exit(3)
== end
ACCEPT
--- unknown case (round-3 commit not in WT, temp files)
unknown
== n8n_start.sh
== n8n_kill.py
-print("confirmed gone")
+print("), confirmed gone")
+sys.exit(3)
== end
ACCEPT
--- acceptance rule on made-up outputs (rule implemented in acc5.sh)
case: good
ACCEPT
case: exit 30 only
STOP (other exit text: +sys.exit(30)|)
case: main() plus 3
STOP (other exit text: +sys.exit(main())|)
case: exit 3 only in the start.sh block
STOP (no exit 3 in kill block)
case: no exit 3
STOP (no exit 3 in kill block)
case: exit 4 with 3
STOP (other exit text: +sys.exit(4)|)
case: named constant
STOP (other exit text: +EXIT_CODE = 3|)
case: exit 20 in start
STOP (other exit text: + exit 20|)
STOP (block missing)
(above: no == end line)
## 6 P-3b span (extracted from the patched plan, cd line swapped to a stub folder)
--- A good (expect: -- scan, scan exit=1, -- p4b words, p4b words exit=1, compile exit=0, syntax end, P-4b files ok, strings bad lines: 0, strings lines: 20)
   -- scan
   scan exit=1
   -- p4b words
   p4b words exit=1
   compile exit=0
   syntax end
   P-4b files ok
   strings bad lines: 0
   strings lines: 20
--- B CR in P-4b.sh
   -- scan
   pastes/P-4b.sh:1:#!/bin/bash^M
   pastes/P-4b.sh:2:exit 0^M
   scan exit=0
   -- p4b words
   p4b words exit=1
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
   -- p4b words
   p4b words exit=1
   compile exit=0
   syntax end
   P-4b files STOP
   strings bad lines: 0
   strings lines: 20
--- D P-4b.sh missing
   -- scan
   scan exit=1
   -- p4b words
   grep: pastes/P-4b.sh: No such file or directory
   p4b words exit=2
   compile exit=0
   syntax end
   P-4b files STOP
   strings bad lines: 0
   strings lines: 20
--- E control missing
   -- scan
   grep: pastes/P-4b.control.txt: No such file or directory
   scan exit=2
   -- p4b words
   p4b words exit=1
   compile exit=0
   syntax end
   P-4b files STOP
   strings bad lines: 0
   strings lines: 20
--- G wrong hash
   -- scan
   scan exit=1
   -- p4b words
   p4b words exit=1
   compile exit=0
   syntax end
   P-4b files STOP
   strings bad lines: 0
   strings lines: 20
--- H hash inside a longer first line
   -- scan
   scan exit=1
   -- p4b words
   p4b words exit=1
   compile exit=0
   syntax end
   P-4b files STOP
   strings bad lines: 0
   strings lines: 20
--- I later control line has the wrong shape
   -- scan
   scan exit=1
   -- p4b words
   p4b words exit=1
   compile exit=0
   syntax end
   P-4b files STOP
   strings bad lines: 0
   strings lines: 20
--- J control holds the hash line only
   -- scan
   scan exit=1
   -- p4b words
   p4b words exit=1
   compile exit=0
   syntax end
   P-4b files STOP
   strings bad lines: 0
   strings lines: 20
--- K comment-only P-4b.sh with matching control
   -- scan
   scan exit=1
   -- p4b words
   p4b words exit=1
   compile exit=0
   syntax end
   P-4b files STOP
   strings bad lines: 0
   strings lines: 20
--- L bad strings line
   -- scan
   scan exit=1
   -- p4b words
   p4b words exit=1
   compile exit=0
   syntax end
   P-4b files ok
   strings bad lines: 1
   strings lines: 21
--- N non-ASCII byte in another file
   -- scan
   env-resmoke.sh:1:cafM-CM-)
   scan exit=0
   -- p4b words
   p4b words exit=1
   compile exit=0
   syntax end
   P-4b files ok
   strings bad lines: 0
   strings lines: 20
--- O shell syntax error in a paste
   -- scan
   scan exit=1
   -- p4b words
   p4b words exit=1
   compile exit=0
   pastes/P-1.sh: line 1: syntax error near unexpected token `then'
   pastes/P-1.sh: line 1: `if then'
   syntax: pastes/P-1.sh
   syntax end
   P-4b files ok
   strings bad lines: 0
   strings lines: 20
--- P word kill in a comment of P-4b.sh, control re-made (word scan must show it)
   -- scan
   scan exit=1
   -- p4b words
   2:# never kills
   p4b words exit=0
   compile exit=0
   syntax end
   P-4b files ok
   strings bad lines: 0
   strings lines: 20
--- Q word env.sh in P-4b.sh, control re-made
   -- scan
   scan exit=1
   -- p4b words
   2:. env.sh
   p4b words exit=0
   compile exit=0
   syntax end
   P-4b files ok
   strings bad lines: 0
   strings lines: 20
--- R R2.sh present (new paste) is syntax checked
   -- scan
   scan exit=1
   -- p4b words
   p4b words exit=1
   compile exit=0
   syntax end
   P-4b files ok
   strings bad lines: 0
   strings lines: 20
## 7 R2.sh block (extracted from the patched plan) with stand-in processes (python, own session, N8N_USER_FOLDER in their environment); HOME swapped to a test folder
--- valid: take pid, which=take
R2 end: alive=no
[exit=0]
stand-in 10617 gone
--- ctl pid but which=take (environ names the other folder)
R2: environ of pid 10726 does not name HOME/hadavin-smoke/take-smoke-1/n8n: STOP, nothing sent
[exit=1]
stand-in 10726 alive
--- pid not alive
R2: pid 999999 is not alive: nothing sent
[exit=0]
--- bad pid values (abc, 1, empty)
R2: bad pid: STOP
[exit=1]
R2: bad pid: STOP
[exit=1]
R2: bad pid: STOP
[exit=1]
--- bad which
R2: which must be take or ctl: STOP
[exit=1]
--- ctl pid, which=ctl
R2 end: alive=no
[exit=0]
stand-in 10726 gone
--- pid that ignores TERM: KILL after 30 s
R2: KILL sent after 30s
R2 end: alive=no
[exit=0]
stand-in 10780 gone
stand-in processes left: 0
## 8 gone() (extracted from the patched plan) with a fake n8n_kill.py; ss is not installed here, so the port-wait loop sees no listener
--- fake exit 0, confirmed gone printed: yes
), confirmed gone
kill exit=0
ports free after 0s; groups of 99999 left: 0
GONE-OK
gone-rc=0
--- fake exit 3, confirmed gone printed: yes
), confirmed gone
kill exit=3
ports free after 0s; groups of 99999 left: 0
GONE-FAIL: kill exit=3, expected 0 only (3 = an unreadable n8n-shaped process of this user exists, per lead): STOP (R1: no fallback kill)
gone-rc=1
--- fake exit 1, confirmed gone printed: yes
), confirmed gone
kill exit=1
ports free after 0s; groups of 99999 left: 0
GONE-FAIL: kill exit=1, expected 0 only (3 = an unreadable n8n-shaped process of this user exists, per lead): STOP (R1: no fallback kill)
gone-rc=1
--- fake exit 2, confirmed gone printed: yes
), confirmed gone
kill exit=2
ports free after 0s; groups of 99999 left: 0
GONE-FAIL: kill exit=2, expected 0 only (3 = an unreadable n8n-shaped process of this user exists, per lead): STOP (R1: no fallback kill)
gone-rc=1
--- fake exit 0, confirmed gone printed: no

kill exit=0
ports free after 0s; groups of 99999 left: 0
GONE-FAIL: STOP (R1: no fallback kill)
gone-rc=1
## 9 P-4b proposal (LEAD-FILL-list-v5.md) end to end; stand-in as uid 65534, environ unreadable
bash -n rc=0
dash -n rc=0
word scan exit=1
--- negative control (no stand-in), as uid 65534
exit=0
--- positive control
P-4b-HIT pid=<digits>
exit=0
stand-in left: 0
--- P-3b on this folder
-- scan
scan exit=1
-- p4b words
p4b words exit=1
compile exit=0
syntax end
P-4b files ok
strings bad lines: 0
strings lines: 20
## 10 banned-word scan of the new files (list read from tests/test_no_reference_material.py; the words are not printed)
plan-v5-repin-v5.patch 0 hits
LEAD-FILL-list-v5.md 0 hits
REPORT-repin-v5.md 0 hits
checkpoint-v5.md 0 hits
FINDING-MAP-v5.md absent
