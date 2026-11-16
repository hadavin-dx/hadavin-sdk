"""One-time patch: turns build_c6l.py (copied) into build_c6m.py. Run once from the evidence-c6m folder; asserts every replacement matches."""
import re
p = "build_c6m.py"
s = open(p, encoding="utf-8").read()


def rep(old, new, cnt=1):
    global s
    assert s.count(old) == cnt, (s.count(old), old[:90])
    s = s.replace(old, new)


def replace_edit(key, newcode):
    global s
    m = re.search(r'^edit\("%s",' % re.escape(key), s, re.M)
    assert m, key
    st = m.start()
    nxt = re.search(r'^(edit\(|# ====|for fk|# ---)', s[m.end():], re.M)
    en = m.end() + nxt.start()
    s = s[:st] + newcode.strip("\n") + "\n" + s[en:]


# ---- names and paths
rep('"""Builds REPORT-c6l.md', '"""Builds REPORT-c6m.md')
rep("this script writes only REPORT-c6l.md and evidence-c6l/edits.json", "this script writes only REPORT-c6m.md and evidence-c6m/edits.json")
rep('"/evidence-c6l/edits.json"', '"/evidence-c6m/edits.json"')
rep("report_c6l.py", "report_c6m.py")
rep('''    "RCO": (''', '''    "RLD": (C6 + "/review-c6l-design.md", "handover/core-hardening/c6-skip-audit/review-c6l-design.md", CH, "the c6l design review"),
    "RLN": (C6 + "/review-c6l-naive.md", "handover/core-hardening/c6-skip-audit/review-c6l-naive.md", CH, "the c6l naive-reader review"),
    "RCO": (''')
rep('''    "OS19": (''', '''    "OS26": (H + "/steps-edits/OWNER-SHEET-v26-SOURCE.md", "handover/core-hardening/steps-edits/OWNER-SHEET-v26-SOURCE.md", CH, "owner sheet v26 source file (a template with placeholders; the newest file in the folder)"),
    "OS19": (''')

# ---- the 'the lead' -> 'the studio lead' rewrite must not touch 'the lead table' or 'the lead's made-up ...' (contact record meaning)
rep('''(?! fields| key| id| ends| is\\b)(?='s|\\b)''', '''(?! fields| key| id| ends| table| is\\b)(?!'s made)(?!'s name)(?!'s e-mail)(?='s|\\b)''')
# plain words: run sheet vs owner sheet
rep('''    new = _fx(new); why = _fx(why)''', '''    new = _fx(new); why = _fx(why)
    if fk == "RS":
        new = new.replace("on this sheet", "on this run sheet").replace("written on the run sheet", "written on this run sheet")''')

# ---- row 1 (scene 4 caption): attribute only what the decision covers
replace_edit("rs90", r'''
edit("rs90", "RS", "WHOLE", 'Scene 4 caption: no timing number in any caption, text card or voice (the studio lead cut the number from the video on 2026-11-16), and no rounded wording such as "about a minute". A live stopwatch overlay and the label "setting: lease 45 s" (a setting, not a measured time) are shown. The 18 kept crash runs of lane3 (60.1 to 61.9 s from the crash to the final state; 52.8 to 54.9 s from n8n coming back up) were measured on the film-v4 stand-in flows, not on the flows of this take, and stay out of the video. Two further lane3 runs at the same lease, VOID-fl45k3b (it never reached a final state, 338.7 s) and VOID-fl45k6c (the stand-in services were not up), were voided and are not counted; the cause is unknown. The kill cases K3B and K3 are not mentioned in scene 4. No statement about alert delay is made. Never "within 60 s".',
     "Line 90 was a FINAL caption with the number the studio lead cut, a kill-case sentence that is false for K3B, a 13-minute figure relayed for other flows, and the wrong from-n8n-up start (52.9; RESULTS.md line 92 says 52.8). Only the cut of the number is the studio lead's decision (decision 1); the ban on rounded wording is question L-APPROX and the missing kill-case words are question L-KILL, both unconfirmed defaults, so the new text no longer says 'decided' for them (c6l design review M1). It says 'no timing number in any caption or text card' because a live stopwatch overlay is shown. The 18 runs are the 18 KEPT runs; the two voided runs are named.",
     [("DEC", "1. SCOPE"), ("MF", "def k3b"), ("RES", "| 873a908a-film-v4-lease45 | K6 | 3 |"), ("RCO", "VOID-fl45k3b K3"), ("RJL", '"label": "VOID-fl45k3b"')], dep="L-KILL, L-APPROX", ln=90)
''')

# ---- row 3 (rs82): no date attribution for a card default
replace_edit("rs82", r'''
edit("rs82", "RS", "History line for the card: on v4", "Withdrawn from the card (the card makes no statement about alert delay: it says only that we make no statement about how quickly an alert mail arrives). Old history line, left in place as history: on v4",
     "Line 82 told the filmer to put the 13-minute figure on the card; the card line 2 does not (c6j design review M4). The figure is a relay for lane3 v4 flows, not the flows of the take (RESULTS.md lines 78 and 79). The new text carries no date and no 'decided', because the card text is only a default (c6l design review M1).",
     [("RES", "| 7709d058-v4 | v3KS | v4ks1 |")], dep="Q1")
''')

# ---- row 31 (rs5b)
replace_edit("rs5b", r'''
edit("rs5b", "RS", OLD["rs5b"], "The V7 and lane3 numbers are not on the closing card (see the closing card row of this run sheet, line 41); they stay in the raw files as history.",
     "Line 5 says the numbers sit on the closing card; the closing-card edits remove them. The new text carries no date and no 'decided' (c6l design review M1).", [("RS", "| 12. Closing card |")], dep="Q1")
''')

# ---- row 5 (rs79)
replace_edit("rs79", r'''
edit("rs79", "RS", OLD["rs79"], "5. Decided: no recovery number on screen (the studio lead cut the number from the video on 2026-11-16). What the closing card says is settled by the closing card row of this run sheet (line 41).",
     "Open decision 5 is answered by the cut of the number from the video (decision 1, DEC:2). The studio lead's decision does not cover the closing card line 'lease plus 25 to 30 s'; its removal is only the default of L-CARDCUT, so the new text no longer says 'none on the closing card' (c6l design review M1).", [("DEC", "1. SCOPE")])
''')

# ---- row 17 (rs33a): independent of the rounded-wording question
replace_edit("rs33a", r'''
edit("rs33a", "RS", OLD["rs33a"],
     'No timing number in any caption or in the voice; the stopwatch overlay (the clock of this run) and the label "setting: lease 45 s" are on screen.',
     "Line 33 still carried the dropped caption 'about the lease plus 25 to 30 s', which decision 1 removes with the number. The part about rounded wording such as 'about a minute' is no longer in this row (split, c6l design review M4): it stays in rows 1 and pg161 under question L-APPROX, so this row is ready. The old text says 'no number' yet shows a label: this says 'no timing number'. The live stopwatch overlay and any 'sped up' label with the real wait show the clock of this very run as it happens; they are not a timing number in the sense of section 'Words' and no row changes them (run sheet lines 21 and 33).", [("DEC", "1. SCOPE")])
''')

# ---- row 5/other: time zones in new text
replace_edit("rs23a", r'''
edit("rs23a", "RS", OLD["rs23"], "Recovery wording: NONE (the studio lead dropped the plus 25 to 30 s caption at 17:05 UTC = 22:35 IST; on 2026-11-16 the studio lead cut the number 60.1 to 61.9 s from the video).",
     "Line 23 still plans a measured-number caption. Times are given in UTC and IST (c6l naive review M8).", [("DEC", "1. SCOPE")])
''')

# ---- rs31: no pointer to a section that only another row creates
replace_edit("rs31", r'''
edit("rs31", "RS", OLD["rs31"],
     "to the form entry on the LOOPBACK address, path mf-form. The owner types nothing into the lead fields except what the prepared note already contains; never a key, a password or a token in any form field (n8n saves the request body, see N8N-START.md).",
     "Do-not rule for the owner: a secret sent in a form field is saved by n8n. The pointer names the file only, because the leak-scan section it used to name is created by another row (c6l design review m5).", [("NS", "3. Nobody must send a secret"), ("PG", "18. UNBACKED")])
''')

# ---- rs32: lease sentence does not need saved runs
replace_edit("rs32", r'''
edit("rs32", "RS", OLD["rs32"],
     'Caption: "a lead sent twice with the same id is processed once". Second caption line: "We say this only when the second send comes within 45 seconds of the first. The 45 seconds is a setting: for that long the system keeps a lead for the run that took it first." No result exists for this repeat send on the flows of this take, so the rehearsal must show the repeat reply, and the real seconds between the first reply and the repeat (write them on this run sheet; the gap must be less than 45 seconds), before the take. The screen is the evidence.',
     "The studio lead's answer (ORDERS.md Q21.2 and Q22) requires the statement plus one honest sentence that a gap longer than the lease is not claimed; the studio lead gave that sentence in brackets, not as a caption, so the caption text is a question (L-LEASE). This row no longer waits for the import check: the lease sentence and the rehearsal evidence do not depend on saved runs (c6l design review m1).",
     [("ORD", "Q21.2:"), ("ORD", "Q22:"), ("DEC", "1. SCOPE")], dep="L-LEASE")
''')

# ---- row 6 (rs71): re-issued against the answers Q23 and Q27, plus the saved-runs gate (c6l design M5)
replace_edit("rs71", r'''
edit("rs71", "RS", OLD["rs71"],
     '10. Run the whole take once with a stopwatch; compare to the EST column and re-total.\n11. Before every rehearsal and before the take, list the active workflows in n8n. Only workflows imported from the folder n8n-flows-real-v5 may be active: the form entry flow, the hook entry flow, the recovery flow, and the shared-step flow if it is active. No workflow from any other folder, and no workflow with the paths mf-form or mf-hook from n8n-flows-film-v5 or an older folder, may be active. Write the list into the studio lead session note (the handoff). (This check needs n8n and is not run yet.)\n12. Closing check for contact deletion and the owner sheet, run by the studio lead when the final version of the files is known: (a) read the take script scripts/run_real_check_n8n.py (the one the video uses; the older script scripts/run_real_check.py is not used) at that version and search it with grep -n -i archive and grep -n -i delete. The studio lead\'s written answer of 2026-11-16 12:50 UTC (18:20 IST) says that the independent review of 11:00 UTC (16:30 IST) found no archive and no delete call there, only a listing request; this is UNVERIFIED until the grep output is written here with the version id and the date and time in UTC. (b) read the owner sheet the owner reads: it must say that the owner deletes leftover made-up contacts by hand, and it must not say that the HubSpot key is read-only or limited to create and change unless the owner has confirmed that.\n13. Scene 3: write down the real seconds between the first reply of scene 2 and the repeat send, and the reply text of the repeat. The gap must be less than 45 seconds (the lease); if it is longer, redo the scene. After the repeat the CRM list must still show 1 row and the test mailbox 1 mail; if not, stop and tell the studio lead.\n14. GATE, saved runs. From the edit of the four flow files on, n8n saves every run, so a secret sent in a form field would be stored. The take (and any rehearsal with real accounts) does not start until this run sheet shows two lines, each with the date and time in UTC and IST and the name of the person who ran it: "import check passed: the execution list shows runs of an entry flow and of the recovery flow" and "leak scan for saved runs passed: pass lines met on the loopback stand-ins". Owner of this gate: the studio lead (he runs both checks himself, or names a builder to write the leak scan and writes that name here: ______). Both checks run on this computer only, with stand-in services, before the first rehearsal.',
     "Eleven flow folders carry the same webhook paths mf-form and mf-hook; only real-v5 may be live (c6j design review minor and c6i review). Item 12 is re-issued against the studio lead's answers Q23 and Q27 (ORDERS.md): decision 2 stands (the take never deletes), the audited tree has no take script, so the grep is the studio lead's step at the final version and its result is UNVERIFIED until written; the old requirement of 0 hits for 'never deletes' in the decisions file is dropped because the file states the rule (c6l design review B1). Item 14 is new: saved runs are switched on by the flow-file rows, the import check and the leak scan are not run yet, so the take is blocked until both lines are on the run sheet, with a named owner (c6l design review M5). The shared-step flow may be active if it is a real-v5 file. Item 13 has a target (under 45 seconds) and a pass test.",
     [("EVDIR", "n8n-flows-real-v5"), ("DEC", "2. TAKE IDENTITY"), ("ORD", "Q23:"), ("ORD", "Q27:"), ("MF", "CREATE TABLE mf_leads")])
''')

# ---- row 8 (rs59): gate re-issued
replace_edit("rs59", r'''
edit("rs59", "RS", OLD["rs59"],
     '10. Step-2 fault for a real mailbox and the Slack alert are NOT BUILT; the take says "stand-in" or cuts.\n11. GATE, contact deletion. The studio lead decided that the take never deletes contacts, and his written answer of 2026-11-16 12:50 UTC (18:20 IST) confirms it: the independent review of 11:00 UTC (16:30 IST) found no archive and no delete call in the take script scripts/run_real_check_n8n.py (only a listing request), and the HubSpot key is not widened. This is UNVERIFIED by the audit: the script is not in the audited files. Two scripts have similar names: scripts/run_real_check_n8n.py is the take script the video uses; scripts/run_real_check.py is an older script whose help text offers a clean-up option that archives contacts, and it is not used. Older plan text that shows the owner a notice "up to 3 HubSpot contacts archived at the end" is stale according to that answer and must not be shown. The take does not start until the studio lead has written here, with date and time in UTC and IST: (1) the version id of the files he read; (2) the output of grep -n -i archive and grep -n -i delete on scripts/run_real_check_n8n.py at that version (no hit, or the lines); (3) "matches the decision" or, if a line was found, "stop: tell the owner"; (4) that no owner sheet and no notice shows a line promising that contacts will be deleted or archived by the program. Until then the take is blocked and nothing is touched in the CRM. Not checked: whether an archived contact keeps its e-mail address reserved.\n12. GATE, the repeat-send statement: scene 3 and card line 1 are not filmed until the unique index on the contact table (the database rule that refuses a second row for the same contact id) has been seen in the table of the take\'s own database (the loopback re-smoke result), or the studio lead writes here "index not seen, accepted" with the date and time in UTC and IST. In the test program the table is created with a primary key on the contact id (mf.py line 45), which is the same kind of rule; that is not proof for the take database.',
     "Re-issued against the studio lead's answers Q23 and Q27 (ORDERS.md; c6l design review B1): decision 2 stands, so the gate no longer offers a choice between changing the program and changing the decision, no longer states that the end-of-take step archives 'also after an error' (that came from plan text, not from the script), and names both scripts and which one the video uses. The gate record has four yes-or-no lines written by the studio lead at the re-pin. The old plan 4 notice and the help text of the older script are cited as stale or unused in section 6. Item 12: who writes 'index not seen' is named.",
     [("ORD", "Q23:"), ("ORD", "Q27:"), ("ORD", "Q20.4:"), ("EQ4", "--cleanup"), ("P4", "up to 3 HubSpot contacts archived at the end"), ("DEC", "2. TAKE IDENTITY"), ("MF", "CREATE TABLE mf_leads")])
''')

# ---- rs41b2 why: no K3B reference for the card lines (row 14)
rep("Old lines 2 and 3 (80 kills, recovery time) are cut because the K3B 'mail left' wording is false and the recovery line contradicts the data.",
    "Old line 2 (80 kills) is cut because it counts runs of older v3 flows with a 20 s lease on stand-ins, not the flows of the take; old line 3 (recovery 'about the lease plus 25 to 30 s') is cut because the lane3 runs at 45 s ended 60.1 to 61.9 s after the crash, which does not match 70 to 75 s (c6l design review M2: the K3B wording is not on the card).")
rep("so n8n keeps the lead's made-up name and e-mail, and everything", "so n8n keeps the made-up name and e-mail of the contact, and everything")

# ---- page statements
replace_edit("pg105", r'''
edit("pg105", "PG", "The only v4 recovery figure is a lane3 relay: K1 recovered in 144.3 s at its lease of 120 s (n=1, v4 K1).",
     "The v4 recovery figure is a lane3 relay: K1 recovered in 144.3 s at a lease of 120 s (n=1, one run, v4 K1). Lane3 also ran crash tests at a 45 s lease on film-v4 stand-in flows; they are in statement 20.",
     "Statement 14 contradicts statement 20 (c6j design review m5). The new text points to statement 20 without its figure and without saying whether statement 20 is for the web page, so it is true whatever the studio lead answers (c6l design review m2).", [("RES", "| 7709d058-v4 | K3 | 1 |")])
''')
replace_edit("pg120a", r'''
edit("pg120a", "PG", OLD["pg17"], "at the 45 s film lease lane3 ran crash tests on film-v4 stand-in flows (see statement 20); nothing is measured on real-v5.",
     "Statement 17 says nothing is measured at 45 s; statement 20 on the same page gives the lane3 runs. The new text carries no figure and no 'not for the web page' (c6l design review m2).", [("RES", "| 873a908a-film-v4-lease45 | K1 | 5 |")])
''')
replace_edit("pg139", r'''
edit("pg139", "PG", OLD["pg139"], "- Lease 45 s: measured only on film-v4 stand-in flows by lane3 (see statement 20), not on real-v5. Lease 120 s: one lane3 figure only.",
     "Same contradiction in the honest-limits list. No figure of statement 20 and no 'not for the web page' (c6l design review m2).", [("RES", "| 873a908a-film-v4-lease45 | K1 | 5 |")])
''')
replace_edit("pg149a", r'''
edit("pg149a", "PG", OLD["pg149a"],
     '20. "On the film-v4 stand-in flows (not the flows in the video), with a 45 s lease, each of the 18 kept crash runs reached a final state 60.1 to 61.9 s after the crash." Final states: 10 runs done (K1 5, K2 5) and 8 runs unknown with one alert to the owner (K3B 5, K3 3, in this page\'s names), which is the intended safe end state of those two cases (the system cannot tell whether the CRM entry and the mail happened, so it sends one alert and a person decides). Two more runs of the same series were voided by the lane3 session (labelled VOID in its raw file) and are not counted: VOID-fl45k3b (it never reached a final state, 338.7 s) and VOID-fl45k6c (the stand-in services were not up); the cause of the first is unknown. Five of the 18 counted runs ran at the same time as a voided run (fl45k2d, fl45k2e, fl45k6a, fl45k3d, fl45k6b), so the voided runs may have disturbed them; this was not checked. Not measured on real-v5.',
     "Statement 20 said all 18 runs finished, but 8 of 18 ended unknown (RESULTS.md lines 91 and 92). 'About a minute' is the rounded wording of question L-APPROX, so it is removed here as well. 'Each of 18' now says 18 KEPT runs and names the two voided runs; the new text also says that 5 kept runs overlap the voided K3B window in time (c6l design review m3) and what 'unknown with one alert' means (c6l naive review m5). This row is a correction and no longer waits for the web-page question L-PAGE (c6l design review M3): it carries the figure that the statement already carried; whether the page may publish it is decided by the row that marks statement 20 (L-PAGE).",
     [("RES", "| 873a908a-film-v4-lease45 | K3 | 5 |"), ("RES", "| 873a908a-film-v4-lease45 | K6 | 3 |"), ("RCO", "VOID-fl45k3b K3"), ("RJL", '"label": "VOID-fl45k3b"')], dep="L-APPROX")
''')
replace_edit("pg154", r'''
edit("pg154", "PG", "- From n8n coming back up: 52.9 to 54.9 s (about 8 s restart is inside the kill-to-final numbers).",
     "- From n8n coming back up: 52.8 to 54.9 s (RESULTS.md lines 89 to 92; about 8 s restart is inside the kill-to-final numbers).",
     "The K6 row of RESULTS.md starts at 52.8, not 52.9 (c6j design review m1). This is a correction that holds whatever the studio lead answers about the web page (c6l design review M3).", [("RES", "| 873a908a-film-v4-lease45 | K6 | 3 |")])
''')

# ---- dependency overrides (one place): card set split into three questions, L-ROUND renamed, ready rows
rep('''CARD = ["rs82", "rs80", "rs41a", "rs41b1", "rs41b2", "rs41c", "rs33d", "rs14", "rs5b"]
DEP = {"rs33a": "L-ROUND", "pg161": "L-ROUND", "pg154": "L-PAGE", "pg134": "L-PAGE", "pg148": "L-PAGE",
       "ns4a": "L-ONEDB, C-8", "ns4b": "L-ONEDB, C-8"}
for e in EDITS:
    if e["key"] in CARD:
        e["dep"] = "L-CARD, L-LEASE"
    if e["key"] in DEP:
        e["dep"] = DEP[e["key"]]''',
'''CARD = ["rs82", "rs80", "rs41a", "rs41b1", "rs41b2", "rs41c", "rs33d", "rs14", "rs5b"]
DEP = {"rs82": "L-CARD, L-CARDCUT", "rs80": "L-CARD, L-CARDTEXT", "rs41a": "L-CARD, L-CARDCUT, L-CARDTEXT",
       "rs41b1": "L-CARD, L-LEASE", "rs41b2": "L-CARD, L-CARDCUT, L-CARDTEXT", "rs41c": "L-CARD, L-CARDCUT",
       "rs33d": "L-CARD, L-CARDCUT", "rs14": "L-CARD, L-CARDCUT", "rs5b": "L-CARD, L-CARDCUT",
       "rs33a": "", "pg161": "L-APPROX", "pg154": "", "pg134": "L-PAGE", "pg148": "L-PAGE", "pg149a": "L-APPROX",
       "rs32": "L-LEASE", "ns4a": "L-ONEDB, C-8", "ns4b": "L-ONEDB, C-8"}
for e in EDITS:
    if e["key"] in DEP:
        e["dep"] = DEP[e["key"]]
    assert "L-ROUND" not in e["dep"]''')
rep('''dep="Q9")''', '''dep="L-APPROX")''')
s = s.replace("L-ROUND", "L-APPROX")

# ---- viewer column: one short phrase per row
VIEW = {
 "rs90": "Scene 4 shows no timing number and no rounded wording; the live stopwatch and the label 'setting: lease 45 s' stay.",
 "rs85": "Nothing (an old note on the run sheet is corrected).",
 "rs82": "The closing card makes no statement about how quickly an alert mail arrives.",
 "rs80": "Closing card: the retention sentence is the third spoken line.",
 "rs79": "Nothing on screen (an open question on the run sheet is closed).",
 "rs71": "Nothing on screen; the take is blocked until the workflow list, the contact-deletion check and the saved-runs checks are written on the run sheet.",
 "rs70": "Nothing (a note on the run sheet).",
 "rs59": "Nothing on screen; the take is blocked until the studio lead has written the result of the contact-deletion check.",
 "rs51": "Nothing (a note on the run sheet).",
 "rs47": "Nothing (a note on the run sheet).",
 "rs44": "Nothing on screen; the run sheet gives the length of the one video: 3 minutes.",
 "rs41a": "Closing card has four spoken lines instead of six.",
 "rs41b1": "Closing card line 1 adds the sentence that the repeat-send statement holds only within 45 seconds.",
 "rs41b2": "Closing card lines 2 to 4: no alert-delay statement, the retention sentence, what was not tested.",
 "rs41c": "Closing card shows none of the old history numbers.",
 "rs36": "Nothing (a note on the run sheet).",
 "rs33a": "Scene 4 caption row: no recovery-time caption.",
 "rs33b": "Nothing on screen (planning note for the cut).",
 "rs33c": "Nothing on screen (planning note).",
 "rs33d": "Nothing on screen (planning note).",
 "rs32": "Scene 3 caption adds the sentence about the 45 seconds.",
 "rs31": "Nothing on screen (a rule for the owner).",
 "rs30a": "Before scene 1 the execution list is cleaned and checked; old runs are not on screen.",
 "rs30b": "Scene 1 shows the execution list with the recovery flow's run every 30 seconds.",
 "rs24": "Nothing (a note on the run sheet).",
 "rs23a": "Nothing on screen (planning note).",
 "rs23b": "Nothing on screen (planning note).",
 "rs22": "Nothing (a note on the run sheet).",
 "rs14": "Nothing (a note on the run sheet).",
 "rs5b": "Nothing (a note on the run sheet).",
 "rs5a": "Nothing (a note on the run sheet).",
 "rs4": "Nothing (a note on the run sheet).",
 "pg23": "Web page: the lane3 numbers note says which numbers were read from files.",
 "pg105": "Web page, statement 14: points to statement 20 instead of a contradiction.",
 "pg120a": "Web page, statement 17: points to statement 20.",
 "pg120b": "Web page, statement 17: the rough recovery rule is called unusable.",
 "pg125": "Web page, statement 18: says n8n keeps the data of every run (still unbacked).",
 "pg134": "Web page: statement 19 (13-minute alert delay) is marked not for the page.",
 "pg139": "Web page: the limits list points to statement 20.",
 "pg148": "Web page: statement 20 is marked not for the page.",
 "pg149a": "Web page, statement 20: correct count (10 done, 8 unknown with one alert) and the two voided runs named.",
 "pg149b": "Web page, statement 20: says the raw table was read.",
 "pg150": "Web page: the two crash test names K3B and K3 are described correctly.",
 "pg153": "Web page: the K3B and K3 results are described correctly (0 and 1 mails).",
 "pg154": "Web page, statement 20: the from-n8n-back-up range starts at 52.8.",
 "pg156": "Web page: the 13-minute figure is labelled as not used in the video.",
 "pg159": "Web page: caption rule says no timing number.",
 "pg161": "Web page: no caption wording for the recovery time.",
 "ns4a": "Nothing on screen (start notes: where n8n keeps its data).",
 "ns4b": "Nothing on screen (start notes: the claim table's database).",
 "ns15": "Start notes: the take saves every run, so the execution list shows runs.",
 "ns17": "Nothing on screen (setting value for the take).",
 "ns18": "Nothing on screen (setting value for the take).",
 "ns23": "Nothing on screen (start notes).",
 "ns24": "Nothing on screen (start notes).",
 "ns27": "Nothing on screen (start notes: flow-file settings and the import check).",
 "ns43": "Nothing on screen (start notes: what the page may say).",
 "ns45": "Nothing on screen (start notes: what n8n keeps).",
 "ns48": "Nothing on screen (start notes: the leak scan for saved runs is described).",
 "mf276": "Nothing (a comment in the test program).",
 "mf320": "Nothing (a printed line of the test program).",
 "one13": "Nothing (the one-store decision is marked as a target).",
 "one14": "Nothing (the one-store decision wording).",
 "one16": "Nothing (the one-store decision wording).",
}
for fk in ("JF", "JH", "JR", "JS"):
    for w in ("Success", "Error"):
        VIEW["j%s%s" % (fk, w)] = "Scenes 1 and 2: the execution list shows the runs of this flow (setting 'save %s runs' = all)." % ("successful" if w == "Success" else "failed")
rep("# ---------------------------------------------------------------- order and numbering",
    "VIEW = " + repr(VIEW) + "\nfor e in EDITS:\n    e['view'] = VIEW[e['key']]\n\n# ---------------------------------------------------------------- order and numbering")
open(p, "w", encoding="utf-8").write(s)
print("patched build")
