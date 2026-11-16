import re, sys, os
root = "/home/user/hadavin-sdk"; A = "/home/user/hadavin-sdk/handover/core-hardening/audit-r460/"
docs = ["CORE-PR-HANDOFF-v11.md", "CORE-PR-HANDOFF-v11-other-tracks.md"]
def src(rel):
    return open(os.path.join(root, rel), encoding="utf-8").read().split("\n")
def show(rel, a, b):
    L = src(rel); n = len(L) - (1 if L[-1] == "" else 0)
    print("  [%s len=%d] %d-%d %s" % (rel, n, a, b, "IN-RANGE" if 1 <= a <= b <= n else "OUT-OF-RANGE"))
    for i in range(max(1, a), min(n, b) + 1): print("    %d: %s" % (i, L[i-1][:140]))
def grep(pat):
    for d in docs:
        for i, l in enumerate(open(A + d, encoding="utf-8").read().split("\n"), 1):
            for m in re.finditer(pat, l): print("DOC %s:%d  ...%s..." % (d, i, l[max(0, m.start()-60):m.end()+60].replace("\n", " ")))
print("== 1 retry.py cites (file has %d lines)" % len(src("src/hadavin_sdk/llm/retry.py")))
grep(r"retry\.py[: ]+\d+(?:-\d+)?(?:\s*(?:,|and)\s*:?\d+(?:-\d+)?)*")
print("== 2 app.py:161"); grep(r"app\.py:\d+(?:[-,]\d+)*"); show("src/hadavin_sdk/app.py", 161, 161)
print("== 3 fifth assign site tests/test_p6_detectors.py:186"); grep(r"test_p6_detectors\.py[:\d,\- ]{0,30}"); show("tests/test_p6_detectors.py", 186, 186)
print("== 4 _limits_stop"); grep(r"_limits_stop[^.]{0,200}"); 
for i, l in enumerate(src("src/hadavin_sdk/runtime/agent_loop.py"), 1):
    if "_limits_stop" in l: print("  agent_loop.py %d: %s" % (i, l.strip()[:120]))
print("== 5 guard/redact.py:513"); grep(r"redact\.py:\d+"); show("src/hadavin_sdk/guard/redact.py", 513, 513)
print("== 6 bedrock_guardrail.py:36"); grep(r"bedrock_guardrail\.py:\d+(?:-\d+)?"); show("src/hadavin_sdk/guard/bedrock_guardrail.py", 36, 36)
print("== 7 migrate.py:53-54 and :94"); grep(r"migrate\.py[:\d,\- and]{0,30}"); show("src/hadavin_sdk/store/migrate.py", 53, 54); show("src/hadavin_sdk/store/migrate.py", 93, 94)
