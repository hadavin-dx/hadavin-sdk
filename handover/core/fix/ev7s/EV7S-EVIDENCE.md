# EV7S evidence, order 268 (r7s patch). EVIDENCE RUNNER: raw results, no verdicts.

## FAILED / NOT RUN / DIFFERENT FROM THE BRIEF (first)
1. Frozen tree head differs from the brief: `git rev-parse HEAD` in /home/user/build/rr6/demo-frozen/repo2 prints 58aa4031e911e682ec5702e0641d11cbaf927817, not 49d3c85938fe5323a3378a49195d3b8da434b3ca (that sha is not in `git log --all`). The patch applied cleanly on that tree anyway (rc 0) and the result equals tree-R7S.
2. `scripts/run_real_check.py --dry-fakes` was NOT run: without --assume-yes the code asks `Start? [y/N]` (line 1129); the brief says stop at a prompt. Instead: the behaviours (fake CRM hiding a created contact -> EXIT_FAILED with the "contacts may be left" line; stale desk-<oldtag>-* counter files) were run through the patch's own tests (tests/test_r7s_findings.py, 51 passed, verbose list in hostile-b-r7s-tests.txt, tests s3*), not through the script. I did not read the stdout of the script's "contacts may be left" line itself.
3. Hostile table (a): one cell did NOT refuse: `make_fakes_server(host="")` built a socket and bound 127.0.0.1 (code: `where = host or Config().fakes_host`, an empty string falls back to the configured loopback default). The patch's own test `test_s1_the_fakes_server_refuses` has no "" case (parameters listed: 0.0.0.0, 192.0.2.1, ::, example.com). QuietServer, FakeHubspot, FakesServer (class) and the model fake's make function with "" refused.
4. Mutant runner R-set rows: `mutA` as written in mut2.py is NOT-APPLIED on r7s (its text `ThreadingHTTPServer` entry in CALLS no longer exists in this form); I ran an equivalent `mutA2` (delete the `("demo_only/bad_request.py","ThreadingHTTPServer")` allow entry) instead.
5. Own random mutants: 6 SURVIVED (list below), see raw rows. R07 survived with the r7s test file but was killed by tests/test_r7q_findings.py -k q8 (the file that tests handle_error).
6. Suppression count: frozen tree 424, tree-a (patched) 367 (builder said 367 on r7r and r7s: patched number matches; the frozen-tree number is a different base).
7. Not checked: CodeQL/Sonar/bandit (not asked); no run on Windows (7 skips are platform/root related).

## Hashes (unpacked files) vs expected
```
d173173c4e3c4477853719dc99a1e91c63f6dfaba507f6626659528f186fe4b1  crlf.patch   (expected same: MATCH)
9d716ca237c612ac42a35d136f951ab505b67841b26d117de3af4ef438051e87  lf.patch     (expected same: MATCH)
48271ae9fedef2be6f37fd1731e55085c8de5f23bb922d33ba0d29e14a010410  delta.patch  (expected same: MATCH)
```
Snapshot MANIFEST.txt (28 entries) `sha256sum -c` in handover/core/snapshot-r7s: 0 lines not OK. (The snapshot's delta-r7r-to-r7s.diff is the LF text and has a different hash than the unpacked CRLF delta; its MANIFEST entry matches itself.)

## Apply equals tree
cp -r frozen repo2 -> tree-a; `git apply --whitespace=nowarn crlf.patch` rc=0; `diff -rq -x .git -x __pycache__ -x .ruff_cache -x .pytest_cache tree-a /home/user/build/rr6/tree-R7S` -> 0 differences (applyeq.txt empty; also empty when `data` is not excluded). After the full run htree vs tree-a: 0 differences; `git status` in htree shows only staged adds, `git diff` empty.

## Full run (once, final head, htree = tree-a + git init + git add -A, no commit)
Command: wrapper out/EV7S/run-full.sh (copy of EV7R/run-full.sh; env -i, TMPDIR in tmp-full, PYTHONPATH=htree/src, DPLD_REQUIRE_SCAN=1, DPLD_REQUIRE_DEMO=1, GITLEAKS_BIN, unshare -n + lo_up-q4g driver, `pytest -q -p no:cacheprovider -rfs tests/test_load_tools.py tests/test_r7k_findings.py tests`).
Start 2026-11-14T13:41:52Z, end 14:21:04Z, rc=0.
Result line: `6072 passed, 7 skipped, 60 warnings in 2350.33s (0:39:10)`. 0 failed. "REPOSITORY FOLDER CHANGED" occurs 0 times in the log.
Skips (-rs):
- tests/test_book_folder_refusals.py:237 root can read any file
- tests/test_n8n_api_url.py:524 root (and Windows) can read a file with no permissions
- tests/test_path_confinement.py:285 ntpath.isreserved needs Python 3.13
- tests/test_r7b_fake_deep_and_head.py:58 (2) only the model fake has /v1/messages
- tests/test_server_hardening.py:224 measurement run: set LEAD_DESK_LOAD_N
- tests/test_stall_eviction.py:526 the reset that destroys the reply happens on Windows only
Raw: pytest-full.log, wrapper.log.

## Ruff (0.17.1 binary, on a copy ruff-copy of tree-a, --no-cache)
`ruff check` rc=0: "All checks passed!". `ruff format --check` rc=0: "230 files already formatted". Raw: ruff-check.txt, ruff-format.txt.

## Suppressions (grep -rEo 'noqa|type: ignore|nosemgrep|nosec' --exclude-dir=.git,__pycache__,data,.ruff_cache,.pytest_cache . | wc -l)
- frozen repo2: 424 (noqa 251, type: ignore 121, nosemgrep 40, nosec 12)
- tree-a (frozen + r7s patch): 367 (noqa 193, type: ignore 126, nosemgrep 40, nosec 8)
Raw: supp-repo2.txt, supp-tree-a.txt.

## Hostile table (in-process, unshare -n + lo_up driver; socket.socket.__init__ counted; raw hostile-a.txt)
Hosts 0.0.0.0, 192.0.2.1, "", "::", example.com against 6 entry points each (QuietServer, FakeHubspot, FakesServer, hubspot serve(), make_fakes_server, make_model_server): 30 cells; 29 = ValueError with 0 sockets made. 1 cell = NO-REFUSAL: make_fakes_server(host="") sockets_made=1, bound address 127.0.0.1 (the configured default).
(b) run_real_check: not run (prompt, see FAILED item 2). Covered by test_r7s_findings.py: s3c counting rule, s3e exit code, "a created contact the list does not show ends the check with the failed exit code" (3 variants), "contact left by a failed archive said once as left", "nothing hidden still ends with zero", s3b older-run counter files do not count (3 tests): all PASSED in the 51-test run (hostile-b-r7s-tests.txt).

## Mutant rows (own runner mut2-ev.py = copy of mut2.py with paths on my own copies; restore from tree-a, compared byte for byte)
(i) S set on mutS copy (mut-results-S.tsv): S01-S24 all KILLED, restored-byte-equal=True on every row (25 rows incl. X1ctx).
(ii) R-set on r7s copy (mut-results-RSRS.tsv): Q13 KILLED, Q14 KILLED, Q19 KILLED, X1 KILLED, X1ctx KILLED, mutB KILLED, mutA NOT-APPLIED (text gone); mutA2 (equivalent, my own) KILLED (mut-results-SA2.tsv). All restored-byte-equal=True.
(iii) 40 own mutants, mutX copy, tests = tests/test_r7s_findings.py -x -k <selector> (mut-results-rand40.tsv, rand40.py has every old/new text): 34 KILLED, 6 SURVIVED, 0 not applied, all 40 restored-byte-equal=True.
SURVIVED rows (raw, no judgement):
- R07 bad_request.py handle_error `isinstance(sys.exception(), CLIENT_GONE)` -> `not isinstance(...)`; selector "quiet or gone or hang" in test_r7s_findings (6 passed). Re-run with tests/test_r7q_findings.py -k q8: KILLED (mut-results-R07q.tsv).
- R10 run_real_check.py `(created or 0) - accounted` -> `(created or 1) - accounted`; -k s3: 14 passed.
- R19 `glob(f"desk-{tag}-*{suffix}")` -> `glob(f"desk-{tag}*{suffix}")`; -k s3: 14 passed.
- R20 `glob(f"desk-{tag}-*{suffix}")` -> `glob(f"desk-{tag}-*")`; -k s3: 14 passed.
- R27 `exit_code_of(result["ok"], written, left, unseen)` -> `exit_code_of(result["ok"], True, left, unseen)`; -k s3: 14 passed.
- R39 support.py `if os.environ.get(REQUIRE_SCAN_ENV):` -> `... == "1":`; -k s6: 3 passed (the run environment sets the variable to "1").
Only test_r7s_findings.py was run per mutant (not the whole suite), so a survivor here is not proof that the full suite misses it.

## Process list at end
Started by me: full run wrapper (setsid, pid in full.pid), mut2-ev.py S, mut2-ev.py RS, mutA2, rand40.py, rand40q.py; one backgrounded hostile-b pytest. `ps` check at the end: no pytest, mut2, rand40 or EV7S process left. Nothing committed or pushed. No /dev path typed; no prompt answered.
