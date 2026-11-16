import time, os, sys, hadavin_sdk
from hadavin_sdk.guard.redact import redact
N=200_000
def mk(u): return (u*(N//len(u)+1))[:N]
shapes={
 "A letters only": "a"*N,
 "B 40 letters+pass repeated": mk("a"*40+"pass"),
 "C 40 letters+password= value": mk("a"*40+"password=xyz "),
 "D digits/letters glue + token: ": mk("a1"*20+"b"+"token: "),
 "E --a*39 pass flag": mk("--"+"a"*39+"pass v "),
 "F 'a-' runs flag": "--"+"a-"*(N//2),
 "G 'a_' runs flag": "--"+"a_"*(N//2),
 "H digits after key word": "pass"+"1234567890"*(N//10),
 "I Digest + many spaces": "Authorization: Digest"+" "*N,
 "J Digest + newlines": "Authorization: Digest"+"\n"*N,
 "K word + many spaces": mk("authorization abc"+" "*50),
 "L cookie prefixes": mk("--a-b-c-d-cookies "),
 "M plural tokens glued": mk("--apiTokens "),
 "N pass words": mk("pass "),
 "O hostile hyphen words": mk("a-b-c-d-e-f-g-password "),
}
print("src",hadavin_sdk.__file__,"load",os.getloadavg())
for k,t in shapes.items():
    ts=[]; st="ok"
    for i in range(3):
        t0=time.perf_counter()
        try: redact(t)
        except Exception as e: st=type(e).__name__
        ts.append(round(time.perf_counter()-t0,3))
    print(f"{k}\t{ts}\t{st}")
