# Timelines: the course calendar vs Hadavin's compressed calendar

**Rule:** compress the calendar, never the stages. Every stage in `LIFECYCLE.md` still produces its exit artifact and keeps its exit point.

**Names:** text a client reads says Hadavin; this file is studio-internal and keeps the old folder names until the rename gate runs (README "Names").

**Sources:**
- the course: topic 02 and `LIFECYCLE.md`;
- market evidence: `..\research\research_notes\FDE stack and AI software factory 2026\compressed_timelines.md`, 2026-10-29.

## Course calendar (12 weeks)

| Stage | Weeks | Exit artifact |
|---|---|---|
| 1 Discovery and scoping | 1–2 | `scoping.md` with a success number; eval contract |
| 2 Prototype | 3–5 | demo on real data that a real user called useful |
| 3 Pilot | 6–9 | `success-criteria.md` agreed first; numbers report and the sponsor's verdict |
| 4 Hardening and handoff | 10–12 | named owner; runbook; the customer has run it; monitoring runs without us |

## Hadavin calendar (typical build: 6–8 weeks)

| Day / week | Stage | What happens | Exit artifact |
|---|---|---|---|
| Day 0 (entry condition) | — | Signed order paid (a Blueprint is 100% upfront; a direct Core order follows the free call and the architecture plan, with no free sample check; payments follow the one schedule of decisions 2026-11-01 evening item 5), **data and system access granted**, sponsor named (`..\egm\pricing\pricing-plan.md` §3.2.3, §3.5). Real client data stays in the client's environment until the data-handling rule exists (PLAYBOOK 0.10). Superseded by this text on 2026-11-01: "a direct order follows the free sample check" | access checklist ticked |
| Days 1–5 (Incident Response: the Replay Check, report within 15 working days of the client's export; it is client-owned, so log the delay) | 1 Discovery: the "Blueprint" | interviews, the three filters, baseline, sample measurement (20–50 samples), accuracy target agreed in writing (set in week 1 of the paid phase) | `scoping.md` + eval contract + the frozen tuning set and sealed scoring set (checksums); the build order's fixed price is pinned to the signed `scoping.md` (R35) |
| Days 6–15 (2 weeks) | 2 Prototype → build | proof of concept on real data by about day 4 of the stage, then the build, with the golden set and gate running in CI from the start | demo on real data; gate green |
| End of days 6–15 | 3 Pilot, its "build the proof" step (LIFECYCLE Stage 3 step 3) [Hadavin practice] | the full golden set, judge, gate and score report; the acceptance run on the frozen test set. The client's engineer runs the frozen scoring script on the sealed set. Target met → the final payment falls due (Net 14), and **the user-pilot group goes live only after it** (pricing-plan §3.2, §3.5: live use before the final payment makes it due; exception: the Incident Response watch-only pilot may read live alerts read-only before it, pricing-plan §3.2.5) | scores + gate green; acceptance report; `cost-estimate.md` |
| Weeks 4–6 or more | 3 Pilot (the **user pilot**, Step 3b; not Week 1) | **at least 3 weeks**: week 1 for teething, then a final measurement window of at least 2 weeks that excludes week 1 (R253); **4 weeks if the KPI follows a weekly or monthly business cycle**; weekly thumbs-down review. Superseded by this text on 2026-11-01: "at least 2 weeks" | numbers report and verdict against `success-criteria.md` |
| After the pilot's "go" verdict (day-one guards built in the build; training started in the pilot), at least 1 week | 4 Hardening and handoff | guardrails, cost caps, logs and monitoring are built before go-live and prove themselves during the pilot; training goes "you do / they do with you / they do alone" from the pilot on; stage 4 itself starts only on the pilot's "go" (LIFECYCLE Stage 4 entry) and ends with the exit-test week: the customer runs a full week, including one failure, without us (02 L2) | owner named, runbook, a week run without us |

**What cannot be compressed** (it belongs to the client; say so in the SOW and log every client delay):
- data and system access;
- the client's security review (the delay cited most often in surveys);
- stakeholder interview slots;
- the pilot measurement window;
- the client's review and approval time.

## Running deals in parallel
- **At most 3 projects in active build.** Others wait in a waiting stage (access pending, pilot measuring, client review).
- **Human review is the bottleneck:** land one significant change at a time per project. Research and small tasks can run in parallel agents, each in its own checkout.
- Each project has its own repo; its memory (`memory\projects\<project>\`) and handoff (`handoff\projects\<project>.md`)
  live in the Hadavin main folder. No client data or prompts cross between projects.
- **Cost of starting a project, kept low by reuse:** hadavin-sdk modules, the golden-set and gate templates, the runbook and README templates (topic 44's deliverables list), and the lifecycle checklists.

## Evidence quality
- Most market timelines come from agencies' own offer pages, not audited case studies. Use them as ranges, not promises.
- Re-check them before quoting a client.
- Re-check the pricing and payment terms in `pricing-plan.md` the day you quote; this file does not carry prices.
