---
name: parallel-agents-and-build-now
description: "Owner 2026-11-03 (said multiple times): run independent work in parallel agents, finish fast at production grade, use EGM everywhere; stop over-reviewing plans"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 3c13c170-55b8-4c77-8cca-2988a10a077d
  modified: 2026-11-03T14:10:51.462Z
---

Owner message 2026-11-03: "why are you not using multiple agents, I said multiple times use multiple agents in parallel which do not depend on others' work, complete as quick as possible but with top notch premium production grade level" and "make sure you are using egm everywhere".

**Why:** the lead spent the session on 16 review rounds of the Intake plan and nothing was built; core PRs, the portal and the demos were idle; the owner read that as not using parallel agents.
**How to apply:** (1) After a plan has two clean-ish rounds (0 blockers), freeze it, write errata, and start builders; let each work package's own EGM result review catch the rest. Do not run more than 3 plan-review rounds on any plan. (2) Launch every independent piece of work as its own builder in its own git worktree at once (core PR WIPs, each Intake work package whose dependencies are met, portal, Jagrat, website). (3) Builders build and record evidence only; the lead runs the egm:* result reviewers, `egm:egm-resolve` and the drift report, with the blocker ledger updated the same turn. (4) Keep the lead's own turns short: report numbers, not essays. Related: [[egm-review-routing]], [[review-loop-speed-rules]], [[jagrat-not-paused-priorities]].

There is no fixed agent cap; supervision (see the agent supervision rule) is the control.
