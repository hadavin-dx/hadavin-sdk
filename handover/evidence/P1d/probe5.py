import sys; sys.path.insert(0, sys.argv[1])
from hadavin_sdk.guard import runmap
from hadavin_sdk import tools
K = "AKIA" + "IOSFODNN7" + "EXAMPLE"
H = "hs-" + "q7Zp" + "Lm3Xv9" + "Rt2Kw8Yn"   # a handed-out secret, from parts
splits = {"md": f"{K[:4]}**{K[4:]}**", "ansi": f"{K[:4]}\x1b[0m{K[4:]}", "bs": f"x\x08{K}", "comb": f"{K[:4]}́{K[4:]}",
          "cyr": "АKIА" + K[4:], "lower": K.lower(), "split": f"{K[:10]}\n{K[10:]}", "dot": f"{K[:4]}.{K[4:]}"}
hsplits = {"plain": H, "md": f"{H[:6]}**{H[6:]}**", "ansi": f"{H[:6]}\x1b[0m{H[6:]}", "upper": H.upper(), "split": f"{H[:9]}\n{H[9:]}",
           "ent": f"{H[:6]}&#8203;{H[6:]}", "cyr": H.replace("p", "р")}
def show(o): 
    flat = "".join(c for c in o if c.isalnum()).upper()
    return ("LEAK " if K in flat or H.replace("-","").upper() in flat else "ok   ") + repr(o)[:70]
prods = {
 "redact_untrusted(doc)": lambda t: runmap.redact_untrusted(t, runmap.RunMap({})),
 "safe_head": lambda t: runmap.safe_head(t, 200),
 "redact_value(dict)": lambda t: repr(runmap.redact_value({"k": t}, runmap.RunMap({}))),
 "prepare_output": lambda t: tools.prepare_output(t, runmap.RunMap({}), 4000),
 "error_reason": lambda t: tools.error_reason(ValueError(t)),
}
for pn, f in prods.items():
    for n, s in splits.items():
        try: o = f(f"v {s} w")
        except Exception as e: o = "RAISE " + type(e).__name__
        print(f"{pn:22} {n:6} {show(o) if not o.startswith('RAISE') else o}")
for n, s in hsplits.items():
    o = tools.prepare_output(f"v {s} w", runmap.RunMap({}), 4000, secrets=[H]); print(f"{'prepare_output+handed':22} {n:6} {show(o)}")
    o = tools.error_reason(ValueError(f"v {s} w"), secrets=[H]); print(f"{'error_reason+handed':22} {n:6} {show(o)}")
