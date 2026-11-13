import subprocess,shutil,os
src="/tmp/work/sn-og"; PY="/tmp/work/rv38-x/v312/bin/python"
URLLINE='    url = f"{desk_origin(target_host(cfg.bind), cfg.port)}/leads"  # from the configuration only\n'
PARSE='    args = ap.parse_args(argv)\n'
M={
"F1 re-add --url option with config default":(PARSE,'    ap.add_argument("--url", default=f"{desk_origin(target_host(cfg.bind), cfg.port)}/leads")\n'+PARSE+'    args.url = args.url\n'),
"F2 --url accepted via parse_known_args":(PARSE,'    args, _ignored = ap.parse_known_args(argv)\n'),
"F3 hidden --url (SUPPRESS) used":(PARSE,'    ap.add_argument("--url", default=None, help=argparse.SUPPRESS)\n'+PARSE),
"F4 url uses getattr(args,'url')":(URLLINE,'    url = getattr(args, "url", None) or f"{desk_origin(target_host(cfg.bind), cfg.port)}/leads"\n'),
"F5 new --host option overrides host (OTHER OPTION)":(URLLINE,'    url = f"{desk_origin(args.host or target_host(cfg.bind), cfg.port)}/leads"\n'),
"F6 skip target_host (raw bind)":(URLLINE,'    url = f"{desk_origin(cfg.bind, cfg.port)}/leads"\n'),
"F7 port hardcoded":(URLLINE,'    url = f"{desk_origin(target_host(cfg.bind), 8765)}/leads"\n'),
"F8 literal address":(URLLINE,'    url = "http://127.0.0.1:8765/leads"\n'),
"F9 wrong path":(URLLINE,'    url = f"{desk_origin(target_host(cfg.bind), cfg.port)}/lead"\n'),
"F10 config ignored (always default bind)":("    cfg = Config.from_env()\n","    cfg = Config()\n"),
"F11 url built before parse (equivalent)":(URLLINE,''),
"F12 url from --source (argument into address)":(URLLINE,'    url = f"{desk_origin(target_host(cfg.bind), cfg.port)}/leads?{args.source}"\n'),
"F13 docstring line dropped (doc only; equivalent)":("not from the command\nline: there is no option to point the request anywhere else.","not from this file."),
"F14 add_argument('--url') with required=False store_true":(PARSE,'    ap.add_argument("--url", action="store_true")\n'+PARSE),
}
for name,(old,new) in M.items():
    d="/tmp/work/og/mf"; shutil.rmtree(d,ignore_errors=True); shutil.copytree(src,d,ignore=shutil.ignore_patterns(".git"))
    p=d+"/scripts/feed.py"; t=open(p).read()
    if old not in t: print("SKIP(no match)",name); continue
    if name.startswith("F11"):
        t=t.replace(old,""); t=t.replace(PARSE,URLLINE+PARSE)
    else: t=t.replace(old,new,1)
    open(p,"w").write(t)
    r=subprocess.run([PY,"-m","pytest","-q","-x","-p","no:cacheprovider","tests/test_sonar_p2_optional_gaps.py"],cwd=d,capture_output=True,text=True,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
    k=[l for l in r.stdout.splitlines() if l.startswith("FAILED")]
    print(("KILLED  " if r.returncode else "SURVIVED"),name,"|",(k[0][:100] if k else r.stdout.strip().splitlines()[-1]),flush=True)
