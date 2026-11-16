"""v22 class guard = v21 plus (security MJ2) `add_pins=None` means every ALTER TABLE ... ADD is a problem (v21 skipped the pin check for a file that is not a key of the pin table, so a renamed
or new held file could carry `ADD CONSTRAINT ... CHECK (true)`); (security m6) the pin table also pins CREATE TABLE, CREATE INDEX and COMMENT ON statements; (security m2) a SET LOCAL timeout must be a canonical
positive integer with unit ms, s, min or h and at most MAX_TIMEOUT_MS (one hour; my number): `0x0`, `0_0`, `0e0`, `0.0`, `'0'` and `999999h` are refused; (m6) `require_lock_timeout` and `require_stmt_timeout`:
the file must set the timeout BEFORE its first ALTER TABLE, CREATE TABLE, CREATE INDEX or CREATE TRIGGER. PIN_ANY switches the DDL pin off for a unit mutant; None means nothing is allowed. The v21 text follows unchanged.

v21 class guard = v20 plus the round-7 findings of the security review (m4 alias column list and TABLESAMPLE in the relation scan, m5 ASCII-only case folding
(AStr; regex flags re.ASCII), m6 search_path items folded like names, m7 a -- comment ends at \\n or \\r, m9 fingerprint = sha256 of the exact token texts plus token kind and a
gap flag (so `@-` and `@ -`, `E'x'` and `E 'x'` differ; comments and the amount of white space do not count), m11 contextual syntax words, zero timeouts, INHERITS, DROP TRIGGER table).
The v20 text follows unchanged.

v20 class guard (v19 plus the round-6 findings, see the N-rules at the end of this docstring; the v19 text follows unchanged)

v19 class guard for SECURITY DEFINER and everything that can change who may run, who owns, or what a session is, in a .sql file
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

New in v20 (security review of v19, round 6, and the independent runner of v19, F1 and F2):
 B1 a definer is scannable or it is a problem: the head after the attributes must be BEGIN ATOMIC, RETURN <expr> (the expression is scanned like an atomic body) or EXACTLY one
    string/dollar body; a head with none of these, or with a body string next to ATOMIC/RETURN, is refused. LEAKPROOF, SUPPORT, TRANSFORM, WINDOW are refused in the head.
 M1 `%I.name(` hides nothing any more: it is skipped only right after INTO (the column list of an INSERT); everywhere else it is a schema-qualified call. A function in FROM/JOIN is a call.
 M2 triggers are pinned per file (`trigger_pins`: name -> fingerprint of the whole CREATE TRIGGER statement: timing, events, table, WHEN, function). A trigger that is not pinned, or whose
    statement differs from the pin, is a problem; a pinned trigger that the file does not create is a problem; DROP TRIGGER IF EXISTS is allowed only for a pinned name AND only if the
    same file creates it again later (a drop that leaves the table without its trigger is a problem).
 M3 in atomic and RETURN bodies a relation after MERGE INTO, USING, TABLE, TRUNCATE, LOCK, COPY and SELECT ... INTO is checked against the pinned relations like FROM; in EXECUTE strings
    USING <relation>, TABLE x and SELECT INTO need %I. like the others.
 M4 every listed function has a pinned fingerprint (`fn_pins`: signature -> fingerprint of the whole CREATE FUNCTION statement, head and body). The pin is TEXT level (the guard reads .sql files);
    the catalog level is the start-up query (names from pg_proc). A hash of pg_proc.prosrc is NOT used: for BEGIN ATOMIC the stored text is a parse tree and its stability across 14, 16 and 17 is untested.
 F1 (runner) statement kinds are pinned per definer (`kinds`: signature -> set of INSERT, UPDATE, SELECT ...): DELETE, TRUNCATE, MERGE, COPY and WITH (a CTE can hide a DELETE) are problems
    unless the function lists them; this is checked in atomic bodies, RETURN expressions, plpgsql/sql bodies and inside EXECUTE strings.
 m1/F2 expressions inside allowed shapes are read: every call in ALTER TABLE, CREATE TABLE, CREATE INDEX and CREATE TRIGGER (WHEN) must be on EXPR_CALLS_OK; OPERATOR(...) is refused.
 m2 the SET that is exempt from the "SET ROLE" rule is the one that follows `UPDATE [ONLY] name [AS alias]` or `DO UPDATE` directly (structural, not "an UPDATE within 4 tokens").
 m3 one tokenizer that follows the server: only space, tab, newline, CR, FF and VT separate words (NBSP and other Unicode spaces do not), identifier characters are A-Z a-z _ and any non-ASCII
    character including characters above U+FFFF; digits are ASCII only. Checked against a real server in `tok_vs_server_v20.py`.
 PIN_ANY (for unit mutants only): a value that switches one pin check off. A real caller passes dicts; None means "nothing is pinned" and every listed function or trigger is a problem.
"""
import re, hashlib, json
_UPMAP = {c: c - 32 for c in range(ord("a"), ord("z") + 1)}; _LOMAP = {c: c + 32 for c in range(ord("A"), ord("Z") + 1)}
class AStr(str):
    """v21 m5: Postgres folds ONLY ASCII letters in an unquoted name or keyword (multibyte characters are left alone); Python's str.upper() also maps U+212A (Kelvin) to K, U+017F (long s) to S and so on."""
    def upper(self): return AStr(str.translate(self, _UPMAP))
    def lower(self): return AStr(str.translate(self, _LOMAP))
class Tok(tuple):
    """(kind, text) with a `gap` flag: True when white space or a comment came right before it (v21 m9)."""
    def __new__(cls, kind, text, gap=True):
        o = super().__new__(cls, (kind, AStr(text))); o.gap = gap; return o

class _Any:
    def __repr__(self): return "PIN_ANY"
PIN_ANY = _Any()

# ---------------------------------------------------------------- one tokenizer for everything (class fix for spellings A and F)
_WORD = re.compile(r"[A-Za-z_\u0080-\U0010FFFF][A-Za-z0-9_$\u0080-\U0010FFFF]*")
_DOLLAR = re.compile(r"\$([A-Za-z_\u0080-\U0010FFFF][A-Za-z0-9_\u0080-\U0010FFFF]*)?\$")
def tokenize(t):
    """list of (kind, text): word, qid (double-quoted name, quotes kept), str, dollar, num, punct. Comments are dropped."""
    out, i, n, last_end = [], 0, len(t), 0
    while i < n:
        c = t[i]; i0, nb = i, len(out)
        if c in " \t\n\r\f\v": i += 1
        elif t.startswith("--", i):
            m = re.compile(r"[\n\r]").search(t, i); i = n if m is None else m.start()   # v21 m7: Postgres scan.l: non_newline is [^\n\r]
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
        elif c in "0123456789":
            j = i
            while j < n and (t[j] in "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_." ): j += 1
            out.append(("num", t[i:j])); i = j
        else:
            out.append(("punct", c)); i += 1
        if len(out) > nb: out[-1] = Tok(out[-1][0], out[-1][1], i0 > last_end); last_end = i
    return out

def _is(tok, *words): return tok[0] == "word" and tok[1].upper() in words

def split_statements(toks):
    """Split at top-level ';'. After BEGIN ATOMIC the body ends at the END that closes it; every CASE inside needs its own END."""
    stmts, cur, atomic, depth = [], [], False, 0
    for k, tk in enumerate(toks):
        if not atomic and _is(tk, "BEGIN") and k + 1 < len(toks) and _is(toks[k + 1], "ATOMIC"):
            atomic, depth = True, 0
        elif atomic and _is(tk, "CASE") and not (k and _is(toks[k - 1], "AS")): depth += 1
        elif atomic and _is(tk, "END") and not (k and _is(toks[k - 1], "AS")):
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
def _sp_item(tk):
    """v21 m6: one search_path item as the SERVER reads it: a word is folded to ASCII lower case, a double-quoted name by _fold (so "PG_CATALOG" stays a different schema), a string
    by the server's list rule (no double quote or comma inside is accepted, then folded); anything else keeps a marker that never equals pg_catalog or pg_temp."""
    if tk[0] == "word": return str(tk[1].lower())
    if tk[0] == "qid": return str(_fold(tk))
    if tk[0] == "str":
        inner = tk[1][1:-1].replace("''", "'")
        return "?" + inner if ('"' in inner or "," in inner or "\\" in tk[1]) else str(AStr(inner).lower())
    return "?" + str(tk[1])
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
_BODY_BAD = re.compile(r"\b(ALTER|GRANT|REVOKE|CREATE|DROP|SESSION\s+AUTHORIZATION|SESSION_AUTHORIZATION|SET\s+(?:LOCAL\s+|SESSION\s+)?\"?ROLE\"?|RESET|CALL|PREPARE|REASSIGN|DISCARD|LISTEN|NOTIFY|VACUUM|REINDEX|CLUSTER)\b", re.I | re.A)
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
        if tk[0] == "str" and _BODY_BAD.search(_sql_of(tk)) and re.search(r"(?:^|;)\s*(ALTER|GRANT|REVOKE|CREATE|DROP|SET)\b", _sql_of(tk), re.I | re.A):
            p.append(f"{fn} string starts a forbidden statement")
    if strict: p += [f"{fn} {x}" for x in _intro_problems(toks)]
    return p

_DENY_NOTE = {"ALTER": "ALTER of anything but ADD on a table", "GRANT": "GRANT (grants come from configuration)", "DO": "DO block", "SET": "SET other than SET LOCAL lock_timeout|statement_timeout",
              "RESET": "RESET", "SELECT": "bare SELECT", "DROP": "DROP other than DROP TRIGGER IF EXISTS", "LOCK": "LOCK", "CALL": "CALL", "PREPARE": "PREPARE", "REASSIGN": "REASSIGN OWNED",
              "INSERT": "INSERT at file level", "UPDATE": "UPDATE at file level", "DELETE": "DELETE at file level", "COPY": "COPY", "TRUNCATE": "TRUNCATE", "BEGIN": "BEGIN", "COMMIT": "COMMIT"}

# ---------------------------------------------------------------- body scans new in v19 (N3)
CALLS_OK = {"date_trunc", "clock_timestamp", "now", "format", "coalesce", "least", "greatest", "length"}
EXPR_CALLS_OK = CALLS_OK | {"btrim", "char_length", "extract"}   # calls a CHECK, DEFAULT, index or WHEN expression may use (v20 m1)
_SYNTAX_BEFORE_PAREN = {"IN", "VALUES", "AS", "AND", "OR", "NOT", "EXISTS", "ANY", "ALL", "SOME", "WHEN", "THEN", "ELSE", "CASE", "ON", "USING", "SELECT", "WHERE", "FROM", "JOIN", "SET", "INTO",
    "UPDATE", "DELETE", "INSERT", "RETURNING", "BETWEEN", "LIKE", "IS", "DISTINCT", "ONLY", "TABLE", "WITH", "IF", "LOOP", "WHILE", "RETURN", "CONFLICT", "DO", "BY", "HAVING", "LIMIT",
    "UNION", "EXCEPT", "INTERSECT", "OVER", "FILTER", "TO", "END", "BEGIN", "DEFAULT", "CHECK", "UNIQUE", "KEY", "NULL", "TRUE", "FALSE", "EXECUTE", "RETURNS", "NUMERIC", "VARCHAR", "CHAR",
    "CHARACTER", "TIMESTAMP", "TIMESTAMPTZ", "TIMETZ", "TIME", "INTERVAL", "DECIMAL", "BIT", "VARYING", "PRECISION", "NOTHING", "SESSION_USER", "CURRENT_USER"}
_SYNTAX_BEFORE_PAREN.discard("NOTHING")
def _syntax_paren(toks, k):
    """v21 m11: CONFLICT, KEY, FILTER and OVER can also be function names: they are syntax only in their own place."""
    w = toks[k][1].upper()
    if w not in _SYNTAX_BEFORE_PAREN: return False
    prev = toks[k - 1] if k else None
    if w == "CONFLICT": return bool(prev and _is(prev, "ON"))
    if w == "KEY": return bool(prev and _is(prev, "PRIMARY", "FOREIGN"))
    if w in ("FILTER", "OVER"): return prev == ("punct", ")")
    return True
def _call_problems(toks, fn, ddl=False, ok=None):
    ok = CALLS_OK if ok is None else ok
    out = []
    for k in range(len(toks) - 1):
        tk = toks[k]
        if _is(tk, "OPERATOR") and toks[k + 1] == ("punct", "("): out.append(f"{fn} uses OPERATOR(...), which can name any operator"); continue
        if toks[k + 1] != ("punct", "(") or tk[0] not in ("word", "qid"): continue
        if tk[0] == "qid": out.append(f"{fn} body calls a quoted name {tk[1]}"); continue
        if _syntax_paren(toks, k): continue
        if k and _is(toks[k - 1], "AS"): continue   # v21: `FROM t AS d (a, b)` is an alias with a column list, and `AS type(n)` a type modifier, not a call
        # v20 M1: `%I.name (` is a relation with a column list ONLY right after INTO (v19 skipped it everywhere, which hid EXECUTE format('SELECT %I.evil_fn($1)', ...))
        if k >= 3 and toks[k - 1] == ("punct", ".") and toks[k - 2] == ("word", "I") and toks[k - 3] == ("punct", "%"):
            if k >= 4 and _is(toks[k - 4], "INTO"): continue
            out.append(f"{fn} body calls a schema-qualified function %I.{tk[1]}(): only `INSERT INTO %I.name (columns)` may have a bracket after %I.name"); continue
        # v20: a name after INTO is a relation with a column list; after FROM, JOIN, UPDATE, ONLY, TABLE it is a function call (a set-returning function in FROM) except in DDL
        if k and _is(toks[k - 1], "INTO"): continue
        if k > 1 and _is(toks[k - 1], "ONLY") and _is(toks[k - 2], "INTO"): continue
        if ddl and k and _is(toks[k - 1], "TABLE", "EXISTS", "ON", "REFERENCES", "USING", "INCLUDE", "FUNCTION", "PROCEDURE", "INDEX", "ONLY"): continue
        if k and toks[k - 1] == ("punct", "."): out.append(f"{fn} body calls a schema-qualified function ...{tk[1]}"); continue
        if tk[1].lower() not in ok: out.append(f"{fn} body calls {tk[1]}(), which is not on the short list of calls a definer body may use ({sorted(ok)})")
    return out
def _set_follows_update(toks, k):
    """v20 m2: True when the SET at toks[k] directly follows `UPDATE [ONLY] name [AS alias]` or `DO UPDATE` (no ';' or other punctuation between)."""
    for j in range(k - 1, max(-1, k - 6), -1):
        t = toks[j]
        if _is(t, "UPDATE"): return True
        if t[0] not in ("word", "qid") and t != ("punct", "."): return False
        if _is(t, "SET", "SELECT", "WHERE", "FROM", "RETURNING", "VALUES", "AND", "OR"): return False
    return False
KIND_WORDS = {"INSERT", "UPDATE", "DELETE", "TRUNCATE", "MERGE", "COPY", "SELECT", "WITH"}
def _kind_problems(toks, fn, kinds):
    """v20 F1: the statement kinds a body may use are pinned per function. A kind word counts unless it is part of ON CONFLICT DO UPDATE / FOR UPDATE / ON DELETE."""
    if kinds is PIN_ANY: return []
    if kinds is None: return [f"{fn} has no statement kinds pinned for this file"]
    out, seen = [], set()
    for k, tk in enumerate(toks):
        if tk[0] != "word" or tk[1].upper() not in KIND_WORDS: continue
        w = tk[1].upper()
        if w == "UPDATE" and k and _is(toks[k - 1], "FOR", "KEY", "NO"): continue
        if w not in kinds and w not in seen: seen.add(w); out.append(f"{fn} body uses a {w} statement; the statement kinds pinned for it are {sorted(kinds)}")
    return out
def _extra_body_problems(toks, fn, definer):
    out = []
    for k, tk in enumerate(toks):
        if _is(tk, "SET") and not _set_follows_update(toks, k):
            out.append(f"{fn} body has a SET that is not part of an UPDATE (SET ROLE, SET \"role\", SET session_authorization or SET search_path)")
        if _is(tk, "DO") and not (k + 1 < len(toks) and _is(toks[k + 1], "UPDATE", "NOTHING")): out.append(f"{fn} body has a DO block")
        if _is(tk, "RESET"): out.append(f"{fn} body has RESET")
    out += _call_problems(toks, fn)
    return out
_STOP = {"WHERE", "JOIN", "INNER", "LEFT", "RIGHT", "FULL", "CROSS", "ON", "GROUP", "ORDER", "LIMIT", "HAVING", "RETURNING", "SET", "VALUES", "USING", "UNION", "FOR", "WINDOW", "DO", "SELECT", "LATERAL", "NATURAL"}
def _atomic_problems(toks, fn, tables, kinds=PIN_ANY):
    """toks = tokens of BEGIN ATOMIC ... END. Relations must be unqualified and pinned for the file; no EXECUTE; the extra rules of every body."""
    out, n = [], len(toks)
    if tables is None: return [f"{fn} has a BEGIN ATOMIC body but no `atomic_tables` are pinned for this file (a body that is not scanned is refused)"]
    def skip_paren(i):
        d = 0
        while i < n:
            if toks[i] == ("punct", "("): d += 1
            elif toks[i] == ("punct", ")"):
                d -= 1
                if d == 0: return i + 1
            i += 1
        return i
    def take(i):
        if i < n and _is(toks[i], "ONLY"): i += 1
        if i >= n or toks[i][0] not in ("word", "qid"): return i
        if i + 1 < n and toks[i + 1] == ("punct", "."):
            out.append(f"{fn} body names a schema-qualified relation"); return i + 3
        nm = _fold(toks[i])
        if nm not in tables: out.append(f"{fn} body uses the relation {toks[i][1]}, which is not pinned for this file ({sorted(tables)})")
        i += 1
        aliased = False
        if i < n and _is(toks[i], "AS"): i += 1; aliased = True
        if i < n and toks[i][0] in ("word", "qid") and not (toks[i][0] == "word" and toks[i][1].upper() in _STOP) and not _is(toks[i], "TABLESAMPLE"): i += 1; aliased = True
        if aliased and i < n and toks[i] == ("punct", "("): i = skip_paren(i)      # v21 m4: alias column list, `FROM spend AS d (a, b), pg_authid`
        if i < n and _is(toks[i], "TABLESAMPLE"):                                  # v21 m4: TABLESAMPLE method (args) [REPEATABLE (seed)]
            i += 1
            if i < n and toks[i][0] in ("word", "qid"): i += 1
            if i < n and toks[i] == ("punct", "("): i = skip_paren(i)
            if i < n and _is(toks[i], "REPEATABLE"):
                i += 1
                if i < n and toks[i] == ("punct", "("): i = skip_paren(i)
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
            if w == "INTO" and not (prev and _is(prev, "INSERT", "MERGE")): i = take(i + 1); continue   # SELECT ... INTO newtable
            if w == "INTO" and prev and _is(prev, "MERGE"): i = take(i + 1); continue
            if w == "USING": i = take(i + 1); continue          # MERGE ... USING x, DELETE ... USING x, JOIN ... USING (col) (a bracket is skipped by take)
            if w == "TABLE": i = take(i + 1); continue           # TABLE x
            if w in ("TRUNCATE", "LOCK", "COPY"):
                j = i + 1
                if j < n and _is(toks[j], "TABLE"): j += 1
                i = take(j); continue
            if w == "EXECUTE": out.append(f"{fn} body has EXECUTE")
        i += 1
    if _BODY_BAD.search(" ".join(tk[1] for tk in toks if tk[0] == "word")): out.append(f"{fn} body contains ALTER, GRANT, REVOKE, CREATE, DROP, SET ROLE, RESET, CALL or SESSION AUTHORIZATION")
    return out + _extra_body_problems(toks, fn, True) + _kind_problems(toks, fn, kinds)
def _body_problems_v19(source, fn, strict, kinds=PIN_ANY):
    p = _body_problems(source, fn, strict)
    toks = tokenize(source)
    p += _extra_body_problems(toks, fn, strict)
    if strict:
        p += _kind_problems(toks, fn, kinds)
    if strict:  # the SQL held in EXECUTE format('...') strings is scanned for calls too
        for k, tk in enumerate(toks):
            if _is(tk, "EXECUTE") and k + 3 < len(toks) and toks[k + 3][0] == "str":
                lt = tokenize(_sql_of(toks[k + 3]))
                p += _call_problems(lt, fn + " EXECUTE string") + _kind_problems(lt, fn + " EXECUTE string", kinds)
                for q, t2 in enumerate(lt):   # v20 M3: USING x, TABLE x, SELECT ... INTO x in an EXECUTE string need %I. right after
                    if _is(t2, "USING", "TABLE") and q + 1 < len(lt) and lt[q + 1] != ("punct", "(") and not _pct_i(lt, q + 1): p.append(f"{fn} EXECUTE string: {t2[1]} without %I. right after it")
                    if _is(t2, "INTO") and q and not _is(lt[q - 1], "INSERT", "MERGE") and not _pct_i(lt, q + 1): p.append(f"{fn} EXECUTE string: INTO without %I. right after it")
    return p

MAX_TIMEOUT_MS = 3600000   # one hour (my number, v22 m2): a longer lock or statement limit is as good as none for a cutover
_TO_RE = re.compile(r"\s*([1-9][0-9]{0,9})\s*(ms|s|min|h)?\s*", re.I | re.A)
_TO_UNIT = {"": 1, "ms": 1, "s": 1000, "min": 60000, "h": 3600000}
def _timeout_ms(tok):
    """v22 m2: the value of a SET LOCAL lock_timeout|statement_timeout in milliseconds, or None when the spelling is not a canonical positive integer (digits only: no 0x0, 0_0, 0e0, 0.0, no sign) with
    unit ms, s, min or h, or when it is larger than MAX_TIMEOUT_MS. A plain number (no unit) is milliseconds, like the server."""
    if tok[0] not in ("str", "num"): return None
    txt = str(tok[1])
    if tok[0] == "str": txt = txt[1:-1]
    m = _TO_RE.fullmatch(txt)
    if not m: return None
    ms = int(m.group(1)) * _TO_UNIT[(m.group(2) or "").lower()]
    return ms if 1 <= ms <= MAX_TIMEOUT_MS else None
def fingerprint(st):
    """v21 m9: first 16 hex of sha256 over the JSON list of [kind, gap flag, exact token text] (comments dropped; the amount of white space does not count, its presence does)."""
    return hashlib.sha256(json.dumps([[tk[0], int(getattr(tk, "gap", True)), str(tk[1])] for tk in st], ensure_ascii=True).encode()).hexdigest()[:16]
def _sigs(part_toks, name, problems, pre, kind):
    """REVOKE signature list -> keys (unqualified only)"""
    keys = []
    for part in _split_commas_top(part_toks):
        na = _name_and_args(part, 0)
        if na is None or na[3] != len(part): problems.append(pre + f"{kind}: a signature the guard cannot read: {_flat(part)[:60]!r}"); continue
        if na[1]: problems.append(pre + f"{kind}: a schema-qualified function name is not allowed (write the unqualified name): {_flat(part)[:60]!r}"); continue
        keys.append(sigkey(na[0], na[2]))
    return keys

def check_sql_text(name, text, allowed, grants_allowed=(), extra_statements=(), atomic_tables=None, trigger_pins=None, fn_pins=None, kinds=None, add_pins=None, require_lock_timeout=False, require_stmt_timeout=False, require_pins=None):
    """allowed: {"fname(type,type)": "definer" | "invoker"} for THIS file only; extra_statements: fingerprints pinned for this file; atomic_tables: the relations a
    BEGIN ATOMIC body of this file may use. Returns a list of problems (empty = clean). Anything that matches no shape (module docstring) is a problem."""
    problems, created_at, revoked_at, definer_keys = [], {}, {}, set()
    trig_created, trig_dropped, trig_drop_tbl, trig_tbl = {}, {}, {}, {}
    fn_names = {k.split("(")[0] for k in allowed}
    pre = f"{name}: "
    seen_to, to_warned, seen_ddl = set(), set(), set()
    def _ddl_pin(st_, what):
        seen_ddl.add(fingerprint(st_))   # v22 m6: CREATE TABLE, CREATE INDEX and COMMENT ON are pinned like ALTER TABLE ... ADD (PIN_ANY = off; None = nothing is allowed)
        if add_pins is not PIN_ANY and (add_pins is None or fingerprint(st_) not in add_pins): problems.append(pre + f"{what} whose text is not the pinned text of this file (v22 m6): {_flat(st_)[:70]!r}")
    for idx, st in enumerate(split_statements(tokenize(text))):
        lead, flat = _lead(st), _flat(st)
        short = flat[:70]
        if fingerprint(st) in extra_statements: seen_ddl.add(fingerprint(st)); continue
        if lead[:1] in (["ALTER"], ["CREATE"]) and any(w in lead for w in ("TABLE", "INDEX", "TRIGGER")) and "FUNCTION" not in lead:
            problems += [pre + x for x in _call_problems(st, "DDL expression", ddl=True, ok=EXPR_CALLS_OK)]   # v20 m1 / runner F2
        if any(_is(a, "OWNER") and _is(b, "TO") for a, b in zip(st, st[1:])):
            problems.append(pre + f"OWNER TO is not allowed: {short!r}"); continue
        first = lead[:1]
        if first == ["SET"]:
            if len(st) == 5 and _is(st[1], "LOCAL") and st[2][0] == "word" and st[2][1].lower() in ("lock_timeout", "statement_timeout") and (st[3] == ("punct", "=") or _is(st[3], "TO")) and _timeout_ms(st[4]) is not None:
                seen_to.add(st[2][1].lower()); continue
            problems.append(pre + f"SET is allowed only as `SET LOCAL lock_timeout|statement_timeout = <value>` with a positive whole number and the unit ms, s, min or h, at most one hour (a zero value switches the limit off); not SET ROLE, SET \"role\", SET session_authorization, SET search_path: {short!r}"); continue
        if (first == ["ALTER"] and lead[1:2] == ["TABLE"]) or (first == ["CREATE"] and any(w in lead for w in ("TABLE", "INDEX", "TRIGGER")) and "FUNCTION" not in lead):   # v22 m6: the timeouts come first
            for need, lab in ((require_lock_timeout, "lock_timeout"), (require_stmt_timeout, "statement_timeout")):
                if need and lab not in seen_to and lab not in to_warned:
                    to_warned.add(lab); problems.append(pre + f"SET LOCAL {lab} must come before the first statement that takes a table lock (v22 m6): {short!r}")
        if first == ["ALTER"] and lead[1:2] == ["TABLE"]:
            i = 2
            if i + 1 < len(st) and _is(st[i], "IF") and _is(st[i + 1], "EXISTS"): i += 2
            if i < len(st) and _is(st[i], "ONLY"): i += 1
            if i >= len(st) or st[i][0] not in ("word", "qid"): problems.append(pre + f"ALTER TABLE the guard cannot read: {short!r}")
            elif i + 1 < len(st) and st[i + 1] == ("punct", "."): problems.append(pre + f"ALTER TABLE with a schema-qualified name: {short!r}")
            else:
                acts = _split_commas_top(st[i + 1:])
                if not acts or not all(_is(a[0], "ADD") for a in acts): problems.append(pre + f"ALTER TABLE: every action must start with ADD (DISABLE TRIGGER, DROP CONSTRAINT, SET, OWNER, ENABLE are refused): {short!r}")
                elif (seen_ddl.add(fingerprint(st)) or True) and add_pins is not PIN_ANY and (add_pins is None or fingerprint(st) not in add_pins): problems.append(pre + f"ALTER TABLE ... ADD whose text is not the pinned text of this file, or this file has no pins at all (the CHECK expression, the column and the constraint name are pinned, v21 B1; v22 MJ2: no pin table for a file name means every ADD is a problem): {short!r}")
            continue
        if first == ["COMMENT"] and lead[1:2] == ["ON"]:
            _ddl_pin(st, "COMMENT ON"); continue
        if first == ["DROP"] and len(st) == 7 and _is(st[1], "TRIGGER") and _is(st[2], "IF") and _is(st[3], "EXISTS") and st[4][0] in ("word", "qid") and _is(st[5], "ON") and st[6][0] in ("word", "qid"):
            tn = _fold(st[4])   # v20 M2: only a trigger pinned for this file may be dropped, and the file must create it again later
            if trigger_pins is not PIN_ANY:
                if not trigger_pins or tn not in trigger_pins: problems.append(pre + f"DROP TRIGGER of {tn}, which is not a trigger pinned for this file")
                else: trig_dropped[tn] = idx; trig_drop_tbl[tn] = _fold(st[6])
            continue
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
            if AStr(re.sub(r"\s+", " ", flat, flags=re.A)).upper() not in {AStr(g).upper() for g in grants_allowed}: problems.append(pre + f"GRANT is not allowed in a .sql file (grants come from configuration): {flat[:70]!r}")
            continue
        if first == ["CREATE"]:
            orr = lead[1:3] == ["OR", "REPLACE"]
            rest = lead[3:] if orr else lead[1:]
            kind = (rest or [""])[0]
            if kind == "TABLE" and not orr:
                i = 2 if lead[1:2] == ["TABLE"] else None
                if i is not None:
                    if lead[2:5] == ["IF", "NOT", "EXISTS"]: i = 5
                    if i < len(st) and st[i][0] in ("word", "qid") and i + 1 < len(st) and st[i + 1] == ("punct", "(") and not any(_is(tk, "INHERITS") for tk in st):
                        _ddl_pin(st, "CREATE TABLE"); continue
                problems.append(pre + f"CREATE TABLE must be `CREATE TABLE [IF NOT EXISTS] <unqualified name> ( ... )` (no AS, TEMP, PARTITION OF, schema): {short!r}"); continue
            if (rest[:1] == ["INDEX"] or rest[:2] == ["UNIQUE", "INDEX"]) and not orr:
                _ddl_pin(st, "CREATE INDEX"); continue
            if kind == "TRIGGER":
                ex = [k for k, tk in enumerate(st) if _is(tk, "EXECUTE")]
                ok = False
                if ex and ex[-1] + 4 < len(st) and _is(st[ex[-1] + 1], "FUNCTION", "PROCEDURE") and st[ex[-1] + 2][0] in ("word", "qid") and st[ex[-1] + 3] == ("punct", "(") and ex[-1] + 4 <= len(st):
                    ok = _fold(st[ex[-1] + 2]) in fn_names and st[ex[-1] + 3 - 0] == ("punct", "(") and not (ex[-1] + 3 < len(st) and st[ex[-1] + 2 + 1] == ("punct", "."))
                if not ok: problems.append(pre + f"CREATE TRIGGER must end with EXECUTE FUNCTION <a function listed for this file>(): {short!r}")
                ti = next((k for k, tk in enumerate(st) if _is(tk, "TRIGGER")), None)
                if trigger_pins is not PIN_ANY:
                    tn = _fold(st[ti + 1]) if ti is not None and ti + 1 < len(st) else "?"
                    fp = fingerprint(st)
                    if not trigger_pins or tn not in trigger_pins: problems.append(pre + f"trigger {tn} is not pinned for this file (fingerprint {fp})")
                    elif trigger_pins[tn] != fp: problems.append(pre + f"trigger {tn} differs from its pin (timing, events, table, WHEN or function changed; fingerprint {fp})")
                    trig_created[tn] = idx
                    oi = next((k for k, tk in enumerate(st) if _is(tk, "ON")), None)
                    trig_tbl[tn] = _fold(st[oi + 1]) if oi is not None and oi + 1 < len(st) else "?"
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
                cutA = next((k for k, tk in enumerate(head) if _is(tk, "BEGIN") and k + 1 < len(head) and _is(head[k + 1], "ATOMIC")), None)
                cutR = next((k for k, tk in enumerate(head) if _is(tk, "RETURN")), None)   # v20 B1: SQL-standard `RETURN <expr>` body
                cut = min([c for c in (cutA, cutR) if c is not None], default=None)
                attrs, atomic = (head if cut is None else head[:cut]), cutA is not None and cut == cutA
                retexpr = head[cutR + 1:] if cut is not None and cut == cutR else None
                nb = len([tk for tk in attrs if tk[0] in ("str", "dollar")])
                if cut is None and nb != 1: problems.append(pre + f"{key}: the head after the attributes is not BEGIN ATOMIC, RETURN <expression> or exactly one string or dollar body (found {nb} bodies): the function would not be scanned")
                if cut is not None and nb: problems.append(pre + f"{key}: a string or dollar body next to BEGIN ATOMIC or RETURN")
                if any(_is(tk, "LEAKPROOF", "SUPPORT", "TRANSFORM", "WINDOW") for tk in attrs): problems.append(pre + f"{key}: LEAKPROOF, SUPPORT, TRANSFORM and WINDOW are not allowed")
                if fn_pins is not PIN_ANY:
                    fp = fingerprint(st)
                    if not fn_pins or key not in fn_pins: problems.append(pre + f"{key} has no pinned fingerprint for this file (fingerprint {fp})")
                    elif fn_pins[key] != fp: problems.append(pre + f"{key} differs from its pin (head or body changed; fingerprint {fp})")
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
                                items.append(_sp_item(a2[m])); m += 1
                                if m < len(a2) and a2[m] == ("punct", ","): m += 1
                                else: break
                            paths.append(items)
                        else: problems.append(pre + f"{key}: a SET attribute other than search_path")
                    if paths != [["pg_catalog", "pg_temp"]]: problems.append(pre + f"{key}: search_path must be exactly pg_catalog, pg_temp (found {paths})")
                kd = kinds if kinds is PIN_ANY else (kinds or {}).get(key)
                if atomic: problems += [pre + x for x in _atomic_problems(head[cut:], key, atomic_tables, kd if definer else PIN_ANY)]
                elif retexpr is not None: problems += [pre + x for x in _atomic_problems([("word", "BEGIN"), ("word", "ATOMIC")] + retexpr, key + " RETURN expression", atomic_tables, kd if definer else PIN_ANY)]
                else:
                    for b in bodies: problems += [pre + x for x in _body_problems_v19(_body_source(b), key, definer, kd if definer else PIN_ANY)]
                continue
        problems.append(pre + f"statement is not on the allow-list of shapes ({_DENY_NOTE.get(first[0], ' '.join(lead[:2])) if first else 'unreadable'}): {short!r}")
    if trigger_pins is not PIN_ANY:   # v20 M2: every pinned trigger exists after the file; a drop is followed by a create
        for tn in sorted(trigger_pins or {}):
            if tn not in trig_created: problems.append(f"{name}: pinned trigger {tn} is not created by this file")
            elif tn in trig_dropped and trig_created[tn] < trig_dropped[tn]: problems.append(f"{name}: trigger {tn} is dropped after its last CREATE (the table would be left without it)")
            elif tn in trig_drop_tbl and trig_drop_tbl[tn] != trig_tbl.get(tn): problems.append(f"{name}: DROP TRIGGER {tn} ON {trig_drop_tbl[tn]} names another table than the CREATE TRIGGER ({trig_tbl.get(tn)}): it would drop a same-named trigger of a different table")
    for key in sorted(definer_keys):
        if key not in revoked_at: problems.append(f"{name}: {key} has no REVOKE ALL ON FUNCTION {key} FROM PUBLIC for this signature")
        elif revoked_at[key] < created_at[key]: problems.append(f"{name}: the REVOKE of {key} comes BEFORE its last CREATE (a re-created function would get PUBLIC execute back): put the REVOKE after the CREATE")
    if require_pins:   # v22 (v21 evidence R01-R04, R08, H23, Q02-Q07): every pinned DDL statement must be PRESENT, not only unchanged when present
        for fp_ in sorted(set(require_pins) - seen_ddl): problems.append(pre + f"pinned statement {fp_} is missing from this file (a deleted ADD CONSTRAINT / column / COMMENT would leave the server without that check)")
    for need, lab in ((require_lock_timeout, "lock_timeout"), (require_stmt_timeout, "statement_timeout")):
        if need and lab not in seen_to and lab not in to_warned: problems.append(pre + f"SET LOCAL {lab} is missing from this file (v22)")
    return problems

def _split_commas_top(toks): return [p for p in _split_commas(toks) if p]
