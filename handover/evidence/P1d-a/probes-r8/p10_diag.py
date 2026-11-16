"""P10: which regex matches in each remaining link failure. usage: PYTHONPATH=<tree>/src python p10_diag.py"""
import sys
sys.argv = ["x", "A"]
exec(open("p10_props.py").read().split("which = ")[0])
xs = gen("TXT-A", A, 2000)
for x in xs:
    c = channel.clean(x)
    for t in gate._MD.parse(c):
        for ch in (t.children or []):
            if ch.type == "text":
                hit = [n for n, r in (("DOMAIN", gate._DOMAIN), ("NONASCII", gate._NON_ASCII_HOST), ("PHDOT", gate._PLACEHOLDER_DOT), ("WIDE", gate._WIDE_DOTS)) if r.search(ch.content)]
                if hit:
                    print(hit, repr(ch.content)[:150], "| code spans real:", [cc.content[:30] for cc in t.children if cc.type == "code_inline"][:3])
