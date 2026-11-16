# v19 map: every finding of the v18 reviews and where it is fixed in v19

Written Mon 16 Nov 2026. **Sheet** = OWNER-SHEET-v19.md (section number, rule id R1 to R10); **Note** = LEAD-RELEASE-NOTE-v3.md (G1 to G32 are its gates, "Note n" its section); **Open** = v19-OPEN-FOR-LEAD.md (item number). Id prefixes: SB = stranger blocker, SC = stranger contradiction, SM = stranger major, SQ = the stranger's two extra questions, XM = security major, XN = security nit, EM = evidence mismatch. "Fixed" means the text is written and the form check passes; nothing was run or seen working.

## 0. Failures first: findings not fully fixed, and why
| Item | State | Why | Next step |
|---|---|---|---|
| SB2 second way to reach the lead | PARTLY | the sheet now needs a second way the owner used before the run day, but only the lead can name one | Open 26; Note G31; no name, no run |
| XM4 lead-side stop | PARTLY | written as a duty and a gate; the timer or scheduled message is the lead's to set and to show | Open 27; Note G30 |
| SB4 what the take program does after a key cancel mid-run | NOT KNOWN | nobody has seen it | Open 28; Note G18; the sheet says type nothing, send the words |
| SM5 UNVERIFIED items | PARTLY | the sheet still marks the same unseen items; v19 adds a numbers message line listing items the lead has since seen | Note 3 template; Open 19 |
| SM11 run length, film pause | NOT MEASURABLE by the owner | the figures are the lead's; the sheet now says the alarm ends the run | Open 11 |
| SC-D From column on the raw recording | PARTLY | stated honestly in R9 (only the editor sees it and crops it); no way to hide the column is known | Open 29 |
| Sheet length (SQ-len) | NOT SHORTER | about 102 lines (v18: 98) and about 5,200 words (v18: about 4,250); every added line answers a finding | Open 30; v19-CHANGES.md |
| take program deletes contacts (v18 Open 1) | UNCHANGED | not in this checkout | Open 1; Note G1 stays NO |
| SB1 "real example" | the example is invented and its numbers are consistent, but the real wording of the notice, the printed result and the page words comes from the lead | the take program is not in this checkout | Note G17 |

## 1. Stranger review of v18, blockers and contradictions
| Id | Fixed where |
|---|---|
| SB1 numbers message only a template | Sheet 3: a full sample numbers message with consistent made-up numbers (balance 189, highest balance 200, program limit 13.21, times, counts), a sample notice and a sample printed result, and "Reading the counts" |
| SB2 no way to tell a fake first message, no second channel | Sheet 1 (message place = the chat where the sheet was received; second way), R8 (odd message: ask by the second way), 3 sample; Note G31; Open 26 |
| SB3 older key cancelled before the new key exists | Sheet R2 (b) (only if name and date match and the message says nothing uses it), 6.5 (a failed save leaves no older key and the sheet says why it is no loss), 5.8 yes line names it; Note G32; Open 2, 31 |
| SB4 R3 hard end against "touch nothing"; what happens after cancel | Sheet R3 (type nothing in the take window), 7.7, section 3 line "If you cancel the key during the run"; Note G18; Open 28 |
| SB5 "end" and counts never explained | Sheet 3 "Reading the counts"; R6 (what happens if `end` is not typed: the take program gives up after the minutes in the message); order table row 8 |
| SB6 window rules conflict (R6 / R10 / 7.7) | Sheet R6 is the one list of everything typed in WSL (take window, second window, once before the take program); R10 allows only `date -u` and `ls -l`; `echo $?` only in the take window once after the prompt returns (7.8) |
| SC-A R8 against "go", "n8n is off", "post" | Sheet R8 names exactly four words that start or end steps |
| SC-B R2, R10, R3 order | Sheet intro (precedence line), R10 last column |
| SC-C "do nothing is safe" against a live paid key | Sheet intro (before and after the key), order table rows 6 to 10 ("NOT safe") |
| SC-D receiver mail list in the film | Sheet R9 (raw recording shows the From column; the editor crops it; items (a) to (f)); Open 29 |

## 2. Stranger review of v18, majors and extra questions
| Id | Fixed where |
|---|---|
| SM1 "replaces all earlier sheets", "separate note" | Sheet intro ("Do not use any older sheet (v4 to v18)") |
| SM2 lead "never sees your screen" against R1 | Sheet 1 (lead: never sees the screen, can run commands as you, could read any file you can read) |
| SM3 "contact" and "key" several meanings | Sheet 1 (key list, key file, contact, contact id, person id defined; only model key and older key are "key") |
| SM4 HubSpot unexplained | Sheet 1 |
| SM5 UNVERIFIED nearly everywhere | Sheet 1 (the numbers message lists items seen since); Note 3 |
| SM6 money words | Sheet 1 (balance, highest balance, program limit, run total, usage page); "Backstop" and "Credit" removed; Note 0 (money words) |
| SM7 how to lower a too-high balance | Sheet R4 (you cannot; above your figure is no run unless you knowingly raise it), 3 check 6 |
| SM8 "head", "commit id", "checksum" | Sheet 1 (version id, fingerprint, `sha256sum`); R4 says "older version" |
| SM9 R4 "may spend before y" against the yes | Sheet R4, 5.8 (the yes says so and says the balance could be lost entirely) |
| SM10 silence minutes | Sheet 3 sample (3 min), 7.5, R10 |
| SM11 run length and film pause cannot be measured | Sheet 3 check 6 (the alarm ends the run); Note 2 |
| SM12 ls, grep, pgrep, ps outside R10's read list | Sheet R6 (the full list, split into take window, read-only second window, one write before the take program), R10 (only two during a FREEZE) |
| SM13 5.4 deletes mails before the clean-up message | Sheet R7 (the earlier demo mails of 5.4 by the subject start in the numbers message), 5.4 |
| SM14 retry after a failed save can pass the latest start | Sheet 6.5 (a new numbers message with new times; latest start passed: no run), R3 |
| SM15 pasting twice gives an error, not `exit 0` | Sheet 6.4 (paste once), 6.5 (an existing-file error counts as failure) |
| SM16 6.6 cannot show which key loaded | Sheet 6.6 (says so), 8.1 (last-used times) |
| SM17 "(good here)" | Sheet 7.3 ("wanted here: the take program could sign in to both") |
| SM18 "run started" destination | Sheet 7.4 (to the lead in the message place) |
| SM19 7.7 seven actions | Sheet 7.7 (end, then R3) and 7.8 (reading) |
| SM20 8.1 format | Sheet 8.1 ("name \| last used time" per key) |
| SM21 8.5 eight forbidden items | Sheet R9 items (a) to (f); 8.5 points to them |
| SM22 "Take program last start" against "Latest start" | Sheet 1 ("Program's last start"), 3 sample, check 4; Note 2 |
| SM23 "window end" two meanings | Sheet R4 ("end-date setting" for the program's own setting); glossary keeps one meaning |
| SM24 "printed forms", "REAL run", person id against contact id, exit code | Sheet 1 (person id, exit code), 3 sample (REAL run explained), R6 (exact forms) |
| SM25 Recall location | Sheet 6.1 |
| SQ-len length | Open 30; v19-CHANGES.md |

## 3. Security review of v18
| Id | Fixed where |
|---|---|
| XM1 R4 checked at 5.6 before the older key is cancelled | Sheet R4 (three moments: 5.6 older key allowed, after 6.2, at 7.1), 6.2, 7.1 |
| XM2 typo in the key name | Sheet R2 (a) (any key you created today after starting section 6, whatever its name) |
| XM3 clipboard until 6.6; `ps` and `pgrep` print command lines; cancelled word fallback | Sheet 6.4 (clipboard replaced right after `exit 0`), R1 (a secret-looking text in a printed line), R3 step 2 (a key no longer listed counts as cancelled) |
| XM4 lead-side stop after the window end | Sheet R3 (last sentence); Note G30, 4; Open 27 |
| XM5 real exposure is the whole balance; sample showed 189 against 20 | Sheet R4, 5.8, 3 sample (balance 189, highest 200); Note G14 |
| XM6 charset allows `&` and spaces in shell values | Sheet R8 (shell values: letters, digits, `. _ / -`, not starting with `-`, paths start with `/`; other typed values may add spaces and `: = @ + ,`) |
| XM7 end then R3 at once | Sheet 7.7, R3 |
| XM8 alarm formula leaves out the owner's minutes | Sheet 1 (alarm time), 3 sample and check 3 and 4; Note 2, G10 |
| XN1 older-key sentence not in the yes line | Sheet 5.8; Note G25 |
| XN2 "on the run date" against 23 Nov | Sheet 3 check 2 (cancel-by not later than window end); Note 2 second example |
| XN3 `@example.com` against the take-prep contact | Sheet R7; Note G13, G27 (the take-prep contact is on the list and ends `@example.com`) |
| XN4 `grep -F` substring | Sheet 5.7 and R6 (anchored `grep "^<setting name>="`, names hold letters, digits, `_`) |
| XN5 R9 mixed film and charset | Charset moved to R8; R9 is film only |
| XN6 say bash | Sheet 1 (WSL uses bash), 6.4 |
| XN7 expected counts must not change after `y` | Sheet R6, 3 sample |
| XN8 "put back" Recall | Sheet 5.3, 6.1 (write down values), 8.4 (back to those values) |

## 4. Evidence runner summary of v18
| Id | Fixed where |
|---|---|
| EM1 post-by time has a source | Sheet 9 (no UNVERIFIED label); Note 2 (ORDERS.md line 150, OWNER-STEPS-realrun-v3.md line 130, QUESTIONS.md line 55), G24 (source item removed); Open 20 |
| EM2 map row RC-5 pointed to Open 24 | The v18 row is replaced: length is now Open 30 and v19-CHANGES.md; no v19 row points to a number that does not say it |
| EM3 "US$180 of 189 in-code backstop" exact only in FACTS line 3 | Note 2 (FACTS line 3 and AGENT-SCOPE line 15 quoted separately); Open 6 |
| EM4 Note wording "a made-up sales contact sent twice" against decision 1 | Note 5 (decision 1 wording: "a lead sent twice with the same id is processed once") |
| EM5 DECISION-one-store line 14 against its CORRECTIONS (a), lines 25 and 26 | Note 0 item 3, G20; Open 21 |

## 5. The brief's key items
| Id | Fixed where |
|---|---|
| K1 a real example numbers message with consistent numbers | Sheet 3 sample |
| K2 second channel for odd lead messages | SB2 |
| K3 older key check order (R4 after 6.2 and at 7.1) | XM1 |
| K4 R2 typo-key rule | XM2 |
| K5 clipboard cleared right after exit 0 | XM3 |
| K6 cancelled-word fallback | XM3 |
| K7 lead-side duty at alarm time and by 18:29 UTC | XM4 |
| K8 real exposure = whole prepaid balance | XM5 |
| K9 R9 charset | XM6 |
| K10 type end, then immediately R3 | XM7 |
| K11 alarm formula with the owner's y and setup minutes | XM8 |
| K12 explain count words | SB5 |
| K13 R6, R10, 7.7 window rule conflict | SB6 |
| K14 R8 against "go" | SC-A |
| K15 "do nothing is safe" against a live key | SC-C |
| K16 receiver mail list in the film | SC-D |
| K17 money words | SM6 |
| K18 head, commit id, checksum in plain words | SM8 |
| K19 commands outside R10's read list | SM12 |
| K20 say bash | XN6 |
| K21 anchored grep | XN4 |
| K22 sheet length | Open 30 |
