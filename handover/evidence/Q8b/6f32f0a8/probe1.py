"""Readable-secret probe (evidence runner). Made-up pieces built from parts. Prints JSON: input -> path -> list of readable pieces."""
import json, sys
from datetime import UTC, datetime
from hadavin_sdk.approvals.channel import clean
from hadavin_sdk.guard import runmap
from hadavin_sdk.guard.redact import redact
from hadavin_sdk.k1b.bundle import Bundle
from hadavin_sdk.k1b.redaction import redact_bundle
from hadavin_sdk import tools

_n = [0]
def piece(tag):
    _n[0] += 1
    return "Qx" + tag + "Vb" + str(_n[0] * 7 + 100) + "mz" + chr(97 + _n[0] % 26) + "Kt"

def P(k): return [piece(k) for _ in range(k and 3)]

inputs = []  # (id, text, record_dict_or_None, pieces)
def add(i, text_tpl, rec_tpl, n=1):
    ps = [piece("p") for _ in range(n)]
    text = text_tpl.format(*ps)
    rec = None if rec_tpl is None else json.loads(json.dumps(rec_tpl).replace("{0}", ps[0]).replace("{1}", ps[1] if n > 1 else "").replace("{2}", ps[2] if n > 2 else ""))
    inputs.append((i, text, rec, ps))

# cookie jars
add("jar-semicolon", "Cookie: session={0}; theme={1}; lang={2}", {"cookie": "session={0}; theme={1}; lang={2}"}, 3)
add("jar-semicolon-key", "cookie={0}; {1}={2}", {"cookie": "{0}; {1}={2}"}, 3)
add("jar-comma", "Cookie: session={0}, theme={1}, lang={2}", {"cookie": "session={0}, theme={1}, lang={2}"}, 3)
add("jar-comma-key", "cookie={0}, {1}={2}", {"cookie": "{0}, {1}={2}"}, 3)
add("jar-set-cookie", "Set-Cookie: sid={0}; Path=/; HttpOnly; {1}={2}", {"set-cookie": "sid={0}; Path=/; HttpOnly; {1}={2}"}, 3)
add("a_token_cookie-comma", "a_token_cookie={0},{1}", {"a_token_cookie": "{0},{1}"}, 2)
add("a_token_cookie-comma-space", "a_token_cookie={0}, {1}", {"a_token_cookie": "{0}, {1}"}, 2)
add("a_token_cookie-semi", "a_token_cookie={0};{1}", {"a_token_cookie": "{0};{1}"}, 2)
# flags (two-word value so a half-mask shows)
for f in ["newpass", "oldpass", "postgresauth", "authorization", "bypass", "compass", "oauth", "obsession"]:
    add("flag-" + f + "-space", "run --" + f + " {0} {1} --verbose", None, 2)
    add("flag-" + f + "-eq", "run --" + f + "={0} --verbose", None, 1)
    add("key-" + f + "-eq", f + "={0}", {f: "{0}"}, 1)
    add("key-" + f + "-two-words", f + "={0} {1}", {f: "{0} {1}"}, 2)
# oauth in records
add("rec-oauth", "oauth: {0}", {"oauth": "{0}"}, 1)
add("rec-oauth-nested", "oauth_x: {0}", {"cfg": {"oauth_x": "{0}", "items": [{"oauth": "{1}"}]}}, 2)
add("rec-oauth2-key", "oauth2_client={0}", {"oauth2_client": "{0}"}, 1)
# digit-start names
for nm in ["2fa_token", "1password", "3pass", "9auth", "4secret", "0token", "7api_key", "2oauth"]:
    add("digit-" + nm, nm + "={0}", {nm: "{0}"}, 1)
    add("digit-" + nm + "-flag", "--" + nm + " {0} {1}", None, 2)

def readable(out, pieces):
    return [p for p in pieces if p in out]

def bundle(**kw):
    base = dict(case_id="c", alert_time=datetime(2026, 1, 1, 10, tzinfo=UTC), alert_time_text="2026-01-01T10:00:00Z",
                alert={}, metrics=(), logs=(), deploys=(), k8s=(), runbooks=(), ids=frozenset(), manifest_sha256="0" * 64)
    base.update(kw)
    return Bundle(**base)

res = {}
for i, text, rec, ps in inputs:
    r = {}
    def go(name, fn):
        try:
            out = fn()
            r[name] = readable(out if isinstance(out, str) else json.dumps(out, default=str), ps)
        except Exception as e:
            r[name] = "EXC " + type(e).__name__
    go("card", lambda: clean(text))
    go("tool", lambda: tools.redact_layered(text, runmap.RunMap()))
    go("run", lambda: runmap.redact_text(text, runmap.RunMap()))
    go("log", lambda: redact(text).text)
    go("log-bundle", lambda: redact_bundle(bundle(logs=(("a.log", text),)))[0].logs)
    if rec is not None:
        go("record", lambda: redact_bundle(bundle(deploys=(rec,)))[0].deploys)
    res[i] = r
json.dump(res, sys.stdout, indent=0, sort_keys=True)
