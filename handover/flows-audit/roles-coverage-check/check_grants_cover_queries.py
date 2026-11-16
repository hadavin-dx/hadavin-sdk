"""Text-only check of the proposed database logins (ROLES-PROPOSAL.md section 4)
against every Postgres query in the flow folders. Reads files only; no database.

It fails (exit 1, one FAIL line each) when:
  - a query touches a table other than mf_leads, or is not SELECT/INSERT/UPDATE
    (or contains DELETE, TRUNCATE, DROP, ALTER, ...);
  - a column a query needs is not granted (uncovered);
  - a grant is wider than the queries need (table-level grant, or a column
    granted that no query of that login uses: "unused grant");
  - a login has no grants in the document, a folder is missing, a flow file is
    not valid JSON, a folder has zero Postgres nodes, or ONE FILE has none;
  - a node that is not the checked Postgres node still holds database access:
    a database-type node (MySQL, postgresTool, MSSQL, Mongo, ...) or any text
    (Code, Set, HTTP ... any parameter) that looks like SQL or names mf_leads.
The grants are PARSED from section 4 of ROLES-PROPOSAL.md (no copy in this
script), so the script and the document cannot silently differ.
Also fails: a folder that does not hold exactly the 4 flow files and 14 Postgres nodes; a
Postgres node whose operation is not executeQuery, whose query is an n8n expression
(starts with "="), or that has no credential; SELECT *, RETURNING *, INSERT without a
column list, UPDATE ... FROM, WITH (CTE), quoted names. Columns are matched ignoring case.
With --require-new-credentials: each node's credential must be the one the document
(section 3 table) names for its login, and never the old shared one.
Usage: python3 -I check_grants_cover_queries.py [--roles-doc PATH] [--require-new-credentials] <flow_folder> [...]
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
EXPECTED_FLOWS = {"mf-form", "mf-hook", "mf-recovery", "mf-sub-crm-mail"}
EXPECTED_PG_NODES = 14      # per folder; a different count means a wrong folder or a changed flow
OLD_CREDENTIAL = "n8n-publish-pg"   # the shared login the proposal replaces
PG_TYPE = "n8n-nodes-base.postgres"
# any node type containing one of these is a database door the check does not read
DB_TYPE_WORDS = ("postgres", "mysql", "mariadb", "mssql", "sql", "oracle", "mongo", "redis",
                 "snowflake", "bigquery", "cockroach", "timescale", "questdb", "supabase",
                 "database", "dynamo", "cassandra", "elastic", "sqlite", "db2")
SQL_TEXT = re.compile(
    r"\bselect\b[^;]*\bfrom\b|\binsert\s+into\b|\bupdate\s+[\w.\"]+\s+set\b|\bdelete\s+from\b"
    r"|\bdrop\s+(table|schema|database|role|user|index|view)\b|\btruncate\b|\balter\s+(table|role|user)\b"
    r"|\bcreate\s+(table|role|user|index|view|function)\b|\bgrant\s+\w+.*\bto\b|\bmf_leads\b",
    re.I | re.S)
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


def strings(obj):
    """Every text value inside a parameter tree (keys are not text to check)."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from strings(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from strings(v)


def foreign_db_access(node):
    """Reasons why a node that is NOT the checked Postgres node still holds database access."""
    why = []
    t = str(node.get("type", ""))
    if any(w in t.lower() for w in DB_TYPE_WORDS):
        why.append(f"database node type {t!r} (only {PG_TYPE} is read by this check)")
    for txt in strings([node.get("parameters"), node.get("notes")]):
        m = SQL_TEXT.search(txt)
        if m:
            why.append(f"SQL-like text in a {t!r} node ({m.group(0)[:30]!r}); the check reads only {PG_TYPE} nodes")
            break
    return why


def parse_credentials(doc_path):
    """login -> n8n credential name, from the login table of the roles document."""
    try:
        text = pathlib.Path(doc_path).read_text(encoding="utf-8")
    except OSError:
        return {}
    out = {}
    for m in re.finditer(r"^\|\s*(mf_\w+)\s*\|[^\n]*\|\s*`([^`]+)`[^|\n]*\|\s*$", text, re.M):
        out[m.group(1)] = m.group(2)
    return out


def paren_free(sql):
    """The statement with every (...) group removed, so only its top level is left."""
    prev = None
    while prev != sql:
        prev, sql = sql, re.sub(r"\([^()]*\)", " ", sql)
    return sql


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
        if '"' in st:
            errors.append("quoted name not allowed (a quoted name hides the real table or column)")
        if re.search(r"\bwith\b", low):
            errors.append("WITH (CTE) not allowed")
        if re.search(r"\bselect\s+(distinct\s+)?\*|\breturning\s+\*|,\s*\*\s*(from\b|,|;|$)|\w\.\*", low):
            errors.append("SELECT * / RETURNING * not allowed (name the columns)")
        if first == "insert" and not re.match(r"\s*insert\s+into\s+[\w.]+\s*\(", low):
            errors.append("INSERT without a column list not allowed")
        if first == "update" and re.search(r"\bfrom\b", paren_free(low)):
            errors.append("UPDATE ... FROM not allowed")
        names, comma = table_names(st)
        for n in names:
            if n != TABLE:
                errors.append(f"touches table {n!r}, only {TABLE} is allowed")
        if comma:
            errors.append("comma-joined tables not allowed")
    s = " ; ".join(sts).lower()
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


def run(folders, doc, out=print, require_new_cred=False):
    """Return the number of problems; prints one line per node and per problem."""
    bad = 0

    def fail(msg):
        nonlocal bad
        bad += 1
        out("FAIL " + msg)

    grants, problems = parse_grants(doc)
    creds = parse_credentials(doc)
    if require_new_cred and not creds:
        problems.append("--require-new-credentials: no login/credential table found in the roles document")
    for p in problems:
        fail(p)
    if not folders:
        fail("no flow folder given")
    for folder in folders:
        label = str(folder).rstrip("/").split("/")[-1]
        fp = pathlib.Path(folder)
        n = 0
        seen_files = set()
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
            file_pg = 0
            seen_files.add(flow)
            for node in nodes:
                if node.get("type") != PG_TYPE:
                    for why in foreign_db_access(node):
                        fail(f"{label} {flow} {node.get('name', '?')}: {why}")
                    continue
                file_pg += 1
                params = node.get("parameters") or {}
                q = params.get("query", "")
                q = q if isinstance(q, str) else ""
                name = node.get("name", "?")
                if params.get("operation") != "executeQuery":
                    fail(f"{label} {flow} {name}: operation is {params.get('operation')!r}, only executeQuery is checked")
                if q.startswith("="):
                    fail(f"{label} {flow} {name}: query is an n8n expression (starts with '='); the real SQL is not visible to this check")
                    q = q[1:]
                cred = ((node.get("credentials") or {}).get("postgres") or {}).get("name")
                login = NODE_LOGIN.get((flow, name)) or (SUB if flow == "mf-sub-crm-mail" else None)
                n += 1
                if login is None:
                    fail(f"{label} {flow} {name}: no login mapped"); continue
                if not cred:
                    fail(f"{label} {flow} {name}: no postgres credential on the node")
                elif require_new_cred:
                    if cred == OLD_CREDENTIAL:
                        fail(f"{label} {flow} {name}: still uses the old shared credential {OLD_CREDENTIAL!r}")
                    elif cred != creds.get(login):
                        fail(f"{label} {flow} {name}: credential {cred!r} is not {creds.get(login)!r} (the one for {login})")
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
            if file_pg == 0:
                fail(f"{label} {flow}: this file has zero Postgres nodes (nothing in it was checked)")
        out(f"{label}: {n} postgres nodes")
        if seen_files != EXPECTED_FLOWS:
            fail(f"{label}: flow files are {sorted(seen_files)}, expected {sorted(EXPECTED_FLOWS)}")
        if n != EXPECTED_PG_NODES:
            fail(f"{label}: {n} postgres nodes, expected {EXPECTED_PG_NODES} (wrong folder or changed flow)")
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
    doc, args, newc = DEFAULT_DOC, list(argv), False
    while args[:1] and args[0].startswith("--"):
        if args[0] == "--require-new-credentials":
            newc, args = True, args[1:]
        elif args[0] == "--roles-doc":
            if len(args) < 2:
                print("FAIL --roles-doc needs a path"); return 1
            doc, args = args[1], args[2:]
        else:
            print(f"FAIL unknown option {args[0]}"); return 1
    return 1 if run(args, doc, require_new_cred=newc) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
