"""usage: job.py TREE [steps...]  extract run blocks, run under bash -e in TREE"""
import sys, os, subprocess, yaml, pathlib
tree=sys.argv[1]; want=sys.argv[2:] or ["Delete","Ruff","Tests"]
wf=yaml.safe_load(open(f"{tree}/.github/workflows/nodemo.yml"))
job=wf["jobs"]["no-demo"]
rt=f"/tmp/work/sn-v4-drv/rt-{pathlib.Path(tree).name}"; os.makedirs(rt,exist_ok=True)
base=dict(os.environ); base["PATH"]=os.environ.get("PYBIN","/tmp/work/rv29-1/v312/bin")+":/usr/local/bin:/usr/bin:/bin"
base["RUNNER_TEMP"]=rt; os.makedirs(rt+"/gitleaks",exist_ok=True); import shutil; shutil.copy("/tmp/work/gl/gitleaks",rt+"/gitleaks/gitleaks"); base.update(job["env"]); base.update({k[4:]:v for k,v in os.environ.items() if k.startswith("OVR_")}); base.pop("DPLD_REQUIRE_DEMO",None)
rcs={}
for s in job["steps"]:
    n=s.get("name","")
    if "run" not in s or not any(n.startswith(w) or w in n for w in want): continue
    env=dict(base)
    for k,v in s.get("env",{}).items(): env[k]=v.replace("${{ runner.temp }}",rt)
    p=pathlib.Path(rt)/"step.sh"; p.write_text(s["run"])
    r=subprocess.run(["bash","-e",str(p)],cwd=tree,env=env,capture_output=True,text=True)
    out=(r.stdout+r.stderr).splitlines()
    msg=[l for l in out if l.strip()][-1:] or ["<no output>"]
    print(f"RESULT job-step-rc={r.returncode} last-line={msg[0][:200]!r}",flush=True)
    summ=[l for l in out if l.startswith("TOTAL")]
    if summ: print(summ[0],flush=True)
    rcs[n]=r.returncode
    if r.returncode: break
sys.exit(max(rcs.values()) if rcs else 1)
