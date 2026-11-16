# "What did we not check" lane, REAL-V5 take (agent a8df56e3; condensed by flows-audit; reviewer words unverified; it read DECISIONS, flow-check README, FIX-PLAN, FINDINGS 1-96, REPORT top 80 only)
G1 Blocker: no take start-state gate (table 0 rows for take keys, mailbox and run list empty/filtered, HubSpot search empty, fresh keys per attempt). -> FIX-PLAN item 3 + flow-check README "Before the take" (lead Q22-3 agrees; owner sheet r6 carries it).
G2 Blocker (claim can be false): "processed once" has no observable counts; CRM upsert is keyed on e-mail so a contact count cannot prove one CRM call. Say "one mail sent, one row in state done, one CRM contact"; ban "CRM called once". (Lead Q22-4 agrees; CT change pending.)
G3 Major: counts proof from rehearsal or Postgres preview needs a label ("from rehearsal, take id X" / time of preview) and a SELECT-only login.
G4 Major: expected run list and timing of POST 2 not written (second entry run still appears; if POST 2 lands while the first holds the claim, reply is "stored" early); sender retry on non-200 could make 4 posts (sender not in repo).
G5 Major: lease 45 s vs recovery every 30 s; no Qualify/CRM timeout compared with 45 s; check in rehearsal or switch recovery off for the take.
G6 Major: clean-up contradiction (FIX-PLAN item 4/FINDINGS "deleted at clean-up" vs Q19-1); no owner for rows, saved runs, mail. Pick one sentence everywhere.
G7 Blocker (leak): what the camera shows is never scanned for personal data or secrets (mailbox addresses, env-derived values, credential names). Add shown-not-opened list, made-up addresses, one full watch before publishing.
G8 Major: which mailbox is shown; stray alert mail rule = stop and retake.
G9 Major: no abort/retake rule.
Not read: FINDINGS 97-136, CT, RW, OWNER-STEPS, QUESTIONS, PLAN-4, flow JSON.
