# FAILED / NOT RUN (raw evidence has no verdicts; read REPORT-repin-v6.md section 1 first): nothing ran on Git Bash, PowerShell, WSL, n8n or Docker; `ss` missing here; WSL kernel not tested; negative control 4 of section 9 is weak (root).
# evidence-c7g (raw, 2026-11-16). Evidence runner output, no verdicts. Builder tests on this Linux container only (plain bash and dash; not Git Bash, not PowerShell, not WSL). Scratch plan copies lived in the session scratchpad; stub folders live in the session scratchpad.
## 0 start: sha256 of the three patches and of the real inputs plan (the real inputs file is never edited)
9e8d06ddb5bb5b57  plan-v5-fixes.patch
8a142d2e062d10bc  plan-v5-repin-v5.patch
bedcad9fbdc4422a  plan-v5-repin-v6.patch
67a0a195537de875
## 1 apply order (patch -p1 from core-hardening/ on a pristine copy of inputs/plan-wp6-resmoke-v5.md)
$ patch -p1 --dry-run < plan-v5-fixes.patch
checking file inputs/plan-wp6-resmoke-v5.md
rc=0
$ patch -p1 < plan-v5-fixes.patch
patching file inputs/plan-wp6-resmoke-v5.md
rc=0
$ patch -p1 --dry-run < plan-v5-repin-v6.patch
checking file inputs/plan-wp6-resmoke-v5.md
rc=0
$ patch -p1 < plan-v5-repin-v6.patch
patching file inputs/plan-wp6-resmoke-v5.md
rc=0
$ cmp result vs build copy
cmp rc=0
$ residue (.orig/.rej)
plan-wp6-resmoke-v5.md
$ re-extract spans from the final patched plan
ex rc=0
$ order check 1: v6 dry-run on the ORIGINAL plan (fixes not applied), expected to fail
Hunk #15 FAILED at 561.
5 out of 15 hunks FAILED
rc=1
$ order check 2: v6 dry-run on fixes + the v5 patch (v5 already applied), expected to fail
Hunk #15 FAILED at 556.
15 out of 15 hunks FAILED
rc=1
$ real inputs file untouched (sha256 first 16, must equal the line in section 0)
67a0a195537de875
## 2 leftover-marker counts on the patched plan (grep -c counts LINES)
FINAL lines (expect 24): 24
LEAD-FILL lines (plan says 10): 10
control lines (expect 2): 2
patch-marker lines (expect 1): 1
$ marker places
2:LEAD-FILL 7 3:LEAD-FILL 5 3:LEAD-FILL 6 3:LEAD-FILL 9 3:LEAD-FILL 7 4:LEAD-FILL 8 4:LEAD-FILL 3 125:LEAD-FILL 4 258:LEAD-FILL 1 258:LEAD-FILL 1b 258:LEAD-FILL 2 258:LEAD-FILL 1b 275:LEAD-FILL 6 433:LEAD-FILL 4 434:LEAD-FILL 4 585:LEAD-FILL 7 586:LEAD-FILL 1
marker texts: 17
$ lines of each pattern (Grep-tool style)
2 136 251 536 538 539 540 541 542 543 544 545 546 547 548 549 550 551 552 553 554 555 556 557
2 3 4 125 258 275 433 434 585 586
2:**HEAD_PIN = <FINAL-SH
251:$HEAD_PIN = '<FINAL-
$ simulated fill and flip: must go to 0, 0, control still 2
0
0
2
1
$ partial flip, all markers except 1b
258:LEAD-FILL 1b
258:LEAD-FILL 1b
1
$ last-check command as printed (PF swapped): patched plan | filled+flipped copy | wrong path | copy without HEAD_PIN lines | UNPATCHED plan (fixes patch only; the v5 last check would print 0 0 2 here)
24 10 2 1
0 0 2 1
grep: /nonexistent/x.md: No such file or directory grep: /nonexistent/x.md: No such file or directory grep: /nonexistent/x.md: No such file or directory grep: /nonexistent/x.md: No such file or directory
0 0 0 1
0 0 2 0
$ same, with the v5 last check (3 commands only) on the unpatched plan, to show what the old check could not see
0 0 2
$ names check as printed (PF swapped)
2:nlite-fix5 2:nlite-int-r5 2:nlite-fix5 2:nlite-int-r5 3:nlite-fix5 3:nlite-fix5 3:nlite-fix5 3:nlite-fix5 3:nlite-fix5 3:nlite-int-r5 77:nlite-fix5 77:nlite-int-r5 136:nlite-fix5 251:nlite-fix5 512:nlite-fix5 534:nlite-fix5 534:nlite-int-r5 582:nlite-fix5 582:nlite-int-r5 585:nlite-fix5 585:nlite-int-r5 587:nlite-fix5
$ line numbers of the sections named in the names check list (nlite-fix5 lines -> section heading above)
2 -> |3 -> |77 -> ## COULD NOT RESOLVE without a|136 -> ## 2. Pinned values|251 -> ## 4. Steps|512 -> ## 8. MUST-NOT (run)|534 -> ## 11. Quoted strings and thei|582 -> ## UNVERIFIED in this plan (re|585 -> ## UNVERIFIED in this plan (re|587 -> ## UNVERIFIED in this plan (re
## 3 syntax (bash -n and dash -n)
$ fenced blocks of the patched plan (blocks.py of c7e, sh/bash blocks only; powershell and python blocks not checked)
fenced blocks total: 15 langs: ['bash', 'powershell', 'python', 'sh']
line 111 lang=sh lines=11: bash -n rc=0; dash -n rc=0
line 149 lang=sh lines=28: bash -n rc=0; dash -n rc=0
line 182 lang=sh lines=5: bash -n rc=0; dash -n rc=0
line 191 lang=sh lines=13: bash -n rc=0; dash -n rc=0
line 230 lang=bash lines=5: bash -n rc=0; dash -n rc=0
line 265 lang=sh lines=8: bash -n rc=0; dash -n rc=0
line 302 lang=sh lines=2: bash -n rc=0; dash -n rc=0
line 308 lang=sh lines=5: bash -n rc=0; dash -n rc=0
line 348 lang=sh lines=1: bash -n rc=0; dash -n rc=0
line 369 lang=sh lines=4: bash -n rc=0; dash -n rc=0
line 377 lang=sh lines=15: bash -n rc=0; dash -n rc=0
line 402 lang=sh lines=15: bash -n rc=0; dash -n rc=0
line 436 lang=sh lines=1: bash -n rc=0; dash -n rc=0
$ new or changed command spans extracted from the patched plan (P-3b, fill, diff command, last check, names check, R2.sh block, gone)
P-3b: bash -n rc=0 dash -n rc=0
fill: bash -n rc=0 dash -n rc=0
diff: bash -n rc=0 dash -n rc=0
last: bash -n rc=0 dash -n rc=0
names: bash -n rc=0 dash -n rc=0
R2: bash -n rc=0 dash -n rc=0
gone: bash -n rc=0 dash -n rc=0
$ inline-span extractor of c3 (extract_spans.py, S13 line number made a variable): rows failing bash -n or dash -n raw, and after placeholders are replaced, old v4 plan vs new plan
after-v5: spans 289; raw fail 30; fail after placeholders 4
work: spans 290; raw fail 30; fail after placeholders 4
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
--- acceptance rule on made-up outputs (rule implemented in paste-check/acc5.sh)
case: good                                         -> ACCEPT
case: good with comment tail                       -> ACCEPT
case: exit 30 only                                 -> STOP (other exit text: +sys.exit(30)|)
case: exit 3x                                      -> STOP (other exit text: +sys.exit(3x)|)
case: upper case Exit(3)                           -> ACCEPT
case: main() plus exit 3                           -> ACCEPT
case: main() plus return 3 (stuck case, now ACCEPT) -> ACCEPT
case: main() alone                                 -> STOP (no exit 3 or return 3 in kill block)
case: return 31                                    -> STOP (no exit 3 or return 3 in kill block)
case: exit 3 only in the start.sh block            -> STOP (no exit 3 or return 3 in kill block)
case: no exit 3                                    -> STOP (no exit 3 or return 3 in kill block)
case: exit 4 with 3                                -> STOP (other exit text: +sys.exit(4)|)
case: named constant                               -> STOP (other exit text: +EXIT_CODE = 3|)
case: exit 20 in start                             -> STOP (other exit text: + exit 20|)
case: print("exit 3") (text only, ACCEPT, documented) -> ACCEPT
case: comment line only (stuck case: STOP)         -> STOP (no exit 3 or return 3 in kill block)
case: comment line plus exit 3                     -> ACCEPT
case: comment return 3 only                        -> STOP (no exit 3 or return 3 in kill block)
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
## 7 R2.sh block (extracted from the patched plan) with stand-in processes (python, own session, N8N_USER_FOLDER in their environment; some stand-ins keep a child in the same process group); HOME swapped to a test folder. NEW block first, then the v5 block on the same cases
=== NEW (v6)
--- A single process, TERM works
R2 end: alive=no group=0
[exit=0]
  group 10770 members left (not zombie): 0
--- B leader plus child, child ignores TERM, leader ends on TERM (old block: leader gone = alive=no)
R2: KILL sent after 30s
R2 end: alive=no group=0
[exit=0]
  group 10798 members left (not zombie): 0
--- C leader plus child, both end on TERM
R2 end: alive=no group=0
[exit=0]
  group 12017 members left (not zombie): 0
--- D leader already gone, child still alive
R2: pid 12132 is gone but 1 process(es) of its group are left: STOP, nothing sent (the environ of the leader cannot be checked), tell the lead
[exit=1]
  group 12132 members left (not zombie): 1
--- E pid not alive, group empty
R2: pid 999999 is not alive and its process group is empty: nothing sent
[exit=0]
--- D2 leader gone and reaped, child alive
R2: pid 12549 is gone but 1 process(es) of its group are left: STOP, nothing sent (the environ of the leader cannot be checked), tell the lead
[exit=1]
  group members left: 1
=== OLD (v5 block, extracted from the v5-patched plan)
--- A single process, TERM works
R2 end: alive=no
[exit=0]
  group 12879 members left (not zombie): 0
--- B leader plus child, child ignores TERM, leader ends on TERM (old block: leader gone = alive=no)
R2 end: alive=no
[exit=0]
  group 13220 members left (not zombie): 1
--- C leader plus child, both end on TERM
R2 end: alive=no
[exit=0]
  group 13318 members left (not zombie): 0
--- D leader already gone, child still alive
R2: pid 13390 is not alive: nothing sent
[exit=0]
  group 13390 members left (not zombie): 1
--- E pid not alive, group empty
R2: pid 999999 is not alive: nothing sent
[exit=0]
--- D2 leader gone and reaped, child alive
R2: pid 13733 is not alive: nothing sent
[exit=0]
  group members left: 1
--- remaining cases of the v5 test set on the NEW block (bad pid, bad which, wrong folder, ctl)
--- ctl pid but which=take
R2: environ of pid 14243 does not name HOME/hadavin-smoke/take-smoke-1/n8n: STOP, nothing sent
[exit=1]
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
R2 end: alive=no group=0
[exit=0]
--- pid that ignores TERM: KILL after 30 s
R2: KILL sent after 30s
R2 end: alive=no group=0
[exit=0]
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
## 9 P-4b proposal (LEAD-FILL-list-v5.md, v6 text with the status Uid filter, extracted from that file) end to end; stand-ins as uid 65534
bash -n rc=0
dash -n rc=0
word scan exit=1 (1 = nothing printed)
--- one-line test of the lead (LEAD-FILL list) as uid 65534, stand-in from the recipe
me=65534
65534 /proc/<pid>
0 /proc/<pid>/environ
status-uid=65534
bash: /proc/<pid>/environ: Permission denied
--- negative control (no stand-in), as uid 65534
exit=0
--- negative control 2: a READABLE n8n-shaped process of the same user (dumpable), as uid 65534: must print nothing
exit=0
--- negative control 3: an unreadable process of the same user whose command line has no n8n: must print nothing
exit=0
--- negative control 4: as root, with the unreadable stand-in of ANOTHER user (65534): must print nothing (not this user)
exit=0
--- positive control (recipe stand-in), as uid 65534
P-4b-HIT pid=17212
exit=0
--- control file made from that run (steps 3 and 4 of the recipe), then P-3b on this folder
P-4b.sh sha256 <hash>
P-4b-HIT pid=<n>
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
plan-v5-repin-v6.patch 0 hits
LEAD-FILL-list-v5.md 0 hits
LEAD-CHECKLIST-v5.md 0 hits
acc5.sh 0 hits
REPORT-repin-v5.md 0 hits
REPORT-repin-v6.md 0 hits
checkpoint-v6.md 0 hits
evidence-c7g.md: see section 12 (scan of the file before that section was added)
## 11 git apply fallback and checklist steps A1 to A6 (pristine copy, outside any git repository)
$ sha256 first 16 / CR count
67a0a195537de875
0
$ git apply -p1 --check < plan-v5-fixes.patch
rc=0
$ git apply -p1 < plan-v5-fixes.patch
rc=0
$ git apply -p1 --check < plan-v5-repin-v6.patch
rc=0
$ git apply -p1 < plan-v5-repin-v6.patch
rc=0
$ result of git apply equals the patch -p1 result (build copy C.md)
cmp rc=0
$ git apply in the WRONG order (v6 first) on a fresh copy
error: patch failed: inputs/plan-wp6-resmoke-v5.md:106
error: inputs/plan-wp6-resmoke-v5.md: patch does not apply
rc=1
$ A6 counts on the patched copy (expect 24 10 2 1) and the marker list length (17)
24
10
2
1
17
## 12 round-3 fix pass (2026-11-16): apply chain, R2 re-test, acc5 cases, checklist commands, scan
### 12.1 apply chain on a scratch copy (patch -p1; real inputs untouched)
# apply chain on a scratch copy, 2026-11-16T10:50:47Z
67a0a195537de875
/home/user/hadavin-sdk/handover/core-hardening/paste-check/plan-v5-fixes.patch:0
/home/user/hadavin-sdk/handover/core-hardening/paste-check/plan-v5-repin-v6.patch:0
inputs/plan-wp6-resmoke-v5.md:0
checking file inputs/plan-wp6-resmoke-v5.md
rc=0
patching file inputs/plan-wp6-resmoke-v5.md
rc=0
checking file inputs/plan-wp6-resmoke-v5.md
rc=0
patching file inputs/plan-wp6-resmoke-v5.md
rc=0
counts
24
10
2
1
markers
2:LEAD-FILL 7 3:LEAD-FILL 5 3:LEAD-FILL 6 3:LEAD-FILL 9 3:LEAD-FILL 7 4:LEAD-FILL 8 4:LEAD-FILL 3 125:LEAD-FILL 4 258:LEAD-FILL 1 258:LEAD-FILL 1b 258:LEAD-FILL 2 258:LEAD-FILL 1b 275:LEAD-FILL 6 433:LEAD-FILL 4 434:LEAD-FILL 4 585:LEAD-FILL 7 586:LEAD-FILL 1 
17
8a83abaa5c10db10ec84adabc82a855b087ff67286a44cec1611b812c90011d2  /home/user/hadavin-sdk/handover/core-hardening/paste-check/plan-v5-repin-v6.patch
39af84aec78b650f287d20013cdfa2d45dde8b75632e6d6729660bbc21ce3f5b  /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/c/w/inputs/plan-wp6-resmoke-v5.md
real inputs untouched:
67a0a195537de875
### 12.2 R2 block extracted from the patched plan (the paste between the sh fences), bash -n and dash -n rc 0; stand-ins are python processes in their own session with N8N_USER_FOLDER in their environment, HOME swapped to a scratch folder; term_ok = leader ends at TERM and is collected; term_ok_unreaped = ends at TERM but nobody collects it (zombie after TERM); term_ignored = ignores TERM; leader_dies_child_stays = leader ends at TERM, a child ignores TERM and stays; zombie_leader = leader already a zombie at the start
=== case term_ok pid 6826
R2 end: alive=no group=0

exit=0 after 1s
=== case term_ok_unreaped pid 6903
R2: before KILL the environ of pid 6903 no longer names HOME/hadavin-smoke/take-smoke-1/n8n (leader gone or pid reused): STOP, KILL not sent, tell the lead

exit=1 after 30s
=== case term_ignored pid 7605
R2: KILL sent after 30s
R2 end: alive=no group=0

exit=0 after 31s
=== case leader_dies_child_stays pid 8293
R2: before KILL the environ of pid 8293 no longer names HOME/hadavin-smoke/take-smoke-1/n8n (leader gone or pid reused): STOP, KILL not sent, tell the lead

exit=1 after 30s
=== case zombie_leader pid 8982
R2: environ of pid 8982 does not name HOME/hadavin-smoke/take-smoke-1/n8n: STOP, nothing sent

exit=1 after 0s
(bad-argument and dead-pid cases of the first run, same block:)
abc -> R2: bad pid: STOP exit=1; 1 -> R2: bad pid: STOP exit=1; 999999 -> R2: pid 999999 is not alive and its process group is empty: nothing sent exit=0; 12345 foo -> R2: which must be take or ctl: STOP exit=1
After the runs: pgrep for the stand-in command line printed nothing (all stand-ins were started by the test and ended by it).
Honest note: in the first run the harness did not collect the ended leader (zombie), so term_ok showed the zombie-after-TERM stop; the harness was fixed to collect it for term_ok and term_ignored, and the zombie cases are kept as their own cases.
### 12.3 acc5.sh, 18 cases (acc5-cases.sh)
case: good -> ACCEPT
case: good with comment tail -> ACCEPT
case: exit 30 only -> STOP (other exit text: +sys.exit(30)|)
case: exit 3x -> STOP (other exit text: +sys.exit(3x)|)
case: upper case Exit(3) -> ACCEPT
case: main() plus exit 3 -> ACCEPT
case: main() plus return 3 -> ACCEPT
case: main() alone -> STOP (no exit 3 or return 3 in kill block)
case: return 31 -> STOP (no exit 3 or return 3 in kill block)
case: exit 3 only in the start.sh block -> STOP (no exit 3 or return 3 in kill block)
case: no exit 3 -> STOP (no exit 3 or return 3 in kill block)
case: exit 4 with 3 -> STOP (other exit text: +sys.exit(4)|)
case: named constant -> STOP (other exit text: +EXIT_CODE = 3|)
case: exit 20 in start -> STOP (other exit text: + exit 20|)
case: print("exit 3") text only (ACCEPT, documented) -> ACCEPT
case: comment line only -> STOP (no exit 3 or return 3 in kill block)
case: comment line plus exit 3 -> ACCEPT
case: comment return 3 only -> STOP (no exit 3 or return 3 in kill block)
cases ok=18 bad=0
STOP (block missing)
(above: no == end line, expect STOP (block missing))
### 12.4 checklist commands (A2, A8, C9 with swapped paths) and bash -n of all 18 bash blocks of LEAD-CHECKLIST-v5.md (no output = rc 0 for every block)
--- A2
/home/user/hadavin-sdk/handover/core-hardening/paste-check/plan-v5-fixes.patch:0
/home/user/hadavin-sdk/handover/core-hardening/paste-check/plan-v5-repin-v6.patch:0
--- A8 (path swapped to scratch)
copied
already there: STOP, look at it first
--- C9 first run, second run (EV swapped)
LEAD-GO RE-PIN 2026-11-16T10:54Z
a LEAD-GO line is already there: STOP
### 12.5 final patch checksum
8a83abaa5c10db10ec84adabc82a855b087ff67286a44cec1611b812c90011d2  plan-v5-repin-v6.patch
### 12.6 marker lines in the patched plan (real grep): 2,3,4,125,258,275,433,434,585,586; LEAD-FILL-list-v5.md column now matches (125 R2 exit 3; 258 P-4b; 275 (0.1); 433 and 434 (13.1, 13.3); 585 UNVERIFIED 14; 586 UNVERIFIED 15)
### 12.7 banned-word scan after all edits (list read from tests/test_no_reference_material.py; words not printed)
plan-v5-repin-v6.patch 0 hits
LEAD-FILL-list-v5.md 0 hits
LEAD-CHECKLIST-v5.md 0 hits
acc5.sh 0 hits
acc5-cases.sh 0 hits
REPORT-repin-v6.md 0 hits
checkpoint-v6.md 0 hits
evidence-c7g.md 0 hits

## 13 Round-4 fix pass (2026-11-16; findings review-c3b-v6-readiness-r4.md M1-M5 and review-c3b-v6-facts-r4.md minor). Linux container only (kernel 6.18), plain bash and dash, stand-in folders, stand-in git repositories, stand-in processes. Nothing ran in Git Bash, WSL or PowerShell; `cygpath` does not exist here and was replaced by a shell function that prints a fixed Windows path.
### 13.1 apply chain on a fresh scratch copy (patch file NOT changed in this pass)
input plan sha256 prefix 67a0a195537de875; patch -p1 plan-v5-fixes.patch rc=0; patch -p1 plan-v5-repin-v6.patch rc=0
counts (<FINAL[-] / LEAD-FILL [0-9] / HEAD_PIN control / patch marker): 24 10 2 1
marker lines (real grep -n -o on the patched scratch plan): 2 3 4 125 258 275 433 434 585 586 ; 17 markers (unchanged from section 12.6)
patch sha256 (unchanged): 8a83abaa5c10db10ec84adabc82a855b087ff67286a44cec1611b812c90011d2
### 13.2 syntax of every bash block of the new LEAD-CHECKLIST-v5.md (24 blocks): bash -n rc 0 for all, dash -n rc 0 for all (no output)
### 13.3 facts-r4 minor: the early R2 branch "pid gone but N group processes left" (patch line 60), block extracted from the patched plan (11 lines, bash -n and dash -n rc 0)
case: leader (own session) forks a child that ignores TERM, leader exits and is collected by the test, then `bash R2.sh <leader pid> take`
```
OUT: R2: pid 18264 is gone but 1 process(es) of its group are left: STOP, nothing sent (the environ of the leader cannot be checked), tell the lead | rc 1
group members before cleanup: ['18265']
```
The test then ended its own child (pkill on that group; the child was gone afterwards). Nothing was sent by R2 (the block prints STOP before any signal). Earlier section 7 had the same case (D, D2) only for the v6 block before the round-3 changes; this is the run on the final block.
### 13.4 new and changed checklist commands, run in scratch (paths swapped with sed; the tested text is the text extracted from the file)
A8 (M4): fresh -> `copied`; second run -> `already there: STOP. Next: run cmp ...` (full message printed); `cmp` on an untouched copy prints nothing; on an edited copy prints `differ/EOF`; after `mv "$PF" "$PF.old"` A8 prints `copied` and both files exist.
A9 (M2, new): stub cygpath = the plan's guess path -> `string (1) found: 1 (must be 1)` and `strings (2) and (3) found: 2 (must be 2)`; stub = a different path (D:\x\plan.md) -> 0 and 0 (the lead must edit line 3 of PF). The plan has exactly these three path strings (grep -o on the patched plan: one Windows form, two `PF=...;`); only the Windows form is read by the runner.
C6 (minor, new ready block, with a stand-in git repo whose `n8n_kill.py` gains `sys.exit(3)`, the old head replaced for `eec6ba4`): known case -> `ACCEPT`, then the `== n8n_kill.py` part with `+    sys.exit(3)`; unknown case (shallow clone without the old commit, old text read from a second repo) -> `ACCEPT`, same part; empty `PIN` -> `STOP (block missing)` and an empty part (out.txt holds `PIN empty: STOP`).
C9 (M4): file with no final line end -> `(the last line of PROGRESS.md had no line end: one was added)`, last two lines printed, bytes checked with od (the line end sits between the old line and the new line, new line ends with LF); second run -> `a LEAD-GO line is already there: STOP`; no folder or file yet -> the line is written.
D1 (M4, new command): `PID=` empty -> `PID must be digits: STOP`; `PID=12x` -> same; `PID=432` when the log has `NEED-LEAD R2 pid=4321` (no glue to a longer pid) -> `no NEED-LEAD R2 line for pid 432 ... STOP`; `PID=4321` with a NEED-LEAD last line that has no line end -> line end added, `LEAD-YES R2 pid=4321 <time>` appended (od shows LF on both lines).
D2 (M5): the awk command on a log with blocks `== P-3b`, `== P-4b` (two HIT lines and exit=0), `== P-5` prints exactly the P-4b block; on a log whose last block is `== P-4b` it prints only that last block; the cmdline read of a process started as `exec -a n8n-stand-in sleep 3` prints `n8n-stand-in 3`.
### 13.5 not tested (honest list)
The D2 steps in a real WSL shell (`/proc` there), a real hit, the stand-in under WSL, `cygpath -w` in Git for Windows, `less` in A-C2b, the Git Bash `tail -c 1` behaviour with CRLF files (a PROGRESS.md with CRLF line ends would pass the line-end guard, because its last byte is LF; the added LEAD line has LF only), `patch` in Git Bash. The checklist is still a text for a person; no single run from A1 to D2 was made.
### 13.6 banned-word scan (list read from tests/test_no_reference_material.py; words not printed): LEAD-CHECKLIST-v5.md 0, LEAD-FILL-list-v5.md 0, plan-v5-repin-v6.patch 0; no CR, no non-ASCII byte in the checklist

## 14 Round-5 fix pass (2026-11-16; findings review-c3b-v7-readiness-r5.md R5-M1, R5-M2, nits). Linux container only, plain bash and dash, stand-in folders. Nothing ran in Git Bash, WSL or PowerShell; `cygpath` replaced by a shell function that prints a fixed Windows path.
### 14.1 apply chain on a fresh scratch copy (patch file NOT changed)
input plan sha256 prefix 67a0a195537de875; patch -p1 plan-v5-fixes.patch rc=0; patch -p1 plan-v5-repin-v6.patch rc=0; counts 24 10 2 1; marker lines (real grep -n -o): 2 3 3 3 3 4 4 125 258 258 258 258 275 433 434 585 586 (17 markers on the same 10 lines as 12.6); patch sha256 still 8a83abaa5c10db10ec84adabc82a855b087ff67286a44cec1611b812c90011d2.
### 14.2 syntax: all 27 bash blocks of LEAD-CHECKLIST-v5.md (24 before, 3 new): bash -n and dash -n rc 0 for every block. No CR, no non-ASCII byte; banned-word scan (list from tests/test_no_reference_material.py, words not printed): 0 hits.
### 14.3 R5-M1, A9 flip block (new)
- PF at the plan's guessed path, stub cygpath = the guess: prints `marker 9 flipped; left:` and `(end of list)` with nothing between; `LEAD-FILL 9` count 0, `LEAD-DECIDED 9` count 1 (guess-right case flips too). dash: same.
- stub cygpath = a different path, PF unedited: counts are not 1 and 2, prints STOP, file byte-identical to the original (cmp).
- PF with line 3 edited to another path (D:/x/plan.md), stub = same: flips.
- C7 simulation: all markers except 9 flipped to LEAD-DECIDED, then the A9 block: `LEAD-FILL [0-9]` count before 1, after 0. Without the A9 flip the count stays 1 (the R5-M1 defect).
### 14.4 R5-M2, C2b stand-in pid note (new ready block); C9 and D1 now say their EV line is the same as in C2b
- `SP=` empty or `12x`: `SP must be digits: STOP`, nothing written.
- no folder yet, `SP=4242`: folder and file made, one line `NOTE lead stand-in pid=4242 <UTC>` ending in LF (od).
- file whose last line has no line end: line end added first, then the note (od); dash run: same line written.
- the note starts with NOTE: `grep -c -E '^(LEAD-GO|LEAD-YES)'` on the files = 0; C9 run after the note writes its LEAD-GO line and the second run prints `a LEAD-GO line is already there: STOP` (the note does not trip it).
- D2: new read command `grep -E '^NOTE lead stand-in pid=[0-9]+' PROGRESS.md | tail -n 1` prints the note line; prints nothing when there is none.
### 14.5 nit: D1 regex now `NEED-LEAD R2 pid=$PID([[:space:]]|$)`
CRLF PROGRESS.md (`NEED-LEAD R2 pid=4321` + CR LF): accepted in bash and dash; LEAD-YES line appended with LF (od); line with trailing text accepted; pid 432 against 4321 refused; empty and `12x` refused; LF file without final line end still gets the line end first. The plan itself holds no grep for NEED-LEAD (only text that names the line), so there was no plan regex to compare; the shape `NEED-LEAD R2 pid=<digits>` is what the plan tells the runner to write.
### 14.6 nit: checklist line 4 (variables) now says PC is set at A2 (it said A3).
### 14.7 not tested: Git Bash, WSL /proc, cygpath -w, patch in Git Bash, a real CRLF PROGRESS.md written by a Windows runner (only simulated with printf).
