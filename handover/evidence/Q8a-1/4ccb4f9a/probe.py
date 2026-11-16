"""EVIDENCE RUNNER probes for Q8a-1 (own script). Marker is built from parts; never printed raw except where it LEAKS."""
import copy, shutil, sys, tempfile, traceback, io, json
from pathlib import Path
import yaml

WT = Path("/home/user/build/EV-q8a1-4ccb4f9a/wt")
sys.path.insert(0, str(WT / "src")); sys.path.insert(0, str(WT))
from hadavin_sdk.config import load_config, ConfigError, config_error_text
from hadavin_sdk.registry import load_registry

MARK = "zq" + "-probe-" + "mk4417"   # made-up marker
FIX = WT / "tests" / "fixtures" / "config"

def fresh():
    d = Path(tempfile.mkdtemp(prefix="q8a1probe-")) 
    shutil.copytree(FIX, d / "config")
    for n in ("recorded", "inputs", "golden"):
        shutil.copytree(WT / "tests" / "fixtures" / n, d / n)
    cfg = d / "config" / "config.yaml"
    cfg.write_text(cfg.read_text().replace("{port}", "1"))
    return d / "config"

def run(label, mutate):
    root = fresh()
    mutate(root)
    out = {"label": label}
    try:
        cfg = load_config(root)
        out["load_config"] = "OK"
        try:
            load_registry(cfg)
            out["load_registry"] = "OK"
        except BaseException as e:
            out["load_registry"] = fmt(e)
    except BaseException as e:
        out["load_config"] = fmt(e)
        # still try registry with a clean config so registry-only files are probed
    if out.get("load_config") != "OK":
        # probe registry too: use clean config, only the registry files carry the mutation
        try:
            clean = fresh()
            # copy mutated non-config files over
            for p in root.rglob("*"):
                if p.is_file() and p.name != "config.yaml":
                    t = clean / p.relative_to(root)
                    t.parent.mkdir(parents=True, exist_ok=True)
                    t.write_bytes(p.read_bytes())
            cfg2 = load_config(clean)
            try:
                load_registry(cfg2); out["load_registry(clean config + mutated other files)"] = "OK"
            except BaseException as e:
                out["load_registry(clean config + mutated other files)"] = fmt(e)
        except BaseException as e:
            out["load_registry(clean config + mutated other files)"] = "n/a: clean config failed " + type(e).__name__
    shutil.rmtree(root.parent, ignore_errors=True)
    return out

def fmt(e):
    full = "".join(traceback.format_exception(e))
    s = str(e)
    chain = []
    x = e
    seen = 0
    while x is not None and seen < 10:
        chain.append(type(x).__name__ + ":" + str(x))
        x = x.__cause__ or x.__context__
        seen += 1
    return {"type": type(e).__name__, "str": s, "repr": repr(e), "chain": chain,
            "marker_in_str": s.count(MARK), "marker_in_repr": repr(e).count(MARK),
            "marker_in_chain": sum(c.count(MARK) for c in chain),
            "marker_in_full_traceback": full.count(MARK),
            "marker_lines": [l for l in full.splitlines() if MARK in l],
            "cause_present": e.__cause__ is not None, "context_present": e.__context__ is not None,
            "suppress_context": e.__suppress_context__}

def edit_yaml(name, fn):
    def m(root):
        p = root / name
        d = yaml.safe_load(p.read_text())
        d = fn(d)
        p.write_text(yaml.safe_dump(d))
    return m

def raw(name, text, append=True):
    def m(root):
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text((p.read_text() if (append and p.exists()) else "") + text)
    return m

# NFKC-folding characters
FW_AT, FW_COLON, FW_HASH, FW_SLASH, FW_Q = "＠", "：", "＃", "／", "？"
SM_AT, SM_COLON, SM_HASH, SM_Q = "﹫", "﹕", "﹟", "﹖"
A_C, C_O, FW_LB, FW_RB, FW_PCT = "℀", "℅", "［", "］", "％"
netlocs = {
 "fw@+fw:": f"user{FW_COLON}{MARK}{FW_AT}host.example",
 "fw@ only (login-less user)": f"{MARK}{FW_AT}host.example",
 "fw: port marker": f"host.example{FW_COLON}{MARK}",
 "fw: bad port 99999x": f"host.example{FW_COLON}99999999{MARK}",
 "fw# fragment": f"host.example{FW_HASH}{MARK}",
 "fw/ path": f"host.example{FW_SLASH}{MARK}",
 "fw? query": f"host.example{FW_Q}{MARK}",
 "small@ small:": f"user{SM_COLON}{MARK}{SM_AT}host.example",
 "a/c char (U+2100)": f"{MARK}{A_C}host.example",
 "c/o char (U+2105)": f"{MARK}{C_O}host.example",
 "fw brackets": f"{FW_LB}{MARK}{FW_RB}host.example",
 "ascii [ unbalanced": f"[{MARK}host.example",
 "ascii bracket bad ipv6": f"[{MARK}]",
 "ascii bad port": f"host.example:{MARK}",
 "ascii userinfo": f"user:{MARK}@host.example",
 "fw percent": f"host{FW_PCT}{MARK}.example",
}

probes = []
def sysset(netloc):
    def f(d):
        d["systems"]["fixture-records"]["base_url"] = f"https://{netloc}/x"; return d
    return f
def llmset(netloc):
    def f(d):
        d["backends"]["llm"] = {"kind": "openai_compat", "base_url": f"https://{netloc}/v1"}; return d
    return f
def vaultset(netloc):
    def f(d):
        d["backends"]["secrets"] = {"kind": "vault", "address": f"https://{netloc}"}; return d
    return f
for k, n in netlocs.items():
    probes.append((f"systems.base_url | {k}", edit_yaml("config.yaml", sysset(n))))
    probes.append((f"openai_compat.base_url | {k}", edit_yaml("config.yaml", llmset(n))))
    probes.append((f"vault.address | {k}", edit_yaml("config.yaml", vaultset(n))))
# also http scheme + loopback-lookalike / other schemes with fullwidth
probes.append(("systems.base_url | scheme fw colon", edit_yaml("config.yaml", lambda d: (d["systems"]["fixture-records"].__setitem__("base_url", f"https{FW_COLON}//{MARK}{FW_AT}host.example/"), d)[1])))
probes.append(("openai_compat.base_url | no-scheme marker", edit_yaml("config.yaml", lambda d: (d["backends"].__setitem__("llm", {"kind":"openai_compat","base_url":MARK}), d)[1])))
probes.append(("vault.address | no-scheme marker", edit_yaml("config.yaml", lambda d: (d["backends"].__setitem__("secrets", {"kind":"vault","address":MARK}), d)[1])))

# broken YAML
bad = f"  - id: oops\n    key: [unclosed {MARK}\n    other: {{a: 1\n"
probes.append(("broken YAML tools/test-agent.yaml (marker on bad line)", raw("tools/test-agent.yaml", f"- name: x\n  function: [{MARK}\n  bad: : {MARK}\n", append=False)))
probes.append(("broken YAML tools/test-agent.yaml (tab + marker)", raw("tools/test-agent.yaml", f"- name: x\n\tfunction: {MARK}\n", append=False)))
probes.append(("broken YAML config.yaml (marker on bad line)", raw("config.yaml", f"\nbroken: [unclosed {MARK}\nx: {{a: {MARK}\n")))
probes.append(("broken YAML config.yaml (bad indent+marker)", raw("config.yaml", f"\n  stray: {MARK}\n bad: {MARK}\n")))
probes.append(("duplicate key config.yaml (marker)", raw("config.yaml", f"\nenvironment: {MARK}\n")))
probes.append(("broken YAML agents.yaml", raw("agents.yaml", f"\n- id: [{MARK}\n")))
probes.append(("broken YAML principals.yaml", raw("principals.yaml", f"\n- id: [{MARK}\n")))
probes.append(("broken YAML chains.yaml", raw("chains.yaml", f"\n- id: [{MARK}\n")))
probes.append(("broken YAML egress.yaml", raw("egress.yaml", f"\nhosts: [{MARK}\n")))
probes.append(("broken YAML actions/lookup_record.yaml", raw("actions/lookup_record.yaml", f"\nx: [{MARK}\n")))
probes.append(("YAML non-utf8 bytes + marker config.yaml", lambda root: (root/"config.yaml").write_bytes(MARK.encode()+b"\xff\xfe: 1\n")))
probes.append(("YAML non-utf8 bytes + marker tools/test-agent.yaml", lambda root: ((root/"tools").mkdir(exist_ok=True), (root/"tools"/"test-agent.yaml").write_bytes(MARK.encode()+b"\xff\xfe: 1\n"))))
probes.append(("YAML anchors/tags marker config.yaml", raw("config.yaml", f"\nz: !!python/object:os.system {MARK}\n")))
probes.append(("YAML alias unknown config.yaml", raw("config.yaml", f"\nz: *{MARK}\n")))

# unknown key / unknown value per file
def add_key(name, listlike=False):
    def f(d):
        if isinstance(d, list):
            d[0][MARK] = 1
        else:
            d[MARK] = 1
        return d
    return edit_yaml(name, f)
for fn in ("config.yaml", "agents.yaml", "principals.yaml", "chains.yaml", "actions/lookup_record.yaml"):
    probes.append((f"unknown KEY marker | {fn}", add_key(fn)))
probes.append(("unknown KEY marker | egress.yaml", edit_yaml("egress.yaml", lambda d: (d.__setitem__(MARK, 1), d)[1])))
probes.append(("unknown KEY marker nested | config.yaml routes.default", edit_yaml("config.yaml", lambda d: (d["routes"]["default"].__setitem__(MARK, 1), d)[1])))
probes.append(("unknown KEY marker nested | config.yaml backends", edit_yaml("config.yaml", lambda d: (d["backends"].__setitem__(MARK, 1), d)[1])))
probes.append(("unknown KEY marker nested | config.yaml systems.x", edit_yaml("config.yaml", lambda d: (d["systems"]["fixture-records"].__setitem__(MARK, 1), d)[1])))
probes.append(("unknown KEY marker nested | config.yaml backends.llm kind settings", edit_yaml("config.yaml", lambda d: (d["backends"]["llm"].__setitem__(MARK, 1), d)[1])))
probes.append(("unknown KEY marker | tools/test-agent.yaml entry", raw("tools/test-agent.yaml", f"- name: t\n  function: m:f\n  description: d\n  input_schema: {{type: object}}\n  side_effect: none\n  {MARK}: 1\n", append=False)))
probes.append(("unknown KEY marker | agents.yaml budget_usd", edit_yaml("agents.yaml", lambda d: (d[0]["budget_usd"].__setitem__(MARK, "1"), d)[1])))
probes.append(("unknown KEY marker | actions executor", edit_yaml("actions/lookup_record.yaml", lambda d: (d["executor"].__setitem__(MARK, 1), d)[1])))
probes.append(("unknown KEY marker | chains step", edit_yaml("chains.yaml", lambda d: (d[0]["steps"][0].__setitem__(MARK, 1), d)[1])))

# unknown values
probes.append(("unknown VALUE model_route | agents.yaml", edit_yaml("agents.yaml", lambda d: (d[0].__setitem__("model_route", MARK), d)[1])))
probes.append(("unknown VALUE scope name | agents.yaml scope_allowed", edit_yaml("agents.yaml", lambda d: (d[0].__setitem__("scope_allowed", [MARK]), d)[1])))
probes.append(("unknown VALUE status | agents.yaml", edit_yaml("agents.yaml", lambda d: (d[0].__setitem__("status", MARK), d)[1])))
probes.append(("unknown VALUE data_class | agents.yaml", edit_yaml("agents.yaml", lambda d: (d[0].__setitem__("data_class", MARK), d)[1])))
probes.append(("unknown VALUE tools_allowed | agents.yaml", edit_yaml("agents.yaml", lambda d: (d[0].__setitem__("tools_allowed", [MARK]), d)[1])))
probes.append(("unknown VALUE environment | config.yaml", edit_yaml("config.yaml", lambda d: (d.__setitem__("environment", MARK), d)[1])))
probes.append(("unknown VALUE backend kind | config.yaml", edit_yaml("config.yaml", lambda d: (d["backends"].__setitem__("store", MARK), d)[1])))
probes.append(("unknown VALUE backend kind (mapping) | config.yaml", edit_yaml("config.yaml", lambda d: (d["backends"].__setitem__("llm", {"kind": MARK}), d)[1])))
probes.append(("unknown VALUE route key | config.yaml routes", edit_yaml("config.yaml", lambda d: (d["routes"].__setitem__(MARK, d["routes"]["default"]), d)[1])))
probes.append(("unknown VALUE system name | actions target_system", edit_yaml("actions/lookup_record.yaml", lambda d: (d.__setitem__("target_system", MARK), d)[1])))
probes.append(("unknown VALUE chain_id | actions", edit_yaml("actions/lookup_record.yaml", lambda d: (d.__setitem__("chain_id", MARK), d)[1])))
probes.append(("unknown VALUE risk_class | actions", edit_yaml("actions/lookup_record.yaml", lambda d: (d.__setitem__("risk_class", MARK), d)[1])))
probes.append(("unknown VALUE executor kind | actions", edit_yaml("actions/lookup_record.yaml", lambda d: (d["executor"].__setitem__("kind", MARK), d)[1])))
probes.append(("unknown VALUE approver_of | principals", edit_yaml("principals.yaml", lambda d: (d[1].__setitem__("approver_of", [MARK]), d)[1])))
probes.append(("unknown VALUE principal kind | principals", edit_yaml("principals.yaml", lambda d: (d[0].__setitem__("kind", MARK), d)[1])))
probes.append(("unknown VALUE approver_ids | chains", edit_yaml("chains.yaml", lambda d: (d[0]["steps"][0].__setitem__("approver_ids", [MARK]), d)[1])))
probes.append(("unknown VALUE rights | principals", edit_yaml("principals.yaml", lambda d: (d[0].__setitem__("rights", [MARK]), d)[1])))
probes.append(("unknown VALUE egress host | egress.yaml", edit_yaml("egress.yaml", lambda d: (d.__setitem__("hosts", [MARK]), d)[1])))
probes.append(("unknown VALUE check_modules | config.yaml", edit_yaml("config.yaml", lambda d: (d.__setitem__("check_modules", [MARK]), d)[1])))
probes.append(("unknown VALUE prompt_file | agents.yaml", edit_yaml("agents.yaml", lambda d: (d[0].__setitem__("prompt_file", MARK), d)[1])))
probes.append(("unknown VALUE verify_check | actions", edit_yaml("actions/lookup_record.yaml", lambda d: (d.__setitem__("verify_check", MARK), d)[1])))
probes.append(("unknown VALUE tool file name (no agent) | tools/<marker>.yaml", raw(f"tools/{MARK}.yaml", "[]\n", append=False)))
probes.append(("unknown VALUE tool function/operations/hosts/secret_names | tools/test-agent.yaml", raw("tools/test-agent.yaml", f"- name: t\n  function: {MARK}:f\n  description: d\n  input_schema: {{type: object}}\n  side_effect: none\n  operations: [{MARK}]\n  hosts: [{MARK}]\n  secret_names: [{MARK}]\n", append=False)))
probes.append(("unknown VALUE tool side_effect | tools/test-agent.yaml", raw("tools/test-agent.yaml", f"- name: t\n  function: m:f\n  description: d\n  input_schema: {{type: object}}\n  side_effect: {MARK}\n", append=False)))
probes.append(("unknown VALUE tool name pattern | tools/test-agent.yaml", raw("tools/test-agent.yaml", f"- name: {MARK}\n  function: m:f\n  description: d\n  input_schema: {{type: object}}\n  side_effect: none\n", append=False)))
probes.append(("duplicate tool name marker | tools/test-agent.yaml", raw("tools/test-agent.yaml", f"- name: t_{'a'}\n  function: m:f\n  description: d\n  input_schema: {{type: object}}\n  side_effect: none\n- name: t_a\n  function: m:f\n  description: {MARK}\n  input_schema: {{type: object}}\n  side_effect: none\n", append=False)))
probes.append(("tools/test-agent.yaml top-level not a list (marker)", raw("tools/test-agent.yaml", f"{MARK}: 1\n", append=False)))
probes.append(("tools/test-agent.yaml entry not a dict (marker string)", raw("tools/test-agent.yaml", f"- {MARK}\n", append=False)))

results = [run(l, m) for l, m in probes]
leaks = 0
lines = []
for r in results:
    for k, v in r.items():
        if isinstance(v, dict):
            tot = v["marker_in_str"] + v["marker_in_repr"] + v["marker_in_chain"] + v["marker_in_full_traceback"]
            vis = v["marker_in_str"] + v["marker_in_repr"] + v["marker_in_full_traceback"]
            flag = "LEAK-READABLE" if vis else ("hidden-in-suppressed-context-only" if tot else "clean")
            if vis: leaks += 1
            lines.append(f"{flag} | {r['label']} | {k} | {v['type']} | str={v['marker_in_str']} repr={v['marker_in_repr']} chain={v['marker_in_chain']} traceback={v['marker_in_full_traceback']} cause={v['cause_present']} ctx={v['context_present']} suppress={v['suppress_context']} | text: {v['str'][:300]!r}")
            for ml in v["marker_lines"]:
                lines.append(f"     MARKER LINE: {ml[:3000]}")
        elif k != "label":
            lines.append(f"ok-no-error | {r['label']} | {k} | {v}")
print("\n".join(lines))
print(f"\nTOTAL probes={len(results)} readable-marker-results={leaks}")
