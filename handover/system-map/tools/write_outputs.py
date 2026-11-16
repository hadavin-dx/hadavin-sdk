"""Writes SWEEP.md and ONE-PLACE-TABLE.md from work/merged-findings.md and work/L6.md (PLAN-002 5.2, 5.3), version 2
(result review round 1 applied, see work/result-resolve-r1.md). Usage: python3 tools/write_outputs.py <dir>"""
import re, sys, os
base = sys.argv[1]
esc = lambda s: s.replace(" | ", " / ").replace("|", "/")

KEY_TEXT = """## How to read this file
- **Take** = the lead-intake automation Hadavin will show in the video (n8n flows, one Postgres). Its code repository `duplicate-proof-lead-desk` is NOT in this box; the laptop lead checks it locally. That is why every NOT-NEEDED verdict says UNVERIFIED for the take repo.
- **Laptop lead** = the engineer who gave the order. **Sales lead** = a person who sends a request through the form. **Studio head** = the owner who says yes to money, archive moves and secret changes.
- **DECISION-one-store.md** = the laptop lead's written decision that the take keeps its data in one Postgres, with three stores by design (n8n data, table `mf_leads`, file `stage.journal`). "DECISION line 14" means line 14 of that file.
- **Job** = something a part of the system does. Job keys: STORE (holds data), LOG (record of what ran), FILTER (decides what enters, for example duplicate checks), COUNTER (counts, for proof or for a money cap), RETRY (runs stuck work again), NOTICE (tells a person), OTHER.
- **Job owner place** (the line starting `Owner:`) = the one place that does the job in the take. It is a place, not a person.
- **Verdicts.** OWNER: the one place that does this job. NEEDED: a second place the take must keep; it carries an exception id. DUPLICATE: a copy of what the job owner place already does. CRM-COULD-DO: the customer system (CRM) may do this itself; only a dated source proves it, otherwise UNVERIFIED. NOT-NEEDED: nothing in the files seen calls it (UNVERIFIED for the take repo). KEEP-CORE: shared core code in `src/`, out of take scope, never moved.
- **Proposals.** keep; KEEP-CORE; CHANGE; MERGE-INTO <place>; STOP; ARCHIVE = move to `archive/<same path>` after the studio head says yes. Nothing is deleted.
- **State against DECISION.** OK; PLAN NOT DONE (DECISION states the target and the change is not made yet); CONFLICT (the repo does the opposite of DECISION); UNDECIDED.
- **Ids.** `L1c-FD-021` = lane L1, `c` = continuation lane, FD = finding, number. Kinds: S store, W workflow, X script, J job, K credential, C component. A lane is one part of the repository read by one reading agent.
- **Words.** desk = the older lead desk program with its own SQLite file and web screens (portal), retired from the take by DECISION line 15. rig = the kill-test setup that crashes the flows on purpose. journal = a file that records each model call before it is made. lease = a time limit during which one run owns a lead. sweep (lower case) = the recovery flow that runs every 30 seconds. claim = the first database insert that reserves a lead; "claim type" = the category of a finding; "Claims check" = statements made in files and whether they hold.
"""

fl = []
for l in open(os.path.join(base, "work/merged-findings.md"), encoding="utf-8"):
    if l.startswith("| ") and not l.startswith("| id "):
        c = [x.strip() for x in l.strip().strip("|").split(" | ")]
        if len(c) == 6:
            fl.append(c)
RERATE = {"L4-FD-004": ("Major", "count slip, no action changes"), "L3-FD-040": ("Major", "no claim sentence; the cited review says 0 Blocker"),
          "L2c-FD-001": ("Major", "shell hygiene, no real call shown"), "L6-FD-017": ("Blocker", "a lead is lost with no mail (severity table: mail)"),
          "L2-FD-007": ("Blocker", "same: a lead in state review gets no notice"), "L1-FD-021": ("Blocker", "false claim in live text"),
          "L1c-FD-001": ("Blocker", "credential on the same runner as test code")}
NOTE = {"L2-FD-001": "Result review: static inference from harness.py:34 (the GREP step shows SQLite in 11 runs); evidence is the kill rig, not the take flows (film-v5, real-v5 NOT VISIBLE); state: PLAN NOT DONE (DECISION line 8 already corrects it).",
        "L6-FD-001": "Result review: same as L2-FD-001; state PLAN NOT DONE; rig evidence.",
        "L6-FD-002": "Result review: rig flows set saving none on purpose for the planted-data test; turning saving on needs the masking check first (Fix plan row 2).",
        "L2-FD-008": "Result review: fault Fc holds every SMTP connection for the whole run (a total mail outage); no alert was seen within the 330 s window plus 20 s settle; Fc1 (first connection only) gave lead_alerts=1 in 6 of 6 runs (RESULTS.md); the design point stands: with mail fully down there is no second channel.",
        "L6-FD-005": "Result review: same as L2-FD-008; also one SMTP credential serves alert mail and lead mail, and both run inside the same n8n and Postgres.",
        "L3-FD-040": "Result review: cites a round-12 design review of a paused patch; its own text says 0 Blocker, 2 Major; claim sentence missing in the lane row."}
DEDUP = {"L6-FD-001", "L6-FD-002", "L6-FD-005", "L4c-FD-011", "L4c-FD-012", "L2c-FD-010"}
EXTRA = [
 ["L6-FD-026", "ops", "Blocker", "The recovery sweep, the only RETRY owner, swallows database errors (onError continueRegularOutput), so a Postgres hiccup can stop recovery with no notice. `handover/demo3/kill/flows-go1/mf-recovery.json:43 \"continueRegularOutput\"`", "DECISION line 7", "RETRY"],
 ["L6-FD-027", "ops", "Major", "One Postgres holds intake, claim state, recovery, n8n data and the execution log: if it is down everything stops. Backup, restore test, volume persistence, retention, start/stop/kill and egress answers are in no file seen (UNVERIFIED for the take). `handover/system-map/DECISION-one-store.md:14 \"ONE database for everything we own\"`", "DECISION line 14", "STORE"],
 ["L6-FD-028", "unverified", "Major", "Tenant isolation: the take serves one client, so N/A if the studio head confirms; the table has no source or tenant column. `handover/demo3/kill/flows-go1/mf_leads.sql:4 \"CREATE TABLE mf_leads(\"`", "DECISION line 14", "STORE"]]
LANE_SCOPE = [("L2", "take-rig"), ("L3", "take-rig"), ("L5", "core or demo"), ("L1", "build-process"), ("L4", "desk (retired from the take)"), ("L6", "cross-lane")]
def scope(i):
    for p, s in LANE_SCOPE:
        if i.startswith(p): return s
    return "see evidence"
rows_f = []
for c in fl + EXTRA:
    c = list(c); sev = c[2]
    if c[0] in RERATE:
        new, why = RERATE[c[0]]
        c[2] = "%s (was %s: %s)" % (new, sev, why) if new != sev else sev
        base_sev = new
    else:
        base_sev = sev
    if c[0] in NOTE:
        c[3] = c[3] + " " + NOTE[c[0]]
    rows_f.append((c, base_sev))
sevo = {"Blocker": 0, "Major": 1, "Nit": 2}
rows_f.sort(key=lambda r: (sevo.get(r[1], 3), r[0][0]))
cnt = {}
for c, s in rows_f:
    cnt[(c[1], s)] = cnt.get((c[1], s), 0) + 1
types = sorted({k[0] for k in cnt}); sevs = ["Blocker", "Major", "Nit"]
counts = ["| claim type | Blocker | Major | Nit | total |", "|---|---|---|---|---|"]
for t in types:
    counts.append("| %s | %s | %d |" % (t, " | ".join(str(cnt.get((t, s), 0)) for s in sevs), sum(cnt.get((t, s), 0) for s in sevs)))
tot = {s: sum(cnt.get((t, s), 0) for t in types) for s in sevs}
counts.append("| all (raw rows) | %s | %d |" % (" | ".join(str(tot[s]) for s in sevs), len(rows_f)))
ded = [(c, s) for c, s in rows_f if c[0] not in DEDUP]
dt = {s: sum(1 for c, x in ded if x == s) for s in sevs}
counts.append("| deduplicated (minus %d rows that restate another row) | %s | %d |" % (len(rows_f) - len(ded), " | ".join(str(dt[s]) for s in sevs), len(ded)))
EX = [
 ("L6-EX-01", "n8n internal data (workflows, credentials, execution history)", "second of the three stores DECISION keeps; must run on Postgres, but the kill rig used SQLite", "laptop lead", "n8n data moved to the one Postgres (DECISION line 14)", "DECISION line 14"),
 ("L6-EX-02", "stage.journal file (per-lead write-ahead guard against a second model call)", "the one stated exception in DECISION; real file NOT VISIBLE: qualify_stage.py", "laptop lead", "after the video, core store-kind item (DECISION line 17)", "DECISION line 17"),
 ("L6-EX-03", "HubSpot (CRM) and Gmail", "client systems of record; the take writes to them, the independent count reads them", "client", "none: not an exception to the one-store rule, it is the client's own system", "DECISION line 11"),
 ("L6-EX-04", "process output files (n8n output, stage stderr and result.json)", "diagnostics meant to hold no lead data; UNVERIFIED because lead data was found in the n8n database (L2-FD-002)", "laptop lead", "none: not an exception to the one-store rule", "DECISION line 10"),
 ("L6-EX-05", "mf_leads lifecycle rows", "state per lead, latest state only: not an append-only history, so it cannot show a double send or a sequence (an event table was ruled out before the video by DECISION line 16)", "laptop lead", "none: not an exception to the one-store rule", "DECISION line 16"),
 ("L6-EX-06", "shape check node (Valid regex) in the entry flow", "cheap check before the claim insert; same flow", "laptop lead", "none: part of a flow", "DECISION line 7"),
 ("L6-EX-07", "alert claim and backoff as helper of the recovery sweep", "stops a second alert for the same lead; double-alert window if a send was in flight at a kill (not tested)", "laptop lead", "if the sweep gets a second channel, re-check", "DECISION line 7"),
 ("L6-EX-08", "lead intake mail inside the sub-workflow", "a notice to the lead of the client, not to our person", "client", "none: part of a flow", "DECISION line 11"),
 ("L6-EX-09", "proof screens for the video (n8n executions)", "DECISION names these as the screens shown", "laptop lead", "after the video", "DECISION line 18"),
 ("L6-EX-10", "never-delete rule: tracked credential files", "a secret is rotated and untracked, not archived; an archived copy would keep it in the repository", "studio head", "after rotation and untracking", "never-delete rule of ARCHITECTURE-AUDIT-CHECKLIST.md"),
 ("L6-EX-11", "stopping or archiving the desk", "L4c-FD-001 (key sent to a vendor), L4c-FD-002 (n8n API key sent to a second server) and L4c-FD-003 (real-spend consent flag) are fixed only in pending patches", "laptop lead", "the three patches are applied", "DECISION line 15"),
]
BANDS = ["before the video (Wed 18 Nov: config changes on proven flows only)", "needs the studio head's yes", "after the video"]
fixrows = [
 (BANDS[0], "L6-FD-017, L2-FD-007, L6-FD-026", "every lead ends in a state a person sees; the recovery sweep alerts on its own database error", "laptop lead", "no"),
 (BANDS[0], "L6-FD-002, L2-FD-002", "FIRST run the planted-data check on Postgres-backed n8n; write down what is stored, who can read it (n8n role or app role), the prune and retention setting and what is masked; THEN switch execution saving on in the take flows", "laptop lead", "yes"),
 (BANDS[0], "L6-FD-005, L2-FD-008", "give the alert its own credential and its own path plus a heartbeat check from outside n8n; name the second channel (the laptop lead decides)", "laptop lead", "yes"),
 (BANDS[0], "L6-FD-006", "three Postgres roles (n8n, app, read-only count) PLUS a fourth identity for roles, schemas and migrations; each with a negative test; name the exact tables the count role may read; give the count's Gmail and HubSpot credentials their own minimum scopes", "laptop lead", "yes"),
 (BANDS[0], "L1c-FD-021, L1-FD-023", "correct the three live pull request bodies: the final tree is NOT identical to PR #1 (95 files differ)", "laptop lead", "yes"),
 (BANDS[1], "L2-FD-018", "stop tracking the four creds-lane.json files; ROTATE anything real; rewrite history only on the studio head's yes (exception L6-EX-10)", "studio head", "yes"),
 (BANDS[1], "L6-FD-003, L6-FD-004", "name the take's owner of the dollar cap (UNVERIFIED, take repo NOT VISIBLE); until then the desk SpendLedger, the askdata meter and core Limits are kept; six counter places exist (stage.journal, desk SpendLedger, askdata meter, core Limits, k1b cap, eval counter); make the rig use the real journal", "laptop lead", "yes"),
 (BANDS[1], "all desk rows marked ARCHIVE BLOCKED", "archive the desk, its portal and retry loops ONLY after the laptop lead shows which counter the take proof reads, and after the pending security patches (L6-EX-11) are applied", "laptop lead", "yes"),
 (BANDS[1], "L1-FD-003, L1c-FD-007", "archive superseded patch, PR-text and evidence versions (about 519 KB)", "studio head", "yes"),
 (BANDS[2], "L6-FD-001, L2-FD-001", "move n8n data to the one Postgres and re-run the kill tests on it (needs a runtime; the re-smoke plan in DECISION line 14 covers it)", "laptop lead", "no"),
 (BANDS[2], "L6-FD-019", "reconcile the test counts before quoting any number", "laptop lead", "no"),
 (BANDS[2], "L6-J-028, L6-J-042", "merge mf-hook into mf-form (key becomes source plus id) and trim the node retry (n8n Retry On Fail cannot filter by error type: UNVERIFIED)", "laptop lead", "no"),
]
named = " ".join(r[1] for r in fixrows)
blk = [(c, s) for c, s in rows_f if s == "Blocker" and c[0] not in named]
for c, s in blk:
    ev = esc(c[3].split("`")[0].strip())[:160]
    yes = "yes" if re.search(r"credential|spend|key|desk", ev, re.I) else "no"
    fixrows.append((BANDS[1] if yes == "yes" else BANDS[0], c[0], ev, "laptop lead", yes))
for t in ("duplicate", "dead", "idle"):
    ids = [c[0] for c, s in rows_f if c[1] == t and s == "Major"]
    fixrows.append((BANDS[2], "%d Major %s findings: %s" % (len(ids), t, ", ".join(ids[:6]) + (" and more (see Findings)" if len(ids) > 6 else "")), "work through them in the order of the Findings table after the video", "laptop lead", "no"))
claims = [
 ("the final tree of PRs 2 to 4 is identical to PR #1", "handover/demo/pr-text/github-current/pr3-body.md:5", "VERIFY.md measured 95 files differing (L1c-FD-021)", "CONTRADICTED"),
 ("SonarQube runs on every pull request", "pr4 text v5", "AB-PAPER shows 0 SonarQube jobs since 0841f36 (L1c-FD-002)", "CONTRADICTED"),
 ("n8n runs on Postgres in the take", "DECISION-one-store.md line 14 (a plan)", "kill rig used the default SQLite file (harness.py:34); take flows NOT VISIBLE", "PLAN NOT DONE (rig evidence)"),
 ("execution history is saved in Postgres", "DECISION-one-store.md line 16 (a plan)", "the rig flows set execution saving to none (L6-FD-002)", "PLAN NOT DONE (rig evidence)"),
 ("no lead data reaches n8n's store", "implied by L6-EX-04", "made-up e-mail, name and a key canary were found in n8n files with saving off (L2-FD-002)", "CONTRADICTED (rig)"),
 ("DB_POSTGRESDB_SCHEMA works for import and for start", "DECISION UNVERIFIED item 6", "not run", "UNVERIFIED"),
 ("stage.journal is independent of the flow identity", "DECISION line 17", "nothing shows who can write the file or whether two stage processes run at once", "UNVERIFIED"),
 ("the take has a model-call spend cap", "DECISION line 17 (implied)", "stage.journal is a per-lead repeat guard; no dollar-cap owner in files seen (take repo NOT VISIBLE)", "UNVERIFIED"),
 ("Postgres sits behind n8n's credential layer (no single dependency)", "DECISION line 18c", "no kind with an alternative is described", "UNVERIFIED"),
 ("the kill tests prove the money guard", "kill RESULTS", "model_calls=1 is counted from an in-memory fake journal (L6-FD-004)", "UNVERIFIED"),
 ("the DeepSource carry-over holds about 96 distinct findings among 213 comments", "L1c-FD-003", "counted by block, rows not compared one by one", "UNVERIFIED"),
 ("test totals quoted across the lanes (2329, 3138, 4125, 4409 and others)", "L1, L2c, L3, L4", "no lane reconciles them (L6-FD-019)", "UNVERIFIED"),
 ("every file under handover/ was read", "lane Coverage tables", "183 files NOT-READ (L1c 18, L3c 66, L4c 99)", "CONTRADICTED"),
]
out = ["# SWEEP: duplicates, dead, idle, inconsistent and unverified parts", "",
 "Static review of the repository on branch cloud/system-map. No n8n runtime, no network: anything needing a runtime is UNVERIFIED. The take code repo `duplicate-proof-lead-desk` is NOT VISIBLE here (the laptop lead covers it locally).", "",
 "**NOT-READ files: L1c 18, L3c 66, L4c 99 (183 in total). Unread means UNVERIFIED, not clean.** The laptop lead may order one more continuation lane for these three lists.", "",
 "Severity: Blocker = contradicts DECISION-one-store.md in the take, or touches money, credentials, mail or personal data, or a claim that a reader would act on is false. A wrong count or number that changes no action is Major. Major = a duplicate, dead or idle part, or an inconsistency, that costs time or confuses the take. Nit = wording or tidiness. Severity is the lane's candidate, re-rated by the result review where the Severity cell says `was`.", "",
 "The citation check proves each quoted line exists, not that it supports the claim; support was checked by sample by the result reviewers. Some findings are counted twice by two lanes (see Counts: raw and deduplicated).", "", KEY_TEXT,
 "## Findings", "", "Scope: take-rig = evidence comes from the kill rig, not the take flows; desk (retired from the take) = the older desk program; build-process = patches, pull requests, CI; core or demo = `src/`, `demos/`; cross-lane = the job pass. Default by lane; the evidence cell is the proof.", "",
 "| id | claim type | severity | evidence | conflicts with | job key | scope |", "|---|---|---|---|---|---|---|"]
out += ["| " + " | ".join(esc(x) if i != 3 else x for i, x in enumerate(c)) + " | " + scope(c[0]) + " |" for c, s in rows_f] + [""]
out += ["## Fix plan", "", "Bands: before the video, needs the studio head's yes, after the video. Each Blocker has a row.", "", "| order | band | finding ids | action | owner | needs studio head yes |", "|---|---|---|---|---|---|"]
for i, r in enumerate(fixrows, 1):
    out.append("| %d | %s |" % (i, " | ".join(esc(x) for x in r)))
out += ["", "## Exceptions", "", "An exception is a second place or a rule departure that we accept on purpose. NEEDED rows in ONE-PLACE-TABLE.md point at these ids.", "", "| id | what | reason | owner | removal trigger | decision line |", "|---|---|---|---|---|---|"]
out += ["| " + " | ".join(r) + " |" for r in EX]
out += ["", "Open question for the laptop lead: the second alert channel and its heartbeat (Fix plan, band before the video) has no named owner yet.", ""]
out += ["## Claims check", "", "Status: PROVEN = a raw file shows it; CONTRADICTED = a raw file shows the opposite; PLAN NOT DONE = DECISION states a target and the change is not made; UNVERIFIED = needs a runtime or a file not in this box.", "", "| claim | where claimed | evidence | status |", "|---|---|---|---|"] + ["| " + " | ".join(r) + " |" for r in claims] + [""]
out += ["## Lessons", "",
 "- For the audit checklist: check the engine behind every test number (SQLite or Postgres) before quoting it.",
 "- For studio memory: one name per file; the desk money file has four names across lanes.",
 "- For agent briefs: ban unbounded wait loops in test rigs; every quoted test count names its commit.",
 "- For the lane method: a lane that reads about 100 files runs out of context; cap lanes at about 60 files and keep a READ status honest.", "",
 "## Counts", "", "Counts of finding rows after re-rating. Raw = every row; deduplicated = minus rows that restate another row.", ""] + counts + [""]
open(os.path.join(base, "SWEEP.md"), "w").write("\n".join(out))

# ONE-PLACE-TABLE
rows = {}
for l in open(os.path.join(base, "work/L6.md"), encoding="utf-8"):
    m = re.match(r"\| (L6-J-(\d+)) \|", l)
    if m:
        rows[int(m.group(2))] = [x.strip() for x in l.strip().strip("|").split(" | ")]
RANGES = [("STORE", 1, 12), ("LOG", 13, 23), ("FILTER", 24, 33), ("COUNTER", 34, 40), ("RETRY", 41, 50), ("NOTICE", 51, 57), ("OTHER", 58, 59)]
APPX = {12, 18, 22, 33, 39, 40, 49, 50, 57, 59}
OWNERLINE = {
 "STORE": "Postgres table mf_leads in the single Postgres of the take (written by the n8n Postgres nodes)",
 "LOG": "n8n execution history in Postgres (DECISION line 16)",
 "FILTER": "the claim insert with ON CONFLICT on mf_leads",
 "COUNTER": "PROOF COUNT: the independent count (read-only role over mf_leads, HubSpot and Gmail); code NOT VISIBLE: take repo, so the owner is UNVERIFIED. The MONEY CAP is a second job under this key: see below",
 "RETRY": "the mf-recovery sweep (every 30 s, lease 120 s, 3 attempts)",
 "NOTICE": "the mf-recovery alert mail for unknown or failed leads",
 "OTHER": "none proposed (OTHER is not a place; the laptop lead decides whether to add a key)"}
OWNEV = {
 "STORE": "`handover/system-map/DECISION-one-store.md:7 \"written by the n8n Postgres nodes Claim, Stored\"`",
 "LOG": "`handover/system-map/DECISION-one-store.md:16 \"Logs: one place = Postgres\"`",
 "FILTER": "`handover/demo3/kill/flows-go1/mf-form.json:97 \"ON CONFLICT\"`",
 "COUNTER": "`handover/system-map/DECISION-one-store.md:11 \"the independent count reads them\"`",
 "RETRY": "`handover/demo3/kill/flows-go1/mf-recovery.json:26 \"attempts=attempts+1\"`",
 "NOTICE": "`handover/demo3/kill/flows-go1/mf-recovery.json:196 \"mf-mail-smtp\"`",
 "OTHER": "`handover/system-map/DECISION-one-store.md:14 \"three least-privilege roles\"`"}
CORE = {6, 7, 21, 31, 32, 38, 45, 46, 47, 56}
FORCE = {17: "NOT-NEEDED", 10: "NOT-NEEDED", 40: "DUPLICATE", 18: "DUPLICATE", 58: "NOT-NEEDED", 5: "NOT-NEEDED", 37: "NOT-NEEDED"}
BLOCKED = "ARCHIVE BLOCKED until the laptop lead shows which counter the take proof reads, and the desk security patches are applied (L6-EX-11)"
PROP = {10: "KEEP (test evidence; Fix plan rows need the rig)", 17: "KEEP (test evidence)", 22: "KEEP (CI)", 33: "KEEP (CI)",
        58: "CHANGE (replace by three least-privilege roles plus a migrations identity, see Fix plan)", 59: "STOP (process waste, not a file)",
        23: "FIX THE HARNESS (it recreates the empty files every run); no archive", 5: "KEEP until the owner of the dollar cap is named (Fix plan)",
        37: "KEEP until the owner of the dollar cap is named (Fix plan)", 27: "KEEP until a dated source shows the CRM does this; the keyed upsert keeps crm_rows=1 under retries",
        28: "MERGE-INTO mf-form AFTER THE VIDEO; the key must become source plus id (L2-FD-004: ids from two sources can collide and a lead is dropped as a duplicate)",
        42: "AFTER THE VIDEO: n8n Retry On Fail cannot filter by error type (UNVERIFIED), so the trim is not implementable as written; removing it also makes recovery wait for the 120 s lease",
        4: BLOCKED, 16: BLOCKED, 29: BLOCKED, 36: BLOCKED, 44: BLOCKED, 54: BLOCKED}
CONFLICT = {4, 5, 16, 29, 36, 44, 54}; NOTDONE = {2, 13}; UNDEC = {58}
TEXT = {23: "NOT-NEEDED: most of the 378 log files are empty (check: count lines per file; run folder fl45k6c has non-empty logs); fakes write to events.jsonl",
        20: "NOT-NEEDED for the take, UNVERIFIED for take repo; query text passes clean() (terminal escapes stripped, `ledger.py:3`); whether personal data is masked is UNVERIFIED"}
EVID = {11: "`handover/system-map/DECISION-one-store.md:11 \"HubSpot (CRM) and Gmail\"`; real HubSpot and Gmail NOT VISIBLE"}
def verdict(n, p):
    if n in CORE: return "KEEP-CORE"
    if n in FORCE: return FORCE[n]
    for v in ["OWNER", "CRM-COULD-DO", "DUPLICATE", "NOT-NEEDED", "NEEDED"]:
        if p.startswith(v) and not (v == "NEEDED" and p.startswith("NOT")): return v
    return "NOT-NEEDED"
def render(n):
    c = rows[n]; name, purpose, ev = c[1], TEXT.get(n, c[2]), EVID.get(n, c[14])
    v = verdict(n, c[2])
    ex = re.search(r"L6-EX-\d+", c[2])
    exid = ex.group(0) if (ex and v == "NEEDED") else "none"
    if v == "NEEDED" and exid == "none": exid = "L6-EX-05"
    m = re.search(r"MERGE-INTO ([^;,.)]+)", c[2])
    if n in PROP: prop = PROP[n]
    elif v == "KEEP-CORE": prop = "KEEP-CORE (out of take scope; no move)"
    elif v in ("OWNER", "NEEDED"): prop = "keep"
    else: prop = "MERGE-INTO " + m.group(1) if m else "ARCHIVE (after the studio head says yes)"
    yes = "no" if re.match(r"(keep|KEEP|STOP|FIX)", prop) else "yes"
    st = "CONFLICT" if n in CONFLICT else "PLAN NOT DONE" if n in NOTDONE else "UNDECIDED (DECISION line 20)" if n in UNDEC else "OK"
    if v == "KEEP-CORE": purpose = "Result review: core code with callers, never moved. Lane wording: " + purpose
    if n == 42: purpose += "; the mail node has retryOnFail false (`mf-sub-crm-mail.json:230`), only lines 35 and 91 show 3 tries"
    if n == 43: purpose += "; double-alert window if a send was in flight at a kill (not tested; two n8n at once not tested)"
    return "| %s |" % " | ".join(esc(x) for x in (c[0], name, v, exid, prop, yes, st, purpose, ev))
HDR = ["| copy | what | verdict | exception | proposal | studio head yes needed | state vs DECISION | reason | evidence |", "|---|---|---|---|---|---|---|---|---|"]
op = ["# ONE-PLACE-TABLE: one place per job", "",
 "Source of rows: work/L6.md (proposals of the job pass; the laptop lead decides). Every copy except the job owner place, NEEDED rows and KEEP-CORE rows has a proposal. Nothing is deleted. 49 rows are in the job blocks and 10 build-process rows are in the appendix.", "", KEY_TEXT]
for key, a, b in RANGES:
    op += ["## Job: " + key, "", "Owner: %s | %s | exception: none" % (OWNERLINE[key], OWNEV[key]), ""]
    if key == "NOTICE":
        op += ["Alert mail (L6-J-051) and lead intake mail (L6-J-052) use ONE SMTP credential (mf-mail-smtp) and run inside the same n8n and the same Postgres. If mail, n8n or Postgres is down, nobody is told. Needed: a second channel with its own credential and a heartbeat watched from outside n8n. The second channel has no named owner yet: open question for the laptop lead.", ""]
    ns = [n for n in range(a, b + 1) if n not in APPX]
    mc = [n for n in ns if key == "COUNTER" and n in (35, 37, 38)]
    op += HDR + [render(n) for n in ns if n not in mc] + [""]
    if mc:
        op += ["### Money cap (a second job under the key COUNTER)", "", "Money-cap place: UNVERIFIED. No owner of a dollar cap for the take is identified: `stage.journal` is a per-lead write-ahead guard against a second model call, not a dollar ceiling (`handover/system-map/DECISION-one-store.md:9 \"file in the take folder (qualify_stage.py)\"`). The desk SpendLedger, the askdata meter and core Limits enforce dollar ceilings (`src/hadavin_sdk/limits.py:17 \"def charge(self, agent_id: str, usd: Decimal)\"`); they are kept until the owner is named (question for the laptop lead).", ""] + HDR + [render(n) for n in mc] + [""]
op += ["## Appendix: build-process rows (not places of a take job)", ""] + HDR + [render(n) for n in sorted(APPX)] + [""]
op += ["## Seed check against DECISION", "", "| seed row | state in repo | status | evidence |", "|---|---|---|---|",
 "| n8n internal data | kill rig used default SQLite; take flows NOT VISIBLE | PLAN NOT DONE (DECISION line 8 already corrects it) | `handover/demo3/kill/harness.py:34 \"N8N_USER_FOLDER=home\"` |",
 "| Postgres mf_leads | table and claim insert exist in the kill flows; created in the default schema, not schema app; one shared credential | CONSISTENT for the table; CONFLICT for the schema (DECISION line 14) and for roles | `handover/demo3/kill/flows-go1/mf_leads.sql:4 \"CREATE TABLE mf_leads(\"` |",
 "| desk SQLite plus portal | still built, reviewed and soaked | CONFLICT (DECISION line 15) | `handover/system-map/DECISION-one-store.md:15 \"The desk SQLite and its portal are retired from the take\"` |",
 "| stage.journal | real file NOT VISIBLE; rig counts a fake journal | CONSISTENT with DECISION (line 17); proof UNVERIFIED | `handover/demo3/kill/fakes.py:137 \"requests, model_calls, journal, lock\"` |",
 "| process logs | execution saving is none in the rig flows | PLAN NOT DONE (DECISION line 16) | `handover/system-map/DECISION-one-store.md:16 \"Logs: one place = Postgres\"` |",
 "| HubSpot and Gmail | client systems; only a fake CRM in the rig; real run NOT VISIBLE | CONSISTENT with DECISION (line 11); real run UNVERIFIED | `handover/demo3/kill/fakes.py:103 \"hit = next((r for r in rows.values()\"` |", "",
 "## Not visible", "", "| copy | what | verdict | exception | proposal | studio head yes needed | state vs DECISION | reason | evidence |", "|---|---|---|---|---|---|---|---|---|",
 "| TAKE-REPO | duplicate-proof-lead-desk | N/A: not visible | none | N/A: not visible | no | N/A: not visible | not visible, the laptop lead covers it locally; content not guessed | NOT VISIBLE: duplicate-proof-lead-desk |", ""]
open(os.path.join(base, "ONE-PLACE-TABLE.md"), "w").write("\n".join(op))
print(len(rows_f), "findings;", len(rows), "job rows")
