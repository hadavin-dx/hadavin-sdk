import subprocess, shutil, os, sys, re
ROOT="/tmp/work/sn-v5"; PY=ROOT+"/venv/bin/python"
FILES=["tests/test_client_copy.py","tests/test_raw_bidi_chars.py","tests/test_no_placeholders.py","tests/test_nosemgrep_form.py","tests/test_shell_single_bracket.py","tests/test_demo_folder_guard.py","tests/test_hygiene.py"]
SEL=["-k","not gitleaks and not term_scan and not sh_blobs_has and (client_copy or raw_bidi or no_placeholders or nosemgrep or shell_single or demo_folder or scan_public or control_char or sh_blobs_no_cr or secret_scan_files or hygiene)"]
def run(copy, env_extra, tests):
    env={k:v for k,v in os.environ.items() if not k.startswith("DPLD_")}
    env["PATH"]="/tmp/work/gl:"+env["PATH"]; env.update(env_extra)
    p=subprocess.run([PY,"-u","-m","pytest","-q","-p","no:cacheprovider",*tests],cwd=ROOT+"/"+copy,env=env,capture_output=True,text=True)
    last=[l for l in p.stdout.splitlines() if re.search(r"\d+ (passed|failed|skipped)",l)]
    return (last[-1] if last else "NO RESULT "+p.stdout[-200:]).strip()
def sub(text, a, b):
    assert a in text, a
    return text.replace(a,b,1)
M={
"M1 gap never reported": ("tests/_repo_root.py", lambda t: sub(t,"    why = _scan_gap(repo or REPO)\n","    why = None\n")),
"M2 .git presence only": ("tests/_repo_root.py", lambda t: sub(t,'    if p.returncode != 0:','    if (repo / ".git").exists():\n        return None\n    if p.returncode != 0:')),
"M3 scan_required always false": ("tests/_repo_root.py", lambda t: sub(t,"return bool(os.environ.get(REQUIRE_SCAN_ENV))","return False")),
"M4 scan_required always true": ("tests/_repo_root.py", lambda t: sub(t,"return bool(os.environ.get(REQUIRE_SCAN_ENV))","return True")),
"M5 no skip mark": ("tests/conftest.py", lambda t: sub(t,"            item.add_marker(pytest.mark.skip(reason=gap))","            pass")),
"M6 no failure under CI setting": ("tests/conftest.py", lambda t: sub(t,"    if scan_required() and _is_scan_test(item)","    if False and _is_scan_test(item)")),
"M7 REPO from cwd": ("tests/_repo_root.py", lambda t: sub(t,"REPO = Path(__file__).resolve().parent.parent","REPO = Path.cwd()")),
"M8 scan guard before the canaries": ("tests/test_hygiene.py", lambda t: sub(sub(t,"    # 2. the real tree\n    if gap := repo_scan_gap():","    # 2. the real tree\n    if False:"),"def test_hygiene_scan_public(tmp_path: Path) -> None:\n","def test_hygiene_scan_public(tmp_path: Path) -> None:\n    if gap := repo_scan_gap():\n        (pytest.fail if scan_required() else pytest.skip)(gap)\n")),
"M9 leftover support import in test_no_placeholders (P9)": ("tests/test_no_placeholders.py", lambda t: sub(t,"from support import REPO","from support import REPO, build_rig")),
"M10 support import with a rig in test_hygiene (P10)": ("tests/test_hygiene.py", lambda t: sub(t,"from _repo_root import REPO,","from support import build_rig  # noqa\nfrom _repo_root import REPO,")),
"M11 _needs_demo always true": ("tests/conftest.py", lambda t: sub(t,'    text = path.read_text(encoding="utf-8")\n    if _ENV_NEEDING','    return True\n    text = path.read_text(encoding="utf-8")\n    if _ENV_NEEDING')),
"M12 _needs_demo always false": ("tests/conftest.py", lambda t: sub(t,'    text = path.read_text(encoding="utf-8")\n    if _ENV_NEEDING','    return False\n    text = path.read_text(encoding="utf-8")\n    if _ENV_NEEDING')),
"M13 DEMO_BOUND_NAMES empty": ("tests/support.py", lambda t: sub(t,'DEMO_BOUND_NAMES: Final = frozenset({"DEMO_LEADFLOW", "build_rig"})','DEMO_BOUND_NAMES: Final = frozenset()')),
"M14 support imports demo_only at the top": ("tests/support.py", lambda t: sub(t,"from _repo_root import REPO\n","from _repo_root import REPO\nimport demo_only.fakes\n")),
"M15 registry drops raw_bidi": ("tests/_repo_root.py", lambda t: sub(t,'        ("test_raw_bidi_chars.py", "test_no_tracked_file_holds_a_raw_direction_control_character"),\n','')),
"M16 marker check removed (any listing passes)": ("tests/_repo_root.py", lambda t: sub(t,"    if p.stdout.strip() != MARKER:","    if False:")),
"M17 skip and fail swapped": ("tests/test_hygiene.py", lambda t: sub(t,"(pytest.fail if scan_required() else pytest.skip)(gap)","(pytest.skip if scan_required() else pytest.fail)(gap)")),
"M18 import inside function counts": ("tests/conftest.py", lambda t: sub(t,"        if id(node) in inner:\n            continue\n","")),
}
only=sys.argv[1:]
cases=[("B",{"DPLD_REQUIRE_SCAN":"1"}),("C",{}),("C",{"DPLD_REQUIRE_SCAN":"1"})]
tests=FILES[:]
def tt(): return ["tests/"+os.path.basename(f) for f in FILES]
base={}
for i,(copy,e) in enumerate(cases):
    base[i]=run(copy,e,tt()+SEL)
    print("BASELINE",copy,e,"->",base[i],flush=True)
for name,(f,fn) in M.items():
    if only and not any(name.startswith(o) for o in only): continue
    outs=[]
    for copy in ("B","C"):
        p=ROOT+"/"+copy+"/"+f; orig=open(p).read()
        open(p,"w").write(fn(orig))
    try:
        for i,(copy,e) in enumerate(cases):
            r=run(copy,e,tt()+SEL); outs.append((r,r!=base[i]))
    finally:
        for copy in ("B","C"):
            p=ROOT+"/"+copy+"/"+f; open(p,"w").write(open(ROOT+"/S/"+f).read())
    killed=any(k for _,k in outs)
    print(("KILLED  " if killed else "SURVIVED"),name,"|"," | ".join(f"{c}{'+req' if e else ''}: {r}" for (c,e),(r,_) in zip(cases,outs)),flush=True)
