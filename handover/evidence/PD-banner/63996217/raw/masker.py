import importlib.util,sys
sys.path.insert(0,sys.argv[2])
spec=importlib.util.spec_from_file_location("gnew",sys.argv[1]); new=importlib.util.module_from_spec(spec); sys.modules["gnew"]=new; spec.loader.exec_module(new)
from hadavin_sdk.guard import redact
import inspect; print("core redact:",inspect.signature(redact))
ins=["bypass=true","bypass=true x","bypass=abc123","bypass_key=abc","authorization=Bearer abcdefgh","authorization=Bearer abcdefghij","Bearer abcdefghijk","Bearer abc123defg","Basic abcdefg","Basic abc1234","Bearer"+"qwertyuiopas","Bearer qwertyuiopas","Bearer qwertyuiop"]
for i in ins:
    n=new._hide_secrets(i)
    o=redact(i)
    o=o if isinstance(o,str) else getattr(o,"text",o)
    more = len(n.replace("<hidden>",""))>len(str(o).replace("<hidden>","")) if True else False
    print(f"in={i!r:38} guard_new={n!r:36} main_core_redact={str(o)!r}")
