import subprocess,sys,shutil,os,re
src=sys.argv[1]  # tree with patch applied
PY="/tmp/work/rv38-x/v312/bin/python"
A_OLD=r'''_ADDRESS = re.compile(r"(?<![^\s,;:<>\"'])[^\s,;:<>\"'][^\s,;:<>\"'@]*@[^\s,;<>\"']+")'''
M_NEW=open(src+"/tools/scrub_n8n_export.py").read()
a=M_NEW.index("MAIL = re.compile(");b=M_NEW.index("REPLACEMENT_URL")
M_OLD=M_NEW[a:b]
def A(new): return ("scripts/run_real_check.py",A_OLD,new)
def M(old,new): 
    assert old in M_OLD,old
    return ("tools/scrub_n8n_export.py",M_OLD,M_OLD.replace(old,new,1))
muts={
 "A1 drop lookbehind": A(r'''_ADDRESS = re.compile(r"[^\s,;:<>\"'][^\s,;:<>\"'@]*@[^\s,;<>\"']+")'''),
 "A2 put @ back in repeated class": A(r'''_ADDRESS = re.compile(r"(?<![^\s,;:<>\"'])[^\s,;:<>\"'][^\s,;:<>\"']*@[^\s,;<>\"']+")'''),
 "A3 first char excludes @": A(r'''_ADDRESS = re.compile(r"(?<![^\s,;:<>\"'])[^\s,;:<>\"'@][^\s,;:<>\"'@]*@[^\s,;<>\"']+")'''),
 "A4 domain excludes @": A(r'''_ADDRESS = re.compile(r"(?<![^\s,;:<>\"'])[^\s,;:<>\"'][^\s,;:<>\"'@]*@[^\s,;<>\"'@]+")'''),
 "A5 domain also excludes colon": A(r'''_ADDRESS = re.compile(r"(?<![^\s,;:<>\"'])[^\s,;:<>\"'][^\s,;:<>\"'@]*@[^\s,;:<>\"']+")'''),
 "A6 domain may be empty (+ -> *)": A(r'''_ADDRESS = re.compile(r"(?<![^\s,;:<>\"'])[^\s,;:<>\"'][^\s,;:<>\"'@]*@[^\s,;<>\"']*")'''),
 "A7 lookbehind uses domain class": A(r'''_ADDRESS = re.compile(r"(?<![^\s,;<>\"'])[^\s,;:<>\"'][^\s,;:<>\"'@]*@[^\s,;<>\"']+")'''),
 "A8 local part may be empty (first char optional)": A(r'''_ADDRESS = re.compile(r"(?<![^\s,;:<>\"'])[^\s,;:<>\"']?[^\s,;:<>\"'@]*@[^\s,;<>\"']+")'''),
 "A9 local drops quote from class": A(r'''_ADDRESS = re.compile(r"(?<![^\s,;:<>\"'])[^\s,;:<>\"'][^\s,;:<>\"'@]*@[^\s,;<>\"']+".replace("\\\"'", "\\\""))'''),
 "A10 positive lookbehind": A(r'''_ADDRESS = re.compile(r"(?<=[\s,;:<>\"'])[^\s,;:<>\"'][^\s,;:<>\"'@]*@[^\s,;<>\"']+")'''),
 "A11 domain drops semicolon": A(r'''_ADDRESS = re.compile(r"(?<![^\s,;:<>\"'])[^\s,;:<>\"'][^\s,;:<>\"'@]*@[^\s,<>\"']+")'''),
 "A12 lazy local": A(r'''_ADDRESS = re.compile(r"(?<![^\s,;:<>\"'])[^\s,;:<>\"'][^\s,;:<>\"'@]*?@[^\s,;<>\"']+")'''),
 "M1 drop lookbehind": M("(?<![\\w.%+-])",""),
 "M2 local first char class loses +": M("[\\w.%+-][\\w.%+-]*+","[\\w.%][\\w.%+-]*+"),
 "M3 full-width @ removed": M("[@\\uFF20]","[@]"),
 "M4 drop 'invalid'": M("|invalid","",),
 "M5 drop guard in label (?!example..)": M('(?:(?!example\\.(?:com|test|invalid)(?![\\w-]|\\.[\\w-]))[\\w-]++\\.)*+','(?:[\\w-]++\\.)*+'),
 "M6 drop end guard after allowed name (inner)": M('example\\.(?:com|test|invalid)(?![\\w-]|\\.[\\w-]))"\n    r"[\\w.-]++','example\\.(?:com|test|invalid))"\n    r"[\\w.-]++'),
 "M7 domain class loses dash": M('r"[\\w.-]++"','r"[\\w.]++"'),
 "M8 domain + instead of ++ AND no change (equiv)": M('r"[\\w.-]++"','r"[\\w.-]+"'),
 "M9 negative lookahead -> positive": M("[@\\uFF20]\"\n    r\"(?!","[@\\uFF20]\"\n    r\"(?="),
 "M10 allowed ending (?![\\w-]|\\.[\\w-]) -> (?![\\w-])": M("(?![\\w-]|\\.[\\w-])","(?![\\w-])"),
 "M11 label ++ -> + (equivalent expected)": M("[\\w-]++\\.)*+","[\\w-]+\\.)*+"),
 "M12 group *+ -> * (equivalent expected)": M("\\.)*+example","\\.)*example"),
 "M13 local possessive -> greedy (equivalent expected)": M("[\\w.%+-]*+[@","[\\w.%+-]*[@"),
 "M14 domain min 0 (++ -> *+)": M('r"[\\w.-]++"','r"[\\w.-]*+"'),
 "M15 allowed list adds 'org'": M("com|test|invalid","com|test|invalid|org"),
 "M15b allowed list adds 'org' in BOTH places": ("tools/scrub_n8n_export.py",M_OLD,M_OLD.replace("com|test|invalid","com|test|invalid|org")),
 "M15c allowed list adds 'org' in the final place only": ("tools/scrub_n8n_export.py",M_OLD,M_OLD[::-1].replace("com|test|invalid"[::-1],"com|test|invalid|org"[::-1],1)[::-1]),
 "M16 allowed list adds 'net' in both places": ("tools/scrub_n8n_export.py",M_OLD,M_OLD.replace("com|test|invalid","com|test|invalid|net")),
 "M6b drop end guard in BOTH places": ("tools/scrub_n8n_export.py",M_OLD,M_OLD.replace("(?![\\w-]|\\.[\\w-])","")),
 "M6c drop end guard in the final place only": ("tools/scrub_n8n_export.py",M_OLD,M_OLD[::-1].replace("(?![\\w-]|\\.[\\w-])"[::-1],"",1)[::-1]),
 "M10b allowed ending (?![\\w-]) only in BOTH places": ("tools/scrub_n8n_export.py",M_OLD,M_OLD.replace("(?![\\w-]|\\.[\\w-])","(?![\\w-])")),
 "M10c allowed ending (?![\\w-]) only in the final place": ("tools/scrub_n8n_export.py",M_OLD,M_OLD[::-1].replace("(?![\\w-]|\\.[\\w-])"[::-1],"(?![\\w-])"[::-1],1)[::-1]),
}
res=[]
for name,(f,old,new) in muts.items():
    d="/tmp/work/og/mt"; shutil.rmtree(d,ignore_errors=True); shutil.copytree(src,d,ignore=shutil.ignore_patterns(".git"))
    p=d+"/"+f; t=open(p).read(); assert old in t; open(p,"w").write(t.replace(old,new,1))
    r=subprocess.run([PY,"-m","pytest","-q","-x","-p","no:cacheprovider","tests/test_sonar_p2_optional_gaps.py"],cwd=d,capture_output=True,text=True,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
    last=[l for l in r.stdout.splitlines() if l.strip()][-1]
    k=[l for l in r.stdout.splitlines() if l.startswith("FAILED")]
    print(("KILLED  " if r.returncode else "SURVIVED"),name,"|",last,"|",(k[0][:110] if k else ""),flush=True)
