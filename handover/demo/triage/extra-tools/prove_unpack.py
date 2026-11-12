import sys, types, time
sys.path[:0]=["src","."]
from demo_only import portal_demo as pd
cfg=types.SimpleNamespace(send_timeout_seconds=1.0, fakes_url="http://x")
d=pd.PortalDemo.__new__(pd.PortalDemo); d._desk=types.SimpleNamespace(config=cfg, crm=None, outbox=None)
for label,fn in [("all answer",lambda u,w:{"messages":[],"rows":[],"count":0}),("one unreachable",lambda u,w:None if u.endswith(pd.CRM_PATH) else {"messages":[],"rows":[]}),("all None",lambda u,w:None)]:
    pd._fetch_json=fn
    print(label, "->", d._fakes())
pd.STATE_DEADLINE_SECONDS=-5   # deadline already past: every wait <= 0, three None entries
print("deadline passed ->", d._fakes())
