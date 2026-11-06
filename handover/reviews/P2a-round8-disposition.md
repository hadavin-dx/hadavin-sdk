# P2a round 8: disposition of findings in revision 10 (written 2026-11-06 02:40 UTC = 08:10 IST)

Source of decisions: `reviews/P2a-round8-resolve.md` (20 rows, all PROPOSE FIX, none contested, none declined). Ticket: `tickets/P2a.md` revision 10. Round 8 was round 1 of at most 3 ticket-review rounds (order 16); after round 3 the ticket is FROZEN.

| Finding id | Answer | Where in revision 10 |
|---|---|---|
| ADV-M1 | applied (fix option (b)) | field 11 guard SQL and explanation; DBA recipe `by='dba'`; field 7 view and `old_by` sentences; field 17 fold; S31 g and l; S36 (3); S37; mut-G48, mut-G49; PENDING LEAD 34 |
| ADV-N1 (merged with COR-N1) | applied | title line, header, honest note, fields 2, 15, 16 |
| ADV-N2 | applied | field 12 "Round 8 additions" (two db tests) |
| ADV-N3 | applied | field 13 mut-F15 redefined `n < N - 1`; equivalent-rows note |
| ADV-N4 | applied | field 13 mut-K3 killer named, mut-ST20 wording |
| ADV-N5 | applied | field 7 missing-row sentence; field 11 stop function text; S29 case 7; field 12 view-agrees exemption |
| ADV-N6(a) (merged with COR-N12) | applied | field 9 item (d); new test `cli::test_reset_with_listed_name_refused_when_audit_down`; field 7 reset step (1) and exit codes |
| ADV-N6(b) | applied | field 11 livelock runbook; S32 step 4; PENDING LEAD 36; field 3 P4b1 relay |
| ADV-N6(c) | applied (modified shape: CLI runs `status` once after reset) | field 7 CLI item; mut-L47; test `cli::test_reset_reports_switch_still_on_when_a_stop_arrived` |
| COR-N2 | applied | field 11 lock_timeout after the advisory lock; field 9 item (t); mut-G50; S39; field 3 P3a coupling |
| COR-N3 | applied | field 7 doc-behaviour paragraph; field 11 cap exception |
| COR-N4 | applied (the Dropped row no longer names `clear_kill_switch_if`; it was never built) | field 7 method line; v1.1 Dropped row |
| COR-N5 | applied | field 9 ACCEPTED_CHANGES entry (one entry) |
| COR-N6 | applied | field 3 P4d and P2d relays |
| COR-N7 | applied | field 3 hot-file lines; PENDING LEAD 35 |
| COR-N8 | applied | field 9 `_pk_tree` and memo-5 cites by item |
| COR-N9 | applied | field 9 homes of the new errors |
| COR-N10 | applied | S31 case i rewritten |
| COR-N11 | applied | field 9 item (r): 26 `migrate(` sites re-grepped at `ce70eb5` |
| COR-N13 | applied | revision 9 counts line wording |

Counts: 20 applied, 0 contested, 0 declined.

Mutants (script count of distinct `mut-` ids in the final text): G 47, F 16, R 19, ST 22, P 21, L 46, K 7 = 178 (revision 9: 174; 4 new: G48, G49, G50, L47; none removed). 175 if PENDING LEAD 33 cuts reconciliation. SQL steps still 14 (S29-S42). New named Python tests: 5 (+1 changed, +1 must-pass).

My additions beyond the resolve (flagged in the ticket): CLI behaviour when its second status read fails (minimal choice, UNVERIFIED); S32 step 4 written as two ordered runbook steps; P3a row relay sentence dropped because `P3a.md:164` already cites by item.
