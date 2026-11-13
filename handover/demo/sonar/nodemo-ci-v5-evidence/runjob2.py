import sys, os, subprocess, yaml, time, shutil, tempfile
repo = sys.argv[1]; venv = sys.argv[2]; wf = sys.argv[3] if len(sys.argv)>3 else repo+"/.github/workflows/nodemo.yml"
skip_install = True
d = yaml.safe_load(open(wf))
job = d["jobs"]["no-demo"]
rt = os.path.join(repo, "..", "rt-"+os.path.basename(repo)); rt=os.path.abspath(rt)
shutil.rmtree(rt, ignore_errors=True); os.makedirs(rt+"/gitleaks")
shutil.copy("/tmp/work/gl/gitleaks", rt+"/gitleaks/gitleaks")
base = dict(os.environ); base["PATH"] = venv+"/bin:"+base["PATH"]; base["RUNNER_TEMP"]=rt
for k,v in job.get("env",{}).items(): base[k]=str(v)
base["VIRTUAL_ENV"]=venv
for st in job["steps"]:
    if "run" not in st: continue
    name = st.get("name","?")
    if name.startswith("Install") or (os.environ.get("NORUFF") and name.startswith("Ruff")): print("SKIP", name); continue
    env = dict(base)
    for k,v in st.get("env",{}).items(): env[k]=str(v).replace("${{ runner.temp }}", rt).replace("${{ github.event.before }}", os.environ.get("TEST_BEFORE",""))
    f = tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False); f.write(st["run"]); f.close()
    t=time.time()
    print("=== STEP", name, flush=True)
    r = subprocess.run(["bash","-e",f.name], cwd=repo, env=env)
    print(f"=== STEP rc={r.returncode} {time.time()-t:.0f}s", flush=True)
    if r.returncode: print("RESULT RED"); sys.exit(1)
print("RESULT GREEN")
