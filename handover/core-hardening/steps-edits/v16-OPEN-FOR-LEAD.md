# v16 open for the studio lead (the package is NOT handover-ready until these are answered)

Written Mon 16 Nov 2026. Nothing here was run against any real system. "Proposal" = my suggested value, not sourced: the lead decides. v15 blank B-n is now open item OI-n (same numbers); OI-30 to OI-38 are new. The sheet is ONE file, `OWNER-SHEET-v16.md` (the lead's answer "collapse to one sheet" is applied). Every OI-1 to OI-38 has a row below, and the text in the "What is needed" column repeats what the sheet says.

## A. Open items (owner sheet carries the number only; values go here first)
| OI | What is needed | Proposal or source |
|---|---|---|
| OI-1 | How the three n8n connection values (Postgres app role, sender's mail login, HubSpot key) get into n8n; the checker expects three (go item 4) | Source: DECISIONS-2026-11-16 (three credentials). No source for the method |
| OI-2 | Exit-code rule for person C "unknown" and every number the take program leaves (go item 7) | R2 facts say no code for person C yet; proposal `none` |
| OI-3 | Database server and names of the clean start, and the file and line that show two databases on one server (go item 9); caption "one Postgres server, two databases" only with that evidence | Lead |
| OI-4 | Model account page names, the prepaid and auto-reload page, the emergency cancel click path | Lead reads from the console; not verified by me |
| OI-5 | Is step 0 run at all (it writes live to the HubSpot test account; the earlier decision said no extra real-account smoke: still open, see B.2) | Lead chooses: keep gated, or drop step 0 |
| OI-6 | Per-key spending limit: exists (page, amount) or "none exists" | Lead looks in the console |
| OI-7 | Permission names of the HubSpot key in n8n and of the probe key | Lead reads from HubSpot |
| OI-8 | What the local flow copy holds and when it may be erased; answered before the model key exists | Facts from another session (DESK_URL, DESK_TIMEOUT_MS, DESK_ALERT_TO plus placeholders): NOT verified by me |
| OI-9 | Real wording of the notice and the printed result (does the printed result show person A sent twice with one person id?) | Lead copies from the program |
| OI-10 | Call ceiling with file and line; whether retries by the model software and a restart of the model program are inside it; whether it holds for the whole life of the key; whether the backstop refuses a further call; measured in the rehearsal, else "informational only"; answered before the model key exists | Lead |
| OI-11 | What the take program does on a wrong line after `end`, Ctrl-C, or the film pause ending | Lead reads the program |
| OI-12 | Go item 5 statement (file and line): no delete or archive call in the take program and the named repository files; node types of the flows; the fields removed before a flow checksum (expected: ids, created and updated times, version counters) | Lead exports the flows through n8n's API after activation and shows the form is stable across two imports |
| OI-13 | The lease sentence (appendix 7): NOT APPROVED. Which is true: the ORDERS answer (Q21.2) says no takeover after the lease ends unless the file says otherwise; plan-v10 lines 456 to 459 (Text B) and the v15 candidate said recovery re-claims an unfinished lead up to three tries. v16 withdrew the contradictory wording and carries only "a stored person id is skipped, the lease is not claimed to recover anything" | Lead runs the crash test and chooses; owner is told the result before posting |
| OI-14 | Who creates the Postgres app-role password and who enters it into n8n | Lead (proposal) |
| OI-15 | Is the take program's own HubSpot login the same key as n8n's; its permission names | Lead |
| OI-16 | Time you have at "Type y to start" | Proposal 5 minutes (unsourced) |
| OI-17 | Retire-check runs allowed | Proposal 3 (unsourced) |
| OI-18 | E.0 begins this long before the latest start | Proposal 20 minutes (unsourced) |
| OI-19 | Start margin in the latest-start formula | Proposal 15 minutes (v15's "5 minutes" was less than the program's own start margin of about 860 s, v3 line 171: corrected; at least that margin) |
| OI-20 | Where the probe key comes from and who creates the probe key file | Lead decides |
| OI-21 | Clock tolerance between `date -u` and the Windows clock | Proposal 2 minutes |
| OI-22 | Usage page lag and gap before the second cancel reading (gap at least the lag); measured against the ledger in the rehearsal, else "informational only" | Proposal lag 30 minutes, gap 30 minutes (v15's gap of 15 was shorter than its lag: corrected) |
| OI-23 | Who holds rows 4 to 7 and 15 (humans); who may see a take marked "Key exposed" (proposal: only the studio lead and the owner; rows 4 and 15 never the owner; the owner holds at most one of rows 5 to 7; so two other humans) | Proposal |
| OI-24 | Highest balance the owner accepts | Lead and owner |
| OI-25 | Token counts and model name per call, where the limit is enforced, hidden thinking tokens, whether the program obeys the settings file | Lead |
| OI-26 | Second fact per Gmail account (for A.5, I.1, step G) | Lead |
| OI-27 | When n8n is switched off after the run, and the wording of "n8n is off" | Lead |
| OI-28 | Length for the long-string filter in 0.5; rehearsal proof that the real result file passes both filters (the contact-owner change may print a real owner address) | Proposal 30 |
| OI-29 | Rehearsal stamp (date UTC and IST, transcript file) | Lead after a rehearsal; I cannot fill it |
| OI-30 | Recording tool and where the file is saved | Lead; none exists in any input |
| OI-31 | How the finished clip, proof screen and post text travel between owner, row 6 and row 15; what row 6 may see | Lead |
| OI-32 | Posting site, who uploads, the player used in step H | Lead and owner |
| OI-33 | The place where owner and studio lead exchange written messages (a go message arrives there) | Lead |
| OI-34 | The real scenes of the shot list (the writer's list is a proposal) and whether the person C "unknown" line is shown (proposal: cut) | Lead |
| OI-35 | The exact step 0 contact address and exact probe private app name for the go step 0 message | Lead |
| OI-36 | What the receiver mail list shows in its From column, from the rehearsal | Lead |
| OI-37 | Confirm each owner step beyond `y`, challenge and `end` (A.0, A.5, step 0, I.x, G) is wanted; the earlier decision said the owner only types those three | Lead |
| OI-38 | Whether the studio lead's scripts need the n8n owner login (secrets table); if not, say it is never shared | Lead |

## B. Questions and facts for the lead
1. One file: DONE in v16 (`OWNER-SHEET-v16.md`: Part 1 steps, Part 2 day card, Part 3 appendix). The v15 three files are untouched (nothing deleted). Part 1 is 36,315 bytes against v15's 35,882: about 430 bytes over; the whole file is larger than v15's three files together (see v16-CHANGES.md).
2. Step 0 versus the earlier "no extra real smoke" decision, and "the take never deletes": step 0 still creates, changes and tries to delete one contact in the test account (OI-5). Also ORDERS Q17 still counts the owner's HubSpot probe as covering the HubSpot node.
3. DECISION-one-store line 14 still says "ONE database": your input; v16 uses "one Postgres server, two databases". AGENT-SCOPE section 3 needs a rewrite (the delete-call sentence). I may not edit inputs.
4. US$180 versus US$189: the sources disagree (FACTS: "US$180 of 189 in-code backstop"; AGENT-SCOPE: "backstop setting, US$180 of 189"); the owner sheet no longer mentions either; say which is the backstop and which the credit.
5. The take scripts `n8n_kill.py`, `n8n_start.sh` and `run_real_check_n8n.py` are on no branch in this checkout; the owner text marks what they do UNVERIFIED (appendix 10).
6. Take key read-only line (ORDERS Q20.3): the sheet claims no HubSpot identity is read-only; it lists permission names (OI-7, OI-15). If the take's own key is read-only, say so and I will add the sentence.
7. Contact ids: no file gives them; the delete method uses exactly one search result per address plus the list's shape check (appendix 8). If the take program can print HubSpot contact ids, tell me.
8. Writer additions beyond the inputs (remove any you do not want): the stop word Time; key name `run-<run name>`; people window rule 9; Decimal price calculator; appendix 8 delete method; OI-30 to OI-38.
9. Not looked up: any bible R-number (the bible is not in this checkout).
10. I did not run any command in the sheet; I tested only the Decimal calculator and `TZ=UTC` on this sandbox (not WSL).
