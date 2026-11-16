"""Writes SWEEP.md and ONE-PLACE-TABLE.md from work/merged-findings.md and work/L6.md (PLAN-002 5.2, 5.3). Usage: python3 tools/write_outputs.py <dir>"""
import re, sys, os
base = sys.argv[1]
fl = [l for l in open(os.path.join(base, "work/merged-findings.md"), encoding="utf-8") if l.startswith("| ") and not l.startswith("| id ")]
cnt = {}
for l in fl:
    c = [x.strip() for x in l.strip().strip("|").split(" | ")]
    cnt[(c[1], c[2])] = cnt.get((c[1], c[2]), 0) + 1
types = sorted({k[0] for k in cnt})
sevs = ["Blocker", "Major", "Nit"]
counts = ["| claim type | Blocker | Major | Nit | total |", "|---|---|---|---|---|"]
for t in types:
    counts.append("| %s | %s | %d |" % (t, " | ".join(str(cnt.get((t, s), 0)) for s in sevs), sum(cnt.get((t, s), 0) for s in sevs)))
counts.append("| all | %s | %d |" % (" | ".join(str(sum(cnt.get((t, s), 0) for t in types)) for s in sevs), len(fl)))
EX = [
 ("L6-EX-01", "n8n internal data (workflows, credentials, execution history)", "second of the three stores DECISION keeps; must run on Postgres, but every kill run used SQLite", "lead", "n8n data moved to the one Postgres (DECISION line 14)", "DECISION line 14"),
 ("L6-EX-02", "stage.journal file (model-call write-ahead money guard)", "the one stated exception in DECISION; real file NOT VISIBLE: qualify_stage.py", "lead", "after the video, core store-kind item (DECISION line 17)", "DECISION line 17"),
 ("L6-EX-03", "HubSpot (CRM) and Gmail", "client systems of record; the take writes to them, the independent count reads them", "client", "none: external systems", "DECISION line 11"),
 ("L6-EX-04", "process output files (n8n.out, stage stdout)", "diagnostics with no lead data; not stores", "lead", "none while no lead data is written there", "DECISION line 10"),
 ("L6-EX-05", "mf_leads lifecycle rows as the audit half of the log", "DECISION says logs live in Postgres: n8n history plus these rows", "lead", "none", "DECISION line 16"),
 ("L6-EX-06", "shape check node (Valid regex) in the entry flow", "cheap check before the Claim insert; same flow", "lead", "none", "DECISION line 7"),
 ("L6-EX-07", "alert claim and backoff as helper of the recovery sweep", "stops a second alert for the same lead", "lead", "if the sweep gets a second channel, re-check", "DECISION line 7"),
 ("L6-EX-08", "lead intake mail inside the sub-workflow", "a notice to the lead of the client, not to our person", "client", "none", "DECISION line 11"),
 ("L6-EX-09", "proof screens for the video (n8n executions)", "DECISION names these as the screens shown", "lead", "after the video", "DECISION line 18"),
]
fix = [
 (1, "L6-FD-001, L2-FD-001", "move n8n data to the one Postgres and re-run the kill tests on it (needs a runtime)", "lead", "no"),
 (2, "L6-FD-002", "turn on execution saving in the four flows so the log exists in Postgres", "lead", "no"),
 (3, "L6-FD-003, L6-FD-004", "name stage.journal as the one money counter; archive the other five counters; make the rig use the real journal", "lead", "yes"),
 (4, "L6-FD-005", "give the alert mail a channel apart from the lead mail (second SMTP server or second channel)", "lead", "yes"),
 (5, "L6-FD-006", "three least-privilege Postgres roles (n8n, app, read-only count) in place of one shared credential", "lead", "no"),
 (6, "L1c-FD-021, L1-FD-023", "correct the three live pull request bodies (final tree is NOT identical to PR #1; 95 files differ)", "lead", "yes"),
 (7, "all DUPLICATE rows with CONFLICT WITH DECISION line 15", "ARCHIVE the desk, its portal and retry loops after the owner says yes (never delete); stop building and reviewing them", "lead", "yes"),
 (8, "L6-FD-019", "reconcile the test counts before quoting any number", "lead", "no"),
 (9, "all Major findings", "work through by claim type: duplicate, then dead, then idle, then inconsistent (file ids in the Findings table)", "lead", "no"),
]
claims = [
 ("the final tree of PRs 2 to 4 is identical to PR #1", "handover/demo/pr-text/github-current/pr3-body.md:5", "VERIFY.md measured 95 files differing (L1c-FD-021)", "CONTRADICTED"),
 ("SonarQube runs on every pull request", "pr4 text v5", "AB-PAPER shows 0 SonarQube jobs since 0841f36 (L1c-FD-002)", "CONTRADICTED"),
 ("n8n runs on Postgres in the take", "DECISION-one-store.md line 14", "kill harness used the default SQLite file in every run (L2-FD-001)", "CONTRADICTED for the kill runs; the take itself UNVERIFIED"),
 ("execution history is saved in Postgres", "DECISION-one-store.md line 16", "the four flows set execution saving to none (L6-FD-002)", "CONTRADICTED"),
 ("the kill tests prove the money guard", "kill RESULTS", "model_calls=1 is counted from an in-memory fake journal (L6-FD-004)", "UNVERIFIED"),
 ("the DeepSource carry-over holds about 96 distinct findings among 213 comments", "L1c-FD-003", "counted by block, rows not compared one by one", "UNVERIFIED"),
 ("test totals quoted across the lanes (2329, 3138, 4125, 4409 and others)", "L1, L2c, L3, L4", "no lane reconciles them (L6-FD-019)", "UNVERIFIED"),
 ("every file under handover/ was read", "lane Coverage tables", "L1c 18, L3c 66 and L4c 99 files NOT-READ", "CONTRADICTED: see Exceptions note below"),
]
out = ["# SWEEP: duplicates, dead, idle, inconsistent and unverified parts", "",
 "Static review of the repo on branch cloud/system-map. No n8n runtime, no network: anything needing a runtime is UNVERIFIED. The take code repo `duplicate-proof-lead-desk` is NOT VISIBLE here (lead covers locally); every NOT-NEEDED verdict is UNVERIFIED for the take repo. Severity: Blocker = contradicts DECISION-one-store.md, or touches money, credentials, mail or personal data, or a claim that is false; Major = duplicate, dead or idle part or inconsistency that costs time; Nit = wording or tidiness. Severity is the lane's candidate until the result review.", "",
 "## Findings", "", "All lane finding rows, severity-sorted (source: work/merged-findings.md). Some findings are counted twice by two lanes (for example L2-FD-001 and L2c-FD-010; L4-FD-003 and L4c-FD-011; L4-FD-005 and L4c-FD-012); counts below are raw row counts.", ""]
out += ["| id | claim type | severity | evidence | conflicts with | job key |", "|---|---|---|---|---|---|"] + [l.rstrip("\n") for l in fl] + [""]
out += ["## Fix plan", "", "| order | finding ids | action | owner | needs owner yes |", "|---|---|---|---|---|"]
out += ["| %d | %s | %s | %s | %s |" % r for r in fix] + [""]
out += ["## Exceptions", "", "| id | what | reason | owner | removal trigger | decision line |", "|---|---|---|---|---|---|"]
out += ["| " + " | ".join(r) + " |" for r in EX]
out += ["", "Open NOT-READ lists (not reported as clean): L1c 18 files (pr2, pr3, pr4 text v1 to v4; Semgrep bodies v1 to v5; semgrep-pr-claims.md lines 31 to 76), L3c 66 evidence files, L4c 99 report files (see the Coverage tables in work/L3c.md and work/L4c.md). The laptop lead can order one more continuation lane, or accept them: these folders describe the retired desk and the files read there mention no mf_leads, stage.journal or n8n data.", ""]
out += ["## Claims check", "", "| claim | where claimed | evidence | status |", "|---|---|---|---|"] + ["| " + " | ".join(r) + " |" for r in claims] + [""]
out += ["## Lessons", "",
 "- Checklist: add a line to check the engine behind every test number (SQLite versus Postgres) before quoting it.",
 "- Memory: one name per file; the desk money file has four names across lanes.",
 "- Brief preamble: ban unbounded wait loops in test rigs; require every quoted test count to name its commit.",
 "- Lane method: a lane that reads about 100 files runs out of context; cap lanes at about 60 files and keep a READ status honest.", "",
 "## Counts", ""] + counts + [""]
open(os.path.join(base, "SWEEP.md"), "w").write("\n".join(out))

# ONE-PLACE-TABLE
rows = {}
for l in open(os.path.join(base, "work/L6.md"), encoding="utf-8"):
    m = re.match(r"\| (L6-J-(\d+)) \|", l)
    if m:
        c = [x.strip() for x in l.strip().strip("|").split(" | ")]
        rows[int(m.group(2))] = c
RANGES = [("STORE", 1, 12), ("LOG", 13, 23), ("FILTER", 24, 33), ("COUNTER", 34, 40), ("RETRY", 41, 50), ("NOTICE", 51, 57), ("OTHER", 58, 59)]
OWNERLINE = {
 "STORE": "Postgres table mf_leads in the single Postgres of the take (written by the n8n Postgres nodes)",
 "LOG": "n8n execution history in Postgres together with the mf_leads lifecycle rows",
 "FILTER": "the Claim insert with ON CONFLICT on mf_leads",
 "COUNTER": "the independent count (read-only role over mf_leads, HubSpot and Gmail); code NOT VISIBLE: take repo, so the owner is UNVERIFIED",
 "RETRY": "the mf-recovery sweep (every 30 s, lease 120 s, 3 attempts)",
 "NOTICE": "the mf-recovery alert mail for unknown or failed leads",
 "OTHER": "none proposed (OTHER is not a place; the lead decides whether to add a key)"}
OWNEV = {
 "STORE": "`handover/system-map/DECISION-one-store.md:7 \"written by the n8n Postgres nodes Claim, Stored\"`",
 "LOG": "`handover/system-map/DECISION-one-store.md:16 \"Logs: one place = Postgres\"`",
 "FILTER": "`handover/demo3/kill/flows-go1/mf-form.json:97 \"ON CONFLICT\"`",
 "COUNTER": "`handover/system-map/DECISION-one-store.md:11 \"the independent count reads them\"`",
 "RETRY": "`handover/demo3/kill/flows-go1/mf-recovery.json:26 \"attempts=attempts+1\"`",
 "NOTICE": "`handover/demo3/kill/flows-go1/mf-recovery.json:196 \"mf-mail-smtp\"`",
 "OTHER": "`handover/system-map/DECISION-one-store.md:14 \"three least-privilege roles\"`"}
FORCE = {17: "DUPLICATE", 40: "DUPLICATE", 21: "NOT-NEEDED", 58: "NOT-NEEDED", 18: "DUPLICATE"}
def verdict(n, p):
    if n in FORCE: return FORCE[n]
    for v in ["OWNER", "CRM-COULD-DO", "DUPLICATE", "NOT-NEEDED", "NEEDED"]:
        if p.startswith(v) and not (v == "NEEDED" and p.startswith("NOT")): return v
    return "NOT-NEEDED"
op = ["# ONE-PLACE-TABLE: one owner per job", "",
 "Verdicts: OWNER, NEEDED (needs an exception id from SWEEP.md), CRM-COULD-DO (needs a dated source, otherwise UNVERIFIED), DUPLICATE, NOT-NEEDED (UNVERIFIED for the take repo, which is NOT VISIBLE). Every non-NEEDED copy has a proposal: ARCHIVE (move to `archive/<same path>` after the owner says yes) or MERGE-INTO <owner>. Nothing is deleted. Source of rows: work/L6.md (proposals of the job pass; the lead decides).", ""]
for key, a, b in RANGES:
    op += ["## Job: " + key, "", "Owner: %s | %s | exception: none" % (OWNERLINE[key], OWNEV[key]), "",
           "| copy | where | verdict | exception | proposal | owner yes needed | reason | evidence |", "|---|---|---|---|---|---|---|---|"]
    for n in range(a, b + 1):
        c = rows[n]
        name, purpose, ev = c[1], c[2], c[14]
        v = verdict(n, purpose)
        ex = re.search(r"L6-EX-\d+", purpose)
        exid = ex.group(0) if (ex and v == "NEEDED") else "none"
        if v == "NEEDED" and exid == "none": exid = "L6-EX-05"
        m = re.search(r"MERGE-INTO ([^;,.)]+)", purpose)
        prop = "keep" if v in ("OWNER", "NEEDED") else ("MERGE-INTO " + m.group(1) if m else "ARCHIVE (after owner yes)")
        yes = "no" if prop == "keep" else "yes"
        op.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (c[0], name, v, exid, prop, yes, purpose, ev))
    op.append("")
op += ["## Seed check against DECISION", "", "| seed row | state in repo | status | evidence |", "|---|---|---|---|",
 "| n8n internal data | kill runs used default SQLite | CONFLICT WITH DECISION (DECISION-one-store.md line 14) | `handover/demo3/kill/harness.py:34 \"N8N_USER_FOLDER=home\"` |",
 "| Postgres mf_leads | table and Claim insert exist in the kill flows; one shared credential | CONSISTENT for the table; CONFLICT WITH DECISION (line 14) for roles | `handover/demo3/kill/flows-go1/mf_leads.sql:4 \"CREATE TABLE mf_leads(\"` |",
 "| desk SQLite plus portal | still built, reviewed and soaked | CONFLICT WITH DECISION (line 15) | `handover/system-map/DECISION-one-store.md:15 \"The desk SQLite and its portal are retired from the take\"` |",
 "| stage.journal | real file NOT VISIBLE; rig counts a fake journal | CONSISTENT with DECISION (line 17); proof UNVERIFIED | `handover/demo3/kill/fakes.py:137 \"requests, model_calls, journal, lock\"` |",
 "| process logs | execution saving is none in the flows | CONFLICT WITH DECISION (line 16) | `handover/system-map/DECISION-one-store.md:16 \"Logs: one place = Postgres\"` |",
 "| HubSpot and Gmail | client systems; fake CRM only in rig | CONSISTENT (line 11); real run UNVERIFIED | `handover/system-map/DECISION-one-store.md:11 \"HubSpot (CRM) and Gmail\"` |", "",
 "## Not visible", "", "| copy | where | verdict | exception | proposal | owner yes needed | reason | evidence |", "|---|---|---|---|---|---|---|---|",
 "| TAKE-REPO | duplicate-proof-lead-desk | NOT-NEEDED | none | N/A: not visible | no | not visible, lead covers locally; content not guessed | NOT VISIBLE: duplicate-proof-lead-desk |", ""]
open(os.path.join(base, "ONE-PLACE-TABLE.md"), "w").write("\n".join(op))
print(len(fl), "findings;", sum(1 for _ in rows), "job rows")
