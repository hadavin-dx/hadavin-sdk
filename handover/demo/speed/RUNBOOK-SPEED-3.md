# RUNBOOK-SPEED-3: how to prove the test-speed changes on each machine

Written 2026-11-12 (UTC) by the phase-4 builder, as SPEED-PLAN-3 section 7 R7 asks. Not reviewed. The builder records; only the LEAD writes GO or NO-GO.
Rule source: SPEED-PLAN-3 R2 (rule v3), R3, R6, R7, R8, R9. Bible: grep of `bible\RULES.md` for testing-speed/eval-gate R-numbers was done by the lead's preamble; this runbook cites SPEED-PLAN-3 rule numbers only, no bible R-number is claimed as read here.

## 0. What is NOT proven yet (read first)
* Nothing in this runbook has been run on the cloud container. The three Linux shell scripts passed `bash -n` (syntax) only. The first cloud window will find the typos, if any: that is why every window has 20 minutes slack (section 6).
* The patched demo tree (xdist + conftest grouping) has been measured on Windows (2 runs) and Linux (1 run, in docker on the laptop), never on the cloud container and never on a hosted GitHub runner.
* The sdk parallel run MISSED the old 400 s rule (median 439.7 s). Under rule v3 (below) it is judged against its OWN serial median on the same machine: 439.7 / 804.5 = 0.55, which would pass, but that is a different machine state than the window will have. The lead decides after the window, not now.

## 1. Rule v3 (the pass rule for every item, fixed BEFORE the runs, no tuning afterwards)
1. At least 2 serial and at least 3 parallel runs, back to back, same machine, same tree (same head and same patch hash), same flags, private TEMP where the OS has it (laptop: `heavy_slot --private-temp`).
2. Median parallel seconds <= 0.67 x median serial seconds (at least 1.5x faster). Seconds are pytest's own summary line ("... in 423.66s"), not wall time of the wrapper.
3. CPU used outside the test processes < 15 percent in every run (the quiet check, section 5, before each run; plus `top -bn1` after). A run that breaks this is discarded, marked DISCARDED in the ledger with the reason, and repeated.
4. Identical results: `python compare-norm.py <serial.xml> <par1.xml> <par2.xml> <par3.xml>` prints `RESULT ALL IDENTICAL` (same test ids, same outcomes, same skip reasons, same failure types; the `@browser`/`@reset` group suffix is normalised away). Baseline failures (section 7g) must appear in BOTH sides.
5. A broken-copy control is listed: an extra failing test copied in must make the parallel run FAIL with exactly that test named (proves parallel does not hide failures). Commands in sections 3 and 4.
6. Over 0.67 = NO-GO. No tuning of the number, the flags or the machine after seeing the result. The old 400 s NO-GO stays recorded as "NO-GO under rule v2 on a loaded laptop".

## 2. The patched demo tree: how the cloud demo session gets it (R7a)
Carrier: sdk repo `hadavin-dx/hadavin-sdk`, branch `demo/handover`, folder `handover/demo/speed/`. The lead pushes the files below (copied from `C:\Users\rakes\Downloads\Hadavin\egm\speedup-repos\runbook-files\`). Nothing is pushed to the public demo repo; the demo tree is rebuilt on the cloud side from the PUBLIC demo repo head `b29bb1f` (branch `pr-3-tests` of `hadavin-dx/duplicate-proof-lead-desk-n8n`) plus the patch files, by `run-demo-linux.sh`.

Files to push (exact sha256 at 2026-11-12, also in `runbook-files\SHA256SUMS`; the cloud side checks with `sha256sum -c SHA256SUMS`). Hashes: ci-xdist-demo-b29bb1f.patch 5680b751...5e64; fake-hubspot-read-body-before-answer.patch 87e06a4d...9559; compare-norm.py 618b82d9...b9b77; quiet-check.sh 649c0689...417a; run-demo-linux.sh 1da3ac4f...7c5; run-sdk-linux.sh 09ce97e5...45da; xdist-overlay-hashes.txt 95768174...33e9; run-ledger.tsv b362a41c...b64 (full values in SHA256SUMS).
| File | Purpose |
|---|---|
| `ci-xdist-demo-b29bb1f.patch` | the CI/xdist patch against b29bb1f: requirements (.in + both locks: pytest-xdist 3.8.0, execnet 2.1.2), `lint.yml` (timeout 60 to 30, `PYTHONHASHSEED=0`, `-n auto --dist loadgroup`), `tests/conftest.py` (browser group, reset group, COLUMNS removal). NO test is rewritten. |
| `fake-hubspot-read-body-before-answer.patch` | R1 result (section 8): the fake HubSpot server reads the request body before it answers and closes; plus one new regression test. Apply AFTER the CI patch. The two closed-port tests are NOT touched. |
| `compare-norm.py` | the comparison script (usage in section 4c) |
| `xdist-overlay-hashes.txt` | hashed pins for the sdk venv (execnet, pytest-xdist) |
| `run-demo-linux.sh`, `run-sdk-linux.sh`, `quiet-check.sh` | the commands below, as scripts |
| `run-ledger.tsv` | the ledger (header + 2 example rows) |
| `SHA256SUMS` | hashes of all of the above |
The old `ci-xdist-demo.patch` (against snapshot 841a318, with the 3-try rewrites) must NOT be used: it does not apply to b29bb1f and contains the retries that SPEED-PLAN-3 R1 rejects.

## 3. Exact commands per place
### 3a. demo-Linux (cloud container: python3.12, nproc 4, 16 GiB, NO docker daemon, github + pypi reachable)
From an EMPTY work folder `W` with the speed files copied beside the scripts (`HERE`):
```
bash $HERE/run-demo-linux.sh serial 1      # then: serial 2
bash $HERE/run-demo-linux.sh par 1 3       # then: par 2, par 3   (3 = workers; nproc is 4, 3 leaves one core for the OS)
python3 $HERE/compare-norm.py out/serial1/junit.xml out/serial2/junit.xml out/par1/junit.xml out/par2/junit.xml out/par3/junit.xml
```
What the script does: clones the demo repo, checks out b29bb1f, applies the patch (and the fake-hubspot patch if present), builds a venv from the HASHED `requirements-dev.txt` (`pip install --require-hashes`), downloads gitleaks 8.30.1 with a checksum check, runs the quiet check, then `python -m pytest -q -p no:cacheprovider -rA [-n 3 --dist loadgroup] --junitxml out/<mode><n>/junit.xml` with `DPLD_REQUIRE_DEMO=1 DPLD_REQUIRE_SCAN=1 PYTHONPATH=src:.` (and `PYTHONHASHSEED=0` in parallel). Playwright is deliberately NOT installed: the real hosted CI has none either (about 119 browser tests skip). Expected baseline on this setup: 2270 passed, 2 failed, 119 skipped of 2391 ids (the laptop docker figure; the container may differ by a few tests: the lane-6 notes saw 2349 passed 116 skipped on an earlier tree, so the counts are compared serial vs parallel on the SAME machine, not against these numbers).
Broken-copy control (demo): in `W/dpld` run `cp tests/test_leads.py tests/test_zz_broken_copy.py` (any small test file that exists), append `\n\ndef test_deliberate_failure_control():\n    assert 1 == 2\n`, run the parallel command once with `--junitxml out/broken/junit.xml`, expect the FAILED list = the 2 baseline failures + this test only, then delete the file. NOT yet run on the demo tree (listed as not done in evidence-phase3).

### 3b. demo-Windows (laptop; the lead or a laptop agent; heavy_slot is the slot guard, max 4 slots, use 2 per run)
From the demo worktree (patched), venv `C:\Users\rakes\Downloads\Hadavin\_local\scratch\venv-dpld-fast`:
```
set PYTHONDONTWRITEBYTECODE=1 & set DPLD_REQUIRE_SCAN=1 & set DPLD_REQUIRE_DEMO=1 & set GITLEAKS_BIN=C:\Users\rakes\Downloads\Hadavin\_local\tools\gitleaks\gitleaks.exe
serial:   python C:\Users\rakes\Downloads\Hadavin\tools\heavy_slot.py --private-temp --count 2 -- <venv>\Scripts\python.exe -m pytest -q -p no:cacheprovider -rA --junitxml <out>\serial1.xml
parallel: set PYTHONHASHSEED=0 & python ...\heavy_slot.py --private-temp --count 2 -- <venv>\Scripts\python.exe -m pytest -q -p no:cacheprovider -rA -n 3 --dist loadgroup --junitxml <out>\par1.xml
```
(the exact earlier calls are in `raw3\chain.sh`, lines 6-8). Broken-copy: same as 3a but on Windows paths.

### 3c. sdk-Linux (cloud; repo `hadavin-dx/hadavin-sdk`, main at the head the lead names)
```
bash $HERE/run-sdk-linux.sh serial 1       # serial 2
bash $HERE/run-sdk-linux.sh par 1 3        # par 2, par 3
bash $HERE/run-sdk-linux.sh broken 1 3
bash $HERE/run-sdk-linux.sh posix 1 3      # the POSIX signal file, serial then -n 3
python3 $HERE/compare-norm.py out/sdk-serial1/junit.xml out/sdk-serial2/junit.xml out/sdk-par1/junit.xml out/sdk-par2/junit.xml out/sdk-par3/junit.xml
```
Install step inside the script (from `raw3\chain.sh`, adapted to a plain Linux shell without docker): `uv sync --locked --no-build --all-extras --group test`, then `uv pip install --require-hashes --no-deps -r xdist-overlay-hashes.txt` (execnet 2.1.2, pytest-xdist 3.8.0; no repo file changes), then `PYTHONHASHSEED=0 PYTHONPATH=src .venv/bin/python -m pytest -q -m 'not live and not perf' -rA -p no:cacheprovider [-n 3 --dist loadgroup] --junitxml ...`. The 492 Postgres/Vault skips (no DSN) are the same serial and parallel; they are NOT proven by this window.
POSIX signal tests: the earlier `ModuleNotFoundError: hadavin_sdk` came from a missing install and missing `PYTHONPATH=src` in the container (raw3 report item 6). Working invocation (raw3\sdk\posix-par.txt: "59 passed in 13.17s"): `PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rA -n 3 --dist loadgroup tests/test_mutation_runner.py`. `uv sync` installs hadavin_sdk editable, so `PYTHONPATH=src` is belt and braces; keep it.

### 3d. sdk-Windows and studio tools (already measured, repeat only if the lead asks)
sdk: `raw3\chain.sh` lines 10-16. Tools: `PYTHONHASHSEED=0 python tools\heavy_slot.py --private-temp --count 2 -- _local\scratch\venv-dpld-fast\Scripts\python.exe -m pytest -q -n 3 --dist loadgroup tools/tests tools/test_dpld_publish_dryrun.py`.

## 4. compare-norm.py
(c) Copied to `runbook-files\compare-norm.py` (sha256 618b82d9...b9b77, same as `raw3\compare-norm.py`). Usage: `python3 compare-norm.py BASE.xml OTHER.xml [OTHER2.xml ...]` where every file is a pytest `--junitxml` file; BASE is the first serial run. Prints the id count, outcome counts, `IDENTICAL` or `DIFFERENT` per other file (up to 10 differing ids each) and a last line `RESULT ALL IDENTICAL` (exit 0) or `RESULT MISMATCH` (exit 1). It compares test id + outcome + (skip reason with quoted paths blanked, or failure type). It does NOT compare failure message text or test order.

## 5. Quiet check for the cloud (e)
`quiet-check.sh OUTFILE` runs before every timed run (the scripts call it): it writes date, `nproc`, `uptime`, `top -bn1 | head -15`, the 1-minute load and any other pytest/playwright/chromium process into the file. Exit 3 ("NOT QUIET") if another test-like process exists or load1 >= 1.0. Stop trigger: on exit 3 do not run; wait 2 minutes, retry once; if still not quiet, stop the window and hand back the quiet file with "another lane was running" (the lead decides). A run during which `top -bn1` after the run shows another lane's pytest is DISCARDED. During the window the cloud session must start no other agent that runs tests.

## 6. Slack and windows (f)
Per window add 20 minutes slack on top of the sum of the runs. Estimates (ESTIMATE, not measured on the container): demo-Linux serial about 15 min each (lane-6 measured 886-953 s on this container), parallel about 6-8 min each; so a full demo item = 2 x 15 + 3 x 7 = about 51 min + 20 slack = about 71 min. sdk-Linux serial about 14 min (laptop 804 s; container speed unknown), parallel about 8 min: 2 x 14 + 3 x 8 + broken 8 + posix 1 = about 61 min + 20 = about 81 min. Run demo and sdk in SEPARATE windows, never at the same time (parallel runs of two items would break the quiet rule).

## 7. Per item (d): output, pass rule, decider, hand-back
Common: output folder `out\<mode><n>\` (junit.xml, pytest.txt, time.txt, quiet-before.txt, head.txt, patch-hash.txt, versions.txt, result.txt); pass rule = rule v3 (section 1); decider = the LEAD only (writes GO or NO-GO in `egm\speedup-repos\`); hand-back = the cloud session commits the whole `out\` folder plus a one-page summary `SUMMARY.md` (numbers only, no verdict) to branch `demo/handover`, folder `handover/demo/speed/results-<item>-<date>/`, and one ledger line per run.
| Item | Output file(s) | Numeric pass rule | Notes |
|---|---|---|---|
| demo-Linux | `out\serial1,2`, `out\par1..3` | v3: median(par) <= 0.67 x median(serial) | counts and skip reasons identical; baseline failures present in all |
| demo-Windows | laptop folder `egm\speedup-repos\raw5\demo-win\` | v3 | existing: raw3 win serial 1206 s, par 423-439 s (0.35 x; the third failure in win-par1 was a flaky socket test, see section 8) |
| sdk-Linux | `out\sdk-serial1,2`, `sdk-par1..3`, `sdk-broken1`, `sdk-posix1` | v3 | the old 400 s rule is retired by rule v3 (R2) |
| sdk POSIX | `out\sdk-posix1\posix-*.txt` | par seconds < serial seconds AND 59 passed in both AND identical | tiny file, no ratio needed beyond that |
| studio tools | `raw4\` / `raw3\tools-*` | v3 (done: 64.6 s median vs 165.1 s serial = 0.39 x) | |

### 7g. Results that already exist (named) and baseline failures
* tools: `raw3\tools-serial2.txt` (165.1 s), `tools-par1..3.txt` (66.7 / 58.0 / 64.6 s), `compare-tools.txt` (identical), `tools-broken.txt` (control). Baseline failure: `test_wordlist_row_selects_the_needs_wordlist_marker`.
* sdk Windows: `raw3\sdk\serial.txt` (804.5 s), `par1..3.txt` (423.7 / 439.7 / 441.0 s), `compare-sdk.txt` (ALL IDENTICAL), `broken.txt` (control, 1 failed = the planted test), `posix-serial.txt` / `posix-par.txt` (59 passed, 35.2 s vs 13.2 s). Baseline failure: `test_no_vendor_brand_string_is_tracked`.
* demo Windows: `raw3\demo\win-serial.txt` (1206 s), `win-par2.txt`, `win-par3.txt` (identical to serial on the tree with the later conftest; `win-par1` had a flaky extra failure), `compare-win.txt`. Baseline failures: the two stage-warning text tests in `test_mode_safety.py` (`test_the_stage_warning_text_sits_beside_the_move_control`, `test_the_stage_warning_names_the_automatic_writes_and_says_may`).
* demo Linux (laptop docker, no Playwright): `raw3\demo\lin-serial\`, `lin-par3\` (867.0 s vs 296.6 s, identical), `compare-lin.txt`.
* NOTE: those results are on the OLD tree (snapshot 841a318 + earlier patch). The final tree b29bb1f + the b29bb1f patch is not yet measured anywhere: the window re-measures it.

### Run ledger (R8)
File `run-ledger.tsv`, tab separated, columns: `head_sha tree_hash os venv_lock_hash command flags exit_code counts seconds date`. A parallel run MATCHES a serial run when head_sha, tree_hash, os, venv_lock_hash, flags-minus-`-n` and counts are all equal. Two example rows (from `raw3\sdk\serial.txt` and `par1.txt`) are in the file. `mutate-parallel.py` is LAPTOP-ONLY (Windows paths, heavy_slot); de-hardcoding its paths is part of S2, not done here.

## 8. R1 and the one known flaky test
Result (details and numbers in `evidence-phase4.md` section 3): the flaky `ConnectionAbortedError` (WinError 10053) seen in demo parallel runs is NOT the freed-port reuse. Cause: `demo_only/fake_hubspot.py` answers a rejected call (401, 404...) and closes while the client's request body is still unread; the system then resets the connection and the client loses the answer. Fix: `fake-hubspot-read-body-before-answer.patch` (the fake reads the body first; no test is weakened). The two closed-port tests (`test_not_reached_is_stored_nothing`, `test_a_closed_fake_server_refuses_new_connections`) stay exactly as in b29bb1f, with NO retries: no failure of them was reproduced, so no edit was made. If either fails in a window, hand it back as a finding.

## 9. Rung table (R9)
| Component | Need | Rung tried | Evidence | What only our code gives | Verdict |
|---|---|---|---|---|---|
| `heavy_slot.py` (slot guard, private TEMP) | stop parallel heavy runs overloading the 12-core laptop and sharing TEMP | 2 (our core module, exists) | 24 tests; raw3 runs | the slot count and private-temp for several agents | KEEP (exists) |
| pytest-xdist 3.8.0 | run test files on 3 workers | 4 (free library, MIT, pinned with hashes) | raw3: identical results x3 on sdk, tools, demo | nothing | KEEP as config |
| conftest `xdist_group` hook (browser + reset files on ONE worker, `COLUMNS` removal) | pytest 9.2 ignores xdist 3.8.0's group suffix (measured: 86 browser tests spread over 3 workers) | 4 tried (xdist_group marker alone: does nothing on pytest 9.2) | evidence-phase3 section 2D | the private `item._id` write | KEEP-CODE (rung 5, 40 lines, canary test still to add per R1; pin pytest and xdist versions) |
| no-code tools | n/a for test speed | 1 | not applicable | n/a | CUT |
| the `-rA` flag | print every captured output | measured, `evidence-phase4.md` section 1 | see there | n/a | decided by the measurement |
