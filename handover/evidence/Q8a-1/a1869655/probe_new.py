"""EVIDENCE RUNNER probes, Q8a-1 head a1869655. probe_old.py = the previous probe (107 results) with the path changed;
this file adds the round-8 probes. Marker built from parts. Run as an unprivileged user (so a no-permission file is really refused)."""
import os, sys, stat, types, traceback, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe_old as P
from probe_old import *  # noqa
from probe_old import MARK, WT, edit_yaml, raw, fmt, fresh, run

def setpfx(p):
    P.PFX = p

# ---- (A) the old 107 probes ----
old = list(P.probes)

# ---- (B) new probes ----
new = []
FW_AT, FW_COLON, FW_PCT, FW_LB, FW_RB = P.FW_AT, P.FW_COLON, P.FW_PCT, P.FW_LB, P.FW_RB

# B1: secret typed as a lower-case plain id (the marker is lower case, digits, '-': plain-id shape)
def agents_edit(fn):
    return edit_yaml("agents.yaml", lambda d: (fn(d[0]), d)[1])
new.append(("PLAINID agent id=marker + unknown scope", agents_edit(lambda a: (a.__setitem__("id", MARK), a.__setitem__("scope_allowed", ["nope_action"])))))
new.append(("PLAINID agent id=marker + unknown model_route", agents_edit(lambda a: (a.__setitem__("id", MARK), a.__setitem__("model_route", "nope_route")))))
new.append(("PLAINID agent id=marker, otherwise valid", agents_edit(lambda a: a.__setitem__("id", MARK))))
new.append(("PLAINID action id=marker (bad target_system)", edit_yaml("actions/lookup_record.yaml", lambda d: (d.__setitem__("id", MARK), d.__setitem__("target_system", "nope_sys"), d)[2])))
new.append(("PLAINID action id=marker (bad chain_id)", edit_yaml("actions/lookup_record.yaml", lambda d: (d.__setitem__("id", MARK), d.__setitem__("chain_id", "nope_chain"), d)[2])))
new.append(("PLAINID action id=marker (bad risk_class)", edit_yaml("actions/lookup_record.yaml", lambda d: (d.__setitem__("id", MARK), d.__setitem__("risk_class", "nope"), d)[2])))
new.append(("PLAINID action id=marker, otherwise valid", edit_yaml("actions/lookup_record.yaml", lambda d: (d.__setitem__("id", MARK), d)[1])))
new.append(("PLAINID chain id=marker (unknown approver)", edit_yaml("chains.yaml", lambda d: (d[0].__setitem__("id", MARK), d[0]["steps"][0].__setitem__("approver_ids", ["nope_p"]), d)[2])))
new.append(("PLAINID chain id=marker, otherwise valid", edit_yaml("chains.yaml", lambda d: (d[0].__setitem__("id", MARK), d)[1])))
new.append(("PLAINID principal id=marker (unknown approver_of)", edit_yaml("principals.yaml", lambda d: (d[1].__setitem__("id", MARK), d[1].__setitem__("approver_of", ["nope_chain"]), d)[2])))
new.append(("PLAINID principal id=marker (unknown right)", edit_yaml("principals.yaml", lambda d: (d[0].__setitem__("id", MARK), d[0].__setitem__("rights", ["nope_right"]), d)[2])))
new.append(("PLAINID principal id=marker, otherwise valid", edit_yaml("principals.yaml", lambda d: (d[1].__setitem__("id", MARK), d)[1])))
new.append(("PLAINID duplicate agent id=marker twice", edit_yaml("agents.yaml", lambda d: (d.append(dict(d[0])), d[0].__setitem__("id", MARK), d[1].__setitem__("id", MARK), d)[3])))
new.append(("PLAINID duplicate principal id=marker twice", edit_yaml("principals.yaml", lambda d: (d.append(dict(d[1])), d[1].__setitem__("id", MARK), d[2].__setitem__("id", MARK), d)[3])))
new.append(("PLAINID duplicate chain id=marker twice", edit_yaml("chains.yaml", lambda d: (d.append(dict(d[0])), d[0].__setitem__("id", MARK), d[1].__setitem__("id", MARK), d)[3])))

# B2: user:marker@host and look-alikes in every URL field of config (backend kinds + systems)
def setbk(cap, val):
    def f(d):
        d["backends"][cap] = val; return d
    return edit_yaml("config.yaml", f)
URLFIELDS = {
 "systems.base_url": lambda u: edit_yaml("config.yaml", lambda d: (d["systems"]["fixture-records"].__setitem__("base_url", u), d)[1]),
 "llm openai_compat.base_url": lambda u: setbk("llm", {"kind": "openai_compat", "base_url": u}),
 "secrets vault.address": lambda u: setbk("secrets", {"kind": "vault", "address": u}),
 "signer vault_transit.address": lambda u: setbk("signer", {"kind": "vault_transit", "address": u, "key_name": "k", "key_version": 1}),
 "secrets azure_key_vault.vault_url": lambda u: setbk("secrets", {"kind": "azure_key_vault", "vault_url": u}),
 "signer azure_key_vault_key.key_id": lambda u: setbk("signer", {"kind": "azure_key_vault_key", "key_id": u}),
 "anchor s3_object_lock.endpoint_url": lambda u: setbk("anchor", {"kind": "s3_object_lock", "bucket": "b", "region": "r", "endpoint_url": u}),
 "anchor azure_immutable_blob.account_url": lambda u: setbk("anchor", {"kind": "azure_immutable_blob", "account_url": u, "container": "abc"}),
 "channel slack.api_base": lambda u: setbk("channel", {"kind": "slack", "channel_id": "c", "signing_secret_name": "s", "bot_token_secret_name": "t", "api_base": u}),
}
SHAPES = {
 "ascii login user:marker@host": lambda p: f"https://user:{MARK}@host.example{p}",
 "ascii login marker@host (user only)": lambda p: f"https://{MARK}@host.example{p}",
 "fullwidth brackets": lambda p: f"https://{FW_LB}{MARK}{FW_RB}host.example{p}",
 "fullwidth percent": lambda p: f"https://host{FW_PCT}{MARK}.example{p}",
 "fullwidth @ and :": lambda p: f"https://user{FW_COLON}{MARK}{FW_AT}host.example{p}",
 "ascii percent": lambda p: f"https://host%{MARK}.example{p}",
 "ascii brackets": lambda p: f"https://[{MARK}]{p}",
 "clean control (no marker)": lambda p: f"https://host.example{p}",
}
PATHS = {"azure_key_vault_key.key_id": "/keys/abc/def123"}
for fld, mk in URLFIELDS.items():
    for sn, sh in SHAPES.items():
        new.append((f"URLFIELD {fld} | {sn}", mk(sh(PATHS.get(fld.split(' ')[-1], "/x") if fld.split(' ')[-1] in PATHS else "/x"))))

# B3: egress.yaml extra key (no marker) and non-bare hosts
new.append(("EGRESS extra key (plain word, no marker)", edit_yaml("egress.yaml", lambda d: (d.__setitem__("extra_thing", 1), d)[1])))
new.append(("EGRESS extra key marker", edit_yaml("egress.yaml", lambda d: (d.__setitem__(MARK, 1), d)[1])))
for hn, hv in {"host with scheme": f"https://{MARK}.example", "host with path": f"{MARK}.example/x", "host with login": f"user:{MARK}@host.example",
               "host with port": f"{MARK}.example:443", "host with space": f"{MARK} .example", "fullwidth dot/colon": f"{MARK}{FW_COLON}443",
               "host with upper": f"{MARK.upper()}.example", "host with percent": f"{MARK}%41.example", "host with wildcard": f"*.{MARK}.example",
               "host with fw brackets": f"{FW_LB}{MARK}{FW_RB}", "host empty": "", "host non-str int": 5, "host list nested": [MARK]}.items():
    new.append((f"EGRESS non-bare host | {hn}", edit_yaml("egress.yaml", lambda d, hv=hv: (d.__setitem__("hosts", [hv]), d)[1])))
new.append(("EGRESS hosts not a list (marker string)", edit_yaml("egress.yaml", lambda d: (d.__setitem__("hosts", MARK), d)[1])))
new.append(("EGRESS top level is a list (marker)", edit_yaml("egress.yaml", lambda d: [MARK])))
new.append(("EGRESS top level is a string (marker)", raw("egress.yaml", f"{MARK}\n", append=False)))

# B4: unhashable YAML key at every yaml file (list key holding the marker)
UK = f"? [{MARK}, b]\n: 1\n"
for fn in ("config.yaml",):
    new.append((f"UNHASHABLE key | {fn} (appended)", raw(fn, "\n" + UK)))
for fn in ("egress.yaml", "agents.yaml", "principals.yaml", "chains.yaml", "actions/lookup_record.yaml", "tools/test-agent.yaml"):
    new.append((f"UNHASHABLE key | {fn} (whole file)", raw(fn, UK, append=False)))
new.append(("UNHASHABLE key | config.yaml nested under routes", lambda root: (root/"config.yaml").write_text((root/"config.yaml").read_text().replace("routes:\n  default:", f"routes:\n  ? [{MARK}, b]\n  : x\n  default:"))))
new.append(("UNHASHABLE key | config.yaml nested under backends", lambda root: (root/"config.yaml").write_text((root/"config.yaml").read_text().replace("backends:\n", f"backends:\n  ? [{MARK}, b]\n  : x\n", 1))))
new.append(("UNHASHABLE key | tuple-like mapping key (marker)", raw("config.yaml", f"\n? {{{MARK}: 1}}\n: 2\n")))

# B5: OSError at load_config and load_registry (directory instead of file; symlink loop; no permission when run unprivileged)
def asdir(name):
    def m(root):
        p = root / name
        if p.exists():
            p.unlink()
        p.mkdir(parents=True)
    return m
def asloop(name):
    def m(root):
        p = root / name
        if p.exists() or p.is_symlink():
            p.unlink()
        p.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(p.name, p)
    return m
def noperm(name):
    def m(root):
        (root / name).chmod(0)
    return m
OSF = ("config.yaml", "egress.yaml", "agents.yaml", "principals.yaml", "chains.yaml", "actions/lookup_record.yaml", "prompts/test-agent.md")
osprobes = []
for fn in OSF:
    osprobes.append((f"OSERROR dir instead of file | {fn}", asdir(fn)))
    osprobes.append((f"OSERROR symlink loop | {fn}", asloop(fn)))
    osprobes.append((f"OSERROR no permission (uid {os.getuid()}) | {fn}", noperm(fn)))
osprobes.append(("OSERROR dir instead of file | tools/test-agent.yaml", asdir("tools/test-agent.yaml")))
osprobes.append(("OSERROR no permission | actions dir", lambda root: (root/"actions").chmod(0)))
osprobes.append(("OSERROR config dir itself missing (path holds marker)", lambda root: shutil.rmtree(root/"actions")))

results = []
for l, m in old + new:
    P.PFX = None
    results.append(run(l, m))
for l, m in osprobes:
    P.PFX = MARK + "-"   # the temp path itself holds the marker, so an echoed path shows it
    results.append(run(l, m))
P.PFX = None

# B6: validator in a module named hadavin_sdk._x calling int/float/fromhex/Decimal and plain ValueError(marker)
from pydantic import BaseModel, ConfigDict, field_validator, ValidationError
from decimal import Decimal
from hadavin_sdk.errors import ConfigValueError
from hadavin_sdk import config as C
modname = "hadavin_sdk._x"
mod = types.ModuleType(modname); sys.modules[modname] = mod
def make(name, check):
    ns = {"__module__": modname}
    class M(BaseModel):
        model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
        v: str
        @field_validator("v")
        @classmethod
        def _c(cls, x):
            return check(x)
    M.__module__ = modname; M.__qualname__ = name
    return M
checks = {
 "int(marker)": lambda x: int(x),
 "float(marker)": lambda x: float(x),
 "bytes.fromhex(marker)": lambda x: bytes.fromhex(x),
 "Decimal(marker)": lambda x: Decimal(x),
 "plain ValueError(marker)": lambda x: (_ for _ in ()).throw(ValueError(x)),
 "ValueError(f'bad {marker!r}')": lambda x: (_ for _ in ()).throw(ValueError(f"bad {x!r}")),
 "AssertionError(marker)": lambda x: (_ for _ in ()).throw(AssertionError(x)),
 "ConfigValueError fixed sentence": lambda x: (_ for _ in ()).throw(ConfigValueError("a fixed sentence")),
 "ConfigValueError holding the marker (author slip, for contrast)": lambda x: (_ for _ in ()).throw(ConfigValueError(x)),
 "ValueError subclass of ConfigValueError? no: subclass of ValueError(marker)": lambda x: (_ for _ in ()).throw(type("MyErr", (ValueError,), {})(x)),
}
vlines = []
for k, ck in checks.items():
    M = make("X", ck)
    try:
        M(v=MARK); vlines.append(f"no-error | {k}")
        continue
    except ValidationError as e:
        for fn_name, fn in (("config_error_text", C.config_error_text), ("_validation_text", C._validation_text)):
            t = fn(e)
            vlines.append(f"{'LEAK-READABLE' if MARK in t else 'clean'} | validator in {modname} | {k} | {fn_name} | text: {t[:200]!r}")
        # also via a real load: a ConfigError wrapping, using a backend kind table entry
    except BaseException as e:
        vlines.append(f"other-exc | {k} | {type(e).__name__}")
# real-path: a custom backend settings model whose validator calls int(marker) through load_config
try:
    from hadavin_sdk.backends import table as T
    base = T.TABLE["secrets"]["env"]
    import dataclasses
    class XS(T.KindSettings):
        n: str
        @field_validator("n")
        @classmethod
        def _c(cls, x):
            return int(x)
    XS.__module__ = modname
    T.TABLE["secrets"]["xx"] = dataclasses.replace(base, settings=XS)
    root = fresh()
    cfgp = root / "config.yaml"
    d = yaml.safe_load(cfgp.read_text()); d["backends"]["secrets"] = {"kind": "xx", "n": MARK}; cfgp.write_text(yaml.safe_dump(d))
    try:
        load_config(root); vlines.append("no-error | real-path int(marker) through load_config")
    except BaseException as e:
        f = fmt(e)
        vis = f["marker_in_str"] + f["marker_in_repr"] + f["marker_in_full_traceback"]
        vlines.append(f"{'LEAK-READABLE' if vis else ('hidden' if f['marker_in_chain'] else 'clean')} | real-path int(marker) via load_config backends.secrets | text: {f['str'][:200]!r}")
    del T.TABLE["secrets"]["xx"]
except BaseException as e:
    vlines.append("real-path setup failed: " + type(e).__name__ + ": " + str(e)[:200])

# B7: tool call URL (ToolContext.fetch), no network (an opener that records; refusal comes before it)
from hadavin_sdk import tools as tools_mod
sys.path.insert(0, str(WT))
from tests.k5_support import TOOL
class _Op:
    def open(self, req, timeout=None): raise RuntimeError("network reached")
tools_mod.http_guard.OPENER = _Op(); tools_mod.http_guard.LOCAL_OPENER = _Op()
def ctx():
    return tools_mod.ToolContext(tools_mod.ToolSpec(**{**TOOL, "hosts": ["api.example.com"], "operations": ["bundle.read"]}), 3.0, lambda n: "x"*20, {"bundle.read": ("GET", r"/x")})
urls = {
 "user:marker@host": f"https://user:{MARK}@api.example.com/x",
 "marker@host": f"https://{MARK}@api.example.com/x",
 "marker@evil host": f"https://user:{MARK}@evil.example.org/x",
 "fullwidth brackets": f"https://{FW_LB}{MARK}{FW_RB}api.example.com/x",
 "fullwidth percent": f"https://api{FW_PCT}{MARK}.example.com/x",
 "ascii percent in host": f"https://api%{MARK}.example.com/x",
 "marker as host": f"https://{MARK}/x",
 "marker as path": f"https://api.example.com/{MARK}",
 "marker in port": f"https://api.example.com:{MARK}/x",
 "bad ipv6 marker": f"https://[{MARK}]/x",
 "backslash+marker": f"https://api.example.com\\{MARK}/x",
 "clean control": "https://api.example.com/x",
}
tl = []
for k, u in urls.items():
    try:
        ctx().fetch("GET", u, operation="bundle.read"); tl.append(f"ok-no-error | {k}")
    except BaseException as e:
        f = fmt(e); vis = f["marker_in_str"] + f["marker_in_repr"] + f["marker_in_full_traceback"]
        tl.append(f"{'LEAK-READABLE' if vis else ('hidden' if f['marker_in_chain'] else 'clean')} | TOOLFETCH url | {k} | {f['type']} | text: {f['str'][:200]!r} | ctx={f['context_present']} suppress={f['suppress_context']}")
for k, kw in {"operation=marker": dict(operation=MARK), "method=marker": dict(operation="bundle.read")}.items():
    try:
        ctx().fetch(MARK if k.startswith("method") else "GET", "https://api.example.com/x", **kw)
    except BaseException as e:
        f = fmt(e); vis = f["marker_in_str"] + f["marker_in_full_traceback"]
        tl.append(f"{'LEAK-READABLE' if vis else 'clean'} | TOOLFETCH {k} (tool-author supplied, not config) | {f['type']} | text: {f['str'][:200]!r}")
# kubernetes api_url
from hadavin_sdk.sources.kubernetes import KubernetesSettings
for sn, sh in SHAPES.items():
    u = sh("")
    try:
        KubernetesSettings(api_url=u, namespaces=("a",)); tl.append(f"ok-no-error | K8S api_url | {sn}")
    except BaseException as e:
        t = C.config_error_text(e) if isinstance(e, ValidationError) else str(e)
        full = "".join(traceback.format_exception(e))
        tl.append(f"{'LEAK-READABLE' if (MARK in t or MARK in full) else 'clean'} | K8S api_url | {sn} | text: {t[:160]!r} | pydantic str has marker: {MARK in str(e)}")

# ---- report ----
leaks = 0; lines = []
for r in results:
    for k, v in r.items():
        if isinstance(v, dict):
            tot = v["marker_in_str"] + v["marker_in_repr"] + v["marker_in_chain"] + v["marker_in_full_traceback"]
            vis = v["marker_in_str"] + v["marker_in_repr"] + v["marker_in_full_traceback"]
            flag = "LEAK-READABLE" if vis else ("hidden-in-suppressed-context-only" if tot else "clean")
            if vis: leaks += 1
            lines.append(f"{flag} | {r['label']} | {k} | {v['type']} | str={v['marker_in_str']} repr={v['marker_in_repr']} chain={v['marker_in_chain']} traceback={v['marker_in_full_traceback']} suppress={v['suppress_context']} | text: {v['str'][:300]!r}")
            for ml in v["marker_lines"]:
                lines.append(f"     MARKER LINE: {ml[:400]}")
        elif k != "label":
            lines.append(f"ok-no-error | {r['label']} | {k} | {v}")
print("\n".join(lines))
print("\n== validator-module probes ==\n" + "\n".join(vlines))
print("\n== tool call URL and K8S probes ==\n" + "\n".join(tl))
nres = sum(1 for r in results for k, v in r.items() if isinstance(v, dict))
print(f"\nTOTAL probes={len(results)} error-results={nres} readable-marker-results(config probes)={leaks} validator-leaks={sum(1 for l in vlines if l.startswith('LEAK'))} tool/k8s-leaks={sum(1 for l in tl if l.startswith('LEAK'))}")
