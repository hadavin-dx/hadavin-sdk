import re, sys
sys.path.insert(0, "/home/user/hadavin-sdk/handover/core-hardening/audit-r460/evidence-handoff-v13")
from patch_lib import Doc
d = Doc("CORE-PR-HANDOFF-v13.md")
d.rep("| store.postgres | store.protocol | |", "| approvals.requests | llm.callgate | |\n| approvals.cards | llm.callgate | |\n| guard.judge | errors | |\n| store.postgres | store.protocol | |")
# file-name renames: only the evidence names of this document (v12 -> v13)
t = d.t
t = t.replace("evidence-handoff-v12/", "evidence-handoff-v13/")
for stem in ["import_graph", "cite_check", "snippet_check", "banned_count", "cycles", "merge_probe"]:
    t = t.replace(stem + "_v12", stem + "_v13")
t = t.replace("cycles_v12_from_independent", "cycles_v13_from_independent")
t = re.sub(r"(raw-[a-z-]+)-v12", r"\1-v13", t)
t = t.replace("CORE-PR-HANDOFF-v12.md", "CORE-PR-HANDOFF-v13.md").replace("CORE-PR-HANDOFF-v12-other-tracks.md", "CORE-PR-HANDOFF-v13-other-tracks.md")
d.t = t
d.save()
