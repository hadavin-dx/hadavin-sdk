import time
from hadavin_sdk.guard import runmap
SVB="4xKp2Vb9Lr3NcW8dYh6uJs"
for k,v in {"K43c":'"password'+"k"*300+'": "'+SVB+'"',"K43d":"'token"+"k"*300+"': '"+SVB+"'","K43a":'password'+'k'*30+'="'+SVB+' x"',"Q1":'"password": "hunter 2 x"',"Q2":"password='hunter 2 x'",
 "K42d":"password"+"k"*256+"="+SVB+" x","K42e":"password"+"k"*2000+"="+SVB+" x"}.items():
    print(k,repr(runmap.redact_text(v,runmap.RunMap()))[:120])
ZW=None
for name,f in {"pwd":lambda n:"pwd"*(n//3),"password=":lambda n:"password="*(n//9),"qpass":lambda n:'"password": '*(n//12),"qtoken":lambda n:"'token"*(n//6)}.items():
    r=[]
    for n in (131072,262144):
        t0=time.perf_counter(); runmap.redact_text(f(n)[:n],runmap.RunMap()); r.append(round(time.perf_counter()-t0,2))
    print(name,r)
