"""Own use of the oracle tests/q8b_older_rule.py: for many keys/values, every value the OLD rules masked must not be readable on head (token level, not P1-P3)."""
import sys, re, itertools
sys.path.insert(0, sys.argv[1])
from tests import q8b_older_rule as older
sys.path.insert(0, sys.argv[1]+"/..")
from hadavin_sdk.approvals.channel import clean
from hadavin_sdk.guard import runmap
from hadavin_sdk.tools import redact_layered
words=["Zk3alpha","Yj4bravo","Xh5charlie"]
vals=[words[0], words[0]+"&"+words[1], words[0]+"["+words[1], words[0]+"{"+words[1], words[0]+"\\"+words[1], f"{words[0]}; {words[1]}={words[2]}", f"{words[0]};{words[1]}", f"{words[0]},{words[1]}"]
keys=[f"{f}{s}{w}" for f in ("","session","auth","set","http","x-auth","my_session","token","user") for s in ("","_","-") for w in ("cookie","cookies","Cookie","COOKIE","Set-Cookie") if f or not s]
keys+=["password","passwd","pwd","pass","secret","token","api_key","apikey","credential","session","sessionid","auth","client_secret","access_key"]
tot=0;left=[];checked=0
for k in keys:
    for v in vals:
        for tmpl in ("x {k}={v} y","{k}={v}","{k}: {v}",'{{"{k}": "{v}"}}',"--{k} {v} z"):
            t=tmpl.format(k=k,v=v)
            parts=older.masked_parts(t)
            if not parts: continue
            for path,fn in (("card",clean),("tool",lambda s: redact_layered(s,{})),("run",lambda s: runmap.redact_text(s,{}))):
                out=fn(t); checked+=1
                for p in parts:
                    for w in words:
                        if w in p and w in out: left.append((path,t,out)); break
print("cells checked",checked,"older-masked pieces readable on this code:",len(left))
for x in left[:15]: print(x)
