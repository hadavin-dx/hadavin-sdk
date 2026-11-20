import sys, tempfile, pathlib
from tests.k5_support import ScriptLLM, build_runtime, handle, k5_cfg
from hadavin_sdk.models import RunState as S
doc = " ".join(f"10.1.1.{i}" for i in range(1, 10)).encode()  # 9 IPv4 values of 8 characters: 72
for cap in (72, 71):
    d = pathlib.Path(tempfile.mkdtemp())
    cfg = k5_cfg(d, config={"evidence": {"max_map_chars": cap}})
    rt, _ = build_runtime(cfg, ScriptLLM([{"noaction": True}]))
    run = handle(rt, document=doc)
    print(cap, run.state, run.reason_code)
from hadavin_sdk.config import EvidenceSettings
for v in (0, 786432, 786433):
    try:
        EvidenceSettings(max_map_chars=v); print(v, "accepted")
    except Exception as e:
        print(v, "rejected", type(e).__name__)
