# Status of F-store-hostile-review-1 on head 8273ff1d0 (builder P3, 2026-11-20)
Method: each finding re-read against code and docs on this head. 203 tests of the touched areas run and pass (test_store_memory_atomic, test_trigger_secret_reader, test_worst_case_documents, contracts/test_store_spend_caps, test_store_lock_timeout_pg). Result: no finding is still true except the stated limits; one doc gap (R1 file list) was extended. No code change needed, no migrate.py change needed.

| # | sev | still true? | evidence (file:line) | action |
|---|---|---|---|---|
| 1 | Blocker | no | interfaces/README.md:3 now "State: BUILT on cloud/core-b" | already fixed |
| 2 | Blocker | no | store/protocol.py:123-136 check_spend_cap has exponent window -12..9, finite, Decimal only; interfaces/README.md invariant 9 (line 27) says "no other upper bound" with the window | already fixed (code and wording agree) |
| 3 | Major | no (limit stated) | store/postgres.py:456-460 SET lock_timeout from defaults.STORE_LOCK_TIMEOUT_MS (defaults.py:185); tests/test_store_lock_timeout_pg.py; CHANGELOG.md:124-126 states a statement's run time is not limited | already fixed |
| 4 | Major | no | store/memory.py:379-390 row built before the counter is booked; tests/test_store_memory_atomic.py | already fixed |
| 5 | Major | no | llm/common.py:95 documents sized as decode("utf-8","replace").encode(); ii-meter.md point 7; tests/test_worst_case_documents.py | already fixed |
| 6 | Major | no | app.py:366-387 _sender_secrets raises RuntimeError("sender secret unavailable") from None; tests/test_trigger_secret_reader.py | already fixed |
| 7 | Major | stated limit | CHANGELOG.md:122-124 (d) | accepted residual (design change for the lead) |
| 8 | Major | stated limit, remedy since built | ii-meter.md point 12 (release command, migration 0008); CHANGELOG.md:117-121 | accepted residual / remedy exists |
| 9 | Major | no | ii-meter.md point 13; CHANGELOG.md:121 (c); llm/retry.py docstring | already fixed (wording) |
| 10 | Nit | noted | | accepted residual |
| 11 | Nit | stated limit | ii-meter.md point 11; CHANGELOG.md:116 (a) | accepted residual |
| 12 | Nit | no | protocol.py check_store_id (lines 89-103: NUL, control chars, lone surrogate), check_purge_bound, MAX_EXPIRY_AGE_S | already fixed |
| 13 | Nit | no | tickets/F-store.md:145 uses <= (the inputs/ draft keeps "<" as the lead's original, not edited) | already fixed |
| 14 | Nit | no | ii-meter.md point 7 (4096-byte overhead, schema twice, doubled attempts) | already fixed |
| 15 | Nit | no | CHANGELOG.md:100-101 "SIX reasons"; no "20 mutants" text left | already fixed |
| 16 | Nit | was partly true | tickets/F-store.md R1 note listed 2 files; later test files missing | fixed here (list extended) |
| 17 | Nit | no | limits.py:182 catches TypeError for an unhashable id; check_store_id requires exactly str | already fixed |
| 18 | Nit | no | requests/001.answer.md:1 "supersedes DRAFT 2 and DRAFT 3" | already fixed |
| 19 | Nit | noted | | accepted residual |
| 20 | Nit | stated | step B code (lead) | accepted residual; needs migrate.py: MAINTAIN right check in effective_problems and PostgreSQL 14 scanner claim, isolation only in connect() (listed, not edited) |

The lead's status sentence is present in README.md:45, SECURITY.md:76, CHANGELOG.md:6 and docs/stop-state-runbook.md:264.
Counts: 20 findings; fixed here 1 (#16); already fixed 13 (1,2,3,4,5,6,9,12,13,14,15,17,18); accepted residual 6 (7,8,10,11,19,20); needs migrate.py: 1 part of #20 (not edited).
