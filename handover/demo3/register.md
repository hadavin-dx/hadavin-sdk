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
