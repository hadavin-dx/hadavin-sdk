# EGM via child `claude -p` processes (cloud container, 2026-11-09)
Why: plugins load when a claude process starts; the running session cannot see egm skills installed mid-session (Skill tool: "Unknown skill"). A child process can. Proof: handover/evidence/egm-child-test-2026-11-09.txt (7 skills, 10 agents listed).
Install (done once): `claude plugin marketplace add google/elephant-goldfish-model && claude plugin install egm@egm && python3 handover/tools/egm_model_patch.py`.
Pattern (one EGM step = one child, own working dir = repo, input from files, output to a file):
```
cd /home/user/hadavin-sdk
timeout 1800 claude -p "Use the egm:egm-review skill. Input: /home/user/build/snap/<head>/ (snapshot), ticket handover/tickets/<T>.md, evidence handover/evidence/<T>/<head>/. Write your full report to /home/user/build/reviews/<T>-<head>-rN.md. Do not read any author verdict." \
  --model claude-sonnet-5-5 --permission-mode acceptEdits < /dev/null > /home/user/build/reviews/<T>-<head>-rN.log 2>&1; echo rc=$?
```
- Opus (`--model claude-opus-5-5`) only for egm-brainstorm, egm-draft, egm-resolve; Sonnet for review, review-loop, drift-report, bootstrap and the reviewer agents.
- Reviewers: fresh child each round, shown the snapshot + ticket + raw evidence only, never the author's or runner's verdict. Register each child in cloud-register.md before starting; heavy tests still go through /home/user/build/heavy.sh.
- Read the report file, copy scrubbed to handover/reviews/, push. A child is a new process: it has no memory of earlier rounds (that is the goldfish).
- NOT yet tested: a full review run, and whether children inherit `--permission-mode`/tool limits as wanted. Test with one small snapshot first.
