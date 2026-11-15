"""GO-1 fix, built from the demo v4 flow files (read-only copy). Usage: python make_go1.py SRC_V4_DIR OUT_DIR
Adds to mf-recovery: n8n 'Instance started' trigger -> ClearStaleAlertClaims (one SQL). Nothing else changes."""
import json, os, shutil, sys
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
for f in os.listdir(src):
    shutil.copy(os.path.join(src, f), out)
p = os.path.join(out, "mf-recovery.json")
d = json.load(open(p))
d["nodes"] += [
    {"parameters": {"events": ["init"]}, "name": "OnN8nStart", "type": "n8n-nodes-base.n8nTrigger", "typeVersion": 1,
     "position": [-200, 600]},
    {"parameters": {"operation": "executeQuery", "options": {},
                    "query": "UPDATE mf_leads SET alert_until=NULL, alert_token=NULL WHERE alert_sent=false AND alert_token IS NOT NULL AND state IN ('unknown','failed') RETURNING lead_key;"},
     "name": "ClearStaleAlertClaims", "type": "n8n-nodes-base.postgres", "typeVersion": 2.5, "position": [40, 600],
     "credentials": {"postgres": {"id": "PG_CREDENTIAL_ID", "name": "n8n-publish-pg"}}, "alwaysOutputData": False,
     "onError": "continueRegularOutput"}]
d["connections"]["OnN8nStart"] = {"main": [[{"node": "ClearStaleAlertClaims", "type": "main", "index": 0}]]}
json.dump(d, open(p, "w"), indent=1)
print("ok", len(d["nodes"]), "nodes")
