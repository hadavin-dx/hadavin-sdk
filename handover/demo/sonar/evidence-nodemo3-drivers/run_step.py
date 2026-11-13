import os, subprocess, sys, yaml
wf, namepart, cwd, rt, py = sys.argv[1:6]
d = yaml.safe_load(open(wf)); job = d["jobs"]["no-demo"]
env = dict(os.environ); env.update({k: str(v) for k, v in job["env"].items()})
env["RUNNER_TEMP"] = rt
env["PATH"] = os.path.dirname(py) + ":" + env["PATH"]   # `python` = the venv's python
for s in job["steps"]:
    if namepart in s.get("name", ""):
        for k, v in s.get("env", {}).items():
            env[k] = str(v).replace("${{ runner.temp }}", rt)
        open(rt + "/step.sh", "w").write(s["run"])
        print("== step:", s["name"], "| bash -e (GitHub's default shell form `bash -e {0}`), no pipefail", flush=True)
        r = subprocess.run(["bash", "-e", rt + "/step.sh"], cwd=cwd, env=env)
        print("exit", r.returncode); sys.exit(r.returncode)
sys.exit("no step")
