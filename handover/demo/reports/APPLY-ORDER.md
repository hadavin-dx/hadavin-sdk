# APPLY-ORDER (cloud session, ORDER 224). Written at 21:38Z.

## Read this first (what I cannot promise)
- Your base `ae19f99` ("laptop final-12") is NOT a commit in this repository (`git cat-file -e ae19f99` fails). I asked which snapshot it is and got no answer. I cannot check that my patches apply to it. Every base below is a tree of mine that I can name and re-check.
- Final-14 (b37e7e1) changed portal files only and no python, according to your order. My patches touch python under src/lead_desk and tests/. Overlap is only possible in portal_api.py, tests/test_portal_*.py and tests/portal_fixtures (my A4r6 tree carries your portal work from the fix7 -> portal tree). I could not diff against b37e7e1 here. If a hunk conflicts, take YOUR portal file and re-run tests/test_portal_api.py.

## Safest way: ONE consolidated diff (recommended)
1. `CONSOLIDATED-A4r7-vs-fix7.diff` (this folder). Base = tarball `handover/demo/dpld-fix7-00e30c5.tar.gz` (extract; directory dpld-fix7-00e30c5). 61+ files (see diff header count). Applied with `patch -p1` on a fresh copy of the base; result byte-identical to my tree /tmp/dpld-s9 = A4r7 (checked with diff -rq, excluding caches/db files).
   It contains S1 .. S1i, T1, T2, desk M2, A4 remainder, mutation tests (all listed below). It does NOT contain the live tooling (item 13). The A4r6-only file was replaced by this one.
2. S1i has landed (item 12): the consolidated diff now includes it.

## Ordered list if you want the pieces (each diff is `patch -p1`, a/ b/ paths)
Chain of my trees: fix7 (00e30c5) -> your portal tree -> A4r3 -> A4r4 -> A4r5 -> A4r6 (-> A4r7 with S1i).
| # | Patch | Applies to | Fail-before evidence | Conflicts / notes |
|---|---|---|---|---|
| 1 | patch-cloud-1-full-fix6.diff, patch-cloud-2, patch-cloud-3 (older, already inside fix7 tarball) | -- | -- | Do NOT apply again: fix7 contains them. |
| 2 | S1.diff | fix7 + your portal tree | reports/S1b-baseline-old.txt (old-code run) | Superseded in parts by S1b..S1h. |
| 3 | S1b.diff (slow sender, connection slots) | my start copy of constants/server; applies to portal tree too | reports/S1b-failbefore.txt | hunks in constants.py do not overlap your PORTAL_ACTIONS lines. |
| 4 | S1c.diff (hygiene/wording) | /tmp/dpld-portal | reports/S1c-report.md names S1c-failbefore.txt (in /home/user/build, not pushed: ask if wanted) | `S1c-stale-tests.diff` is YOUR DECISION (rename/retire stale tests); NOT in the consolidated diff. |
| 5 | S1d.diff (17 files) | A4r3 snapshot | S1d-failbefore.txt (in /home/user/build) | S1d items NOT done: C2, C10, C13-C17, wildcard-bind test, wider duplicate cleanup, slow marker. |
| 6 | S1e.diff (desk M2: model step after claim, 4 files) | A4r3 | in S1e-report.md | -- |
| 7 | T2.diff (mutation tests, 1 new file) | A4r4 | reports/T2-failbefore/<n>.txt | 9 of 11 survivors killed; #41, #48 equivalent (proof in T2-report.md). |
| 8 | S1f.diff (test_mutants.py barrier fix, tests only) | A4r4 | in S1f-report.md | -- |
| 9 | S1g.diff (budget constants, touch busy, give-back) | A4r4 | reports/S1g-failbefore.txt | -- |
| 10 | S1h.diff (budget 10 s/10 s, 4 files per thread, exit 4, EMFILE) | A4r5 (= A4r4+S1g+S1f+T2) | reports/S1h-failbefore.txt | result = A4r6 = consolidated diff. |
| 11 | T1.diff (first mutation tests) + mutation/patch-tests-mutation.diff | fix7 line | reports/T1-failbefore.txt, T1-extra-mutants.txt | T1 is inside the consolidated diff. |
| 12 | S1i.diff (round-6 fixes) | A4r6 | S1i-failbefore.txt | LANDED: S1i.diff (9 files) apply-checked on fresh copy of A4r6, identical to A4r7. Full suite 739 passed / 1 skipped / 2 known red (reports/S1i-full.log). Report reports/S1i-report.md. Round 7 reviews running on snapshot A4r7. Two decisions for you in S1i-report.md items 2 and 3 (budget now 9 s; unbounded give-back after a lock on the stamp). |
| 13 | Live tooling: L2a, L2b, L2c, L2d, L2e (+ SMTP m1/m2 inside L2c/L2d/L2e: smtp_outbox.py and tests) | in this order on dpld-camp tree (A4r4 + live_l2) | reports/L2b..L2e-failbefore*; L2e-mutation.json | They touch live_l2/, smtp_outbox.py and tests/test_live_l2_*, test_smtp_outbox only, no shared desk file, so they can be copied after item 10/12. One needed change: the campaign's http_qualifier must expose a public `timeout_seconds` for the new desk budget check. |
| 14 | portal: portal/patch-portal-A4.diff | clean A3 base | -- | NOT final: must be rebuilt from the final tree plus portal-A4.md (ORDER 217 unfinished). |

## Straight answers (ORDER 224)
- Campaign: run 1 superseded. Run 2 finished and re-checked offline with the fixed L2e checker: 17 of 20 scenarios hold, 3 fail (model-slow, model-timeout, catcher-slow, all on drain time only; no lost lead, no duplicate email in any scenario). Run 3 (long drain) finished: model-timeout never drained in 1200 s (199 pending, 1 failed); the one missing CRM row of run 2 did not recur. Nothing is running now. No scenario has been re-run live on the final tree; the L2e code paths are tested with stand-ins only. The synthetic total-loss book that must FAIL: covered by L2e tests (see L2e-report.md), not by a new campaign.
- Mutation survivors now: 0 unaccounted of the 11. 9 killed by T2, #41 and #48 equivalent with written proof, #3 equivalent through the desk and killed by a direct test. A fresh round of 81 + 20 new mutants on the final tree has NOT been run (ORDER 223: no new scope). Say "run" and I do it.
- In my trees but NOT in any patch you can apply: (a) nothing from S1i is outstanding; (b) /tmp/dpld-final is a combined tree that is STALE (lacks S1h and S1i); do not use it; (c) S1c-stale-tests.diff (your decision); (d) portal-A4 rebuild; (e) README/contract counts in live_l2/README-L2.md still describe old bounds; (f) README.md and contract.md counts of tests are stale until S1i.
- Known red tests, expected: test_hygiene_scan_public (needs gitleaks binary) and test_hygiene_wordlist (needs HYGIENE_WORDLIST). A4r6 full: 731; A4r7 full: 739 passed / 1 skipped / 2 known red (reports/S1h-full.log, S1i-full.log).
- Review state: round 6 had 0 Blockers; its findings are what S1i fixes. Round 7 follows S1i (loss path: no round cap). That is continuation of review fixes, not new scope.

## Update 21:41Z
Round 7 (reports/A4-r7-*.md): 0 Blocker, 1 Major (a hung model call on the reaper thread freezes the reaper; contract rule 4 was untrue for that case), 2 Minor, nits. Builder S1j is fixing them (tree /tmp/dpld-s10, expected ~22:30Z at the latest). Then A4r8 snapshot and round 8. The consolidated diff will be regenerated as CONSOLIDATED-A4r8-vs-fix7.diff; until then use A4r7 (it has the Major above).
