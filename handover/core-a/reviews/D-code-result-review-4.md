Status: extra fresh pass on the committed head (lead order), resolved; fixes queued as d-fix5 after batch6 (it hashes the tree). Fresh reviewer egm-codebase-details, sonnet, read-only. No Blocker; 5 Major (tests that would not fail, ticket contradiction), 4 Nit.
| id | sev | finding | category | action |
|---|---|---|---|---|
| R4-1 | Major | conftest.py pytest_runtest_makereport (DSN/psycopg skip -> FAILED, the point of HADAVIN_REQUIRE_PG) has no test | PROPOSE FIX | child-pytest test with a fake test skipping with the DSN reason: FAILED under =1, skipped without |
| R4-2 | Major | strict means == "1" exactly; "true"/"yes" silently non-strict; two copies of the check | PROPOSE FIX | one shared function; any other non-empty value is an error |
| R4-3 | Major | worker.py _prepare: --host / --allow-non-loopback wiring and the defaults (127.0.0.1, 8081) not pinned on this tree | PROPOSE FIX | test through main(["--host","0.0.0.0",...]) with load_config/build patched: exit 2 'not loopback'; with the flag: passes bind check; defaults pinned |
| R4-4 | Major | Runner.running (new property) never tested for real; serve reads it with getattr default | PROPOSE FIX | gated-loop test: 1 then 0; serve reads runner.running directly |
| R4-5 | Major | ticket lines ~107, 138, 217 (456 superseded) still say AttributeError / exit 3; code and tests say ConfigError / exit 2 | PROPOSE FIX | rewrite those places |
| R4-6 | Nit | _fields prints loc segments that can hold user text (extra YAML key) | PROPOSE FIX | only segments matching [A-Za-z0-9_.-]{1,40}, else '?' |
| R4-7 | Nit | test_t5_cases importorskip hides a broken import | PROPOSE FIX | plain import |
| R4-8 | Nit | strict-mode test checks 'error' not in output | PROPOSE FIX | check rc and FAILED words |
| R4-9 | Nit | skipped empty-body params | DECLINE | pinned by a separate test |
Combined with E-nits (reviews/E-result-review-4.md) in one builder run after batch6.
