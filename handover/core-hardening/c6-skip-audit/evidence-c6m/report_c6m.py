"""Second half of build_c6l.py: writes REPORT-c6m.md. Executed with the edit list already built (EDITS, NUM, F, find, cite)."""
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
P("# REPORT-c6m: video audit fix pass, supersedes REPORT-c6l.md (2026-11-16, UTC; IST = UTC + 5:30)")
P("")
P("## Start here: what I need from you (read this box first; everything after it is detail)")
P("Nothing in this report has been applied to any file. The edit table (section 5) holds %d proposed text changes, each with its old text, its new text and what a viewer of the video sees (%d are 'ready', %d wait for an answer, %d wait for a check that needs n8n). You answer by writing ONE line in ORDERS.md (the paragraph just below the box). The box has one line for every question label (L-) and one line for all check labels (C-). Words used here are explained in the list after the box." % (nrows, RC, RO, RW))
P("")
P("| Label | Plain meaning (one sentence) | Default if you say 'apply all defaults' | Who answers |")
P("|---|---|---|---|")
BOX = [
    ("L-CARD", "Does the closing card (the last card of the video, scene 12) stay as the last card?", "Yes, it stays.", "studio lead"),
    ("L-CARDCUT", "Cut the old card lines about the 80 kills and the recovery time (they come from older flows and an estimate that does not match the data)?", "Yes, cut.", "studio lead"),
    ("L-CARDTEXT", "Use the new spoken card lines 2 to 4: no statement about alert delay, one sentence on what n8n keeps, one sentence on what was not tested?", "Yes.", "studio lead"),
    ("L-LEASE", "Say on the card and in the scene 3 caption that 'sent twice, processed once' holds only when the second send comes within 45 seconds?", "Yes (your answers Q21.2 and Q22 require such a sentence; only its exact wording is open).", "studio lead"),
    ("L-KILL", "Say anything about the two crash tests K3B and K3 in scene 4?", "No.", "studio lead"),
    ("L-APPROX", "May scene 4 and the web page say 'about a minute' in place of the cut number?", "No.", "studio lead"),
    ("L-SAVE", "Does the take save every run in n8n, so that the execution list filmed in scenes 1 and 2 shows runs?", "Yes (the re-smoke plan says 'owner 2026-11-16').", "studio lead"),
    ("L-PAGE", "May the web page carry the 60.1 to 61.9 s range of the stand-in crash runs and the 13-minute alert delay?", "No; both stay in the file, marked not for the page.", "studio lead"),
    ("L-ONEDB", "Ratify the interim sentence 'two stores' for any text written before the re-smoke has shown that n8n runs on Postgres?", "Yes.", "studio lead"),
    ("L-SHEET", "Which owner sheet does the owner read?", "v25 variant A (v26-SOURCE is a newer template, see section 3).", "OWNER ONLY (the studio lead asks him)"),
    ("L-DEL", "Does the take delete contacts? ANSWERED by you in ORDERS.md (Q23, Q19 item 1, Q27): no, never. The part still open is your own check of the take script at the final version (UNVERIFIED until you write it on the run sheet).", "As answered; no reply needed now.", "studio lead (his check at the re-pin)"),
    ("L-CUT", "Mark the run sheet rows of scenes 5 to 11 (not filmed) as 'not in the one video'?", "No edit.", "studio lead"),
    ("C-1 to C-11", "Checks (section 7). Done here with raw output: C-1, C-1b, C-2, C-4a, C-7, C-9 part 1, C-10a, C-10c on the sheets on disk, C-10d, C-11. Not run, they need n8n or files that are not in the audited tree: C-3, C-4, C-5, C-6, C-8, C-9 part 2, C-10b.", "None of them is needed for 'apply all defaults'; the rows that wait for C-4 or C-8 stay unapplied.", "studio lead runs them"),
]
for a, b, c, d in BOX:
    P("| %s | %s | %s | %s |" % (a, b, c, d))
P("")
P("To answer, append this one line to handover/core-hardening/ORDERS.md (the file where you already write your answers): ANSWER c6m (time in UTC): apply all defaults to REPORT-c6m.md; builder: <name>; reviewers: <two names>. To change one default write the same line with 'except L-X: <your answer>' for each differing label. Exact limits of 'apply all defaults':")
P("- It makes the named builder apply wave 1 only: %d rows (the %d ready rows and the %d rows that wait only for a question; section 3c lists them) to the 9 files named in section 3c. The builder applies the table by text, in table order, and writes the list of applied row numbers to a file next to this report." % (RC + RO, RC, RO))
P("- It does NOT apply the %d rows that wait for a check (%s); it does not run any check; it does not import anything into n8n; it spends nothing." % (RW, nums(withc)))
P("- It does NOT confirm any answer: the column 'Confirmed?' in section 3 stays as it is. It does not answer L-SHEET (only the owner can).")
P("- Those %d new texts are NOT yet reviewed. After applying them the two named reviewers (one fact and risk reviewer, one reader who has not seen the project) must read the CHANGED files, not this report. The new texts include a new spoken statement (the 45-second sentence on the closing card) and new blocking checks on the run sheet. The rows that switch on saved runs are included, so n8n will save every run once the files are imported; the take stays blocked by item 14 of the rehearsal list on the run sheet until C-4 and C-6 have passed." % (RC + RO))
P("- A default is reversed by the studio lead naming a builder who puts back the old text of the affected rows (every old text is in the table).")
P("")
P("WORDS (one meaning each; used the same way in the whole report):")
P("- STUDIO LEAD = the one who decides for the studio, writes the answers in ORDERS.md and reads this report. OWNER = the person who runs the take by typing; he reads the owner sheet; he is reached through the studio lead (the studio lead asks him once at take prep; a builder never contacts him). The files call the studio lead 'the lead'; this report never does.")
P("- TAKE = the one filmed run of the video (never a rehearsal). TAKE SCRIPT = the program that runs it (scripts/run_real_check_n8n.py). REHEARSAL = a practice run before the take. LOOPBACK RE-SMOKE = a short test of the whole setup on this computer only, with fake services.")
P("- RUN SHEET = VIDEO-RUNSHEET.md (the scene-by-scene script). OWNER SHEET = the checklist the owner reads (steps-edits folder). The report never writes 'the sheet' alone. LINE N = line number N of a file; the four spoken lines of the closing card are called 'card line 1' to 'card line 4'; a line of a notice shown to the owner is called a 'notice line'.")
P("- CONTACT RECORD = one made-up sales contact the flows process (the files call it a 'lead'). STATEMENT = a sentence said or shown in the video or on the web page.")
P("- KEPT RUN = a crash run counted in the figures; VOIDED RUN = a run that the lane3 session marked VOID in its raw file and that is not counted (two exist; section 2 says why each was voided, as far as the file says). N = number of runs, so 'n=2' means 2 runs.")
P("- DELETE = erase for good. ARCHIVE = move a contact to HubSpot's recycle bin (it can be restored). CLEARING the execution list = hiding rows on the screen; whether n8n erases them from its database is not verified.")
P("- TIMING NUMBER = a figure given as a result of a test (60.1 to 61.9 s, 13 minutes, 80 kills) in a caption, card or voice. A setting label ('setting: lease 45 s') and the live stopwatch overlay (the clock of the run being filmed, including a 'sped up, real wait' label) are not timing numbers; no row changes them.")
P("- REVIEW ROUND = one pass of independent reviewers over a report. (The old question name L-ROUND meant 'rounded wording'; it is renamed L-APPROX so that it cannot be mixed up with a review round.)")
P("- N8N = the workflow tool that runs the flows (flows are its programs). HUBSPOT = the CRM (customer-record system: the web service that stores sales contacts) used by the take. EGM = the studio's review method with independent reviewers; the studio lead runs it, I did not. IMPORT = loading a flow file into n8n. EXECUTION LIST = n8n's screen that lists past runs.")
P("- TIMES AND DATES: times are UTC with IST (UTC + 5:30) where it matters. Take day: target Wed 18 Nov 2026 (not fixed; ORDERS.md Q21.1, %s); the money stop is Mon 23 Nov 2026 18:29 UTC = 23:59 IST; the key must be cancelled by 18:19 UTC = 23:49 IST (Q25, %s); the post is due Wed 25 Nov 2026 15:00 UTC = 20:30 IST. First rehearsal: the studio lead, right after the loopback re-smoke passes (target tonight or tomorrow morning IST; decision 12, %s)." % (quote("ORD", "Q21.1:")[0], quote("ORD", "Q25:")[0], quote("DEC", "12. First laptop rehearsal")[0]))
P("")
P("## 0. Failures, uncertainty, what was not checked, and history")
P("- NOTHING IN THE EDIT TABLE HAS BEEN APPLIED. Every row says NOT APPLIED. Of the %d rows: %d are 'ready' (no open question and no open check; rows %s); %d apply on the default of a question you have not answered (section 3); %d wait for a check that needs n8n (rows %s). The counts per question are made by a script and checked by a second script (section 3, table 3b). A text in the table is a proposal until a builder applies it and a reviewer reads the changed file." % (nrows, RC, nums(ready), RO, RW, nums(withc)))
P("- THE LAST REPORT (REPORT-c6l.md) FAILED TWO INDEPENDENT REVIEWS (review-c6l-design.md: 1 blocker, 6 majors, 6 minors; review-c6l-naive.md: 1 blocker, 9 majors, 8 minors). This report fixes every item of both (section 8: finding, fix, check). THIS REPORT HAS NOT BEEN REVIEWED YET by two independent reviewers; I did not run the EGM steps (the studio lead runs them).")
P("- A SLIP OF REPORT-c6l.md THAT I FOUND AND CORRECT HERE: it cited 'static-checks-output.txt, section C-10c' for the owner-sheet search, but that file had no such section (the search had been run in a shell and not saved). This time the search is in evidence-c6m/static-checks.sh and its output, section C-10c: phrase counts per sheet (never deletes / read, create and change only / does not delete / key read-only): v19 1/0/0/1; v20 and v21 0/0/0/0 and 0/0/0/0; v22 to v26-SOURCE 0/0/0/1 each.")
P("- THE NEWEST OWNER SHEET IS NOT v25: OWNER-SHEET-v26-SOURCE.md (a template with placeholders in double braces, the newest file in the steps-edits folder, still being edited at 15:05 UTC = 20:35 IST) exists. REPORT-c6l.md named v25 as the newest. The rendered sheets are v25 variants A and B. L-SHEET asks which one the owner reads (section 3).")
P("- CONTACT DELETION IS ANSWERED, NOT NEW: the studio lead answered it in ORDERS.md: Q19 item 1 (%s: the take program run_real_check_n8n.py has no delete call; the 'archive in a finally' that was read belongs to the old desk test program run_real_check.py), Q23 (%s: decision 2 stands, the take never deletes; the independent review of 11:00 UTC = 16:30 IST found no archive or delete path in run_real_check_n8n.py; a plan line 1051 is stale; do not widen the HubSpot key) and Q27 (%s: the studio lead reads the script at the final version; until then write 'lead verifies at re-pin'). REPORT-c6l.md called this conflict 'new' and built a gate on the wrong script; rows %d and %d are re-issued against these answers. The part that stays UNVERIFIED is whether the take script really has no archive or delete call: the script is not in the audited files." % (quote("ORD", "1. The take program")[0], quote("ORD", "Q23:")[0], quote("ORD", "Q27:")[0], n("rs71"), n("rs59")))
P("- WHAT IS ABSENT FROM THE CHECKED FILES: the three take and probe scripts (scripts/run_real_check.py, scripts/run_real_check_n8n.py, scripts/hubspot_probe.py: 0 found; the take script is on a local take branch that is never pushed), the lane3 report files HB171, HB180, HB186, HB189 and HB194 (0 found; only their relayed numbers and the lane3 results files in handover/core-hardening/c6-skip-audit/raw-lane3/ exist), and the text of rule R460 (0 hits in handover/bible). The text of QUEUE rule 6 IS on disk (%s). 'The checked files' = a read-only copy of the git branch origin/cloud/flows-audit (the branch that holds the demo files) made in the build session's temporary folder scratchpad/c6/tree/handover; branch cloud/core-hardening (the branch this report sits on) holds the studio lead's own files. Every path in this report is a path inside the repository." % quote("QUE", "6. Inputs copied for you")[0])
P("- NOT RUN: n8n, any flow, the harness, git history, the checks C-3, C-4, C-5, C-6, C-8, C-10b, C-10c (second part) and the second part of C-9 (section 7 gives, for each, the exact missing input). Static reading only.")
P("- What the check script proves (section 7, rows C-1, C-1b and C-4a; raw output evidence-c6m/verify-c6m-output.txt, to be given to every reviewer together with this report): every old text occurs exactly once on the stated line of the stated file; the %d edits can be applied in table order to copies of the files without a mismatch; every cited source line exists; the flow-file edits give the required values on the copies; the per-question counts of section 3 equal a recount from the table; the new texts hold no internal label and no wrong-word slip. It does NOT prove that a statement is true or that a new text is right." % nrows)
P("- Does the web page carry the number 60.1 to 61.9 s? Default: no. Only statement 20 of the page statements file carries it (rows %s: they are corrections and apply whatever you answer on L-PAGE, because the statement already carried the figure); row %d marks statement 20 'not for the web page' and waits for L-PAGE. The rows that used to copy the number into other page statements point to statement 20 without the number and without saying whether statement 20 is for the page (rows %s). The video carries no timing number (decision 1, %s)." % (ids(["pg149a", "pg154"]), n("pg148"), ids(["pg105", "pg120a", "pg120b", "pg139"]), quote("DEC", "1. SCOPE")[0]))
P("- THE 18 RUNS ARE 18 KEPT RUNS. The lane3 series at lease 45 s has 2 more runs that were voided: VOID-fl45k3b (case K3B, never reached a final state, 338.7 s, cause unknown; %s and %s) and VOID-fl45k6c (case K3, the stand-in services were not up, error 'fakes_not_up'; %s). Recount by my own script (evidence-c6m/void-check-output.txt): 18 kept runs (K1 5, K2 5, K3B 5, K3 3), kill to final 60.1 to 61.9 s (median 60.85), from n8n coming back up 52.8 to 54.9 s, restart 6.6 to 8.8 s. The time window of VOID-fl45k3b overlaps 5 kept runs (fl45k2d, fl45k2e, fl45k6a, fl45k3d, fl45k6b; %s) and the window of VOID-fl45k6c overlaps 2 of those (fl45k2e, fl45k6a): so 5 of the 18 kept runs ran at the same time as a voided run; whether that disturbed them was not checked. I could not find in the files who decided to void the two runs beyond the label VOID in the raw rows; the reason for each is the one in the row (error text, or never reached a final state). Every place that writes '18 runs' says kept and names the 2 voided runs." % (quote("RCO", "VOID-fl45k3b K3")[0], quote("RJL", '"label": "VOID-fl45k3b"')[0], quote("RJL", '"label": "VOID-fl45k6c"')[0], quote("RCO", "overlaps VOID-fl45k3b <-> fl45k2d")[0]))
P("- The two numbers 60.1 to 61.9 s and 52.8 to 54.9 s are different measurements of the same 18 kept runs: seconds from the crash to the final state of the contact record, and seconds from n8n coming back up. 45 s is a SETTING (the lease), not a measurement; it may be shown on screen as 'setting: lease 45 s'. 'Not measured on the flows of this take' means: no run on real-v5. 'Measured on stand-in flows' means: lane3 on film-v4. The decisions file calls the cut number 'unmeasured' (%s); that means the same as 'not measured on real-v5'." % quote("DEC", "1. SCOPE")[0])
P("- 'UNKNOWN WITH ONE ALERT' (end state of K3B and K3) IS THE INTENDED SAFE END, NOT A FAILURE: the system cannot tell whether the CRM entry and the mail happened, so it sends one alert and a person decides. K3B being false in 'killed after the mail left' does not make K3 false: K3 (killed after the mail was delivered) is described correctly by mf.py. Only the K3B sentence is wrong.")
P("- HISTORY, slips of REPORT-c6k.md and REPORT-c6l.md corrected over the last versions: take-script behaviour stated as fact (c6k); owner sheets said not to be on disk and v19 assumed (c6k); 'each of 18 runs' without the 2 voided runs (c6k); a closing-card row that waited for three answers at once (c6k); the cut number copied into page statements while the question on publishing it was open (c6k); 'the lead' meant two people and 'claim' meant four things (c6k); a gate built on the wrong script and contradicting Q23 (c6l); an unconfirmed default attributed to a decision (c6l); wrong-word slips 'studio lead's made-up name' and 'studio lead table' caused by a global replacement (c6l; fixed in the replacement rule and checked by the check script).")
P("")
P("## 1. How to use this report")
P("- ONE ID: the first column of the edit table (section 5) is the only ID. Every other section uses these numbers. Old names and the row numbers of REPORT-c6l.md are mapped in section 5 (second table); the row numbers are the same as in REPORT-c6l.md.")
P("- APPLY ORDER, in two waves. Wave 1: every row that says 'ready' or 'on the default of ...' (the rows without a check), in table order. Wave 2: after wave 1 the studio lead runs the checks named in 'after check ...' and applies those rows only when the check has passed: C-4 needs the edited flow files imported (so wave 1 comes first) and C-8 needs the loopback re-smoke. Within one file the rows are sorted from the bottom of the file to the top, so applying them in order never shifts the line number of a row still to come. The column Line is the line number BEFORE any edit of that file. A builder who applies in another order must find each old text by text, not by line.")
P("- Old text and new text are exact file text. '<br>' in a cell means a line break in the file. Nothing else is abbreviated. Several rows on the same line (for example the closing card line) change different pieces of text on that line. The column 'What the viewer sees' says in a few words what changes for a person who watches the video or reads the page; 'Nothing' means the row changes only a note or a program comment.")
P("- STATUS words: 'ready' = no open question and no open check. 'on the default of L-X' = apply it if the studio lead answers L-X with the default or writes 'apply all defaults' (section 3, table 3c); do not apply it if the studio lead answers differently. 'after check C-N' = do not apply until that check has passed (section 7). A row that is not ready is still written out in full, so the studio lead can say yes to its default.")
P("- THE CLOSING CARD ROWS ARE ONE SET: rows %s change the closing card and the lines that talk about it. They apply together or not at all, so the card is never left half-changed. The set depends on four questions (L-CARD, L-CARDCUT, L-CARDTEXT, L-LEASE; section 3 says which row depends on which). If you answer one of them differently, the studio lead names the rows to re-issue; the others stay." % ids(["rs82", "rs80", "rs41a", "rs41b1", "rs41b2", "rs41c", "rs33d", "rs14", "rs5b"]))
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
P("N = number of runs (so n=2 means 2 runs). The setting label (lease 45 s) and the live stopwatch are not timing numbers (Words). The kill-to-final and from-n8n-up figures are for the 18 KEPT runs only; the two voided runs are described in section 0.")
P("")

P("## 3. Questions (who answers, text, default used, confirmed?, what a different answer changes)")
P("The edit table uses the default of each question. Nobody has confirmed any of them (column 'Confirmed?'). A default is what the table assumes if no answer comes; this report never says that a decision made a default. Where one of your answers in ORDERS.md already settles a question, the row cites it (the answers are named Q19 to Q34 in ORDERS.md; Q24 and Q28 to Q34 answer none of these questions). Old names: L-CARD was Q1 (it is now three questions: L-CARD, L-CARDCUT, L-CARDTEXT), L-KILL was Q2, L-APPROX was L-ROUND (renamed: it is about rounded wording, not a review round), L-SHEET was Q10, and Q11 is answered (see L-LEASE). Q3 to Q8 of REPORT-c6h.md touch no edit here; table 3d says who runs the re-smoke and the leak scan and when.")
P("")
P("Who answers: STUDIO LEAD = decides alone. OWNER ONLY = only the owner knows the fact or holds the permission on his own accounts; the studio lead asks him. The decisions file says the owner may veto any decision (%s)." % quote("DEC", "# Lead decisions")[0])
P("")
P("| Question | Who answers | Text of the question | Default used | Confirmed? | If the answer is different | Rows tied to it |")
P("|---|---|---|---|---|---|---|")
P("| L-CARD (was Q1, part 1) | studio lead | Does the closing card (scene 12, the last card of the video, run sheet line 41) stay as the last card? | Yes, it stays. | No | If the card is cut: every row tied to L-CARD is dropped (the card rows are one set, section 1); nothing else changes. | %s |" % nums(dep_list("L-CARD")))
P("| L-CARDCUT (was Q1, part 2) | studio lead | Cut card lines 2 and 3 (the 80 kills and the recovery time; they come from older flows and an estimate that no data of this take backs)? | Yes, cut. | No | If no: the rows tied to it are dropped and the old lines stay (they carry numbers decision 1 cuts from the video, so say so to the studio lead before choosing no). | %s |" % nums(dep_list("L-CARDCUT")))
P("| L-CARDTEXT (was Q1, part 3) | studio lead | Use the new spoken card lines: no statement about alert delay, one sentence on what n8n keeps (statement 18, still unbacked, said as 'may stay in n8n's database'), one sentence on what was not tested? | Yes. | No | The studio lead gives the sentences; the rows tied to it are re-issued. | %s |" % nums(dep_list("L-CARDTEXT")))
P("| L-LEASE | studio lead (his answers Q21.2 at ORD:%d and Q22 at ORD:%d already require an honest sentence on the lease; the exact wording is open) | May the closing card and the scene 3 caption say: 'We say this only when the second send comes within 45 seconds of the first. The 45 seconds is a setting: for that long the system keeps a contact record for the run that took it first.'? (Your Q21.2 word 'claimed' means 'no statement is made'.) | Yes, that sentence. | Choice yes (Q21.2), wording no | The studio lead gives the sentence; the rows tied to it are re-issued with it. | %s |" % (find("ORD", "Q21.2:"), find("ORD", "Q22:"), nums(dep_list("L-LEASE"))))
P("| L-KILL (was Q2) | studio lead | Scene 4 (the crash and the recovery): (a) leave the kill-case words (K3B, K3) out, or (b) keep them, labelled as a stand-in test on film-v4 flows? | (a). REPORT-c6h.md gave (b); (a) is used because decision 8 (%s) allows no extra test run with real accounts, K3B and K3 were never run on the real-v5 flows, and the old K3B sentence is false as written. | No | If (b): row %d is re-issued with: 'Stand-in test, film-v4 flows: n8n killed while the mail connection was opening, the mail was not delivered: the contact record ends unknown with one alert to the owner. Stand-in test, film-v4 flows: n8n killed after the mail was delivered: the contact record ends unknown with one alert to the owner.' | %s |" % (quote("DEC", "8. Real-account smoke")[0], n("rs90"), nums(dep_list("L-KILL"))))
P("| L-APPROX (was L-ROUND) | studio lead | May scene 4 and the web page say 'about a minute, in the test' in place of the cut number? (The live stopwatch and a 'sped up, real wait N s' label are this run's own clock, not a timing number, and are not asked here.) | No. No timing number and no rounded timing wording in the video text; decision 1 (%s) cuts the number. | No | If yes: the studio lead names the exact caption; the rows tied to it are re-issued with it. | %s |" % (quote("DEC", "1. SCOPE")[0], nums(dep_list("L-APPROX"))))
P("| L-SAVE | studio lead (the plan row says 'owner 2026-11-16'; the studio lead confirms it is still current) | Does the take save every run in n8n (EXECUTIONS_DATA_SAVE_ON_SUCCESS=all and _ON_ERROR=all), so that the execution list filmed in scenes 1 and 2 shows runs? | Yes (%s). Checks: C-11 (static, done) and C-4 (import check, not run). | No | If no: the rows tied to it are dropped and the execution list in scenes 1 and 2 stays empty (scene 1 then needs a rewrite this report does not contain). The closing card does not depend on it. | %s |" % (quote("PLAN", "| executions (take) |")[0], nums(dep_list("L-SAVE"))))
P("| L-PAGE | studio lead | May the web page carry the lane3 range 60.1 to 61.9 s (film-v4 stand-in flows, a labelled statement, never a caption) and statement 19 (the 13-minute alert delay, lane3 v4 flows)? | No. Statements 19 and 20 stay in the statements file, marked not for the web page. | No | If yes: the rows that mark them are dropped and the statements are published with their tags. | %s |" % nums(dep_list("L-PAGE")))
P("| L-ONEDB | studio lead | Ratify or veto the interim sentence for any text written before the re-smoke has passed: 'n8n keeps its own records in its own database file. Our claim table is in a separate Postgres database. That is two stores.' (Q21.3 at ORD:%d allows the caption 'one Postgres server, two databases' only once that is true.) | The target wording of decision 10 goes into DECISION-one-store.md marked as a target (rows %s); viewer-facing text uses only the interim sentence until check C-8 passes. | No | If vetoed: no viewer-facing text says anything about the number of databases until C-8 passes. | %s |" % (find("ORD", "Q21.3:"), ids(["one13", "one14", "one16"]), nums(dep_list("L-ONEDB"))))
P("| L-SHEET (was Q10) | OWNER ONLY (the studio lead asks him; the studio lead may answer if the owner agrees) | Which owner sheet does the owner read? Sheets on disk: v19 to v25 variants A and B, and OWNER-SHEET-v26-SOURCE.md (a template, still being edited at 15:05 UTC = 20:35 IST). | v25 variant A. Not decided in any file I read. | No | If another sheet: check C-10c is run on that sheet. No row touches an owner sheet. | none (check C-10c) |")
P("| L-DEL (ANSWERED; part still open) | studio lead (ORDERS.md Q19 item 1 at ORD:%d, Q23 at ORD:%d, Q27 at ORD:%d) | Does the take delete or archive contacts? | NO, never: decision 2 stands; the take program run_real_check_n8n.py has no delete call and uses a HubSpot identity that cannot archive (Q19 item 1); the independent review of 11:00 UTC found no archive or delete path in it; the HubSpot key is not widened (Q23). UNVERIFIED: that the script at the final version still has none; the studio lead reads it at the re-pin and answers (a), (b) or (c) of Q27 with line numbers. Until then the sheet says 'lead verifies at re-pin'. | Answered | If the final version has an archive or delete call: the studio lead says so and a builder re-issues rows %d and %d. | none (rows %d and %d are written to the answer) |" % (find("ORD", "1. The take program"), find("ORD", "Q23:"), find("ORD", "Q27:"), n("rs59"), n("rs71"), n("rs59"), n("rs71")))
P("| L-CUT | studio lead | Scenes 5 to 11 (run sheet lines 34 to 40) are cut from the one video but their rows hold stale text (K3 and K3B history, V7 numbers). Mark each row 'not in the one video'? | No edit now (they are not filmed). | No | If yes: a new row per scene is issued. | none |")
P("")
P("3b. Count of rows per question, made by the build script from the table and checked by evidence-c6m/verify-c6m.py (which recounts from the markdown table of section 5):")
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
P("3c. 'APPLY ALL DEFAULTS': what it does is in the box at the top. Rows it applies: the %d ready rows (%s) and the %d rows that wait only for a question (%s), %d rows in all, in the files %s. Rows it does not apply (they wait for a check): %s. What changes in content: the closing card gets four spoken lines and the lease sentence; scene 4 has no kill-case words and no rounded timing wording; the take saves every run (flow-file rows and saving notes); statements 19 and 20 are marked not for the web page; DECISION-one-store.md gets the target wording marked as a target; row(s) %s wait for the import check C-4 and row(s) %s wait for C-8 (the Postgres wording) and stay unapplied until those checks pass." % (RC, nums(ready), RO, nums(onlyq), RC + RO, ", ".join(F[k][1].split("/")[-1] for k in files), nums(withc), nums(dep_list("C-4")), nums(dep_list("C-8"))))
P("")
P("3d. Who runs the long-standing steps and when (they touch no edit). Loopback re-smoke: the studio lead, before the first rehearsal (%s; decision 12); checks C-4, C-8 and the table part of C-9 are read during it. LEAK SCAN for the take (check C-6): the studio lead names a builder who writes it (the audit writes no code); the studio lead runs it on the loopback stand-ins before the first rehearsal and again after any change to a flow file or a saving setting; the run-sheet gate (item 14 of the rehearsal list, row %d) blocks the take until its pass line is written with a UTC and IST time and the person's name. Import check (C-4): same gate. Execution-list check (C-5): the studio lead, before scene 1 and before scene 2 of every rehearsal and of the take. Active-workflow check (C-3): the studio lead, before every rehearsal and before the take. Dates: take target Wed 18 Nov 2026 (not fixed), money stop Mon 23 Nov 2026 18:29 UTC = 23:59 IST; no hour for any rehearsal step is written in any file I read." % (quote("DEC", "12. First laptop rehearsal")[0], n("rs71")))
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
    ("c6b to c6m", "successive versions of this audit report; c6m (this file) supersedes c6l; c6h is the last full report (REPORT-c6h.md).", "H6:1"),
    ("UNBACKED, RELAYED-INDEPENDENT, MEASURED-ON-LAPTOP", "tags on numbers: no raw file / relayed from another session without the raw file / read by the studio lead from laptop result files.", "RS:18, RS:19"),
    ("V7", "laptop result files and the studio lead's read of them (V7-NUMBERS-lead-read.md) behind the '80 kills' numbers, measured on older v3 flows with a 20 s lease on stand-ins.", "H6:387"),
    ("T13, T15, B90, AF1, KS", "earlier test names in the run sheet and page history lines (T13 same-id and database kill, T15 CRM refuses, B90 alert-send case, AF1 alert refused twice, KS the alert-send kill case); not used by any edit here.", "RS:32"),
    ("ORDERS.md answers Q19 to Q34", "numbered answers inside ORDERS.md (the studio lead's file): Q19 item 1 the take program, Q21.1 dates, Q21.2 the statement wording and the lease sentence, Q21.3 the caption for the number of databases, Q22 option (c), Q23 the take never deletes, Q25 cancel-by time, Q27 the studio lead reads the take script at the final version. They are not the questions L-... of this report.", "ORD:150 to ORD:191"),
    ("L-CARD, L-CARDCUT, L-CARDTEXT, L-LEASE, L-KILL, L-APPROX, L-SAVE, L-PAGE, L-ONEDB, L-SHEET, L-DEL, L-CUT", "the questions of section 3 (L = question for the studio lead or the owner); plain meanings are in the box at the top.", "section 3"),
    ("C-1 to C-11 (C-1b, C-4a, C-10a to C-10d)", "the checks of section 7 (C = check).", "section 7"),
    ("ready, on the default of, after check", "the three kinds of status of an edit row; see section 1.", "section 1"),
    ("wave 1, wave 2", "wave 1 = rows without a check, wave 2 = rows after a check; see section 1.", "section 1"),
]
G += [
    ("n8n, HubSpot, CRM, EGM, import, execution list", "n8n = the workflow tool that runs the flows; HubSpot = the web service that stores the sales contacts (a CRM = customer-record system); EGM = the studio's review method with independent reviewers; import = loading a flow file into n8n; execution list = n8n's screen of past runs.", "Words"),
    ("take script, old desk test program, probe script", "scripts/run_real_check_n8n.py is the take script (the video uses it); scripts/run_real_check.py is the older desk test program (not the take); scripts/hubspot_probe.py tests the HubSpot key. None is in the checked files.", "ORD:%d" % find("ORD", "1. The take program")),
    ("scratchpad/c6/tree/handover, origin/cloud/flows-audit, cloud/core-hardening", "developer paths: a read-only copy of the files of git branch origin/cloud/flows-audit, made in the build session's temporary folder; cloud/core-hardening is the branch this report sits on. Every path in the report is a path inside the repository.", "section 0"),
    ("kept run, voided run, n", "see Words at the top of the report.", "Words"),
]
for t, m, s in G:
    P("| %s | %s | %s |" % (t, m, s))
P("")


# ---------------------------------------------------------------- edit table
OLDK = json.load(open(C6 + "/evidence-c6l/edits.json"))
SPLIT = {"rs41b": ["rs41b1", "rs41b2"]}
was = {}
for o in OLDK:
    for nk in SPLIT.get(o["key"], [o["key"]]):
        was.setdefault(nk, []).append("row %d" % o["n"])
P("## 5. EDIT TABLE (every row: NOT APPLIED)")
P("Rows are in apply order (section 1). Paths are paths inside the repository (section 0). 'What the viewer sees' says what a person watching the video or reading the page sees differently. 'Was (c6l)' gives the row number the same edit had in REPORT-c6l.md ('new' = no such row there). Sources use the short names of section 1.")
P("")
P("| ID | Status | Target file (path inside the repository) | Line before any edit | What the viewer sees | Old text (exact) | New text (exact) | Reason and source file:line | Was (c6l) |")
P("|---|---|---|---|---|---|---|---|---|")
for e in EDITS:
    P("| %d | %s | %s | %d | %s | `%s` | `%s` | %s Sources: %s | %s |" % (e["n"], status(e), F[e["fk"]][1], e["line"], e["view"], cell(e["old"]), cell(e["new"]), e["why"], e["src"], "; ".join(was.get(e["key"], ["new"]))))
P("")
P("Row numbers of REPORT-c6l.md mapped to the IDs of this report (every other section uses only the IDs of this report):")
P("")
P("| c6l row (name there) | ID(s) now |")
P("|---|---|")
for o in OLDK:
    P("| %d (%s) | %s |" % (o["n"], o["key"], ids(SPLIT.get(o["key"], [o["key"]]))))
P("")

P("## 6. The contact gate in detail (does the take delete or archive contacts? every cite below was opened)")
P("Words: ARCHIVE = HubSpot moves the contact to its recycle bin (it can be restored). PERMANENT DELETE = the contact is erased. TAKE SCRIPT = scripts/run_real_check_n8n.py, the program the video uses (on a local take branch that is never pushed; not in the checked files). OLD DESK TEST PROGRAM = scripts/run_real_check.py, an older program that is NOT the take. PROBE SCRIPT = scripts/hubspot_probe.py (a test of the HubSpot key). The studio lead's decision 2 (%s) says the take never deletes contacts; leftover made-up contacts are listed and the owner deletes them by hand in HubSpot after the take." % quote("DEC", "2. TAKE IDENTITY")[0])
P("")
P("WHAT IS ANSWERED (your answers in ORDERS.md): Q19 item 1 (%s): the take script has NO delete call and uses a read-only HubSpot identity with archive_contacts 'no' and lists leftovers; the 'archive in a finally' step that was read belongs to the OLD DESK TEST PROGRAM. Q23 (%s): decision 2 stays, the take never deletes; the independent review of 11:00 UTC (16:30 IST) found no delete or archive path in the take script; line 1051 of the plan is stale text; do not widen the HubSpot key. Q20 item 3: the scope of the HubSpot key is held by the owner and unknown to the studio; the studio lead asks the owner once at take prep. Q27 (%s): UNVERIFIED; the studio lead reads the take script at the final version and answers (a), (b) or (c) with line numbers at the re-pin." % (quote("ORD", "1. The take program")[0], quote("ORD", "Q23:")[0], quote("ORD", "Q27:")[0]))
P("")
P("WHAT IS STALE OR UNVERIFIED (the files still say it; no row may repeat it as program behaviour):")
P("")
P("| What the file says | Cite (opened) | Text at the cite | Status |")
P("|---|---|---|---|")
for lab, k, a, st in [
    ("Old help text: an option that archives the contacts the run made", "EQ4", "--cleanup", "Belongs to the old desk test program or is stale: not the take (Q19 item 1)"),
    ("Plan 4: up to 3 contacts archived at the end", "P4", "up to 3 HubSpot contacts archived at the end", "STALE notice (Q23); must not be shown to the owner; row %d item 11 says so" % n("rs59")),
    ("Plan 4: archives also when the take ends in an error; leftovers listed", "P4", "1. the script archives this take's contacts", "STALE (Q23, Q19 item 1)"),
    ("The probe script docstring and code (audit note)", "CA", "scripts/hubspot_probe.py:4-5", "The probe script is not the take; UNVERIFIED which key it uses"),
    ("The probe tries a permanent delete first, then an archive (audit note)", "CB", "hubspot_probe.py:271-287", "The probe script is not the take; script not in the tree"),
    ("Whether an archived contact keeps its e-mail address reserved", "SH", "ASSUMED to keep its email reserved", "ASSUMPTION, never checked"),
    ("Owner sheet v25 A: a notice line saying contacts will be deleted or archived is a difference; stop", "OS25", "Compare every number and name in the notice", "Consistent with Q23"),
    ("Owner sheet v25 A: the owner deletes made-up contacts by hand", "OS25", "You delete only made-up contacts of this run", "Consistent with decision 2"),
]:
    c, t = quote(k, a)
    P("| %s | %s | %s | %s |" % (lab, c, t, st))
P("")
P("Checked by reading the four real-v5 flow files (command and output: evidence-c6m/contact-grep-output.txt, copied from the c6k run): no DELETE call and no archive call (0 hits). The only places that touch contacts are the take script and the other scripts, and those files are not in the checked files.")
P("")
P("THE GATE (row %d, item 11 of the rehearsal list on the run sheet): before the take the studio lead reads the take script at the final version, runs two searches (one for the word archive, one for the word delete; I give two commands because the table cell must not hold a pipe character), writes the output on the run sheet, and writes a four-line record (version id; search output; 'matches the decision' or 'stop: tell the owner'; no notice that promises delete or archive is shown). Until then the take is blocked. The owner sheet may say that the owner deletes leftovers by hand; it must NOT say that the HubSpot key is read-only or create-and-change-only unless the owner confirmed it (Q20 item 3). The closing check is C-10 (section 7); it no longer requires the decisions file to have 0 hits, because decision 2 itself says never deletes." % n("rs59"))
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
P("| C-1 | Every old text of section 5 occurs once on its line (the same copy method as REPORT-c6k.md) | the build and check scripts (done by me) | every row: exactly one match on the stated line | any row with 0 or 2 matches | DONE; result is in evidence-c6m/verify-c6m-output.txt |")
P("| C-1b | All rows applied in table order to COPIES of the files; no mismatch; no internal label, stale phrase, banned string, secret or e-mail address in a new text | the check script (done by me) | 0 mismatches and 0 hits | any mismatch or hit | DONE; same file |")
P("| C-2 | The 8 flow files (4 real-v5, 4 film-v5) all carry none, none, false and no errorWorkflow | me, file read | the evidence lists the same four values for all 8 | any other value | DONE (static): EVSET:%d to EVSET:%d |" % (find("EVSET", "n8n-flows-real-v5/mf-form.json"), find("EVSET", "n8n-flows-film-v5/mf-recovery.json") if any("n8n-flows-film-v5/mf-recovery.json" in l for l in lines("EVSET")) else find("EVSET", "n8n-flows-real-v5/mf-sub-crm-mail.json")))
P("| C-3 | Only real-v5 flows are active before each rehearsal and before the take (list the active workflows in n8n) | studio lead | the list holds only workflows imported from n8n-flows-real-v5 | any workflow from another folder, or a workflow with the path mf-form or mf-hook from another folder | NOT RUN; missing input: a running n8n on the take computer (impossible-now here; needs-lead) |")
P("| C-4 | Import check: the four edited real-v5 files are imported and one made-up contact record is sent | studio lead | within 60 s the execution list shows at least one run of an entry flow and at least one run of the recovery flow | the list stays empty, or shows only runs from before the clean-up | NOT RUN; missing input: running n8n and the rows %s applied (impossible-now here; needs-lead) |" % ids(["jJFSuccess", "jJFError", "jJHSuccess", "jJHError", "jJRSuccess", "jJRError", "jJSSuccess", "jJSError"]))
P("| C-4a | After the eight flow-file rows are applied to copies, each flow file holds saveDataSuccessExecution all and saveDataErrorExecution all and saveManualExecutions false, once each | the check script (done by me) | counts 1, 1, 1 in each of the 4 files | any other count | DONE on copies; result in evidence-c6m/verify-c6m-output.txt |")
P("| C-5 | Execution list before scene 1 and again before scene 2: no row older than the take start time written on the run sheet, no row with rehearsal data (recovery-flow rows are expected; a screen check, not an erasure) | studio lead | every row shows a start time later than the take start time and no rehearsal data | any older row, or any rehearsal data | NOT RUN; missing input: running n8n and the take start time (impossible-now here; needs-lead) |")
P("| C-6 | Leak scan for the take (N8N-START.md section added by row %d): case 1, case 2, and the name and e-mail rule, on six stores, loopback stand-ins only | a builder named by the studio lead writes it; the studio lead runs it | the pass lines of the section (case 1: 0 hits for both fake secrets in all six stores; case 2: key hits only in n8n's database; name and e-mail: 0 hits in journal, ledger and logs) | any hit outside what the section allows | NOT RUN; missing inputs: the scan itself (not written; the audit writes no code), a running n8n with stand-ins, and the path of the spend ledger from the take's config (needs-lead) |" % n("ns48"))
P("| C-7 | real-v5 and film-v5 differ only in mf-recovery.json and mf-sub-crm-mail.json | me, file read | the file list diff names only those two files (V5-NODE-DIFF.txt exists only in real-v5 and is not a flow file) | any other file or flow differs | DONE (static) PASS: evidence-c6m/static-checks-output.txt, section C-7; whether the import reads only the .json files: NOT RUN, needs a running n8n import (needs-lead) |")
P("| C-8 | The loopback re-smoke shows that n8n's engine is Postgres, before any text says one Postgres server with two databases (decision 10) | studio lead | the setting that names n8n's database type reads Postgres and n8n's data sits on the take's Postgres server | it reads SQLite | NOT RUN; missing input: the loopback re-smoke with a running n8n and Postgres (impossible-now here; needs-lead) |")
P("| C-9 | The repeat-send statement is backed by a unique rule on the claim table (gate, run sheet item 12) | part 1 me (static); part 2 studio lead | part 1: a primary key or unique index on the contact id in the test program and an ON CONFLICT insert in the entry flows; part 2: the same rule seen in the take's own table | part 2: no such rule seen; FAIL: the studio lead may only write 'index not seen, accepted' on the run sheet, with UTC and IST time and name, as an allowance, not a pass; or the statement is not filmed; the studio lead writes 'index not seen, accepted' on the run sheet (ORD:%d) or the statement is not filmed | part 1 DONE (static) PASS: MF:%d and %s, ON CONFLICT in mf-form.json and mf-hook.json (evidence-c6m/static-checks-output.txt); part 2 NOT RUN; missing input: the take's database after the re-smoke (needs-lead) |" % (find("ORD", "Q21.2:"), find("MF", "CREATE TABLE mf_leads"), quote("MF", "CREATE TABLE mf_leads")[0] if False else "MF:%d" % find("MF", "CREATE TABLE mf_leads")))
P("| C-10a | Real-v5 flows contain no delete or archive call: grep -il -E 'DELETE|archive' on the four files | me, file read | 0 hits (grep exit code 1) | any hit | DONE PASS: 0 hits (evidence-c6m/contact-grep-output.txt) |")
P("| C-10b | Take script: two searches of scripts/run_real_check_n8n.py at the final version, one for the word archive and one for the word delete, output written on the run sheet; also the old desk test program and the probe script named, not used by the take | studio lead at the re-pin (ORDERS.md Q27) | the take script has no archive or delete call, or only (b) own contacts archived and the owner sheet says so | any other call | NOT RUN, UNVERIFIED; missing input: the script is not in the checked files (needs-lead) |")
P("| C-10c | The owner sheet the owner reads: grep -n -i -E 'never deletes|read, create and change only|does not delete' on each sheet | me for the sheets on disk; studio lead for the final sheet | the sheet says the owner deletes leftovers by hand and does not say the HubSpot key is read-only or create-and-change-only unless the owner confirmed it (Q20 item 3) | any other statement of the key's scope | part 1 DONE on the sheets on disk (v19 to v25 and v26-SOURCE, evidence-c6m/static-checks-output.txt section C-10c: v19 1 hit, others 0 for these phrases); v26-SOURCE was still being edited at 15:05 UTC; part 2 NOT RUN; missing input: L-SHEET (needs-owner) |")
P("| C-10d | Decisions file: decision 2 still reads 'the take never deletes' (it is the answer Q23 keeps) | me, file read | decision 2 line present once | line missing or changed | DONE: no 0-hit requirement any more (it was unsatisfiable by construction in REPORT-c6l.md) |")
P("| C-11 | L-SAVE check: the re-smoke plan says all for both saving settings (static) | me, file read | the plan row holds EXECUTIONS_DATA_SAVE_ON_SUCCESS=all and EXECUTIONS_DATA_SAVE_ON_ERROR=all | either value is not all | DONE (static) PASS: %s (evidence-c6m/static-checks-output.txt); the runtime proof is C-4 (NOT RUN) |" % quote("PLAN", "| executions (take) |")[0])
P("| C-4 and C-6 as a gate | The run sheet blocks the take until the import check (C-4) and the leak scan for saved runs (C-6) are both written as passed, each with UTC and IST time and a name | studio lead (owner of the gate); a builder he names writes the scan | two lines present before the take | either line missing | Row %d item 14; NOT RUN |" % n("rs71"))
P("")

P("## 8. Coverage: finding -> fix -> where (every item of the two c6l reviews)")
P("")
P("| Review item | Fix | Where / check |")
P("|---|---|---|")
COV = [
    ("Design B1: gate (row 8, row 6 item 12) built on the wrong script, contradicts Q23, never cites Q22 to Q34, calls the conflict new, unsatisfiable 0-hit rule", "Rows %d and %d re-issued against Q19 item 1, Q23 and Q27; both scripts named and the video's script named; the decisions-file 0-hit requirement dropped; archive-after-error no longer stated as behaviour; 'new' removed; L-DEL default is what Q23 says with the UNVERIFIED part labelled; Q22, Q23, Q25, Q27, Q21.1 cited where they answer" % (n("rs59"), n("rs71")), "Sections 0, 3 (L-DEL, L-LEASE), 6; check C-10b, C-10d redefined; verify-c6m.py: no 'archive or delete' pipe text, rows say run_real_check_n8n.py"),
    ("Design M1: unconfirmed defaults attributed to decisions (rows 1, 3, 5, 31)", "Rows reworded: a default is called a default of the named question; only decision 1 is cited for the cut number", "verify-c6m.py scan 'decided' next to L- defaults; table 3b"),
    ("Design M2: L-CARD is a multi-decision question", "Split into L-CARD, L-CARDCUT, L-CARDTEXT; row 14 reason fixed; each card row depends only on what it changes (section 3 and 3b)", "Table 3b"),
    ("Design M3: rows 36 and 39 are corrections tied to L-PAGE", "Rows %s no longer wait for L-PAGE (corrections apply whatever you answer); row %d split from the rest" % (ids(["pg149a", "pg154"]), n("pg148")), "Table 3b"),
    ("Design M4: row 17 tied to L-ROUND although removing the old caption is independent; is the 'sped up' label a timing number?", "Row 17 split; the live stopwatch and 'sped up, real wait N s' label are named as this run's own clock, not a timing number (Words, L-APPROX)", "Words; section 3"),
    ("Design M5: saved runs have no gate (C-4, C-6 not on the run sheet; no owner)", "Row %d item 14: the take is blocked until two lines (import check passed, leak scan for saved runs passed), each with a UTC and IST time and a name, are written; the studio lead owns it and names the builder" % n("rs71"), "Section 3d; checks C-4, C-6"),
    ("Design M6: wrong-word slips 'studio lead's made-up name', 'studio lead table'", "The replacement rule was fixed and rows rewritten; verify-c6m.py greps for 'studio lead' followed by made-up, table or name", "verify-c6m-output.txt"),
    ("Design m1 (rows 21, 23 tied to C-4)", "Dependencies set per row by the DEP table in build_c6m.py", "Table 3b"),
    ("Design m2 (rows 42, 45, 47 say 'not for the web page')", "Wording 'see statement 20' without saying whether it is for the page", "Rows %s" % ids(["pg105", "pg120a", "pg120b", "pg139"])),
    ("Design m3 (statement 20 names voided runs, not the overlap)", "Row %d names the overlap: 5 kept runs overlap the voided K3B window; whether it disturbed them was not checked" % n("pg149a"), "Section 0 (18 runs); void-check-output.txt"),
    ("Design m4 (dates exist)", "Take target Wed 18 Nov, money stop Mon 23 Nov 18:29 UTC = 23:59 IST, cancel by 18:19 UTC = 23:49 IST, post Wed 25 Nov 15:00 UTC = 20:30 IST, first rehearsal after the loopback re-smoke", "Words; section 3d"),
    ("Design m5 (row 22 refers to a leak-scan section only row 49 creates; row 1 L-KILL (b) keeps 'unmeasured')", "Row 22 text no longer relies on the other section; the unmeasured wording is fixed by the Words entry", "Reading"),
    ("Design m6 (verify scanned page files only for 60.1 to 61.9; 'never deletes' hits not acted on)", "verify-c6m.py scans the new text of every row for the figure and for the 'never deletes' phrases", "verify-c6m-output.txt"),
    ("Naive B1: undefined labels before the decision; no action list", "Action box first (section 'Start here'): every L- label with plain meaning, default, who answers; the reply line; exact limits; Words block", "Top of the report"),
    ("Naive M1: 'lead' two meanings; 'studio lead's made-up name'", "Studio lead / owner / contact record fixed in new texts; Words block; verify scan", "verify-c6m-output.txt"),
    ("Naive M2: owner versus studio lead, how to reach the owner", "Words: the owner is reached through the studio lead; L-SAVE answered by the studio lead", "Words; section 3"),
    ("Naive M3, M4, M5: take, line, sheet, claim", "Words block: take, take script, rehearsal; line N, card line, notice line; run sheet, owner sheet; the word claim not used", "Words"),
    ("Naive M6: apply-all-defaults limits, builder and reviewer, answer format, unreviewed edits, how to reverse, 3b unreadable", "Box: exact reply line, what is and is not applied, unreviewed texts named, reversing; table 3b gets a plain heading", "Top; sections 3b, 3c"),
    ("Naive M7: voided and kept runs unexplained", "Words (kept run, voided run); section 0 gives who and why as far as the file says, and the overlap", "Section 0"),
    ("Naive M8: no dates; times without IST; n= undefined; 'no number on screen' versus 'setting: lease 45 s'", "Dates in UTC and IST; n = number of runs; the setting label is not a timing number", "Words; section 2"),
    ("Naive M9: section 5 hard to read; review codes undecoded", "New column 'What the viewer sees'; glossary decodes review item names; the second reading aid is the apply-order sentence in section 1", "Section 5; glossary"),
    ("Naive m1, m3, m8: n8n, HubSpot, CRM, EGM, import, execution list, short names, developer paths", "Words and glossary; the paths are glossed in section 0", "Words; section 4"),
    ("Naive m2: delete / archive senses", "Words: DELETE, ARCHIVE, CLEARING; section 6", "Words"),
    ("Naive m4: L-ROUND clashes with review round", "Renamed L-APPROX", "Section 3"),
    ("Naive m5: 'unknown with one alert' good or bad news", "Section 0: it is the intended safe end", "Section 0"),
    ("Naive m6: C-9 FAIL cell is an allowance", "C-9 FAIL cell says 'fail; the studio lead may only write index not seen, accepted'", "Section 7"),
    ("Naive m7: eight flow rows share one long reason", "Flow-file rows keep one shared reason sentence, repeated text shortened", "Section 5"),
    ("Slip of c6l: cited a static-checks section C-10c that did not exist", "Section added and output regenerated; newest sheet v26-SOURCE included", "Section 0; static-checks-output.txt"),
]
for a, b, c in COV:
    P("| %s | %s | %s |" % (a, b, c))
P("")
P("## 9. Not covered here (each with the label and the exact next step)")
P("- [needs-lead] L-DEL part open: the studio lead reads scripts/run_real_check_n8n.py at the final version and answers (a), (b) or (c) of Q27 with line numbers (his own plan at ORDERS.md Q27); then C-10b is run and the gate record of row %d is written. No date is given in any file." % n("rs59"))
P("- [needs-owner] The scope of the HubSpot key (ORDERS.md Q20 item 3). Next step: the studio lead asks the owner once at take prep; until then the owner sheet must not state the key's scope.")
P("- [needs-owner or needs-lead] L-SHEET: which owner sheet (v25 A, v25 B or the v26 template once it is rendered) the owner reads. Next step: name it; C-10c is run on it. The older sheets v10 to v12 still contain the phrases (v10 2 hits, v11 1, v12 1); they are not used if the owner reads v25 or v26.")
P("- [impossible-now] n8n, Postgres and the harness are not available in this session: checks C-3, C-4, C-5, C-6, C-8 and the second part of C-9 cannot run here. Next step: the studio lead runs them in the loopback re-smoke (table 3d).")
P("- [needs-lead] The take script, the other two scripts, the five lane3 reports (HB171, HB180, HB186, HB189, HB194) and the text of rule R460 are not in the checked files. Next step: add them to a branch the next audit can read; until then statements about them stay 'plan and help text, code not read' or 'relayed'.")
P("- [needs-lead] Scenes 5 to 11 rows (run sheet lines 34 to 40): question L-CUT.")
P("- [needs-lead] plan-wp6-resmoke-v5.md still names film-v5 at the lines listed in REPORT-c6h.md section 4; the plan is an input and is not edited. Plan line 1051 is stale (Q23).")
P("- [needs-lead] The stage's spend ledger path was not found in any file read; the leak scan needs it (row %d). Next step: the builder takes it from the take's config." % n("ns48"))
P("- [needs-lead] Run sheet lines 30 and 52 still say 'the request body stays in n8n data until pruned'; that stays true with saving all, so they are left.")
P("- [impossible-now] Whether deleting an execution in the n8n screen only hides it: not verified. Check C-5 is a screen check and says so.")
P("- [needs-lead] Not reviewed: this report was written and checked by me alone; the EGM review of the changed files, resolve and drift report are run by the studio lead; I started no sub-agent and no background process.")
open(C6 + "/REPORT-c6m.md", "w", encoding="utf-8").write("\n".join(OUT) + "\n")
print("report lines", len(OUT), "rows", nrows, "ready", RC, "defaults-only", RO, "with-check", RW)
