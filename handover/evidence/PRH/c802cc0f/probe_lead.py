"""EVIDENCE RUNNER lead-added probes F1-F3. Made-up values built from parts. Records only."""
import html, json, urllib.parse
from hadavin_sdk import tools
from hadavin_sdk.guard import runmap
ESC = "\x1b"
print("tree", tools.__file__)
def paths(t, hand):
    return {"tool": lambda: tools.prepare_output(t, {}, 4000, [hand]),
            "error": lambda: tools.error_reason(ValueError(t), [hand]),
            "choke(redact_untrusted,no list)": lambda: runmap.redact_untrusted(t, {}),
            "head(safe_head,no list)": lambda: runmap.safe_head(t, 4000, {})}
def decodes(o):
    d = {"unquote": urllib.parse.unquote(o), "html": html.unescape(o)}
    try: d["json"] = json.loads('"' + o.replace('"', '\\"') + '"')
    except Exception: pass
    return d
def f1(hand):
    first = hand[0]; rest = hand[1:]
    pct = lambda c: "%%%02x" % ord(c)
    ent = lambda c: "&#%d;" % ord(c)
    sp = {
     "pct": "x %1b" + pct(first) + rest.replace("-", "%2d") + " y",
     "json-escape-text": "x \\u001b" + hand + " y",
     "entity": "x &#27;" + ent(first) + rest.replace("-", "&#45;") + " y",
     "raw ESC (control)": "x " + ESC + hand + " y",
     "plain": "x " + hand + " y",
    }
    for sn, t in sp.items():
        for pn, f in paths(t, hand).items():
            try: o = f()
            except Exception as e: print(f"F1 {hand[:3]}.. | {sn} | {pn} | EXC {type(e).__name__}"); continue
            dec = {k: (hand in v or rest in v) for k, v in decodes(o).items()}
            print(f"F1 hand={hand[:2]}.. | {sn} | {pn} | HAND={'Y' if hand in o else 'n'} HAND[1:]={'Y' if rest in o else 'n'} dec={ {k:('Y' if v else 'n') for k,v in dec.items()} } | out={o!r}")
f1("Tr" + "0ub4dor-3xyzQ")
f1("tr" + "0ub4dor-3xyzQ")
# F2
H2 = "Prod" + "Company" + "2024!"
t2 = ESC + "[31m" + "err " + H2 + " ok " + tools.MARKER + " word Company elsewhere" + ESC + "[0m"
t2b = ESC + "[31m" + "err " + H2 + " word Company elsewhere" + ESC + "[0m"
for nm, t in [("F2 colour+secret+masked copy+Company", t2), ("F2b colour+secret+Company (no masked copy)", t2b)]:
    for pn, f in paths(t, H2).items():
        o = f(); print(nm, "|", pn, "| whole=MARKER+TRUNCATED:", o == tools.MARKER + tools.TRUNCATED, "| H2 shown:", H2 in o, "| out=", repr(o))
# F3
S3 = "SECRET" + "_ab12cd"
rows = {"F3a ESC[0m": "x " + S3 + " y " + ESC + "[0m z", "F3b ZW cut": "x " + S3[:4] + "​" + S3[4:] + " y", "F3c ESC prefix": "x " + ESC + S3 + " y", "F3d bidi + plain": "x " + S3 + " y‮ z", "F3e no hidden item": "x " + S3 + " y"}
for nm, t in rows.items():
    for pn, f in paths(t, S3).items():
        o = f(); print(nm, "|", pn, "| S3 shown:", S3 in o, "| tail shown:", S3[1:] in o, "| out=", repr(o))
