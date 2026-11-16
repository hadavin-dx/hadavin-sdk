import subprocess, shutil, sys, os
R="/home/user/build/q8a2-fb3/wt-old/src/hadavin_sdk/approvals/receiver.py"
H="/home/user/build/q8a2-fb3/receiver.head.py"
src=open(H).read()
muts={
 "hungup_never": ("hung_up = isinstance(sys.exception(), ConnectionError) and len(kinds) == 1","hung_up = False"),
 "hungup_always_for_conn": ("and len(kinds) == 1",""),
 "message_added": ('" while handling ".join(kinds),','" while handling ".join(kinds) + str(sys.exception()),'),
 "level_error_to_debug": ("logging.DEBUG if hung_up else logging.ERROR","logging.DEBUG"),
 "log_raw": ('_LOG.debug("%s", _plain(text, _MAX_LOG_CHARS))','_LOG.debug(text)'),
 "no_cut": ("text[:limit]","text"),
 "bool_ok": ("type(read_timeout_s) not in (int, float)","not isinstance(read_timeout_s, (int, float))"),
 "no_max": ("0 < read_timeout_s <= RECEIVER_READ_TIMEOUT_MAX_S","0 < read_timeout_s"),
}
env=dict(os.environ, PYTHONPATH="/home/user/build/q8a2-fb3/wt-old/src", UV_PROJECT_ENVIRONMENT="/home/user/build/venv-q8a2f2")
for k in ("AWS_ACCESS_KEY_ID","AWS_SECRET_ACCESS_KEY","AWS_CA_BUNDLE","ANTHROPIC_BASE_URL","GH_TOKEN","GITHUB_TOKEN","CLOUDSDK_AUTH_ACCESS_TOKEN","VAULT_TOKEN","VAULT_SECRET_ID"): env.pop(k,None)
try:
  for name,(a,b) in muts.items():
    assert src.count(a)==1,(name,src.count(a))
    open(R,"w").write(src.replace(a,b))
    r=subprocess.run(["uv","run","--all-extras","--group","test","--offline","pytest","-q","-p","no:cacheprovider","tests/test_q8a2_callback.py","-x","-q"],cwd="/home/user/build/q8a2-fb3/wt-old",env=env,capture_output=True,text=True)
    print(name,"KILLED" if r.returncode else "SURVIVED", r.stdout.strip().splitlines()[-1][:100])
finally:
  open(R,"w").write(src)
