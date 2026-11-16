# v21 changes (builder, Mon 16 Nov 2026; one batched fix pass for all findings of review-v20-security.md, review-v20-stranger.md, review-v20-contradiction.md; failures first)

## 0. Failures first: what v21 does NOT settle
1. **Nothing was run or seen.** The only program run is check-v21.py (reads text, prints counts and problems). It proves form: ids, counts, definitions before use, arithmetic of the invented examples, weekdays, UTC = IST pairs, pointers, banned-word counts. It cannot show that any statement is true. Raw output: evidence-v21/check-v21-raw.txt. I did not run a mutation test of the checker this round (v20 planted five mistakes; v21 did not repeat it): not checked.
2. **The sheet is not shorter: it is longer** (v20: 110 lines, 6,638 words by `wc`; v21: 118 lines, 7943 words). I did what the brief asked for in order of work only partly: a "Your day in short" paragraph now points to the order-of-the-day table (section 4), and the lists of set phrases and commands were moved out of rule cells into one place under the rules table (R6 and R8 shrank), but section numbers stayed (renumbering about 40 pointers across four files was not worth the risk). The additions answer findings (key-save check, film-person disclosure, auto-reload, words-that-look-alike, parts-fit paragraph, tolerated-UNVERIFIED list). Open 30 says what could move out. Not fixed: shorter.
3. **Lead gates unchanged and still open:** G1 (take program never deletes: the lead shows the final head's grep, Q23), G16 (end-date refusal: "lead verifies at re-pin", Q27), G30 (no lead timer, no "go" on or after Mon 23 Nov), G33 to G36, plus the new lead statements in v21-OPEN-FOR-LEAD.md items 42 to 50.
4. I read no take program, flow, model program or vendor page (none are in this checkout). Every vendor behaviour (copy button, key shown once, cancelled word, cancelling ends calls, auto-reload word, set limit while creating) is UNVERIFIED.
5. **Two readings chosen as the safer one (the answers do not decide them):** (a) R1 against R2: the owner cancels only a model key made today or the named older key, any other key or password on screen is reported, not cancelled (cancelling is irreversible); (b) film-person exposure (F7): disclosed in R1 and the yes sentence, not closed technically (a separate machine for the film person is the lead's decision, Open 45).
6. **Which UNVERIFIED items end the run (FREEZE) and which are tolerated:** see section 4 below.

## 1. Findings table (one row per finding id)
### Security review (F1-F7, N1-N9)
| Id | State | Where fixed or why not |
|---|---|---|
| F1 key-save line writes empty file with `exit 0` | FIXED | sheet 6.4 line now `read ... && [ -n "$K" ] && printf ... > file`; empty paste or Ctrl-D gives a non-zero number and no file; 6.6 checks the size against a range in the numbers message (new slot; Open 43: no range, no run); 6.5 handles a wrong size. A wrong non-empty paste is caught only by the size: UNVERIFIED |
| F2 R3 step 0 waits without limit | FIXED | R3 (0): wait at most 60 seconds, then go on and report the raw recording to the editor; says the recording box is the film profile page area only so the key page should not be in it (UNVERIFIED, the editor confirms in the rehearsal); intro "if the lead does not answer" names the 60 seconds as the only wait |
| F3 auto-reload never checked | FIXED | 5.6 (write the word the prepaid page shows), R4 (auto-reload not off: no run), the yes sentence, the numbers message slot, glossary; Note G14 and G25 |
| F4 run on Mon 23 Nov allowed vs not | FIXED | one rule: no run on Mon 23 Nov (sheet check 2, glossary Deadline, numbers message, Note G10, G16, G30, section 2); the 18:19 UTC = 23:49 IST cancel-by statement stays only in check 2, as "latest cancel-by time" |
| F5 call ceiling and run total called a worst case | FIXED | glossary: "Call ceiling" = the lead's figure, nothing you can check enforces it; "Expected total" (renamed from run total) = not a limit, not a worst case; the yes sentence says so; numbers message, notice sample and check 1 follow; Note renamed everywhere |
| F6 older-key sentence not told to the owner | FIXED | 6.2 and section 4 row 6 now say write "I cancel the older key <its name>" then cancel; the sentence is in the set-phrase list; R2(b) matches |
| F7 key readable by film person's session | FIXED by disclosure, not closed | R1 risk sentence, the yes sentence, 7.6 (film person alone drives the browser, owner sits beside, film person opens no terminal or application, R9). Technical closing is the lead's decision (Open 45) |
| N1 "never sees your screen" | FIXED | glossary Lead: "is not meant to" |
| N2 18:19 only at latest start | FIXED | check 2 says "its latest cancel-by time" |
| N3 18:14:40 under Wed 18 Nov | FIXED | sample line: "on the deadline day (it does not bind on Wed 18 Nov)"; Note section 2 says B is an instant on the deadline day |
| N4 "money used before" vs ledger total | FIXED | sample: "ledger total 12.40 + expected total 0.81"; ledger total defined |
| N5 key made long before use; alarm checks; second route | FIXED / PARTLY | earliest key time (glossary, sample, 6.2, Note PS); 6.2 checks alarm date, volume, Do-not-disturb; R3 failure column tries the same page on the phone (UNVERIFIED). A real second route for the key-list page: not known, Open 48 |
| N6 seconds in 6.6 | FIXED | 6.6 compares date, hour, minute and second |
| N7 R5 vs R2(b) older key printed | FIXED (safer reading) | R2(b) allows cancelling at once if the text appeared on screen, with the sentence and the message statement still required; R1 failure column cancels only a model key made today or the named older key |
| N8 `date -u` competes with the challenge | FIXED | 8.1 and R3 (1): `date -u` after the challenge is typed and Enter pressed |
| N9 highest-balance question vs Q24 | FIXED | removed everywhere (glossary, R4, sample, check 6, yes, Note G14, section 2, template, Open 11) |
| UNVERIFIED stated as fact: "cancelling ends further calls" | FIXED | R2 now says "should end ... (vendor behaviour, UNVERIFIED)" |

### Stranger review (blockers S1-S4, major groups, nits)
| Id | State | Where fixed or why not |
|---|---|---|
| S1 how the parts connect, what enforces the ceiling | FIXED (UNVERIFIED text) | section 1 bullet "How the parts fit"; the lead confirms (Open 42) |
| S2 lead software or person | FIXED | glossary Lead: the Claude session, an AI system, not a person; "Claude never posts" became "the lead never posts"; "if the lead does not answer" now covers the time after the run |
| S3 R3 trigger fires on every run | FIXED | "the latest start passes before you press Enter on the start line" |
| S4 R4 accepts losing the balance for a 0.81 run; two things called go | FIXED | expected total wording; "Go marker" renamed "Spend lock"; "go" defined once as the lead's word |
| SW words: key alive two starts | FIXED | one start (create button, 6.3), one end (R3 proof) |
| SW "model key" name vs "whatever its name" | FIXED | glossary Model key |
| SW key / take / run / window / account name / clean-up message / alarm / address / write-send-report / in-out / cut / second | FIXED | "take" is a name tag; run, run day, go, window, send, alarm defined in "words that look alike"; account names one slot per account; clean-up message defined; alarm-time alarm and cancel-by alarm; "mail address" against "page address"; "tokens in and out"; "remove that ending", "each place the editor cut"; "second way" is "other channel", "second terminal" is "read terminal" |
| SC1 R1 vs R2 (key seen on screen) | FIXED (safer reading) | see section 0 item 5 |
| SC2 6.1 "no Recall page: go on" vs UNVERIFIED = FREEZE | FIXED | tolerated list (glossary UNVERIFIED) |
| SC3 8.1 `date -u` vs R3 / R10 | FIXED | R3 (1) writes the time with `date -u`; R6/R10 list it |
| SC4 R8 "only four words" vs set phrases | FIXED | R8 says the four words are the lead's; your own phrases are in one list under the rules table |
| SC5 R1 "stop" vs R3 (0) wait | FIXED | 60 seconds cap |
| SC6 workflow-off word mid-run vs "n8n is off" | FIXED | R8: "n8n is off" counts only after "model key cancelled"; the lead sends no message while it switches n8n for person C ("Reading the counts"); UNVERIFIED |
| SC7 "one lower than you wrote" | FIXED | R3 (2) names step (1) of R3 |
| SC8 "cancel whatever is on the screen" | FIXED | "cancel every model key you made today (R2 a)" |
| SC9 second cancel-by time in sample parenthesis | FIXED | removed from the sample; only in check 2 |
| SM1 paste check does not look at content | FIXED | F1 |
| SM2 older key cancelled before the paste is proved | NOT CHANGED (reason) | cancelling first removes a live key before a new one exists; the run does not need the older key; the cost (start again with a new run name if the save fails) is stated in 6.2; the other order leaves two valid keys alive. Open 2 carries it |
| SM3 5.7 vs R1 | FIXED | R1 failure column and R2(b) align; 5.7 says a long random-looking value is not sent |
| SM4 7.4 fast answers end the run with a key made | FIXED | 7.4 says a refusal is R3 (UNVERIFIED) |
| SM5 R3(2) baseline | FIXED | see SC7 |
| SM6 phone alarm zone, clock zones | PARTLY | 6.2 checks the alarm date, volume and Do-not-disturb and that the alarms are set to IST times; commands already use `TZ=UTC`; the key page zone is written at 5.6 and reported at 8.1; Windows clock zone check: not added (the `date -u` clock counts, 7.1) |
| SM7 5.4 earlier demo mails: no expected count | FIXED | numbers message slot "earlier demo mails expected" (sample 0), 5.4, Note template |
| SM8 8.3/8.4 which mail account | FIXED | 8.3 "in the receiver Gmail" |
| SM9 which balance page counts | FIXED | the yes sentence and R4 name the prepaid page of the numbers message |
| SM10 "unknown" for person C vs unexpected wording | FIXED | "Reading the counts": "unknown" for C is accepted, any other wording: R10 |
| SX1 who drives the browser, who sits where | FIXED | 7.6 and glossary Film person |
| SX2 film cue "it" has no subject | FIXED | glossary Film pause and 7.6 name the cue and who watches what |
| SX3 "gives up after <minutes>" empty | FIXED | sample fills 40 min (invented) |
| SX4 seconds ignored in 6.6 | FIXED | see N6 |
| SX5 `pgrep` prints two numbers | FIXED | 6.6: two numbers or none: R10 |
| SX6 6.3 copy before or after limit | FIXED | set the limit before you copy (UNVERIFIED whether the page allows later) |
| SX7 5.1 run-name rule not in section 1 | FIXED | glossary Run name |
| SX8 older key "none" cannot be ticked or cancelled | FIXED | 7.1 and the yes sentence |
| SL length: 60 labels, 150-330 word cells, 35 cross-references, 15 actions in the film pause | NOT FIXED (reason in section 0 item 2); film pause split into who does what (SX1) |
| SN nits (fingerprint wording; "also read independently by"; version id line; units on PRICE_OUT_CENTS and price per call; R8 vs 6.4 characters; sample placeholders vs "angle brackets: no run"; section 4 row skips 5.2; "any other line" in 5.7; 8.5 cut and editor hours; posting deadline "agreed time") | FIXED | each edited in place: fingerprint is 64 characters, compare first 16; "independent reader of the take script"; version id line says whether the program prints it; units added; the key-save line is the stated exception to R8; "real numbers message"; row 4 says 5.2 to 5.7; "any other line that grep prints"; editor hours slot in the sample; posting deadline is hard |
| "Not understood after rereading": connection, lead, key alive, why older key cancelled, who drives browser, R3(2) baseline, latest start mid-run, three money figures, every UNVERIFIED = FREEZE | FIXED | see S1, S2, key alive, 6.2 (older key reason: "the run does not need it" stays; reason for cancelling it is Open 2), SX1, SC7, S3, F5, tolerated list. Only "why the older key must be cancelled" is not newly explained: R4 key checks need exactly one valid key |

### Contradiction review (M1-M6, m1-m15, note 120)
| Id | State | Where fixed or why not |
|---|---|---|
| M1 money-limit question | FIXED | see N9 |
| M2 post sentence is two sentences, names no person | FIXED | sheet glossary "sentences (normally two)", section 9; Note G29, section 5 (B ten-times variant deleted); Open 7 |
| M3 funding leftovers | FIXED | sheet R4 text; v21-MAP rows 15, 24, 84, 109; this file section 3 (carried v20 text corrected) |
| M4 R3 trigger | FIXED | see S3 |
| M5 Mon 23 Nov allowance | FIXED | see F4 |
| M6 UNVERIFIED written as fact | FIXED | 7.3 command and the order of login lines, notice and prompts marked UNVERIFIED; refusal of fast answers; 5.4 filter and "3 mails" marked UNVERIFIED |
| m1 "never sees" | FIXED | N1 |
| m2 "not genuine" | FIXED | "not accepted" (glossary Message place) |
| m3 "timer" wording G36 / Open 36 | FIXED | offset in minutes, never touches the key |
| m4 think time 20 s | FIXED | Open 11 says proposal; program default 2 s (v3, allowed 1 to 60); sample says "the take program decides" |
| m5 "cancel-by time on Mon 23 Nov" | FIXED | "latest cancel-by time" |
| m6 R4 "does not print the settings figures" | FIXED | "the model settings file's figures" (check phrase updated) |
| m7 "asked once per made-up person" | FIXED | "at most once" |
| m8 "existing credits" | FIXED | "existing balance" |
| m9 7.5 "type nothing" | FIXED | "in the take terminal" |
| m10 contact id optional | NO CHANGE (reviewer: none) | |
| m11 owner does about 15 tasks vs decision 7 | NOT CHANGED | already Open 24 and Note G22 |
| m12 "lead verifies at re-pin" in G16 and R4 | FIXED | both |
| m13 note "(not fixed)" | FIXED | removed |
| m14 first alarm "rings only when the run can be over" | FIXED | "by the lead's proposed figures" |
| m15 length figures differ; CHANGES line 33 | FIXED | counts are by `wc` in section 0; the 18:19 statement is in check 2 |
| note 120 "the take never deletes (G1)" | FIXED | "Decision 2: never deletes; the lead shows the final head's grep at re-pin (Q23, G1)" |

Totals: security 16 findings + 1 unverified-as-fact = 17 rows: fixed 16, partly 1 (N5 second route), none unfixed without reason. Stranger: 4 blockers fixed; majors: 2 not changed with reason (SM2, SL), 1 partly (SM6), the rest fixed. Contradiction: M1-M6 fixed; m1-m15: 13 fixed, 2 no change (m10, m11). Exact counts are in the checkpoint note.

## 2. Lead answers Q22 to Q31 (still applied)
Q22 (c) two sentences, no person; Q23 decision 2, grep at re-pin; Q24 no limit question, no second account, yes names shared Linux user, clipboard, screen (and now the film person's session); Q25 cancel-by 18:19 UTC = 23:49 IST as latest cancel-by, target Wed 18 Nov; Q26 no lead timer, no "go" on or after Mon 23 Nov; Q27 UNVERIFIED, "lead verifies at re-pin"; Q28 D5 OWNER-OPEN, non-blocking (Open 41); Q29 run.py out of every pull request; Q30 and Q31 nothing.

## 3. Carried over from v20-CHANGES.md, corrected
- v20 section 0 item 4 said a dedicated funded account was "the recommended option (R4, the Funding slot, Open 32)": that option and its slot are removed (Q24); the whole balance is the exposure.
- v20 section 2 listed "R4: funding option" and "Section 3: ... funding ...": both removed; the R4 text now is: whole balance, key checks, auto-reload off.
- Recomputed by me (see evidence-v21/arith-v21.txt): price (40,000 x 3 + 10,000 x 15) / 1,000,000 = 0.27; 3 x 0.27 = 0.81; 12.40 + 0.81 = 13.21 = 1321 cents; 11:30 + 25 min = 11:55 = 17:25 IST; + 10 = 12:05 = 17:35 IST; deadline 18:29 UTC = 23:59 IST; latest cancel-by 18:19 UTC = 23:49 IST; deadline - 45 min = 17:44:00 UTC = 23:14 IST; + 25 = 18:09:00 = 23:39 IST; + 10 = 18:19:00; 18:29:00 - 860 s = 18:14:40 UTC = 23:44:40 IST; Earliest key time sample 11:00 UTC = 16:30 IST.

## 4. UNVERIFIED items: which end the run and which are tolerated
- **End the run if a key is alive, otherwise wait (FREEZE):** every UNVERIFIED difference not listed as tolerated, among them: the take script fingerprint and any start-line form (`-I`), the two login lines and their order, the notice and its prompts, the refusal of fast answers, the key file size range, `ps`, `pgrep` and `ls` outputs, the settings figures, the printed result wording, button and state words, the model program's deadline setting, vendor behaviour that cancelling ends calls, the film recording box, the filter and the 3 demo mails.
- **Tolerated (marked "UNVERIFIED, tolerated" in the sheet; the owner writes what he saw and goes on):** Windows menu paths (5.3 and 6.1), the Recall page, the paste method (6.4), the app-password page path (8.3), where the contact id sits in a page address (the mail address check is the control). Note section 0 item 8 gives the lead the same list. Open 47 asks the lead to confirm it.

## 5. Not claimed
Nothing here is reviewed. The EGM steps after the build (independent evidence runner, `egm:*` reviewers, resolve, drift report) are the lead's. I did not run a mutation check of check-v21.py.
