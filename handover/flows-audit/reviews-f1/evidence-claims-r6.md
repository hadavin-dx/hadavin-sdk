# Evidence: claims table round 6 (EVIDENCE RUNNER, raw, no judgement)
Run 2026-11-16, cwd handover/flows-audit, python3 -I.

## 1. python3 -I claims-count.py CLAIMS-TABLE.md
```
verdicts: {'UNSUPPORTED': 29, 'SUPPORTED': 126, 'UNTRACED': 51, 'OVERSTATED': 52, 'RELAYED-ONLY': 69} total 327
lanes (A, B incl. X): {'A': 97, 'B': 226, 'X': 4}
to-do rows: 84
offenders: 0 []
ids: 327 unique: 327
rc=0
```

## 2. python3 -I tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md
```
section '1': 38 rows
section '2': 17 rows
section '3': 56 rows
section '7': 41 rows
total rows: 152
claim ids marked UNSUPPORTED, OVERSTATED, DELETE or STALE in CLAIMS-TABLE.md: 78 | with no row here: ['B-016', 'B-019', 'B-038', 'B-088', 'B-092']
claim ids marked UNTRACED there: 50 | with no row here: 43 (scope: UNTRACED claims have no safe wording, so they get a row only when a file sentence had to change)
FAIL: claim ids missing
RESULT: FAIL
rc=1
```

## 3. own script (scratchpad own.py; to-do rows = lines before '# LANE A' starting '| <number> |'; tag must be the first thing in the note cell = second column from right)
```
import re,sys,collections
L=open(sys.argv[1],encoding='utf-8').read().split("\n")
rows=[];lane=set();laneall=[]
stop=next(i for i,l in enumerate(L) if l.startswith("# LANE A"))
for i,l in enumerate(L):
    m=re.match(r"\| (\d+) \|",l)
    if i<stop and m:
        c=l.strip().strip("|").split(" | ")
        rows.append((int(m.group(1)),i+1,c))
    m=re.match(r"\| (A-\d+|B-\d+|X-\d) \|",l)
    if m: laneall.append(m.group(1))
lane=set(laneall)
print("todo rows",len(rows),"cells!=11:",[(n,len(c)) for n,_,c in rows if len(c)!=11])
tags=collections.Counter();bad=[]
for n,ln,c in rows:
    note=c[-2] if len(c)>=2 else ""
    found=re.findall(r"\[(LIVE, TEXT ONLY|LIVE|OUT[^\]]*)\]",note)
    starts=re.match(r"\[(LIVE, TEXT ONLY|LIVE|OUT[^\]]*)\]",note)
    if len(found)!=1 or not starts: bad.append((n,found,bool(starts)))
    if found: tags[found[0]]+=1
print("tags",dict(tags));print("no/2 tags or not at start",bad)
nums=[n for n,_,_ in rows];d=[k for k,v in collections.Counter(nums).items() if v>1]
print("dup todo numbers",d,"missing in 1..max",[k for k in range(1,max(nums)+1) if k not in nums])
print("dup lane ids",[k for k,v in collections.Counter(laneall).items() if v>1],"lane ids",len(laneall))
used=set()
for n,ln,c in rows: used|=set(re.findall(r"\b(?:A-\d+|B-\d+|X-\d)\b",c[3]))
print("ids cited in col4:",len(used),"no lane row:",sorted(used-lane))
allcit=set()
for n,ln,c in rows: allcit|=set(re.findall(r"\b(?:A-\d+|B-\d+|X-\d)\b"," ".join(c)))
print("ids cited anywhere in todo:",len(allcit),"no lane row:",sorted(allcit-lane))
--- output
todo rows 84 cells!=11: []
tags {'LIVE, TEXT ONLY': 7, 'LIVE': 10, 'OUT OF THIS VIDEO': 67}
no/2 tags or not at start []
dup todo numbers [] missing in 1..max []
dup lane ids [] lane ids 327
ids cited in col4: 95 no lane row: []
ids cited anywhere in todo: 107 no lane row: []
rc=0
```

## 4. 10 cites (seed 6; script cites.py; file found by searching handover/ when the bare name is cited; raw)
```
cites in lane rows: 94
--- table line 596: cite N8N-ENV-PROBE.md:8 (opened ../../handover/demo/N8N-ENV-PROBE.md)
CLAIMED QUOTE: a build made under Node 22 and run under Node 24 crashed with 
SOURCE LINE  : - npm install of n8n run under Node 22 builds the native module isolated-vm for Node 22; starting under Node 24 then crashes ("Could not initialize the vm expression engine"). Fix that worked: `npm re
--- table line 521: cite n8n-tests/smtp_catcher.py:44 (opened ../../handover/demo/n8n-tests/smtp_catcher.py)
CLAIMED QUOTE: `smtp_catcher.py .drop = 1`
SOURCE LINE  :                 try: drop = int(open(FILE + ".drop").read().strip() or 0)                          # fault mode: accept the mail (stored above), then drop the connection without the acknowledgement; t
--- table line 350: cite n8n-flows-real-v5/mf-recovery.json:26 (opened ../../handover/flows-audit/tools/scratch/film-v5/mf-recovery.json)
CLAIMED QUOTE: real-v4 and v5 use 45 s, DESIGN-A-README says 120 s for its flows folder
SOURCE LINE  :     "query": "UPDATE mf_leads SET claimed_until=now() + interval '45 seconds', claim_token=gen_random_uuid()::text, attempts=attempts+1, updated_at=now() WHERE lead_key IN (SELECT lead_key FROM mf_lea
--- table line 350: cite n8n-flows-real-v4/mf-recovery.json:26 (opened ../../handover/flows-audit/tools/scratch/film-v5/mf-recovery.json)
CLAIMED QUOTE: real-v4 and v5 use 45 s, DESIGN-A-README says 120 s for its flows folder
SOURCE LINE  :     "query": "UPDATE mf_leads SET claimed_until=now() + interval '45 seconds', claim_token=gen_random_uuid()::text, attempts=attempts+1, updated_at=now() WHERE lead_key IN (SELECT lead_key FROM mf_lea
--- table line 507: cite stage_server.py:48 (opened ../../handover/demo/n8n-mainframe/stage_server.py)
CLAIMED QUOTE: | B-043 | PLAN:78 | "the stage journal stops the recovery flow from calling the model again after a kill that came after the model call and before the table upd
SOURCE LINE  :         with LK:
--- table line 494: cite stage_server.py:48 (opened ../../handover/demo/n8n-mainframe/stage_server.py)
CLAIMED QUOTE: asks the model once per lead
SOURCE LINE  :         with LK:
--- table line 387: cite mf.py:158 (opened ../../handover/demo/n8n-mainframe/mf.py)
CLAIMED QUOTE: | A-093 | P:51 | "Test: demo K3 (1 intake mail per lead) and K3B (0 intake mails per lead). n=20 each, lease 20 s. Alerts: 1 each, read from the per_lead alerts
SOURCE LINE  :     kill_case("K3B", "n8n killed after mail_sent was set, while the SMTP node was connecting (stand-in holds the greeting 6 s), mail NOT yet delivered", setup, lambda k: (lambda: smtp_conns() >= 1 and
--- table line 581: cite RUN-ON-LAPTOP.md:56 (opened ../../handover/demo/RUN-ON-LAPTOP.md)
CLAIMED QUOTE: lost = no final state in time (done, unknown, failed or review)
SOURCE LINE  : - lost = no final state in time (done, unknown, failed or review), or done without exactly 1 CRM row and 1 mail.
--- table line 701: cite n8n-skip-on-conflict.md:65 (opened ../../handover/demo/n8n-skip-on-conflict.md)
CLAIMED QUOTE: The two-step 
SOURCE LINE  : - The two-step "If Row Does Not Exist" then Insert made extra rows in 9 of 10 bursts for one id (1 row in one fresh burst; 2 to 10 rows in the other nine). I did not repeat this beyond the 10 bursts, 
--- table line 371: cite mf.py:158 (opened ../../handover/demo/n8n-mainframe/mf.py)
CLAIMED QUOTE: lane3 K3 = this page's K3B (killed after the mail left: unknown + 1 alert)
SOURCE LINE  :     kill_case("K3B", "n8n killed after mail_sent was set, while the SMTP node was connecting (stand-in holds the greeting 6 s), mail NOT yet delivered", setup, lambda k: (lambda: smtp_conns() >= 1 and
```

## 5. grep -c -E 'Round 4|Round 5|Round 6|TODO|limitation' CLAIMS-TABLE.md
```
0
grep exit=1 (1 = no match)
```
