import os, sys, tempfile, json
from pathlib import Path
H="/home/user/build/rr6/out/EV7T/hcopy"
sys.path[:0]=[H+"/src",H,H+"/tests",H+"/scripts"]
import scripts.run_real_check as rrc
tmp=Path(tempfile.mkdtemp(dir=os.environ["TMPDIR"]))
def t(name,fn):
    try: print(f"{name:75s} -> {fn()!r}")
    except BaseException as e: print(f"{name:75s} -> RAISED {type(e).__name__}: {str(e)[:80]}")
print("## contacts_not_accounted_for")
t("created=None, accounted=0",lambda:rrc.contacts_not_accounted_for(None,0))
t("created=None, accounted=5",lambda:rrc.contacts_not_accounted_for(None,5))
t("created=None, accounted=0, open=3, leads=9",lambda:rrc.contacts_not_accounted_for(None,0,3,9))
t("created=8, accounted=8, open=1, leads=9",lambda:rrc.contacts_not_accounted_for(8,8,1,9))
t("created=8, accounted=8, open=2 (retried), leads=9",lambda:rrc.contacts_not_accounted_for(8,8,2,9))
t("created=0, accounted=0, open=1 (unknown 1, nothing listed), leads=9",lambda:rrc.contacts_not_accounted_for(0,0,1,9))
t("created=0, accounted=0, open=0",lambda:rrc.contacts_not_accounted_for(0,0,0,9))
t("created=-1 accounted=0",lambda:rrc.contacts_not_accounted_for(-1,0))
print("## read_counter_files_checked / counter_is_known")
def rd(d,tag="rabcdef"):
    r=rrc.read_counter_files_checked(d,".hubspot.json",tag); return (r, rrc.counter_is_known(r))
t("missing folder",lambda:rd(tmp/"nope"))
e=tmp/"empty"; e.mkdir()
t("empty folder (no glob match)",lambda:rd(e))
h=tmp/"half"; h.mkdir(); (h/"desk-rabcdef-1.hubspot.json").write_text('{"created": 3, "cre')
t("half-written file",lambda:rd(h))
z=tmp/"zero"; z.mkdir(); (z/"desk-rabcdef-1.hubspot.json").write_text('')
t("zero-byte file",lambda:rd(z))
nc=tmp/"nocreated"; nc.mkdir(); (nc/"desk-rabcdef-1.hubspot.json").write_text('{"calls": 3}')
t("file with no 'created'",lambda:rd(nc))
ok=tmp/"ok"; ok.mkdir(); (ok/"desk-rabcdef-1.hubspot.json").write_text('{"created": 3, "create_open": 1}')
t("good file",lambda:rd(ok))
(ok/"desk-rabcdef-2.hubspot.json").write_text('[1,2]')
t("good file + list-valued file",lambda:rd(ok))
t("other tag only (older run)",lambda:rd(ok,"rzzzzzz"))
t("empty tag",lambda:rd(ok,""))
t("tag None",lambda:rd(ok,None))
print("## exit_code_of")
t("ok,written,[],0,known",lambda:rrc.exit_code_of(True,True,[],0,True))
t("ok,written,[],0,counter NOT known",lambda:rrc.exit_code_of(True,True,[],0,False))
t("create_unknown=1, nothing listed: unseen=contacts_not_accounted_for(0,0,1,9) then exit_code",lambda:rrc.exit_code_of(True,True,[],rrc.contacts_not_accounted_for(0,0,1,9),True))
t("create_unknown=1, listed 1 (accounted=1): exit_code",lambda:rrc.exit_code_of(True,True,[],rrc.contacts_not_accounted_for(0,1,1,9),True))
print("## HubspotCrm with unwritable counters file, create not sent")
from test_crm_hubspot import REC, Rig
from lead_desk.crm_hubspot import CrmCounterUnwritable
rig=Rig(tmp/"rig") if (tmp/"rig").mkdir() is None else None
try:
    taken=tmp/"desk-rabcdef-1.hubspot.json"; taken.mkdir()
    crm=rig.crm(stats_file=taken)
    t("put() with a folder named as the counters file",lambda:crm.put("L-1",REC))
    print("contacts at the fake after put:",len(rig.state.contacts),"stats:",crm.stats())
    good=tmp/"good.json"; crm2=rig.crm(stats_file=good)
    t("put() with writable file",lambda:crm2.put("L-2",REC))
    print("file after:",good.read_text(), "contacts:",len(rig.state.contacts))
finally: rig.stop()
