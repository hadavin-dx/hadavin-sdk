"""Parse every fenced block tagged python in the given markdown files with ast. usage: python -I snippet_check_v9.py <doc>..."""
import ast, re, sys
n = bad = 0
for doc in sys.argv[1:]:
    txt = open(doc, encoding="utf-8").read()
    for m in re.finditer(r"```(\w*)\n(.*?)```", txt, re.S):
        lang, code = m.group(1), m.group(2)
        line = txt[: m.start()].count("\n") + 1
        if lang != "python":
            print("%s:%d fence tagged %r (not parsed)" % (doc, line, lang)); continue
        n += 1
        try:
            ast.parse(code); print("%s:%d python fence parses (%d lines)" % (doc, line, code.count("\n")))
        except SyntaxError as e:
            bad += 1; print("%s:%d SYNTAX ERROR %s" % (doc, line, e))
print("python fences=%d syntax_errors=%d" % (n, bad))
sys.exit(1 if bad else 0)
