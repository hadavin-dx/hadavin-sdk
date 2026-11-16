# CLOUD RESUME 2026-11-13 (CORE lead, session_014pRo36xK6rXQgBKwtTHfac)

Written at the STOP order (LEAD COMMAND 06:55Z CORE: STOP). No secrets in this file.
Everything below was true at the last `git ls-remote` check. Run the checklist at the end first.

Honest summary first: NO package is finished. Nothing here is a clean round. Every
number marked BUILDER-CLAIMED comes from the builder and was not reproduced by an independent runner.
The independent runner (RUNNER) numbers are named as such.

Rulings I hold (from LEAD-ORDERS): pathguard split by responsibility, never raise the 220-line limit;
q-q8b bare scheme word + token: hide at 16 or more token-charset characters, 15 stays shown, no wider scheme list;
no limit raises; run the 3.12 mutant table before the next runner; runner on the laptop ONCE per FINAL head;
redaction errs on HIDING; stage names demo/pilot/prod only; S603: ONE inline marker on the helper line plus a proving test;
suppression count against `origin/main...HEAD` (three dots); handover/evidence branches are NEVER merged to main;
builders never commit handover/ except on core/cloud-handover; pd-bind: same holder, evaluation-only licence, code fresh from the spec, keep the demo-commit citation in changelog and PR body.

## Package 1: Part 6 (mode banner + demo-only guard)
- Branch `wip/cloud-pd-banner`, remote = local head b4c01568 (a `WIP:` commit, only tools/demo_only_guard.py). Previous clean-ish head 20c369f0. Worktree: none (scratch removed); recreate with `git worktree add <path> origin/wip/cloud-pd-banner`.
- State: RUNNER round 15 at 20c369f0: mutant rows 364 of 366 good (350 KILLED, 14 CRASH pinned, 2 SURVIVED: J27 and R10C2), focused tests 100/100 rc=0 on 3.13 and 3.12, lint clean with ruff 0.16.9 (pin is 0.17.1). Batch 16 (b4c01568) is BUILDER-CLAIMED partial, no tests run: bypass names hidden, bare scheme+token hidden at SHAPED_TOKEN_MIN (16) only.
- Next: give the fresh builder the ONE FIX BRIEF in handover/reviews/PD-banner/goldfish_review_report-r15.md (items 1-12 plus minors); first update the tests known broken by b4c01568 (tests/test_changelog_numbers.py MASKER_CLAIMS; tests/test_demo_only_guard.py near row `x Bearer a1b2c3 y` and mutant row R13B3; CHANGELOG line ~223). Then round 16 (mode-safety path, no cap).
- Open Majors (r15): CHANGELOG token-length claim false; "only place a program is started" claim vs 9 follow-up files (21 starts) + demos/ask-your-data/askdata/cli.py:174; `--bypass=` value shown; "hides more than the core" test weak; sweep lacks rejected samples (os.system, os.popen, os.exec*/spawn*, from-os-import); broken test-name reference tests/test_banner_mutant_table.py:520; 366-rows claim; run_fixed must refuse shells and interpreter eval flags; kill J27 and R10C2; 461 added lines over 100 columns; labels.
- Open question for lead: tools/mutation_runner.py (and its tests) use Popen/start_new_session/stdout=PIPE, cannot move to `run_fixed`; needs a reasoned visible list or a second helper. Also confirm bypass=0/bypass=1 wording (masker shows them, lead rule says visible).

## Package 2: Part 2 (bind guard, pd-bind)
- Branch `wip/cloud-pd-bind`, head 4dd7ce1e (remote = local).
- RUNNER (ab1740f5, at 4dd7ce1e; summary in handover/evidence/PD-bind/4dd7ce1e/RESULTS.md): mutant table 300 rows (builder said 71), 286 KILLED, 11 CRASH, 3 SURVIVED (B240 registry of a runtime not compared, B241 audit sink, B242 limits), 297 of 300 good. tests/test_bindguard.py 396 passed, 1 skipped on 3.12 and 3.13. ruff, format, bandit rc=0 (bandit from /root/.local/bin). 0 suppressions added. Old trees with new tests copied: 83cdb7a2 300 passed/96 failed; 82dd69c1 330 passed/66 failed. Hostile: 93 cases per version, 8 not refused (10,001-item lists/dicts in FakeChannel or MemoryStore, 300 FakeChannels, one shared 200,000-item list) and a metaclass whose `__name__` raises escapes as the raw exception. Not run: full suite, 3.12 mutant table, 3.14.
- Open round-13 findings (reviews in handover/reviews/PD-bind/): 1 Blocker + 6 Majors codebase, 3 Majors design: plain-value seal can 503 a public bind through a stateful bound-method tool (test deleted); false "never raises" docstrings; "scrub by contents" claim false (deep=False route); stale CHANGELOG item 9; object-count contradictions; bind_mutants.py header stale; lines over 100 columns; no real-ToolBox test; survivors B240-B242; unrefused hostile cases above.
- Next: `egm:egm-resolve` on round 13 (not done), then batch 14 builder.

## Package 3: SONAR-PATH (ORDER 260)
- Branch `wip/cloud-sonar-path2`, head 49fc48a4 (a `WIP:` commit, BUILDER-CLAIMED, no runner number). Code-only branch `core/k1b-path-confinement` is the older line; check `git branch -r` for its head.
- State: batch 7 done in part: M1 (vault jwt_path message), M2 (tools._module_files unbounded), M3 (refuse at 4096 bytes or more), new hadavin_sdk/pathtext.py (110 lines), pathguard.py 173 lines (limit untouched), Q-R5-1 text, static ast scan. Gaps: 3.13 mutant table 194 of 209 good (5 SURVIVED, 9 WRONG_REASON, 1 CRASH); 3.12 table not run; 3.12 focused run half done; unwritable-parent test skips as root.
- Next: fresh builder for the rest of batch 7 from the ONE FIX BRIEF (handover/reviews/sonar-path/goldfish_review_report-r6.md), 3.12 mutant table before the next runner, test ids for account-number/ARN-style cases built from parts, then runner once on the laptop at the FINAL head. Report `PR READY: <branch> <sha>` only when clean; never claim a SonarCloud finding is cleared. Q-R5-1 recommendation: keep refusing operator-typed links that leave their folder; `..data/token` stays allowed.

## Package 4: Q8c-1 (notes check)
- Branch `core/q8c1-notes-check`, head 69a5f4e8 (fast-forward from 7712c26e).
- BUILDER-CLAIMED: 3.13 499 passed on 5 files; ruff/format pass; 4 of 4 focused rows killed. 3.12 run stopped at 497 of 499 (unverified). Review of the previous head was 0B/0M.
- RUN ON LAPTOP (lead's list): the 5 test files on 3.12; `HADAVIN_POLICY_FULL_RENEWAL_RUN=1 pytest tests/test_policy_changelog.py -k plant`; `python tests/policy_mutants.py "the files that do not parse are merged"`; also notes_lines_check, trivy, semgrep, pip-audit, zizmor, stale-ignore, demo_only_guard on the final heads.
- Checkpoint: /home/user/build/notes/q8c1-b17-checkpoint.md (copied into handover below if present).

## Other worktrees
About 150 scratch and evidence worktrees under /home/user/build (B-*, EV-*, ER-*, wt/*, er13-*, PRH). The STOP sweep committed every dirty one on a `WIP:` commit: detached trees went to branches `scratch/stop-1113-<name>`; named branches kept their name. Results table: handover/evidence/stop-sweep-2026-11-13.txt. Filtered out by rule: *.xml, *junit*, *.log, raw/, handover/, files over 5 MB. These are scratch (old-tree failbefore, copied tests); the recipe to rebuild is in the review/evidence reports. Delete the scratch branches after the next session reads them.

## Agents and shells at stop
Builders a592bb13 (Q8c-1), ac09a2ce (SONAR-PATH), aa1d792a (Part 6 batch 16) finished and reported. Part 6 builder was launched just before the STOP order arrived; I told it to stop and WIP-push; it pushed one small `WIP:` commit (b4c01568) and ended. Runner ab1740f5 (Part 2) finished; its summary is saved. Finisher adecceff finished. Nothing running at the final check; see the STOPPED block.

## Open questions for lead
1. Popen users vs `run_fixed` (see Package 1). 2. bypass=0/1 wording. 3. Q-R5-1 and the pathtext.py location (hadavin_sdk/pathtext.py, not k1b, to avoid a circular import). 4. Laptop tool list above. 5. .gitleaksignore decision (owner-only; commit d308aaf4 earlier tripped rule aws-access-token on a raw junit XML which is never committed now). 6. Part 2 hostile cases that are not refused: decide whether 10,001-item containers must be refused (limit in standins.py is 250,000).

## Environment notes
- Venvs: /home/user/build/ER6-venv3.13, ER6-venv3.12, er13-venv3.13, er13-venv3.12 (all in the cloud container; recreate with uv if gone). Ruff pin 0.17.1 (the container has 0.16.9: install the pin before judging lint). bandit at /root/.local/bin/bandit.
- Push helper: /home/user/build/bin/cpush.sh "<msg>" (gitleaks-gated; only pushes handover/ on core/cloud-handover). Sweep helper: /home/user/build/bin/sweep.sh. gitleaks binary: /home/user/build/bin/gitleaks. These live outside the repo; copies are in handover/evidence/stop-tools/.
- Always set PYTHONPATH=<worktree>/src and print `hadavin_sdk.__file__`. Never answer y/yes to any prompt that can reach a network. No full suite in the cloud: runs go to the laptop. Reviews are `egm:*` agents, never general-purpose; use full agent ids for SendMessage.
- Stuck rebase: runner writes during `git pull --rebase --autostash` can leave an empty `.git/rebase-merge`; remove it.

## First 15 minutes of the next session
1. `git fetch --all --prune`; `git checkout core/cloud-handover`; `git pull --ff-only`.
2. Read handover/LEAD-ORDERS.md newest section, this file, handover/core/REPORT.md top block.
3. Check for a lead order starting with GO; if none, do nothing.
4. Run the verify script (`/tmp/verify.sh` recipe: dirty count, ahead, remote==local) over `git worktree list`; expect clean.
5. Recreate worktrees for the four heads: b4c01568, 4dd7ce1e, 49fc48a4, 69a5f4e8.
6. Install ruff 0.17.1 in the venvs; print hadavin_sdk.__file__ per worktree.
7. Launch the fresh Part 6 batch 16 builder with the r15 brief; fresh SONAR-PATH batch 7 builder with the r6 brief.
8. Run `egm:egm-resolve` for Part 2 round 13, then a batch 14 builder.
9. Queue RUN ON LAPTOP lines for Q8c-1 and every FINAL head, once each.
10. Append findings to the ledger the same turn; write PULSE lines; push with cpush.sh.

## Added at the end of the STOP sweep
- Two git stashes were saved as branches: `stop-stash/1113-0` (WIP on core/prh-strip-hidden-controls) and `stop-stash/1113-1` (an autostash from a stuck rebase). Inspect, then delete if not needed.
- One local branch had diverged from its remote and was pushed under another name, not forced: `core/prh-b3-local` local head e852b577 is on `stop-local/1113-core-prh-b3-local`.
- 9 other local branches are only behind their remote (local is an ancestor of the remote head): nothing lost.
- Scratch (detached) trees were switched to `scratch/stop-1113-<name>` branches and pushed. Table: handover/evidence/stop-sweep-2026-11-13.txt (state), stop-sweep-actions-2026-11-13.txt (per-tree action).
- Builder notes, checkpoints and briefs from /home/user/build and the scratchpad (markdown only, under 1 MB each) copied to handover/evidence/stop-notes/. Logs, junit and raw files were not committed by rule.
- Two worktrees keep untracked files that were left out on purpose: B-Q8a1-b8 (`handover/`, builders never commit handover/) and B-Q8c1-b12 (a gitleaks log under handover/evidence/Q8c-1/b12/logs/). Both branches are otherwise pushed and equal to the remote.
- Part 6 batch 16 checkpoint: handover/evidence/stop-notes/checkpoint-pdbanner-b16.md if present; SONAR-PATH batch 7 checkpoint: checkpoint-b7.md in the same folder.
