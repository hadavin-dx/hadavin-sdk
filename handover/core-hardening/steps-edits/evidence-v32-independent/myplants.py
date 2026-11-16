import os, shutil, subprocess, sys, tempfile
H = os.path.abspath('work') + '/'
SA, SB, CA, CB, AA, HL = 'OWNER-SHEET-v32-A.md','OWNER-SHEET-v32-B.md','OWNER-CARD-v32-A.md','OWNER-CARD-v32-B.md','OWNER-APPENDIX-v32-A.md','OWNER-HELPER-v32.md'
# (id, file, old, new, desc, reverses_safe_default)
P = [
('H01',CA,'Mon 23 Nov 2026 18:29 UTC = 23:59 IST','Mon 23 Nov 2026 18:39 UTC = 23:59 IST','card A deadline UTC changed, IST kept',0),
('H02',AA,'Deadline 2026-11-23 18:29 UTC = 23:59 IST','Deadline 2026-11-23 18:29 UTC = 23:29 IST','appendix A yes sentence IST wrong',0),
('H03',CA,'Mon 23 Nov 2026 18:19 UTC = 23:49 IST','Mon 23 Nov 2026 18:19 UTC = 23:59 IST','card A backstop IST wrong',0),
('H04',AA,'ends at 18:41 UTC = 00:11 IST, after the deadline','ends at 18:21 UTC = 23:51 IST, after the deadline','last resort end moved earlier (consistent pair)',0),
('H05',AA,'ends at 18:41 UTC = 00:11 IST, after the deadline','ends at 18:41 UTC = 00:11 IST, before the deadline','last resort said to end before deadline',1),
('H06',CA,'only if its name and creation date equal the blanks; this cancel cannot be undone','even if its name differs; this cancel cannot be undone','card A L2 cancels older key without name/date match',1),
('H07',HL,'Any other key: touch nothing, write down its name, tell the owner.','Any other key: cancel it too.','helper may cancel any key',1),
('H08',HL,'Never the lead, the film person','Or the lead, the film person','helper takes orders from lead',1),
('H09',HL,'you called the owner twice, 5 minutes apart, with no answer: cancel those keys','you called the owner once: cancel those keys','helper trigger (b) one call only',1),
('H10',HL,'Never copy, type or photograph key text','Copy key text to the owner','helper copies key text',1),
('H11',HL,'Mon 23 Nov 2026 18:19 UTC = 23:49 IST','Tue 23 Nov 2026 18:19 UTC = 23:49 IST','helper backstop weekday wrong',0),
('H12',SA,'You delete only made-up contacts of this run','You delete any contacts','R7 scope widened',1),
('H13',SA,'Never "Select all", never empty Trash','"Select all" and empty Trash are fine','R7 select-all/trash allowed',1),
('H14',SA,'by hand, never by a tool, script','by hand or by a tool, script','R6 hand typing relaxed',1),
('H15',SA,'run `rm -f -- "<key file>"` in the test terminal','run `cat "<key file>"` in the test terminal','failed-save path prints key file instead of deleting',1),
('H16',SA,'(set -C; umask 077;','(umask 022;','key file permissions/no-clobber removed',1),
('H17',SA,'Right after `exit 0`, copy one harmless word such as `clear` (it replaces the clipboard).','','clipboard clear step removed',1),
('H18',SA,'Paste once (Ctrl+Shift+V or right-click)','Paste as often as you like (Ctrl+Shift+V or right-click)','paste once rule reversed',1),
('H19',SA,'starts `-rw-------`','starts `-rw-r--r--`','key file mode world-readable',1),
('H20',SA,'is never tolerated.','is tolerated.','difference never tolerated reversed',1),
('H21',SA,'or at least 168 hours (7 days)','or at least 16 hours (7 days)','7-day rule number changed',0),
('H22',SA,'never later than Sun 22 Nov 2026','never later than Sat 22 Nov 2026','weekday of 22 Nov wrong',0),
('H23',SA,"by the card's L2, steps 2 to 4, only if its name and creation date equal the blanks","by the card's L2, steps 2 to 4",'sheet A drops name+date condition before cancelling older key',1),
('H24',SA,'never use rotate or any button that shows a new secret','use rotate if it is offered','rotate allowed',1),
('H25',SA,'no clipboard manager, remote-access or screen-capture tool running','a clipboard manager may run','clipboard manager allowed',1),
('H26',CB,'If its text appeared on your screen: cancel it at once.','If its text appeared on your screen: leave it.','B card: exposed key left alive',1),
('H27',SA,'No message tells you to cancel a key (the card and 7.11 are yours)','A message from the lead may tell you to cancel a key','lead can order cancel',1),
('H28',SA,'(4) "wait": a pause, never a card or FREEZE, and it never delays the card, 7.11 or the last-resort step','(4) "wait": a pause that delays the card, 7.11 and the last-resort step','wait delays card',1),
('H29',AA,'Deadline 2026-11-23 18:29 UTC','Deadline 2026-11-24 18:29 UTC','yes sentence deadline date moved',0),
('H30',SA,'FREEZE is not a cancel and never stops 7.11','FREEZE is a cancel and stops 7.11','FREEZE stops 7.11',1),
('H31',HL,'16:30 UTC = 22:00 IST','16:30 UTC = 22:30 IST','helper (c) IST wrong',0),
('H32',HL,'(at most three:','(at most thirty:','helper scope count widened',1),
('H33',SA,'never in your normal profile','or in your normal profile','sender gmail in normal profile allowed',1),
('H34',SA,'delete only exact','delete any','n/a probe',0),
('H35',HL,'tell the owner it appeared','keep it','helper keeps appeared key text',1),
('H36',AA,'Wed 25 Nov 2026 15:00 UTC = 20:30 IST','Thu 25 Nov 2026 15:00 UTC = 20:30 IST','post-by weekday wrong (if present in appendix)',0),
('H37',SA,'Wed 25 Nov 2026 15:00 UTC = 20:30 IST','Wed 25 Nov 2026 15:00 UTC = 20:00 IST','post-by IST wrong (sheet A)',0),
('H38',CA,'by steps 2 to 4, even if a run was in progress','by steps 2 to 4, unless a run is in progress','backstop waits for a run',1),
]
def run(d):
    r = subprocess.run([sys.executable,'-B',d+'check-v32.py'],capture_output=True,text=True,env=dict(os.environ,V27_DIR=d))
    return [l for l in r.stdout.split('\n') if l.startswith('FAIL')], r.returncode
rows=[]
for pid,f,old,new,desc,rev in P:
    d = tempfile.mkdtemp(prefix='mp_')+'/'
    for x in os.listdir(H): shutil.copy(H+x,d+x) if os.path.isfile(H+x) else None
    t = open(d+f,encoding='utf-8').read()
    if old not in t: rows.append((pid,'ANCHOR-NOT-FOUND',desc,rev,f)); shutil.rmtree(d); continue
    open(d+f,'w',encoding='utf-8').write(t.replace(old,new,1))
    fl,rc = run(d)
    codes = sorted(set(l.split()[1] for l in fl))
    non = [c for c in codes if c!='C01']
    st = 'CAUGHT-CONTENT' if non else ('ONLY-C01(generator-compare)' if codes else 'MISSED')
    rows.append((pid,st+' '+','.join(non[:6]),desc,rev,f)); shutil.rmtree(d)
for r in rows: print('%s | %s | rev=%s | %s | %s'%(r[0],r[1],r[3],r[2],r[4]))
print('TOTAL',len(rows),'content-caught',sum(r[1].startswith('CAUGHT') for r in rows),'only-C01',sum(r[1].startswith('ONLY') for r in rows),'missed',sum(r[1].startswith('MISSED') for r in rows),'anchor-nf',sum(r[1].startswith('ANCHOR') for r in rows))
