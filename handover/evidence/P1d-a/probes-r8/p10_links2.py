"""P10: link property, final form: in markdown-it's text tokens (outside code) of the final card, gate._defang_prose(token) == token.
usage: PYTHONPATH=<tree>/src python p10_links2.py"""
import sys
sys.argv = ["x", "A"]
exec(open("p10_props.py").read().split("which = ")[0])
def bad(c):
    out = []
    for t in gate._MD.parse(c):
        for ch in (t.children or []):
            if ch.type == "text" and gate._defang_prose(ch.content) != ch.content:
                out.append(ch.content)
    return out
xs = gen("TXT-A", A, 2000)
f = [x for x in xs if bad(channel.clean(x))]
print("link failures (defang_prose fixed point)", len(f), "with backtick", sum("`" in x for x in f), "no backtick", sum("`" not in x for x in f))
for x in f[:5]: print(repr(bad(channel.clean(x)))[:200])
