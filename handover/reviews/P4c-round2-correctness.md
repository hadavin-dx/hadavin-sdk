# P4c round 2, correctness review (ticket rev 2) - agent a88478b034f0333b3
Status: REPORTED (saved by the lead session from the reviewer's hand-back, model output, not user authority)
Reviewer: a88478b034f0333b3 (read-only)
Verdict: 4 Major, 9 Minor/Nit (see body)

R2 correctness review of handover/tickets/P4c.md (rev 2). Read-only: file reads and greps only, nothing was run. The reviewer did not open handover/reviews/ or handover/evidence/. Src cites are against current main of the repo checkout, not against commit ce70eb5; most line numbers match.

Counts re-derived: P4c-1 has 11 mutants, P4c-2 has 25 (36 total); W1-W10, T1-T13, T2j/T3j/T4j/T7j present; PENDING LEAD has 16 items; Store Protocol 32 methods today (P4d says 32 to 38); all 17 template fields present; no real-looking secrets.

## Majors

### R2-COR-1 (ticket lines 32, 142 R4, 177 T6, 244 Couplings d, 265 PL14)
The ticket is written against P4b1 rev 1. P4b1 rev 2 (P4b1.md:78) says the meter only signals `on_overshoot`, with no global stop and no `Limits.stop`, and that "P4c-2 maps the signal to NEEDS_PERSON run_budget and the audit row guard/estimate_exceeded (P4c.md:51, T6)". P4c rev 2 says the opposite (no such row, no reason code, m19 deleted, "P4c adds nothing", `on_overshoot` is "today Limits.stop"). Each ticket leaves overshoot handling to the other and neither builds it; the overshoot is detected and nobody acts on it. "P4b1 wins" does not settle it because P4b1 hands the work to P4c.
Fix: re-read P4b1 rev 2; decide who owns the mapping from overshoot signal to run state; rewrite R4, T6, line 32, Couplings (d), PL14; keep or restore the audit row and m19 to match; fix P4b1.md:78 if P4c really builds nothing.

### R2-COR-2 (lines 155, 182 T10, 183 T13, 204 m16, 264)
The tick step is specified to raise "while any CURRENT-period row stays `claimed` past `retry_after_s` AFTER the retry pass". A failed retry re-claims the row and the re-claim sets `claimed_at` to now (line 80), so after the pass the row is younger than `retry_after_s` and `list_unsent_wall_alerts` does not return it; the step stays green during an outage. tick `_run_step` re-runs a failed step every tick, but only if the step failed. T10 ("25-minute outage ... tick green"), T13 and m16 cannot all hold as written.
Fix: make the step raise from the `RetryReport` (failed sends > 0, or a current-period row whose first claim is older than the window); define "unsent" by `status='claimed'` and current period, not by `claimed_at` age; update T10, T13, m16.

### R2-COR-3 (lines 142 R6, 143, 154 f, 180 T8, 184)
A P4b1-b `llm/metered.py` (`MeteredLLM`, "puts every model call behind a hold", P4b1.md:221) is not addressed. P4c-2 holds at the call sites and says "not a wrapper on `deps.llm`". If `MeteredLLM` is ever put around `deps.llm`, every call is reserved twice. The T8 AST scan finds `inner.chat(` in `llm/metered.py`, which has no row in the T8 table, so T8 fails on the merged head.
Fix: add a T8 row for `llm/metered.py` with a status; state that P4c-2 does not wire `MeteredLLM` (or that `app.py` and `agent_loop.py` hold only once); add a test that a call is reserved exactly once.

### R2-COR-4 (lines 154 f, 143)
`_screen` returns a verdict (agent_loop.py:310-316) and is called at :387 and :520. Rule 6 needs a refusal to end the run through `_wall_stop`, so `_screen` or its two callers must return or raise a stop. Change list (a)-(g) names neither the signature change nor the two call-site edits. `_wall_stop(run, which, day)` also has no `cited` argument, but the `run_budget` row needs `_abstain(..., cited)`.
Fix: specify how `_screen` signals a stop (internal exception or return `Run | None`); list the edits at :387 and :520; give `_wall_stop` a `cited` parameter, or say the run wall keeps calling `_abstain` itself.

## Minors and Nits (one line each)
- R2-COR-5 Minor (161): test_s5_runtime.py:114-118 has no "one alert" assertion to keep; say the alert assertion is NEW.
- R2-COR-6 Minor (161, test_s5_runtime:107-111): expected NEEDS_PERSON with zero calls assumes the worst-case hold exceeds the 0.001 left; state the fake route's price and max_tokens or assert it.
- R2-COR-7 Minor (148, 150-151): `raise_wall` does not say who derives the monthly `period`; `claim_wall_alert` raises ValueError unless it is the 1st and `raise_wall` never raises, so a wrong period silently loses the alert. State `today.replace(day=1)` and add a test.
- R2-COR-8 Minor (51, 56-57): `blocked()` can return daily and monthly together, `_wall_stop` takes one `which`; the daily text "starts again at 00:00" is false if monthly is also hit. State which reason is alerted.
- R2-COR-9 Minor (244 a, 146): Coupling (a) is stale (P4b1 rev 2 has `REASON_BY_WHICH`); P4b1.md:70 says P4c's `WALLS` imports it but P4c says `WALLS` holds the strings. Decide.
- R2-COR-10 Minor (3, 144, 145, 176, 182): finding ids "A13 declined / A14 declined" clash with lead amendments A13/A14, and A8/A9/A10/A16/A6 are used both ways; rename (for example R1-A13).
- R2-COR-11 Minor (227): Rollback names no loud-failure test for the non-revertible items; add one or say none exists and why.
- R2-COR-12 Nit (38, 156): `SlackChannel.notify` only resolves a `slack:<id>` principal; other principal ids are posted as written into the shared channel, so "tell one named person" is weaker than stated.
- R2-COR-13 Nit (27, 142): `_limits_stop` begins at agent_loop.py:239 not 238; `STEPS` is tick.py:249-266; cite drift.

## Verified on current main (matches the ticket)
Money, registry and `max_run_usd` reads; `config_hash` excludes `levels` (so the `alert_to` exclusion claim holds); agent_loop.py call sites (`_limits_stop`, chat call, charge/`add_cost` pairs, `_screen`, `limits_unavailable`, `blocked`, `Unqualified`); limits.py `blocked`; `AuditEvent` exists and `WallAlert` does not (proposed); tick and app wiring points; `Channel.notify`, `FakeChannel`, Slack timeout and `_call` behaviour; guard model-call sites (judge, evals, extract, k1b loop, bedrock); migrate `_SAFE_CREATE`, grants, `missing_methods`; the cited existing tests; dependency cites in P4d (revision 10), P4a (12), P2a (frozen, rev 10).

## Not checked (UNVERIFIED)
All Postgres and SQL behaviour (ON CONFLICT re-evaluation, trigger acceptance by `check_grants`, forced timestamps, store transaction isolation); Python 3.12/3.13 runs and the re-pointed existing tests (not run); k5_support builder mechanics and fuzz.py beyond line 125; cli.py:283-295 beyond the `Unqualified` catch; P4b2 state and the P2a-1 kill-switch SQL; the round-1 resolve and disposition files and the "31 fixes, 7 cuts" claim; LEAD-ORDERS text for orders 6-11.
