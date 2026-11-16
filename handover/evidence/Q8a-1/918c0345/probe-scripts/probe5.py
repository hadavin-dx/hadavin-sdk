"""EVIDENCE probe (item 5): planted made-up markers in configured names; record whether a marker appears in any returned
problem text, exception message/repr/args, cause, context or formatted traceback, or captured log. Records, never judges."""
import itertools, json, logging, sys, traceback, collections, io
import hadavin_sdk
LEGAL = "zq" + "-probe-" + "mk4417"          # legal namespace/project/bucket/region word
SECRET = "Zq9x" + "-Pw-" + "4417"           # capital letters: secret-shaped, not a legal namespace
HEX = "9f" * 16
MARKS = (LEGAL, SECRET, HEX)
rows = []
class H(logging.Handler):
    def __init__(s): super().__init__(); s.buf = []
    def emit(s, r): s.buf.append(r.getMessage() + " " + str(r.args) + (r.exc_text or ""))
def shown(exc):
    out = []; seen = set(); e = exc
    stack = [exc]
    while stack:
        x = stack.pop()
        if x is None or id(x) in seen: continue
        seen.add(id(x))
        out += [str(x), repr(x), str(x.args)]
        stack += [x.__cause__] + ([] if x.__suppress_context__ else [x.__context__])
    out.append("".join(traceback.format_exception(exc)))
    return "\n".join(out)
def run(group, label, fn, marks=MARKS):
    h = H(); lg = logging.getLogger(); lg.addHandler(h); old = lg.level; lg.setLevel(logging.DEBUG)
    ret = None; exc_t = None; txt = ""
    try:
        ret = fn()
        txt = json.dumps(ret, default=str) if isinstance(ret, (list, str)) and all(isinstance(i, str) for i in ret) else ""
    except BaseException as e:
        exc_t = type(e).__name__; txt = shown(e)
    finally:
        lg.removeHandler(h); lg.setLevel(old)
    txt += "\n".join(h.buf)
    hit = [m for m in marks if m in txt]
    rows.append(dict(group=group, label=label, outcome=("raised " + exc_t) if exc_t else "returned", leak=bool(hit), marks=len(hit)))
    return ret
# ------------------------------------------------------------------ Kubernetes
from hadavin_sdk.sources.kubernetes import KubernetesSettings, KubernetesSource
import hadavin_sdk.sources.kubernetes as kmod
from hadavin_sdk.sources import scope_problems
URL = "https://k8s.example.invalid"
POS = {
 "one": lambda m: (m,), "pos2of3": lambda m: ("calm-ns", m, "other-ns"), "dup": lambda m: (m, m),
 "twenty_pos11": lambda m: tuple(f"ns{i}" if i != 10 else m for i in range(20)),
 "last": lambda m: ("a", "b", m), "with_empty": lambda m: (m, ""),
}
RULE = {
 "write_verb": {"resourceRules": [{"verbs": ["delete"], "resources": ["pods"]}]},
 "wildcard": {"resourceRules": [{"verbs": ["*"], "resources": ["pods"]}]},
 "pods_exec": {"resourceRules": [{"verbs": ["get"], "resources": ["pods/exec"]}]},
 "secrets_read": {"resourceRules": [{"verbs": ["get"], "resources": ["secrets"]}]},
 "malformed": {"resourceRules": [{"verbs": "get"}]},
 "clean": {"resourceRules": [{"verbs": ["get"], "resources": ["pods"]}]},
 "no_status_rules": {"incomplete": False},
 "incomplete": {"resourceRules": [], "incomplete": True},
 "evalerror_quotes_ns": "EVAL",
 "resourcenames_quote_ns": "RN",
 "status_not_dict": "NOTDICT",
 "invalid_json_quotes_ns": "BADJSON",
 "fetch_raises_with_body": "RAISE",
 "fetch_returns_none": "NONE",
}
def mk_fetch(kind, m):
    def fetch(method, url, *, operation, body=None, headers=None, max_bytes=None, **kw):
        ns = json.loads(body)["spec"]["namespace"] if body else ""
        v = RULE[kind]
        if v == "EVAL": return json.dumps({"status": {"resourceRules": [], "evaluationError": f"cannot list in namespace {ns} {m}"}})
        if v == "RN": return json.dumps({"status": {"resourceRules": [{"verbs": ["get"], "resources": ["pods"], "resourceNames": [ns, m]}]}})
        if v == "NOTDICT": return json.dumps({"status": f"error for {ns}"})
        if v == "BADJSON": return "{ not json " + ns + m
        if v == "RAISE": raise OSError(f"{method} {url} body={body} refused for {ns}")
        if v == "NONE": return None
        return json.dumps({"status": v})
    return fetch
for (pn, pf), mi in itertools.product(POS.items(), range(len(MARKS))):
    m = MARKS[mi]
    for rk in RULE:
        def go(pf=pf, m=m, rk=rk):
            s = KubernetesSettings(api_url=URL, namespaces=pf(m))
            src = KubernetesSource(mk_fetch(rk, m), s)
            return src.probe_scope()
        run("k8s.probe_scope", f"pos={pn} marker={mi} rule={rk}", go)
        def go2(pf=pf, m=m, rk=rk):
            s = KubernetesSettings(api_url=URL, namespaces=pf(m))
            src = KubernetesSource(mk_fetch(rk, m), s)
            return scope_problems({"k8s": src}, {})
        run("k8s.scope_problems", f"pos={pn} marker={mi} rule={rk}", go2)
# other settings forms
for fname, bad in {"dict_form": [{"name": "X"}], "int": (1, "x"), "plain_string": "x", "empty_list": ()}.items():
    pass
for mi, m in enumerate(MARKS):
    for nm, val in {"plain_str_not_list": m, "dict_entry": ({"name": m},), "dict_form": {"name": m}, "int_and_marker": (1, m), "marker+space": (m + " x",), "marker/slash": (m + "/x",), "upper": (m.upper(),), "dot": (m + ".x",), "too_long": (m * 6,)}.items():
        run("k8s.settings_form", f"{nm} marker={mi}", lambda val=val: KubernetesSettings(api_url=URL, namespaces=val))
    # direct call of rules_problems with a label
    for lab in (m, f"namespace {m}", f"namespace entry {m}"):
        run("k8s.rules_problems_direct", f"label={lab[:6]}.. marker={mi}", lambda lab=lab, m=m: kmod.rules_problems(lab, [{"verbs": ["patch"], "resources": [m]}]))
# ------------------------------------------------------------------ secret names: GCP / AWS / Azure (shared cache base)
import importlib
class Boom(Exception): pass
def prov(kind, m, texts):
    if kind == "gcp":
        from hadavin_sdk.actions.secrets_gcp import GcpSecretManagerProvider
        class C:
            def access_secret_version(self, name, retry=None, timeout=None): raise RuntimeError(texts.format(path=name, name=m, url=f"https://{m}.vault.example.invalid/secrets/{m}"))
        return GcpSecretManagerProvider(C(), project_id=m)
    if kind == "aws":
        from hadavin_sdk.actions.secrets_aws import SecretsManagerProvider
        class C:
            def get_secret_value(self, SecretId): raise RuntimeError(texts.format(path=SecretId, name=m, url=f"arn:aws:secretsmanager:{m}:1:secret:{SecretId}"))
        return SecretsManagerProvider(C())
    if kind == "azure":
        from hadavin_sdk.actions.secrets_azure import AzureKeyVaultProvider
        class C:
            def get_secret(self, name): raise RuntimeError(texts.format(path=name, name=m, url=f"https://{m}.vault.azure.net/secrets/{name}"))
        return AzureKeyVaultProvider(C())
for kind in ("gcp", "aws", "azure"):
    for mi, m in enumerate(MARKS):
        for tn, t in {"quotes_path": "denied on {path}", "quotes_name": "{name}", "quotes_url": "{url}", "plain": "boom"}.items():
            for secname_is_marker in (False, True):
                # a Azure/GCP name must match a pattern; SECRET and LEGAL both do (letters digits - _)
                sn = m if secname_is_marker else "a_secret"
                def go(kind=kind, m=m, t=t, sn=sn):
                    return prov(kind, m, t).get(sn)
                run(f"secrets.{kind}", f"marker={mi} error={tn} name_is_marker={secname_is_marker}", go)
        # name that violates the pattern, marker inside
        run(f"secrets.{kind}", f"bad_name_pattern marker={mi}", lambda kind=kind, m=m: prov(kind, m, "x").get(m + " /bad"))
# exceptions with attributes (cause chains): an exception raised from another; response dict
def chained():
    from hadavin_sdk.actions.secrets_aws import SecretsManagerProvider
    class E(Exception):
        response = {"Error": {"Code": "AccessDenied", "Message": f"no access to {LEGAL}"}}
    class C:
        def get_secret_value(self, SecretId):
            try: raise KeyError(LEGAL)
            except KeyError as k: raise E(f"denied {LEGAL}") from k
    return SecretsManagerProvider(C()).get(LEGAL)
run("secrets.aws", "chained cause with response Message", chained)
# settings forms
from pydantic import ValidationError
from hadavin_sdk.backends.table import (AnthropicSettings, GcpSecretManagerSettings, AwsSecretsManagerSettings, S3ObjectLockSettings, AzureKeyVaultSettings)
for mi, m in enumerate(MARKS):
    for v in (m + " x", m + "/x", m + "_"):
        run("settings", f"gcp.project_id={v[:4]}..{v[-3:]} m={mi}", lambda v=v: GcpSecretManagerSettings(kind="gcp_secret_manager", project_id=v))
        run("settings", f"anthropic.vertex.region bad m={mi} {v[-3:]}", lambda v=v: AnthropicSettings(kind="anthropic", platform="vertex", region=v, project_id=LEGAL))
        run("settings", f"anthropic.vertex.project bad m={mi} {v[-3:]}", lambda v=v: AnthropicSettings(kind="anthropic", platform="vertex", region="r1", project_id=v))
        run("settings", f"anthropic.foundry.resource bad m={mi} {v[-3:]}", lambda v=v: AnthropicSettings(kind="anthropic", platform="foundry", resource=v, api_key_secret_name="k"))
        run("settings", f"s3.bucket={v[-3:]} m={mi}", lambda v=v: S3ObjectLockSettings(kind="s3_object_lock", bucket=v, region="eu-west-1", retention_ack=True))
        run("settings", f"azure.vault_url m={mi} {v[-3:]}", lambda v=v: AzureKeyVaultSettings(kind="azure_key_vault", vault_url="http://" + v))
        run("settings", f"aws.region extra key m={mi} {v[-3:]}", lambda v=v: AwsSecretsManagerSettings(kind="aws_secrets_manager", region="r", **{v: 1}))
# ------------------------------------------------------------------ Anthropic base URL / client
try:
    import anthropic
    from hadavin_sdk.llm import anthropic as wire
    from types import SimpleNamespace
    class V:
        def __init__(self, **kw): raise ValueError(f"bad base_url {kw['base_url']} for region {kw['region']} project {kw['project_id']}")
    class F:
        def __init__(self, **kw): raise ValueError(f"bad base_url {kw['base_url']}")
    for mi, m in enumerate(MARKS):
        orig_v, orig_f = anthropic.AnthropicVertex, anthropic.AnthropicFoundry
        def go_v(m=m):
            anthropic.AnthropicVertex = V
            try: return wire.client(SimpleNamespace(platform="vertex", region=m, project_id=m, call_timeout_s=5, resource=None), None)
            finally: anthropic.AnthropicVertex = orig_v
        def go_f(m=m):
            anthropic.AnthropicFoundry = F
            try: return wire.client(SimpleNamespace(platform="foundry", resource=m, region=None, project_id=None, call_timeout_s=5), "k")
            finally: anthropic.AnthropicFoundry = orig_f
        run("anthropic.client", f"vertex ValueError quotes url m={mi}", go_v)
        run("anthropic.client", f"foundry ValueError quotes url m={mi}", go_f)
    import os
    for mi, m in enumerate(MARKS):
        os.environ["ANTHROPIC_FOUNDRY_RESOURCE"] = "elsewhere"
        run("anthropic.client", f"REAL library foundry env conflict m={mi}", lambda m=m: wire.client(SimpleNamespace(platform="foundry", resource=m, region=None, project_id=None, call_timeout_s=5), "k"))
        os.environ["ANTHROPIC_BASE_URL"] = "https://" + m + ".example.invalid"
        run("anthropic.client", f"REAL library, ANTHROPIC_BASE_URL env holds marker m={mi}", lambda m=m: wire.client(SimpleNamespace(platform="vertex", region=m, project_id=m, call_timeout_s=5, resource=None), None))
        del os.environ["ANTHROPIC_FOUNDRY_RESOURCE"]; del os.environ["ANTHROPIC_BASE_URL"]
except ImportError as e:
    rows.append(dict(group="anthropic.client", label="NOT RUN: import " + str(e), leak=False, outcome="not run", marks=0))
# ------------------------------------------------------------------ migrate role
from hadavin_sdk.store.migrate import migrate
for mi, m in enumerate(MARKS):
    for opt in ("runtime_role", "portal_role", "purge_role"):
        run("migrate.role", f"{opt}= marker={mi}", lambda opt=opt, m=m: migrate("postgresql://x@127.0.0.1:1/none", **{opt: m}))
        run("migrate.role", f"{opt}= marker+quote marker={mi}", lambda opt=opt, m=m: migrate("postgresql://x@127.0.0.1:1/none", **{opt: m + "'; DROP"}))
    run("migrate.role", f"two roles equal marker={mi}", lambda m=m: migrate("postgresql://x@127.0.0.1:1/none", runtime_role=m, portal_role=m))
# ------------------------------------------------------------------ summary
print("module:", hadavin_sdk.__file__)
cnt = collections.Counter((r["group"], r["leak"]) for r in rows)
print("rows", len(rows), "LEAK rows", sum(r["leak"] for r in rows))
for (g, l), n in sorted(cnt.items()): print(f"  {g:28s} leak={l!s:5s} {n}")
oc = collections.Counter((r["group"], r["outcome"].split()[0] + " " + (r["outcome"].split()[1] if " " in r["outcome"] else "")) for r in rows)
for (g, o), n in sorted(oc.items()): print("  outcome", g, o, n)
json.dump(rows, open(sys.argv[1], "w"), indent=0)
print("LEAK EXAMPLES:")
shownc = collections.Counter()
for r in rows:
    if r["leak"] and shownc[r["group"]] < 3:
        shownc[r["group"]] += 1; print("  ", r["group"], r["label"], r["outcome"])
