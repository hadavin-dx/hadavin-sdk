import re,subprocess,os,sys
W=os.path.dirname(os.path.abspath(__file__))
src=open(W+"/REPORT-c6t.orig.md",encoding="utf-8").read()
ev=W+"/handover/core-hardening/c6-skip-audit/evidence-c6t"
def sub(old,new,count=1,regex=False):
    def f(t):
        if regex:
            r,n=re.subn(old,new,t,count=count if count else 0)
            assert n,old; return r
        assert old in t,old
        return t.replace(old,new) if count==0 else t.replace(old,new,count)
    return f
def delline(pat):
    def f(t):
        L=t.split("\n"); i=[k for k,l in enumerate(L) if re.search(pat,l)]; assert i,pat; del L[i[0]]; return "\n".join(L)
    return f
M=[
("01 first 'Of the 94 rows' -> 93",sub("Of the 94 rows","Of the 93 rows")),
("02 ready 49 -> 48 (first)",sub("94 rows, 49 are ready","94 rows, 48 are ready")),
("03 36 apply on default -> 37",sub("36 apply on the default","37 apply on the default")),
("04 rows 23,58,59 -> 23,58,60",sub("(rows 23, 58, 59)","(rows 23, 58, 60)")),
("05 wave 1 85 -> 86 (first)",sub("85 wave 1 rows","86 wave 1 rows")),
("06 ORDERS example time: 18:00:00Z = 23:30:00 -> 23:00:00",sub("18:00:00Z = 23:30:00 IST","18:00:00Z = 23:00:00 IST")),
("07 swap IST sign: UTC + 5:30 -> UTC - 5:30 (title)",sub("IST = UTC + 5:30","IST = UTC - 5:30")),
("08 check time written time 17:46:03 -> 17:46:30 (first)",sub("17:46:03 UTC = 23:16:03 IST","17:46:30 UTC = 23:16:03 IST")),
("09 IST hour off by one for 17:50:39",sub("17:50:39 UTC = 23:20:39 IST","17:50:39 UTC = 22:20:39 IST")),
("10 stale 58 s in place of 60.1 (first)",sub("60.1 to 61.9","58.0 to 61.9")),
("11 60.1 -> 60.2 everywhere",sub("60.1 to 61.9","60.2 to 61.9",0)),
("12 card words 90 -> 91 (first)",sub("90 words, about 36 s","91 words, about 36 s")),
("13 card seconds 36 -> 38",sub("about 36 s, budget 40 s","about 38 s, budget 40 s")),
("14 74-word text -> 144-word",sub("74-word text","144-word text")),
("15 budget 40 s -> 45 s",sub("budget 40 s","budget 45 s")),
("16 lease 45-second -> 55-second (first)",sub("a 45-second setting","a 55-second setting")),
("17 recovery flow wakes every 30 -> 20 seconds",sub("wakes every 30 seconds","wakes every 20 seconds")),
("18 L-CARD default Yes -> No",sub("| L-CARD | Does the closing card stay as the last card of the video? | Yes. |","| L-CARD | Does the closing card stay as the last card of the video? | No. |")),
("19 L-SAVE default Yes -> No",lambda t:re.sub(r"(\| L-SAVE \| .*?\| )Yes\. \|",r"\1No. |",t,count=1,flags=0) if re.search(r"\| L-SAVE \| .*?\| Yes\. \|",t) else (_ for _ in ()).throw(AssertionError("19"))),
("20 drop definition: GATE line removed",delline(r"^- GATE = ")),
("21 drop definition: TIMES line removed",delline(r"^- TIMES are UTC")),
("22 drop definition: READY line removed",delline(r"^- READY = ")),
("23 drop definition CONTACT line",delline(r"^- CONTACT = ")),
("24 cite LRN14:149 -> LRN14:148 (first)",sub("LRN14:149","LRN14:148")),
("25 cite ORD:150 -> ORD:151",sub("ORD:150","ORD:151")),
("26 rows 6 -> 7 wait for owner failed runs",sub("6 wait for the owner's answer on failed runs (rows 53, 55, 62, 64, 66, 68)","7 wait for the owner's answer on failed runs (rows 53, 55, 62, 64, 66, 68)")),
("27 18 stand-in crash runs -> 17",sub("18 stand-in crash runs","17 stand-in crash runs")),
("28 weekday: 23 Nov Monday -> Tuesday (first)",lambda t:re.sub(r"Mon(day)? 23 Nov",lambda m:"Tue"+(m.group(1) or "")+" 23 Nov",t,count=1) if re.search(r"Mon(day)? 23 Nov",t) else (_ for _ in ()).throw(AssertionError("28"))),
("29 box 2,495 -> 2,496 (first)",sub("2,495","2,496")),
("30 13-minute alert delay -> 12-minute",sub("13-minute alert delay","12-minute alert delay")),
("31 (2 relayed runs) -> (3 relayed runs)",sub("(2 relayed runs)","(3 relayed runs)")),
("32 rows 90, 91 -> rows 90, 92",sub("(rows 90, 91 edit only","(rows 90, 92 edit only")),
("33 swap IST->UTC label in ORDERS line",sub("= 23:30:00 IST","= 23:30:00 UTC")),
("34 stale 'v30' as newest at check time (first)",sub("NEWEST OWNER SHEET VERSION NAMED IN THIS REPORT: v31","NEWEST OWNER SHEET VERSION NAMED IN THIS REPORT: v30")),
("35 NEWEST RELEASE NOTE v15 -> v14",sub("NEWEST RELEASE NOTE NAMED: v15","NEWEST RELEASE NOTE NAMED: v14")),
("36 key-shaped fake token inserted",lambda t:t.replace("L-ONEDB |","L-ONEDB sk-ant-api03-"+"A1b2C3d4E5f6G7h8I9j0"+" |",1)),
("37 AKIA-shaped inserted",lambda t:t.replace("L-ONEDB |","L-ONEDB AKIA"+"ABCDEFGHIJKLMNOP"+" |",1)),
("38 delete the L-ONEDB table row",delline(r"^\| L-ONEDB \|")),
("39 L-KILL default (a) -> (b)",sub("| (a). |","| (b). |")),
("40 section 1 row total: 'TOTAL' row count 94 -> 95 (last)",lambda t:(t.rsplit("94",1)[0]+"95"+t.rsplit("94",1)[1])),
]
res=[]
env=dict(os.environ)
for name,fn in M:
    try: t=fn(src)
    except AssertionError as e:
        res.append((name,"MUTATION-NOT-APPLIED",str(e)[:60])); continue
    assert t!=src
    p=W+"/mut.md"; open(p,"w",encoding="utf-8").write(t)
    r=subprocess.run(["python3","-B","-I","verify-c6t.py",p],cwd=ev,env=env,capture_output=True,text=True)
    nf=len(re.findall(r"^FAIL",r.stdout,re.M))
    res.append((name,"CAUGHT" if r.returncode!=0 else "MISSED",nf))
for r in res: print(*r,sep=" | ")
print("CAUGHT",sum(r[1]=="CAUGHT" for r in res),"MISSED",sum(r[1]=="MISSED" for r in res),"NOT-APPLIED",sum(r[1]=="MUTATION-NOT-APPLIED" for r in res))
