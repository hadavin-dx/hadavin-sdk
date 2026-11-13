import json,subprocess,sys,re
repo=sys.argv[1]
js=json.load(open(repo+'/cov.json'))
files=["load_tools/catcher.py","load_tools/check_invariants.py","load_tools/load_driver.py","scripts/n8n_api.py","tools/pathconfine.py","tools/scrub_n8n_export.py","src/lead_desk/server.py","src/lead_desk/urls.py"]
tot=[0,0]
for f in files:
    d=subprocess.run(['git','diff','-U0','61ded9e','--',f],cwd=repo,capture_output=True,text=True).stdout
    added=set()
    for m in re.finditer(r'^@@ -\S+ \+(\d+)(?:,(\d+))? @@',d,re.M):
        st=int(m.group(1)); n=int(m.group(2) or 1)
        added|=set(range(st,st+n))
    c=js['files'].get(f)
    if not c: print(f,'no data'); continue
    ex=set(c['executed_lines']); mi=set(c['missing_lines'])
    stm=added&(ex|mi)
    cov=stm&ex
    tot[0]+=len(cov); tot[1]+=len(stm)
    print(f"{f}: new executable {len(stm)}, covered {len(cov)}, missing {sorted(stm&mi)}")
print("total",tot)
