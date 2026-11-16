# fix-q16 (fixer, text only, nothing ran besides the two scripts)
Failures: none. Not checked: Postgres, n8n, fill_flows, take folder (not here); the lead verifies at re-pin.
Source: ORDERS.md "ANSWER (lead, 10:29Z): Q16". Backups: scratchpad q16/ (CLAIMS-TABLE.md, QUESTIONS.md, RUNSHEET-WORDING.md).
Own check by reading: demo/n8n-flows-v4/mf_leads.sql lines 17-20 define alert_sent, alert_token, alert_until, alert_attempts. demo/n8n-flows-real-v5/mf-recovery.json uses them at lines 124, 204, 228. Placeholders: mf-recovery.json:177, mf-sub-crm-mail.json:256-257.
Applied: QUESTIONS.md Q16 marked ANSWERED; CLAIMS-TABLE.md to-do rows 85, 86, 87 (Table 1, [LIVE], lead verifies at re-pin), counts text (20 live rows, 87 rows, row ranges, index entry); new file OWNER-STEPS-q16-rows.md.
Counts: claims unchanged (327; SUPPORTED 124, RELAYED-ONLY 69, OVERSTATED 54, UNSUPPORTED 29, UNTRACED 51); to-do rows 84 -> 87 (script: 87).
Commands: python3 claims-count.py CLAIMS-TABLE.md rc=0 (offenders 0); python3 tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md rc=0 (RESULT: PASS). RUNSHEET-WORDING.md unchanged (new rows carry no claim id).
