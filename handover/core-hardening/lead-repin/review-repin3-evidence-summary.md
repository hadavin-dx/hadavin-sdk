# Re-pin v3 independent evidence (runner aca8c2e92aa91057a), condensed, 2026-11-16. Raw: evidence-repin3-independent/01..10. Runner judged nothing.
FAILURES FIRST
1. Fake secrets leaked in main run (13 lines: secret in a trailing comment with no secret-looking name) and in --mask probe (8 of 19 lines): bare base64 blobs (3), prose line (1), `curl -H "X-Auth-Token: v"`, `-H 'Authorization: token v'`, `ENV TOKEN v` (no =), `passwd "v"` (no =). 0 e-mail leaks. Hidden fine: DB_PASS=, token_file=, SECRET_KEY_BASE=, ?api_key=, ?token=, password:v, f(password=v, "pass": "v".
2. Work folder kept by design after a normal run (17 files, 0 fragments, 0 e-mails).
3. Signals: dash SIGINT/SIGTERM during canary leaves st-in.txt (46 fake secrets); bash: one of 4 self-test trials hung and left it; normal run killed during canary leaves it (4 of 4); no kill case removed the folder in a normal run.
4. Self-test does not catch 3 of 12 planted mutations (JWT rule dropped; filter_ready always OK; self_test always 0) and 2 more only with the abort test (abort disabled: normal run continued rc=0 though canary printed FAIL).
5. Non-GNU sed not tested (only GNU sed 4.9, mawk). Shim test: exit 3, nothing left.
6. Not covered: Windows/WSL/macOS, git work tree, non-root user, real take program.
PASSED: sha256 script 7ab0ac10...8a73, doc 21c6b978...9c9f; sh/bash/dash -n rc 0; self-test 119/119 under bash and dash; dummy tree untouched (hashes identical); banned-word count 0; no spend, no network.
