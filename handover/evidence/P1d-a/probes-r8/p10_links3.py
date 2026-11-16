"""P10: link property on ALL 2,000 TXT-A texts. A text token outside code of markdown-it's tokens of clean(x) fails when a match of
_DOMAIN, _NON_ASCII_HOST, _PLACEHOLDER_DOT or _WIDE_DOTS neither starts at the token's first character nor ends at its last (a token
cut at `_` or `*` has unknown context there). usage: PYTHONPATH=<tree>/src python p10_links3.py"""
from markdown_it import MarkdownIt
_FULL = MarkdownIt("commonmark")
import sys
sys.argv = ["x", "A"]
exec(open("p10_props.py").read().split("which = ")[0])
def bad(c):
    out = []
    for t in _FULL.parse(c):
        for ch in (t.children or []):
            if ch.type != "text":
                continue
            s = ch.content
            for r in (gate._DOMAIN, gate._NON_ASCII_HOST, gate._PLACEHOLDER_DOT, gate._WIDE_DOTS):
                for m in r.finditer(s):
                    if m.start() > 0 and m.end() < len(s):
                        out.append(s)
    return out
xs = gen("TXT-A", A, 2000)
f = [x for x in xs if bad(channel.clean(x))]
print("failures", len(f), "with backtick", sum("`" in x for x in f), "no backtick", sum("`" not in x for x in f), "texts with backtick", sum("`" in x for x in xs))
for x in f[:3]: print(repr(bad(channel.clean(x)))[:200])
