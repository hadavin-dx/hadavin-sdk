import os, subprocess, sys
from pathlib import Path
R=Path("/tmp/work/nm4"); PY="/tmp/work/rv18-1/v/bin/python"
ENV=dict(os.environ,GITLEAKS_BIN="/tmp/work/gl/gitleaks",DPLD_REQUIRE_SCAN="1")
F=["tests/test_hygiene.py","tests/test_no_placeholders.py"]
def run(cwd):
    r=subprocess.run([PY,"-u","-m","pytest","-q","-p","no:cacheprovider",*F],cwd=cwd,env=ENV,capture_output=True,text=True)
    l=[x for x in r.stdout.strip().splitlines() if x.strip()]; return l[-1] if l else "(none) "+r.stderr[-200:]
RR="tests/_repo_root.py"; TH="tests/test_hygiene.py"
M=[("O1 helper never skips",RR,'if not (REPO / ".git").exists():',"if False:"),
("O2 _git does not call helper",TH,"    need_git_work_tree_for(cwd)\n",""),
("O3 scan test does not call helper",TH,"    need_git_work_tree()  # the canaries","    pass  # the canaries"),
("O4 .git must be a dir",RR,'(REPO / ".git").exists()','(REPO / ".git").is_dir()'),
("O5 REPO one level too low",RR,"Path(__file__).resolve().parent.parent","Path(__file__).resolve().parent"),
("O6 helper inverted",RR,'if not (REPO / ".git").exists():','if (REPO / ".git").exists():'),
("O7 _git skips for any folder",RR,"    if cwd == REPO:\n        need_git_work_tree()","    need_git_work_tree()"),
("O8 .git must be a file",RR,'(REPO / ".git").exists()','(REPO / ".git").is_file()'),
("O9 _git skips only for OTHER folders",RR,"if cwd == REPO:","if cwd != REPO:"),
]
for n,f,o,nw in M:
    print(n)
    for lab,d in (("B git copy, demo deleted","B"),("C no-.git copy","C")):
        p=R/d/f; s=p.read_text(); assert o in s,o; p.write_text(s.replace(o,nw,1))
        try: print("   ",lab,":",run(R/d))
        finally: p.write_text(s)
    sys.stdout.flush()
