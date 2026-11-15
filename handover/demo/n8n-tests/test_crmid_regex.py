"""Check the CrmIdOk node in v5 flows: the expression is really evaluated (node) on made-up CRM answers.
Run: python3 test_crmid_regex.py ../n8n-flows-real-v5/mf-sub-crm-mail.json ../n8n-flows-film-v5/mf-sub-crm-mail.json
Expect: id 12 and vid 7 pass; 'undefined' text, empty, neither, 12a, -3, 1.5 fail (go to OutStage). Also checks SetCrmId and wiring."""
import json, subprocess, sys, re
CASES = [({"id": 12}, True), ({"vid": 7}, True), ({"id": "34"}, True), ({}, False), ({"id": ""}, False), ({"id": "undefined"}, False),
         ({"id": "12a"}, False), ({"id": -3}, False), ({"id": 1.5}, False), ({"id": None, "vid": 9}, True)]
bad = 0
for path in sys.argv[1:]:
    wf = json.load(open(path)); nodes = {n["name"]: n for n in wf["nodes"]}
    c = nodes["CrmIdOk"]["parameters"]["conditions"]["conditions"][0]
    expr = c["leftValue"]
    assert c["operator"]["type"] == "boolean" and c["operator"]["operation"] == "true", "operator"
    assert "String($json.id ?? $json.vid ?? '')" in nodes["SetCrmId"]["parameters"]["query"] or "String($json.id ?? $json.vid ?? '')" in json.dumps(nodes["SetCrmId"]["parameters"]), "SetCrmId"
    con = wf["connections"]["CrmIdOk"]["main"]
    assert con[0][0]["node"] == "OwnsClaim1" and con[1][0]["node"] == "OutStage", "wiring"
    js = expr[3:-2]
    for ans, want in CASES:
        prog = "const $=()=>({first:()=>({json:%s})});console.log(%s)" % (json.dumps(ans), js)
        got = subprocess.run(["node", "-e", prog], capture_output=True, text=True).stdout.strip() == "true"
        ok = got == want; bad += not ok
        print(("ok  " if ok else "FAIL"), path.split("/")[-2], ans, "->", got)
print("PASS" if not bad else "FAIL %d" % bad); sys.exit(bool(bad))
