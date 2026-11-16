import os,shutil,subprocess,re,sys
SRC='/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
SCR='/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/mut/'
CHK=SRC+'check-v22.py'
need=['OWNER-SHEET-v22.md','OWNER-SHEET-v21.md','LEAD-RELEASE-NOTE-v6.md','LEAD-RELEASE-NOTE-v5.md','v22-OPEN-FOR-LEAD.md','v22-CHANGES.md','checkpoint-v22.md','evidence-v22/pointer-golden-v22.json','evidence-v22/check-v22-raw.txt']
banned_word='Context'+' '+'Lake'
def sub(f,old,new,count=1):
    return (f,old,new)
M=[
 ('M5b-unlisted-set-phrase(lowercase send)',[('OWNER-SHEET-v22.md','Read the usage page and report balance and money used.','Read the usage page and report balance and money used, then send "all done" to the lead.')]),
 ('M10b-wrong-price(notice line 0.27->0.28)',[('OWNER-SHEET-v22.md','Price per call: 0.27 (USD)   Expected total: 0.81','Price per call: 0.28 (USD)   Expected total: 0.81')]),
 ('M10c-wrong-price(expected total in message 0.81->0.82)',[('OWNER-SHEET-v22.md','Expected total: USD 0.81 (not a limit)','Expected total: USD 0.82 (not a limit)')]),
 ('M11b-bad-Open-pointer(single)',[('LEAD-RELEASE-NOTE-v6.md','(Open 51). 10.','(Open 91). 10.')]),
 ('M12b-placeholder(<run name>-><runname> in 5.1)',[('OWNER-SHEET-v22.md','`take-<run name>-a@example.com` (`-b@`','`take-<runname>-a@example.com` (`-b@`')]),
 ('M12c-placeholder(set phrase list <name>-><new name>)',[('OWNER-SHEET-v22.md','new run name <name>" (6.5)','new run name <new name>" (6.5)')]),
]
out=[]
for name,edits in M:
    d=SCR+name.split('(')[0]+'/'
    shutil.rmtree(d,ignore_errors=True)
    for f in need:
        os.makedirs(os.path.dirname(d+f),exist_ok=True); shutil.copy(SRC+f,d+f)
    applied=True
    for f,o,n in edits:
        t=open(d+f,encoding='utf-8').read()
        if t.count(o)!=1: applied=False; print('!! anchor count',t.count(o),'for',name,o[:50])
        open(d+f,'w',encoding='utf-8').write(t.replace(o,n,1))
    r=subprocess.run(['python3','-I',CHK],env={**os.environ,'V22_DIR':d},capture_output=True,text=True,timeout=60)
    probs=[l for l in r.stdout.splitlines() if l.startswith('PROBLEM:')]
    # banned word mutation: do not echo it
    print('%-62s applied=%s rc=%d problems=%d'%(name,applied,r.returncode,len(probs)))
    for p in probs[:4]: print('      '+p[:170])
    if r.returncode not in (0,1): print('   STDERR',r.stderr[-300:])
