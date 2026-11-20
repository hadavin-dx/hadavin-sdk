# ORDERS for core-c (lead to cloud). Newest last. Text starting with GO lifts the hold.

## ORDER 001 (lead, 2026-11-20 04:06 UTC) PROOF ONLY, no work
You are cloud session "core-c" for Hadavin (module builder C: kit and promotions (Jagrat and portal generics, document reader, deploy kit, recipes, harness)), reporting to the laptop lead.
1. Work only on branch cloud/core-c (already checked out) and in handover/core-c/. Read handover/BRIEF-PREAMBLE.md, MODEL-ROUTING.md, RULE-R456-WORK-CONDUCT.md.
2. EGM must already be installed by the environment setup. Prove it at the top of handover/core-c/REPORT.md: the egm:egm-* skills in your Skill tool, the egm:* agents in your Agent tool (exact names), and the output of: grep -rh "^model:" ~/.claude/plugins/*/egm* | sort | uniq -c (TEMP owner 2026-11-19: expect only claude-fable-5-2 lines, no opus or sonnet).
3. If not visible: write NOT VISIBLE with the lists you see, do not retry the install, commit, push to cloud/core-c, stop.
4. If visible: run egm:egm-review-loop on a 3-line test paragraph, save to handover/core-c/egm-dryrun.md, report, push, wait for GO.
Rules: every Agent call sets model explicitly (TEMP owner 2026-11-19: model 'fable' on every call, Fable 5.2 for all work); EGM only via the Skill tool; no secrets, no spend, no live model calls, no merges, no push to any other branch; status block every 10 minutes in REPORT.md (UTC and IST).
