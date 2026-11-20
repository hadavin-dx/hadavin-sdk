# Hostile re-read of the BUILT F-store, provider mark and trigger config (egm:egm-codebase-details, model sonnet, restart after the Fable limit; one round; 2026-11-20 06:46 to 06:58 UTC; STANDING ORDER 016 item 4a)
Nothing run by the reviewer (reading only; recalled PostgreSQL behaviour marked UNVERIFIED). Result: 2 Blockers (both documentation contradictions, no code Blocker), 7 Majors, 10 Nits. No deadlock and no counter overshoot through reserve found (statement orders in the reviewer's report: reserve, settle, add_spend, expire and purge never invert a lock order).
Resolution: code findings go to F-store fix round 3 (builder aaf... see board; commit "code F-store: fix round 3 ..."); documentation findings fixed by core-b now. Findings that are stated limits are written into ii-meter.md and the CHANGELOG.

| # | sev | area | finding (short) | answer |
|---|---|---|---|---|
| 1 | Blocker | doc | interfaces/README.md line 3 says "NOT run: no code for it exists yet" | fixed (state line rewritten) |
| 2 | Blocker | doc/code | invariant 9 says caps are validated like amounts, but check_spend_cap has no upper bound, decimal or exponent limit; stores can then differ | code: same exponent window (fix round 3 F3); README wording |
| 3 | Major | store | no lock timeout: a lock holder that stops (stopped pod, partition) freezes every store call of the process behind the process-wide lock, also the in-process emergency stop | code: lock_timeout on the store connection (F6); stated limit: a statement's own run time is not limited |
| 4 | Major | memory store | books the counter BEFORE building the reservation row; a validation error leaves the counter raised and no row to expire (invariant 2 broken on memory) | code (F1) |
| 5 | Major | worst case | binary documents: raw bytes counted, but the decoder replaces invalid bytes by a 3-byte character, so the price can exceed the reservation | code (F7) |
| 6 | Major | trigger config | app.trigger_secret lets the provider's own exception through; it can carry the secret name | code (F5) |
| 7 | Major | trigger config | a sender whose agent is retired after start keeps launching it until restart; at the next restart one retired agent with a sender stops the whole runtime from starting | stated limit and order of operations in the CHANGELOG ("remove the sender, then retire the agent"); a softer start (skip with a warning) is a design change for the lead |
| 8 | Major | meter | a lost commit acknowledgement (database commits, connection drops) leaves a booked hold with no id returned; closes only by expiry and the counters never go down, so a flapping network can drain a tight daily cap | stated limit in ii-meter.md and the CHANGELOG; the fix (a release path or an idempotent retry of reserve) is a design change, listed for the lead and for Y4 (release command) |
| 9 | Major | provider mark | unproven billing assumptions (stated); no adapter streams today, nothing forbids a later streaming change from breaking the mark silently | sentence "adapters must not stream; a stream needs its own mark rule" added to ii-meter.md and the retry.py docstring |
| 10 | Nit | tick | expiry age uses the tick process's config; an infinite call_timeout_s overflows | noted; no change |
| 11 | Nit | midnight | the day is chosen before a possible row-lock wait; a call waiting across 00:00 UTC books yesterday | stated limit in ii-meter.md |
| 12 | Nit | stores | further differences between memory and PostgreSQL (NUL in run_id or agent_id, lone surrogate, huge cap, huge age, naive purge time, missing counter row) | code (F2, F3, F4) |
| 13 | Nit | doc | draft SQL says < for expiry, code says <= | ticket text corrected |
| 14 | Nit | doc | ii-meter point 7 understates the reservation (a 4096-byte overhead, the schema twice, x2 requests with a schema) | text corrected |
| 15 | Nit | doc | CHANGELOG lists five reasons (six now); "20 mutants" (22) | CHANGELOG corrected after the fix round lands |
| 16 | Nit | doc | two later test files are in no file list | ticket R1 list extended |
| 17 | Nit | limits | an unhashable agent_id raises TypeError, not KeyError | code (F2) |
| 18 | Nit | doc | requests/001.answer.md top half still shows names DRAFT 2 reversed | header "superseded by DRAFT 2" added |
| 19 | Nit | config | a bad sender id (possibly a pasted secret) is echoed in pydantic's error location | noted; low risk |
| 20 | Nit | PostgreSQL 14/17 | MAINTAIN right not checked by effective_problems (existing code); PostgreSQL 14 is outside what the migration scanner claims; isolation only set in connect() | step B code: the lead; stated |
Confirmed by the reviewer: lock order never inverted; a counter never passes its cap through reserve; settle racing expire takes the larger-amount branch after the lock wait (UNVERIFIED EvalPlanQual detail); an overshoot audit row cannot be written twice; purge cannot delete an open row; the mark is set on the instance, cleared on the second openai_compat request, and no src code re-wraps it; the trigger config documents match the code.
Not checked by the reviewer: test contents; the model gate (not in this tree); gemini and anthropic hooks beyond their definitions; migrate.effective_problems internals; actual PostgreSQL behaviour.
