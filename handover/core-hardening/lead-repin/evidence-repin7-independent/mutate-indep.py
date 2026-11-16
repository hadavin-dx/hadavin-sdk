import sys,subprocess,os,re,time
src=open("v7.sh").read()
M=[
("m01 Bearer min 4->40","(Bearer)[[:space:]]+[^[:space:]<\"',;)]{4,}","(Bearer)[[:space:]]+[^[:space:]<\"',;)]{40,}"),
("m02 userinfo min 4->40","s#(://)[^:/@[:space:]]{4,}@#","s#(://)[^:/@[:space:]]{40,}@#"),
("m03 IDENTIFIED BY->BX","BY[[:space:]]+)(${STR}|[^[:space:];<]","BX[[:space:]]+)(${STR}|[^[:space:];<]"),
("m04 requirepass dropped from rootpw rule","(requirepass|masterauth|auth-pass|bindpw|rootpw)","(masterauth|auth-pass|bindpw|rootpw)"),
("m05 ghp min 10->100","(ghp|gho|ghs|ghu)_[A-Za-z0-9]{10,}","(ghp|gho|ghs|ghu)_[A-Za-z0-9]{100,}"),
("m06 AKIA 16->17","(AKIA|ASIA)[0-9A-Z]{16}/<masked>","(AKIA|ASIA)[0-9A-Z]{17}/<masked>"),
("m07 JWT eyJ 8->80","eyJ[A-Za-z0-9_-]{8,}","eyJ[A-Za-z0-9_-]{80,}"),
("m08 email rule TLD 2->20","([A-Za-z0-9-]+\\.)+[A-Za-z]{2,}/<email-masked>","([A-Za-z0-9-]+\\.)+[A-Za-z]{20,}/<email-masked>"),
("m09 STRONG drop token","|credential|token|apikey|","|credential|apikey|"),
("m10 PRE needs ==","PRE=\"[\\\"']?[]]?[[:space:]]*=\"","PRE=\"[\\\"']?[]]?[[:space:]]*==\""),
("m11 := rule broken","[[:space:]]*:=[[:space:]]*)(${STR}","[[:space:]]*:==[[:space:]]*)(${STR}"),
("m12 awk blob 24->240","if (n < 24) return (tok ~","if (n < 240) return (tok ~"),
("m13 umask 077->022","umask 077\n","umask 022\n"),
("m14 git hooksPath removed"," -c core.hooksPath=/dev/null",""),
("m15 git gpg.program removed"," -c gpg.program=/bin/false",""),
("m16 PEM ENCRYPTED removed","/-----BEGIN [A-Z ]*(PRIVATE|SECRET|ENCRYPTED)[A-Z ]*-----/{","/-----BEGIN [A-Z ]*(PRIVATE|SECRET)[A-Z ]*-----/{"),
("m17 curl -u rule: curl|wget|http -> curl","/(curl|wget|http)/I s/","/(curl)/I s/"),
("m18 Basic 16->160","[A-Za-z0-9+/=]{16,}#\\1 <masked>#Ig","[A-Za-z0-9+/=]{160,}#\\1 <masked>#Ig"),
("m19 cleanup path guard removed","  case $WORK in */lead-repin.??????) ;; *) return 0 ;; esac\n","\n"),
("m20 SQ single-quote string rule broken","SQ=\"'([^'\\\\\\\\]|\\\\\\\\.)*'\"","SQ=\"'x([^'\\\\\\\\]|\\\\\\\\.)*'\""),
("m21 xox rule 8->80","xox[abprs]-[A-Za-z0-9-]{8,}","xox[abprs]-[A-Za-z0-9-]{80,}"),
("m22 PWCMDS drop psql","|psql|","|"),
("m23 LC_ALL=C removed","LC_ALL=C; export LC_ALL","export LC_ALL"),
("m24 awk hex 16..23 rule flipped","? 1 : 0     # 16 to 23","? 0 : 0     # 16 to 23"),
]
dsh=sys.argv[1] if len(sys.argv)>1 else "dash"
only=sys.argv[2:] 
for name,a,b in M:
    if only and name.split()[0] not in only: continue
    c=src.count(a)
    if c==0: print(f"{name}: PLANT-FAILED (text not found)",flush=True); continue
    f=f"mut/{name.split()[0]}.sh"
    open(f,"w").write(src.replace(a,b))
    t=time.time()
    try:
        r=subprocess.run([dsh,f,"--self-test"],capture_output=True,text=True,env=dict(os.environ,TMPDIR=os.path.abspath("tmp_root")),timeout=400,errors="replace")
        out=r.stdout+r.stderr; rc=r.returncode
    except subprocess.TimeoutExpired as e:
        out="TIMEOUT"; rc="timeout"
    last=[l for l in out.splitlines() if l.startswith("SELF-TEST")][-1:] or [out[-120:].replace("\n"," | ")]
    verdict="KILLED" if rc!=0 else "SURVIVED"
    print(f"{name}: occurrences_replaced={c} {verdict} exit={rc} {last[0][:140]} ({time.time()-t:.0f}s)",flush=True)
