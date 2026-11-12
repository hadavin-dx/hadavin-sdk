import json
from hadavin_sdk.tools import ToolSpec
canary = "zq" + "-canary-" + "7"
for label, fn in [("str", lambda: ToolSpec.model_validate(canary)),
                  ("list", lambda: ToolSpec.model_validate([canary])),
                  ("badjson", lambda: ToolSpec.model_validate_json(canary))]:
    try:
        fn()
        print(label, "no error")
    except Exception as e:
        out = {"str": str(e), "repr": repr(e)}
        try: out["errors"] = str(e.errors())
        except Exception as x: out["errors"] = "ERR " + type(x).__name__
        try: out["json"] = e.json()
        except Exception as x: out["json"] = "ERR " + type(x).__name__
        print(label, type(e).__name__, {k: (canary in v) for k, v in out.items()})
