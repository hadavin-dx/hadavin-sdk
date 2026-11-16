"""PLAN-002 section 6 checks: empty fields, owner count, coverage, secrets.
Usage: python3 tools/scan_outputs.py <system-map dir>   (exit 1 on any defect; prints one line per defect)"""
import os, re, sys

LANE_HEADS = ["Coverage", "Components", "Stores", "Workflows", "Workflow walk", "Scripts", "Jobs",
              "Credentials", "Docs and tests and folders", "Findings", "Checkpoint"]
KEYS = ["STORE", "LOG", "FILTER", "COUNTER", "RETRY", "NOTICE", "OTHER"]
SECRETS = [r"AKIA[0-9A-Z]{16}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"ghp_[A-Za-z0-9]{36}",
           r"xox[baprs]-[A-Za-z0-9-]{10,}", r"sk-[A-Za-z0-9_-]{20,}", r"github_pat_[A-Za-z0-9_]{20,}", r"gh[ours]_[A-Za-z0-9]{30,}",
           r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", r"[Bb]earer [A-Za-z0-9._~+/=-]{20,}",
           r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}"]
ALLOWED = {"AKIAIOSFODNN7EXAMPLE", "noreply@anthropic.com"}
STATUS = {"READ", "SKIMMED", "NOT-READ"}
OUT_HEADS = {
    "MASTER-MAP.md": ["Components", "Stores", "Workflows", "Workflow walk", "Scripts", "Jobs", "Credentials",
                      "Ports and hosts", "Agents and sessions", "Repos and branches", "Docs", "Tests", "Folders",
                      "Not visible or out of scope"],
    "SWEEP.md": ["Findings", "Fix plan", "Exceptions", "Claims check", "Lessons", "Counts"],
}


def sections(text):
    out, cur = {}, None
    for line in text.splitlines():
        if line.startswith("## "):
            cur = line[3:].strip()
            out[cur] = []
        elif cur is not None:
            out[cur].append(line)
    return out


def table_rows(lines):
    rows = [l for l in lines if l.startswith("|")]
    return [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows[2:]]  # skip header + separator


def empty_fields(name, text, heads):
    d, defects = sections(text), []
    for h in heads:
        if h not in d:
            defects.append(f"{name}: missing heading ## {h}")
            continue
        for r in ([] if h == "Coverage" else table_rows(d[h])):  # Coverage has its own check; note may be empty
            if any(c == "" for c in r):
                defects.append(f"{name}: blank cell in ## {h}: {'|'.join(r)[:80]}")
    return defects


def coverage(name, text):
    d = sections(text).get("Coverage", [])
    rows = table_rows(d)
    bad = [f"{name}: coverage status invalid: {r[:3]}" for r in rows if len(r) < 3 or r[2] not in STATUS]
    if any(len(r) > 2 and r[2] == "NOT-READ" for r in rows) and "PARTIAL" not in text:
        bad.append(f"{name}: has NOT-READ rows but no PARTIAL flag")
    return bad


def owner_count(text):
    defects, d = [], sections_by_job(text)
    for key in KEYS:
        if key not in d:
            continue
        owners = [r for r in d[key] if r.get("_owner")]
        if len(owners) != 1:
            defects.append(f"ONE-PLACE: job {key} has {len(owners)} Owner lines (expected 1)")
        for r in d[key]:
            if r.get("verdict") == "NEEDED" and (r.get("exception") or "none") == "none":
                defects.append(f"ONE-PLACE: job {key} has a NEEDED row without exception id")
    return defects


def missing_jobs(text):
    d = sections_by_job(text)
    return [f"ONE-PLACE: missing section ## Job: {k}" for k in KEYS if k not in d]


def counts_consistent(text):
    """The Findings table must agree with the 'all (raw rows)' row of Counts; a severity outside Blocker/Major/Nit is a defect."""
    d, defects = sections(text), []
    tally = {"Blocker": 0, "Major": 0, "Nit": 0}
    rows = table_rows(d.get("Findings", []))
    for r in rows:
        m = re.match(r"(\w+)", r[2]) if len(r) > 2 else None
        sev = m.group(1) if m else ""
        if sev not in tally:
            defects.append(f"SWEEP: finding {r[0] if r else '?'} has severity {sev!r} (expected Blocker, Major or Nit)")
        else:
            tally[sev] += 1
    raw = [r for r in table_rows(d.get("Counts", [])) if r and r[0].startswith("all (raw rows)")]
    if len(raw) != 1:
        return defects + [f"SWEEP: Counts has {len(raw)} 'all (raw rows)' rows (expected 1)"]
    try:
        got = [int(x) for x in raw[0][1:5]]
    except ValueError:
        return defects + ["SWEEP: Counts 'all (raw rows)' row has a non-number cell"]
    want = [tally["Blocker"], tally["Major"], tally["Nit"], len(rows)]
    if got != want:
        defects.append(f"SWEEP: Counts 'all (raw rows)' says Blocker/Major/Nit/total {got} but the Findings table has {want}")
    return defects


def sections_by_job(text):
    out, key, cols = {}, None, None
    for line in text.splitlines():
        m = re.match(r"## Job: (\w+)", line)
        if m:
            key, cols = m.group(1), None
            out[key] = []
        elif key and line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cols is None:
                cols = [c.lower() for c in cells]
            elif not set("".join(cells)) <= set("-: "):
                row = dict(zip(cols, cells))
                row["verdict"] = row.get("verdict")
                row["exception"] = row.get("exception")
                out[key].append(row)
        elif key and line.startswith("Owner:"):
            out[key].append({"_owner": True})
    return out


def secrets(name, text):
    d = []
    for pat in SECRETS:
        for m in re.finditer(pat, text):
            v = m.group(0)
            if v in ALLOWED:
                continue
            if "@" in v and re.search(r"@(?:[a-z0-9-]+\.)*(?:example\.(?:com|org|net|test)|invalid|test|localhost)$", v):
                continue  # reserved made-up domains (RFC 2606)
            if v.startswith("sk-") and sum(c.isupper() or c.isdigit() for c in v) < 6:
                continue  # an identifier such as sk-address-required-after-v2, not a key
            if True:
                d.append(f"{name}: secret-like value of type {pat[:20]}")
    return d


def run(base):
    defects = []
    for lane in sorted(f for f in os.listdir(os.path.join(base, "work")) if re.fullmatch(r"L\d\w*\.md", f)):
        t = open(os.path.join(base, "work", lane), encoding="utf-8", errors="replace").read()
        defects += empty_fields(lane, t, LANE_HEADS) + coverage(lane, t)
    for f in ("MASTER-MAP.md", "SWEEP.md", "ONE-PLACE-TABLE.md"):
        p = os.path.join(base, f)
        if os.path.exists(p):
            t = open(p, encoding="utf-8", errors="replace").read()
            if f == "ONE-PLACE-TABLE.md":
                defects += missing_jobs(t) + owner_count(t)
            if f == "SWEEP.md":
                defects += counts_consistent(t)
            if f in OUT_HEADS:
                defects += empty_fields(f, t, OUT_HEADS[f])
    skip = {os.path.realpath(os.path.join(base, "tests")), os.path.realpath(os.path.join(base, "tools"))}
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if os.path.realpath(os.path.join(root, d)) not in skip and d != "__pycache__"]
        for f in files:
            if f.endswith((".md", ".tsv", ".json", ".patch", ".txt", ".py", ".sh", ".sql", ".yml", ".yaml", ".env")):
                defects += secrets(os.path.relpath(os.path.join(root, f), base),
                                   open(os.path.join(root, f), encoding="utf-8", errors="replace").read())
    return defects


if __name__ == "__main__":
    res = run(sys.argv[1])
    print("\n".join(res) or "no defects", "\ncount", len(res))
    sys.exit(1 if res else 0)
