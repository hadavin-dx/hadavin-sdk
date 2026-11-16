import sys, pydantic
from decimal import Decimal
print("pydantic", pydantic.VERSION, "python", sys.version.split()[0])
from hadavin_sdk.config import Route
for v in ("NaN","sNaN","Infinity","-Infinity","1"):
    try:
        r = Route(model_id="m", input_usd_per_mtok=v, output_usd_per_mtok="1", max_tokens=1)
        print(repr(v), "-> ACCEPTED", repr(r.input_usd_per_mtok))
    except Exception as e:
        print(repr(v), "->", type(e).__name__, "|", str(e).replace("\n"," / ")[:200])
