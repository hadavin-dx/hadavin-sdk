# ORDERS for core-hardening (lead to cloud). Newest last. Order text starting with GO lifts the hold.

## ORDER 001 (lead, 2026-11-16 SETUP ONLY, no work yet)
You are the cloud session "core-hardening" for Hadavin, reporting to the laptop lead. This is a NEW session.
1. git fetch, check out branch core/cloud-handover (git checkout -B core/cloud-handover origin/core/cloud-handover), pull.
2. Read handover/core-hardening/README.md, handover/BRIEF-PREAMBLE.md, handover/MODEL-ROUTING.md, handover/RULE-R456-WORK-CONDUCT.md.
3. EGM setup (handover/CLOUD-EGM-SETUP-2026-11-12.md): /plugin marketplace add google/elephant-goldfish-model, /plugin install egm@egm, reload. Then run python3 handover/tools/egm_model_patch.py (Opus 5.5 for egm-brainstorm, egm-draft, egm-resolve; Sonnet 5.5 for egm-review, review-loop, drift-report, bootstrap and every egm reviewer agent). Prove it: list the 7 egm:egm-* skills, list the egm:* agents, and paste the output of: grep -rh "^model:" ~/.claude/plugins/*/egm* | sort | uniq -c
4. Models: this session runs Sonnet 5.5; EVERY Agent call sets model explicitly (opus 5.5 only for plan skills, sonnet 5.5 for builders/reviewers/evidence runners, haiku 5.5 only for plain lookups). EGM only through the Skill tool, never by reading SKILL.md. Never native plan mode.
5. If the plugin install is blocked, STOP and write exactly what was refused. Never use a general-purpose agent as reviewer.
6. Write the proof into handover/core-hardening/REPORT.md (top block, UTC and IST, FILE-INDEX line), commit, push to core/cloud-handover (git push origin HEAD:core/cloud-handover).
7. Start NO work until an order starting with GO appears in this file. Rules: no secrets, no real data, no spend, no live model calls, no merges, no pushes to any other branch, register every agent before starting it, status block at least every 10 minutes.
