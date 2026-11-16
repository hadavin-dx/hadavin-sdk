import time
from hadavin_sdk.guard import runmap
for name,f in {"pwd":lambda n:"pwd"*(n//3)}.items():
    r=[]
    for n in (16384,32768,65536):
        t0=time.perf_counter(); runmap.redact_text(f(n)[:n],runmap.RunMap()); r.append(round(time.perf_counter()-t0,2))
    print(name,r)
