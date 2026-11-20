# EGM review round 1 of 1: tickets/C-price-constraint.md, compared with the BUILT code (egm:egm-review-loop through the Skill tool; direct dispatch; model fable)
When: 2026-11-20 05:59 to 06:06 UTC. Reviewers: egm:egm-implementation-readiness = completed; egm:egm-codebase-details = completed. Not run: none. Nothing run by either (reading only).
Round result: NOT CLEAN by the rule (Majors open), but NO Blocker. Blockers 0, Majors 11, Nits 15. Both say the built source equals the ticket's code blocks word for word and the guarantee holds for every Config that goes through validation.
Resolution: ticket section "RESOLUTION of review round 1" (P1 to P8). No source change needed; one CHANGELOG line added.

| id | severity | finding (short) | answered in |
|---|---|---|---|
| cb-1 | Major | the ask-your-data demo has its own config loader that builds Route without Config: a zero price loads there and its demo cap can then never fire; a negative price now fails late with a raw validation error | P1: stated out of scope, follow-up named |
| cb-2 | Major | in demo, a config with kind fake and zero prices plus an injected real model client still prices every call at 0 | P2: stated limit; closed by step F (the gate meters whatever client runs) |
| cb-3 / ir-5 | Major | the replay check is weaker than the ticket says, and test H5 asserts the helper, not the replay refusal | P3: wording corrected; H5 declared regression only |
| cb-4 / ir-2 | Major | the ticket says CHANGELOG is not touched and does not list tests/price_mutants.py; both exist (and are right) | P4: file list corrected |
| cb-5 / ir-6 | Major | evidence paths and the mutant-run procedure in the ticket do not match what exists | P5 |
| ir-1 | Major | five design choices stand as open questions with a recommendation; the code was built on them | P6: recorded as decisions by core-b, lead verdict in DECISIONS.md |
| ir-3 | Major | "done" points to the plan's stop rule without quoting it | P7 |
| ir-4 | Major | no phases or order (who commits what, how fail-before is taken safely) | P7 |
| nits | Nit | stale line numbers after the trigger config landed; one over-long line in the ticket's code block (the built code wraps it correctly); M1 kill list names a test that cannot kill it; regression lists disagree; size line wrong (491 test lines, not 150); defaults.py placement under a wrong header; a free self-hosted model in demo must now write a price; a third price consumer (k1b/loop.py:115-122) not cited | P8 |
Risks in the built tests the reviewer could not settle by reading (rebuilding Config from model_dump; year 0000; pydantic wording): the test file passed 246 of 246 on pydantic 2.14.1; they are fragile on a version bump, noted.
