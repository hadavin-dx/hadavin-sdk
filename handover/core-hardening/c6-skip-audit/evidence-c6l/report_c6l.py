"""Second half of build_c6k.py: writes REPORT-c6k.md. Executed with the edit list already built (EDITS, NUM, F, find)."""
OUT = []
P = OUT.append


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


def waits(tok):
    return [e for e in EDITS if tok in [d.strip() for d in e["dep"].split(",")] or tok in e["dep"].split(" and ") or tok == e["dep"]]


def dep_list(tok):
    out = []
    for e in EDITS:
        toks = re.split(r",| and ", e["dep"])
        if tok in [t.strip() for t in toks]:
            out.append(e["n"])
    return out


def nums(lst):
    return ", ".join(str(x) for x in lst) if lst else "none"


nready = sum(1 for e in EDITS if not e["dep"])
nwait = len(EDITS) - nready
files = sorted(set(e["fk"] for e in EDITS), key=ORDER.index)

P("# REPORT-c6k: video audit fix pass, supersedes REPORT-c6j.md (2026-11-16, UTC; IST = UTC + 5:30)")
P("")
P("## 0. Read this first (failures, uncertainty, what was not checked)")
P("- NOTHING IN THE EDIT TABLE HAS BEEN APPLIED. Every row says NOT APPLIED. %d of the %d rows are 'ready' (they rest only on a written decision of the lead or fix a plain contradiction); %d rows 'wait' for a lead answer or a check that has not run (column Status). This report changes no audited file and none of its own edits is a result: a text in the table is a proposal until a builder applies it and a reviewer reads the changed file." % (nready, len(EDITS), nwait))
P("- NONE OF THE DEFAULTS BELOW IS CONFIRMED BY THE LEAD. A default is what the edit table assumes if no answer comes. Q2 changed its default between reports (REPORT-c6h.md said keep the kill cases, labelled; c6i and this report say drop them). L-SAVE rests on one row of the re-smoke plan that says 'owner 2026-11-16' (%s), not on an answer to this report. Q10 (which owner sheet) is assumed v19 and v19 was not opened. L-DEL has no default; the edit that documents the gate (row %d) only records that the gate is closed." % (quote("PLAN", "| executions (take) |")[0], n("rs59")))
P("- Static reading only. NOT RUN: n8n, any flow, the harness, git history, the bible (rule R460: its text is not on disk), QUEUE rule 6, the lane3 reports HB171, HB180, HB186, HB189 and HB194 (only their relayed numbers and the lane3 table RES are in the tree), the owner sheets v9 to v19 (not in the checked tree, so REPORT-c6h.md's quotes of v9 are NOT verified), and the take program itself: the files scripts/run_real_check.py, scripts/run_real_check_n8n.py and scripts/hubspot_probe.py are not in the tree, so what the take does with contacts comes from their help text, the plan and two audit notes (section 6), not from code.")
P("- What the check script proves (section 7, rows C-1 and C-1b): every old text occurs exactly once on the stated line of the stated file; the %d edits can be applied in table order to copies of the files without a mismatch; every cited source line exists. It does NOT prove that a claim is true or that a new text is right. Raw output: evidence-c6k/verify-c6k-output.txt." % len(EDITS))
P("- The reviews of REPORT-c6j.md (review-c6j-design.md and review-c6j-naive.md) found it not safe to apply. This report fixes every item of both (section 8). It has NOT been reviewed again by two independent reviewers (the lead runs that step).")
P("- Where the files are: the audited files are a read-only copy of branch origin/cloud/flows-audit; checks ran against that copy (folder: scratchpad/c6/tree/handover) and nothing else names it. Every path in this report is a path inside the repository: paths under handover/demo and handover/flows-audit are on branch origin/cloud/flows-audit; paths under handover/core-hardening are on branch cloud/core-hardening (the branch this report sits on).")
P("- Does the web page carry the number 60.1 to 61.9 s? Not decided. Rows %s write the lane3 range into the page statements file with the correct counts, and rows %s withdraw it as a caption; row %d marks statement 20 'not for the web page' until the lead answers L-PAGE. The video carries no number (the lead's decision 1)." % (ids(["pg149a", "pg149b", "pg120a", "pg139"]), ids(["pg159", "pg161"]), n("pg148")))
P("- The two numbers 60.1 to 61.9 s and 52.8 to 54.9 s are different measurements of the same 18 runs: the first is seconds from the crash to the final state of the lead record, the second is seconds from n8n coming back up. REPORT-c6j.md said 52.9 to 54.9: wrong, the lane3 table row for K6 starts at 52.8 (%s). 45 s is a SETTING (the lease), not a measurement. 'Name and e-mail may appear in n8n's database' means the made-up test person only." % quote("RES", "| 873a908a-film-v4-lease45 | K6 | 3 |")[0])
P("- K3B being false in 'killed after the mail left' does not make K3 false: K3 (killed after the mail was delivered) is described correctly by mf.py. Only the K3B sentence is wrong.")
P("- Slips of the earlier report that this one corrects: the edit IDs used in its sections 1, 4, 5 and 6 did not exist in its table (section 4 here maps every old name); its gate 'execution list shows 0 rows' could never pass; its text for the closing card line 2 was an instruction, not a speakable line; it called the contact step 'a delete' although the take script archives; it put internal labels (Q9, Q11, decision 1) into new texts for the run sheet.")
P("")
P("## 1. How to use this report")
P("- ONE ID: the first column of the edit table (section 5) is the only ID. Every other section uses these numbers. Old names (rs32, pg149a, ns48, and the c6j row numbers) are mapped in section 4.")
P("- APPLY ORDER: take the rows in table order, file by file. Within one file the rows are sorted from the bottom of the file to the top, so applying them in order never shifts the line number of a row still to come. The column Line is the line number BEFORE any edit of that file. If a builder applies in another order he must find each old text by text, not by line.")
P("- Old text and new text are exact file text. '<br>' in a cell means a line break in the file. Nothing else is abbreviated. Several rows on the same line (for example the closing card line) change different pieces of text on that line.")
P("- STATUS: NOT APPLIED; ready = no open lead answer and no open check is needed to apply it. NOT APPLIED; waits for X = do not apply until X is answered or has passed (section 3 and section 7). A row that waits is still written out in full, with the default of its question, so the lead can say yes to the default.")
P("- Short names of files used in the Sources column (path inside the repository; branch as in section 0):")
P("")
P("| Short | Path inside the repository | What it is |")
P("|---|---|---|")
for k in F:
    P("| %s | %s | %s |" % (k, F[k][1], F[k][3]))
P("")
P("## 2. Numbers that look alike and are not the same")
P("")
P("| Number | What it is | Source |")
P("|---|---|---|")
for a, b, c in [
    ("60.1 to 61.9 s", "seconds from the crash (the kill) to the final state of the lead record, 18 crash runs, lease 45 s, film-v4 stand-in flows (lane3)", "RES:89 to RES:92"),
    ("52.8 to 54.9 s", "the same 18 runs, counted from n8n coming back up", "RES:89 to RES:92"),
    ("45 s", "the lease SETTING of the take: how long a claimed lead record stays reserved before the recovery flow may take it again. Not a measurement", "RS:22"),
    ("20 s and 120 s", "lease settings of older tests: 20 s for the laptop series (V7), 120 s for one lane3 run (K1, 144.3 s)", "RS:19, RS:23"),
    ("80 kills", "the older laptop series K1, K2, K3, K3B, 20 runs each, flows v3, stand-ins, lease 20 s", "RS:41"),
    ("18", "crash runs of lane3 at lease 45 s: K1 5 done, K2 5 done, K3B 5 unknown, K3 3 unknown (lane3's own names K1, K2, K3, K6)", "RES:89 to RES:92"),
    ("13 minutes (780 s)", "relayed alert delay when n8n dies during the alert send, 2 runs, lane3 v4 flows (not the flows of the video)", "RES:78, RES:79"),
    ("30 s", "how often the recovery flow runs (its timer)", "JR:%d" % find("JR", '"secondsInterval": 30')),
]:
    P("| %s | %s | %s |" % (a, b, c))
P("")
P("## 3. Lead questions (text, default used, lead has confirmed?, what a different answer changes)")
P("The edit table uses the default of each question. Nobody has confirmed any of them. A different answer means the listed rows are not applied, or are re-issued; the lead says so and a builder re-issues those rows. No row contains two choices. Q3 to Q8 of REPORT-c6h.md (who runs the re-smoke, role tests, S1b, flow activation time, owner step 0, proof screenshot) touch no edit here and are not repeated. The names Q1, Q2, Q9, Q10 keep their numbers from REPORT-c6h.md; Q11 is answered (see its row); the names starting with L- are new.")
P("")
P("| Question | Text of the question | Default used | Confirmed by the lead? | If the lead answers differently | Rows that wait for it |")
P("|---|---|---|---|---|---|")
P("| Q1 | Does the closing card (scene 12, the last card of the video, run sheet line 41) stay as the last card? | Yes, it stays; its old lines 2 and 3 (the 80 kills and the recovery time) are cut and it gets four spoken lines. | No | If the card is cut: every row that waits for Q1 is dropped (the card rows); nothing else changes. | %s |" % nums(dep_list("Q1")))
P("| Q2 | Scene 4 (the crash and the recovery): (a) leave the kill-case words out of scene 4, or (b) keep them, labelled as a stand-in test on film-v4 flows? | (a). REPORT-c6h.md gave (b) as default; (a) is used because the lead's decision 8 allows no extra real-account test run and the old K3B sentence is false as written. | No | If (b): row %d is re-issued and says, in place of the sentence about K3B and K3: 'Stand-in test, film-v4 flows: n8n killed while the mail connection was opening, the mail was not delivered: the lead ends unknown with one alert to the owner. Stand-in test, film-v4 flows: n8n killed after the mail was delivered: the lead ends unknown with one alert to the owner.' | %s |" % (n("rs90"), nums(dep_list("Q2"))))
P("| Q9 | May scene 4 and the page use the rounded wording 'about a minute, in the test' in place of the cut number? | No. No timing number and no rounded timing wording anywhere in the video text; the lead's decision 1 already cuts the number. | No | If yes: the lead names the exact caption; rows that wait for Q9 are re-issued with it. | %s |" % nums(dep_list("Q9")))
P("| Q10 | Which owner sheet does the owner read? | v19 (the newest; it says it replaces v4 to v18). Not opened here. | No | If another: the closing check C-10c is run on that sheet. No row touches an owner sheet. | none (check C-10c) |")
P("| Q11 | Which claim wording is in force? | Answered by the lead at ORD:%d (the lead's answer Q21.2): the claim 'a lead sent twice with the same id is processed once' plus one honest sentence on the lease. What is open is the exact sentence, see L-LEASE. | Yes for the choice; no for the sentence | not applicable | see L-LEASE |" % find("ORD", "Q21.2:"))
P("| L-LEASE | The lead said (ORD:%d) 'a gap longer than the lease is not claimed'. May the caption and the card say: 'Not claimed: a second send after a gap longer than the lease, the 45 seconds for which a lead stays reserved to its first run.'? | Yes, that sentence (rows %s). | No | The lead gives the sentence; those rows are re-issued with it. | %s |" % (find("ORD", "Q21.2:"), ids(["rs32", "rs41b"]), nums(dep_list("L-LEASE"))))
P("| L-DEL | The take script ARCHIVES the made-up contacts it created (moves them to the CRM recycle bin) and the probe script tries a permanent delete first, but the lead's decision 2 says the take never deletes contacts. Choose (a) change the program so that the take neither archives nor deletes (the owner removes leftover contacts by hand, as decision 2 says), or (b) change decision 2 and every owner sheet to say: the take archives only its own made-up contacts at the end and never permanently deletes. | NO DEFAULT. The gate (row %d) is closed until the lead chooses. My recommendation: (a), because decision 2 is the lead's written decision and the script was not read here; (b) is the smaller change if the archive step is wanted. | No | After the answer, new rows (the decisions file line 3, the owner sheet, and for (a) a program change) are issued by the next report. | none (the gate row only records that the gate is closed) |" % n("rs59"))
P("| L-SAVE | Does the take really save every run (EXECUTIONS_DATA_SAVE_ON_SUCCESS=all and ON_ERROR=all), so that the execution list filmed in scenes 1 and 2 shows runs? | Yes (the plan's row says 'owner 2026-11-16'). | No | If no: rows that wait for L-SAVE are dropped and the execution list in scenes 1 and 2 stays empty (scene 1 text then needs a rewrite, which this report does not contain). | %s |" % nums(dep_list("L-SAVE")))
P("| L-PAGE | May the web page of the one video carry the lane3 range 60.1 to 61.9 s (for film-v4 stand-in flows, as a labelled statement, never as a caption)? | No. Statement 20 stays in the statements file, marked not for the web page. | No | If yes: row %d is dropped and the statement is published with its Tag. | %s |" % (n("pg148"), nums(dep_list("L-PAGE"))))
P("| L-ONEDB | Ratify or veto the interim sentence for any text written before the re-smoke has passed: 'n8n keeps its own records in its own database file. Our claim table is in a separate Postgres database. That is two stores.' (ORD:%d requires the caption 'one Postgres server, two databases' only once that is true.) | The target wording of the lead's decision 10 goes into DECISION-one-store.md as a target (rows %s); viewer-facing text uses only the interim sentence until check C-8 passes. | No | If vetoed: the interim sentence is not used and no viewer-facing text says anything about the number of databases until C-8 passes. | %s |" % (find("ORD", "Q21.3:"), ids(["one13", "one14", "one16"]), nums(dep_list("L-ONEDB"))))
P("| L-CUT | Scenes 5 to 11 (run sheet lines 34 to 40) are cut from the one video but their rows still hold stale text (K3 and K3B history, V7 numbers). Mark each row 'not in the one video'? | No edit now (they are not filmed). | No | If yes: a new row per scene is issued. | none |")
P("")
P("## 4. Plain-word glossary (term, meaning, where it comes from)")
P("")
P("| Term | Plain meaning | Where it comes from |")
P("|---|---|---|")
G = [
    ("the lead (the studio lead)", "the person who decides for the studio. 'A lead record' (below) is a sales contact; the two are never the same. The owner is the person who runs the take by typing; the lead prepares and supervises.", "H6:53"),
    ("the take", "the one filmed run of the video.", "H6:86"),
    ("run sheet", "VIDEO-RUNSHEET.md, the scene-by-scene script. Scenes are its numbered rows 1 to 12.", "RS:28"),
    ("page", "PAGE-STATEMENTS-V4.md, the text for the web page that goes with the video (statements 1 to 20).", "H6:363"),
    ("closing card", "scene 12, the last on-screen card; its text is one table row, run sheet line 41.", "RS:41"),
    ("decision 1, 2, 8, 10", "the lead's decisions of 2026-11-16 (DECISIONS-2026-11-16.md). 1: the one video is real-v5 only, scenes 1 to 4, and the number 60.1 to 61.9 s is cut. 2: the take never deletes contacts. 8: no extra real-account test run. 10: the wording 'one Postgres server with two databases'.", "DEC:2, DEC:3, DEC:9, DEC:11"),
    ("real-v5", "the n8n flow set in folder n8n-flows-real-v5 that talks to the real mail and CRM services; the only set in the one video. Four files: mf-form (form entry), mf-hook (hook entry), mf-recovery (the recovery flow, every 30 s), mf-sub-crm-mail (a shared step that writes the CRM and sends the mail, called by the entries).", "H6:87"),
    ("entry flows", "mf-form and mf-hook: the two flows that receive a lead by a web address (webhook) on this computer only.", "NS:33"),
    ("recovery flow", "mf-recovery: it wakes every 30 seconds, looks at the lead table and finishes or alerts on lead records that were interrupted. Also called the recovery sweep.", "NS:33"),
    ("film-v4, film-v5", "flow sets that talk to stand-in services; their scenes (5 to 11) are a possible later video. film-v5 differs from real-v5 only in the files mf-recovery.json and mf-sub-crm-mail.json.", "H6:88, EV1:15"),
    ("stand-in", "a fake service we control (fake CRM, fake mail server, fake model) used instead of the real one.", "H6:88"),
    ("loopback", "the address that points to this computer itself, so nothing outside can reach it.", "NS:33"),
    ("loopback re-smoke", "a short repeat test of the whole setup on this computer only, with fake services, run by the lead before the first rehearsal.", "DEC:9"),
    ("rehearsal", "a practice run of the take before the real take.", "DEC:13"),
    ("handoff", "the lead's session note (handoff folder) where facts such as the list of active workflows are written down.", "RS:71"),
    ("lane3", "the separate test session and git branch (origin/demo/lane3) that ran the 45-second-lease crash tests; its results table is RES.", "H6:63"),
    ("HB171, HB180, HB186, HB189, HB194", "numbers of lane3 reports relayed to the demo session by the lead; the files do not say what HB stands for. HB189: alert may be late; HB194: the 18 crash runs at lease 45 s.", "NS:42, RS:82, PG:148"),
    ("lease", "how long a claimed lead record stays reserved before the recovery flow may take it again. The take uses 45 s; older tests used 20 s and 120 s. A setting, not a measurement.", "H6:89"),
    ("lead record, lead id, claim table, claim", "one made-up sales contact the flows process; its identifier; the database table (mf_leads) with one row per lead id; the claim is the row the flow writes first so that no second run takes the same lead. The unique index is the database rule that refuses a second row with the same lead id.", "H6:53, ORD:151"),
    ("alert", "the one mail the system sends to a named address when it cannot tell what happened to a lead record.", "H6:90"),
    ("intake mailbox", "the (made-up) mailbox that receives the lead mail; 'intake got 1 mail' means one mail reached it.", "RS:30"),
    ("end state unknown", "final state of a lead record when the program cannot tell whether the contact and mail happened; a person decides.", "H6:91"),
    ("K1", "crash test: n8n killed after the claim insert, before the CRM write.", "MF:151, RS:33"),
    ("K2", "crash test: n8n killed after the CRM write, before the mail step.", "MF:152"),
    ("K3B (lane3 name K3)", "crash test: n8n killed while the mail connection was opening; the mail was NOT delivered (intake got 0 mails in 5 of 5 runs); end state unknown, one alert.", "MF:153, RES:97"),
    ("K3 (lane3 name K6)", "crash test: n8n killed after the mail was delivered, before the table update; intake got 1 mail (3 of 3 runs); end state unknown, one alert.", "MF:159, PG:150"),
    ("T7b", "a privacy test in mf.py (function t7b): plants a fake model key, a fake mail password, a name and an e-mail, runs leads and searches stores for them. Today it forces execution saving off.", "MF:274"),
    ("saving off, saving all", "the n8n settings EXECUTIONS_DATA_SAVE_ON_SUCCESS and _ON_ERROR: none = n8n keeps no run data; all = it keeps every run (what the execution list shows). The take uses all.", "PLAN:125"),
    ("execution list", "n8n's screen listing past runs; filmed in scenes 1 and 2.", "RS:4"),
    ("stage, stage journal, spend ledger", "the stage is the program step that asks the model to qualify a lead; its journal records a model call before it is made (file stage-journal.jsonl); the spend ledger records the money spent (it exists; its path comes from the take's config and was not found in any file read).", "MF:12"),
    ("write-ahead file", "the database's log file (the -wal file) where recent writes sit before they reach the main file.", "NS:40"),
    ("sub-flow", "mf-sub-crm-mail, a flow that other flows call (n8n calls this a sub-workflow).", "JS:%d" % find("JS", "Execute Workflow Trigger") if any("Execute Workflow Trigger" in l for l in lines("JS")) else "H6:87"),
    ("table screen", "an n8n page that shows the lead table; BUILT, NOT RUN; the lead's decision 9 replaces it by a rehearsal screenshot.", "RS:50, DEC:10"),
    ("older review, c6i and c6j reviews", "review-design.md (items M1 to M3, N1 to N6, m1 to m4: older review); review-c6i-design.md and review-c6i-naive.md (reviews of REPORT-c6i.md); review-c6j-design.md (design review: items M1 to M7, m1 to m8) and review-c6j-naive.md (naive-reader review: items B1, M1 to M6, minors). In this report they are called 'older review', 'c6i review', 'design review' and 'naive review'.", "RDES:6, DD:1, DN:1"),
    ("F-006, F-007, F-011, F-020, F-022, F-023, F-025", "numbered findings in FINDINGS.md: F-006 run sheet claims real CRM in scene 5; F-007 K3/K3B described three ways; F-011 'one database' / n8n keeps run history; F-020 stage journal owner; F-022 the stage returns a web error (502) on the desk door; F-023 table screen README conflict; F-025 old flows can double-mail.", "FND:91, FND:92, FND:97, FND:114, FND:116, FND:99, FND:118"),
    ("c6b to c6k", "successive versions of this audit report; c6k (this file) supersedes c6j; c6h is the last full report (REPORT-c6h.md).", "H6:1"),
    ("D2, G-7, G-4", "row D2 of REPORT-c6h.md: decision 2 against the code that touches contacts; G-7 and G-4 are gates in its gate list (G-4: only real-v5 imported and active).", "H6:262"),
    ("UNBACKED, RELAYED-INDEPENDENT, MEASURED-ON-LAPTOP", "tags on numbers: no raw file / relayed from another session without the raw file / read by the lead from laptop result files.", "RS:18, RS:19"),
    ("V7", "laptop result files and the lead's read of them (V7-NUMBERS-lead-read.md) behind the '80 kills' numbers, measured on older v3 flows with a 20 s lease on stand-ins.", "H6:387"),
    ("T13, T15, B90, AF1", "earlier test names in the run sheet history lines (T13 same-id and database kill, T15 CRM refuses, B90 alert-send case, AF1 alert refused twice); not used by any edit here.", "RS:32"),
    ("Q21.2, Q21.3, Q15.3", "lead answers in ORDERS.md and an earlier order: the claim wording and the lease sentence (Q21.2), the caption for the number of databases (Q21.3).", "ORD:151, ORD:152, H6:106"),
    ("R460, QUEUE rule 6", "rules behind the audit and the lead's queue; their text is not on disk (not checked).", "H6:390"),
]
for t, m, s in G:
    P("| %s | %s | %s |" % (t, m, s))
P("")

# ---------------------------------------------------------------- ID map
ALIAS = {"rs4": ["rs4"], "rs5a": ["rs5a"], "rs5b": ["rs5b"], "rs14": ["rs14"], "rs23": ["rs23a"], "rs24": ["rs24"], "rs30": ["rs30a"], "rs31": ["rs31"],
         "rs32": ["rs32"], "rs33a": ["rs33a"], "rs33b": ["rs33b"], "rs33c": ["rs33c"], "rs33d": ["rs33d"], "rs41a": ["rs41a"], "rs41b": ["rs41b"], "rs41c": ["rs41c"],
         "rs59": ["rs59"], "rs71": ["rs71"], "rs79": ["rs79"], "rs90": ["rs90"], "pg17": ["pg120a"], "pg139": ["pg139"], "pg149a": ["pg149a"], "pg149b": ["pg149b"],
         "pg150": ["pg150"], "pg153": ["pg153"], "pg159": ["pg159"], "pg161": ["pg161"], "ns15": ["ns15"], "ns17": ["ns17"], "ns18": ["ns18"], "ns23": ["ns23"],
         "ns24": ["ns24"], "ns27": ["ns27"], "ns48": ["ns48"], "mf276": ["mf276"], "one14": ["one14"]}
for fk in ("JF", "JH", "JR", "JS"):
    for w in ("Success", "Error"):
        ALIAS["j_%s_saveData%sExecution" % (fk, w)] = ["j%s%s" % (fk, w)]
OLDJ = json.load(open(C6 + "/evidence-c6j/edits.json"))
P("## 5. EDIT TABLE (every row: NOT APPLIED)")
P("Rows are in apply order (section 1). Paths are paths inside the repository (section 0). Column 'Was' gives the name and row number the same edit had in REPORT-c6j.md ('new' = no such row there). Sources use the short names of section 1.")
P("")
P("| ID | Status | Target file (path inside the repository) | Line before any edit | Old text (exact) | New text (exact) | Reason and source file:line | Was (c6j) |")
P("|---|---|---|---|---|---|---|---|")
was = {}
for o in OLDJ:
    for nk in ALIAS.get(o["key"], []):
        was.setdefault(nk, []).append("%s / row %d" % (o["key"], o["n"]))
for e in EDITS:
    status = "NOT APPLIED; ready" if not e["dep"] else "NOT APPLIED; waits for " + e["dep"]
    P("| %d | %s | %s | %d | `%s` | `%s` | %s Sources: %s | %s |" % (e["n"], status, F[e["fk"]][1], e["line"], cell(e["old"]), cell(e["new"]), e["why"], e["src"], "; ".join(was.get(e["key"], ["new"]))))
P("")
P("Old names mapped to the ID (section 5 sentence: every other section uses the ID only):")
P("")
P("| Old name (c6j or c6i) | ID(s) now |")
P("|---|---|")
for o in OLDJ:
    P("| %s (c6j row %d) | %s |" % (o["key"], o["n"], ids(ALIAS[o["key"]])))
P("| rs41a to rs41c, 'the three closing-card edits' | %s |" % ids(["rs41a", "rs41b", "rs41c"]))
P("| ns15 to ns27 (execution saving edits) | %s |" % ids(["ns15", "ns17", "ns18", "ns23", "ns24", "ns27"]))
P("| 'flow-file edits' | %s |" % ids(["jJFSuccess", "jJFError", "jJHSuccess", "jJHError", "jJRSuccess", "jJRError", "jJSSuccess", "jJSError"]))
P("")

# ---------------------------------------------------------------- deletion gate
P("## 6. The contact gate in detail (archive or permanent delete; every cite below was opened)")
P("Words: ARCHIVE = HubSpot moves the contact to its recycle bin (it can be restored). PERMANENT DELETE = the contact is erased. The lead's decision 2 (%s) says 'the take never deletes contacts; leftover made-up contacts are listed by lead key and contact id and the owner deletes them by hand in HubSpot after the take'." % quote("DEC", "2. TAKE IDENTITY")[0])
P("")
P("| What the files say | Cite (opened) | Text at the cite |")
P("|---|---|---|")
for lab, k, a in [
    ("The take script has an option that archives the contacts the run made", "EQ4", "--cleanup"),
    ("Plan 4: up to 3 contacts archived at the end", "P4", "up to 3 HubSpot contacts archived at the end"),
    ("Plan 4: the person types end and the script archives", "P4", "Film the contact list now"),
    ("Plan 4: archives also when the take ends in an error; leftovers are listed and the owner deletes them in the HubSpot screen", "P4", "1. the script archives this take's contacts"),
    ("The probe script: the code TRIES (docstring said 'always deletes')", "CA", "scripts/hubspot_probe.py:4-5"),
    ("The probe script tries a permanent delete first, then an archive delete; if both fail it warns", "CB", "hubspot_probe.py:271-287"),
    ("Whether an archived contact keeps its e-mail address reserved is an ASSUMPTION, never checked", "SH", "ASSUMED to keep its email reserved"),
]:
    c, t = quote(k, a)
    P("| %s | %s | %s |" % (lab, c, t))
P("")
P("Checked by reading the four real-v5 flow files (command and output: evidence-c6k/contact-grep-output.txt): they contain no DELETE call and no archive call (0 hits). So the only places that touch contacts are the take script and the probe script, and those files are not in the tree.")
P("")
P("The gate (run sheet row %d, item 11) therefore says: the program ARCHIVES, it does not permanently delete (the take script), the probe script may permanently delete, the lead decides (a) or (b) of L-DEL, and no sheet says never deletes until then. The closing check is C-10 (section 7); it has three parts and none can be run from the tree." % n("rs59"))
P("")

# ---------------------------------------------------------------- ratings, checks
P("## 7. Ratings and checks (not edits)")
P("")
P("| Item | Rating | Basis |")
P("|---|---|---|")
P("| F-006 | Major (the finding said Blocker) | closed by the lead's decision 1 once rows %s are applied; RDES:%d |" % (ids(["rs4", "rs90"]), find("RDES", "F-006 Major accepted")))
P("| F-007 | Major | three sources disagree; fixed by rows %s; MF:%d |" % (ids(["rs24", "rs36", "pg150", "pg153", "rs90"]), find("MF", "def k3b")))
P("| F-011 | Major | rows %s plus checks C-8 and C-6 |" % ids(["one13", "one14", "one16", "ns4a", "ns4b"]))
P("| F-020, F-022, F-023, F-025 | Nit | accepted by the older review; F-022: real-v5 mf-form.json sets n8n_error false at lines 238, 254, 293 so the bug does not recur in the take flows |")
P("| N1 (stale flow folders share webhook paths) | Major, operational | row %d and check C-3 |" % n("rs71"))
P("| N2 (execution list empty because flows save nothing) | Major for filming, gate | rows %s, check C-4 |" % ids(["jJFSuccess", "jJFError", "jJHSuccess", "jJHError", "jJRSuccess", "jJRError", "jJSSuccess", "jJSError", "rs30a"]))
P("| N5 (closing card says 80 kills) | Nit | rows %s |" % ids(["rs41a", "rs41b", "rs41c"]))
P("")
P("| Check | What | Needs | Status |")
P("|---|---|---|---|")
P("| C-1 | Every old text of section 5 occurs once on its line | file read | DONE: evidence-c6k/verify-c6k-output.txt |")
P("| C-1b | All rows applied in table order to COPIES of the files without a mismatch; no internal label or banned string in a new text | file read | DONE: same file |")
P("| C-2 | The 8 flow files all carry none, none, false and no errorWorkflow | file read | DONE (static): EV:%d to EV:%d |" % (find("EV", "n8n-flows-real-v5/mf-form.json"), find("EV", "n8n-flows-film-v5/mf-recovery.json") if any("n8n-flows-film-v5/mf-recovery.json" in l for l in lines("EV")) else find("EV", "n8n-flows-real-v5/mf-sub-crm-mail.json")))
P("| C-3 | Only real-v5 flows are active before each scene (list active workflows) | n8n | NOT RUN |")
P("| C-4 | Import the four edited real-v5 files and see one run in the execution list; the file hashes have changed, so repeat | n8n | NOT RUN |")
P("| C-5 | Execution list: no row from before the start of the take and no row with rehearsal data, before scene 1 and again before scene 2 (recovery-flow rows are expected; this is a screen check, not an erasure) | n8n | NOT RUN |")
P("| C-6 | Leak scan for the take (N8N-START.md section added by row %d): case 1, case 2 and the name and e-mail rule on six stores, loopback stand-ins only | built scan, n8n | NOT RUN, scan not built |" % n("ns48"))
P("| C-7 | real-v5 and film-v5 differ only in mf-recovery.json and mf-sub-crm-mail.json | file read | DONE (static): EV1:%d to EV1:%d; whether the import reads only the .json files (V5-NODE-DIFF.txt sits in the folder): NOT RUN |" % (find("EV1", "film-v5") , find("EV1", "film-v5") + 4))
P("| C-8 | Loopback re-smoke shows that n8n's engine is Postgres, before any text says one Postgres server with two databases (the lead's decision 10) | n8n, Postgres | NOT RUN |")
P("| C-9 | GATE on the repeat-send claim (scene 3 and card line 1): the unique index on the claim table is seen in the table definition or in the re-smoke result; if it cannot be seen, say 'index not seen' (ORD:%d) | table definition | NOT RUN here |" % find("ORD", "Q21.2:"))
P("| C-10a | Real-v5 flows contain no delete or archive call: grep -il -E 'DELETE|archive' on the four files | file read | DONE: 0 hits (evidence-c6k/contact-grep-output.txt) |")
P("| C-10b | Take script and probe script: grep -n -E 'archive_all|archive|delete' scripts/run_real_check.py scripts/run_real_check_n8n.py scripts/hubspot_probe.py; for L-DEL (a) the take script must show no archive or delete call; for (b) the calls must be archive only, own contacts only | the scripts | NOT RUN, scripts not in the tree |")
P("| C-10c | The owner sheet named in Q10: grep -n -i -E 'never deletes|read, create and change only|does not delete' sheet; 0 hits required, and the sheet must say what the take does with its made-up contacts as the lead chose | the sheet | NOT RUN, sheet not in the tree |")
P("| C-10d | The lead's decisions file: the same grep on DECISIONS-2026-11-16.md. Today line 3 matches (it says never deletes), so this check fails until the lead's choice is written there | file read | KNOWN FAIL (expected: waits for L-DEL) |")
P("")

# ---------------------------------------------------------------- coverage
P("## 8. Coverage: finding -> fix -> check (every item of the design review and the naive review)")
P("")
P("| Review item | Fix (row IDs) | Check |")
P("|---|---|---|")
COV = [
    ("Design M1: 'execution list shows 0 rows' cannot pass (recovery flow refills it; delete only hides)", ["rs30a", "rs30b", "rs71"], "C-5 reworded; C-4"),
    ("Design M2: closing card line 1 keeps the claim without the lease sentence", ["rs41b"], "check C-9; reading of the new card"),
    ("Design M3: scene 3 caption invented wording; unique index not seen; resend outside the lease", ["rs32", "rs41b", "rs59", "rs71"], "C-9 is now a gate (risk item 12); rehearsal item 14"),
    ("Design M4: card line 2 not speakable; line 82 contradicts", ["rs41b", "rs82"], "reading of the new card (four speakable lines)"),
    ("Design M5: contact gate has no check row, says delete not archive, false 'never deletes' remains", ["rs59", "rs71"], "section 6; C-10a (DONE), C-10b, C-10c, C-10d"),
    ("Design M6: N8N-START.md lines 38 to 48 and page statement 18 become false", ["ns43", "ns45", "pg125", "ns27"], "C-1b (apply simulation); stale phrase search in verify output"),
    ("Design M7: T7b for the take: stand-ins only, expectation not result, scan lines, mf.py line 320", ["ns48", "mf276", "mf320"], "C-6"),
    ("Design m1: from-n8n-up range is 52.8 to 54.9", ["pg154", "rs90"], "section 0 and section 2 (RES:89 to RES:92)"),
    ("Design m2: run sheet line 36 old K3 meaning; K3B undefined", ["rs36", "rs24"], "stale phrase search"),
    ("Design m3: garbled sentence on line 5; 70 to 75 s left on line 23", ["rs5a", "rs23b"], "reading of the new sentences"),
    ("Design m4: stale lines 22, 44, 45, 47, 51, 70, 80, 85", ["rs22", "rs44", "rs47", "rs51", "rs70", "rs80", "rs85"], "stale phrase search"),
    ("Design m5: page lines 23, statement 14, 17, 19, line 156", ["pg23", "pg105", "pg120a", "pg120b", "pg134", "pg156"], "stale phrase search"),
    ("Design m6: 'no number on screen' yet a label is shown", ["rs33a", "rs90"], "wording now 'no timing number'"),
    ("Design m7: target not true until C-8; N8N-START line 4 says SQLite", ["one13", "one14", "one16", "ns4a", "ns4b"], "C-8"),
    ("Design m8: page statement 20 keeps the number; ledger 'not found' overstated", ["pg148", "ns48"], "L-PAGE; ns48 says the ledger exists and its path comes from config"),
    ("Naive B1: edit IDs in later sections do not exist", ["rs4"], "one ID column; section 5 column 'Was' and the old-name table"),
    ("Naive M1: paths point into a scratchpad copy", ["rs4"], "every path is now a path inside the repository (section 0 and section 1)"),
    ("Naive M2: line numbers shift when rows are applied", ["rs4"], "rows sorted bottom-up per file; check C-1b applies them in table order"),
    ("Naive M3: 'NOT APPLIED' can be misread; no depends-on column", ["rs4"], "column Status: ready or waits for X; section 3 last column"),
    ("Naive M4: page may or may not carry 60.1 to 61.9 s", ["pg148"], "one sentence in section 0; question L-PAGE"),
    ("Naive M5: defaults written as settled", ["rs4"], "section 0 second bullet; column 'Confirmed by the lead?' in section 3"),
    ("Naive M6: internal labels in new text", ["rs32", "rs71", "rs41b", "rs90", "ns48"], "C-1b scans every new text for labels such as Q9, L-SAVE, decision numbers, report names"),
    ("Naive minors: colliding names, numbers, short names used before they are defined, EV against EV1, dropped card line 4, ORDERS.md:152", ["rs41b"], "sections 1, 2, 4; row rs41b reason names the dropped content; L-ONEDB cites ORD:152"),
    ("Naive: unexplained labels", ["rs4"], "section 4 (claim table, unique index, recovery flow, intake mailbox, desk door 502, table screen, entry flows, sub-flow, loopback re-smoke, handoff, owner against lead, HB, scenes, Q series, R460)"),
    ("Naive: question wording (Q1, Q9 targets; Q2(b) sentence; Q11 sentences; Q3 to Q8 gap)", ["rs4"], "section 3"),
]
for a, b, c in COV:
    P("| %s | %s | %s |" % (a, ids(b) if b != ["rs4"] else "see check column", c))
P("")
P("## 9. Not covered here (each with the exact next step)")
P("- Owner sheets (steps-edits v9 to v19) are not in the checked tree: the lines REPORT-c6h.md quotes for 'never deletes' (v9 :18, :40, :169, :285, :288) are not verified and not edited. Next step: after the lead answers L-DEL, a builder opens the sheet named in Q10 and issues rows for those lines; check C-10c closes it.")
P("- The decisions file line 3 (DECISIONS-2026-11-16.md, decision 2) still says the take never deletes; it is the lead's own file and no row edits it. Next step: the lead rewrites it with his answer to L-DEL (check C-10d).")
P("- Scenes 5 to 11 rows (run sheet lines 34 to 40): question L-CUT.")
P("- plan-wp6-resmoke-v5.md still names film-v5 at the lines listed in REPORT-c6h.md section 4; not repeated here.")
P("- The stage's spend ledger path was not found in any file read; the leak scan needs it (row %d). Next step: the builder takes it from the take's config." % n("ns48"))
P("- Run sheet lines 30 and 52 still say 'the request body stays in n8n data until pruned'; that stays true with saving all (the node data is kept too), so they are left.")
P("- Whether deleting an execution in the n8n screen only hides it: UNVERIFIED here (N8N-START.md lines 42 and 47 describe hiding then pruning); check C-5 is a screen check and says so.")
open(C6 + "/REPORT-c6k.md", "w").write("\n".join(OUT) + "\n")
print("report lines", len(OUT))
