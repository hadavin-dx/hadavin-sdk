# Hand-off v14 readiness review, round 3 (egm-implementation-readiness, condensed copy of the inline report), 2026-11-16
Target: CORE-PR-HANDOFF-v14.md (497 lines), -other-tracks, v14-CHANGES.md, v14-OPEN-FOR-LEAD.md. Read-only; nothing run. Verdict: NOT READY for a builder with only these files and src/. 0 blockers, 7 majors. No GRANTS/migrate() ordering defect remains (the v12 blocker is gone: held files are never scanned by check_grants).

## MAJOR
- M1 The "5.11 wins" layering forces a builder to merge two texts; older sentences are still wrong: GRANTS for the log (`Grant("table","",portal=True)` in 5.6/5.11 vs `Grant("table","")` in 7.1); measured cost (167 bytes, +0.28 ms in 5.6 and L9 vs 136.4 bytes, +0.26 ms in 5.11 and OPEN-FOR-LEAD); "47 of 47" in 5.4/E0-DB-1 vs "61 of 61" in sections 0 and 8; owner of the `reply()` edit and `clean_tokens` (5.4 heading S-2a, 5.11 item 18 S-1, 7.1 list silent); section 0 item 1 cites the wrong point. Fix: fold 5.11 into 5.1-5.9 and delete superseded sentences; at least name a PR owner per 5.11 item.
- M2 R2 not fixed in the test list: E0-S1-3(b) (7.2 line 416) still says `spend_refused`; 5.11 item 15 says `guard_unavailable`. `spend_refused` arrives only in S-2a, so the S-1 test would fail.
- M3 `Limits` has no source for the spend numbers (`max_call_usd`, `unattributed_*`, `cli_*`): the new signature has no settings argument. Design choice left to the builder in the signature both S-1 and S-2a depend on.
- M4 Three code pieces without an owning PR or signature: start-up checks on PostgresStore (`idle_in_transaction_session_timeout`, TEMP privilege, `statement_timeout_ms`, `reconnect`); `PostgresStore.__init__(conn)` knows no environment; `store/postgres.py` is not in the DB-2 hot-file list; the portal's second database address has no setting name, secrets key or PR; no statement how S-2b detects `spend_decrease_log`.
- M5 Test list not conditional on the lead's open answers: L7 default says the Infinity clause is NOT built, but 5.6 item 1(a), the held `spend_nonneg.sql` (sha256-pinned, includes `usd < 'Infinity'`), E0-DB-1 and E0-S2-2 assume it is. Same for L11 and L10 (DB-0 alternative not specified). Provide two held files or a conditional test table.
- M6 E0-S2-2 and the S-2a test seam depend on a later PR (DB-1 file applied; DB-1 merges after S-2a). The DB-1 test "real migrations/ has no held name" would fail the move PR: say "no held name without an OWNER_YES entry".
- M7 Retry and release wording contradicts itself: 5.11 item 11 releases "4xx other than 429" with new event `spend_released_client_error`; 5.3 releases only {400,401,403,404,422} (408, 409 differ); event not in the 5.3 note list; nobody calls `note` on release. Item 26 makes `SpendScope` frozen with a separate `KeptTotal` (no class definition or wiring), while 5.3 and 5.5 still say `scope.kept`.

## v13 readiness findings status
R1 fixed in text (three lambda sites not named as must-stay-green). R2 NOT fixed (M2). R3 fixed only in 5.11 item 16 (E0-S1-7 still points to 5.1 item 7). R4 mostly fixed (S-2a row omits `llm/anthropic.py`, `llm/gemini.py`; CHANGELOG in no column; DB-2 row omits `store/postgres.py`). R5 not fixed in place (M1). R6 fixed in text, no PR owner. R7 text added, no test for the `k1b/loop.py:205` refusal path. N1, N3, N4, N9 fixed. N2 fixed (5.3 still says "three attributes"). N5 fixed in text (`spend.reason_string` not in S-1 list). N6 see M7. N7 `gate4.sh` still UNTESTED yet it is the S-1 pass rule. N8 text only (no place in `app.build`).

## MINOR
Section 0 item 12 says D5 gates DB-1/DB-2; 7.1 and L11 say it does not. DB-1 depends column differs between tables. 5.9 table row 7 has an extra cell. 5.11 item 10 claim "stated in 5.5" is only a test. E0-S1-3 labels out of order. S-1 mutants named only for the handler; window-logic mutants proved only in S-2a E0-S2-8. S-1 scope very large for two 60-minute sessions (minutes unmeasured). Every Postgres claim is 16.15 only; CI uses 17.10.

## Builder can do without asking
Serial order S-1, S-2a, S-2b, DB-1, DB-2, then other tracks; hot-file column adequate for conflict planning; GRANTS timing and migrate ledger guards correct; each L-id has a stated default ("silence means NO").

## Not checked
Other-tracks file after line 200 (O-8 on) and K1/A1/G/R content against src/; `held-sql/spend_decrease_log.sql` and raw Postgres outputs ("61 of 61", "47 of 47" taken as written); ORDERS.md Q24/Q28/Q33/Q34; line-by-line recheck of about 400 cites; vendor facts; anything needing a run.
