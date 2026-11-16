import sys; from lib import *
from hadavin_sdk.approvals.requests import summary
from hadavin_sdk.models import Plan, Target
print("## import", path_src())
def show(name, inp, out, secrets=(), extra=""):
    rd = [s for s in secrets if readable(s, out)]
    print(f"[{name}]\n  in : {js(inp)[:230]}\n  out: {js(out)[:330]}\n  readable={rd} {extra}")
# ---- E2 card path value with spaces
PW = "correct horse battery staple"; W = ["correct", "horse", "battery", "staple"]
for t in [f"password={PW}", f"password: {PW}", f"password%3D{PW.replace(' ', '%20')}", f'password="{PW}"', f"password='{PW}'", f"db_password={PW} and more", f"x password={PW}\nnext line", f"password={PW}.", f"Password = {PW}", f"PASSWD={PW}", f"passphrase={PW}", f"pwd={PW}"]:
    c = clean(t); s = slack(t)
    show("E2 card " + t[:30], t, {"clean": c, "slack": s}, W, f"idempotent={clean(c)==c}")
    show("E2 walk " + t[:30], t, walk({"message": t}), W)
# ---- E3 secrets
V = "<made-up-value-A>"; LOG = {"message": f"login failed with {V} twice {V}"}
sec_cases = {
 "kind Secret (control)": {"kind": "Secret", "name": "s", "data": {"DB_PASSWORD": b64(V)}},
 "kind secret lower": {"kind": "secret", "name": "s", "data": {"DB_PASSWORD": b64(V)}},
 "kind SECRET upper": {"kind": "SECRET", "name": "s", "data": {"DB_PASSWORD": b64(V)}},
 "kind ' Secret ' spaces": {"kind": " Secret ", "name": "s", "data": {"DB_PASSWORD": b64(V)}},
 "kind secret lower under spec": {"kind": "secret", "name": "s", "spec": {"data": {"DB_PASSWORD": b64(V)}}},
 "Secret stringData": {"kind": "Secret", "stringData": {"DB_PASSWORD": V}},
 "data is a string (valid b64)": {"kind": "Secret", "data": b64(V)},
 "data is a string (invalid b64)": {"kind": "Secret", "data": "!!not base64*" + V},
 "data is a list": {"kind": "Secret", "data": [b64(V), V]},
 "data is a list of maps": {"kind": "Secret", "data": [{"DB_PASSWORD": V}]},
 "data map, entry invalid b64": {"kind": "Secret", "data": {"DB_PASSWORD": "***" + V}},
 "data map, entry is list": {"kind": "Secret", "data": {"DB_PASSWORD": [V, b64(V)]}},
 "data map, entry is map": {"kind": "Secret", "data": {"DB_PASSWORD": {"x": V}}},
 "data map, entry number": {"kind": "Secret", "data": {"PORT": 123456789}},
 "data None": {"kind": "Secret", "data": None},
 "data is int": {"kind": "Secret", "data": 12345678},
 "data nested spec.spec": {"kind": "Secret", "spec": {"spec": {"data": {"A": V}}}},
 "stringData non-cred key": {"kind": "Secret", "stringData": {"CONFIG": V}},
}
for name, sec in sec_cases.items():
    out = walk([sec, LOG])
    secrets = [V, b64(V)]
    show("E3 " + name, [sec, LOG], out, secrets)
# ---- M5 and short/common values
for name, v in [("M5 orders", "orders"), ("8 chars", "abcdefgh"), ("7 chars", "abcdefg"), ("digits 8", "12345678"), ("upper 8", "ABCDEFGH"), ("mixed 8", "abcdEF12")]:
    sec = {"kind": "Secret", "data": {"DB_NAME": b64(v)}}
    log = {"message": f"{v}-api timeout"}
    show(name, [sec, log], walk([sec, log]), [v, b64(v)])
# the appendix row exactly
row = [{"kind": "Secret", "data": {"DB_NAME": b64("orders")}}, {"message": "orders-api timeout"}]
show("APPENDIX M5 orders-api timeout (exact)", row, walk(row), ["orders-api timeout"])
# ---- E4 keys
for name, o in [
 ("env entry PWD", [{"name": "PWD", "value": "/srv/app"}]), ("env entry OLDPWD", [{"name": "OLDPWD", "value": "/srv"}]),
 ("env entry auth_method", [{"name": "auth_method", "value": "oauth2"}]), ("map PWD", {"PWD": "/srv/app"}), ("map OLDPWD", {"OLDPWD": "/srv"}),
 ("map auth_method", {"auth_method": "oauth2"}), ("map author", {"author": "bob"}), ("map authority", {"authority": "internal"}),
 ("map authorization_type", {"authorization_type": "bearer"}), ("map session_id", {"session_id": "abc123"}), ("map pwd_enabled", {"pwd_enabled": "true"}),
 ("map password_policy", {"password_policy": "strict"}), ("map password_policy_enabled yes", {"password_policy_enabled": "yes"}),
 ("map token_expiry ts", {"token_expiry": "2026-11-11T10:00:00Z"}), ("map secret_count 5", {"secret_count": 5}), ("map secretary", {"secretary": "alice"}),
 ("map keyboard_layout", {"keyboard_layout": "us"}), ("map monkey", {"monkey": "x"}), ("map hostname", {"hostname": "node1"}),
]:
    show("E4 " + name, o, walk(o), [])
# ---- code fence mention
for t in ["```\n10.20.30.40@channel\n```", "`10.20.30.40@channel`", "ping 10.20.30.40@channel", "```\n10.20.30.40@here now\n```\nafter 10.20.30.40@everyone", "~~~\n10.20.30.40@channel\n~~~", "```\n10.20.30.40@channel"]:
    c = clean(t); show("MENTION " + t[:30], t, {"clean": c, "slack": slack(t)}, [], f"idempotent={clean(c)==c}")
# ---- target labels
def plan(system, ins=None): return Plan(run_id="run_1", agent_id="agent-ops", action_id="restart_service", action_version=1, risk_class="reversible", inputs=ins or {"n": 1}, target=Target(system=system), idempotency_key="k1", expected_outcome="service restarted")
def lab(system, labels, ins=None):
    try: return summary(plan(system, ins), None, labels) if labels is not None else summary(plan(system, ins))
    except TypeError as e: return f"TypeError {e}"
tl = [("host, no label", "db01.corp.internal", None), ("host + label orders-db", "db01.corp.internal", {"db01.corp.internal": "orders-db"}),
 ("host + host-shaped label", "db01.corp.internal", {"db01.corp.internal": "x.evil.corp"}), ("host + email label", "db01.corp.internal", {"db01.corp.internal": "bob.smith@example.com"}),
 ("host + label L5 (assignment-shaped)", "db01.corp.internal", {"db01.corp.internal": "<assignment-shaped label, text removed>"}), ("host + label with markdown link", "db01.corp.internal", {"db01.corp.internal": "[x](http://evil.example)"}),
 ("host + label with @channel", "db01.corp.internal", {"db01.corp.internal": "orders @channel"}), ("host + label with newline heading", "db01.corp.internal", {"db01.corp.internal": "a\n# forged"}),
 ("host + label that is an IP", "db01.corp.internal", {"db01.corp.internal": "10.20.30.40"}), ("ip target, no label", "10.20.30.40", None),
 ("label for other system", "other.corp.internal", {"db01.corp.internal": "orders-db"}), ("plain target", "orders-db", None), ("email target", "bob.smith@example.com", None),
 ("host + 500-char label", "db01.corp.internal", {"db01.corp.internal": "L" * 500}), ("host + zero-width label", "db01.corp.internal", {"db01.corp.internal": "orders​-db"})]
for n, s, l in tl:
    o = lab(s, l); show("LABEL " + n, [s, l], o, ["<made-up-value-C>", "evil", "bob.smith"] if "label" in n else [], f"sl={slack(o)[:0]}")
