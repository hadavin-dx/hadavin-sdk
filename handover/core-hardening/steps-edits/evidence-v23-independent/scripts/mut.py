import os,shutil,subprocess,re,sys,ast
SRC='/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
SCR='/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/v23ind/mut/'
FILES=['OWNER-SHEET-v23.md','LEAD-RELEASE-NOTE-v7.md','v23-OPEN-FOR-LEAD.md','v23-CHANGES.md','OWNER-SHEET-v22.md','LEAD-RELEASE-NOTE-v6.md','checkpoint-v23.md','check-v23.py']
S,N,O,C='OWNER-SHEET-v23.md','LEAD-RELEASE-NOTE-v7.md','v23-OPEN-FOR-LEAD.md','v23-CHANGES.md'
tree=ast.parse(open('/home/user/hadavin-sdk/tests/test_no_reference_material.py',encoding='utf-8').read())
banned=[]
for node in ast.walk(tree):
    if isinstance(node,ast.Assign) and any(getattr(x,'id','')=='BANNED' for x in node.targets): banned=[e.value for e in node.value.elts]
BW=banned[0]
# (id, class, file, old, new, occurrence index (0-based) or 'all')
M=[
('M01','price line (sheet message) 0.27->0.28',S,'Price per call at full size: USD 0.27','Price per call at full size: USD 0.28',0),
('M02','expected total line 0.81->0.82',S,'Expected total: USD 0.81 (not a limit)','Expected total: USD 0.82 (not a limit)',0),
('M03','sample notice price line',S,'Price per call: 0.27 (USD)','Price per call: 0.28 (USD)',0),
('M04','filled yes example total',S,'expected total USD 0.81, not a limit, balance USD 189.00, which I accept I could lose entirely, even if cancelling a key does not end the calls, auto-reload off','expected total USD 0.82, not a limit, balance USD 189.00, which I accept I could lose entirely, even if cancelling a key does not end the calls, auto-reload off',0),
('M05','sheet pointer wrong target: card step 6 "Go on at 7.9" -> 7.5',S,'Go on at 7.9 if you typed','Go on at 7.5 if you typed',0),
('M06','sheet pointer: "back on in 8.7" -> 8.5',S,'back on in 8.7','back on in 8.5',0),
('M07','note pointer sheet 8.4 -> 8.3 (HubSpot secret revoke)',N,'the HubSpot app secret revoke (G42, sheet 8.4)','the HubSpot app secret revoke (G42, sheet 8.3)',0),
('M08','note pointer sheet 7.8 -> 7.6 (order end then cancel)',N,'The order `end` then cancel (sheet 7.8)','The order `end` then cancel (sheet 7.6)',0),
('M09','note R8 -> R7 (characters of owner sheet)',N,'only the characters of owner sheet R8','only the characters of owner sheet R7',0),
('M10','note R7 -> R9 (delete method)',N,'The owner\'s method is owner sheet R7','The owner\'s method is owner sheet R9',0),
('M11','weekday sheet Wed 18 -> Tue 18',S,'Wed 18 Nov passes','Tue 18 Nov passes',0),
('M12','weekday note Mon 23 -> Tue 23',N,'On Mon 23 Nov (no run is released','On Tue 23 Nov (no run is released',0),
('M13','IST pair sheet 12:10 UTC = 17:40 -> 17:50',S,'Cancel-by time: 12:10 UTC = 17:40 IST','Cancel-by time: 12:10 UTC = 17:50 IST',0),
('M14','IST pair note 12:00 = 17:30 -> 17:00',N,'LF = 12:00 UTC = 17:30 IST','LF = 12:00 UTC = 17:00 IST',0),
('M15','IST pair open list 12:00 = 17:30 -> 17:20',O,'alarm 12:00 UTC = 17:30 IST','alarm 12:00 UTC = 17:20 IST',0),
('M16','placeholder renamed <run name> -> <runname> (one place)',S,'`run-<run name>`','`run-<runname>`',0),
('M17','placeholder renamed <its name or none> -> <its name or nome>',S,'older key <its name or none>.','older key <its name or nome>.',0),
('M18','list-form pointer "Open 2 and 31" -> "Open 2 and 91"',N,'(Open 2 and 31)','(Open 2 and 91)',0),
('M19','paraphrased cancel rule added outside the card (sheet 7.6)',S,'The model key is still alive. The film person alone','The model key is still alive: if you must stop it, click Cancel beside each key and refresh the page twice to see the cancelled state. The film person alone',0),
('M20','8.4 -> 8.3 on set phrase "HubSpot apps revoked"',S,'"HubSpot apps revoked" (8.4)','"HubSpot apps revoked" (8.3)',0),
('M21','R7 -> R9 in sheet 5.4',S,'delete exactly those as R7 says','delete exactly those as R9 says',0),
('M22','wrong sum check 3 (11:30 + 30 = 12:10)',S,'sample: 11:30 + 30 = 12:00','sample: 11:30 + 30 = 12:10',0),
('M23','wrong sum in sums line 5+15+10 = 35',S,'film pause 10 = 30; margin 10','film pause 10 = 35; margin 10',0),
('M24','A/B bracket text left inside the other variant ([[B:..]] inside [[A:..]])',S,'[[A: (b) the older key named in the numbers message','[[A: [[B: leftover]] (b) the older key named in the numbers message',0),
('M25','stray [[ marker left after variants removed',S,'The balance is at least the expected total.','The balance is at least the expected total. [[ left',0),
('M26','banned word inserted (note)',N,'## 9. Kept from earlier appendices (lead\'s own use)','## 9. Kept from earlier appendices (lead\'s own use) '+BW,0),
('M27','open list numbering gap (row 40 -> 41)',O,'| 40 | Does the take program print','| 41 | Does the take program print',0),
('M28','note G pointer wrong (lease wording G12 -> G32)',N,'the lease wording (G12)','the lease wording (G32)',0),
('M29','note Open 51 -> Open 15 (order 034)',N,'before it goes to the owner (Open 51)','before it goes to the owner (Open 15)',0),
('M30','note "Shutdown order as in section 4" -> section 3',N,'Shutdown order as in section 4','Shutdown order as in section 3',0),
('M31','run length 15 -> 14 (below 860 s)',S,'Run length: 15 (','Run length: 14 (',0),
('M32','860 s = 14.33 -> 14.4 in sheet',S,'at least 860 seconds = 14.33 minutes','at least 860 seconds = 14.4 minutes',0),
('M33','weekday glossary deadline Mon 23 -> Tue 23',S,'**deadline** = Mon 23 Nov 2026','**deadline** = Tue 23 Nov 2026',0),
('M34','R10 sentence without "key alive: card first" (6.6)',S,'two or none: FREEZE, R10, key alive: card first)','two or none: FREEZE, R10)',0),
('M35','tolerated item dropped from note (HubSpot private-app page path)',N,'the HubSpot private-app page path (8.4), ','',0),
('M36','paraphrased cancel rule added to the note',N,'## 6. Contact list after the take','## 6. Contact list after the take\nThe owner reloads the key list twice and sees the cancelled word each time before telling the lead.',0),
('M37','program limit 13.21 -> 13.22 (sheet message)',S,'Program limit: USD 13.21','Program limit: USD 13.22',0),
('M38','settings TOKENS_OUT 10000 -> 12000',S,'TOKENS_OUT = 10000 (tokens)','TOKENS_OUT = 12000 (tokens)',0),
('M39','set phrase spelled differently (cancelled -> canceled) in card step 5',S,'Tell the lead exactly: model key cancelled.','Tell the lead exactly: model key canceled.',0),
('M40','B submitted 10 -> 12 times (sheet 3 expected line)',S,'B submitted 10 times, 1 contact','B submitted 12 times, 1 contact',0),
('M41','note IST definition UTC + 5:30 -> 5:00',N,'(IST = UTC + 5:30)','(IST = UTC + 5:00)',0),
('M42','open row 56 14.4 -> 14.5 minutes',O,'at least 860 seconds (14.4 minutes)','at least 860 seconds (14.5 minutes)',0),
('M43','note G33 -> G38 (spend lock)',N,'the spend lock (G33)','the spend lock (G38)',0),
('M44','sheet table "Type the yes (5.8)" -> 5.7',S,'Type the yes (5.8)','Type the yes (5.7)',0),
('M45','glossary key-list check 6.6 -> 6.5',S,'at 5.6, 6.2 and 6.6 (again at 7.1)','at 5.6, 6.2 and 6.5 (again at 7.1)',0),
('M46','8.1 "card step 3" -> "card step 5"',S,'cancel press, card step 3)','cancel press, card step 5)',0),
('M47','post-by IST wrong 20:30 -> 20:00',S,'15:00 UTC = 20:30 IST','15:00 UTC = 20:00 IST',0),
('M48','changes file pointer 7.8 -> 7.7',C,'corrected (7.8, 15 minutes','corrected (7.7, 15 minutes',0),
('M49','open row 34 pointer: sheet 7.8 error sentence -> 7.7 (the v22 failure P1)',O,"the sheet's 7.8 error sentence stays","the sheet's 7.7 error sentence stays",0),
('M50','price in note 0.27 -> 0.28 (note worked price)',N,'gives 0.27; ceiling 3 gives expected total 0.81','gives 0.28; ceiling 3 gives expected total 0.81',0),
('M51','unlisted set phrase told ("tell \\"all done\\"") in 8.5',S,'tell "demo mails deleted <number>".','tell "all done".',0),
('M52','"Open 2 and 91" in open list style: "Open 2, 31 and 91" in note',N,'(Open 2 and 31)','(Open 2, 31 and 91)',0),
('M53','number message Expected total in Open (0.81 -> 0.80 in note)',N,'expected total 0.81. Ledger total 12.40','expected total 0.80. Ledger total 12.40',0),
('M54','sheet 5.8 deadline pair: 23:59 -> 23:29',S,'Deadline 2026-11-23 18:29 UTC = 23:59 IST','Deadline 2026-11-23 18:29 UTC = 23:29 IST',0),
]
def prep():
    if os.path.exists(SCR): shutil.rmtree(SCR)
    os.makedirs(SCR)
def run_case(cid,desc,f,old,new,idx):
    d=SCR+cid+'/'
    os.makedirs(d)
    for x in FILES: shutil.copy(SRC+x,d+x)
    os.makedirs(d+'evidence-v23',exist_ok=True)
    t=open(d+f,encoding='utf-8').read()
    n=t.count(old)
    if n==0: return (cid,desc,'ANCHOR-NOT-FOUND',0,'')
    t=t.replace(old,new,1) if idx==0 else t.replace(old,new)
    open(d+f,'w',encoding='utf-8').write(t)
    r=subprocess.run(['python3',d+'check-v23.py'],capture_output=True,text=True,env=dict(os.environ,V23_DIR=d),timeout=120)
    probs=[l for l in r.stdout.splitlines() if l.startswith('PROBLEM:')]
    err=(r.stderr.strip().splitlines() or [''])[-1][:100]
    return (cid,desc,'CAUGHT' if r.returncode!=0 else 'MISSED',len(probs),(probs[0][:150].replace(BW,'<banned>') if probs else err))
if __name__=='__main__':
    prep()
    # baseline
    d=SCR+'M00/'; os.makedirs(d)
    for x in FILES: shutil.copy(SRC+x,d+x)
    os.makedirs(d+'evidence-v23',exist_ok=True)
    r=subprocess.run(['python3',d+'check-v23.py'],capture_output=True,text=True,env=dict(os.environ,V23_DIR=d)); 
    print('M00 baseline (copies, no change): rc=%d problems=%d'%(r.returncode,r.stdout.count('PROBLEM:')))
    res=[run_case(*m) for m in M]
    for x in res: print('%s | %-8s | problems=%2d | %s | first: %s'%(x[0],x[2],x[3],x[1],x[4]))
    c=sum(1 for x in res if x[2]=='CAUGHT'); mi=sum(1 for x in res if x[2]=='MISSED'); nf=sum(1 for x in res if x[2]=='ANCHOR-NOT-FOUND')
    print('TOTAL planted %d: caught %d, missed %d, anchor not found %d'%(len(res),c,mi,nf))
    print('MISSED list:',[x[0] for x in res if x[2]=='MISSED'])
