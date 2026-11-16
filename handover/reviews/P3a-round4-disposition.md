# P3a round 4 disposition (ticket revision 6, 2026-11-05)

Categories: applied / contested / declined / pending. "Ticket" gives the place in `handover/tickets/P3a.md` revision 6. Nothing was run through the repo test suite; SQL claims were run on a throwaway PostgreSQL 16.15 (order 7(2)).

- A1 = C1 (blocker): applied. Ticket: Interface, `gone_message` (classified by NAME: case 1 rename, 2 newer, 3 a person must look; prefix kept; "drop what it made" removed); tests H7b, H8, H9a, mixed ledger; mutant M32. Deviation: the rename line does NOT print the file stem, because `tests/test_k5_fixes2.py:304` asserts `0006_evidence` is not in the message; the runbook says how to find it.
- A2 = C3: applied. Ticket: `gone_message` prefix; Files, "Existing tests" bullet (`test_k2_migrations.py:387-394` stays green; P4d told through the lead); mutant M34.
- A3 = C2: applied. Ticket: FAIL-BEFORE 7 (asserts "newer than this release"; "drop what it made" and "rename the ledger row by hand" absent); M18, M19.
- A4 = C5: applied. Ticket: Interface `statement_text` (single pass, fails closed); lexer tests; real-file statement counts 12, 9, 8, 2, 3 (throwaway lexer, not the builder's code); M26 per branch.
- A5 = C8: applied, narrowed as the resolve said. Ticket: layer 1 planted cases (removals, strictness, row changes) and the plain statement that the real-folder run compares nothing at P3a; M27 per kind. No new compared kinds.
- A6: applied (negative control) and pending (reading). Ticket: Layer 2 negative control `DROP COLUMN state`; Open point 10.
- A7: applied. Ticket: Rollback runbook (e) as one complete sequence with exact SQL (variants E1, E2, E3); tests H9a-H9c; no drop advice except for scratch databases.
- A8 = C13: applied (exact `psql` command and `SET search_path`); the psql-subprocess test is CONTESTED (agrees with resolve). Instead one hand run on 16.15 is evidence command 7.
- A9: applied. Ticket: `order_problems` text ("review each file against every later applied migration"). No new test.
- A10 = C4: applied. Ticket: `MigrationNumberError` (`ascii(name)[1:-1]`), recipe printed once; M31, M35.
- A11 = C6 = C14: applied. Ticket: `refused_statements` (widened list: SET/RESET allowlist, `set_config(`, CLUSTER, DISCARD ALL, subscriptions, DETACH CONCURRENTLY, `ALTER TYPE ... ADD VALUE` own reason, BEGIN ATOMIC); M25, M37. Each reason was run on 16.15.
- A12: pending (lead). Ticket: Open point 9; built WITHOUT the manifest; v1.1 row with trigger; all manifest content removed.
- A13: applied and pending. Ticket: header (overlaps for P0e's table), Open point 11 (CHANGELOG exception), Existing core code. `require_backend` stays UNVERIFIED.
- A14 = C16 = C17: applied. Ticket: FAIL-BEFORE 1 and 6; tests H1, H4, H7a-c, `test_order_check_sees_committed_ledger` with exact ledger and folder contents; M13 killer.
- C7: applied. Ticket: M9 (M5 merged; distinct "not a regular file" assertion in FAIL-BEFORE 4 and 5).
- C9: applied. Ticket: layer 1, `ACCEPTED_CHANGES` first consumer P2a-1; P4d `CHECK (usd >= 0)` removed (not in `P4d.md`). The reviewer's P2a "downgrade-read" cite was not found: UNVERIFIED.
- C10: applied. Ticket: `check_ledger` refuses 0000; FAIL-BEFORE 8 (on `ce70eb5` it returns `[]`, reproduced); M36.
- C11: applied. Ticket: layer 2 request cited by item name; `require_backend` wording (P3a merges first).
- C12: applied. Ticket: "(b) and (e)" in the merge precondition; hand tests renamed H1-H10, runbook cases stay (a)-(f).
- C15: applied. Ticket: `test_statement_start_anchor`; M34b.
- Header note: applied, with a disagreement. Ticket: header lists only packages that edit `store/migrate.py` (P4d-b, P2a-1, P4b2-b; P4b1 UNVERIFIED); P5b3, P5b4, P5c, P6a, P6b2 removed. The resolve report said the changed files include `ci.yml`; the ticket changes no workflow file, so I did not list it.

Disagreements with the resolve report: (1) rename line prints no file stem (see A1). (2) `ci.yml` not listed (see header note). No finding declined.
