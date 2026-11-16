# Evidence F8 round 5 (raw output only, no judgement)

HEAD at start: bbe3bacc145921c77b989800fca15a90cfb9b734; HEAD at end: d8c36dd137004edf1c203b0395dfb1fd4ba4249c (other sessions commit in this repo)
sha256 (16 hex...) at start:
bb3050fe0aae33ae...  take_check.sh
822b5b0ae6859bed...  run_all.sh
a8964603d3549fc1...  test_take_check.sh
sha256 at end: identical (take_check bb3050fe0aae33ae..., run_all 822b5b0ae6859bed..., test_take_check a8964603d3549fc1...)
Working-tree take_check.sh equals the version committed in c79f8074d. Previous version = commit 7d309aef0 (sha f83cd41175b09b39..., the r4b start sha).
Patched copy built as run_all.sh does (F-002, F-008 apply rc=0, gen rc=0, 4 flow files). Scratch: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev8r5 (mirror, mirror-old, build/g/real).

## name -> exit code
| name | exit |
|---|---|
| bash -n take_check.sh | 0 |
| bash -n run_all.sh | 0 |
| bash -n test_take_check.sh | 0 |
| test_take_check.sh (100 of 100 as expected, 0 FAIL lines) | 0 |
| run_all.sh fresh work dir | 0 |
| concurrent: second run_all.sh on same raw folder | 2 |
| concurrent: first run_all.sh | 0 |
| tools check_secrets.py (python3 -I handover/flows-audit/tools/check_secrets.py; tools/check_secrets.py at repo root does not exist) | 0 (PASS 0 hits in 1807 files) |
| git checkout -- raw selftest-output | 0 |

## (2) test_take_check first 15 / last 15
ok   control: the committed pin gives exit 0, or exit 4 with 'pin not yet confirmed by the lead' while its reviewer line names a session; the reviewer line is printed as written; OVERRIDES says none (got exit 4)
ok   Q1/B3: a pin with a person's reviewer line gives exit 5 (a would-be pass with the pin override; 5, never 0); the line is printed as written; the output does not say a person read the pin (got exit 5)
ok   Q1: a reviewer line naming a session and 'lead to confirm' is exit 4 with the plain reason, never 'a person read' (got exit 4)
ok   Q1: '# reviewed by: Audit Session B, 2026-11-16' is exit 4 (got exit 4)
ok   Q1: '# reviewed by: A. Person, 2026-11-16, Lead To Confirm' is exit 4 (got exit 4)
ok   B1a: --write-warn-pin on the pin in use is refused (exit 2) and leaves it unchanged (got exit 2)
ok   B1b: a clean run writes a NEW pin with date and sha256 and exits 4, not 0 (got exit 4)
ok   B1: the written pin carries the '# flows sha256' line
ok   M-3: the written pin says it is not yet read and holds the placeholder line
ok   M-3: a pin whose header still has the placeholder is exit 4 (got exit 4)
ok   M-3: a pin with no 'reviewed by' line is exit 4 (got exit 4)
ok   B1b: the written pin, used as the pin, gives exit 5 (would-be pass with the pin override) (got exit 5)
ok   B1c: --write-warn-pin on an existing file is refused (exit 2) and leaves it unchanged (got exit 2)
ok   B1d: a run with a FAIL writes no pin and keeps exit 1 (got exit 1)
ok   B1e: a changed WARN set prints the difference, writes the new file, exits 4 (got exit 4)
...
ok   M2: the same raw folder with a DIFFERENT TMPDIR is refused, exit 2
ok   M2: the same raw folder given through a symbolic link (and another TMPDIR) is refused, exit 2
ok   M2: the same raw folder given as a relative path from another folder is refused, exit 2
ok   M2: the same raw folder given with a double slash, a link and .. is refused, exit 2
ok   M2: a DIFFERENT raw folder is not blocked by that lock (exit 0)
ok   M2: no lock file was left in either TMPDIR
ok   RUN_ALL_TAKE_FLOWS without RUN_ALL_NESTED is refused, exit 2 (got exit 2)
ok   Q5: a checker that exits 3 is shown as 3 and the take exits 3 (got exit 3)
ok   Q5: a checker that exits 4 is shown as 4 and the take exits 3 (got exit 3)
ok   Q5: a checker that exits 127 is shown as 127 and the take exits 3 (got exit 3)
ok   Q5: a checker that exits 137 is shown as 137 and the take exits 3 (got exit 3)
ok   Q5: --write-warn-pin with a checker that exits 127 writes nothing and exits 3 (got exit 3)
ok   count: mf-form.json with one extra wired step is exit 1 with a node-count FAIL and no orphan FAIL (got exit 1)
ok   count: mf-hook.json with one extra wired step is exit 1 with a node-count FAIL and no orphan FAIL (got exit 1)
test_take_check: 100 of 100 cases as expected, 0 not as expected

## (3) run_all first 15 / last 15
applied F-002-take-key-check-and-claim-error-path
applied F-008-save-runs-for-the-take
checker runs wall time: 0 s; self-test wall time: 7 s
==== real-v5 (THE TAKE) ====
---- default mode must be exit 0; strict mode shows what the owner's two open decisions would do ----
[pristine]
######## pristine real
RESULT: 0 FAIL, 23 WARN
Known open problems: 17
exit=0
[patched]
######## patched real
RESULT: 0 FAIL, 22 WARN
Known open problems: 16
exit=0
...
######## pristine-strict film
RESULT: 4 FAIL, 17 WARN
Known open problems: 11
exit=1
[patched-strict-film]
######## patched-strict film
RESULT: 4 FAIL, 16 WARN
Known open problems: 10
exit=1
[selftest exit=0] SELFTEST: 682 as expected, 0 not as expected, 62 skipped (not applicable)
[take_check.sh exit=5] missing lines: none
run_all exit status (real-v5 default runs + self-test): 0
real-v5 placeholder ids: 12 file(s) warn in the committed flows (pass --strict to make that a failure)
COMMITTED PIN (take-warns.pin) reviewer line, as written: 'flows-audit session, 2026-11-16, content read by that session only, lead to confirm'. NOT confirmed by the lead: a bare take_check.sh exits 4 until the lead replaces that line (this run used a stand-in line, so its take check could pass).
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check

## (4)+(5) hostile reviewer lines (name<TAB>exit<TAB>reason); mirror copy, bare take_check.sh --flows patched; pin sha line set to combined sha 989f552965a1b155...
### NEW script (round 5)
Pat O.L.L.M.	rc=4	NOT A PERSON'S NAME AND A DATE
P.a.t C.l.a.u.d.e	rc=4	NOT A PERSON'S NAME AND A DATE
L.L.M.	rc=4	NOT A PERSON'S NAME AND A DATE
A.I. Bot	rc=4	NOT A PERSON'S NAME AND A DATE
Pat Smith	rc=0	
O'Brien	rc=0	
Aiden Botha	rc=0	
Zed Smith	rc=0	
J.R.R. Tolkien	rc=0	
Jane Q. Roe-Smith	rc=0	
A.B.	rc=4	NOT A PERSON'S NAME AND A DATE
Pat C.L.A.U.D.E. Smith	rc=4	NOT A PERSON'S NAME AND A DATE
pat o.l.l.m.	rc=4	NOT A PERSON'S NAME AND A DATE
Pat O-L-L-M	rc=4	NOT A PERSON'S NAME AND A DATE
Pat O_L_L_M	rc=4	NOT A PERSON'S NAME AND A DATE
### PREVIOUS script (git show 7d309aef0)
Pat O.L.L.M.	rc=0	
P.a.t C.l.a.u.d.e	rc=0	
L.L.M.	rc=0	
A.I. Bot	rc=4	NOT A PERSON'S NAME AND A DATE
Pat Smith	rc=0	
O'Brien	rc=0	
Aiden Botha	rc=0	
Zed Smith	rc=0	
J.R.R. Tolkien	rc=0	
Jane Q. Roe-Smith	rc=0	
A.B.	rc=4	NOT A PERSON'S NAME AND A DATE
Pat C.L.A.U.D.E. Smith	rc=0	
pat o.l.l.m.	rc=0	
Pat O-L-L-M	rc=0	
Pat O_L_L_M	rc=4	NOT A PERSON'S NAME AND A DATE
### Differ (new vs previous):
Pat O.L.L.M.: new rc=4, previous rc=0
P.a.t C.l.a.u.d.e: new rc=4, previous rc=0
L.L.M.: new rc=4, previous rc=0
Pat C.L.A.U.D.E. Smith: new rc=4, previous rc=0
pat o.l.l.m.: new rc=4, previous rc=0
Pat O-L-L-M: new rc=4, previous rc=0

## (6) concurrent
second run_all rc=2
REFUSED: another run_all.sh holds the lock for the raw folder /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev8r5/raw6; wait for it to end, or use another raw folder (RUN_ALL_RAW is for the nested tests only)
first run_all rc=0

## secrets
PASS 0 hits in 1807 files
