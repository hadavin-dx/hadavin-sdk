"""Text-only check of the proposed database logins (ROLES-PROPOSAL.md section 4)
against every Postgres query in the flow folders. Reads files only; no database.

It fails (exit 1, one FAIL line each) when:
  - a query touches a table other than mf_leads, or is not SELECT/INSERT/UPDATE
    (or contains DELETE, TRUNCATE, DROP, ALTER, ...);
  - a column a query needs is not granted (uncovered);
  - a grant is wider than the queries need (table-level grant, or a column
    granted that no query of that login uses: "unused grant");
  - a login has no grants in the document, a folder is missing, a flow file is
    not valid JSON, or a folder has zero Postgres nodes.
The grants are PARSED from section 4 of ROLES-PROPOSAL.md (no copy in this
script), so the script and the document cannot silently differ.
Usage: python3 -I check_grants_cover_queries.py [--roles-doc PATH] <flow_folder> [...]
Rough parser: it can miss unusual SQL. The real proof is the database tests."""
import json, re, sys, pathlib

TABLE = "mf_leads"
KINDS = ("select", "insert", "update")
FORBIDDEN = ("delete", "truncate", "drop", "alter", "create", "grant", "revoke", "copy",
             "merge", "call", "execute", "vacuum", "comment")
COLS = ("lead_key email name state claimed_until claim_token attempts crm_id mail_sent "
        "created_at updated_at alert_sent alert_token alert_until alert_attempts").split()
NODE_LOGIN = {("mf-form", "Claim"): "mf_door", ("mf-form", "Stored"): "mf_door",
              ("mf-hook", "Claim"): "mf_door", ("mf-hook", "Stored"): "mf_door",
              ("mf-recovery", "ClaimStuck"): "mf_recover", ("mf-recovery", "MarkFailed"): "mf_recover",
              ("mf-recovery", "AlertClaim"): "mf_alert", ("mf-recovery", "AlertBackoff"): "mf_alert",
              ("mf-recovery", "AlertMark"): "mf_alert"}
SUB = "mf_sub"
DEFAULT_DOC = pathlib.Path(__file__).resolve().parent.parent / "ROLES-PROPOSAL.md"


def toks(s):
    return re.findall(r"[a-z_]+", s)


def parse_grants(doc_path):
    """Return (grants, problems). grants: login -> {select, insert, update: set(cols)}."""
    problems, grants = [], {}
    try:
        text = pathlib.Path(doc_path).read_text(encoding="utf-8")
    except OSError as e:
        return {}, [f"cannot read roles document {doc_path}: {e}"]
    m = re.search(r"^## 4\..*?(?=^## 5\.)", text, re.S | re.M)
    if not m:
        return {}, ["roles document has no section 4"]
    sec = re.sub(r"--[^\n]*", "", m.group(0))
    for g in re.finditer(r"\bGRANT\s+(SELECT|INSERT|UPDATE)\b\s*(\([^)]*\))?\s+ON\s+(?:TABLE\s+)?(\w+)\s+TO\s+([\w,\s]+?);",
                         sec, re.I):
        kind, cols, table, roles = g.group(1).lower(), g.group(2), g.group(3), g.group(4)
        roles = [r.strip() for r in roles.split(",") if r.strip()]
        if table != TABLE:
            problems.append(f"grant on table {table}, only {TABLE} is allowed: {g.group(0)!r}")
            continue
        if cols is None:
            problems.append(f"table-level {kind.upper()} grant (wider than columns) to {roles}")
            continue
        for r in roles:
            grants.setdefault(r, {k: set() for k in KINDS})[kind] |= set(toks(cols))
    return grants, problems


def statements(sql):
    s = re.sub(r"'[^']*'", "''", sql)
    return [p.strip() for p in s.split(";") if p.strip()]


def table_names(stmt):
    s = re.sub(r"\bfor\s+(no\s+key\s+)?(update|share)\b", " ", stmt, flags=re.I)
    names = [m.group(2).lower() for m in re.finditer(r"\b(from|join|into|update)\s+([\w.\"]+)", s, re.I)]
    comma = re.search(r"\bfrom\s+[\w.\"]+(\s+\w+)?\s*,", s, re.I)
    return names, bool(comma)


def analyse(sql):
    """Return (writes_insert, writes_update, reads, errors)."""
    errors = []
    sts = statements(sql)
    if not sts:
        errors.append("empty query")
    for st in sts:
        low = st.lower()
        first = (toks(low) or [""])[0]
        if first not in KINDS:
            errors.append(f"statement kind {first!r} not allowed (SELECT/INSERT/UPDATE only)")
        for w in toks(low):
            if w in FORBIDDEN:
                errors.append(f"forbidden keyword {w.upper()}")
        names, comma = table_names(st)
        for n in names:
            if n != TABLE:
                errors.append(f"touches table {n!r}, only {TABLE} is allowed")
        if comma:
            errors.append("comma-joined tables not allowed")
    s = " ; ".join(sts)
    writes_i, writes_u = set(), set()
    m = re.search(r"insert\s+into\s+\w+\s*\(([^)]*)\)", s, re.I)
    ins_tokens = []
    if m:
        ins_tokens = toks(m.group(1))
        writes_i = {t for t in ins_tokens if t in COLS}
    set_tokens = []
    for m in re.finditer(r"\bset\b(.*?)(?=\bwhere\b|\breturning\b|\bfrom\b|$)", s, re.I | re.S):
        depth, cur, parts = 0, "", []
        for ch in m.group(1):
            depth += ch == "("; depth -= ch == ")"
            if ch == "," and depth == 0: parts.append(cur); cur = ""
            else: cur += ch
        parts.append(cur)
        for p in parts:
            t = re.match(r"\s*([a-z_]+)\s*=", p, re.I)
            if t and t.group(1) in COLS:
                writes_u.add(t.group(1)); set_tokens.append(t.group(1))
    reads = set()
    skip = list(ins_tokens) + set_tokens
    for t in (t for t in toks(s) if t in COLS):
        if t in skip: skip.remove(t)
        else: reads.add(t)
    return writes_i, writes_u, reads, errors


def run(folders, doc, out=print):
    """Return the number of problems; prints one line per node and per problem."""
    bad = 0

    def fail(msg):
        nonlocal bad
        bad += 1
        out("FAIL " + msg)

    grants, problems = parse_grants(doc)
    for p in problems:
        fail(p)
    if not folders:
        fail("no flow folder given")
    for folder in folders:
        label = str(folder).rstrip("/").split("/")[-1]
        fp = pathlib.Path(folder)
        n = 0
        used = {}
        if not fp.is_dir():
            fail(f"{label}: folder does not exist")
            continue
        for f in sorted(fp.glob("mf-*.json")):
            flow = f.stem
            try:
                nodes = json.load(open(f, encoding="utf-8")).get("nodes", [])
                nodes = [x for x in nodes if isinstance(x, dict)]
            except (OSError, ValueError, AttributeError) as e:
                fail(f"{label} {flow}: cannot read flow file ({type(e).__name__}: {e})")
                continue
            for node in nodes:
                if node.get("type") != "n8n-nodes-base.postgres":
                    continue
                q = (node.get("parameters") or {}).get("query", "")
                q = q if isinstance(q, str) else ""
                q = q[1:] if q.startswith("=") else q
                name = node.get("name", "?")
                login = NODE_LOGIN.get((flow, name)) or (SUB if flow == "mf-sub-crm-mail" else None)
                n += 1
                if login is None:
                    fail(f"{label} {flow} {name}: no login mapped"); continue
                wi, wu, rd, errs = analyse(q)
                for e in errs:
                    fail(f"{label} {flow} {name}: {e}")
                if login not in grants:
                    fail(f"{label} {flow} {name}: login {login} has no grants in the document"); continue
                g = grants[login]
                u = used.setdefault(login, {k: set() for k in KINDS})
                u["insert"] |= wi; u["update"] |= wu; u["select"] |= rd
                miss = ([("INSERT", c) for c in sorted(wi - g["insert"])] + [("UPDATE", c) for c in sorted(wu - g["update"])]
                        + [("SELECT", c) for c in sorted(rd - g["select"])])
                if miss:
                    fail(f"{label} {flow} {name} -> {login}: UNCOVERED {miss}")
                elif not errs:
                    out(f"{label} {flow} {name} -> {login}: covered")
        out(f"{label}: {n} postgres nodes")
        if n == 0:
            fail(f"{label}: zero Postgres nodes (nothing was checked)")
        for login, g in sorted(grants.items()):
            u = used.get(login, {k: set() for k in KINDS})
            for k in KINDS:
                extra = sorted(g[k] - u[k])
                if extra:
                    fail(f"{label}: unused grant {k.upper()} {extra} for {login} (no query needs it)")
    out(f"TOTAL PROBLEMS: {bad}")
    return bad


def main(argv):
    doc, args = DEFAULT_DOC, list(argv)
    if args[:1] == ["--roles-doc"]:
        if len(args) < 2:
            print("FAIL --roles-doc needs a path"); return 1
        doc, args = args[1], args[2:]
    return 1 if run(args, doc) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
