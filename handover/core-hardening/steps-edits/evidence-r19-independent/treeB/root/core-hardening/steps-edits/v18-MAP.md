# v18 map: every finding of the v17 reviews and where it is fixed in v18

Written Mon 16 Nov 2026. **Sheet** = OWNER-SHEET-v18.md (section number, rule id R1 to R10); **Note** = LEAD-RELEASE-NOTE-v2.md (G1 to G29 are its gates, "Note n" its section); **Open** = v18-OPEN-FOR-LEAD.md (item number). Finding id prefixes: ST = stranger, SE = security, CO = contradiction, AD = adversarial (readiness), RC = root-cause readers, BR = the brief's lettered list (a) to (s) and the readiness list. FIXED = text changed; LEAD = needs the lead; NOT FIXED = reason given. Nothing was run except check-v18.py; "FIXED" means the text now says it, not that a person or program was tested.

## 0. Failures first: findings not fully fixed, and why
| Item | State | Why | Next step |
|---|---|---|---|
| CO-2, CO-14, SE-M6 (take program deletes) | NOT FIXED in code | the code is not in this checkout and I may edit only the new v18 files | Open 1; G1 is NO until the lead shows the fix |
| SE-M2, ST-T1, AD-M9 (window-end setting, which key the model program loaded) | NOT FIXED | no way to see it from the files; R4 and G16 say UNVERIFIED | Open 15 |
| ST-M5 and AD-B4 (contact id location, source of ids) | partly | the address check replaces the id as the deciding check (R7); the id source stays open | Open 10 |
| AD-M13 (usage lag) | NOT FIXED | a loopback rehearsal cannot measure it; the 30 minutes stays an unsourced proposal | Open 11 |
| AD-M4 (about 50 template values) | partly | every group has a filler, source and time (Note 3); the values themselves come from the lead | Open 11, 19 |
| SE-N6 | NOT FIXED | the checker proves form only; it cannot prove a statement true | the independent reader (Open 23) |
| ST-N7, ST-N9 (Windows and console menus) | NOT FIXED | button words and menu names were never seen: marked UNVERIFIED and sourced from the lead's copy | Open 19 |
| CO-1 root | FIXED as a rule; Open 2 asks the lead to accept that the sheet asks the owner for more than FACTS | | Open 2 |

## 1. The brief's list (a) to (s) and the readiness list
| Id | Fixed where |
|---|---|
| BR-a older key deadlock | Sheet R2 (a) and (b), R4, section 1 word "older key", 5.x, 6.2, 7.1; Note G26, 8; Open 2 |
| BR-b one non-circular time rule | Note 2 (terms, rule, worked example, absolute last start 18:14:40 UTC on 23 Nov at the default lease, `need_seconds` read at the final head); Sheet section 1 words, 3 sample and checks; Note G10 |
| BR-c owner enforces the hard end | Sheet R3 (cancel, confirm, "model key cancelled", then read), 5.8 ("go"), 7.1 tick, 7.7; Note G25 |
| BR-d failed key save | Sheet 6.5 (cancel at once, new run name, no second copy) |
| BR-e FREEZE after y | Sheet R10 ("cancel the key first"), R3 |
| BR-f end override | Sheet R6, R8; Note 5 no longer releases `end` |
| BR-g delete by id | Sheet R7 (address check, id optional, exact address fallback), Note G13, G27, Open 10 |
| BR-h R5 escape removed, truth in the lead note | Sheet R5; Note 0 item 1, G1, G17; Open 1 |
| BR-i charset | Sheet R9 (allowed characters) |
| BR-j roles | Sheet 5.2; R9 (film); Note 7; G11 |
| BR-k gate split | Note 1a, 1b, 1c; G15 = rehearsal printed result; G16, G25, G26 before the take; G13 shape before, G27 list after |
| BR-l dropped controls | Sheet R5 (recognise masked accounts), 7.2 (`sha256sum` of the take program), 3 check 5; Note G1, G2 (independent reader), G17 |
| BR-m each rule once | Sheet R9 (film, recording, charset), R1 (OFF lists, with the back-on in 8.4), glossary (window end); Note 5 (ban list once) |
| BR-n 180 and 189 | Note 2 (backstop), G14; Sheet 3 sample (credit slot, backstop); Open 6 |
| BR-o port | Note G7 (5678, 5679, 5690 to 5693 avoided; proposal 5701, 5702; `ss -tlnH`); Open 4 |
| BR-p who is sent twice | Note 5 (stated once); Sheet 3 expected counts, 9; Open 7 |
| BR-q template fields | Note 3 (expected counts, minutes at y, subject start in the clean-up message, second take rule); Sheet 3 |
| BR-r key file reuse | Note 3 (per-run key path), 8; Sheet 6.4 |
| BR-s sheet followable alone | Sheet 1, 3 (sample message, notice, result), 4 (one page order and "if you do nothing"), 5 to 9, R-table; Sheet 1 (how a message arrives, if the lead is silent) |
| BR-M3 run passing the cancel-by time | Note 2 formula (film pause inside alarm time); Sheet R3 alarm; Note G18 |
| BR-M4 template values and sources | Note 3 table |
| BR-M5 owner recomputes | Sheet 3 checks 1 to 5; Note G25 |
| BR-M12 lead secrets | Note G3, 8; Open 13, 22 |
| BR-M13 lag unsourced | Note G5, 2; Open 11 |
| BR-M14 take-prep contact | Note G13, G27; Open 10 |
| BR-N1 | Note G15 now says "the rehearsal's printed result"; no pointer to G12 |
| BR-N2 | Note G20 and Open 21 name the lead's edit |
| BR-N3 | Sheet 7.1 (clock tolerance in the message); Note 3 |
| BR-N4 | Note 3 ("Model settings names to compare") and Sheet 5.7 |
| BR-N5 | Note 0 item 3 lists the conflicts by name |
| BR-N6 | Note G17 (masked form copied after the rehearsal) |

## 2. Stranger review of v17
| Id | Fixed where |
|---|---|
| ST-B1 message unseen | Sheet 1 (what a message is, where it arrives), 3 sample |
| ST-B2 lead could read the key | Sheet R1 (may decline), 5.8 yes line |
| ST-B3 spend before y | Sheet R4 (the balance is the most you can lose; the owner decides the highest balance), 5.8 |
| ST-B4 calculator one-liner | Sheet 3 check 1 (by hand) |
| ST-B5 key-save command | Sheet 6.4 (what shows), 6.5 |
| ST-B6 FREEZE read commands | Sheet R10 (three read commands) |
| ST-B7 no notice shown | Sheet 3 sample notice and printed result |
| ST-M1 run name format | Sheet 1 words |
| ST-M2 "six things" | Sheet 1 (ordered list of what you do) |
| ST-M3 who "the lead" is, how a message arrives | Sheet 1 |
| ST-M4 meanings of "key" | Sheet 1 (only the model key and the older key are "key"; secret text in R1) |
| ST-M5 contact id | Sheet R7 (address decides) |
| ST-M6 throwaway accounts named | Sheet 1; Note 3 |
| ST-M7 key deadline circular | Note 2 |
| ST-M8 highest balance | Sheet R4 (owner decides) |
| ST-M9 delete button | Sheet R7 (copied from the page, UNVERIFIED) |
| ST-M10 answering a bad message | Sheet R8 |
| ST-M11 take settings file | Note 3 (folder and file name from the message); Sheet 7.3, R10 |
| ST-M12 person sent twice | Note 5; Sheet 3 sample counts |
| ST-M13 balance in the yes | Sheet 5.8 |
| ST-M14 exit code | Sheet 3, 7.7 (only 0 unless named) |
| ST-M15 revoke path | Sheet 8.3 |
| ST-M16 erase order | Note 4 step 7 to 9; Sheet 8.3 |
| ST-M17 posting place | Sheet 9, Note 3 |
| ST-M18 "both answers" | removed |
| ST-T1 UNVERIFIED items | Sheet R4, 1; Note 9 |
| ST-T2 one contact and mail each | Sheet 7.6 checks counts before `end` (R6) |
| ST-T3 key belongs to the project | Sheet 5.6 key names and R4 |
| ST-T4 recording and clipboard off | Sheet R1 (where turned off and back on); 6.1 |
| ST-T5 account name | Sheet R2, 5.5, 5.6 |
| ST-N1 "replaces v4 to v16" | Sheet intro ("all earlier sheets") |
| ST-N2 "message" | Sheet 1 (numbers message, clean-up message) |
| ST-N3 app password | Sheet 1 |
| ST-N4 close terms | Sheet 1 (defined once each) |
| ST-N5 worst-case price | Sheet 3 check 1 (an upper figure from the lead) |
| ST-N6 step 0 | removed from the sheet; Open 18 |
| ST-N7 Control Panel paths | Sheet 5.3 (UNVERIFIED for your version) |
| ST-N8 line 38 grammar | Sheet 5.4 rewritten |
| ST-N9 section 5 menus | Sheet 6 title (UNVERIFIED) and 6.3 (words in the message) |
| ST-N10 silence minutes | Sheet 3 sample (3 min), Open 11 |
| ST-N11 who crops | Sheet R9 (the editor) |
| ST-N12 R references | kept (rules once, referenced by id) |
| ST-N13 "backstop", "closed gate" | Sheet R4 (closed gate explained as "no gate"); Note 2 (backstop) |
| ST-N14 gap in minutes | Sheet 8.1; Note 3 |
| ST-N15 | checked fine in v17; unchanged |
| ST-Never contact route, companies, dollars at risk, WSL, how long, absent film person, order of the day, doing nothing | Sheet 1 (silent lead), 3, 4, R4 (balance is the most you can lose), 5.2 (minimal people); the model company and posting site names come from the message (Note 3, Open 19) |

## 3. Security review of v17
| Id | Fixed where |
|---|---|
| SE-B1 older key | Sheet R2, R4; BR-a |
| SE-B2 hard end and cancel order | Sheet R3, 3 check 2, 7.7; Note 2 |
| SE-M1 duplicate or lost same-name key | Sheet R2 (a) (every key of that name), 6.5, 6.6 (exactly one key) |
| SE-M2 which key the model program used | Sheet 8.1 (last-used times), 6.6 states what the start time proves |
| SE-M3 "model key cancelled" | Sheet R3; Note 4 step 7 |
| SE-M4 `end` override | Sheet R6, R8 |
| SE-M5 address check before delete | Sheet R7 |
| SE-M6 take program deletes | Note 0 item 1, G1; Sheet R7, R5; Open 1 |
| SE-M7 lead attests its own work | Note G1, G2 (independent reader); Sheet 7.2 (checksum) |
| SE-M8 account check | Sheet R5 (masked accounts), 5.5 and 5.6 |
| SE-M9 ban list | Note 5 (post checker's brief) |
| SE-M10 editor and R9; charset | Sheet R9; Note 7 |
| SE-M11 "go" word | Sheet 5.8, 7.1; Note G25 |
| SE-M12 FREEZE after y | Sheet R10, R3 |
| SE-N1 `grep -E` to `-F` | Sheet 5.7 (`grep -F`); Note 3 (no secret names in the list) |
| SE-N2 account-name typo | Sheet R2 |
| SE-N3 clipboard history back on | Sheet 8.4 |
| SE-N4 180 against 189 | Note 2, G14 |
| SE-N5 confirm cancelled | Sheet R3 (key list word in the message) |
| SE-N6 checker proves form only | stated in Note 0 and check-v18 output; Open 23 |
| SE-D dropped controls (M-D, A.5, key deadline, `end`, M-C, flow and file checksum) | Sheet R2, R5, R3, R6, 7.2; Note G1, G2 |

## 4. Contradiction review of v17
| Id | Fixed where |
|---|---|
| CO-1 | BR-a |
| CO-2 | BR-h |
| CO-3 charset against typed addresses | Sheet R9 |
| CO-4 delete by id against fallback | Sheet R7 |
| CO-5 FREEZE against `end` | Sheet R6, R10 (counts differ: R3 then R10) |
| CO-6 cancel against usage read | Sheet R3, 7.7 |
| CO-7 "two things only" against four | Sheet R4 (three, listed) |
| CO-8 film rules | Sheet R9 (once); Note 5 film content; Open 9 |
| CO-9 more owner tasks than decision 7 | Note G22; Open 24 |
| CO-10 backstop | BR-n |
| CO-11 three, two, four values | Note G3; Open 14 |
| CO-12 port | BR-o |
| CO-13 who is sent twice | BR-p |
| CO-14 take deletes | BR-h |
| CO-15 stale worst-case figure line | Note 9 last bullet |
| CO-16 window-end setting wording | Sheet R4 ("tested on an older head") |
| CO-17 circular formula | BR-b |
| CO-18 template fields missing | BR-q |
| CO-19 post-take order | Note 4; Sheet 8 |
| CO-20 R8 list | Sheet R8 (no list of ids) |
| CO-21 post condition | Sheet 9 and Note G29 (counts); lease sentence once (Note 5) |
| CO-22 nits (line counts, 10 terms, account and last-4 check) | counts removed from the text; last-4 check dropped, the account name check is Sheet 5.5 |
| CO-drift ban list, film rules, recording lists, R7 method, R9 presence, account name, window end, post-by, 30 minutes, five roles, narrow claim | BR-m; the 30 minutes is now only the proposal for lag and gap (Open 11); post-by only in Sheet 9 |

## 5. Readiness review of v17
| Id | Fixed where |
|---|---|
| AD-B1 | BR-a |
| AD-B2 (a to e) | BR-b |
| AD-B3 | BR-k |
| AD-B4 | BR-g; Note G13 |
| AD-M1 | BR-r |
| AD-M2 two takes | Note 2 (second take), Open 17; Sheet 8.5 |
| AD-M3 | BR-M3 |
| AD-M4 | BR-M4 |
| AD-M5 | BR-M5 |
| AD-M6 go rows likely NO | Note 0 items 1 and 2, G1, G3, G21 |
| AD-M7 | BR-n |
| AD-M8 | BR-o |
| AD-M9 G16 against Open 11 | Note G16 (run or read qs_37 at the final head) |
| AD-M10 | BR-i |
| AD-M11 | BR-j |
| AD-M12 | BR-M12 |
| AD-M13 | BR-M13 |
| AD-M14 | BR-M14 |
| AD-M15 | Note 2 (`need_seconds`), G10 |
| AD-N1 to N6 | BR-N1 to BR-N6 |

## 6. Root-cause readers
| Id | Fixed where |
|---|---|
| RC-1 one rule in many places | each rule once (BR-m); check-v18 counts key phrases |
| RC-2 owner asked to trust the lead's facts | Note 1 carries every lead statement; the owner keeps only checks he can see (Sheet 3 sums, 5.7, 7.2, R5) |
| RC-3 owner role grew | Sheet 1 lists the tasks plainly; Note G22; Open 24 |
| RC-4 language | glossary with bold first use, checked by check-v18 |
| RC-5 length | the sheet is longer than v17 because the strangers asked for samples and an order of the day; Open 24 says what to cut if you disagree |
