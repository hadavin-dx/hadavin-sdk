"""Builds REPORT-c6j.md. Old text in the edit table is copied from the files (never typed by hand).
Every old text must occur exactly once on one line of its file, else this script stops."""
import sys, re, os, json

T = "/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/c6/tree/handover"
H = "/home/user/hadavin-sdk/handover/core-hardening"
C6 = H + "/c6-skip-audit"
F = {
    "RS": T + "/demo/VIDEO-RUNSHEET.md",
    "PG": T + "/demo/n8n-flows/PAGE-STATEMENTS-V4.md",
    "NS": T + "/demo/n8n-flows/N8N-START.md",
    "MF": T + "/demo/n8n-mainframe/mf.py",
    "JF": T + "/demo/n8n-flows-real-v5/mf-form.json",
    "JH": T + "/demo/n8n-flows-real-v5/mf-hook.json",
    "JR": T + "/demo/n8n-flows-real-v5/mf-recovery.json",
    "JS": T + "/demo/n8n-flows-real-v5/mf-sub-crm-mail.json",
    "ONE": H + "/inputs/DECISION-one-store.md",
    "DEC": H + "/inputs/DECISIONS-2026-11-16.md",
    "PLAN": H + "/inputs/plan-wp6-resmoke-v5.md",
    "FND": T + "/flows-audit/FINDINGS.md",
    "RES": C6 + "/raw-lane3/RESULTS.md",
    "H6": C6 + "/REPORT-c6h.md",
    "RD": C6 + "/review-c6i-design.md",
    "RN": C6 + "/review-c6i-naive.md",
    "RDES": C6 + "/review-design.md",
    "R6I": C6 + "/REPORT-c6i.md",
    "ORD": H + "/ORDERS.md",
    "QST": H + "/QUESTIONS.md",
    "EV": C6 + "/evidence-c6i/02-workflow-settings.txt",
    "EV1": C6 + "/evidence-c6i/01-flow-folders.txt",
}
LINES = {}


def lines(k):
    if k not in LINES:
        LINES[k] = open(F[k], encoding="utf-8", errors="replace").read().split("\n")
    return LINES[k]


def find(k, anchor, nth=None):
    hits = [i + 1 for i, l in enumerate(lines(k)) if anchor in l]
    if nth is not None:
        return hits[nth]
    if len(hits) != 1:
        sys.exit("ANCHOR %s %r matched %d lines %s" % (k, anchor, len(hits), hits[:6]))
    return hits[0]


def src(*pairs):
    out = []
    for k, a in pairs:
        out.append("%s:%d" % (k, find(k, a)))
    return ", ".join(out)


EDITS = []


def edit(key, fk, old, new, why, sources=(), whole_line=None, status="NOT APPLIED"):
    if whole_line:
        old = lines(fk)[whole_line - 1]
        ln = whole_line
    else:
        hits = [i + 1 for i, l in enumerate(lines(fk)) if old in l]
        if len(hits) != 1:
            sys.exit("EDIT %s old text matched %d lines %s: %r" % (key, len(hits), hits, old[:70]))
        ln = hits[0]
        if lines(fk)[ln - 1].count(old) != 1:
            sys.exit("EDIT %s old text occurs more than once on line %d" % (key, ln))
    for bad in ("|", "`"):
        if bad in old or bad in new:
            sys.exit("EDIT %s contains %r, cannot be placed in a table cell" % (key, bad))
    EDITS.append(dict(key=key, fk=fk, line=ln, old=old, new=new, why=why, src=src(*sources), status=status))


BR = "\n"  # a new line inside the file text

# ---------------------------------------------------------------- run sheet
edit("rs4", "RS", "real CRM service in scenes 1 to 5", "real CRM service in scenes 1 to 4",
     "Scene 5 runs on a stand-in CRM and decision 1 cuts it; the sheet itself says scenes 1 to 4 at line 11. Review Minor list item (:4).",
     [("RS", "Scenes 1 to 4: real mail"), ("DEC", "1. SCOPE"), ("FND", "| F-006 |")])
edit("rs5a", "RS", "then the caption is the measured median and max at lease 45, whatever they are.",
     "then no caption carries a number (replaced 2026-11-16: decision 1 of DECISIONS-2026-11-16.md cuts the number 60.1 to 61.9 s, and lead question Q9 defaults to no time caption).",
     "Line 5 still promises a measured number caption; decision 1 and the Q9 default remove it. Review Major 2 (:5).",
     [("DEC", "1. SCOPE"), ("H6", "**Q9. Time wording.**")])
edit("rs5b", "RS", "All V7 and lane3 numbers moved to the closing card as labelled history (older flow version v3, stand-ins, 20 s test lease).",
     "V7 and lane3 numbers are not on the closing card (card lines 2 and 3 are cut, see the closing-card edits below); they stay in the raw files as history.",
     "Line 5 says the numbers sit on the closing card; the closing-card edits below remove them (Question Q1 default). Keeps the sheet consistent with itself.",
     [("RS", "| 12. Closing card |"), ("H6", "**Q1. Closing card.**")])
edit("rs14", "RS", "and appear only on the closing card, labelled as history",
     "and do not appear in the video (the closing card carries none of them after the closing-card edits below)",
     "Same reason as the previous edit; line 14 says the old numbers appear on the closing card.",
     [("RS", "| 12. Closing card |")])
edit("rs23", "RS", "Recovery wording: NONE for now (lead 17:05Z dropped the plus 25 to 30 s caption); after lane3 lease-45 runs land: measured median and max at lease 45 with n and the setting on screen.",
     "Recovery wording: NONE (lead 17:05Z dropped the plus 25 to 30 s caption; decision 1 of 2026-11-16 cut the number 60.1 to 61.9 s; Q9 defaults to no time caption).",
     "Line 23 still plans a measured-number caption. Review Major 2 (:23).",
     [("DEC", "1. SCOPE"), ("H6", "**Q9. Time wording.**")])
edit("rs24", "RS", "Lane3 K3 = killed after the CRM write.",
     "Lane3 K3 = this sheet's K3B (n8n killed while the mail connection was opening, mail not delivered); lane3 K6 = this sheet's K3.",
     "Line 24 gives lane3 K3 a third, wrong meaning. The files agree on the pair: mf.py:158 (K3B: mail NOT yet delivered), RESULTS.md:97 (lane3 K3 = their K3B), page :150 (lead's final naming).",
     [("MF", "def k3b"), ("RES", "Names differ: my K3"), ("PG", "NAMING (lead, final)")])
edit("rs30", "RS", "Executions older than the take are pruned first; if a leftover execution shows, do not open it.",
     "Before scene 1 the lead deletes every execution made before the take (rehearsal and smoke runs) and checks that the execution list shows 0 rows; scene 2 does not start until it shows 0 rows. If a leftover execution still shows, stop and tell the lead.",
     "Saving is set to all for the take (plan v5:125), so rehearsal runs are saved and would show in scene 1; the old text had no check. Review Design Minor 4.",
     [("PLAN", "| executions (take) |"), ("RD", "Edit 5 (N2)")])
edit("rs31", "RS", "to the form entry on the LOOPBACK address, path mf-form.",
     "to the form entry on the LOOPBACK address, path mf-form. The owner types nothing into the lead fields except what the prepared note already contains; never a key, a password or a token in any form field (n8n saves the request body, see T7b case 2 in N8N-START.md).",
     "Do-not rule for the owner: a secret sent in a form field is saved by n8n (N8N-START.md:46, page statement 18). Review Design Minor 8.",
     [("NS", "3. Nobody must send a secret"), ("PG", "18. UNBACKED")])
edit("rs32", "RS", 'Caption: "a lead sent twice with the same id is processed once". The screen is the evidence.',
     'Caption: "a lead sent twice with the same id is processed once". Second caption line (lead answer Q21.2, default (c) of question Q11): "Shown for a second send that arrives while the lead record is still reserved; a second send after the lease has run out is not covered by this video." Unproven on real-v5, to be shown live: no real-v5 same-id-twice result exists (REPORT-c6h.md:42), so the rehearsal must show the repeat reply before the take. The screen is the evidence.',
     "The claim wording is the lead's (ORDERS.md:151 asks for DECISIONS item 1 plus one honest lease sentence); no real-v5 result backs it. Review Design Minor 8 (scene 3 label).",
     [("ORD", "Q21.2:"), ("H6", "Nothing in the audited tree matches a real-v5 same-id-twice")])
edit("rs33a", "RS", 'Caption: "recovery takes about the lease plus 25 to 30 s (an estimate, not measured at 45 s)".',
     'No number in any caption or in the voice (decision 1 of 2026-11-16; Q9 defaults to no time caption); the stopwatch overlay and the label "setting: lease 45 s" are on screen.',
     "Line 33 still carries the dropped caption; the old report said ':33 matches' and was wrong. Review Design Major 2.",
     [("RD", "VIDEO-RUNSHEET.md:33 still has"), ("DEC", "1. SCOPE"), ("RS", "Recovery wording: NONE")])
edit("rs33b", "RS", "60 s EST (real wait: unmeasured at 45 s; planning guess about 70 to 75 s)",
     "60 s EST (real wait: not measured on real-v5; planning only: the film-v4 stand-in flows finished 60.1 to 61.9 s after the crash, RES:89 to RES:92)",
     "The old planning guess (70 to 75 s) is replaced by the lane3 film-v4 range, labelled planning only and never a caption.",
     [("RES", "| 873a908a-film-v4-lease45 | K1 | 5 |"), ("RES", "| 873a908a-film-v4-lease45 | K6 | 3 |")])
edit("rs33c", "RS", "NO NUMBER measured for 45 s. Basis of the estimate:",
     "NO NUMBER on screen (not measured on real-v5). Basis of the older estimate:",
     "Wording only: avoids saying nothing is measured at 45 s, which is false for the film-v4 flows (RESULTS.md:89 to :92).",
     [("RES", "| 873a908a-film-v4-lease45 | K1 | 5 |")])
edit("rs33d", "RS", "Those go on the closing card only.",
     "None of these goes on screen or on the closing card.",
     "The closing-card edits below remove them from the card.",
     [("RS", "| 12. Closing card |")])
edit("rs41a", "RS", "Voice over one card, six short lines.", "Voice over one card, four short lines.",
     "Card lines 2 and 3 are cut (next edit), so six becomes four. Review Design Minor 6.",
     [("RD", "After removing line 3")])
edit("rs41b", "RS",
     " Line 2, history (older flow version v3, stand-ins, 20 s test lease): kill series K1, K2, K3, K3B, 80 kills, 0 lost, 0 doubled; 40 of the 80 (K3, K3B) ended UNKNOWN by design, a person decides. Line 3, recovery: about the lease plus 25 to 30 s, an estimate (lane3 v4 K1 144.3 s at lease 120 s, n=1, relayed independent, plus the 20 s laptop data); the take ran at 45 s, which is NOT measured. Line 4, alerts: v3 sent two alerts on a slow alert send (lane3 3 of 3); v4 one (lane3 n=3 plus laptop 1, relayed). Line 5, retention: the request body, with the made-up name and address, stays in n8n data until pruned (age not measured). Line 6, not tested:",
     " Line 2, alerts: no alert time is claimed and the card must not imply that alerts are always quick (lead note HB189, run sheet line 82). Line 3, retention: the request body and the node data, with the made-up name and address, stay in n8n's saved runs until n8n's pruning removes them (age not measured). Line 4, not tested:",
     "Default of Q1 and Q2 (a): the old line 2 (80 kills, K3/K3B ended unknown) and line 3 (lease plus 25 to 30 s) are cut because K3B 'mail left' is false (mf.py:158), the count '0 lost' counts unknown as not lost, and line 3 contradicts the data. Old line 4 becomes line 2 with the lead's HB189 note; old line 5 says request and node data because saving is now all.",
     [("MF", "def k3b"), ("RS", "Added 17:40Z (lead note, lane3 HB189)"), ("PLAN", "| executions (take) |"), ("H6", "**Q1. Closing card.**")])
edit("rs41c", "RS",
     "V7 first table: K1, K2, K3, K3B, n=20 each, lost 0, doubled 0 (80 kills); K3 and K3B UNKNOWN 20 each. Lane3 v4 K1 144.3 s at lease 120 s (n=1, RELAYED-INDEPENDENT). Lane3 B90: v3 two alerts in 3 of 3; v4 one alert, n=3 plus laptop 1. All labelled as history, none measured at 45 s.",
     "NO NUMBER on the card. The V7 kill series, the lane3 144.3 s figure and the lane3 B90 alert counts are not shown; they belong to stand-in flows, not to the take.",
     "Matches the card text after the previous edit.",
     [("RS", "| 12. Closing card |")])
edit("rs59", "RS", '10. Step-2 fault for a real mailbox and the Slack alert are NOT BUILT; the take says "stand-in" or cuts.',
     '10. Step-2 fault for a real mailbox and the Slack alert are NOT BUILT; the take says "stand-in" or cuts.' + BR +
     "11. GATE, contact deletion (closed until the lead chooses): decision 2 of DECISIONS-2026-11-16.md says the take never deletes contacts, but the program's CRM code does call a delete (REPORT-c6h.md row D2, gate G-7; this audit did not read the code). The take does not start until the lead chooses: (a) change the code so that the take never deletes, or (b) change decision 2 in writing and make every owner sheet say what the CRM key may do. No sheet may say never deletes or read, create and change only until then.",
     "Review Design Minor 8: contact deletion was passed to the lead with no gate. The choice itself is the lead's (question L-DEL).",
     [("DEC", "2. TAKE IDENTITY"), ("H6", "**D2 (decision 2)**")])
edit("rs71", "RS", "10. Run the whole take once with a stopwatch; compare to the EST column and re-total.",
     "10. Run the whole take once with a stopwatch; compare to the EST column and re-total." + BR +
     "11. Before every rehearsal and before the take, list the active workflows in n8n. Only workflows imported from the folder n8n-flows-real-v5 may be active (the entry flows, the recovery flow, and the table-screen flow only if it is used). No workflow from any other folder, and no workflow with the paths mf-form or mf-hook from n8n-flows-film-v5 or an older folder, may be active. Write the list into the handoff. (This check needs n8n and is not run yet.)",
     "Eleven flow folders carry the same webhook paths mf-form and mf-hook; only real-v5 may be live (EV1). Review Design Minor 5 rewords the old rule 'exactly 4 flows active', which may be wrong (a table-screen flow may be a fifth; the sub-workflow may not need to be active).",
     [("EV1", "== n8n-flows-real-v5"), ("RD", "Edit 4 (N1)")])
edit("rs79", "RS", '5. Whether the recovery estimate "lease plus 25 to 30 s" stays as a caption at all, given it is not backed at 45 s; the safe alternative is no recovery wording on screen and the wording only on the closing card.',
     "5. Decided (decision 1 of 2026-11-16 and the Q9 default): no recovery wording and no number on screen, and none on the closing card.",
     "Open decision 5 is answered by decision 1; leaving it open contradicts the sheet. Review Design Major 2 (:79).",
     [("DEC", "1. SCOPE"), ("H6", "**Q9. Time wording.**")])
edit("rs90", "RS", "", "Scene 4 caption (decision 1 of 2026-11-16 and the Q9 default): no number on screen and none in the voice. The screen shows the stopwatch overlay and the label \"setting: lease 45 s\". The 18 crash runs of lane3 (60.1 to 61.9 s) were measured on the film-v4 stand-in flows, not on real-v5, and stay out of the video. No kill-case sentence is spoken (Q2 default (a)): K3B and K3 are not mentioned in scene 4. No alert-delay claim (up to 13 minutes late) is made. Never \"within 60 s\".",
     "Line 90 is a FINAL caption with a number the lead cut (DECISIONS item 1), a kill-case sentence that is false for K3B (mf.py:158), and a 13-minute figure relayed from film-v4 flows at lease 120 s, n=2. Replacing the whole line fixes Major 1 and Major 3 of the old report and review Design Majors 2 and 3.",
     [("DEC", "1. SCOPE"), ("MF", "def k3b"), ("RS", "Raw not seen by me")], whole_line=90)

# ---------------------------------------------------------------- page
edit("pg17", "PG", "at the 45 s film lease nothing is measured.",
     "at the 45 s film lease lane3 measured 60.1 to 61.9 s on film-v4 stand-in flows (statement 20); nothing is measured on real-v5.",
     "Statement 17 contradicts statement 20 on the same page.",
     [("RES", "| 873a908a-film-v4-lease45 | K1 | 5 |")])
edit("pg139", "PG", "- Lease 45 s: nothing measured. Lease 120 s: one lane3 figure only.",
     "- Lease 45 s: measured only on film-v4 stand-in flows by lane3 (statement 20), not on real-v5. Lease 120 s: one lane3 figure only.",
     "Same contradiction in the honest-limits list.",
     [("RES", "| 873a908a-film-v4-lease45 | K1 | 5 |")])
edit("pg149a", "PG",
     "20. \"At the film lease of 45 s, a lead interrupted by an n8n crash was finished about a minute after the crash.\" Seconds from the kill to a final state, all 18 kill runs correct: 60.1 to 61.9 s (K1 5 runs, K2 5, K3B 5, K3 3 in this page's names).",
     "20. \"On the film-v4 stand-in flows (not the flows in the video), with a 45 s lease, each of 18 crash runs reached a final state 60.1 to 61.9 s after the crash.\" Final states: 10 runs done (K1 5, K2 5) and 8 runs unknown with one alert to the owner (K3B 5, K3 3, in this page's names), which is the intended end state of those two cases. Not measured on real-v5.",
     "Statement 20 said all 18 runs finished, but 8 of 18 ended unknown (RESULTS.md:91, :92 show unknown for lane3 K3 x5 and K6 x3). The words about a minute are the Q9 rounded wording, whose default is NO. Review Design Major 2.",
     [("RES", "| 873a908a-film-v4-lease45 | K3 | 5 |"), ("RES", "| 873a908a-film-v4-lease45 | K6 | 3 |"), ("H6", "**Q9. Time wording.**")])
edit("pg149b", "PG", "Raw: lane3 HB194 table; file name not given to me, not in my checkout, I read nothing.",
     "Raw: the lane3 table at handover/core-hardening/c6-skip-audit/raw-lane3/RESULTS.md lines 89 to 92 (read by the c6 audit; the lane3 report named HB194 is not itself in the tree).",
     "Review Design Major 1 of the earlier review: the page and the run sheet said raw not read, while the c6 audit had read RESULTS.md. The sentence must say what was read.",
     [("RES", "| 873a908a-film-v4-lease45 | K1 | 5 |"), ("RDES", "- M1 Run sheet")])
edit("pg150", "PG", "(killed after the mail left: unknown + 1 alert); lane3 K6 = this page's demo K3.",
     "(killed while the mail connection was opening, mail not delivered: unknown + 1 alert); lane3 K6 = this page's K3 (killed after the mail was delivered: unknown + 1 alert).",
     "mf.py:158 says K3B is killed with the mail NOT yet delivered; mf.py:164 says K3 is killed after delivery; RESULTS.md:97 says the same.",
     [("MF", "def k3b"), ("MF", "def k3():"), ("RES", "Names differ: my K3")])
edit("pg153", "PG",
     "lead ends unknown with 1 alert to the owner, no second mail. Plain wording: \"killed after the mail left: the lead ends unknown with one alert to the owner\". n small; no timing in a caption.",
     "lead ends unknown with 1 alert to the owner, no second mail. K3B: killed while the mail connection was opening; the mail was not delivered (intake got 0 mails in 5 of 5 runs). K3: killed after the mail was delivered (intake got 1 mail in 3 of 3 runs). The words killed after the mail left are not used for K3B. n small; no timing in a caption.",
     "Same facts as the previous edit; intake counts from RESULTS.md:22 (lane3 K3, intake_mails=0) and :25 (lane3 K6, intake_mails=1).",
     [("RES", "| K3 [flows 873a908a-film-v4-lease45]"), ("RES", "| K6 [flows 873a908a-film-v4-lease45]")])
edit("pg159", "PG", 'Caption rule: only K1 and K2 (done), or the range. NEVER "within 60 s".',
     'Caption rule: no time caption (Q9 default). NEVER "within 60 s".',
     "Matches the withdrawn caption (next edit).",
     [("H6", "**Q9. Time wording.**")])
edit("pg161", "PG", "", 'Caption wording: none. Decision 1 of 2026-11-16 cut the scene 4 number and Q9 defaults to no time caption; the earlier wording "about a minute after the crash (measured at lease 45 s ...)" is withdrawn. Do not pool medians.',
     "Line 161 still publishes the cut number and the rounded wording. Review Design Major 2.",
     [("DEC", "1. SCOPE"), ("H6", "**Q9. Time wording.**")], whole_line=161)

# ---------------------------------------------------------------- N8N-START
edit("ns15", "NS", "## Execution saving: all four settings are REQUIRED",
     "## Execution saving: the take saves every run (owner 2026-11-16, plan-wp6-resmoke-v5.md line 125), so the execution list in scenes 1 and 2 shows runs",
     "N2: the old text requires none; the plan for the take sets all. Review Design Minor 4.",
     [("PLAN", "| executions (take) |"), ("RDES", "N2 upgrade to Major")])
edit("ns17", "NS", "EXECUTIONS_DATA_SAVE_ON_SUCCESS=none", "EXECUTIONS_DATA_SAVE_ON_SUCCESS=all",
     "plan v5:125 value for the take.", [("PLAN", "| executions (take) |")])
edit("ns18", "NS", "EXECUTIONS_DATA_SAVE_ON_ERROR=none", "EXECUTIONS_DATA_SAVE_ON_ERROR=all",
     "plan v5:125 value for the take.", [("PLAN", "| executions (take) |")])
edit("ns23", "NS", "- SAVE_ON_SUCCESS=none: n8n stores no run data (node inputs and outputs, which hold lead name and e-mail) for runs that succeed.",
     "- SAVE_ON_SUCCESS=all: n8n stores the run data (node inputs and outputs, which hold the made-up lead name and e-mail) for runs that succeed, so the execution list shows them.",
     "Follows the value change.", [("PLAN", "| executions (take) |")])
edit("ns24", "NS", "- SAVE_ON_ERROR=none: the same for runs that fail.", "- SAVE_ON_ERROR=all: the same for runs that fail.",
     "Follows the value change.", [("PLAN", "| executions (take) |")])
edit("ns27", "NS",
     "Without them n8n keeps run data. The lane3 grep (as relayed by the lead, n=1, flows without the four settings): lead name, e-mail AND the key were in the write-ahead file. With the four settings queued (lane3, n=3) and in the laptop T7b: see the T7b section; name and e-mail were still found in the write-ahead file there. The settings reduce what is stored; they do not make it zero. Every flow also carries the same values in its own workflow settings (saveDataSuccessExecution none, saveDataErrorExecution none, saveManualExecutions false).",
     "With these settings n8n keeps run data for every run until its pruning removes it, including the request body (the made-up name and e-mail) and everything the nodes pass on. The earlier lane3 grep (relayed by the lead, n=1, flows without saving settings; tagged UNBACKED in PAGE-STATEMENTS-V4.md statement 18) found name, e-mail and key in the write-ahead file: it is a reason to run the take-settings test T7b below, not a result. A flow's own workflow settings override the instance settings (n8n behaviour, UNVERIFIED here), so the four real-v5 flow files must carry saveDataSuccessExecution all, saveDataErrorExecution all and saveManualExecutions false (the four flow-file edits in the edit table). After those edits the flows must be imported again and one run must be seen in the execution list before the take.",
     "Review Design Minor 4: do not rely on the instance setting alone; changing the flow files changes their file hashes, so re-import and one run are required.",
     [("EV", "n8n-flows-real-v5/mf-form.json"), ("RD", "Edit 5 (N2)")])
edit("ns48", "NS", "My flows never put a key into n8n; the likely route is a key sent as a body field (matches HB171), not proven.",
     "My flows never put a key into n8n; the likely route is a key sent as a body field (matches HB171), not proven." + BR + BR +
     "## T7b for the take (execution saving all; NOT RUN yet; replaces the old pass rule written for saving off)" + BR +
     "Stores to scan, hits counted per store and never merged: (1) n8n's database and its write-ahead and shared-memory files, (2) n8n's log, (3) the exported flow files, (4) the stage journal (the file stage-journal.jsonl named at mf.py line 12), (5) the stage's spend ledger (this audit did not find its path; the builder names it from the take's config), (6) the stage's own log." + BR +
     "Planted values (all made up, built from parts): a fake model key, a fake mail password, a name, an e-mail address." + BR +
     "Case 1, secrets in their proper places: the fake model key sits in the stage key file and the fake mail password in the n8n mail credential; no lead field carries either. PASS: 0 hits for both in all six stores. FAIL: any hit; filming stops, the leak is fixed where the value escapes (a credential or masking fault), and the test is run again unchanged." + BR +
     "Case 2, key in a request body field: one lead is sent whose form field carries the fake key. EXPECTED and PASS: hits for the key in n8n's database (the request body is saved while saving is all) and 0 hits in the stage journal, the spend ledger, the logs and the flow files. This case is the evidence for the written warning never to send a secret in a lead form field. FAIL: a hit in any store other than n8n's database. 0 hits in n8n's database is recorded as a surprise and is not a fail." + BR +
     "Name and e-mail: expected in n8n's database. PASS: 0 hits in the stage journal, the spend ledger and the logs. FAIL: re-scope the page claim to what the scan showed (statement 18); never change the test to make it pass." + BR +
     "Who builds the scan: the lead's builder extends t7b in mf.py. Today it scans only n8n's data folder, n8n's log and the flow JSON (mf.py lines 296 to 320) and forces saving off (line 278), so a pass of today's t7b says nothing about the take. This audit wrote no code.",
     "Review Design Major 1: the old rule 'key in a request body field: 0 hits' cannot pass because the body is saved. Review Naive: T7b, stage journal and spend ledger were not defined.",
     [("NS", "3. Nobody must send a secret"), ("MF", "def t7b"), ("MF", "EXTRA.update(EXECUTIONS_DATA_SAVE_ON_SUCCESS"), ("MF", "JOURNAL, CRMLOG = os.path.join"), ("RD", "Edit 2 (T7b)")])

# ---------------------------------------------------------------- mf.py
edit("mf276", "MF", "Pass: key 0 hits and SMTP password 0 hits (credentials are encrypted at rest; they must not appear in execution data), name and e-mail 0 hits when execution saving is off",
     "SAVING-OFF CHECK ONLY (line 278 forces saving off, so a pass here says nothing about the take, which saves all runs: plan v5 line 125; the take test is described in N8N-START.md under T7b for the take). Pass: key 0 hits and SMTP password 0 hits (credentials are encrypted at rest; they must not appear in execution data), name and e-mail 0 hits when execution saving is off",
     "Review Design Major 1 and the old report's edit 2: the old docstring presents this test as the privacy test of the take.",
     [("MF", "EXTRA.update(EXECUTIONS_DATA_SAVE_ON_SUCCESS"), ("PLAN", "| executions (take) |")])

# ---------------------------------------------------------------- flow files (N2)
for fk, nm in (("JF", "mf-form.json"), ("JH", "mf-hook.json"), ("JR", "mf-recovery.json"), ("JS", "mf-sub-crm-mail.json")):
    for field in ("saveDataSuccessExecution", "saveDataErrorExecution"):
        edit("j_%s_%s" % (fk, field), fk, '"%s": "none"' % field, '"%s": "all"' % field,
             "N2: the flow's own setting is none, which hides every run in the execution list that scene 1 and 2 film (EV: all 8 flow files carry none/none/false and no error workflow). Value for the take: plan v5:125. Default of the lead question L-SAVE.",
             [("EV", "n8n-flows-real-v5/" + nm), ("PLAN", "| executions (take) |")])

# ---------------------------------------------------------------- F-011
edit("one14", "ONE", "**ONE database for everything we own: the single Postgres instance of the take** (one container, one engine)",
     "**One Postgres server with two databases: n8n's own and the take's** (one container, one engine)",
     "Decision 10 orders this wording (the target); review Design Minor 7 asked for the edit. Row F-011 says n8n still starts on its own SQLite file, so no video or owner text may use the target sentence until the loopback re-smoke shows the engine is Postgres (check C-8).",
     [("DEC", "10. Wording"), ("FND", "| F-011 |")])

# ---------------------------------------------------------------- numbering and substitution
for i, e in enumerate(EDITS, 1):
    e["n"] = i
ids = {e["key"]: e["n"] for e in EDITS}
json.dump(EDITS, open(C6 + "/evidence-c6j/edits.json", "w"), indent=1)


def cell(t):
    return t.replace("\n", "<br>")


def short(fk):
    return fk


# ---------------------------------------------------------------- other tables
def s(*pairs):
    return src(*pairs)


out = []
P = out.append

P("# REPORT-c6j: video audit fix pass, supersedes REPORT-c6i.md (2026-11-16, UTC; IST = UTC + 5:30)")
P("")
P("## 0. Read this first (failures, uncertainty, what was not checked)")
P("- NOTHING IN THE EDIT TABLE HAS BEEN APPLIED. Every edit has the status NOT APPLIED. The word 'closed' in REPORT-c6i.md meant 'written down as text', not 'edited in a file'. This report changes no audited file.")
P("- Static reading only. Not run: n8n, any flow, the harness, git history, the bible (rule R460 is a rule whose text is not on disk), QUEUE rule 6, the original lane3 reports HB171, HB180, HB186, HB189, HB194 (only their relayed numbers and the lane3 table RES are in the tree), the owner sheets v9 to v19 (not in the checked tree, so the lines of v9 quoted by REPORT-c6h.md for contact deletion are NOT verified here), and the contact-deletion code.")
P("- What the cite script proves: that every old text in the edit table occurs, character for character, once on the stated line of the stated file, and that every cited source line exists (the anchor text of each source line was checked when the report was built). It does NOT prove that a claim is true or that a new text is right. Script and raw output: evidence-c6j/ (build_c6j.py, verify-c6j.py, verify-c6j-output.txt).")
P("- The independent reviews of REPORT-c6i.md found it was not safe to apply. This report fixes every Major and Minor of review-c6i-design.md and every item of review-c6i-naive.md (map in section 6). It has NOT yet been reviewed by two independent reviewers (the lead runs that step).")
P("- Two ranges are different numbers: 60.1 to 61.9 s is kill to final state; 52.9 to 54.9 s is from n8n coming back up (RES:89 to RES:92). 45 s is a SETTING (the lease), not a measurement. 'Name and e-mail may appear in n8n's database' means the made-up test person only.")
P("- K3B being false in 'killed after the mail left' does not make K3 false: K3 (mail delivered, then killed) is described correctly by mf.py:164. Only the K3B sentence is wrong.")
P("- Path rule: the audited files are a copy of the branch origin/cloud/flows-audit (header of review-design.md). Edit table paths are the full paths of that copy; a builder applies the same relative path under handover/ on the branch (for example handover/demo/VIDEO-RUNSHEET.md). Edits to DECISION-one-store.md use the repository path directly.")
P("- Edit-table convention: old text and new text are exact file text. '<br>' in a new text means start a new line in the file. Nothing else is abbreviated.")
P("")
P("## 1. Lead questions (text, default used in the edit table, what a different answer changes)")
P("The edit table uses the default of each question. A different answer means the listed edits are not applied or are replaced; the lead says so and a builder re-issues those rows. No edit contains two choices.")
P("")
P("| Question | Text of the question | Default used | If the lead answers differently |")
P("|---|---|---|---|")
P("| Q1 (H6:%d) | Does the closing card (last card of the video, run sheet line 41) stay as the last card? | It stays; lines 2 and 3 are cut and the rest is reworded. | If the card is cut: the three closing-card edits are dropped; nothing else changes. |" % find("H6", "**Q1. Closing card.**"))
P("| Q2 (H6:%d) | Kill cases in scene 4: (a) drop the kill-case wording from scene 4, or (b) keep it labelled film-v4 stand-in? | (a). REPORT-c6h.md gave (b) as its default, REPORT-c6i.md used (a); this report uses (a) because decision 8 allows no real-account smoke and K3B text is false as written. | If (b): the line-90 replacement and the card edit are re-issued with a labelled kill-case sentence (K3B: killed while the mail connection was opening, mail not delivered; K3: killed after the mail was delivered). |" % find("H6", "**Q2. Kill cases in scene 4.**"))
P("| Q9 (H6:%d) | Accept the rounded wording 'about a minute, in the test' in place of the cut number? | NO: no time caption of any kind. | If YES: the lead names the exact caption; edits rs33a, rs90, pg149a and pg161 are re-issued with it. |" % find("H6", "**Q9. Time wording.**"))
P("| Q10 (H6:%d) | Which owner sheet does the owner read? | v19 (newest; says it replaces v4 to v18). No edit here touches an owner sheet. | If another: contact-deletion lines of that sheet are the ones to check (section 7). |" % find("H6", "**Q10. Which owner sheet"))
P("| Q11 (H6:%d) | Which claim wording is in force: (a) 'inside the lease' wording of 10:13 UTC, (b) DECISIONS item 1, (c) item 1 plus one honest lease sentence (ORD:%d)? | (c), used in edit rs32. | If (a) or (b): edit rs32 is re-issued with that wording. |" % (find("H6", "**Q11. Which claim wording"), find("ORD", "Q21.2:")))
P("| L-DEL (new) | The code deletes contacts but decision 2 (DEC:%d) says the take never deletes. Choose (a) change the code so the take never deletes, or (b) change decision 2 in writing and every sheet. | NO DEFAULT: the gate (edit rs59) stays closed until the lead chooses. Recommended: (a), because decision 2 is the lead's written decision and the code was not read here. | Not applicable: the gate has no default. |" % find("DEC", "2. TAKE IDENTITY"))
P("| L-SAVE (new) | Saved runs: does the take really use saving all (plan v5 line %d says owner 2026-11-16 yes)? | Yes, all (edits to N8N-START.md and the four flow files). | If no: the four flow-file edits, ns15 to ns27 and rs30 are dropped and the execution list in scenes 1 and 2 stays empty (scene 1 text then needs a rewrite). |" % find("PLAN", "| executions (take) |"))
P("| L-ONEDB (H6:%d) | Ratify or veto the interim sentence 'n8n keeps its own records in its own database file. Our claim table is in a separate Postgres database. That is two stores.' for any text written before the re-smoke has passed. | The target sentence of decision 10 goes into DECISION-one-store.md (edit one14); viewer-facing text may use only the interim sentence until check C-8 passes. | If vetoed: the interim sentence is not used and no viewer-facing text says anything about the number of databases until C-8 passes. |" % find("H6", "**Interim sentence"))
P("")
P("## 2. Glossary (term, plain meaning, file and line it comes from)")
P("")
P("| Term | Plain meaning | Where it comes from |")
P("|---|---|---|")


def g(term, meaning, *pairs):
    P("| %s | %s | %s |" % (term, meaning, s(*pairs) if pairs else "not defined in any file read"))


g("the take", "the one filmed run of the video.", ("H6", "- \"The take\" = the one recorded"))
g("run sheet", "VIDEO-RUNSHEET.md, the scene-by-scene script (90 lines). RS in this report.", ("H6", "- run sheet: VIDEO-RUNSHEET.md"))
g("page", "PAGE-STATEMENTS-V4.md, the text of the web page that goes with the video. PG in this report.", ("H6", "- page: PAGE-STATEMENTS-V4.md"))
g("closing card", "scene 12, the last on-screen card; its text is one table row, run sheet line 41.", ("RS", "| 12. Closing card |"))
g("decision 1", "lead decision: the one video is REAL-V5 ONLY, scenes 1 to 4; scene 5 and the caption number 60.1 to 61.9 s are cut.", ("DEC", "1. SCOPE"))
g("decision 2", "lead decision: the take never deletes contacts; the owner deletes leftover made-up contacts by hand after the take.", ("DEC", "2. TAKE IDENTITY"))
g("decision 8 / 10", "8: no extra real-account smoke (a loopback re-smoke plus one made-up lead instead). 10: wording 'one Postgres server with two databases'.", ("DEC", "8. Real-account smoke"), ("DEC", "10. Wording"))
g("real-v5", "the n8n flow set in folder n8n-flows-real-v5 that talks to the real mail and CRM services; the only set in the one video.", ("H6", "- real-v5 = the n8n flows in folder"))
g("film-v4, film-v5", "flow sets that talk to stand-in (fake, controlled by us) services; their scenes (5 to 11) are a possible later video. Newer film-v5 differs from real-v5 only in the files mf-recovery.json and mf-sub-crm-mail.json.", ("H6", "- film-v4 / film-v5 = flow sets"), ("EV1", "Files n8n-flows-real-v5/mf-recovery.json"))
g("stand-in", "a fake service we control (fake CRM, fake mail server, fake model) used instead of the real one.", ("H6", "- film-v4 / film-v5 = flow sets"))
g("lane3", "the separate test session and git branch (origin/demo/lane3) that ran the 45-second-lease crash tests; its table is RES.", ("H6", "| lane3 | the separate test session"))
g("HB171, HB180, HB186, HB189, HB194", "numbers of lane3 reports relayed to the demo session by the lead; the files do not say what HB stands for. HB189: alert may be late; HB194: the 18 crash runs at lease 45 s.", ("NS", "lane3 HB171"), ("RS", "Added 17:40Z (lead note, lane3 HB189)"), ("PG", "## Statement 20"))
g("lease", "how long a claimed lead record stays reserved before the recovery sweep may take it again; the take uses 45 s; older tests used 20 s and 120 s. It is a setting, not a measurement.", ("H6", "- lease = how long a claimed lead record"))
g("lead record / lead id", "one made-up sales contact the flows process / its identifier. 'The lead' alone means the studio lead (the decision maker), not a sales contact.", ("H6", "| lead | the studio lead"))
g("alert", "the one mail the system sends to a named address when it cannot tell what happened to a lead record.", ("H6", "- alert = the one mail"))
g("end state unknown", "final state of a lead record when the program cannot tell whether the contact and mail happened; a person decides.", ("H6", "- end state `unknown`"))
g("K1", "crash test: n8n killed after the claim insert, before the CRM write.", ("MF", "def k1"), ("RS", "| 4. Kill n8n mid-lead"))
g("K2", "crash test: n8n killed after the CRM write, before the mail step.", ("MF", "def k2"))
g("K3B (lane3 name K3)", "crash test: n8n killed while the mail connection was opening; the mail was NOT delivered (intake got 0 mails in 5 of 5 runs); end state unknown, one alert.", ("MF", "def k3b"), ("RES", "Names differ: my K3"))
g("K3 (lane3 name K6)", "crash test: n8n killed after the mail was delivered, before the table update; intake got 1 mail (3 of 3 runs); end state unknown, one alert.", ("MF", "def k3():"), ("PG", "NAMING (lead, final)"))
g("T7b", "a privacy test in mf.py (function t7b): plants a fake model key, a fake mail password, a name and an e-mail, runs leads and searches stores for them. Today it forces execution saving off.", ("MF", "def t7b"))
g("saving off / saving all", "the n8n setting EXECUTIONS_DATA_SAVE_ON_SUCCESS and _ON_ERROR: none = n8n keeps no run data, all = it keeps every run (what the execution list shows). The take uses all.", ("PLAN", "| executions (take) |"))
g("execution list", "n8n's screen listing past runs; filmed in scenes 1 and 2 (run sheet line 4).", ("RS", "the n8n execution list IS filmed"))
g("stage journal / spend ledger", "files kept by the stage (the program step that asks the model to qualify a lead): the journal records a model call before it is made (named at mf.py:12); the spend ledger path is not found in any file read.", ("MF", "JOURNAL, CRMLOG = os.path.join"))
g("write-ahead file", "the database's log file (the -wal file) where recent writes sit before they reach the main file.", ("NS", "ONLY in the write-ahead file"))
g("M1, M2, M3", "the three Majors of review-design.md (M1 scene 4 caption has a number against the sheet's own rules; M2 saved runs invalidate T7b; M3 'killed after the mail left' is false for K3B).", ("RDES", "- M1 Run sheet"), ("RDES", "- M2 Saved runs"), ("RDES", "- M3 F-007"))
g("N1 to N6", "new items of review-design.md: N1 stale flow folders share webhook paths; N2 execution list empty because flows save nothing; N3 client-build item; N4 duplicate of M3; N5 closing card says 80 kills; N6 reply node naming.", ("RDES", "N1 Major accepted"))
g("m1 to m4", "minor items of review-design.md (m1 flow-set diff claim has no command output; m2 bible not on disk; m3 statement 20 counts; m4 add lane3 HB194 raw to not-checked).", ("RDES", "m1 flow-set diff"))
g("F-006, F-007, F-011, F-020, F-022, F-023, F-025", "numbered findings in FINDINGS.md: F-006 run sheet claims real CRM in scene 5; F-007 K3/K3B described three ways; F-011 'one database' / n8n keeps run history; F-020 stage journal owner; F-022 desk door 502 reply; F-023 table screen README conflict; F-025 old flows can double-mail.", ("FND", "| F-006 |"), ("FND", "| F-007 |"), ("FND", "| F-011 |"), ("FND", "| F-020 |"), ("FND", "| F-022 |"), ("FND", "| F-023 |"), ("FND", "| F-025 |"))
g("c6b to c6j", "successive versions of this audit report; c6j (this file) supersedes c6i; c6h is the last full report (REPORT-c6h.md).", ("H6", "# C6h (revision of C6g)"))
g("D2 / G-7, G-4", "row D2 of REPORT-c6h.md: decision 2 against the code that deletes contacts; G-7 and G-4 are gates in its gate list (G-4: only real-v5 imported and active).", ("H6", "**D2 (decision 2)**"))
g("UNBACKED, RELAYED-INDEPENDENT, MEASURED-ON-LAPTOP", "tags on numbers: no raw file / relayed from another session without the raw file / read by the lead from laptop result files.", ("RS", "MEASURED-ON-LAPTOP lead-read ="), ("RS", "RELAYED-INDEPENDENT = lane3"))
g("V7", "laptop result files and the lead's read of them (V7-NUMBERS-lead-read.md) behind the '80 kills' numbers, measured on older v3 flows with a 20 s lease on stand-ins.", ("H6", "- V7: laptop files"))
g("T13, T15, B90, AF1", "earlier test names in the run sheet history lines (T13 same-id and database kill, T15 CRM refuses, B90 alert-send case, AF1 alert refused twice); not used by any edit here.", ("RS", "T13 (n=13"))
g("Q21.2, Q15.3", "lead answers in ORDERS.md and an earlier order: the claim wording and the lease sentence.", ("ORD", "Q21.2:"), ("H6", "Narrow claim: **a lead sent twice"))
g("R460", "the rule behind the audit; its text is not on disk (not checked).", ("H6", "- R460: the rule behind"))
P("")
P("## 3. EDIT TABLE (every edit: NOT APPLIED)")
P("Sources: short names resolve to the full paths in section 8. Line numbers in the second column are lines of the target file as it is now.")
P("")
P("| # | Target file (full path) | Line | Old text (exact) | New text (exact) | Reason and source file:line | Status |")
P("|---|---|---|---|---|---|---|")
for e in EDITS:
    P("| %d | %s | %d | `%s` | `%s` | %s Sources: %s | %s |" % (e["n"], F[e["fk"]], e["line"], cell(e["old"]), cell(e["new"]), e["why"], e["src"], e["status"]))
P("")
P("## 4. Ratings (not edits)")
P("")
P("| Item | Rating | Basis |")
P("|---|---|---|")
P("| F-006 | Major (the finding said Blocker) | closed by decision 1 once the first edits are applied; RDES:%d |" % find("RDES", "F-006 Major accepted"))
P("| F-007 | Major | three sources disagree; fixed by the K3B/K3 edits; mf.py:%d |" % find("MF", "def k3b"))
P("| F-011 | Major | edit one14 plus checks C-8 and T7b for the take; RD:%d |" % find("RD", "7 F-011 rated Major"))
P("| F-020, F-022, F-023, F-025, N3, N5, N6 | Nit | accepted by review-design.md; F-022: real-v5 mf-form.json sets n8n_error false at lines 238, 254, 293 so the bug does not recur in the take flows (R6I:%d) |" % find("R6I", "F-022: real-v5"))
P("| N1 | Major, operational | check C-3 and edit rs71 |")
P("| N2 | Major for filming, gate | flow-file edits, ns15 to ns27, rs30 |")
P("| N5 | Nit | closing-card edits rs41a to rs41c remove the 80-kills line |")
P("")
P("## 5. Checks (not edits; status says whether it was run)")
P("")
P("| # | Check | Needs | Status |")
P("|---|---|---|---|")
P("| C-1 | Every old text of section 3 occurs once on its line | file read | DONE: evidence-c6j/verify-c6j-output.txt |")
P("| C-2 | The 8 flow files all carry none, none, false and no errorWorkflow | file read | DONE (static): EV:%d to EV:%d |" % (find("EV", "n8n-flows-real-v5/mf-form.json"), find("EV", "n8n-flows-film-v5/mf-sub-crm-mail.json")))
P("| C-3 | Only real-v5 flows are active before each scene (list active workflows) | n8n | NOT RUN |")
P("| C-4 | Import the four edited real-v5 files and see one run in the execution list; file hashes have changed, so the check is repeated | n8n | NOT RUN |")
P("| C-5 | Execution list shows 0 rows before scene 2 | n8n | NOT RUN |")
P("| C-6 | T7b case 1, case 2 and the name and e-mail rule on six stores (N8N-START.md section added by edit ns48) | built scan, n8n | NOT RUN, scan not built |")
P("| C-7 | real-v5 and film-v5 differ only in mf-recovery.json and mf-sub-crm-mail.json | file read | DONE (static): EV1:%d to EV1:%d (V5-NODE-DIFF.txt also sits in real-v5; check the import reads only .json files: NOT RUN) |" % (find("EV1", "== diff -rq"), find("EV1", "diff exit")))
P("| C-8 | Loopback re-smoke shows the n8n engine is Postgres before any text says one Postgres server with two databases | n8n, Postgres | NOT RUN |")
P("| C-9 | The unique index on the claim table exists (ORD:%d: say 'index not seen' if it cannot be seen) | table definition | NOT RUN here |" % find("ORD", "Q21.2:"))
P("")
P("## 6. Coverage: every Major and Minor of the two reviews")
P("")
P("| Review item | Where fixed |")
P("|---|---|")
cov = [
    ("Design Major 1 (T7b cannot pass)", "ns48 (two cases, six stores, pass and fail rule, who builds), mf276, ns27"),
    ("Design Major 2 (M1 incomplete: :33, :5, :23, :79, :4, :90, page :149, :161, statement 20 8 of 18, 13 min)", "rs4, rs5a, rs5b, rs14, rs23, rs33a to rs33d, rs79, rs90, pg149a, pg149b, pg159, pg161, pg17, pg139"),
    ("Design Major 3 (K3B/K3 wording, page :150 :153, run sheet :24, card line)", "rs24, rs41b, rs90, pg150, pg153"),
    ("Design Minor 4 (N2 re-import, pre-take deletion gate)", "ns15 to ns27 (re-import and one run), rs30, flow-file edits, checks C-4 and C-5"),
    ("Design Minor 5 (N1 reword)", "rs71, check C-3"),
    ("Design Minor 6 (N5: no-op label, six to five)", "rs41a to rs41c (card lines 2 and 3 cut, so four lines)"),
    ("Design Minor 7 (F-011 has no edit)", "one14, check C-8, question L-ONEDB"),
    ("Design Minor 8 (contact-deletion gate, scene 3 label, key-in-field rule, card line 5)", "rs59, rs32, rs31, rs41b"),
    ("Naive: no file paths, no exact strings", "section 3 (full path, line, exact old and new text)"),
    ("Naive: unexplained labels", "section 2"),
    ("Naive: Q1, Q2, Q9, Q10, Q11 without text", "section 1"),
    ("Naive: edits 4 and 6 are not edits", "section 4 and section 5 (checks and ratings kept out of the edit table)"),
    ("Naive: 'or' choices", "removed: every edit has one new text; the question that changes it is in section 1"),
    ("Naive: 'closed' meant written, not applied", "section 0 and the Status column"),
    ("Naive: what 35 cites 0 mismatches proves", "section 0"),
    ("Naive: 52.9 to 54.9 s against 60.1 to 61.9 s; 45 s a setting; made-up data; K3B false versus K3", "section 0 and section 2"),
]
for a, b in cov:
    P("| %s | %s |" % (a, b))
P("")
P("## 7. Not covered here (each with the exact next step)")
P("- Owner sheets (steps-edits v9 to v19) are not in the checked tree: the lines REPORT-c6h.md quotes for 'never deletes' (v9 :18, :40, :169, :285, :288) are not verified and not edited. Next step: the builder who applies section 3 opens the sheet the lead names in Q10 and fixes those lines after the lead answers L-DEL.")
P("- Scenes 5 to 11 (run sheet lines 34 to 40) are cut from the one video by decision 1 but their rows still hold stale text (K3 and K3B history, V7 numbers). They are not filmed, so no edit is made; marking them 'not in the one video' is a lead choice (it has not been asked before): next step is for the lead to say yes or no.")
P("- plan-wp6-resmoke-v5.md still names film-v5 at the lines listed in REPORT-c6h.md section 4 (plan edit text given there); not repeated here.")
P("- The stage's spend ledger path was not found; the T7b scan needs it (edit ns48).")
P("- Line 52 and line 30 of the run sheet still say 'the request body stays in n8n data until pruned'; that stays true with saving all (the node data is kept too), so it is left.")
P("")
P("## 8. Short names of files used in the Sources column")
P("")
P("| Short | Full path |")
P("|---|---|")
for k in ("RS", "PG", "NS", "MF", "JF", "JH", "JR", "JS", "ONE", "DEC", "PLAN", "FND", "RES", "H6", "RD", "RN", "RDES", "R6I", "ORD", "QST", "EV", "EV1"):
    P("| %s | %s |" % (k, F[k]))
open(C6 + "/REPORT-c6j.md", "w").write("\n".join(out) + "\n")
print("edits", len(EDITS), "report lines", len(out))
