# v15 open for the studio lead (the package is NOT handover-ready until these are answered)

Written Mon 16 Nov 2026. Nothing here was run against any real system. "Proposal" = my suggested value, not sourced: the lead decides. Every blank B1 to B29 of the sheet has a row below.

## A. Blanks (owner files carry the number only; values go here first)
| B | What is needed | Proposal or source |
|---|---|---|
| B1 | The three n8n connection values: Postgres app role, mail, HubSpot key; who creates the Postgres one | Source: DECISIONS-2026-11-16 (three credentials). Who creates it: no source; proposal the studio lead |
| B2 | Exit-code rule for case C "unknown": `none`, or one number plus the exact printed result | Source: R2 facts say no code for C yet; proposal `none` |
| B3 | Take database server, database and table names; caption "one Postgres server, two databases" only with evidence | Names: lead. Caption: only with written evidence (a printed listing) |
| B4 | Model account: usage, key list, prepaid and auto-reload page addresses; account name | Lead reads from the console; not verified by me |
| B5 | Is step 0 run at all (conflicts with the earlier decision to drop extra real checks) | Lead chooses: keep gated, or drop step 0 |
| B6 | Per-key spend limit: exists (page, amount) or "none exists" | Lead looks in the console |
| B7 | Permission names of the HubSpot key in n8n and of the probe key | Lead reads from HubSpot |
| B8 | DESK_* values the program reads; answered before the model key exists | Facts from another session (R2); NOT verified by me |
| B9 | Real wording of the notice and the printed result, sent in the step A message | Lead copies from the program |
| B10 | Call ceiling and run total (file and line) | Lead; before the key exists |
| B11 | What the program does on a wrong line after "end", Ctrl-C, or the film pause ending | Lead reads the program; UNVERIFIED in owner files |
| B12 | Node types and flow checksums for go item 5 | Lead exports the flows |
| B13 | Lease Text B (plan-v10-real-v5-edits.md lines 456 to 459): NOT APPROVED. Lead runs the crash test first and tells the owner the result before posting | Facts: recovery re-claims an unfinished lead up to three tries; a stored row blocks a second send whatever the lease |
| B14 | Postgres app-role value row in the secrets table | Lead |
| B15 | The program's own HubSpot login: name and permission names | Lead |
| B16 | Time at "Type y to start" | Proposal 5 minutes (unsourced) |
| B17 | Retire-check runs allowed | Proposal 3 (unsourced) |
| B18 | E.0 begins this long before the latest start | Proposal 20 minutes (unsourced) |
| B19 | Start margin in the latest-start formula | Proposal 5 minutes, and at least the program's own start margin 860 s (v3 line 171) |
| B20 | Where the probe key comes from | Lead decides |
| B21 | Clock tolerance between `date` and the Windows clock | Proposal 2 minutes |
| B22 | Usage page lag; gap before the second reading | Proposal 30 minutes; 15 minutes |
| B23 | Who may hold rows 4 to 7 and 15 (a human; whether the same person may hold several) | Proposal: four different people if possible; otherwise lead's rule |
| B24 | Highest balance the owner accepts | Lead and owner |
| B25 | Worst-case price per call: file and line, thinking tokens, whether the program obeys the settings file | Lead |
| B26 | Second fact per Gmail account for delete checks | Lead |
| B27 | Wording of "n8n is off" (lead's written word before F.5) | Lead |
| B28 | Length for the long-string filter in step 0.5 | Proposal 30 |
| B29 | Rehearsal stamp (date UTC and IST, transcript file) | Lead after a rehearsal; cannot be filled by me |

## B. Questions for the lead
1. Q18(3), one file or three? The sheet is the one to read; the card and the appendix are parts of it. Collapse to one file? Your choice.
2. Step 0 versus the earlier "no extra real smoke" decision (B5).
3. Approve or reject the lease Text B (B13) after the crash test.
4. The figures 180 and 189: unresolved; the earlier claim that they are absent from owner files is withdrawn (appendix 17).
5. DECISION-one-store line 14 says "ONE database": input owned by you; it conflicts with "two databases".
6. AGENT-SCOPE section 3 needs a rewrite (not touched; outside my folder).
7. SUPERSEDED banners on v4 to v13 were not added (I may edit only this folder).
8. "Index not seen" (citation-1): the primary key was seen in the v4 `mf_leads.sql` table file, not in the take database. Show the lead's psql output at rehearsal.
9. DESK_* facts from other-sessions-r2 were not verified.
10. Retake count (row 10) is yours; the take port (row 13) is named nowhere.
11. OR-4: the owner asked for a "HubSpot key read-only" card line; the answer said unknown, so the card holds permission names (B7, B15).
12. Writer additions beyond the decisions: the people list at the top, the blank-cell rule, name plus last-4 delete checks, I.0 as the single key-deadline place. Remove any you do not want.
13. No bible R-number was looked up; only the preamble rules were used.
