#!/usr/bin/env python3
"""Self-test of check_flows.py (F8, round 1 fixes). Stdlib only. Nothing is run in n8n. Made-up data only.

Usage:  selftest.py PRISTINE_REAL_DIR [PATCHED_REAL_DIR [PRISTINE_FILM_DIR]]
  PRISTINE_REAL_DIR  committed folder handover/demo/n8n-flows-real-v5
  PATCHED_REAL_DIR   generated folder (run_all.sh makes it: <work dir>/g/real); enables the patch cases
  PRISTINE_FILM_DIR  committed folder handover/demo/n8n-flows-film-v5; enables the film-file cases
Environment (both optional, both documented here and nowhere else):
  FC_CK   path of another checker script to run the same cases against (default: check_flows.py next to this file).
          Used to prove the new cases fail on the old patch-apply/check_flows.py.
  FC_OUT  folder for the raw .out files (default: selftest-output/ next to this file). It is emptied first, but only if it is
          empty, missing, or holds the marker file CHECK-COMMAND.txt of an earlier run; otherwise the self-test stops.
Each case copies a pristine folder, plants ONE defect, runs the checker, and requires ALL of:
  (1) the exit code (1 for a FAIL case, 0 for a WARN case or a control),
  (2) a line that STARTS with FAIL (or WARN) and holds the named text,
  (3) for FAIL cases: every FAIL line is the named cause or a listed knock-on of it (so an unrelated FAIL cannot hide behind it),
  (4) for WARN cases: no FAIL line except listed knock-ons of the planted node, and the same WARN line is not already in the unmutated control.
Expected node and connection counts are recomputed from the mutated file so a count mismatch is not a knock-on, except in the case that tests it.
Generic cases run on 4 real files and 1 film file; cases that cannot apply to a file are printed as skipped."""
import json, os, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
CK = os.environ.get("FC_CK") or HERE + "/check_flows.py"
OUT = os.environ.get("FC_OUT") or HERE + "/selftest-output"
args = [a for a in sys.argv[1:]]
if not args: print(__doc__); sys.exit(2)
PRIS = args[0]; PATCHED = args[1] if len(args) > 1 else None; FILM = args[2] if len(args) > 2 else None
FILES = ["mf-form.json", "mf-hook.json", "mf-recovery.json", "mf-sub-crm-mail.json"]
PCOUNTS = {"mf-form.json": (15, 14), "mf-hook.json": (15, 14), "mf-recovery.json": (10, 9), "mf-sub-crm-mail.json": (20, 26)}
SKIP = "SKIP"

def link(dst, i=0): return {"node": dst, "type": "main", "index": i}
def noop(name): return {"name": name, "type": "n8n-nodes-base.noOp", "typeVersion": 1, "position": [0, 0], "parameters": {}}
def sticky(name, text="note only"): return {"name": name, "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": [0, 0], "parameters": {"content": text}}
def node(j, n): return [x for x in j["nodes"] if x["name"] == n][0]
def has(j, n): return any(x["name"] == n for x in j["nodes"])
def trig(j): return [x["name"] for x in j["nodes"] if x["type"].endswith("Trigger") or x["type"] == "n8n-nodes-base.webhook"]
def first_nt(j): return [x for x in j["nodes"] if x["name"] not in trig(j) and x["type"] != "n8n-nodes-base.stickyNote"][0]
def first_of(j, short):
    r = [x for x in j["nodes"] if x["type"].split(".")[-1] == short]; return r[0] if r else None
def a_source(j): return [s for s, o in j["connections"].items() if o.get("main") and o["main"][0]][0]
def parts(*p): return "".join(p)

# ---- generic mutators (work on any of the flow files) ----
def g_orphan(j, d): j["nodes"].append(noop("OrphanX"))
def g_cycle(j, d):
    j["nodes"] += [noop("CycA"), noop("CycB")]; j["connections"]["CycA"] = {"main": [[link("CycB")]]}; j["connections"]["CycB"] = {"main": [[link("CycA")]]}
def g_dangling(j, d): j["connections"][a_source(j)]["main"][0].append(link("Ghost"))
def g_dupname(j, d): nm = first_nt(j)["name"]; j["nodes"].append(noop(nm)); j["connections"][a_source(j)]["main"][0].append(link(nm))
def g_case(j, d): nm = first_nt(j)["name"]; j["nodes"].append(noop(nm.lower() if nm.lower() != nm else nm.upper())); j["connections"][a_source(j)]["main"][0].append(link(j["nodes"][-1]["name"]))
def g_dupid(j, d): j["nodes"][0]["id"] = "a1"; j["nodes"][1]["id"] = "a1"
def g_trigin(j, d): j["connections"].setdefault(first_nt(j)["name"], {"main": [[]]}); j["connections"][first_nt(j)["name"]].setdefault("main", [[]]); j["connections"][first_nt(j)["name"]]["main"][0].append(link(trig(j)[0]))
def g_sticky_link(j, d): j["nodes"].append(sticky("Note")); j["connections"]["Note"] = {"main": [[link(first_nt(j)["name"])]]}
def g_sticky_ok(j, d): j["nodes"].append(sticky("Note"))
def put_note(j, v): first_nt(j)["parameters"]["note"] = v
def g_secret_sk(j, d): put_note(j, "sk-" + "A1b2C3d4" * 3)
def g_secret_aws(j, d): put_note(j, "AKIA" + "ABCDEFGHIJKLMNOP")
def g_aws_example(j, d): put_note(j, "AKIA" + "IOSFODNN7EXAMPLE")
def g_secret_gh(j, d): put_note(j, parts("gh", "p_", "a1B2c3D4" * 4))
def g_secret_slack(j, d): put_note(j, parts("xo", "xb-", "1234567890-", "abcdefghij"))
def g_secret_pk(j, d): put_note(j, parts("-----", "BEGIN RSA PRIVATE", " KEY-----"))
def g_secret_jwt(j, d): put_note(j, parts("ey", "J", "hbGciOiJIUzI1NiJ9", ".", "eyJzdWIiOiIxMjM0NTY3ODkw", ".sig"))
def g_secret_url(j, d): put_note(j, parts("postgres://", "app:", "hunter2xyz", "@host/db"))
def g_secret_bearer(j, d): put_note(j, parts("Bearer ", "abcdef0123456789xyz"))
def g_secret_key(j, d): first_nt(j)["parameters"]["apiKey"] = "".join(["h", "unter", "2", "xyz"])
def g_secret_key_caps(j, d): first_nt(j)["parameters"]["apiKey"] = "".join(["HUNTER", "2XYZ", "ABC"])   # the old ALL-CAPS bypass
def g_secret_sticky(j, d): j["nodes"].append(sticky("Note", "my key " + "sk-" + "A1b2C3d4" * 3))
def g_secret_top(j, d): j["pinData"] = {"x": [{"json": {"note": "sk-" + "A1b2C3d4" * 3}}]}
def g_secret_topkey(j, d): j["staticData"] = {"password": "".join(["h", "unter", "2", "xyz"])}
def g_passthrough(j, d): first_nt(j)["parameters"]["passThrough"] = "some ordinary text value"
def g_env_ok(j, d): first_nt(j)["parameters"]["apiKey"] = "={{ $env.SOME_NAME }}"
def g_cred_missing(j, d):
    n = first_of(j, "postgres") or first_of(j, "emailSend")
    if not n: return SKIP
    n.pop("credentials")
def g_cred_noname(j, d):
    n = first_of(j, "postgres") or first_of(j, "emailSend")
    if not n: return SKIP
    k = list(n["credentials"])[0]; n["credentials"][k]["name"] = ""
def g_cred_noid(j, d):
    n = first_of(j, "postgres") or first_of(j, "emailSend")
    if not n: return SKIP
    k = list(n["credentials"])[0]; n["credentials"][k].pop("id")
def g_http_auth(j, d): j["nodes"].append({"name": "Http", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4, "position": [0, 0], "parameters": {"authentication": "genericCredentialType", "method": "GET"}}); j["connections"][a_source(j)]["main"][0].append(link("Http"))
def g_nopos(j, d): first_nt(j).pop("position")
def g_notypever(j, d): first_nt(j).pop("typeVersion")
def g_notrig(j, d):
    for n in j["nodes"]:
        if n["name"] in trig(j): n["type"] = "n8n-nodes-base.noOp"
def g_disabled(j, d): first_nt(j)["disabled"] = True
def g_badretry(j, d): first_nt(j)["retryOnFail"] = "yes"
def g_badaod(j, d): first_nt(j)["alwaysOutputData"] = "yes"
def g_badonerr(j, d): first_nt(j)["onError"] = "ignore"
def g_maxtries(j, d): n = first_nt(j); n.update({"retryOnFail": True, "maxTries": 9})
def g_wait(j, d): n = first_nt(j); n.update({"retryOnFail": True, "maxTries": 3, "waitBetweenTries": 9000})
def g_tries_noretry(j, d): n = first_nt(j); n["maxTries"] = 3; n["retryOnFail"] = False
def g_badref(j, d): first_nt(j)["parameters"]["note"] = "={{ $('Nope').item.json.x }}"
def g_badref_items(j, d): first_nt(j)["parameters"]["note"] = '={{ $items("Nope")[0] }}'
def g_badref_dot(j, d): first_nt(j)["parameters"]["note"] = "={{ $node.Nope.json.x }}"
def g_selfref(j, d): n = first_nt(j); n["parameters"]["note"] = "={{ $('%s').item.json.x }}" % n["name"]
def g_prev(j, d): first_nt(j)["parameters"]["note"] = "={{ $prevNode.name }}"
def g_notup(j, d):
    j["nodes"] += [noop("LateA"), noop("LateB")]; j["connections"][a_source(j)]["main"][0].append(link("LateA")); j["connections"][a_source(j)]["main"][0].append(link("LateB"))
    node(j, "LateA")["parameters"]["note"] = "={{ $('LateB').item.json.x }}"
def g_shape_conn(j, d): j["connections"][a_source(j)] = "x"
def g_shape_link(j, d): j["connections"][a_source(j)]["main"][0].append({"type": "main", "index": 0})
def g_shape_node(j, d): j["nodes"].append("not a node")
def g_shape_params(j, d): first_nt(j)["parameters"] = []
def g_shape_idx(j, d): j["connections"][a_source(j)]["main"][0].append({"node": first_nt(j)["name"], "type": "main", "index": "0"})
def g_shape_top(j, d): return ("REPLACE", [j])          # whole file becomes a JSON list
def g_noname(j, d): first_nt(j).pop("name")
def g_nonlist_nodes(j, d): j["nodes"] = {"a": 1}
def g_parse(j, d): open(d + "/" + FOCUS, "w").write("{bad"); return False
def g_missing(j, d): os.remove(d + "/" + FOCUS); return False
def g_sticky_only(j, d): j["nodes"] = [sticky("Note", "x")]; j["connections"] = {}
def g_trig_sticky(j, d): j["nodes"] = [x for x in j["nodes"] if x["name"] in trig(j)] + [sticky("Note")]; j["connections"] = {}
def g_dupwh(j, d):
    o = [f for f in FILES if f != FOCUS and os.path.isfile(d + "/" + f)][0]; h = json.load(open(d + "/" + o))
    for n in j["nodes"]:
        if n["type"] == "n8n-nodes-base.webhook":
            for m in h["nodes"]:
                if m["type"] == "n8n-nodes-base.webhook": m["parameters"]["path"] = n["parameters"]["path"]; m["parameters"]["httpMethod"] = n["parameters"].get("httpMethod", "GET")
            json.dump(h, open(d + "/" + o, "w")); return None
    return SKIP
def g_dupwhid(j, d):
    o = [f for f in FILES if f != FOCUS and os.path.isfile(d + "/" + f)][0]; h = json.load(open(d + "/" + o)); ok = False
    for n in j["nodes"]:
        if n["type"] == "n8n-nodes-base.webhook":
            n["webhookId"] = "wid-1"
            for m in h["nodes"]:
                if m["type"] == "n8n-nodes-base.webhook": m["webhookId"] = "wid-1"; ok = True
    if not ok: return SKIP
    json.dump(h, open(d + "/" + o, "w"))
def g_noresp_any(j, d):
    k = 0
    for n in j["nodes"]:
        if n["type"] == "n8n-nodes-base.respondToWebhook": n["type"] = "n8n-nodes-base.noOp"; k += 1
    if not k: return SKIP
def g_resp_disabled(j, d):
    k = 0
    for n in j["nodes"]:
        if n["type"] == "n8n-nodes-base.respondToWebhook": n["disabled"] = True; k += 1
    if not k: return SKIP
def g_wh_disabled(j, d):
    k = 0
    for n in j["nodes"]:
        if n["type"] == "n8n-nodes-base.webhook": n["disabled"] = True; k += 1
    if not k: return SKIP
def g_noreply_dead(j, d):
    w = [n["name"] for n in j["nodes"] if n["type"] == "n8n-nodes-base.webhook"]
    if not w: return SKIP
    j["nodes"].append(noop("DeadEnd")); j["connections"][w[0]]["main"][0].append(link("DeadEnd"))
def g_formtrig(j, d):
    w = [n for n in j["nodes"] if n["type"] == "n8n-nodes-base.webhook"]
    if not w: return SKIP
    w[0]["type"] = "n8n-nodes-base.formTrigger"
def g_silent(j, d):
    c = [x for x in j["nodes"] if x["type"].split(".")[-1] in ("postgres", "httpRequest") and x.get("onError") != "continueRegularOutput"]
    if not c: return SKIP
    c[0]["onError"] = "continueRegularOutput"
def g_write_silent(j, d):
    n = first_of(j, "emailSend")
    if not n: return SKIP
    n["onError"] = "continueRegularOutput"
def g_aod_err(j, d):
    n = first_of(j, "postgres")
    if not n: return SKIP
    n["onError"] = "continueErrorOutput"; n["alwaysOutputData"] = True
    j["connections"].setdefault(n["name"], {"main": [[]]}); m = j["connections"][n["name"]]["main"]
    while len(m) < 2: m.append([])
    m[1] = [link([x["name"] for x in j["nodes"] if x["name"] not in trig(j) and x["name"] != n["name"] and x["type"] != "n8n-nodes-base.stickyNote"][0])]
def g_errout_unwired(j, d):
    n = first_of(j, "postgres")
    if not n: return SKIP
    n["onError"] = "continueErrorOutput"
    m = j["connections"].get(n["name"], {}).get("main", [])
    if len(m) > 1: m.pop()
def g_if_one_branch(j, d):
    n = first_of(j, "if")
    if not n: return SKIP
    m = j["connections"][n["name"]]["main"]
    if len(m) < 2 or not m[1]: return SKIP
    m.pop()
def g_switch_gap(j, d):
    j["nodes"].append({"name": "Sw", "type": "n8n-nodes-base.switch", "typeVersion": 3, "position": [0, 0], "parameters": {"rules": {"values": [{}, {}]}}})
    j["connections"][a_source(j)]["main"][0].append(link("Sw")); j["connections"]["Sw"] = {"main": [[link(first_nt(j)["name"])]]}
def g_filter_ok(j, d):   # a Filter node with ONE output must not FAIL
    j["nodes"].append({"name": "Flt", "type": "n8n-nodes-base.filter", "typeVersion": 2, "position": [0, 0], "parameters": {}})
    j["connections"][a_source(j)]["main"][0].append(link("Flt")); j["connections"]["Flt"] = {"main": [[link(first_nt(j)["name"])]]}
def g_if_err_last(j, d):   # IF with continueErrorOutput: error output is index 2
    j["nodes"].append({"name": "IfX", "type": "n8n-nodes-base.if", "typeVersion": 2, "position": [0, 0], "parameters": {}, "onError": "continueErrorOutput"})
    t = first_nt(j)["name"]; j["connections"][a_source(j)]["main"][0].append(link("IfX")); j["connections"]["IfX"] = {"main": [[link(t)], [link(t)]]}
def g_src_ghost(j, d): j["connections"]["Ghost"] = {"main": [[link(first_nt(j)["name"])]]}
def g_env_read(j, d): first_nt(j)["parameters"]["note"] = "={{ $env.SOME_NAME }}"
def g_wrongcount(j, d): j["nodes"].append(sticky("Extra"))   # a note changes the node count and nothing else

# ---- file-specific mutators ----
def f_noreply(j, d): j["connections"]["Stored"] = {"main": [[]]}
def f_bad_ref_reply(j, d): node(j, "ReplyStored")["parameters"]["responseBody"] = "={{ $('Nope').item.json.x }}"
def f_selfref_ok(j, d): node(j, "Valid")["parameters"]["note"] = "={{ $('Valid').item.json.x }}"

# case: (name, mutator, level, text, extra checker options, knock-on texts, files)   level: FAIL, WARN or None (control)
GEN5 = "gen"
G = [
 ("orphan_node", g_orphan, "FAIL", "orphan nodes (no incoming link, not a trigger)", (), ["unreachable"]),
 ("cycle_only", g_cycle, "FAIL", "unreachable from any trigger ['CycA', 'CycB']", (), []),
 ("dangling", g_dangling, "FAIL", "dangling target 'Ghost'", (), []),
 ("duplicate_name", g_dupname, "FAIL", "duplicate names", (), ["names that differ only by case or spaces"]),
 ("name_case_dup", g_case, "FAIL", "names that differ only by case or spaces", (), ["WITHOUT respondToWebhook"]),
 ("duplicate_id", g_dupid, "FAIL", "duplicate node ids ['a1']", (), []),
 ("trigger_has_input", g_trigin, "FAIL", "into a trigger node", (), []),
 ("sticky_with_link", g_sticky_link, "FAIL", "sticky note 'Note' has a connection", (), []),
 ("secret_sk", g_secret_sk, "FAIL", "secret-looking value (sk- style key)", (), []),
 ("secret_aws", g_secret_aws, "FAIL", "secret-looking value (AWS access key id)", (), []),
 ("secret_github", g_secret_gh, "FAIL", "secret-looking value (GitHub token)", (), []),
 ("secret_slack", g_secret_slack, "FAIL", "secret-looking value (Slack token)", (), []),
 ("secret_private_key", g_secret_pk, "FAIL", "secret-looking value (private key block)", (), []),
 ("secret_jwt", g_secret_jwt, "FAIL", "secret-looking value (JWT)", (), []),
 ("secret_url_password", g_secret_url, "FAIL", "secret-looking value (password inside a URL)", (), []),
 ("secret_bearer", g_secret_bearer, "FAIL", "secret-looking value (literal Bearer value)", (), []),
 ("secret_under_key", g_secret_key, "FAIL", "literal value under key 'apiKey'", (), []),
 ("secret_under_key_all_caps", g_secret_key_caps, "FAIL", "literal value under key 'apiKey'", (), []),
 ("secret_in_sticky_note", g_secret_sticky, "FAIL", "secret-looking value (sk- style key)", (), []),
 ("secret_top_level_value", g_secret_top, "FAIL", "top-level data (not a node): secret-looking value (sk- style key)", (), []),
 ("secret_top_level_key", g_secret_topkey, "FAIL", "top-level data (not a node): secret-looking value (literal value under key 'password')", (), []),
 ("cred_block_missing", g_cred_missing, "FAIL", "has no credentials block", (), []),
 ("cred_name_empty", g_cred_noname, "FAIL", "has no name", (), []),
 ("cred_id_missing", g_cred_noid, "FAIL", "has no id", (), []),
 ("httprequest_auth_no_credentials", g_http_auth, "FAIL", "(httpRequest) has no credentials block", (), ["WITHOUT respondToWebhook"]),
 ("missing_position", g_nopos, "FAIL", "lacks position [x, y]", (), []),
 ("missing_typeversion", g_notypever, "FAIL", "lacks a numeric typeVersion", (), []),
 ("no_trigger", g_notrig, "FAIL", "no enabled trigger node in file", (), ["unreachable", "orphan"]),
 ("bad_retry_type", g_badretry, "FAIL", "retryOnFail='yes' is not a boolean", (), []),
 ("bad_alwaysoutput_type", g_badaod, "FAIL", "alwaysOutputData='yes' is not a boolean", (), []),
 ("bad_ref", g_badref, "FAIL", "refers to $('Nope')", (), []),
 ("bad_items_ref", g_badref_items, "FAIL", "refers to $('Nope')", (), []),
 ("bad_node_dot_ref", g_badref_dot, "FAIL", "refers to $('Nope')", (), []),
 ("shape_connection_not_object", g_shape_conn, "FAIL", "are not an object", (), []),
 ("shape_link_without_node", g_shape_link, "FAIL", "a link has no text 'node'", (), []),
 ("shape_node_not_object", g_shape_node, "FAIL", "is not an object", (), []),
 ("shape_parameters_not_object", g_shape_params, "FAIL", "parameters is not an object", (), []),
 ("shape_top_level_list", g_shape_top, "FAIL", "top level is not a JSON object", (), []),
 ("shape_nodes_not_list", g_nonlist_nodes, "FAIL", "no nodes list", (), []),
 ("shape_node_without_name", g_noname, "FAIL", "lacks a text name or type", (), []),
 ("shape_link_index_text", g_shape_idx, "FAIL", "lacks a valid type/index", (), []),
 ("sticky_only_file", g_sticky_only, "FAIL", "sticky-note-only file", (), ["no enabled trigger node in file"]),
 ("trigger_plus_notes_only", g_trig_sticky, "FAIL", "holds only trigger and sticky notes", (), ["no respondToWebhook reachable", "WITHOUT respondToWebhook"]),
 ("parse_fail", g_parse, "FAIL", "parse failure", (), []),
 ("missing_file", g_missing, "FAIL", "file list", (), []),
 ("webhook_path_reused_in_other_file", g_dupwh, "FAIL", "two webhooks share method+path", (), []),
 ("webhook_id_reused_in_other_file", g_dupwhid, "FAIL", "two webhooks share webhookId", (), []),
 ("webhook_no_reply_node", g_noresp_any, "FAIL", "no respondToWebhook reachable", (), ["WITHOUT respondToWebhook"]),
 ("webhook_reply_node_disabled", g_resp_disabled, "FAIL", "no respondToWebhook reachable", (), ["WITHOUT respondToWebhook"]),
 ("webhook_disabled_no_trigger", g_wh_disabled, "FAIL", "no enabled trigger node in file", (), ["unreachable"]),
 ("webhook_dead_branch", g_noreply_dead, "FAIL", "WITHOUT respondToWebhook at ['DeadEnd']", (), []),
 ("webhook_without_auth_strict", None, "FAIL", "has no authentication", ("--require-webhook-auth",), []),
 ("form_trigger_without_auth_strict", g_formtrig, "FAIL", "has no authentication setting", ("--require-webhook-auth",), ["unreachable", "orphan", "has no authentication", "WITHOUT respondToWebhook", "no respondToWebhook"]),
 ("connection_source_not_a_node", g_src_ghost, "FAIL", "connection source 'Ghost' is not a node", (), []),
 ("env_read_blocked_strict", g_env_read, "FAIL", "reads $env", ("--block-env-access",), []),
 ("wrong_count", g_wrongcount, "FAIL", "node count", (), []),
 # WARN cases
 ("bad_onerror_value_is_warn", g_badonerr, "WARN", "n8n rule UNVERIFIED", (), []),
 ("max_tries_out_of_range_is_warn", g_maxtries, "WARN", "maxTries=9", (), []),
 ("wait_out_of_range_is_warn", g_wait, "WARN", "waitBetweenTries=9000", (), []),
 ("max_tries_without_retry_on_fail", g_tries_noretry, "WARN", "sets maxTries/waitBetweenTries but retryOnFail is not true", (), []),
 ("disabled_node", g_disabled, "WARN", "is disabled", (), []),
 ("read_node_not_upstream", g_notup, "WARN", "which is not upstream of it", (), ["WITHOUT respondToWebhook"]),
 ("read_own_output", g_selfref, "WARN", "reads its own output", (), []),
 ("prev_node_used", g_prev, "WARN", "uses $prevNode", (), []),
 ("silent_error_external_call", g_silent, "WARN", "continueRegularOutput (an error becomes normal-looking data)", (), []),
 ("write_node_continues_on_error", g_write_silent, "WARN", "write node", (), []),
 ("always_output_with_error_output", g_aod_err, "WARN", "alwaysOutputData together with continueErrorOutput", (), []),
 ("switch_unwired_output_is_warn", g_switch_gap, "WARN", "SWITCH node Sw has unwired output(s)", (), []),
 ("env_read_default_is_warn", g_env_read, "WARN", "$env.SOME_NAME", (), []),
 ("webhook_without_auth_default", None, "WARN", "has no authentication", (), []),
 ("form_trigger_without_auth_default", g_formtrig, "WARN", "has no authentication setting", (), []),
]
# cases that need a particular node of the real form flow (run on mf-form and mf-hook only)
FH = [
 ("error_output_unwired", g_errout_unwired, "FAIL", "its error output main[1]", (), []),
 ("if_one_branch", g_if_one_branch, "FAIL", "IF node", (), ["orphan", "unreachable"]),
 ("if_error_output_is_last_output", g_if_err_last, "FAIL", "its error output main[2]", (), []),
 ("reply_after_store_cut", f_noreply, "FAIL", "WITHOUT respondToWebhook at ['Stored']", (), ["orphan", "unreachable"]),
]
CONTROLS = [
 ("control_unmutated", None, ()),
 ("control_sticky_note_present_and_unlinked", g_sticky_ok, ()),
 ("control_aws_example_key_allowed", g_aws_example, ()),
 ("control_pass_through_key_is_not_a_secret", g_passthrough, ()),
 ("control_env_reference_is_not_a_secret", g_env_ok, ()),
 ("control_filter_with_one_output", g_filter_ok, ()),
]

FOCUS = "mf-form.json"
def count(j):
    try: return len(j["nodes"]), sum(1 for o in j["connections"].values() for l in o.values() for ll in l for c in (ll or []))
    except Exception: return None
def run(c, name):
    r = subprocess.run(c, capture_output=True, text=True); out = r.stdout + r.stderr
    open("%s/%s.out" % (OUT, name), "w").write("$ " + " ".join(c) + "\n" + out + "exit=%d\n" % r.returncode); return r.returncode, out
def make(name, mut, work, src, which, keep_counts=False):
    """copy src, mutate file `which`; returns (dir, skipped, expect options)"""
    global FOCUS
    FOCUS = which
    d = "%s/%s" % (work, name); shutil.copytree(src, d)
    if not os.path.isfile(d + "/" + which): return d, True, []
    if mut is not None:
        j = json.load(open(d + "/" + which)); r = mut(j, d)
        if r == SKIP: return d, True, []
        if isinstance(r, tuple) and r and r[0] == "REPLACE": j = r[1]
        if r is not False: json.dump(j, open(d + "/" + which, "w"), indent=1)
    exp = []
    for f in FILES:
        if not os.path.isfile(d + "/" + f): continue
        try: j = json.load(open(d + "/" + f)); c = count(j)
        except Exception: c = None
        if f == which and keep_counts: c = count(json.load(open(src + "/" + f)))
        if c: exp += ["--expect", "%s=%d:%d" % (f, c[0], c[1])]
    return d, False, exp
def lines_of(out, level): return [l for l in out.splitlines() if l.startswith(level + " ")]

def main():
    if os.path.isdir(OUT) and os.listdir(OUT) and not os.path.isfile(OUT + "/CHECK-COMMAND.txt"):
        print("REFUSED: %s is not empty and is not an earlier self-test output folder; set FC_OUT to a new or empty folder" % OUT); return 2
    shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT); work = tempfile.mkdtemp(prefix="fc-selftest-"); ok = bad = skipped = 0
    open(OUT + "/CHECK-COMMAND.txt", "w").write("checker: %s\nfixed command per case: python3 -I CHECKER D --baseline PRISTINE <--expect lines recomputed from D> --quiet-info [extra option]\n" % CK)
    targets = [("real", PRIS, f) for f in FILES]
    if FILM: targets.append(("film", FILM, "mf-form.json"))
    base_out, base_warn = {}, {}
    def cmd(d, src, exp, extra=()): return ["python3", "-I", CK, d, "--baseline", src] + exp + ["--quiet-info"] + list(extra)
    def report(label, good, why=""):
        nonlocal ok, bad
        print("%-72s %s" % (label, "as expected" if good else "NOT AS EXPECTED " + why)); ok += good; bad += not good
    # controls (one per target for the plain control, form file for the rest)
    for tv, src, f in targets:
        d, sk, exp = make("control_unmutated@%s-%s" % (tv, f), None, work, src, f)
        rc, out = run(cmd(d, src, exp), "control_unmutated@%s-%s" % (tv, f)); base_out[(tv, f)] = out; base_warn[(tv, f)] = {l.replace(d, "D") for l in lines_of(out, "WARN")}
        must = ["credentials (node, kind, name, id):", "Passing this check does NOT mean the flows are ready to film.", "Known open problems:", "Not proven:"]
        miss = [m for m in must if m not in out]
        report("control_unmutated@%s-%s (exit 0, no FAIL, closing block)" % (tv, f), rc == 0 and not lines_of(out, "FAIL") and not miss, "rc=%d fails=%d missing=%s" % (rc, len(lines_of(out, "FAIL")), miss))
    mf = [t for t in targets if t[2] == "mf-form.json"]
    for name, mut, extra in CONTROLS[1:]:
        for tv, src, f in mf:
            n = "%s@%s-%s" % (name, tv, f); d, sk, exp = make(n, mut, work, src, f)
            rc, out = run(cmd(d, src, exp, extra), n); report(n + " (exit 0, no FAIL)", rc == 0 and not lines_of(out, "FAIL"), "rc=%d fails=%s" % (rc, lines_of(out, "FAIL")[:2]))
    # the reply-gap and no-auth WARN must be listed as known open problems on the unmutated form file
    out = base_out[("real", "mf-form.json")]
    report("control_known_problems_are_listed (REPLY GAP and no authentication counted)", "REPLY GAP" in out and any(l.startswith("  - ") and "no authentication" in l for l in out.splitlines()))
    # negative / warn cases
    def one(name, mut, level, text, extra, also, tv, src, f):
        nonlocal skipped
        n = "%s@%s-%s" % (name, tv, f); d, sk, exp = make(n, mut, work, src, f, keep_counts=(name == "wrong_count"))
        if sk: skipped += 1; print("%-72s skipped (not applicable to this file)" % n); return
        rc, out = run(cmd(d, src, exp, extra), n); fl, wl = lines_of(out, "FAIL"), lines_of(out, "WARN")
        if level == "FAIL":
            named = [l for l in fl if text in l]; stray = [l for l in fl if text not in l and not any(a in l for a in also)]
            good = rc == 1 and bool(named) and not stray; why = "rc=%d named=%d stray=%s" % (rc, len(named), [s[:90] for s in stray[:2]])
        else:
            named = [l for l in wl if text in l]; fresh = [l for l in named if mut is None or l.replace(d, "D") not in base_warn.get((tv, f), set())]
            stray = [l for l in fl if not any(a in l for a in also)]
            good = rc == (1 if fl else 0) and not stray and bool(fresh); why = "rc=%d stray_fails=%s new_named_warn=%d" % (rc, [x[:90] for x in stray[:2]], len(fresh))
        report("%s (%s, exit %d)" % (n, level, 1 if level == "FAIL" else 0), good, why)
    for name, mut, level, text, extra, also in G:
        for tv, src, f in targets: one(name, mut, level, text, extra, also, tv, src, f)
    for name, mut, level, text, extra, also in FH:
        for tv, src, f in [t for t in targets if t[2] in ("mf-form.json", "mf-hook.json")]: one(name, mut, level, text, extra, also, tv, src, f)
    if PATCHED:
        P = [("patched_control", None, 0, ""),
             ("patched_wrong_code", lambda j, d: node(j, "ReplyBadKey")["parameters"]["options"].__setitem__("responseCode", 400), 1, "ReplyBadKey responseCode is 400 expected 422"),
             ("patched_failreply_cut", lambda j, d: j["connections"].__setitem__("ReplyStoreFail", {"main": [[link("Claimed")]]}), 1, "unexplained connection change for source ReplyStoreFail"),
             ("patched_errlink_cut", lambda j, d: j["connections"]["Claim"]["main"].pop(), 1, "its error output main[1]"),
             ("patched_badkey_reply_cut", lambda j, d: j["connections"].__setitem__("ReplyBadKey", {"main": [[link("Item")]]}), 1, "unexplained connection change for source ReplyBadKey")]
        for name, mut, want, text in P:
            d, sk, _ = make(name, mut, work, PATCHED, "mf-form.json")
            exp = []
            for f, (nn, cc) in PCOUNTS.items(): exp += ["--expect", "%s=%d:%d" % (f, nn, cc)]
            if name != "patched_control":   # planted edits change counts only by the connection cut; keep the fixed patched counts
                exp = [x for x in exp]
            c = ["python3", "-I", CK, d, "--baseline", PRIS] + exp + ["--patch-checks", "F002,F008", "--diff-base", PRIS, "--allow", "F002,F008", "--quiet-info"]
            rc, out = run(c, name); fl = lines_of(out, "FAIL")
            good = rc == want and (want == 0 and not fl or any(text in l for l in fl) and all(text in l or any(k in l for k in ("connection count", "orphan nodes", "unreachable from", "unexplained connection change")) for l in fl))
            report("%s (exit %d)" % (name, want), good, "rc=%d fails=%s" % (rc, [x[:90] for x in fl[:2]]))
    print("SELFTEST: %d as expected, %d not as expected, %d skipped (not applicable)" % (ok, bad, skipped))
    shutil.rmtree(work, ignore_errors=True); return 1 if bad else 0
sys.exit(main())
