"""P10: link property over all 2,000 TXT-A texts (with and without backtick). usage: PYTHONPATH=<tree>/src python p10_links.py"""
import sys
sys.argv = ["x", "A"]
src = open("p10_props.py").read().split("which = ")[0]
exec(src)
xs = gen("TXT-A", A, 2000)
bt = [x for x in xs if "`" in x]
fails = [x for x in xs if links(channel.clean(x))]
print("texts", len(xs), "with backtick", len(bt), "link failures", len(fails), "of which with backtick", sum("`" in x for x in fails))
idem = [x for x in xs if gate.defang_text(gate.defang_text(x)) != gate.defang_text(x)]
print("defang_text idempotence failures", len(idem))
for x in sorted(fails, key=len)[:4]:
    print(repr(x), "->", repr(channel.clean(x)), links(channel.clean(x)))
print("x1", repr(gate.defang_text("x ` y\n` evil.com `")))
