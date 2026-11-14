"""Builds the import files for the n8n command line from the read-only copy of the Design A v2 files.
Replaces only the three named placeholders. Usage: python prepare_probe.py SRC_DIR OUT_DIR"""
import json
import os
import sys

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
creds = [
    {"id": "pgcred01", "name": "n8n-publish-pg", "type": "postgres",
     "data": {"host": "127.0.0.1", "port": 55432, "database": "kill_t", "user": "postgres", "password": "stand-in",
              "ssl": "disable", "allowUnauthorizedCerts": False, "maxConnections": 10}},
    {"id": "smtpcred1", "name": "mf-mail-smtp", "type": "smtp",
     "data": {"user": "stand-in", "password": "stand-in", "host": "127.0.0.1", "port": 2525, "secure": False,
              "disableStartTls": True, "hostName": ""}}]
json.dump(creds, open(os.path.join(out, "creds.json"), "w"))
ids = {"mf-sub-crm-mail": "subflow0000000001", "mf-form": "form000000000001", "mf-hook": "hook000000000001",
       "mf-recovery": "recov00000000001"}
for n, i in ids.items():
    t = open(os.path.join(src, n + ".json")).read()
    t = t.replace("PG_CREDENTIAL_ID", "pgcred01").replace("SMTP_CREDENTIAL_ID", "smtpcred1").replace("SUB_WORKFLOW_ID", ids["mf-sub-crm-mail"])
    d = json.loads(t)
    d["id"], d["active"] = i, False
    json.dump(d, open(os.path.join(out, n + ".json"), "w"))
    print(n, i, len(d["nodes"]), "nodes")
