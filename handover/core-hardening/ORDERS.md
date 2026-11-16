# ORDERS for core-hardening (lead to cloud). Newest last. Text starting with GO lifts the hold.

## ORDER 001 (lead, 2026-11-16 06:32 UTC) PROOF ONLY, no work
You are cloud session "core-hardening" for Hadavin (hadavin-sdk core hardening r7u/r7v, EV7U, mutant survivors, core part of architecture audit), reporting to the laptop lead.
1. Work only on branch cloud/core-hardening (already checked out) and in handover/core-hardening/. Read handover/BRIEF-PREAMBLE.md, MODEL-ROUTING.md, RULE-R456-WORK-CONDUCT.md.
2. EGM must already be installed by the environment setup. Prove it at the top of handover/core-hardening/REPORT.md: the egm:egm-* skills in your Skill tool, the egm:* agents in your Agent tool (exact names), and the output of: grep -rh "^model:" ~/.claude/plugins/*/egm* | sort | uniq -c (expect 6 opus-5-5, 64 sonnet-5-5).
3. If not visible: write NOT VISIBLE with the lists you see, do not retry the install, commit, push to cloud/core-hardening, stop.
4. If visible: run egm:egm-review-loop on a 3-line test paragraph, save to handover/core-hardening/egm-dryrun.md, report, push, wait for GO.
Rules: every Agent call sets model explicitly (opus 5.5 only for egm-brainstorm/draft/resolve, sonnet 5.5 otherwise, haiku 5.5 plain lookups); EGM only via the Skill tool; no secrets, no spend, no live model calls, no merges, no push to any other branch; status block every 10 minutes in REPORT.md (UTC and IST).
