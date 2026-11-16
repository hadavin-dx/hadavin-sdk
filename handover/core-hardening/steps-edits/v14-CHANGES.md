# v14 changes: one row per finding. S = sheet, C = day card, A = appendix, OP = v14-OPEN-FOR-LEAD.md. "Lead" = studio lead. Nothing was run; the check script only reads text.

| Finding | Where fixed (or why the lead must answer) |
|---|---|
| N1 blanks without a list | S "The blanks": B1 to B13, every marker in S carries "blank Bn"; check-v14.py enforces it |
| N2 notice layout points nowhere | A5 now has an invented sample notice; C E.2 points to it and to B9; OP L1 corrected |
| N3 two 20-minute rules | C E.0 "Time" tick; row 3 latest start is the one source (A2 row 3); S go item 5 no longer states minutes |
| N4 no cd on the card | C blanks (cd line), C E.0 last tick; rule 11 lists `cd` |
| N5 which window | C line 3 defines run window and check window; S rule 11 and Words |
| N6 step 0 yes wording; start again after exit 1/2 | S step 0 warning gives the sentence; C E.4 says do not start again, lead decides in writing |
| N7 which UNVERIFIED is Freeze | S marker paragraph: Stop that step, send words, no variant |
| N8 A or B not 1 and 1; pause maximum | C F.1 (pause end, B11), F.4 (do not post); S step J |
| Nit: "lead" two meanings | S Words: "sales lead" vs "studio lead"; claim quoted once |
| Nit: lead key / key / take / run key / proof screen / Q-numbers | S Words defines person id (not a secret), take, take key, run key; Q-numbers removed from S and C (check enforces) |
| Nit: money lag, two start readings | S money rule item 4 (A reading 30 min after last call, largest figure, E reading is the start) |
| Nit: "window" meanings; money stop names | S top: "money stop" with the alias; C E.2 alias; A9 deadline text; one name |
| Nit: step A timing | S step A: run day or evening before; key lifetime 24 hours |
| Nit: checksum cell | C "checksum list" |
| Nit: delete or revoke verbs | A2 row 20 |
| Nit: no input at 5 minutes | S DO THIS FIRST 3; C E.2 minute 5 type `n` |
| SE-M1 emergency cancel spares run key | S stop table, money rule 6; C words 2 |
| SE-M2 key page shows key | S stop word 1 exception; A15 step 2; A18 |
| SE-M3 other secrets | S rules 13; A18 secrets table; Key exposed covers app passwords and apps |
| SE-M4 go item 5 Python only; two HubSpot identities | S go item 5 (a)(b)(c); A2 row 19; statement itself B12 (lead) |
| SE-M5 run total not worst case | S money rule call ceiling; C blank; A6 yes; the ceiling value is B10 (lead) |
| SE-M6 run key lives for days | S DO THIS FIRST 3, step A, I.0 (24 hours, also if called off) |
| SE-M7 "not depend on lead's word" | S money rule: usage page is the one independent figure |
| SE-m reading order | S money rule 4 names F.4, first I.0 reading, second reading |
| SE-m cancel key when frozen at F.3 | S I.0; C words 3 |
| SE-m Key exposed coverage | S/C Key exposed |
| SE-m Stop in step 0 | S step 0 warning |
| SE-m "nothing is sent" is not "no spend" | C E.2 and E.4 |
| SE-m A.6 ceiling sentence | S A.6 |
| SE-m cancel every older key | S A.0b |
| SE-m start line path | C E.1 file name only; A14 item 10 |
| SE-m step 0 patch status | S B5; OP L12 |
| ADV 1, 2, 3 | S/C words 1, 2; C E.0 first tick; A14 H list |
| ADV 4, 5 | C E.2 (no masked accounts); C E.0 alert address; A3, A5 |
| ADV 6 | C E.1 and cd; A14 |
| ADV 7 | S 0.1, A.5; C blanks; A3 (last 4 digits, outside film) |
| ADV 8 | S 0.3 |
| ADV 9 | S A.0b |
| ADV 10, 11, 12 | C F.2, F.1 (B11), E.2 |
| ADV 13, 14, 15, 16 | S stop table (Freeze no longer holds money figures; Freeze never stops F.4/I.0; "Stop (no run)"; words only) |
| ADV 17, 18 | C blanks row 3 formula; S money rule 4 and I.0 |
| ADV 19 | S DO THIS FIRST 1 (you are never row 4); S step J row 15 is a human who is not you. Other rows: OP L21 |
| ADV 20 | C exit-code cell rule |
| OP-1 lease sentence | S step J box uses row 3 length and no number or Q-id; decision B13 (lead) |
| OP-2 lease length | S uses row 3 only (no 45) |
| OP-3 port | S/C use row 13 only; rehearsal port 5690 is not named in owner files |
| OP-4 money stop names | S one name "money stop"; latest start only on row 3 |
| OP-5 180/189 | not in owner files; OP L18 |
| OP-6 superseded banners | S top "Older versions are replaced"; banners on v4-v13 files not added (outside this brief's owner files; OP L22) |
| OP-7 one server two databases | S go item 9 and step J; A8 item 8 "aim" wording unchanged |
| OP-8, OP-9 test counts, mutation evidence | not owner files; lead (OP L19) |
| F2 DECISION-one-store line 14 | inputs file: lead only (OP L20) |
| F4 program does not print figures | S money rule words |
| F5 masked outputs, rules not overridable | S rule 14; A3 |
| F6 probe contact on a deletion list | S 0.6; C F.5; A12 |
| CI-m1 notice sample | see N2 |
| CI-m2 `cut` | A17 |
| CI-m3 SKIPPED / delete FAIL exit 1 | S 0.5, 0.6 (PASS, FAIL, NOT NEEDED; exit 1: send, do not repeat) |
| CI-m4 "do not start again" vs v3 "retry at most once" | deliberate deviation from v3 step 17 (safer: repeated failed logins can trigger a Google alert); stated here |
| CI-m5 draft statement line | card line 3 (this file corrects the v13 row ST-m4 which said line 1) |
| OP L12 decision numbers | OP L12 now "decision 1 and decision 8" |
| Notice wording blank | S blank B9; C E.2; A5; OP L1 |
