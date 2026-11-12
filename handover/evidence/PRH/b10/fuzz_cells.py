"""EVIDENCE for PR H batch 10: the own fuzz of batch 9 (handover/evidence/PRH/f01a9f8f/own_fuzz_b9.py, same generator) with one
line per text: cell name, whether an 8-character stretch of the planted secret is readable, whether the output is withheld, the error
type if any, and a short hash of the text. NO readable value is printed. Usage: python fuzz_cells.py <tree-root> <out.jsonl>"""
import hashlib, importlib.util, json, sys
tree, outp = sys.argv[1], sys.argv[2]
src = open("/home/user/hadavin-sdk/handover/evidence/PRH/f01a9f8f/own_fuzz_b9.py").read()
src = src.replace("sys.path.insert(0, sys.argv[1] + \"/src\")", "sys.path.insert(0, %r + \"/src\")" % tree)
head, _, _ = src.partition("def main():")
ns = {"__name__": "fuzzgen"}
sys.argv = [sys.argv[0], tree]
exec(compile(head, "own_fuzz_b9_gen", "exec"), ns)
tools, runmap = ns["tools"], ns["runmap"]
rows = []
for name, s, t in ns["cases"]():
    cat = name.split("/")[0]
    err = ""
    try:
        o = tools.prepare_output(t, {}, 4000, [ns["HAND"], ns["LONG"]])
    except runmap.RedactionError as e:
        err, o = type(e).__name__, ""
    except Exception as e:  # noqa
        err, o = "OTHER:" + type(e).__name__, ""
    w = []
    if err == "" and (s or name.startswith("runcap/")):
        p = name.split("/")
        if p[0] == "runcap": w = []
        elif p[0] in ("spaced", "spaced_esc"): w = ns["spaced_windows"](s, o, ns["SEPS"][p[2]])
        elif p[0] == "spaced_unknown": w = ns["spaced_windows"](s, o, " ")
        else: w = ns["windows"](s, o)
    wh = err == "" and (o.replace(tools.MARKER, "").replace(tools.TRUNCATED, "").strip() == "" or "withheld" in o)
    rows.append({"cell": name, "readable": bool(w), "withheld": bool(wh), "err": err, "h": hashlib.sha256(t.encode()).hexdigest()[:12]})
with open(outp, "w") as f:
    for r in rows: f.write(json.dumps(r) + "\n")
print(tree, "texts", len(rows), "readable", sum(r["readable"] for r in rows), "withheld", sum(r["withheld"] for r in rows), "errors", sum(1 for r in rows if r["err"]))
