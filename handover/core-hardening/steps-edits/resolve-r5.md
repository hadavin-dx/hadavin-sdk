# C4 resolve pass, round 5 (money/secret/delete/data-leaving paths, uncapped), 2026-11-16
Only EDITS.md changed (and this file). Inputs untouched. Nothing run except a text check; no code, network, spend or commit. The result of round 5 is NOT reviewed yet.
## Findings and actions (all from review-c4-r4-design.md and review-c4-r4-naive.md, verified against the inputs; none contested)
| finding | action | rows |
|---|---|---|
| design M1 (loopback = no egress; "you do nothing") | word "loopback" and "nothing leaves" removed; "watched, not blocked" (plan 102); "nothing to do unless the lead asks", Docker Desktop and firewall named (plan P-4, 506) | E-03 (E-11/E-19/E-20 use only "rehearsal") |
| design M2a, naive 4 (prep paid call inside the 3) | text keeps "NO paid model call"; question moved to NOT DECIDED 6 with options, cost, risk | E-11, ND 6 |
| design M2b, naive 4 (prep contact and mail) | owner deletes prep contact and mail by hand, says "label and inbox empty" | E-11, E-04 |
| design M3 (FACTS names only key given) | E-04 why corrected; E-37 lists only what FACTS names; lead confirms read-only token and app 2; question in ND 7 | E-04, E-37, ND 7 |
| design M4, m5, naive 5 (revoke) | revoke only the key made for the take, ask first if unsure, UNVERIFIED click path, crop, "record not test", key file deleted with rm, take-folder removal is not a revoke | E-48, ND 7 |
| design m1, naive A1 | "is planned to test" / "planned to be deleted" | E-16, E-20, E-22, E-25, E-38, E-39 |
| design m2 | runner rule moved to section 4; E-35 DELETED (content merged into E-34) | E-34, E-35 |
| design m3, naive 18 | gate on independent reviewers moved to confirm g, not owner text | E-03, confirm g |
| design m4 | count screen labelled rehearsal footage, no independent-check claim | E-15 |
| design m6 | "if the program printed it"; rm not shred | E-42, E-30, E-48 |
| naive 2 | step 22 item 1 stated as the lead's job | E-16 |
| naive 3 | E-37: plain rule for step 8 (do not do until asked), heading deadline limited | E-37 |
| naive 6, 24 | gate repeated inside E-04, E-05, E-41, E-42; E-41 no quoted prompt | those rows |
| naive 7 | E-25 text now inside the cell (`<br>` = line break); separate section deleted | E-25 |
| naive 8 | E-01/E-02 no overlap; E-02 has no final full stop because `; this file...` follows | E-01, E-02 |
| naive 9 | E-06 punctuation exact, no rehearsal port, real-take port in ND 2 | E-06 |
| naive 10, 14 | E-13 line 11 old text given; both strings occur once | E-13 |
| naive 11 | E-23 replaces HEAD_PIN and PROVISIONAL wording | E-23 |
| naive 12 | R4 decision rule for E-39; apply order E-43, E-46, E-47 | E-39, E-43 |
| naive 15, 16 | server = "database server"; databases = "n8n's own database" / "the take's database"; "login" kept for mailbox/HubSpot only, "database user" for Postgres accounts; password typed by owner, lead names the user only | E-03, E-09, E-15, E-27, E-31, E-43 |
| naive 17 | E-20 split into four items, Postgres explained | E-20 |
| naive 19 | who decides pass: lead states, owner decides | E-12 |
| naive 20 | E-14 guess stated inside text; E-15 unknown words removed | E-14, E-15 |
| naive 21 | keep-or-delete rules in "Rules for the lead" R1-R5 | E-17, E-18 |
| naive 22, 23, 25 | E-01 branch names removed; fix vs review rounds; AIM/OBSERVED/EG/schema app explained; one name "rehearsal" | E-01, E-02, E-26 to E-29, E-31 |
| naive D | NOT DECIDED renumbered 1 to 7; item 1 has options a to c; prep-money and key questions added; confirm items reordered | header |
## Checks (text only)
`chk.py`: rows 46, old-text cells that do not occur exactly once: 0 (E-13 checked as two strings, line 99 and line 11), rows with an edit 43. Counts: 29/13/4 = 46; types STALE 15, UNCLEAR WORD 6, MISSING STEP 10, CONTRADICTION 12, DEFERRED 3.
## Not done / uncertain
NOT DECIDED options 1, 3, 6 are proposals; nothing read proves the start script supports them. Owner-facing new text is not yet reviewed by a stranger. The "(a firewall rule would be yours to set)" and Docker Desktop wording rest on plan lines 102 and 506 only.
