"""v18 class guard for SECURITY DEFINER and everything that can change who may run, or who owns, a function
(security major MA1 of the v17 review). Reference for the DB-1 builder, not product code.
Class: a text scan that looks for ONE spelling of the danger (v16: a token in one statement shape; v17: a token plus a few
shapes) is bypassed by every other spelling. v18 is DENY BY DEFAULT: one tokenizer (comments, single quotes, E'..',
dollar quotes and double-quoted names are read by the same code, so no quoted name can start a comment), statements are split
once, and a statement is a problem unless it is on this file's allow-list or is a harmless kind.
Rules (each has a mutant in secdef_mutants_v18.py):
 R1 every CREATE FUNCTION is `CREATE OR REPLACE FUNCTION name(types)` and its name AND signature are on THIS file's list
    (list value `definer` or `invoker`; the token must match the list); no PROCEDURE, ROUTINE, AGGREGATE, DO, LANGUAGE c.
 R2 ALTER FUNCTION/ROUTINE/PROCEDURE, ALTER DEFAULT PRIVILEGES, ALTER ROLE/SCHEMA/DATABASE/SYSTEM, `OWNER TO`, SET ROLE,
    SET SESSION AUTHORIZATION, RESET ROLE/ALL are problems in any file. SECURITY DEFINER anywhere else is a problem.
 R3 every GRANT is a problem (grants come from config, never from a .sql file); a file may name exact (statement) grants
    in `grants_allowed`, none does today.
 R4 a definer function has `SET search_path = pg_catalog, pg_temp` exactly, no other SET attribute, and one
    `REVOKE ALL ON FUNCTION name(types) FROM PUBLIC` PER SIGNATURE (overloads each need their own).
 R5 in a plpgsql or sql string body every relation after INSERT INTO, UPDATE, DELETE FROM, TRUNCATE, MERGE INTO, COPY, LOCK,
    DROP .., FROM, JOIN is written `%I.` (inside the format string of EXECUTE); every EXECUTE is `EXECUTE format('..', TG_TABLE_SCHEMA..)`
    followed by USING, INTO or `;`; the format string has only %I and %% (no %s, %L); ALTER, GRANT, REVOKE, CREATE, SET ROLE in a body are problems.
 R6 a BEGIN ATOMIC body (names bound at creation) needs no %I.; CASE ... END inside it does not end the body."""
import re

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
def _type_of(toks):
    ws, d = [], 0
    for tk in toks:
        if tk == ("punct", "("): d += 1; continue
        if tk == ("punct", ")"): d -= 1; continue
        if d: continue
        if _is(tk, "DEFAULT") or tk == ("punct", "="): break
        ws.append(tk[1].lower().strip('"') if tk[0] != "punct" else tk[1])
    if ws and ws[0].upper() in _MODES: ws = ws[1:]
    if len(ws) >= 2 and ws[0].upper() not in _MULTI and ws[1] != "[": ws = ws[1:]
    s = " ".join(ws).replace(" [ ]", "[]").replace("pg_catalog . ", "")
    return _ALIAS.get(s, s)
def sigkey(name, arg_toks):
    parts = [p for p in _split_commas(arg_toks) if p]
    return f"{name.lower()}({','.join(_type_of(p) for p in parts)})"
def _name_and_args(st, i):
    """st[i] is the first token of the (possibly schema-qualified) name; returns (name, arg tokens, index after ')') or None."""
    j, name = i, None
    while j < len(st) and st[j][0] in ("word", "qid"):
        name = st[j][1].strip('"') if st[j][0] == "qid" else st[j][1]; j += 1
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
    return name, st[j + 1:k], k + 1

# ---------------------------------------------------------------- body rules (R5)
_RELATION_INTRO = [("INSERT", "INTO"), ("DELETE", "FROM"), ("MERGE", "INTO"), ("TRUNCATE", "TABLE"), ("LOCK", "TABLE")]
_ONE = {"UPDATE", "TRUNCATE", "COPY", "LOCK", "FROM", "JOIN", "ONLY"}
_BODY_BAD = re.compile(r"\b(ALTER|GRANT|REVOKE|CREATE|DROP|SESSION\s+AUTHORIZATION|SET\s+(?:LOCAL\s+|SESSION\s+)?ROLE|RESET\s+ROLE)\b", re.I)
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
def _body_problems(source, fn):
    p = []
    toks = tokenize(source)
    for k, tk in enumerate(toks):
        if _is(tk, "EXECUTE"):
            ok = k + 3 < len(toks) and _is(toks[k + 1], "format") and toks[k + 2] == ("punct", "(") and toks[k + 3][0] == "str"
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
    p += [f"{fn} {x}" for x in _intro_problems(toks)]
    return p

_DENY_CREATE = {"PROCEDURE", "ROUTINE", "AGGREGATE", "OPERATOR", "CAST", "LANGUAGE", "EXTENSION", "TRANSFORM", "EVENT", "RULE", "ROLE", "USER", "GROUP", "SCHEMA"}
_DENY_ALTER = {"FUNCTION", "ROUTINE", "PROCEDURE", "ROLE", "USER", "GROUP", "SYSTEM", "SCHEMA", "DATABASE", "LANGUAGE", "EXTENSION"}

def check_sql_text(name, text, allowed, grants_allowed=()):
    """allowed: {"fname(type,type)": "definer" | "invoker"} for THIS file only. Returns a list of problems (empty = clean)."""
    problems, created, revoked = [], {}, set()
    for st in split_statements(tokenize(text)):
        lead, flat = _lead(st), _flat(st)
        pre = f"{name}: "
        if lead[:1] == ["ALTER"] and (lead[1:2] and lead[1] in _DENY_ALTER or lead[1:3] == ["DEFAULT", "PRIVILEGES"]):
            problems.append(pre + f"{' '.join(lead[:3])} is not allowed in a migration or held file: {flat[:60]!r}"); continue
        if any(_is(a, "OWNER") and _is(b, "TO") for a, b in zip(st, st[1:])):
            problems.append(pre + f"OWNER TO is not allowed: {flat[:60]!r}"); continue
        if lead[:1] == ["SET"] and [w for w in lead[1:] if w not in ("LOCAL", "SESSION")][:1] in (["ROLE"], ["AUTHORIZATION"]):
            problems.append(pre + f"SET ROLE or SET SESSION AUTHORIZATION is not allowed: {flat[:60]!r}"); continue
        if lead[:1] == ["RESET"] and lead[1:2] in (["ROLE"], ["SESSION"], ["ALL"]):
            problems.append(pre + f"RESET ROLE, SESSION AUTHORIZATION or ALL is not allowed: {flat[:60]!r}"); continue
        if lead[:1] == ["DO"]:
            problems.append(pre + "DO block is not allowed"); continue
        if lead[:1] == ["GRANT"]:
            if re.sub(r"\s+", " ", flat).upper() not in {g.upper() for g in grants_allowed}: problems.append(pre + f"GRANT is not allowed in a .sql file (grants come from configuration): {flat[:70]!r}")
            continue
        if lead[:1] == ["REVOKE"]:
            m = [k for k, tk in enumerate(st) if _is(tk, "FUNCTION")]
            if m and any(_is(tk, "FROM") and k + 1 < len(st) and _is(st[k + 1], "PUBLIC") for k, tk in enumerate(st)) and _is(st[1], "ALL", "EXECUTE"):
                k = m[0] + 1
                for part in _split_commas_top(st[k:next(i for i, tk in enumerate(st) if i > k and _is(tk, "FROM"))]):
                    na = _name_and_args(part, 0)
                    if na: revoked.add(sigkey(na[0], na[1]))
            continue
        if lead[:1] == ["CREATE"]:
            rest = lead[2:] if lead[1:3] == ["OR", "REPLACE"] else lead[1:]
            kind = (rest or [""])[0]
            if kind in _DENY_CREATE:
                problems.append(pre + f"CREATE {kind} is not allowed: {flat[:60]!r}"); continue
            if kind == "FUNCTION":
                i0 = next(i for i, tk in enumerate(st) if _is(tk, "FUNCTION")) + 1
                na = _name_and_args(st, i0)
                if na is None:
                    problems.append(pre + f"CREATE FUNCTION with a head the guard cannot read: {flat[:60]!r}"); continue
                fn, args, after = na; key = sigkey(fn, args)
                if lead[1:3] != ["OR", "REPLACE"]: problems.append(pre + f"{key} is a plain CREATE FUNCTION (use CREATE OR REPLACE)")
                want = allowed.get(key)
                if want is None: problems.append(pre + f"function {key} is not on the list of this file")
                created[key] = want
                head = st[after:]
                cut = next((k for k, tk in enumerate(head) if _is(tk, "BEGIN") and k + 1 < len(head) and _is(head[k + 1], "ATOMIC")), None)
                attrs, atomic = (head if cut is None else head[:cut]), cut is not None
                a2 = [("str", "<body>") if tk[0] in ("str", "dollar") else tk for tk in attrs]
                definer_here = [k for k in range(len(st) - 1) if _is(st[k], "SECURITY") and _is(st[k + 1], "DEFINER")]
                has_def = any(_is(a2[k], "SECURITY") and k + 1 < len(a2) and _is(a2[k + 1], "DEFINER") for k in range(len(a2) - 1))
                if len(definer_here) != (1 if has_def else 0): problems.append(pre + f"{key}: SECURITY DEFINER is written inside a body or twice")
                if want == "definer" and not has_def: problems.append(pre + f"{key} is listed as definer but has no SECURITY DEFINER")
                if want == "invoker" and has_def: problems.append(pre + f"{key} is listed as invoker but is SECURITY DEFINER")
                lang = [a2[k + 1][1].lower() for k in range(len(a2) - 1) if _is(a2[k], "LANGUAGE")]
                if any(l not in ("sql", "plpgsql") for l in lang): problems.append(pre + f"{key}: LANGUAGE {lang} is not allowed")
                bodies = [tk for tk in attrs if tk[0] in ("str", "dollar")]
                if has_def or want == "definer":
                    sets = [k for k in range(len(a2)) if _is(a2[k], "SET")]
                    paths = []
                    for k in sets:
                        if k + 1 < len(a2) and _is(a2[k + 1], "search_path"):
                            items, m = [], k + 3 if k + 2 < len(a2) and (a2[k + 2] == ("punct", "=") or _is(a2[k + 2], "TO")) else None
                            while m is not None and m < len(a2):
                                items.append(a2[m][1].strip('"').strip("'").lower()); m += 1
                                if m < len(a2) and a2[m] == ("punct", ","): m += 1
                                else: break
                            paths.append(items)
                        else: problems.append(pre + f"{key}: a SET attribute other than search_path")
                    if paths != [["pg_catalog", "pg_temp"]]: problems.append(pre + f"{key}: search_path must be exactly pg_catalog, pg_temp (found {paths})")
                    if not atomic:
                        for b in bodies: problems += [pre + x for x in _body_problems(b[1][2:-2] if b[0] == "str" is False else (_sql_of(b) if b[0] == "str" else b[1][b[1].index("$", 1) + 1:b[1].rindex("$", 0, len(b[1]) - 1 - (len(b[1]) - 1 - b[1].rindex("$", 0, len(b[1]) - 1)))]), key)]
                else:
                    for b in bodies: problems += [pre + x for x in _body_problems(_sql_of(b) if b[0] == "str" else b[1][b[1].index("$", 1) + 1:b[1].rindex("$", 0, len(b[1]) - 1)], key) if "forbidden" in x or "ALTER, GRANT" in x]
                continue
        if any(_is(a, "SECURITY") and _is(b, "DEFINER") for a, b in zip(st, st[1:])):
            problems.append(pre + f"SECURITY DEFINER outside a declared CREATE OR REPLACE FUNCTION: {flat[:60]!r}")
    for key, want in created.items():
        if want == "definer" and key not in revoked: problems.append(f"{name}: {key} has no REVOKE ALL ON FUNCTION {key} FROM PUBLIC for this signature")
    return problems

def _split_commas_top(toks): return [p for p in _split_commas(toks) if p]
