# EV7P evidence (independent run of the r7q patch set on the frozen tree)

Evidence runner EV7P. I ran commands and saved raw output; I do not judge or fix. Raw files: `/home/user/build/rr6/out/EV7P/` (wrapper.log, pytest-full.log, fail-ids-ev7p.txt, stage-*.log, stage-summary.txt, filecallguard-problems.txt, ruff-check.txt, ruff-format.txt, suppressions.txt, supp-lines-*.txt, hostile-*.txt, hostile_*.py, diff-a.txt, diff-c.txt). Run tree: `.../EV7P/tree-run` (plain copy, no .git). Times UTC (IST = +5:30). Start 11:13, last step 11:52 (about 39 of 60 min). No spend, loopback only (`unshare -n`), no prompt answered, no permission refusal happened.

## What failed, what is uncertain, what I did not check (read this first)
1. **Two real failures on r7q that are not in your "expected" list, both from the r7q changes.**
   - `tests/test_file_call_guard.py::test_every_import_and_file_call_in_the_code_is_listed_with_a_reason_or_goes_through_the_one_reader` FAILS in the plain full run AND in the staged git copy. It does not need git. Cause (raw: `filecallguard-problems.txt`): `demo_only/bad_request.py:30: ThreadingHTTPServer ... is not listed in ALLOWED_CALLS` (the new `QuietServer(ThreadingHTTPServer)` class), and `demo_only/fake_hubspot.py` and `demo_only/fakes_server.py`: "the allowed call ThreadingHTTPServer is not in the file any more (remove it from the table)". The table in `tests/test_file_call_guard.py` (lines about 537 and 549) was not updated for the move. On r7n this test passed (EV7N). The builder's narrow runs did not include this file.
   - `tests/test_hygiene.py::test_hygiene_scan_public` FAILS in the staged git copy (the hygiene scan, the thing r7p was meant to fix; the r7o literal is gone but new hits exist): "hardcoded literals found": `tests/test_r7q_findings.py:95` (`a-much-longer-domain-for-this-test.example.com"`), `:168` and `:170` (`MiXed@Example.COM`), `:356` (`C:\n`), `:362` (`e:\n`), `:374` (`y:\n`), `:375` (`e:\n`). The other 23 tests of that file pass there. So no release candidate is clean yet for the CI gate.
2. Everything else in the full run is the expected git-only set (see step 2). Failed count in the plain full run: **8**, not 7, because of the file-call-guard test above.
3. Not checked: Windows / PowerShell (the two `.ps1` files only as patch application); real IPv6; mutation runs (not asked); bandit, mypy, gitleaks standalone (gitleaks ran only inside the hygiene test); the full suite inside the staged copy (only the 8 git-needing files, as asked); a really quiet machine (another lane started a pytest at 11:46 while my staged run and hostile runs were going; the full run itself started at load 0.08 and ended at load 1.29, wrapper.log); Python versions other than 3.12.
4. My slip: the first run of my MemoryError hostile driver reported "leaks" in 22 of 24 rows; the cause was my driver counting its own top-level frame (it holds the canary as a module variable). I kept that file as `hostile-mem-INVALID-driver-counted-its-own-module-frame.txt`, excluded the module frame, and re-ran; the second run is the one reported.
5. LF patch note: `core-fix-on-frozen-r7q-lf.patch` does NOT apply (`git apply --check` rc=1, "scripts/reset.ps1: patch does not apply") to a plain `git archive` copy of the frozen tree, whose `.ps1` files are CRLF. It applies only after the two `.ps1` files are made LF (as in your checkout "c"), and the result then differs from tree-R7Q in exactly those two `.ps1` files (line endings: 0 CR bytes vs 84 in reset.ps1). The CRLF patch on the plain copy gives a tree identical to tree-R7Q. (In EV7N the sed-LF checkout got CR bytes back after applying; here it did not, so I did not reproduce that.) I ran the tests on the CRLF-patched copy.
6. Skip count: 8 skipped (same 8 reasons as EV7N), not the builder's 37. Not investigated further.
7. The server line `Exception occurred during processing of request` appears 0 times in the full log (EV7N: 1). Not investigated beyond the count.

## Step 1: patches and rebuild
- sha256 of the three patches equal `sha256-r7q.txt`: crlf 4f271992...407832b, lf 03dc17bd...fa3dfe, delta b468bcc7...f557fd (`sha256sum -c`: all OK).
- Frozen tree id `49d3c859...a3ca` (tag `frozen2` of repo2, `git archive` copy; repo2 not edited).
- Tree A (crlf patch on plain copy): `git apply --binary` rc=0; `diff -r` against tree-R7Q: only `__pycache__` folders that exist in tree-R7Q (diff-a.txt, 3 lines). Identical in source.
- Tree C (`.ps1` made LF, then lf patch): rc=0; differs from tree-R7Q only in `scripts/reset.ps1` and `scripts/start_all.ps1` (CR bytes) (diff-c.txt). See item 5.
- Delta patch applied on a copy of tree-R7P: rc=0; `diff -rq` against tree C shows only cache folders and the same two `.ps1` files.

## Step 2: ONE full run (plain copy A, full recipe)
Command: `run-full.sh <tree-run> full 3000`: `env -i`, TMPDIR outside the tree, PYTHONPATH=tree/src, PYTHONDONTWRITEBYTECODE=1, PLAYWRIGHT_BROWSERS_PATH, GITLEAKS_BIN=rr6/bin/gitleaks, DPLD_REQUIRE_SCAN=1, DPLD_REQUIRE_DEMO=1; `unshare -n python3 lo_up-q4g.py venv-br/bin/python -m pytest -q -p no:cacheprovider -rfs`. rc=1, no signal. Order: default collection (alphabetical): test_load_tools at position 1645 of the list, test_r7k_findings at 4312, so load tools first (I checked the collection order, the quiet log does not name files).
- **8 failed, 6012 passed, 8 skipped, 60 warnings in 1830.82s (0:30:30)** (11:13:36 to 11:44:08). Total 6028 (EV7N on r7n: 5929).
- Failing ids: test_hygiene x4 (`test_no_control_characters_in_markdown`, `test_hygiene_scan_public`, `test_sh_blobs_no_cr`, `test_the_secret_scan_files_have_no_carriage_return`), `test_nosemgrep_form::test_no_bare_nosemgrep_comment`, `test_raw_bidi_chars::test_no_tracked_file_holds_a_raw_direction_control_character`, `test_shell_single_bracket::...single_bracket_test` (the 7 expected, all because the plain copy is no git work tree) and **`test_file_call_guard::test_every_import_and_file_call_...` (NEW, real)**.
- After the run `diff -rq` run tree vs tree A: only 4 `__pycache__` folders (demo_only, scripts, src/lead_desk, tools), as in EV7K and EV7N.

## Step 2b: the 8 git-needing files in a STAGED git copy (`git init; git add -A` in my own scratch dir, 318 staged entries, no commit), each file alone, same recipe
| file | result | untracked after |
|---|---|---|
| test_hygiene | **1 failed, 23 passed** (37.4s) | 0 |
| test_nosemgrep_form | 114 passed | 0 |
| test_raw_bidi_chars | 3 passed | 0 |
| test_shell_single_bracket | 146 passed | 0 |
| test_file_call_guard | **1 failed, 10 passed** | 0 |
| test_no_placeholders | 2 passed | 0 |
| test_gitleaks_exceptions | 44 passed | 0 |
| test_gitleaks_semgrep_lock | 4 passed | 0 |
The 4 tests of test_hygiene that failed in the plain copy pass here except the scan (item 1). EV7N on r7n: test_hygiene 24 passed.

## Step 3: ruff 0.17.1 on a COPY (`--no-cache`)
`ruff check`: All checks passed! (rc 0). `ruff format --check`: 229 files already formatted (rc 0). Builder claim "ruff clean" matches. (Ruff does not run the file-call guard or the hygiene scan; both failures above are outside ruff.)

## Step 4: suppressions (grep -o, py/toml/yml/yaml/ps1/sh, no .git/data/caches; raw `suppressions.txt`)
| | noqa | type: ignore | nosemgrep | nosec | S603 |
|---|---|---|---|---|---|
| r7p (tree-R7P) | 188 | 126 | 31 | 8 | 7 |
| r7q | **193** | 126 | 31 | 8 | 7 |
Builder claim noqa 193: matches. Builder's nosemgrep 40 vs my 31: a different counting method; delta 0 in both. The 5 added noqa lines (line diff, `supp-lines-*.txt`): 4 x `# noqa: E402` in the new `tests/test_r7q_findings.py` imports, 1 x `# noqa: PLR2004` at `and len(f.args) >= 2` in the guard in `tests/test_r7n_findings.py`. In src+scripts+load_tools: 56 noqa / 8 nosec / 21 type: ignore, unchanged from r7p.

## Step 5: hostile-input table (loopback only, `unshare -n`, own copy `htree`)
a. **Banner bytes** (`hostile-banner.txt`, driver `hostile_banner.py`): 420 direct cases (3 model names incl. 800 chars x 7 domains incl. umlaut, Chinese, uppercase and dotted capital I `İ` x 5 tags incl. 1 character, 31 characters, non-ASCII x persons 8, 13, 100, 1000): `longest_request_bytes` equals my own independent `json.dumps` length (own body builder, real-length lead id `L` + 12 hex made the way desk.py makes it, email lower-cased) in 420 of 420; 0 mismatches. 6 end-to-end runs of `run_real_check.main --live-model` answered `n` at Start (rc=6, stopped): the printed "worst case model cost" equals my arithmetic to 4 decimals in 6 of 6 (e.g. 8 people: US$7.7708; 1000 people: US$709.7629). Placeholder body from the r7p method for the 800-character model: 1155 bytes; the r7q banner is above it in the cases where the addresses are longer (the unit tests q1 pin that). Not done: the actual desk reserve of a spawned desk process against the banner (I compared with the same request builder the call uses, so it is not independent of `request_body`/`question_text`; the JSON length itself is independent).
b. **MemoryError through secret_boundary** (`hostile-mem.txt`, driver `hostile_mem.py`): 22 cases (11 error kinds x with and without fallback) + 2 on the real `smtp_provider.read_secret_file`; canary searched in text, args, frame locals of every error in the cause/context chain. Result: 24 cases, 0 leaks other than text a raiser puts in its own `args`. With fallback: MemoryError, a MemoryError subclass and a no-argument MemoryError come back as MemoryError (chain cut, `__cause__` and `__context__` None); RecursionError, RuntimeError, OSError and a foreign `ExceptionGroup` become the fixed refusal; KeyboardInterrupt, SystemExit, GeneratorExit and a `lead_desk` error class come back as they are. Real function: MemoryError raised in the file reader now leaves as MemoryError; OSError becomes `SendRefused` ("the smtp password file cannot be used"). Negative control on r7p (`hostile-mem-r7p-control.txt`): same table, but all 4 with-fallback MemoryError rows become the refusal (that is the r7n behaviour the change reverses). Observed, not judged: (i) a MemoryError whose own message holds the secret keeps it in `args` (the scrub.py docstring says args are never rewritten): the real-function row shows `args=('read failed s3cret-made-up-canary-9f',)`; (ii) an `ExceptionGroup` wrapping a MemoryError becomes the refusal with a fallback and passes through without one.
c. **QuietServer** (`hostile-quiet.txt`, driver `hostile_quiet.py`): real loopback sockets, 3 clients per mode that send a request and reset the connection (SO_LINGER 0), child process, real stderr, 11 modes, once with `demo_only.bad_request.QuietServer` and once with a plain `ThreadingHTTPServer` as control.
| mode | QuietServer stderr | plain server (control) |
|---|---|---|
| ok | 0 bytes | 0 |
| handler writes 12 MB to a client that left | 0 bytes | 3129 bytes, 3 tracebacks |
| ValueError in handler | 2853 bytes, 3 tracebacks | same |
| ValueError raised while handling a BrokenPipeError (context) | 3810, 3 tracebacks | same |
| ConnectionRefusedError | 2832, 3 tracebacks | same |
| TimeoutError | 0 | 0 (the standard handler already swallows it) |
| OSError(EPIPE) | 0 | 2922, 3 tracebacks |
| OSError(ECONNRESET) | 0 | 2979, 3 tracebacks |
| ssl.SSLEOFError | 2757, 3 tracebacks | same |
| ExceptionGroup(BrokenPipeError) | 3498, 3 tracebacks | same |
| KeyboardInterrupt in handler thread | 3066 bytes (thread hook, 0 server tracebacks) | same |
So only the closed-connection classes are silent; every other error is still printed. Observed: a real handler bug that itself surfaces as BrokenPipeError/ConnectionReset would also be silent (the class cannot tell them apart); not judged. Full-run count of the stray server line: 0.

## Builder-claimed versus measured
| item | builder claim | measured |
|---|---|---|
| patch sha256 and apply | 3 patches OK, crlf on frozen = tree | OK; lf patch needs LF `.ps1` first (item 5) |
| nine-file run | 378 passed 1 failed (file edited mid-run); 224 passed re-run | not repeated; my full run: 6012 passed, 8 failed, 8 skipped |
| ruff | clean, 229 files | clean, 229 files |
| noqa | 188 to 193 | 188 to 193 |
| test_file_call_guard | not mentioned | FAILS (plain and staged) |
| hygiene scan | not run by builder | FAILS on 7 hits in tests/test_r7q_findings.py |

## Processes and leftovers
Started by me: the full-run wrapper (ended 11:44:08), `stage.sh` (ended, DONE written), foreground hostile drivers (ended). pids in `mypids.txt` checked with `kill -0`: none alive. One pytest process (pid 2980, started 11:46, `tests/test_load_tools.py tests/test_burst_retry.py ...`) belongs to another lane; I did not touch it. I did not edit repo2, tree-R7B..R7Q, EV7*, M8-M12*, REV*. The only source tree I wrote into is my own copies; my `pytest --collect-only` once made a `tests/__pycache__` in my tree-a, removed. No file was committed.

R-numbers used: R330 (honest tamper-evidence claims: stated only what each check detects), the fix-dont-defer rule (reported, fixed nothing), the reviewer-independence rule (no judging).
