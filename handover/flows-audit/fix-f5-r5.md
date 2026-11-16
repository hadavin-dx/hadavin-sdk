# fix-f5-r5: change log of round 5 for RUNSHEET-WORDING.md (2026-11-16)

## What failed, what is uncertain, what I did not do (first)
- No review follows round 5 (cap). No new string is reviewed. I do not call the file paste-ready.
- I did not use Edit for the whole change: the restructure moved about 60 rows between sections, so I rebuilt the file with a throwaway script (scratchpad build_r5.py and prose_r5.py; row texts copied from the saved round 4 file, RUNSHEET-r4.bak in the scratchpad, which is the safe copy). Rows I did not mean to change are byte-identical to round 4 (script copies them). Not diffed line by line: UNCHECKED beyond the row-count check below.
- Decisions I had to make where the inputs were silent (each is a question in the file): Q-F (does the video end with the closing card; default: yes, lines 2 and 4 left out), Q-G (which program types captions and cards), Q-A (who does the machine actions in scenes 1 to 4).
- Conflict I could not resolve: lead decision item 10 wording (n8n has its own database in Postgres) against DECISION-one-store.md lines 8 and 9 and N8N-START.md line 4 (n8n runs on SQLite today). Row X-5a holds the decision wording, held until check P4b; X-5b is the default. The decision wording has apostrophes; the string uses "one that belongs to n8n and one that belongs to the take" so the one-clean-string rule holds.
- Not checked: any flow behaviour (nothing was re-read in real-v5 beyond the existence of five node names), CLAIMS-TABLE.md lines 262 to 758 for wording, the take scripts, scripts/n8n_api.py (absent).
- Rows A-026, A-033c: the claim "the coordinator confirms it" is removed (now: not confirmed, Q-E).
- B-067 and B-091 were NO PASTE; they now hold new strings from lead decision item 2 (read-only take identity). Their source is the decision, not a file; the take script is absent.

## Facts Majors (review r5 facts)
1. Stand-in CRM refuse switch: crm_stub.py documents POST /control {fail_status}; section 7a states it (lines 2, 16, 22 of crm_stub.py read; RUN-ON-LAPTOP.md line 27). Old "no refuse switch" text in Q-C and line 80 replaced. Scene 5 is cut from the take anyway.
2. CLAIMS-TABLE.md cites re-read against the current file and fixed: D1 72, D2 73, D3 74, coordinator 29, owner 30, laptop agent 32, P1 77, P2 78, P4a 79, P4b 80, P4c 81, A-012 row 261. A-088 is at 336 (not cited by line).
3. run_mf.py: now says it does not start the stand-ins; mf.py does (lines 27, 41, 42, read). Take-script switch stays UNCHECKED.
4. Nits fixed: smtp_catcher greeting (line 13) and .pre (lines 10 to 12) in 7a and A-033a; stage_server /mail_count in 7a; "owner" versus "studio owner" defined in 0-words with the sources; D1 delegation to the studio owner removed; A-044 note kept (later section).

## Reader Blockers and Majors that apply to scenes 1 to 4
- Blocker 1 (steps say what to say, not what to do): steps 5 to 8 now name the machine actions from the run sheet columns (R:30 to R:33) with [WHO: Q-A] tags; Q-A rewritten. Stopwatch is Q-B.
- Blocker 2 (step 9.1 and 9.2 placeholders): the stand-in start steps are scene 5 to 11 material, moved to section 7b with the values that exist; the take no longer needs them.
- Blocker 3 (recording two meanings): recording = the finished video; screen capture = what the laptop records while filming (0-words and Words).
- Blocker 4/5/6 (rows claiming more than the evidence): A-026a/b/c and A-033c (confirmation claim removed), A-050b (attribution in the string; "each stop hit one lead" removed; alert caveat added), A-040/A-041/B-085 (second sentence split into A-040b, A-041b, B-085b with the hold-back rule), line 331 "no row missing" replaced by a scoped, script-checked statement, "paste-ready" removed, "script checks" now name tools/check_runsheet_paste.py.
- Major 7 (edit by line number): step 2 says match by exact old sentence, bottom-up per file.
- Major 8 (held and default rows): new section 0b (rule HELD plus a table) and default rows A-087c, A-087d, A-053b, X-5b; closing card table gives a default per line; A-017a/A-019a/A-051a defaults stated.
- Major 9 (where to paste): "Where to paste" paragraph; paths (flows-audit/ under handover/, others under handover/demo/); Line N words are not printed (strings no longer start with Line N); A-016e is in step 10; Q-G open for the editing program.
- Major 10 (words): claim, lead (coordinator), owner, review, K1/K2, window ("alert hold"), recording defined; "cap stage" in B-145 replaced by the stage service. Not all of queue, approval and stage were individually re-checked: UNCHECKED.
- Major 11 (A-035 "Outcome"): string now starts "Unknown:" (section 7).
- Major 12 (evidence gaps): A-008a added to the P4a list; A-091 reworded; A-057 held on F-001; MailClaim, AlertMark, MarkFailed names confirmed present in real-v5 files but logic not re-read (said in Read first); A-050b alert caveat. A-030, A-033, A-035 depend on P1 and are in section 7.
- Major 13 (order): caveats moved to the top ("Read first"), D/P checks defined in 0a before any row uses them, extra terms (run sheet, scene, CrmIdOk, F-008, FIX-PLAN item 7, lane3, page) added to 0-words.
- Minor 14, 17, 18, 19, 21 fixed (step 1 says how the laptop agent gets its checks; Q at 17:05 UTC explained; N-7 never existed, said so; 59.4 s added; "I" defined). Minor 15 (viewer strings with n8n, lead table) and 16 not changed beyond what moved to section 7: UNCHECKED for scenes 1 to 4 strings such as A-010 and A-053, which still use lead table and n8n; A-053 now says lead table without explaining it on screen (the card is the closing card; the term is not defined for the viewer).

## Scope moved to section 7 (LATER VIDEO, NOT FOR THE TAKE)
Rows: A-001L, A-004, A-008b, A-026a/b/c, S5-voice, N-4a/b/c, N-5c, A-030, A-033a/b/c, A-035, A-036a/b, N-1, A-021, A-040/b, A-041/b, B-085/b, A-042, A-092, A-097a/b, N-2, A-043, A-044a/b, B-076, B-077, B-078, N-8, S5-a/b/c, steps L-1 to L-16.
Cut from the take: flow-set switch, scene 5, "60.1 to 61.9 s" (row A-019a deletes the line), table screen (not run), the real-account HubSpot delete (decision 2: the take never deletes; B-215 rewritten, studio owner deletes by hand).

## Evidence (script flows-audit/tools/check_runsheet_paste.py, run on the new file)
```
section '1': 38 rows
section '2': 17 rows
section '3': 54 rows
section '7': 41 rows
total rows: 150
claim ids marked UNSUPPORTED, OVERSTATED, DELETE or STALE in CLAIMS-TABLE.md: 71 | with no row here: []
claim ids marked UNTRACED there: 69 | with no row here: 58 (scope: UNTRACED claims have no safe wording, so they get a row only when a file sentence had to change)
RESULT: PASS
```
Round 4 file for comparison (same script): 65 + 3 + 17 + 56 = 141 rows. New: 150 (141 + A-087c, A-087d, A-053b, A-001L, A-040b, A-041b, B-085b, X-5b, N-5c, X-5a minus the old X-5 = +9). Every old row id is in the new file (build script: only N-8 and a table header were hand-written).

## Files changed
- /home/user/hadavin-sdk/handover/flows-audit/RUNSHEET-WORDING.md (rebuilt)
- /home/user/hadavin-sdk/handover/flows-audit/tools/check_runsheet_paste.py (new, read-only checker)
- /home/user/hadavin-sdk/handover/flows-audit/fix-f5-r5.md (this file)
- Safe copy of round 4: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/RUNSHEET-r4.bak
Nothing committed. EGM: reviews of rounds 1 to 4 exist; round 5 has no review by the cap (stated in the file).
