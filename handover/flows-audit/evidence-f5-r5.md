# evidence-f5-r5: raw output for RUNSHEET-WORDING.md round 5 (EVIDENCE RUNNER; no judging)
Run 2026-11-16 about 10:12 UTC (15:42 IST). Subject mtime 10:11:32 UTC; CLAIMS-TABLE.md mtime 10:11:33 UTC (both changed during the run window).

## FAILURES AND SURPRISES (first)
1. check_runsheet_paste.py with CLAIMS-TABLE.md now exits 1 (FAIL): 73 claim ids marked UNSUPPORTED/OVERSTATED/DELETE/STALE, B-219 has no row in RUNSHEET-WORDING.md. fix-f5-r5.md reports 71 and PASS. Cause seen: B-219 is OVERSTATED in the current CLAIMS-TABLE.md (line 716) but SUPPORTED in the saved r4 copy (CLAIMS-r4.bak line 689); run against that r4 copy the checker gives 71 / PASS. So CLAIMS-TABLE.md changed after the r5 build (206924 bytes now; r4 copy 189748 bytes).
2. Without the CLAIMS-TABLE.md argument the checker crashes (IndexError, argv[1] absent); with only the runsheet argument it passes its row checks (see part 1). The fix-f5 note shows no argument form.
3. Line cites: the r5 file cites CLAIMS-TABLE.md lines 12, 29, 30, 32, 40, 72, 73, 74, 77, 78, 79, 80, 81, 261. In the CURRENT CLAIMS-TABLE.md none of the cited lines holds the claimed text (a "Scope 2026-11-16" block was added near the top and shifted the file). In the saved r4 copy every one of them points at the claimed text (part 5). Note: a plain "lines 262 to 758" range at line 15 and a cite "line 40" (see part 5) are listed too.
4. Changed rows NOT mentioned in fix-f5-r5.md by id: 23 (list in part 2; 5 of them have a changed PASTE cell: A-001, A-016e, N-5a, N-5b, A-050c? see cell indexes; A-051b, V-41 and A-023a rows changed paste or note cells). Row ids matched by whole-token search of fix-f5-r5.md; lettered ids (A-016b) count as unmentioned if the file says only "A-016a/b/c" style, so read the list, do not trust the count blindly.
5. My row parse counts every table row with the id cell (165 ids in r5, 147 in r4, incl. header-like rows of the small tables); the checker counts 150 paste rows. Both numbers are printed.

## PART 1: tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md (exit code 1)
section '1': 38 rows
section '2': 17 rows
section '3': 54 rows
section '7': 41 rows
total rows: 150
claim ids marked UNSUPPORTED, OVERSTATED, DELETE or STALE in CLAIMS-TABLE.md: 73 | with no row here: ['B-219']
claim ids marked UNTRACED there: 68 | with no row here: 58 (scope: UNTRACED claims have no safe wording, so they get a row only when a file sentence had to change)
FAIL: claim ids missing
RESULT: FAIL

Same checker against the saved r4 copy of CLAIMS-TABLE (CLAIMS-r4.bak):
section '1': 38 rows
section '2': 17 rows
section '3': 54 rows
section '7': 41 rows
total rows: 150
claim ids marked UNSUPPORTED, OVERSTATED, DELETE or STALE in CLAIMS-TABLE.md: 71 | with no row here: []
claim ids marked UNTRACED there: 69 | with no row here: 58 (scope: UNTRACED claims have no safe wording, so they get a row only when a file sentence had to change)
RESULT: PASS
(exit 0)
No-argument call tail: IndexError: list index out of range (argv[1])

## PART 2: row diff r4 (RUNSHEET-r4.bak) vs r5
r4 row ids 147 r5 row ids 165 identical 101 changed 44 removed 2 added 20

== CHANGED rows NOT mentioned in fix-f5-r5.md (id-token match; letter suffix stripped as fallback) == 23
A-001
  r4: | A-001 | R:4 | "real mail service and real CRM service in scenes 1 to 5 (made-up people only)" | "Scenes 1 to 4 use a real mail service and a real CRM service, with made-up people only. Scene 5 uses a stand-in CRM." | FILE EDIT | F-006, F-003. Scene 5 runs on film-v5, where the CRM step calls the stand-in web address (MF_CRM_URL; re-read this round). |
  r5: | A-001 | R:4 | "real mail service and real CRM service in scenes 1 to 5 (made-up people only)" | "Scenes 1 to 4 use a real mail service and a real CRM service, with made-up people only." | FILE EDIT | F-006, F-003. Round 5: the second sentence (Scene 5 uses a stand-in CRM) is cut from this video by lead decision 2026-11-16 item 1; it is kept as row A-001L in section 7. |
A-005
  r4: | A-005 | R:8 | "All people in the take are made up (addresses only on example.test)." | "All leads in this recording are made-up people with made-up e-mail addresses." | FILE EDIT | F-029. In this row and in A-084 address always means e-mail address. The lead e-mail addresses in scenes 5 to 10 are on example.test (CHECKED in the film flow JSON for the constants). For scenes 1 to 4 the real flows 
  r5: | A-005 | R:8 | "All people in the take are made up (addresses only on example.test)." | "All leads in this recording are made-up people with made-up e-mail addresses." | FILE EDIT | F-029. In this row and in A-084 address always means e-mail address. For scenes 1 to 4 the real flows send the lead mail to a placeholder e-mail address that the coordinator fills in (B-154), so that all lead e-mail a
A-087a
  r4: | A-087a | R:23 (last sentence) | "At 45 s the estimate is roughly 70 to 75 s: for planning the sped-up cut only, never a caption number." | "At 45 s the estimate is about 62 s: for planning the sped-up cut only, never a caption number." | FILE EDIT | F-003. One stop point only (K1: 5 runs, longest 61.9 s, relayed from older flows, not seen by us). The earlier pooled range of K1 and K2 is gone (ru
  r5: | A-087a | R:23 (last sentence) | "At 45 s the estimate is roughly 70 to 75 s: for planning the sped-up cut only, never a caption number." | "At 45 s the estimate is about 62 s: for planning the sped-up cut only, never a caption number." | FILE EDIT | F-003. One stop point only (K1: 5 runs, longest 61.9 s, relayed from older flows, not seen by us). The earlier pooled range of K1 and K2 is gone (ru
A-087b
  r4: | A-087b | R:33 (time cell) | "planning guess about 70 to 75 s" | "planning guess about 62 s" | FILE EDIT | Same facts and condition as A-087a (D2). |
  r5: | A-087b | R:33 (time cell) | "planning guess about 70 to 75 s" | "planning guess about 62 s" | FILE EDIT | Same facts and condition as A-087a (D2). Default while D2 is open: A-087d. |
A-084
  r4: | A-084 | R:30 | "No address on screen except example.test." | "Real mailbox e-mail addresses are cropped or hidden in the recording. The only e-mail address left on screen is on example.test." | FILE EDIT | F-029. Replacement line for the run sheet; the cropping itself is step 3 and step 18 in section 0b. Web addresses (the browser address bar, n8n page addresses with ports) are not covered by th
  r5: | A-084 | R:30 | "No address on screen except example.test." | "Real mailbox e-mail addresses are cropped or hidden in the recording. The only e-mail address left on screen is on example.test." | FILE EDIT | F-029. Replacement line for the run sheet; the cropping itself is steps 3 and 11 in section 0c. Web addresses (the browser address bar, n8n page addresses with ports) are not covered by this s
A-016b
  r4: | A-016b | R:32 (scene 3) | (no sentence today) | "One CRM row, one e-mail message." | VOICE, scene 3 (added in the edit, step 19) | W-17, post-edit insert. Spoken only after you read the CRM list and the mailbox in this recording and they show exactly 1 CRM row and 1 e-mail message. If they show anything else, speak nothing and tell the coordinator. |
  r5: | A-016b | R:32 (scene 3) | (no sentence today) | "One CRM row, one e-mail message." | VOICE, scene 3 (added in the edit, step 10) | W-17, post-edit insert. Spoken only after you read the CRM list and the mailbox in this recording and they show exactly 1 CRM row and 1 e-mail message. If they show anything else, speak nothing and tell the coordinator. |
A-016c
  r4: | A-016c | R:32 (scene 3) | "Caption: "a lead sent twice with the same id is processed once"" | "The same lead ID sent twice: one CRM row and one e-mail message in this recording." | SCREEN, scene 3 (added in the edit, step 19) | F-002. The old caption said processed once, which reads as a general promise. The file n8n-published-numbers.md (B-195) reports, for its variant a, ten leads at once endi
  r5: | A-016c | R:32 (scene 3) | "Caption: "a lead sent twice with the same id is processed once"" | "The same lead ID sent twice: one CRM row and one e-mail message in this recording." | SCREEN, scene 3 (added in the edit, step 10) | F-002. The old caption said processed once, which reads as a general promise. The file n8n-published-numbers.md (B-195) reports, for its variant a, ten leads at once endi
A-016e (extra)
  r4: | A-016e (extra) | R:41 line 1 | "Line 1, claim: a lead sent twice with the same id is processed once." | "Line 1, one test: the same lead ID sent twice gave one CRM row and one e-mail message in this recording." | CARD line 1 | Same condition as A-016c: read the CRM list and the mailbox in the recording first; otherwise delete card line 1 and tell the coordinator. The old line said processed once
  r5: | A-016e (extra) | R:41 line 1 | "Line 1, claim: a lead sent twice with the same id is processed once." | "One test: the same lead ID sent twice gave one CRM row and one e-mail message in this recording." | CARD line 1 (the words Line 1 are not printed) | Same condition as A-016c: read the CRM list and the mailbox in the recording first; otherwise leave card line 1 out and tell the coordinator. Th
N-5a (new)
  r4: | N-5a (new) | R:33 and scenes 4, 5, 9 | label "setting: lease 45 s" | "n8n lets another run take over a lead that stopped only after 45 seconds. We call this wait the lease. A check that runs every 30 seconds does the takeover, so the lead is picked up at the first check after the lease ends." | VOICE, scene 4, once | W-07. Explains the label before it appears. Round 4: the old string said n8n wa
  r5: | N-5a (new) | R:33 and scene 4 | label "setting: lease 45 s" | "n8n lets another run take over a lead that stopped only after 45 seconds. We call this wait the lease. A check that runs every 30 seconds does the takeover, so the lead is picked up at the first check after the lease ends." | VOICE, scene 4, once | W-07. Round 5: scene 4 only (scenes 5 and 9 are in section 7). Explains the label befo
N-5b (new)
  r4: | N-5b (new) | scenes 4, 5, 9 | label "setting: lease 45 s" | "setting: lease 45 s" | SCREEN, scenes 4, 5 and 9 | Keep the label. |
  r5: | N-5b (new) | scene 4 | label "setting: lease 45 s" | "setting: lease 45 s" | SCREEN, scene 4 | Keep the label. Round 5: scene 4 only; the copy for scenes 5 and 9 is N-5c in section 7. |
A-050c
  r4: | A-050c | R:41 line 2 | (voice) | "When a lead ends unknown, the alert gives the lead ID. Someone has to look at the lead in the table and decide, outside this flow, whether the mail has to be sent again. The flow does not record what they decide." | VOICE, scene 12 | M1. Round 3: no run count in the voice sentence. Same sentence as A-036b and N-1. |
  r5: | A-050c | R:41 line 2 | (voice) | "When a lead ends unknown, the alert gives the lead ID. Someone has to look at the lead in the table and decide, outside this flow, whether the mail has to be sent again. The flow does not record what they decide." | VOICE, scene 12 (not spoken by default: this video has no unknown-lead or alert scene) | M1. Round 3: no run count in the voice sentence. Same sente
A-051b
  r4: | A-051b | R:41 line 3 | same | "Line 3, recovery: in earlier tests on similar test flows, 5 runs recovered a stopped lead in a median of 60.8 seconds and at most 61.9 seconds. The source is another test session; we have not seen its raw files." | CARD line 3 | Only if D1 is yes and D2 is confirmed. Source: K1, 5 runs, relayed. |
  r5: | A-051b | R:41 line 3 | same | "Recovery: in earlier tests on similar test flows, 5 runs recovered a stopped lead in a median of 60.8 seconds and at most 61.9 seconds. The source is another test session; we have not seen its raw files." | CARD line 3 (the word Line 3 is not printed) | Only if D1 is yes and D2 is confirmed. Source: K1, 5 runs, relayed. |
V-41 (extra, W-02 gap)
  r4: | V-41 (extra, W-02 gap) | R:41 line 4 | "Line 4, alerts: v3 sent two alerts on a slow alert send (lane3 3 of 3); v4 one (lane3 n=3 plus laptop 1, relayed)" | "Line 4, alerts: when the mail server held its answer for 90 seconds, version 3 sent two alerts in 3 of 3 runs. Version 4 sent one alert in each of 4 runs. These counts were reported by another test session; we have not seen its raw files. T
  r5: | V-41 (extra, W-02 gap) | R:41 line 4 | "Line 4, alerts: v3 sent two alerts on a slow alert send (lane3 3 of 3); v4 one (lane3 n=3 plus laptop 1, relayed)" | "Alerts: when the mail server held its answer for 90 seconds, version 3 sent two alerts in 3 of 3 runs. Version 4 sent one alert in each of 4 runs. These counts were reported by another test session; we have not seen its raw files. The alert
A-023a
  r4: | A-023a | R:90 | "Alert after a crash during the alert send: up to 13 min late (n=2)." | "In one test reported by another test session (2 runs, raw files not seen by us), when n8n stopped while sending the alert, the alert arrived about 13 minutes late. It was not lost in those 2 runs." | CARD line 4, second part | F-014, W-20. 720 s is read from the flow; 780 s and 2 runs are RELAYED (HB189). No
  r5: | A-023a | R:90 | "Alert after a crash during the alert send: up to 13 min late (n=2)." | "In one test reported by another test session (2 runs, raw files not seen by us), when n8n stopped while sending the alert, the alert arrived about 13 minutes late. It was not lost in those 2 runs." | CARD line 4, second part | F-014, W-20. 720 s is read from the flow; 780 s and 2 runs are RELAYED (HB189). No
N-8 (new, ORDER 019)
  r4: | N-8 (new, ORDER 019) | between scene 4 and scene 5 (the run sheet has no line for it) | (no sentence today) | NO PASTE | FILE EDIT (run sheet, rehearsal list and take-day checks) | ORDER 019, SCENE-FLOW-MAP C1. The numbered steps are step 9 (9.1 to 9.6) in section 0b, all COORDINATOR. Not a viewer sentence; not a studio owner step. Start commands and ports are read (nothing run): crm_stub.py POR
  r5: | N-8 (new, ORDER 019) | between scene 4 and scene 5 (the run sheet has no line for it) | (no sentence today) | NO PASTE | FILE EDIT (run sheet, rehearsal list and take-day checks) | ORDER 019, SCENE-FLOW-MAP C1. The numbered steps are L-9.1 to L-9.6 above, all COORDINATOR. Not a viewer sentence; not a studio owner step. Round 5: the round 4 sentence that run_mf.py starts all three stand-ins was w
line 2 (history of the stop tests)
  r4: | line 2 (history of the stop tests) | A-050a, then A-050b | condition D2 |
  r5: | line 2 (history of the stop tests) | A-050a, then A-050b | Left out while D2 is open. |
line 3 (recovery)
  r4: | line 3 (recovery) | A-051a (default), or A-051b if D1 is yes and D2 is confirmed | D1 |
  r5: | line 3 (recovery) | A-051a (default), or A-051b if D1 is yes and D2 is confirmed | A-051a. |
line 4 (alerts)
  r4: | line 4 (alerts) | V-41, then A-023a | condition D2 |
  r5: | line 4 (alerts) | V-41, then A-023a | Left out while D2 is open. |
line 5 (what we keep)
  r4: | line 5 (what we keep) | A-053 | condition P2 |
  r5: | line 5 (what we keep) | A-053 if P2 is confirmed | A-053b. |
line 6 (not tested, and the review row)
  r4: | line 6 (not tested, and the review row) | A-091, then N-3 | N-3 is also said once in voice before the video if the coordinator wants it |
  r5: | line 6 (not tested, and the review row) | A-091, then N-3 | Both are used (no decision holds them). |
B-017
  r4: | B-017 | PLAN:43 | "Independent CRM count and archive ... HubspotCrm.rows_with_prefix(L), archive_all ... reused as is" | NO PASTE | FILE EDIT (no wording change) | No wording change, reason: UNTRACED (the code is not in this checkout), so there is no true sentence to put in its place. Do not use it as a fact. P4c: until it is read, nothing may say the script archives or deletes the contacts. |
  r5: | B-017 | PLAN:43 | "Independent CRM count and archive ... HubspotCrm.rows_with_prefix(L), archive_all ... reused as is" | NO PASTE | FILE EDIT (no wording change) | No wording change, reason: UNTRACED (the code is not in this checkout), so there is no true sentence to put in its place. Do not use it as a fact. Round 5: lead decision 2026-11-16 item 2 says the take identity is read-only and the ta
B-182
  r4: | B-182 | n8n-owns-vs-desk-owns.md:4 | "n8n owns (stated by the lead): intake, field mapping, the ten-at-once trigger, alerts, and plain sends in client builds." | "n8n receives the leads, maps the fields, keeps the one-row-per-lead claim, sends the lead mail and the alert mail." | FILE EDIT | 'Ten-at-once trigger' dropped: no node is that. |
  r5: | B-182 | n8n-owns-vs-desk-owns.md:4 | "n8n owns (stated by the lead): intake, field mapping, the ten-at-once trigger, alerts, and plain sends in client builds." | "n8n receives the leads, maps the fields, keeps the one-row-per-lead claim, sends the lead mail and the alert mail." | FILE EDIT | 'Ten-at-once trigger' dropped: no node is that. In the old sentence the lead means the Claude session tha
B-214
  r4: | B-214 | flows-audit/inputs/OWNER-STEPS-realrun-v3.md:103 | "Only the exact word end ends the pause ... the second wrong line also prints type exactly: end and then the script goes ahead and archives anyway; ... Ctrl-C or closing the window also still archives." | NO PASTE | FILE EDIT (no wording change) | No wording change, reason: UNTRACED (the script is absent); compare PLAN:111 (archive in a 
  r5: | B-214 | flows-audit/inputs/OWNER-STEPS-realrun-v3.md:103 | "Only the exact word end ends the pause ... the second wrong line also prints type exactly: end and then the script goes ahead and archives anyway; ... Ctrl-C or closing the window also still archives." | NO PASTE | FILE EDIT (no wording change) | No wording change, reason: UNTRACED (the script is absent); compare PLAN:111 (archive in a 

== CHANGED rows mentioned == 21
A-008a, A-012, A-017a, A-026a, A-026b, A-033a, A-033c, A-035, A-040, A-041, B-085, A-042, A-050b, A-051a, A-053, A-091, A-057, B-067, B-091, B-145, B-215

== REMOVED ids == ['line 1 (claim)', 'X-5']

== ADDED ids == ['decision or check', 'D1 (recovery number on screen or page)', 'D2 (relayed figures; medians 60.8 s and 60.9 s unconfirmed)', 'P2 (saving of runs on)', 'P4a (real CRM answers an all-digit id)', 'P4b (n8n data store)', 'P4c (leftover contacts)', 'F-001 (alert columns, not applied)', 'Q-F (does the video end with the closing card)', 'A-087c (default for A-087a)', 'A-087d (default for A-087b)', 'A-053b (default for A-053)', 'line 1 (one test)', 'X-5a (new)', 'X-5b (default for X-5a)', 'A-001L', 'N-5c (later copy of N-5b)', 'A-040b (second sentence of A-040)', 'A-041b (second sentence of A-041)', 'B-085b (second sentence of B-085)']

== added ids not mentioned in fix: ['decision or check', 'D1 (recovery number on screen or page)', 'D2 (relayed figures; medians 60.8 s and 60.9 s unconfirmed)', 'P2 (saving of runs on)', 'P4a (real CRM answers an all-digit id)', 'P4b (n8n data store)', 'P4c (leftover contacts)', 'A-087c (default for A-087a)', 'A-087d (default for A-087b)', 'A-053b (default for A-053)', 'line 1 (one test)', 'X-5b (default for X-5a)', 'N-5c (later copy of N-5b)', 'A-040b (second sentence of A-040)', 'A-041b (second sentence of A-041)', 'B-085b (second sentence of B-085)']

== For each changed row (all 44): which cells changed (cell index 0-based) and whether fix-f5-r5.md mentions the id ==
A-001                                      cells [3, 5] mentioned=no
A-005                                      cells [5] mentioned=no
A-087a                                     cells [5] mentioned=no
A-087b                                     cells [5] mentioned=no
A-008a                                     cells [5] mentioned=yes
A-084                                      cells [5] mentioned=no
A-012                                      cells [5] mentioned=yes
A-016b                                     cells [4] mentioned=no
A-016c                                     cells [4] mentioned=no
A-016e (extra)                             cells [3, 4, 5] mentioned=no
A-017a                                     cells [5] mentioned=yes
N-5a (new)                                 cells [1, 5] mentioned=no
N-5b (new)                                 cells [1, 4, 5] mentioned=no
A-026a                                     cells [5] mentioned=yes
A-026b                                     cells [5] mentioned=yes
A-033a                                     cells [5] mentioned=yes
A-033c                                     cells [5] mentioned=yes
A-035                                      cells [3, 5] mentioned=yes
A-040                                      cells [3, 5] mentioned=yes
A-041                                      cells [3, 5] mentioned=yes
B-085                                      cells [3, 5] mentioned=yes
A-042                                      cells [5] mentioned=yes
A-050b                                     cells [3, 5] mentioned=yes
A-050c                                     cells [4, 5] mentioned=no
A-051a                                     cells [3, 4, 5] mentioned=yes
A-051b                                     cells [3, 4] mentioned=no
A-053                                      cells [3, 4, 5] mentioned=yes
A-091                                      cells [3, 4, 5] mentioned=yes
V-41 (extra, W-02 gap)                     cells [3, 4, 5] mentioned=no
A-023a                                     cells [5] mentioned=no
N-8 (new, ORDER 019)                       cells [5] mentioned=no
line 2 (history of the stop tests)         cells [2] mentioned=no
line 3 (recovery)                          cells [2] mentioned=no
line 4 (alerts)                            cells [2] mentioned=no
line 5 (what we keep)                      cells [1, 2] mentioned=no
line 6 (not tested, and the review row)    cells [2] mentioned=no
A-057                                      cells [5] mentioned=yes
B-017                                      cells [5] mentioned=no
B-067                                      cells [3, 4, 5] mentioned=yes
B-091                                      cells [3, 4, 5] mentioned=yes
B-145                                      cells [3] mentioned=yes
B-182                                      cells [5] mentioned=no
B-214                                      cells [5] mentioned=no
B-215                                      cells [3, 5] mentioned=yes

## PART 3: rows for claim ids marked UNSUPPORTED/OVERSTATED/DELETE/STALE
Count in CLAIMS-TABLE.md now: 73 ids; rows present in r5: 72; missing: B-219. (Counting by A-/B- number, letters ignored, as the checker does.)
Count against r4 copy of CLAIMS-TABLE: 71 ids; missing: none.

## PART 4: banned phrases and paste-cell characters
grep -ci counts (lines containing the phrase, whole file): one database 3 | approval 4 | audit trail 2 | paste-ready 1
5:Status: round 5 (the last round; the cap allows no review after it). Round 5 inputs: review-runsheet-wording-r5-facts.md, review-runsheet-wording-r5-reader.md and input
110:1. No "one database" anywhere in a paste cell. Where n8n's own storage must be named: "n8n keeps its own records". Script check: the three banned phrases (one databas
111:2. No "approval" and no "audit trail" in any paste string. The narrow statement is only what the recording shows: the same lead ID sent twice gave one CRM row and one
253:| B-189 | n8n-owns-vs-desk-owns.md:26-29 | "a receipt written before anything else happens, a keyed claim ..., ambiguous sends marked for a person, the portal, approv
255:| B-183 | n8n-owns-vs-desk-owns.md:5 | "...ambiguous sends marked for a person, approval, its own counts, ..." (replace exactly the part from ambiguous to counts) | "
268:| X-5a (new) | flows-audit/inputs/DECISION-one-store.md:14 | "ONE database for everything we own: the single Postgres instance of the take (one container, one engine)
269:| X-5b (default for X-5a) | flows-audit/inputs/DECISION-one-store.md:14 | "ONE database for everything we own: the single Postgres instance of the take (one container
Inside quoted paste cells (4- and 6-cell rows, 150 rows incl. NO PASTE/DELETE): banned words 0; apostrophe, backtick, pipe or extra double quote inside a paste string 0; paste cell not exactly one quoted string/NO PASTE/DELETE 0.
Line 5 paste-ready hit is the status paragraph; hit at 110 and 111 are the rule text; 253, 255, 268, 269 are in the original-sentence column, not in the Paste-this column.

## PART 5: every CLAIMS-TABLE.md line cite in RUNSHEET-WORDING.md (cited line now, first 120 chars; and same line in the r4 copy, first 60 chars)
RS:23 cites CT:30 | NOW: **What failed or was not checked (read this first).** | IN r4 COPY: - The owner (the person who films and posts the video) does 
RS:23 cites CT:40 | NOW: **Rows and scenes that can break the take (short list).** Each depends on a check or decision below. Items marked OUT OF | IN r4 COPY: 6. Deleting leftover HubSpot contacts by hand in the HubSpot
RS:24 cites CT:29 | NOW:  | IN r4 COPY: - The coordinator settles D1, D2 and D3 (decisions, below), 
RS:24 cites CT:32 | NOW: - 69 of the 327 claims are RELAYED-ONLY: they rest on a number that another session sent us and whose raw file is not in | IN r4 COPY: - The laptop agent (the session on the take laptop) runs the
RS:39 cites CT:72 | NOW: **Glossary (the labels and words used in this file; a few are used above before they are explained here).** | IN r4 COPY: - D1: put a recovery number on screen or on the card? Defaul
RS:40 cites CT:73 | NOW: - Files read. Lane A (run sheet and page statements): VIDEO-RUNSHEET.md and PAGE-STATEMENTS-V4.md. Lane B (plans, notes, | IN r4 COPY: - D2: confirm the final per-kill medians (K1 60.8 s and max 
RS:41 cites CT:74 | NOW: - Lane A and lane B are the two reading passes below. Lane A ids are A-001 to A-098 (A-056 unused, so 97 claims). Lane B | IN r4 COPY: - D3: the alert mail's own text says "A person decides", whi
RS:42 cites CT:77 | NOW: - D1 to D3: three decisions the coordinator makes (listed below under "Decisions"): D1 = whether a recovery time goes on | IN r4 COPY: - P1: rehearsal step 3 (VIDEO-RUNSHEET.md:64): the laptop ag
RS:43 cites CT:78 | NOW: - Test and kill labels (the names used by mf.py, the test runner in the demo folder; mf.py:151-164): K1, K2, K3, K3B = t | IN r4 COPY: - P2: F-008 applied, the 8 flow files rebuilt, saving ON con
RS:44 cites CT:79 | NOW: - Earlier test series by other sessions: lane3 (older film flows, 18 kill runs at lease 45 s), V7 (v3 flows, lease 20 s) | IN r4 COPY: - P4a (the id HubSpot gives each contact): with ONE made-up 
RS:45 cites CT:80 | NOW: - Parts of the system: "desk" = the studio's earlier lead-desk program (its repository is not in this checkout). "Stage" | IN r4 COPY: - P4b (n8n database): list the files in the take's n8n data 
RS:46 cites CT:81 | NOW: - File keys for the lanes: R = VIDEO-RUNSHEET.md; P = PAGE-STATEMENTS-V4.md; and the other names in the index by file be | IN r4 COPY: - P4c (clean-up): after the take, count the made-up contacts
RS:56 cites CT:78 | NOW: - Test and kill labels (the names used by mf.py, the test runner in the demo folder; mf.py:151-164): K1, K2, K3, K3B = t | IN r4 COPY: - P2: F-008 applied, the 8 flow files rebuilt, saving ON con
RS:67 cites CT:78 | NOW: - Test and kill labels (the names used by mf.py, the test runner in the demo folder; mf.py:151-164): K1, K2, K3, K3B = t | IN r4 COPY: - P2: F-008 applied, the 8 flow files rebuilt, saving ON con
RS:67 cites CT:80 | NOW: - Parts of the system: "desk" = the studio's earlier lead-desk program (its repository is not in this checkout). "Stage" | IN r4 COPY: - P4b (n8n database): list the files in the take's n8n data 
RS:145 cites CT:261 | NOW: ## Node facts checked in text, used below (quoted from the built JSON or BM) | IN r4 COPY: | A-012 | R:31 | "table row state done, mail_sent true; CRM 
RS:145 cites CT:79 | NOW: - Earlier test series by other sessions: lane3 (older film flows, 18 kill runs at lease 45 s), V7 (v3 flows, lease 20 s) | IN r4 COPY: - P4a (the id HubSpot gives each contact): with ONE made-up 
RS:268 cites CT:12 | NOW: 7. Also live, text only: rows 1, 2, 4, 5, 17, 21, 22, 32, 79. Rows 9 and 22 only delete a recovery caption from scene 4; | IN r4 COPY: - n8n runs on its own database today (a small SQLite file). 
RS:269 cites CT:12 | NOW: 7. Also live, text only: rows 1, 2, 4, 5, 17, 21, 22, 32, 79. Rows 9 and 22 only delete a recovery caption from scene 4; | IN r4 COPY: - n8n runs on its own database today (a small SQLite file). 
RS:272 cites CT:30 | NOW: **What failed or was not checked (read this first).** | IN r4 COPY: - The owner (the person who films and posts the video) does 
Range cite at RS line 15 (CT lines 262 to 758): CT:262 now starts '- Lease: interval 45 seconds ...'; CT:758 'Source of the done facts...'.
