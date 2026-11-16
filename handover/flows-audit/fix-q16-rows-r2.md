# fix-q16-rows-r2
Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-q16b/OWNER-STEPS-q16-rows.md
Edited only OWNER-STEPS-q16-rows.md (plus this log). Nothing run except grep/ls reads.

## Could not verify first
- Where the "take folder" lives, and who defines it (not in v3, ORDERS, or DECISIONS).
- That the older table makes the alert step fail in practice (read from files only: cron 30 s line 10, onError continueRegularOutput line 141, columns used at lines 124/204/228; old file has 0 matches for "alert"). Not run.
- That INTAKE_ADDRESS_PLACEHOLDER is the RECEIVER mailbox (inferred; file shows only toEmail).
- The psql command and output shape: written from information_schema, not run.
- Reviewer claims R1-R8 were unverified words; each checked against the files above.

## Changed rows
R1 all rows 1-3 labelled "Nothing for you to do. For the lead."; row 4 stated as an owner action (written yes with numbers). R2 "coordinator" removed, "the lead" only. R3 "lead table" replaced by "the table that stores incoming people (mf_leads)". R4 row 1 rewritten (repo-root paths, lead copies before DB creation/import, take folder defined, older file named, claims cited with lines or marked not run, v3:166 noted). R5 row 2 rewritten (first send defined, psql shape, 4 expected rows, lead stops). R6 row 3 rewritten (which address each placeholder is, owner-types-nothing contradiction against v3 step 8, version words explained once). R7 "re-pin" replaced by plain phrase. R8 "answer Q16" removed from text (header says "the lead's answer to question 16", kept only as a header source note).
Rows marked lead-verifies kept (all four).

## Lead questions
1. Where is the take folder?
2. Where does the lead get the From and intake addresses (v3 says owner sends none)?
3. Is INTAKE_ADDRESS the RECEIVER mailbox?
