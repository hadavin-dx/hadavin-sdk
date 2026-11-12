---
name: no-lost-messages-isolation-load
description: "HARD RULE (owner 2026-11-01): no inbound message/email may be lost or double-applied (even in a burst of 10), users/tenants never affect each other whatever names/data/counts, and every build is load-tested at very hard big-company numbers with free tools"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1c82e358-dcf8-4402-88bb-431ce10c72d0
  modified: 2026-11-01T13:14:22.496Z
---

Owner 2026-11-01: "even things like immediate messages, emails: sometimes in 10 continuous ones a few misses, so no such things should be done on our projects ... no matter how many users and with their names and data, none should be affected by one another ... number of users at once: give a very hard number on tests which really big companies face, with any tools to replicate them. Keep them in memory and rules and other places."

**Why:** the studio sells "mistakes cannot cause damage"; one dropped order email or one cross-tenant leak ends a first client relationship. The owner also wants every honest limit a builder states (no sealed split, accepted exposure, 214 cases) fixed, not documented.

**How to apply (every design, PR, review):**
1. Bible rules R368 (no lost or double-applied messages: write-ahead receipt, at-least-once plus idempotency, terminal state for every message, reconciliation against the source's own ids, dead-letter, backpressure not drop, burst test with injected faults), R369 (tenant/user isolation enforced in the data layer, colliding names and ids stay separate, per-tenant canaries, cross-tenant negative tests) and R370 (hard load numbers from the client's real peak, 3x peak, spike, soak, fault injection, free tools k6/Locust/Vegeta/Toxiproxy against fakes, written pass criteria, raw numbers).
2. A builder's "accepted exposure", "known limitation" or "documented" is a defect to fix, not to ship (see [[fix-dont-defer-be-honest]]). Forged-input exposures get a control, not a note.
3. Load tests run locally against fakes: no spend, no live model call without numbers and the owner's yes ([[approvals-2026-11-01]]).
4. Demos use the "large enterprise" profile in `egm\load-and-isolation\` until a client's own numbers exist.
5. Segregation of demos, clients and training (owner 2026-11-01: "demo-related data or training outputs must not affect clients' outputs and data; one demo's or client's data and LLM training must not affect others"): bible R371. Per client and per demo its own store, index, embeddings, cache, few-shot, eval sets, logs, secrets, model config and cloud project; no cross-client learning, shared fine-tune or shared prompt cache; fine-tunes only on that client's own data; provider no-training setting stated with date; canary test across clients; A's outputs unchanged when B's data changes.
6. Purpose limitation and small blast radius (owner 2026-11-01: "AI must not affect any client's systems, no data leakage, no AI using data for work it should not do"): bible R372. Data used only for the stated job and needed fields; no training/analytics/other-client use; reads via read-only replica/role with rate and connection caps; writes only via the governed executor (dry-run default, approval, idempotency, caps, kill switch, undo); no schema/bulk-delete/permission/credential change by an agent; egress allowlist and DLP check on outputs; provider no-training setting dated; every read logged and client-reviewable; negative tests per control.
7. One repo per client, clean-template export (owner 2026-11-01: "those stuff should not reach our demo repo; always a separate repo per client, copy the demo-related project to it and train there; trained data and its effect on outputs must not carry to other clients; could leak policies or other companies' names"): bible R373. Demo repos = code + config schema + synthetic data only; client repo created fresh by an export script with new git history; training/tuning/eval only inside the client's repo and environment; hygiene scan (deny-list of other clients' names, canaries, file-type rules, manifest diff) before the first commit; client-specific policies and prompts live in that client's config only.
Related: [[class-level-fixes]], [[least-privilege-hard-rule]], [[vision-reliability]].
