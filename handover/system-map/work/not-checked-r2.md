UPDATE 16 Nov 10:35Z: item 2 (patched or unpatched) is DECIDED by the lead's answer 10:20Z: the PATCHED real-v5 copy (F-002 and F-008 applied, then the fill values). The licence test failure is a branch artefact (decision 11); the vendor-word failure is gone at 60338533. S9-1 and S9-4 are deferred, describe-only (decision 5): do not claim a closed gate. T19 is still not run.
# Not checked, real-v5-only take (zoom-out read, 16 Nov 2026; unverified reviewer report, files read: REPORT.md, flowcheck/REPORT.md, flowset/REPORT.md, DECISIONS)
Ranked. Items 1 and 2 can end the take; the rest can be fixed in a day.
1. Real-v5 flows never ran in n8n with real settings (the `$env` fill is not built, BL-wp6-G1). Check on the laptop: import filled copy, post one made-up lead, reach MarkDone. Laptop only; tonight IST.
2. Which flow files are imported (patched or unpatched)? F-002 and F-008 change the generator only; committed JSON is unchanged until regenerated. Claim "processed once" depends on `Claim` handing on one item when the insert is empty (flowcheck: NOT VERIFIED; test T19 not run). Decide and write down the imported state first.
3. Regenerated folder must be re-checked (flowcheck on the final folder, record its git sha). Cloud can do it once the folder is on a fetchable branch.
4. Two guard tests fail on core-hardening (vendor-word, licence): choose the source tree for the take and run the full suite there, gate on exit code.
5. Saved runs (F-008) hold lead key, e-mail and name; nothing says the n8n execution list stays off camera or is cleaned. Check n8n executions page and Postgres tables in the rehearsal.
6. Mail sender and the 3 recipients are not listed; confirm all are the owner's inboxes and that nothing sends before `y` (S9-1 deferred, so nothing enforces this).
7. Run sheet is not in this checkout; open it on origin/demo/handover, mark scene 1 to 4 sentences that mention stand-ins, refusal, 60 s or counts; answer open question D.
8. flowcheck blind spots (writes without "crm" in the address, `$node[...]`, disabled steps); HubSpot create/update scope and duplicate behaviour of `CrmUpsert` unchecked (owner's own free trial).
Small: the proof screen from decision 9 is a rehearsal capture; the caption must say so.
