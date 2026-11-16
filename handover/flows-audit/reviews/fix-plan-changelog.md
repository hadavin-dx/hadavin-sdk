# FIX-PLAN changelog (round 64 fixes; made-up data; static review, nothing run)
Written by the fixer. Reader findings are from reviews/fix-plan-reader-r64.md. Round and finding labels for the new text live here, not in FIX-PLAN.md.
- B1: Step 14 Pass line written; self-check item 7 prints `gate-pass` or `gate-pass-e-not-checked`; the second word opens only the sends before Row 4, the positive control and rehearsal 1; RUNBOOK step 24 must treat it as FAIL.
- B2: Step 0a (4) is the only maker of shas.env; Block R3 only appends and refuses if the file is missing; take-folder path due 03:30Z (09:00 IST) is needed before R3 (03:00Z, 08:30 IST).
- M3: step-own words (`-LABEL` suffixes, `mail-count-ok-step10`, `-row4`, `-control-1`, `-control-2`, `-rehearsal-A`, `-rehearsal-B`, `db-is-take-db-iv`, `sha-pin1-line-ok`).
- M4/M5/M10/M11: new section "How each step passes"; new self-check items 12-15; last-section table gets item 50 row; BLOCKED text now says which table holds which word; owner row added to Roles.
- M6/M7/M12/M13/M14/M15: Step 4 text, WARN reader time 03:30Z (09:00 IST), Case A/B, three gates, 307-minute sum, Step 3a word.
- M8: 08:00Z re-pin statements labelled "only if step 1 starts at 03:31Z (09:01 IST), otherwise 08:29Z (13:59 IST)".
- M9: item 50 due Tue 08:29Z (13:59 IST).
- M16: general rule on line 35: a LEAD FILLS/DECIDES with no own time is due at its row time, else Tue 04:00Z (09:30 IST); named times added for Steps 10, 12, 13.
- M17: UTC/IST pairs added in Steps 12 and 13 and Wednesday schedule.
