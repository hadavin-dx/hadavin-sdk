# v21 map: carried over from v20 (every finding of the five v19 reviews and where it is fixed), corrected for v21; the v21 findings are in v21-CHANGES.md

Written Mon 16 Nov 2026. **Sheet** = OWNER-SHEET-v21.md (section number such as 6.4, rule id R1 to R10); **Note** = LEAD-RELEASE-NOTE-v5.md (G1 to G38 are its gates, "Note n" its section); **Open** = v21-OPEN-FOR-LEAD.md (item number). Id prefixes: XB, XM, XN = security review (B1, M-A to M-F, N-1 to N-6); SB, SM, SN, SW = stranger review (blockers, majors, nits, words not understood); RG = readiness review (gaps 1 to 24); CB, CM, CN, CC = contradiction review (blockers, majors, nits, the compromise); EV = evidence summary (mismatches 1 to 9). Three states: FIXED (text written, form check passes), LEAD (the fix needs the lead's code or statement: written as a gate with a "no run" or "stated and accepted" default, never claimed as done), NOT FIXED (with the reason). "FIXED" never means run or seen working: nothing here was run.

## 0. Failures first: findings not fully fixed, and why
| Item | State | Why | Next step |
|---|---|---|---|
| XB1 take program deletes contacts today | LEAD | the code is not in this checkout; no later fix was read | Open 1; Note G1 stays NO; the sheet no longer relies on the Note (R7 now needs the clean-up message sentence) |
| CM1 spend lock (model program waits for a marker after the challenge) | LEAD | needs the lead's code at the final head | Open 33; Note G33; sheet R4 keeps the "may spend before y" fallback and 8.1 has the weaker last-used check |
| CM4 and the 7.7 error sentence (take program never calls the model after `end`) | LEAD | needs a code reading | Open 34; Note G34; the sheet 7.7 error sentence stays and the message states the accepted exit code |
| XM-B end-date refusal shown at the final head | LEAD | needs a test run at the final head | Open 15; Note G16; sheet check 2 forbids any run on Mon 23 Nov |
| XM-F typed worst-case figure prompt | LEAD | needs a code reading; a decision cannot change code | Open 35; Note G35; sheet R5, R10 and 7.3 make any request to type a figure a FREEZE |
| RG21 lead-side stop mechanism, CB (stop at alarm) | DECIDED (Q26) | no lead timer exists and none is invented; the sheet tells the owner to cancel the key himself | Open 27; Note G30; no "go" on Mon 23 Nov |
| RG1 film cue and the lead's n8n timing | LEAD | the printed line and the offsets come from the rehearsal | Open 36; Note G36; no cue, no run |
| CC separate funding option | DECIDED (Q24) | removed: no second account or workspace; the whole balance stays the exposure and the yes names the shared Linux user, clipboard and screen | Open 32; sheet R4 and 5.8 |
| Sheet length (brief: aim shorter than v19 if quality allows) | NOT SHORTER | quality did not allow: about 6,500 words and 109 lines against v19 5,246 words and 102 lines; about 100 findings added definitions, rules and sample slots; no safety rule dropped | Open 30 |
| Other channel (the v18 stranger blocker SB2, still open) and XM-E lead reach beyond the key file | PARTLY | the other channel is the lead's to name (Open 26, G31); the yes sentence now names the clipboard and the screen, but nothing technical stops the lead | Open 22, 26 |
| Everything marked UNVERIFIED | UNCHANGED | take scripts, flows, model program, page words are not in this checkout | Note section 0 item 2 |

## 1. Security review (review-v19-security.md)
| Id | State | Fixed where |
|---|---|---|
| XB1 | LEAD | see section 0; Note G1, G27 (the clean-up message carries "the take program made no delete call"); sheet R7 no longer cites a note |
| XM-A 6.2 against R4 | FIXED | Sheet R4 key checks (5.6 only the older key; 6.2 no valid key at all; 6.6 and 7.1 exactly one) and 6.2, 6.6; a second old key: no run |
| XM-B zero slack, no mechanism | FIXED (text) and LEAD | Sheet 1 (cancel-by never later than 10 minutes before the deadline), check 2 to 4, R3 (second phone alarm, cancel-by alarm rule); Note 2 (cancel buffer Z, new worked examples), G10, G16, G30; the end-date refusal stays LEAD (Q27: lead verifies at re-pin) and no timer exists (Q26) |
| XM-C absence counted as cancelled | FIXED | Sheet 1 (cancelled word = what the owner saw beside the older key), R3 step 2 (state word, reload, count with all filters off); the lead no longer supplies the word |
| XM-D word that ends a FREEZE | FIXED | Sheet R8 (the fourth word is "continue"; a FREEZE with a key alive ends in R3 and a finished run) |
| XM-E lead reach | FIXED (honest wording) | Sheet 1 (lead), R1, 5.8 yes sentence (key file, clipboard, screen); Open 22 |
| XM-F typed figure prompt | LEAD | see section 0 |
| XN-1 charset against `$` and `<` | FIXED | Sheet 5.8 (USD, no dollar sign, no brackets typed), R8 (second charset), intro line on angle brackets; check-v20.py tests the yes sentence |
| XN-2 cancel-by time has no rule | FIXED | Sheet R3 (second alarm at the cancel-by time, "nothing else matters until it is proven cancelled") |
| XN-3 app password on the screen | FIXED | Sheet R2 (c), R1 failure column |
| XN-4 model-account tabs open during the film pause | FIXED | Sheet 7.6 (close every model-account tab in every browser profile first) |
| XN-5 one fingerprint named as the program | FIXED | Sheet 7.2 ("this checks one file"), sample label "Take script fingerprint"; Note template |
| XN-6 `pgrep -af` prints command lines | FIXED | Sheet R6 and 6.6 (`ps ... comm=` and `pgrep -f`, no command line); Note G16, 9 |

## 2. Stranger review (review-v19-stranger.md)
| Id | State | Fixed where |
|---|---|---|
| SB1 `set -C` and an old key file | FIXED | Sheet 6.3 (the file must not exist before the key is made), 6.5 (new run name = new key file path); Note G37; Open 37 |
| SB2 the word that ends a FREEZE | FIXED | Sheet R8 ("continue") |
| SB3 R10 against R3 and R6 for the exit code | FIXED | Sheet R10 (`echo $?` once as R6 says), R6 (once after R3 is complete) |
| SM1 purpose of paid calls | FIXED | Sheet 1 (opening paragraph) |
| SM2 Recording against 7.6, 8.4 | FIXED | Sheet 1 (Recording, Recording OFF, Privacy switches), R1, 8.4 |
| SM3 R1 against 6.3 | FIXED | Sheet R1 failure column (outside 6.3 and the 6.4 paste) |
| SM4 R2(b) message, "valid key", "then no run" | FIXED | Sheet R2 (b), 1 (valid key), R4 key checks, 6.2 |
| SM5 garbled roles sentence | FIXED | Sheet 1 (film person, editor, post checker; the owner holds none), 5.2 |
| SM6 alarm during the film pause against R9 | FIXED | Sheet R3 (0), R9 (page area only), 7.6 |
| SM7 browser profile unsaid | FIXED | Sheet R1, 5.6 ("in your normal profile"), 7.6 |
| SM8 "gap in minutes", "note G1", "take-prep contact", "rehearsal" | FIXED | Sheet 3 sample ("gap before the second usage reading"), 1 (prep contact, rehearsal), R7 (no note cited) |
| SM9 ps time against ls time | FIXED | Sheet 6.6 (worked example of both forms, compare date, hour, minute) |
| SM10 charset against the yes and the post, typed by hand | FIXED | Sheet R8, 5.8, 9; Note 5 (the post sentence uses only the R8 characters) |
| SM11 lagging counts | FIXED | Sheet R6 (reload up to 3 times within 2 minutes) |
| SM12 "ignore" against "ask by the other channel" | FIXED | Sheet 1 (message place points to R8; the behaviour is only in R8) |
| SM13 every real value arrives in a message the reader lacks | FIXED | Sheet intro (angle brackets), 3 (full sample) |
| SN nits (do nothing against cancel first; angle brackets; WSL; "window" four meanings; "take" two meanings; sample masks `@example.net`; harmless word; recorder names; "your Linux user"; expected totals) | FIXED | Sheet intro; 1 (WSL, Linux user, take terminal, read terminal, "run" for the event); 3 sample (`@gmail.com` masks, expected totals 3 contacts and 3 mails); 6.4 (harmless word); 6.1 (the recorder the message names) |
| SW words not understood (lead, message place, other channel, numbers message, clean-up message, FREEZE, Recording, take-prep contact, rehearsal, G1, valid key, masked account, program limit, per-key limit, auto-reload, prepaid page, cancelled word, program's last start, silence minutes, person id, challenge, notice, film person, editor, post checker, deadline, tokens, clipboard history, Recall, exit code, app passwords) | FIXED | Sheet 1 defines each once (FREEZE is named in the UNVERIFIED bullet and defined in R10; the money words, tokens, masked account and silence minutes are in the "Plain money words" bullet); "G1" is no longer cited in the sheet |

## 3. Readiness review (review-v19-readiness.md)
| Id | State | Fixed where |
|---|---|---|
| RG1 film pause start and the lead's n8n cue | LEAD | Sheet 1 (film cue), 3 sample, 7.6; Note G36; Open 36 |
| RG2 subject start slot, R7 list | FIXED | Sheet 1 (demo mail), 3 sample, R7 (count them first); Note template, G38, G27 |
| RG3 third known valid key, no key-list read after 6.3 | FIXED | Sheet R4 (key checks), 6.3, 6.6; Open 39 |
| RG4 setting name to figure, units, deadline format | FIXED | Sheet 3 sample (name = value (unit), cents and USD, ISO deadline), check 1, 5.7; Note G14 |
| RG5 yes sentence characters and number format | FIXED | Sheet 5.8 (USD, exactly two decimals), R8; Note G25 |
| RG6 older key name and button words asked before the message | FIXED | Sheet 5.1 (the owner sends them with the run name); Note template and slot table |
| RG7 prep contact undefined, note cited | FIXED | Sheet 1 (prep contact), R7; Note G38 |
| RG8 label assignment and mail to person | FIXED | Sheet 5.4 (filter), 1 (demo mail), 3 (counts only: 3 mails); Note G38 |
| RG9 recording and filmed as roles, tool unnamed | FIXED | Sheet 1 (roles), 6.1; Note G24, 7 |
| RG10 minimum delay before `y`, refusal consequence | FIXED | Sheet 7.4, 3 sample (minimum think time) |
| RG11 paste, harmless word, folder must exist | FIXED | Sheet 6.4, 6.5 |
| RG12 ps and ls formats | FIXED | Sheet 6.6 |
| RG13 clock times of `y` and cancel, time zone, usage lag | FIXED | Sheet 8.1 (`date -u` at `y` and at the cancel; the key list zone); Note G5 unchanged |
| RG14 which mails, Sent, Trash, Spam | FIXED | Sheet R7 (label `demo` view only; never Sent, Spam, empty Trash), 5.4 |
| RG15 film delivery, editing time, upload, when the checker sees the post | FIXED | Sheet 3 sample, 8.5, 9; Note G24 |
| RG16 where to write values, lid close plugged or battery | FIXED | Sheet 5.3 (on paper; "plugged in" lid action), 6.1, 8.4 |
| RG17 "send the words you see" against no file contents | FIXED | Sheet 1 (report in words), R1 (settings lines may be sent), R10 |
| RG18 cancel-by time used by no step | FIXED | Sheet R3 (second alarm), 3 check 2 to 4 |
| RG19 version id cannot be compared | FIXED | Sheet 7.2 (compare only if the message says it prints), 3 sample; Open 40 |
| RG20 marker files end in `.used` | FIXED | Sheet 5.1 |
| RG21 lead timer before "go" | DECIDED (Q26) | Note G30 (no timer; no "go" on Mon 23 Nov); Open 27 |
| RG22 unresolved lead items block template slots | FIXED | Note 3 (a slot may hold "NOT SHOWN", "none" or "no" in the stated form; a missing line is no run) |
| RG23 template lacks slots | FIXED | Note 3 (subject start, prep address, setting map with units, recording tool and box, expected demo mail count, film cue, think time, spend lock, typed figure, end-date refusal, how the film reaches people) |
| RG24 older key and button words requested but the owner has no step | FIXED | Sheet 5.1 |

## 4. Contradiction review (review-v19-contradiction.md)
| Id | State | Fixed where |
|---|---|---|
| CB1 "send the words you see" sends the secret | FIXED | Sheet 1 (report in words, defined once), R1, R5, R6, R10; fingerprint reported as match or differ |
| CB2 a FREEZE with a key alive but before `y` | FIXED | Sheet intro, R3 (trigger = a key is alive), R10 ("A key alive: R3 first, and the run is over"), R8; a new try needs a new numbers message, run name, key file, key and yes |
| CB3 key page shown at the alarm while Recording is ON | FIXED | Sheet R3 step 0 ("stop" and wait until OFF), R1, 1 (film person switches OFF on "stop") |
| CM1 8.1 against R4 | LEAD | see section 0; sheet 8.1 has both wordings |
| CM2 take-prep contact | FIXED | Sheet 1 (`prep-<run name>@example.com`, never found by the film search), R7; Note G38 |
| CM3 never send a file's contents against sent lines | FIXED | Sheet R1 (class rule), 5.7 (a long random-looking value is a secret) |
| CM4 cancel while the take program may still need the key; exit code | LEAD (with sheet wording) | Sheet 3 sample line, 7.7, 7.8; Note G34; Open 34 |
| CM5 R7 covers only 5.4 mails | FIXED | Sheet 1 (demo mail), R7, 8.3 |
| CM6 R9 crops only the From column | FIXED | Sheet R9 (page area box agreed with the editor in the rehearsal), 5.4 (list view of label `demo` only); Note G24, 7; Open 29 |
| CM7 third known key deadlock | FIXED | Sheet R4 key checks (one wording), 6.2; Open 39 |
| CM8 `$` against R8 | FIXED | USD everywhere; check-v20.py counts zero dollar signs in the sheet |
| CM9 glossary "ignore" against R8 | FIXED | Sheet 1 (message place) |
| CN1 cancel-by time used by no rule | FIXED | Sheet R3 |
| CN2 version id with no check | FIXED | Sheet 7.2 |
| CN3 copy for the key against the harmless word | FIXED | Sheet R9 (one definition of the only copying) |
| CN4 claimed people each need 1 contact and 1 mail, C prints unknown | FIXED | Sheet 9, Note 5 and G29 (the sentence names only A and/or B) |
| CN5 R7 cites a note the owner need not read | FIXED | Sheet R7 |
| CN6 clock | FIXED | Sheet 7.1 (`date -u` is the clock that counts; phone alarms are the second guard, set to the IST times) |
| CN7 "key" against R2(a) | FIXED | Sheet 1 (model key = any paid-model key created after starting section 6) |
| CC unexamined compromise | DECIDED (Q24) | the funding option is dropped; no second account is proposed | Open 32 (answered) |

## 5. Evidence summary (review-v19-evidence-summary.md; each fix is in the v20 files, not in v19)
| Id | State | Fixed where |
|---|---|---|
| EV1 Open row 7 cites line 1051 of a 35-line file | FIXED | Open 1 now reads "AGENT-SCOPE section 3, line 20, which quotes `run_real_check_n8n.py:1051`" |
| EV2 map SM5 pointed to Open 19 | FIXED | v20 has no row that cites Open 19 for UNVERIFIED items; the UNVERIFIED line is Note 3 (template) and Note 0 item 2 |
| EV3 order-table rows 6 to 10 "NOT safe" | FIXED | this map says "rows 8, 9 and 10 of the sheet's order table say NOT safe"; rows 6 and 7 say "cancel it" |
| EV4 SB3 pointed to 6.5 | FIXED | the "why no loss" sentence is in sheet 6.2; this map cites 6.2 |
| EV5 "Note 0 (money words)" | FIXED | the money words are in the Note's opening paragraph (before section 0); the v20 map cites "the Note's opening paragraph" |
| EV6 SQ-len source not found in the stranger copy | FIXED | v20 cites no stranger length question; the length item is Open 30 and the v20 brief |
| EV7 Note section 3 statements line omits G31, G32 | FIXED | Note 3: "every 1a gate (G1 to G15, G17 to G24, G31 to G38)"; check-v20.py compares that range with the gates in table 1a |
| EV8 G20 labels stage.journal "decision 10" | FIXED | Note G20 cites ORDERS.md line 152 (Q21.3) and says what DECISIONS item 10 and DECISION-one-store line 26 say |
| EV9 AGENT-SCOPE and FACTS lines both called stale | FIXED | Note 9 names AGENT-SCOPE line 22 only, and quotes FACTS line 4 as the different wording it is |
