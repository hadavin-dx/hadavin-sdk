"""EVIDENCE for Q8a-1 b8 (builder's own): every configured path unreadable in six ways, plus realistic secret shapes
typed where an id belongs. Marker built from parts. Run as an unprivileged user:  python probe_b8.py"""
import os, sys, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe_old as P
from probe_old import MARK, run, edit_yaml, fmt, fresh, load_config, load_registry, WT
from pathlib import Path

def setcfg(fn):
    def m(root):
        p = root / "config.yaml"
        import yaml
        d = yaml.safe_load(p.read_text()); fn(d); p.write_text(yaml.safe_dump(d))
    return m

def agent(fn):
    return edit_yaml("agents.yaml", lambda d: (fn(d[0]), d)[1])

VARIANTS = {
    "missing": MARK + "-missing",
    "over-long": "n" * 300 + MARK,
    "null byte": MARK + "\x00",
    "loop": None,       # made per run
    "folder": None,
}

def path_variants(setter, label):
    rows = []
    for vname, val in VARIANTS.items():
        def mutate(root, vname=vname, val=val):
            if vname == "loop":
                (root / "loop").symlink_to("loop"); v = "loop"
            elif vname == "folder":
                (root / "folder-d").mkdir(); v = "folder-d"
            else:
                v = val
            setter(v)(root)
        rows.append((f"PATH {label} = {vname}", mutate))
    return rows

rows = []
rows += path_variants(lambda v: agent(lambda a: a.__setitem__("prompt_file", v)), "agents.yaml prompt_file")
rows += path_variants(lambda v: setcfg(lambda d: d.__setitem__("golden_dir", v)), "config golden_dir")
rows += path_variants(lambda v: setcfg(lambda d: d.__setitem__("inputs_dir", v)), "config inputs_dir")
rows += path_variants(lambda v: setcfg(lambda d: d["backends"]["llm"].__setitem__("recorded_dir", v)), "config llm.recorded_dir")
rows += path_variants(lambda v: setcfg(lambda d: d["backends"].__setitem__("audit", {"kind": "local_dir", "dir": v})), "config audit.dir")
rows += path_variants(lambda v: setcfg(lambda d: d.__setitem__("sources", {"k8s": {"kind": "kubernetes", "ca_file": v, "settings": {"api_url": "https://k8s.example", "namespaces": ["ns"]}}})), "config sources.k8s.ca_file")
for name in ("config.yaml", "egress.yaml", "agents.yaml", "principals.yaml", "chains.yaml"):
    def mutate(root, name=name):
        p = root / name
        if p.exists(): p.unlink()
        p.symlink_to(name)
    rows.append((f"UNREADABLE {name} is a loop of links", mutate))
def actions_dir_is_file(root):
    shutil.rmtree(root / "actions"); (root / "actions").write_text(MARK)
rows.append(("UNREADABLE actions/ is a file", actions_dir_is_file))
def tools_manifest_folder(root):
    (root / "tools").mkdir(exist_ok=True); (root / "tools" / "test-agent.yaml").mkdir()
rows.append(("UNREADABLE tools/test-agent.yaml is a folder", tools_manifest_folder))

# realistic secret shapes typed as ids (D-2322: long, hex-like or digit-run texts are not shown)
SHAPES = {"hex32": "t" + "0123456789abcdef" * 2, "hex64": "k" + "9f" * 32, "long-token": "tok-" + "abcdefghij" * 5,
          "digit-run": "key" + "7" * 24, "forty-one": "w" * 41, "sk-style": "sk-" + "a1b2c3d4" * 4}
for sn, sv in SHAPES.items():
    P.MARK = sv  # the marker for these rows
    rows.append((f"SHAPE {sn} agent id + unknown scope", agent(lambda a, sv=sv: (a.__setitem__("id", sv), a.__setitem__("scope_allowed", ["nope_action"])))))
    rows.append((f"SHAPE {sn} principal id + unknown right", edit_yaml("principals.yaml", lambda d, sv=sv: (d[0].__setitem__("id", sv), d[0].__setitem__("rights", ["nope_right"]), d)[2])))
    rows.append((f"SHAPE {sn} action id + bad chain", edit_yaml("actions/lookup_record.yaml", lambda d, sv=sv: (d.__setitem__("id", sv), d.__setitem__("chain_id", "nope_chain"), d)[2])))
    rows.append((f"SHAPE {sn} chain id + unknown approver", edit_yaml("chains.yaml", lambda d, sv=sv: (d[0].__setitem__("id", sv), d[0]["steps"][0].__setitem__("approver_ids", ["nope_p"]), d)[2])))

import re
lines, readable, results = [], 0, 0
for label, mutate in rows:
    mk = MARK
    if label.startswith("SHAPE"):
        mk = SHAPES[label.split()[1]]
    P.MARK = mk
    r = run(label, mutate)
    for k, v in r.items():
        if not isinstance(v, dict):
            continue
        results += 1
        full = "\n".join([v["str"], v["repr"]] + v["chain"]) + "".join(v["marker_lines"])
        vis = v["marker_in_str"] + v["marker_in_repr"] + v["marker_in_full_traceback"]
        shown_path = (str(WT) in v["str"]) or (str(WT) in "\n".join(v["marker_lines"]))
        flag = "LEAK-READABLE" if (vis or shown_path) else "clean"
        if vis or shown_path: readable += 1
        lines.append(f"{flag} | {label} | {k} | {v['type']} | marker(str/repr/traceback)={v['marker_in_str']}/{v['marker_in_repr']}/{v['marker_in_full_traceback']} suppress={v['suppress_context']} | {v['str'][:140]!r}")
    for k, v in r.items():
        if not isinstance(v, dict) and k != "label":
            lines.append(f"ok-no-error | {label} | {k} | {v}")
print("\n".join(lines))
print(f"\nTOTAL rows={len(rows)} error-results={results} readable={readable}")
