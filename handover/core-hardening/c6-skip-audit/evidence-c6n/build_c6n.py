"""Builds REPORT-c6n.md from REPORT-c6m.md (read only). Every text patch must match exactly once (assert), so a silent miss is impossible.
Usage: python3 build_c6n.py   (run from anywhere). Output: REPORT-c6n.md next to REPORT-c6m.md."""
import re, sys
D = "/home/user/hadavin-sdk/handover/core-hardening/c6-skip-audit/"
src = open(D + "REPORT-c6m.md", encoding="utf-8").read()
LINES = src.split("\n")


def sub(t, old, new, count=1):
    n = t.count(old)
    assert n == count, "patch matched %d times (want %d): %r" % (n, count, old[:90])
    return t.replace(old, new)


# ---------------------------------------------------------------- parse rows
PAT = re.compile(r"^\| (\d+) \| (NOT APPLIED[^|]*?) \| (handover/[^|]+?) \| (\d+) \| ([^|]*) \| `(.*?)` \| `(.*?)` \| (.*) \| ([^|]*) \|$")
rows = {}
row_line_idx = {}
for i, l in enumerate(LINES):
    m = PAT.match(l)
    if m:
        k = int(m.group(1))
        rows[k] = dict(i=k, st=m.group(2), f=m.group(3), ln=m.group(4), view=m.group(5), old=m.group(6), new=m.group(7), why=m.group(8), was=m.group(9))
        row_line_idx[k] = i
assert sorted(rows) == list(range(1, 73)), "rows parsed wrong"


def rnew(k, old, new, count=1):
    rows[k]["new"] = sub(rows[k]["new"], old, new, count)


def rwhy(k, old, new, count=1):
    rows[k]["why"] = sub(rows[k]["why"], old, new, count)


def rview(k, old, new):
    rows[k]["view"] = sub(rows[k]["view"], old, new)


def set_dep(k, toks):
    rows[k]["st"] = "NOT APPLIED; " + ("ready" if not toks else "; ".join(
        ([("after check " + ", ".join(t for t in toks if t.startswith("C-")))] if any(t.startswith("C-") for t in toks) else []) +
        ([("on the default of " + ", ".join(t for t in toks if t.startswith("L-")))] if any(t.startswith("L-") for t in toks) else [])))


TOK = re.compile(r"L-[A-Z]+|C-\d+[a-d]?")
# sanity: the status builder reproduces the c6m status strings
for k, r in rows.items():
    before = r["st"]
    set_dep(k, TOK.findall(before))
    assert rows[k]["st"] == before, (k, before, rows[k]["st"])

# ---------------------------------------------------------------- row edits
# --- R1 (naive m5, M6; design none)
rows[1]["new"] = ('Scene 4 filming note (a note for the person filming; it is not a caption): no test result in seconds in any caption, text card or voice '
                  '(the studio lead cut the number from the video on 2026-11-16), and no rounded wording such as "about a minute". A live stopwatch overlay and the label '
                  '"setting: lease 45 s" (a setting, not a measured time) are shown. The 18 kept crash runs of lane3 (60.1 to 61.9 s from the crash to the final state; '
                  '52.8 to 54.9 s from n8n coming back up) were measured on the film-v4 stand-in flows, not on the flows of this take, and stay out of the video. '
                  'Two further lane3 runs at the same lease, VOID-fl45k3b (it never reached a final state, 338.7 s) and VOID-fl45k6c (the stand-in services were not up), '
                  'were voided and are not counted; the cause is unknown. The kill cases K3B and K3 are not mentioned in scene 4. No statement about alert delay is made. Never "within 60 s".')
rview(1, "Scene 4 shows no timing number and no rounded wording", "Scene 4 shows no test result in seconds and no rounded wording")
rwhy(1, "It says 'no timing number in any caption or text card' because a live stopwatch overlay is shown.", "It says 'no test result in seconds' because a live stopwatch overlay and the 45-second lease setting are shown (the 45 seconds is a setting that the video says, not a test result; section 'Words').")
rwhy(1, "The 18 runs are the 18 KEPT runs;", "The new text is a filming note, not a caption (c6m naive review m5). The 18 runs are the 18 KEPT runs;")

# --- R3, R4 dependency ties (design m4)
set_dep(3, ["L-CARD", "L-CARDCUT", "L-CARDTEXT"])
set_dep(4, ["L-CARD", "L-CARDCUT", "L-CARDTEXT"])
rwhy(3, "Sources: RES:78", "Row 3 is tied to L-CARDTEXT as well (it is the card line about alert delay); c6m design review m4. Sources: RES:78")
rwhy(4, "Sources: RS:41", "Row 4 is tied to L-CARDCUT as well (the line moves only if the card is shortened); c6m design review m4. Sources: RS:41")

# --- R9 wording
rnew(9, "failed-lead wait", "failed-contact wait")

# --- R11 (naive M4; design M2 of word count is in section 0)
rnew(11, "(lead decision of 2026-11-16)", "(the studio lead's decision of 2026-11-16)")
rwhy(11, "Sources: DEC:2 (decision 1)", "The closing card is budgeted 30 s here; its four spoken lines hold about 150 words, which is more than 30 s of speech (section 0 gives the count); rehearsal list item 10 (stopwatch) decides whether the card or the total changes. Sources: DEC:2 (decision 1)")

# --- R6 (naive M3, M7, M8, m1; design m5, m9)
rows[6]["new"] = (
    "10. Run the whole take once with a stopwatch; compare to the EST column and re-total."
    "<br>11. ACTIVE FLOWS. Before every rehearsal and before the take, list the active workflows in n8n. Only workflows imported from the folder n8n-flows-real-v5 may be active: the form entry flow, the hook entry flow, the recovery flow, and the shared-step flow if it is active. "
    "No workflow from any other folder, and no workflow with the paths mf-form or mf-hook from n8n-flows-film-v5 or an older folder, may be active. "
    "Write the list, with the date and time in UTC and IST, into the studio's handoff note (the file handoff\\SESSION-HANDOFF.md in the studio folder, not in this repository). "
    "If any other workflow is active, the studio lead stops, switches it off, and lists again; nothing starts until the list is right. (This check needs n8n and is not run yet.)"
    "<br>12. OWNER SHEET. When the final version of the files is known, the studio lead reads the owner sheet the owner reads. It must say that the owner deletes leftover made-up contacts by hand, "
    "and it must not say that the HubSpot key is read-only or limited to create and change, unless the owner has confirmed that. "
    "(The search of the take script for archive and delete calls is item 11 of the list \"Risks the owner must see\" on this run sheet; it is not repeated here.) "
    "If the sheet says otherwise, the studio lead has it corrected before any rehearsal with real accounts, and the take does not start."
    "<br>13. REPEAT-SEND TIMING (scene 3). The 45-second lease starts when the first send arrives, because the flow writes the claim row at that moment (mf-form.json line 97), not when the reply is shown. "
    "Write down the clock time of the first send in scene 2 and of the repeat send in scene 3 (UTC, to the second), and the reply text of the repeat. "
    "The gap between the two sends must be less than 30 seconds, so that 15 seconds of margin remain before the lease ends. "
    "Scene 2 is budgeted 40 seconds, so if the first send is the first thing in scene 2 the repeat comes about 40 seconds later, too close to 45: make the first send late in scene 2, or shorten scene 2, and redo the scene until the gap is under 30 seconds. "
    "After the repeat the CRM list must still show 1 row and the test mailbox 1 mail; if not, stop and tell the studio lead (rule: the person who sees it first says stop; the studio lead decides whether to film again)."
    "<br>14. GATE, saved runs. This item applies from the moment the four real-v5 flow files are edited to save every run (if they are not edited, delete this item). From then on n8n saves every run, so a secret sent in a form field would be stored. "
    "The take, and any rehearsal with real accounts, does not start until this run sheet shows two lines, each with the date and time in UTC and IST (for example 2026-11-18 09:00 UTC = 14:30 IST) and the name of the person who ran it: "
    "\"import check passed: the execution list shows runs of an entry flow and of the recovery flow\" and \"leak scan for saved runs passed: pass lines met on the loopback stand-ins\". "
    "Gate owner: the studio lead. He runs both checks himself, or names a builder to write the leak scan; the builder's name is written here: ______ (while it is empty, the gate cannot pass). "
    "Both checks run on this computer only, with stand-in services, before the first rehearsal with real accounts. If either check fails, the studio lead stops, the take and every rehearsal with real accounts stay blocked, the cause is fixed where the value escapes, the check is run again unchanged, and the owner is told that the take is delayed.")
rwhy(6, "Item 12 is re-issued against the studio lead's answers Q23 and Q27 (ORDERS.md): decision 2 stands (the take never deletes), the audited tree has no take script, so the grep is the studio lead's step at the final version and its result is UNVERIFIED until written; the old requirement of 0 hits for 'never deletes' in the decisions file is dropped because the file states the rule (c6l design review B1).",
        "Item 12 now holds only the owner-sheet check: the search of the take script was written twice (here and in row 8) and is kept only in row 8 (c6m design review m5, c6m naive review M3). The old requirement of 0 hits for 'never deletes' in the decisions file stays dropped because the file states the rule (c6l design review B1).")
rwhy(6, "Item 14 is new: saved runs are switched on by the flow-file rows, the import check and the leak scan are not run yet, so the take is blocked until both lines are on the run sheet, with a named owner (c6l design review M5). The shared-step flow may be active if it is a real-v5 file. Item 13 has a target (under 45 seconds) and a pass test.",
        "Item 14 is the saved-runs gate (c6l design review M5): it now says it applies only if the flow files are edited (it does not depend on the rows that edit them, c6m design review m9), names the gate owner and gives a stop rule with UTC and IST (c6m naive review M8, m1). Item 13 measures from the first SEND, not from the first reply, and asks for under 30 seconds, because the lease starts when the claim row is written (c6m design review M1). Names of the two lists: this row adds items 11 to 14 to the REHEARSAL LIST (heading 'What must be rehearsed on the laptop before the take', run sheet line 71); row 8 adds items 11 and 12 to the RISKS LIST (heading 'Risks the owner must see', run sheet line 59). The shared-step flow may be active if it is a real-v5 file.")
rwhy(6, "ORD:132, MF:45", "ORD:132, MF:45, JF:97")
rview(6, "Nothing on screen; the take is blocked until the workflow list, the contact-deletion check and the saved-runs checks are written on the run sheet.", "Nothing on screen; the take is blocked until the workflow list, the owner-sheet check and the saved-runs checks are written on the run sheet, and scene 3 is timed from the first send.")
rows[6]["old"] = rows[6]["old"]  # unchanged

# --- R8 (naive M3, M7, M8; design m6, m9)
rows[8]["new"] = (
    "10. Step-2 fault for a real mailbox and the Slack alert are NOT BUILT; the take says \"stand-in\" or cuts."
    "<br>11. GATE, contact deletion (the studio lead's step). The studio lead decided that the take never deletes contacts, and his written answer of 2026-11-16 12:50 UTC (18:20 IST) confirms it: the independent review of 11:00 UTC (16:30 IST) found no archive and no delete call in the take script scripts/run_real_check_n8n.py (only a listing request), and the HubSpot key is not widened. "
    "This is UNVERIFIED by the audit, because the script is not in the audited files: the studio lead verifies at the re-pin (the moment the final version of the take files is put together and he reads them again). "
    "Two scripts have similar names: scripts/run_real_check_n8n.py is the take script the video uses (it lives on a local take branch that is never pushed); scripts/run_real_check.py is the old desk test program, whose help text offers a clean-up option that archives contacts, and it is not the take (the studio lead's written answer of 10:35 UTC = 16:05 IST says the archive step the audit read belongs to that old program). "
    "Older plan text that shows the owner a notice \"up to 3 HubSpot contacts archived at the end\" is probably stale (the studio lead's answers of 10:35 UTC and 12:50 UTC say so; he confirms at the re-pin) and must not be shown. "
    "The take does not start until the studio lead has written here, with date and time in UTC and IST: (1) the version id of the files he read; (2) the output of grep -n -i archive and grep -n -i delete on scripts/run_real_check_n8n.py at that version (no hit, or the lines); "
    "(3) \"matches the decision\" or, if a line was found, \"stop: tell the owner\"; (4) that no owner sheet and no notice shows a line promising that contacts will be deleted or archived by the program. "
    "If a line is found the take does not start until the studio lead and the owner have decided in writing what happens. Until then nothing is touched in the CRM. Not checked: whether an archived contact keeps its e-mail address reserved."
    "<br>12. GATE, the repeat-send statement: scene 3 and card line 1 are not filmed until the unique index on the contact table (the database rule that refuses a second row for the same contact id) has been seen in the table of the take's own database. "
    "Seen means: in the loopback re-smoke the studio lead lists the table's rules (the psql command \\d mf_leads) and writes the output here, and the output shows a primary key or a unique rule on the contact id. "
    "If it is not seen, only the studio lead may write \"index not seen, accepted\" here, with the date and time in UTC and IST, before the take and after telling the owner; if he does not, scene 3 and card line 1 are cut and the take goes on without them. "
    "In the test program the table is created with a primary key on the contact id (mf.py line 45), which is the same kind of rule; that is not proof for the take database.")
rwhy(8, "Item 12: who writes 'index not seen' is named.", "Item 12: who writes 'index not seen', when, and what happens if nobody does are named (c6m naive review M8); 'seen in the take's own database' now says how it is seen (c6m naive review 'could not follow'). This row adds items 11 and 12 to the RISKS LIST (run sheet line 59); row 6 adds items 11 to 14 to the REHEARSAL LIST (line 71); the contact-deletion search exists only here (c6m naive review M3, design m5). The older plan notice is called 'probably stale' because the audit only infers it from the studio lead's answers (c6m design review m6).")
rview(8, "Nothing on screen; the take is blocked until the studio lead has written the result of the contact-deletion check.", "Nothing on screen; the take is blocked until the studio lead has written the result of the contact-deletion check, and scene 3 is filmed only if the repeat-send rule was seen or accepted.")

# --- R13 (lead -> contact; alert/lease words; from the first send)
rows[13]["new"] = ('Line 1, statement, spoken: "A lead sent twice with the same id is processed once. We say this only when the second send comes within 45 seconds of the first send. '
                   'The 45 seconds is a setting called the lease: for that long the system keeps that contact reserved for the run that took it first."')
rwhy(13, "this sentence says the same in plain words and is the question L-LEASE.", "this sentence says the same in plain words and is the question L-LEASE. The first sentence is the studio lead's own exact wording (decision 1); in it 'lead' means a made-up sales contact, and the new sentences say 'contact' (c6m naive review M4). 'Lease' is explained where it is first spoken (c6m naive review M5). The 45 seconds are counted from the first send because the lease starts when the claim row is written (c6m design review M1).")
rwhy(13, "Sources: ORD:151", "Sources: ORD:151, JF:97")

# --- R14 (alert defined; retention wording; design m3)
rows[14]["new"] = ('Line 2, alerts, spoken: "When the system cannot tell whether a contact was fully handled, it sends one alert: a warning mail that asks a person to look. We make no statement about how quickly an alert mail arrives." '
                   'Line 3, retention, spoken: "The made-up name and e-mail address sent to n8n may stay in n8n\'s own database. We did not measure how long they stay, or whether n8n\'s automatic removal of old runs ever removes them." '
                   'Line 4, not tested, spoken: "Not tested: other mailboxes, other CRMs (customer-record systems), alerts sent as chat messages, other lease settings. One machine, made-up people, our own runs."')
rows[14]["why"] = ("Split of the old row 13 (c6k design review M1): alerts, retention and not-tested lines. Line 2 now says what an alert is before it says anything about alerts (c6m naive review M5). "
                   "Line 3 no longer assumes that n8n's automatic removal of old runs is on: N8N-START.md line 42 says the setting was still being tested and no file sets it, so the line says we did not measure how long the data stays or whether the removal ever happens (c6m design review m3); it is true whether saving is all or none, because the request body reaches n8n's database in both cases (N8N-START.md lines 44 to 46); 'name and address' is 'name and e-mail address'; 'Slack alert' is 'alerts sent as chat messages'. "
                   "Old line 2 (80 kills) is cut because it counts runs of older v3 flows with a 20 s lease on stand-ins, not the flows of the take; old line 3 (recovery 'about the lease plus 25 to 30 s') is cut because the lane3 runs at 45 s ended 60.1 to 61.9 s after the crash, which does not match 70 to 75 s (c6l design review M2: the K3B wording is not on the card). Sources: MF:153, RS:82, NS:42, NS:45")

# --- R17 (M6 contradiction)
rows[17]["new"] = ('No test result in seconds in any caption or in the voice. On screen: the stopwatch overlay (the clock of this run) and the label "setting: lease 45 s". '
                   'The 45-second lease setting is also said on the closing card and in the scene 3 caption (it is a setting, not a test result).')
rview(17, "Scene 4 caption row: no recovery-time caption.", "Scene 4 caption row: no recovery-time caption; the stopwatch and the lease label stay.")
rwhy(17, "The old text says 'no number' yet shows a label: this says 'no timing number'.", "The old text says 'no number' yet shows a label: this says 'no test result in seconds' and names what stays (c6m naive review M6).")

# --- R21
rows[21]["new"] = ('Caption: "a lead sent twice with the same id is processed once". Second caption line: "We say this only when the second send comes within 45 seconds of the first send. '
                   'The 45 seconds is a setting called the lease: for that long the system keeps that contact reserved for the run that took it first." '
                   'No result exists for this repeat send on the flows of this take, so the rehearsal must show the repeat reply and the clock times of both sends (write them on this run sheet); '
                   'the repeat send must come less than 30 seconds after the first send (the lease starts when the first send arrives), before the take. The screen is the evidence.')
rwhy(21, "Sources: ORD:151, ORD:186", "The gap is counted from the first send, not from the first reply, and must be under 30 seconds (c6m design review M1). Sources: ORD:151, ORD:186, JF:97")

# --- R22, R24
rnew(22, "into the lead fields", "into the contact fields")
rnew(24, "(no lead in flight)", "(no contact in flight)")
# --- R23 (naive M8, m1, m2)
rows[23]["new"] = ("Before scene 1 the studio lead (not the owner) removes every execution made before the take (rehearsal and smoke runs) from n8n's execution list on the screen, and writes the time of that removal, in UTC and IST, on this run sheet as the take start time. "
                   "Then the studio lead checks on the screen that every row shows a start time after the take start time and that no row shows rehearsal data. "
                   "This hides the old runs from the screen; whether n8n also erases them from its database is not verified (the start notes say a deleted run is only marked deleted until n8n's automatic removal of old runs; the re-smoke plan says deletion is removal of the container). "
                   "New rows from the recovery flow (one run every 30 seconds) are expected and are not a fault. The same check is made before every rehearsal and again before scene 2, with the same take start time. "
                   "If a row older than the take start time still shows, the studio lead stops filming, hides the rows again and checks again; filming goes on only when the check passes.")
rview(23, "Before scene 1 the execution list is cleaned and checked; old runs are not on screen.", "Before scene 1 the old runs are hidden from the execution list and checked; none is on screen.")
rwhy(23, "It now says who deletes (the studio lead)", "It now says who removes the old runs from the screen (the studio lead) and who stops filming if one still shows (the studio lead, not the owner: c6m naive review M8)")

# --- R37 (lead -> contact)
rnew(37, "lead ends unknown with 1 alert to the owner, no second mail. K3B:", "the contact ends unknown with 1 alert to the owner, no second mail. K3B:")
# --- R40, R48: file lives on another branch (design m9)
rnew(40, "(read by the audit; the lane3 report named HB194 is not itself in the tree).", "(read by the audit on the branch cloud/core-hardening; that file is not on the demo branch that holds the page statements, so a reader of this page needs that branch; the lane3 report named HB194 is not itself in the tree).")
rnew(48, "the audit read their lane3 results table (RESULTS.md, lines 89 to 92, in handover/core-hardening/c6-skip-audit/raw-lane3/).", "the audit read their lane3 results table (RESULTS.md, lines 89 to 92, in handover/core-hardening/c6-skip-audit/raw-lane3/ on the branch cloud/core-hardening, not on the demo branch that holds this file).")
rnew(48, "is a lead relay", "was relayed by the studio lead")
rnew(41, "FINAL, lead relay of lane3 HB194", "FINAL, relayed by the studio lead from lane3 report HB194")
# --- R44 (retention; design m3)
rnew(44, "so n8n keeps the made-up name and e-mail of the contact, and everything the nodes pass on, in its own database until n8n's pruning removes the run; the pruning age is not measured.",
     "so n8n keeps the made-up name and e-mail of the contact, and everything the nodes pass on, in its own database; whether and when n8n's automatic removal of old runs (pruning) removes them was not measured (N8N-START.md line 42 says the pruning setting was still being tested, and no file sets it).")
rwhy(44, "Sources: PLAN:125", "Sources: PLAN:125, NS:42")
# --- R49, R50, R54 (lead -> contact)
rnew(49, "runs leads and searches", "runs contact records and searches")
rnew(49, "one lead is sent whose form field carries the fake key", "one contact record is sent whose form field carries the fake key")
rnew(49, "to send a secret in a lead form field", "to send a secret in a form field")
rnew(50, "The lead fields (name, e-mail)", "The contact fields (name, e-mail)")
rnew(54, "made-up lead name and e-mail", "made-up contact name and e-mail")
rnew(50, "until n8n's pruning removes the run.", "until n8n's automatic removal of old runs (pruning) removes the run, if it ever does.")
# --- R58, R59 (design M2 / naive m3: L-ONEDB no longer ties any row)
set_dep(58, ["C-8"])
set_dep(59, ["C-8"])
rnew(59, "for the lead table (a separate", "for the contact table (a separate")
rwhy(58, "Sources: ONE:14", "This row no longer waits for the question L-ONEDB: it carries target wording, not an interim sentence about stores (c6m design review M2). Sources: ONE:14")
rwhy(59, "Sources: ONE:14", "Same as row 58. Sources: ONE:14")
# --- R62-R69 (naive m6, m7)
rwhy(62, "(all 8 flow files carry none, none, false and no error workflow)", "(all 8 flow files, 4 real-v5 and 4 film-v5, carry none, none, false and no error workflow; these eight rows edit only the 4 real-v5 files)")
for k in range(63, 70):
    r = rows[k]
    m = re.match(r"The flow's own setting is none, which hides every run from the execution list that scenes 1 and 2 film \(all 8 flow files carry none, none, false and no error workflow\)\. Sources: (.*)$", r["why"])
    assert m, (k, r["why"][:200])
    r["why"] = "Same reason as row 62 (this flow file, this one setting). Sources: " + m.group(1)

# ---------------------------------------------------------------- regenerate the table
HEAD_IDX = [i for i, l in enumerate(LINES) if l.startswith("| ID | Status | Target file")][0]


def row_line(r):
    return "| %s | %s | %s | %s | %s | `%s` | `%s` | %s | %s |" % (r["i"], r["st"], r["f"], r["ln"], r["view"], r["old"], r["new"], r["why"], r["was"])


for k, idx in row_line_idx.items():
    LINES[idx] = row_line(rows[k])
text = "\n".join(LINES)

# per-question recount (same logic as verify)
cnt = {}
for k, r in rows.items():
    for t in set(TOK.findall(r["st"])):
        cnt.setdefault(t, []).append(k)
ready = [k for k, r in rows.items() if not TOK.findall(r["st"])]
onlyq = [k for k, r in rows.items() if TOK.findall(r["st"]) and all(t.startswith("L-") for t in TOK.findall(r["st"]))]
withc = [k for k, r in rows.items() if any(t.startswith("C-") for t in TOK.findall(r["st"]))]
assert (len(ready), len(onlyq), len(withc)) == (35, 34, 3), (len(ready), len(onlyq), len(withc))
fl = lambda xs: ", ".join(str(x) for x in sorted(xs))

# ---- 3b table
tb = ["| Question or check | Rows tied to it | How many | Of those: wait ONLY for this | Of those: also wait for something else |", "|---|---|---|---|---|"]
for t in sorted(cnt, key=lambda x: (x[0] != "L", x)):
    ks = sorted(cnt[t])
    only = [k for k in ks if set(TOK.findall(rows[k]["st"])) == {t}]
    other = [k for k in ks if k not in only]
    tb.append("| %s | %s | %d | %d (%s) | %d (%s) |" % (t, fl(ks), len(ks), len(only), fl(only) if only else "none", len(other), fl(other) if other else "none"))
tb.append("| (no question, no check) | %s | %d | ready | none |" % (fl(ready), len(ready)))
tb.append("| TOTAL | all rows | 72 | ready %d, on defaults only %d, with a check %d | |" % (len(ready), len(onlyq), len(withc)))
s3b = text.index("| Question or check | Rows tied to it |")
e3b = text.index("\n\n3c.")
text = text[:s3b] + "\n".join(tb) + text[e3b:]

# ---- section 3 'Rows tied to it' column
def fix_tied(text, tok, label_line_prefix):
    lines = text.split("\n")
    for i, l in enumerate(lines):
        if l.startswith("| " + tok + " ") and "| Yes" in l or l.startswith("| " + tok + " (") or l.startswith("| " + tok + " |"):
            pass
    return text


tied = {t: (fl(cnt[t]) if t in cnt else "none") for t in ["L-CARD", "L-CARDCUT", "L-CARDTEXT", "L-LEASE", "L-KILL", "L-APPROX", "L-SAVE", "L-PAGE", "L-ONEDB"]}
s3 = text.index("## 3. Questions")
e3 = text.index("3b. Count of rows per question")
sec3 = text[s3:e3].split("\n")
for i, l in enumerate(sec3):
    m = re.match(r"^\| (L-[A-Z]+)( \(was [^)]*\))? \|", l)
    if m and m.group(1) in tied and len(l.split(" | ")) >= 7:
        cells = l.rstrip(" |").split(" | ")
        cells[-1] = tied[m.group(1)]
        sec3[i] = " | ".join(cells) + " |"
text = text[:s3] + "\n".join(sec3) + text[e3:]

# ================================================================ SECTION PATCHES
# ---- box + WORDS replaced as a block (from '## Start here' to the line before '## 0.')
BOX = open(D + "evidence-c6n/box_c6n.md", encoding="utf-8").read().rstrip("\n")
a = text.index("## Start here")
b = text.index("## 0. Failures")
text = text[:a] + BOX + "\n\n" + text[b:]
text = sub(text, "# REPORT-c6m: video audit fix pass, supersedes REPORT-c6l.md (2026-11-16, UTC; IST = UTC + 5:30)",
           "# REPORT-c6n: video audit fix pass, supersedes REPORT-c6m.md (2026-11-16, UTC; IST = UTC + 5:30)")

# ---- apply the section patches file (exec) so that the long patch list stays readable
ns = dict(sub=sub, rows=rows, cnt=cnt, fl=fl, D=D)
exec(open(D + "evidence-c6n/sections_c6n.py", encoding="utf-8").read(), ns)
text = ns["patch_sections"](text)

open(D + "REPORT-c6n.md", "w", encoding="utf-8").write(text)
print("written REPORT-c6n.md, lines", text.count("\n") + 1, "rows", len(rows), "ready", len(ready), "defaults-only", len(onlyq), "with-check", len(withc))
