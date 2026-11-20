# EGM review round 2 of at most 3: tickets/F-install.md, section "RESOLUTION of review round 1" (lead ORDER 014, alongside the build)
When: 2026-11-20 06:24 to 06:30 UTC. Reviewer: egm:egm-implementation-readiness = completed (model fable, through the Skill tool). egm:egm-codebase-details: NOT RUN on this target this round (that reviewer was used for the hostile re-read of the built A, B, C code at the same time; a round with a reviewer not run is not clean by the rule).
Round result: NOT CLEAN. Blockers 2, Majors 5, Nits 10. Nothing run by the reviewer.
Resolution: ticket section "RESOLUTION of review round 2" (W1 to W7), sent to the running builder at 06:31 UTC.

| id | severity | finding (short) | answered in |
|---|---|---|---|
| ir-2-B1 | Blocker | the "one try" does not cover where a judge refusal surfaces (document screen, tool-result screen, the shadow card's own except, replay's detector call): a run could still strand in WORKING or end shadow_undelivered | W1, W6 |
| ir-2-B2 | Blocker | Budget.forfeit "closes the budget" through a "case scope" with no interface; closing the whole budget breaks the pinned test that the next case runs after exhausted retries | W2 |
| ir-2-M1 | Major | the retry multiplier under-counts the openai_compat kind (a forced answer can cost a second request round) | W3 |
| ir-2-M2 | Major | the formula is not pinned enough for a builder and a separate test writer to reach the same number (None, separators, empty routes, sizing failure) | W4 |
| ir-2-M3 | Major | the re-raise in guard/injection.py makes an import cycle if imported at module top | W5 |
| ir-2-M4 | Major | "any other exception before provider contact -> gate_error" cannot be told apart from a client fault | W1 (no blanket catch), W4 |
| ir-2-M5 | Major | refusals on the replay and eval paths are only half mapped | W6 |
| nits | Nit | stale app.py numbers; no default for an unknown reason; Budget and "unknown agent"; docstrings; one test marked unverified; stale table cell and invariant wording; mutant numbering | W1, W7 |
Round-1 answers, per the reviewer: V1, V3, V5, V8, V9, V10, V11, V12 and the producers text HOLD; V2/V4 (Budget forfeit), V6/V7 (where refusals are caught) FAILED in part.
