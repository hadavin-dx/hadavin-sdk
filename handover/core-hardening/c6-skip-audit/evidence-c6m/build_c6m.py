"""Builds REPORT-c6m.md from the audited files. Old text is read from the files (never typed by hand) and must occur exactly once
on its line; every cited source line is found by an anchor text, so a cite that does not exist stops the build.
The audited tree is read-only; this script writes only REPORT-c6m.md and evidence-c6m/edits.json."""
import sys, re, os, json

SCR = "/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad"
T = SCR + "/c6/tree/handover"          # read-only copy of branch origin/cloud/flows-audit (verification ran here)
REPO = "/home/user/hadavin-sdk"
H = REPO + "/handover/core-hardening"
C6 = H + "/c6-skip-audit"

# short name -> (absolute path read, path inside the repository, branch, plain description)
FA, CH = "origin/cloud/flows-audit", "cloud/core-hardening"
F = {
    "RS": (T + "/demo/VIDEO-RUNSHEET.md", "handover/demo/VIDEO-RUNSHEET.md", FA, "the run sheet (scene by scene script)"),
    "PG": (T + "/demo/n8n-flows/PAGE-STATEMENTS-V4.md", "handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md", FA, "the page statements (text for the web page)"),
    "NS": (T + "/demo/n8n-flows/N8N-START.md", "handover/demo/n8n-flows/N8N-START.md", FA, "the n8n start notes"),
    "MF": (T + "/demo/n8n-mainframe/mf.py", "handover/demo/n8n-mainframe/mf.py", FA, "the test program (crash tests and the leak scan)"),
    "JF": (T + "/demo/n8n-flows-real-v5/mf-form.json", "handover/demo/n8n-flows-real-v5/mf-form.json", FA, "real-v5 flow: form entry"),
    "JH": (T + "/demo/n8n-flows-real-v5/mf-hook.json", "handover/demo/n8n-flows-real-v5/mf-hook.json", FA, "real-v5 flow: hook entry"),
    "JR": (T + "/demo/n8n-flows-real-v5/mf-recovery.json", "handover/demo/n8n-flows-real-v5/mf-recovery.json", FA, "real-v5 flow: recovery (runs every 30 s)"),
    "JS": (T + "/demo/n8n-flows-real-v5/mf-sub-crm-mail.json", "handover/demo/n8n-flows-real-v5/mf-sub-crm-mail.json", FA, "real-v5 flow: shared step (CRM write and mail)"),
    "ONE": (H + "/inputs/DECISION-one-store.md", "handover/core-hardening/inputs/DECISION-one-store.md", CH, "the one-store decision"),
    "DEC": (H + "/inputs/DECISIONS-2026-11-16.md", "handover/core-hardening/inputs/DECISIONS-2026-11-16.md", CH, "the studio lead's decisions of 2026-11-16"),
    "PLAN": (H + "/inputs/plan-wp6-resmoke-v5.md", "handover/core-hardening/inputs/plan-wp6-resmoke-v5.md", CH, "the re-smoke plan (version 5)"),
    "ORD": (H + "/ORDERS.md", "handover/core-hardening/ORDERS.md", CH, "the studio lead's orders and answers"),
    "H6": (C6 + "/REPORT-c6h.md", "handover/core-hardening/c6-skip-audit/REPORT-c6h.md", CH, "the last full audit report"),
    "RES": (C6 + "/raw-lane3/RESULTS.md", "handover/core-hardening/c6-skip-audit/raw-lane3/RESULTS.md", CH, "the lane3 results table"),
    "FND": (T + "/flows-audit/FINDINGS.md", "handover/flows-audit/FINDINGS.md", FA, "the numbered findings"),
    "RDES": (C6 + "/review-design.md", "handover/core-hardening/c6-skip-audit/review-design.md", CH, "the older design review"),
    "EVSET": (C6 + "/evidence-c6i/02-workflow-settings.txt", "handover/core-hardening/c6-skip-audit/evidence-c6i/02-workflow-settings.txt", CH, "evidence: flow-file saving settings"),
    "EVDIR": (C6 + "/evidence-c6i/01-flow-folders.txt", "handover/core-hardening/c6-skip-audit/evidence-c6i/01-flow-folders.txt", CH, "evidence: flow folders"),
    "RJD": (C6 + "/review-c6j-design.md", "handover/core-hardening/c6-skip-audit/review-c6j-design.md", CH, "the c6j design review"),
    "RJN": (C6 + "/review-c6j-naive.md", "handover/core-hardening/c6-skip-audit/review-c6j-naive.md", CH, "the c6j naive-reader review"),
    "RKD": (C6 + "/review-c6k-design.md", "handover/core-hardening/c6-skip-audit/review-c6k-design.md", CH, "the c6k design review"),
    "RKN": (C6 + "/review-c6k-naive.md", "handover/core-hardening/c6-skip-audit/review-c6k-naive.md", CH, "the c6k naive-reader review"),
    "RLD": (C6 + "/review-c6l-design.md", "handover/core-hardening/c6-skip-audit/review-c6l-design.md", CH, "the c6l design review"),
    "RLN": (C6 + "/review-c6l-naive.md", "handover/core-hardening/c6-skip-audit/review-c6l-naive.md", CH, "the c6l naive-reader review"),
    "RCO": (C6 + "/raw-lane3/recompute-output.txt", "handover/core-hardening/c6-skip-audit/raw-lane3/recompute-output.txt", CH, "lane3 recomputed numbers (raw output)"),
    "RJL": (C6 + "/raw-lane3/results.jsonl", "handover/core-hardening/c6-skip-audit/raw-lane3/results.jsonl", CH, "lane3 raw run records, one per line"),
    "OS25": (H + "/steps-edits/OWNER-SHEET-v25-A.md", "handover/core-hardening/steps-edits/OWNER-SHEET-v25-A.md", CH, "owner sheet v25, variant A (the newest sheet on disk)"),
    "OS26": (H + "/steps-edits/OWNER-SHEET-v26-SOURCE.md", "handover/core-hardening/steps-edits/OWNER-SHEET-v26-SOURCE.md", CH, "owner sheet v26 source file (a template with placeholders; the newest file in the folder)"),
    "OS19": (H + "/steps-edits/OWNER-SHEET-v19.md", "handover/core-hardening/steps-edits/OWNER-SHEET-v19.md", CH, "owner sheet v19 (assumed newest by REPORT-c6k.md)"),
    "QUE": (H + "/QUEUE.md", "handover/core-hardening/QUEUE.md", CH, "the studio lead's queue (header rule 6)"),
    "EQ4": (T + "/demo/real-run/evidence-q4-rrc.txt", "handover/demo/real-run/evidence-q4-rrc.txt", FA, "help text of the take script"),
    "P4": (T + "/demo/PLAN-4-NLITE-FROM-LEAD.md", "handover/demo/PLAN-4-NLITE-FROM-LEAD.md", FA, "plan 4 (the take script plan)"),
    "CA": (T + "/demo/claims-audit.md", "handover/demo/claims-audit.md", FA, "earlier claims audit"),
    "CB": (T + "/demo/claims-fix/claims-fix-B1-notes.md", "handover/demo/claims-fix/claims-fix-B1-notes.md", FA, "notes of the claims fix"),
    "SH": (T + "/demo/real-run/start-prompt-hardening-v1-to-v2.diff", "handover/demo/real-run/start-prompt-hardening-v1-to-v2.diff", FA, "diff of the start prompt"),
}
LINES = {}


def lines(k):
    if k not in LINES:
        LINES[k] = open(F[k][0], encoding="utf-8", errors="replace").read().split("\n")
    return LINES[k]


def find(k, anchor):
    hits = [i + 1 for i, l in enumerate(lines(k)) if anchor in l]
    if len(hits) < 1:
        sys.exit("ANCHOR %s %r matched no line" % (k, anchor))
    return hits[0]


def cite(k, a):
    n = find(k, a)
    if k == "DEC":
        m = re.match(r"^(\d+)\.", lines(k)[n - 1])
        if m:
            return "DEC:%d (decision %s)" % (n, m.group(1))
    return "%s:%d" % (k, n)


def src(pairs):
    return ", ".join(cite(k, a) for k, a in pairs)


# ----- old text taken from the c6j edit list (already verified once), re-verified here
OLD = {e["key"]: e["old"] for e in json.load(open(C6 + "/evidence-c6j/edits.json"))}
EDITS = []
ORDER = ["RS", "PG", "NS", "MF", "JF", "JH", "JR", "JS", "ONE"]


def edit(key, fk, old, new, why, sources, dep="", ln=None, span=None, qsrc=()):
    _fx = lambda t: re.sub(r"\b(the|The) lead(?! fields| key| id| ends| table| is\b)(?!'s made)(?!'s name)(?!'s e-mail)(?='s|\b)", lambda m: m.group(1) + " studio lead", t) if "DECISION-one-store" not in fk else t
    new = _fx(new); why = _fx(why)
    if fk == "RS":
        new = new.replace("on this sheet", "on this run sheet").replace("written on the run sheet", "written on this run sheet")
    if span:
        a, b = span
        for i, l in enumerate(lines(fk)):
            if a in l:
                j = l.index(a)
                e = l.index(b, j) + len(b)
                old = l[j:e]
                break
        else:
            sys.exit("SPAN %s not found %r" % (key, a))
    if old == "WHOLE":
        old = lines(fk)[ln - 1]
    hits = [i + 1 for i, l in enumerate(lines(fk)) if old in l]
    if len(hits) != 1:
        sys.exit("EDIT %s old text matched %d lines %s: %r" % (key, len(hits), hits, old[:70]))
    n = hits[0]
    if lines(fk)[n - 1].count(old) != 1:
        sys.exit("EDIT %s old text occurs more than once on line %d" % (key, n))
    for bad in ("|", "`"):
        if bad in old or bad in new:
            sys.exit("EDIT %s contains %r, cannot be placed in a table cell" % (key, bad))
    EDITS.append(dict(key=key, fk=fk, line=n, old=old, new=new, why=why, src=src(sources), dep=dep))


# =============================== RUN SHEET (VIDEO-RUNSHEET.md)
edit("rs4", "RS", OLD["rs4"], "real CRM service in scenes 1 to 4",
     "Scene 5 runs on a stand-in CRM and the lead cut it from the video; the sheet itself says scenes 1 to 4 at line 11.",
     [("RS", "Scenes 1 to 4: real mail"), ("DEC", "1. SCOPE")])
edit("rs5a", "RS", "", "no recovery number in any caption. On 2026-11-16 the lead also cut the number 60.1 to 61.9 s from the video.)",
     "Line 5 promised a measured-number caption 'until lane3 runs land'; the lead cut that number. Replaces the whole clause so no sentence is left half-finished (c6j design review m3).",
     [("DEC", "1. SCOPE")], span=("no recovery number in any caption until", "whatever they are.)"))
edit("rs5b", "RS", OLD["rs5b"], "The V7 and lane3 numbers are not on the closing card (see the closing card row of this run sheet, line 41); they stay in the raw files as history.",
     "Line 5 says the numbers sit on the closing card; the closing-card edits remove them. The new text carries no date and no 'decided' (c6l design review M1).", [("RS", "| 12. Closing card |")], dep="Q1")
edit("rs14", "RS", OLD["rs14"], "and do not appear in the video (the closing card carries none of them)",
     "Line 14 says the old numbers appear on the closing card.", [("RS", "| 12. Closing card |")], dep="Q1")
edit("rs22", "RS", "", 'in scene 4 (scenes 5 and 9 are not in the one video). The 45 s lease is a setting, not a measurement.',
     "A setting cannot be 'unmeasured'; scenes 5 and 9 are cut (c6j design review m4).", [("RS", "Lease: the take runs at lease 45 s")],
     span=("in scenes 4, 5 and 9. The 45 s lease is UNMEASURED.", "UNMEASURED."))
edit("rs23a", "RS", OLD["rs23"], "Recovery wording: NONE (the studio lead dropped the plus 25 to 30 s caption at 17:05 UTC = 22:35 IST; on 2026-11-16 the studio lead cut the number 60.1 to 61.9 s from the video).",
     "Line 23 still plans a measured-number caption. Times are given in UTC and IST (c6l naive review M8).", [("DEC", "1. SCOPE")])
edit("rs23b", "RS", "At 45 s the estimate is roughly 70 to 75 s: for planning the sped-up cut only, never a caption number.",
     "For planning the sped-up cut only, never a caption number: the lane3 runs on the film-v4 stand-in flows at a 45 s lease ended 60.1 to 61.9 s after the crash; nothing is measured on the flows of this take.",
     "Line 23 tail still gives the old 70 to 75 s guess that the scene 4 row replaces (c6j design review m3).", [("RES", "| 873a908a-film-v4-lease45 | K1 | 5 |")])
edit("rs24", "RS", OLD["rs24"], "Lane3 K3 = this sheet's K3B (n8n killed while the mail connection was opening, mail not delivered); lane3 K6 = this sheet's K3 (n8n killed after the mail was delivered).",
     "Line 24 gave lane3 K3 a third, wrong meaning. mf.py, RESULTS.md and the page agree on the pair.", [("MF", "def k3b"), ("MF", "def k3():"), ("RES", "Names differ: my K3")])
edit("rs30a", "RS", OLD["rs30"],
     "Before scene 1 the studio lead (not the owner) deletes every execution made before the take (rehearsal and smoke runs) in n8n's execution list and writes the time (UTC) of that clean-up on this sheet as the take start time. Then the studio lead checks on the screen that every row shows a start time after the take start time and that no row shows rehearsal data. This hides the old runs from the screen; whether it erases them from n8n's database is not verified (the start notes say a deleted run is only marked deleted until pruning; the re-smoke plan says deletion is removal of the container). New rows from the recovery flow (one run every 30 seconds) are expected and are not a fault. The same check is made before every rehearsal and again before scene 2, with the same take start time. If a row older than the take start time still shows, the owner stops and tells the studio lead.",
     "The old gate 'list shows 0 rows' cannot be passed: the recovery flow runs every 30 s and the take saves every run, so the list refills within 30 s (c6j design review M1). It now says who deletes (the studio lead), gives the start time that makes 'a row from before the take' testable (c6k naive review, row 22), marks the hide-only behaviour as not verified (c6k design review m3), and holds the old item 12 of the rehearsal list (c6k design review M4). The row also assumes saved runs, which are true only after the flow files are edited and imported (c6k design review M4), so it waits for the import check.",
     [("JR", '"secondsInterval": 30'), ("NS", "a run that is not to be saved is only marked deleted"), ("PLAN", "| executions (take) |"), ("PLAN", "deletion = container removal")], dep="L-SAVE, C-4")
edit("rs30b", "RS", "Panes empty or at rest, the execution list on screen (status and time columns).",
     "Panes at rest (no lead in flight), the execution list on screen (status and time columns); the recovery flow adds one run to the list every 30 seconds, which is expected.",
     "Same reason: 'panes empty' is not true when the recovery flow saves a run every 30 s.", [("JR", '"secondsInterval": 30')], dep="L-SAVE")
edit("rs31", "RS", OLD["rs31"],
     "to the form entry on the LOOPBACK address, path mf-form. The owner types nothing into the lead fields except what the prepared note already contains; never a key, a password or a token in any form field (n8n saves the request body, see N8N-START.md).",
     "Do-not rule for the owner: a secret sent in a form field is saved by n8n. The pointer names the file only, because the leak-scan section it used to name is created by another row (c6l design review m5).", [("NS", "3. Nobody must send a secret"), ("PG", "18. UNBACKED")])
edit("rs32", "RS", OLD["rs32"],
     'Caption: "a lead sent twice with the same id is processed once". Second caption line: "We say this only when the second send comes within 45 seconds of the first. The 45 seconds is a setting: for that long the system keeps a lead for the run that took it first." No result exists for this repeat send on the flows of this take, so the rehearsal must show the repeat reply, and the real seconds between the first reply and the repeat (write them on this run sheet; the gap must be less than 45 seconds), before the take. The screen is the evidence.',
     "The studio lead's answer (ORDERS.md Q21.2 and Q22) requires the statement plus one honest sentence that a gap longer than the lease is not claimed; the studio lead gave that sentence in brackets, not as a caption, so the caption text is a question (L-LEASE). This row no longer waits for the import check: the lease sentence and the rehearsal evidence do not depend on saved runs (c6l design review m1).",
     [("ORD", "Q21.2:"), ("ORD", "Q22:"), ("DEC", "1. SCOPE")], dep="L-LEASE")
edit("rs33a", "RS", OLD["rs33a"],
     'No timing number in any caption or in the voice; the stopwatch overlay (the clock of this run) and the label "setting: lease 45 s" are on screen.',
     "Line 33 still carried the dropped caption 'about the lease plus 25 to 30 s', which decision 1 removes with the number. The part about rounded wording such as 'about a minute' is no longer in this row (split, c6l design review M4): it stays in rows 1 and pg161 under question L-APPROX, so this row is ready. The old text says 'no number' yet shows a label: this says 'no timing number'. The live stopwatch overlay and any 'sped up' label with the real wait show the clock of this very run as it happens; they are not a timing number in the sense of section 'Words' and no row changes them (run sheet lines 21 and 33).", [("DEC", "1. SCOPE")])
edit("rs33b", "RS", OLD["rs33b"],
     "60 s EST (real wait: not measured on the flows of this take; planning only, never said on screen or in the voice: the lane3 runs on the film-v4 stand-in flows ended 60.1 to 61.9 s after the crash)",
     "The old planning guess (70 to 75 s) is replaced by the lane3 range, labelled planning only and never a caption.", [("RES", "| 873a908a-film-v4-lease45 | K1 | 5 |"), ("RES", "| 873a908a-film-v4-lease45 | K6 | 3 |")])
edit("rs33c", "RS", OLD["rs33c"], "NO NUMBER on screen (not measured on the flows of this take). Basis of the older estimate:",
     "'Not measured at 45 s' is false for the film-v4 stand-in flows (RESULTS.md lines 89 to 92).", [("RES", "| 873a908a-film-v4-lease45 | K1 | 5 |")])
edit("rs33d", "RS", OLD["rs33d"], "None of these goes on screen or on the closing card.", "The closing-card edits remove them from the card.", [("RS", "| 12. Closing card |")], dep="Q1")
edit("rs36", "RS", "Lane3 K3 (killed after the CRM write): a different test, never cite it.",
     "Lane3 K3 (this sheet's K3B, n8n killed while the mail connection was opening): a different test from the stand-in drop, never cite it here.",
     "Line 36 repeats the wrong meaning of lane3 K3 and uses K3B without defining it (c6j design review m2).", [("MF", "def k3b"), ("RES", "Names differ: my K3")])
edit("rs41a", "RS", OLD["rs41a"], "Voice over one card, four short lines.", "Card lines 2 and 3 are cut, so six becomes four. All card rows apply together or not at all (c6k design review M1).", [("RS", "| 12. Closing card |")], dep="L-CARD, L-LEASE")
edit("rs41b1", "RS", "", "Line 1, statement, spoken: \"A lead sent twice with the same id is processed once. We say this only when the second send comes within 45 seconds of the first. The 45 seconds is a setting: for that long the system keeps a lead for the run that took it first.\"",
     "Split of the old row 13 (c6k design review M1): this row holds only the statement and the lease sentence, in plain words (c6k naive review: 'reserved to its first run' replaced; the word claim is not used for the video). The studio lead's own words were 'a gap longer than the lease is not claimed' (ORDERS.md answer Q21.2); this sentence says the same in plain words and is the question L-LEASE.",
     [("ORD", "Q21.2:")], dep="L-CARD, L-LEASE", span=("Line 1, claim: a lead sent twice", "processed once."))
edit("rs41b2", "RS", "", "Line 2, alerts, spoken: \"We make no statement about how quickly an alert mail arrives.\" Line 3, retention, spoken: \"The made-up name and e-mail address sent to n8n may stay in n8n's database until n8n's automatic clean-up removes them; we did not measure how long that takes.\" Line 4, not tested, spoken: \"Not tested: other mailboxes, other CRMs (customer-record systems), alerts sent as chat messages, other lease settings. One machine, made-up people, our own runs.\"",
     "Split of the old row 13 (c6k design review M1): alerts, retention and not-tested lines. The retention line is worded so that it is true whether saving is all or none, because the request body reaches n8n's database in both cases (N8N-START.md lines 44 to 46); 'may stay' replaces the setting claim 'stay in n8n's saved runs', since the leak scan has not run and page statement 18 is UNBACKED (c6k design review m2). 'name and address' is now 'name and e-mail address'. 'pruning' is now 'automatic clean-up', 'Slack alert' is 'alerts sent as chat messages', and the vague 'we do not claim ...' is a plain sentence (c6k naive review, row 13). Old line 2 (80 kills) is cut because it counts runs of older v3 flows with a 20 s lease on stand-ins, not the flows of the take; old line 3 (recovery 'about the lease plus 25 to 30 s') is cut because the lane3 runs at 45 s ended 60.1 to 61.9 s after the crash, which does not match 70 to 75 s (c6l design review M2: the K3B wording is not on the card).",
     [("MF", "def k3b"), ("RS", "Added 17:40Z (lead note, lane3 HB189)"), ("NS", "2. The lead fields (name, e-mail) DO reach")], dep="L-CARD, L-LEASE", span=("Line 2, history (older flow version v3", "own runs."))
edit("rs41c", "RS", OLD["rs41c"], "NO NUMBER on the card. The V7 kill series, the lane3 144.3 s figure and the lane3 B90 alert counts are not shown; they belong to stand-in flows, not to the take.",
     "Matches the card text after the previous edit.", [("RS", "| 12. Closing card |")], dep="Q1")
edit("rs44", "RS", "- Core scenes 1 to 10 and 12:",
     "- The one video: scenes 1 to 4 and the closing card (scene 12): scene 1 25 s + scene 2 40 s + scene 3 25 s + scene 4 60 s + closing card 30 s = 180 s, 3 min. The next two lines count scenes 5 to 11, which are not in the one video (lead decision of 2026-11-16).\n- Core scenes 1 to 10 and 12:",
     "The old total counts cut scenes (c6j design review m4). The five times (25, 40, 25, 60, 30 s) were checked against the Time column of the run sheet rows 1, 2, 3, 4 and 12 and add to 180 (c6k design review m6).", [("DEC", "1. SCOPE")])
edit("rs47", "RS", "are UNMEASURED at 45 s; read them from the stopwatch in the take.", "are not measured on the flows of this take; read them from the stopwatch in the take.",
     "Stale 'UNMEASURED' wording (c6j design review m4).", [("RES", "| 873a908a-film-v4-lease45 | K1 | 5 |")])
edit("rs51", "RS", "The 45 s lease has no measurement: recovery, the failed-lead wait and the alert wait on screen are all unmeasured; no caption number for them.",
     "No recovery time, failed-lead wait or alert wait is measured on the flows of this take (the lane3 45 s runs were on film-v4 stand-in flows); no caption number for them.",
     "Stale 'no measurement' wording (c6j design review m4).", [("RES", "| 873a908a-film-v4-lease45 | K1 | 5 |")])
edit("rs59", "RS", OLD["rs59"],
     '10. Step-2 fault for a real mailbox and the Slack alert are NOT BUILT; the take says "stand-in" or cuts.\n11. GATE, contact deletion. The studio lead decided that the take never deletes contacts, and his written answer of 2026-11-16 12:50 UTC (18:20 IST) confirms it: the independent review of 11:00 UTC (16:30 IST) found no archive and no delete call in the take script scripts/run_real_check_n8n.py (only a listing request), and the HubSpot key is not widened. This is UNVERIFIED by the audit: the script is not in the audited files. Two scripts have similar names: scripts/run_real_check_n8n.py is the take script the video uses (it lives on a local take branch that is never pushed); scripts/run_real_check.py is the old desk test program, whose help text offers a clean-up option that archives contacts, and it is not the take (the studio lead\'s written answer of 10:35 UTC = 16:05 IST says the archive step the audit read belongs to that old program). Older plan text that shows the owner a notice "up to 3 HubSpot contacts archived at the end" is stale according to that answer and must not be shown. The take does not start until the studio lead has written here, with date and time in UTC and IST: (1) the version id of the files he read; (2) the output of grep -n -i archive and grep -n -i delete on scripts/run_real_check_n8n.py at that version (no hit, or the lines); (3) "matches the decision" or, if a line was found, "stop: tell the owner"; (4) that no owner sheet and no notice shows a line promising that contacts will be deleted or archived by the program. Until then the take is blocked and nothing is touched in the CRM. Not checked: whether an archived contact keeps its e-mail address reserved.\n12. GATE, the repeat-send statement: scene 3 and card line 1 are not filmed until the unique index on the contact table (the database rule that refuses a second row for the same contact id) has been seen in the table of the take\'s own database (the loopback re-smoke result), or the studio lead writes here "index not seen, accepted" with the date and time in UTC and IST. In the test program the table is created with a primary key on the contact id (mf.py line 45), which is the same kind of rule; that is not proof for the take database.',
     "Re-issued against the studio lead's answers Q23 and Q27 (ORDERS.md; c6l design review B1): decision 2 stands, so the gate no longer offers a choice between changing the program and changing the decision, no longer states that the end-of-take step archives 'also after an error' (that came from plan text, not from the script), and names both scripts and which one the video uses. The gate record has four yes-or-no lines written by the studio lead at the re-pin. The old plan 4 notice and the help text of the older script are cited as stale or unused in section 6. Item 12: who writes 'index not seen' is named.",
     [("ORD", "Q23:"), ("ORD", "Q27:"), ("ORD", "Q20.4:"), ("ORD", "1. The take program"), ("EQ4", "--cleanup"), ("P4", "up to 3 HubSpot contacts archived at the end"), ("DEC", "2. TAKE IDENTITY"), ("MF", "CREATE TABLE mf_leads")])
edit("rs70", "RS", "is visible in scenes 4, 5 and 9.", "is visible in scene 4.", "Scenes 5 and 9 are not in the one video.", [("DEC", "1. SCOPE")])
edit("rs71", "RS", OLD["rs71"],
     '10. Run the whole take once with a stopwatch; compare to the EST column and re-total.\n11. Before every rehearsal and before the take, list the active workflows in n8n. Only workflows imported from the folder n8n-flows-real-v5 may be active: the form entry flow, the hook entry flow, the recovery flow, and the shared-step flow if it is active. No workflow from any other folder, and no workflow with the paths mf-form or mf-hook from n8n-flows-film-v5 or an older folder, may be active. Write the list into the studio lead session note (the handoff). (This check needs n8n and is not run yet.)\n12. Closing check for contact deletion and the owner sheet, run by the studio lead when the final version of the files is known: (a) read the take script scripts/run_real_check_n8n.py (the one the video uses; the old desk test program scripts/run_real_check.py is not the take) at that version and search it with grep -n -i archive and grep -n -i delete. The studio lead\'s written answer of 2026-11-16 12:50 UTC (18:20 IST) says that the independent review of 11:00 UTC (16:30 IST) found no archive and no delete call there, only a listing request; this is UNVERIFIED until the grep output is written here with the version id and the date and time in UTC. (b) read the owner sheet the owner reads: it must say that the owner deletes leftover made-up contacts by hand, and it must not say that the HubSpot key is read-only or limited to create and change unless the owner has confirmed that.\n13. Scene 3: write down the real seconds between the first reply of scene 2 and the repeat send, and the reply text of the repeat. The gap must be less than 45 seconds (the lease); if it is longer, redo the scene. After the repeat the CRM list must still show 1 row and the test mailbox 1 mail; if not, stop and tell the studio lead.\n14. GATE, saved runs. From the edit of the four flow files on, n8n saves every run, so a secret sent in a form field would be stored. The take (and any rehearsal with real accounts) does not start until this run sheet shows two lines, each with the date and time in UTC and IST and the name of the person who ran it: "import check passed: the execution list shows runs of an entry flow and of the recovery flow" and "leak scan for saved runs passed: pass lines met on the loopback stand-ins". Owner of this gate: the studio lead (he runs both checks himself, or names a builder to write the leak scan and writes that name here: ______). Both checks run on this computer only, with stand-in services, before the first rehearsal.',
     "Eleven flow folders carry the same webhook paths mf-form and mf-hook; only real-v5 may be live (c6j design review minor and c6i review). Item 12 is re-issued against the studio lead's answers Q23 and Q27 (ORDERS.md): decision 2 stands (the take never deletes), the audited tree has no take script, so the grep is the studio lead's step at the final version and its result is UNVERIFIED until written; the old requirement of 0 hits for 'never deletes' in the decisions file is dropped because the file states the rule (c6l design review B1). Item 14 is new: saved runs are switched on by the flow-file rows, the import check and the leak scan are not run yet, so the take is blocked until both lines are on the run sheet, with a named owner (c6l design review M5). The shared-step flow may be active if it is a real-v5 file. Item 13 has a target (under 45 seconds) and a pass test.",
     [("EVDIR", "n8n-flows-real-v5"), ("DEC", "2. TAKE IDENTITY"), ("ORD", "Q23:"), ("ORD", "Q27:"), ("ORD", "1. The take program"), ("MF", "CREATE TABLE mf_leads")])
edit("rs79", "RS", OLD["rs79"], "5. Decided: no recovery number on screen (the studio lead cut the number from the video on 2026-11-16). What the closing card says is settled by the closing card row of this run sheet (line 41).",
     "Open decision 5 is answered by the cut of the number from the video (decision 1, DEC:2). The studio lead's decision does not cover the closing card line 'lease plus 25 to 30 s'; its removal is only the default of L-CARDCUT, so the new text no longer says 'none on the closing card' (c6l design review M1).", [("DEC", "1. SCOPE")])
edit("rs80", "RS", "kept (line 5).", "kept (line 3 of the shortened card).", "The retention line moves from line 5 to line 3 (c6j design review m4).", [("RS", "| 12. Closing card |")], dep="Q1")
edit("rs82", "RS", "History line for the card: on v4", "Withdrawn from the card (the card makes no statement about alert delay: it says only that we make no statement about how quickly an alert mail arrives). Old history line, left in place as history: on v4",
     "Line 82 told the filmer to put the 13-minute figure on the card; the card line 2 does not (c6j design review M4). The figure is a relay for lane3 v4 flows, not the flows of the take (RESULTS.md lines 78 and 79). The new text carries no date and no 'decided', because the card text is only a default (c6l design review M1).",
     [("RES", "| 7709d058-v4 | v3KS | v4ks1 |")], dep="Q1")
edit("rs85", "RS", "NO number in voice or caption until lane3 lease-45 numbers land (first about 17:10Z, all about 17:45Z).",
     "NO number in voice or caption (the lane3 lease-45 numbers landed later; on 2026-11-16 the lead cut the number from the video).", "Stale: the numbers landed and were cut (c6j design review m4).", [("DEC", "1. SCOPE")])
edit("rs90", "RS", "WHOLE", 'Scene 4 caption: no timing number in any caption, text card or voice (the studio lead cut the number from the video on 2026-11-16), and no rounded wording such as "about a minute". A live stopwatch overlay and the label "setting: lease 45 s" (a setting, not a measured time) are shown. The 18 kept crash runs of lane3 (60.1 to 61.9 s from the crash to the final state; 52.8 to 54.9 s from n8n coming back up) were measured on the film-v4 stand-in flows, not on the flows of this take, and stay out of the video. Two further lane3 runs at the same lease, VOID-fl45k3b (it never reached a final state, 338.7 s) and VOID-fl45k6c (the stand-in services were not up), were voided and are not counted; the cause is unknown. The kill cases K3B and K3 are not mentioned in scene 4. No statement about alert delay is made. Never "within 60 s".',
     "Line 90 was a FINAL caption with the number the studio lead cut, a kill-case sentence that is false for K3B, a 13-minute figure relayed for other flows, and the wrong from-n8n-up start (52.9; RESULTS.md line 92 says 52.8). Only the cut of the number is the studio lead's decision (decision 1); the ban on rounded wording is question L-APPROX and the missing kill-case words are question L-KILL, both unconfirmed defaults, so the new text no longer says 'decided' for them (c6l design review M1). It says 'no timing number in any caption or text card' because a live stopwatch overlay is shown. The 18 runs are the 18 KEPT runs; the two voided runs are named.",
     [("DEC", "1. SCOPE"), ("MF", "def k3b"), ("RES", "| 873a908a-film-v4-lease45 | K6 | 3 |"), ("RCO", "VOID-fl45k3b K3"), ("RJL", '"label": "VOID-fl45k3b"')], dep="L-KILL, L-APPROX", ln=90)
# =============================== PAGE STATEMENTS (PAGE-STATEMENTS-V4.md)
edit("pg23", "PG", "Every lane3 number below is a lead relay only.",
     "Every lane3 number below is a lead relay, except the 18 kept crash runs of statement 20 (two voided runs, VOID-fl45k3b and VOID-fl45k6c, are not counted): the audit read their lane3 results table (RESULTS.md, lines 89 to 92, in handover/core-hardening/c6-skip-audit/raw-lane3/).",
     "Line 23 says no lane3 file was read, but the audit read the results table (c6j design review m5).", [("RES", "| 873a908a-film-v4-lease45 | K1 | 5 |")])
edit("pg105", "PG", "The only v4 recovery figure is a lane3 relay: K1 recovered in 144.3 s at its lease of 120 s (n=1, v4 K1).",
     "The v4 recovery figure is a lane3 relay: K1 recovered in 144.3 s at a lease of 120 s (n=1, one run, v4 K1). Lane3 also ran crash tests at a 45 s lease on film-v4 stand-in flows; they are in statement 20.",
     "Statement 14 contradicts statement 20 (c6j design review m5). The new text points to statement 20 without its figure and without saying whether statement 20 is for the web page, so it is true whatever the studio lead answers (c6l design review m2).", [("RES", "| 7709d058-v4 | K3 | 1 |")])
edit("pg120a", "PG", OLD["pg17"], "at the 45 s film lease lane3 ran crash tests on film-v4 stand-in flows (see statement 20); nothing is measured on real-v5.",
     "Statement 17 says nothing is measured at 45 s; statement 20 on the same page gives the lane3 runs. The new text carries no figure and no 'not for the web page' (c6l design review m2).", [("RES", "| 873a908a-film-v4-lease45 | K1 | 5 |")])
edit("pg120b", "PG", "Rough rule from lane3: about the lease plus 25 s; the 20 s data is lease + 40 s so treat the rule as rough.",
     "Rough rule from lane3: about the lease plus 25 s; the 20 s laptop data is up to lease + 40 s and the 45 s film-v4 runs of statement 20 ended sooner than lease + 25 s, so the rule fits neither and is not used on screen.",
     "Statement 17 keeps a rule the 45 s data does not support (c6j design review m5). The new text carries no figure of statement 20 (c6k design review M2).", [("RES", "| 873a908a-film-v4-lease45 | K1 | 5 |")])
edit("pg125", "PG", "UNBACKED (do not publish until backed). Carried over from the old section C, not re-checked: with the four n8n settings turned off (success data, error data, progress data, manual execution data), n8n may still keep the lead's name and e-mail from the incoming request in its own database until pruning removes the run; the pruning age is not measured.",
     "UNBACKED (do not publish until backed). For the take, n8n saves the data of every run (the setting for successful runs and the setting for failed runs are both on), so n8n keeps the made-up name and e-mail of the contact, and everything the nodes pass on, in its own database until n8n's pruning removes the run; the pruning age is not measured. The earlier wording of this statement was written for the four settings turned off (success data, error data, progress data, manual execution data), which is not the take.",
     "Statement 18 says 'four settings turned off', which the take no longer does (c6j design review M6).", [("PLAN", "| executions (take) |")], dep="L-SAVE")
edit("pg134", "PG", '19. "An alert can arrive up to about 13 minutes late', '19. NOT USED in the one video or on its closing card, and NOT FOR THE WEB PAGE unless the studio lead says yes (relayed for lane3 v4 flows, not the flows of the video; RESULTS.md lines 78 and 79). "An alert can arrive up to about 13 minutes late',
     "Statement 19 and the 13-minute figure no longer back anything in the video (c6j design review m5).", [("RES", "| 7709d058-v4 | v3KS | v4ks1 |")])
edit("pg139", "PG", OLD["pg139"], "- Lease 45 s: measured only on film-v4 stand-in flows by lane3 (see statement 20), not on real-v5. Lease 120 s: one lane3 figure only.",
     "Same contradiction in the honest-limits list. No figure of statement 20 and no 'not for the web page' (c6l design review m2).", [("RES", "| 873a908a-film-v4-lease45 | K1 | 5 |")])
edit("pg148", "PG", "## Statement 20 (FINAL, lead relay of lane3 HB194, lease 45 s, film-v4, n8n 2.46.6, independent harness)",
     "## Statement 20 (FINAL, lead relay of lane3 HB194, lease 45 s, film-v4, n8n 2.46.6, independent harness). NOT FOR THE WEB PAGE of the one video unless the lead says yes to carrying the range 60.1 to 61.9 s there (decision pending). It is not a caption and not spoken in the video.",
     "The page may or may not carry the number; this marker keeps it out of the page until the lead decides (L-PAGE).", [("DEC", "1. SCOPE")], dep="L-PAGE")
edit("pg149a", "PG", OLD["pg149a"],
     '20. "On the film-v4 stand-in flows (not the flows in the video), with a 45 s lease, each of the 18 kept crash runs reached a final state 60.1 to 61.9 s after the crash." Final states: 10 runs done (K1 5, K2 5) and 8 runs unknown with one alert to the owner (K3B 5, K3 3, in this page\'s names), which is the intended safe end state of those two cases (the system cannot tell whether the CRM entry and the mail happened, so it sends one alert and a person decides). Two more runs of the same series were voided by the lane3 session (labelled VOID in its raw file) and are not counted: VOID-fl45k3b (it never reached a final state, 338.7 s) and VOID-fl45k6c (the stand-in services were not up); the cause of the first is unknown. Five of the 18 counted runs ran at the same time as a voided run (fl45k2d, fl45k2e, fl45k6a, fl45k3d, fl45k6b), so the voided runs may have disturbed them; this was not checked. Not measured on real-v5.',
     "Statement 20 said all 18 runs finished, but 8 of 18 ended unknown (RESULTS.md lines 91 and 92). 'About a minute' is the rounded wording of question L-APPROX, so it is removed here as well. 'Each of 18' now says 18 KEPT runs and names the two voided runs; the new text also says that 5 kept runs overlap the voided K3B window in time (c6l design review m3) and what 'unknown with one alert' means (c6l naive review m5). This row is a correction and no longer waits for the web-page question L-PAGE (c6l design review M3): it carries the figure that the statement already carried; whether the page may publish it is decided by the row that marks statement 20 (L-PAGE).",
     [("RES", "| 873a908a-film-v4-lease45 | K3 | 5 |"), ("RES", "| 873a908a-film-v4-lease45 | K6 | 3 |"), ("RCO", "VOID-fl45k3b K3"), ("RJL", '"label": "VOID-fl45k3b"')], dep="L-APPROX")
edit("pg149b", "PG", OLD["pg149b"], "Raw: the lane3 results table, handover/core-hardening/c6-skip-audit/raw-lane3/RESULTS.md lines 89 to 92 (read by the audit; the lane3 report named HB194 is not itself in the tree).",
     "The page and the run sheet said raw not read, while the audit had read RESULTS.md.", [("RES", "| 873a908a-film-v4-lease45 | K1 | 5 |")])
edit("pg150", "PG", OLD["pg150"], "(killed while the mail connection was opening, mail not delivered: unknown + 1 alert); lane3 K6 = this page's K3 (killed after the mail was delivered: unknown + 1 alert).",
     "mf.py says K3B is killed with the mail NOT yet delivered and K3 after delivery; RESULTS.md agrees.", [("MF", "def k3b"), ("MF", "def k3():"), ("RES", "Names differ: my K3")])
edit("pg153", "PG", OLD["pg153"],
     "lead ends unknown with 1 alert to the owner, no second mail. K3B: killed while the mail connection was opening; the mail was not delivered (the test mailbox received 0 mails in 5 of 5 runs). K3: killed after the mail was delivered (the test mailbox received 1 mail in 3 of 3 runs). The words killed after the mail left are not used for K3B. n small; no timing in a caption.",
     "Same facts; intake counts from RESULTS.md (lane3 K3 rows and K6 rows).", [("RES", "| 873a908a-film-v4-lease45 | K3 | 5 |"), ("RES", "| 873a908a-film-v4-lease45 | K6 | 3 |")])
edit("pg154", "PG", "- From n8n coming back up: 52.9 to 54.9 s (about 8 s restart is inside the kill-to-final numbers).",
     "- From n8n coming back up: 52.8 to 54.9 s (RESULTS.md lines 89 to 92; about 8 s restart is inside the kill-to-final numbers).",
     "The K6 row of RESULTS.md starts at 52.8, not 52.9 (c6j design review m1). This is a correction that holds whatever the studio lead answers about the web page (c6l design review M3).", [("RES", "| 873a908a-film-v4-lease45 | K6 | 3 |")])
edit("pg156", "PG", "up to 13 minutes late (KS n=2, 780 s), not lost (statement 19).", "up to 13 minutes late (KS n=2, 780 s), not lost (statement 19; relayed for lane3 v4 flows, not used in the one video).",
     "Stale (c6j design review m5).", [("RES", "| 7709d058-v4 | v3KS | v4ks1 |")])
edit("pg159", "PG", OLD["pg159"], 'Caption rule: no timing number in any caption or in the voice of the one video (the lead cut it on 2026-11-16). NEVER "within 60 s".', "Matches the withdrawn caption (next edit).", [("DEC", "1. SCOPE")])
edit("pg161", "PG", OLD["pg161"], 'Caption wording: none. The lead cut the scene 4 number on 2026-11-16, and the earlier wording "about a minute after the crash (measured at lease 45 s ...)" is withdrawn. Do not pool medians.',
     "Line 161 still published the cut number and the rounded wording.", [("DEC", "1. SCOPE")], dep="L-APPROX")

# =============================== N8N-START.md
edit("ns4a", "NS", "regular mode (no queue), SQLite inside n8n.", "regular mode (no queue), n8n's own database inside the take's Postgres server.",
     "Only true once check C-8 shows n8n runs on Postgres; until then the old text is the true one (c6j design review m7).", [("ONE", "**ONE database for everything we own")], dep="C-8 and L-ONEDB")
edit("ns4b", "NS", "Postgres 16 for the lead table (separate from n8n's own SQLite).", "Postgres 16 for the lead table (a separate database from n8n's own).",
     "Same condition as the previous row.", [("ONE", "**ONE database for everything we own")], dep="C-8 and L-ONEDB")
edit("ns15", "NS", OLD["ns15"], "## Execution saving: four settings; for the take two of them are set to all (owner decision of 2026-11-16), so the execution list in scenes 1 and 2 shows runs",
     "The old text requires none; the take saves every run.", [("PLAN", "| executions (take) |")], dep="L-SAVE")
edit("ns17", "NS", OLD["ns17"], "EXECUTIONS_DATA_SAVE_ON_SUCCESS=all", "Value for the take.", [("PLAN", "| executions (take) |")], dep="L-SAVE")
edit("ns18", "NS", OLD["ns18"], "EXECUTIONS_DATA_SAVE_ON_ERROR=all", "Value for the take.", [("PLAN", "| executions (take) |")], dep="L-SAVE")
edit("ns23", "NS", OLD["ns23"], "- SAVE_ON_SUCCESS=all: n8n stores the run data (node inputs and outputs, which hold the made-up lead name and e-mail) for runs that succeed, so the execution list shows them.",
     "Follows the value change.", [("PLAN", "| executions (take) |")], dep="L-SAVE")
edit("ns24", "NS", OLD["ns24"], "- SAVE_ON_ERROR=all: the same for runs that fail.", "Follows the value change.", [("PLAN", "| executions (take) |")], dep="L-SAVE")
edit("ns27", "NS", OLD["ns27"],
     "With these settings n8n keeps run data for every run until its pruning removes it, including the request body (the made-up name and e-mail) and everything the nodes pass on. The earlier lane3 grep (relayed by the lead, n=1, flows without saving settings; tagged UNBACKED in PAGE-STATEMENTS-V4.md statement 18) found name, e-mail and key in the write-ahead file: it is a reason to run the leak scan for the take (T7b section below), not a result. Whether a flow's own saving setting overrides the instance setting is not verified here (n8n was not run). The four real-v5 flow files (mf-form, mf-hook, mf-recovery, mf-sub-crm-mail in the folder n8n-flows-real-v5) carry their own settings (none today), so they are set to saveDataSuccessExecution all, saveDataErrorExecution all and saveManualExecutions false; this is right whichever setting n8n lets win. After those flow-file edits the flows must be imported again and one run must be seen in the execution list before the take (the import check).",
     "Do not rely on the instance setting alone; changing the flow files changes their file hashes, so re-import and one run are required. The old text stated n8n's precedence rule as fact while it was not verified (c6k naive review B1); the edit is now safe under either precedence, and the pass or fail test is the import check after the edit (C-4 in the check list).", [("PLAN", "| executions (take) |"), ("EVSET", "n8n-flows-real-v5/mf-form.json")], dep="L-SAVE")
edit("ns43", "NS", "What the page may say (conditions: one machine, made-up data, flows 1ced4e1f):",
     "What the page may say (conditions: one machine, made-up data, flows 1ced4e1f; these scans ran with saving turned off, the take saves every run, so points 1 and 2 were not re-tested for the take):",
     "Lines 44 to 46 describe scans made with saving off (c6j design review M6).", [("PLAN", "| executions (take) |")], dep="L-SAVE")
edit("ns45", "NS", "2. The lead fields (name, e-mail) DO reach n8n's database through the webhook request body, even with the four settings on, until n8n's pruning removes the run. So the four settings reduce what is kept; they do not make n8n keep nothing.",
     "2. The lead fields (name, e-mail) DO reach n8n's database through the webhook request body until n8n's pruning removes the run. For the take, saving is set to all, so n8n also keeps the data every node passes on. Nothing is claimed about n8n keeping less.",
     "Lines 44 to 46 said the four settings reduce what is kept, which is false once saving is all (c6j design review M6).", [("PLAN", "| executions (take) |")], dep="L-SAVE")
edit("ns48", "NS", OLD["ns48"],
     "My flows never put a key into n8n; the likely route is a key sent as a body field (matches HB171), not proven.\n\n## T7b for the take (the leak scan; saving is all; NOT RUN yet; replaces the old pass rule written for saving off)\nT7b is the test t7b in the test program mf.py: it plants fake values, runs leads and searches the stores for them. Run this version on the loopback stand-ins only (fake CRM, fake mail server, fake model), never on the real CRM or the real mailbox: case 2 puts a fake key into a form field and on the real path that field would reach a real CRM row and a real mail.\nStores to scan, hits counted per store and never merged: (1) n8n's database with its write-ahead and shared-memory files (a SQLite file today; the n8n database inside Postgres if the loopback re-smoke shows that n8n runs on Postgres, and then the scan must read that database), (2) n8n's log, (3) the exported flow files, (4) the stage journal (the file stage-journal.jsonl named at mf.py line 12), (5) the stage's spend ledger (the ledger exists; its path comes from the take's config and this audit did not find it, so the builder names it), (6) the stage's own log.\nPlanted values (all made up, built from parts): a fake model key, a fake mail password, a name, an e-mail address.\nCase 1, secrets in their proper places: the fake model key sits in the stage key file and the fake mail password in the n8n mail credential; no form field carries either. PASS: 0 hits for both in all six stores. FAIL: any hit; filming stops, the leak is fixed where the value escapes (a credential or masking fault), and the test is run again unchanged.\nCase 2, key in a request body field: one lead is sent whose form field carries the fake key. EXPECTED (not yet measured): hits for the key in n8n's database, because the request body is saved while saving is all, and 0 hits in the stage journal, the spend ledger, the logs and the flow files; the 0 hits in the stage journal are an expectation to be measured, not a known result. This case is the evidence for the written warning never to send a secret in a lead form field. FAIL: a hit in any store other than n8n's database. 0 hits in n8n's database is recorded as a surprise and is not a fail.\nName and e-mail: expected in n8n's database. PASS: 0 hits in the stage journal, the spend ledger and the logs. FAIL: re-scope the page statement to what the scan showed (statement 18); never change the test to make it pass.\nWho builds the scan: a builder named by the studio lead extends t7b in mf.py; the studio lead runs the scan before the first rehearsal and again after any change to a flow file or to a saving setting. Today t7b scans only n8n's data folder, n8n's log and the flow JSON (mf.py lines 283 to 295, with the write-ahead check at lines 297 to 318) and forces saving off (line 278), so a pass of today's t7b says nothing about the take. This audit wrote no code.",
     "The old rule 'key in a request body field: 0 hits' cannot pass because the body is saved (c6i design review). Added in c6j design review M7: loopback stand-ins only; stage-journal 0 hits is an expectation; scan line numbers 283 to 295 (the write-ahead check is 297 to 318); the n8n database may be Postgres after C-8.",
     [("NS", "3. Nobody must send a secret"), ("MF", "def t7b"), ("MF", "EXTRA.update(EXECUTIONS_DATA_SAVE_ON_SUCCESS"), ("MF", "JOURNAL, CRMLOG")], dep="L-SAVE")

# =============================== mf.py
edit("mf276", "MF", "Pass: key 0 hits and SMTP password 0 hits (credentials are encrypted at rest; they must not appear in execution data), name and e-mail 0 hits when execution saving is off",
     "SAVING-OFF CHECK ONLY (line 278 forces saving off, so a pass here says nothing about runs that n8n saves; the leak scan for saved runs, once written, is described in N8N-START.md under T7b for the take). Pass: key 0 hits and SMTP password 0 hits (credentials are encrypted at rest; they must not appear in execution data), name and e-mail 0 hits when execution saving is off",
     "The docstring presented this test as the privacy test of the take. The new text is true whether the take saves runs or not, so the row needs no answer (c6k design review m4).", [("MF", "EXTRA.update(EXECUTIONS_DATA_SAVE_ON_SUCCESS")])
edit("mf320", "MF", "execution saving off at env and workflow level: hits per needle: %s",
     "execution saving forced off by this test (says nothing about runs that n8n saves): hits per needle: %s",
     "The printed result line also said 'execution saving off' as if it described the take (c6j design review M7). The new line is short and true either way, so the row needs no answer (c6k design review m4 and naive minor on a long printed line).", [("MF", "def t7b")])
# =============================== flow files (real-v5)
for fk, fname in (("JF", "mf-form.json"), ("JH", "mf-hook.json"), ("JR", "mf-recovery.json"), ("JS", "mf-sub-crm-mail.json")):
    for which, ev in (("Success", OLD["j_%s_saveDataSuccessExecution" % fk]), ("Error", OLD["j_%s_saveDataErrorExecution" % fk])):
        edit("j%s%s" % (fk, which), fk, ev, ev.replace("none", "all"),
             "The flow's own setting is none, which hides every run from the execution list that scenes 1 and 2 film (all 8 flow files carry none, none, false and no error workflow).",
             [("EVSET", "n8n-flows-real-v5/mf-form.json"), ("PLAN", "| executions (take) |")], dep="L-SAVE")

# =============================== DECISION-one-store.md
edit("one13", "ONE", "## DECISION", "## DECISION (TARGET: the sentences below say what the take is meant to look like; they are not true until the loopback re-smoke shows that n8n runs on Postgres, check C-8)",
     "The wording of decision 10 is the target; findings row F-011 says n8n still starts on its own SQLite file (c6j design review m7).", [("FND", "| F-011 |")])
edit("one14", "ONE", OLD["one14"], "**One Postgres server with two databases: n8n's own and the take's** (one container, one engine)",
     "The lead's decision 10 orders this wording.", [("DEC", "10. Wording"), ("FND", "| F-011 |")])
edit("one16", "ONE", "3. **Logs: one place = Postgres.**", "3. **Logs: one place = Postgres (target; true only after check C-8).**",
     "Line 16 states the target as fact (c6j design review m7).", [("FND", "| F-011 |")])


# ---------------------------------------------------------------- dependency overrides (one place)
CARD = ["rs82", "rs80", "rs41a", "rs41b1", "rs41b2", "rs41c", "rs33d", "rs14", "rs5b"]
DEP = {"rs82": "L-CARD, L-CARDCUT", "rs80": "L-CARD, L-CARDTEXT", "rs41a": "L-CARD, L-CARDCUT, L-CARDTEXT",
       "rs41b1": "L-CARD, L-LEASE", "rs41b2": "L-CARD, L-CARDCUT, L-CARDTEXT", "rs41c": "L-CARD, L-CARDCUT",
       "rs33d": "L-CARD, L-CARDCUT", "rs14": "L-CARD, L-CARDCUT", "rs5b": "L-CARD, L-CARDCUT",
       "rs33a": "", "pg161": "L-APPROX", "pg154": "", "pg134": "L-PAGE", "pg148": "L-PAGE", "pg149a": "L-APPROX",
       "rs32": "L-LEASE", "ns4a": "L-ONEDB, C-8", "ns4b": "L-ONEDB, C-8"}
for e in EDITS:
    if e["key"] in DEP:
        e["dep"] = DEP[e["key"]]
    assert "L-ROUND" not in e["dep"]

VIEW = {'rs90': "Scene 4 shows no timing number and no rounded wording; the live stopwatch and the label 'setting: lease 45 s' stay.", 'rs85': 'Nothing (an old note on the run sheet is corrected).', 'rs82': 'The closing card makes no statement about how quickly an alert mail arrives.', 'rs80': 'Closing card: the retention sentence is the third spoken line.', 'rs79': 'Nothing on screen (an open question on the run sheet is closed).', 'rs71': 'Nothing on screen; the take is blocked until the workflow list, the contact-deletion check and the saved-runs checks are written on the run sheet.', 'rs70': 'Nothing (a note on the run sheet).', 'rs59': 'Nothing on screen; the take is blocked until the studio lead has written the result of the contact-deletion check.', 'rs51': 'Nothing (a note on the run sheet).', 'rs47': 'Nothing (a note on the run sheet).', 'rs44': 'Nothing on screen; the run sheet gives the length of the one video: 3 minutes.', 'rs41a': 'Closing card has four spoken lines instead of six.', 'rs41b1': 'Closing card line 1 adds the sentence that the repeat-send statement holds only within 45 seconds.', 'rs41b2': 'Closing card lines 2 to 4: no alert-delay statement, the retention sentence, what was not tested.', 'rs41c': 'Closing card shows none of the old history numbers.', 'rs36': 'Nothing (a note on the run sheet).', 'rs33a': 'Scene 4 caption row: no recovery-time caption.', 'rs33b': 'Nothing on screen (planning note for the cut).', 'rs33c': 'Nothing on screen (planning note).', 'rs33d': 'Nothing on screen (planning note).', 'rs32': 'Scene 3 caption adds the sentence about the 45 seconds.', 'rs31': 'Nothing on screen (a rule for the owner).', 'rs30a': 'Before scene 1 the execution list is cleaned and checked; old runs are not on screen.', 'rs30b': "Scene 1 shows the execution list with the recovery flow's run every 30 seconds.", 'rs24': 'Nothing (a note on the run sheet).', 'rs23a': 'Nothing on screen (planning note).', 'rs23b': 'Nothing on screen (planning note).', 'rs22': 'Nothing (a note on the run sheet).', 'rs14': 'Nothing (a note on the run sheet).', 'rs5b': 'Nothing (a note on the run sheet).', 'rs5a': 'Nothing (a note on the run sheet).', 'rs4': 'Nothing (a note on the run sheet).', 'pg23': 'Web page: the lane3 numbers note says which numbers were read from files.', 'pg105': 'Web page, statement 14: points to statement 20 instead of a contradiction.', 'pg120a': 'Web page, statement 17: points to statement 20.', 'pg120b': 'Web page, statement 17: the rough recovery rule is called unusable.', 'pg125': 'Web page, statement 18: says n8n keeps the data of every run (still unbacked).', 'pg134': 'Web page: statement 19 (13-minute alert delay) is marked not for the page.', 'pg139': 'Web page: the limits list points to statement 20.', 'pg148': 'Web page: statement 20 is marked not for the page.', 'pg149a': 'Web page, statement 20: correct count (10 done, 8 unknown with one alert) and the two voided runs named.', 'pg149b': 'Web page, statement 20: says the raw table was read.', 'pg150': 'Web page: the two crash test names K3B and K3 are described correctly.', 'pg153': 'Web page: the K3B and K3 results are described correctly (0 and 1 mails).', 'pg154': 'Web page, statement 20: the from-n8n-back-up range starts at 52.8.', 'pg156': 'Web page: the 13-minute figure is labelled as not used in the video.', 'pg159': 'Web page: caption rule says no timing number.', 'pg161': 'Web page: no caption wording for the recovery time.', 'ns4a': 'Nothing on screen (start notes: where n8n keeps its data).', 'ns4b': "Nothing on screen (start notes: the claim table's database).", 'ns15': 'Start notes: the take saves every run, so the execution list shows runs.', 'ns17': 'Nothing on screen (setting value for the take).', 'ns18': 'Nothing on screen (setting value for the take).', 'ns23': 'Nothing on screen (start notes).', 'ns24': 'Nothing on screen (start notes).', 'ns27': 'Nothing on screen (start notes: flow-file settings and the import check).', 'ns43': 'Nothing on screen (start notes: what the page may say).', 'ns45': 'Nothing on screen (start notes: what n8n keeps).', 'ns48': 'Nothing on screen (start notes: the leak scan for saved runs is described).', 'mf276': 'Nothing (a comment in the test program).', 'mf320': 'Nothing (a printed line of the test program).', 'one13': 'Nothing (the one-store decision is marked as a target).', 'one14': 'Nothing (the one-store decision wording).', 'one16': 'Nothing (the one-store decision wording).', 'jJFSuccess': "Scenes 1 and 2: the execution list shows the runs of this flow (setting 'save successful runs' = all).", 'jJFError': "Scenes 1 and 2: the execution list shows the runs of this flow (setting 'save failed runs' = all).", 'jJHSuccess': "Scenes 1 and 2: the execution list shows the runs of this flow (setting 'save successful runs' = all).", 'jJHError': "Scenes 1 and 2: the execution list shows the runs of this flow (setting 'save failed runs' = all).", 'jJRSuccess': "Scenes 1 and 2: the execution list shows the runs of this flow (setting 'save successful runs' = all).", 'jJRError': "Scenes 1 and 2: the execution list shows the runs of this flow (setting 'save failed runs' = all).", 'jJSSuccess': "Scenes 1 and 2: the execution list shows the runs of this flow (setting 'save successful runs' = all).", 'jJSError': "Scenes 1 and 2: the execution list shows the runs of this flow (setting 'save failed runs' = all)."}
for e in EDITS:
    e['view'] = VIEW[e['key']]

# ---------------------------------------------------------------- order and numbering
def sortkey(e):
    return (ORDER.index(e["fk"]), -e["line"], e["key"])


EDITS.sort(key=sortkey)
for i, e in enumerate(EDITS, 1):
    e["n"] = i
NUM = {e["key"]: e["n"] for e in EDITS}
json.dump(EDITS, open(C6 + "/evidence-c6m/edits.json", "w"), indent=1)
print("edits", len(EDITS))
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'report_c6m.py')).read())
