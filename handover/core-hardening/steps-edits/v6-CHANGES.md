# v6 changes: one row per review item (review-c4b-v5-naive.md, review-c4b-v5-design.md) plus the lead's orders

Status: FIXED = fixed in OWNER-STEPS-realrun-v6.md; OPEN = needs the studio lead (row in v6-OPEN-FOR-LEAD.md, "L" number). Nothing was run. Honest limits: I could not read the memory files that FACTS names (no memory folder here), so every memory check below rests on the inputs only. The probe facts in step 0 come from a copy of `hubspot_probe.py` in an evidence folder, not from `inputs/`.

## Naive reader (N1-N10 are the numbered items; Ns are the "Smaller" list in order)
| Item | Status | Where / why |
|---|---|---|
| N1 open items hidden in a file | FIXED, parts OPEN L7, L8, L12, L2 | run card (12 rows with defaults); table has "open" rows; run name rule explained |
| N2 lead has no screen access yet gets laptop actions | FIXED, part OPEN L8 | Words box "studio lead" (runs its own commands, never types in your terminal); table "who" column; I.5 says the lead removes things |
| N3 wrong cross-reference "step 6" | FIXED | step I.4 now says "item 5" |
| N4 Delete vs recoverable copy | FIXED, OPEN L11 | Words box "Delete" says what is and is not known; step 0 shows permanent vs archived |
| N5 two settings files, backstop undefined | FIXED | Words box: run settings file, model settings file (`stage.env`), spending backstop |
| N6 n8n password place, duration, finish sign, stuck rule | FIXED, OPEN L26 | C.3 (keep where you keep your own passwords), step E "How long it takes", run card rows 3, 12 |
| N7 undefined terms | FIXED | Words box adds proof screen, crash-safe, independent count, saved runs, run program, hook door, contact, lead id, label `demo`, settings files, company address |
| N8 step F mistype consequences | FIXED | boxed warning and step F |
| N9 crop tool, 2-Step, Gmail select, HubSpot filter | FIXED, OPEN L27 | I.1 (Snipping Tool, 2-Step already on), G.1 (subject filter, Trash check), F (search run name) |
| N10 move "not proven yet" | FIXED | shortened to a short box; full list stays with the lead |
| Ns "lead wins" weakens sheet | FIXED | intro paragraph (see design M1) |
| Ns done items have no owner check | FIXED | step 0 (HubSpot delete), C.1 (label), rule 5 sentence; intro says to tell the lead if a done item is missing |
| Ns order of B, C, D vs A, days ahead | FIXED, OPEN L4 | Order of the day; run card row 1 |
| Ns fast-typing exit code | FIXED | step E and exit-code list (exit 2; v3 line 172) |
| Ns login failure exit code | FIXED | step E item 1 (exit 2: probe, v3 line 172) |
| Ns lock per name unclear | FIXED | Words box "Run lock file"; refusals list |
| Ns I.1 revoke has no confirmed list | FIXED, OPEN L23 | step I.1 |
| Ns "company address" undefined | FIXED | Words box |
| Ns "archive" on screen vs delete | FIXED | Words box "Delete": if a screen says something else, stop |
| Ns final words not available, checker open | FIXED, OPEN L16, L18 | step J, run card row 11 |
| Ns I.2 key question hard to answer | OPEN L22 | step I.2 says: if you cannot tell, delete nothing; no mapping exists |
| Ns `retire`, "real company mailbox" not checkable | FIXED | retire check defined; rule 5 gives a sentence to send before step E |

## Design review (M = Major, D-N = Nit)
| Item | Status | Where / why |
|---|---|---|
| M1 lead messages override safety rules | FIXED | intro paragraph: only values, lists, counts; never rules 1-7, boxed warnings, marker rule |
| M2 C.3 unsupported premise; connection list unreconciled | FIXED, OPEN L10 | C.3 conditional; says list not reconciled; no new login; FACTS cited |
| M3 "exactly 3 contacts and 3 mails" | FIXED | Words box "Send counts": A and B one each; C one or unknown with alert; step E notice line says "up to 3" consistently |
| M4 example.com claim | FIXED, OPEN L3 | Words box "Test person" |
| M5 click paths only blanket-tagged | FIXED | "(path not checked)" in B, C, F, G, I and Words box |
| M6 spend claims too strong | FIXED | cost section and step J wording; matches scope sheet |
| D-N1 run name timing | FIXED, OPEN L2 | Words box "Run name" |
| D-N2 n8n conditional vs proof screen | FIXED | C.3 and D.4: n8n filmed only if the lead asks for the sign-in |
| D-N3 latest start | FIXED, OPEN L4 | 18:14:40 UTC = 23:44:40 IST at default lease; lead gives exact |
| D-N4 cross-reference | FIXED | same as N3 |
| D-N5 stage.env "in the run folder" | FIXED, OPEN L6 | "the studio lead gives its path" |
| D-N6 Empty Trash | FIXED | G.1: Trash must hold only these mails |
| D-N7 rehearsal gate in no input | FIXED, OPEN L20 | marked as the lead's own gate in step A and table |
| D-N8 one-database wording, bookkeeping files | FIXED | step J must-not-say, "not proven" box lists lock files and `n8n.pid` (DECISION-one-store) |
| Gap: retire check 2 of 4 secrets | FIXED, OPEN L21 | Words box and I.5 |
| Gap: TAKE_MIN_ANSWER_SECONDS | FIXED | step E (2 s default, 1-60) |
| Gap: exit 3 residuals, status 120 | FIXED | exit-code list "Rare" |
| Gap: v3-only steps memory check | FIXED (see below), OPEN L28 | tags in sheet |
| Gap: n8n stop "lead's session" stated as fact | FIXED, OPEN L8 | now "open; planned: the studio lead" |

## Orders added in this round
| Item | Status | Where |
|---|---|---|
| ORDER 017 HubSpot probe, 7 calls, US$0, token in `HUBSPOT_PROBE_TOKEN`, paste table, answers the delete question | FIXED, OPEN L19 | step 0 (key read from a named secret file so it is never typed or shown; "what a pass looks like for this run" is the lead's; the script's own rule is exit 0 only if every line is PASS or SKIPPED) |
| FACTS: owner creates no account/mailbox/key/HubSpot account, no Docker | FIXED, checked | no step asks for these; removed from v5: C.3 "create an owner login" and "choose a new n8n password"; C.1 no longer says "you made the label" as fact; C.2 creates a Chrome profile (not an account), tagged for lead confirmation |
| ORDER 019 table with person per row | FIXED, OPEN L8, L7 | "Table of every owner step"; "open" in who column for n8n stop and restart and filming |
| Date conflict | FIXED, OPEN L4 | ORDERS 017 aims at Wed 18 Nov with latest Wed 25 Nov 20:30 IST; sheet states both |

## Memory check (FACTS rule) for steps that come only from v3
Supported means named in FACTS or in the scope sheet / plan. None of the memory files were readable here, so "UNVERIFIED" means: kept in the sheet, tagged for the lead to confirm.
| Item | Source | Kept? | Support in inputs |
|---|---|---|---|
| C.1 receiver label and Inbox empty | v3 steps 4, 16, 17 | kept as a check (nothing is created) | scope sheet section 3: the program reads only label `demo`; FACTS lists "settings done" but not the label: label existence UNVERIFIED (L9) |
| C.2 browser profile `demo-take` | v3 step 19 | kept, tagged UNVERIFIED | not in FACTS (L24) |
| D what the film may show | v3 step 19 | kept, tagged UNVERIFIED | FACTS lists watching the video as owner-only, not this check; the crop list is from v3 only |
| G failed-run clean-up | v3 step 20 | kept, tagged UNVERIFIED | not in FACTS; the plan refers to it only through the claim rules (L25) |
| I.2 delete HubSpot private apps | v3 step 22.3 | kept as "only after the lead confirms", UNVERIFIED | FACTS lists only the app-password revoke (L22) |
| I.3 screenshots to the Windows folder | v3 step 22.4 | kept | FACTS lists the revoke clean-up; folder name from v3 only |
| I.4 retire check | v3 step 22.5 | kept | supported: scope sheet section 3 (`--retire-check`, 2 of 4 secrets) |
| I.5 lead removes n8n, run folder, container | v3 step 22.1 | kept as lead's | plan section 4 S13 and 13.6 (rehearsal clean-up); real-run method undecided (plan section 9) |
| I.6 delete secret files, keep marker | v3 step 22.6 | kept | FACTS says keys were saved in files by the owner; `shred` unverified (L13) |
| I.7 settings back, sign out | v3 step 22 end | kept | FACTS lists the take-day laptop settings as owner-only; sign-out UNVERIFIED |
