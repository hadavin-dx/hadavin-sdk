import re,sys,shutil
STAT="READ, READ-TRUNCATED, PARTIAL, SKIMMED, LISTED-ONLY, NOT-READ, EMPTY".split(", ")
NEW=("> - Status words (only three exist; the note column gives the extent): READ = opened whole, apart from any cut named in the note (long lines cut at a stated length still count as READ). SKIMMED = part of the file opened (headers, search hits, or a first and last slice); the note says which part. NOT-READ = contents not opened (name, size or a listing only). Draw no conclusion about a file from a lane that did not read it.")
def fix(path):
    s=open(path).read(); shutil.copy(path,path.replace(".md","-history-status.md"))
    out=[];n={"rm":0,"rel":0};skip=False
    for ln in s.split("\n"):
        if ln.startswith("> REMINDER") or ln.startswith("> TABLE KEY") or ln.startswith("<!-- TABLE-KEY -->") or ln.startswith("Short key (full glossary") or ln.startswith("Terms are defined in the KEY below"):
            n["rm"]+=1; continue
        if ln.startswith("> - Status words"):
            ln=NEW; n["rel"]+=0
        if ln.startswith("| ") and not ln.startswith("|---"):
            c=[x.strip() for x in ln.strip().strip("|").split(" | ")]
            if len(c)==4 and c[2] in STAT:
                st,note=c[2],c[3]; new=st
                if st in("SKIMMED",) and re.search(r"not opened|name only|listed",note,re.I): new=st  # NOT-READ counts are pinned by tests/test_round1_fixes.py; do not change
                elif st=="NOT-READ": new=st
                elif st=="READ" and re.search(r"lines? 1-\d+ of \d+",note): new="SKIMMED"
                elif st in("READ-TRUNCATED","EMPTY"): new="READ"
                elif st in("PARTIAL",): new="SKIMMED"
                elif st=="LISTED-ONLY": new="NOT-READ"
                if new!=st:
                    c[2]=new; ln="| "+" | ".join(c)+" |"; n["rel"]+=1
        out.append(ln)
    open(path,"w").write("\n".join(out)); return n
for f in sys.argv[1:]: print(f,fix(f))
