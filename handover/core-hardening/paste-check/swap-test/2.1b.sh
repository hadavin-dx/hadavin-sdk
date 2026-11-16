. $HOME/hadavin-smoke/env.sh; CRM=$(grep '^CRM_URL=' $T/flow-values.env | cut -d= -f2-); F=$T/flows/mf-sub-crm-mail.json; echo "before $(sha256sum $F | cut -c1-12)"
python3 -I - "$F" "$CRM" <<'PYEOF'
import json, sys
p, crm = sys.argv[1], sys.argv[2]
assert crm == "http://127.0.0.1:8771", "CRM_URL is not exactly http://127.0.0.1:8771: STOP"
d = json.load(open(p)); w = d[0] if isinstance(d, list) else d
n = [x for x in w["nodes"] if x["name"] == "CrmUpsert"]
assert len(n) == 1 and n[0]["type"] == "n8n-nodes-base.hubspot", "CrmUpsert is not the HubSpot node: STOP"
n = n[0]; n["type"] = "n8n-nodes-base.httpRequest"; n["typeVersion"] = 4.2; n.pop("credentials", None)
n["parameters"] = {"method": "POST", "url": crm + "/upsert", "sendBody": True, "contentType": "json", "specifyBody": "json", "jsonBody": "={{ { hadavin_lead_id: $('SubIn').first().json.lead_key, email: $('SubIn').first().json.email, label: $('Qualify').first().json.label } }}", "options": {"timeout": 10000}}
json.dump(d, open(p, "w"))
print("CrmUpsert swapped to the loopback stand-in")
PYEOF
echo "python rc=$?"; echo "after $(sha256sum $F | cut -c1-12)"; grep -c 'n8n-nodes-base.hubspot' $T/flows/*.json; grep -c 'hubapi' $T/flows/*.json; true
