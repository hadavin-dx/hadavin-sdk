import re, ast, os, sys, textwrap
A = "/home/user/hadavin-sdk/handover/core-hardening/audit-r460/"
main = open(A + "CORE-PR-HANDOFF-v11.md", encoding="utf-8").read().split("\n")
oth = open(A + "CORE-PR-HANDOFF-v11-other-tracks.md", encoding="utf-8").read().split("\n")
def table_ids(lines, start_pat, end_pat):
    on = False; ids = []
    for l in lines:
        if re.match(start_pat, l): on = True; continue
        if on and re.match(end_pat, l): break
        if on and l.startswith("|"):
            c = [x.strip() for x in l.strip("|").split("|")]
            if len(c) > 2 and not c[0].startswith(("Order", "---", ":--")): ids.append((c[0], c[1]))
    return ids
mi = table_ids(main, r"^### 7\.1", r"^### 7\.2")
oi = table_ids(oth, r"^## O-6", r"^## O-7")
print("== main file 7.1 PR table rows (order, pr):"); [print("  ", r) for r in mi]
print("== other-tracks O-6 PR table rows (order, pr):"); [print("  ", r) for r in oi]
nm = [p for o, p in mi if re.match(r"\*\*[A-Z]", p) or re.match(r"[A-Z]", p)]
no = [p for o, p in oi if not p.startswith("all")]
print("main 7.1 distinct PR ids with a numbered/aliased order:", [p.strip("*") for o, p in mi if o != "later"], "count=", len([1 for o, p in mi if o != "later"]), "(+ 'later' row L-1..L-7)")
print("other-tracks distinct PR ids:", [p for p in no if not p.startswith('gate')], "count=", len([p for p in no if p != 'gate']))
print("== statements with seven / nine (word, line):")
for name, ls in (("main", main), ("other", oth)):
    for i, l in enumerate(ls, 1):
        for m in re.finditer(r"\b(?i:seven|nine)\b", l):
            print("  %s:%d ...%s..." % (name, i, l[max(0, m.start()-70):m.end()+70]))
print("== python fences")
bad = 0; tot = 0
for name, ls in (("main", main), ("other", oth)):
    txt = "\n".join(ls)
    for m in re.finditer(r"```(\w*)[^\n]*\n(.*?)```", txt, re.S):
        lang = m.group(1).lower(); body = m.group(2)
        ln = txt[:m.start()].count("\n") + 1
        if lang in ("python", "py"):
            tot += 1
            try: ast.parse(textwrap.dedent(body)); print("  %s:%d python fence OK (%d lines)" % (name, ln, body.count("\n")))
            except SyntaxError as e: bad += 1; print("  %s:%d python fence SYNTAX ERROR line %s: %s" % (name, ln, e.lineno, e.msg))
        else: print("  %s:%d fence lang=%r (not python, skipped)" % (name, ln, lang))
print("python fences:", tot, "errors:", bad)
