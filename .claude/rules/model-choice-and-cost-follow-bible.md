---
name: model-choice-and-cost-follow-bible
description: "owner HARD rule 2026-11-04: tools, projects, demos, core modules, portals and future projects choose models and control cost exactly as the bible says (R110, R211-R216, R278-R292, R335); the the demo test budget is ONLY for demo test calls, never for tooling tokens"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 3c13c170-55b8-4c77-8cca-2988a10a077d
  modified: 2026-11-04T12:21:10.780Z
---

Owner 2026-11-04: "The API budget is for demo test calls only, not for tooling tokens. Tools, projects, demos, future projects, core modules and client portals must all use the models that cost control, quality and speed say, as in the Geeta/bible. Do not go against it. Be brutally honest, do multiple checks, double check everything against the bible."

**Why:** the bible rules are the base of every project; the demo test budget window is a testing budget for the live model calls the demo makes, not a pot for agent/tool tokens.

**How to apply (checked against the bible 2026-11-04):**
- Model choice is made per workload BEFORE launch, from evidence (course, Topic 7, R278-R281): profile the workload (how hard is one call, is a person waiting, calls per day, plus what a wrong answer costs: the course shows this last one in its examples, R278); run ~20 real or approved examples [Hadavin practice: synthetic in demos, the client's real samples in the pilot] on the cheap candidate (hard, low-volume steps go to the strong model directly on the course chart; a cheap test there is optional); run the stronger tier on those same 20 only if the cheap one falls short, side by side (R279; R283 never a whole batch through both); pick ONE model per workload. [Hadavin practice] Tiers go Haiku 5.5 -> Sonnet 5.5 -> Opus 5.5 one at a time with the eval result written down (R290).
- At run time a workload uses its one chosen model, or sits behind a classify-first router (course, Topic 33, R213): a cheap classifier picks the lane BEFORE the answer is generated, the decision is logged, and any doubt goes to the strong lane ("wrong-and-expensive beats wrong-and-cheap"). [Hadavin practice] "Cheap model first, retry on the strong one if it fails" is NOT a course pattern; it may run only as a labelled TRIAL with its own eval, a logged override rate and the owner's yes (R290, R424). Correction 2026-11-04: an earlier version of this note called a Haiku-first cascade with one Sonnet retry "the written substitute"; that was wrong (`egm\course-reread\CONSOLIDATED-1-engineering.md` A1).
- Money, approval and permission steps: a fallback answer passes the same checks, is marked `fell_back=true`, never triggers the action by itself, and prefers the same tier, then the strong tier, then a person ([Hadavin practice], R219).
- Two saving levers in this order (R211): exact-match response cache, then classify-first router; the hard budget in code is not a third lever, it is on from the first live call (R214); cache the stable prefix with an explicit TTL (R216, R335); per-run token and cost budget (R110); reserve before the call, reconcile after (R214); fail loudly at the budget wall with a log line AND an alert to a person (R215); log tokens, latency, route, fallback, cache hit, prompt version, purpose (R221, R226).
- Model ids come from config and the official page, dated (R16/R17/R292). Checked 2026-11-04 on platform.claude.com models overview: `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5` (and `claude-fable-5-1`). Pricing 2026-11-04: Haiku 5.5 $0.10 in / $0.50 out per MTok for prompts up to 100,000 tokens (cache read $0.01), $0.50 / $2.50 above 100,000; Sonnet 5.5 $2 / $10 (cache read $0.10); Opus 5.5 $4 / $20; Batch 50% off. Sonnet 5.5 rejects `thinking: disabled` (it accepts `between_tools`): extra_body must be per tier.
- Tooling (Claude Code agents, reviewers, evidence runners): separate cost from the the demo test budget; Sonnet 5.5 for building and review, Opus 5.5 only for planning skills, Haiku for plain lookups; read only needed lines; never re-run an unchanged check; report spend in two buckets: demo-test-calls (ledger, tagged by purpose) and tooling.
- No live call without the owner's numbers and the cap/limit steps; the code must enforce the end date of the window.

Related: [[live-model-budget-2026-11-03]], [[agent-speed-estimates]], [[tool-ladder-before-code]], [[mac-studio-plan-2027]]
