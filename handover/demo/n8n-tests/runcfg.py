"""One place for every port, name and label a test run uses. DEFAULTS = the values the harness had before (a run without any of these variables behaves exactly as before). Set RUN_ID (a short lowercase name, letters and digits, starting with a letter, up to 12) to get a second, parallel run: it suffixes the Postgres container name and the label VALUE, and you give that run its own ports and its own work folder (--work-dir). Nothing here starts or stops anything.
Environment variables (all optional):
  RUN_ID               ''  -> container n8n-publish-pg, label n8n-evidence.run=1.   'b' -> container n8n-publish-pg-b, label n8n-evidence.run=b
  MF_STAGE_PORT 8770   MF_CRM_PORT 8771
  DN1_DESK_PORT 8765   DN1_FAKE_PORT 8766   DN1_MODEL_PORT 48767   DN1_PROXY_PORT 8760   DN1_MAIL_PORT 8791
  MF_N8N_PORT 5679     MF_N8N_BROKER_PORT 5780   MF_PG_PORT 55432   MF_RUN_PORT 8790 (listed in the free-port check as before)
NOTE: the harness lib.py still hard-codes n8n 5679 / broker 5780; a second parallel run needs LIB-PORT-PATCH.md applied (see there). Without it, MF_N8N_PORT / MF_N8N_BROKER_PORT must stay at their defaults."""
import os, re
RUN_ID = os.environ.get("RUN_ID", "")
if RUN_ID and not re.fullmatch(r"[a-z][a-z0-9]{0,11}", RUN_ID): raise SystemExit("RUN_ID must match [a-z][a-z0-9]{0,11}: %r" % RUN_ID)
def _p(name, default):
    v = os.environ.get(name, "")
    try: return int(v) if v else default
    except ValueError: raise SystemExit("%s must be a port number: %r" % (name, v))
def config(env=None):
    """the full set for the CURRENT environment (or for a given dict of variables, used by the disjointness test)"""
    e = os.environ if env is None else env
    rid = e.get("RUN_ID", "")
    if rid and not re.fullmatch(r"[a-z][a-z0-9]{0,11}", rid): raise ValueError("bad RUN_ID %r" % rid)
    g = lambda n, d: int(e.get(n) or d)
    c = dict(run_id=rid, pg_name="n8n-publish-pg" + ("-" + rid if rid else ""), label="n8n-evidence.run=" + (rid or "1"),
             stage=g("MF_STAGE_PORT", 8770), crm=g("MF_CRM_PORT", 8771), desk=g("DN1_DESK_PORT", 8765), fake=g("DN1_FAKE_PORT", 8766), model=g("DN1_MODEL_PORT", 48767),
             proxy=g("DN1_PROXY_PORT", 8760), mail=g("DN1_MAIL_PORT", 8791), n8n=g("MF_N8N_PORT", 5679), broker=g("MF_N8N_BROKER_PORT", 5780), pg_port=g("MF_PG_PORT", 55432), run=g("MF_RUN_PORT", 8790))
    return c
PORT_KEYS = ("stage", "crm", "desk", "fake", "model", "proxy", "mail", "n8n", "broker", "pg_port", "run")
def disjoint(a, b):
    """problems between two configs (empty list = disjoint): shared ports, same container name, same label"""
    bad = [("port", k, a[k]) for k in PORT_KEYS for j in PORT_KEYS if a[k] == b[j]]
    if a["pg_name"] == b["pg_name"]: bad.append(("name", a["pg_name"]))
    if a["label"] == b["label"]: bad.append(("label", a["label"]))
    return bad
C = config()
STAGEP, CRMP, DESKP, FAKEP, MODELP, PROXYP, MAILP, N8NP, BROKERP, PGP, RUNP = (C[k] for k in ("stage", "crm", "desk", "fake", "model", "proxy", "mail", "n8n", "broker", "pg_port", "run"))
PG_NAME, LABEL = C["pg_name"], C["label"]
PORTS = (N8NP, BROKERP, RUNP, PGP)
