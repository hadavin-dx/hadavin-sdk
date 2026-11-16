import re,sys,shutil
for f in sys.argv[1:]:
    p=f+".md"; s=open(p).read(); shutil.copy(p,f+"-history-head.md")
    s2=re.sub(r"Old rows that say SKIMMED.*?mean READ-TRUNCATED\. ","",s,flags=re.S)
    c={k:len(re.findall(r"^\| [^|]* \| -?\d+ \| "+k+r" \|",s2,re.M)) for k in ("READ","SKIMMED","NOT-READ")}
    tot=sum(c.values())
    summ=("\nSUMMARY (counted from the coverage table by a script on 16 Nov 2026): this page lists %d files that lane %s looked at. READ (opened whole): %d. SKIMMED (only part, or only a listing, looked at): %d. NOT-READ (nothing of the contents looked at): %d. Treat everything marked SKIMMED or NOT-READ as unchecked. Findings are in the findings table further down the page and in merged-findings.md, cited by id. Which of these files lie on the scenes 1 to 4 path is NOT established by this lane: the lane listed what the brief gave it; the studio lead decides which findings matter for the take.\n")%(tot,f,c["READ"],c["SKIMMED"],c["NOT-READ"])
    if "SUMMARY (counted from" not in s2:
        s2=re.sub(r"(^# Lane[^\n]*\n)",lambda m:m.group(1)+summ,s2,count=1,flags=re.M)
    print(f,c,s2!=s); open(p,"w").write(s2)
