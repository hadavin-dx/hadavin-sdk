"""v17 class guard for SECURITY DEFINER (security major M2 of the v16 review). Reference for the DB-1 builder, not product code.
v16 looked for the token only in `CREATE [OR REPLACE] FUNCTION name(args) <header> AS $tag$ body $tag$` and was bypassed
by: attributes AFTER the body, a single-quoted body, a BEGIN ATOMIC body, a schema-qualified name, ALTER FUNCTION,
CREATE PROCEDURE, DO blocks, a comment or newline inside `SECURITY DEFINER`, and one `%I.` hiding a bare table.
v17 rule: split the text into statements (respecting comments, quotes, dollar quotes and BEGIN ATOMIC ... END); the token
SECURITY DEFINER may appear ONLY in a statement that is `CREATE OR REPLACE FUNCTION <declared name>(...)`; anywhere else
(ALTER, PROCEDURE, DO, a second spelling) it is a problem. Declared functions must: end search_path with pg_temp and not
name public; have every DML in a string or dollar body written `<DML> %I.` (a schema taken from the trigger), or use a
BEGIN ATOMIC body (bound at creation); have no EXECUTE that is not format(); be revoked from PUBLIC and never granted to
PUBLIC."""
import re

def strip_comments(t):
    out, i, n = [], 0, len(t)
    while i < n:
        if t.startswith("--", i):
            j = t.find("\n", i); i = n if j < 0 else j
        elif t.startswith("/*", i):
            depth, i = 1, i + 2
            while i < n and depth:
                if t.startswith("/*", i): depth += 1; i += 2
                elif t.startswith("*/", i): depth -= 1; i += 2
                else: i += 1
            out.append(" ")
        elif t[i] == "'":
            j = i + 1
            while j < n:
                if t[j] == "'":
                    if j + 1 < n and t[j + 1] == "'": j += 2; continue
                    break
                j += 1
            out.append(t[i:j + 1]); i = j + 1
        elif t[i] == "$":
            m = re.match(r"\$(\w*)\$", t[i:])
            if m:
                tag = m.group(0); j = t.find(tag, i + len(tag)); j = n if j < 0 else j + len(tag)
                out.append(t[i:j]); i = j
            else: out.append(t[i]); i += 1
        else:
            out.append(t[i]); i += 1
    return "".join(out)

def statements(t):
    """Split on top-level semicolons; BEGIN ATOMIC ... END is one statement part."""
    stmts, buf, i, n, atomic = [], [], 0, len(t), False
    while i < n:
        c = t[i]
        if c == "'":
            j = i + 1
            while j < n:
                if t[j] == "'":
                    if j + 1 < n and t[j + 1] == "'": j += 2; continue
                    break
                j += 1
            buf.append(t[i:j + 1]); i = j + 1; continue
        if c == "$":
            m = re.match(r"\$(\w*)\$", t[i:])
            if m:
                tag = m.group(0); j = t.find(tag, i + len(tag)); j = n if j < 0 else j + len(tag)
                buf.append(t[i:j]); i = j; continue
        if c == '"':
            j = t.find('"', i + 1); j = n if j < 0 else j + 1
            buf.append(t[i:j]); i = j; continue
        if not atomic and re.match(r"BEGIN\s+ATOMIC\b", t[i:], re.I) and (i == 0 or not t[i - 1].isalnum()):
            atomic = True
        if atomic and re.match(r"END\b", t[i:], re.I) and (i == 0 or not (t[i - 1].isalnum() or t[i - 1] == "_")):
            atomic = False
        if c == ";" and not atomic:
            stmts.append("".join(buf).strip()); buf = []; i += 1; continue
        buf.append(c); i += 1
    if "".join(buf).strip(): stmts.append("".join(buf).strip())
    return [s for s in stmts if s]

TOKEN = re.compile(r"SECURITY\s+DEFINER", re.I)
HEAD = re.compile(r"CREATE\s+OR\s+REPLACE\s+FUNCTION\s+(?:(?:\"?\w+\"?)\s*\.\s*)?\"?(\w+)\"?\s*\(", re.I)
BODY = re.compile(r"\$(\w*)\$.*?\$\1\$|'(?:[^']|'')*'|BEGIN\s+ATOMIC\b.*\bEND\b", re.I | re.S)
DML = re.compile(r"\b(INSERT\s+INTO|UPDATE|DELETE\s+FROM|TRUNCATE(?:\s+TABLE)?|MERGE\s+INTO|COPY)\s+(?:ONLY\s+)?(?!%I\.)", re.I)

def check_sql_text(name, text, allowed):
    problems = []
    text = strip_comments(text)
    for st in statements(text):
        flat = re.sub(r"\s+", " ", st)
        if not TOKEN.search(flat):
            continue
        m = HEAD.match(flat)
        if not m:
            problems.append(f"{name}: SECURITY DEFINER outside a declared CREATE OR REPLACE FUNCTION: {flat[:50]!r}")
            continue
        fn = m.group(1)
        if fn not in allowed:
            problems.append(f"{name}: SECURITY DEFINER function {fn} is not on the declared list")
        attrs = BODY.sub(" <body> ", st)
        if len(TOKEN.findall(attrs)) != 1:
            problems.append(f"{name}: {fn} has the token inside a body or twice")
        sp = re.search(r"SET\s+search_path\s*(?:=|TO)\s*([\w\s,\"]+?)(?=\s+(?:AS|BEGIN|RETURN|LANGUAGE|SECURITY|SET|COST|STABLE|VOLATILE|IMMUTABLE|STRICT)\b|\s+<body>|\s*$)", attrs, re.I)
        if not sp: problems.append(f"{name}: {fn} has no SET search_path"); items = []
        else:
            items = [i.strip().strip('"').lower() for i in sp.group(1).split(",") if i.strip()]
            if not items or items[-1] != "pg_temp": problems.append(f"{name}: {fn} search_path does not end with pg_temp")
            if "public" in items: problems.append(f"{name}: {fn} search_path names public")
        atomic = re.search(r"BEGIN\s+ATOMIC\b", st, re.I) is not None
        if not atomic:
            for b in BODY.finditer(st):
                body = b.group(0)
                if DML.search(body): problems.append(f"{name}: {fn} has a DML statement without %I. right after it")
                if re.search(r"\bEXECUTE\b(?!\s+format\s*\()", body, re.I) and "EXECUTE" in body.upper() and not re.search(r"EXECUTE\s+format\s*\(", body, re.I):
                    problems.append(f"{name}: {fn} has an EXECUTE that is not format()")
        pat = r"\s*\(\s*(?:[^)]*)\)"
        if not re.search(r"REVOKE\s+ALL\s+ON\s+FUNCTION\s+(?:\w+\s*\.\s*)?" + re.escape(fn) + pat + r"\s+FROM\s+PUBLIC", text, re.I):
            problems.append(f"{name}: {fn} has no REVOKE ALL ON FUNCTION ... FROM PUBLIC")
        if re.search(r"GRANT\s+(?:ALL|EXECUTE)[^;]*FUNCTION\s+(?:\w+\s*\.\s*)?" + re.escape(fn) + r"[^;]*\sTO\s+PUBLIC", text, re.I):
            problems.append(f"{name}: {fn} is granted to PUBLIC")
    return problems
