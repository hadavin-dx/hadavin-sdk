Status: resolved (round 1 of 3; categories by the Elephant; fixes queued for builder d-fix2 after d-fix1 ends)
# Goldfish Annotated Review Report: step D tests (fresh reviewer egm-design, sonnet, read-only)
Target: tests/triggers/* , tests/endpoint_mutants.py. No Blocker.
| id | sev | finding | category | action |
|---|---|---|---|---|
| T-1 | Major | agent/principal half of the 409 rule (worker.py _answer) has no test and no mutant | PROPOSE FIX | test: same key and ref, other agent / other principal -> 409; add 2 mutants |
| T-2 | Major | test_t5_main_start.py is skipped on this tree (no TriggerSettings); strict switch does not turn the skip into a failure | PROPOSE FIX | ORDER 020 item: HADAVIN_REQUIRE_PG also fails this skip; evidence on a combined scratch tree |
| T-3 | Major | worker.py docstring promises a WARNING for missing settings fields; code does not emit it | PROPOSE FIX | same as DC1-3: code-side check or docstring fix (d-fix1) |
| T-4 | Major | refusal tests check 2 headers only (ticket H10 exact header set) | PROPOSE FIX | refused(): header names subset of {Content-Length, Allow, Retry-After}; mutant X-Reason |
| T-5a | Major | Windows: test pins "(OSError)" but Windows gives PermissionError | PROPOSE FIX | accept OSError family name, keep "cannot listen" |
| T-5b | Major | allow_reuse_address on Windows | PROPOSE FIX | same as DC1-1 (d-fix1) |
| T-5c | Major | Windows reset hides 400 in raw-socket tests | ESCALATE-to-checklist | needs real Windows; in WINDOWS-NOTES.md; also catch ConnectionAbortedError in exchange() (cheap) |
| T-6 | Suspect | seen.seconds < 0.5 flake margin; test_n9 buffers; _handlers_done cross-test; patch by string name; new Runner validation untested; poll_s=True text | PROPOSE FIX (cheap ones) | widen margin to 2 s; assert list non-empty; tests for float/bool/NaN; TypeError -> ConfigError (d-fix1) |
| T-7 | Nit | oracle self-agreement, skips, importorskip, D3 duplicate bound | DECLINE | recorded |
| T-8 | Ticket | contradictions (trigger_resolve, IPv6, logging, waiting, config shape, line numbers) | PROPOSE FIX | same as DC1-2 (ticket text rewrite, d-fix1/d-fix2) |
