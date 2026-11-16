import sys, importlib.util
sys.argv=['x']
spec=importlib.util.spec_from_file_location('cyc','cycles.py')
import io,contextlib
buf=io.StringIO()
with contextlib.redirect_stdout(buf):
    cyc=importlib.util.module_from_spec(spec); spec.loader.exec_module(cyc)
P=cyc.PKG
def show(mod):
    for t,k in cyc.edges_of(mod):
        print(f"   {mod.replace(P+'.','')} -> {t.replace(P+'.','')} [{k}]")
for m in ["hadavin_sdk.llm","hadavin_sdk.llm.common","hadavin_sdk.llm.fake","hadavin_sdk.llm.retry","hadavin_sdk.llm.protocol","hadavin_sdk.config","hadavin_sdk.registry","hadavin_sdk.deferred","hadavin_sdk.replay_records","hadavin_sdk.guard.judge","hadavin_sdk.guard.injection","hadavin_sdk.guard","hadavin_sdk.guard.runmap"]:
    print(m); show(m)
