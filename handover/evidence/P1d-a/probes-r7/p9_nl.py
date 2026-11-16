"""P9: what the 36 no-link failures contain. usage: PYTHONPATH=<tree>/src python p9_nl.py"""
import sys, collections
sys.argv = ["x", "Z"]
exec(open("p9_props.py").read().split("which = ")[0])
xs = gen("TXT-A", A, 2000)
cls = collections.Counter(); shown = 0
for x in xs:
    c = channel.clean(x); l = links(c)
    if not l: continue
    multi = "\n" in c
    # does the same text with every newline replaced by a space still fail?
    one = links(channel.clean(x.replace("\n", " ")))
    cls[("has newline" if multi else "single line", "fails when joined" if one else "ok when joined")] += 1
    if shown < 4 and len(c) < 160: shown += 1; print(repr(c), "->", l)
print(dict(cls))
