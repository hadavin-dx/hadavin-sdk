# Evidence run, claims r8 (EVIDENCE RUNNER: raw output, no judgement)
Work copy: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/claimev8/flows-audit (copy of handover/flows-audit, unmodified)

## FAILURES FIRST
1. `python3 claims-count.py` with NO argument: rc=1, IndexError (script needs the table path as argument). Re-run with `CLAIMS-TABLE.md`: rc=0.
2. CLAIMS-TABLE.md lines 814-821 ("Part 7: counts", lane B table) state SUPPORTED 80, RELAYED 45, UNSUPPORTED 12, OVERSTATED 30, UNTRACED 63 (total 230). My own count of lane B + X rows: SUPPORTED 90, RELAYED 45, UNSUPPORTED 16, OVERSTATED 35, UNTRACED 44 (total 230). The table text differs in four of five verdicts (totals agree). Line 151 says lane B has 44 untraced (matches my count, contradicts line 820's 63).
3. CLAIMS-TABLE.md lines 414-420 (lane A block): 34/24/13/19/7 total 97: matches my lane A count.
4. Strings: 'coordinator confirms' hits 1 time (CLAIMS-TABLE.md:87). Others: see section 3.

## 1. Commands and exit codes
- `python3 tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md` rc=0. Output:
  section '1': 38 rows | '2': 17 | '3': 61 | '7': 41 | total rows: 157
  claim ids marked UNSUPPORTED, OVERSTATED, DELETE or STALE in CLAIMS-TABLE.md: 80 | with no row here: []
  claim ids marked UNTRACED there: 50 | with no row here: 43
  RESULT: PASS
- `find . -name 'claims-count*'` -> ./claims-count.py
- `python3 claims-count.py` (no argument) rc=1, IndexError at line 59 (sys.argv[1]).
- `python3 claims-count.py CLAIMS-TABLE.md` rc=0. Output:
  verdicts: {'UNSUPPORTED': 29, 'SUPPORTED': 124, 'UNTRACED': 51, 'OVERSTATED': 54, 'RELAYED-ONLY': 69} total 327
  lanes (A, B incl. X): {'A': 97, 'B': 226, 'X': 4}   [claims-count.py labels B 226 and X 4 separately]
  to-do rows: 87 | offenders: 0 [] | ids: 327 unique: 327

## 2. My own count (script /tmp/.../claimev8/count.py, first verdict phrase of cell 6, 7 cells per row)
Total rows 327, unique ids 327, non-parsed rows none.
SUPPORTED 124, RELAYED-ONLY 69, OVERSTATED 54, UNSUPPORTED 29, UNTRACED 51. Lanes: A 97, B 226, X 4.
Per lane: A = SUPPORTED 34, RELAYED 24, OVERSTATED 19, UNSUPPORTED 13, UNTRACED 7 (97). B only = 90/45/34/14/43 (226). X = UNSUPPORTED 2, OVERSTATED 1, UNTRACED 1 (4). B+X = SUPPORTED 90, RELAYED 45, OVERSTATED 35, UNSUPPORTED 16, UNTRACED 44 (230).
Derived: A+B flagged (OVERSTATED+UNSUPPORTED) = 19+13+34+14 = 80; with X = 83. UNTRACED A+B = 50; with X = 51. Traced = 327-51 = 276.

### Count sentences, with the number stated and my count
CLAIMS-TABLE.md:
- :48 "95 of the 327 claims in 87 rows": 327 matches total; 87 matches claims-count to-do rows. (95 claims not recomputed.)
- :52 "69 of the 327 claims are RELAYED-ONLY": 69 = 69 match
- :53 "51 claims are UNTRACED": 51 = 51; "(29 claims)" UNSUPPORTED: 29 = 29; "69 RELAYED-ONLY and 51 UNTRACED": match; "18 claims moved from UNTRACED": not recomputed
- :58 "124 SUPPORTED claims": 124 = 124 match
- :94 "A-001 to A-098 ... 97 claims": 97 = 97 match
- :105 "327 claims read, 276 traced, 51 UNTRACED (lane A 97, lane B including X 230): SUPPORTED 124, RELAYED-ONLY 69, OVERSTATED 54, UNSUPPORTED 29, UNTRACED 51": all match. "83 claims ... (54 + 29)": 83 = 83. "four X rows (X-1 UNSUPPORTED, X-2 OVERSTATED, X-4 UNSUPPORTED, X-3 UNTRACED)": my X counts = UNSUPPORTED 2, OVERSTATED 1, UNTRACED 1: match. "80 flagged and 50 UNTRACED" (A,B only): 80 = 80, 50 = 50 match.
- :151 "lane B (incl X) 45 relayed-only and 44 untraced; 7 + 44 = 51": 45 = 45, 44 = 44, 51 = 51 match
- :414-420 lane A: 34/24/13/19/7, total 97: match
- :816-822 lane B Part 7: SUPPORTED 80 (mine 90 MISMATCH), RELAYED 45 (45 ok), UNSUPPORTED 12 (mine 16 MISMATCH), OVERSTATED 30 (mine 35 MISMATCH), UNTRACED 63 (mine 44 MISMATCH), "Total 230 (226 B-rows + 4 X-rows)": total 230 ok
RUNSHEET-WORDING.md:
- :305 (section 6) "157 rows ... section 1: 38, 2: 17, 3: 61, 7: 41": = checker output (157, 38, 17, 61, 41) match; "80 by the checker's count" = 80 match; "CLAIMS-TABLE.md counts 83 = 54 OVERSTATED + 29 UNSUPPORTED": match; "50 by the checker's count ... 51 because it also counts X-3": match; "43 have no row": = checker 43 match.
- No other numeric verdict-count sentence found in RUNSHEET-WORDING.md by grep.

## 3. String hits (file:line; count of occurrences on that line in brackets when more than 1)
'The old desk harness still deletes; the take does not.' (exact, case-sensitive):
 CLAIMS-TABLE.md: 56, 125, 209, 210 [3], 237 [2], 554, 586, 748, 749, 750
 RUNSHEET-WORDING.md: 223, 239 [2], 242 [2], 272 [2], 274 [2], 275 [2]
'lead verifies at re-pin':
 CLAIMS-TABLE.md: 24 [2], 125, 209, 210 [2], 237 [5], 500, 554 [2], 586 [2], 748, 750
 RUNSHEET-WORDING.md: 22, 23, 47, 60, 239, 242, 272, 273, 274, 275, 289, 301
'coordinator confirms': CLAIMS-TABLE.md:87 ; RUNSHEET-WORDING.md none
'desk script as checked in': no hits in either file
'until fix F-01': no hits in either file
'archives anyway': CLAIMS-TABLE.md: 210, 749 ; RUNSHEET-WORDING.md: 273 [2]  (210 is row 33 quoting the old sentence; 749 is lane row B-214; 273 is the quote of B-214)

## 4. Paste cells side by side (full lines split into cells; RUNSHEET first, then CLAIMS-TABLE)
Note: RUNSHEET rows have columns per its own table; CLAIMS-TABLE rows 33/48 are to-do rows (11 cells: replacement text is cell 7 "wording"), B-lane rows are 7 cells.
=== RUNSHEET-WORDING.md rows (full lines, cells numbered)

--- RUNSHEET line 239 id B-067
  [cell 1]  B-067
  [cell 2] WATCH-CHECKLIST.md:10
  [cell 3] "The run reads and archives contacts by a lead id (starting with L) and the contact property hadavin_lead_id."
  [cell 4] "The run reads contacts by a lead id (starting with L) and the contact property hadavin_lead_id. In the take the HubSpot identity is read-only and cleanup is OFF (result.json archive_contacts is no); the owner deletes leftovers by hand. The old desk harness still deletes; the take does not. This is a statement by the lead; the take scripts are not in this repository, and lead verifies at re-pin."
  [cell 5] FILE EDIT
  [cell 6] Round 8: Lead answer Q13 (ORDERS.md, 10:23Z): the take uses run_real_check_n8n.py (take mode) plus n8n_drive.py; its HubSpot identity is read-only and cleanup is OFF (result.json archive_contacts 'no'); leftovers are listed once by lead key and contact id and the owner deletes them by hand. The old desk harness still deletes; the take does not. Lead verifies at re-pin (the take scripts are not in this repository: the lead's statement, not seen by us). CLAIMS-TABLE.md rows B-067, B-091, B-213, B-215, B-215b, to-do rows 32, 33 and 48 carry the same text. Verdict in CLAIMS-TABLE.md is OVERSTATED (true of the old desk harness only). The flow property name matches (RV5 CrmUpsert). P4c. 

--- RUNSHEET line 242 id B-091
  [cell 1]  B-091
  [cell 2] FAILED-TAKE-NOTE.md:9
  [cell 3] "With --cleanup the run archives only the contacts that carry this run's lead ids"
  [cell 4] "In the take, cleanup is OFF (result.json archive_contacts is no) and the HubSpot identity is read-only; leftovers are listed once by lead key and contact id and the owner deletes them by hand. The old desk harness still deletes; the take does not. This is a statement by the lead; the take scripts are not in this repository, and lead verifies at re-pin."
  [cell 5] FILE EDIT
  [cell 6] Round 8: Lead answer Q13 (ORDERS.md, 10:23Z): the take uses run_real_check_n8n.py (take mode) plus n8n_drive.py; its HubSpot identity is read-only and cleanup is OFF (result.json archive_contacts 'no'); leftovers are listed once by lead key and contact id and the owner deletes them by hand. The old desk harness still deletes; the take does not. Lead verifies at re-pin (the take scripts are not in this repository: the lead's statement, not seen by us). CLAIMS-TABLE.md rows B-067, B-091, B-213, B-215, B-215b, to-do rows 32, 33 and 48 carry the same text. Verdict in CLAIMS-TABLE.md is OVERSTATED (true of the old desk harness with --cleanup). P4c. 

--- RUNSHEET line 272 id B-213
  [cell 1]  B-213
  [cell 2] flows-audit/inputs/OWNER-STEPS-realrun-v3.md:99
  [cell 3] "During the take: contacts appear in HubSpot, one mail per person appears in the `demo` label."
  [cell 4] "During the take: contacts appear in the real CRM, and up to one mail per person appears in the mail label named demo. A person whose mail step is cut off ends unknown, an alert is sent, and the label may hold 0 or 1 mail. After the take the made-up contacts stay in the real CRM: the take does not delete them (cleanup is OFF), and the owner deletes them by hand. The old desk harness still deletes; the take does not. This is a statement by the lead; the take scripts are not in this repository, and lead verifies at re-pin."
  [cell 5] FILE EDIT
  [cell 6] F-042. Real-v5 only. No studio owner step added. Round 4: backticks removed; HubSpot is named in the current sentence only. Round 8: the last three sentences (contacts after the take) are the same text as in B-067, B-091, B-215 and in CLAIMS-TABLE.md row B-213 and to-do row 32. Lead answer Q13 (ORDERS.md, 10:23Z): the take uses run_real_check_n8n.py (take mode) plus n8n_drive.py; its HubSpot identity is read-only and cleanup is OFF (result.json archive_contacts 'no'); leftovers are listed once by lead key and contact id and the owner deletes them by hand. The old desk harness still deletes; the take does not. Lead verifies at re-pin (the take scripts are not in this repository: the lead's statement, not seen by us). Condition P4c for the clean-up after the take. 

--- RUNSHEET line 273 id B-214
  [cell 1]  B-214
  [cell 2] flows-audit/inputs/OWNER-STEPS-realrun-v3.md:103
  [cell 3] "Only the exact word end ends the pause ... the second wrong line also prints type exactly: end and then the script goes ahead and archives anyway; ... Ctrl-C or closing the window also still archives."
  [cell 4] NO PASTE
  [cell 5] FILE EDIT (HELD marker only)
  [cell 6] No wording is written, reason: UNTRACED (the take script is absent, so what it does at a wrong or closed answer is not known to us). Round 8: the clauses "the script goes ahead and archives anyway" and "Ctrl-C or closing the window also still archives" must not stand as a statement about the take (decision 2026-11-16 item 2; lead answer Q13: the take never deletes and a closed window or Ctrl-C does not archive in the take; lead verifies at re-pin, the lead's statement, not seen by us). Therefore, by rule HELD (section 0b): the coordinator types the words HELD, DO NOT QUOTE in front of the sentence from "Only the exact word end" to the end of that line, and rewrites it from the take script text (FAILED-TAKE-NOTE.md line 24) after the lead's re-pin check. CLAIMS-TABLE.md row 33 says the same. P4c. 

--- RUNSHEET line 274 id B-215
  [cell 1]  B-215
  [cell 2] OWNER-STEPS-realrun-v3.md:103 (the sentence); :95 and :104 also mention the archive
  [cell 3] "The script then archives this take's contacts."
  [cell 4] "After the take, the made-up contacts stay in the real CRM until the studio owner deletes them by hand in the CRM user interface. The take does not delete or archive any contact: its identity is read-only and cleanup is OFF. The old desk harness still deletes; the take does not. The coordinator lists the leftover contacts once, by lead key and contact id. This is a statement by the lead; the take scripts are not in this repository, and lead verifies at re-pin."
  [cell 5] FILE EDIT
  [cell 6] Round 8: Lead answer Q13 (ORDERS.md, 10:23Z): the take uses run_real_check_n8n.py (take mode) plus n8n_drive.py; its HubSpot identity is read-only and cleanup is OFF (result.json archive_contacts 'no'); leftovers are listed once by lead key and contact id and the owner deletes them by hand. The old desk harness still deletes; the take does not. Lead verifies at re-pin (the take scripts are not in this repository: the lead's statement, not seen by us). CLAIMS-TABLE.md rows B-067, B-091, B-213, B-215, B-215b, to-do rows 32, 33 and 48 carry the same text. Still UNTRACED in CLAIMS-TABLE.md (take scripts absent). :95 (the notice 'up to 3 contacts archived at the end' quotes the take program's own notice, not seen by us): the coordinator types HELD, DO NOT QUOTE in front of that fragment until the re-pin check. :104 is row B-215b; the rest of :103 is row B-214. One word, one meaning: delete is the word used for removing a contact; archive is the CRM vendor's own word (see Words and ids) and is not used in the pasted text except in the quoted file name archive_contacts. Condition P4c. 

--- RUNSHEET line 275 id B-215b (extra, new in round 6)
  [cell 1]  B-215b (extra, new in round 6)
  [cell 2] OWNER-STEPS-realrun-v3.md:104
  [cell 3] "STOP and tell the lead: closing the window or Ctrl-C early still archives, but tell the lead; leftover contacts are deleted by you in the HubSpot UI, the lead gives the count."
  [cell 4] "STOP and tell the lead if you close the window or press Ctrl-C early. The take does not delete or archive any contact: its identity is read-only and cleanup is OFF, so closing early removes nothing from the CRM. The old desk harness still deletes; the take does not. The lead gives you the count of leftover made-up contacts, and you delete them by hand in the CRM user interface. This is a statement by the lead; the take scripts are not in this repository, and lead verifies at re-pin."
  [cell 5] FILE EDIT
  [cell 6] Round 8: Lead answer Q13 (ORDERS.md, 10:23Z): the take uses run_real_check_n8n.py (take mode) plus n8n_drive.py; its HubSpot identity is read-only and cleanup is OFF (result.json archive_contacts 'no'); leftovers are listed once by lead key and contact id and the owner deletes them by hand. The old desk harness still deletes; the take does not. Lead verifies at re-pin (the take scripts are not in this repository: the lead's statement, not seen by us). CLAIMS-TABLE.md to-do row 33 carries the same text (B-215b has no lane row there: it is the second half of line :104, next to B-215). Reading of OWNER-STEPS-realrun-v3.md lines 104 and 112 (round 8, read by me; no v4 of that file is in this checkout): :112 (step 20) says delete any leftover HubSpot contacts the lead counted, which agrees with decision 2. :104 says two things: "closing the window or Ctrl-C early still archives" (out of date for the take: this row rewrites it) and "leftover contacts are deleted by you in the HubSpot UI, the lead gives the count" (agrees; kept). So :104 does not fully agree with decision 2; only its first half changes. What the take script does on Ctrl-C is not seen by us (script absent). Condition P4c. 

=== CLAIMS-TABLE.md to-do rows 33, 48 and lane rows

--- CLAIMS line 210 id 33
  [cell 1]  33
  [cell 2] OWNER-STEPS-realrun-v3.md
  [cell 3] OWNER-STEPS-realrun-v3.md:95 (notice reading: 'up to 3 contacts archived at the end'), :103 and :104
  [cell 4] B-214, B-215, B-215b (B-215b = the first half of :104, no lane row)
  [cell 5] "Only the exact word `end` ends the pause ... the second wrong line also prints "type exactly: end" and then the script goes ahead and archives anyway; ... Ctrl-C or closing the window also still archives."
  [cell 6] decision 2 (the coordinator's binding decision of 2026-11-16): the take identity is read-only and the take never deletes contacts; the owner deletes leftover made-up contacts by hand. Line 103 (and the notice at :95) say the script archives them; PLAN-4-NLITE-FROM-LEAD.md:111 and AGENT-SCOPE-DO-AND-DONT.md:20 say the same (archive_all in a finally block; AGENT-SCOPE names the code run_real_check_n8n.py:1051, absent here). Only flows-audit/ORDERS.md:82 says the contacts stay. Round 8, read myself (inputs/OWNER-STEPS-realrun-v3.md lines 103, 104, 112; no v4 of that file is in this checkout): :112 (step 20) says delete any leftover contacts the lead counted: it agrees with decision 2. :104 says two things: 'closing the window or Ctrl-C early still archives' (out of date for the take) and 'leftover contacts are deleted by you in the HubSpot UI, the lead gives the count' (agrees). So :104 and :112 agree only on who deletes leftovers; :104 as a whole does NOT agree, and its first half is rewritten below (an earlier version of this row said they do not disagree: that was wrong).
  [cell 7] none before the take (the text is safe now); P4c runs after the take and confirms
  [cell 8] [:103 first sentence, B-215] "After the take, the made-up contacts stay in the real CRM until the studio owner deletes them by hand in the CRM user interface. The take does not delete or archive any contact: its identity is read-only and cleanup is OFF. The old desk harness still deletes; the take does not. The coordinator lists the leftover contacts once, by lead key and contact id. This is a statement by the lead; the take scripts are not in this repository, and lead verifies at re-pin." [:104 first half, B-215b] "STOP and tell the lead if you close the window or press Ctrl-C early. The take does not delete or archive any contact: its identity is read-only and cleanup is OFF, so closing early removes nothing from the CRM. The old desk harness still deletes; the take does not. The lead gives you the count of leftover made-up contacts, and you delete them by hand in the CRM user interface. This is a statement by the lead; the take scripts are not in this repository, and lead verifies at re-pin." [:103 from 'Only the exact word end', B-214] no wording; put HELD, DO NOT QUOTE in front of that sentence (we have not seen what the take script does at a wrong or closed answer) [:95 notice fragment] no wording; HELD, DO NOT QUOTE in front of it until the re-pin check
  [cell 9] Lead answer Q13 (10:23Z): the take uses run_real_check_n8n.py in take mode plus n8n_drive.py, not the desk script's archive_all path (run_real_check.py:993, :1101-1107, the old harness); the take's HubSpot identity is read-only and result.json archive_contacts is 'no'. The old desk harness still deletes; the take does not. Lead verifies at re-pin. Use the word 'deletes' for removing a contact, never 'archives'.
  [cell 10] [LIVE] Lead verifies at re-pin (the take scripts are not in this repository; this is the lead's statement, not seen by us). P4c (after the take) counts what is left. The 'script archives' sentences at :95, :103, :104 and in PLAN-4:111 and AGENT-SCOPE:20 describe the old desk harness, not the take.
  [cell 11] [ ] 

--- CLAIMS line 237 id 48
  [cell 1]  48
  [cell 2] PLAN-4-NLITE-FROM-LEAD.md ; WATCH-CHECKLIST.md ; FAILED-TAKE-NOTE.md
  [cell 3] PLAN-4-NLITE-FROM-LEAD.md:43; WATCH-CHECKLIST.md:10; FAILED-TAKE-NOTE.md:9
  [cell 4] B-017, B-067, B-091 (was new)
  [cell 5] PLAN-4:43 (B-017): "Independent CRM count and archive ... HubspotCrm.rows_with_prefix("L"), archive_all ... reused as is"; WATCH-CHECKLIST:10 (B-067) and FAILED-TAKE-NOTE:9 (B-091): the sentences quoted in the lane rows
  [cell 6] WATCH-CHECKLIST.md:10 and FAILED-TAKE-NOTE.md:9 say the run archives the contacts; that is true of the old desk harness (run_real_check.py with --cleanup) and not of the take (lead answer Q13, 10:23Z; lead verifies at re-pin). PLAN-4:43 (B-017) describes the desk code and is SUPPORTED as that: no wording change.
  [cell 7] none before the take (P4c runs after the take and confirms)
  [cell 8] [WATCH-CHECKLIST.md:10, B-067] "The run reads contacts by a lead id (starting with L) and the contact property hadavin_lead_id. In the take the HubSpot identity is read-only and cleanup is OFF (result.json archive_contacts is no); the owner deletes leftovers by hand. The old desk harness still deletes; the take does not. This is a statement by the lead; the take scripts are not in this repository, and lead verifies at re-pin." [FAILED-TAKE-NOTE.md:9, B-091] "In the take, cleanup is OFF (result.json archive_contacts is no) and the HubSpot identity is read-only; leftovers are listed once by lead key and contact id and the owner deletes them by hand. The old desk harness still deletes; the take does not. This is a statement by the lead; the take scripts are not in this repository, and lead verifies at re-pin." [PLAN-4:43, B-017] no wording change
  [cell 9] -
  [cell 10] [OUT OF THIS VIDEO] None of these three files is filmed, shown or spoken, so nothing in the video depends on them; that is the only meaning of OUT here. The text is the same as in RUNSHEET-WORDING.md rows B-067 and B-091 (it lists them as FILE EDIT, and its step 0c.2 applies FILE EDIT rows before filming); applying it earlier or later changes nothing in the video. Under decision 2 and lead answer Q13 (10:23Z, lead verifies at re-pin) the take leaves the contacts and the owner deletes them; the sentence need not wait for F-01. This is a statement by the lead; the take scripts are not in this repository, and lead verifies at re-pin.
  [cell 11] [ ] 

--- CLAIMS line 554 id B-067
  [cell 1]  B-067
  [cell 2] WATCH:10
  [cell 3] "The run reads and archives contacts by a lead id (starting with `L`) and the contact property `hadavin_lead_id`."
  [cell 4] flow property name matches (RV5 CrmUpsert); script absent; desk repository src/lead_desk/crm_hubspot.py:88; scripts/run_real_check.py:572-581, :993, :1101-1103 (old desk harness)
  [cell 5] -
  [cell 6] OVERSTATED (true of the old desk harness, which archives; the take does not: lead answer Q13 10:23Z; lead verifies at re-pin, take scripts not seen by us)
  [cell 7] The run reads contacts by a lead id (starting with L) and the contact property hadavin_lead_id. In the take the HubSpot identity is read-only and cleanup is OFF (result.json archive_contacts is no); the owner deletes leftovers by hand. The old desk harness still deletes; the take does not. This is a statement by the lead; the take scripts are not in this repository, and lead verifies at re-pin. 

--- CLAIMS line 586 id B-091
  [cell 1]  B-091
  [cell 2] FAILED:9
  [cell 3] "With `--cleanup` the run archives only the contacts that carry this run's lead ids"
  [cell 4] desk repository scripts/run_real_check.py:993, :1101-1103; src/lead_desk/crm_hubspot.py:492-499 (old desk harness)
  [cell 5] -
  [cell 6] OVERSTATED (true of the old desk harness with --cleanup; the take uses run_real_check_n8n.py plus n8n_drive.py with cleanup OFF: lead answer Q13 10:23Z; lead verifies at re-pin, take scripts not seen by us)
  [cell 7] In the take, cleanup is OFF (result.json archive_contacts is no) and the HubSpot identity is read-only; leftovers are listed once by lead key and contact id and the owner deletes them by hand. The old desk harness still deletes; the take does not. This is a statement by the lead; the take scripts are not in this repository, and lead verifies at re-pin. 

--- CLAIMS line 748 id B-213
  [cell 1]  B-213
  [cell 2] ONS:99
  [cell 3] "During the take: contacts appear in HubSpot, one mail per person appears in the `demo` label."
  [cell 4] CrmUpsert; MailClaim; SendMail
  [cell 5] F-042
  [cell 6] OVERSTATED
  [cell 7] During the take: contacts appear in the real CRM, and up to one mail per person appears in the mail label named demo. A person whose mail step is cut off ends unknown, an alert is sent, and the label may hold 0 or 1 mail. After the take the made-up contacts stay in the real CRM: the take does not delete them (cleanup is OFF), and the owner deletes them by hand. The old desk harness still deletes; the take does not. This is a statement by the lead; the take scripts are not in this repository, and lead verifies at re-pin. (to-do row 32) 

--- CLAIMS line 749 id B-214
  [cell 1]  B-214
  [cell 2] ONS:103
  [cell 3] "Only the exact word `end` ends the pause ... the second wrong line also prints "type exactly: end" and then the script goes ahead and archives anyway; ... Ctrl-C or closing the window also still archives."
  [cell 4] none
  [cell 5] -
  [cell 6] UNTRACED
  [cell 7] No wording (HELD, DO NOT QUOTE marker in front of the sentence). Lead answer Q13 (10:23Z): the take uses run_real_check_n8n.py plus n8n_drive.py, not the desk archive path; cleanup is OFF; a closed window or Ctrl-C does not archive in the take. Lead verifies at re-pin (take scripts not in this repository, not seen by us). What the take script does at a wrong or closed answer is not known to us. PLAN:111 describes the old desk harness. The old desk harness still deletes; the take does not. 

--- CLAIMS line 750 id B-215
  [cell 1]  B-215
  [cell 2] ONS:103, :112
  [cell 3] "The script then archives this take's contacts."
  [cell 4] AGENT-SCOPE:20 says the code does it as a DELETE call (`crm_hubspot.py`, absent)
  [cell 5] -
  [cell 6] UNTRACED
  [cell 7] After the take, the made-up contacts stay in the real CRM until the studio owner deletes them by hand in the CRM user interface. The take does not delete or archive any contact: its identity is read-only and cleanup is OFF. The old desk harness still deletes; the take does not. The coordinator lists the leftover contacts once, by lead key and contact id. This is a statement by the lead; the take scripts are not in this repository, and lead verifies at re-pin. (same sentence group: B-215b at :104, see to-do row 33) 
