import re
p = "build_c6l.py"
s = open(p, encoding="utf-8").read()

def rep(old, new, cnt=1):
    global s
    assert s.count(old) == cnt, (s.count(old), old[:80])
    s = s.replace(old, new)

def replace_edit(key, newcode):
    """replace the whole edit("key", ...) call"""
    global s
    m = re.search(r'^edit\("%s",' % re.escape(key), s, re.M)
    assert m, key
    st = m.start()
    nxt = re.search(r'^(edit\(|# ====|for fk|# ---)', s[m.end():], re.M)
    en = m.end() + nxt.start()
    s = s[:st] + newcode.rstrip("\n") + "\n" + s[en:]

rep("REPORT-c6k.md", "REPORT-c6l.md", 1) if "REPORT-c6k.md" in s and s.count("REPORT-c6k.md") == 1 else None
s = s.replace("c6k", "c6l")
# short names renamed and added
s = s.replace('("EV1",', '("EVDIR",').replace('("EV",', '("EVSET",')
s = s.replace('"EV1": (', '"EVDIR": (').replace('"EV": (', '"EVSET": (')
s = s.replace('"DD": (', '"RJD": (').replace('"DN": (', '"RJN": (')
rep('''    "EQ4": (''', '''    "RKD": (C6 + "/review-c6k-design.md", "handover/core-hardening/c6-skip-audit/review-c6k-design.md", CH, "the c6k design review"),
    "RKN": (C6 + "/review-c6k-naive.md", "handover/core-hardening/c6-skip-audit/review-c6k-naive.md", CH, "the c6k naive-reader review"),
    "RCO": (C6 + "/raw-lane3/recompute-output.txt", "handover/core-hardening/c6-skip-audit/raw-lane3/recompute-output.txt", CH, "lane3 recomputed numbers (raw output)"),
    "RJL": (C6 + "/raw-lane3/results.jsonl", "handover/core-hardening/c6-skip-audit/raw-lane3/results.jsonl", CH, "lane3 raw run records, one per line"),
    "OS25": (H + "/steps-edits/OWNER-SHEET-v25-A.md", "handover/core-hardening/steps-edits/OWNER-SHEET-v25-A.md", CH, "owner sheet v25, variant A (the newest sheet on disk)"),
    "OS19": (H + "/steps-edits/OWNER-SHEET-v19.md", "handover/core-hardening/steps-edits/OWNER-SHEET-v19.md", CH, "owner sheet v19 (assumed newest by REPORT-c6k.md)"),
    "QUE": (H + "/QUEUE.md", "handover/core-hardening/QUEUE.md", CH, "the lead's queue (header rule 6)"),
    "EQ4": (''')
# DEC cite annotation
rep('''def src(pairs):
    return ", ".join("%s:%d" % (k, find(k, a)) for k, a in pairs)''', '''def cite(k, a):
    n = find(k, a)
    if k == "DEC":
        m = re.match(r"^(\\d+)\\.", lines(k)[n - 1])
        if m:
            return "DEC:%d (decision %s)" % (n, m.group(1))
    return "%s:%d" % (k, n)


def src(pairs):
    return ", ".join(cite(k, a) for k, a in pairs)''')

# ---- rows
replace_edit("rs90", '''edit("rs90", "RS", "WHOLE", 'Scene 4 caption (decided 2026-11-16): no timing number in any caption, text card or voice, and no rounded wording such as "about a minute". A live stopwatch overlay and the label "setting: lease 45 s" (a setting, not a measured time) are shown. The 18 kept crash runs of lane3 (60.1 to 61.9 s from the crash to the final state; 52.8 to 54.9 s from n8n coming back up) were measured on the film-v4 stand-in flows, not on the flows of this take, and stay out of the video. Two further lane3 runs at the same lease, VOID-fl45k3b (it never reached a final state, 338.7 s) and VOID-fl45k6c (the stand-in services were not up), were voided and are not counted; the cause is unknown. The kill cases K3B and K3 are not mentioned in scene 4. No statement about alert delay is made. Never "within 60 s".',
     "Line 90 was a FINAL caption with the number the studio lead cut, a kill-case sentence that is false for K3B, a 13-minute figure relayed for other flows, and the wrong from-n8n-up start (52.9; RESULTS.md line 92 says 52.8). The new text says 'no timing number in any caption or text card' because a live stopwatch overlay is shown (c6k design review m1). The 18 runs are the 18 KEPT runs; the two voided runs are named (c6k design review M3).",
     [("DEC", "1. SCOPE"), ("MF", "def k3b"), ("RES", "| 873a908a-film-v4-lease45 | K6 | 3 |"), ("RCO", "VOID-fl45k3b K3"), ("RJL", '"label": "VOID-fl45k3b"')], dep="L-KILL, L-ROUND", ln=90)
''')
replace_edit("rs59", '''edit("rs59", "RS", OLD["rs59"],
     '10. Step-2 fault for a real mailbox and the Slack alert are NOT BUILT; the take says "stand-in" or cuts.\\n11. GATE, what the CRM key may do (closed until the studio lead chooses). The studio lead decided on 2026-11-16 that the take never deletes contacts (decisions file, line 3). According to plan 4 and the help text of the take script (the script code was not read by the audit), the program does not match: plan 4 shows the owner a notice "up to 3 HubSpot contacts archived at the end"; the end-of-take step ARCHIVES the made-up contacts it created (moves them to the CRM recycle bin; this is not a permanent delete), also after an error; the separate probe script tries a permanent delete first and archives if that fails (audit notes of that script).\\nThe take does not start until the studio lead has written this gate record on this sheet, with the date and time in UTC: (1) choice (a) the program is changed so that the take neither archives nor deletes, or choice (b) the written decision and every owner sheet are changed to say that the take archives only its own made-up contacts and never permanently deletes; (2) the studio lead has read the take script and it matches the choice (a: no archive or delete call; b: archive of own contacts only); (3) the owner sheet the owner reads has been searched for the phrases never deletes, read create and change only, and does not delete: 0 hits, and it says what the take does with its made-up contacts; (4) the decisions file states the chosen option. Until the record is complete the take is blocked, nothing is touched in the CRM, and no sheet may say never deletes or read, create and change only. Whether an archived contact keeps its e-mail address reserved is not checked.\\n12. GATE, the repeat-send statement: scene 3 and card line 1 are not filmed until the unique index on the contact table (the database rule that refuses a second row for the same contact id) has been seen in the table of the take own database (the loopback re-smoke result), or the studio lead writes here "index not seen, accepted" with the date and time in UTC. In the test program the table is created with a primary key on the contact id (mf.py line 45), which is the same kind of rule; that is not proof for the take database.',
     "The contact-deletion gate was only a risk item with no check row and no rehearsal item (c6j design review M5); it now names archive and permanent delete separately, qualifies every take-script statement as plan text and help text with the code not read (c6k design review M5), records the contradiction between the decisions file (never deletes) and the plan 4 notice (archived at the end), says that an unanswered question leaves the take blocked and nothing unsafe, and has a gate record with four yes-or-no lines that the studio lead writes (c6k naive review B3). Item 12: who writes 'index not seen' is now named (c6k naive review minor). The gate text documents a closed gate, so it can be applied before the studio lead chooses.",
     [("EQ4", "--cleanup"), ("P4", "up to 3 HubSpot contacts archived at the end"), ("P4", "1. the script archives this take's contacts"), ("CA", "scripts/hubspot_probe.py:4-5"), ("CB", "hubspot_probe.py:271-287"), ("SH", "ASSUMED to keep its email reserved"), ("DEC", "2. TAKE IDENTITY"), ("MF", "CREATE TABLE mf_leads")])
''')
replace_edit("rs71", '''edit("rs71", "RS", OLD["rs71"],
     '10. Run the whole take once with a stopwatch; compare to the EST column and re-total.\\n11. Before every rehearsal and before the take, list the active workflows in n8n. Only workflows imported from the folder n8n-flows-real-v5 may be active: the form entry flow, the hook entry flow, the recovery flow, and the shared-step flow if it is active. No workflow from any other folder, and no workflow with the paths mf-form or mf-hook from n8n-flows-film-v5 or an older folder, may be active. Write the list into the studio lead session note (the handoff). (This check needs n8n and is not run yet.)\\n12. Closing check for the CRM key wording, run by the studio lead once the sheet the owner reads is named: search that sheet and the studio lead decisions file for the phrases never deletes, read create and change only, and does not delete; 0 hits are required, and the sheet must state what the take does with its made-up contacts (archive or nothing), as the studio lead chose.\\n13. Scene 3: write down the real seconds between the first reply of scene 2 and the repeat send, and the reply text of the repeat. The gap must be less than 45 seconds (the lease); if it is longer, redo the scene. After the repeat the CRM list must still show 1 row and the test mailbox 1 mail; if not, stop and tell the studio lead.',
     "Eleven flow folders carry the same webhook paths mf-form and mf-hook; only real-v5 may be live (c6j design review minor and c6i review). Split of the old row 6 (c6k design review M4): the items that do not depend on saving (workflow list, closing check, repeat-send seconds) are in this row and need no answer; the old item 12 (execution-list check) moved into the scene 1 row, which waits for the saving answer and for the import check. The shared-step flow is no longer a guess: it may be active if it is active, because it is a real-v5 file (c6k naive review, row 6). Item 13 now has a target (under 45 seconds) and a pass test (c6k naive review, row 6).",
     [("EVDIR", "n8n-flows-real-v5"), ("DEC", "2. TAKE IDENTITY"), ("MF", "CREATE TABLE mf_leads")])
''')
replace_edit("rs30a", '''edit("rs30a", "RS", OLD["rs30"],
     "Before scene 1 the studio lead (not the owner) deletes every execution made before the take (rehearsal and smoke runs) in n8n's execution list and writes the time (UTC) of that clean-up on this sheet as the take start time. Then the studio lead checks on the screen that every row shows a start time after the take start time and that no row shows rehearsal data. This hides the old runs from the screen; whether it erases them from n8n's database is not verified (the start notes say a deleted run is only marked deleted until pruning; the re-smoke plan says deletion is removal of the container). New rows from the recovery flow (one run every 30 seconds) are expected and are not a fault. The same check is made before every rehearsal and again before scene 2, with the same take start time. If a row older than the take start time still shows, the owner stops and tells the studio lead.",
     "The old gate 'list shows 0 rows' cannot be passed: the recovery flow runs every 30 s and the take saves every run, so the list refills within 30 s (c6j design review M1). It now says who deletes (the studio lead), gives the start time that makes 'a row from before the take' testable (c6k naive review, row 22), marks the hide-only behaviour as not verified (c6k design review m3), and holds the old item 12 of the rehearsal list (c6k design review M4). The row also assumes saved runs, which are true only after the flow files are edited and imported (c6k design review M4), so it waits for the import check.",
     [("JR", '"secondsInterval": 30'), ("NS", "a run that is not to be saved is only marked deleted"), ("PLAN", "| executions (take) |"), ("PLAN", "deletion = container removal")], dep="L-SAVE, C-4")
''')
replace_edit("rs41b", '''edit("rs41b1", "RS", "", "Line 1, statement, spoken: \\"A lead sent twice with the same id is processed once. We say this only when the second send comes within 45 seconds of the first. The 45 seconds is a setting: for that long the system keeps a lead for the run that took it first.\\"",
     "Split of the old row 13 (c6k design review M1): this row holds only the statement and the lease sentence, in plain words (c6k naive review: 'reserved to its first run' replaced; the word claim is not used for the video). The studio lead's own words were 'a gap longer than the lease is not claimed' (ORDERS.md answer Q21.2); this sentence says the same in plain words and is the question L-LEASE.",
     [("ORD", "Q21.2:")], dep="L-CARD, L-LEASE", span=("Line 1, claim: a lead sent twice", "processed once."))
edit("rs41b2", "RS", "", "Line 2, alerts, spoken: \\"We make no statement about how quickly an alert mail arrives.\\" Line 3, retention, spoken: \\"The made-up name and e-mail address sent to n8n may stay in n8n's database until n8n's automatic clean-up removes them; we did not measure how long that takes.\\" Line 4, not tested, spoken: \\"Not tested: other mailboxes, other CRMs (customer-record systems), alerts sent as chat messages, other lease settings. One machine, made-up people, our own runs.\\"",
     "Split of the old row 13 (c6k design review M1): alerts, retention and not-tested lines. The retention line is worded so that it is true whether saving is all or none, because the request body reaches n8n's database in both cases (N8N-START.md lines 44 to 46); 'may stay' replaces the setting claim 'stay in n8n's saved runs', since the leak scan has not run and page statement 18 is UNBACKED (c6k design review m2). 'name and address' is now 'name and e-mail address'. 'pruning' is now 'automatic clean-up', 'Slack alert' is 'alerts sent as chat messages', and the vague 'we do not claim ...' is a plain sentence (c6k naive review, row 13). Old lines 2 and 3 (80 kills, recovery time) are cut because the K3B 'mail left' wording is false and the recovery line contradicts the data.",
     [("MF", "def k3b"), ("RS", "Added 17:40Z (lead note, lane3 HB189)"), ("NS", "2. The lead fields (name, e-mail) DO reach")], dep="L-CARD, L-LEASE", span=("Line 2, history (older flow version v3", "own runs."))
''')
replace_edit("rs41a", '''edit("rs41a", "RS", OLD["rs41a"], "Voice over one card, four short lines.", "Card lines 2 and 3 are cut, so six becomes four. All card rows apply together or not at all (c6k design review M1).", [("RS", "| 12. Closing card |")], dep="L-CARD, L-LEASE")
''')
# rs44 per-scene mapping
rep('''"- The one video: scenes 1 to 4 and the closing card (scene 12): 25 + 40 + 25 + 60 + 30 = 180 s, 3 min. The next two lines''', '''"- The one video: scenes 1 to 4 and the closing card (scene 12): scene 1 25 s + scene 2 40 s + scene 3 25 s + scene 4 60 s + closing card 30 s = 180 s, 3 min. The next two lines''')
rep('''"The old total counts cut scenes (c6j design review m4).", [("DEC", "1. SCOPE")])
edit("rs47"''', '''"The old total counts cut scenes (c6j design review m4). The five times (25, 40, 25, 60, 30 s) were checked against the Time column of the run sheet rows 1, 2, 3, 4 and 12 and add to 180 (c6k design review m6).", [("DEC", "1. SCOPE")])
edit("rs47"''')
# rs33b
rep('"60 s EST (real wait: not measured on the flows of this take; planning only: the lane3 runs on the film-v4 stand-in flows ended 60.1 to 61.9 s after the crash)"', '"60 s EST (real wait: not measured on the flows of this take; planning only, never said on screen or in the voice: the lane3 runs on the film-v4 stand-in flows ended 60.1 to 61.9 s after the crash)"')
# rs32
rep('''Second caption line: "Not claimed: a second send after a gap longer than the lease, the 45 seconds for which a lead stays reserved to its first run." No result exists for this repeat send on the flows of this take, so the rehearsal must show the repeat reply, and the real seconds between the first reply and the repeat (write them on this sheet), before the take.''', '''Second caption line: "We say this only when the second send comes within 45 seconds of the first. The 45 seconds is a setting: for that long the system keeps a lead for the run that took it first." No result exists for this repeat send on the flows of this take, so the rehearsal must show the repeat reply, and the real seconds between the first reply and the repeat (write them on this sheet; the gap must be less than 45 seconds), before the take.''')
rep('''the lead gave that sentence in brackets, not as a caption, so the caption text is a lead question (L-LEASE).''', '''the studio lead gave that sentence in brackets, not as a caption, so the caption text is a question (L-LEASE). The row assumes the execution list shows runs, which is true only after the flow files are edited and imported, so it also waits for the import check (c6k design review M4).''')
rep('''[("ORD", "Q21.2:"), ("DEC", "1. SCOPE")], dep="L-LEASE")''', '''[("ORD", "Q21.2:"), ("DEC", "1. SCOPE")], dep="L-LEASE, C-4")''')
# rs82 wording
rep("(the card makes no alert-delay claim; it says only that alerts are not claimed to arrive quickly)", "(the card makes no statement about alert delay: it says only that we make no statement about how quickly an alert mail arrives)")
# page rows figure-free
replace_edit("pg105", '''edit("pg105", "PG", "The only v4 recovery figure is a lane3 relay: K1 recovered in 144.3 s at its lease of 120 s (n=1, v4 K1).",
     "The v4 recovery figure is a lane3 relay: K1 recovered in 144.3 s at a lease of 120 s (n=1, v4 K1). Lane3 also ran crash tests at a 45 s lease on film-v4 stand-in flows; they are in statement 20, which is not for the web page.",
     "Statement 14 contradicts statement 20 (c6j design review m5). The new text points to statement 20 without its figure, so it is safe whatever the studio lead answers about the web page (c6k design review M2).", [("RES", "| 7709d058-v4 | K3 | 1 |")])
''')
replace_edit("pg120a", '''edit("pg120a", "PG", OLD["pg17"], "at the 45 s film lease lane3 ran crash tests on film-v4 stand-in flows (statement 20, not for the web page); nothing is measured on real-v5.",
     "Statement 17 says nothing is measured at 45 s; statement 20 on the same page gives the lane3 runs. The new text carries no figure (c6k design review M2).", [("RES", "| 873a908a-film-v4-lease45 | K1 | 5 |")])
''')
replace_edit("pg120b", '''edit("pg120b", "PG", "Rough rule from lane3: about the lease plus 25 s; the 20 s data is lease + 40 s so treat the rule as rough.",
     "Rough rule from lane3: about the lease plus 25 s; the 20 s laptop data is up to lease + 40 s and the 45 s film-v4 runs of statement 20 ended sooner than lease + 25 s, so the rule fits neither and is not used on screen.",
     "Statement 17 keeps a rule the 45 s data does not support (c6j design review m5). The new text carries no figure of statement 20 (c6k design review M2).", [("RES", "| 873a908a-film-v4-lease45 | K1 | 5 |")])
''')
rep('''"- Lease 45 s: measured only on film-v4 stand-in flows by lane3 (statement 20), not on real-v5. Lease 120 s: one lane3 figure only.",
     "Same contradiction in the honest-limits list.",''', '''"- Lease 45 s: measured only on film-v4 stand-in flows by lane3 (statement 20, not for the web page), not on real-v5. Lease 120 s: one lane3 figure only.",
     "Same contradiction in the honest-limits list. No figure of statement 20 (c6k design review M2).",''')
rep('''"Every lane3 number below is a lead relay, except the 18 crash runs of statement 20: the audit read their lane3 results table''', '''"Every lane3 number below is a lead relay, except the 18 kept crash runs of statement 20 (two voided runs, VOID-fl45k3b and VOID-fl45k6c, are not counted): the audit read their lane3 results table''')
rep('''(c6j design review m5).", [("RES", "| 873a908a-film-v4-lease45 | K1 | 5 |")])
edit("pg105"''', '''(c6j design review m5).", [("RES", "| 873a908a-film-v4-lease45 | K1 | 5 |"), ("RCO", "VOID-fl45k3b K3")])
edit("pg105"''') if False else None
# pg134
rep('''19. NOT USED in the one video or on its closing card (relayed for lane3 v4 flows, not the flows of the video; RESULTS.md lines 78 and 79). "An alert''', '''19. NOT USED in the one video or on its closing card, and NOT FOR THE WEB PAGE unless the studio lead says yes (relayed for lane3 v4 flows, not the flows of the video; RESULTS.md lines 78 and 79). "An alert''')
# pg149a
replace_edit("pg149a", '''edit("pg149a", "PG", OLD["pg149a"],
     '20. "On the film-v4 stand-in flows (not the flows in the video), with a 45 s lease, each of the 18 kept crash runs reached a final state 60.1 to 61.9 s after the crash." Final states: 10 runs done (K1 5, K2 5) and 8 runs unknown with one alert to the owner (K3B 5, K3 3, in this page\\'s names), which is the intended end state of those two cases. Two more runs of the same series were voided and are not counted: VOID-fl45k3b (it never reached a final state, 338.7 s) and VOID-fl45k6c (the stand-in services were not up); the cause is unknown. Not measured on real-v5.',
     "Statement 20 said all 18 runs finished, but 8 of 18 ended unknown (RESULTS.md lines 91 and 92). 'About a minute' is the rounded wording of question L-ROUND, so it is removed here as well. 'Each of 18' now says 18 KEPT runs and names the two voided runs (c6k design review M3). This row carries the figure and is applied together with the row that marks statement 20 not for the web page.",
     [("RES", "| 873a908a-film-v4-lease45 | K3 | 5 |"), ("RES", "| 873a908a-film-v4-lease45 | K6 | 3 |"), ("RCO", "VOID-fl45k3b K3"), ("RJL", '"label": "VOID-fl45k3b"')], dep="L-ROUND, L-PAGE")
''')
# pg153 mailbox wording
rep("(intake got 0 mails in 5 of 5 runs)", "(the test mailbox received 0 mails in 5 of 5 runs)")
rep("(intake got 1 mail in 3 of 3 runs)", "(the test mailbox received 1 mail in 3 of 3 runs)")
# pg154 / pg148 sources unchanged
# ns27 override statement
rep("A flow's own workflow settings override the instance settings (n8n behaviour, not verified here), so the four real-v5 flow files (mf-form, mf-hook, mf-recovery, mf-sub-crm-mail in the folder n8n-flows-real-v5) must carry saveDataSuccessExecution all, saveDataErrorExecution all and saveManualExecutions false. After those flow-file edits the flows must be imported again and one run must be seen in the execution list before the take.",
    "Whether a flow's own saving setting overrides the instance setting is not verified here (n8n was not run). The four real-v5 flow files (mf-form, mf-hook, mf-recovery, mf-sub-crm-mail in the folder n8n-flows-real-v5) carry their own settings (none today), so they are set to saveDataSuccessExecution all, saveDataErrorExecution all and saveManualExecutions false; this is right whichever setting n8n lets win. After those flow-file edits the flows must be imported again and one run must be seen in the execution list before the take (the import check).")
rep('''"Do not rely on the instance setting alone; changing the flow files changes their file hashes, so re-import and one run are required."''', '''"Do not rely on the instance setting alone; changing the flow files changes their file hashes, so re-import and one run are required. The old text stated n8n's precedence rule as fact while it was not verified (c6k naive review B1); the edit is now safe under either precedence, and a pass or fail test (override test C-11b) is in the check list."''')
# ns48: people words
rep("no lead field carries either.", "no form field carries either.")
rep("FAIL: re-scope the page claim to what the scan showed (statement 18); never change the test to make it pass.", "FAIL: re-scope the page statement to what the scan showed (statement 18); never change the test to make it pass.")
rep("Who builds the scan: the lead's builder extends t7b in mf.py.", "Who builds the scan: a builder named by the studio lead extends t7b in mf.py; the studio lead runs the scan before the first rehearsal and again after any change to a flow file or to a saving setting.")
# mf rows neutral
replace_edit("mf276", '''edit("mf276", "MF", "Pass: key 0 hits and SMTP password 0 hits (credentials are encrypted at rest; they must not appear in execution data), name and e-mail 0 hits when execution saving is off",
     "SAVING-OFF CHECK ONLY (line 278 forces saving off, so a pass here says nothing about runs that n8n saves; the leak scan for saved runs, once written, is described in N8N-START.md under T7b for the take). Pass: key 0 hits and SMTP password 0 hits (credentials are encrypted at rest; they must not appear in execution data), name and e-mail 0 hits when execution saving is off",
     "The docstring presented this test as the privacy test of the take. The new text is true whether the take saves runs or not, so the row needs no answer (c6k design review m4).", [("MF", "EXTRA.update(EXECUTIONS_DATA_SAVE_ON_SUCCESS")])
''')
replace_edit("mf320", '''edit("mf320", "MF", "execution saving off at env and workflow level: hits per needle: %s",
     "execution saving forced off by this test (says nothing about runs that n8n saves): hits per needle: %s",
     "The printed result line also said 'execution saving off' as if it described the take (c6j design review M7). The new line is short and true either way, so the row needs no answer (c6k design review m4 and naive minor on a long printed line).", [("MF", "def t7b")])
''')
# ns4a/b dep token and DEP overrides appended before sorting
rep('''# ---------------------------------------------------------------- order and numbering''', '''# ---------------------------------------------------------------- dependency overrides (one place)
CARD = ["rs82", "rs80", "rs41a", "rs41b1", "rs41b2", "rs41c", "rs33d", "rs14", "rs5b"]
DEP = {"rs33a": "L-ROUND", "pg161": "L-ROUND", "pg154": "L-PAGE", "pg134": "L-PAGE", "pg148": "L-PAGE",
       "ns4a": "L-ONEDB, C-8", "ns4b": "L-ONEDB, C-8"}
for e in EDITS:
    if e["key"] in CARD:
        e["dep"] = "L-CARD, L-LEASE"
    if e["key"] in DEP:
        e["dep"] = DEP[e["key"]]

# ---------------------------------------------------------------- order and numbering''')
open(p, "w", encoding="utf-8").write(s)
print("ok")
