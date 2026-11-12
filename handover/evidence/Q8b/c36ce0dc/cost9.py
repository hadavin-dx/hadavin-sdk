"""EVIDENCE RUNNER own cost script: 200 kB hostile texts, 3 runs each, median seconds. src from sys.path[0]."""
import sys, time, statistics
from hadavin_sdk.guard.redact import redact
N = 200_000
def rep(u): return (u * (N // len(u) + 1))[:N]
S = {
 "A letters only": "a" * N,
 "B 40 letters + pass": rep("a" * 40 + "pass"),
 "C 40 letters + password= x": rep("a" * 40 + "password=xyz "),
 "D glued digits + token: ": rep("a1" * 20 + "b" + "token: "),
 "E --a*39 pass flag": rep("--" + "a" * 39 + "pass v "),
 "F --a- runs": "--" + "a-" * (N // 2),
 "G --a_ runs": "--" + "a_" * (N // 2),
 "H pass + digit run": "pass" + "1234567890" * (N // 10),
 "I Digest + spaces": "Authorization: Digest" + " " * N,
 "J Digest + newlines": "Authorization: Digest" + "\n" * N,
 "K authorization abc + spaces": rep("authorization abc" + " " * 50),
 "L cookie prefixes": rep("--a-b-c-d-cookies "),
 "M glued plural tokens": rep("--apiTokens "),
 "N pass words": rep("pass "),
 "O hyphen words": rep("a-b-c-d-e-f-g-password "),
 "P wrapped Basic": rep("Authorization: Basic\n"),
 "Q cookie + long run": "cookie" + "a" * N,
 "R unclosed quote Digest": 'Authorization: Digest "' + "a" * N,
 "S --a-authorization": rep("--a-authorization "),
 "T cookie2 digits": rep("cookie2222222222222222222 "),
}
print("#src", __import__("hadavin_sdk").__file__)
for k, t in S.items():
    ts = []; st = "ok"
    for _ in range(3):
        t0 = time.perf_counter()
        try: redact(t)
        except Exception as e: st = type(e).__name__
        ts.append(time.perf_counter() - t0)
    print(f"{k}\tmedian={statistics.median(ts):.3f}\truns={[round(x, 3) for x in ts]}\t{st}")
