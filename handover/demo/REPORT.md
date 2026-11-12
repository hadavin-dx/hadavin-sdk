# DEMO session report (the ONE file this session reports to the lead in; newest block on top)
Session: https://claude.ai/code/session_014pRo36uYfYwuEDby9epxu8. Write a status block at least every 10 minutes (UTC and IST, what runs, what is pushed, what is stuck, what you need from the lead).

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

