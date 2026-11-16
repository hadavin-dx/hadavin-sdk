"""P9: no-link property with the oracle read per line (Slack code spans do not cross a line). usage: PYTHONPATH=<tree>/src python p9_nl2.py"""
import sys, collections
sys.argv = ["x", "Z"]
exec(open("p9_props.py").read().split("which = ")[0])
xs = gen("TXT-A", A, 2000)
whole = per_line = nobt = 0; ex = []
for x in xs:
    c = channel.clean(x)
    if "`" in x: nobt += 1
    if links(c): whole += 1
    bad = [ln for ln in c.split("\n") if links(ln)]
    if bad:
        per_line += 1; ex.append(bad[0])
print("texts", len(xs), "with a backtick", nobt, "fail whole-text oracle", whole, "fail per-line oracle", per_line)
for e in sorted(ex, key=len)[:6]: print(repr(e), "->", links(e))
print("--- which regex matches (per-line failures)")
cnt = collections.Counter()
for x in xs:
    for ln in channel.clean(x).split("\n"):
        for t in gate._MD.parse(ln):
            for ch in (t.children or []):
                if ch.type != "text": continue
                for nm, rx in (("_DOMAIN", gate._DOMAIN), ("_NON_ASCII_HOST", gate._NON_ASCII_HOST), ("_PLACEHOLDER_DOT", gate._PLACEHOLDER_DOT), ("_WIDE_DOTS", gate._WIDE_DOTS)):
                    m = rx.search(ch.content)
                    if m: cnt[nm] += 1; print(nm, repr(m.group(0)), "in", repr(ch.content[max(0,m.start()-12):m.end()+8]))
print(dict(cnt))
