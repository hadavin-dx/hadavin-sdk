"""Prototype of the DB-1 class-level guard test (security major 6): a text check over every SQL file in migrations/
and migrations_held/. Reference for the builder of DB-1, not product code. Rules for every SECURITY DEFINER function:
(1) it must be on the declared list ALLOWED_SECDEF; (2) its header has SET search_path = <list> whose LAST item is pg_temp
and which names no schema called public; (3) a body that changes a table must name the schema with %I (taken from
TG_TABLE_SCHEMA), never a bare table name; (4) the same file revokes EXECUTE on it from PUBLIC."""
import re
FUNC = re.compile(r"CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+(\w+)\s*\(([^)]*)\)(.*?)\bAS\s+(\$\w*\$)(.*?)\4", re.I | re.S)
def check_sql_text(name, text, allowed):
    text = re.sub(r"--[^\n]*", "", text)
    problems = []
    for m in FUNC.finditer(text):
        fn, args, header, _tag, body = m.groups()
        if not re.search(r"SECURITY\s+DEFINER", header, re.I):
            continue
        if fn not in allowed:
            problems.append(f"{name}: SECURITY DEFINER function {fn} is not on the declared list")
        sp = re.search(r"SET\s+search_path\s*(?:=|TO)\s*([^\n]*?)\s*$", header.strip(), re.I | re.M)
        if not sp:
            problems.append(f"{name}: {fn} has no SET search_path"); items = []
        else:
            items = [i.strip().lower() for i in sp.group(1).split(",") if i.strip()]
            if not items or items[-1] != "pg_temp": problems.append(f"{name}: {fn} search_path does not end with pg_temp")
            if "public" in items: problems.append(f"{name}: {fn} search_path names public")
        if re.search(r"\b(INSERT\s+INTO|UPDATE|DELETE\s+FROM)\b", body, re.I) and "%I." not in body:
            problems.append(f"{name}: {fn} changes a table without a %I schema")
        if not re.search(r"REVOKE\s+ALL\s+ON\s+FUNCTION\s+" + re.escape(fn) + r"\s*\([^)]*\)\s+FROM\s+PUBLIC", text, re.I):
            problems.append(f"{name}: {fn} has no REVOKE ALL ON FUNCTION ... FROM PUBLIC")
    return problems
