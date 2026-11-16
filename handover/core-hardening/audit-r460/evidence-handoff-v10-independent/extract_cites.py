#!/usr/bin/env python3
"""Independent citation extractor (written fresh for the v10 independent audit).
Reads the two v10 hand-off files, finds every file:line / file:a-b citation (including
bare ':N' continuations and 'file N-M' prose form), resolves the file against the real tree
(read only) and writes cites.json. Does not look at evidence-handoff-v10/."""
import json, os, re, sys

ROOT = "/home/user/hadavin-sdk"
AUD = ROOT + "/handover/core-hardening/audit-r460/"
DOCS = ["CORE-PR-HANDOFF-v10.md", "CORE-PR-HANDOFF-v10-other-tracks.md"]

# index of every real file by basename and by relative path
byname = {}
allfiles = set()
for base in ("src", "tests", "demos", ".github", "docs"):
    for d, _, fs in os.walk(os.path.join(ROOT, base)):
        if "__pycache__" in d:
            continue
        for f in fs:
            rel = os.path.relpath(os.path.join(d, f), ROOT)
            allfiles.add(rel)
            byname.setdefault(f, []).append(rel)
for f in os.listdir(ROOT):
    if os.path.isfile(os.path.join(ROOT, f)):
        allfiles.add(f)
        byname.setdefault(f, []).append(f)

PREFIXES = ["", "src/hadavin_sdk/", "tests/", "demos/", "demos/ask-your-data/askdata/",
            "demos/ask-your-data/", ".github/workflows/", "src/hadavin_sdk/llm/"]


def resolve(tok, hint_dirs):
    tok = tok.strip("`")
    for p in PREFIXES:
        if p + tok in allfiles:
            return p + tok, "exact"
    # suffix match
    suf = [f for f in allfiles if f.endswith("/" + tok)]
    suf = [f for f in suf if not f.startswith("handover")]
    if len(suf) == 1:
        return suf[0], "suffix"
    if len(suf) > 1:
        # prefer src
        s2 = [f for f in suf if f.startswith("src/")]
        for h in hint_dirs:
            hs = [f for f in suf if h in f]
            if len(hs) == 1:
                return hs[0], "hint"
        if len(s2) == 1:
            return s2[0], "src-pref"
        return None, "ambiguous:" + "|".join(suf)
    return None, "missing"


FILE = r"(?:[A-Za-z0-9_./-]+/)?[A-Za-z0-9_.-]+\.(?:py|sql|ya?ml|md|sh|json|toml)"
# `file:12-34`  or  file.py:12  (ranges or single, also ',:N' lists via continuation below)
TOK = re.compile(
    r"(?P<file>" + FILE + r")(?::(?P<a>\d+)(?:-(?P<b>\d+))?(?P<rest>(?:,\d+(?:-\d+)?)*))"
    r"|(?P<file2>" + FILE + r")`?\s+(?P<a2>\d+)-(?P<b2>\d+)\b"      # `file` 140-250
    r"|`:(?P<a3>\d+)(?:-(?P<b3>\d+))?`"                              # `:N` continuation
    r"|(?<![\w/.])(?:,|and|;|\s)\s*:(?P<a4>\d+)(?:-(?P<b4>\d+))?"  # ', :N'
)

out = []
for doc in DOCS:
    cur = None
    cur_hint = []
    for n, line in enumerate(open(AUD + doc, encoding="utf-8"), 1):
        for m in TOK.finditer(line):
            f = m.group("file") or m.group("file2")
            if f:
                cur = f
                if "/" in f:
                    cur_hint = [os.path.dirname(f)]
                a = m.group("a") or m.group("a2")
                b = m.group("b") or m.group("b2")
            else:
                a = m.group("a3") or m.group("a4")
                b = m.group("b3") or m.group("b4")
            if cur is None:
                continue
            res, how = resolve(cur, cur_hint)
            out.append(dict(doc=doc, line=n, token=cur, path=res, how=how, a=int(a),
                            b=int(b) if b else int(a), ctx=line.strip()[:160]))
            rest = m.groupdict().get("rest")
            for part in (rest or "").split(","):
                if part:
                    x, _, y = part.partition("-")
                    out.append(dict(doc=doc, line=n, token=cur, path=res, how=how + "+list", a=int(x),
                                    b=int(y) if y else int(x), ctx=line.strip()[:160]))
json.dump(out, open(os.path.dirname(os.path.abspath(__file__)) + "/cites.json", "w"), indent=0)
print("citations", len(out))
unres = [o for o in out if not o["path"]]
print("unresolved", len(unres))
for o in unres:
    print(o["doc"], o["line"], o["token"], o["how"], o["a"], o["b"])
