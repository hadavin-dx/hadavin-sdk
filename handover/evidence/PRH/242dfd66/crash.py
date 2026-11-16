import sys, os
tree = sys.argv[1]; sys.path.insert(0, tree + "/src")
from hadavin_sdk import tools
from hadavin_sdk.guard import runmap
assert os.path.realpath(tools.__file__).startswith(os.path.realpath(tree))
HAND = "".join(["vK4n", "Ts8Q", "w2Ld", "Rm6x", "Bf9H", "jYc3", "pZ5g"])
def boom(*a, **k): raise RuntimeError("planted bug")
res = {}
real = runmap._clean
runmap._clean = boom
for name, txt in (("plain", "plain text"), ("hidden", "one \x1b[0m two"), ("handed", "token " + HAND), ("spaced", " ".join(HAND))):
    try:
        out = tools.prepare_output(txt, {}, 4000, [HAND]); res[name] = "RETURNED " + ("limit-marker" if out.startswith(tools.MARKER) else "text")
    except BaseException as e: res[name] = "raised " + type(e).__name__
for name, fn in (("error_reason", lambda: tools.error_reason(ValueError("bad value"))), ("safe_head", lambda: runmap.safe_head("an error", 50))):
    try: fn(); res[name] = "RETURNED"
    except BaseException as e: res[name] = "raised " + type(e).__name__
print(os.path.basename(tree), "has RedactorCrash:", hasattr(runmap, "RedactorCrash"), res)
