# Not checked, real-v5-only take (open items only; rewritten 2026-11-16 11:58 UTC / 17:28 IST by the system-map session)
Source: an unverified zoom-out read of REPORT.md, flowcheck/REPORT.md, flowset/REPORT.md and DECISIONS-2026-11-16. Items settled by decisions 1 to 12 are removed: patched copy chosen (lead answer 10:20Z), source tree and licence copies (decision 11), S9-1 and S9-4 deferred and no closed-gate claim (decision 5), scenes 5 to 11 cut (decision 1), HubSpot write scope moot because the take never deletes (decision 2), proof screen is a rehearsal capture (decision 9). T19 (the test for "processed once") has not run. Nothing below is verified.
Words: studio lead = the Claude session that runs technical steps; owner = the person who types answers; rehearsal = test run on the laptop without a real account (decision 12, target tonight or tomorrow morning IST).
| # | open item | person | due |
|---|---|---|---|
| 1 | Real-v5 flows have never run in n8n with real settings (the fill script for `$env` values is not built, BL-wp6-G1). Import the filled copy on the laptop, send one made-up lead, reach MarkDone. Yes/no: did it reach MarkDone? | studio lead | before the rehearsal, 2026-11-16 or 17 (UTC and IST to be written when scheduled) |
| 2 | Run T19: does `Claim` hand on one item when the insert is empty? Yes/no. The claim "processed once" depends on it. | studio lead | in the rehearsal |
| 3 | Re-check the regenerated flow folder (flowcheck on the final folder, write its git sha). | core-hardening session | after the folder is on a fetchable branch |
| 4 | Saved runs hold lead id, e-mail and name. Is the n8n executions list kept off camera or cleaned? Look at the executions page and the Postgres tables in the rehearsal. | studio lead | in the rehearsal |
| 5 | List the mail sender and the 3 recipients; confirm all are the owner's own inboxes. No program check enforces this (S9-1 deferred). | owner | before the written yes |
| 6 | Run sheet is not in this checkout (it is on origin/demo/handover). Mark scene 1 to 4 sentences that mention stand-ins, refusal, 60 s or counts. | studio lead | before the film |
| 7 | flowcheck blind spots (writes without "crm" in the address, `$node[...]`, disabled steps). | core-hardening session | after the rehearsal |
| 8 | Duplicate behaviour of `CrmUpsert` on the owner's own free HubSpot trial is unchecked. | studio lead | in the rehearsal |
