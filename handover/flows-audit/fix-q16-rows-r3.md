# fix-q16-rows-r3 (flows-audit fixer, third pass)
Could not verify first: no check was run (static edit). Not found in any file: the take folder location; where the two addresses come from; whether INTAKE_ADDRESS is the receiving mailbox; whether id equals vid. fill_flows.py path found: handover/flows-audit/fill_flows/fill_flows.py (not run). Backup: scratchpad/bak-q16c/.
Verified against files: 4 alert columns only in v4 SQL (0 "alert" in older); lines 9,10,124,141,177,178,204,228 of mf-recovery.json; lines 117,146,256,257,284 of mf-sub-crm-mail.json; v3 line 166; decision numbers 5 (ORDERS Q17), 8 and 12 (DECISIONS). New finding: DESK_ALERT_TO (line 178) is a third address, source unnamed.
Majors 1-13 and Nits 14-22 applied; nit 17 no change needed.
