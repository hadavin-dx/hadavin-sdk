"""EVIDENCE RUNNER probe, batch 19 head: canary through every HiddenInputModel class, many shapes, many channels."""
import importlib, pkgutil, sys, json, traceback
import pydantic
from pydantic import BaseModel, ValidationError
import hadavin_sdk
from hadavin_sdk.hidden_input import HiddenInputModel

for m in pkgutil.walk_packages(hadavin_sdk.__path__, "hadavin_sdk."):
    try:
        importlib.import_module(m.name)
    except Exception as e:
        print("IMPORT-SKIP", m.name, type(e).__name__)

def subs(c):
    out = []
    for s in c.__subclasses__():
        out.append(s); out.extend(subs(s))
    return out
him = []
for c in [HiddenInputModel] + subs(HiddenInputModel):
    if c not in him: him.append(c)
allm = []
for c in subs(BaseModel):
    if c.__module__.startswith("hadavin_sdk") and c not in allm: allm.append(c)
nonhim = [c for c in allm if not issubclass(c, HiddenInputModel)]
print("pydantic", pydantic.VERSION, "python", sys.version.split()[0])
print("HiddenInputModel classes probed (itself plus transitive subclasses):", len(him))
print("other hadavin_sdk BaseModel classes (not HiddenInputModel):", len(nonhim))
for c in nonhim: print("  NONHIM", c.__module__ + "." + c.__name__, "hide_input_in_errors=", c.model_config.get("hide_input_in_errors"))

C = "zq" + "-canary-" + "8"
CK = "zq" + "-keycanary-" + "9"
class Bomb:
    def __str__(self): return C
    __repr__ = __str__

def chans(e, tb_text):
    ch = {}
    ch["str"] = str(e); ch["repr"] = repr(e)
    for lab, kw in (("errors()", {}), ("errors(include_input=True)", {"include_input": True}), ("errors(include_context=True)", {"include_context": True}), ("errors(include_url=True)", {"include_url": True})):
        try: ch[lab] = str(e.errors(**kw))
        except Exception as x: ch[lab] = "ERR " + type(x).__name__
    try: ch["json()"] = e.json()
    except Exception as x: ch["json()"] = "ERR " + type(x).__name__
    ch["args"] = repr(e.args)
    ch["__cause__"] = repr(e.__cause__) + (str(e.__cause__) if e.__cause__ else "")
    ch["__context__"] = repr(e.__context__) + (str(e.__context__) if e.__context__ else "")
    ch["traceback"] = tb_text
    ch["__dict__"] = repr(getattr(e, "__dict__", {}))
    return ch

SHAPES = {
 "validate_str": lambda c: c.model_validate(C),
 "validate_list_entry": lambda c: c.model_validate([C]),
 "validate_None": lambda c: c.model_validate(None),
 "validate_int": lambda c: c.model_validate(12345),
 "validate_object": lambda c: c.model_validate(Bomb()),
 "validate_json_str": lambda c: c.model_validate_json(json.dumps(C)),
 "validate_json_invalid": lambda c: c.model_validate_json(C),
 "validate_json_list": lambda c: c.model_validate_json(json.dumps([C])),
 "validate_json_obj_badvalue": lambda c: c.model_validate_json(json.dumps({"x": C})),
 "dict_nontext_key": lambda c: c.model_validate({C: 1, 7: C, (C,): C, b"k": C}),
 "dict_text_key_canary": lambda c: c.model_validate({CK: C}),
 "dict_nested_canary": lambda c: c.model_validate({"a": {"b": [C, {C: C}]}}),
 "ctor_kwargs_canary": lambda c: c(**{CK: C}),
 "validate_strings_str": lambda c: c.model_validate_strings(C),
 "validate_strings_dict": lambda c: c.model_validate_strings({CK: C}),
}
needles = [C, CK]
rows = []; leaks = 0; noerr = 0; runs = 0
for c in him:
    for sh, fn in SHAPES.items():
        runs += 1
        try:
            fn(c)
            noerr += 1
            rows.append((c.__name__, sh, "NO-ERROR", []))
            continue
        except ValidationError as e:
            tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            ch = chans(e, tb)
            hit = [k for k, v in ch.items() if any(n in v for n in needles)]
            if hit: leaks += 1
            rows.append((c.__module__ + "." + c.__name__, sh, "ValidationError", hit))
        except Exception as e:
            tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            hit = [k for k, v in (("str", str(e)), ("repr", repr(e)), ("traceback", tb), ("__cause__", repr(e.__cause__)), ("__context__", repr(e.__context__))) if any(n in v for n in needles)]
            if hit: leaks += 1
            rows.append((c.__module__ + "." + c.__name__, sh, "OTHER:" + type(e).__name__, hit))
print("classes", len(him), "shapes", len(SHAPES), "runs", runs, "no-error runs", noerr, "runs with canary in some channel", leaks)
from collections import Counter
print("outcome kinds:", dict(Counter(r[2] for r in rows)))
for r in rows:
    if r[3] or r[2] != "ValidationError": print("ROW", r)
# ToolSpec explicit
from hadavin_sdk.tools import ToolSpec
print("ToolSpec in set:", ToolSpec in him)
