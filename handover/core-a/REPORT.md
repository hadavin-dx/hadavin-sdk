# REPORT from core-a (newest on top, UTC and IST)

## ORDER 001 proof: EGM IS VISIBLE. 2026-11-20 04:11 UTC / 09:41 IST

**What failed or is not proven (first):**
- The dry run is one round only and is not converged: 2 Major findings stay open on the throwaway paragraph. No resolve step, no fixes, no round 2.
- Only 2 of 10 EGM agents were actually started (style, comprehension). The other 8 are listed by the Agent tool but were not run.
- I chose the reviewer set myself; the skill wants a person to confirm it. Nobody was present.
- Commit trailer: this session's harness requires "Co-Authored-By: Claude Fable 5.2", not the "Claude Sonnet 5.5" line of preamble rule 9. I used the Fable line because Fable did the work. Lead: say if you want it otherwise.
- The session's configured push branch for this repo is claude/pensive-cannon-alwylt; the push to cloud/core-a was done on the order of the person who started the session. Result of the push is in the status block below.
- Studio files on the laptop (bible\RULES.md, memory index) cannot be read from the cloud, so no R-numbers were looked up beyond those quoted in handover/.

**1. EGM skills in the Skill tool (8):**
egm:egm-bootstrap, egm:egm-brainstorm, egm:egm-draft, egm:egm-drift-report, egm:egm-lite, egm:egm-resolve, egm:egm-review, egm:egm-review-loop

**2. EGM agents in the Agent tool (10, exact names):**
egm:egm-bootstrap-orchestrator, egm:egm-codebase-details, egm:egm-comprehension, egm:egm-design, egm:egm-implementation-readiness, egm:egm-inventive-catalyst, egm:egm-structural, egm:egm-style, egm:egm-synthesizer, egm:egm-zoom-out

**3. Model lines:**
```
$ grep -rh "^model:" ~/.claude/plugins/*/egm* | sort | uniq -c
     72 model: claude-fable-5-2
```
Only claude-fable-5-2. No opus, no sonnet, no haiku. Same result when the whole ~/.claude/plugins folder is searched without case.
Plugin: egm@egm 0.1.1, commit 70406c4d, installed 2026-11-20T04:09:10Z.

**4. Session model:** configured claude-fable-5-2, last served claude-fable-5-2 (from the session record).

**5. Dry run:** egm:egm-review-loop started through the Skill tool; 2 reviewers, both with Agent model 'fable', both completed. Round 1: 0 Blocker, 2 Major, 6 Nit. Full output: handover/core-a/egm-dryrun.md. Target: handover/core-a/egm-dryrun-target.md.

**Rules used:** MODEL-ROUTING (all Fable, model set on every Agent call), preamble 4 (no spend, no live product model call), 6 (honest report), 13 (EGM skipped for the order itself: status check), 19 (no loops, no background process left), 23 RIGHT-SIZE (this is a manual one-off step, about 3 minutes of clock), R456.
CODE-LAST n/a: proof step, no component created.
Token use: 2 reviewer agents, 20,311 tokens together; main session not metered here.
Files changed: handover/core-a/REPORT.md, egm-dryrun.md, egm-dryrun-target.md. Nothing outside handover/core-a/.

### Status block 04:11 UTC / 09:41 IST
Push: proof commit 484172c pushed to cloud/core-a at 04:11 UTC, accepted by GitHub (fd9d08d..484172c).
ORDER: 001. STATE: WAITING-LEAD (waiting for GO). Agents running: 0 language-model agents, 0 script lanes (2 started, 2 finished, none lost). Background processes: none. Next: nothing until ORDERS.md has a line starting with GO.
Note: a cloud session only acts when it receives a message, so the "status block every 10 minutes" rule cannot run while it waits; no timer was set (no unbounded loops, rule 19). Send GO as a message or as a new order plus a message.
