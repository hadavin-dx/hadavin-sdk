"""R7U-A mutant runner. ONE runner, ONE mutant copy (out/EV7U/mutA, only mutated file is changed); after every
mutant the file is restored from tree-R7U-A and compared byte for byte. usage: mut_a.py <copydir> <result.tsv> [ids]"""
import filecmp, os, shutil, subprocess, sys
R = "/home/user/build/rr6/"; O = R + "out/EV7U/"; M = O + sys.argv[1] + "/"; S = R + "tree-R7U/"; TMP = O + "tmp-mut"
os.makedirs(TMP, exist_ok=True)
RR = "scripts/run_real_check.py"; T = "tests/test_r7u_a_findings.py"
FAST_RULE = "test_a1_one_more or test_a1_the_rule or test_a1_named or test_a1b_a_retried or test_a3_the_counter_check"
FAST_INT = "test_a2 and not real_run"
CAP = "    open_part = max(0, open_creates)\n    if leads is not None:\n        open_part = min(open_part, max(0, leads - created))\n    return max(0, created + open_part - accounted)"
def capm(new): return (CAP, new)
muts = [
 ("M01", RR, *capm(CAP.replace("min(open_part, max(0, leads - created))", "min(open_part, leads)")), FAST_RULE),
 ("M02", RR, *capm(CAP.replace("max(0, leads - created)", "leads - created")), FAST_RULE),
 ("M03", RR, *capm(CAP.replace("leads - created", "leads + created")), FAST_RULE),
 ("M04", RR, *capm(CAP.replace("leads - created", "created - leads")), FAST_RULE),
 ("M05", RR, *capm(CAP.replace("open_part = min(", "open_part = max(")), FAST_RULE),
 ("M06", RR, *capm(CAP.replace("open_part = max(0, open_creates)", "open_part = open_creates")), FAST_RULE),
 ("M07", RR, *capm(CAP.replace("- accounted)", "- accounted + 1)")), FAST_RULE),
 ("M08", RR, *capm(CAP.replace("created + open_part -", "created - open_part -")), FAST_RULE),
 ("M09", RR, *capm(CAP.replace("if leads is not None:", "if leads:")), FAST_RULE),
 ("M10", RR, *capm(CAP.replace("return max(0, created + open_part - accounted)", "return created + open_part - accounted")), FAST_RULE),
 ("M11", RR, *capm(CAP.replace("leads - created)", "leads - created - 1)")), FAST_RULE),
 ("M12", RR, *capm(CAP.replace("leads - created)", "leads - created + 1)")), FAST_RULE),
 ("M13", RR, *capm(CAP.replace("max(0, created + open_part - accounted)", "max(1, created + open_part - accounted)")), FAST_RULE),
 ("I01", RR, "all(type(v) is int and v >= 0", "all(isinstance(v, int) and v >= 0", FAST_INT),
 ("I02", RR, "type(v) is int and v >= 0 for", "type(v) is int and v > 0 for", FAST_INT),
 ("I03", RR, "type(v) is int and v >= 0 for", "type(v) is int and v >= -1 for", FAST_INT),
 ("I04", RR, "all(type(v) is int and v >= 0 for", "all(v >= 0 for", FAST_INT),
 ("I05", RR, "if not all(type(v) is int", "if not any(type(v) is int", FAST_INT),
 ("I06", RR, "except (OSError, ValueError, AttributeError, TypeError, ArithmeticError):", "except (OSError, ValueError, AttributeError, TypeError):", FAST_INT),
 ("I07", RR, '                raise ValueError("a counter value is not a whole number from 0")', "                pass", FAST_INT),
 ("I08", RR, "            total.update(values)\n", "            total.update({})\n", FAST_INT),
 ("I09", RR, "type(v) is int and v >= 0 for", "type(v) is int or v >= 0 for", FAST_INT),
 ("F01", RR, '"counter_known": counter_known,\n        "unseen_contacts"', '"counter_known": True,\n        "unseen_contacts"', "test_a3 and not counter_check"),
 ("F02", RR, '"unseen_contacts": unseen,\n', '"unseen_contacts": 0,\n', "test_a3 and not counter_check"),
 ("F03", RR, '    result["checks"].append(counter_check(counter_known, unseen, hub_stats))  # before the table and the result file\n', "", "test_a3 and not counter_check"),
 ("F04", RR, '"ok": known and not unseen,', '"ok": known,', "test_a3"),
 ("F05", RR, '"ok": known and not unseen,', '"ok": not unseen,', "test_a3"),
 ("F06", RR, '            len(crm_pairs),\n            hub_stats.get("create_open", 0)', '            0,\n            hub_stats.get("create_open", 0)', "test_a3 and not counter_check"),
 ("F07", RR, "    if counter_known:\n        unseen = contacts_not_accounted_for(", "    if True:\n        unseen = contacts_not_accounted_for(", "test_a3_a_counter_that_is_not_known"),
 ("F08", RR, '            hub_stats.get("create_open", 0) + hub_stats.get("create_unknown", 0),\n            len(lead_ids),\n        )\n    result["checks"]', '            hub_stats.get("create_open", 0),\n            len(lead_ids),\n        )\n    result["checks"]', "test_a1c"),
 ("F09", RR, '            hub_stats.get("create_open", 0) + hub_stats.get("create_unknown", 0),\n            len(lead_ids),\n        )\n    result["checks"]', '            hub_stats.get("create_unknown", 0),\n            len(lead_ids),\n        )\n    result["checks"]', "test_a1c"),
 ("F10", RR, '    result["ok"] = all(c["ok"] for c in result["checks"])\n    result = mask_result', '    result["ok"] = all(c["ok"] for c in result["checks"][:-1])\n    result = mask_result', "test_a3_a_counter_that_is_not_known"),
 ("B01", RR, "    known = counter_is_known(hub_read)\n    created = hub_stats", "    known = True\n    created = hub_stats", "test_a4"),
 ("B02", RR, '    unknown_outcome = hub_stats.get("create_open", 0) + hub_stats.get("create_unknown", 0)', '    unknown_outcome = hub_stats.get("create_open", 0)', "test_a4"),
 ("B03", RR, "        if unknown_outcome:\n            note +=", "        if True:\n            note +=", "test_a4"),
 ("B04", RR, "most = contacts_not_accounted_for(created, 0, unknown_outcome, leads)", "most = contacts_not_accounted_for(created, 0, unknown_outcome, None)", "test_a4"),
 ("B05", RR, '{hub_stats.get(\'create_unknown\', 0)} ended with an unknown outcome', '{hub_stats.get(\'create_open\', 0)} ended with an unknown outcome', "test_a4"),
 ("B06", RR, "read_counter_files_checked(run_dir, \".hubspot.json\", tag)\n        )", "CounterRead(read_counter_files(run_dir, \".hubspot.json\", tag), 0, 0)\n        )", "test_a4"),
]
only = sys.argv[3:]
out = open(O + sys.argv[2], "a")
for mid, f, old, new, k in muts:
    if only and mid not in only: continue
    p = M + f; s = open(p, encoding="utf-8", newline="").read()
    if s.count(old) != 1:
        out.write(f"{mid}\tNOT-APPLIED count={s.count(old)}\n"); out.flush(); continue
    open(p, "w", encoding="utf-8", newline="").write(s.replace(old, new))
    try:
        env = dict(os.environ, PYTHONPATH=M + "src", PYTHONDONTWRITEBYTECODE="1", TMPDIR=TMP, PATH=R + "bin:" + os.environ["PATH"],
                   GITLEAKS_BIN=R + "bin/gitleaks", DPLD_REQUIRE_SCAN="1", DPLD_REQUIRE_DEMO="1")
        cmd = ["unshare", "-n", "python", R + "src-v6/drivers/lo_up-q4g.py", R + "venv-br/bin/python", "-m", "pytest", "-q",
               "-p", "no:cacheprovider", "-x", "-k", k, T]
        try:
            r = subprocess.run(cmd, cwd=M, env=env, capture_output=True, text=True, timeout=900)
            res = "KILLED" if r.returncode == 1 else ("SURVIVED" if r.returncode == 0 else "ERR rc=%d" % r.returncode)
            tail = r.stdout.strip().splitlines()[-1:]
            open(O + f"mutraw-{mid}.txt", "w").write(r.stdout[-2000:])
        except subprocess.TimeoutExpired:
            res = "TIMEOUT"; tail = []
        out.write(f"{mid}\t{f}\t{k}\t{res}\t{tail}\n"); out.flush()
    finally:
        shutil.copyfile(S + f, p); same = filecmp.cmp(S + f, p, shallow=False)
        out.write(f"{mid}\trestored-byte-equal={same}\n"); out.flush()
