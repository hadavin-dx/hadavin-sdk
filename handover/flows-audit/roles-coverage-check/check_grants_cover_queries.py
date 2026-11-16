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
Round 5: a flow file must be an object whose "nodes" is a list of objects (name and type text,
parameters, credentials objects), at most 5 MB (the roles document too); anything else is one
clean FAIL line, never a traceback. SQL-like text in the notes or any other parameter of a Postgres
node is flagged (only its query field is read). A disabled Postgres node is flagged (it is still
checked as if enabled). A forbidden keyword inside a string literal, a dollar-quoted string and an
unbalanced quote are flagged (the check cannot tell data from SQL there; pass values as parameters).
Rough parser: it can miss unusual SQL. The real proof is the database tests."""

import json
import pathlib
import re
import sys

TABLE = "mf_leads"
MAX_FILE_BYTES = 5 * 1024 * 1024  # a flow file or the roles document above this is refused unread
KINDS = ("select", "insert", "update")
FORBIDDEN = (
    "delete",
    "truncate",
    "drop",
    "alter",
    "create",
    "grant",
    "revoke",
    "copy",
    "merge",
    "call",
    "execute",
    "vacuum",
    "comment",
)
COLS = [
    "lead_key",
    "email",
    "name",
    "state",
    "claimed_until",
    "claim_token",
    "attempts",
    "crm_id",
    "mail_sent",
    "created_at",
    "updated_at",
    "alert_sent",
    "alert_token",
    "alert_until",
    "alert_attempts",
]
NODE_LOGIN = {
    ("mf-form", "Claim"): "mf_door",
    ("mf-form", "Stored"): "mf_door",
    ("mf-hook", "Claim"): "mf_door",
    ("mf-hook", "Stored"): "mf_door",
    ("mf-recovery", "ClaimStuck"): "mf_recover",
    ("mf-recovery", "MarkFailed"): "mf_recover",
    ("mf-recovery", "AlertClaim"): "mf_alert",
    ("mf-recovery", "AlertBackoff"): "mf_alert",
    ("mf-recovery", "AlertMark"): "mf_alert",
}
SUB = "mf_sub"
EXPECTED_FLOWS = {"mf-form", "mf-hook", "mf-recovery", "mf-sub-crm-mail"}
EXPECTED_PG_NODES = 14  # per folder; a different count means a wrong folder or a changed flow
OLD_CREDENTIAL = "n8n-publish-pg"  # the shared login the proposal replaces
PG_TYPE = "n8n-nodes-base.postgres"
# what a surprising file shape can raise; main() turns these into one FAIL line, never a traceback
UNEXPECTED = (OSError, ValueError, LookupError, TypeError, AttributeError, RecursionError)
# any node type containing one of these is a database door the check does not read
DB_TYPE_WORDS = (
    "postgres",
    "mysql",
    "mariadb",
    "mssql",
    "sql",
    "oracle",
    "mongo",
    "redis",
    "snowflake",
    "bigquery",
    "cockroach",
    "timescale",
    "questdb",
    "supabase",
    "database",
    "dynamo",
    "cassandra",
    "elastic",
    "sqlite",
    "db2",
)
SQL_TEXT = re.compile(
    r"\bselect\b[^;]*\bfrom\b|\binsert\s+into\b|\bupdate\s+[\w.\"]+\s+set\b|\bdelete\s+from\b"
    r"|\bdrop\s+(table|schema|database|role|user|index|view)\b|\btruncate\b|\balter\s+(table|role|user)\b"
    r"|\bcreate\s+(table|role|user|index|view|function)\b|\bgrant\s+\w+.*\bto\b|\bmf_leads\b",
    re.IGNORECASE | re.DOTALL,
)
DEFAULT_DOC = pathlib.Path(__file__).resolve().parent.parent / "ROLES-PROPOSAL.md"


def type_name(x):
    return "null" if x is None else type(x).__name__


def read_limited(path):
    """Return (text, problem). A file over MAX_FILE_BYTES is refused before it is read."""
    try:
        size = pathlib.Path(path).stat().st_size
        if size > MAX_FILE_BYTES:
            return None, f"file is {size} bytes, over the {MAX_FILE_BYTES} byte limit (not read)"
        return pathlib.Path(path).read_text(encoding="utf-8"), None
    except (OSError, ValueError) as e:
        return None, f"{type(e).__name__}: {e}"


def flow_nodes(path):
    """Return (nodes, problems) for one flow file; every malformed shape is a problem line."""
    text, why = read_limited(path)
    if why:
        return None, [f"cannot read flow file ({why})"]
    try:
        data = json.loads(text)
    except (ValueError, RecursionError) as e:
        return None, [f"cannot read flow file ({type(e).__name__}: {e})"]
    if not isinstance(data, dict):
        return None, [f"malformed flow file: top level is {type_name(data)}, expected an object"]
    raw = data.get("nodes")
    if not isinstance(raw, list):
        return None, [f"malformed flow file: 'nodes' is {type_name(raw)}, expected a list"]
    nodes, problems = [], []
    for i, x in enumerate(raw):
        if not isinstance(x, dict):
            problems.append(f"malformed node {i}: it is {type_name(x)}, expected an object")
            continue
        bad = [
            f"'{k}' is {type_name(x[k])}, expected text"
            for k in ("name", "type")
            if k in x and not isinstance(x[k], str)
        ]
        bad += [
            f"'{k}' is {type_name(x[k])}, expected an object"
            for k in ("parameters", "credentials")
            if x.get(k) is not None and not isinstance(x[k], dict)
        ]
        cr = x.get("credentials")
        if (
            isinstance(cr, dict)
            and cr.get("postgres") is not None
            and not isinstance(cr["postgres"], dict)
        ):
            bad.append(f"credentials.postgres is {type_name(cr['postgres'])}, expected an object")
        if bad:
            problems.append(f"malformed node {i} ({x.get('name', '?')!s:.40}): " + "; ".join(bad))
            continue
        nodes.append(x)
    return nodes, problems


def toks(s):
    return re.findall(r"[a-z_]+", s)


def parse_grants(doc_path):
    """Return (grants, problems). grants: login -> {select, insert, update: set(cols)}."""
    problems, grants = [], {}
    text, why = read_limited(doc_path)
    if why:
        return {}, [f"cannot read roles document {doc_path}: {why}"]
    m = re.search(r"^## 4\..*?(?=^## 5\.)", text, re.DOTALL | re.MULTILINE)
    if not m:
        return {}, ["roles document has no section 4"]
    sec = re.sub(r"--[^\n]*", "", m.group(0))
    for g in re.finditer(
        r"\bGRANT\s+(SELECT|INSERT|UPDATE)\b\s*(\([^)]*\))?\s+ON\s+(?:TABLE\s+)?(\w+)\s+TO\s+([\w,\s]+?);",
        sec,
        re.IGNORECASE,
    ):
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
            why.append(
                f"SQL-like text in a {t!r} node ({m.group(0)[:30]!r}); the check reads only {PG_TYPE} nodes"
            )
            break
    return why


def stray_sql_in_postgres_node(node):
    """SQL-like text in a Postgres node outside its query field (notes, other parameters)."""
    params = {k: v for k, v in (node.get("parameters") or {}).items() if k != "query"}
    for txt in strings([params, node.get("notes")]):
        m = SQL_TEXT.search(txt)
        if m:
            return (
                f"SQL-like text ({m.group(0)[:30]!r}) in the notes or another parameter of a Postgres "
                "node; only its query field is checked, so move the text out or into the query"
            )
    return None


def parse_credentials(doc_path):
    """login -> n8n credential name, from the login table of the roles document."""
    text, why = read_limited(doc_path)
    if why:
        return {}
    out = {}
    for m in re.finditer(
        r"^\|\s*(mf_\w+)\s*\|[^\n]*\|\s*`([^`]+)`[^|\n]*\|\s*$", text, re.MULTILINE
    ):
        out[m.group(1)] = m.group(2)
    return out


def paren_free(sql):
    """The statement with every (...) group removed, so only its top level is left."""
    prev = None
    while prev != sql:
        prev, sql = sql, re.sub(r"\([^()]*\)", " ", sql)
    return sql


LITERAL = re.compile(r"'(?:[^']|'')*'")
DOLLAR_QUOTE = re.compile(r"\$(?:[A-Za-z_]\w*)?\$")


def statements(sql):
    s = LITERAL.sub("''", sql)
    return [p.strip() for p in s.split(";") if p.strip()]


def table_names(stmt):
    s = re.sub(r"\bfor\s+(no\s+key\s+)?(update|share)\b", " ", stmt, flags=re.IGNORECASE)
    names = [
        m.group(2).lower()
        for m in re.finditer(r"\b(from|join|into|update)\s+([\w.\"]+)", s, re.IGNORECASE)
    ]
    comma = re.search(r"\bfrom\s+[\w.\"]+(\s+\w+)?\s*,", s, re.IGNORECASE)
    return names, bool(comma)


def analyse(sql):
    """Return (writes_insert, writes_update, reads, errors)."""
    errors = []
    sts = statements(sql)
    if not sts:
        errors.append("empty query")
    if DOLLAR_QUOTE.search(sql):
        errors.append("dollar-quoted string not allowed (its body is not read by this check)")
    if "'" in LITERAL.sub("", sql):
        errors.append("unbalanced single quote (the rest of the query cannot be read)")
    for lit in LITERAL.findall(sql):
        for w in sorted({w for w in toks(lit.lower()) if w in FORBIDDEN}):
            errors.append(
                f"forbidden keyword {w.upper()} inside a string literal "
                "(the check cannot tell data from SQL; pass it as a parameter)"
            )
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
        if re.search(
            r"\bselect\s+(distinct\s+)?\*|\breturning\s+\*|,\s*\*\s*(from\b|,|;|$)|\w\.\*", low
        ):
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
    m = re.search(r"insert\s+into\s+\w+\s*\(([^)]*)\)", s, re.IGNORECASE)
    ins_tokens = []
    if m:
        ins_tokens = toks(m.group(1))
        writes_i = {t for t in ins_tokens if t in COLS}
    set_tokens = []
    for m in re.finditer(
        r"\bset\b(.*?)(?=\bwhere\b|\breturning\b|\bfrom\b|$)", s, re.IGNORECASE | re.DOTALL
    ):
        depth, cur, parts = 0, "", []
        for ch in m.group(1):
            depth += ch == "("
            depth -= ch == ")"
            if ch == "," and depth == 0:
                parts.append(cur)
                cur = ""
            else:
                cur += ch
        parts.append(cur)
        for p in parts:
            t = re.match(r"\s*([a-z_]+)\s*=", p, re.IGNORECASE)
            if t and t.group(1) in COLS:
                writes_u.add(t.group(1))
                set_tokens.append(t.group(1))
    reads = set()
    skip = list(ins_tokens) + set_tokens
    for t in (t for t in toks(s) if t in COLS):
        if t in skip:
            skip.remove(t)
        else:
            reads.add(t)
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
        problems.append(
            "--require-new-credentials: no login/credential table found in the roles document"
        )
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
            nodes, shape_problems = flow_nodes(f)
            for sp in shape_problems:
                fail(f"{label} {flow}: {sp}")
            if nodes is None:
                continue
            file_pg = 0
            seen_files.add(flow)
            for node in nodes:
                if node.get("type") != PG_TYPE:
                    for why in foreign_db_access(node):
                        fail(f"{label} {flow} {node.get('name', '?')}: {why}")
                    continue
                file_pg += 1
                if node.get("disabled") not in (None, False):
                    fail(
                        f"{label} {flow} {node.get('name', '?')}: node is disabled "
                        f"({node.get('disabled')!r}); it is checked as if enabled, remove it or enable it"
                    )
                stray = stray_sql_in_postgres_node(node)
                if stray:
                    fail(f"{label} {flow} {node.get('name', '?')}: {stray}")
                params = node.get("parameters") or {}
                q = params.get("query", "")
                q = q if isinstance(q, str) else ""
                name = node.get("name", "?")
                if params.get("operation") != "executeQuery":
                    fail(
                        f"{label} {flow} {name}: operation is {params.get('operation')!r}, only executeQuery is checked"
                    )
                if q.startswith("="):
                    fail(
                        f"{label} {flow} {name}: query is an n8n expression (starts with '='); the real SQL is not visible to this check"
                    )
                    q = q[1:]
                cred = ((node.get("credentials") or {}).get("postgres") or {}).get("name")
                login = NODE_LOGIN.get((flow, name)) or (SUB if flow == "mf-sub-crm-mail" else None)
                n += 1
                if login is None:
                    fail(f"{label} {flow} {name}: no login mapped")
                    continue
                if not cred:
                    fail(f"{label} {flow} {name}: no postgres credential on the node")
                elif require_new_cred:
                    if cred == OLD_CREDENTIAL:
                        fail(
                            f"{label} {flow} {name}: still uses the old shared credential {OLD_CREDENTIAL!r}"
                        )
                    elif cred != creds.get(login):
                        fail(
                            f"{label} {flow} {name}: credential {cred!r} is not {creds.get(login)!r} (the one for {login})"
                        )
                wi, wu, rd, errs = analyse(q)
                for e in errs:
                    fail(f"{label} {flow} {name}: {e}")
                if login not in grants:
                    fail(f"{label} {flow} {name}: login {login} has no grants in the document")
                    continue
                g = grants[login]
                u = used.setdefault(login, {k: set() for k in KINDS})
                u["insert"] |= wi
                u["update"] |= wu
                u["select"] |= rd
                miss = (
                    [("INSERT", c) for c in sorted(wi - g["insert"])]
                    + [("UPDATE", c) for c in sorted(wu - g["update"])]
                    + [("SELECT", c) for c in sorted(rd - g["select"])]
                )
                if miss:
                    fail(f"{label} {flow} {name} -> {login}: UNCOVERED {miss}")
                elif not errs:
                    out(f"{label} {flow} {name} -> {login}: covered")
            if file_pg == 0:
                fail(
                    f"{label} {flow}: this file has zero Postgres nodes (nothing in it was checked)"
                )
        out(f"{label}: {n} postgres nodes")
        if seen_files != EXPECTED_FLOWS:
            fail(f"{label}: flow files are {sorted(seen_files)}, expected {sorted(EXPECTED_FLOWS)}")
        if n != EXPECTED_PG_NODES:
            fail(
                f"{label}: {n} postgres nodes, expected {EXPECTED_PG_NODES} (wrong folder or changed flow)"
            )
        if n == 0:
            fail(f"{label}: zero Postgres nodes (nothing was checked)")
        for login, g in sorted(grants.items()):
            u = used.get(login, {k: set() for k in KINDS})
            for k in KINDS:
                extra = sorted(g[k] - u[k])
                if extra:
                    fail(
                        f"{label}: unused grant {k.upper()} {extra} for {login} (no query needs it)"
                    )
    out(f"TOTAL PROBLEMS: {bad}")
    return bad


def main(argv):
    doc, args, newc = DEFAULT_DOC, list(argv), False
    while args[:1] and args[0].startswith("--"):
        if args[0] == "--require-new-credentials":
            newc, args = True, args[1:]
        elif args[0] == "--roles-doc":
            if len(args) < 2:
                print("FAIL --roles-doc needs a path")
                return 1
            doc, args = args[1], args[2:]
        else:
            print(f"FAIL unknown option {args[0]}")
            return 1
    try:
        return 1 if run(args, doc, require_new_cred=newc) else 0
    except UNEXPECTED as e:  # last safety net: an unexpected shape must never end in a traceback
        print(f"FAIL internal error while checking ({type(e).__name__}: {e}); nothing is verified")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
