import sys, time, os
from hadavin_sdk.guard.redact import redact
N=200_000
def mk(unit): return (unit*(N//len(unit)+1))[:N]
shapes={
 "A letters only 200k": "a"*N,
 "B 40 letters + pass, repeated (no sep)": mk("a"*40+"pass"),
 "C 40 letters + password= value space": mk("a"*40+"password=xyz "),
 "D 41 digits+letters glued, then token: ": mk("a1"*20+"b"+"token: "),
 "E 39 letters + --pass flag repeated": mk("--"+"a"*39+"pass v "),
 "F 40 letters + password (no sep, no =)": mk("a"*40+"password"),
 "G 200k of 'pass' words": mk("pass "),
}
print("src",__import__("hadavin_sdk").__file__, "load", os.getloadavg())
for name,t in shapes.items():
    ts=[]
    for i in range(3):
        t0=time.perf_counter()
        try: redact(t); st="ok"
        except Exception as e: st=type(e).__name__
        ts.append(round(time.perf_counter()-t0,3))
    print(f"{name}: {ts} {st}")
