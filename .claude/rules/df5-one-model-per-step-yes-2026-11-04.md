---
name: df5-one-model-per-step-yes-2026-11-04
description: Owner yes 2026-11-04 to change Intake DF5 from a Haiku-then-Sonnet run-time cascade to ONE model per step chosen up front from evidence; Sonnet 5.5 on the money-bearing read until evidence says otherwise
metadata:
  node_type: memory
  type: project
  originSessionId: 3c13c170-55b8-4c77-8cca-2988a10a077d
  modified: 2026-11-04T12:57:00.357Z
---

Owner said "yes df5" on 2026-11-04, after the lead explained that the course (Topic 7 design-time choice, Topic 33 up-front router, book Ch 5 p.122 / Ch 6 p.175) teaches no run-time "cheap first, retry on strong" cascade, and that three independent audits plus the code audit found the cascade in Intake (`model.py`, `extract.py`, test pin) and in cost-controls decisions-1 #4 / design-v2:71.

**Decision (what the owner approved):**
- Intake read step uses ONE model chosen up front. Default: Sonnet 5.5 (hard, low volume, money-bearing field extraction: course Topic 7 sends this class straight to the stronger model). Haiku 5.5 may take the step only after a dated side-by-side evidence file (about 20 masked made-up invoices, exact-field agreement incl. total_minor) shows no loss; that is a config change, never a run-time retry.
- No call-then-retry-on-another-model for quality (`max_tokens`, `bad_reply`, `over_cap`, grounding failures go to a person via a visible flag). A fallback model is allowed ONLY for transport/availability errors (timeout, 5xx, 429 after bounded backoff), same guards, `fell_back=true` logged and shown to the approver (R219, studio money-path clause).
- Worst-case spend per document becomes ONE Sonnet call instead of Haiku plus Sonnet; normal invoices cost more per call (Sonnet US$2/10 per MTok vs Haiku US$0.10/0.50 up to 100K prompt tokens, official pages 2026-11-04). The minimum provider limit (`min_limit_usd`) is recomputed after the change and stated to the owner before any live call; the total cap for live calls is the demo test budget (owner 2026-11-04, replaces the earlier US$100 Intake cap).

**Why:** course fidelity (R213, R219, R278-R290 as corrected 2026-11-04) and safety: a cheap read that is wrong but passes the checks is accepted as "done".
**How to apply:** cost-controls design-v4 and the Intake extract/model code and tests are changed through EGM (plan review, build, evidence, result review); update decisions-1 #4, design-v2/v3 wording, DF5 in FOLLOW-UPS; supersedes the "Haiku-first cascade" lines in [[model-choice-and-cost-follow-bible]]. Live-call rules unchanged: numbers and the owner's yes first.
