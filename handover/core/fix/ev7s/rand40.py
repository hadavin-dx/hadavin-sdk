import filecmp, os, shutil, subprocess, sys, random
R="/home/user/build/rr6/"; O=R+"out/EV7S/"; M=O+"mutX/"; S=O+"tree-a/"; TMP=O+"tmp-mutX"; os.makedirs(TMP,exist_ok=True)
RR="scripts/run_real_check.py"; BR="demo_only/bad_request.py"; SUP="tests/support.py"; T="tests/test_r7s_findings.py"
muts=[
("R01",BR,'if not isinstance(host, str) or not is_loopback_host(host):','if not isinstance(host, str) and not is_loopback_host(host):',"s1"),
("R02",BR,'host = server_address[0] if isinstance(server_address, tuple) and server_address else None','host = server_address[0] if isinstance(server_address, tuple) else None',"s1"),
("R03",BR,'host = server_address[0] if isinstance(server_address, tuple) and server_address else None','host = server_address[0] if server_address else None',"s1"),
("R04",BR,'    daemon_threads = True\n','    daemon_threads = False\n',"s1 or quiet"),
("R05",BR,'raise ValueError(LOOPBACK_HOST_TEXT)','raise ValueError("")',"s1"),
("R06",BR,'super().__init__(server_address, request_handler_class, bind_and_activate)','super().__init__(server_address, request_handler_class, False)',"s1"),
("R07",BR,'isinstance(sys.exception(), CLIENT_GONE)','not isinstance(sys.exception(), CLIENT_GONE)',"quiet or gone or hang"),
("R08",BR,'if not isinstance(host, str) or not is_loopback_host(host):','if not isinstance(host, str) or is_loopback_host(host):',"s1"),
("R09",RR,'return max(0, (created or 0) - accounted)','return max(0, (created or 0) - accounted + 1)',"s3"),
("R10",RR,'return max(0, (created or 0) - accounted)','return max(0, (created or 1) - accounted)',"s3"),
("R11",RR,'return max(0, (created or 0) - accounted)','return min(0, (created or 0) - accounted)',"s3"),
("R12",RR,'return max(0, (created or 0) - accounted)','return (created or 0) - accounted',"s3"),
("R13",RR,'return 0 if ok and written and not left and not unseen else EXIT_FAILED','return 0 if ok and written and not left and not unseen else EXIT_STOPPED',"s3"),
("R14",RR,'return 0 if ok and written and not left and not unseen else EXIT_FAILED','return 0 if ok or written and not left and not unseen else EXIT_FAILED',"s3"),
("R15",RR,'return 0 if ok and written and not left and not unseen else EXIT_FAILED','return 0 if ok and not left and not unseen else EXIT_FAILED',"s3"),
("R16",RR,'return 0 if ok and written and not left and not unseen else EXIT_FAILED','return 0 if ok and written and not unseen else EXIT_FAILED',"s3"),
("R17",RR,'return 0 if ok and written and not left and not unseen else EXIT_FAILED','return 0 if written and not left and not unseen else EXIT_FAILED',"s3"),
("R18",RR,'(f"desk-{tag}-{label}.log" if tag else f"desk-{label}.log")','(f"desk-{tag}-{label}.log" if not tag else f"desk-{label}.log")',"s3"),
("R19",RR,'run_dir.glob(f"desk-{tag}-*{suffix}")','run_dir.glob(f"desk-{tag}*{suffix}")',"s3"),
("R20",RR,'run_dir.glob(f"desk-{tag}-*{suffix}")','run_dir.glob(f"desk-{tag}-*")',"s3"),
("R21",RR,'d1 = Desk(child_env, run_dir, port, "1", tag)','d1 = Desk(child_env, run_dir, port, "1")',"s3"),
("R22",RR,'d2 = Desk({**child_env}, run_dir, port, "2", tag)','d2 = Desk({**child_env}, run_dir, port, "2")',"s3"),
("R23",RR,'smtp_stats = read_counter_files(run_dir, ".smtp.json", tag)','smtp_stats = read_counter_files(run_dir, ".smtp.json", "")',"s3"),
("R24",RR,'unseen = contacts_not_accounted_for(hub_stats.get("created"), accounted)','unseen = contacts_not_accounted_for(hub_stats.get("created"), accounted + 1)',"s3"),
("R25",RR,'unseen = contacts_not_accounted_for(hub_stats.get("created"), accounted)','unseen = contacts_not_accounted_for(hub_stats.get("created", 0), 0)',"s3"),
("R26",RR,'return exit_code_of(result["ok"], written, left, unseen)','return exit_code_of(result["ok"], written, left, 0)',"s3"),
("R27",RR,'return exit_code_of(result["ok"], written, left, unseen)','return exit_code_of(result["ok"], True, left, unseen)',"s3"),
("R28",RR,'return exit_code_of(result["ok"], written, left, unseen)','return exit_code_of(result["ok"], written, [], unseen)',"s3"),
("R29",RR,'{unseen} contacts may be left in HubSpot','{unseen} contacts are fine in HubSpot',"s3"),
("R30",RR,'accounted = len(crm_pairs)\n','accounted = len(crm_pairs) + 1\n',"s3"),
("R31",RR,'        accounted = done + len(left)\n','        accounted = done + len(left) + 1\n',"s3"),
("R32",RR,'hub_stats = read_counter_files(run_dir, ".hubspot.json", tag)\n    smtp_stats','hub_stats = {}\n    smtp_stats',"s3"),
("R33",RR,'len(lead_ids), read_counter_files(run_dir, ".hubspot.json", tag))','len(lead_ids), read_counter_files(run_dir, ".hubspot.json", "x"))',"s3"),
("R34",SUP,'    if os.environ.get(REQUIRE_SCAN_ENV):','    if not os.environ.get(REQUIRE_SCAN_ENV):',"s6"),
("R35",SUP,'    pytest.skip(text)\n','    return None\n',"s6"),
("R36",SUP,'REQUIRE_SCAN_ENV: Final = "DPLD_REQUIRE_SCAN"','REQUIRE_SCAN_ENV: Final = "DPLD_REQUIRE_SCANX"',"s6"),
("R37",SUP,'pytest.fail(f"{text} ({REQUIRE_SCAN_ENV} is set: a skip here would hide the test)")','pytest.skip(f"{text} ({REQUIRE_SCAN_ENV} is set: a skip here would hide the test)")',"s6"),
("R38",SUP,'    text = "the openssl program is not installed, so no test certificate can be made"','    text = ""',"s6"),
("R39",SUP,'    if os.environ.get(REQUIRE_SCAN_ENV):','    if os.environ.get(REQUIRE_SCAN_ENV) == "1":',"s6"),
("R40",SUP,'    if os.environ.get(REQUIRE_SCAN_ENV):','    if os.environ.get(REQUIRE_SCAN_ENV, "1"):',"s6"),
]
only=sys.argv[1:]
out=open(O+"mut-results-rand40.tsv","a")
for mid,f,old,new,k in muts:
    if only and mid not in only: continue
    p=M+f; s=open(p,encoding="utf-8",newline="").read()
    if s.count(old)!=1:
        out.write(f"{mid}\tNOT-APPLIED count={s.count(old)}\n"); out.flush(); continue
    open(p,"w",encoding="utf-8",newline="").write(s.replace(old,new))
    try:
        env=dict(os.environ,PYTHONPATH=M+"src",PYTHONDONTWRITEBYTECODE="1",TMPDIR=TMP,PATH=R+"bin:"+os.environ["PATH"],GITLEAKS_BIN=R+"bin/gitleaks",DPLD_REQUIRE_SCAN="1",DPLD_REQUIRE_DEMO="1")
        if mid in ("R34","R35","R36","R37","R38","R39"): pass
        cmd=["unshare","-n","python",R+"src-v6/drivers/lo_up-q4g.py",R+"venv-br/bin/python","-m","pytest","-q","-p","no:cacheprovider","-x","-k",k,T]
        try:
            r=subprocess.run(cmd,cwd=M,env=env,capture_output=True,text=True,timeout=600)
            res="KILLED" if r.returncode==1 else ("SURVIVED" if r.returncode==0 else "ERR rc=%d"%r.returncode)
            tail=r.stdout.strip().splitlines()[-1:]
            open(O+f"mutraw-rand-{mid}.txt","w").write(r.stdout[-2000:])
        except subprocess.TimeoutExpired:
            res="TIMEOUT"; tail=[]
        out.write(f"{mid}\t{f}\t{k}\t{res}\t{tail}\n"); out.flush()
    finally:
        shutil.copyfile(S+f,p); same=filecmp.cmp(S+f,p,shallow=False)
        out.write(f"{mid}\trestored-byte-equal={same}\n"); out.flush()
