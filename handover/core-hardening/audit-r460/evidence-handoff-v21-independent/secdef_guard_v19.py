"""v19 class guard for SECURITY DEFINER and everything that can change who may run, who owns, or what a session is, in a .sql file
(security majors MA1 and MA2 of the v18 review). Reference for the DB-1 builder, not product code.
Class (v16, v17, v18 all had it): a guard that lists the bad shapes passes every shape not on the list. v18 said "deny by default"
and was not: only CREATE FUNCTION was checked for what it is, every other statement passed unless a deny branch matched its lead
word. v19 is a REAL ALLOW-LIST: every statement must match one of the shapes below, otherwise it is a problem (a new SQL
keyword is therefore refused until someone adds a shape and a mutant). One tokenizer reads comments, strings, E'..', dollar
quotes and double-quoted names, statements are split once.
Allowed statement shapes (everything else, including SELECT, DROP, LOCK, CALL, PREPARE, REASSIGN OWNED, CREATE VIEW/POLICY,
SET of anything but the two timeouts, RESET, DO, GRANT, COPY, INSERT/UPDATE/DELETE at file level, ALTER of anything but ADD on a table):
 S1 SET LOCAL lock_timeout|statement_timeout (=|TO) <string or number>        (exact shape; quoted and underscore forms of role,
    session_authorization, and search_path at file level are therefore refused)
 S2 ALTER TABLE [IF EXISTS] [ONLY] <name> ADD ... [, ADD ...]                 (every top-level action starts with ADD; DISABLE TRIGGER,
    DROP CONSTRAINT, OWNER TO, SET, ENABLE are refused)
 S3 CREATE TABLE [IF NOT EXISTS] <name> ( ... ) | CREATE [UNIQUE] INDEX ... | CREATE [OR REPLACE] TRIGGER ... EXECUTE FUNCTION f()
    where f is a function listed for THIS file | COMMENT ON ...
 S4 DROP TRIGGER IF EXISTS <name> ON <name>
 S5 REVOKE ALL|EXECUTE ON FUNCTION <sig> [, <sig>] FROM PUBLIC  with signatures listed for this file
 S6 CREATE OR REPLACE FUNCTION <unqualified name>(types) for a signature listed for this file (R1 to R6 of v18 below)
 S7 a statement whose fingerprint (first 16 hex of sha256 of its tokens joined by one space, comments removed) is pinned for THIS file
    in `extra_statements` (the one-off DELETE and INSERT of migration 0003 and the DROP CONSTRAINT of the upgrade file): a pin, not a shape.
Rules that stay from v18: R1 name AND signature on this file's list, definer or invoker as listed; no PROCEDURE, ROUTINE, AGGREGATE, DO, LANGUAGE c.
R3 every GRANT is a problem. R4 a definer function has `SET search_path = pg_catalog, pg_temp` exactly and nothing else SET.
R5 plpgsql or sql string bodies: every relation after INSERT INTO, UPDATE, DELETE FROM, ... is written `%I.` inside EXECUTE format(..) with only %I.
New in v19:
 N1 (MA2) a function name or a type with a schema in front of it is a problem (the real one is the unqualified name): `other.spend_reserve(...)`
    can never stand for the listed `spend_reserve(...)`; a quoted name or type keeps its case (`"Spend_Reserve"`, `"Date"` are not `spend_reserve`, `date`);
    the REVOKE must name the same unqualified signature.
 N2 (MA1a) the REVOKE of a signature must come AFTER the last CREATE of that signature in the file (a REVOKE then a re-create re-opens PUBLIC EXECUTE);
    DROP FUNCTION is refused outright.
 N3 (MA1d) a BEGIN ATOMIC body is scanned (v18 never scanned it): only the relations pinned for that file (`atomic_tables`), no ALTER, GRANT, CREATE, DROP, SET
    that is not part of an UPDATE, RESET, CALL, DO, EXECUTE; and in EVERY definer body (atomic, plpgsql or sql) a called function must be on a short
    list (CALLS_OK): set_config, query_to_xml and its relatives, dblink, pg_read_file and every other name are refused because they are not listed.
"""
import re, hashlib

# ---------------------------------------------------------------- one tokenizer for everything (class fix for spellings A and F)
_WORD = re.compile(r"[A-Za-z_\u0080-￿][A-Za-z0-9_$\u0080-￿]*")
_DOLLAR = re.compile(r"\$([A-Za-z_\u0080-￿][A-Za-z0-9_\u0080-￿]*)?\$")
def tokenize(t):
    """list of (kind, text): word, qid (double-quoted name, quotes kept), str, dollar, num, punct. Comments are dropped."""
    out, i, n = [], 0, len(t)
    while i < n:
        c = t[i]
        if c.isspace(): i += 1
        elif t.startswith("--", i):
            j = t.find("\n", i); i = n if j < 0 else j
        elif t.startswith("/*", i):
            depth, i = 1, i + 2
            while i < n and depth:
                if t.startswith("/*", i): depth += 1; i += 2
                elif t.startswith("*/", i): depth -= 1; i += 2
                else: i += 1
        elif c == "'":
            esc = bool(out) and out[-1][0] == "word" and out[-1][1].upper() in ("E", "U&") and t[i - 1] == out[-1][1][-1] and not t[i - 1].isspace()
            j = i + 1
            while j < n:
                if esc and t[j] == "\\": j += 2; continue
                if t[j] == "'":
                    if j + 1 < n and t[j + 1] == "'": j += 2; continue
                    break
                j += 1
            out.append(("str", t[i:j + 1])); i = j + 1
        elif c == '"':
            j = i + 1
            while j < n:
                if t[j] == '"':
                    if j + 1 < n and t[j + 1] == '"': j += 2; continue
                    break
                j += 1
            out.append(("qid", t[i:j + 1])); i = j + 1
        elif c == "$" and (m := _DOLLAR.match(t, i)):
            tag = m.group(0); j = t.find(tag, i + len(tag)); j = n if j < 0 else j + len(tag)
            out.append(("dollar", t[i:j])); i = j
        elif m := _WORD.match(t, i):
            out.append(("word", m.group(0))); i = m.end()
        elif c.isdigit():
            j = i
            while j < n and (t[j].isalnum() or t[j] == "."): j += 1
            out.append(("num", t[i:j])); i = j
        else:
            out.append(("punct", c)); i += 1
    return out

def _is(tok, *words): return tok[0] == "word" and tok[1].upper() in words

def split_statements(toks):
    """Split at top-level ';'. After BEGIN ATOMIC the body ends at the END that closes it; every CASE inside needs its own END."""
    stmts, cur, atomic, depth = [], [], False, 0
    for k, tk in enumerate(toks):
        if not atomic and _is(tk, "BEGIN") and k + 1 < len(toks) and _is(toks[k + 1], "ATOMIC"):
            atomic, depth = True, 0
        elif atomic and _is(tk, "CASE"): depth += 1
        elif atomic and _is(tk, "END"):
            if depth: depth -= 1
            else: atomic = False
        if tk == ("punct", ";") and not atomic:
            if cur: stmts.append(cur)
            cur = []
        else: cur.append(tk)
    if cur: stmts.append(cur)
    return stmts

def _lead(st, n=6):
    w = []
    for tk in st[:n]:
        if tk[0] != "word": break
        w.append(tk[1].upper())
    return w

def _flat(st): return " ".join(tk[1] for tk in st)

# ---------------------------------------------------------------- signatures (class fix for spelling C)
_MODES = {"IN", "OUT", "INOUT", "VARIADIC"}
_MULTI = {"DOUBLE", "CHARACTER", "TIMESTAMP", "TIME", "BIT", "NATIONAL", "INTERVAL", "CHAR"}
_ALIAS = {"int": "integer", "int4": "integer", "int8": "bigint", "int2": "smallint", "bool": "boolean", "float8": "double precision",
          "float4": "real", "varchar": "character varying", "timestamptz": "timestamp with time zone", "timetz": "time with time zone"}
def _split_commas(toks):
    parts, cur, d = [], [], 0
    for tk in toks:
        if tk == ("punct", "("): d += 1
        if tk == ("punct", ")"): d -= 1
        if tk == ("punct", ",") and d == 0: parts.append(cur); cur = []
        else: cur.append(tk)
    if cur or parts: parts.append(cur)
    return parts
_SAFE = re.compile(r"[a-z_][a-z0-9_$]*\Z")
def _fold(tk):
    """Postgres name folding (v19, MA2): an unquoted word is lower-cased; a double-quoted name that is already a plain lower-case name is the same name;
    any other quoted name keeps its case AND its quotes, so "Date" and "Spend_Reserve" can never equal date and spend_reserve."""
    if tk[0] == "qid":
        inner = tk[1][1:-1].replace('""', '"')
        return inner if _SAFE.match(inner) else tk[1]
    return tk[1].lower()
def _type_of(toks):
    ws, d = [], 0
    for tk in toks:
        if tk == ("punct", "("): d += 1; continue
        if tk == ("punct", ")"): d -= 1; continue
        if d: continue
        if _is(tk, "DEFAULT") or tk == ("punct", "="): break
        ws.append(_fold(tk) if tk[0] != "punct" else tk[1])
    if ws and ws[0].upper() in _MODES: ws = ws[1:]
    if len(ws) >= 2 and ws[0].upper() not in _MULTI and ws[1] not in ("[", "."): ws = ws[1:]
    s = " ".join(ws).replace(" [ ]", "[]").replace("pg_catalog . ", "")
    return _ALIAS.get(s, s)
def sigkey(name, arg_toks):
    parts = [p for p in _split_commas(arg_toks) if p]
    return f"{name}({','.join(_type_of(p) for p in parts)})"
def _name_and_args(st, i):
    """st[i] is the first token of the (possibly schema-qualified) name; returns (folded name, qualified?, arg tokens, index after ')') or None.
    v19: the schema part is no longer thrown away: `qualified` is True when any part stands before the last one."""
    j, name, parts = i, None, 0
    while j < len(st) and st[j][0] in ("word", "qid"):
        name = _fold(st[j]); parts += 1; j += 1
        if j < len(st) and st[j] == ("punct", "."): j += 1
        else: break
    if name is None or j >= len(st) or st[j] != ("punct", "("): return None
    d, k = 0, j
    while k < len(st):
        if st[k] == ("punct", "("): d += 1
        elif st[k] == ("punct", ")"):
            d -= 1
            if d == 0: break
        k += 1
    return name, parts > 1, st[j + 1:k], k + 1

# ---------------------------------------------------------------- body rules (R5)
_RELATION_INTRO = [("INSERT", "INTO"), ("DELETE", "FROM"), ("MERGE", "INTO"), ("TRUNCATE", "TABLE"), ("LOCK", "TABLE")]
_ONE = {"UPDATE", "TRUNCATE", "COPY", "LOCK", "FROM", "JOIN", "ONLY"}
_BODY_BAD = re.compile(r"\b(ALTER|GRANT|REVOKE|CREATE|DROP|SESSION\s+AUTHORIZATION|SESSION_AUTHORIZATION|SET\s+(?:LOCAL\s+|SESSION\s+)?\"?ROLE\"?|RESET|CALL|PREPARE|REASSIGN|DISCARD|LISTEN|NOTIFY|VACUUM|REINDEX|CLUSTER)\b", re.I)
def _pct_i(toks, k):  # toks[k:k+3] is % I .
    return k + 2 < len(toks) and toks[k] == ("punct", "%") and _is(toks[k + 1], "I") and toks[k + 2] == ("punct", ".")
def _intro_problems(toks):
    """relations introduced without %I. right after (words and the strings that hold the SQL of EXECUTE are both scanned)"""
    out = []
    for k, tk in enumerate(toks):
        if tk[0] != "word": continue
        w = tk[1].upper(); nxt = k + 1
        if w in ("INSERT", "DELETE", "MERGE") and k + 1 < len(toks) and _is(toks[k + 1], "INTO", "FROM"): nxt = k + 2
        elif w == "DROP": nxt = k + 2  # DROP TABLE x
        elif w in ("TRUNCATE", "LOCK") and k + 1 < len(toks) and _is(toks[k + 1], "TABLE"): nxt = k + 2
        elif w == "ONLY" and k and _is(toks[k - 1], "UPDATE", "FROM", "INTO"): continue
        elif w in ("UPDATE", "COPY", "TRUNCATE", "LOCK", "JOIN"): nxt = k + 1
        elif w == "FROM":
            if k and _is(toks[k - 1], "DISTINCT", "INTO"): continue
            nxt = k + 1
        else: continue
        if nxt < len(toks) and _is(toks[nxt], "ONLY"): nxt += 1
        if w == "UPDATE" and k and _is(toks[k - 1], "FOR", "KEY", "NO"): continue  # FOR UPDATE row lock
        if not _pct_i(toks, nxt): out.append(f"{w} without %I. right after it")
    return out
def _sql_of(strtok): return strtok[1][1:-1].replace("''", "'")
def _body_source(tk):
    if tk[0] == "str": return _sql_of(tk)
    tag = _DOLLAR.match(tk[1]).group(0)
    return tk[1][len(tag):len(tk[1]) - len(tag)] if tk[1].endswith(tag) and len(tk[1]) >= 2 * len(tag) else tk[1][len(tag):]
def _body_problems(source, fn, strict=True):
    p = []
    toks = tokenize(source)
    for k, tk in enumerate(toks):
        if strict and _is(tk, "EXECUTE"):
            ok = k + 3 < len(toks) and _is(toks[k + 1], "FORMAT") and toks[k + 2] == ("punct", "(") and toks[k + 3][0] == "str"
            if not ok: p.append(f"{fn} has an EXECUTE that is not EXECUTE format('literal', TG_TABLE_SCHEMA ...)"); continue
            lit = _sql_of(toks[k + 3])
            if re.search(r"%(?!I|%)", lit.replace("%%", "")): p.append(f"{fn} format string uses a substitution other than %I")
            d, m, args, cur = 1, k + 4, [], []
            while m < len(toks) and d:
                if toks[m] == ("punct", "("): d += 1
                if toks[m] == ("punct", ")"):
                    d -= 1
                    if d == 0: break
                if toks[m] == ("punct", ",") and d == 1: args.append(cur); cur = []
                else: cur.append(toks[m])
                m += 1
            if cur: args.append(cur)
            if any(not (len(a) == 1 and _is(a[0], "TG_TABLE_SCHEMA")) for a in args if a): p.append(f"{fn} format argument is not TG_TABLE_SCHEMA")
            if m + 1 < len(toks) and not (_is(toks[m + 1], "USING", "INTO") or toks[m + 1] == ("punct", ";")): p.append(f"{fn} EXECUTE format(...) is followed by something other than USING, INTO or ;")
            p += [f"{fn} EXECUTE string: {x}" for x in _intro_problems(tokenize(lit))]
    words = [tk for tk in toks if tk[0] == "word"]
    if _BODY_BAD.search(" ".join(w[1] for w in words)): p.append(f"{fn} body contains ALTER, GRANT, REVOKE, CREATE, DROP, SET ROLE or SESSION AUTHORIZATION")
    for tk in toks:
        if tk[0] == "str" and _BODY_BAD.search(_sql_of(tk)) and re.match(r"\s*(ALTER|GRANT|REVOKE|CREATE|DROP|SET)\b", _sql_of(tk), re.I):
            p.append(f"{fn} string starts a forbidden statement")
    if strict: p += [f"{fn} {x}" for x in _intro_problems(toks)]
    return p

_DENY_NOTE = {"ALTER": "ALTER of anything but ADD on a table", "GRANT": "GRANT (grants come from configuration)", "DO": "DO block", "SET": "SET other than SET LOCAL lock_timeout|statement_timeout",
              "RESET": "RESET", "SELECT": "bare SELECT", "DROP": "DROP other than DROP TRIGGER IF EXISTS", "LOCK": "LOCK", "CALL": "CALL", "PREPARE": "PREPARE", "REASSIGN": "REASSIGN OWNED",
              "INSERT": "INSERT at file level", "UPDATE": "UPDATE at file level", "DELETE": "DELETE at file level", "COPY": "COPY", "TRUNCATE": "TRUNCATE", "BEGIN": "BEGIN", "COMMIT": "COMMIT"}

# ---------------------------------------------------------------- body scans new in v19 (N3)
CALLS_OK = {"date_trunc", "clock_timestamp", "now", "format", "coalesce", "least", "greatest", "length"}
_SYNTAX_BEFORE_PAREN = {"IN", "VALUES", "AS", "AND", "OR", "NOT", "EXISTS", "ANY", "ALL", "SOME", "WHEN", "THEN", "ELSE", "CASE", "ON", "USING", "SELECT", "WHERE", "FROM", "JOIN", "SET", "INTO",
    "UPDATE", "DELETE", "INSERT", "RETURNING", "BETWEEN", "LIKE", "IS", "DISTINCT", "ONLY", "TABLE", "WITH", "IF", "ELSIF", "LOOP", "WHILE", "RETURN", "CONFLICT", "DO", "BY", "HAVING", "LIMIT",
    "UNION", "EXCEPT", "INTERSECT", "OVER", "FILTER", "TO", "END", "BEGIN", "DEFAULT", "CHECK", "UNIQUE", "KEY", "NULL", "TRUE", "FALSE", "EXECUTE", "RETURNS", "NUMERIC", "VARCHAR", "CHAR",
    "CHARACTER", "TIMESTAMP", "TIME", "INTERVAL", "DECIMAL", "BIT", "VARYING", "PRECISION", "NOTHING", "SESSION_USER", "CURRENT_USER"}
def _call_problems(toks, fn):
    out = []
    for k in range(len(toks) - 1):
        tk = toks[k]
        if toks[k + 1] != ("punct", "(") or tk[0] not in ("word", "qid"): continue
        if tk[0] == "qid": out.append(f"{fn} body calls a quoted name {tk[1]}"); continue
        if tk[1].upper() in _SYNTAX_BEFORE_PAREN: continue
        if k >= 3 and toks[k - 1] == ("punct", ".") and toks[k - 2] == ("word", "I") and toks[k - 3] == ("punct", "%"): continue  # %I.name ( : a relation in an EXECUTE string
        if k and _is(toks[k - 1], "INTO", "UPDATE", "FROM", "JOIN", "ONLY", "TABLE"): continue  # a relation name followed by a column list
        if k and toks[k - 1] == ("punct", "."): out.append(f"{fn} body calls a schema-qualified function ...{tk[1]}"); continue
        if tk[1].lower() not in CALLS_OK: out.append(f"{fn} body calls {tk[1]}(), which is not on the short list of calls a definer body may use ({sorted(CALLS_OK)})")
    return out
def _extra_body_problems(toks, fn, definer):
    out = []
    for k, tk in enumerate(toks):
        if _is(tk, "SET") and not any(_is(x, "UPDATE") for x in toks[max(0, k - 4):k]):
            out.append(f"{fn} body has a SET that is not part of an UPDATE (SET ROLE, SET \"role\", SET session_authorization or SET search_path)")
        if _is(tk, "DO") and not (k + 1 < len(toks) and _is(toks[k + 1], "UPDATE", "NOTHING")): out.append(f"{fn} body has a DO block")
        if _is(tk, "RESET"): out.append(f"{fn} body has RESET")
    if definer: out += _call_problems(toks, fn)
    return out
_STOP = {"WHERE", "JOIN", "INNER", "LEFT", "RIGHT", "FULL", "CROSS", "ON", "GROUP", "ORDER", "LIMIT", "HAVING", "RETURNING", "SET", "VALUES", "USING", "UNION", "FOR", "WINDOW", "DO", "SELECT", "LATERAL", "NATURAL"}
def _atomic_problems(toks, fn, tables):
    """toks = tokens of BEGIN ATOMIC ... END. Relations must be unqualified and pinned for the file; no EXECUTE; the extra rules of every body."""
    out, n = [], len(toks)
    if tables is None: return [f"{fn} has a BEGIN ATOMIC body but no `atomic_tables` are pinned for this file (a body that is not scanned is refused)"]
    def take(i):
        if i < n and _is(toks[i], "ONLY"): i += 1
        if i >= n or toks[i][0] not in ("word", "qid"): return i
        if i + 1 < n and toks[i + 1] == ("punct", "."):
            out.append(f"{fn} body names a schema-qualified relation"); return i + 3
        nm = _fold(toks[i])
        if nm not in tables: out.append(f"{fn} body uses the relation {toks[i][1]}, which is not pinned for this file ({sorted(tables)})")
        i += 1
        if i < n and _is(toks[i], "AS"): i += 1
        if i < n and toks[i][0] in ("word", "qid") and not (toks[i][0] == "word" and toks[i][1].upper() in _STOP): i += 1
        return i
    i = 0
    while i < n:
        tk = toks[i]
        if tk[0] == "word":
            w, prev = tk[1].upper(), (toks[i - 1] if i else None)
            if w == "INTO" and prev and _is(prev, "INSERT"): i = take(i + 1); continue
            if w == "UPDATE" and not (prev and _is(prev, "DO", "FOR", "KEY", "NO")): i = take(i + 1); continue
            if w == "FROM" and not (prev and _is(prev, "DISTINCT")):
                i = take(i + 1)
                while i < n and toks[i] == ("punct", ",") and not _is(toks[i - 1], "VALUES"): i = take(i + 1)
                continue
            if w == "JOIN": i = take(i + 1); continue
            if w == "EXECUTE": out.append(f"{fn} body has EXECUTE")
        i += 1
    if _BODY_BAD.search(" ".join(tk[1] for tk in toks if tk[0] == "word")): out.append(f"{fn} body contains ALTER, GRANT, REVOKE, CREATE, DROP, SET ROLE, RESET, CALL or SESSION AUTHORIZATION")
    return out + _extra_body_problems(toks, fn, True)
def _body_problems_v19(source, fn, strict):
    p = _body_problems(source, fn, strict)
    toks = tokenize(source)
    p += _extra_body_problems(toks, fn, strict)
    if strict:  # the SQL held in EXECUTE format('...') strings is scanned for calls too
        for k, tk in enumerate(toks):
            if _is(tk, "EXECUTE") and k + 3 < len(toks) and toks[k + 3][0] == "str": p += _call_problems(tokenize(_sql_of(toks[k + 3])), fn + " EXECUTE string")
    return p

def fingerprint(st): return hashlib.sha256(" ".join(tk[1] for tk in st).encode()).hexdigest()[:16]
def _sigs(part_toks, name, problems, pre, kind):
    """REVOKE signature list -> keys (unqualified only)"""
    keys = []
    for part in _split_commas_top(part_toks):
        na = _name_and_args(part, 0)
        if na is None or na[3] != len(part): problems.append(pre + f"{kind}: a signature the guard cannot read: {_flat(part)[:60]!r}"); continue
        if na[1]: problems.append(pre + f"{kind}: a schema-qualified function name is not allowed (write the unqualified name): {_flat(part)[:60]!r}"); continue
        keys.append(sigkey(na[0], na[2]))
    return keys

def check_sql_text(name, text, allowed, grants_allowed=(), extra_statements=(), atomic_tables=None):
    """allowed: {"fname(type,type)": "definer" | "invoker"} for THIS file only; extra_statements: fingerprints pinned for this file; atomic_tables: the relations a
    BEGIN ATOMIC body of this file may use. Returns a list of problems (empty = clean). Anything that matches no shape (module docstring) is a problem."""
    problems, created_at, revoked_at, definer_keys = [], {}, {}, set()
    fn_names = {k.split("(")[0] for k in allowed}
    pre = f"{name}: "
    for idx, st in enumerate(split_statements(tokenize(text))):
        lead, flat = _lead(st), _flat(st)
        short = flat[:70]
        if fingerprint(st) in extra_statements: continue
        if any(_is(a, "OWNER") and _is(b, "TO") for a, b in zip(st, st[1:])):
            problems.append(pre + f"OWNER TO is not allowed: {short!r}"); continue
        first = lead[:1]
        if first == ["SET"]:
            if len(st) == 5 and _is(st[1], "LOCAL") and st[2][0] == "word" and st[2][1].lower() in ("lock_timeout", "statement_timeout") and (st[3] == ("punct", "=") or _is(st[3], "TO")) and st[4][0] in ("str", "num"): continue
            problems.append(pre + f"SET is allowed only as `SET LOCAL lock_timeout|statement_timeout = <value>` (not SET ROLE, SET \"role\", SET session_authorization, SET search_path): {short!r}"); continue
        if first == ["ALTER"] and lead[1:2] == ["TABLE"]:
            i = 2
            if i + 1 < len(st) and _is(st[i], "IF") and _is(st[i + 1], "EXISTS"): i += 2
            if i < len(st) and _is(st[i], "ONLY"): i += 1
            if i >= len(st) or st[i][0] not in ("word", "qid"): problems.append(pre + f"ALTER TABLE the guard cannot read: {short!r}")
            elif i + 1 < len(st) and st[i + 1] == ("punct", "."): problems.append(pre + f"ALTER TABLE with a schema-qualified name: {short!r}")
            else:
                acts = _split_commas_top(st[i + 1:])
                if not acts or not all(_is(a[0], "ADD") for a in acts): problems.append(pre + f"ALTER TABLE: every action must start with ADD (DISABLE TRIGGER, DROP CONSTRAINT, SET, OWNER, ENABLE are refused): {short!r}")
            continue
        if first == ["COMMENT"] and lead[1:2] == ["ON"]: continue
        if first == ["DROP"] and len(st) == 7 and _is(st[1], "TRIGGER") and _is(st[2], "IF") and _is(st[3], "EXISTS") and st[4][0] in ("word", "qid") and _is(st[5], "ON") and st[6][0] in ("word", "qid"): continue
        if first == ["REVOKE"]:
            fi = [k for k, tk in enumerate(st) if _is(tk, "FROM")]
            fk = [k for k, tk in enumerate(st) if _is(tk, "FUNCTION")]
            ok = bool(fi and fk) and _is(st[1], "ALL", "EXECUTE") and fk[0] < fi[0] and len(st) == fi[0] + 2 and _is(st[fi[0] + 1], "PUBLIC") and any(_is(st[k], "ON") and k + 1 == fk[0] for k in range(len(st)))
            if not ok: problems.append(pre + f"REVOKE is allowed only as REVOKE ALL|EXECUTE ON FUNCTION <signatures> FROM PUBLIC: {short!r}"); continue
            for key in _sigs(st[fk[0] + 1:fi[0]], name, problems, pre, "REVOKE"):
                if key not in allowed: problems.append(pre + f"REVOKE names {key}, which is not on the list of this file")
                revoked_at[key] = idx
            continue
        if first == ["GRANT"]:
            if re.sub(r"\s+", " ", flat).upper() not in {g.upper() for g in grants_allowed}: problems.append(pre + f"GRANT is not allowed in a .sql file (grants come from configuration): {flat[:70]!r}")
            continue
        if first == ["CREATE"]:
            orr = lead[1:3] == ["OR", "REPLACE"]
            rest = lead[3:] if orr else lead[1:]
            kind = (rest or [""])[0]
            if kind == "TABLE" and not orr:
                i = 2 if lead[1:2] == ["TABLE"] else None
                if i is not None:
                    if lead[2:5] == ["IF", "NOT", "EXISTS"]: i = 5
                    if i < len(st) and st[i][0] in ("word", "qid") and i + 1 < len(st) and st[i + 1] == ("punct", "("): continue
                problems.append(pre + f"CREATE TABLE must be `CREATE TABLE [IF NOT EXISTS] <unqualified name> ( ... )` (no AS, TEMP, PARTITION OF, schema): {short!r}"); continue
            if (rest[:1] == ["INDEX"] or rest[:2] == ["UNIQUE", "INDEX"]) and not orr: continue
            if kind == "TRIGGER":
                ex = [k for k, tk in enumerate(st) if _is(tk, "EXECUTE")]
                ok = False
                if ex and ex[-1] + 4 < len(st) and _is(st[ex[-1] + 1], "FUNCTION", "PROCEDURE") and st[ex[-1] + 2][0] in ("word", "qid") and st[ex[-1] + 3] == ("punct", "(") and ex[-1] + 4 <= len(st):
                    ok = _fold(st[ex[-1] + 2]) in fn_names and st[ex[-1] + 3 - 0] == ("punct", "(") and not (ex[-1] + 3 < len(st) and st[ex[-1] + 2 + 1] == ("punct", "."))
                if not ok: problems.append(pre + f"CREATE TRIGGER must end with EXECUTE FUNCTION <a function listed for this file>(): {short!r}")
                continue
            if kind == "FUNCTION":
                i0 = next(i for i, tk in enumerate(st) if _is(tk, "FUNCTION")) + 1
                na = _name_and_args(st, i0)
                if na is None:
                    problems.append(pre + f"CREATE FUNCTION with a head the guard cannot read: {short!r}"); continue
                fname, qual, args, after = na; key = sigkey(fname, args)
                if qual: problems.append(pre + f"{key}: a schema-qualified function name is not allowed (it could be another function than the listed one)")
                if not orr: problems.append(pre + f"{key} is a plain CREATE FUNCTION (use CREATE OR REPLACE)")
                want = None if qual else allowed.get(key)
                if want is None: problems.append(pre + f"function {key} is not on the list of this file")
                if key in created_at: problems.append(pre + f"{key} is created twice in this file")
                created_at[key] = idx
                head = st[after:]
                cut = next((k for k, tk in enumerate(head) if _is(tk, "BEGIN") and k + 1 < len(head) and _is(head[k + 1], "ATOMIC")), None)
                attrs, atomic = (head if cut is None else head[:cut]), cut is not None
                a2 = [("str", "<body>") if tk[0] in ("str", "dollar") else tk for tk in attrs]
                definer_here = [k for k in range(len(st) - 1) if _is(st[k], "SECURITY") and _is(st[k + 1], "DEFINER")]
                has_def = any(_is(a2[k], "SECURITY") and k + 1 < len(a2) and _is(a2[k + 1], "DEFINER") for k in range(len(a2) - 1))
                if len(definer_here) != (1 if has_def else 0): problems.append(pre + f"{key}: SECURITY DEFINER is written inside a body or twice")
                if want == "definer" and not has_def: problems.append(pre + f"{key} is listed as definer but has no SECURITY DEFINER")
                if want == "invoker" and has_def: problems.append(pre + f"{key} is listed as invoker but is SECURITY DEFINER")
                if has_def or want == "definer": definer_keys.add(key)
                lang = [a2[k + 1][1].lower() for k in range(len(a2) - 1) if _is(a2[k], "LANGUAGE")]
                if any(l not in ("sql", "plpgsql") for l in lang): problems.append(pre + f"{key}: LANGUAGE {lang} is not allowed")
                bodies = [tk for tk in attrs if tk[0] in ("str", "dollar")]
                definer = has_def or want == "definer"
                if definer:
                    sets = [k for k in range(len(a2)) if _is(a2[k], "SET")]
                    paths = []
                    for k in sets:
                        if k + 1 < len(a2) and _is(a2[k + 1], "SEARCH_PATH"):
                            items, m = [], k + 3 if k + 2 < len(a2) and (a2[k + 2] == ("punct", "=") or _is(a2[k + 2], "TO")) else None
                            while m is not None and m < len(a2):
                                items.append(a2[m][1].strip('"').strip("'").lower()); m += 1
                                if m < len(a2) and a2[m] == ("punct", ","): m += 1
                                else: break
                            paths.append(items)
                        else: problems.append(pre + f"{key}: a SET attribute other than search_path")
                    if paths != [["pg_catalog", "pg_temp"]]: problems.append(pre + f"{key}: search_path must be exactly pg_catalog, pg_temp (found {paths})")
                if atomic: problems += [pre + x for x in _atomic_problems(head[cut:], key, atomic_tables)]
                else:
                    for b in bodies: problems += [pre + x for x in _body_problems_v19(_body_source(b), key, definer)]
                continue
        problems.append(pre + f"statement is not on the allow-list of shapes ({_DENY_NOTE.get(first[0], ' '.join(lead[:2])) if first else 'unreadable'}): {short!r}")
    for key in sorted(definer_keys):
        if key not in revoked_at: problems.append(f"{name}: {key} has no REVOKE ALL ON FUNCTION {key} FROM PUBLIC for this signature")
        elif revoked_at[key] < created_at[key]: problems.append(f"{name}: the REVOKE of {key} comes BEFORE its last CREATE (a re-created function would get PUBLIC execute back): put the REVOKE after the CREATE")
    return problems

def _split_commas_top(toks): return [p for p in _split_commas(toks) if p]
