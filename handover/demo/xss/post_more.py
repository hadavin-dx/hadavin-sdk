import json, urllib.request
def post(n,k,payload):
    env={"source":"form","source_ref":f"xss-{n}","payload":payload}
    r=urllib.request.Request("http://127.0.0.1:8765/leads",data=json.dumps(env).encode(),headers={"Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(r,timeout=10) as x: print(k,n,x.status,x.read().decode()[:160])
    except urllib.error.HTTPError as e: print(k,n,e.code,e.read().decode()[:160])
tests=[("g1-rlo-only","Eve‮txet"),("g2-zw-only","Zero​Width‍Name"),
 ("h1-len100","H"*100),("h2-len200","H"*200),("h3-len500","H"*500),("h4-len1000","H"*1000),
 ("h5-len120-spaced",("word "*24).strip())]
n=20
for k,v in tests:
    n+=1; post(n,k,{"name":v,"company":"Co "+k,"message":"msg","email":f"xss-{k}@example.test"})
# long hostile values in company and message (2000 chars) with a normal name
n+=1; post(n,"h6-longcompany-msg",{"name":"Long Fields","company":"L"*2000,"message":"M"*2000,"email":"xss-h6@example.test"})
n+=1; post(n,"h7-longunbroken-company",{"name":"Long Company","company":"U"*300,"message":"x","email":"xss-h7@example.test"})
n+=1; post(n,"l-hostile-company-msg-normal-name",{"name":"Normal Person","company":"<script>window.__xss=11</script><img src=x onerror=window.__xss=12>","message":'<svg onload="window.__xss=13"> "><iframe srcdoc="<script>parent.__xss=14</script>">',"email":"xss-l@example.test"})
