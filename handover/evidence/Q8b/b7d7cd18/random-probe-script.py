"""EVIDENCE: own run of appendix C generators (P1, P2, N9) and the 200,000-key check, typed from the appendix. usage: python rand7.py <repo root>"""
import sys, random, re, time, json
from datetime import UTC, datetime
root=sys.argv[1]; sys.path.insert(0, root); WT="/home/user/build/EV-Q8bb7-b7d7cd18/wt"
from hadavin_sdk.approvals import channel as C, gate
from hadavin_sdk.approvals.channel import clean
from hadavin_sdk.guard import runmap
from hadavin_sdk.k1b.bundle import Bundle
from hadavin_sdk.k1b.redaction import redact_bundle
PW="pass"+"word"; ONE="hunter2"+"secretXYZ"
def bundle(**kw):
    base=dict(case_id="case-ev",alert_time=datetime(2026,1,1,10,tzinfo=UTC),alert_time_text="2026-01-01T10:00:00Z",alert={},metrics=(),logs=(),deploys=(),k8s=(),runbooks=(),ids=frozenset(),manifest_sha256="0"*64)
    base.update(kw); return Bundle(**base)
ALPHA="qxzjkwvy"; SPACE=[chr(c) for c in range(0x3000) if chr(c).isspace()]; BREAK=list(";&,\"'")
ODD=["\x1b[0m","\x08","\x7f","%20","%3B","\\u0041","\\n","&#59;","<",">","=",":","|","/","@","ａｂ","＂","＇","\u200b","\u200d","<SECRET_1>"]
COMPOSITE=["bob.smith@example.com","db01.corp.internal","AKIA"+"IOSFODNN7EXAMPLE","10.20.30.40"]
KEYS=[PW,"api_key","clientSecret","accessToken","PG"+PW.upper(),"pwd","authorization","private_key","bearer","passphrase","refresh_tokens","session",PW+"_for_the_primary_database_replica"]
ENDS=set(SPACE)|set(BREAK)
def word(rng): return "".join(rng.choice(ALPHA+"0123456789") for _ in range(rng.randint(4,9)))
def value(rng):
    target=rng.randint(256,300) if rng.random()<0.06 else rng.randint(1,255); out=""
    while len(out)<target:
        r=rng.random()
        out+=word(rng) if r<0.55 else rng.choice(SPACE) if r<0.75 else rng.choice(BREAK) if r<0.85 else rng.choice(ODD) if r<0.97 else rng.choice(COMPOSITE)
    return out[:target]
def runs(v):
    out,cur=[],""
    for ch in v:
        if ch in ENDS:
            if len(cur)>=4: out.append(cur)
            cur=""
        else: cur+=ch
    if len(cur)>=4: out.append(cur)
    return [r for r in out if all(c in ALPHA+"0123456789" for c in r)]
PH=re.compile(r"(?:<[A-Z0-9_]+>)+")
def p1(seed=20261111,cases=3000):
    rng=random.Random(seed); a=b=c=chk=0; ref=0; t=time.time()
    for i in range(cases):
        v=value(rng); k=rng.choice(KEYS)
        try:
            r=redact_bundle(bundle(alert={k:v},logs=(("l.jsonl",({"ts":"2026-01-01T10:00:00Z",k:v},{"ts":"2026-01-01T10:00:01Z","message":"repeat "+v}),),)))[0]
        except Exception as e:
            ref+=1; continue
        shown=r.alert[k]
        if not (isinstance(shown,str) and (PH.fullmatch(shown) or shown=="<SECRET_REDACTED>")): a+=1
        rs=runs(v)
        if any(x in json.dumps(r.alert,ensure_ascii=False) for x in rs): b+=1
        visible=all((32<=ord(ch)<127) or ch.isspace() for ch in v)
        if 4<=len(v)<=255 and not('"' in v and "'" in v) and visible and runmap.redact_text(v,{})==v:
            chk+=1
            if any(x in r.logs[0][1][1]["message"] for x in rs): c+=1
    return dict(seed=seed,cases=cases,refused=ref,a_not_placeholder=a,b_runs_readable=b,c_checked=chk,c_readable=c,seconds=round(time.time()-t,1))
IDS=["bob.smith@example.com","a.b-c@mail.corp.example.org","db01.corp.internal","pay-api.prod.svc.cluster.local","10.20.30.40","wiki.corp.internal","priya.nair@example.co.in"]
NOISE=["contact","restart","\t\t"," ","\n","```\n","\n```\n","`","~~~\n","<b>","</b>","@here","**","> ","# ","- ",PW+"=","see","(",")","[x]","<",">","&lt;","%40","。",",",";",":","/","evil.com","http://"]
def p2_text(rng):
    parts=[rng.choice(IDS if rng.random()<0.4 else NOISE) for _ in range(rng.randint(1,9))]
    return "".join(p if rng.random()<0.5 else " "+p+" " for p in parts)
def outside_code(text):
    code=set()
    for s,l,ch in gate._closed_fences(text):
        if ch=="`": code.update(range(s+1,l))
    out=[]
    for i,line in enumerate(text.split("\n")):
        if i in code: continue
        segs=[line] if "``" in line else gate._INLINE_CODE.split(line)
        out+=[seg for k,seg in enumerate(segs) if k%2==0]
    return out
def bare(text):
    bad=[]
    for seg in outside_code(text):
        for tok in seg.split():
            t=tok.replace("[.]","|")
            for i,ch in enumerate(t):
                if ch!="." or i==0 or not(t[i-1].isalnum() or t[i-1]==">"): continue
                j=i+1
                while j<len(t) and t[j].isalpha(): j+=1
                if j-(i+1)<2: continue
                bad.append(tok); break
    return bad
def p2(seed=8,cases=4000):
    rng=random.Random(seed); a=b=c=0; t=time.time(); b_ex=[]
    for _ in range(cases):
        x=p2_text(rng)
        try: out=clean(x)
        except Exception as e: a+=1; continue
        flat=out.replace("[.]",".")
        m={}
        try: runmap.redact_text(x,m)
        except Exception: m={}
        origs=[o for o in (m.values() if hasattr(m,"values") else []) if len(o)>=4]
        if any(re.search(r"(?<![A-Za-z0-9])"+re.escape(o)+r"(?![A-Za-z0-9])",flat) for o in origs): a+=1
        if bare(out): b+=1; b_ex.append(x) if len(b_ex)<3 else None
        if clean(out)!=out: c+=1
    return dict(seed=seed,cases=cases,a_identifier_readable=a,b_bare_domain_token=b,c_not_idempotent=c,seconds=round(time.time()-t,1),b_examples=[repr(e) for e in b_ex])
N9_IDS=["bob.smith@example.com","db01.corp.internal","10.20.30.40","wiki.corp.internal"]; N9_SEC=[ONE,"Zx9"+"tailpart77"]
N9_BITS=["<b>","</b>","<i></i>","<span x>"," ","\n",PW+"=",PW+"%","3D","token: ","note",";","<br/> "]
def n9(seed=9,cases=3000):
    rng=random.Random(seed); n=0; t=time.time()
    for _ in range(cases):
        text="".join(rng.choice(N9_IDS+N9_SEC if rng.random()<0.45 else N9_BITS) for _ in range(rng.randint(2,10)))
        m1=C._seeded(text.replace("\x00",""))
        runmap.redact_text(text,m1) if False else None
        flat=clean(text).replace("[.]",".")
        if [o for o in m1.values() if not o.startswith("\0seed") and len(o)>=4 and re.search(r"(?<![A-Za-z0-9])"+re.escape(o)+r"(?![A-Za-z0-9])",flat)]: n+=1
    return dict(seed=seed,cases=cases,readable=n,seconds=round(time.time()-t,1))
# 200,000-key check
sys.path.append(WT)
def keycheck(n=200000,seed=5):
    from hadavin_sdk.k1b import redaction as R
    from tests import q8b_older_rule as older
    rng=random.Random(seed)
    W=["password","passwd","pwd","pass","secret","token","api","key","apikey","credential","credentials","authorization","bearer","private","session","auth","oauth","new","old","db","root","user","my","x","cookie","id","type","count","max","enabled","policy","author","bypass","compass","tokens","name","value","data","client","access","account","sas","cert","jsessionid","connect","sid","passphrase","Password","Token","Secret","ApiKey","2","1","0"]
    SEP=["_","-",".","", " "]
    tried=acc=refused=0; ex=[]
    for _ in range(n):
        k=rng.choice(SEP).join(rng.choice(W) for _ in range(rng.randint(1,4)))
        tried+=1
        if older.record_key_masked(k):
            acc+=1
            if not R.sensitive(k): refused+=1; ex.append(k) if len(ex)<10 else None
    return dict(tried=tried,accepted_by_main_rule=acc,refused_by_this_code=refused,examples=ex)
which=sys.argv[2:] or ["keycheck","p1","p2","n9"]
for w in which:
    print(w, json.dumps({"keycheck":keycheck,"p1":p1,"p2":p2,"n9":n9}[w](),ensure_ascii=False), flush=True)
