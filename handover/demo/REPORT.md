# DEMO session report (the ONE file this session reports to the lead in; newest block on top)
Session: https://claude.ai/code/session_014pRo36uYfYwuEDby9epxu8. Write a status block at least every 10 minutes (UTC and IST, what runs, what is pushed, what is stuck, what you need from the lead).

## 2026-11-12 19:08Z - lane 5 builder done, EGM review of it running; lanes 1, 3, 4 and the lane 5 review running (4 agents)
- Lane 5 file: reuse/CORE-TO-DEMO.md. Nothing was run or tested (read-only comparison). Builder verdicts, NOT yet reviewed: (a) text fold NO (core folds look-alikes together, the demo keeps them as separate mailboxes); (b) mutation runner NO as replacement / YES as optional addition (the demo has no mutants script: its mutants are tests/test_mutants.py, test_mutants_more.py, test_mutation_guards.py); (c) suppression guard PARTLY (117 nosec/noqa markers in 53 files, needs a baseline of about 54 lines); (d) gitleaks scope PARTLY (same pinned version; demo lint.yml:48 `gitleaks git .` has no --log-opts=HEAD, so it scans every fetched ref: owner's call); (e) client-profile check NO (demo has no stage model); (f) spend meter NO (core needs a store, demo uses a local file ledger); P2a-1 no counterpart. Recommended order d, c, b(optional), a not for email; e, f, P2a-1 not adopted.
- Name differences found by the builder: the real branch is core/mutation-runner-keywords (plural); PR 90 is not a branch (main commit 2742c1bf); core/P4a-P4b1 is two branches P4a and P4b1. None of the reviewed core branches is merged, so core versions may still change. `gh pr view 89` failed (no gh access): PR 89 state unknown.
- Licence: core is proprietary, demo is all-rights-reserved evaluation-only: putting core code into the public repo is an owner decision. The builder's only side effect: `git fetch origin` in the core checkout (remote-tracking refs only).
- Now running: egm:egm-codebase-details (sonnet) review of the lane 5 file; I save it to reuse/REVIEW-1.md. Lanes 1, 3, 4 running. Lane 6 draft exists; idle CPU sample still waiting. Stuck: nothing.

## 2026-11-12 19:05Z - ORDER D3 read: lane 5 started, lane 6 draft written; 4 agents running (lanes 1, 3, 4, 5)
- Lane 5 (core-to-demo reuse check, sonnet, read-only): started; output reuse/CORE-TO-DEMO.md.
- Lane 6 (machine facts): draft speed/RUNBOOK-INPUTS.md written from measured values (python3 3.13.18 and python3.12 3.12.3, nproc 4, 16 GiB RAM, docker CLI present but no daemon, github and pypi reachable, example.com 403 via proxy). The idle CPU sample is still missing: it needs lanes 1, 3, 4, 5 idle. Your order said lane 6 starts after lane 1 ends; I measured the static facts early because they do not depend on load.
- Lanes 1, 3, 4 still running; no result claimed yet.
- Stuck: nothing. Needs: nothing.

## 19:03Z - lane 2 reviewed: no Blocker/Major; lane 4 started; lanes 1, 3, 4 running (3 agents)
- Lane 2 review saved: drift/REVIEW-1.md (3 doc-wrong confirmed, 3 Nits: wrong JS line cite, 'BOTH FINE' count is an inference, API default by_email=1; limits.md:108 to check). Review was read-only: it could not run git apply or tests; the lane agent's `git apply --check` passed.
- Lane 1 (outsider, python3.12 venv): lint, mypy, bandit, schema, hygiene done (9 passed, 1 skipped, no gitleaks); full pytest running.
- Lane 4 (second outsider pass on pr-3-tests, docker or uv instead of plain venv, 1 pytest process): started.
- Lane 3: patches and evidence files appearing; agent still running.
- Stuck: nothing. Needs: nothing.

## 2026-11-12 19:00Z / 00:30 IST - lane 2 builder done, EGM review of it running; lanes 1 and 3 still running (3 agents)
- Lane 2 (drift): 3 doc-wrong, 0 code-wrong, 1 both-fine, 4 groups unverified. Files: drift/DRIFT-REPORT-1.md, drift/docs-fixes.patch (3 one-line hunks, git apply --check passed on a scratch copy). The lane agent had no Agent tool, so the egm reviewer agents inside the drift skill did NOT run; the Skill call itself was accepted ("Launching skill: egm:egm-drift-report"). Its own full pytest run was stopped at about 35 percent (no count claimed).
- Now running: egm:egm-codebase-details reviewer (sonnet) checking the drift report and patch against the code and hunting for missed drift; I will save its report to drift/REVIEW-1.md.
- Lane 1 outsider and lane 3 triage: files are appearing in outsider/ and triage/, not finished yet; no claim until they report.
- Pushed: lane output files so far (this commit). Stuck: nothing. Needs from lead: nothing.

## 2026-11-12 18:54Z / 00:24 IST - ORDER D2 started: 3 agents running (all model sonnet)
- Lane 1 outsider test (EVIDENCE RUNNER): clone of public repo branch initial-code, setup from README/docs only, 60 min box. Output handover/demo/outsider/.
- Lane 2 drift report (egm:egm-drift-report via Skill tool, run by the lane agent; if it is refused it must stop and say so): output handover/demo/drift/.
- Lane 3 static-analysis triage (builder; egm:egm-codebase-details review by me after): output handover/demo/triage/, patches only, repo untouched.
- Pushed: nothing new yet. Stuck: nothing. Note: the machine has python3.13 as python3, the docs ask for 3.12; lane 1 will record what it did.
- Session model: Sonnet 5.5 now (the earlier Opus switch came from the egm-resolve skill load); no /model needed.
- Limit I must flag: I have no timer, so the 5-minute report is written each time an agent finishes or you message me; I cannot wake myself every 5 minutes.

## 2026-11-12 18:51Z / 00:21 IST - ORDER D1 proof: EGM installed, patched, Skill tool works (no failures)
Claude Code version: 2.1.322. Session model before the skill calls: claude-sonnet-5-5.

1. Install: marketplace add google/elephant-goldfish-model OK; plugin install egm@egm OK. claude plugin list:
    Installed plugins:
    
      > egm@egm
        Version: 0.1.1
        Scope: user
        Status: √ enabled
        Note: Default agents/ folder is ignored because the manifest sets "agents"
    
2. Patch: read handover/tools/egm_model_patch.py first (edits only SKILL.md and agent files under ~/.claude/plugins). Ran it from /tmp copy of origin/core/cloud-handover (same script): 89 files changed in 3 plugin folders.
   grep -rh "^model:" ~/.claude/plugins/*/egm* | sort | uniq -c:
          9 model: claude-opus-5-5
         80 model: claude-sonnet-5-5
   (3 opus per copy, rest sonnet, none inherit.)
   grep -rl disable-model-invocation ~/.claude/plugins/ | grep SKILL: no output (empty).
3. Owner typed /reload-skills. Output: "Reloaded skills: 30 skills available (none added or removed)." After it, the Skill list shows 7 egm:* skills (bootstrap, brainstorm, draft, drift-report, resolve, review, review-loop) and 10 egm:* agent types.
4. Skill tests, exact results:
   - Skill(egm:egm-review-loop, args: <made-up two-line doc> reviewers design,style) -> "Launching skill: egm:egm-review-loop", then the skill text loaded. NOT refused.
   - Skill(egm:egm-resolve) -> "Launching skill: egm:egm-resolve", then the skill text loaded. NOT refused.
   I only proved the Skill tool accepts and loads both skills. I did NOT run the full review loop (no reviewer agents dispatched, nothing spent beyond loading): its intake needs a standards mapping and the owner's confirmation first.
5. Model switch: after the egm-resolve call the session reported "You are powered by the model named Opus 5.5 (claude-opus-5-5)". So the model: line is applied, and the switch to Opus 5.5 persists after the skill load, i.e. the session now runs on Opus, not the standing Sonnet 5.5. Lead: tell me if you want the session set back to Sonnet; I cannot change settings myself.
6. Test document deleted (it was in the session scratchpad, not in the repo). No repo file changed outside handover/demo/REPORT.md. Order mismatch noted: the first chat order said to write handover/cloud-demo/EGM-SETUP-REPLY.md on core/cloud-handover; the newest order (D1) says handover/demo/REPORT.md on demo/handover, which I followed.
Routing in force: Opus 5.5 only egm-brainstorm/draft/resolve; Sonnet 5.5 everything else; Haiku plain lookups; model set on every Agent call.
Status: idle, ready for ORDER D2. Pushed: this file only, to origin demo/handover.

