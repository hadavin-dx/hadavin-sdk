"""pytest plugin (PR H rev 3 probe): the author's rev-2 prototype + rev-2 fixes, with the views of the escaped joined
reading dropped (rev 3, D4) and a counter for the step-6 fallback (D1): each firing appends one line to the file
named by the environment variable PRH_STEP6_LOG."""
import os, sys, types
ERR = "/home/user/build/prh-author/errata"
src = open(ERR + "/prh_proto.py", encoding="utf-8").read()
old = "for base in dict.fromkeys((raw, nD)):"
old6 = "if any(p not in r.text for p in held): return found.text, found.mapping, nD, nS"
assert src.count(old) == 1 and src.count(old6) == 1
src = src.replace(old, "for base in (raw,):").replace(
    old6,
    "if any(p not in r.text for p in held):\n"
    "        open(__import__('os').environ['PRH_STEP6_LOG'], 'a').write('fired\\n'); return found.text, found.mapping, nD, nS",
)
mod = types.ModuleType("prh_proto"); mod.__file__ = ERR + "/prh_proto.py"
exec(compile(src, mod.__file__, "exec"), mod.__dict__)
sys.modules["prh_proto"] = mod
import fixes  # noqa: E402
mod.install(); fixes.install()
