"""ERRATA rev 2 design changes, applied on top of the author prototype (throwaway, never committed).
fix790: earlier-mask spellings applied longest first. M1: count only values that need the gap; over 256 -> InputTooLarge;
values under 4 characters only as a whole word. M2: one more decoded reading = undo with the joined reading taken at the end
of every round. M5: removing hidden items never creates a placeholder or marker shape. FD: _first_decoded reads unstripped."""
import re, html
from urllib.parse import unquote
import prh_proto as proto
from hadavin_sdk.guard import runmap
from hadavin_sdk import tools, defaults
import fix790

def _both(text, mapping, neutralise, cache, stats):
    D, S = proto.strip(text)
    nS = runmap.fits_after_nfkc(neutralise(S)) if neutralise else S
    if S == D:
        stats[0] += 1
        r = runmap.redact(nS, mapping=mapping, _cache=cache); return r.text, r.mapping, nS, nS
    nD = runmap.fits_after_nfkc(neutralise(D)) if neutralise else D
    stats[0] += 2
    found = runmap.redact(nD, mapping=mapping, _cache=cache)
    held = [p for p in proto.GENUINE.findall(found.text) if p in found.mapping]
    need = sorted({p for p in held if found.mapping[p] not in nS and not found.mapping[p].startswith("\0seed")}, key=lambda p: -len(found.mapping[p]))
    if not need:
        r = runmap.redact(nS, mapping=found.mapping, _cache=cache)
        if any(p not in r.text for p in set(held)): return found.text, found.mapping, nD, nS
        return r.text, r.mapping, nD, nS
    if len(need) > runmap.MAX_DECODED_MASKS: raise runmap.InputTooLarge("InputTooLarge")
    masked = nS
    for p in need:
        val = found.mapping[p]
        pat = proto.GAP.join(re.escape(c) for c in val)
        if len(val) < 4: pat = r"(?<!\w)" + pat + r"(?!\w)"
        masked = re.sub(pat, lambda m, p=p: p, masked)
    r = runmap.redact(masked, mapping=found.mapping, _cache=cache)
    if any(p not in r.text for p in set(held)): return found.text, found.mapping, nD, nS
    return r.text, r.mapping, nD, nS

def undo_joined(text):
    cur = text
    for _ in range(defaults.SCRUB_MAX_LAYERS + 1):
        step = cur
        for decode in (runmap.nfkc, runmap.json_unescape, runmap.hex_unescape, unquote, html.unescape):
            step = decode(step)
        step = _created(step, _orig_strip(step)[0])
        if step == cur: return cur
        cur = step
    raise runmap.TooDeep("TooDeep")

_orig_strip = proto.strip
_orig_views = runmap._views
def views(text):
    out = _orig_views(text)
    if any(c in text for c in "\\%&"):
        v = runmap._clean(runmap.fits_after_nfkc(undo_joined(text)))
        if v != text and v not in out: out.append(v)
    return out

def _created(raw, red):
    if red == raw: return red  # nothing removed: nothing can be created (and no extra NFKC of the whole text)
    for m in sorted(set(runmap.PLACEHOLDER.findall(red) and [x.group(0) for x in runmap.PLACEHOLDER.finditer(red)])):
        if red.count(m) > raw.count(m):
            red = red.replace(m, "‹" + m[1:-1] + "›")
    if len(runmap._MARKER.findall(runmap.canonical(runmap.fits_after_nfkc(red)))) > len(runmap._MARKER.findall(runmap.canonical(runmap.fits_after_nfkc(raw)))):
        red = runmap.escape_markers(red)
    return red
def strip(text):
    D, S = _orig_strip(text)
    if D is S or D == S:
        D2 = _created(text, D); return D2, D2
    return _created(text, D), _created(text, S)

def install(m2=True, m5=True):
    fix790.install()
    proto._both = _both
    if m5: proto.strip = strip
    if m2:
        runmap._views = views
        _dec = tools._decoded
        tools._decoded = lambda t: _orig_strip(undo_joined(t))[0]
    tools._first_decoded = __import__("functools").lru_cache(maxsize=4096)(lambda ch: (lambda: runmap.undo(ch)[:1])() if True else ch)
