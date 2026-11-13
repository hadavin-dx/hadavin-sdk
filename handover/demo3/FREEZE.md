# lane3 FREEZE REPORT (15:45Z / 21:15 IST), written once, as ordered

All agents of this lane have reported and are closed (register.md). Nothing was pushed to the demo repo or merged. All patches are under `handover/demo3/evidence/`. Tests are full serial runs, `python -m pytest -q -rs`, on the base f3c39cf8 plus the patch.

## NOT merged-ready (product code with no independent review of the final patch)
| Patch | Full suite | Why not ready |
|---|---|---|
| lane3-fix-8 (dotted domain, Q-19) | 3723 passed, 200 skipped, 0 failed | No independent review at all (freeze order). Still accepted: label over 63 characters, dots before the @, IP literal `a@[127.0.0.1]`. 11 of 12 hand mutants killed. |
| lane3-fix-2 r4 (one secret-file rule, path checks) | 3809 passed, 237 skipped, 0 failed | Round 3 had 7 major findings; r4 has had no review. Tests written after the code. The `on-fix-1-r6` variant had only 193 tests run. Applies only AFTER fix-1 r6. A refused key file still leaves a `.lock` file (documented). |
| lane3-fix-5 r5 (reset scripts) | 3780 passed, 206 skipped, 0 failed (run alone; an earlier 57-failed run was invalid: wrong basetemp) | r4 review found 1 major (reset.ps1); r5 fixes it but is unreviewed. reset.ps1 was NOT run on Windows. xdist: 20 of 20 passed. 6 skips above the 200 baseline: 4 are the new Windows PowerShell tests, 2 not reconciled. |

## Documentation and tests only: ready if you accept that the last fixes were not re-reviewed
| Patch | Full suite | Note |
|---|---|---|
| lane3-fix-1 r6 | 3716 passed, 200 skipped | Fixes the 2 majors of the round-5 review; r6 not reviewed. Licence-key wording not checked on screen. |
| lane3-fix-4 r4 | 3711 passed, 200 skipped | Fixes the 1 major (portal shows small letters; Node run confirms the lower-casing). Portal not rendered in a browser. README lists the three letter pairs twice. |
| lane3-fix-6 r3 | 3705 passed, 200 skipped (tree before its last edit; 7 files re-run after, 894 passed) | Fixes 18 resolve items. 241, 72, 3684 and 3683/200 counts stay "reported, not re-measured". |

## Apply order (checked only in pieces)
Claims stack, then fix-3 r5, fix-5 r4, fix-1 r6, then fix-2 r4-on-fix-1-r6 (each rc 0 in B1f and B2d checks). fix-4 r4 applies in both orders with fix-8 and on the claims stack. NOT checked: one complete stack with fix-5 r5, fix-4 r4, fix-6 r3 and fix-8 all together; no full suite was run on any stack. fix-3 and fix-7: not re-read for this report, see the register.

## Not done, not checked, or unexplained
- No ruff, ruff format, mypy, bandit, gitleaks or Windows run anywhere (CI only per owner rule; no Windows runner).
- E3b three cut runs: unexplained. The 2 `E` marks of the PR #12 run: unexplained. The old xdist port-43217 flake: never reproduced, so not proven gone.
- Shell for several runs had AWS_* and ANTHROPIC_* sandbox variables set (no-cloud-config condition not met); no failure came from it.
- 6 full suites ran at once at one point (limit is 3); those timings are not clean.
- The EGM drift report (`egm:egm-drift-report`) was NOT run: the freeze order said no more steps. The blocker ledger was not run either.
- My own slips: guessed register times (corrected by notes), REV-1f resolve done inline instead of through the Skill tool, my fix-6 plan item A1 was wrong.
- Left in the sandbox: system user `b2dtest`, worktrees under /home/user/work.

## Open questions for you
xdist in CI (report only); PR #12 E marks; run the 4 remaining skips; Q8 vs B3 M11; D10 "sender" word; whether to add the 63-character label rule and the IP literal to fix-8.

FROZEN.
