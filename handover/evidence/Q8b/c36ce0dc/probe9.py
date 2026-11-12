"""EVIDENCE RUNNER own probe, batch 9. src from PYTHONPATH. R = made-up value readable in output, M = masked.
Prints TSV: case, redact-result, clean-result."""
import sys
import hadavin_sdk
from hadavin_sdk.guard.redact import redact
from hadavin_sdk.approvals.channel import clean
V = "Jq7" + "firstValue"
b64 = "dXNlcjpw" + "YXNzd29yZDEyMw=="
tok = "qzxwvutsrqponmlk" + "jihg"
low16 = "abcdefghijklmnop" + "qrstu"
U = "http://example.com/path"
cases = []
def add(n, t, p=V): cases.append((n, t, p))
# wrapped Authorization (r9 Issue 1)
for sch, val in [("Basic", b64), ("Token", tok), ("ApiKey", tok), ("Digest", tok), ("Bearer", tok)]:
    for sep_name, sep in [("LF", "\n"), ("CRLF", "\r\n"), ("LF+sp", "\n "), ("LF+tab", "\n\t"), ("sp", " "), ("2sp", "  "), ("tab", "\t"),
                          ("VT", "\x0b"), ("FF", "\x0c"), ("FS", "\x1c"), ("US", "\x1f"), ("NEL", "\x85"), ("LS", " "), ("PS", " "), ("%0b", "%0b"), ("%0c", "%0c"), ("%0a", "%0a"), ("%1c", "%1c")]:
        add(f"Authorization: {sch}<{sep_name}>val", f"Authorization: {sch}{sep}{val}", val)
add("Digest+LF+prose", f"Authorization: Digest\nplease contact {tok} about this", tok)
add("Basic+LF+lowercase16 alone", f"Authorization: Basic\n{low16}", low16)
add("Token+LF+lowercase16 alone", f"Authorization: Token\n{low16}", low16)
add("Basic+LF+prose short", "Authorization: Basic\nhello there", "hello there")
add("--authorization Basic wrapped", f"curl --authorization Basic\n{b64}", b64)
add("-H quoted wrapped", f'curl -H "Authorization: Basic\n{b64}"', b64)
# Issue 6 cells
for k in ["bypass", "protection_bypass", "protection-bypass", "x-vercel-protection-bypass", "bypass_key", "bypass_code", "bypass-code", "bypass_value", "bypass_token", "bypass_secret", "bypass_phrase", "bypasskey", "bypasscode",
          "compass_code", "compass_key", "overpass_key", "possession_id", "obsession_id", "encompass_key", "passkey", "pass_code", "session_id", "api_key"]:
    add(f"kv {k}=V", f"{k}={V}")
    add(f"colon {k}: V", f"{k}: {V}")
    add(f"json {k}", '{"%s": "%s"}' % (k, V))
for c in ["no-cookies", "keep-session-cookies", "junk-session-cookies", "load-cookies", "save-cookies", "cookies", "cookie", "set-cookie", "session-cookie", "sessioncookie", "set_cookie"]:
    add(f"wget --{c} url", f"wget --{c} {U}", "example.com/path")
    add(f"wget --{c} V", f"wget --{c} {V}")
    add(f"curl --{c} V", f"curl --{c} {V} {U}")
add("curl -b V", f"curl -b {V} {U}")
add("curl --cookie V", f"curl --cookie {V} {U}")
# cookie digits / cookie2
for k in ["cookie", "cookie1", "cookie2", "cookie9", "Cookie2", "cookie_name2", "cookie_name", "set-cookie2", "Set-Cookie2", "cookie20", "cookie123456"]:
    add(f"{k}=V", f"{k}={V}")
    add(f"{k}: V", f"{k}: {V}")
# digit-bound drift (r9 Issue 4b)
for w in ["pass", "password", "auth", "session", "bearer", "secret", "token", "apikey"]:
    for n in [0, 1, 5, 19, 20, 21, 22, 30, 40, 41]:
        add(f"{w}+{n}digits=V", f"{w}{'7'*n}={V}")
        add(f"{w}+{n}digits: V", f"{w}{'7'*n}: {V}")
# KEY_TAIL
for tail in ["a", "_x", "-x" , "x"*20, "x"*21, "_"+"x"*19, "_"+"x"*25, "1_x", "12_" + "x"*20]:
    add(f"password{tail}=V", f"password{tail}={V}")
    add(f"api_key{tail}=V", f"api_key{tail}={V}")
# flags
for f in ["--password", "--pass2", "--newpass", "--a-password", "--a-b-c-d-e-f-password", "--a-b-c-d-e-f-g-h-password", "--apiTokens", "--apiInputTokens", "--max_tokens", "--authorization", "--token"]:
    add(f"flag {f} V", f"run {f} {V} now")
    add(f"flag {f} V W", f"run {f} {V} Zk9secondWord now", V)
add("authorization=a b", f"authorization={V} Zk9secondWord", V)
add("COOKIEJAR=v", f"COOKIEJAR={V}"); add("cookiejar=v", f"cookiejar={V}")
add("COOKIESTORE=v", f"COOKIESTORE={V}"); add("cookiestore=v", f"cookiestore={V}")
# multi-cut / wrapped header texts
add("password split by LF", f"pass\nword={V}")
add("password= LF V", f"password=\n{V}")
add("password: LF V", f"password:\n{V}")
add("%-encoded password", f"password%3D{V}")
add("html-tag split", f"password%<i></i>3D{V}")
add("Authorization wrapped fold in json", '{"h": "Authorization: Basic\\n%s"}' % b64, b64)
def run(path):
    out = {}
    for n, t, p in cases:
        try: r = "R" if p in redact(t).text else "M"
        except Exception as e: r = "E:" + type(e).__name__
        try: c = "R" if p in clean(t) else "M"
        except Exception as e: c = "E:" + type(e).__name__
        out[n] = (r, c)
    return out
if __name__ == "__main__":
    print("#src", hadavin_sdk.__file__, file=sys.stderr)
    for n, (r, c) in run(None).items():
        print(f"{n}\t{r}\t{c}")
