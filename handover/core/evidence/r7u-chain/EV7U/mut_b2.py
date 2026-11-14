"""R7U-B mutant runner: one runner, one mutant at a time, in place in tree-R7U-B; each file is restored from
out/EV7U/final/ and compared byte for byte after every mutant. Usage: mut_b.py <results.tsv> [ids...]"""
import filecmp, os, shutil, subprocess, sys
R="/home/user/build/rr6/"; O=R+"out/EV7U/"; M=O+"mutB/"; S=R+"tree-R7U/"; TMP=O+"tmp-mut"; os.makedirs(TMP,exist_ok=True)
RR="scripts/run_real_check.py"; RL="src/lead_desk/loopback.py"; FK="demo_only/fakes_server.py"
T="tests/test_r7u_b_findings.py"
KNOWN='return read.files > 0 and read.unreadable == 0 and "sent" in read.totals'
RD='smtp_read = read_counter_files_checked(run_dir, ".smtp.json", tag)'
muts=[
("B01",RR,KNOWN,KNOWN.replace("read.files > 0","read.files >= 0"),"rule or no-file"),
("B02",RR,KNOWN,KNOWN.replace("read.unreadable == 0","True"),"rule or one_unreadable or cut_in_half or only-unreadable"),
("B03",RR,KNOWN,KNOWN.replace('"sent" in read.totals','True'),"rule or no_sent"),
("B04",RR,KNOWN,KNOWN.replace("read.files > 0 and","read.files > 0 or"),"rule"),
("B05",RR,KNOWN,KNOWN.replace("read.unreadable == 0","read.unreadable < 2"),"rule or one_unreadable"),
("B06",RR,KNOWN,KNOWN.replace('"sent" in','"attempts" in'),"rule or readable_mail_counter"),
("B07",RR,"    smtp_stats = smtp_read.totals if smtp_known else {}","    smtp_stats = smtp_read.totals","one_unreadable or only-unreadable"),
("B08",RR,"    smtp_known = smtp_counter_is_known(smtp_read)","    smtp_known = True","one_unreadable or cut_in_half"),
("B09",RR,RD,RD.replace(".smtp.json",".hubspot.json"),"readable_mail_counter"),
("B10",RR,RD,RD.replace(".smtp.json",".smtp.jsonx"),"readable_mail_counter"),
("B11",RR,"    if not smtp_known:  # fail closed","    if False:  # fail closed","in_words"),
("B12",RR,"    smtp_stats = smtp_read.totals if smtp_known else {}","    smtp_stats = smtp_read.totals if smtp_known else {'sent': 0}","one_unreadable or only-unreadable or no-file"),
("B13",RL,'    if name.lower() == "localhost":','    if name == "localhost":',"b8_the_rule"),
("B14",FK,'Config().fakes_host if host is None else host','Config().fakes_host',"b8"),
("B15",RL,'        ip = ip.ipv4_mapped  # the same answer','        pass  # the same answer',"b8_the_rule"),
("B16",RR,'return read.files > 0 and read.unreadable == 0 and "created" in read.totals','return read.files > 0 and "created" in read.totals',"b5_a_hidden"),
("B17",RR,'counter_known = counter_is_known(hub_read)','counter_known = True',"b5_a_hidden"),
]
only=sys.argv[2:]
out=open(O+sys.argv[1],"a")
for mid,f,old,new,k in muts:
    if only and mid not in only: continue
    p=M+f; s=open(p,encoding="utf-8",newline="").read()
    if s.count(old)!=1 or old==new:
        out.write(f"{mid}\tNOT-APPLIED count={s.count(old)}\n"); out.flush(); continue
    open(p,"w",encoding="utf-8",newline="").write(s.replace(old,new))
    try:
        env=dict(os.environ,PYTHONPATH=M+"src",PYTHONDONTWRITEBYTECODE="1",TMPDIR=TMP,PATH=R+"bin:"+os.environ["PATH"],GITLEAKS_BIN=R+"bin/gitleaks",DPLD_REQUIRE_SCAN="1",DPLD_REQUIRE_DEMO="1",HOME=TMP)
        cmd=["unshare","-n","python3",R+"src-v6/drivers/lo_up-q4g.py",R+"venv-br/bin/python","-m","pytest","-q","-p","no:cacheprovider","-x","-k",k,T]
        try:
            r=subprocess.run(cmd,cwd=M,env=env,capture_output=True,text=True,timeout=900)
            res="KILLED" if r.returncode==1 else ("SURVIVED" if r.returncode==0 else "ERR rc=%d"%r.returncode)
            tail=r.stdout.strip().splitlines()[-1:]
            open(O+f"mutraw-{mid}.txt","w").write(r.stdout[-2000:])
        except subprocess.TimeoutExpired:
            res="TIMEOUT"; tail=[]
        out.write(f"{mid}\t{f}\t{k}\t{res}\t{tail}\n"); out.flush()
    finally:
        shutil.copyfile(S+f,p); same=filecmp.cmp(S+f,p,shallow=False)
        out.write(f"{mid}\trestored-byte-equal={same}\n"); out.flush()
