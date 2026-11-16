"""EVIDENCE probe for round-7 Issues 1-5 (own script, outside the repo). usage: PYTHONPATH=<src> python probe7.py out.json"""
import json, sys
from datetime import UTC, datetime
import hadavin_sdk
from hadavin_sdk.approvals.channel import clean
from hadavin_sdk.guard import runmap
from hadavin_sdk.tools import redact_layered
from hadavin_sdk.k1b.bundle import Bundle
from hadavin_sdk.k1b.redaction import redact_bundle

def bundle(**kw):
    base = dict(case_id="case-ev", alert_time=datetime(2026, 1, 1, 10, tzinfo=UTC), alert_time_text="2026-01-01T10:00:00Z",
                alert={}, metrics=(), logs=(), deploys=(), k8s=(), runbooks=(), ids=frozenset(), manifest_sha256="0" * 64)
    base.update(kw)
    return Bundle(**base)

def paths_text(text):
    out = {}
    out["card"] = clean(text)
    out["tool"] = redact_layered(text, {})
    out["run"] = runmap.redact_text(text, {})
    out["log"] = runmap.safe_head(text, 4000, {})
    b = bundle(logs=(("l.jsonl", ({"ts": "2026-01-01T10:00:00Z", "message": text},)),))
    out["record_msg"] = redact_bundle(b)[0].logs[0][1][0]["message"]
    return out

def record_key(key, value):
    b = bundle(logs=(("l.jsonl", ({"ts": "2026-01-01T10:00:00Z", key: value},)),), alert={key: value})
    r = redact_bundle(b)[0]
    return {"record_key_log": json.dumps(r.logs[0][1][0], ensure_ascii=False), "record_key_alert": json.dumps(r.alert, ensure_ascii=False)}

cells = []
def run(issue, label, texts_fn, frags):
    try:
        outs = texts_fn()
    except Exception as e:
        outs = {"ERR": repr(e)[:120]}
    for path, out in outs.items():
        cells.append({"issue": issue, "cell": label, "path": path, "readable": [f for f in frags if f in out], "out": out})

V1 = ("Qa1solo", ["Qa1solo"])
V2 = ("Qb2first Qb2second", ["Qb2first", "Qb2second"])
def forms(issue, key, value, frags, record=True):
    for form, tmpl in (("flag-space", "ran tool --{k} {v} --verbose"), ("flag-eq", "ran tool --{k}={v} --verbose"),
                       ("kv-eq", "cfg {k}={v} end"), ("kv-colon", "header {k}: {v}"), ("json", '{{"{k}": "{v}"}} tail')):
        run(issue, f"{key}|{form}", lambda t=tmpl: paths_text(t.format(k=key, v=value)), frags)
    if record:
        run(issue, f"{key}|record", lambda: record_key(key, value), frags)

# Issue 1: digits glued behind a credential word
for k in ["pass2", "newpass2", "session2", "auth1", "rootauth2", "auth0", "oauth2", "pass", "oauth", "password2"]:
    forms(1, k, *V1)
for k in ["pass2", "newpass2", "api_key2", "auth0", "oauth2"]:
    run(1, f"--{k} space two-word", lambda k=k: paths_text(f"ran tool --{k} {V2[0]} --verbose"), V2[1])
# max_tokens stays a count (must stay readable)
for t in ["max_tokens=1024", "--max_tokens 1024", "--tokens 5", "tokens=77", "reasoning_tokens: 4321"]:
    run(1, f"count|{t}", lambda t=t: paths_text("run " + t + " end"), [t.split()[-1].split("=")[-1]])
run(1, "count|record max_tokens", lambda: record_key("max_tokens", 1024), ["1024"])
# Issue 2: plurals
for k in ["secrets", "passwords", "apikeys", "api_tokens", "access_tokens", "credentials", "tokens", "max_tokens", "secret", "api_token"]:
    forms(2, k, *V1)
# Issue 3: cookie in any case
for k in ["Cookie", "COOKIE", "Set-Cookie", "cookies", "cookie", "cookie_policy_enabled", "cookie_name", "session_cookie"]:
    run(3, f"{k}|record", lambda k=k: record_key(k, "Qc3cookieval"), ["Qc3cookieval"])
    run(3, f"{k}|kv-eq", lambda k=k: paths_text(f"cfg {k}=Qc3cookieval end"), ["Qc3cookieval"])
    run(3, f"{k}|kv-colon", lambda k=k: paths_text(f"header {k}: Qc3cookieval"), ["Qc3cookieval"])
for k in ["cookie", "Cookie", "COOKIE", "set-cookie", "session_cookie"]:
    run(3, f"--{k} space", lambda k=k: paths_text(f"curl --{k} Qc3cookieval --verbose"), ["Qc3cookieval"])
    run(3, f"--{k} name=value", lambda k=k: paths_text(f"curl --{k} sid=Qc3cookieval --verbose"), ["Qc3cookieval"])
run(3, "Cookie=a;b", lambda: paths_text("hdr Cookie=Qc3one;Qc3two end"), ["Qc3one", "Qc3two"])
run(3, "session_cookie=a;b", lambda: paths_text("hdr session_cookie=Qc3one;Qc3two end"), ["Qc3one", "Qc3two"])
# Issue 4: authorization schemes
TOK = "Qd4tokenpart"
for scheme in ["Bearer", "Basic", "Token", "Digest", "ApiKey"]:
    run(4, f"--authorization {scheme} tok", lambda s=scheme: paths_text(f"ran --authorization {s} {TOK} --verbose"), [TOK])
    run(4, f"authorization={scheme} tok", lambda s=scheme: paths_text(f"cfg authorization={s} {TOK} end"), [TOK])
    run(4, f"authorization: {scheme} tok", lambda s=scheme: paths_text(f"Authorization: {s} {TOK}"), [TOK])
    run(4, f"--authorization={scheme} tok", lambda s=scheme: paths_text(f"ran --authorization={s} {TOK} --verbose"), [TOK])
    run(4, f"record authorization", lambda s=scheme: record_key("authorization", f"{s} {TOK}"), [TOK])
run(4, "Digest params", lambda: paths_text('Authorization: Digest username="bob", realm="r", response="Qd4hash", more prose'), ["Qd4hash"])
run(4, "generic 2nd word --newpass a b", lambda: paths_text("ran --newpass Qd4first Qd4second --verbose"), ["Qd4first", "Qd4second"])
run(4, "generic 2nd word --password a b", lambda: paths_text("ran --password Qd4first Qd4second --verbose"), ["Qd4first", "Qd4second"])
run(4, "generic 2nd word --newpass=a b", lambda: paths_text("ran --newpass=Qd4first Qd4second --verbose"), ["Qd4first", "Qd4second"])
run(4, "sibling authorization=a b (no scheme)", lambda: paths_text("cfg authorization=Qd4first Qd4second more words"), ["Qd4first", "Qd4second"])
run(4, "sibling --db-root-user-password", lambda: paths_text("ran --db-root-user-password Qd4solo --verbose"), ["Qd4solo"])
run(4, "sibling 4 words prefix", lambda: paths_text("ran --a-b-c-d-password Qd4solo --verbose"), ["Qd4solo"])
# Issue 5: ordinary words
for k in ["bypass", "compass", "obsession", "author", "possession", "encompass", "supersession"]:
    forms(5, k, "Qe5ordinary", ["Qe5ordinary"])
for k in ["bypasspass", "compassword", "xbypass", "newpass", "bypass_password"]:
    forms(5, k, "Qe5secretval", ["Qe5secretval"])
json.dump({"src": hadavin_sdk.__file__, "cells": cells}, open(sys.argv[1], "w"), indent=0)
