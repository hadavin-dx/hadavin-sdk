import time,sys
from hadavin_sdk.guard import runmap
def t(s):
    t0=time.perf_counter(); runmap.redact_text(s,runmap.RunMap()); return time.perf_counter()-t0
ZW="​"
cases={
 "pwd*N":lambda n:"pwd"*(n//3),
 "password=*N":lambda n:"password="*(n//9),
 "zwsplit pass<zw>word=*N":lambda n:("pass"+ZW+"word=")*(n//10),
 "fullwidth":lambda n:"ｐａｓｓｗｏｒｄ＝"*(n//9),
 "pwd*85+sp":lambda n:("pwd"*85+" ")*(n//256),
 "dots a.a.-":lambda n:"a.a.-"*(n//5),
 "amp":lambda n:"&"*n,
 "?password*N":lambda n:"?"+"password"*(n//8),
 "mix a.password-":lambda n:"a.password-"*(n//11),
}
for name,f in cases.items():
    out=[]
    for n in (65536,131072,262144):
        out.append(round(t(f(n)[:n]),2))
    print(f"{name:28s} 64K={out[0]} 128K={out[1]} 256K={out[2]} ratio256/128={out[2]/max(out[1],1e-3):.2f}")
