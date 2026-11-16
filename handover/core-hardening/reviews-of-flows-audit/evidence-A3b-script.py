#!/usr/bin/python3 -I
# EVIDENCE RUNNER A3b script. Records raw output; never judges.
import json, os, subprocess, shutil, sys, datetime
S = "/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad"
FA = S + "/fa"
PATCHES = {k: f"handover/flows-audit/patches/{v}" for k, v in {
 "F-001": "F-001-one-ddl.patch",
 "F-002": "F-002-take-key-check-and-claim-error-path.patch",
 "F-003": "F-003-runsheet-claims.patch",
 "F-004": "F-004-page-statement-17.patch",
 "F-008": "F-008-save-runs-for--the-take.patch".replace("-for--","-for-")}.items()}
PATCHES["F-008"] = "handover/flows-audit/patches/F-008-save-runs-for-the-take.patch"
GEN = "handover/demo/n8n-mainframe"
ENVBASE = ["env", "-i", "PATH=/usr/bin:/bin", "HOME=/nonexistent"]
BUILDS = [
 (["MF_REAL=1","MF_V4=1","MF_TRIES=2","MF_TMO_MS=10000"], "../n8n-flows-real-v5", ["PG_CREDENTIAL_ID","SMTP_CREDENTIAL_ID","SUB_WORKFLOW_ID","45","HS_CRED_PLACEHOLDER"]),
 (["MF_V4=1","MF_TRIES=2","MF_TMO_MS=10000"], "../n8n-flows-film-v5", ["PG_CREDENTIAL_ID","SMTP_CREDENTIAL_ID","SUB_WORKFLOW_ID","45"]),
]
FOLDERS = ("n8n-flows-real-v5", "n8n-flows-film-v5")
FILES = ("mf-form", "mf-hook", "mf-recovery", "mf-sub-crm-mail")
out = []
def P(s=""): out.append(s)
def run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    P(f"$ (cwd={cwd}) {' '.join(cmd)}\nexit={r.returncode}")
    if r.stdout.strip(): P("stdout:\n" + r.stdout.rstrip())
    else: P("stdout: (empty)")
    if r.stderr.strip(): P("stderr:\n" + r.stderr.rstrip())
    else: P("stderr: (empty)")
    return r.returncode
def fresh(name):
    d = f"{S}/{name}"
    if os.path.exists(d): shutil.rmtree(d)
    shutil.copytree(FA, d, symlinks=True)
    for c in (["git","init","-q"],["git","add","-A"],["git","-c","user.name=ev","-c","user.email=ev@example.invalid","commit","-q","-m","baseline"]):
        subprocess.run(c, cwd=d, capture_output=True, text=True, check=True)
    return d
def apply(d, ids):
    rc = {}
    for i in ids:
        P(f"-- apply {i} in {os.path.basename(d)}")
        rc[i] = run(["git","apply","-p1","-v",PATCHES[i]], d)
    return rc
def rebuild(d):
    rcs = []
    for envs, outdir, args in BUILDS:
        rcs.append(run(ENVBASE + envs + ["/usr/bin/python3","build_mainframe.py",outdir] + args, f"{d}/{GEN}"))
    return rcs
def load(d, f, v):
    return json.load(open(f"{d}/handover/demo/{v}/{f}.json"))
def nm(d): return {n["name"]: n for n in d["nodes"]}
def cs(d):
    s = set()
    for a, o in d.get("connections", {}).items():
        for t, lists in o.items():
            for i, l in enumerate(lists):
                for c in l: s.add((a, t, i, c["node"], c["type"], c["index"]))
    return s
def short(x): return json.dumps(x, sort_keys=True)[:400]
def compare(da, db, la, lb):
    """rows of differences: a=reference (la), b=other (lb). Returns list of row strings."""
    rows = []
    for v in FOLDERS:
        for f in FILES:
            try:
                a, b = load(da, f, v), load(db, f, v)
            except Exception as e:
                rows.append(f"{v}/{f}.json | UNVERIFIED | cannot load: {e!r}"); continue
            na, nb = nm(a), nm(b); ca, cb = cs(a), cs(b)
            for k in sorted(set(na)-set(nb)): rows.append(f"{v}/{f}.json | node only in {la} | {k}")
            for k in sorted(set(nb)-set(na)): rows.append(f"{v}/{f}.json | node only in {lb} | {k}")
            for c in sorted(ca-cb): rows.append(f"{v}/{f}.json | connection only in {la} | {c}")
            for c in sorted(cb-ca): rows.append(f"{v}/{f}.json | connection only in {lb} | {c}")
            for k in sorted(set(na)&set(nb)):
                if na[k] != nb[k]:
                    for key in sorted(set(na[k])|set(nb[k])):
                        if na[k].get(key) != nb[k].get(key):
                            rows.append(f"{v}/{f}.json | node {k} field {key} differs | {la}={short(na[k].get(key))} || {lb}={short(nb[k].get(key))}")
            for key in sorted((set(a)|set(b)) - {"nodes","connections"}):
                if a.get(key) != b.get(key):
                    if isinstance(a.get(key), dict) and isinstance(b.get(key), dict):
                        for sk in sorted(set(a[key])|set(b[key])):
                            if a[key].get(sk) != b[key].get(sk):
                                rows.append(f"{v}/{f}.json | top-level {key}.{sk} differs | {la}={short(a[key].get(sk))} || {lb}={short(b[key].get(sk))}")
                    else:
                        rows.append(f"{v}/{f}.json | top-level {key} differs | {la}={short(a.get(key))} || {lb}={short(b.get(key))}")
    return rows
def table(rows, label):
    P(f"### {label}: {len(rows)} difference row(s)")
    if not rows: P("(no differences found by this comparison)")
    for i, r in enumerate(rows, 1): P(f"{i}. {r}")

P("# evidence-A3b (baseline and independence; supplement to evidence-A3.md)")
P("date UTC: " + datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M"))
P(f"target (read-only, no .git, head sha as given in the brief, not verified by me): {FA} (cloud/flows-audit 35235ace26a516d932e73542c235875f390f333d)")
P("Generator environment: env -i PATH=/usr/bin:/bin HOME=/nonexistent plus the MF_* variables of each README line; python /usr/bin/python3; cwd = <copy>/handover/demo/n8n-mainframe (the folder the V5-README says: 'run in the n8n-mainframe folder').")
P("Each fresh copy: cp -r of fa, then git init + one commit 'baseline' inside the copy only.\n")

P("## Step 1: BASELINE (work-base, no patch)")
base = fresh("work-base")
rc = rebuild(base)
P(f"rebuild exit codes: {rc}")
P("### Baseline rebuilt vs committed v5 JSON in fa (all 8 files)")
table(compare(FA, base, "committed", "rebuilt-base"), "baseline vs committed")

P("\n## Step 2: PRISTINE per patch (each on its own fresh copy)")
for pid in ("F-001","F-002","F-003","F-004","F-008"):
    d = fresh("work-" + pid.lower().replace("-",""))
    P(f"\n### {pid} in {d}")
    arc = apply(d, [pid])
    if pid in ("F-002","F-008"):
        P(f"rebuild after {pid} only:")
        rb = rebuild(d); P(f"rebuild exit codes: {rb}")
        table(compare(base, d, "baseline-rebuild", f"{pid}-rebuild"), f"{pid} rebuild vs BASELINE rebuild")
    else:
        P("(no rebuild requested for this patch)")

P("\n## Step 3: PAIRS (reverse order: F-008 alone, then F-002 on top)")
d = fresh("work-pair-f008-f002")
apply(d, ["F-008"])
apply(d, ["F-002"])
rb = rebuild(d); P(f"rebuild exit codes: {rb}")
table(compare(base, d, "baseline-rebuild", "pair-rebuild"), "pair F-008 then F-002 vs BASELINE rebuild")
P("\n### same pair in forward order (F-002 then F-008), extra, for contrast")
d2 = fresh("work-pair-f002-f008")
apply(d2, ["F-002"]); apply(d2, ["F-008"])
rb = rebuild(d2); P(f"rebuild exit codes: {rb}")
table(compare(base, d2, "baseline-rebuild", "pair-fwd-rebuild"), "pair F-002 then F-008 vs BASELINE rebuild")

P("\n## Step 4: CUMULATIVE (F-001, F-002, F-003, F-004, F-008)")
d = fresh("work-cum")
apply(d, ["F-001","F-002","F-003","F-004","F-008"])
rb = rebuild(d); P(f"rebuild exit codes: {rb}")
table(compare(base, d, "baseline-rebuild", "cumulative-rebuild"), "cumulative vs BASELINE rebuild")

P("\n## Step 5: F-001 mf_leads.sql")
d = f"{S}/work-f001"
P("### git diff of mf_leads.sql in work-f001 (changed lines)")
r = subprocess.run(["git","diff","-U0","--","handover/demo/n8n-flows/mf_leads.sql"], cwd=d, capture_output=True, text=True)
P(r.stdout.rstrip() or "(empty)")
P("### other files in fa mentioning names touched by F-001 (patch only adds columns alert_sent, alert_token, alert_until, alert_attempts and a NOTE; it renames or adds NO constraint or index; the only existing named object in the DDL is the PRIMARY KEY on lead_key, unnamed)")
for pat in ("alert_attempts","alert_until","alert_token","alert_sent","mf_leads_pkey","CREATE INDEX","CONSTRAINT"):
    r = subprocess.run(["grep","-rIl","--exclude-dir=.git","-e",pat,"handover/demo","handover/flows-audit"], cwd=FA, capture_output=True, text=True)
    files = [x for x in r.stdout.split("\n") if x]
    P(f"- pattern {pat!r} (grep -rIl under handover/demo and handover/flows-audit): {len(files)} file(s)")
    for x in files[:60]: P(f"    {x}")
    if len(files) > 60: P(f"    ... {len(files)-60} more")
r = subprocess.run(["grep","-rIn","--exclude-dir=.git","-e","mf_leads","-e","CREATE TABLE","handover/demo/n8n-flows/mf_leads.sql"], cwd=FA, capture_output=True, text=True)
P("### mf_leads.sql in fa: lines with CREATE/INDEX/CONSTRAINT/UNIQUE/PRIMARY")
r = subprocess.run(["grep","-nEi","create |index|constraint|unique|primary","handover/demo/n8n-flows/mf_leads.sql"], cwd=FA, capture_output=True, text=True)
P(r.stdout.rstrip() or "(none)")
open("/home/user/hadavin-sdk/handover/core-hardening/reviews-of-flows-audit/evidence-A3b.md","w").write("\n".join(out)+"\n")
print("done", len(out))
