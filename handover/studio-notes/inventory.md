# Core completion: Phase 0 inventory summary (lead, 2026-11-05 ~13:50Z)

Detail files (read them, tables live there): inventory-A.md (core repo, PRs, WP status), inventory-B.md (Intake + portal kit), inventory-C.md (Jagrat + reference), inventory-D.md (Apexc, DealDesk, Refunds, website).
All four are leads from docstrings and file names: function bodies, diffs between copies and test state were NOT verified. Phase 1 packages must start with a verification step.

## Verified by the lead this session
- origin/main = ce70eb5 (PR #42 K5-core, merged 2026-11-04). Local checkout main = 6608146, and every demo pin is 6608146. Branches C18a, C1a, PR #50 local are based on the old main: rebase conflicts expected.
- `ledger_check --topic core` was broken by raw newlines inside rows BL-core-c1a-015 and BL-core-pr50-r3-001; lead repaired the two rows (joined with " [newline] "); it now runs and reports 83 unresolved core rows (real).

## Cross-cutting findings (need a plan decision)
1. Conflicts: PR #49 and PR #50 both add `guard/textnorm.py` (different content), both touch limits.py, approvals/gate.py, models.py, store/*, and migration number 0005 collides. Demos' textnorm copies have drifted (3 versions).
2. Three reserve-and-settle money designs: Intake budget.py, PR #48 llm/metered.py, PR #49 store/reservations.py (+ core askdata/meter.py). One core design needed.
3. Most generic Intake code is unpinned (budget, workqueue, inbox, decisions, lockfile, secret_store, sink_guard, service...). Intake worktrees differ by lane (inbox.py 70/317/897 lines): one named source branch per capability before promotion.
4. Jagrat is a trimmed copy of Warden (Apache-2.0, owner-authored); promote once, from Warden, names stripped. Not in core: grounding, numbers check, quarantine, freeze windows, environment policy, autonomy levels, breaker, heartbeat, cascading kill, passkeys, vault, model routing, MCP schemas (batches P-A, P-B, P-C in inventory-C).
5. Generic candidates in demos not in core/PR: inbound message ledger (high value, different terminal states per demo), tenant namespace helper, RateCap/ReadLog, least-privilege authorize/requires, canonical JSON ASCII form, dev signer/Ed25519 split, money parsing (demos disagree on negatives), test helpers (rng, FakeClock, FaultSchedule), data-source loader, no-training lock, mutation runners (3 copies; Intake's KILLED/CRASH split is best).
6. Lock-in gaps: executor only http; channel fake+slack; store postgres only durable; no redactor kind on main, C1a has no second backend; store/migrate.py imports psycopg.sql outside kind.
7. WP status: in branch/PR: C1a, C17 (PR48), C18a (superseded by frozen redesign). Not started in core: C1b/c/d, C1f, KERNEL-1, C2, C3, C4a, C8, C9, C18b.
8. Open core ledger: c18a 32 MAJOR, c1a 27, pr50 19 (+ others); none for #41,#43,#47,#48,#49.

## Owner decisions this plan needs (ask once, plain words)
- D-kit: is the portal kit a separate package (today) or a core module? (rule 2026-11-02 says core modules identical everywhere.)
- D-killswitch: copy agent-killswitch into core or depend on the PyPI package behind a kind (no-single-dependency says a kind).
- D-licence: core licence not checked; promoting from Apache Warden copy needs it confirmed.
