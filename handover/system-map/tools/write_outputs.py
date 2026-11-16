"""Writes SWEEP.md and ONE-PLACE-TABLE.md from work/merged-findings.md and work/L6.md (PLAN-002 5.2, 5.3), version 3
(result review round 1 and round 2 applied, see work/result-resolve-r1.md and work/result-resolve-r2.md).
Usage: python3 tools/write_outputs.py <dir>"""
import re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from safe_write import safe_write, refused
OVERWRITE_OK = "--force" in sys.argv
from collections import Counter
base = sys.argv[1]
for _n in ("SWEEP.md", "ONE-PLACE-TABLE.md"):
    if refused(base, _n, OVERWRITE_OK):
        print("REFUSED: %s was edited by hand or has no record of being generated; nothing written; use --force to overwrite" % _n); sys.exit(1)
esc = lambda s: s.replace(" | ", " / ").replace("|", "/")

KEY_TEXT = """## How to read this file
- **Take** = the lead-intake automation that Hadavin (the one-person AI studio this repository belongs to) will show in the video on Wed 18 Nov: n8n flows and one Postgres. Its code repository `duplicate-proof-lead-desk` is NOT in this box ("this box" = this checkout of the repository). The laptop lead checks the take repository locally, so a verdict about the take repository stays UNVERIFIED.
- **People.** **Laptop lead** = the engineer who gave the written work order (ORDERS.md) to this session. **Studio head** = the person who runs the studio and says yes to money, archive moves and secret changes. **Sales request** = what a person sends through the form. In finding text the word "lead" means a sales request or its row in the table `mf_leads`; it never means the laptop lead. **Client** = a company that buys a build; in demos the client is made up. **Responsible person** (a column) = the human who does or approves a step; the word "owner" is kept for a place.
- **DECISION-one-store.md** = the laptop lead's written decision that the take keeps its data in one Postgres, with three stores by design (n8n data, table `mf_leads`, file `stage.journal`). "DECISION line 14" means line 14 of that file.
- **Job** = something a part of the system does. Job keys sort every part of the repository, build-process parts included (those are in the appendix): STORE (holds data), LOG (record of what ran; also audit chains and evidence reports), FILTER (decides what enters, for example duplicate checks; also outbound action gates and scans), COUNTER (counts, for proof or for a money cap; also test totals and slot limits), RETRY (runs stuck work again), NOTICE (tells a person), OTHER (everything else, for example identities and roles).
- **Job owner place** (the line starting `Owner:`) = the one place that does the job in the take. It is a place, never a person. `Open owner:` = no place does this job yet or the files do not show one.
- **Verdicts.** OWNER: the place DECISION chooses for the job (the state column says whether the repository already works that way). NEEDED: a second place the take must keep; it carries an exception id. DUPLICATE: a copy of what the job owner place already does. CRM-COULD-DO: the customer system (CRM) may do this itself; only a dated source proves it, otherwise UNVERIFIED. NOT-NEEDED: nothing in the files seen calls it for the take. This does NOT mean safe to remove: grep `src/`, `pyproject.toml` and `tests/` for callers first. KEEP-CORE: code or gate configuration with callers outside the take (`src/`, `demos/ask-your-data`, CI files); out of take scope, never moved.
- **Proposals.** keep; KEEP-CORE; CHANGE; MERGE-INTO <place>; STOP; ARCHIVE = move to `archive/<same path>` after the studio head says yes. Nothing is deleted, and nothing with a caller is archived.
- **State against DECISION.** OK (no conflict found in the files seen); PLAN NOT DONE (DECISION states the target and the change is not made yet); CONFLICT (the repository does the opposite of DECISION); CONSISTENT (used in the seed check: matches DECISION); UNVERIFIED (not checked, or needs a runtime or the take repository); UNDECIDED.
- **Severity.** Blocker = contradicts DECISION in the take, or touches money, credentials, mail or personal data, or a false claim a reader would act on. Major = a duplicate, dead or idle part, or an inconsistency, that costs time or confuses the take. Nit = wording or tidiness. `was X` in a severity cell = the lane's candidate severity before the result review.
- **Ids.** `L1c-FD-021` = lane L1, `c` = continuation lane, FD = finding, number. Kinds: S store, W workflow, WK workflow walk, X script, J job, K credential, C component, D doc, T test, EX exception. A lane is one part of the repository read by one reading agent.
- **Words.** desk = the older lead desk program with its own SQLite file and web screens (portal), retired from the take by DECISION line 15. rig = the kill-test setup that crashes the flows on purpose (its runs, film-v5 and real-v5, are NOT VISIBLE here). flow = one n8n workflow file. stand-in = a code node that imitates a real service. canary = a planted fake value used to see whether it leaks. journal = a file that records each model call before it is made. lease = a time limit during which one run owns a request. sweep (lower case) = the recovery flow that runs every 30 seconds. claim insert = the first database insert that reserves a request; claim type = the category of a finding; Claims check = statements made in files and whether they hold. request states: review (needs a person), unknown, failed. schema app = the database schema DECISION line 14 plans for our own tables. heartbeat = a regular signal that shows a watcher is alive. k1b, core Limits, DeadLetter, SpendLedger = names of modules in `src/` (spend limits, failed-work store). proof = what the video shows: 10 test requests give 1 new, 9 duplicates, 1 e-mail and 1 CRM row.
"""

fl = []
for l in open(os.path.join(base, "work/merged-findings.md"), encoding="utf-8"):
    if l.startswith("| ") and not l.startswith("| id "):
        c = [x.strip() for x in l.strip().strip("|").split(" | ")]
        if len(c) == 6:
            fl.append(c)
RERATE = {"L4-FD-004": ("Major", "count slip, no action changes"), "L3-FD-040": ("Major", "no claim sentence; the cited review says 0 Blocker"),
          "L2c-FD-001": ("Major", "shell hygiene, no real call shown"), "L6-FD-017": ("Blocker", "a request is lost with no mail (severity table: mail)"),
          "L2-FD-007": ("Blocker", "a request in state review gets no notice; L6-FD-017 is the same finding and is counted once in the deduplicated row"),
          "L1-FD-021": ("Blocker", "false claim in live text, plus personal data in file paths; the laptop lead confirms (Fix plan)"),
          "L1c-FD-001": ("Blocker", "credential on the same runner as test code")}
NOTE = {"L2-FD-001": "Result review: static inference from harness.py:34 (the GREP step shows SQLite in 11 runs); evidence is the kill rig, not the take flows (film-v5, real-v5 NOT VISIBLE); state: PLAN NOT DONE (DECISION line 8 already corrects it).",
        "L6-FD-001": "Result review: same as L2-FD-001; state PLAN NOT DONE; rig evidence.",
        "L6-FD-002": "Result review: rig flows set saving none on purpose for the planted-data test; turning saving on needs the masking check first (Fix plan row 1).",
        "L2-FD-008": "Result review: fault Fc holds every SMTP connection for the whole run (a total mail outage); no alert was seen within the 330 s window plus 20 s settle; Fc1 (first connection only) gave lead_alerts=1 in 6 of 6 runs (RESULTS.md); the design point stands: with mail fully down there is no second channel.",
        "L6-FD-005": "Result review: same as L2-FD-008; also one SMTP credential serves alert mail and lead mail, and both run inside the same n8n and Postgres.",
        "L3-FD-040": "Result review: cites a round-12 design review of a paused patch; its own text says 0 Blocker, 2 Major; claim sentence missing in the lane row.",
        "L6-FD-023": "Result review round 2: NOT all are empty: run folder fl45k6c has crm.log 849, smtp.log 655 and stage.log 853 bytes (work/L2.md:331-333). Read 'most'; the count of non-empty files is still to be counted by the laptop lead (find with -size +0).",
        "L2-FD-024": "Result review round 2: NOT all are empty: run folder fl45k6c has crm.log 849, smtp.log 655 and stage.log 853 bytes (work/L2.md:331-333). Read 'most'.",
        "L6-FD-016": "Result review round 2: extract.py has no runtime caller in the take, but it is registered in the guard registry (src/hadavin_sdk/guard/producers.py lines 36 and 58) and imported by a test: so it is idle, not dead; never archive it."}
RETYPE = {"L6-FD-016": "idle"}
DEDUP = {"L6-FD-001", "L6-FD-002", "L6-FD-005", "L6-FD-017", "L4c-FD-011", "L4c-FD-012", "L2c-FD-010"}
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
    if c[0] in RETYPE: c[1] = RETYPE[c[0]]
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
touch = sum(1 for c, s in ded if s == "Blocker" and scope(c[0]) in ("take-rig", "cross-lane"))
touch_line = ["", "Rule: a Blocker touches the take when its scope is take-rig or cross-lane and it is not a restated row; build-process and desk rows do not touch the take.", "",
              "| measure | count |", "|---|---|", "| Blockers that touch the take, deduplicated | %d |" % touch, "| Blockers in total, deduplicated | %d |" % dt["Blocker"]]

# ---- job pass (work/L6.md): parsed first because the Fix plan and the headline use it
rows = {}
for l in open(os.path.join(base, "work/L6.md"), encoding="utf-8"):
    m = re.match(r"\| (L6-J-(\d+)) \|", l)
    if m:
        rows[int(m.group(2))] = [x.strip() for x in l.strip().strip("|").split(" | ")]
RANGES = [("STORE", 1, 12), ("LOG", 13, 23), ("FILTER", 24, 33), ("COUNTER", 34, 40), ("RETRY", 41, 50), ("NOTICE", 51, 57), ("OTHER", 58, 59)]
assert sorted(rows) == list(range(1, 60)), "work/L6.md job rows are not exactly L6-J-001..059: %s" % sorted(set(range(1, 60)) ^ set(rows))
APPX = {12, 18, 22, 33, 39, 40, 49, 50, 57, 59}
OWNERLINE = {
 "STORE": "Postgres table mf_leads in the single Postgres of the take (written by the n8n Postgres nodes)",
 "LOG": "n8n execution history in Postgres (DECISION line 16)",
 "FILTER": "the claim insert with ON CONFLICT on mf_leads",
 "COUNTER": "PROOF COUNT: recommended place for the take is stage.journal (the per-lead write-ahead file, DECISION line 17); for the later client portal, core Limits (`src/hadavin_sdk/limits.py:17 \"def charge(self, agent_id: str, usd: Decimal)\"`). What the take proof reads is UNVERIFIED (take repository NOT VISIBLE); this is a proposal to the laptop lead, not a decision",
 "RETRY": "the mf-recovery sweep (every 30 s, lease 120 s, 3 attempts)",
 "NOTICE": "the mf-recovery alert mail for unknown or failed requests",
 "OTHER": "none proposed yet: identities and roles (L6-J-058) have no single place; the laptop lead names one"}
OPEN = {
 "LOG": "Open owner (audit, who approved what): none proposed; the audit place L6-J-014 is NEEDED under L6-EX-05 for the desk and core only.",
 "COUNTER": "Open owner (money cap): none. No place enforces a dollar ceiling for the take in the files seen; stage.journal is a per-lead repeat guard, not a dollar ceiling. The laptop lead names the place before the video (Fix plan row 2).",
 "OTHER": "Open owner (identities and roles): the laptop lead names one; the fix is the three roles of DECISION line 14 plus a migrations identity (Fix plan)."}
SHORT = {"STORE": "table mf_leads in the one Postgres", "LOG": "n8n execution history in Postgres (plan, not done in the rig)",
         "FILTER": "claim insert with ON CONFLICT on mf_leads", "COUNTER": "proof count: stage.journal (proposal, UNVERIFIED); money cap: no place, open",
         "RETRY": "the mf-recovery sweep", "NOTICE": "mf-recovery alert mail (no second channel yet)", "OTHER": "identities and roles: no place, open"}
OWNEV = {
 "STORE": "`handover/system-map/DECISION-one-store.md:7 \"written by the n8n Postgres nodes Claim, Stored\"`",
 "LOG": "`handover/system-map/DECISION-one-store.md:16 \"Logs: one place = Postgres\"`",
 "FILTER": "`handover/demo3/kill/flows-go1/mf-form.json:97 \"ON CONFLICT\"`",
 "COUNTER": "`handover/system-map/DECISION-one-store.md:11 \"the independent count reads them\"`",
 "RETRY": "`handover/demo3/kill/flows-go1/mf-recovery.json:26 \"attempts=attempts+1\"`",
 "NOTICE": "`handover/demo3/kill/flows-go1/mf-recovery.json:196 \"mf-mail-smtp\"`",
 "OTHER": "`handover/system-map/DECISION-one-store.md:14 \"three least-privilege roles\"`"}
CORE = {6, 7, 21, 31, 32, 38, 45, 46, 47, 56, 8, 9, 20, 30, 48, 50, 57}
FORCE = {17: "NOT-NEEDED", 10: "NOT-NEEDED", 40: "DUPLICATE", 18: "DUPLICATE", 58: "NOT-NEEDED", 5: "DUPLICATE", 37: "DUPLICATE"}
BLOCKED = "ARCHIVE BLOCKED until the laptop lead shows which counter the take proof reads, and the desk security patches are applied (L6-EX-11)"
ASKDATA = "KEEP-CORE (callers: guard/producers.py lines 63 and 68, the askdata extra in pyproject.toml, tests/demo_askdata/); archive only after those references move"
PROP = {10: "KEEP (test evidence; Fix plan rows need the rig)", 17: "KEEP (test evidence)", 22: "KEEP (CI)", 33: "KEEP (CI)",
        58: "CHANGE (replace by three least-privilege roles plus a migrations identity, see Fix plan)", 59: "STOP (process waste, not a file)",
        23: "FIX THE HARNESS (it recreates the empty files every run); no archive",
        5: "MERGE-INTO core Limits, only after the place that holds the dollar cap is named; keep until then",
        37: "MERGE-INTO core Limits, only after the place that holds the dollar cap is named; keep until then",
        27: "KEEP until a dated source shows the CRM does this; the keyed upsert keeps crm_rows=1 under retries",
        28: "MERGE-INTO mf-form AFTER THE VIDEO; the key must become source plus id (L2-FD-004: ids from two sources can collide and a request is dropped as a duplicate). The dead if-nodes UnknownNewA and UnknownNew are in mf-sub-crm-mail.json (lines 326 and 358, reviewer-read); both branches go to OutUnknown so they decide nothing: remove them in that file, a separate CHANGE after the video",
        42: "AFTER THE VIDEO: n8n Retry On Fail cannot filter by error type (UNVERIFIED), so the trim is not implementable as written; removing it also makes recovery wait for the 120 s lease",
        8: ASKDATA, 9: ASKDATA, 20: ASKDATA, 30: ASKDATA, 48: ASKDATA,
        50: "CHANGE (keep the weekly cron and tools/mutation_runner.py, which tests use; bound the curl retry at ci.yml line 228 and add a failure notice)",
        57: "KEEP (dependabot.yml and .coderabbit.yaml are live gates; CLAUDE.md lists CodeRabbit as a required pull request gate)",
        4: BLOCKED, 16: BLOCKED, 29: BLOCKED, 36: BLOCKED, 44: BLOCKED, 54: BLOCKED}
CONFLICT = {1, 4, 5, 16, 29, 36, 44, 54}; NOTDONE = {2, 13}; UNDEC = {58}; UNVER = {3, 14}
TEXT = {23: "NOT-NEEDED: most of the 378 log files are empty (run folder fl45k6c has non-empty logs, work/L2.md:331-333); fakes write to events.jsonl",
        20: "KEEP-CORE: has callers (see proposal); the take does not use it. Query text passes clean() (terminal escapes stripped, `ledger.py:3`); whether personal data is masked is UNVERIFIED",
        35: "NEEDED for the per-lead repeat guard only: stage.journal stops a second model call for one request; it is NOT a dollar ceiling (`handover/system-map/DECISION-one-store.md:9 \"file in the take folder (qualify_stage.py)\"`); the place that holds the dollar cap is open",
        47: "KEEP-CORE: no runtime caller in the take, but registered in the guard registry (`src/hadavin_sdk/guard/producers.py:36 \"extract validation errors\"`) and used by a test; never archive"}
EVID = {11: "`handover/system-map/DECISION-one-store.md:11 \"HubSpot (CRM) and Gmail\"`; real HubSpot and Gmail NOT VISIBLE"}
def verdict(n, p):
    if n in CORE: return "KEEP-CORE"
    if n in FORCE: return FORCE[n]
    for v in ["OWNER", "CRM-COULD-DO", "DUPLICATE", "NOT-NEEDED", "NEEDED"]:
        if p.startswith(v) and not (v == "NEEDED" and p.startswith("NOT")): return v
    return "NOT-NEEDED"
def info(n):
    c = rows[n]; name, purpose, ev = c[1], TEXT.get(n, c[2]), EVID.get(n, c[14])
    v = verdict(n, c[2])
    ex = re.search(r"L6-EX-\d+", c[2])
    exid = ex.group(0) if (ex and v == "NEEDED") else "none"
    if v == "NEEDED" and exid == "none": exid = "L6-EX-05"
    m = re.search(r"MERGE-INTO ([^;,.()]+)", c[2])
    if n in PROP: prop = PROP[n]
    elif v == "KEEP-CORE": prop = "KEEP-CORE (out of take scope; no move)"
    elif v in ("OWNER", "NEEDED"): prop = "keep"
    else: prop = "MERGE-INTO " + m.group(1).strip() if m else "ARCHIVE (after the studio head says yes)"
    assert not (prop.startswith("ARCHIVE") and v == "KEEP-CORE"), "row %d: KEEP-CORE code must not be archived" % n
    yes = "no" if re.match(r"(keep|KEEP|STOP|FIX)", prop) else "yes"
    st = ("CONFLICT" if n in CONFLICT else "PLAN NOT DONE" if n in NOTDONE else "UNDECIDED (DECISION line 20)" if n in UNDEC
          else "UNVERIFIED (file not read for this row)" if n in UNVER else "OK")
    if v == "KEEP-CORE" and n not in TEXT: purpose = "Result review: code with callers outside the take, never moved. Lane wording: " + purpose
    if n == 42: purpose += "; the mail node has retryOnFail false (`mf-sub-crm-mail.json:230`), only lines 35 and 91 show 3 tries"
    if n == 43: purpose += "; double-alert window if a send was in flight at a kill (not tested; two n8n at once not tested)"
    return [c[0], name, v, exid, prop, yes, st, purpose, ev]
def render(n):
    return "| %s |" % " | ".join(esc(x) for x in info(n))
def block_ns(key, a, b):
    return [n for n in range(a, b + 1) if n not in APPX]

# ---- Fix plan
W0 = "before Wed 18 Nov (a decision or a config change: no new node, no new identity)"
W1 = "before Wed 18 Nov ONLY if the laptop lead chooses it (changes the proven flows; needs a re-smoke; default: after)"
W3 = "after Wed 18 Nov"
RESMOKE = "Re-smoke pass criterion: 10 test requests give 1 new, 9 duplicates, 1 e-mail and 1 CRM row. Rollback: re-import the exported flow files from git."
ACTIONS = {
 "L1c-FD-001": "run the SonarCloud token only in a job that runs no test code; rotate the token if it was ever on the same runner as test code",
 "L1-FD-021": "rename the tracked files and folders that carry a personal name in the path, in a normal commit; rewriting history is a separate step that needs the studio head's yes"}
# columns: when, ids, action, responsible person, studio head yes, needs a runtime
fixrows = [
 (W0, "L6-FD-001, L2-FD-001, L6-FD-002, L2-FD-002, L2-FD-003", "ONE sequence, stop at the first step that fails: (1) start n8n on the one Postgres (the re-smoke DECISION lines 8, 14 and 18a already plan); (2) run the planted-data check there and write down what n8n stores, who can read it (n8n role or app role) and what is masked; (3) only then switch execution saving on (a config change, not a node); (4) write down the prune and retention setting.", "laptop lead", "yes", "yes"),
 (W0, "L6-FD-003, L6-FD-004, L2-FD-004", "decisions, no change to the flows: name the place that holds the dollar cap for the take (UNVERIFIED, take repository NOT VISIBLE; proposal: stage.journal as the per-request guard, core Limits for the later portal); say what the take proof counter reads; say whether the independent count runs outside n8n and name its identity; check that the take does not use mf-hook (its keys share one key space without a source column).", "laptop lead", "no", "no"),
 (W0, "L1c-FD-021, L1-FD-023", "correct the three live pull request bodies: the final tree is NOT identical to PR #1 (95 files differ)", "laptop lead", "yes", "no"),
 (W1, "L6-FD-017, L2-FD-007, L6-FD-026", "add the missing branch so a request in state review or unknown ends in a mail or alert, and make the recovery sweep alert on its own database error (a new branch and a changed error setting in mf-recovery). " + RESMOKE + " Force one database error: expect 1 alert.", "laptop lead", "no", "yes"),
 (W1, "L6-FD-005, L2-FD-008", "a second alert channel with its own credential, its own path and a heartbeat watched from outside n8n; the laptop lead names the channel and the person who watches it. " + RESMOKE, "laptop lead", "yes", "yes"),
 (W1, "L6-FD-006", "three Postgres roles (n8n, app, read-only count) plus a fourth identity for roles, schemas and migrations, take tables moved to the schema app, and minimum scopes for the count's Gmail and HubSpot credentials. This touches every Postgres credential and every SQL statement, so it needs the full re-smoke (DECISION line 14 says the schema and roles are not in it). The n8n role and the app role both live inside the same n8n, so a compromise of n8n gives both: stated as a limit. DECISION line 14 says three roles; the fourth is proposed here and DECISION is not changed.", "laptop lead", "yes", "yes"),
 (W0, "L2-FD-018", "stop tracking the four creds-lane.json files; rotate anything real and check the rotated values are stand-ins (UNVERIFIED here); the four n8n working folders with encryption keys (about 220 MB in history) and the SQLite files with planted made-up personal data move to archive/ or are untracked, never deleted; history rewrite only on the studio head's yes (exception L6-EX-10)", "studio head", "yes", "no"),
 (W3, "all desk rows marked ARCHIVE BLOCKED", "archive the desk, its portal and retry loops ONLY after the laptop lead shows which counter the take proof reads, and after the pending security patches (L6-EX-11) are applied", "laptop lead", "yes", "no"),
 (W3, "L1-FD-003, L1c-FD-007", "archive superseded patch, PR-text and evidence versions (about 519 KB)", "studio head", "yes", "no"),
 (W3, "L6-FD-019", "reconcile the test counts before quoting any number", "laptop lead", "no", "no"),
 (W3, "L6-J-028, L6-J-042", "merge mf-hook into mf-form (key becomes source plus id) and trim the node retry (n8n Retry On Fail cannot filter by error type: UNVERIFIED)", "laptop lead", "no", "no"),
 (W3, "negative tests (D-M1 of round 2)", "write the negative tests that exist in no file seen: the alert credential, the heartbeat identity, the stage.journal writer, and the count's Gmail and HubSpot scopes (each identity is denied what it must not do)", "laptop lead", "no", "yes"),
]
def first_sentence(t):
    s = t.split("`")[0].strip().rstrip(":;, ")
    if len(s) > 240:
        cut = s[:240].rfind(". ")
        s = s[:cut + 1] if cut > 40 else s[:240].rsplit(" ", 1)[0]
    return s.rstrip(".") + ". (full text: Findings)"
named = " ".join(r[1] for r in fixrows)
blk = [(c, s) for c, s in rows_f if s == "Blocker" and c[0] not in named and c[0] not in DEDUP]
for c, s in blk:
    ev = esc(ACTIONS.get(c[0]) or first_sentence(c[3]))
    yes = "yes" if (c[0] in ACTIONS and re.search(r"credential|token|history", ACTIONS[c[0]], re.I)) or re.search(r"credential|spend|key|desk", ev, re.I) else "no"
    fixrows.append((W0 if yes == "no" else W3 if "desk" in ev.lower() else W0, c[0], ev, "laptop lead" if yes == "no" else "studio head", yes, "no"))
for key, a, b in RANGES:
    todo = []
    for n in range(a, b + 1):
        i = info(n)
        if re.match(r"(MERGE-INTO|CHANGE|FIX|ARCHIVE)", i[4]):
            todo.append("%s: %s" % (i[0], i[4].split(";")[0][:110]))
    if todo:
        fixrows.append((W3, "ONE-PLACE-TABLE.md block %s" % key, "apply the proposals of this block, one at a time: " + "; ".join(todo), "laptop lead", "yes", "no"))
fixrows = [(r[0], r[1], r[2].rstrip().rstrip(".") + ".", r[3], r[4], r[5]) for r in fixrows]
claims = [
 ("the final tree of PRs 2 to 4 is identical to PR #1", "handover/demo/pr-text/github-current/pr3-body.md:5", "VERIFY.md measured 95 files differing (L1c-FD-021)", "CONTRADICTED"),
 ("SonarQube runs on every pull request", "pr4 text v5", "AB-PAPER shows 0 SonarQube jobs since 0841f36 (L1c-FD-002)", "CONTRADICTED"),
 ("n8n runs on Postgres in the take", "DECISION-one-store.md line 14 (a plan)", "kill rig used the default SQLite file (harness.py:34); take flows NOT VISIBLE", "PLAN NOT DONE (rig evidence)"),
 ("execution history is saved in Postgres", "DECISION-one-store.md line 16 (a plan)", "the rig flows set execution saving to none (L6-FD-002)", "PLAN NOT DONE (rig evidence)"),
 ("no lead data reaches n8n's store", "implied by L6-EX-04", "made-up e-mail, name and a key canary were found in n8n files with saving off (L2-FD-002)", "CONTRADICTED (rig)"),
 ("DB_POSTGRESDB_SCHEMA works for import and for start", "DECISION UNVERIFIED item 6", "not run", "UNVERIFIED"),
 ("stage.journal is independent of the flow identity", "DECISION line 17", "nothing shows who can write the file or whether two stage processes run at once", "UNVERIFIED"),
 ("the take has a model-call spend cap", "DECISION line 17 (implied)", "stage.journal is a per-request repeat guard; no dollar-cap place in files seen (take repository NOT VISIBLE)", "UNVERIFIED"),
 ("Postgres sits behind n8n's credential layer (no single dependency)", "DECISION line 18c", "no kind with an alternative is described", "UNVERIFIED"),
 ("the independent count is independent and read-only", "DECISION line 11; ONE-PLACE-TABLE job COUNTER", "the only artefact seen is an n8n Code node stand-in (L6-J-034) run in the same n8n and the same Postgres, checked in node only; a real n8n run is NOT VISIBLE; the count's identity and a test that the count identity can write nothing are in no file seen", "UNVERIFIED"),
 ("every request reaches a terminal state and nothing is sent twice", "studio rule on lost and double messages", "state review gets no mail (L2-FD-007); mf_leads keeps only the latest state (L6-EX-05); the double-send window is untested (L6-EX-07)", "UNVERIFIED"),
 ("single dependency for the take: n8n, the one SMTP server and the model behind stage each have an alternative and a trigger", "ARCHITECTURE-AUDIT-CHECKLIST.md dependency question", "none of the three is described with an alternative; not checked beyond the files seen", "UNVERIFIED"),
 ("SECURITY (egress, retention, redaction), OPS and the workflow walk (kill, restart, out-of-order input, huge input) are answered for the take", "ARCHITECTURE-AUDIT-CHECKLIST.md", "not answered: take repository NOT VISIBLE and no runtime; only the rig kill tests exist", "UNVERIFIED"),
 ("the kill tests prove the money guard", "kill RESULTS", "model_calls=1 is counted from an in-memory fake journal (L6-FD-004)", "UNVERIFIED"),
 ("the DeepSource carry-over holds about 96 distinct findings among 213 comments", "L1c-FD-003", "counted by block, rows not compared one by one", "UNVERIFIED"),
 ("test totals quoted across the lanes (2329, 3138, 4125, 4409 and others)", "L1, L2c, L3, L4", "no lane reconciles them (L6-FD-019)", "UNVERIFIED"),
 ("every file under handover/ was read", "lane Coverage tables", "183 files NOT-READ (L1c 18, L3c 66, L4c 99)", "CONTRADICTED"),
]
HEADLINE = ["## Headline", ""]
for key, a, b in RANGES:
    ns = block_ns(key, a, b)
    vc = Counter(info(n)[2] for n in ns)
    HEADLINE.append("- %s: place = %s; %d rows (%s)." % (key, SHORT[key], len(ns), ", ".join("%s %d" % kv for kv in sorted(vc.items()))))
HEADLINE += ["- Open for the laptop lead: the place that holds the dollar cap, the second alert channel and its watcher, what the take proof counter reads.",
             "- Open for the studio head: key rotation and any history rewrite (Fix plan row 7).",
             "- NOT VISIBLE: the take repository `duplicate-proof-lead-desk`; anything that needs n8n running is UNVERIFIED.", ""]
out = ["# SWEEP: duplicates, dead, idle, inconsistent and unverified parts", "",
 "Static review of the repository on branch cloud/system-map. No n8n runtime, no network: anything needing a runtime is UNVERIFIED. The take code repository `duplicate-proof-lead-desk` is NOT VISIBLE here (the laptop lead covers it locally).", "",
 "**NOT-READ files: L1c 18, L3c 66, L4c 99 (183 in total). Unread means UNVERIFIED, not clean.** The laptop lead may order one more continuation lane for these three lists.", ""] + HEADLINE + [
 "The citation check proves each quoted line exists, not that it supports the claim; support was checked by sample by the result reviewers. Some findings are counted twice by two lanes (see Counts: raw and deduplicated).", "", KEY_TEXT,
 "## Findings", "", "Scope: take-rig = evidence comes from the kill rig, not the take flows; desk (retired from the take) = the older desk program; build-process = patches, pull requests, CI; core or demo = `src/`, `demos/`; cross-lane = the job pass. Default by lane; the evidence cell is the proof.", "",
 "| id | claim type | severity | evidence | conflicts with | job key | scope |", "|---|---|---|---|---|---|---|"]
out += ["| " + " | ".join(esc(x) if i != 3 else x for i, x in enumerate(c)) + " | " + scope(c[0]) + " |" for c, s in rows_f] + [""]
out += ["## Fix plan", "", "Two separate columns: `when` (the date) and `needs studio head yes`. Rows marked ONLY IF THE LAPTOP LEAD CHOOSES IT are not recommended before the video: they add nodes, a channel or identities, and DECISION line 16 says new nodes change the proven flows. Each Blocker has a row; restated Blockers are covered by the row of the finding they restate.", "",
        "| order | when | finding ids | action | responsible person | needs studio head yes | needs a runtime (UNVERIFIED here) |", "|---|---|---|---|---|---|---|"]
for i, r in enumerate(fixrows, 1):
    out.append("| %d | %s |" % (i, " | ".join(esc(x) for x in r)))
EXH = "| id | what | reason | responsible person | removal trigger | decision line ||---|---|---|---|---|---|"
exh = ["| id | what | reason | responsible person | removal trigger | decision line |", "|---|---|---|---|---|---|"]
EX1 = [
 ("L6-EX-01", "n8n internal data (workflows, credentials, execution history)", "second of the three stores DECISION keeps; must run on Postgres, but the kill rig used SQLite", "laptop lead", "n8n data moved to the one Postgres (DECISION line 14; Fix plan row 1)", "DECISION line 14"),
 ("L6-EX-02", "stage.journal file (per-request write-ahead guard against a second model call)", "the one stated exception in DECISION; real file NOT VISIBLE: qualify_stage.py", "laptop lead", "after the video, core store-kind item (DECISION line 17)", "DECISION line 17"),
 ("L6-EX-05", "mf_leads lifecycle rows", "state per request, latest state only: not an append-only history, so it cannot show a double send or a sequence (an event table was ruled out before the video by DECISION line 16). Not accepted until tested: this is a defect with a next step", "laptop lead", "an event table after the video, or the independent count proves no double send", "DECISION line 16"),
 ("L6-EX-07", "alert claim and backoff as helper of the recovery sweep", "stops a second alert for the same request; double-alert window if a send was in flight at a kill (not tested). Not accepted until tested: this is a defect with a next step", "laptop lead", "test: kill a send in flight and count the alerts; re-check if the sweep gets a second channel", "DECISION line 7")]
EX2 = [
 ("L6-EX-03", "HubSpot (CRM) and Gmail", "client systems of record; the take writes to them, the independent count reads them", "client", "not an exception to the one-store rule: it is the client's own system; no removal", "DECISION line 11"),
 ("L6-EX-04", "process output files (n8n output, stage stderr and result.json)", "diagnostics meant to hold no lead data; the claim 'no lead data' is CONTRADICTED by L2-FD-002 (Claims check)", "laptop lead", "not an exception to the one-store rule; the planted-data check in Fix plan row 1 decides what may stay", "DECISION line 10"),
 ("L6-EX-06", "shape check node (Valid regex) in the entry flow", "cheap check before the claim insert; same flow", "laptop lead", "not an exception: part of a flow, no removal", "DECISION line 7"),
 ("L6-EX-08", "request intake mail inside the sub-workflow", "a notice to the sales request's sender, not to our person", "client", "not an exception: part of a flow, no removal", "DECISION line 11"),
 ("L6-EX-09", "proof screens for the video (n8n executions)", "DECISION names these as the screens shown", "laptop lead", "after the video", "DECISION line 18")]
EX3 = [
 ("L6-EX-10", "never-delete rule: three kinds of tracked files", "(a) credential files (creds-lane.json): untracked and rotated, never archived (an archive copy would keep the secret); (b) the four n8n working folders with encryption keys (about 220 MB in history) and (c) the SQLite files with planted made-up personal data: moved to archive/ or untracked, never deleted. Nothing is deleted without the studio head's yes", "studio head", "(a) after rotation and untracking; (b) and (c) after the Postgres move; a history rewrite only on the studio head's yes", "never-delete rule of ARCHITECTURE-AUDIT-CHECKLIST.md"),
 ("L6-EX-11", "stopping or archiving the desk", "L4c-FD-001 (key sent to a vendor), L4c-FD-002 (n8n API key sent to a second server) and L4c-FD-003 (real-spend consent flag) are fixed only in pending patches", "laptop lead", "the three patches are applied", "DECISION line 15")]
out += ["", "## Exceptions", "", "An exception is a second place or a rule departure that we accept on purpose. NEEDED rows in ONE-PLACE-TABLE.md point at these ids. The ids are in three groups; only the first group is a second place the take keeps.", "",
        "Second places the take keeps:", ""] + exh + ["| " + " | ".join(r) + " |" for r in EX1]
out += ["", "Listed so every id resolves, NOT exceptions to the one-store rule:", ""] + exh + ["| " + " | ".join(r) + " |" for r in EX2]
out += ["", "Rule departures:", ""] + exh + ["| " + " | ".join(r) + " |" for r in EX3]
out += ["", "Open question for the laptop lead: the second alert channel and its watcher (Fix plan) has no named responsible person yet.", ""]
out += ["## Claims check", "", "Status: PROVEN = a raw file shows it; CONTRADICTED = a raw file shows the opposite; PLAN NOT DONE = DECISION states a target and the change is not made; UNVERIFIED = needs a runtime or a file not in this box.", "", "| claim | where claimed | evidence | status |", "|---|---|---|---|"] + ["| " + " | ".join(r) + " |" for r in claims] + [""]
out += ["## Lessons", "",
 "- For the audit checklist: check the engine behind every test number (SQLite or Postgres) before quoting it.",
 "- For studio memory: one name per file; the desk money file has four names across lanes.",
 "- For agent briefs: ban unbounded wait loops in test rigs; every quoted test count names its commit.",
 "- For the lane method: a lane that reads about 100 files runs out of context; cap lanes at about 60 files and keep a READ status honest.",
 "- For any ARCHIVE proposal: grep the registry (`src/hadavin_sdk/guard/producers.py`), `pyproject.toml` and `tests/` for callers first; round 2 found five demo rows and two CI rows that would have broken the core guard and the gates.", "",
 "## Counts", "", "Counts of finding rows after re-rating. Raw = every row; deduplicated = minus rows that restate another row.", ""] + counts + touch_line + [""]
bad = [r[1] for r in fixrows if not r[2].rstrip().endswith((".", ")", "?")) and not r[2].startswith("apply the proposals")]
if bad:
    print("Fix plan action cells not ending in a full stop:", bad); sys.exit(1)
SWEEP_TEXT = "\n".join(out)  # written together with ONE-PLACE-TABLE.md at the end, after both are built

# ---- ONE-PLACE-TABLE
HDR = ["| copy | what | verdict | exception | proposal | studio head yes needed | state vs DECISION | reason | evidence |", "|---|---|---|---|---|---|---|---|---|"]
nrows = sum(len(block_ns(k, a, b)) for k, a, b in RANGES)
op = ["# ONE-PLACE-TABLE: one place per job", "",
 "Source of rows: work/L6.md (proposals of the job pass; the laptop lead decides). Every copy except the job owner place, NEEDED rows and KEEP-CORE rows has a proposal. Nothing is deleted, and nothing with a caller is archived. %d rows are in the job blocks and %d build-process rows are in the appendix." % (nrows, len(APPX)), "", KEY_TEXT]
for key, a, b in RANGES:
    op += ["## Job: " + key, "", "Owner: %s | %s | exception: none" % (OWNERLINE[key], OWNEV[key]), ""]
    if key in OPEN and key != "COUNTER":
        op += [OPEN[key], ""]
    if key == "NOTICE":
        op += ["Alert mail (L6-J-051) and request intake mail (L6-J-052) use ONE SMTP credential (mf-mail-smtp) and run inside the same n8n and the same Postgres. If mail, n8n or Postgres is down, nobody is told. Needed: a second channel with its own credential and a heartbeat watched from outside n8n. The second channel has no named responsible person yet: open question for the laptop lead.", ""]
    ns = block_ns(key, a, b)
    mc = [n for n in ns if key == "COUNTER" and n in (35, 37, 38)]
    op += HDR + [render(n) for n in ns if n not in mc] + [""]
    if mc:
        op += ["### Money cap (a second job under the key COUNTER)", "", OPEN["COUNTER"], "",
               "Money-cap place: UNVERIFIED. `stage.journal` is a per-request write-ahead guard against a second model call, not a dollar ceiling (`handover/system-map/DECISION-one-store.md:9 \"file in the take folder (qualify_stage.py)\"`). The desk SpendLedger, the askdata meter and core Limits enforce dollar ceilings (`src/hadavin_sdk/limits.py:17 \"def charge(self, agent_id: str, usd: Decimal)\"`); they are kept until the place is named (question for the laptop lead).", ""] + HDR + [render(n) for n in mc] + [""]
op += ["## Appendix: build-process rows (not places of a take job)", "", "These rows keep job keys because the keys sort every part of the repository (see How to read this file).", ""] + HDR + [render(n) for n in sorted(APPX)] + [""]
op += ["## Seed check against DECISION", "", "| seed row | state in repo | status | evidence |", "|---|---|---|---|",
 "| n8n internal data | kill rig used default SQLite; take flows NOT VISIBLE | PLAN NOT DONE (DECISION line 8 already corrects it) | `handover/demo3/kill/harness.py:34 \"N8N_USER_FOLDER=home\"` |",
 "| Postgres mf_leads | table and claim insert exist in the kill flows; created in the default schema, not schema app; one shared credential | CONSISTENT for the table; CONFLICT for the schema (DECISION line 14) and for roles | `handover/demo3/kill/flows-go1/mf_leads.sql:4 \"CREATE TABLE mf_leads(\"` |",
 "| desk SQLite plus portal | still built, reviewed and soaked | CONFLICT (DECISION line 15) | `handover/system-map/DECISION-one-store.md:15 \"The desk SQLite and its portal are retired from the take\"` |",
 "| stage.journal | real file NOT VISIBLE; rig counts a fake journal | CONSISTENT with DECISION (line 17); proof UNVERIFIED | `handover/demo3/kill/fakes.py:137 \"requests, model_calls, journal, lock\"` |",
 "| process logs | execution saving is none in the rig flows | PLAN NOT DONE (DECISION line 16) | `handover/system-map/DECISION-one-store.md:16 \"Logs: one place = Postgres\"` |",
 "| HubSpot and Gmail | client systems; only a fake CRM in the rig; real run NOT VISIBLE | CONSISTENT with DECISION (line 11); real run UNVERIFIED | `handover/demo3/kill/fakes.py:103 \"hit = next((r for r in rows.values()\"` |", "",
 "## Not visible", "", "| copy | what | verdict | exception | proposal | studio head yes needed | state vs DECISION | reason | evidence |", "|---|---|---|---|---|---|---|---|---|",
 "| TAKE-REPO | duplicate-proof-lead-desk | N/A: not visible | none | N/A: not visible | no | N/A: not visible | not visible, the laptop lead covers it locally; content not guessed | NOT VISIBLE: duplicate-proof-lead-desk |", ""]
if not safe_write(base, "SWEEP.md", SWEEP_TEXT, OVERWRITE_OK):
    print("REFUSED: SWEEP.md was edited by hand or has no record of being generated; use --force to overwrite"); sys.exit(1)
if not safe_write(base, "ONE-PLACE-TABLE.md", "\n".join(op), OVERWRITE_OK):
    print("REFUSED: ONE-PLACE-TABLE.md was edited by hand or has no record of being generated; use --force to overwrite"); sys.exit(1)
print(len(rows_f), "findings;", len(rows), "job rows;", nrows, "in blocks;", len(fixrows), "fix rows; blockers touching the take", touch)
