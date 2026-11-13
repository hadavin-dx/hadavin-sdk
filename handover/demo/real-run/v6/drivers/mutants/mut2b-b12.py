import subprocess, os
from pathlib import Path
root=Path(os.environ["ROOT"])
cases=[("P2b hubspot: no required check AND fallback to the vendor","src/lead_desk/crm_hubspot.py",[("if not env.get(\"DESK_HUBSPOT_BASE_URL\", \"\").strip():","if False:"),("kw: dict[str, Any] = {\"base_url\": env[\"DESK_HUBSPOT_BASE_URL\"]}","kw: dict[str, Any] = {\"base_url\": env.get(\"DESK_HUBSPOT_BASE_URL\") or \"https://api.hubapi.com\"}")]),
("P4b live: no required check AND fallback to the provider","src/lead_desk/config.py",[("if not e.get(\"DESK_LIVE_BASE_URL\", \"\").strip():","if False:"),("kw: dict[str, Any] = {\"base_url\": e[\"DESK_LIVE_BASE_URL\"]}","kw: dict[str, Any] = {\"base_url\": e.get(\"DESK_LIVE_BASE_URL\") or LIVE_DEFAULT_BASE_URL}")])]
for name,f,reps in cases:
    p=root/f; o=p.read_text()
    s=o
    for a,b in reps:
        assert a in s,(a); s=s.replace(a,b,1)
    p.write_text(s)
    try:
        r=subprocess.run([os.environ["RUN"],"/tmp/work/b12-harness/logm.txt","/tmp/work/fresh-venv5/bin/python","-m","pytest","-q","-x","-p","no:cacheprovider","tests/test_desk_address_required.py"],capture_output=True,text=True,timeout=600,env={"PATH":"/usr/bin:/bin"})
        print(name,"SURVIVED" if r.returncode==0 else "killed", r.stdout.strip().splitlines()[-1])
    finally: p.write_text(o)
