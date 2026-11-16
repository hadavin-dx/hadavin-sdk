# ORDERS for flows-audit (lead to cloud). Newest last. Order text starting with GO lifts the hold.

## ORDER 001 (lead, 2026-11-16 SETUP ONLY, no work yet)
You are the cloud session "flows-audit" for Hadavin, reporting to the laptop lead. This is a NEW session.
1. git fetch, check out branch demo/handover (git checkout -B demo/handover origin/demo/handover), pull.
2. Read handover/flows-audit/README.md, handover/BRIEF-PREAMBLE.md, handover/MODEL-ROUTING.md, handover/RULE-R456-WORK-CONDUCT.md.
3. EGM setup (handover/CLOUD-EGM-SETUP-2026-11-12.md): /plugin marketplace add google/elephant-goldfish-model, /plugin install egm@egm, reload. Then run python3 handover/tools/egm_model_patch.py (Opus 5.5 for egm-brainstorm, egm-draft, egm-resolve; Sonnet 5.5 for egm-review, review-loop, drift-report, bootstrap and every egm reviewer agent). Prove it: list the 7 egm:egm-* skills, list the egm:* agents, and paste the output of: grep -rh "^model:" ~/.claude/plugins/*/egm* | sort | uniq -c
4. Models: this session runs Sonnet 5.5; EVERY Agent call sets model explicitly (opus 5.5 only for plan skills, sonnet 5.5 for builders/reviewers/evidence runners, haiku 5.5 only for plain lookups). EGM only through the Skill tool, never by reading SKILL.md. Never native plan mode.
5. If the plugin install is blocked, STOP and write exactly what was refused. Never use a general-purpose agent as reviewer.
6. Write the proof into handover/flows-audit/REPORT.md (top block, UTC and IST, FILE-INDEX line), commit, push to demo/handover (git push origin HEAD:demo/handover).
7. Start NO work until an order starting with GO appears in this file. Rules: no secrets, no real data, no spend, no live model calls, no merges, no pushes to any other branch, register every agent before starting it, status block at least every 10 minutes.

## ORDER 002 (lead, 2026-11-16, RETRY of ORDER 001 setup; still NO work)
The owner APPROVED the EGM plugin install for this session. Redo ORDER 001 steps 3 to 6 now: claude plugin marketplace add google/elephant-goldfish-model (if not yet), claude plugin install egm@egm, python3 handover/tools/egm_model_patch.py (setup docs are now in handover/CLOUD-EGM-SETUP-2026-11-12.md and handover/EGM-CHILD-HOWTO.md), then the proof (7 egm skills, egm agents, grep model: lines) at the top of handover/flows-audit/REPORT.md, commit, push to demo/handover. If the skills do not show in this session after install, say so and tell me whether a new session is needed. Still start NO work until an order starting with GO.

## ORDER 003 (lead, 2026-11-16, PROOF ONLY, still NO work)
Install and patch are accepted (thank you). Now check whether egm skills and agents are visible to you: list the egm:egm-* skills in your Skill tool and the egm:* agents in your Agent tool (names exactly as shown). If still unknown, do NOT retry the install; write "NOT VISIBLE" at the top of handover/flows-audit/REPORT.md with the exact lists you do see, commit, push to demo/handover and stop. If visible, run the dry run (egm:egm-review-loop on a 3-line test paragraph, model shown), save its output to handover/flows-audit/egm-dryrun.md, report, push, and wait for GO.
