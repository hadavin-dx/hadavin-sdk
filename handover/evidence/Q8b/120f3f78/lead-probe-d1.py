import sys
from hadavin_sdk.guard.redact import redact
v="Zq"+"7Kp2Lm9Xw4"
for k in ["x--bypass","x--compass","-bypass","x-bypass","new_bypass","x--overpass","x--possession","bypass"]:
    for f in ["cfg {k}={v} end",'{{"{k}": "{v}"}}',"--{k} {v}"]:
        t=f.format(k=k,v=v); o=redact(t)
        o=o if isinstance(o,str) else getattr(o,'text',str(o))
        print(k,"|",f[:12],"|","READABLE" if v in o else "masked")
