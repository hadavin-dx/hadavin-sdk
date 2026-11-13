# Register (id | purpose | started UTC / IST | expected end | last checked | state | next action)
A | agent aebdbd..: full product suite, PR#12 8d65577 and main 61ded9e, 2 runs each (~16 min/run) | 09:39Z / 15:09 | ~10:45Z / 16:15 | 09:39Z | running | check 09:50Z
B | agent a2dce4..: hostile-input pass | 09:39Z / 15:09 | done 09:49Z | 09:52Z | reported, closed | none |
C | agent ae1559..: hang hunt | 09:53 Z | ~11:00Z | 09:53 Z | running | check progress-C.txt

A | stopped by container restart after 4 runs ended | - | - | 10:25Z | stopped | none
C2 | agent a107e0..: hang hunt d2 + c | 10:25Z / 15:55 | ~10:58Z | 10:25Z | running | check 10:35Z
D | agent a22cfb..: ORDER 3 suite twice on d5b4451 + F7 rerun | 10:25Z / 15:55 | ~11:05Z | 10:25Z | running | check 10:35Z
L | my shell: tests/test_real_check_dry.py alone on main, timeout 600, started 10:30Z | running | check 10:36Z
R1 | my rescue copy loops for orphaned logs of pids 652 (D run1) and 1351 (C2 full), 15 s, max 100 rounds | 10:40Z | ends when the pytest ends | running | check rescue.log
E | agent ab117a..: edadd00 full suite once + F7/C1/bytes | 10:42Z | ~11:05Z | 10:47Z | running | check 10:55Z
D | reported 10:57Z, closed (run 1 only, exit 0; suite-pr14.md corrected) | closed
C2 | reported 11:02Z, closed: no hang, no failure; c2 full main 3407 passed 198 skipped 0 failed exit 0 1067 s | closed
E | reported 11:05Z, closed: edadd00 3681 passed 0 failed 200 skipped exit 0 1215 s | closed
F | agent a48ec4..: 6b1fe49 full suite once + F7/new cases | 11:09Z / 16:39 | ~11:30Z, hard stop 11:50Z | 11:10Z | running | check 11:20Z
G | NOT STARTED (ORDER 7), waits for F | c14a514 path tests only | - | waiting
F | reported 11:28Z closed: 6b1fe49 3683 passed 0 failed 200 skipped
G | agent a5f7fd..: c14a514 path tests + F7 cases | 11:31Z / 17:01 | ~11:42Z | 11:31Z | running | check 11:38Z
G | reported 11:35Z closed: c14a514 path tests 378 passed 0 failed 1 skipped
H | agent a9451e..: rebase claims stack v1-v2b onto f3c39cf8 | 11:36Z / 17:06 | ~12:10Z, hard stop 12:20Z | 11:38Z | running | check 11:50Z
J | agent acac22..: stale sentences after PR 14 (read-only) | 11:36Z / 17:06 | ~12:00Z, hard stop 12:15Z | 11:38Z | running | check 11:50Z
I | NOT STARTED, waits for H and for lead answer on ruff/gitleaks | - | - | - | waiting | start at H report
H | reported 11:36Z closed: no conflicts, patch sha 7138e884, apply --check rc 0 (verified by me)
I | agent ad7742..: STACK and BASE hygiene + full suite | 11:39Z | ~12:05Z, stop 12:35Z | 11:40Z | running | check 11:52Z
J | reported 11:43Z closed: 2 STALE (3726 -> 3883 collected, 91 -> 92 files), 4 CANNOT TELL, 10 STILL TRUE
I | reported 11:58Z closed: STACK and BASE both 3683 passed 0 failed 200 skipped exit 0
K | agent a2c7fe..: unskip browser tests BASE then STACK | 12:00Z | ~12:30Z, stop 12:45Z | now | running | check 5 min
L | agent afb874..: unskip gitleaks tests + hygiene, DPLD_REQUIRE_SCAN=1, BASE then STACK | 12:00Z | ~12:25Z, stop 12:45Z | now | running | check 5 min
M | agent a275db..: classify the 200 skips (read-only) | 12:00Z | ~12:20Z, stop 12:30Z | now | running | check 5 min
M | reported 12:00Z closed: 4 others classified (2 never on Linux/3.12, 1 opt-in LEAD_DESK_LOAD_N, 1 root)
L | reported 12:02Z closed: 72 passed 0 failed 0 skipped on BASE and STACK
K | reported 12:07Z closed: browser tests all pass BASE and STACK (241 per head), 0 skipped
N | agent ae964c..: py3.13 full suite BASE | 12:12Z | ~12:35Z, stop 12:55Z | now | running | check 5 min
O | agent ab5cea..: py3.13 full suite STACK | 12:12Z | ~12:35Z, stop 12:55Z | now | running | check 5 min
P | NOT STARTED: 3.12 vs 3.13 per-test diff, read-only | after N and O | - | waiting
N, O | reported 12:25Z closed: 3.13.18 BASE and STACK 3684 passed 0 failed 199 skipped; P done by me (1 test differs)
Q1 | agent a2cfc4..: xdist proof | 12:31Z | ~13:50Z, stop 14:20Z | now | running
Q2 | agent a360ec..: identity fuzz | 12:31Z | ~13:30Z+ | now | running
Q3 | agent afbc0d..: crash soak 300 rounds | 12:31Z | ~13:30Z | now | running
Q4 | agent a942fb..: load claims | 12:31Z | ~13:30Z | now | running
Q5 | agent ac29a8..: cold reader README | 12:31Z | ~13:15Z | now | running
Q6 | agent ae462c..: cold reader n8n+limits | 12:31Z | ~13:20Z | now | running
Q7 | starting: 196 tests under 3.13 | | | |
Q8 | queued: mutation on pathconfine | | | |
Q5 | reported 12:34Z closed (no failure; unclear points listed)
Q5b | agent a77adc..: cold reader settings/portal/why-this-code/contract/SECURITY | 12:34Z | ~13:25Z | running
Q7 | agent aa5a44..: 196 tests under 3.13 | 12:32Z | ~13:00Z | running
Q8 | agent a101c8..: mutation on pathconfine | 12:34Z | ~13:35Z | running
Q6 | reported 12:36Z closed (4 fails, n8n not installable here)
Q6b | agent a0a58e..: cold reader tests/real-services/hubspot-probe docs, dry mode only | 12:37Z | ~13:25Z | running
Q9 | agent ab82f8..: cross-check demo numbers script | 12:37Z | ~13:20Z | running
Q7 | reported 12:40Z closed: 196 tests pass under 3.13 BASE and STACK
Q9 | reported 12:40Z closed: 1 mismatch (versions.md:9 collect flags); edge-case test x20 passed
B1 | agent a089825..: lane3-fix-1 prose patch (builder) | 12:42Z | ~13:20Z, stop 14:00Z | running
R1 | agent a502a2..: numbers audit (read-only) | 12:42Z | ~13:05Z, stop 13:30Z | running
Q5b | reported 12:41Z closed: 5 fails (bad-value claims, line count, switch wording, extra key, portal pages)
B2 | agent a5bf93..: lane3-fix-2 settings/docs patch builder | 12:45Z | ~13:30Z stop 14:00Z | running
R1 | reported 12:47Z closed: 20 rows invalid/unknown, all in the lane's own files
Q2b | agent a9f4ab..: fuzz seeds 7001-7005 + 7 extra generators | 12:49Z | ~14:00Z stop 14:20Z | running
Q3b | agent afb32a..: crash soak seed 20261114, 5 leads/round, double kill in 151-300 | 12:49Z | ~13:40Z stop 14:20Z | running
Q8b | agent a5a33c..: mutation of identity.py + claim logic | 12:49Z | ~13:50Z stop 14:20Z | running
B3 | agent ada279..: lane3-fix-3 tests-only patch for Q8 survivors | 12:49Z | ~13:30Z stop 14:00Z | running
B1 | reported 12:50Z closed: lane3-fix-1 (10 of 11 findings patched)
B3 | reported 12:51Z closed: lane3-fix-3 tests-only
Q3 | reported 12:52Z closed: 300 rounds 0 violations 0 hangs
Q8 | reported 12:52Z closed: 34 mutants 29 killed 5 survived
E3 | agent a25177..: lane3-fix-1 full suites | 12:52Z | ~13:25Z | running
E4 | agent afcb3f..: lane3-fix-3 mutant proof | 12:52Z | ~13:20Z | running
REV-1a | agent ae1e1c..: egm:egm-codebase-details on lane3-fix-1 | 12:51Z | ~13:10Z | running
REV-1b | agent a07d07..: egm:egm-comprehension on lane3-fix-1 | 12:51Z | ~13:10Z | running
REV-3 | agent a4b680..: egm:egm-implementation-readiness on lane3-fix-3 | 12:53Z | ~13:15Z | running
Q1 serial | ended 12:53Z ok: 3683 passed 200 skipped 1295 s
REV-1a/1b/3 | reported 12:57-13:00Z closed (round 1 saved: review-lane3-fix-1-*.md, review-lane3-fix-3-r1.md)
egm-resolve | done 13:05Z via Skill tool: evidence/resolve-round1-lane3-fix-1-and-3.md
B1b | agent aeb061..: lane3-fix-1 round 2 builder | 12:58Z | ~13:35Z stop 14:00Z | running
B3b | agent a266bb..: lane3-fix-3 round 2 builder | 12:58Z | ~13:35Z stop 14:00Z | running
Q2 | told 12:57Z to finish its campaign and stop
E4 | reported 13:01Z closed: lane3-fix-3 round 1: all 5 survivors killed, sha ok; one setup slip (11 failed with TMPDIR inside worktree)
B3b | reported 13:01Z closed: lane3-fix-3-r2.patch (393 passed 2 skipped; M15 real gap proven by a real input)
REV-3b | agent a50a99..: fresh egm:egm-implementation-readiness round 2 on lane3-fix-3-r2 | 13:03Z | ~13:20Z | running
E4b | agent a77229..: independent proof of lane3-fix-3-r2 | 13:03Z | ~13:25Z | running
Q3b | reported 13:02Z closed: 300 rounds 0 violations; 35 of 46 recovery point kills never fired
REV-3b | reported 13:08Z closed: 0 blocker 0 major 4 minor (saved review-lane3-fix-3-r2.md)
B3c | agent a7bcc5..: lane3-fix-3 r3 minors | 13:06Z | ~13:30Z stop 13:50Z | running
Q3c | agent ab9f5d..: blind-mail soak | 13:03Z | ~14:00Z stop 14:20Z | running
Q10 | agent a38c40..: flake chase PR12 E marks | 13:04Z | ~13:40Z stop 14:00Z | running
B3c | reported 13:10Z closed: lane3-fix-3-r3.patch sha b272b9a8
Q2 | reported 13:08Z closed: 0 violations; UNDOCUMENTED casefold class (861/867 variants)
B2 | reported 13:09Z closed: lane3-fix-2.patch (code + docs + tests; changed one old test)
REV-2a | agent a31bac..: egm:egm-codebase-details on lane3-fix-2 | 13:10Z | ~13:30Z | running
REV-2b | agent aebdf3..: egm:egm-design on lane3-fix-2 | 13:10Z | ~13:30Z | running
B4 | agent a52889..: lane3-fix-4 identity case docs + casefold analysis | 13:11Z | ~13:45Z stop 14:10Z | running
Q1 | reported 13:11Z closed: xdist -n 3 same node ids, 2 xdist-only failures (reset.sh exit 6)
Q11 | agent ae29d7..: root cause of the 2 xdist-only failures | 13:11Z | ~13:40Z stop 14:10Z | running
Q4 | reported 13:13Z closed: F1/F2 doc mismatches (measure_burst fails at N=300 without retry; Linux answers 503 not OS refusals); NOISY
E3 | reported 13:14Z closed: lane3-fix-1 r1: 3692 passed 0 failed both trees; hygiene did not scan the untracked file
B1b | reported 13:14Z closed: lane3-fix-1-r2.patch
B4 | reported 13:14Z closed: lane3-fix-4.patch (conflicts after the claims stack)
Q11 | reported 13:15Z closed: xdist failures proven: COLUMNS=80 truncates ps in reset.sh
egm-resolve fix-2 | done 13:30Z: evidence/resolve-round1-lane3-fix-2.md
B2b | agent a643db..: lane3-fix-2 round 2 | 13:15Z | ~14:00Z stop 14:15Z | running
B5 | agent (lane3-fix-5 builder) | 13:16Z | ~13:45Z | running
E3b | agent a16b68..: lane3-fix-1 r2 suites | 13:22Z | ~14:15Z | running
REV-1c | agent a90a66..: fresh codebase-details on fix-1-r2 | 13:21Z | ~13:40Z | running
REV-1d | agent a7c172..: fresh comprehension on fix-1-r2 | 13:21Z | ~13:40Z | running
Q10 | reported 13:17Z closed: 72 runs on main 0 errors; PR12 tree never started
resolve round 2 fix-1 | done 13:40Z: evidence/resolve-round2-lane3-fix-1.md (17 items)
B5 | reported 13:27Z closed: lane3-fix-5.patch (reset.sh ps width; 3 tests; xdist 0 failed)
B1c | agent ade8ef..: lane3-fix-1 round 3 builder | 13:27Z | ~14:05Z stop 14:25Z | running
REV-5 | agent addec0..: egm:egm-codebase-details on lane3-fix-5 | 13:27Z | ~13:45Z | running
| B4b | BUILDER lane3-fix-4 round 2 (docs+test) | 13:38Z | ~14:15Z; stop 14:30Z | running |
| B6 | BUILDER lane3-fix-6 docs from Q6b+Q3c | 13:38Z | ~14:15Z; stop 14:30Z | running |
| B7 | BUILDER lane3-fix-7 tests that kill Q8b survivors | 13:38Z | ~14:15Z; stop 14:30Z | running |
| Q8b | closed 13:31Z, report mutation-identity-claims.md | | | closed |
| E4b | closed 13:41Z, evidence/lane3-fix-3-r2-evidence.md (r2+r3 same: new file alone 15 passed 1 skipped; old+new 393 passed 2 skipped; 5 q8 survivors killed by new file; hand mutant d killed by old file) | | | closed |
| REV-3c | fresh egm-codebase-details on lane3-fix-3-r3 | 13:42Z | ~14:00Z | running |
| B1c | closed 13:50Z: lane3-fix-1-r3.patch sha256 0c45bbfe4c87a54d180ff086b37de530e367dcb346e173b67516f4e99ce53a52; new test 14 passed on patched, 12 failed on base, 11 failed on r2; hygiene 20 passed 4 skipped; 774 passed 31 skipped across 11 files; 0 lines >120; git apply --check clean on base and after stack/fix-3/fix-5. Not tried: Windows steps, n8n | | | closed |
| REV-1e | fresh egm-comprehension on lane3-fix-1-r3 | 13:51Z | ~14:10Z | running |
| REV-1f | fresh egm-codebase-details on lane3-fix-1-r3 | 13:51Z | ~14:10Z | running |
| REV-3c | closed 13:58Z: 0 blocker, 1 major (2 lines >120, fixed by lane lead in lane3-fix-3-r4.patch sha256 520ff284c018a2cc21852c2978bf77efcc2cfc7292a6aa1b3e3932b1bcab81f0; 413 passed 6 skipped incl. old path-confinement tests and hygiene), 4 minors (2 fixed) | | | closed, needs one fresh pass on r4 |
| REV-1e | closed: 0 blocker, 5 major, 11 minor (n8n start/owner-account order/step naming, receipt wording, burst counts reference) | | | closed |
| REV-1f | closed: 0 blocker, 0 major, 9 minor | | | closed |
| B1d | BUILDER lane3-fix-1 round 4 (5 majors + 20 minors from r3 reviews) | 14:00Z | ~14:30Z; stop 14:35Z | running |
| REV-3d | fresh egm-codebase-details on lane3-fix-3-r4 (security path, no cap) | 14:00Z | ~14:15Z | running |
| B5b | closed: lane3-fix-5-r2.patch sha256 d6edf82c...ad09f; old script + new tests 7 failed 4 passed; xdist -n 2 56 passed; serial 76 passed 4 skipped; builder's claim that pid files 'abc'/'1 ; true' exit 6 was wrong (exit 0, stale file removed; those 4 tests are regression guards); 1 unexplained xdist failure in the existing zombie test (message lost; 16 reruns passed) -> E6 chases it | | | closed |
| REV-5b | fresh egm-codebase-details on lane3-fix-5-r2 | now | ~14:00 | running |
| E6 | EVIDENCE RUNNER lane3-fix-5-r2 + xdist chase of the lost-message failure | now | stop 14:35Z | running |
| REV-3d | closed: 0 blocker 0 major 4 minor, all applied in lane3-fix-3-r5.patch | | | closed (security path: fresh pass found nothing real) |
| REV-5b | closed: 3 blocker (E501 x3, noqa S603 x2, isort), 4 major, 5 minor | | | closed; builder B5c next |
| B5c | BUILDER lane3-fix-5 round 3 (3 blockers, 4 majors from REV-5b) | now | stop 14:35Z | running |
| B5c | closed: lane3-fix-5-r3.patch sha256 e677e3d6...709f, notes lane3-fix-5-r3-notes.md; old script 8 failed/7 passed, r2+r3 tests 1 failed (blank), new 226 passed 4 skipped; 1 moved noqa S603 remains | | | closed |
| REV-5c | fresh egm-codebase-details on lane3-fix-5-r3 (13:46Z) | 13:46Z | ~14:05Z | running |
| E7 | EVIDENCE RUNNER lane3-fix-5-r3 (reset tests, xdist, full suite once) | 13:46Z | stop 14:30Z | running |
| B2b | closed: lane3-fix-2-r2.patch (+ for-stack); items 1-13,15 done, 14 declined; OPEN: r2 does not apply after lane3-fix-1-r2 (docs/limits.md:117 exit-code line); unwritable-parent test skipped as root | | | closed |
| REV-2c | fresh egm-design on lane3-fix-2-r2 | now | ~14:10Z | running |
| REV-2d | fresh egm-codebase-details on lane3-fix-2-r2 | now | ~14:10Z | running |
| E5 | EVIDENCE RUNNER lane3-fix-2-r2 (full suite once, tests fail on f3c39cf8 code) | now | stop 14:35Z | running |
| REV-5c | closed: 0 blocker, 1 major (ruff I001 import style, 2 files), 4 minor, 1 nit; saved evidence/review-lane3-fix-5-r3.md | | | closed; builder B5d next (round 4, security-adjacent so uncapped) |
| REV-2c | closed: 0 blocker, 1 major (PermissionError from Path.is_dir on chmod 000 parent; LEAD VERIFIED in stdlib source), 6 minor; saved evidence/review-lane3-fix-2-r2-design.md | | | closed; waits for REV-2d + E5, then resolve + B2c |
| REV-2d | closed: 0 logic blocker, 2 major (E501 x8 lines LEAD VERIFIED by awk; PermissionError same as REV-2c), 5 minor; saved evidence/review-lane3-fix-2-r2-codedetails.md | | | closed; E5 still running; resolve + B2c next |
| RES-2b | egm-resolve round 2 of fix-2: 11 accepted, 1 contested (.lock left; lockfile.py has no unlink), 0 escalated, 2 declined; saved evidence/resolve-round2-lane3-fix-2.md | | | closed; B2c next |
| B1d | closed: lane3-fix-1-r4.patch (full diff from f3c39cf8, replaces r3) sha256 df2515f3...; first 12-file run had 1 hygiene failure (4 literals in own test file), fixed; other 10 files not re-run after; n8n/Docker/Windows not tried | | | closed |
| REV-1g | fresh egm-comprehension on lane3-fix-1-r4 | 13:55Z | ~14:15Z | running |
| REV-1h | fresh egm-codebase-details on lane3-fix-1-r4 | 13:55Z | ~14:15Z | running |
| E3c | EVIDENCE RUNNER lane3-fix-1-r4 (hygiene, awk, docs files, apply checks) | 13:55Z | stop 14:35Z | running |
| B7 | closed: lane3-fix-7.patch (only tests/test_identity_claims_lane3.py, 16 tests, no product code); 7 of 8 Q8b survivors killed, C18 equivalent (alive); own full suite rc=0 3699 passed 200 skipped 1161 s; C03/C19 reached via private steps, no real two-thread race | | | closed |
| REV-7a | fresh egm-codebase-details on lane3-fix-7 | 13:57Z | ~14:15Z | running |
| REV-1g | closed: 0 blocker, 5 major, 7 minor; saved evidence/review-lane3-fix-1-r4-comprehension.md (reader did not read patch lines 609-835) | | | closed; wait REV-1h + E3c, then resolve + B1e |
| REV-1h | closed: 0 blocker, 1 major (new noqa S603 + 5 type: ignore, LEAD VERIFIED), 5 minor (n8n_api strip claim LEAD VERIFIED); saved evidence/review-lane3-fix-1-r4-technical.md | | | closed; resolve + B1e next |
| REV-7a | closed: 0 blocker, 0 major, 3 minor; saved evidence/review-lane3-fix-7-r1.md; minors fixed by B7b (small) | | | closed |
| RES-1d | egm-resolve round 4 of fix-1: 18 accepted, 0 contested, 0 escalated, 1 declined; saved evidence/resolve-round4-lane3-fix-1.md | | | closed; B1e next |
| B1e | BUILDER lane3-fix-1 round 5 (18 accepted items of RES-1d) | 13:57Z | stop 14:45Z | running |
| B6 | closed 13:58Z: fix-6 docs patch (4 files +79 -6). FAILED first: builder's single full run on final tree = 1 failed (hygiene flagged text `src:\.`), fixed, NOT repeated; only hygiene+new tests re-run (26 passed 4 skipped). No green full run yet. Skip numbers 30 gitleaks/166 browser (brief said 29/163). saved evidence/lane3-fix-6.patch, -notes.md | | | closed; E8, REV-6a, REV-6b launched 13:59Z |
| E8 | EVIDENCE RUNNER fix-6 (valid full run, fails-before, commands run) | 13:59Z | stop 14:40Z | running |
| REV-6a | egm-codebase-details fix-6 r1 | 13:59Z | | running |
| REV-6b | egm-comprehension fix-6 r1 | 13:59Z | | running |
| B4b | closed 13:59Z: fix-4 r2 (docs+23 tests), 5 fail on base docs, 10 fail on casefold copy; ONE full run 3706 passed 200 skipped rc 0 (19m28s). Not run: ruff/mypy/bandit/gitleaks (CI only). Open: loc@.dom / loc@a..b accepted (ASK to lead). Patches lane3-fix-4-r2.patch, -for-stack-r2.patch | | | closed; REV-4c next |
| B1d | closed (report relayed 14:03Z; already reviewed as r4; replaced by B1e round 5) | | | closed |
| B8 | BUILDER lane3-fix-8 (LEAD Q-19 ANSWERED 13:37Z: dotted/double-dot domain goes to review; sweep domain-shape checks) | 14:03Z | stop 14:50Z | running |
| REV-6b | closed 14:05Z: 0 blocker, 9 major (F1-3,8-10,13,14 + F11 minor), 10 minor/nit; saved evidence/review-lane3-fix-6-r1-comprehension.md | | | closed; waits for REV-6a then resolve |
| REV-4c | closed 14:05Z: 0 blocker, 2 major (loose README doc anchor; "emails" vs queued rows), 4 minor, 3 nit; saved evidence/review-lane3-fix-4-r2-technical.md | | | closed; resolve next |
| REV-6a | closed 14:07Z: 0 blocker, 2 major (false ModuleNotFoundError sentence; contract.md:68 sibling), 4 minor, 3 nit; saved evidence/review-lane3-fix-6-r1-technical.md | | | closed; resolve next |
| E6 | closed 14:09Z: fix-5 r2 full serial 1 failed 3693 passed 200 skipped (noqa comment contains "our" -> first-person test); xdist 10/10 passed, flake NOT reproduced (not a root cause); raw/e6/ | | | closed |
| RES-6a4c | egm-resolve fix-6 r1 (28 accepted) + fix-4 r2 (9 accepted); saved evidence/resolve-lane3-fix-6-r1-and-fix-4-r3.md | | | closed; B6b, B4c next |
| B6 | (duplicate hand-back relayed 14:12Z; adds: first full run on final tree was 1 failed 3689 passed 199 skipped; already closed) | | | closed |
| B6b | BUILDER lane3-fix-6 round 2 (A1-A13 of RES-6a4c) + lane3-fix-6b | 14:12Z | stop 14:55Z | running |
| B4c | BUILDER lane3-fix-4 round 3 (B1-B9 of RES-6a4c) | 14:12Z | stop 14:55Z | running |
| E5 | closed 14:13Z: fix-2 r2 evidence. Full serial 3784 passed 201 skipped 0 failed (18m15s; exit code not captured). Fails-before: test_live_claude 1 of 48 fails on old code; test_settings_lane3.py import error (env_yes_no); test_env_numbers.py 355/355 pass on OLD code (no fails-before). Long lines: config.py 5 (base 2), test_settings_lane3.py 4. r2 after lane3-fix-1-r2 conflicts at docs/limits.md:117. for-stack patch only apply --check'd. Logs raw/E5-*.log | | | closed; findings sent to B2c |
| E7 | closed 14:15Z: fix-5 r3 evidence. FAILED: full serial 1 failed 3697 passed 200 skipped rc 1 (test_no_first_person_plural...: noqa comment "our" in tests/support.py; base has 0 matches, LEAD CHECKED with git show). xdist -n 2 run 1 of 3 FAILED (test_reset_ps_width pid-file empty text, exit 4 port 43217 still answers; 1 flake, cause not investigated); n=4 3/3 pass. Fails-before on old reset.sh: 8 failed 198 passed. awk >120: reset.sh 7 (base 7), support.py 1, test_reset_scripts.py 3. raw/E7-*.log | | | closed; findings sent to B5d |
| E3b | closed 14:17Z (STALE: evidence for fix-1 r2, now superseded by r4/r5). GAP: e3b-fix1 full suite never ran to the end in one run: 3 runs cut by outside signals (KeyboardInterrupt exit 2 at 86% and 67%, SIGTERM exit 143 at 5%), cause UNKNOWN (likely another process); no test failed. Stack tree full: 3692 passed 0 failed 200 skipped rc 0 1142s. fix1 pieces: 3196 passed before stop + tail 512 passed rc 0 (not one clean run). New test file 9 passed both trees; hygiene 20 passed 4 skipped. evidence/lane3-fix-1-r2-evidence.md | | | closed; no rerun for r2 (replaced by E3c for r4 and a fresh run for r5) |
