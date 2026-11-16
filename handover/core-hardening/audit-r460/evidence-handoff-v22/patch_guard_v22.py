"""Builds secdef_guard_v22.py from secdef_guard_v21.py. Every replacement is asserted to match exactly once. Round 9 (v22).
v22 changes (security MJ2, m2, m6): (1) add_pins=None now means EVERY ALTER TABLE ... ADD is a problem (v21 skipped the check for a file that is not a key of the pin table);
(2) the same pin table also pins CREATE TABLE, CREATE INDEX and COMMENT ON; (3) a timeout must be a canonical positive integer with unit ms|s|min|h, at most one hour
(`0x0`, `0_0`, `0e0`, `0.0`, a unit-less 0 and `999999h` are refused); (4) a file may be required to set both timeouts BEFORE its first locking statement."""
src = open("secdef_guard_v21.py").read()
def rep(old, new, count=1):
    global src
    assert src.count(old) == count, (src.count(old), old[:80])
    src = src.replace(old, new)
rep('"""v21 class guard = v20 plus', '''"""v22 class guard = v21 plus (security MJ2) `add_pins=None` means every ALTER TABLE ... ADD is a problem (v21 skipped the pin check for a file that is not a key of the pin table, so a renamed
or new held file could carry `ADD CONSTRAINT ... CHECK (true)`); (security m6) the pin table also pins CREATE TABLE, CREATE INDEX and COMMENT ON statements; (security m2) a SET LOCAL timeout must be a canonical
positive integer with unit ms, s, min or h and at most MAX_TIMEOUT_MS (one hour; my number): `0x0`, `0_0`, `0e0`, `0.0`, `'0'` and `999999h` are refused; (m6) `require_lock_timeout` and `require_stmt_timeout`:
the file must set the timeout BEFORE its first ALTER TABLE, CREATE TABLE, CREATE INDEX or CREATE TRIGGER. PIN_ANY switches the DDL pin off for a unit mutant; None means nothing is allowed. The v21 text follows unchanged.

v21 class guard = v20 plus''')
rep("def fingerprint(st):", '''MAX_TIMEOUT_MS = 3600000   # one hour (my number, v22 m2): a longer lock or statement limit is as good as none for a cutover
_TO_RE = re.compile(r"\\s*([1-9][0-9]{0,9})\\s*(ms|s|min|h)?\\s*", re.I | re.A)
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
def fingerprint(st):''')
rep("trigger_pins=None, fn_pins=None, kinds=None, add_pins=None):", "trigger_pins=None, fn_pins=None, kinds=None, add_pins=None, require_lock_timeout=False, require_stmt_timeout=False):")
rep('''    fn_names = {k.split("(")[0] for k in allowed}
    pre = f"{name}: "
''', '''    fn_names = {k.split("(")[0] for k in allowed}
    pre = f"{name}: "
    seen_to, to_warned = set(), set()
    def _ddl_pin(st_, what):   # v22 m6: CREATE TABLE, CREATE INDEX and COMMENT ON are pinned like ALTER TABLE ... ADD (PIN_ANY = off; None = nothing is allowed)
        if add_pins is not PIN_ANY and (add_pins is None or fingerprint(st_) not in add_pins): problems.append(pre + f"{what} whose text is not the pinned text of this file (v22 m6): {_flat(st_)[:70]!r}")
''')
rep('''and st[4][0] in ("str", "num") and not re.fullmatch(r"'?\\s*0*(\\.0*)?\\s*(us|ms|s|min|h|d)?\\s*'?", str(st[4][1]), re.I | re.A): continue
            problems.append(pre + f"SET is allowed only as `SET LOCAL lock_timeout|statement_timeout = <value>` (not SET ROLE, SET \\"role\\", SET session_authorization, SET search_path): {short!r}"); continue''',
'''and _timeout_ms(st[4]) is not None:
                seen_to.add(st[2][1].lower()); continue
            problems.append(pre + f"SET is allowed only as `SET LOCAL lock_timeout|statement_timeout = <value>` with a positive whole number and the unit ms, s, min or h, at most one hour (a zero value switches the limit off); not SET ROLE, SET \\"role\\", SET session_authorization, SET search_path: {short!r}"); continue
        if (first == ["ALTER"] and lead[1:2] == ["TABLE"]) or (first == ["CREATE"] and any(w in lead for w in ("TABLE", "INDEX", "TRIGGER")) and "FUNCTION" not in lead):   # v22 m6: the timeouts come first
            for need, lab in ((require_lock_timeout, "lock_timeout"), (require_stmt_timeout, "statement_timeout")):
                if need and lab not in seen_to and lab not in to_warned:
                    to_warned.add(lab); problems.append(pre + f"SET LOCAL {lab} must come before the first statement that takes a table lock (v22 m6): {short!r}")''')
rep('''                elif add_pins is not None and fingerprint(st) not in add_pins: problems.append(pre + f"ALTER TABLE ... ADD whose text is not the pinned text of this file (the CHECK expression, the column and the constraint name are pinned, v21 B1): {short!r}")''',
'''                elif add_pins is not PIN_ANY and (add_pins is None or fingerprint(st) not in add_pins): problems.append(pre + f"ALTER TABLE ... ADD whose text is not the pinned text of this file, or this file has no pins at all (the CHECK expression, the column and the constraint name are pinned, v21 B1; v22 MJ2: no pin table for a file name means every ADD is a problem): {short!r}")''')
rep('''if first == ["COMMENT"] and lead[1:2] == ["ON"]: continue''', '''if first == ["COMMENT"] and lead[1:2] == ["ON"]:
            _ddl_pin(st, "COMMENT ON"); continue''')
rep('''not any(_is(tk, "INHERITS") for tk in st): continue''', '''not any(_is(tk, "INHERITS") for tk in st):
                        _ddl_pin(st, "CREATE TABLE"); continue''')
rep('''if (rest[:1] == ["INDEX"] or rest[:2] == ["UNIQUE", "INDEX"]) and not orr: continue''', '''if (rest[:1] == ["INDEX"] or rest[:2] == ["UNIQUE", "INDEX"]) and not orr:
                _ddl_pin(st, "CREATE INDEX"); continue''')
open("secdef_guard_v22.py", "w").write(src)
print("secdef_guard_v22.py written", len(src))
