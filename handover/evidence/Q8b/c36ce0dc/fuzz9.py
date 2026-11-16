"""EVIDENCE RUNNER own fuzz, batch 9. Random texts with made-up secrets (built from parts) in wrapped / multi-cut headers.
Prints one line per readable case (secret still in output after redact) and counts. Seed fixed; same cases on every tree."""
import random, sys, string
from hadavin_sdk.guard.redact import redact
from hadavin_sdk.approvals.channel import clean
rnd = random.Random(20261112)
def secret():
    n = rnd.choice([16, 20, 24, 32, 40])
    al = rnd.choice([string.ascii_letters + string.digits, string.ascii_lowercase, string.ascii_letters + string.digits + "+/=", string.hexdigits.lower()])
    return "Zq" + "".join(rnd.choice(al) for _ in range(n))
SEPS = [" ", "\n", "\r\n", "\t", "  ", "\n ", "\n\t", "\x0b", "\x0c", " ", "%0a", "%0b", " \n"]
KEYS = ["password", "passwd", "pass", "api_key", "apikey", "secret", "token", "access_token", "auth_token", "client_secret", "bypass_key", "session_id", "cookie", "private_key", "x-api-key"]
HDR = ["Authorization", "authorization", "AUTHORIZATION", "Proxy-Authorization", "X-Auth-Token"]
SCH = ["Basic", "Bearer", "Token", "ApiKey", "Digest", "token", "basic", "Bearer"]
def mk():
    s = secret(); kind = rnd.randrange(5)
    pre = " ".join(rnd.choice(["error", "while", "calling", "host", "retry", "log:", "GET", "/v1/x"]) for _ in range(rnd.randrange(0, 4)))
    post = " ".join(rnd.choice(["failed", "status=500", "done", "at", "line", "12"]) for _ in range(rnd.randrange(0, 4)))
    if kind == 0:
        t = f"{rnd.choice(HDR)}:{rnd.choice([' ', '', '  '])}{rnd.choice(SCH)}{rnd.choice(SEPS)}{s}"
    elif kind == 1:
        t = f"{rnd.choice(KEYS)}{rnd.choice(['=', ': ', ' = ', '=\"', ':'])}{s}"
    elif kind == 2:
        k = rnd.choice(KEYS); i = rnd.randrange(1, len(k)); t = f"{k[:i]}{rnd.choice(['\n', ' ', '%0a', '<b></b>', '​'])}{k[i:]}={s}"
    elif kind == 3:
        t = f"curl -H '{rnd.choice(HDR)}: {rnd.choice(SCH)}{rnd.choice(SEPS)}{s}' https://example.com/a"
    else:
        t = f"--{rnd.choice(KEYS)}{rnd.choice([' ', '=', '\n'])}{s}"
    return s, f"{pre} {t} {post}".strip() if rnd.random() < .5 else f"{pre}\n{t}\n{post}"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
bad = 0
for i in range(N):
    s, t = mk()
    try:
        r = redact(t).text; c = clean(t)
    except Exception as e:
        print(f"ERR\t{i}\t{type(e).__name__}"); continue
    # readable stretch = longest common substring run of the secret (>= 12 chars) inside output
    def stretch(out):
        best = 0
        for a in range(0, len(s) - 11):
            L = 12
            if s[a:a + L] in out:
                while a + L < len(s) and s[a:a + L + 1] in out: L += 1
                best = max(best, L)
        return best
    rr, cc = stretch(r), stretch(c)
    if rr or cc:
        bad += 1; print(f"READABLE\t{i}\tredact={rr}\tclean={cc}\t{t!r}"[:260])
print(f"TOTAL\t{N}\treadable_cases\t{bad}")
