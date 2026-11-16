import sys, os, json
from pathlib import Path
root = Path(sys.argv[1]); sys.path[:0]=[str(root/"src"), str(root)]
from lead_desk.crm_hubspot import HubspotCrm, HubspotSettings
p = Path(os.environ["TMPDIR"])/"desk-x-a.hubspot.json"
if p.exists(): p.unlink()
c = HubspotCrm(HubspotSettings(key_file=Path("/nonexistent-key"), max_calls=5, stats_file=p))
print("after construct, file exists:", p.exists())
c._count("rate_limited")   # the write helper any non-create call path reaches (line 280-284)
print("after one _count, file:", p.read_text())
