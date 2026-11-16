#!/usr/bin/env python3
"""Negative tests of check_flows.py (round 3). Takes the PATCHED generator output (order glob, real variant) and the
unpatched baseline output made by run-round2.sh, plants one defect per mutant into mf-form.json (or the file set), and runs the
checker with ONE fixed command line. A mutant counts as caught only if the exit code is 1 AND the named FAIL line is in the output.
Also runs one control (no defect, must exit 0) and two argument-misuse cases (same command plus/minus one option).
The exact command is saved to negative-output/CHECK-COMMAND.txt. Exit code 0 only if every case behaves as expected."""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(tempfile.gettempdir(), "pa13b")
SRC = W + "/g/glob/real"
BASE = W + "/g/base/real"
NEG = W + "/neg"
OUT = HERE + "/negative-output"
CK = HERE + "/check_flows.py"
COUNTS = [
    "--expect",
    "mf-form.json=15:14",
    "--expect",
    "mf-hook.json=15:14",
    "--expect",
    "mf-recovery.json=10:9",
    "--expect",
    "mf-sub-crm-mail.json=20:26",
]


def cmd(d, extra=(), patch_checks=True):
    c = ["python3", "-I", CK, d, "--baseline", BASE] + COUNTS
    if patch_checks:
        c += ["--patch-checks", "F002,F008"]
    return c + ["--diff-base", BASE, "--allow", "F002,F008", "--quiet-info"] + list(extra)


def node(j, name):
    return next(x for x in j["nodes"] if x["name"] == name)


def conn(src, dst, idx=0):
    return {"node": dst, "type": "main", "index": idx}


def m_cycle(j, d):
    j["nodes"] += [
        {
            "name": "CycA",
            "type": "n8n-nodes-base.noOp",
            "typeVersion": 1,
            "position": [0, 0],
            "parameters": {},
        },
        {
            "name": "CycB",
            "type": "n8n-nodes-base.noOp",
            "typeVersion": 1,
            "position": [0, 0],
            "parameters": {},
        },
    ]
    j["connections"]["CycA"] = {"main": [[conn("CycA", "CycB")]]}
    j["connections"]["CycB"] = {"main": [[conn("CycB", "CycA")]]}


def m_switch(j, d):
    j["nodes"].append(
        {
            "name": "Sw",
            "type": "n8n-nodes-base.switch",
            "typeVersion": 3,
            "position": [0, 0],
            "parameters": {"rules": {"values": [{}, {}]}},
        }
    )
    j["connections"]["Item"]["main"][0].append(conn("Item", "Sw"))
    j["connections"]["Sw"] = {"main": [[conn("Sw", "ReplyStored")]]}


def m_parse(j, d):
    with open(d + "/mf-form.json", "w", encoding="utf-8") as fh:
        fh.write("{bad")
    return False


def m_missing(j, d):
    os.remove(d + "/mf-hook.json")
    return False


def m_selfloop(j, d):
    j["connections"]["Stored"]["main"][0] = [conn("Stored", "Stored")]


def m_reroute(j, d):
    j["connections"]["ReplyStoreFail"] = {"main": [[conn("ReplyStoreFail", "Claimed")]]}


def m_valid_type(j, d):
    a = next(
        x
        for x in node(j, "Valid")["parameters"]["assignments"]["assignments"]
        if x.get("name") == "lead_key"
    )
    a["type"] = "number"


def m_cond(j, d):
    node(j, "KeyOk")["parameters"]["conditions"]["conditions"][0]["leftValue"] = "={{ true }}"


def m_struct(j, d):
    j["connections"]["KeyOk"]["main"][0][0]["index"] = 1


# name -> (mutator, text that MUST appear in the checker output)
MUTANTS = [
    (
        "orphan_reply",
        lambda j, d: j["connections"].pop("Stored"),
        "orphan nodes (no incoming link, not a trigger)",
    ),
    ("self_only", m_selfloop, "orphan nodes (no incoming link, not a trigger)"),
    ("cycle_only", m_cycle, "unreachable from any trigger ['CycA', 'CycB']"),
    ("reroute_failreply", m_reroute, "unexplained connection change for source ReplyStoreFail"),
    (
        "no_errlink",
        lambda j, d: j["connections"]["Claim"]["main"].pop(),
        "onError=continueErrorOutput but main[1] is missing",
    ),
    (
        "if_one_branch",
        lambda j, d: j["connections"]["KeyOk"]["main"].pop(),
        "IF node KeyOk lacks output(s) [1]",
    ),
    ("switch_gap", m_switch, "SWITCH node Sw lacks output(s) [1]"),
    (
        "bad_ref",
        lambda j, d: node(j, "ReplyStoreFail")["parameters"].__setitem__(
            "responseBody", "={{ $('Nope').item.json.x }}"
        ),
        "refers to $('Nope')",
    ),
    (
        "bad_items_ref",
        lambda j, d: node(j, "ReplyStoreFail")["parameters"].__setitem__(
            "responseBody", '={{ $items("Nope")[0] }}'
        ),
        "refers to $('Nope')",
    ),
    (
        "no_trigger",
        lambda j, d: node(j, "Receive").__setitem__("type", "n8n-nodes-base.respondToWebhook"),
        "no trigger node in file",
    ),
    (
        "dangling",
        lambda j, d: j["connections"]["Item"]["main"][0].append(conn("Item", "Ghost")),
        "dangling target 'Ghost'",
    ),
    ("no_name", lambda j, d: node(j, "Item").pop("name"), "lack name or type"),
    (
        "count_wrong",
        lambda j, d: j["nodes"].pop(-1) and False or None,
        "node count 14 != expected 15",
    ),
    ("parse_fail", m_parse, "parse failure"),
    ("missing_file", m_missing, "file list"),
    (
        "wrong_save",
        lambda j, d: j["settings"].__setitem__("saveDataSuccessExecution", "none"),
        "F-008 saveDataSuccessExecution is 'none' expected 'all'",
    ),
    (
        "extra_change",
        lambda j, d: node(j, "Stored").__setitem__("alwaysOutputData", False),
        "unexplained change in node Stored at alwaysOutputData",
    ),
    (
        "wrong_code",
        lambda j, d: node(j, "ReplyBadKey")["parameters"]["options"].__setitem__(
            "responseCode", 400
        ),
        "ReplyBadKey responseCode is 400 expected 422",
    ),
    (
        "wrong_code503",
        lambda j, d: node(j, "ReplyStoreFail")["parameters"]["options"].__setitem__(
            "responseCode", 500
        ),
        "ReplyStoreFail responseCode is 500 expected 503",
    ),
    ("wrong_cond", m_cond, "KeyOk condition is not the expected string"),
    (
        "no_valid_ref",
        lambda j, d: node(j, "ReplyStoreFail")["parameters"].__setitem__(
            "responseBody", "={{ { n8n_error: true } }}"
        ),
        "ReplyStoreFail body lacks the $('Valid') reference",
    ),
    (
        "valid_other_path",
        m_valid_type,
        "unexplained change in node Valid at parameters.assignments.assignments[lead_key].type",
    ),
    ("conn_structure", m_struct, "F-002 connection structure of KeyOk"),
]


def run(c, name):
    r = subprocess.run(c, capture_output=True, text=True, check=False)  # exit code is the result
    out = r.stdout + r.stderr
    with open(f"{OUT}/{name}.out", "w") as fh:
        fh.write("$ " + " ".join(c) + "\n" + out + f"exit={r.returncode}\n")
    return r.returncode, out


def main():
    shutil.rmtree(NEG, ignore_errors=True)
    os.makedirs(NEG)
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT)
    ref = cmd("<DIR>")
    with open(OUT + "/CHECK-COMMAND.txt", "w") as fh:
        fh.write(
            " ".join(ref)
            + "\n(<DIR> = the mutated copy of "
            + SRC
            + "; usage cases below add or drop one option)\nusage case 1: same plus  --expect mf-bogus.json=1:1\nusage case 2: same without --patch-checks\n"
        )
    good = 0
    bad = []

    def judge(name, want_rc, text, c):
        nonlocal good
        rc, out = run(c, name)
        ok = rc == want_rc and (text is None or text in out)
        print(
            f"{name:<18} {'OK  ' if ok else 'BAD '} exit={rc} want_exit={want_rc} "
            f"named_line_present={None if text is None else text in out}"
        )
        if ok:
            good += 1
        else:
            bad.append(name)

    d = NEG + "/control"
    shutil.copytree(SRC, d)
    judge("control_unmutated", 0, "RESULT: 0 FAIL", cmd(d))
    for name, fn, text in MUTANTS:
        d = NEG + "/" + name
        shutil.copytree(SRC, d)
        p = d + "/mf-form.json"
        with open(p) as fh:
            j = json.load(fh)
        r = fn(j, d)
        if r is not False:
            with open(p, "w") as fh:
                json.dump(j, fh)
        judge(name, 1, text, cmd(d))
    judge(
        "usage_unknown_expect",
        1,
        "unknown file key 'mf-bogus.json'",
        cmd(NEG + "/control", ["--expect", "mf-bogus.json=1:1"]),
    )
    judge("usage_allow_no_pc", 1, "needs --patch-checks", cmd(NEG + "/control", patch_checks=False))
    total = len(MUTANTS) + 3
    print(
        f"CASES: {total} total = {len(MUTANTS)} mutants + 1 control + 2 usage; "
        f"{good} as expected, {len(bad)} not as expected {bad}"
    )
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
