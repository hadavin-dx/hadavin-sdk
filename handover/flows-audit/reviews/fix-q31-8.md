# fix-q31-8 (QUESTIONS.md Q31 only; no other file edited; not committed)

Not verified: RUNBOOK/TAKE-CHECKLIST text beyond the lines I grepped (step 30 exists; steps 4a/4b/19a roles; sections 6 and 8 chains 367/422 = Case A/B, 55 minutes apart); the "N6 chain on a later day" reading in items 84/85 is marked UNVERIFIED; the "about 116" count of sub-answers is rough; no clock file (FIX-PLAN/TAKE-CHECKLIST) touched, so no clock diff run.

Verified real and fixed: stale 75 count (now 79 + 1 + 1 = 81); item 85 (11:55Z limit exists in no RUNBOOK/TAKE-CHECKLIST/FIX-PLAN line, dropped; limit is 12:00Z; both chains asked; implied step 1 starts 02:24Z/01:29Z (zero margin), 02:19Z/01:24Z (5 min); limit applies only to the last slip day Mon 23 Nov); item 84 default no longer tested against item 85 on Wed 18; "send" vs contact/mail wording (glossary sentence; "positive-control mail run/script"); Timing case vs chain sum merged into one pair (chain sum names removed); "five different things" now two pairs; steps 1 to 30 and 4a/4b/19a; THE GATE replaced by GO row 7 / Tuesday GO test; item 3 default per sub-question; item 8 (b)/(c) one answer; item 8(e)/49 one winning default (patch not used); item 14(b) default = item 38(a) default; line 421 AUDIT PROPOSAL wording and "items 1 to 31 only" sentence; index rows (step 4a/5 one default per item, item 87 time, 06:55 row order, item 9 default, item 40 time, "step does not run" text for import); delete message 1 window 07:30-07:40Z (items 5, 8d).
Found stale (already fixed earlier, no change): item 38(f) has a time and index row; item 53 is 06:00Z everywhere; item 9 has a concrete default; "less than 31" absent.
Not changed (nits): history text inside items 15, 32; PARTLY SUPERSEDED label inside item 8; naming nits.

New item 88 (DB_GRANTS item), appended after item 87; counts updated in lines 40, 42, 449, 605 and the index (group B 04:54Z row, group D).

My grep count: main list 81 numbered (79 OPEN, 1 ANSWERED item 20, 1 NOTE item 66); second list 7 (1 OPEN item 40, 1 ANSWERED item 43, 5 NOTE) plus 15A OPEN: 89 labelled, 81 OPEN. Every OPEN main item appears in lines 513-575 (script check printed no misses).
Checks (from flows-audit): check_refs PASS 5176; check_names PASS 655; check_secrets PASS 0 hits; ruff format --check: 720 files already formatted.
