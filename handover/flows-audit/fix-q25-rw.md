# fix-q25-rw: Q25 and Q26 applied to RUNSHEET-WORDING.md and CLAIMS-TABLE.md

Date 2026-11-16. Static edit only. Nothing run, nothing deleted, nothing committed. EGM review and evidence were not run here; the lead runs them.
Backups of both original files: scratchpad folder bak-q25-rw/.

## Checks (real output)
- check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md: RESULT PASS (159 rows).
- claims-count.py: 327 ids, 327 unique, 0 offenders; to-do rows 87 (unchanged; only text was edited, no verdict word changed).
  Verdicts: SUPPORTED 124, RELAYED-ONLY 69, OVERSTATED 54, UNTRACED 51, UNSUPPORTED 29.

## Applied
Q25 items 1-5, 6, 7, 8, 9, 12; citation-check Majors 1-8 and nits (RWQ-n labels, Q21 answered, one choice for A-012). Q26: r20/r21/r22 are scripts and tests only; no change.

## Open or uncertain
- A-012: one choice made by me (no CRM clause, no mail_sent); the lead may veto.
- RWQ-7 answered by inference from Q22 item 2; the lead should confirm.
- Item 8: decision 1 (not 4) in DECISIONS-2026-11-16.md covers recovery numbers; ORDERS line 121 says decisions 1 and 4. Files cite decision 1.
- Who types y/challenge/end and who revokes passwords and the model key: marked "lead fills in".
- A-016g held; N-5b held until the lease is confirmed at re-pin.
- Claim half of Q-W unanswered.
- Stale text in files I may not edit: OWNER-STEPS-q16-rows.md (T2/T3/T4/T12), FIX-PLAN.md (b4, b7), VIDEO-RUNSHEET.md lines 6 and 21, QUESTIONS.md.
