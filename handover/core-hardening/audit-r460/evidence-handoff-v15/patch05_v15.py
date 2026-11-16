import re, sys; sys.path.insert(0, "evidence-handoff-v15")
from pl import *
MAP = [("src/hadavin_sdk/config.py:57-58","src/hadavin_sdk/config.py:55-58"),("limits.py:18","limits.py:17-18"),("limits.py:24","limits.py:24-25"),("limits.py:26","limits.py:26-27"),
("agent_loop.py:425","agent_loop.py:425-427"),("agent_loop.py:432","agent_loop.py:432-435"),("gemini.py:98","gemini.py:98-99"),("tests/test_p5p6_followups.py:101","tests/test_p5p6_followups.py:101-102"),
("registry.py:41","registry.py:39-41"),("agent_loop.py:310","agent_loop.py:310-312"),("guard/judge.py:72","guard/judge.py:70-72"),("app.py:161","app.py:161-162"),("app.py:165","app.py:162-165"),
("app.py:162","app.py:162-167"),("guard/http.py:93","guard/http.py:90-93"),("approvals/requests.py:37","approvals/requests.py:37-40"),("approvals/cards.py:76-80","approvals/cards.py:76-83"),("approvals/cards.py:79","approvals/cards.py:79-83"),
(".github/workflows/ci.yml:40",".github/workflows/ci.yml:36-40"),("store/migrate.py:55","store/migrate.py:53-55"),("guard/bedrock_guardrail.py:28","guard/bedrock_guardrail.py:28-29"),
("actions/secrets_file.py:34-64","actions/secrets_file.py:33-64"),("tests/warden_port/privacy_corpus.py:42","tests/warden_port/privacy_corpus.py:41-42"),("src/hadavin_sdk/config.py:366-367","src/hadavin_sdk/config.py:366-368"),
("tests/warden_port/test_audit_chain.py:568","tests/warden_port/test_audit_chain.py:568-573"),("anchor_s3.py:5-7","anchor_s3.py:4-7"),("ci.yml:83","ci.yml:83-88")]
def fix(t):
    n = 0
    for old, new in MAP:
        pat = re.compile(r"(?<![\w.-])" + re.escape(old) + r"(?![\d-])") if not old.startswith(("src/","tests/",".github","actions","guard","approvals","store")) else re.compile(re.escape(old) + r"(?![\d-])")
        t, c = pat.subn(new, t); n += c
    return t, n
# agent_loop.py:179 in other-tracks only (main file uses other agent_loop:179 meaning? check by count)
if __name__ == "__main__":
    for f in ("CORE-PR-HANDOFF-v15.md", "CORE-PR-HANDOFF-v15-other-tracks.md"):
        t = load(f); t, n = fix(t)
        if f.endswith("tracks.md"):
            t, c = re.subn(r"(?<![\w-])agent_loop\.py:179(?![\d-])", "agent_loop.py:174-179", t); n += c
        save(t, f); print(f, "cites extended:", n)
