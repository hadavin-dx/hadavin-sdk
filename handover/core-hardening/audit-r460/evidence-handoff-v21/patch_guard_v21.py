"""Builds secdef_guard_v21.py from secdef_guard_v20.py. Every replacement is asserted to match exactly once. Round 8."""
import sys
src = open("secdef_guard_v20.py").read()
def rep(old, new, count=1):
    global src
    assert src.count(old) == count, (src.count(old), old[:70])
    src = src.replace(old, new)
rep('"""v20 class guard (v19 plus', '''"""v21 class guard = v20 plus the round-7 findings of the security review (m4 alias column list and TABLESAMPLE in the relation scan, m5 ASCII-only case folding
(AStr; regex flags re.ASCII), m6 search_path items folded like names, m7 a -- comment ends at \\\\n or \\\\r, m9 fingerprint = sha256 of the exact token texts plus token kind and a
gap flag (so `@-` and `@ -`, `E'x'` and `E 'x'` differ; comments and the amount of white space do not count), m11 contextual syntax words, zero timeouts, INHERITS, DROP TRIGGER table).
The v20 text follows unchanged.

v20 class guard (v19 plus''')
rep("import re, hashlib\n", '''import re, hashlib, json
_UPMAP = {c: c - 32 for c in range(ord("a"), ord("z") + 1)}; _LOMAP = {c: c + 32 for c in range(ord("A"), ord("Z") + 1)}
class AStr(str):
    """v21 m5: Postgres folds ONLY ASCII letters in an unquoted name or keyword (multibyte characters are left alone); Python's str.upper() also maps U+212A (Kelvin) to K, U+017F (long s) to S and so on."""
    def upper(self): return AStr(str.translate(self, _UPMAP))
    def lower(self): return AStr(str.translate(self, _LOMAP))
class Tok(tuple):
    """(kind, text) with a `gap` flag: True when white space or a comment came right before it (v21 m9)."""
    def __new__(cls, kind, text, gap=True):
        o = super().__new__(cls, (kind, AStr(text))); o.gap = gap; return o
''')
rep('''    out, i, n = [], 0, len(t)
    while i < n:
        c = t[i]
        if c in " \\t\\n\\r\\f\\v": i += 1
        elif t.startswith("--", i):
            j = t.find("\\n", i); i = n if j < 0 else j''', '''    out, i, n, last_end = [], 0, len(t), 0
    while i < n:
        c = t[i]; i0, nb = i, len(out)
        if c in " \\t\\n\\r\\f\\v": i += 1
        elif t.startswith("--", i):
            m = re.compile(r"[\\n\\r]").search(t, i); i = n if m is None else m.start()   # v21 m7: Postgres scan.l: non_newline is [^\\n\\r]''')
rep('''        else:
            out.append(("punct", c)); i += 1
    return out
''', '''        else:
            out.append(("punct", c)); i += 1
        if len(out) > nb: out[-1] = Tok(out[-1][0], out[-1][1], i0 > last_end); last_end = i
    return out
''')
rep('''def fingerprint(st): return hashlib.sha256(" ".join(tk[1] for tk in st).encode()).hexdigest()[:16]''',
    '''def fingerprint(st):
    """v21 m9: first 16 hex of sha256 over the JSON list of [kind, gap flag, exact token text] (comments dropped; the amount of white space does not count, its presence does)."""
    return hashlib.sha256(json.dumps([[tk[0], int(getattr(tk, "gap", True)), str(tk[1])] for tk in st], ensure_ascii=True).encode()).hexdigest()[:16]''')
rep('re.compile(r"\\b(ALTER|GRANT', 're.compile(r"\\b(ALTER|GRANT')  # sanity, unchanged
rep('|CLUSTER)\\b", re.I)', '|CLUSTER)\\b", re.I | re.A)')
rep('''re.match(r"\\s*(ALTER|GRANT|REVOKE|CREATE|DROP|SET)\\b", _sql_of(tk), re.I)''', '''re.match(r"\\s*(ALTER|GRANT|REVOKE|CREATE|DROP|SET)\\b", _sql_of(tk), re.I | re.A)''')
rep('''if re.sub(r"\\s+", " ", flat).upper() not in {g.upper() for g in grants_allowed}''', '''if AStr(re.sub(r"\\s+", " ", flat, flags=re.A)).upper() not in {AStr(g).upper() for g in grants_allowed}''')
# m6 search_path items
rep('''items.append(a2[m][1].strip('"').strip("'").lower()); m += 1''', '''items.append(_sp_item(a2[m])); m += 1''')
rep('def _type_of(toks):', '''def _sp_item(tk):
    """v21 m6: one search_path item as the SERVER reads it: a word is folded to ASCII lower case, a double-quoted name by _fold (so "PG_CATALOG" stays a different schema), a string
    by the server's list rule (no double quote or comma inside is accepted, then folded); anything else keeps a marker that never equals pg_catalog or pg_temp."""
    if tk[0] == "word": return str(tk[1].lower())
    if tk[0] == "qid": return str(_fold(tk))
    if tk[0] == "str":
        inner = tk[1][1:-1].replace("''", "'")
        return "?" + inner if ('"' in inner or "," in inner or "\\\\" in tk[1]) else str(AStr(inner).lower())
    return "?" + str(tk[1])
def _type_of(toks):''')
# m4 alias column list and TABLESAMPLE
rep('''        if i < n and _is(toks[i], "AS"): i += 1
        if i < n and toks[i][0] in ("word", "qid") and not (toks[i][0] == "word" and toks[i][1].upper() in _STOP): i += 1
        return i''', '''        aliased = False
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
        return i''')
rep('''    def take(i):
        if i < n and _is(toks[i], "ONLY"): i += 1''', '''    def skip_paren(i):
        d = 0
        while i < n:
            if toks[i] == ("punct", "("): d += 1
            elif toks[i] == ("punct", ")"):
                d -= 1
                if d == 0: return i + 1
            i += 1
        return i
    def take(i):
        if i < n and _is(toks[i], "ONLY"): i += 1''')
# m11 contextual syntax words
rep('"WITH", "IF", "ELSIF", "LOOP", "WHILE", "RETURN", "CONFLICT",', '"WITH", "IF", "LOOP", "WHILE", "RETURN", "CONFLICT",')
rep('"OVER", "FILTER", "TO", "END"', '"OVER", "FILTER", "TO", "END"')
rep('"KEY", "NULL", "TRUE"', '"KEY", "NULL", "TRUE"')
rep('"SESSION_USER", "CURRENT_USER"}', '"SESSION_USER", "CURRENT_USER"}\n_SYNTAX_BEFORE_PAREN.discard("NOTHING")\ndef _syntax_paren(toks, k):\n    """v21 m11: CONFLICT, KEY, FILTER and OVER can also be function names: they are syntax only in their own place."""\n    w = toks[k][1].upper()\n    if w not in _SYNTAX_BEFORE_PAREN: return False\n    prev = toks[k - 1] if k else None\n    if w == "CONFLICT": return bool(prev and _is(prev, "ON"))\n    if w == "KEY": return bool(prev and _is(prev, "PRIMARY", "FOREIGN"))\n    if w in ("FILTER", "OVER"): return prev == ("punct", ")") or w == "OVER"\n    return True')
rep('        if tk[1].upper() in _SYNTAX_BEFORE_PAREN: continue', '        if _syntax_paren(toks, k): continue')
# m11 zero timeouts
rep('''and st[4][0] in ("str", "num"): continue''', '''and st[4][0] in ("str", "num") and not re.fullmatch(r"'?\\s*0*(\\.0*)?\\s*(us|ms|s|min|h|d)?\\s*'?", str(st[4][1]), re.I | re.A): continue''')
# m11 INHERITS
rep('''                    if i < len(st) and st[i][0] in ("word", "qid") and i + 1 < len(st) and st[i + 1] == ("punct", "("): continue''', '''                    if i < len(st) and st[i][0] in ("word", "qid") and i + 1 < len(st) and st[i + 1] == ("punct", "(") and not any(_is(tk, "INHERITS") for tk in st): continue''')
# m11 DROP TRIGGER table must equal the table of the later CREATE TRIGGER
rep('trig_created, trig_dropped = {}, {}', 'trig_created, trig_dropped, trig_drop_tbl, trig_tbl = {}, {}, {}, {}')
rep('else: trig_dropped[tn] = idx', 'else: trig_dropped[tn] = idx; trig_drop_tbl[tn] = _fold(st[6])')
rep('                    trig_created[tn] = idx\n', '                    trig_created[tn] = idx\n                    oi = next((k for k, tk in enumerate(st) if _is(tk, "ON")), None)\n                    trig_tbl[tn] = _fold(st[oi + 1]) if oi is not None and oi + 1 < len(st) else "?"\n')
rep('''            elif tn in trig_dropped and trig_created[tn] < trig_dropped[tn]: problems.append(f"{name}: trigger {tn} is dropped after its last CREATE (the table would be left without it)")''',
 '''            elif tn in trig_dropped and trig_created[tn] < trig_dropped[tn]: problems.append(f"{name}: trigger {tn} is dropped after its last CREATE (the table would be left without it)")
            elif tn in trig_drop_tbl and trig_drop_tbl[tn] != trig_tbl.get(tn): problems.append(f"{name}: DROP TRIGGER {tn} ON {trig_drop_tbl[tn]} names another table than the CREATE TRIGGER ({trig_tbl.get(tn)}): it would drop a same-named trigger of a different table")''')
open("secdef_guard_v21.py", "w").write(src)
print("written", len(src))
