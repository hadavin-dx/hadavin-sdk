Status: DRAFT, unverified

# CRITICAL PATH r2: working backward from the take on Mon 23 Nov 2026 (written Mon 16 Nov 2026; replaces work/critical-path-r1.md, which was built on a missed 14:00 start)

## 0. Words and sources (read this first; added in the wording fix of 16 Nov 2026)
Status of this section: DRAFT. Each meaning below is taken only from the file named; "not recorded" means no file I read states it.

### 0a. Glossary
| word | meaning | where it comes from |
|---|---|---|
| take | the one filmed run of the lead-intake demo (a made-up sales lead goes into n8n, is stored once, creates one HubSpot contact and sends one mail) on made-up data. Its one claim: a lead sent twice with the same id is processed once. In this page its window ends Mon 23 Nov 18:29 UTC / 23:59 IST. Preparation and rehearsal are not a take | work/GLOSSARY.md lines 4 and 61; stop time: section 1 below |
| n8n | the tool that runs the demo steps | work/GLOSSARY.md line 62 |
| A13 | the question whether a 4-hour margin for one rerun of the take is kept. The question is written in work/owner-timeline-draft.md lines 7 and 48, which say it is on work/decision-list-for-lead.md; that decision list, as I read it (32 lines), has no row named A13 (it lists drift rows D-01 to D-10). Its answer: not recorded | work/owner-timeline-draft.md |
| A4 | the question "does run (a) start today", item A4 of work/decision-list-for-lead.md according to work/open-items-table.md lines 23 and 51. The decision list as I read it has no row named A4. Due Mon 16 Nov 13:00 UTC / 18:30 IST, passed, answer unknown (open-items-table.md line 51). "Run (a)" is the loopback re-smoke (next row), as section 2 step 5 states | work/open-items-table.md |
| row N | row N of work/owner-timeline-draft.md (the owner's order of messages), unless the text says "step N" or "chain table" (this page's table in section 2) or "r1 row" (work/critical-path-r1.md) | work/GLOSSARY.md line 64 for the general rule; my reading for this page |
| owner notice | the message from the studio lead to the owner giving the run date and start time, sent at least 3 hours before the start (row 1 of work/owner-timeline-draft.md). The owner then plugs the laptop in, sets sleep to Never and lid action to Do nothing | work/owner-timeline-draft.md row 1 |
| loopback re-smoke | a manual one-off re-run of the demo flows in n8n 2.46.6 on the laptop's own loopback address (no real mailbox, HubSpot, Gmail, model call or DNS), made-up data, US$0, re-running only what the first smoke run could not prove. The plan's own estimate is 171 min | inputs/plan-wp6-resmoke-v5.md lines 1 and 5 |
| fill_flows.py | a script that puts the laptop's settings into the n8n flows (open-items-table.md line 45). Whether it exists is UNVERIFIED: open-items-table.md says "not built", the plan (lines 4 and 223) says it read one, and I did not look on disk | work/open-items-table.md; inputs/plan-wp6-resmoke-v5.md |
| HEAD_PIN | the exact code version (commit eec6ba4 on branch take/nlite-int-r3) the re-smoke plan tests. It is marked PROVISIONAL; only the lead session re-pins it once the final round of scripts exists | inputs/plan-wp6-resmoke-v5.md lines 2 and 3 |
| lead session | the Claude session that gives orders to the system-map session (me). Old pages say "the lead"; read that as lead session. It is not the studio lead | work/GLOSSARY.md lines 2 and 22 |
| studio lead | the Claude session that does the technical steps and is the only one that messages the owner | work/GLOSSARY.md line 23 |
| laptop lead | a label used on SWEEP.md and ONE-PLACE-TABLE.md for the one who gave the written work order. It matches "lead session", but no file says so; its meaning is not confirmed. In the chain table below it stands in the owner column of step 6 only; read it as "lead session, UNCONFIRMED" | work/GLOSSARY.md line 71 |
| owner | the human at the laptop | work/GLOSSARY.md line 2 |

### 0b. Sources (full paths; all under /home/user/hadavin-sdk/handover/system-map/)
| name used on this page | full path | purpose in one line |
|---|---|---|
| r1 | /home/user/hadavin-sdk/handover/system-map/work/critical-path-r1.md | the earlier critical-path page (marked SUPERSEDED by this one); source of the 2.5 h, 5 h, 1.5 h and 2 h step estimates and of the "now" of Mon 16 Nov 14:25 UTC |
| plan | /home/user/hadavin-sdk/handover/system-map/inputs/plan-wp6-resmoke-v5.md | the plan for the loopback re-smoke: steps, minutes, preconditions |
| owner-timeline-draft.md | /home/user/hadavin-sdk/handover/system-map/work/owner-timeline-draft.md | draft table of the messages the owner and studio lead exchange, with the stop time, notice and post times |
| open-items-table.md | /home/user/hadavin-sdk/handover/system-map/work/open-items-table.md | list of open questions with proposed answer-by times (A4, builder of fill_flows.py) |
| decision-list-for-lead.md | /home/user/hadavin-sdk/handover/system-map/work/decision-list-for-lead.md | recommended answers to drift rows D-01 to D-10 |
| GLOSSARY.md | /home/user/hadavin-sdk/handover/system-map/work/GLOSSARY.md | shared word meanings for the system-map pages |

### 0c. What the 14 h total contains, and how the margin is counted
- Inside the 14 h (section 2, chain table): step 4 (2 h 30 min), step 5 (5 h), step 6 (1 h 30 min), step 7 (2 h) and step 9 (3 h): 2:30 + 5:00 + 1:30 + 2:00 + 3:00 = 14:00. Step 8 (notice send) has no duration and adds nothing. Steps 1 to 3 have no stated duration and are NOT in the 14 h.
- Excluded: steps 10, 11 and 12 (owner setup, the take itself, take end). They come after the 14 h chain, which ends at the take start of 17:40 UTC. The owner setup is assumed to fit inside the 3 h wait of step 9 (section 4a, item 2).
- "7 d - 10 h 45 min" (section 3) is plain clock arithmetic: seven days after Mon 16 Nov 14:25 UTC is Mon 23 Nov 14:25 UTC; the latest start of step 4 is Mon 23 Nov 03:40 UTC, which is 10 h 45 min earlier (14:25 - 03:40). 7 d - 10 h 45 min = 6 d 13 h 15 min.
- The "now" of Mon 16 Nov 14:25 UTC / 19:55 IST is borrowed from r1 (r1 line 21, the last clock reading there). I took no clock reading myself.

### 0d. Recommendation (PROPOSAL; the lead session decides)
Of the three readings of the 3-hour notice in section 5, I propose the second: 3 hours before the owner's setup, with setup 30 minutes before the start (notice by 14:10 UTC / 19:40 IST with A13 = no; 10:10 UTC / 15:40 IST with A13 = yes). Reason: it is the stricter one, costs 30 minutes of the roughly 6 days of margin, and cannot leave the owner setting up the laptop inside the 3 hours. The 30-minute setup is r1's guess with no source, so the lead session or the owner should confirm it. The third reading (the draft's 14 min 20 s window) conflicts with the lead's 49-minute window and should not be used.

### 0e. UNVERIFIED against the v4.2 runbook
The v4.2 runbook IS in this checkout at /home/user/hadavin-sdk/handover/system-map/inputs/lead-reviews/LEAD-RUNBOOK-TAKE-DAY-v4.2.md; its section 3 "Schedule" starts at line 202. This page was built without reading it. Every time and duration on this page is therefore UNVERIFIED against v4.2. (While making this wording fix I saw only the first rows of section 3: they give a different schedule, with the re-pin done by Tue 17 Nov 08:00 UTC, a GO / NO-GO at Tue 17 Nov 14:00 UTC and a practice run on Wed 18 Nov. I did not read the section through or compare it with this page, so the conflict, if any, is not assessed.)


Times are UTC / IST (IST = UTC + 5:30). Every deadline below is a PROPOSAL unless a source file states it. "NOT STATED" means no input file gives the number. Nothing here was run; I read only the five input files named in the brief.

## 1. Fixed ends (what the lead ordered, and what the files say)
| item | value | source |
|---|---|---|
| Latest start of the take | about Mon 23 Nov 17:40 UTC / 23:10 IST | lead order in my brief (PROPOSAL; no input file states it) |
| Worst-case window | 49 min | lead order (no input file states it or says what is inside it) |
| Stop time (window end) | Mon 23 Nov 18:29 UTC / 23:59 IST | lead order; owner-timeline-draft.md:19 and :41 print the same stop time. Check: 17:40 + 0:49 = 18:29 |
| Post | Wed 25 Nov 15:00 UTC / 20:30 IST | owner-timeline-draft.md:43 (a "current rule" written by the system-map session: PROPOSAL, not a decision) |

Conflict to settle: owner-timeline-draft.md:41 gives a latest start of 18:14:40 UTC / 23:44:40 IST. That is a window of only 14 min 20 s (18:29:00 - 18:14:40). The lead's 49-minute window gives 17:40. The draft's start, notice (:42) and A13 times are all 34 min 40 s too late if the lead's window is right. I did not edit the draft (inputs are read-only for me).

## 2. Chain table, working backward (A13 = NO, no rerun; base case)
The "3-hour notice before the start" is anchored the way owner-timeline-draft.md:16 and :42 say (3 hours before the START). critical-path-r1.md:4 and :20 instead counted it back from the owner's setup, which it assumed starts 30 minutes before the take (ASSUMED, no source). The two readings differ by 30 minutes; the stricter reading is in section 5.

Arithmetic: each row's latest start = the next row's latest start - this row's duration. All on Mon 23 Nov except where marked.

| # | step | owner (role) | stated duration (source) | latest start UTC / IST | depends on |
|---|---|---|---|---|---|
| 12 | Take ends (stop time) | owner + laptop lead | window 49 min (lead order; what fills it NOT STATED) | end 18:29 / 23:59 | 11 |
| 11 | Take: rows 5-8 (the program runs; owner types `y` and the challenge; up to 3 model calls; film pause; `end`) | owner, studio lead | 49 min worst case (lead order). Inside it only one limit is written: row 7 pause alarm 10 min (owner-timeline-draft.md:40, PROPOSAL). The rest NOT STATED | 17:40 / 23:10 (17:40 + 0:49 = 18:29) | 10 |
| 10 | Owner setup (laptop plugged in, sleep Never, lid action Do nothing) and owner "yes" (row 4), studio lead numbers message (row 3) | owner, studio lead | NOT STATED. r1 assumed 30 min (r1:4, ASSUMED) | NOT STATED; must fit between 9 and 17:40 | 9 |
| 9 | 3-hour wait after the owner notice | owner (waits) | 3 h (owner-timeline-draft.md:16 and :42: "at least 3 hours") | 14:40 / 20:10 (17:40 - 3:00) | 8 |
| 8 | Owner notice sent (row 1) | studio lead | send time NOT STATED (a message) | send by 14:40 / 20:10; the cell text is still TBD (owner-timeline-draft.md:16) | 7 |
| 7 | Review of the rehearsal results (r1 row 2c: a person reads them) | person NOT NAMED (r1 condition 2) | 2 h (r1:20, an r1 estimate with no cited source) | 12:40 / 18:10 (14:40 - 2:00) | 6 |
| 6 | Rehearsal on the laptop with stand-in programs (r1 row 2b; decision 12: "first laptop rehearsal of the changed flows") | laptop lead | 1.5 h (r1:20, same limit); decision 12 gives no duration | 11:10 / 16:40 (12:40 - 1:30) | 5 |
| 5 | Loopback re-smoke (r1 row 2a = plan-wp6-resmoke-v5 = open-items "run (a)") | studio lead | Plan: 171 min = 2 h 51 min clean, "a floor, not a quote" (plan:5, :443); quote 3.5 to 4.5 h realistic (plan:5, :22, :445). r1 used 5 h (r1:20). Base uses 5 h | 06:10 / 11:40 (11:10 - 5:00) | 4 |
| 4 | Build fill_flows copy and import the flows into n8n (r1 row 1) | builder NOT NAMED | 2.5 h (r1:20, an r1 estimate). open-items-table.md:28 says fill_flows.py is "not built"; the plan (:4, :223) says it read `fill_flows.py` in the glue folder. I could not check the disk | 03:40 / 09:10 (06:10 - 2:30) | 1, 2, 3 |
| 3 | Decision A4 (does run (a) start) answered yes | studio lead | answer UNKNOWN; due Mon 16 Nov 13:00 / 18:30 and already passed (open-items-table.md:34) | NOT STATED; before step 5 | none |
| 2 | scripts/n8n_api.py supplied; core-hardening edits finished | lead session / core-hardening | NOT STATED (r1:7-12 conditions 4 and 6) | NOT STATED; before step 4 and step 5 | none |
| 1 | A builder named for step 4 | studio head, else the owner | NOT STATED. Proposed: if unnamed by Mon 16 Nov 18:00 / 23:30 the owner is asked and answers by Tue 17 Nov 01:30 / 07:00 (open-items-table.md:14, PROPOSAL) | Tue 17 Nov 03:30 / 09:00 (open-items-table.md:28, PROPOSAL) | none |

Backward totals: from the latest start of step 4 (Mon 23 Nov 03:40 / 09:10) to the take start (17:40 / 23:10) is 14 h (2:30 + 5:00 + 1:30 + 2:00 + 3:00 = 14:00). Check: 03:40 + 14:00 = 17:40.

### Same chain with A13 = YES (4-hour rerun margin kept, one rerun fits)
Rule used: owner-timeline-draft.md:42 shows A13 = yes moves the last start 4 h earlier (18:14:40 to 14:14:40) and the notice 4 h earlier (15:14:40 to 11:14:40). I apply the same 4 h to the lead's 17:40.
| step | latest start UTC / IST |
|---|---|
| Take (first run) start | 13:40 / 19:10 (17:40 - 4:00) |
| Owner notice sent | 10:40 / 16:10 (13:40 - 3:00) |
| Review of rehearsal results | 08:40 / 14:10 |
| Rehearsal | 07:10 / 12:40 |
| Loopback re-smoke | 02:10 / 07:40 |
| Build and import | Sun 22 Nov 23:40 / Mon 23 Nov 05:10 |
| Rerun (a second run, if the first fails) | last start 17:40 / 23:10; must end by 18:29 / 23:59 |

## 3. Margin
Margin here = calendar time between the earliest the chain can start and the latest start in section 2. Last known state: row 1 had not started at Mon 16 Nov 14:25 UTC (r1:21). I use that as "now" because I have no later clock reading.

| case | latest start of step 4 (build and import) | margin from Mon 16 Nov 14:25 |
|---|---|---|
| A13 = no, no rerun | Mon 23 Nov 03:40 | 6 d 13 h 15 min (7 d - 10 h 45 min) |
| A13 = yes, one rerun of 4 h (the A13 value) | Sun 22 Nov 23:40 | 6 d 9 h 15 min (4 h less) |
| One rerun that needs a fresh 3 h notice too (7 h; whether a rerun needs a new notice is NOT STATED; row 11 of owner-timeline-draft.md:26 only says "new run name and new yes") | Sun 22 Nov 20:40 | 6 d 6 h 15 min |
| Re-smoke at its realistic top plus every "only if hit" extra (see 4b) | 03:17 on Mon 23 Nov (23 min earlier than base) | 6 d 12 h 52 min |

Reading it honestly: the arithmetic margin is large (about 6 days) but it is not usable until the blockers in rows 1 to 3 of the chain table are cleared. None of r1's six conditions is confirmed (r1:6-12). Each hour of an unstated step placed before the notice moves every earlier latest start one hour earlier and cuts the margin by one hour.

Rerun fit (does a second run physically fit in the window): the first take can end at 18:29 at worst, so a rerun can only fit if the first one starts at or before 17:40 - R, where R = first run (up to 49 min) + clean-up of the failed run (row 11: delete demo mails, empty Trash, new run name and new yes; time NOT STATED) + the rerun's own 49 min. R is not stated anywhere. A13's 4 hours is a placeholder proposal, not a measurement. With A13 = no, there is no rerun: any failed take inside the window ends the plan for 23 Nov (a later date is a separate decision).

## 4. Steps whose duration is stated nowhere, and the effect
a) NOT STATED at all:
1. What fills the 49-minute take (owner typing, up to 3 model calls, film pause length, `end`, film check). Effect: the 49 min is the lead's number; if the real worst case is longer, 17:40 moves earlier by the same amount and every row in section 2 moves with it.
2. Owner setup before the take (30 min is only r1's guess). Effect: it fits inside the 3 h notice wait; only if the owner needs more than 3 h after reading the notice does it add time.
3. Studio lead numbers message (row 3) and owner "yes" (row 4): lead times before the start. Effect: they sit between the notice wait and 17:40 and are unmeasured; they eat the last minutes of the wait.
4. Result review of the re-smoke evidence by `egm:*` reviewers, `egm:egm-resolve`, ledger rows and `egm:egm-drift-report` (plan section 10, :505). Effect: not in r1's chain at all; it sits between step 5 and step 6. Every hour here moves steps 4 and 5 one hour earlier.
5. Fixing a STOP or a GO finding and re-running the re-smoke. The plan prices single items (glue fix +15 min, crash D +15, B2 re-run +8, E2 +8 to 12, MODS attempt 2 +10, option (a) about 1 h; plan:445 and :506) but not a full re-run. Effect: one full re-run would add the 3.5 to 4.5 h quote again (my reading, not stated) and moves step 4 about 4 h earlier.
6. Round-5 script build and the lead's re-pin (plan:2, :3). Effect: HEAD_PIN is provisional (plan:2); step 5 cannot start until the final head exists. Duration and owner NOT STATED.
7. Docker Desktop started by the lead before the run (P-4, plan:240). Effect: small, not in the 171-minute total.
8. fill_flows.py build time and builder (r1's 2.5 h is r1's own estimate; no builder named). Effect: if it takes longer, step 4's latest start moves earlier one-for-one.
9. n8n_api.py supply and core-hardening finish (r1 conditions 4 and 6). Effect: gates steps 4 and 5; duration NOT STATED.
10. Rehearsal (1.5 h) and rehearsal review (2 h): stated only in r1, an earlier draft of mine with no cited source. Effect: 3.5 h of the 14 h chain rests on that.
11. Clock-time questions that Tue 17 Nov answers: items 1a, 1b, 2, 3, 4, 4b, 5 (open-items-table.md:28-34); all dates there are PROPOSAL.
12. Everything after the take (see section 6).

b) Plan inconsistency to fix: plan:228 says the preconditions (P-3a to P-5) are "outside the clock", but plan:428-441 counts their 24 minutes inside the 151 step minutes. I re-added the table (24+6+10+9+7+12+6+10+9+5+31+11+11 = 151; +20 write-up = 171) and the sum matches, so the 171 minutes includes them. The "only if hit" extras: 10 + 15 + 8 + 12 + 6 + 2 = 53 min; 4 h 30 min + 53 min = 5 h 23 min, above r1's 5 h. That is the last margin row above.

c) The plan's own run window: the loopback re-smoke is bounded by the plan's sampler and keep-alive, which end after 8 h (plan:123, :241). No step of the chain should take longer than that.

## 5. Variants of the anchor (so the lead can choose)
| reading of the 3-hour notice | notice must be sent by (A13 = no) | notice by (A13 = yes) |
|---|---|---|
| 3 h before the START (owner-timeline-draft.md:16, :42; base) | 14:40 / 20:10 | 10:40 / 16:10 |
| 3 h before the owner's SETUP, with setup 30 min before the start (r1:4; setup time is ASSUMED) | 14:10 / 19:40 | 10:10 / 15:40 |
| The draft's own numbers (window 14 min 20 s; owner-timeline-draft.md:41, :42) | 15:14:40 / 20:44:40 | 11:14:40 / 16:44:40 |

## 6. After the take (for completeness; no durations are stated)
Span from the worst-case end to the post: Mon 23 Nov 18:29 to Wed 25 Nov 15:00 = 44 h 31 min (48 h - 3 h 29 min). Steps in that span from owner-timeline-draft.md:26-35, in table order (the file does not say which must finish before the post):
- video edit: owner and duration NOT STATED
- owner watches the edited video twice, says "accepted" (row 12): NOT STATED
- clean-up rows 13 to 19 (leftover contacts, delete HubSpot apps, retire check, n8n removal, secret files, revoke the model key): each NOT STATED; the card OWNER-CLEANUP-CARD.md is not among my inputs and I did not read it
- failed-run repeat steps (rows 10 and 11: delete leftover contacts, demo mails): NOT STATED
- post wording (row 20 "[studio lead fills]") and second-person check: owner of the check NOT NAMED, duration NOT STATED

Backward arithmetic is impossible past 15:00 on Wed 25 Nov because no duration is stated; the only number is the 44 h 31 min span. If the rerun is used, the rerun's last end is still 18:29 on Mon 23 Nov, so the span is the same.

## 7. What I did not check
- In the first draft I opened only the five input files. For the wording fix (section 0) I also read parts of work/GLOSSARY.md, work/decision-list-for-lead.md, work/open-items-table.md, work/owner-timeline-draft.md and the first rows of section 3 of the v4.2 runbook. I did not look for fill_flows.py, scripts/n8n_api.py, OWNER-CLEANUP-CARD.md, decision-list-for-lead.md or TAKE-BLOCKERS.md on disk.
- I do not know the current time or whether A4, the builder, or any condition has changed since Mon 16 Nov 14:25 UTC.
- The role names in the "owner" column ("laptop lead", "lead session") are my mapping of the roles named in the brief to the steps; the inputs use only "studio lead", "studio head", "owner", "core-hardening" (r1:15 defines them).
- No number was measured; the 14 h chain rests on r1's own estimates (r1:20), the plan's estimates (plan:5, :443, :445) and the lead's order.
