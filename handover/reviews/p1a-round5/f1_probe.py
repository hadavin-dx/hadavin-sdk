import sys, unicodedata
sys.path.insert(0, "src")
from hadavin_sdk.guard import textnorm as t
print(sys.version.split()[0], unicodedata.unidata_version, [n for n in dir(t) if "views" in n])
rngs = {"neg circled L":(0x1F150,0x1F169),"neg squared L":(0x1F170,0x1F189),"regional":(0x1F1E6,0x1F1FF),"dingbat neg circled digits":(0x2776,0x277F),"sans neg circled digit":(0x278A,0x2793),"neg circled digit zero":(0x24FF,0x24FF),"circled digit 1-10":(0x2460,0x2468),"squared L":(0x1F130,0x1F149)}
for name,(a,b) in rngs.items():
    empties=[]; ok=0
    for cp in range(a,b+1):
        c=chr(cp)
        sv=t.squeeze_views(c); fv=t.fold_views(c)
        if all(v=="" for v in sv): empties.append(f"{cp:04X}")
        else: ok+=1
    print(f"{name}: read={ok} empty={len(empties)} {empties[:6]}")
for cp in (0x0C02,0x0B03,0x02B0):
    c=chr(cp); s="pass"+c+"word"
    print(f"U+{cp:04X}", unicodedata.category(c), "squeeze:", t.squeeze_views(s), "fold:", t.fold_views(s))
print("negsq PASSWORD:", t.squeeze_views("".join(chr(0x1F170+ord(x)-65) for x in "PASSWORD")))
