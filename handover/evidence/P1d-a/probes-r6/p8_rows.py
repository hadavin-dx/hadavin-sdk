import sys,re
exec(open("/tmp/p7/probe.py").read().split("for k,v in rows.items()")[0])
rows["Q23"]="?password=ab&x==1 y"
rows["Q23b"]="?password=ab&cd==e x"
rows["BEN1"]="client_secret_rotation_policy_document_name_v2_final_draft_for_review_only=enabled x"
for k,v in rows.items(): print(k, repr(runmap.redact_text(v,runmap.RunMap())))
for k,v in {"Q23":"?token=ab&cdEFG== x","Q23b":"?password=ab&x==1 y","Q23c":"?token=ab&cdEFG=  x","Q23d":"?token=ab&cd=EF x"}.items(): print("N"+k, repr(runmap.redact_text(v,runmap.RunMap())))
