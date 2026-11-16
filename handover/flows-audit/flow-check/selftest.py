#!/usr/bin/env python3
"""Self-test of check_flows.py (F8). Usage: selftest.py PRISTINE_DIR [PATCHED_DIR]   (stdlib only; nothing is run in n8n).
Copies PRISTINE_DIR (the committed real-v5 flows) to a temp folder, plants ONE defect per case, runs the checker with one fixed
command line and requires: exit code 1 AND the named FAIL text in the output. One positive control (no defect) must exit 0.
With PATCHED_DIR (patched generator output) 3 more cases run the patch checks. Raw output goes to selftest-output/NAME.out."""
import json, os, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
# FC_CK = run the same cases against another checker (e.g. the old patch-apply one); FC_OUT = where the raw .out files go
CK = os.environ.get("FC_CK") or HERE + "/check_flows.py"; OUT = os.environ.get("FC_OUT") or HERE + "/selftest-output"
PRIS = sys.argv[1]; PATCHED = sys.argv[2] if len(sys.argv) > 2 else None
COUNTS = ["--expect", "mf-form.json=12:11", "--expect", "mf-hook.json=12:11", "--expect", "mf-recovery.json=10:9", "--expect", "mf-sub-crm-mail.json=20:26"]
PCOUNTS = ["--expect", "mf-form.json=15:14", "--expect", "mf-hook.json=15:14", "--expect", "mf-recovery.json=10:9", "--expect", "mf-sub-crm-mail.json=20:26"]
def cmd(d, extra=()): return ["python3", "-I", CK, d, "--baseline", PRIS] + COUNTS + ["--quiet-info"] + list(extra)
def node(j, n): return [x for x in j["nodes"] if x["name"] == n][0]
def link(dst, i=0): return {"node": dst, "type": "main", "index": i}
def noop(name): return {"name": name, "type": "n8n-nodes-base.noOp", "typeVersion": 1, "position": [0, 0], "parameters": {}}
def m_cycle(j, d):
    j["nodes"] += [noop("CycA"), noop("CycB")]; j["connections"]["CycA"] = {"main": [[link("CycB")]]}; j["connections"]["CycB"] = {"main": [[link("CycA")]]}
def m_switch(j, d):
    j["nodes"].append({"name": "Sw", "type": "n8n-nodes-base.switch", "typeVersion": 3, "position": [0, 0], "parameters": {"rules": {"values": [{}, {}]}}})
    j["connections"]["Item"]["main"][0].append(link("Sw")); j["connections"]["Sw"] = {"main": [[link("ReplyStored")]]}
def m_dupname(j, d): j["nodes"].append(noop("Item")); j["connections"]["Item"]["main"][0].append(link("Item"))
def m_trigin(j, d): j["connections"]["Item"]["main"][0].append(link("Receive"))
def m_sticky_only(j, d): j["nodes"] = [{"name": "Note", "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": [0, 0], "parameters": {"content": "x"}}]; j["connections"] = {}
def m_sticky_ok(j, d): j["nodes"].append({"name": "Note", "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": [0, 0], "parameters": {"content": "note only"}})
def m_dupid(j, d): node(j, "Item")["id"] = "a1"; node(j, "Valid")["id"] = "a1"
def m_case(j, d): j["nodes"].append(noop("item")); j["connections"]["Item"]["main"][0].append(link("item"))
def m_secret(j, d): node(j, "Valid")["parameters"]["note"] = "sk-" + "A1b2C3d4" * 3
def m_secretkey(j, d): node(j, "Valid")["parameters"]["apiKey"] = "".join(["h", "unter", "2", "xyz"])
def m_aws(j, d): node(j, "Valid")["parameters"]["note"] = "AKIA" + "ABCDEFGHIJKLMNOP"
def m_aws_example(j, d): node(j, "Valid")["parameters"]["note"] = "AKIA" + "IOSFODNN7EXAMPLE"
def m_nocred(j, d): node(j, "Claim").pop("credentials")
def m_credname(j, d): node(j, "Claim")["credentials"]["postgres"]["name"] = ""
def m_credid(j, d): node(j, "Claim")["credentials"]["postgres"].pop("id")
def m_noreply(j, d): j["connections"].pop("Stored"); j["connections"]["Stored"] = {"main": [[]]}
def m_dead_branch(j, d): j["nodes"].append(noop("DeadEnd")); j["connections"]["IsProcessing"]["main"][1] = [link("DeadEnd")]
def m_noresp_any(j, d):
    for n in j["nodes"]:
        if n["type"] == "n8n-nodes-base.respondToWebhook": n["type"] = "n8n-nodes-base.noOp"
def m_dupwh(j, d):
    h = json.load(open(d + "/mf-hook.json")); node(h, "Receive")["parameters"]["path"] = "mf-form"; json.dump(h, open(d + "/mf-hook.json", "w")); return False
def m_parse(j, d): open(d + "/mf-form.json", "w").write("{bad"); return False
def m_missing(j, d): os.remove(d + "/mf-hook.json"); return False
def m_nopos(j, d): node(j, "Item").pop("position")
def m_notrig(j, d): node(j, "Receive")["type"] = "n8n-nodes-base.respondToWebhook"
def m_selfref(j, d): node(j, "Valid")["parameters"]["note"] = "={{ $('Valid').item.json.x }}"
M = [  # name, mutator, text that MUST be in the output, extra checker options
 ("orphan_reply", lambda j, d: j["connections"].pop("Stored"), "orphan nodes (no incoming link, not a trigger)", ()),
 ("cycle_only", m_cycle, "unreachable from any trigger ['CycA', 'CycB']", ()),
 ("dangling", lambda j, d: j["connections"]["Item"]["main"][0].append(link("Ghost")), "dangling target 'Ghost'", ()),
 ("duplicate_name", m_dupname, "duplicate names ['Item']", ()),
 ("name_case_dup", m_case, "names that differ only by case or spaces", ()),
 ("duplicate_id", m_dupid, "duplicate node ids ['a1']", ()),
 ("trigger_has_input", m_trigin, "incoming link Item -> Receive into a trigger node", ()),
 ("no_trigger", m_notrig, "no trigger node in file", ()),
 ("if_one_branch", lambda j, d: j["connections"]["Claimed"]["main"].pop(), "IF node Claimed lacks output(s) [1]", ()),
 ("switch_gap", m_switch, "SWITCH node Sw lacks output(s) [1]", ()),
 ("errout_unwired", lambda j, d: node(j, "Claim").__setitem__("onError", "continueErrorOutput"), "onError=continueErrorOutput but main[1] is missing", ()),
 ("bad_onerror_value", lambda j, d: node(j, "Claim").__setitem__("onError", "ignore"), "onError='ignore' is not one of", ()),
 ("bad_maxtries", lambda j, d: node(j, "Claim").update({"retryOnFail": True, "maxTries": 9}), "maxTries=9", ()),
 ("bad_retry_type", lambda j, d: node(j, "Claim").__setitem__("retryOnFail", "yes"), "retryOnFail='yes' is not a boolean", ()),
 ("bad_alwaysoutput_type", lambda j, d: node(j, "Claim").__setitem__("alwaysOutputData", "yes"), "alwaysOutputData='yes' is not a boolean", ()),
 ("bad_ref", lambda j, d: node(j, "ReplyStored")["parameters"].__setitem__("responseBody", "={{ $('Nope').item.json.x }}"), "refers to $('Nope')", ()),
 ("bad_items_ref", lambda j, d: node(j, "ReplyStored")["parameters"].__setitem__("responseBody", "={{ $items(\"Nope\")[0] }}"), "refers to $('Nope')", ()),
 ("bad_node_dot_ref", lambda j, d: node(j, "ReplyStored")["parameters"].__setitem__("responseBody", "={{ $node.Nope.json.x }}"), "refers to $('Nope')", ()),
 ("secret_sk", m_secret, "secret-looking value (sk- style key)", ()),
 ("secret_aws", m_aws, "secret-looking value (AWS access key id)", ()),
 ("secret_under_key", m_secretkey, "literal value under key 'apiKey'", ()),
 ("cred_block_missing", m_nocred, "node Claim (postgres) has no credentials block", ()),
 ("cred_name_empty", m_credname, "credential 'postgres' has no name", ()),
 ("cred_id_missing", m_credid, "credential 'postgres' has no id", ()),
 ("webhook_path_no_reply", m_noreply, "path(s) end WITHOUT respondToWebhook at ['Stored']", ()),
 ("webhook_dead_branch", m_dead_branch, "path(s) end WITHOUT respondToWebhook at ['DeadEnd']", ()),
 ("webhook_no_reply_node", m_noresp_any, "no respondToWebhook reachable", ()),
 ("sticky_only_file", m_sticky_only, "sticky-note-only file", ()),
 ("missing_position", m_nopos, "node Item lacks position [x, y]", ()),
 ("count_wrong", lambda j, d: j["nodes"].pop(-1) and False or None, "node count 11 != expected 12", ()),
 ("duplicate_webhook_path", m_dupwh, "two webhooks share method+path", ()),
 ("parse_fail", m_parse, "parse failure", ()),
 ("missing_file", m_missing, "file list", ()),
 ("webhook_auth_required", lambda j, d: None, "webhook Receive has no authentication", ("--require-webhook-auth",)),
]
CONTROLS = [("control_unmutated", lambda j, d: None, ()), ("control_sticky_note_present_and_unlinked", m_sticky_ok, ("--expect", "mf-form.json=13:11")), ("control_aws_example_key_allowed", m_aws_example, ()), ("control_self_reference_is_warn_only", m_selfref, ())]
def run(c, name, tmpl):
    r = subprocess.run(c, capture_output=True, text=True); out = r.stdout + r.stderr
    open("%s/%s.out" % (OUT, name), "w").write("$ " + " ".join(c) + "\n" + out + "exit=%d\n" % r.returncode); return r.returncode, out
def make(name, mut, work, src, which="mf-form.json"):
    d = "%s/%s" % (work, name); shutil.copytree(src, d)
    if not os.path.isfile(d + "/" + which): return d
    j = json.load(open(d + "/" + which)); r = mut(j, d)
    if r is not False: json.dump(j, open(d + "/" + which, "w"), indent=1)
    return d
def main():
    shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT); work = tempfile.mkdtemp(prefix="fc-selftest-"); ok = bad = 0
    open(OUT + "/CHECK-COMMAND.txt", "w").write("fixed command (D = mutated copy of the pristine flows): " + " ".join(cmd("D")) + "\nplus the extra option where a case lists one\n")
    for name, mut, extra in CONTROLS:
        rc, out = run(cmd(make(name, mut, work, PRIS), extra), name, None); good = rc == 0
        print("%-46s exit=%d expected 0   %s" % (name, rc, "as expected" if good else "NOT AS EXPECTED")); ok += good; bad += not good
    for name, mut, text, extra in M:
        rc, out = run(cmd(make(name, mut, work, PRIS), extra), name, None); good = rc == 1 and text in out
        print("%-46s exit=%d expected 1   named_line_present=%s %s" % (name, rc, text in out, "as expected" if good else "NOT AS EXPECTED")); ok += good; bad += not good
    if PATCHED:
        pc = ["python3", "-I", CK, "D", "--baseline", PRIS] + PCOUNTS + ["--patch-checks", "F002,F008", "--diff-base", PRIS, "--allow", "F002,F008", "--quiet-info"]
        def pcmd(d): return [d if x == "D" else x for x in pc]
        P = [("patched_control", lambda j, d: None, 0, ""),
             ("patched_wrong_code", lambda j, d: node(j, "ReplyBadKey")["parameters"]["options"].__setitem__("responseCode", 400), 1, "ReplyBadKey responseCode is 400 expected 422"),
             ("patched_failreply_cut", lambda j, d: j["connections"].__setitem__("ReplyStoreFail", {"main": [[link("Claimed")]]}), 1, "unexplained connection change for source ReplyStoreFail"),
             ("patched_errlink_cut", lambda j, d: j["connections"]["Claim"]["main"].pop(), 1, "onError=continueErrorOutput but main[1] is missing"),
             ("patched_badkey_reply_cut", lambda j, d: j["connections"].__setitem__("ReplyBadKey", {"main": [[link("Item")]]}), 1, "unexplained connection change for source ReplyBadKey")]
        for name, mut, want, text in P:
            d = make(name, mut, work, PATCHED); rc, out = run(pcmd(d), name, None); good = rc == want and text in out
            print("%-46s exit=%d expected %d   named_line_present=%s %s" % (name, rc, want, text in out, "as expected" if good else "NOT AS EXPECTED")); ok += good; bad += not good
    print("SELFTEST: %d as expected, %d not as expected (%d negative cases + %d controls on pristine%s)" % (ok, bad, len(M), len(CONTROLS), ", 4 negatives + 1 control on patched" if PATCHED else ""))
    shutil.rmtree(work, ignore_errors=True); return 1 if bad else 0
sys.exit(main())
