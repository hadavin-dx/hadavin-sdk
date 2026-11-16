import json, time, unicodedata, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ZW = dict.fromkeys(map(ord, "​‌‍⁠﻿"))
def fold(s): return unicodedata.normalize("NFKC", s).translate(ZW)
def classify(out, values):
    of = fold(out); st = []
    for v in values:
        vf = fold(v)
        if v in out or vf in of: st.append("MISS"); continue
        n = min(len(vf), 5)
        part = any(vf[i:i+n] in of for i in range(len(vf)-n+1)) if len(vf) > 0 else False
        st.append("PARTIAL" if part else "FULL")
    if all(s == "FULL" for s in st): return "FULL"
    if all(s == "MISS" for s in st): return "MISS"
    return "PARTIAL"
def run_tool(name, init, fn, meta=None):
    """init() -> state ; fn(state, text) -> (output_text, [entity labels])"""
    c = json.load(open(os.path.join(HERE, "corpus.json"), encoding="utf-8"))
    t0 = time.perf_counter(); st = init(); t_start = time.perf_counter() - t0
    res = {"tool": name, "meta": meta or {}, "start_s": round(t_start, 2), "hostile": [], "mustmask": [], "mustkeep": []}
    t1 = time.perf_counter(); n = 0
    for grp in ("hostile", "mustmask"):
        for it in c[grp]:
            try: out, ents = fn(st, it["text"]); err = None
            except Exception as e: out, ents, err = it["text"], [], repr(e)[:200]
            n += 1
            r = {"cls": it["cls"], "input": it["text"], "values": it["values"], "output": out, "entities": ents, "verdict": classify(out, it["values"])}
            if err: r["error"] = err
            res[grp].append(r)
    for it in c["mustkeep"]:
        try: out, ents = fn(st, it["text"]); err = None
        except Exception as e: out, ents, err = it["text"], [], repr(e)[:200]
        n += 1
        r = {"input": it["text"], "output": out, "entities": ents, "verdict": "KEPT" if out == it["text"] else "ALTERED"}
        if err: r["error"] = err
        res["mustkeep"].append(r)
    el = time.perf_counter() - t1
    res["lines"] = n; res["per100_s"] = round(el * 100 / n, 3)
    cnt = lambda g, vs: {v: sum(1 for r in res[g] if r["verdict"] == v) for v in vs}
    res["counts"] = {"hostile": cnt("hostile", ["FULL", "PARTIAL", "MISS"]), "mustmask": cnt("mustmask", ["FULL", "PARTIAL", "MISS"]), "mustkeep": cnt("mustkeep", ["KEPT", "ALTERED"])}
    p = os.path.join(HERE, "out_" + name + ".json")
    json.dump(res, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(name, res["counts"], "start", res["start_s"], "per100", res["per100_s"], "errors", sum(1 for g in ("hostile","mustmask","mustkeep") for r in res[g] if "error" in r))
def spans_mask(text, spans, fmt=lambda lab: "<%s>"):
    """spans: [(start,end,label)] -> masked text (non-overlapping merge)"""
    spans = sorted(spans); out = []; pos = 0
    for s, e, lab in spans:
        if s < pos: 
            if e > pos: out.pop() if False else None
            continue
        out.append(text[pos:s]); out.append("<%s>" % lab); pos = e
    out.append(text[pos:]); return "".join(out)
