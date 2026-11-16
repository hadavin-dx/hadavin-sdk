import os,shutil,subprocess,re,sys
SRC='/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
SCR='/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/mut/'
CHK=SRC+'check-v22.py'
need=['OWNER-SHEET-v22.md','OWNER-SHEET-v21.md','LEAD-RELEASE-NOTE-v6.md','LEAD-RELEASE-NOTE-v5.md','v22-OPEN-FOR-LEAD.md','v22-CHANGES.md','checkpoint-v22.md','evidence-v22/pointer-golden-v22.json','evidence-v22/check-v22-raw.txt']
banned_word='Context'+' '+'Lake'
def sub(f,old,new,count=1):
    return (f,old,new)
M=[
 ('M0-baseline',[]),
 ('M1-wrong-IST-pair',[('OWNER-SHEET-v22.md','Latest start: 11:30 UTC = 17:00 IST','Latest start: 11:30 UTC = 17:30 IST')]),
 ('M2-wrong-weekday',[('OWNER-SHEET-v22.md','Run day: Wed 18 Nov 2026','Run day: Thu 18 Nov 2026')]),
 ('M3-broken-pointer',[('OWNER-SHEET-v22.md','"go" (5.8), "n8n is off"','"go" (5.9), "n8n is off"')]),
 ('M4-changed-R-pointer-target',[('OWNER-SHEET-v22.md','Check items (a) to (f) of R9.','Check items (a) to (f) of R7.')]),
 ('M5-unlisted-set-phrase',[('OWNER-SHEET-v22.md','Read the usage page and report balance and money used.','Read the usage page and report balance and money used. Send "all done" to the lead.')]),
 ('M6-banned-word',[('OWNER-SHEET-v22.md','Post checker** = a human','Post checker** = a human (see '+banned_word+')')]),
 ('M7-wrong-sum',[('OWNER-SHEET-v22.md','run length 15 + film pause 10 = 30; margin 10','run length 15 + film pause 10 = 31; margin 10')]),
 ('M8-repeated-rule-phrase(exact)',[('LEAD-RELEASE-NOTE-v6.md','## 0. Failures first (what this note cannot settle)','## 0. Failures first (what this note cannot settle)\nCancelling may not be undoable here too.')]),
 ('M9-gate-id-in-sheet',[('OWNER-SHEET-v22.md','Cancel each key of Part 2 (a), one by one.','Cancel each key of Part 2 (a), one by one (G30).')]),
 ('M10-wrong-price',[('OWNER-SHEET-v22.md','Price per call at full size: USD 0.27','Price per call at full size: USD 0.28')]),
 ('M11-bad-Open-pointer',[('LEAD-RELEASE-NOTE-v6.md','Open 2 and 31 carry','Open 2 and 91 carry')]),
 ('M12-placeholder-name-mismatch',[('OWNER-SHEET-v22.md','write to the lead "I cancel the older key <its name>, nothing else I know uses it", then','write to the lead "I cancel the older key <older key name>, nothing else I know uses it", then')]),
 # extras beyond the 12
 ('X1-repeated-rule-paraphrase(trigger+steps restated in 7.9)',[('OWNER-SHEET-v22.md','9. Only after the card is complete','9. If any phone alarm rings or you typed `end`, cancel every key you made today, reload the key list and check the cancelled word. Only after the card is complete')]),
 ('X2-Open-pointer-exists-but-wrong-target',[('LEAD-RELEASE-NOTE-v6.md','send the sheet to one more outside reader before it goes to the owner (Open 51)','send the sheet to one more outside reader before it goes to the owner (Open 15)')]),
 ('X3-sheet-pointer-in-open-wrong-target(7.8->7.6)',[('v22-OPEN-FOR-LEAD.md','(sheet 7.8 now says cancel at once','(sheet 7.6 now says cancel at once')]),
 ('X4-note-sheet-pointer-wrong-target(8.4->8.3)',[('LEAD-RELEASE-NOTE-v6.md','the owner revokes the named apps at sheet 8.4','the owner revokes the named apps at sheet 8.3')]),
 ('X5-run-length-below-need(15->10 in sample)',[('OWNER-SHEET-v22.md','Run length: 15 (','Run length: 10 (')]),
 ('X6-R-pointer-in-note-wrong-target(R7->R9)',[('LEAD-RELEASE-NOTE-v6.md','The owner\'s method is owner sheet R7','The owner\'s method is owner sheet R9')]),
 ('X7-cancel-by-too-late(12:10->18:25 pair consistent)',[('OWNER-SHEET-v22.md','Cancel-by time: 12:10 UTC = 17:40 IST','Cancel-by time: 12:15 UTC = 17:45 IST')]),
 ('X8-card-step-pointer-wrong(card step 5->card step 3)',[('OWNER-SHEET-v22.md','"model key cancelled" (card step 5)','"model key cancelled" (card step 3)')]),
 ('X9-sheet-section-pointer-wrong(section 4->section 5)',[('OWNER-SHEET-v22.md','follow the table in section 4','follow the table in section 5')]),
 ('X10-stale-section-in-note(G9 section 4->section 3)',[('LEAD-RELEASE-NOTE-v6.md','Shutdown order as in section 4','Shutdown order as in section 3')]),
 ('X11-deadline-weekday-in-note',[('LEAD-RELEASE-NOTE-v6.md','"Deadline" = the old "window end" (Mon 23 Nov 2026','"Deadline" = the old "window end" (Tue 23 Nov 2026')]),
 ('X12-wrong-sum-in-sample-total-11:30+30',[('OWNER-SHEET-v22.md','(sample: 11:30 + 30 = 12:00; 12:00 + 10 = 12:10)','(sample: 11:30 + 30 = 12:10; 12:00 + 10 = 12:10)')]),
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
