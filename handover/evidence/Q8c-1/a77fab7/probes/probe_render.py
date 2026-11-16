import sys, json
sys.path.insert(0, "tools")
import policy_page as p

pols = p.load_all()
V, T, K = pols["secrets/vault"], pols["signer/vault_transit"], pols["source/kubernetes"]
okv = {"mount": "kv", "path_prefix": "app/"}
okt = {"transit_mount": "transit", "key_name": "sign-key"}
okk = {"namespaces": "team-a", "ROLE_NAME": "reader-role", "SERVICE_ACCOUNT": "reader-sa", "SERVICE_ACCOUNT_NAMESPACE": "team-a"}

def tryit(label, fn):
    try:
        out = fn()
        print(f"ACCEPTED  | {label} | output {len(out)} chars | first lines: {out.splitlines()[:3] if out else ''}")
        return out
    except Exception as e:
        print(f"REFUSED   | {label} | {type(e).__name__}: {str(e)[:150]}")

print("== page mode (no values) ==")
for n, (pol, r) in {"vault": (V, p.render_vault), "transit": (T, p.render_vault), "k8s": (K, p.render_kubernetes)}.items():
    out = r(pol)
    print(f"page {n}: {len(out)} chars; lines containing placeholders: {sum(1 for l in out.splitlines() if '{' in l or '<' in l)}")

print("== baseline ok values ==")
tryit("vault ok", lambda: p.render_vault(V, okv))
tryit("transit ok", lambda: p.render_vault(T, okt))
tryit("k8s ok", lambda: p.render_kubernetes(K, okk))

print("== hostile values ==")
cases = []
def v(k, val, base=okv, pol=V): cases.append((f"vault {k}={val!r:.60}", lambda b=dict(base, **{k: val}), pol=pol: p.render_vault(pol, b)))
def t(k, val): cases.append((f"transit {k}={val!r:.60}", lambda b=dict(okt, **{k: val}): p.render_vault(T, b)))
def k(key, val, base=None):
    b = dict(okk, **{key: val}); 
    cases.append((f"k8s {key}={val!r:.60}", lambda b=b: p.render_kubernetes(K, b)))
for m in ["sys", "sys/foo", "auth", "auth/token", "identity", "cubbyhole", "kv/sys", "system", "sysx"]:
    v("mount", m)
    t("transit_mount", m)
for ns in ["kube-system", "kube-public", "kube-x", "kube", "default", "team-a,team-a", "team-a,team-b", "a"*63, "a"*64, "a"*300]:
    k("namespaces", ns)
    k("SERVICE_ACCOUNT_NAMESPACE", ns)
for r in ["cluster-admin", "admin", "edit", "view", "system:node", "system-x", "systemic", "Admin", "reader"]:
    k("ROLE_NAME", r)
for s in ["default", "Default", "ok-sa"]:
    k("SERVICE_ACCOUNT", s)
k("ROLE_NAME", "r"*253); k("ROLE_NAME", "r"*254); k("SERVICE_ACCOUNT", "s"*300)
for val in ["a"*300, "a/"*130, "app/\x00x/", "app/\nx/", "app/\tx/", "app/\x1b[0m/", "app/\r/", "kv\x00", "app/+/", "app/*/", "app/*", "+/", "*/", "app/+", "app/**/", "app/?/", "app/[a]/", "app/{x}/", "app/<x>/", "app/../", "app/./", "/app/", "app//", "app/x y/", "app/$(id)/", "app/`id`/", "app/;rm -rf/", "app/|x/", "app/&x/", "app/'x/", 'app/"x/', "app/\\x/", "app/%2e/", "app/é/", "", "app"]:
    v("path_prefix", val)
for val in ["kv/+", "kv/*", "k*", "+", "*", "kv/**", "kv\x00", "kv\n", "kv;id", "kv$(id)", "kv`id`", "kv|x", "kv&x", "kv x", "a"*300, "kv/../sys", "kv/.", "", "kv/", "/kv", "kv//x", "kv/nested/mount"]:
    v("mount", val)
for val in ["k*", "+", "*", "key/+", "key\x00", "key\n", "key;id", "key$(id)", "key`id`", "k"*300, "..", ".", "a b", ""]:
    t("key_name", val)
for key in ["namespaces", "ROLE_NAME", "SERVICE_ACCOUNT", "SERVICE_ACCOUNT_NAMESPACE"]:
    for val in ["*", "a*", "team-*", "team-+", "a\x00b", "a\nb", "a;b", "a$(id)", "a`id`", "a|b", "a&b", "a'b", 'a"b', "a b", "A", "-a", "a-", "a:b", "x" * 300, "", "team-a,", ",team-a", "a,,b"]:
        k(key, val)
# extra keys / missing keys / non-str
cases.append(("vault extra key", lambda: p.render_vault(V, dict(okv, extra="x"))))
cases.append(("vault missing key", lambda: p.render_vault(V, {"mount": "kv"})))
cases.append(("vault non-str mount", lambda: p.render_vault(V, dict(okv, mount=5))))
cases.append(("vault empty dict values", lambda: p.render_vault(V, {})))
cases.append(("k8s namespaces 1+ with default sa-ns", lambda: p.render_kubernetes(K, dict(okk, namespaces="team-a,team-b,team-c"))))
for label, fn in cases:
    tryit(label, fn)
