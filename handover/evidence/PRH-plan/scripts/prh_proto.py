"""AUTHOR PROTOTYPE (throwaway, never committed): the planned change applied by monkeypatching a clean main import."""
import re, time, unicodedata, importlib, subprocess, sys
from hadavin_sdk.guard import runmap
from hadavin_sdk import tools, defaults
R = importlib.import_module("hadavin_sdk.guard.redact")
CONT = "--cont" in sys.argv
import os
PRUNE = os.environ.get("NOPRUNE") != "1"
# ---- class table (prototype) ----
SPACE_LIKE = frozenset("\x0b\x0c\x1c\x1d\x1e\x1f\x85  ")
KEEP = frozenset("\t\n\r")
STRING_ESC = "PX]^_"; STRING_C1 = "\x90\x98\x9d\x9e\x9f"
def is_ctl(c): 
    o = ord(c); return o < 0x20 or 0x7f <= o <= 0x9f
def _word(c): return c.isalnum() or c == "_"
def strip(text):
    """-> (D, S). One pass, ECMA-48 state machine."""
    if text.isascii() and text.isprintable(): return text, text
    out = []; i = 0; n = len(text); pend = False  # pend: a removed run directly before the next kept char
    joints = []
    def keep(ch):
        nonlocal pend
        if pend and out and _word(out[-1]) and _word(ch): joints.append(len(out))
        pend = False; out.append(ch)
    while i < n:
        c = text[i]
        if CONT and c == "\\" and (text.startswith("\n", i + 1) or text.startswith("\r\n", i + 1)):
            j = i + (2 if text[i + 1] == "\n" else 3)
            joints.append((len(out), text[i:j])); i = j; pend = False; continue
        if not is_ctl(c) and c not in "  ": keep(c); i += 1; continue
        if c in KEEP: keep(c); i += 1; continue
        if c in SPACE_LIKE: keep(" "); i += 1; continue
        kind = None
        if c == "\x1b" and i + 1 < n:
            d = text[i + 1]
            if d == "[": kind, i = "csi", i + 2
            elif d in STRING_ESC: kind, i = ("osc" if d == "]" else "str"), i + 2
            elif " " <= d <= "/":
                j = i + 1
                while j < n and " " <= text[j] <= "/": j += 1
                i = j + 1 if j < n and "0" <= text[j] <= "~" else i + 1
            elif "0" <= d <= "~": i += 2
            else: i += 1
        elif c == "\x9b": kind, i = "csi", i + 1
        elif c in STRING_C1: kind, i = ("osc" if c == "\x9d" else "str"), i + 1
        else: i += 1
        if kind == "csi":
            while i < n:
                e = text[i]
                if "@" <= e <= "~": i += 1; break
                if " " <= e <= "?": i += 1; continue
                if e in "\x18\x1a": i += 1; break
                if e in "\n\r\x1b" or e in "\x9b" or e in STRING_C1 or not is_ctl(e): break
                i += 1  # a C0 control or DEL inside the sequence
        elif kind:
            while i < n:
                e = text[i]
                if e == "\x9c" or (e == "\x07" and kind == "osc") or e in "\x18\x1a": i += 1; break
                if e == "\x1b" and text.startswith("\\", i + 1): i += 2; break
                if e in "\n\r": break
                i += 1
        pend = True
    D = "".join(out)
    if not joints: return D, D
    s = []; last = 0
    for j in joints:
        pos, ins = (j, " ") if isinstance(j, int) else j
        s += [D[last:pos], ins]; last = pos
    s.append(D[last:])
    return D, "".join(s)
# ---- default ignorable, from memory, checked against perl below ----
def _di_formula():
    out = set()
    rng = [(0x34F,0x34F),(0x115F,0x1160),(0x17B4,0x17B5),(0x180B,0x180D),(0x180F,0x180F),(0x2065,0x2065),(0x3164,0x3164),(0xFE00,0xFE0F),(0xFFA0,0xFFA0),(0xFFF0,0xFFF8),(0xE0000,0xE0000),(0xE0002,0xE001F),(0xE0080,0xE0FFF)]
    for a, b in rng: out.update(range(a, b + 1))
    out.update(c for c in range(0x110000) if unicodedata.category(chr(c)) == "Cf")
    for a, b in [(0xFFF9,0xFFFB),(0x13430,0x1343F),(0x600,0x605),(0x6DD,0x6DD),(0x70F,0x70F),(0x890,0x891),(0x8E2,0x8E2),(0x110BD,0x110BD),(0x110CD,0x110CD)]:
        out.difference_update(range(a, b + 1))
    return out
DI = _di_formula()
IGN = frozenset(chr(c) for c in DI)
def _ign(c): return c in IGN or unicodedata.category(c) == "Cf"
def canonical(text):
    return "".join(c for c in unicodedata.normalize("NFKC", text) if not _ign(c))
def _canonical_view(text):
    chars, index = [], []
    for i, c in enumerate(text):
        for d in unicodedata.normalize("NFKC", c):
            if not _ign(d): chars.append(d); index.append(i)
    return "".join(chars), index
GAP = r"(?: |\\\r?\n)?" if CONT else " ?"
def _spaced(v):
    return re.compile(GAP.join(re.escape(c) for c in v))
MAXV = 256
def _both(text, mapping, neutralise, cache, stats):
    D, S = strip(text)
    nS = runmap.fits_after_nfkc(neutralise(S)) if neutralise else S
    if S == D:
        stats[0] += 1
        r = runmap.redact(nS, mapping=mapping, _cache=cache); return r.text, r.mapping, nS, nS
    nD = runmap.fits_after_nfkc(neutralise(D)) if neutralise else D
    stats[0] += 2
    found = runmap.redact(nD, mapping=mapping, _cache=cache)
    held = sorted({p for p in GENUINE.findall(found.text) if p in found.mapping}, key=lambda p: -len(found.mapping[p]))
    if not held:
        r = runmap.redact(nS, mapping=mapping, _cache=cache); return r.text, r.mapping, nD, nS
    if len(held) > MAXV: return found.text, found.mapping, nD, nS
    masked = nS
    for p in held:
        masked = _spaced(found.mapping[p]).sub(lambda m, p=p: p, masked)
    r = runmap.redact(masked, mapping=found.mapping, _cache=cache)
    if any(p not in r.text for p in held): return found.text, found.mapping, nD, nS
    return r.text, r.mapping, nD, nS
STATS = [0]
def redact_text(text, mapping, neutralise=None):
    runmap._within_cap(text); started = time.monotonic()
    try:
        text = runmap.fits_after_nfkc(text.encode('utf-8', 'replace').decode('utf-8', 'replace'))
        cache = getattr(mapping, "redact_cache", None)
        out, current, nD, nS = _both(text, mapping, neutralise, cache, STATS)
        views = []
        raw = text if neutralise is None else runmap.fits_after_nfkc(neutralise(text))
        for base in dict.fromkeys((raw, nD)):
            if not base.isascii() or any(c in base for c in "\\%&"):
                views += [v for v in runmap._views(base) if v not in views and v not in (nS, nD)]
        pairs = []
        if views:
            for base in dict.fromkeys((nS, nD)):
                pairs += [x for x in runmap._decoded_masks(current, base) if x not in pairs]
        if neutralise is not None:
            pairs += [(ph, n) for ph, d in pairs if (n := runmap.fits_after_nfkc(neutralise(d))) != d and len(n) >= 4]
        pairs += [(ph, sd) for ph, d in pairs if (sd := strip(d)[0]) != d and len(sd) >= 4]
        for view in views:
            if time.monotonic() - started > defaults.REDACT_BUDGET_S: raise runmap.InputTooLarge("InputTooLarge")
            vt, vm = _both_view(view, current, neutralise, cache, pairs, set(mapping))
            if vm != current or runmap._held(vt) > runmap._held(out): out, current = vt, vm
        out = runmap._clean(out)
        if neutralise is runmap.neutralise_untrusted: _last_check(out, current)
    except (runmap.InputTooLarge, runmap.TooDeep): raise
    except Exception as exc: raise runmap.RedactionError(type(exc).__name__) from None
    before = set(mapping)
    if PRUNE: current = {p: v for p, v in current.items() if p in before or p in out}
    mapping.clear(); mapping.update(current); return out
def _both_view(view, mapping, neutralise, cache, pairs, before=()):
    held = sorted((p for p in mapping if p not in before), key=lambda p: -len(mapping[p]))[:MAXV]
    def neut(t):
        t = runmap.fits_after_nfkc(neutralise(t)) if neutralise else t
        t = runmap._keep_earlier_masks(t, pairs)
        return t
    return _both(view, mapping, neut, cache, STATS)[:2]
GENUINE = re.compile(r"<[A-Z][A-Z0-9]*_\d+>")
def _last_check(out, mapping):
    for t in (out, canonical(out)):
        if runmap._MARKER.search(t) or any(p not in mapping for p in GENUINE.findall(t)):
            raise RuntimeError("forgery")
_old_views = runmap._views
def install():
    runmap.canonical = canonical; runmap._canonical_view = _canonical_view; runmap.redact_text = redact_text
    R._Redactor.find = lambda self, text: _find(self, text)
    tools._sanitise = lambda t: strip_tool(t)
    _dec = tools._decoded
    tools._decoded = lambda t: strip(_dec(t))[0]
    _scrub = tools._scrub
    def scrub(raw, long_enough, sc=tools._DEFAULT_SCRUB):
        D = strip(raw)[0]
        s = _scrub(D, long_enough, sc)
        return raw if s == D else s
    tools._scrub = scrub
def _find(self, text):
    out = text
    for label, pattern in R.PATTERNS:
        out = pattern.sub(lambda m, label=label: self._mask(m, label), out)
    return out
def strip_tool(t):
    return t.encode("utf-8", "replace").decode("utf-8")
if __name__ == "__main__":
    try:
        p = subprocess.run(["perl", "-e", 'for my $c (0..0x10FFFF){ next if $c>=0xD800 && $c<=0xDFFF; print "$c\n" if chr($c) =~ /\\p{Default_Ignorable_Code_Point}/ }'], capture_output=True, text=True, timeout=120)
        perl = {int(x) for x in p.stdout.split()}
        print("Default_Ignorable: formula from memory", len(DI), "code points; perl 5.38 (Unicode 15.0.0) table", len(perl), "; only in formula", sorted(hex(x) for x in DI - perl)[:8], "; only in perl", sorted(hex(x) for x in perl - DI)[:8])
    except Exception as e: print("perl check failed", type(e).__name__)
