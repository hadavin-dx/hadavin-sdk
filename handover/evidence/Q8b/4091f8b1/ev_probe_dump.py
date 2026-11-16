"""Dump per-probe readable results (key|path|style -> readable pieces) for the add-on keys and the corpus keys. Records only."""
import sys, json
exec(open("/home/user/hadavin-sdk/handover/evidence/Q8b/4091f8b1/ev_probe_keys.py").read().split('if __name__')[0])
keys = ADDON + json.load(open(sys.argv[1]))
json.dump(run(keys, "x"), open(sys.argv[2], "w"))
