# PLAN READ-BACK of core-b, role SPINE (2026-11-20 05:22 UTC / 10:52 IST)
Read in full: inputs/plan-v2.md, plan-v3.md, plan-v4-final.md, review-plan-3-codebase.md, review-plan-3-zoom-out.md, draft-tickets-C-D.md, lead-baselines-SUMMARY.md, TICKET-TEMPLATE.md. NOT read: old-plan-v4-1.md, old-plan-v4-3.md, atlas-n8n.md, both inventories, the round 1 and 2 reviews and resolve-plan-1.md (plan-v4-final replaces them; I open them only where a ticket needs a fact).

## 1. My steps, in build order (plan-v4-final B1)
| step | what I build | migration | ticket review |
|---|---|---|---|
| A | Audit drain: a new tick step (not named reconcile) writes parked audit events from the outbox table; the runtime process also writes its own in-memory parked events at its next write; says what happens when the card note fails; the test crosses a process boundary. Also: README and SECURITY get ONLY the "not guaranteed by the core this round" list (B3). | none | none |
| B | Stop state with a separate reset identity: the runtime's database role may switch stop ON but not OFF; a reset role may switch it OFF and may append audit; the limits reset command takes its own reset connection string. | 0006 | one round |
| C | Price constraint: a config with a zero, negative or not-finite price is refused at load (zero allowed only for the fake model kind in the demo stage); a prices_as_of date on Config, required in pilot and prod. | none | one round |
| D (my part) | Config fields for the signed endpoint (TriggerSender, TriggerSettings, Config.triggers), the registry cross-check, and one App field so the worker can read the sender secrets. The endpoint and worker files are core-a's. | none | reviewed with core-a's ticket |
| F-store | Reserve before a model call and settle after it: store methods, memory and PostgreSQL implementations, grants; installing core-c's gate wrapper inside Runtime.__init__, _replay and evals.gate; deleting the five charge sites; Budget gets reserve and settle with a lock; binding the judge per call; charging the shadow-card judge call; deleting extract.py with its tests and fixtures; expired-reservation sweep tick step; test T1 with 50 separate connections. | 0007 | one round, together with core-c's wrapper ticket |
| H (store part) | Only if a failing case proves a gap. The lead's draft (finding 2) says no gap is left: CUT unless a review finds one. | 0008 only if proven | cut |
Interface tickets come FIRST: (i) store methods, (ii) reserve/settle API, as a Protocol addition plus signatures in handover/core-b/interfaces/.

## 2. My files
Every EXISTING file of the package and tests, and all persistence (plan-v3 A1): store Protocol, memory and PostgreSQL stores, migrations, store/migrate.py, tick STEPS, app.py, cli.py, config.py, limits.py, evals.py, k1b/*, guard/judge.py, llm/*, pyproject, lock file, CHANGELOG, README, tests/conftest.py, tests/fixtures/migrations_released.json, the store contract test.

## 3. What I must NOT touch or do
- core-c (TEXT) owns guard/textnorm*, guard/redact.py, guard/runmap.py, the wording in approvals/gate.py lines 42-44, 59, 63, and the NEW gate wrapper module. core-a (DOOR) owns the NEW triggers/ package, testing/ helpers and the n8n pack.
- No source code before "GO BUILD <letter>" in ORDERS.md, except step A (and E, which is not mine).
- No merge, no force-push, no push except cloud/core-b and wip/cloud-core-b/*; input branches (core/*, PR branches) are read-only.
- No migration applied to a lasting database; no new store kind; no live executor; no tier 2 code; no stub merged; no scanner finding dismissed; no .gitleaksignore change.
- No secrets, no live model call, no spend. Stage names only demo, pilot, prod. No project words in core types.
- A positive guarantee sentence enters README or SECURITY only in the change that lands its step (B3).

## 4. Conflicts I see between the inputs (lead: please rule)
1. Migration numbers: plan-v3 A1 says 0006 reservations, 0007 stop state; plan-v4-final B1 and ORDER 004 say 0006 stop state, 0007 reservations. I follow plan-v4-final (later file wins).
2. Step D shape: plan-v4-final B1 describes a separate worker; the lead's draft ticket (finding 1) makes endpoint and worker ONE process with no table. I follow the draft for the config fields.
3. as_of: plan-v4-final step C says "dated as_of" without a place; the draft ticket (finding 3) puts prices_as_of on Config, not Route, so agents do not lose their qualification on a price refresh. I follow the draft.
4. Commit trailer: BRIEF-PREAMBLE rule 9 says Sonnet 5.5; plan-v2 section 5 says the session harness line (Fable 5.2). I use the harness line.

## 5. Open questions (also in QUESTIONS.md)
1. The one-minute board cron is refused by this session's permission check (ESCALATIONS.md E1, tried twice). Is a board at the end of each tool batch acceptable?
2. Baselines: the summary has only core/P2a-1 and core/P4a (1 failed each). Which test fails, and is it the same on main? The tickets must label it INHERITED.
3. Step A exception: may I cut wip/cloud-core-b/A and build as soon as the ticket is written, without a further GO (ORDER 004 item 5 reads that way)?
4. T1 needs 50 separate PostgreSQL connections. This container runs PostgreSQL 16 without Docker (CAPABILITY.md). May my own lane run use it, as an extra signal only?

## 6. Facts I have checked myself so far (origin/main 51c9fc4)
- store/protocol.py:107-116: add_spend, spend_totals, get_kill_switch, set_kill_switch are the only money and stop methods; no reserve or settle exists.
- limits.py:17-30: charge() adds spend after the call; blocked() reads totals: no pre-call hold. limits.py:43-51: stop writes the switch then audit; reset writes audit intent then the switch; both through the same store.
- k1b/loop.py:40-52: Budget has limit, spent, charge, exhausted; no lock, no reserve.
Everything else in the tickets will cite the lookup notes in handover/core-b/notes/ (three lookup agents are reading main and the input branches now).
