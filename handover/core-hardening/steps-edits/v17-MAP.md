# v17 map: every v16 section, appendix, open item and review finding, and where it lives now

Written Mon 16 Nov 2026. Abbreviations: **Sheet** = OWNER-SHEET-v17.md (section number or rule id R1 to R10); **Note** = LEAD-RELEASE-NOTE-v1.md (G1 to G24 are its go/no-go rows, "Note §n" its sections); **Open** = v17-OPEN-FOR-LEAD.md (item number). DROPPED = not carried, with the reason. Finding ids are those of the v16 review files (review-v16-security.md, -stranger.md, -adversarial.md, -contradiction.md, citation-check-v16.md). Nothing here was run.

## 0. Failures first: controls or findings that are DROPPED or weakened, and the risk
| Item | What changed | Risk, honestly | Next step |
|---|---|---|---|
| Owner's account check A.5 (sign in to each Gmail, read the second fact, read HubSpot's account and private-app page) | reduced to: the account name each page shows equals the message (Sheet §3 item 6) plus the notice compare (R5); the lead states the rest (Note G23) | the owner no longer reads the HubSpot private-app permission names; a wrong account would be caught only by the name check and the masked accounts in the notice | lead: Open 6, G21 |
| Step 0 and the probe key (security M-E, adversarial B3, M2, M3, stranger M7, M14) | removed by decision 8 | the live HubSpot write path is covered only by the loopback re-smoke and one made-up contact in take prep (decision 8) | lead: Open 5 |
| Owner's flow-file and file checksum checks (E.0 tick, adversarial B1) | moved to the lead (Note G1, G2) | the owner cannot detect a changed file; the lead's statement is the only evidence | lead: G1, G2 |
| Second-fact checks of the Gmail accounts (OI-26) | DROPPED | one fewer check that the right account is open | the name check above |
| Older-key decisions (A.0b) | DROPPED; R2 and R4 give one rule instead | a kept older key is neither cancelled nor listed by the sheet; R4 says any other valid key means no run | Open 9 |
| Window-end enforcement | stated plainly as the owner's cancel plus the model program's setting, UNVERIFIED (R4) | the setting is unproven (Open 11) | lead |
| Whole v16 card (57 underscore lines), appendices 1 to 18 as owner text | replaced by the lead's message (Note §3) | the lead must fill about 45 values correctly; a wrong value reaches the owner only as a mismatch with the notice or the model settings file | lead |

## 1. v16 sections, parts and appendices
| v16 place | Lives now | Note |
|---|---|---|
| Title, dates, "ONE sheet", markers (S1-7) | Sheet title and §1 | one marker only: UNVERIFIED (stranger nit n1) |
| DO THIS FIRST 1 (value list, card complete, row 22) | Note §3, G23; Sheet §3 item 1 | card dropped |
| DO THIS FIRST 2 (run name, proof-screen number) | Sheet §3 item 2; Note G11 | owner no longer chooses a proof screen |
| DO THIS FIRST 3 (exit codes) | Note G6; Sheet R10 | |
| DO THIS FIRST 4 (key deadline) | Sheet R3; Note §2, G10 | |
| DO THIS FIRST 5 (unsure: Freeze) | Sheet R10 | |
| Words (S17-28) | Sheet §1 (shorter; 10 terms) and checker | terms that only served the lead moved to Note |
| Stop word 1 Key exposed | Sheet R1 (second column) | |
| Stop word 2 Emergency cancel | Sheet R4 (last column), R2 | |
| Stop word 3 Time | Sheet R3 | |
| Stop word 4 Freeze | Sheet R10 | |
| Stop word 5 Stop | DROPPED as a word (one wait word) | bare "stop" is banned by the checker |
| Precedence | Sheet R10 | |
| What typed answers gate | Sheet R4 (honest sentence) | |
| Part 1 order line | Sheet section order | linear sheet |
| Go list 1 (card complete, humans) | Note G11, G23 | |
| Go list 2 (rehearsal file) | Note G15 | |
| Go list 3 (step 0 answered) | DROPPED (decision 8) | |
| Go list 4 (three n8n values) | Note G3 | |
| Go list 5 (hard stop statement a to c) | Note G1, G2, G21 | |
| Go list 6 (model program restarted) | Note G16; Sheet §5 item 5 | |
| Go list 7 (exit-code rule) | Note G6 | |
| Go list 8 (yes, accounts check, veto) | Sheet §4 item 4, R4; veto DROPPED (the owner may always refuse to type the yes) | |
| Go list 9 (clean start) | Note G19 | |
| Money rule plain words, items 1 to 6 | Sheet R4 and §4 (owner part); Note §2 and G4, G5, G14 (lead part) | |
| Rules 1 to 15 | R1 (rules 1, 5), R6 (2, 11), R8 (14), R9 (9, 10), R10 (7, 8, 12), R2 and R3 (13); rule 3 (written yes) §4; rule 4 (post) §8; rule 6 (laptop) §3; rule 15 (UTC compare) §5 item 5 | |
| Step 0 header and 0.1 to 0.6 | DROPPED | decisions 8 and 2; Sheet §1 one line |
| A.0 exposure, key | Sheet R1, §5 | |
| A.0b model program, old keys | model program part: Sheet §5 item 5, Note G16; old keys DROPPED | |
| A.1 settings | Sheet §4 item 2 | |
| A.2 price | Sheet §4 item 3 | |
| A.3 money | Sheet §4 item 1; Note G4, G14 | |
| A.4 rehearsal first line | Note G15 | |
| A.5 accounts check | reduced, see §0 | |
| A.6 the yes | Sheet §4 item 4 | |
| Trial run (row 10) | Note §9 | |
| I.0 cancel key | Sheet R2, R3, §6 item 7, §7 item 1 | |
| H watch video | Sheet §7 item 4 | |
| Warning before I | Sheet R7 ("unclear: remove nothing") | |
| I.1 app passwords, demo mails | Sheet R7, §3 item 5, §7 item 3 | |
| I.2 HubSpot private apps | Note §8, Open 6 | |
| I.3 screenshots | DROPPED (row 18 default; not needed) | |
| I.4 retire check | Note §8 | |
| I.5 n8n and database | Note §4 | |
| I.6 erase secret files | Note §4 step 11, §9 | |
| I.7 laptop back | Sheet §7 item 5 | |
| J post | Sheet §8; Note §5 | |
| Part 2 header, "complete card" | DROPPED | |
| Value table (card lines, 57) | Note §3 template | |
| "Not underlined" notice wording | Note G17 | |
| B laptop | Sheet §3 item 4 | |
| C.1 receiver | Sheet §3 item 5 | |
| C.2 film profile | Sheet §3 item 6 | |
| D what the film may show | Sheet §3 item 6, §7 item 4; Note §5 | person C line decided by the lead (cut) |
| Recording, editing, posting roles | Sheet R9; Note §7, G11, G24 | |
| E.0 ticks | Sheet §6 item 1 | lead-side ticks moved to Note |
| E start | Sheet §6 items 2 and 3, R5, R6 | |
| While it runs | Sheet §6 item 4 | |
| F.1 film pause | Sheet §6 item 5 | |
| F.2 `end` | Sheet R6, §6 item 5 | |
| F.3 recording off, exit code | Sheet §6 item 6 | |
| F.4 finish reading, cancel key | Sheet §6 item 7 | |
| F.5 contacts | Sheet R7, §7 item 2; Note §6, G13 | |
| Stop rules | Sheet R4, R10 | |
| After | Sheet §7 | |
| Appendix 1 more words, worked example, calculator | Sheet §4 item 3; Note §2 | |
| Appendix 2 value list (23 rows) | Note §3, G-list | rows 8 and 9 "not used" gone |
| Appendix 3 messages, flow checksum form | Note §3, G2 | |
| Appendix 4 rule 10 | Sheet R9 | |
| Appendix 5 counts, sample notice, sample result | Sheet §6 item 6; Note G17 | invented samples DROPPED; the lead copies the real wording |
| Appendix 6 order table | Note §4 | |
| Appendix 7 post ban, lease candidate | Note §5 | |
| Appendix 8 delete method | Sheet R7; Note §6 | by contact id |
| Appendix 9 refusals, lock file | Note §9 | |
| Appendix 10 n8n stop and start | Note G8 | |
| Appendix 11 trial run | Note §9 | |
| Appendix 12 failed run, demo mails | Note §9; Sheet §3 item 5 | |
| Appendix 13 retire check | Note §8 | |
| Appendix 14 film rules, shot list | Note §5; Sheet §3 item 6, §7 item 4 | |
| Appendix 15 saving the model key | Sheet R1, §5 | |
| Appendix 16 screenshots, erase tests | erase tests Note §9; screenshots DROPPED | |
| Appendix 17 secrets table | Note §8 | |
| Appendix 18 open items, not proven | Note §0, §9 and Open | |

## 2. Open items OI-1 to OI-38
| OI | Lives now | OI | Lives now |
|---|---|---|---|
| OI-1 | G3 | OI-20 | DROPPED (probe key) |
| OI-2 | G6, Open 2 | OI-21 | Note §2 (clock tolerance); owner part DROPPED |
| OI-3 | G19 | OI-22 | G5, Note §2 |
| OI-4 | G14 | OI-23 | G11, Note §7 |
| OI-5 | Open 5 | OI-24 | G14 |
| OI-6 | G14, Open 12 | OI-25 | G4, G14 |
| OI-7 | G21 | OI-26 | DROPPED (second fact) |
| OI-8 | Note §9 (flow copy erased by the lead) | OI-27 | Note §4 step 9 |
| OI-9 | G17 | OI-28 | DROPPED (step 0) |
| OI-10 | G4 | OI-29 | G15 |
| OI-11 | G18, Open 16 | OI-30 | G24 |
| OI-12 | G1, G2 | OI-31 | G24 |
| OI-13 | G12, Open 1 | OI-32 | G24 |
| OI-14 | G3 | OI-33 | G24 |
| OI-15 | G21 | OI-34 | Note §5 (shot list), G24 |
| OI-16 | Note §2 | OI-35 | DROPPED (step 0) |
| OI-17 | Note §8 | OI-36 | G24 |
| OI-18 | Note §2 | OI-37 | G22, Open 6 |
| OI-19 | Note §2 | OI-38 | Note §8, Open 18 |

## 3. Security review (M-A to M-H, v15 carry-over, nits)
| Id | Lives now |
|---|---|
| M-A | Sheet R2 (one cancel rule); the two other cancel wordings are gone |
| M-B | DROPPED: the TOKEN setting-name rule no longer exists; R9 limits only typed values; Sheet §4 item 2 names settings from the message |
| M-C | Sheet R3 (alarm, cancel after abort), R4 (enforcement stated plainly, UNVERIFIED); Note G10, G16; Open 11 |
| M-D | DROPPED with A.0b; R2 and R4 (any other valid key: no run); Open 9 |
| M-E | DROPPED (step 0, decision 8); Open 5 |
| M-F | Sheet §8; Note §5, G12; Open 1 |
| M-G | Sheet shrunk to decision 7 roles; Note G22; Open 6 |
| M-H | Note G21, Open 4 (no read-only claim by default); `end` on written word: Sheet R6 (permission is part of the rule, not an override) |
| v15 M1 (flow checksum) | Note G2 |
| v15 M2 (probe app name) | DROPPED (step 0) |
| v15 M3 (key choices) | R2, R3 |
| v15 M4 (N8N_ENCRYPTION_KEY, n8n.env end) | Note §8 |
| v15 M5 (ceiling informational) | Note G4 |
| v15 M6 (Emergency cancel exception) | R4, R2 |
| v15 M7 (gate only) | R4 |
| n1 (F.4 lists as key-ending but reads) | R3 and §6 item 7 (cancel is its own step) |
| n2 (`set -C` refusal leaves key on clipboard) | Sheet §5 item 3 |
| n3 (command line must hold only key path) | Note G16 |
| n4 (A.0b decisions have no send step) | DROPPED with A.0b |
| n5 (no tick forces I.0 before H) | Sheet §6 item 7 then §7 order |
| n6 (second key, same run name) | R2 (name and creation time), §3 item 2, §5 item 3 |
| n7 (appendix 4 exception easy to miss) | R9 (inside the rule) |
| n8 (US$180 against 189) | Open 7, G14 |
| n9 (who can reach the n8n port) | Note G7 |
| Holds (leak paths, honest disclosure, narrow claims, arithmetic) | R1, R4, §8, Note §2 |

## 4. Stranger read (M1 to M15, nits, not-understood)
| Id | Lives now |
|---|---|
| M1 blanks without a card line | Note §3 (every blank has a named filler), Open 17 |
| M2 who fills proposals | Open (all items are proposals with defaults) |
| M3 how many people | Note G11, §7 |
| M4 two meanings of recording period | R9 (one definition) |
| M5 DO THIS FIRST uses undefined terms | DROPPED; Sheet §1 words first |
| M6 "second fact of OI-26" | DROPPED |
| M7 probe key | DROPPED (step 0) |
| M8 money rule dense | R4 and §4 |
| M9 card not stand-alone | DROPPED card; linear sheet |
| M10 mismatch with no action | R10, §4 item 2 |
| M11 "program", "settings file" two meanings | §1 words (take and model forms); checker |
| M12 "the writer", "old desk program", "the v15 candidate" | DROPPED |
| M13 first real step late in the file | Sheet §3 is the first action |
| M14 "row 19 (3)" | DROPPED |
| M15 zero search results | R7 |
| n1 four marker types | §1 (one) |
| n2 8x8 checksum by eye | DROPPED (G1, G2) |
| n3 letters reused | numbered sections and R ids only |
| n4 "lead" two meanings | §1 (one meaning); claim wording says made-up sales contact |
| n5 no "tell the lead" | R9 |
| n6 "(UTC = IST)" labels | every time written in UTC and IST |
| n7 "New in v16", loopback jargon | DROPPED; Note §9 plain words |
| n8 Time says cancel even if no key | R3 ("if you made one") |
| n9 Chrome assumed | §3 item 6 names Chrome only for the film profile; other browsers: ask (Open 17) |
| n10 who judges the ban list | Note §7 (post checker) |
| U1 where OI-33 is | G24 |
| U2 UNVERIFIED then Freeze | §1, R10 |
| U3 ledger and backstop | R4, Note §2 |
| U4 lease sentence in an owner document | DROPPED from the sheet; Note §5 |
| U5 trial, step G, failed run, run name marker | Note §9; Sheet §6 item 3 |
| U6 wrong `end`, film pause end | R6, G18 |
| U7 why the second reading waits | §7 item 1, Note §2 |

## 5. Adversarial review (B1 to B3, M1 to M11, nits, scenarios)
| Id | Lives now |
|---|---|
| B1 flow checksum | Note G2 (the owner is not asked) |
| B2 A.0b against I.0 | R2 |
| B3 0.6 erases first | DROPPED (step 0) |
| M1 owner role | G22; sheet shrunk |
| M2 step 0 default | §1, Open 5 |
| M3 probe app and key | DROPPED |
| M4 card incomplete when sent | DROPPED card; Note §3 |
| M5 old-key criterion, who sets balance | DROPPED; G14 |
| M6 informational ceiling | Note G4 |
| M7 stop-word order, Key exposed against Freeze | R10 order; R1 (close that window, not the take program window); R2 always allowed |
| M8 F.5 missing from checklist | Sheet §7 item 2; Note G13 |
| M9 lease sentence order | Note §5 |
| M10 candidate reads as a promise | Note §5 (candidate shortened to the honest two sentences) |
| M11 film cannot show person A's mail | Sheet §8, Note §5 (printed result must say it; else no post) |
| n1 stamp line multi-value | Note §3 (two lines) |
| n2 lowercase "stop" | checker |
| n3 418 lines | Sheet is 70 lines |
| n4 DECISION-one-store line 14 | G20, Open 10 |
| n5 ban list ok | Note §5 (kept) |
| SC1 step 0 skipped | decision 8; G15 |
| SC2 step A late | Note §2 (latest start includes step A time and lag wait) |
| SC3 wrong numbers typed in the yes | Sheet §4 items 2 and 3; Note §3 (lead compares the yes before "go") |
| SC4 wrong `end` word | R6, G18 |
| SC5 lost key | R2 (name and creation time), §5 item 3 |
| SC6 take late past window end | R3, Note G10 |
| SC7 leftover contact | R7, G13 |
| Audit of v16-CHANGES "FIXED" marks | process: v17-check-output.txt and this map replace the CHANGES file; no mark is made without a text position |

## 6. Contradiction re-read (1 to 17)
| Id | Lives now |
|---|---|
| 1 A.0b against I.0 | R2 |
| 2 rows 4, 5, 7 against 4 to 7 | R9 (film, "recording", "filmed"; editor and post checker never) |
| 3 step 0 contact against F.5 | DROPPED (step 0); Note §6 (three addresses at most) |
| 4 step 0 against decisions | §1 |
| 5 A.0 key against FACTS | Open 9 |
| 6 shutdown timing | Note §4 (stated once) |
| 7 key deadline not tied to run date | Note §2, G10 |
| 8 `none` exit-code rule | G6, Open 2 |
| 9 Freeze lists browser steps | R10 (R2, R3, R7) |
| 10 rule 10 charset against `@` `:` `?` | R9 (typed values only; printed lines exempt) |
| 11 "database" definition | DROPPED word; G19, G20 |
| 12 post time value against fixed 15:00 | Sheet §8 (fixed 15:00 UTC = 20:30 IST) |
| 13 recording period E.0 to F.3 | R9 (Recording ON to Recording OFF) |
| 14 stale text | DROPPED |
| 15 "earlier one counts" | Note §2 (key deadline never after window end, same date) |
| 16 appendix 3 older keys; OI-25 timing | DROPPED; G4 (answered before the key is made) |
| 17 appendix 5 against step J on person A | Sheet §8, Note §5, G15 |

## 7. Citation check (items 1 to 10)
| Id | Lives now |
|---|---|
| 1, 2 byte sizes in CHANGES | DROPPED (v16 notes not carried) |
| 3 stale check output | check-v17.py reruns write v17-check-output.txt |
| 4 eight against nine open items | DROPPED (OI numbering retired; table §2) |
| 5 "film nothing" pointer | Sheet §3 item 6 |
| 6 "D (Part 2 first section)" | DROPPED |
| 7 B20 against OI-35 numbering | DROPPED |
| 8 CI id literalness | DROPPED |
| 9 card lines one value each | Note §3 (one value per line; checked by eye, not by script) |
| 10 plan-v10 path | Note §5 (`paste-check/plan-v10-real-v5-edits.md` lines 456 to 459) |
