# Fresh review: PR72 (P6a-1 e6a4220)
Reviewer: egm-codebase-details (fresh, read-only, ran nothing). No Blocker; 3 Majors, 6 Nits.
M1. Pilot/prod refusal of made_up_data_only (config.py ~409-411) contradicts frozen ticket P6a.md line 70 ("no effect in pilot and prod"); the "ratified order 132" text exists only in the builder's evidence file. LEAD: put the F2 text into the ticket.
M2. CHANGELOG overclaims tests/test_strict_flags.py "fails when a new loose bool field is added to any model": it sees only module-level models, silently skips ImportError/AttributeError modules, exempts retention_ack by field name only, does not see dataclasses. Fix: fail on skipped modules, key the exemption on the class, or narrow the claim.
M3. owner-visible-limits.md has no entry for made_up_data_only / allow_test_doubles (F6 open); five suggested entries are at the end of evidence-p6a.md. LEAD-owned.
N4. "line 1 of every log is the head SHA" is false for recount, uvsync, rows, failbefore-table, mutants-body, pgstart files; "14 of 14 rows fail at 80f94b8" has only a stale log.
N5. Fail-before totals confirmed (43 failed/21 passed; strict 10 failed); the made_up_data_only strict row fails on the base with extra_forbidden, not for missing strictness (t7h and mutant 54 carry that proof).
N6. Mutants 29-55 not seen by the reviewer.
N7. max_completion_tokens is operator-set but sits in INTERNAL whose header says "written by the code".
N8. Verdict.flagged etc. may load lax from model JSON: same bug class; check how Verdict and ReplayRecord are built.
N9. test_a_safety_flag_loads_only_from_a_real_bool accepts any ConfigError/ValidationError; t5q and t7f use states load_config cannot produce (labelled).
Not checked: CI, Postgres 17, cli.py paths, demo YAML bools.
