import importlib.util, sys, json, tempfile, os
from pathlib import Path
root = Path(sys.argv[1])
sys.path[:0] = [str(root/"src"), str(root), str(root/"scripts")]
spec = importlib.util.spec_from_file_location("rrc", root/"scripts/run_real_check.py")
rrc = importlib.util.module_from_spec(spec); sys.modules["rrc"] = rrc; spec.loader.exec_module(rrc)
print("tree", root.name, "has counter_is_known:", hasattr(rrc, "counter_is_known"))
d = Path(tempfile.mkdtemp(dir=os.environ["TMPDIR"]))
# case 1: no desk hubspot counter file at all (Design A, desk never calls HubSpot)
if hasattr(rrc, "read_counter_files_checked"):
    r = rrc.read_counter_files_checked(d, ".hubspot.json", "t1")
    print("case1 read:", r, "known:", rrc.counter_is_known(r))
    known = rrc.counter_is_known(r)
    print("case1 exit_code_of(ok=True,written=True,[],0,known):", rrc.exit_code_of(True, True, [], 0, known), "EXIT_FAILED=", rrc.EXIT_FAILED)
    # case 2: file with created:0 (desk made a call but created nothing)
    (d/"desk-t2-a.hubspot.json").write_text(json.dumps({"calls":1,"created":0,"create_open":0,"create_unknown":0,"patch":1}))
    r2 = rrc.read_counter_files_checked(d, ".hubspot.json", "t2")
    print("case2 read:", r2, "known:", rrc.counter_is_known(r2), "exit:", rrc.exit_code_of(True, True, [], 0, rrc.counter_is_known(r2)))
    # case 3: file without 'created'
    (d/"desk-t3-a.hubspot.json").write_text(json.dumps({"calls":1}))
    r3 = rrc.read_counter_files_checked(d, ".hubspot.json", "t3")
    print("case3 read:", r3, "known:", rrc.counter_is_known(r3))
else:
    t = rrc.read_counter_files(d, ".hubspot.json", "t1")
    print("case1 totals:", t, "unseen:", rrc.contacts_not_accounted_for(t.get("created"), 0))
    print("case1 exit_code_of(ok=True,written=True,[],0):", rrc.exit_code_of(True, True, [], 0), "EXIT_FAILED=", rrc.EXIT_FAILED)
