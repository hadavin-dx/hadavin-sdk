"""D4 probe (PR H rev 3): the author's rev-2 prototype with ONE change, the views of the escaped JOINED reading
dropped (rev 3 keeps only the views of the escaped original plus the strip_hidden decoded reading). Loads
/home/user/build/prh-author/errata/prh_proto.py with that one line replaced, registers it as `prh_proto`, then
also prints a line each time the step-6 fallback (a held placeholder missing after the mask pass) fires, then
runs the given author script (check2.py or repro.py) unchanged with its own arguments."""
import runpy, sys, types
ERR = "/home/user/build/prh-author/errata"
sys.path.insert(0, ERR)
src = open(ERR + "/prh_proto.py", encoding="utf-8").read()
old = "for base in dict.fromkeys((raw, nD)):"
assert src.count(old) == 1, "prototype line not found exactly once"
mod = types.ModuleType("prh_proto"); mod.__file__ = ERR + "/prh_proto.py"
src = src.replace(old, "for base in (raw,):")
old6 = "if any(p not in r.text for p in held): return found.text, found.mapping, nD, nS"
assert src.count(old6) == 1, "step-6 line not found exactly once"
src = src.replace(old6, "if any(p not in r.text for p in held):\n        print('STEP6-FALLBACK-FIRED', flush=True); return found.text, found.mapping, nD, nS")
exec(compile(src, mod.__file__, "exec"), mod.__dict__)
sys.modules["prh_proto"] = mod
print("PATCHED prototype: views of the escaped joined reading dropped; step-6 fallback prints STEP6-FALLBACK-FIRED")
script = sys.argv[1]; sys.argv = [script] + sys.argv[2:]
runpy.run_path(script, run_name="__main__")
