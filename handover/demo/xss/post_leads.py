import json, urllib.request
cases = {
 "a": "<script>window.__xss=1</script>",
 "b": '<img src=x onerror="window.__xss=2">',
 "c": '<svg onload="window.__xss=3">',
 "d": '"><iframe srcdoc="<script>parent.__xss=4</script>">',
 "e": "javascript:window.__xss=5",
 "f": "'; DROP TABLE leads;--",
 "g": "Eve‮txet​zero‍width",
 "h": "H"*2000,
 "i": "{{7*7}} and ${7*7}",
 "j": "   ",
 "k": "Emoji \U0001F600 Person",
}
n=0
for k,v in cases.items():
    n+=1
    payload={"name":v,"company":v if k!="h" else "C"*50,"message":v,"email":f"xss-{k}@example.test"}
    if k=="e": payload["website"]="javascript:window.__xss=5"; payload["company"]="javascript:window.__xss=5"
    if k=="j": payload["name"]="   "
    env={"source":"form","source_ref":f"xss-{n}","payload":payload}
    r=urllib.request.Request("http://127.0.0.1:8765/leads",data=json.dumps(env).encode(),headers={"Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(r,timeout=10) as x: print(k,n,x.status,x.read().decode()[:160])
    except urllib.error.HTTPError as e: print(k,n,e.code,e.read().decode()[:160])
# a lead with hostile data only in company, to have a clean "everything hostile in message" variant: skip
