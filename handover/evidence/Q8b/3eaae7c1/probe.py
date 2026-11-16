"""EVIDENCE RUNNER probe (own script). Usage: python probe.py > out. src comes from PYTHONPATH.
Each case: a template with a made-up value V; cell = (case, form); readable = V in output.
Text form uses guard.redact.redact; record form uses k1b.redaction sensitive/_pair via redact_bundle-free walk."""
import sys, json
import hadavin_sdk
from hadavin_sdk.guard.redact import redact
V = "Jq7" + "firstValue"          # made-up secret-shaped word
W = "Zk9" + "secondWord"
U = "http://example.com/path"
cases = []
def add(name, text, probe=V): cases.append((name, text, probe))
# plural tokens, glued/camelCase flags
for f in ["apiTokens","accessTokens","refreshTokens","idTokens","accesstokens","idtokens","authtokens","apitokens","maxTokens","max_tokens","input_tokens","audio_tokens","tokens"]:
    add(f"flag --{f} V", f"run --{f} {V} now")
    add(f"kv {f}=V", f"{f}={V}")
# cookie flags
for f in ["no-cookies","keep-session-cookies","junk-session-cookies","load-cookies","save-cookies","cookie","set-cookie","session_cookie","cookies"]:
    add(f"wget --{f} url", f"wget --{f} {U}", "example.com/path")
add("curl -b url-ish", f"curl --cookie {V} {U}")
add("cookie_name=V", f"cookie_name={V}"); add("cookie_name: V", f"cookie_name: {V}")
add("cookie-policy=V", f"cookie-policy={V}")
# ordinary words
for w in ["possession_id","obsession_id","bypass_key","compass_code","bypass_code","xbypass_key","bypasspass_key","session_id","pass_code","passkey","auth_value"]:
    add(f"kv {w}=V", f"{w}={V}")
# authorization schemes
for s in ["Bearer","Basic","Digest","Token","NTLM","Negotiate","OAuth","Splunk","Hawk","AWS4-HMAC-SHA256"]:
    add(f"--authorization {s} V", f"--authorization {s} {V}")
    add(f"Authorization: {s} V", f"Authorization: {s} {V}")
    add(f"--authorization={s} V", f"--authorization={s} {V}")
add("--authorization Bearer 'V'", f"--authorization Bearer '{V}'")
add("--authorization \"Bearer V\"", f'--authorization "Bearer {V}"')
add("--bearer V", f"--bearer {V}")
add("Digest quoted hdr", f'Authorization: Digest username="u", response="{V}"')
add("--authorization Digest quoted", f'--authorization Digest username=u, response="{V}"')
add("Digest json one-line", f'{{"h": "Authorization: Digest username=u response={V}", "next": "ok"}}')
add("Digest newline then prose", f"Authorization: Digest\nthe quick {V} fox", V)
add("Digest line", f"Authorization: Digest username=u, response={V}")
# prefix words, six
for n in range(0,8):
    p = "-".join(["a%d"%i for i in range(n)])
    add(f"{n} prefix words --P-password V", f"--{(p+'-') if p else ''}password {V}")
    p2 = "_".join(["a%d"%i for i in range(n)])
    add(f"{n} prefix words _ --P_password V", f"--{(p2+'_') if p2 else ''}password {V}")
add("--cloud-sql-proxy-db-password V", f"--cloud-sql-proxy-db-password {V} now")
# digits after key word
for d in (1,2,8,9,10,11,40,41):
    add(f"pass{'1234567890'*5:.{d}}=V ({d} digits)", f"pass{('1234567890'*5)[:d]}={V}")
add("password1234567890123456789012345678901234567890 = V", f"password{'1234567890'*4}={V}")
# second-word cases
for f in ["--pass2","--password","--newpass","authorization="]:
    add(f"{f} V W", f"{f} {V} {W}" if not f.endswith("=") else f"{f}{V} {W}", W)
cases_n = len(cases)
# record walk
from hadavin_sdk.k1b import redaction as kr
def rec(text):
    try:
        return kr.redact_bundle
    except Exception: return None
def text_out(t):
    try: return redact(t).text
    except Exception as e: return "ERR:"+type(e).__name__
out = {}
for name, t, p in cases:
    o = text_out(t)
    out[name] = {"in": t, "out": o, "readable": p in o}
json.dump({"src": hadavin_sdk.__file__, "n": cases_n, "cells": out}, sys.stdout, indent=0, sort_keys=False)
