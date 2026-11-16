# Corrections to plan-v10-real-v5-edits.md when the edits are applied AFTER the patch chain (2026-11-16, chain builder; fix pass 2 after review-chain-r1.md)
The old file `plan-v10-real-v5-edits.md` is NOT edited (only a banner at the end of its line 1). It was written against the unpatched plan (input sha256 starts `67a0a195537de875`). After the chain `plan-v5-fixes.patch`, `plan-v5-repin-v6.patch`, `plan-v5-gate-rows-v3.patch` (see `PLAN-CHAIN.md`; plan sha256 must start `515cf4704ebba5bd`) the old list needs these changes. Do not apply the old list alone on the chained plan: `apply-v10-after-chain.py` does both and refuses a wrong input.
What is replaced or added here (9 blocks below; the other 22 edits of the old list are used unchanged and in their old order):
- Edits 2, 18, 19, 20, 21: old text no longer found after the chain (the floor minutes, steps, unrun files and the section 7 row count moved); replaced by edits written against the chained plan.
- Edit 4: old text found, but its new CHANGES row said "steps 151 to 153, clean floor 171 to 173 min = 2 h 53 min"; after the chain the right values are steps 154 to 156 and 174 to 176 min = 2 h 56 min.
- Edit 5: old text found; its new text is now the whole floor sentence including the HISTORY words, which said "which is what section 5 says now" (true only at 174 min). Edit 30 (added here) does the same for the second HISTORY row ("lead ruling 3 (estimate)").
- Edit 21 keeps the sentence about line 1 of `INDEX.md` ("Evidence: real-v5 minus ONE node (CrmUpsert), loopback; not real-v5 as shipped", lead answer Q17), because edit 13 refers to it.
- Edit 29: the old edit appended UNVERIFIED items 13 to 16 after item 12, but the chain already has items 13 to 16 (`plan-v5-fixes.patch` adds 13, `plan-v5-repin-v6.patch` adds 14 to 16). Applied as written the list would run 12, 13, 14, 15, 16, 13, 14, 15, 16. The corrected edit 29 appends the four items after chain item 16 and numbers them 17 to 20.
- Cross-references: the NEW text of edits 8, 13 and 27 says "UNVERIFIED 13", "14" and "15" meaning the four new items. The script adds 4 to each of those numbers inside those three edits only (rule line below), so they read 17, 18 and 19. Nothing else is renumbered; the header lines 3, 9 and 11 of the old file are not applied text.
RENUMBER edits=8,13,27 from=13 to=16 shift=4
Arithmetic (chain end: 154 steps, 174 min = 2 h 54 min, 77 unrun files, section 7 heading "(23 rows)"; v10 adds 2.1b = 2 steps, 2 minutes, 1 unrun file (old edit 20), 1 row CS): 156 steps, 176 min = 2 h 56 min, 78 unrun files, 24 rows. The "+1 unrun file" and "+1 row" are taken from v10 (edits 20 and 21); they were not re-counted by hand against the chained plan.
Edit 6 of the old file (the `$R/demo` archive line) is unaffected by the chain and stays as it is. Take the +1 unrun file from old edit 20, not from edit 6.

## Edit 2 (corrected): plan line 6 after the chain (RIGHT-SIZE, floor time)
~~~~old
Floor about 2 h 54 min clean
~~~~
~~~~new
Floor about 2 h 56 min clean
~~~~

## Edit 4 (corrected new text): CHANGES FROM v5 block, row "time" (steps and floor after the chain; old text found)
~~~~old
## CHANGES FROM v4 (every round-3 finding and lead ruling, and the step that fixes it)
~~~~
~~~~new
## CHANGES FROM v5 (real-v5 edit, 2026-11-16; lead answers Q15.1, Q15.2, Q15.3, Q17; DECISIONS-2026-11-16 items 1, 2, 8, 10)
| id | finding | fixed in / verdict |
|---|---|---|
| Q15.1 | step 2.1 filled the film flow set; cases A, B, B2 ran on it | 2.1 fills `n8n-flows-real-v5`; P-2 archives it; 2.1b swaps only `CrmUpsert` for the loopback stand-in (the HubSpot node would leave loopback); every film reference removed or marked LATER VIDEO |
| Q17 | what the loopback evidence is called | exactly "real-v5 minus ONE node (CrmUpsert)"; never "real-v5 passed" (header, section 7 title note, section 9) |
| what runs | the plan said "real-v5 at run time" without saying what runs | section 9 now says: real-v5 runs minus one node; the HubSpot node, its credential and its real answer are not exercised |
| claim wording | "processed once" overreaches | both wordings carried in section 10b, labelled Text A (Q15.3) and Text B (Q21.2, DECISIONS item 1, plus one lease sentence); the lead picks one (lead decision 6); claim limited to the claim step and scenes C and E; read in the flow files, not run |
| Q15.2 | no clean start before the take | row CS in section 7 (proves only that the table is empty at T0 here) and section 10b (the lead's steps; the parts beyond Q15.2 are marked there as drafter additions) |
| static pass 6 | empty or missing lead-record id untested | named in section 9 as not proven |
| time | 2.1b adds a step | S2 12 to 14 min, steps 154 to 156, clean floor 174 to 176 min = 2 h 56 min (2.1b = 2 min, a builder estimate, not measured) |
| not changed | A, B, B2 pass rules; `mf-form.json` (holds the Claim node) has the same whole-file sha256 in real-v5 and film-v5: `74a823d4bc99`, `evidence-A2.md:7` and `:11` (`mf-hook.json` too, `:6` and `:10`; `mf-recovery.json` and `mf-sub-crm-mail.json` differ) | so the claim-path result carries over; only the CRM call (and the recovery and mail files) differ |

## CHANGES FROM v4 (every round-3 finding and lead ruling, and the step that fixes it)
~~~~

## Edit 5 (corrected): CHANGES FROM v4 table, estimate row (the HISTORY text of this row says "what section 5 says now"; after this edit section 5 says 176)
~~~~old
171 min clean is a floor (HISTORY: the re-pin patch made section 5 say 172 min = 2 h 52 min; the gate rows then made it 174 min = 2 h 54 min, which is what section 5 says now)
~~~~
~~~~new
176 min clean is a floor (HISTORY: the re-pin patch made section 5 say 172 min = 2 h 52 min; the gate rows then made it 174 min = 2 h 54 min; the real-v5 edit makes it 176 min = 2 h 56 min, which is what section 5 says now)
~~~~

## Edit 18 (corrected): section 5, steps total
~~~~old
| **steps** | | **154** |
~~~~
~~~~new
| **steps** | | **156** |
~~~~

## Edit 19 (corrected): section 5, clean total
~~~~old
| **clean total (a FLOOR, not a quote)** | | **174 min = 2 h 54 min** |
~~~~
~~~~new
| **clean total (a FLOOR, not a quote)** | | **176 min = 2 h 56 min** |
~~~~

## Edit 20 (corrected): section 5, quote sentence
~~~~old
2 h 54 min is a floor: about 77 files are unrun
~~~~
~~~~new
2 h 56 min is a floor: about 78 files are unrun
~~~~

## Edit 21 (corrected): section 7 heading (the INDEX.md line 1 sentence, lead answer Q17, is kept; edit 13 refers to it)
~~~~old
## 7. PASS/FAIL table to fill in `evidence-2\INDEX.md` (23 rows)
~~~~
~~~~new
## 7. PASS/FAIL table to fill in `evidence-2\INDEX.md` (24 rows)
Line 1 of `INDEX.md` reads "Evidence: real-v5 minus ONE node (CrmUpsert), loopback; not real-v5 as shipped" (lead answer Q17); line 2 is the hash line of 2.1b.
~~~~

## Edit 29 (corrected): UNVERIFIED items, appended after chain item 16 and numbered 17 to 20
~~~~old
PowerShell (P-2, P-5, 9.0k, 11.0k, 13.5k) and `wsl.exe` were not run.
~~~~
~~~~new
PowerShell (P-2, P-5, 9.0k, 11.0k, 13.5k) and `wsl.exe` were not run.
17. The glue `fill_flows.py` and `drive.py` (take-branch files, local only, not readable in this plan's inputs; the lead verifies at re-pin): that the glue accepts the flow-set word `real`, prints `filled real 4 object`, fills the real-v5 tokens (`DESK_URL`, `DESK_TIMEOUT_MS`, `DESK_ALERT_TO`) and the placeholders only real-v5 has (`FROM_ADDRESS_PLACEHOLDER`, `INTAKE_ADDRESS_PLACEHOLDER`, `HS_CRED_PLACEHOLDER`) from `flow-values.env`, and exits non-zero while a placeholder is left. The lead edits 2.1's expected line before the run.
18. Step 2.1b: that n8n 2.46.6 imports and runs the swapped `CrmUpsert` (an HTTP Request node, version 4.2: the node type and version of the film flow's `CrmUpsert` and of `Qualify` in the same file); that the heredoc python is free of syntax errors on the laptop (it ran on Linux in scratch copies: `swap-test-negative.txt`); that `CRM_URL=http://127.0.0.1:8771` is a line of `flow-values.env` (step 1.2 of the plan lists it; not run); that `$HD` holds commit `5fdc659d1` for the recipe's `git archive`; that `crm_stub.py` on the laptop answers `{"id": <whole number>}` as the scratch copy does, and that n8n 2.46.6 evaluates the `CrmIdOk` expression as read (`swap-test/input/mf-sub-crm-mail.json:146`: true for a whole-number `id`; the expression is read, its evaluation in n8n is not run); that the PowerShell command of the film-file recipe (`git -C $HD archive -o ...`, then the file-exists and size test) runs on the laptop and that `$S` is the folder bash sees as `$W/_local/scratch/wp6-smoke` (the bash paste ran on Linux, 1 positive and 7 failing cases). The node's 10000 ms timeout is the film node's own value and is above the 8000 ms CRM hold (section 2, row `crash holds`), as it was in the film set.
19. The take's database, schema, table, logins and read-only count role names for section 10b, the take's n8n health address (`N8N_HEALTH_URL`) and how the take stops n8n, and that the lead's own machine has `psql` 13 or newer (the export file is written by `psql` on the machine where it runs): the plan's own container uses database `postgres`, schema `app`, table `mf_leads`; DECISIONS item 10 says the take has its own database; the take's names are not read; the lead fills `TAKE_DB_NAME`, `SCHEMA`, `PGURL` and `OUT` (the paste was tested only with a scratch server: login by password file on 127.0.0.1, users `own_t` and `cnt_t`, database `take_db`, schema `app`). Also unverified: `COPY` and `\o` output on the take's `psql` version (tested with psql 16.15); the command `n8n list:workflow --active=true` in step 3 route B (not in the plan's own steps: 2.5 uses `list:workflow` without the flag); a PGPASSFILE read on Windows-side `psql` (the paste is bash; tested on Linux only).
20. That the exported list matches the contacts really created in HubSpot: the list holds the made-up lead records sent to the flows, not what HubSpot holds; the owner checks the HubSpot contact list against it after the take.
~~~~

## Edit 30 (added, not in the old list): second HISTORY row of the plan (the "lead ruling 3 (estimate)" row of the CHANGES table), same stale "says now" text
~~~~old
realistic 3 h 20 min to 4 h 05 min (HISTORY: the re-pin patch made section 5 say 172 min = 2 h 52 min; the gate rows then made it 174 min = 2 h 54 min, which is what section 5 says now)
~~~~
~~~~new
realistic 3 h 20 min to 4 h 05 min (HISTORY: the re-pin patch made section 5 say 172 min = 2 h 52 min; the gate rows then made it 174 min = 2 h 54 min; the real-v5 edit makes it 176 min = 2 h 56 min, which is what section 5 says now)
~~~~

