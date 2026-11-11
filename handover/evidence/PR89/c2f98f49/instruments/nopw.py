import json, sys
sys.argv = ["leak.py", sys.argv[1]]
import leak
leak.PW["NOPW"] = ""
out = []
for mode in ("assert_msg", "assert_first", "exc_msg", "exc_class_dynamic", "param_id", "fixture_raises", "fixture_missing", "skip_reason", "collect_error", "func_dynamic", "baseline_fail", "baseline_skip", "canary_fail"):
    r = leak.run_case("NOPW", mode)
    out.append({"mode": mode, "exc_type": r["exc_type"], "returned": {k: v for k, v in r["returned"].items() if k in ("rows", "first_lines", "exception.str", "exception.rows", "parent stdout", "parent stderr")}})
json.dump(out, open(leak.RAW + "/nopw-records.json", "w"), indent=1)
for o in out:
    print("MODE", o["mode"], "| raised:", o["exc_type"])
    for k, v in o["returned"].items():
        if v: print("   ", k, "=>", v.replace("\n", " / ")[:400])
