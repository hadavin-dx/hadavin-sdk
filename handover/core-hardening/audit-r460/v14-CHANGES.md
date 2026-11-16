# v14 changes, one row per finding

Sources: `review-handoff-v13-security.md` (B1, M1-M4, minors 1-8), `review-handoff-v13-readiness.md` (R1-R7, N1-N9), `review-handoff-v13-citations.md` (C1-C8). "Text" = written into `CORE-PR-HANDOFF-v14.md` section 5.11 (item number) unless said otherwise. **Not fixed first:**

| Id | Status | Reason and next step |
|---|---|---|
| N0 | NOT FIXED | Sentences in 5.1 to 5.9 that 5.11 contradicts were not rewritten in place (time). 5.11 states it wins. Next: a builder or v15 pass removes the older sentences. |
| all | NOT RUN | Unit tests, `ruff`, `bandit`, `gate4.sh`, Postgres 17.10, EGM skills (I cannot invoke them). Nothing in `src/`, `tests/` was edited, so there was nothing to test; every code change is specified text only. |
| C7-anchor | NOT FIXED | 98 ANCHOR-MISS rows of `raw-cites-v14.txt` not read by hand; range-only cites that moved are not detected by either program. |
| C6 | PARTLY | Hot-file column completed from the reviewer's list (patch8); the 16 pairs of the citation check's list were not re-derived. |

| Id | Fixed? | How | Evidence |
|---|---|---|---|
| B1 | fixed in text and prototype | schema from `TG_TABLE_SCHEMA`, `search_path = pg_catalog, pg_temp`, `REVOKE TEMPORARY` operator step and start-up check; item 1 and 5.6 | `raw-pg-real-code-v14.txt` (negative control: v13 function fails, v14 passes, 61 of 61), `raw-pg-tmp-v14.txt` T0a, T0b, T1, T2, T3. Note: the bypass needs one `GRANT` on the temporary table; without it the attack fails closed (T0a). The review did not say so; v14 states it. 16.15 only |
| M1 | fixed in text | fail-closed kept; size and age monitor; export-then-delete retention, 400 days; item 2 | `raw-pg-m3-v14.txt` (136.4 bytes per row, +0.26 ms) |
| M2 | fixed in text | portal reads the log; "not read" never 0; item 3 | `raw-pg-real-code-v14.txt` portal checks |
| M3 | fixed in text | inline ALTER equality test plus UPDATE-shape test as mechanical G-4(i); item 4 | not run (needs the S-2a code) |
| M4 | fixed in text | L7 silence = not built, L10, L11, L12, deviations disclosed; item 5, `v14-OPEN-FOR-LEAD.md` | none needed |
| minor 1 | text | ValueError and LookupError; item 6 | prototype in `raw-pg-real-code-v14.txt` |
| minor 2 | text | C7 literal `False`, new C8 census; item 7 | not run |
| minor 3 | fixed in held SQL | trigger WHEN formula; item 8 | `raw-pg-tmp-v14.txt` T6 |
| minor 4 | fixed in held SQL | `SET LOCAL lock_timeout = '5s'`; item 9 | 55P03 after 5.0 s, rollback, `raw-pg-real-code-v14.txt` |
| minor 5 | text | 5.9 row 9, item 10 | not run |
| minor 6 | text | event `spend_released_client_error`; item 11 | not run |
| minor 7 | text | transient false refusal stated; item 12 | not run |
| minor 8 | text | `_Mapping` wording and disclosure; item 13, other-tracks file | none |
| R1 | text | item 14 | not run |
| R2 | text | item 15 | |
| R3 | text | item 16 (5.1 item 7b content is in 5.11 item 16, not in 5.1) | |
| R4 | text | item 17, 7.1 hot-file column (patch8) | `raw-cite-check-v14.txt` for the cites only |
| R5 | text | item 18 (the S-1 content list in 7.1 not reworded) | |
| R6 | text | item 19 | not run |
| R7 | text | item 20 | not run |
| N1 | text | item 21 | |
| N2 | text | item 22 | |
| N3 | text | item 23 | |
| N4 | text | item 24 | |
| N5 | text | item 25 | |
| N6 | text | item 26 | |
| N7 | disclosed | section 8 and item 27; `gate4.sh` unchanged (no skip-if-absent steps added) | `raw-gate4-vs-ci.txt` |
| N8 | text | item 28 | |
| N9 | fixed | "5 files" in 5.1 item 7 and item 29 | `raw-greps-v14.txt` G4 (14 lines, 5 files) |
| C1 | fixed | H-2 grep bounded to the files it read (other-tracks) | |
| C2 | fixed | L7 cites `raw-pg-real-code-v13.txt` | |
| C3 | fixed | llm group 9 today, 10 planned, sizes [10,4,3,3,2,2] | `raw-cycles-v14-independent-script.txt` |
| C4 | fixed | 26 `build(llm=)` calls, 0 NetworkLLM, ast method | `raw-greps-v14.txt` G1 |
| C5 | fixed | `max_requests`, `allow_group_read`, `fileguard.py`, `injection_check(spend=)` marked planned | `raw-greps-v14.txt` G20 (0 files in src) |
| C8 | fixed | `mutants.py`, `reserve_table.py`, `masking_damage.py`, `needed-check/` named as "does not exist yet" | none |
| Q-checks | n/a | PR-2 NEEDED-CHECK stays UNVERIFIED; run.py stays out; D5 OWNER-OPEN | |
