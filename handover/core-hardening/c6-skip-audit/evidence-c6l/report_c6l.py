"""Second half of build_c6l.py: writes REPORT-c6l.md. Executed with the edit list already built (EDITS, NUM, F, find, cite)."""
OUT = []
P = OUT.append
TOK = re.compile(r"L-[A-Z]+|C-\d+[a-d]?")


def n(key):
    return NUM[key]


def ids(keys):
    return ", ".join(str(n(k)) for k in keys)


def quote(k, anchor, width=170):
    ln = find(k, anchor)
    t = lines(k)[ln - 1].strip()
    return "%s:%d" % (k, ln), (t[:width] + ("..." if len(t) > width else "")).replace("|", "/")


def cell(s):
    return s.replace("\n", "<br>")


def toks(e):
    return TOK.findall(e["dep"])


def dep_list(tok):
    return [e["n"] for e in EDITS if tok in toks(e)]


def nums(lst):
    return ", ".join(str(x) for x in lst) if lst else "none"


def status(e):
    t = toks(e)
    if not t:
        return "NOT APPLIED; ready"
    q = [x for x in t if x.startswith("L-")]
    c = [x for x in t if x.startswith("C-")]
    parts = []
    if c:
        parts.append("after check " + ", ".join(c))
    if q:
        parts.append("on the default of " + ", ".join(q))
    return "NOT APPLIED; " + "; ".join(parts)


nrows = len(EDITS)
ready = [e["n"] for e in EDITS if not toks(e)]
onlyq = [e["n"] for e in EDITS if toks(e) and all(x.startswith("L-") for x in toks(e))]
withc = [e["n"] for e in EDITS if any(x.startswith("C-") for x in toks(e))]
files = sorted(set(e["fk"] for e in EDITS), key=ORDER.index)
RC, RO, RW = len(ready), len(onlyq), len(withc)
assert RC + RO + RW == nrows

P("# REPORT-c6l: video audit fix pass, supersedes REPORT-c6k.md (2026-11-16, UTC; IST = UTC + 5:30)")
P("")
P("## 0. Read this first (failures, uncertainty, what was not checked)")
P("- NOTHING IN THE EDIT TABLE HAS BEEN APPLIED. Every row says NOT APPLIED. Of the %d rows: %d are 'ready' (no open question and no open check; rows %s); %d apply on the default of a question the studio lead has not answered (section 3); %d wait for a check that cannot run here (rows %s; the checks need n8n). The counts per question are made by a script and checked by a second script (section 3, table 3b). A text in the table is a proposal until a builder applies it and a reviewer reads the changed file." % (nrows, RC, nums(ready), RO, RW, nums(withc)))
P("- NONE OF THE DEFAULTS IS CONFIRMED BY THE STUDIO LEAD. A default is what the table assumes if no answer comes. The question names changed in this report (section 3 maps every old name): the old Q1, Q2, Q9, Q10 are now L-CARD, L-KILL, L-ROUND, L-SHEET, so that they cannot be mixed up with the question numbers of ORDERS.md. L-SAVE rests on one row of the re-smoke plan that says 'owner 2026-11-16' (%s), not on an answer to this report; its pass or fail check is C-11 (done, static) and the import check C-4 (not run). L-DEL has no default; the row that documents the gate (row %d) only records that the gate is closed." % (quote("PLAN", "| executions (take) |")[0], n("rs59")))
P("- CORRECTION OF REPORT-c6k.md ON THE OWNER SHEETS: REPORT-c6k.md said the owner sheets are not on disk and assumed v19 was the newest. Both are wrong. The owner sheets are on this branch in handover/core-hardening/steps-edits/ (OWNER-STEPS-realrun-v4 to v15, OWNER-SHEET-v16 to v25; v24 and v25 each have variants A and B and a SOURCE file). I searched the sheets from v19 on for the three phrases of the closing check (never deletes, read, create and change only, does not delete): v19 has 1 hit (%s) and v20 to v25 (all variants) have 0 hits (evidence-c6l/static-checks-output.txt, section C-10c). So the assumption 'v19' in REPORT-c6k.md was the one sheet that still has a hit. I read only the matching lines and line 46 and 48 of v25-A, not whole sheets." % quote("OS19", "You delete only made-up contacts of this run")[0])
P("- WHAT IS ABSENT FROM THE CHECKED TREE (the read-only copy of branch origin/cloud/flows-audit used for every check; the same copy method as REPORT-c6k.md; folder scratchpad/c6/tree/handover): the three take and probe scripts (scripts/run_real_check.py, scripts/run_real_check_n8n.py, scripts/hubspot_probe.py: 0 found), the lane3 report files HB171, HB180, HB186, HB189 and HB194 (0 found; only their relayed numbers and the lane3 results files in handover/core-hardening/c6-skip-audit/raw-lane3/ exist), and the text of rule R460 (0 hits in handover/bible). The text of QUEUE rule 6 IS on disk (%s, header rule 6) and I read it; REPORT-c6k.md said it was not." % quote("QUE", "6. Inputs copied for you")[0])
P("- WHAT THE TAKE SCRIPT DOES comes from the plan and help text, code not read. Wherever this report says the take script archives contacts or the probe script tries a permanent delete, the basis is plan 4 (%s), the help text of the take script (%s) and two audit notes (%s, %s); the script code is not in the tree and was not read." % (quote("P4", "up to 3 HubSpot contacts archived at the end")[0], quote("EQ4", "--cleanup")[0], quote("CA", "scripts/hubspot_probe.py:4-5")[0], quote("CB", "hubspot_probe.py:271-287")[0]))
P("- A CONFLICT THAT IS NEW IN THIS REPORT: the studio lead's decisions file says the take never deletes contacts (%s) while plan 4 shows the owner a notice 'up to 3 HubSpot contacts archived at the end' (%s) and owner sheet v25 tells the owner that any notice line saying contacts will be deleted or archived is a difference and to stop (%s). If the plan 4 notice is shown as written, the owner is told to stop. That is a reason the gate in row %d stays closed; nothing unsafe happens while it is closed (the take is blocked and no contact is touched)." % (quote("DEC", "2. TAKE IDENTITY")[0], quote("P4", "up to 3 HubSpot contacts archived at the end")[0], quote("OS25", "Compare every number and name in the notice")[0], n("rs59")))
P("- NOT RUN: n8n, any flow, the harness, git history, the checks C-3, C-4, C-5, C-6, C-8, C-10b, C-10c (second part) and the second part of C-9 (section 7 gives, for each, the exact missing input). Static reading only.")
P("- What the check script proves (section 7, rows C-1, C-1b and C-4a; raw output evidence-c6l/verify-c6l-output.txt, to be given to every reviewer together with this report): every old text occurs exactly once on the stated line of the stated file; the %d edits can be applied in table order to copies of the files without a mismatch; every cited source line exists; the flow-file edits give the required values on the copies; the per-question counts of section 3 equal a recount from the table. It does NOT prove that a statement is true or that a new text is right." % nrows)
P("- The reviews of REPORT-c6k.md (review-c6k-design.md and review-c6k-naive.md) found it not safe to apply. This report fixes every item of both (section 8 gives finding, fix and check). It has NOT been reviewed again by two independent reviewers; I did not run the EGM steps (the studio lead runs them).")
P("- Where the files are: audited files are a read-only copy of branch origin/cloud/flows-audit; paths under handover/demo and handover/flows-audit are on that branch; paths under handover/core-hardening are on branch cloud/core-hardening (the branch this report sits on). Every path in this report is a path inside the repository.")
P("- Does the web page carry the number 60.1 to 61.9 s? Default: no. Only statement 20 of the page statements file carries it (rows %s), and row %d marks statement 20 'not for the web page'. The rows that used to copy the number into other page statements now point to statement 20 without the number (rows %s), so they are safe whatever the studio lead answers. The video carries no number (decision 1, %s)." % (ids(["pg149a", "pg154"]), n("pg148"), ids(["pg105", "pg120a", "pg120b", "pg139"]), quote("DEC", "1. SCOPE")[0]))
P("- THE 18 RUNS ARE 18 KEPT RUNS. The lane3 series at lease 45 s has 2 more runs that were voided: VOID-fl45k3b (case K3B, never reached a final state, 338.7 s, cause unknown; %s and %s) and VOID-fl45k6c (case K3, the stand-in services were not up; %s). Recount by my own script (evidence-c6l/void-check-output.txt): 18 kept runs (K1 5, K2 5, K3B 5, K3 3), kill to final 60.1 to 61.9 s (median 60.85), from n8n coming back up 52.8 to 54.9 s, restart 6.6 to 8.8 s. The time window of VOID-fl45k3b overlaps 5 kept runs by time (fl45k2d, fl45k2e, fl45k6a, fl45k3d, fl45k6b; %s), the window of VOID-fl45k6c overlaps 2 (fl45k2e, fl45k6a). REPORT-c6k.md's design review said 6 kept runs; my count from the file is 5 kept plus the other voided run. Every place of this report and of the edit table that writes '18 runs' now says kept and names the 2 voided runs." % (quote("RCO", "VOID-fl45k3b K3")[0], quote("RJL", '"label": "VOID-fl45k3b"')[0], quote("RJL", '"label": "VOID-fl45k6c"')[0], quote("RCO", "overlaps VOID-fl45k3b <-> fl45k2d")[0]))
P("- The two numbers 60.1 to 61.9 s and 52.8 to 54.9 s are different measurements of the same 18 kept runs (the 2 voided runs VOID-fl45k3b and VOID-fl45k6c are not counted): seconds from the crash to the final state of the contact record, and seconds from n8n coming back up. 45 s is a SETTING (the lease), not a measurement. 'Not measured on the flows of this take' means: no run on real-v5. 'Measured on stand-in flows' means: lane3 on film-v4. The decisions file calls the cut number 'unmeasured' (%s); that means the same thing as 'not measured on real-v5' (c6k design review m5, said once here)." % quote("DEC", "1. SCOPE")[0])
P("- K3B being false in 'killed after the mail left' does not make K3 false: K3 (killed after the mail was delivered) is described correctly by mf.py. Only the K3B sentence is wrong.")
P("- Slips of REPORT-c6k.md that this report corrects: it stated take-script behaviour as fact; it said the owner sheets and the QUEUE rule were not on disk; it assumed v19; it wrote 'each of 18 runs' without naming the 2 voided runs (VOID-fl45k3b, VOID-fl45k6c); its closing-card row waited for three answers at once and left the card half-changed when only one was answered; it copied the cut number into three page statements while the answer on publishing it was open; 'the lead' meant both the studio lead and a sales contact, and 'claim' meant four things.")
P("")
P("## 1. How to use this report")
P("- ONE ID: the first column of the edit table (section 5) is the only ID. Every other section uses these numbers. Old names and the row numbers of REPORT-c6k.md are mapped in section 5 (second table). Because row 13 of REPORT-c6k.md is split into two rows, every ID after it moves up by one.")
P("- WORDS: 'studio lead' = the person who decides for the studio (the person reading this report). 'owner' = the person who runs the take by typing; the owner sees the owner sheet. 'contact record' = one made-up sales contact the flows process (the files and the spoken video statement call it a 'lead'). 'statement' = a sentence said or shown in the video or on the web page. 'claim row' = a row of the database table that reserves a contact record for one run (the table is the 'claim table'). 'reserved' = held for the run that took it. The word 'claim' is used for nothing else.")
P("- APPLY ORDER, in two waves. Wave 1: every row that says 'ready' or 'on the default of ...' (the rows without a check), in table order. Wave 2: after wave 1 the studio lead runs the checks named in 'after check ...' and applies those rows only when the check has passed: C-4 needs the edited flow files imported (so wave 1 comes first) and C-8 needs the loopback re-smoke. Within one file the rows are sorted from the bottom of the file to the top, so applying them in order never shifts the line number of a row still to come. The column Line is the line number BEFORE any edit of that file. A builder who applies in another order must find each old text by text, not by line.")
P("- Old text and new text are exact file text. '<br>' in a cell means a line break in the file. Nothing else is abbreviated. Several rows on the same line (for example the closing card line) change different pieces of text on that line.")
P("- STATUS words: 'ready' = no open question and no open check. 'on the default of L-X' = apply it if the studio lead answers L-X with the default or writes 'apply all defaults' (section 3, table 3c); do not apply it if the studio lead answers differently. 'after check C-N' = do not apply until that check has passed (section 7). A row that is not ready is still written out in full, so the studio lead can say yes to its default.")
P("- THE CLOSING CARD ROWS ARE ONE SET: rows %s change the closing card and the lines that talk about it. They apply together (status L-CARD, L-LEASE) or not at all, so the card is never left half-changed (c6k design review M1)." % ids(["rs82", "rs80", "rs41a", "rs41b1", "rs41b2", "rs41c", "rs33d", "rs14", "rs5b"]))
P("- Short names of files used in the Sources column and in section 4 (path inside the repository; branch as in section 0):")
P("")
P("| Short | Path inside the repository | What it is |")
P("|---|---|---|")
for k in F:
    P("| %s | %s | %s |" % (k, F[k][1], F[k][3]))
P("")
P("A source written KEY:number means line number in the file of that short name. A source written DEC:3 (decision 2) means line 3 of the decisions file, which is decision 2: in that file decision N is on line N + 1.")
P("")
P("## 2. Numbers and names that look alike and are not the same")
P("")
P("| Number | What it is | Names (this report / lane3 / test program) | Source |")
P("|---|---|---|---|")
for a, b, c, d in [
    ("60.1 to 61.9 s", "seconds from the crash (the kill) to the final state of the contact record, 18 KEPT crash runs (2 voided runs, VOID-fl45k3b and VOID-fl45k6c, not counted), lease 45 s, film-v4 stand-in flows", "kill_to_final_s in lane3", "RES:89 to RES:92, RCO:2, RJL"),
    ("52.8 to 54.9 s", "the same 18 kept runs (2 voided runs, VOID-fl45k3b and VOID-fl45k6c, not counted), counted from n8n coming back up", "recovery_s in lane3", "RES:89 to RES:92, RCO"),
    ("45 s", "the lease SETTING of the take: how long a reserved contact record stays reserved before the recovery flow may take it again. Not a measurement", "lease", "RS:22"),
    ("20 s and 120 s", "lease settings of older tests: 20 s for the laptop series (V7), 120 s for one lane3 run (K1, 144.3 s)", "lease", "RS:19, RS:23"),
    ("80 kills", "the older laptop series K1, K2, K3, K3B, 20 runs each, flows v3, stand-ins, lease 20 s", "V7", "RS:41"),
    ("18", "KEPT crash runs of lane3 at lease 45 s: K1 5 done, K2 5 done, K3B 5 unknown, K3 3 unknown; plus 2 voided runs not counted", "lane3 names K1, K2, K3, K6", "RES:89 to RES:92, RJL"),
    ("13 minutes (780 s)", "relayed alert delay when n8n dies during the alert send, 2 runs, lane3 v4 flows (not the flows of the video)", "KS, v3KS, v4ks1", "RES:78, RES:79"),
    ("30 s", "how often the recovery flow runs (its timer)", "secondsInterval", "JR:%d" % find("JR", '"secondsInterval": 30')),
]:
    P("| %s | %s | %s | %s |" % (a, b, c, d))
P("")
P("Crash test names (the same four tests carry different names in different files; this table is the key; K3 and K3B are the ones that were mixed up):")
P("")
P("| Name on the run sheet and the page | What happens | lane3 name | Test program | Lane3 kept runs at lease 45 s (end state, mails at the test mailbox) |")
P("|---|---|---|---|---|")
P("| K1 | n8n killed after the claim row was written, before the CRM write | K1 | MF:%d | 5 runs, done, 1 mail |" % find("MF", "def k1"))
P("| K2 | n8n killed after the CRM write, before the mail step | K2 | MF:%d | 5 runs, done, 1 mail |" % find("MF", "def k2"))
P("| K3B | n8n killed while the mail connection was opening; the mail was NOT delivered | K3 | MF:%d | 5 runs, unknown with one alert, 0 mails |" % find("MF", "def k3b"))
P("| K3 | n8n killed after the mail was delivered, before the table update | K6 | MF:%d | 3 runs, unknown with one alert, 1 mail |" % find("MF", "def k3():"))
P("")
P("## 3. Questions (who answers, text, default used, confirmed?, what a different answer changes)")
P("The edit table uses the default of each question. Nobody has confirmed any of them. A different answer means the listed rows are not applied or are re-issued; the studio lead says so and a builder re-issues those rows. No row contains two choices. Old names: L-CARD was Q1, L-KILL was Q2, L-ROUND was Q9, L-SHEET was Q10 (of REPORT-c6h.md); the old Q11 is answered (see its row). Q3 to Q8 of REPORT-c6h.md (who runs the re-smoke, role tests, S1b, flow activation time, owner step 0, proof screenshot) touch no edit here and are not repeated; section 3 table 3d says who runs the re-smoke and the leak scan and when.")
P("")
P("Who answers: STUDIO LEAD ONLY = the studio lead decides and needs nobody else. OWNER ONLY = only the owner can answer, because it is a fact only the owner knows or a permission on the owner's own accounts. The decisions file says the owner may veto any decision (%s)." % quote("DEC", "# Lead decisions")[0])
P("")
P("| Question | Who answers | Text of the question | Default used | Confirmed? | If the answer is different | Rows tied to it |")
P("|---|---|---|---|---|---|---|")
P("| L-CARD (was Q1) | studio lead only | Does the closing card (scene 12, the last card of the video, run sheet line 41) stay as the last card? | Yes, it stays; its old lines 2 and 3 (the 80 kills and the recovery time) are cut and it gets four spoken lines. | No | If the card is cut: every card row (set of 9, section 1) is dropped; nothing else changes. | %s |" % nums(dep_list("L-CARD")))
P("| L-KILL (was Q2) | studio lead only | Scene 4 (the crash and the recovery): (a) leave the kill-case words out of scene 4, or (b) keep them, labelled as a stand-in test on film-v4 flows? | (a). REPORT-c6h.md gave (b) as default; (a) is used because decision 8 (%s) allows no extra test run with real accounts: the kill cases K3B and K3 were never run on the real-v5 flows (only on stand-ins), so no result for them can be shown as a result of this take; and the old K3B sentence is false as written. | No | If (b): row %d is re-issued and says, in place of the sentence about K3B and K3: 'Stand-in test, film-v4 flows: n8n killed while the mail connection was opening, the mail was not delivered: the contact record ends unknown with one alert to the owner. Stand-in test, film-v4 flows: n8n killed after the mail was delivered: the contact record ends unknown with one alert to the owner.' | %s |" % (quote("DEC", "8. Real-account smoke")[0], n("rs90"), nums(dep_list("L-KILL"))))
P("| L-ROUND (was Q9) | studio lead only | May scene 4 and the page use the rounded wording 'about a minute, in the test' in place of the cut number? | No. No timing number and no rounded timing wording anywhere in the video text; decision 1 (%s) already cuts the number. | No | If yes: the studio lead names the exact caption; rows that tie to it are re-issued with it. | %s |" % (quote("DEC", "1. SCOPE")[0], nums(dep_list("L-ROUND"))))
P("| L-SHEET (was Q10) | OWNER ONLY (the owner knows which sheet he reads; the studio lead may answer if the owner agrees that the newest sheet is the one) | Which owner sheet does the owner read? | The newest sheet on disk: v25 (variants A and B and a SOURCE file, steps-edits folder). REPORT-c6k.md assumed v19; that was wrong (section 0). Variant A or B is the studio lead's choice and is not decided in any file I read. | No | If another sheet: check C-10c is run on that sheet. No row touches an owner sheet. | none (check C-10c) |")
P("| Q11 (answered) | answered | Which statement wording is in force? | Answered by the studio lead at ORD:%d (ORDERS.md answer Q21.2): the statement 'a lead sent twice with the same id is processed once' plus one honest sentence on the lease. What is open is the exact sentence, see L-LEASE. | Yes for the choice; no for the sentence | not applicable | see L-LEASE |" % find("ORD", "Q21.2:"))
P("| L-LEASE | studio lead only | The studio lead said (ORD:%d) 'a gap longer than the lease is not claimed' (his word 'claimed' means: no statement is made). May the caption and the card say, in plain words: 'We say this only when the second send comes within 45 seconds of the first. The 45 seconds is a setting: for that long the system keeps a lead for the run that took it first.'? | Yes, that sentence (rows %s). | No | The studio lead gives the sentence; those rows are re-issued with it. | %s |" % (find("ORD", "Q21.2:"), ids(["rs32", "rs41b1"]), nums(dep_list("L-LEASE"))))
P("| L-DEL | studio lead only (the owner is told the answer, because it decides what the owner finds in his CRM account after the take) | The take script ARCHIVES the made-up contacts it created (moves them to the CRM recycle bin) and the probe script tries a permanent delete first (plan and help text, code not read), but decision 2 says the take never deletes contacts and owner sheet v25 tells the owner to stop at any notice line about deleting or archiving. Choose (a) change the program so that the take neither archives nor deletes (the owner removes leftover contacts by hand, as decision 2 says), or (b) change decision 2 and every owner sheet to say: the take archives only its own made-up contacts at the end and never permanently deletes. | NO DEFAULT. The gate (row %d) stays closed and the take is blocked until the studio lead chooses; nothing unsafe happens while it is closed. My recommendation: (a), because decision 2 is his written decision and v25 already says the owner deletes by hand; (b) is the smaller change if the archive step is wanted. | No | After the answer, new rows (the decisions file line 3, the owner sheet, and for (a) a program change) are issued by the next report. Needs the studio lead; no date is given in any file. | none (the gate row only records that the gate is closed) |" % n("rs59"))
P("| L-SAVE | studio lead only (the plan row says it is the owner's own decision of 2026-11-16; the studio lead confirms the row is still current) | Does the take really save every run (EXECUTIONS_DATA_SAVE_ON_SUCCESS=all and ON_ERROR=all), so that the execution list filmed in scenes 1 and 2 shows runs? | Yes (the plan's row says 'owner 2026-11-16'). Pass or fail check before any row depends on it: C-11 (static, DONE: the plan row says all for both) and C-4 (import check, NOT RUN). | No | If no: rows that tie to it are dropped and the execution list in scenes 1 and 2 stays empty (scene 1 text then needs a rewrite, which this report does not contain). The closing card and the two test-program rows do not depend on it any more. | %s |" % nums(dep_list("L-SAVE")))
P("| L-PAGE | studio lead only | May the web page of the one video carry the lane3 range 60.1 to 61.9 s (film-v4 stand-in flows, a labelled statement, never a caption) and statement 19 (the 13-minute alert delay, lane3 v4 flows)? | No. Statements 19 and 20 stay in the statements file, marked not for the web page. | No | If yes: the rows that mark them are dropped and the statements are published with their tags. The rows that point to statement 20 without a number need no change. | %s |" % nums(dep_list("L-PAGE")))
P("| L-ONEDB | studio lead only | Ratify or veto the interim sentence for any text written before the re-smoke has passed: 'n8n keeps its own records in its own database file. Our claim table is in a separate Postgres database. That is two stores.' (ORD:%d requires the caption 'one Postgres server, two databases' only once that is true.) | The target wording of decision 10 goes into DECISION-one-store.md as a target (rows %s); viewer-facing text uses only the interim sentence until check C-8 passes. | No | If vetoed: the interim sentence is not used and no viewer-facing text says anything about the number of databases until C-8 passes. | %s |" % (find("ORD", "Q21.3:"), ids(["one13", "one14", "one16"]), nums(dep_list("L-ONEDB"))))
P("| L-CUT | studio lead only | Scenes 5 to 11 (run sheet lines 34 to 40) are cut from the one video but their rows still hold stale text (K3 and K3B history, V7 numbers). Mark each row 'not in the one video'? | No edit now (they are not filmed). | No | If yes: a new row per scene is issued. | none |")
P("")
P("3b. Count of rows per question, made by the build script from the table and checked by evidence-c6l/verify-c6l.py (which recounts from the markdown table of section 5):")
P("")
P("| Question or check | Rows tied to it | How many | Of those: wait ONLY for this | Of those: also wait for something else |")
P("|---|---|---|---|---|")
alltoks = sorted(set(t for e in EDITS for t in toks(e)), key=lambda x: (x[0] != "L", x))
for t in alltoks:
    rows = [e for e in EDITS if t in toks(e)]
    only = [e["n"] for e in rows if toks(e) == [t]]
    also = [e["n"] for e in rows if toks(e) != [t]]
    P("| %s | %s | %d | %d (%s) | %d (%s) |" % (t, nums([e["n"] for e in rows]), len(rows), len(only), nums(only), len(also), nums(also)))
P("| (no question, no check) | %s | %d | ready | none |" % (nums(ready), RC))
P("| TOTAL | all rows | %d | ready %d, on defaults only %d, with a check %d | |" % (nrows, RC, RO, RW))
P("")
P("3c. 'APPLY ALL DEFAULTS' (the instruction the studio lead may give; its exact effect). If the studio lead writes the words apply all defaults in his answer file (ORDERS.md) or tells the builder, the builder applies wave 1 only: the %d ready rows (%s) and the %d rows that wait only for a question (%s), that is %d rows, to the files %s. The %d rows that wait for a check (%s) are NOT applied; they stay for wave 2. The instruction does NOT confirm any answer (the column Confirmed stays No), does NOT answer L-DEL (no default; the gate row only records that the gate is closed), does NOT answer L-SHEET (owner only), and does NOT run any check. What changes in content: the closing card gets four spoken lines and the lease sentence (L-CARD yes, L-LEASE yes); scene 4 has no kill-case words and no rounded timing wording (L-KILL a, L-ROUND no); the take saves every run, so the eight flow-file rows and the saving notes change (L-SAVE yes); statements 19 and 20 are marked not for the web page (L-PAGE no); DECISION-one-store.md gets the target wording marked as a target (L-ONEDB ratified); the wait for C-4 and C-8 leaves the scene 1 and scene 2 execution-list rows, the repeat-send caption row and the two n8n start-note rows about Postgres unapplied. A default can be reversed afterwards because every old text is in the table." % (RC, nums(ready), RO, nums(onlyq), RC + RO, ", ".join(F[k][1].split("/")[-1] for k in files), RW, nums(withc)))
P("")
P("3d. Who runs the long-standing steps and when (they touch no edit; they are named so that nobody has to guess). Loopback re-smoke (a short repeat test of the whole setup on this computer only, with fake services): run by the studio lead, before the first rehearsal (%s, decision 12: the first rehearsal is 'the lead, right after the loopback re-smoke passes'); checks C-4, C-8 and the table part of C-9 are read during it. Leak scan for the take (check C-6): a builder named by the studio lead writes it (the audit writes no code); the studio lead runs it on the loopback stand-ins before the first rehearsal and again after any change to a flow file or to a saving setting. Execution-list check (C-5): the studio lead, before scene 1 and before scene 2 of every rehearsal and of the take. Active-workflow check (C-3): the studio lead, before every rehearsal and before the take. No date or hour for any of these is written in any file I read; the studio lead sets them." % quote("DEC", "12. First laptop rehearsal")[0])
P("")
P("## 4. Plain-word glossary (every short name and label used in this report; term, meaning, where it comes from)")
P("")
P("| Term | Plain meaning | Where it comes from |")
P("|---|---|---|")
G = [
    ("studio lead", "the person who decides for the studio and reads this report. The owner is the person who runs the take by typing and reads the owner sheet; the studio lead prepares and supervises. The files call the studio lead 'the lead'.", "H6:53"),
    ("contact record, lead, lead id, lead key", "one made-up sales contact the flows process. The files and the spoken video statement call it a 'lead'; this report calls it a contact record so that it cannot be mixed up with the studio lead. 'Lead id' and 'lead key' are its identifier (the key is the letter L plus 16 hex characters).", "H6:53, RS:31"),
    ("statement", "a sentence said or shown in the video or on the web page. The word 'claim' is not used for this.", "section 1"),
    ("claim table, claim row, reserved", "the database table (mf_leads) holds one row per contact id; the flow writes the row first so that no second run takes the same contact record: that row is the claim row. The contact record is then 'reserved' for the run that took it, for as long as the lease lasts. The unique index is the database rule that refuses a second row with the same contact id.", "H6:53, ORD:151"),
    ("decision 1, 2, 8, 10, 12 (and line numbers DEC:2, DEC:3 ...)", "the studio lead's numbered decisions of 2026-11-16 in the decisions file. Decision N is on line N + 1 of that file: 1 = DEC:2 (the one video is real-v5 only, scenes 1 to 4, the number is cut); 2 = DEC:3 (the take never deletes contacts); 8 = DEC:9 (no extra test run with real accounts); 10 = DEC:11 (wording one Postgres server with two databases); 12 = DEC:13 (first rehearsal by the studio lead after the loopback re-smoke).", "DEC:2, DEC:3, DEC:9, DEC:11, DEC:13"),
    ("the take", "the one filmed run of the video.", "H6:86"),
    ("run sheet", "VIDEO-RUNSHEET.md, the scene-by-scene script. Scenes are its numbered rows 1 to 12.", "RS:28"),
    ("page, page statements, statement 14, 17, 18, 19, 20", "PAGE-STATEMENTS-V4.md, the text for the web page that goes with the video, numbered statements 1 to 20. 18: what n8n keeps (UNBACKED). 19: the 13-minute alert delay (relayed). 20: the lane3 crash runs at 45 s.", "H6:363"),
    ("closing card", "scene 12, the last on-screen card; its text is one table row, run sheet line 41.", "RS:41"),
    ("real-v5", "the n8n flow set in folder n8n-flows-real-v5 that talks to the real mail and CRM services; the only set in the one video. Four files: mf-form (form entry), mf-hook (hook entry), mf-recovery (the recovery flow, every 30 s), mf-sub-crm-mail (a shared step that writes the CRM and sends the mail, called by the entries).", "H6:87"),
    ("entry flows", "mf-form and mf-hook: the two flows that receive a contact record by a web address (webhook) on this computer only.", "NS:33"),
    ("recovery flow", "mf-recovery: it wakes every 30 seconds, looks at the claim table and finishes or alerts on contact records that were interrupted. Also called the recovery sweep.", "NS:33"),
    ("shared step, sub-flow", "mf-sub-crm-mail, a flow that other flows call (n8n calls this a sub-workflow).", "H6:87"),
    ("film-v4, film-v5", "flow sets that talk to stand-in services; their scenes (5 to 11) are a possible later video. film-v5 differs from real-v5 only in the files mf-recovery.json and mf-sub-crm-mail.json (check C-7).", "H6:88, EVDIR:15"),
    ("stand-in", "a fake service we control (fake CRM, fake mail server, fake model) used instead of the real one.", "H6:88"),
    ("loopback", "the address that points to this computer itself, so nothing outside can reach it.", "NS:33"),
    ("loopback re-smoke", "a short repeat test of the whole setup on this computer only, with fake services, run by the studio lead before the first rehearsal.", "DEC:9, DEC:13"),
    ("rehearsal", "a practice run of the take before the real take.", "DEC:13"),
    ("handoff", "the studio lead's session note (the handoff folder of the studio) where facts such as the list of active workflows are written down; not in this repository.", "RS:71"),
    ("lane3", "the separate test session and git branch (origin/demo/lane3) that ran the 45-second-lease crash tests; its results table is RES, its raw rows are RJL.", "H6:63"),
    ("HB171, HB180, HB186, HB189, HB194", "numbers of lane3 reports relayed to the demo session by the studio lead; the files do not say what HB stands for and none of the five report files is in the tree. HB189: alert may be late; HB194: the 18 kept crash runs at lease 45 s (2 voided runs, VOID-fl45k3b and VOID-fl45k6c, not counted); HB171: a key found in a database file once (relayed, n=1).", "NS:42, RS:82, PG:148"),
    ("lease", "how long a contact record stays reserved before the recovery flow may take it again. The take uses 45 s; older tests used 20 s and 120 s. A setting, not a measurement.", "H6:89"),
    ("VOID-fl45k3b, VOID-fl45k6c, fl45k...", "run labels in lane3 raw rows. fl45k1a is a kept run (case K1, first run); the two labels starting VOID are runs that were voided and are not counted.", "RJL, RCO"),
    ("alert", "the one mail the system sends to a named address when it cannot tell what happened to a contact record.", "H6:90"),
    ("test mailbox (the files say 'intake mailbox' and 'intake')", "the made-up mailbox that receives the contact mail; 'intake got 1 mail' in the files means one mail reached it.", "RS:30"),
    ("end state unknown", "final state of a contact record when the program cannot tell whether the CRM entry and the mail happened; a person decides.", "H6:91"),
    ("K1, K2, K3B, K3 (and lane3 K3, K6)", "crash tests; see the table of crash test names in section 2.", "MF:151 to MF:159"),
    ("T7b, leak scan", "a privacy test in mf.py (function t7b): plants a fake model key, a fake mail password, a name and an e-mail, runs contact records and searches stores for them. Today it forces execution saving off. 'Leak scan for the take' = the new version of this test for a take that saves every run.", "MF:274"),
    ("saving off, saving all", "the n8n settings EXECUTIONS_DATA_SAVE_ON_SUCCESS and _ON_ERROR: none = n8n keeps no run data; all = it keeps every run (what the execution list shows). The take uses all.", "PLAN:125"),
    ("execution list", "n8n's screen listing past runs; filmed in scenes 1 and 2.", "RS:4"),
    ("stage, stage journal, spend ledger", "the stage is the program step that asks the model to qualify a contact record; its journal records a model call before it is made (file stage-journal.jsonl); the spend ledger records the money spent (it exists; its path comes from the take's config and was not found in any file read).", "MF:12"),
    ("write-ahead file", "the database's log file (the -wal file) where recent writes sit before they reach the main file.", "NS:40"),
    ("table screen", "an n8n page that shows the claim table; BUILT, NOT RUN; decision 9 replaces it by a rehearsal screenshot.", "RS:50, DEC:10"),
    ("desk door", "one of two old entry flows (desk-form-door, desk-webhook-door) that send contact records to the older desk program; not in the one video. Finding F-022 is about its web error 502.", "FND:64"),
    ("bible, R460, QUEUE rule 6", "the bible is the studio's rule book (handover/bible/RULES.md). R460 is a rule number the audit order cites; its text is not in the bible folder (0 hits). QUEUE rule 6 is header rule 6 of the studio lead's queue file and is on disk (QUE:8): it lists the decisions in force.", "QUE:8, H6:390"),
    ("older review, c6i, c6j and c6k reviews; item names M1, m1, B1", "review-design.md (older review); review-c6i-design.md and -naive.md; review-c6j-design.md (RJD) and review-c6j-naive.md (RJN); review-c6k-design.md (RKD) and review-c6k-naive.md (RKN). In a review item name, M = major, m = minor, B = blocker, followed by the item number; 'design' reviews check facts and risk, 'naive' reviews check that a reader who has not seen the project can follow.", "RKD:1, RKN:1"),
    ("F-006, F-007, F-011, F-020, F-022, F-023, F-025", "numbered findings in FINDINGS.md: F-006 run sheet states a real CRM in scene 5; F-007 K3/K3B described three ways; F-011 'one database' / n8n keeps run history; F-020 stage journal owner; F-022 the stage returns a web error (502) on the desk door; F-023 table screen README conflict; F-025 old flows can double-mail.", "FND:91, FND:92, FND:97, FND:114, FND:116, FND:99, FND:118"),
    ("c6b to c6l", "successive versions of this audit report; c6l (this file) supersedes c6k; c6h is the last full report (REPORT-c6h.md).", "H6:1"),
    ("UNBACKED, RELAYED-INDEPENDENT, MEASURED-ON-LAPTOP", "tags on numbers: no raw file / relayed from another session without the raw file / read by the studio lead from laptop result files.", "RS:18, RS:19"),
    ("V7", "laptop result files and the studio lead's read of them (V7-NUMBERS-lead-read.md) behind the '80 kills' numbers, measured on older v3 flows with a 20 s lease on stand-ins.", "H6:387"),
    ("T13, T15, B90, AF1, KS", "earlier test names in the run sheet and page history lines (T13 same-id and database kill, T15 CRM refuses, B90 alert-send case, AF1 alert refused twice, KS the alert-send kill case); not used by any edit here.", "RS:32"),
    ("ORDERS.md answer Q21.2, Q21.3", "numbered answers inside ORDERS.md (the studio lead's file): Q21.2 is the statement wording and the lease sentence, Q21.3 the caption for the number of databases. They are not the questions L-... of this report.", "ORD:151, ORD:152"),
    ("L-CARD, L-KILL, L-ROUND, L-SHEET, L-LEASE, L-DEL, L-SAVE, L-PAGE, L-ONEDB, L-CUT", "the open questions of section 3 (L = question for the studio lead or the owner).", "section 3"),
    ("C-1 to C-11 (C-1b, C-4a, C-10a to C-10d)", "the checks of section 7 (C = check).", "section 7"),
    ("ready, on the default of, after check", "the three kinds of status of an edit row; see section 1.", "section 1"),
    ("wave 1, wave 2", "wave 1 = rows without a check, wave 2 = rows after a check; see section 1.", "section 1"),
]
for t, m, s in G:
    P("| %s | %s | %s |" % (t, m, s))
P("")

# ---------------------------------------------------------------- edit table
OLDK = json.load(open(C6 + "/evidence-c6k/edits.json"))
SPLIT = {"rs41b": ["rs41b1", "rs41b2"]}
was = {}
for o in OLDK:
    for nk in SPLIT.get(o["key"], [o["key"]]):
        was.setdefault(nk, []).append("row %d" % o["n"])
P("## 5. EDIT TABLE (every row: NOT APPLIED)")
P("Rows are in apply order (section 1). Paths are paths inside the repository (section 0). Column 'Was (c6k)' gives the row number the same edit had in REPORT-c6k.md ('new' = no such row there). Sources use the short names of section 1.")
P("")
P("| ID | Status | Target file (path inside the repository) | Line before any edit | Old text (exact) | New text (exact) | Reason and source file:line | Was (c6k) |")
P("|---|---|---|---|---|---|---|---|")
for e in EDITS:
    P("| %d | %s | %s | %d | `%s` | `%s` | %s Sources: %s | %s |" % (e["n"], status(e), F[e["fk"]][1], e["line"], cell(e["old"]), cell(e["new"]), e["why"], e["src"], "; ".join(was.get(e["key"], ["new"]))))
P("")
P("Row numbers of REPORT-c6k.md mapped to the IDs of this report (every other section uses only the IDs of this report):")
P("")
P("| c6k row (name there) | ID(s) now |")
P("|---|---|")
for o in OLDK:
    P("| %d (%s) | %s |" % (o["n"], o["key"], ids(SPLIT.get(o["key"], [o["key"]]))))
P("")

# ---------------------------------------------------------------- contact gate
P("## 6. The contact gate in detail (archive or permanent delete; every cite below was opened; plan and help text, code not read)")
P("Words: ARCHIVE = HubSpot moves the contact to its recycle bin (it can be restored). PERMANENT DELETE = the contact is erased. The studio lead's decision 2 (%s) says 'the take never deletes contacts; leftover made-up contacts are listed by lead key and contact id and the owner deletes them by hand in HubSpot after the take'. Everything below about what the take script and the probe script do rests on plan text, help text and audit notes; the code of both scripts is not in the tree." % quote("DEC", "2. TAKE IDENTITY")[0])
P("")
P("| What the files say | Cite (opened) | Text at the cite |")
P("|---|---|---|")
for lab, k, a in [
    ("The take script has an option that archives the contacts the run made (help text)", "EQ4", "--cleanup"),
    ("Plan 4: up to 3 contacts archived at the end", "P4", "up to 3 HubSpot contacts archived at the end"),
    ("Plan 4: the person types end and the script archives", "P4", "Film the contact list now"),
    ("Plan 4: archives also when the take ends in an error; leftovers are listed and the owner deletes them in the HubSpot screen", "P4", "1. the script archives this take's contacts"),
    ("The probe script: the code TRIES (docstring said 'always deletes') (audit note)", "CA", "scripts/hubspot_probe.py:4-5"),
    ("The probe script tries a permanent delete first, then an archive delete; if both fail it warns (audit note)", "CB", "hubspot_probe.py:271-287"),
    ("Whether an archived contact keeps its e-mail address reserved is an ASSUMPTION, never checked", "SH", "ASSUMED to keep its email reserved"),
    ("Owner sheet v25 (variant A): a notice line saying contacts will be deleted or archived is a difference; stop", "OS25", "Compare every number and name in the notice"),
    ("Owner sheet v25 (variant A): the owner deletes made-up contacts by hand, one by one", "OS25", "You delete only made-up contacts of this run"),
]:
    c, t = quote(k, a)
    P("| %s | %s | %s |" % (lab, c, t))
P("")
P("Checked by reading the four real-v5 flow files (command and output: evidence-c6l/contact-grep-output.txt, copied from the c6k run): they contain no DELETE call and no archive call (0 hits). So the only places that touch contacts are the take script and the probe script, and those files are not in the tree.")
P("")
P("The gate (run sheet row %d, item 11) therefore says: the program ARCHIVES (take script, plan and help text), the probe script may permanently delete, the studio lead decides (a) or (b) of L-DEL and writes a gate record of four yes-or-no lines; no sheet says never deletes until then; an unanswered L-DEL means the take is blocked and nothing is touched. The closing check is C-10 (section 7), four parts; part a is done, part b cannot be run (scripts absent), parts c and d wait for L-DEL." % n("rs59"))
P("")

# ---------------------------------------------------------------- ratings, checks
P("## 7. Ratings and checks (not edits)")
P("")
P("| Item | Rating | Basis |")
P("|---|---|---|")
P("| F-006 | Major (the finding said Blocker) | closed by decision 1 once rows %s are applied; RDES:%d |" % (ids(["rs4", "rs90"]), find("RDES", "F-006 Major accepted")))
P("| F-007 | Major | three sources disagree; fixed by rows %s; MF:%d |" % (ids(["rs24", "rs36", "pg150", "pg153", "rs90"]), find("MF", "def k3b")))
P("| F-011 | Major | rows %s plus checks C-8 and C-6 |" % ids(["one13", "one14", "one16", "ns4a", "ns4b"]))
P("| F-020, F-022, F-023, F-025 | Nit | accepted by the older review; F-022: real-v5 mf-form.json sets n8n_error false at lines 238, 254, 293 so the bug does not recur in the take flows |")
P("| N1 (stale flow folders share webhook paths) | Major, operational | row %d and check C-3 |" % n("rs71"))
P("| N2 (execution list empty because flows save nothing) | Major for filming, gate | rows %s, checks C-4 and C-4a |" % ids(["jJFSuccess", "jJFError", "jJHSuccess", "jJHError", "jJRSuccess", "jJRError", "jJSSuccess", "jJSError", "rs30a"]))
P("| N5 (closing card says 80 kills) | Nit | rows %s |" % ids(["rs41a", "rs41b1", "rs41b2", "rs41c"]))
P("")
P("Every check has an owner, a pass line, a fail line and a status. NOT RUN names the exact missing input. Labels for what blocks a check: impossible-now (cannot be done in this session), needs-lead, needs-owner, needs-third-party.")
P("")
P("| Check | What | Who runs it | PASS when | FAIL when | Status and missing input |")
P("|---|---|---|---|---|---|")
P("| C-1 | Every old text of section 5 occurs once on its line (the same copy method as REPORT-c6k.md) | the build and check scripts (done by me) | every row: exactly one match on the stated line | any row with 0 or 2 matches | DONE; result is in evidence-c6l/verify-c6l-output.txt |")
P("| C-1b | All rows applied in table order to COPIES of the files; no mismatch; no internal label, stale phrase, banned string, secret or e-mail address in a new text | the check script (done by me) | 0 mismatches and 0 hits | any mismatch or hit | DONE; same file |")
P("| C-2 | The 8 flow files (4 real-v5, 4 film-v5) all carry none, none, false and no errorWorkflow | me, file read | the evidence lists the same four values for all 8 | any other value | DONE (static): EVSET:%d to EVSET:%d |" % (find("EVSET", "n8n-flows-real-v5/mf-form.json"), find("EVSET", "n8n-flows-film-v5/mf-recovery.json") if any("n8n-flows-film-v5/mf-recovery.json" in l for l in lines("EVSET")) else find("EVSET", "n8n-flows-real-v5/mf-sub-crm-mail.json")))
P("| C-3 | Only real-v5 flows are active before each rehearsal and before the take (list the active workflows in n8n) | studio lead | the list holds only workflows imported from n8n-flows-real-v5 | any workflow from another folder, or a workflow with the path mf-form or mf-hook from another folder | NOT RUN; missing input: a running n8n on the take computer (impossible-now here; needs-lead) |")
P("| C-4 | Import check: the four edited real-v5 files are imported and one made-up contact record is sent | studio lead | within 60 s the execution list shows at least one run of an entry flow and at least one run of the recovery flow | the list stays empty, or shows only runs from before the clean-up | NOT RUN; missing input: running n8n and the rows %s applied (impossible-now here; needs-lead) |" % ids(["jJFSuccess", "jJFError", "jJHSuccess", "jJHError", "jJRSuccess", "jJRError", "jJSSuccess", "jJSError"]))
P("| C-4a | After the eight flow-file rows are applied to copies, each flow file holds saveDataSuccessExecution all and saveDataErrorExecution all and saveManualExecutions false, once each | the check script (done by me) | counts 1, 1, 1 in each of the 4 files | any other count | DONE on copies; result in evidence-c6l/verify-c6l-output.txt |")
P("| C-5 | Execution list before scene 1 and again before scene 2: no row older than the take start time written on the run sheet, no row with rehearsal data (recovery-flow rows are expected; a screen check, not an erasure) | studio lead | every row shows a start time later than the take start time and no rehearsal data | any older row, or any rehearsal data | NOT RUN; missing input: running n8n and the take start time (impossible-now here; needs-lead) |")
P("| C-6 | Leak scan for the take (N8N-START.md section added by row %d): case 1, case 2, and the name and e-mail rule, on six stores, loopback stand-ins only | a builder named by the studio lead writes it; the studio lead runs it | the pass lines of the section (case 1: 0 hits for both fake secrets in all six stores; case 2: key hits only in n8n's database; name and e-mail: 0 hits in journal, ledger and logs) | any hit outside what the section allows | NOT RUN; missing inputs: the scan itself (not written; the audit writes no code), a running n8n with stand-ins, and the path of the spend ledger from the take's config (needs-lead) |" % n("ns48"))
P("| C-7 | real-v5 and film-v5 differ only in mf-recovery.json and mf-sub-crm-mail.json | me, file read | the file list diff names only those two files (V5-NODE-DIFF.txt exists only in real-v5 and is not a flow file) | any other file or flow differs | DONE (static) PASS: evidence-c6l/static-checks-output.txt, section C-7; whether the import reads only the .json files: NOT RUN, needs a running n8n import (needs-lead) |")
P("| C-8 | The loopback re-smoke shows that n8n's engine is Postgres, before any text says one Postgres server with two databases (decision 10) | studio lead | the setting that names n8n's database type reads Postgres and n8n's data sits on the take's Postgres server | it reads SQLite | NOT RUN; missing input: the loopback re-smoke with a running n8n and Postgres (impossible-now here; needs-lead) |")
P("| C-9 | The repeat-send statement is backed by a unique rule on the claim table (gate, run sheet item 12) | part 1 me (static); part 2 studio lead | part 1: a primary key or unique index on the contact id in the test program and an ON CONFLICT insert in the entry flows; part 2: the same rule seen in the take's own table | part 2: no such rule seen; then the studio lead writes 'index not seen, accepted' on the sheet (ORD:%d) or the statement is not filmed | part 1 DONE (static) PASS: MF:%d and %s, ON CONFLICT in mf-form.json and mf-hook.json (evidence-c6l/static-checks-output.txt); part 2 NOT RUN; missing input: the take's database after the re-smoke (needs-lead) |" % (find("ORD", "Q21.2:"), find("MF", "CREATE TABLE mf_leads"), quote("MF", "CREATE TABLE mf_leads")[0] if False else "MF:%d" % find("MF", "CREATE TABLE mf_leads")))
P("| C-10a | Real-v5 flows contain no delete or archive call: grep -il -E 'DELETE|archive' on the four files | me, file read | 0 hits (grep exit code 1) | any hit | DONE PASS: 0 hits (evidence-c6l/contact-grep-output.txt) |")
P("| C-10b | Take script and probe script: grep -n -E 'archive_all|archive|delete' scripts/run_real_check.py scripts/run_real_check_n8n.py scripts/hubspot_probe.py | studio lead (reads the code) | (a): no archive or delete call in the take script; (b): archive of own contacts only, no permanent delete | any other call | NOT RUN; missing input: the three script files are not in the tree (needs-lead to supply them) |")
P("| C-10c | The owner sheet the owner reads: grep -n -i -E 'never deletes|read, create and change only|does not delete' sheet | me for the sheets on disk; studio lead for the final sheet | 0 hits, and (second part, after L-DEL) the sheet contains once the sentence the studio lead recorded in the gate record | any hit, or the sentence is missing | part 1 DONE on the sheets on disk: v19 1 hit (FAIL for v19), v20 to v25 0 hits (PASS; evidence-c6l/static-checks-output.txt); second part NOT RUN; missing inputs: the answer to L-DEL and to L-SHEET (needs-lead, needs-owner) |")
P("| C-10d | The decisions file: the same grep on DECISIONS-2026-11-16.md | studio lead (it is his file; no row edits it) | 0 hits and decision 2 states the chosen option | any hit | KNOWN FAIL today: line 3 matches (it says never deletes); stays failing until the studio lead writes his answer to L-DEL (needs-lead) |")
P("| C-11 | L-SAVE check: the re-smoke plan says all for both saving settings (static) | me, file read | the plan row holds EXECUTIONS_DATA_SAVE_ON_SUCCESS=all and EXECUTIONS_DATA_SAVE_ON_ERROR=all | either value is not all | DONE (static) PASS: %s (evidence-c6l/static-checks-output.txt); the runtime proof is C-4 (NOT RUN) |" % quote("PLAN", "| executions (take) |")[0])
P("")

# ---------------------------------------------------------------- coverage
P("## 8. Coverage: finding -> fix -> check (every item of the c6k design review and the c6k naive review)")
P("")
P("| Review item | Fix (row IDs and sections) | Check |")
P("|---|---|---|")
COV = [
    ("RKD M1: closing card rows wait for different answers; half-changed card", "rows %s (card set; row 13 split into %s)" % (ids(["rs82", "rs80", "rs41a", "rs41b1", "rs41b2", "rs41c", "rs33d", "rs14", "rs5b"]), ids(["rs41b1", "rs41b2"])), "section 1 card set; table 3b; retention line true for either L-SAVE answer"),
    ("RKD M2: rows copy 60.1 to 61.9 s into page statements while L-PAGE defaults no", "rows %s now point to statement 20 without the number; rows %s carry it and apply together with row %d" % (ids(["pg105", "pg120a", "pg120b", "pg139"]), ids(["pg149a", "pg154"]), n("pg148")), "verify: banned-figure scan of the new text of rows %s" % ids(["pg105", "pg120a", "pg120b", "pg139"])),
    ("RKD M3: 'each of 18' without the 2 voided runs", "rows %s name VOID-fl45k3b and VOID-fl45k6c; sections 0, 2" % ids(["rs90", "pg23", "pg149a"]), "evidence-c6l/void-check-output.txt; verify: every '18' next to 'run' names both voided runs"),
    ("RKD M4: row 6 items 11, 13, 14 wait for L-SAVE; rows speaking about saved runs", "row %d ready (items renumbered 11, 12, 13); the execution-list item moved into row %d; rows %s wait for C-4" % (n("rs71"), n("rs30a"), ids(["rs30a", "rs30b", "rs32"])), "table 3b; C-4"),
    ("RKD M5: row 8 states take-script behaviour as fact", "row %d: 'according to plan 4 and the help text; code not read'; conflict with the decisions file stated; unanswered L-DEL = take blocked, nothing unsafe; section 6" % n("rs59"), "section 0; C-10b"),
    ("RKD m1: 'no timing number on screen' vs live stopwatch", "row %d (and %d): 'no timing number in any caption, text card or voice; a live stopwatch overlay is shown'" % (n("rs90"), n("rs33a")), "stale phrase scan"),
    ("RKD m2: 'name and address'; 'stay in n8n's saved runs'", "row %d: 'name and e-mail address'; 'may stay in n8n's database'" % n("rs41b2"), "reading of the new text"),
    ("RKD m3: row 22 states hide-only deletion as fact", "row %d: 'whether it erases them is not verified'" % n("rs30a"), "reading"),
    ("RKD m4: rows 59 and 60 wait for L-SAVE but are true either way", "rows %s are ready and worded for either answer" % ids(["mf320", "mf276"]), "table 3b"),
    ("RKD m5: 'unmeasured' vs 'measured on stand-in flows'", "said once in section 0", "reading"),
    ("RKD m6: row 11 durations not checked against the run sheet", "row %d lists 25 + 40 + 25 + 60 + 30 per scene; checked against the Time column of run sheet rows 1, 2, 3, 4, 12" % n("rs44"), "script check in evidence-c6l/static-checks-output.txt not needed: read by me, 180 s"),
    ("RKN B1: L-SAVE default rests on one plan line; row 51 states n8n precedence as fact", "check C-11 (static, done) and C-4; row %d no longer states the precedence as fact and is right under either" % n("ns27"), "C-11, C-4"),
    ("RKN B2: 'ready' count vs table; counts per question", "section 0 and table 3b made by script; verify recounts from the markdown table", "verify-c6l.py: recount equals table 3b"),
    ("RKN B3: gate item 11 has no pass or fail test and no record", "row %d: gate record of four yes-or-no lines written by the studio lead" % n("rs59"), "C-10b, C-10c, C-10d"),
    ("RKN M: row 6 guess about the shared-step flow; '0 hits' needs the sheet; 'write down the seconds' without target", "row %d: shared step allowed if it is a real-v5 file; closing check run by the studio lead once the sheet is named (L-SHEET); repeat gap under 45 s with a pass test" % n("rs71"), "C-3, C-10c"),
    ("RKN M: row 22 no start time; who deletes", "row %d: the studio lead deletes and writes the take start time" % n("rs30a"), "C-5"),
    ("RKN M: row 13 spoken text (jargon; 'claimed'; Slack; pruning)", "rows %s plain words; the word claim is not used in video text" % ids(["rs41b1", "rs41b2"]), "reading; scan for the word claim in new texts"),
    ("RKN M: L-DEL no default; C-10c and C-10d only pass by an unscheduled decision", "table of section 3 (who answers, 'needs the studio lead; no date in any file'); section 7 labels", "C-10c, C-10d"),
    ("RKN M: 'lead' has two meanings; 'claim' has four", "section 1 words and glossary: studio lead, contact record, statement, claim row, reserved; verify scans prose", "verify word scan"),
    ("RKN M: decision N labels vs DEC:2 / DEC:3", "src() prints DEC:3 (decision 2); glossary row with the mapping", "section 1 sentence"),
    ("RKN M: who runs the loopback re-smoke and leak scan, when", "table 3d", "reading"),
    ("RKN M: short names confuse (EV vs EV1, DD, DN, Q21.2 vs ORDERS)", "EVSET, EVDIR, RJD, RJN, RKD, RKN; questions renamed L-...; glossary row for ORDERS.md answers", "verify: every short name appears in section 1 and every label in section 4"),
    ("RKN minor: planning-only 60.1 to 61.9 s needs 'not to be said'", "row %d" % n("rs33b"), "reading"),
    ("RKN minor: row 36 'intake'", "row %d: 'the test mailbox received'" % n("pg153"), "reading"),
    ("RKN minor: flow-file rows repeat the same reason; need a grep pass check", "check C-4a on copies", "C-4a"),
    ("RKN minor: row 37 four case names need a table", "table of crash test names in section 2", "reading"),
    ("RKN minor: row 8 item 12 'index not seen' who writes", "row %d: the studio lead writes it, with date and time (UTC)" % n("rs59"), "C-9"),
    ("RKN minor: row 4 depends on Q1 and row 13", "row %d is in the card set" % n("rs80"), "table 3b"),
    ("RKN minor: row 42 may withdraw statement 19 from the web page", "row %d says so and L-PAGE now covers statement 19" % n("pg134"), "table 3b"),
    ("RKN minor: row 59 long printed line", "row %d shortened" % n("mf320"), "reading"),
    ("RKN minor: section 2 name mapping needs a column", "section 2 has the column and the crash test table", "reading"),
    ("RKN minor: Q2 link from decision 8 to dropping kill cases", "the L-KILL row explains it", "reading"),
    ("RKN minor: undefined 'desk door', 'handoff', 'HB', 'bible', 'R460'", "glossary", "verify glossary scan"),
    ("RKN: defaults all unconfirmed; no 'apply all defaults'; lead-only vs owner-only; Q10 an owner question", "section 3 (who answers), table 3c; L-SHEET owner only", "table 3b"),
    ("RKN: row 40 'waits for L-PAGE' although the default applies", "status words 'on the default of' (section 1)", "table 3b"),
    ("RKN: checks without a clear pass or fail (C-3 to C-10c); C-1 evidence not given to the reviewer", "section 7 table: owner, pass, fail, status for every check; evidence files named in section 0", "section 7"),
]
for a, b, c in COV:
    P("| %s | %s | %s |" % (a, b, c))
P("")
P("## 9. Not covered here (each with the label and the exact next step)")
P("- [needs-lead] L-DEL has no answer. Next step: the studio lead answers (a) or (b); then a builder issues the rows for the decisions file (line 3), the owner sheet he names, and for (a) the take script; then C-10b, C-10c and C-10d are run and the gate record of row %d is written." % n("rs59"))
P("- [needs-owner or needs-lead] L-SHEET: which owner sheet, and variant A or B of v25, is read by the owner. Next step: the owner or the studio lead names it; C-10c is run on it. Also the older sheets v10 to v12 still contain the phrases (v10 2 hits, v11 1, v12 1); they are not used if the owner reads v25.")
P("- [impossible-now] n8n, Postgres and the harness are not available in this session: checks C-3, C-4, C-5, C-6, C-8 and the second part of C-9 cannot run here. Next step: the studio lead runs them on the take computer in the loopback re-smoke (section 3 table 3d).")
P("- [needs-lead] The three take and probe scripts, the five lane3 reports (HB171, HB180, HB186, HB189, HB194) and the text of rule R460 are not in the tree. Next step: the studio lead adds them to a branch the next audit can read; until then every statement about them stays 'plan and help text, code not read' or 'relayed'.")
P("- [needs-lead] The decisions file line 3 (decision 2) still says the take never deletes; it is the studio lead's own file and no row edits it (check C-10d).")
P("- [needs-lead] Scenes 5 to 11 rows (run sheet lines 34 to 40): question L-CUT.")
P("- [needs-lead] plan-wp6-resmoke-v5.md still names film-v5 at the lines listed in REPORT-c6h.md section 4; not repeated here; the plan is an input and is not edited.")
P("- [needs-lead] The stage's spend ledger path was not found in any file read; the leak scan needs it (row %d). Next step: the builder takes it from the take's config." % n("ns48"))
P("- [needs-lead] Run sheet lines 30 and 52 still say 'the request body stays in n8n data until pruned'; that stays true with saving all (the node data is kept too), so they are left.")
P("- [impossible-now] Whether deleting an execution in the n8n screen only hides it: not verified (N8N-START.md lines 42 and 47 say hiding then pruning; the plan says deletion is removal of the container). Check C-5 is a screen check and says so.")
P("- [needs-lead] The old reviews and this report were read by me alone: the EGM steps (review of the result by the egm reviewers, resolve, drift report) are run by the studio lead; I did not start any sub-agent.")
open(C6 + "/REPORT-c6l.md", "w", encoding="utf-8").write("\n".join(OUT) + "\n")
print("report lines", len(OUT), "rows", nrows, "ready", RC, "defaults-only", RO, "with-check", RW)
