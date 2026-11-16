# v13 CHANGES: one row per finding, status and where

Files: S = `OWNER-STEPS-realrun-v13.md`, C = `OWNER-DAY-CARD-v13.md`, A = `OWNER-STEPS-v13-APPENDIX.md`. Ids: ST-B/M/m = `review-v12-stranger.md` blocker/major/minor (numbered in the order of the condensed list; minors m1 to m12 are my numbering); SE-M/m = `review-v12-security.md` (nit = SE-nit); CI-M/m = `citation-check-v12.md` (minors keep their numbers 5 to 11); R(a) to R(g) = the lead's rulings in the task. "Open" rows point to `v13-OPEN-FOR-LEAD.md` (L-numbers). Locations are section names, not line numbers.

**Not done or not good enough, first.** (1) Nothing was run: every command stays UNVERIFIED; the card has a blank stamp line the lead fills after a rehearsal (L1). (2) The sheet is 28.6 KB against the 25 KB target; I cut duplicates and moved text to the appendix but not required content; the stop table, the worked money example and the fix for the security majors added about 2.5 KB. (3) Several fixes only exist as blanks or sentences "THE STUDIO LEAD FILLS THIS IN" because the value is the lead's (L1 to L20). (4) Inputs (AGENT-SCOPE, DECISIONS) not edited (L12). (5) The reviews were read as condensed copies; my numbering of minors may differ from the full reports.

| Id | Finding | Status | Where fixed / why open |
|---|---|---|---|
| ST-B1 | commands and screens UNVERIFIED decide Freeze | partly: stamp line + single UNVERIFIED legend; transcript needed | C "Stamp"; S "Two markers"; open L1, L16 |
| ST-B2 | money rule not followable (3 definitions, no example, two thresholds) | fixed | S money rule: words once, worked example (invented numbers), one start point (E reading), expected rise before E; A section 1 points back; open L6, L7 |
| ST-B3 | emergency cancel has no click path; precedence | fixed in text, page names open | S stop-word table, money rule item 6; C table; open L2 |
| ST-B4 | key-like text judgement | fixed | S stop table row 1 (any doubt = key); step 0.5 any count above 0 = key |
| ST-B5 | exit-code rule contradiction | fixed | S go item 7, A sections 5 and 9, C F.3: one rule, no number; open L4 |
| ST-M1 | Freeze vs key on screen | fixed | S stop table (precedence, run-window exception) |
| ST-M2 | card relies on row numbers | fixed | C "The blanks" table; open L5 |
| ST-M3 | notice has 8 conditions, invented layout, yes text | partly | C E.2 numbers match the blanks; A.6 yes text in S; real layout open L1 |
| ST-M4 | "at once" vs 2 seconds; "helper window" | fixed | C E.3, E.4 |
| ST-M5 | film pause clock, rows 4 and 7, exit 3 | fixed | C F.1 to F.2, blanks name people; silence rule not during pause |
| ST-M6 | deleting contacts by masked id; account by memory | fixed in text | C F.5 (test address, count ticks, account name blank); open L19 |
| ST-M7 | step 0 deletes vs go item 5; authority "being patched" | fixed in text, patch open | S step 0 warning separates the two programs, asks for the patch done; open L9, L12 |
| ST-M8 | step 0.4 curly quotes, errors | fixed | S rule 10 (type by hand), 0.4 text |
| ST-M9 | hidden preconditions | fixed | S Words (WSL, read-only commands, checksum), C E.0 |
| ST-M10 | key list address by hand, wrong site | fixed in text, address open | S money rule words; C blanks (address, account name); open L2 |
| ST-M11 | cancel anyway vs "model program shut down"; two deadlines | fixed | S I.0 (right after F.4, same day, no waiting); C F.4; open L20 |
| ST-M12 | owner posts a claim not proven; 12 vs 13 | fixed | S step J (claim shown by the printed result; lease sentence not approved); "full list of 13" |
| ST-m1 | 12 vs 13 | fixed | S step J; check script |
| ST-m2 | "three files" vs notes | fixed | S opening ("studio lead keeps other notes") |
| ST-m3 | rows 8 and 9 counted | fixed | S DO THIS FIRST 1; A section 2 |
| ST-m4 | card marked draft with date | fixed | C first line states draft until the stamp is filled |
| ST-m5 | "lead" two meanings | fixed | S Words ("lead" alone = made-up sales contact; the studio lead always in full) |
| ST-m6 | undefined terms | fixed | S Words (re-pin, commit id, checksum, lease, database); A section 1 (`mf_leads`, `DESK_*`, `MF_*`) |
| ST-m7 | 20 vs 14 minutes | fixed | S go item 5 explains both |
| ST-m8 | 5678/5679 vs one digit | fixed | S C.3 "digit for digit"; C blanks |
| ST-m9 | partial-match checksum | fixed | S step 0.2 and C E.0: all eight groups |
| ST-m10 | read -rs recovery order | fixed | A section 15 steps 3 to 5 (paste after the prompt shows) |
| ST-m11 | four stop words | fixed | S table: three words plus Stop (ruling (f)) |
| ST-m12 | [UNVERIFIED] on seven card lines | fixed | C has none; one stamp line instead |
| SE-M1 | "limited key" never made limited | fixed in text, fact open | S A.0 two-branch sentence, never "limited" unless the message says so; owner prints the ledger total; open L3, L6 |
| SE-M2 | run key stays after a trial | fixed | S Step A heading, trial paragraph, I.0; A sections 11 and 15 |
| SE-M3 | go item 5 covers one script; read-only stated as fact | fixed in text | S go item 5 (every imported file, file and line); row 19 (A section 2); A.5 compares the take app's permissions; open L8, L9 |
| SE-M4 | probe key stays | fixed | S 0.6 deletes the probe app and erases its file; row 20 split (A section 2); exposure names the probe key |
| SE-M5 | lease sentence in post | fixed | S step J box "NOT APPROVED"; open L11 |
| SE-M6 | how connection values enter n8n | fixed in text, plan open | S go item 4; open L10 |
| SE-M7 | notice on film | fixed | S D; A section 14 item 10 and S1 note; C E.2 |
| SE-m1 | one deadline | fixed | S I.0; C F.4 and "After" |
| SE-m2 | name not hint | fixed | S I.0 warning |
| SE-m3 | Clear all after history off | fixed | A section 15 step 1 and 4 |
| SE-m4 | paste after the prompt | fixed | A section 15 step 3 |
| SE-m5 | cut -c1-12 | fixed | S 0.5 (command removed; counts only) |
| SE-m6 | "cannot be undone" for contacts | fixed | S step I warning ("treat as final") |
| SE-m7 | n8n timing during C | open | A section 10 unchanged; L13 |
| SE-m8 | accepted exposure by silence | fixed in text | S A.6 sentence "I accept the exposure"; L20 |
| SE-m9 | erase timing, `DESK_*` | open | S I.6 asks the lead to state; L14 |
| SE-nit | "follow" reads as guarantee | fixed | S typed-answers paragraph ("are expected to follow") |
| CI-M1 | lease sentence contradicts Q21.2 | fixed | S step J box; wording "three tries in total including the first"; open L11 |
| CI-M2 | go item 7 self-contradiction | fixed | see ST-B5; the phrase "exit 3 only when C is unknown" is gone (check script) |
| CI-M3 | "full list of 12" | fixed | S says 13; check script compares with appendix 8 |
| CI-M4 | F.2 for the usage page | fixed | S money rule item 4 names F.4 |
| CI-m5 | "60 minutes after F.4" | fixed | C F.4 and After: same day |
| CI-m6 | E.0 not a card heading | fixed | C heading "E.0 Before E" |
| CI-m7 | "appendix G" | fixed | S rule 12 "appendix 12" |
| CI-m8 | CHANGES anchors | fixed | this file uses section names |
| CI-m9 | A:101 F.1 vs F.2 | fixed | A section 11 "at F.2" |
| CI-m10 | NOTES "row 2" is the order table | fixed | OPEN file avoids row-only names |
| CI-m11 | a placeholder word in meta text trips a literal grep gate | fixed | the check script counts the three placeholder words (list in `check-v13.py`): zero in all five files |
| R(a) | one exit-code rule | fixed | see ST-B5 |
| R(b) | post only DECISIONS 1 wording; lease sentence gated | fixed | S step J |
| R(c) | one cancel deadline | fixed | S I.0, Step A heading, C, A sections 6, 11, 2 row 21 |
| R(d) | worked example; define once | fixed | S money rule |
| R(e) | row values as blanks on the card | fixed | C "The blanks" |
| R(f) | one table with precedence | fixed | S stop table; C copy |
| R(g) | ban list count and cross references | fixed | S step J, rule 12, money rule item 4, C E.0 heading; check script |
| Q15 to Q21 | lead answers | applied as in v12 plus: Q19.1 delete wording unchanged; Q19.3 exposure plus probe key; Q20.4 no number stated; Q21.1 cancel same day; Q21.2 only DECISIONS 1 wording in the post, gated sentence; Q21.3 caption; Q21.4 retake count "lead computes" kept in A row 10 | S, A |
