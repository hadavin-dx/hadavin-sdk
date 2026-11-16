# EV7H RESULTS: EV6 hostile drivers re-run on the r7 patch (EVIDENCE RUNNER; raw numbers, no verdicts)

Run 2026-11-13 22:36Z to about 23:00Z (IST = UTC+5:30: 04:06 to 04:30 on 14 Nov). Machine: load average under 1.3 throughout. Old = clean `git archive` of frozen2 (tree 49d3c85938fe5323a3378a49195d3b8da434b3ca) at `tree-old-EV7H`; new = same archive plus `core-fix-on-frozen-r7.patch` (sha256 24f3f82223382d823c014fb8dd7b875070f3378a1e3019beea3d2341a531c586) at `tree-EV7H`. `git apply --check` rc=0, `git apply` rc=0, 104 changed paths per `git status --short | wc -l`. The new tree is byte-identical to `tree-R7` for `src/lead_desk/regfile.py` and `tests/test_file_call_guard.py` (`cmp` printed "same"). Both trees were deleted at the end.

## 0. NOT RUN / NOT CHECKED / CHANGED (read first)
1. **FAILURE FOUND in the r7 tree itself (raw output below, section 4): `tests/test_file_call_guard.py::test_every_import_and_file_call_in_the_code_is_listed_with_a_reason_or_goes_through_the_one_reader` FAILS on the r7 tree with no planted shape: `src/lead_desk/regfile.py:242: os.stat (is os.stat) is not listed in ALLOWED_CALLS`.** The same file pair is in the builder's `tree-R7`. I did not run the full suite (not asked), so I do not know if this was known. This also means the run6b `j` part (planted file-call shapes) cannot show a clean baseline: baseline rc=1 on r7 (rc=0 on r6). In each of the 10 planted-shape logs the planted `scripts/zz_shape_*.py` is named in the problem list next to the regfile.py:242 line (count of lines mentioning zz_shape = 2 in each log).
2. The hostile PKI folder (`tmp-EV6/h/pki`), `tmp-EV6/h/env.json` and `hostile-leaf.pem` no longer existed. I REBUILT them: made-up CA and leaf (CN=localhost, SAN localhost + 127.0.0.1, 30 days, openssl, nothing real) and `env.json` from `scripts/real-run.env.example` via `make_synthetic_config.py` (14 keys). These are NOT the same bytes as the EV6 ones. Cases whose result depends on the config file or certificate bytes could differ for that reason and not because of r7. (Old and new used the same rebuilt inputs; old rows match the EV6 old rows on rc/hang/traceback in every compared row except the ones listed as ONLY-EV6 / ONLY-EV7H in section 3.) The `.pem` files could not be copied from the EV6 folder (the tool blocked the copy), so I rebuilt them.
3. /dev/null was a regular file at the start of this run (`ls -la /dev/null`: `-rw-r--r-- 1 0 root 48`). I did not touch any /dev path. I changed the copied drivers so they never open one: every `subprocess.DEVNULL` stdin became an empty file under `tmp-EV7H/h/art/empty`; `password_file=Path("/dev/null")` in `hostile_inproc.py` and `hostile_secret.py` became that empty file; and the cases that point the code at `/dev/full`, `/dev/zero` and `/dev/urandom` were REMOVED (3 case labels x old/new = 6 rows not run: `real_check:REAL_RESULT_FILE=/dev/full`, `snippet _read_int/read_regular_text(/dev/zero)`, `(/dev/urandom)`). The case "live_check stdin /dev/null" now reads "stdin empty-tmp-file" (a different case: empty regular file, not a character device). Row count: hostile_ev3 276 vs EV6 282.
4. The 7 NEW r7 cases of EV7-PLAN section 7 (`hostile_r7.py`: IMAP user quoting, fake_hubspot chunked/short, slow sender, burst URL listener count, start_all port owner, n8n exit-code table, r6 survivors) were NOT written or run: the brief asked for the EV6 drivers only. Only the existing EV6 cases that cover parts of them ran (run6.py `imap_user`, `cl_fake_hubspot`, `h` part for burst URLs, `g` part for start_all/reset).
5. Not run: NUL byte in an environment value or argument (the operating system refuses to start it; the same `HARNESS embedded null byte` rows as EV6 appear). `rc=None HANG` for `fake_model_server:--port=0` is a server that does not exit; the driver kills it at its timeout (same in EV6).
6. The `Start? [y/N]` question of `run_live_check.py` appears in some outputs; stdin was always closed or an empty file, so the script stopped by itself ("stopped, nothing was called"). I never answered it.
7. Windows scripts, CodeQL, SonarCloud, CodeRabbit, the full test suite, mutation runs: not run (not in this brief).

## 1. What ran (commands)
```
git -C demo-frozen/repo2 archive frozen2 | tar -x -C tree-EV7H     (and tree-old-EV7H);  git init + commit in tree-EV7H; git apply --check; git apply   (rc 0, 0)
cp EV6 drivers to out/EV7H; sed 's#tree-old-EV6#tree-old-EV7H#g; s#tree-EV6#tree-EV7H#g; s#tmp-EV6#tmp-EV7H#g; s#out/EV6#out/EV7H#g; s#EV6#EV7H#g'  (grep EV6 afterwards: nothing)
gen_inputs.py  (book.sqlite3, req1/req100k logs, 300 MB files, drain/facts variants)
bash run-hostile.sh      22:38:20Z to 22:51:55Z  (driver rc=0, extra rc=0, ev3 rc=0, rerun_ci rc=0, resultfile old/new rc=0, ev5 rc=0)
python3 run6.py          67 cases, 134 rows (22:52Z to about 22:56Z)
python3 run6b.py g, h, j, f, f2   each rc=0   (run6b-all.sh)
```
All server and script runs are inside `unshare -n` with `lo_up-q4g.py` as the drivers did. Raw files: `hostile/results*.jsonl`, `hostile/*.out`, `run6.out`, `run6b-*.out`, `hostile/j-*.log`, `hostile-table.md` (full per-case table with class name, typed echo, peak MB), `counts-new.txt`.

## 2. Counts of rows with a traceback or a hang (hang = my timeout hit, including rc=TIMEOUT)
| driver | old rows | old traceback | old hang | new rows | new traceback | new hang |
|---|---|---|---|---|---|---|
| hostile_driver.py+hostile_extra.py | 149 | 17 | 26 | 149 | 0 | 1 |
| hostile_ev3.py | 138 | 23 | 22 | 138 | 0 | 3 |
| rerun_ci.py | 17 | 0 | 1 | 17 | 0 | 0 |
| hostile_ev5.py | 157 | 24 | 27 | 157 | 2 | 6 |
| run6.py (hostile_r6.py) | 67 | 9 | 1 | 67 | 0 | 0 |
| run6b g (scripts) | 4 | 0 | 2 | 4 | 0 | 0 |
| run6b h (burst url) | 2 | 0 | 0 | 2 | 0 | 0 |
| run6b f | 5 | 0 | 0 | 5 | 0 | 0 |
| run6b f2 | 1 | 0 | 0 | 1 | 0 | 0 |
| TOTAL | 540 | 73 | 79 | 540 | 2 | 10 |

EV6 counts for comparison (from EV6-EVIDENCE-r6.md section 5, rows by file): new traceback 2 (ev5) + 1 (r6, `e:fake_hubspot Content-Length=missing`), new hang flag 1 + 2 + 2; here new traceback 2 (both `load_driver:dead desk burst` rows, same as EV6) and r6 file 0.

## 3. Differences between EV6 (r6) and EV7H (r7), new tree and old tree (rc, hang, traceback, lines compared; rows in both runs)
Old tree: no row differs from EV6 except the cases listed ONLY-... (renamed or removed /dev cases, and f2 whose generated file is 881 bytes per row now, 883 then). New tree differences (raw, from `diff-vs-EV6.txt`):
```
== results-ci-validfacts.jsonl EV6 rows 34 EV7H rows 34
 DIFF ('check_invariants3:--book=fifo', 'new') [('rc', '2', '4')]
 DIFF ('check_invariants3:--catcher=fifo', 'new') [('rc', '2', '4')]
 DIFF ('check_invariants3:--crm=fifo', 'new') [('rc', '2', '4')]
 DIFF ('check_invariants3:--facts=fifo', 'new') [('rc', '2', '4')]
 DIFF ('check_invariants3:--model-log=fifo', 'new') [('rc', '2', '4')]
 DIFF ('check_invariants3:--requests=fifo', 'new') [('rc', '2', '4')]
== results-ev5.jsonl EV6 rows 314 EV7H rows 314
 DIFF ("lead_desk.server:DESK_BIND='[::1]'", 'new') [('rc', '1', '7')]
 DIFF ("lead_desk.server:DESK_BIND='xxxxxxxxxxxx'", 'new') [('rc', '1', '7')]
 DIFF ('burst.py:--url=http://0.0.0.0:1', 'new') [('rc', 'TIMEOUT', '2'), ('lines', 0, 1)]
 DIFF ('burst.py:--url=http://evil.example:1', 'new') [('rc', '1', '2'), ('lines', 4, 1)]
 DIFF ('live_check:--cap-run 1 valid, closed stdin', 'new') [('rc', '1', '6'), ('lines', 1, 3)]
 DIFF ('n8n_api:list, N8N_URL bad', 'new') [('rc', '1', '4')]
 DIFF ('n8n_api:list, no key file set', 'new') [('rc', '1', '4')]
 DIFF ('real_check bad config:DESK_BIND=bad host!', 'new') [('rc', '1', '6')]
== results-f.jsonl EV6 rows 10 EV7H rows 10
== results-f2.jsonl EV6 rows 2 EV7H rows 2
 ONLY-EV7H ('f2:100,000-row log, ~881-byte rows, valid facts', 'new')
 ONLY-EV7H ('f2:100,000-row log, ~881-byte rows, valid facts', 'old')
 ONLY-EV6 ('f2:100,000-row log, ~883-byte rows, valid facts', 'new')
 ONLY-EV6 ('f2:100,000-row log, ~883-byte rows, valid facts', 'old')
== results-g.jsonl EV6 rows 8 EV7H rows 8
== results-h.jsonl EV6 rows 4 EV7H rows 4
 DIFF ('h:burst.py --url http://192.0.2.1:1', 'new') [('rc', 1, 2)]
 DIFF ('h:burst.py --url http://evil.example:1', 'new') [('rc', 1, 2)]
== results-j.jsonl EV6 rows 2 EV7H rows 1
 ONLY-EV6 ('[["failed", []], ["rc", 0], ["shape", "00-baseline-no-shape"', None)
== results-new-cases.jsonl EV6 rows 282 EV7H rows 276
 DIFF ('check_invariants3:--book=fifo', 'new') [('rc', '2', '4')]
 DIFF ('check_invariants3:--catcher=fifo', 'new') [('rc', '2', '4')]
 DIFF ('check_invariants3:--crm=fifo', 'new') [('rc', '2', '4')]
 DIFF ('check_invariants3:--facts=fifo', 'new') [('rc', '2', '4')]
 DIFF ('check_invariants3:--model-log=fifo', 'new') [('rc', '2', '4')]
 DIFF ('check_invariants3:--requests=fifo', 'new') [('rc', '2', '4')]
 DIFF ('live_check:closed stdin (<&-)', 'new') [('rc', 1, 6)]
 DIFF ('live_check:leads=1 (stdin /dev/null)', 'new') [('rc', '1', '6'), ('lines', 1, 3)]
 DIFF ('live_check:runs=1 (stdin /dev/null)', 'new') [('rc', '1', '6'), ('lines', 1, 3)]
 ONLY-EV6 ('live_check:stdin /dev/null', 'new')
 ONLY-EV6 ('live_check:stdin /dev/null', 'old')
 ONLY-EV7H ('live_check:stdin empty-tmp-file', 'new')
 ONLY-EV7H ('live_check:stdin empty-tmp-file', 'old')
 DIFF ('real_check:IMAP_1_CA=PEM+utf8-comment', 'new') [('rc', '1', '6')]
 DIFF ('real_check:IMAP_1_CA=leaf-cert', 'new') [('rc', '1', '6')]
 DIFF ('real_check:IMAP_1_CA=valid-made-up-CA', 'new') [('rc', '1', '6')]
 DIFF ('real_check:IMAP_2_CA=PEM+utf8-comment', 'new') [('rc', '1', '6')]
 DIFF ('real_check:IMAP_2_CA=leaf-cert', 'new') [('rc', '1', '6')]
 DIFF ('real_check:IMAP_2_CA=valid-made-up-CA', 'new') [('rc', '1', '6')]
 ONLY-EV6 ('real_check:REAL_RESULT_FILE=/dev/full', 'new')
 ONLY-EV6 ('real_check:REAL_RESULT_FILE=/dev/full', 'old')
 DIFF ('real_check:REAL_RESULT_FILE=100MB-file', 'new') [('rc', '1', '6')]
 DIFF ('real_check:SMTP_CA=100MB', 'new') [('rc', '1', '6')]
 DIFF ('real_check:SMTP_CA=PEM+utf8-comment', 'new') [('rc', '1', '6')]
 DIFF ('real_check:SMTP_CA=directory', 'new') [('rc', '1', '6')]
 DIFF ('real_check:SMTP_CA=empty', 'new') [('rc', '1', '6')]
 DIFF ('real_check:SMTP_CA=fifo', 'new') [('rc', '1', '6')]
 DIFF ('real_check:SMTP_CA=garbage', 'new') [('rc', '1', '6')]
 DIFF ('real_check:SMTP_CA=leaf-cert', 'new') [('rc', '1', '6')]
 DIFF ('real_check:SMTP_CA=valid-made-up-CA', 'new') [('rc', '1', '6')]
 DIFF ('real_check:SMTP_CA=whitespace', 'new') [('rc', '1', '6')]
 ONLY-EV6 ('snippet _read_int/read_regular_text(/dev/urandom)', 'new')
 ONLY-EV6 ('snippet _read_int/read_regular_text(/dev/urandom)', 'old')
 ONLY-EV6 ('snippet _read_int/read_regular_text(/dev/zero)', 'new')
 ONLY-EV6 ('snippet _read_int/read_regular_text(/dev/zero)', 'old')
== results-r6.jsonl EV6 rows 134 EV7H rows 134
 DIFF ('a:run_live_check key-file=bom-ok', 'new') [('lines', 1, 3)]
 DIFF ('a:run_live_check key-file=good', 'new') [('lines', 1, 3)]
 DIFF ('e:fake_hubspot Content-Length=missing', 'new') [('tb', True, False), ('lines', 20, 0)]
== results.jsonl EV6 rows 298 EV7H rows 298
 DIFF ('check_invariants2:--book=fifo', 'new') [('rc', 2, 4)]
 DIFF ('check_invariants2:--catcher=fifo', 'new') [('rc', 2, 4)]
 DIFF ('check_invariants2:--crm=fifo', 'new') [('rc', 2, 4)]
 DIFF ('check_invariants2:--facts=fifo', 'new') [('rc', 2, 4)]
 DIFF ('check_invariants2:--model-log=fifo', 'new') [('rc', 2, 4)]
 DIFF ('check_invariants2:--requests=fifo', 'new') [('rc', 2, 4)]
 DIFF ('check_invariants:--book=fifo', 'new') [('rc', 2, 4)]
 DIFF ('check_invariants:--catcher=fifo', 'new') [('rc', 2, 4)]
 DIFF ('check_invariants:--crm=fifo', 'new') [('rc', 2, 4)]
 DIFF ('check_invariants:--facts=fifo', 'new') [('rc', 2, 4)]
 DIFF ('check_invariants:--model-log=fifo', 'new') [('rc', 2, 4)]
 DIFF ('check_invariants:--requests=100MB', 'new') [('rc', 2, 4)]
 DIFF ('check_invariants:--requests=fifo', 'new') [('rc', 2, 4)]
 DIFF ('live_check:model-ctl', 'new') [('rc', 1, 6)]
 DIFF ('live_check_closed_stdin', 'new') [('rc', 1, 6)]
 DIFF ('real_check:DESK_HUBSPOT_KEY_FILE=fifo', 'new') [('rc', 1, 6)]
 DIFF ('real_check:DESK_SMTPP_PASSWORD_FILE=dir', 'new') [('rc', 1, 6)]
 DIFF ('real_check:DESK_SMTPP_PASSWORD_FILE=fifo', 'new') [('rc', 1, 6)]
 DIFF ('real_check_imap_ca:valid', 'new') [('rc', 1, 6)]
 DIFF ('real_check_smtp_ca:100MB', 'new') [('rc', 1, 6)]
 DIFF ('real_check_smtp_ca:dir', 'new') [('rc', 1, 6)]
 DIFF ('real_check_smtp_ca:empty', 'new') [('rc', 1, 6)]
 DIFF ('real_check_smtp_ca:fifo', 'new') [('rc', 1, 6)]
 DIFF ('real_check_smtp_ca:valid', 'new') [('rc', 1, 6)]
 DIFF ('real_check_smtp_ca:ws-only', 'new') [('rc', 1, 6)]
```
Plain reading of the raw differences, no verdict: most changed rows are exit codes (r6 1 or 2, r7 4, 6 or 7 for the same refusal text); `burst.py --url http://0.0.0.0:1` went from TIMEOUT (no output) to rc=2 with a one-line refusal; `burst.py --url http://evil.example:1` went from rc=1 with 4 lines to rc=2 with 1 line and 0 connect() calls (strace count in run6b h: old 6, new 0; `http://192.0.2.1:1`: old 1, new 0); `fake_hubspot Content-Length=missing` went from a traceback (20 lines) to no output and no traceback; `live_check` with valid inputs now prints the "models: ... calls per model" lines (3 lines instead of 1) before it stops at the question. `real_check ... CA=valid-made-up-CA` rows: rc 1 to 6 with the same first line, and the config here is my rebuilt one (see gap 2).

## 4. Raw output for the failure in gap 1
```
$ (tree-EV7H) unshare -n ... lo_up-q4g.py python -m pytest -q -p no:cacheprovider tests/test_file_call_guard.py
E   AssertionError: assert not ['src/lead_desk/regfile.py:242: os.stat (is os.stat) is not listed in ALLOWED_CALLS']
FAILED tests/test_file_call_guard.py::test_every_import_and_file_call_in_the_code_is_listed_with_a_reason_or_goes_through_the_one_reader
1 failed, 10 passed in 1.91s
```
(`fileguard-direct.txt`; the old tree has no such test file.) Context line: `regfile.py:242  mode = os.stat(path).st_mode` inside `refuse_replacing_special`. The table `ALLOWED_CALLS` in the test lists `os.stat` for desk.py and lockfile.py only. run6b j summary on r7: every shape row "1 failed, 10 passed" (baseline included); on r6: baseline "9 passed", each shape "1 failed, 8 passed".

## 5. Per-case table (driver | case | old | new). `rc=None HANG` and `rc=TIMEOUT HANG` rows are listed in full; other columns are raw rc / traceback flag
| driver | case | old | new |
|---|---|---|---|
| hostile_driver.py+hostile_extra.py | smtp_ca:fifo | rc=None HANG | rc=0 |
| hostile_driver.py+hostile_extra.py | smtp_ca:empty | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | smtp_ca:100MB | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | smtp_ca:valid | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | smtp_ca:ws-only | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | smtp_ca:garbage | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | smtp_ca:dir | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | smtp_ca:nul-name | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | smtp_ca:missing | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | live_key:fifo | rc=None HANG | rc=0 |
| hostile_driver.py+hostile_extra.py | live_key:100MB-NUL | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | live_key:valid | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | live_key:empty | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | live_key:dir | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | hooks_flag:fifo | rc=None HANG | rc=0 |
| hostile_driver.py+hostile_extra.py | hooks_flag:100MB | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | hooks_flag:dir | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | trace_flag:fifo | rc=None HANG | rc=0 |
| hostile_driver.py+hostile_extra.py | trace_flag:100MB | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | trace_flag:dir | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | portal_armed:fifo | rc=None HANG | rc=0 |
| hostile_driver.py+hostile_extra.py | portal_armed:100MB | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | portal_armed:dir | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | catcher_control:fifo | rc=None HANG | rc=0 |
| hostile_driver.py+hostile_extra.py | catcher_control:100MB | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | catcher_control:dir | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | driver_int:fifo | rc=None HANG | rc=0 |
| hostile_driver.py+hostile_extra.py | driver_int:100MB | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | driver_int:dir | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | model_control:fifo | rc=None HANG | rc=0 |
| hostile_driver.py+hostile_extra.py | model_control:100MB | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | model_control:dir | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | real_check_smtp_ca:fifo | rc=1 | rc=6 |
| hostile_driver.py+hostile_extra.py | real_check_imap_ca:fifo | rc=None HANG | rc=2 |
| hostile_driver.py+hostile_extra.py | real_check_smtp_ca:empty | rc=1 | rc=6 |
| hostile_driver.py+hostile_extra.py | real_check_imap_ca:empty | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | real_check_smtp_ca:100MB | rc=1 | rc=6 |
| hostile_driver.py+hostile_extra.py | real_check_imap_ca:100MB | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | real_check_smtp_ca:valid | rc=1 | rc=6 |
| hostile_driver.py+hostile_extra.py | real_check_imap_ca:valid | rc=1 | rc=6 |
| hostile_driver.py+hostile_extra.py | real_check_smtp_ca:ws-only | rc=1 | rc=6 |
| hostile_driver.py+hostile_extra.py | real_check_imap_ca:ws-only | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | real_check_smtp_ca:dir | rc=1 | rc=6 |
| hostile_driver.py+hostile_extra.py | real_check_imap_ca:dir | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | live_check_closed_stdin | rc=1 TRACEBACK | rc=6 |
| hostile_driver.py+hostile_extra.py | live_check:effort-' low' | rc=1 TRACEBACK | rc=2 |
| hostile_driver.py+hostile_extra.py | live_check:effort-ultra | rc=1 TRACEBACK | rc=2 |
| hostile_driver.py+hostile_extra.py | live_check:leads-0 | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | live_check:leads-huge | rc=None HANG | rc=2 |
| hostile_driver.py+hostile_extra.py | live_check:timeout-nan | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | live_check:timeout-inf | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | live_check:max-tokens-0 | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | live_check:cap-negative | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | live_check:cap-huge | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | live_check:model-ctl | rc=1 TRACEBACK | rc=6 |
| hostile_driver.py+hostile_extra.py | live_check:price-date-ctl | rc=1 TRACEBACK | rc=2 |
| hostile_driver.py+hostile_extra.py | live_check:key-file-fifo | rc=1 TRACEBACK | rc=2 |
| hostile_driver.py+hostile_extra.py | live_check:key-file-dir | rc=1 TRACEBACK | rc=2 |
| hostile_driver.py+hostile_extra.py | live_check:ledger-fifo | rc=1 TRACEBACK | rc=2 |
| hostile_driver.py+hostile_extra.py | live_check:ledger-dir | rc=1 TRACEBACK | rc=2 |
| hostile_driver.py+hostile_extra.py | live_check:base-url-ctl | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | check_invariants:--requests=fifo | rc=2 | rc=4 |
| hostile_driver.py+hostile_extra.py | check_invariants:--catcher=fifo | rc=2 | rc=4 |
| hostile_driver.py+hostile_extra.py | check_invariants:--crm=fifo | rc=2 | rc=4 |
| hostile_driver.py+hostile_extra.py | check_invariants:--model-log=fifo | rc=2 | rc=4 |
| hostile_driver.py+hostile_extra.py | check_invariants:--book=fifo | rc=2 | rc=4 |
| hostile_driver.py+hostile_extra.py | check_invariants:--facts=fifo | rc=None HANG | rc=4 |
| hostile_driver.py+hostile_extra.py | check_invariants:--requests=100MB | rc=2 | rc=4 |
| hostile_driver.py+hostile_extra.py | catcher:--control=fifo(server) | rc=None HANG | rc=2 |
| hostile_driver.py+hostile_extra.py | catcher:--out=fifo | rc=None HANG | rc=2 |
| hostile_driver.py+hostile_extra.py | load_driver:--log=fifo | rc=None HANG | rc=2 |
| hostile_driver.py+hostile_extra.py | load_driver:--facts=fifo | rc=None HANG | rc=2 |
| hostile_driver.py+hostile_extra.py | load_driver:bad-scenario-huge | rc=None HANG | rc=2 |
| hostile_driver.py+hostile_extra.py | load_driver:workers-0 | rc=None HANG | rc=2 |
| hostile_driver.py+hostile_extra.py | load_driver:workers-huge | rc=None HANG | rc=2 |
| hostile_driver.py+hostile_extra.py | fake_model_server:--control-file=fifo(server) | rc=None HANG | rc=2 |
| hostile_driver.py+hostile_extra.py | fake_model_server:--key-file=fifo | rc=None HANG | rc=2 |
| hostile_driver.py+hostile_extra.py | fake_model_server:--call-log=fifo | rc=None HANG | rc=2 |
| hostile_driver.py+hostile_extra.py | fake_model_server:--port=0 | rc=None HANG | rc=None HANG |
| hostile_driver.py+hostile_extra.py | fake_model_server:--port=-1 | rc=1 TRACEBACK | rc=2 |
| hostile_driver.py+hostile_extra.py | fake_model_server:--port=70000 | rc=1 TRACEBACK | rc=2 |
| hostile_driver.py+hostile_extra.py | fake_model_server:--port=999999 | rc=1 TRACEBACK | rc=2 |
| hostile_driver.py+hostile_extra.py | real_check:dry-port-base=0 | rc=1 | rc=2 |
| hostile_driver.py+hostile_extra.py | real_check:dry-port-base=-1 | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | real_check:dry-port-base=70000 | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | real_check:dry-port-base=huge | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | real_check:dry-smtp-script-ctl | rc=1 | rc=2 |
| hostile_driver.py+hostile_extra.py | real_check:config-fifo | rc=None HANG | rc=2 |
| hostile_driver.py+hostile_extra.py | real_check:config-dir | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | real_check:config-100MB | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | real_check:config-nul-bytes | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | real_check:config-missing | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | real_check:assume-yes-without-dry | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | real_check:config-ctl-chars | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | real_check:REAL_RESULT_FILE=fifo | rc=1 | rc=2 |
| hostile_driver.py+hostile_extra.py | real_check:REAL_PERSONS=huge | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | real_check:DESK_PORT=70000 | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | real_check:DESK_HUBSPOT_KEY_FILE=fifo | rc=1 | rc=6 |
| hostile_driver.py+hostile_extra.py | real_check:DESK_SMTPP_PASSWORD_FILE=fifo | rc=1 | rc=6 |
| hostile_driver.py+hostile_extra.py | real_check:DESK_SMTPP_PASSWORD_FILE=dir | rc=1 | rc=6 |
| hostile_driver.py+hostile_extra.py | desk_setting:port,DESK_PORT='0' | rc=2 | rc=0 |
| hostile_driver.py+hostile_extra.py | desk_setting:port,DESK_PORT='-1' | rc=2 | rc=4 |
| hostile_driver.py+hostile_extra.py | desk_setting:port,DESK_PORT='70000' | rc=2 | rc=4 |
| hostile_driver.py+hostile_extra.py | desk_setting:port,DESK_PORT='99999999' | rc=2 | rc=4 |
| hostile_driver.py+hostile_extra.py | desk_setting:port,DESK_PORT='1e999' | rc=2 | rc=4 |
| hostile_driver.py+hostile_extra.py | desk_setting:port,DESK_PORT='\x1b[0m' | rc=2 | rc=4 |
| hostile_driver.py+hostile_extra.py | desk_setting:port,DESK_PORT=' 5' | rc=2 | rc=0 |
| hostile_driver.py+hostile_extra.py | desk_setting:port,DESK_PORT='5 ' | rc=2 | rc=0 |
| hostile_driver.py+hostile_extra.py | desk_setting:data-dir,DESK_DB_PATH=fifo | rc=2 | rc=4 |
| hostile_driver.py+hostile_extra.py | desk_setting:db-path,DESK_DB_PATH=dir | rc=2 | rc=4 |
| hostile_driver.py+hostile_extra.py | desk_setting:no-args | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | desk_setting:DESK_LIVE_EFFORT=' low' | rc=2 | rc=4 |
| hostile_driver.py+hostile_extra.py | desk_setting:DESK_LIVE_EFFORT=ultra | rc=2 | rc=4 |
| hostile_driver.py+hostile_extra.py | feed:--index=huge | rc=1 TRACEBACK | rc=2 |
| hostile_driver.py+hostile_extra.py | feed:--index=0 | rc=1 TRACEBACK | rc=2 |
| hostile_driver.py+hostile_extra.py | feed:--index=-1 | rc=1 TRACEBACK | rc=2 |
| hostile_driver.py+hostile_extra.py | hubspot_probe:--yes-spend-calls=huge | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | hubspot_probe:--token-env=ctl | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | hubspot_probe:--dry-run=ctl-url | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | n8n_api:KEY_FILE=fifo | rc=None HANG | rc=2 |
| hostile_driver.py+hostile_extra.py | n8n_api:KEY_FILE=100MB | rc=1 | rc=2 |
| hostile_driver.py+hostile_extra.py | n8n_api:KEY_FILE=dir | rc=1 | rc=2 |
| hostile_driver.py+hostile_extra.py | scrub_n8n_export:in=fifo | rc=None HANG | rc=2 |
| hostile_driver.py+hostile_extra.py | scrub_n8n_export:in=100MB | rc=1 TRACEBACK | rc=2 |
| hostile_driver.py+hostile_extra.py | scrub_n8n_export:out=fifo | rc=1 TRACEBACK | rc=2 |
| hostile_driver.py+hostile_extra.py | scrub_n8n_export:out=dir | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | scrub_n8n_export:in=missing | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | crash_desk:DESK_DB_PATH=fifo | rc=1 | rc=4 |
| hostile_driver.py+hostile_extra.py | reset_check:no-args | rc=0 | rc=0 |
| hostile_driver.py+hostile_extra.py | feed:--source=ctl | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | desk_setting_live:EFFORT='low' | rc=2 | rc=0 |
| hostile_driver.py+hostile_extra.py | desk_setting_live:EFFORT=' low' | rc=2 | rc=0 |
| hostile_driver.py+hostile_extra.py | desk_setting_live:EFFORT='ultra' | rc=2 | rc=4 |
| hostile_driver.py+hostile_extra.py | desk_setting_live:EFFORT='low\x1b' | rc=2 | rc=4 |
| hostile_driver.py+hostile_extra.py | desk_setting_live:EFFORT='' | rc=2 | rc=4 |
| hostile_driver.py+hostile_extra.py | desk_setting_live:EFFORT='LLLLLLLLLL' | rc=2 | rc=4 |
| hostile_driver.py+hostile_extra.py | desk_setting_live:key-file=fifo | rc=2 | rc=0 |
| hostile_driver.py+hostile_extra.py | desk_setting_live:ledger=fifo | rc=2 | rc=0 |
| hostile_driver.py+hostile_extra.py | check_invariants2:--requests=fifo | rc=2 | rc=4 |
| hostile_driver.py+hostile_extra.py | check_invariants2:--catcher=fifo | rc=2 | rc=4 |
| hostile_driver.py+hostile_extra.py | check_invariants2:--crm=fifo | rc=2 | rc=4 |
| hostile_driver.py+hostile_extra.py | check_invariants2:--model-log=fifo | rc=2 | rc=4 |
| hostile_driver.py+hostile_extra.py | check_invariants2:--book=fifo | rc=2 | rc=4 |
| hostile_driver.py+hostile_extra.py | check_invariants2:--facts=fifo | rc=None HANG | rc=4 |
| hostile_driver.py+hostile_extra.py | check_invariants2:--requests=100MB | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | check_invariants2:--catcher=100MB | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | check_invariants2:--crm=100MB | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | check_invariants2:--model-log=100MB | rc=2 | rc=2 |
| hostile_driver.py+hostile_extra.py | check_invariants2:--facts=100MB | rc=2 | rc=2 |
| hostile_ev3.py | fake_model_server.py:--port='-1' | rc=1 TRACEBACK | rc=2 |
| hostile_ev3.py | fake_model_server.py:--port='70000' | rc=1 TRACEBACK | rc=2 |
| hostile_ev3.py | fake_model_server.py:--port='99999999' | rc=1 TRACEBACK | rc=2 |
| hostile_ev3.py | fake_model_server.py:--port='abc' | rc=2 | rc=2 |
| hostile_ev3.py | fake_model_server.py:--port='' | rc=2 | rc=2 |
| hostile_ev3.py | fake_model_server.py:--host='bad' | rc=2 | rc=2 |
| hostile_ev3.py | fake_model_server.py:--host='bad host!' | rc=2 | rc=2 |
| hostile_ev3.py | fake_model_server.py:--host='256.1.1.1' | rc=2 | rc=2 |
| hostile_ev3.py | fake_model_server.py:--host='' | rc=2 | rc=2 |
| hostile_ev3.py | fake_model_server.py:port already in use (loopback 18777) | rc=1 TRACEBACK | rc=2 |
| hostile_ev3.py | catcher.py:--port='-1' | rc=1 TRACEBACK | rc=2 |
| hostile_ev3.py | catcher.py:--port='70000' | rc=1 TRACEBACK | rc=2 |
| hostile_ev3.py | catcher.py:--port='99999999' | rc=1 TRACEBACK | rc=2 |
| hostile_ev3.py | catcher.py:--port='abc' | rc=2 | rc=2 |
| hostile_ev3.py | catcher.py:--port='' | rc=2 | rc=2 |
| hostile_ev3.py | catcher.py:--host='bad' | rc=1 TRACEBACK | rc=2 |
| hostile_ev3.py | catcher.py:--host='bad host!' | rc=1 TRACEBACK | rc=2 |
| hostile_ev3.py | catcher.py:--host='256.1.1.1' | rc=1 TRACEBACK | rc=2 |
| hostile_ev3.py | catcher.py:--host='' | rc=TIMEOUT | rc=2 |
| hostile_ev3.py | catcher.py:port already in use (loopback 18777) | rc=1 TRACEBACK | rc=2 |
| hostile_ev3.py | fakes_server.py:--port='-1' | rc=1 TRACEBACK | rc=2 |
| hostile_ev3.py | fakes_server.py:--port='70000' | rc=1 TRACEBACK | rc=2 |
| hostile_ev3.py | fakes_server.py:--port='99999999' | rc=1 TRACEBACK | rc=2 |
| hostile_ev3.py | fakes_server.py:--port='abc' | rc=2 | rc=2 |
| hostile_ev3.py | fakes_server.py:--port='' | rc=2 | rc=2 |
| hostile_ev3.py | fakes_server.py:--host='bad' | rc=2 | rc=2 |
| hostile_ev3.py | fakes_server.py:--host='bad host!' | rc=2 | rc=2 |
| hostile_ev3.py | fakes_server.py:--host='256.1.1.1' | rc=2 | rc=2 |
| hostile_ev3.py | fakes_server.py:--host='' | rc=2 | rc=2 |
| hostile_ev3.py | fakes_server.py:port already in use (loopback 18777) | rc=1 TRACEBACK | rc=2 |
| hostile_ev3.py | burst.py:--n=0 | rc=2 | rc=2 |
| hostile_ev3.py | burst.py:--n=-1 | rc=2 | rc=2 |
| hostile_ev3.py | burst.py:--n=1 | rc=2 | rc=2 |
| hostile_ev3.py | burst.py:--n=1000000000 | rc=2 | rc=2 |
| hostile_ev3.py | burst.py:--n=99999999999999999999 | rc=2 | rc=2 |
| hostile_ev3.py | burst.py:--n=nan | rc=2 | rc=2 |
| hostile_ev3.py | load_driver:--scenario=burst:nan | rc=1 TRACEBACK | rc=2 |
| hostile_ev3.py | load_driver:--scenario=burst:inf | rc=1 TRACEBACK | rc=2 |
| hostile_ev3.py | load_driver:--scenario=burst:99999999 | rc=TIMEOUT | rc=2 |
| hostile_ev3.py | load_driver:--scenario=burst:0 | rc=2 | rc=2 |
| hostile_ev3.py | load_driver:--scenario=burst:-1 | rc=2 | rc=2 |
| hostile_ev3.py | load_driver:--scenario=burst:1.5 | rc=TIMEOUT HANG | rc=TIMEOUT HANG |
| hostile_ev3.py | load_driver:--scenario=burst:1e9 | rc=TIMEOUT | rc=2 |
| hostile_ev3.py | load_driver:burst:1 workers=0 | rc=TIMEOUT HANG | rc=2 |
| hostile_ev3.py | load_driver:burst:1 threads=0 | rc=TIMEOUT HANG | rc=2 |
| hostile_ev3.py | load_driver:burst:1 workers=1e9 | rc=TIMEOUT HANG | rc=2 |
| hostile_ev3.py | load_driver:burst:1 threads=1e9 | rc=TIMEOUT HANG | rc=2 |
| hostile_ev3.py | load_driver:burst:1 workers=huge | rc=TIMEOUT HANG | rc=2 |
| hostile_ev3.py | load_driver:burst:1 threads=huge | rc=TIMEOUT HANG | rc=2 |
| hostile_ev3.py | load_driver:burst:1 workers=-1 | rc=TIMEOUT HANG | rc=2 |
| hostile_ev3.py | load_driver:burst:1 seed=huge | rc=TIMEOUT HANG | rc=2 |
| hostile_ev3.py | load_driver:burst:1 unreachable-url (timed) | rc=TIMEOUT HANG | rc=TIMEOUT HANG |
| hostile_ev3.py | real_check:REAL_RESULT_FILE=missing-folder | rc=1 | rc=2 |
| hostile_ev3.py | real_check:REAL_RESULT_FILE=folder | rc=1 | rc=2 |
| hostile_ev3.py | real_check:REAL_RESULT_FILE=fifo | rc=1 | rc=2 |
| hostile_ev3.py | real_check:REAL_RESULT_FILE=100MB-file | rc=1 | rc=6 |
| hostile_ev3.py | live_check:leads=0 (stdin /dev/null) | rc=2 | rc=2 |
| hostile_ev3.py | live_check:leads=1 (stdin /dev/null) | rc=1 TRACEBACK | rc=6 |
| hostile_ev3.py | live_check:leads=1001 (stdin /dev/null) | rc=1 TRACEBACK | rc=2 |
| hostile_ev3.py | live_check:leads=huge (stdin /dev/null) | rc=TIMEOUT | rc=2 |
| hostile_ev3.py | live_check:runs=0 (stdin /dev/null) | rc=2 | rc=2 |
| hostile_ev3.py | live_check:runs=101 (stdin /dev/null) | rc=1 TRACEBACK | rc=2 |
| hostile_ev3.py | live_check:runs=1 (stdin /dev/null) | rc=1 TRACEBACK | rc=6 |
| hostile_ev3.py | desk_setting:DESK_PORT=' 5' | rc=2 | rc=0 |
| hostile_ev3.py | desk_setting:DESK_PORT='5 ' | rc=2 | rc=0 |
| hostile_ev3.py | desk_setting:DESK_PORT='5\n' | rc=2 | rc=0 |
| hostile_ev3.py | desk_setting:DESK_PORT='٥' (arabic-indic digit) | rc=2 | rc=4 |
| hostile_ev3.py | desk_setting:DESK_PORT='1_0' | rc=2 | rc=4 |
| hostile_ev3.py | desk_setting:DESK_LIVE_EFFORT=' low' | rc=2 | rc=4 |
| hostile_ev3.py | desk_setting:DESK_LIVE_EFFORT='low ' | rc=2 | rc=4 |
| hostile_ev3.py | desk_setting:db-path DESK_DB_PATH=folder | rc=2 | rc=4 |
| hostile_ev3.py | desk_setting:db-path DESK_DB_PATH=fifo | rc=2 | rc=4 |
| hostile_ev3.py | desk_setting:data-dir DESK_DB_PATH=folder | rc=2 | rc=4 |
| hostile_ev3.py | fake_model_server:--key-file=FIFO | rc=TIMEOUT | rc=2 |
| hostile_ev3.py | fake_model_server:--key-file=3MB | rc=TIMEOUT | rc=2 |
| hostile_ev3.py | fake_model_server:--key-file=100MB | rc=TIMEOUT | rc=2 |
| hostile_ev3.py | fake_model_server:--key-file=good | rc=TIMEOUT | rc=TIMEOUT |
| hostile_ev3.py | real_check:IMAP_1_CA=fifo | rc=TIMEOUT | rc=2 |
| hostile_ev3.py | real_check:IMAP_2_CA=fifo | rc=TIMEOUT | rc=2 |
| hostile_ev3.py | real_check:SMTP_CA=fifo | rc=1 | rc=6 |
| hostile_ev3.py | inproc smtp_ca:fifo | rc=TIMEOUT | rc=0 |
| hostile_ev3.py | real_check:IMAP_1_CA=empty | rc=2 | rc=2 |
| hostile_ev3.py | real_check:IMAP_2_CA=empty | rc=2 | rc=2 |
| hostile_ev3.py | real_check:SMTP_CA=empty | rc=1 | rc=6 |
| hostile_ev3.py | inproc smtp_ca:empty | rc=0 | rc=0 |
| hostile_ev3.py | real_check:IMAP_1_CA=whitespace | rc=2 | rc=2 |
| hostile_ev3.py | real_check:IMAP_2_CA=whitespace | rc=2 | rc=2 |
| hostile_ev3.py | real_check:SMTP_CA=whitespace | rc=1 | rc=6 |
| hostile_ev3.py | inproc smtp_ca:whitespace | rc=0 | rc=0 |
| hostile_ev3.py | real_check:IMAP_1_CA=garbage | rc=2 | rc=2 |
| hostile_ev3.py | real_check:IMAP_2_CA=garbage | rc=2 | rc=2 |
| hostile_ev3.py | real_check:SMTP_CA=garbage | rc=1 | rc=6 |
| hostile_ev3.py | inproc smtp_ca:garbage | rc=0 | rc=0 |
| hostile_ev3.py | real_check:IMAP_1_CA=directory | rc=2 | rc=2 |
| hostile_ev3.py | real_check:IMAP_2_CA=directory | rc=2 | rc=2 |
| hostile_ev3.py | real_check:SMTP_CA=directory | rc=1 | rc=6 |
| hostile_ev3.py | inproc smtp_ca:directory | rc=0 | rc=0 |
| hostile_ev3.py | real_check:IMAP_1_CA=100MB | rc=2 | rc=2 |
| hostile_ev3.py | real_check:IMAP_2_CA=100MB | rc=2 | rc=2 |
| hostile_ev3.py | real_check:SMTP_CA=100MB | rc=1 | rc=6 |
| hostile_ev3.py | inproc smtp_ca:100MB | rc=0 | rc=0 |
| hostile_ev3.py | real_check:IMAP_1_CA=PEM+utf8-comment | rc=1 | rc=6 |
| hostile_ev3.py | real_check:IMAP_2_CA=PEM+utf8-comment | rc=1 | rc=6 |
| hostile_ev3.py | real_check:SMTP_CA=PEM+utf8-comment | rc=1 | rc=6 |
| hostile_ev3.py | inproc smtp_ca:PEM+utf8-comment | rc=0 | rc=0 |
| hostile_ev3.py | real_check:IMAP_1_CA=valid-made-up-CA | rc=1 | rc=6 |
| hostile_ev3.py | real_check:IMAP_2_CA=valid-made-up-CA | rc=1 | rc=6 |
| hostile_ev3.py | real_check:SMTP_CA=valid-made-up-CA | rc=1 | rc=6 |
| hostile_ev3.py | inproc smtp_ca:valid-made-up-CA | rc=0 | rc=0 |
| hostile_ev3.py | real_check:IMAP_1_CA=leaf-cert | rc=1 | rc=6 |
| hostile_ev3.py | real_check:IMAP_2_CA=leaf-cert | rc=1 | rc=6 |
| hostile_ev3.py | real_check:SMTP_CA=leaf-cert | rc=1 | rc=6 |
| hostile_ev3.py | inproc smtp_ca:leaf-cert | rc=0 | rc=0 |
| hostile_ev3.py | check_invariants3:--requests=100MB-A | rc=2 | rc=2 |
| hostile_ev3.py | check_invariants3:--requests=100MB-NUL | rc=2 | rc=2 |
| hostile_ev3.py | check_invariants3:--requests=fifo | rc=2 | rc=4 |
| hostile_ev3.py | check_invariants3:--catcher=100MB-A | rc=2 | rc=2 |
| hostile_ev3.py | check_invariants3:--catcher=100MB-NUL | rc=2 | rc=2 |
| hostile_ev3.py | check_invariants3:--catcher=fifo | rc=2 | rc=4 |
| hostile_ev3.py | check_invariants3:--crm=100MB-A | rc=2 | rc=2 |
| hostile_ev3.py | check_invariants3:--crm=100MB-NUL | rc=2 | rc=2 |
| hostile_ev3.py | check_invariants3:--crm=fifo | rc=2 | rc=4 |
| hostile_ev3.py | check_invariants3:--model-log=100MB-A | rc=2 | rc=2 |
| hostile_ev3.py | check_invariants3:--model-log=100MB-NUL | rc=2 | rc=2 |
| hostile_ev3.py | check_invariants3:--model-log=fifo | rc=2 | rc=4 |
| hostile_ev3.py | check_invariants3:all valid small inputs (control) | rc=2 | rc=2 |
| hostile_ev3.py | check_invariants3:--book=100MB-A | rc=2 | rc=2 |
| hostile_ev3.py | check_invariants3:--book=fifo | rc=2 | rc=4 |
| hostile_ev3.py | check_invariants3:--facts=100MB-A | rc=2 | rc=2 |
| hostile_ev3.py | check_invariants3:--facts=fifo | rc=TIMEOUT | rc=4 |
| hostile_ev3.py | snippet _read_int/read_regular_text(/proc) | rc=0 | rc=0 |
| hostile_ev3.py | snippet _read_int/read_regular_text(/proc/kcore) | rc=0 | rc=0 |
| hostile_ev3.py | snippet _read_int/read_regular_text(/proc/self/maps) | rc=0 | rc=0 |
| hostile_ev3.py | snippet _read_int/read_regular_text(/proc/self/mem) | rc=0 | rc=0 |
| hostile_ev3.py | snippet _read_int/read_regular_text(/proc/meminfo) | rc=0 | rc=0 |
| hostile_ev3.py | machine_facts() whole | rc=0 | rc=0 |
| hostile_ev3.py | live_check:closed stdin (<&-) | rc=1 TRACEBACK | rc=6 |
| hostile_ev3.py | live_check:stdin empty-tmp-file | rc=1 TRACEBACK | rc=6 |
| rerun_ci.py | check_invariants3:--requests=100MB-A | rc=2 | rc=2 |
| rerun_ci.py | check_invariants3:--requests=100MB-NUL | rc=2 | rc=2 |
| rerun_ci.py | check_invariants3:--requests=fifo | rc=2 | rc=4 |
| rerun_ci.py | check_invariants3:--catcher=100MB-A | rc=2 | rc=2 |
| rerun_ci.py | check_invariants3:--catcher=100MB-NUL | rc=2 | rc=2 |
| rerun_ci.py | check_invariants3:--catcher=fifo | rc=2 | rc=4 |
| rerun_ci.py | check_invariants3:--crm=100MB-A | rc=2 | rc=2 |
| rerun_ci.py | check_invariants3:--crm=100MB-NUL | rc=2 | rc=2 |
| rerun_ci.py | check_invariants3:--crm=fifo | rc=2 | rc=4 |
| rerun_ci.py | check_invariants3:--model-log=100MB-A | rc=2 | rc=2 |
| rerun_ci.py | check_invariants3:--model-log=100MB-NUL | rc=2 | rc=2 |
| rerun_ci.py | check_invariants3:--model-log=fifo | rc=2 | rc=4 |
| rerun_ci.py | check_invariants3:all valid small inputs (control) | rc=2 | rc=2 |
| rerun_ci.py | check_invariants3:--book=100MB-A | rc=2 | rc=2 |
| rerun_ci.py | check_invariants3:--book=fifo | rc=2 | rc=4 |
| rerun_ci.py | check_invariants3:--facts=100MB-A | rc=2 | rc=2 |
| rerun_ci.py | check_invariants3:--facts=fifo | rc=TIMEOUT | rc=4 |
| hostile_ev5.py | ss:fake_model_server.py --host='' | rc=2 | rc=2 |
| hostile_ev5.py | ss:fake_model_server.py --host='0.0.0.0' | rc=2 | rc=2 |
| hostile_ev5.py | ss:fake_model_server.py --host='not a host' | rc=2 | rc=2 |
| hostile_ev5.py | ss:fake_model_server.py --host='bad host!' | rc=2 | rc=2 |
| hostile_ev5.py | ss:fake_model_server.py --host='256.1.1.1' | rc=2 | rc=2 |
| hostile_ev5.py | ss:fake_model_server.py --host='aaaaaaaaaaaa' | rc=2 | rc=2 |
| hostile_ev5.py | ss:fake_model_server.py --host='ｌｏｃａｌｈｏｓｔ' | rc=2 | rc=2 |
| hostile_ev5.py | ss:fake_model_server.py --host='localhost' | rc=2 | rc=2 |
| hostile_ev5.py | ss:fake_model_server.py --host='127.0.0.1' | rc=2 | rc=2 |
| hostile_ev5.py | ss:fake_model_server.py --host='::1' | rc=2 | rc=2 |
| hostile_ev5.py | ss:catcher.py --host='' | rc=None | rc=2 |
| hostile_ev5.py | ss:catcher.py --host='0.0.0.0' | rc=None | rc=2 |
| hostile_ev5.py | ss:catcher.py --host='not a host' | rc=1 TRACEBACK | rc=2 |
| hostile_ev5.py | ss:catcher.py --host='bad host!' | rc=1 TRACEBACK | rc=2 |
| hostile_ev5.py | ss:catcher.py --host='256.1.1.1' | rc=1 TRACEBACK | rc=2 |
| hostile_ev5.py | ss:catcher.py --host='aaaaaaaaaaaa' | rc=1 TRACEBACK | rc=2 |
| hostile_ev5.py | ss:catcher.py --host='ｌｏｃａｌｈｏｓｔ' | rc=None | rc=2 |
| hostile_ev5.py | ss:catcher.py --host='localhost' | rc=None | rc=None |
| hostile_ev5.py | ss:catcher.py --host='127.0.0.1' | rc=None | rc=None |
| hostile_ev5.py | ss:catcher.py --host='::1' | rc=1 TRACEBACK | rc=2 |
| hostile_ev5.py | ss:fakes_server.py --host='' | rc=2 | rc=2 |
| hostile_ev5.py | ss:fakes_server.py --host='0.0.0.0' | rc=2 | rc=2 |
| hostile_ev5.py | ss:fakes_server.py --host='not a host' | rc=2 | rc=2 |
| hostile_ev5.py | ss:fakes_server.py --host='bad host!' | rc=2 | rc=2 |
| hostile_ev5.py | ss:fakes_server.py --host='256.1.1.1' | rc=2 | rc=2 |
| hostile_ev5.py | ss:fakes_server.py --host='aaaaaaaaaaaa' | rc=2 | rc=2 |
| hostile_ev5.py | ss:fakes_server.py --host='ｌｏｃａｌｈｏｓｔ' | rc=2 | rc=2 |
| hostile_ev5.py | ss:fakes_server.py --host='localhost' | rc=2 | rc=2 |
| hostile_ev5.py | ss:fakes_server.py --host='127.0.0.1' | rc=2 | rc=2 |
| hostile_ev5.py | ss:fakes_server.py --host='::1' | rc=2 | rc=2 |
| hostile_ev5.py | ss:fake_model_server.py no --host (default bind) | rc=None | rc=None |
| hostile_ev5.py | ss:catcher.py no --host (default bind) | rc=None | rc=None |
| hostile_ev5.py | ss:fakes_server.py no --host (default bind) | rc=None | rc=None |
| hostile_ev5.py | burst.py:--url=http://127.0.0.1:1@evil | rc=1 | rc=2 |
| hostile_ev5.py | load_driver:--base-url=http://127.0.0.1:1@evil | rc=TIMEOUT HANG | rc=2 |
| hostile_ev5.py | burst.py:--url=http://0.0.0.0:1 | rc=TIMEOUT | rc=2 |
| hostile_ev5.py | load_driver:--base-url=http://0.0.0.0:1 | rc=TIMEOUT HANG | rc=2 |
| hostile_ev5.py | burst.py:--url=http://evil.example:1 | rc=1 | rc=2 |
| hostile_ev5.py | load_driver:--base-url=http://evil.example:1 | rc=TIMEOUT HANG | rc=2 |
| hostile_ev5.py | burst.py:--url=http://１２７.0.0.1:1 | rc=1 TRACEBACK | rc=2 |
| hostile_ev5.py | load_driver:--base-url=http://１２７.0.0.1:1 | rc=TIMEOUT HANG | rc=2 |
| hostile_ev5.py | burst.py:--url=http://127.0.0.1:0 | rc=TIMEOUT | rc=2 |
| hostile_ev5.py | load_driver:--base-url=http://127.0.0.1:0 | rc=TIMEOUT HANG | rc=2 |
| hostile_ev5.py | burst.py:--url=http://127.0.0.1:65536 | rc=TIMEOUT | rc=2 |
| hostile_ev5.py | load_driver:--base-url=http://127.0.0.1:65536 | rc=TIMEOUT HANG | rc=2 |
| hostile_ev5.py | burst.py:--url=file:///home/user/build/rr6/tm | rc=TIMEOUT | rc=2 |
| hostile_ev5.py | load_driver:--base-url=file:///home/user/build/rr6/tm | rc=TIMEOUT HANG | rc=2 |
| hostile_ev5.py | burst.py:--url=file:///etc/hostname | rc=1 TRACEBACK | rc=2 |
| hostile_ev5.py | load_driver:--base-url=file:///etc/hostname | rc=TIMEOUT HANG | rc=2 |
| hostile_ev5.py | burst.py:--url=ftp://x@x | rc=1 | rc=2 |
| hostile_ev5.py | load_driver:--base-url=ftp://x@x | rc=TIMEOUT HANG | rc=2 |
| hostile_ev5.py | burst.py:--url=http://[::1 | rc=1 TRACEBACK | rc=2 |
| hostile_ev5.py | load_driver:--base-url=http://[::1 | rc=0 | rc=2 |
| hostile_ev5.py | burst.py:--url=http://127.0.0.1:1 | rc=TIMEOUT | rc=TIMEOUT |
| hostile_ev5.py | load_driver:--base-url=http://127.0.0.1:1 | rc=TIMEOUT HANG | rc=TIMEOUT HANG |
| hostile_ev5.py | burst.py:--url=http://localhost:1 | rc=TIMEOUT | rc=TIMEOUT |
| hostile_ev5.py | load_driver:--base-url=http://localhost:1 | rc=TIMEOUT HANG | rc=TIMEOUT HANG |
| hostile_ev5.py | load_driver:--id-prefix=129 chars | rc=TIMEOUT HANG | rc=2 |
| hostile_ev5.py | load_driver:--id-prefix=control chars | rc=TIMEOUT HANG | rc=2 |
| hostile_ev5.py | load_driver:--id-prefix=newline | rc=TIMEOUT HANG | rc=2 |
| hostile_ev5.py | load_driver:--scenario=burst:1_0 | rc=TIMEOUT HANG | rc=2 |
| hostile_ev5.py | load_driver:--scenario=burst:nan | rc=1 TRACEBACK | rc=2 |
| hostile_ev5.py | load_driver:--scenario=burst:inf | rc=1 TRACEBACK | rc=2 |
| hostile_ev5.py | load_driver:--scenario=burst:١ | rc=TIMEOUT HANG | rc=2 |
| hostile_ev5.py | load_driver:dead desk burst:1 (valid url, nothing listening) | rc=TIMEOUT TRACEBACK | rc=TIMEOUT TRACEBACK |
| hostile_ev5.py | load_driver:dead desk burst:20 | rc=TIMEOUT TRACEBACK | rc=TIMEOUT TRACEBACK |
| hostile_ev5.py | ci:control valid small inputs | rc=1 | rc=1 |
| hostile_ev5.py | ci:100,000-row log (real shape) | rc=1 | rc=2 |
| hostile_ev5.py | ci:--requests=300MB-A | rc=2 | rc=2 |
| hostile_ev5.py | ci:--requests=300MB-NUL | rc=2 | rc=2 |
| hostile_ev5.py | ci:--catcher=300MB-A | rc=2 | rc=2 |
| hostile_ev5.py | ci:--catcher=300MB-NUL | rc=2 | rc=2 |
| hostile_ev5.py | ci:--model-log=300MB-A | rc=2 | rc=2 |
| hostile_ev5.py | ci:--model-log=300MB-NUL | rc=2 | rc=2 |
| hostile_ev5.py | ci:--crm=300MB-A | rc=2 | rc=2 |
| hostile_ev5.py | ci:--crm=300MB-NUL | rc=2 | rc=2 |
| hostile_ev5.py | ci:log row ts-abc | rc=1 TRACEBACK | rc=2 |
| hostile_ev5.py | ci:log row attempts-5 | rc=1 TRACEBACK | rc=2 |
| hostile_ev5.py | ci:log row rid-5 | rc=1 | rc=2 |
| hostile_ev5.py | ci:log row sent-nan | rc=1 | rc=2 |
| hostile_ev5.py | ci:--drain abc | rc=1 TRACEBACK | rc=2 |
| hostile_ev5.py | ci:--drain list | rc=1 TRACEBACK | rc=2 |
| hostile_ev5.py | ci:--drain nan | rc=1 | rc=2 |
| hostile_ev5.py | ci:--drain neg | rc=1 | rc=2 |
| hostile_ev5.py | ci:facts intended_requests neg5 | rc=1 | rc=2 |
| hostile_ev5.py | ci:facts intended_requests f1.5 | rc=1 | rc=2 |
| hostile_ev5.py | ci:facts intended_requests true | rc=1 | rc=2 |
| hostile_ev5.py | live_check:--cap-run bad, closed stdin | rc=2 | rc=2 |
| hostile_ev5.py | live_check:--cap-run 1 valid, closed stdin | rc=1 TRACEBACK | rc=6 |
| hostile_ev5.py | live_check:--base-url https://127.0.0.1:99999 | rc=1 TRACEBACK | rc=2 |
| hostile_ev5.py | live_check:key file FIFO | rc=1 TRACEBACK | rc=2 |
| hostile_ev5.py | live_check:ledger FIFO | rc=1 TRACEBACK | rc=2 |
| hostile_ev5.py | live_check:--model 'm=1_0,2' | rc=1 TRACEBACK | rc=2 |
| hostile_ev5.py | live_check:--model 'm=١,2' | rc=1 TRACEBACK | rc=2 |
| hostile_ev5.py | live_check:--max-tokens 0 | rc=2 | rc=2 |
| hostile_ev5.py | live_check:--timeout nan | rc=2 | rc=2 |
| hostile_ev5.py | live_check:--leads 0 | rc=2 | rc=2 |
| hostile_ev5.py | live_check:--leads 1001 | rc=1 TRACEBACK | rc=2 |
| hostile_ev5.py | live_check:--runs 0 | rc=2 | rc=2 |
| hostile_ev5.py | live_check:--runs 101 | rc=1 TRACEBACK | rc=2 |
| hostile_ev5.py | desk_setting:DESK_BIND='xxxxxxxxxxxx' (port) | rc=2 | rc=0 |
| hostile_ev5.py | lead_desk.server:DESK_BIND='xxxxxxxxxxxx' | rc=1 | rc=7 |
| hostile_ev5.py | desk_setting:DESK_BIND='[::1]' (port) | rc=2 | rc=0 |
| hostile_ev5.py | lead_desk.server:DESK_BIND='[::1]' | rc=1 | rc=7 |
| hostile_ev5.py | desk_setting:DESK_BIND='bad host!' (port) | rc=2 | rc=4 |
| hostile_ev5.py | lead_desk.server:DESK_BIND='bad host!' | rc=1 | rc=4 |
| hostile_ev5.py | real_check bad config:DESK_PORT=abc | rc=2 | rc=2 |
| hostile_ev5.py | real_check bad config:DESK_PORT=-1 | rc=2 | rc=2 |
| hostile_ev5.py | real_check bad config:REAL_PERSONS=x | rc=2 | rc=2 |
| hostile_ev5.py | real_check bad config:REAL_PERSONS=-3 | rc=2 | rc=2 |
| hostile_ev5.py | real_check bad config:DESK_SMTPP_HOST=bad host! | rc=2 | rc=2 |
| hostile_ev5.py | real_check bad config:DESK_SMTPP_PORT=abc | rc=2 | rc=2 |
| hostile_ev5.py | real_check bad config:DESK_SMTPP_MAX_SENDS=0 | rc=2 | rc=2 |
| hostile_ev5.py | real_check bad config:DESK_SMTPP_RECIPIENTS=bad | rc=2 | rc=2 |
| hostile_ev5.py | real_check bad config:DESK_HUBSPOT_MAX_CALLS=x | rc=2 | rc=2 |
| hostile_ev5.py | real_check bad config:REAL_IMAP_1_PORT=99999 | rc=2 | rc=2 |
| hostile_ev5.py | real_check bad config:DESK_BIND=bad host! | rc=1 | rc=6 |
| hostile_ev5.py | real_check:--config with unknown keys + binary | rc=2 | rc=2 |
| hostile_ev5.py | real_check:DESK_SMTPP_CA_FILE=empty | rc=1 | rc=2 |
| hostile_ev5.py | desk_setting env DESK_SMTPP_CA_FILE=empty | rc=2 | rc=0 |
| hostile_ev5.py | real_check:DESK_SMTPP_CA_FILE=blank | rc=1 | rc=2 |
| hostile_ev5.py | desk_setting env DESK_SMTPP_CA_FILE=blank | rc=2 | rc=0 |
| hostile_ev5.py | real_check:REAL_IMAP_1_CA_FILE=empty | rc=1 | rc=2 |
| hostile_ev5.py | desk_setting env REAL_IMAP_1_CA_FILE=empty | rc=2 | rc=0 |
| hostile_ev5.py | real_check:REAL_IMAP_1_CA_FILE=blank | rc=1 | rc=2 |
| hostile_ev5.py | desk_setting env REAL_IMAP_1_CA_FILE=blank | rc=2 | rc=0 |
| hostile_ev5.py | n8n_api:no args, no key file | rc=1 | rc=2 |
| hostile_ev5.py | n8n_api:bad command, no key file | rc=1 | rc=2 |
| hostile_ev5.py | n8n_api:import without file, no key file | rc=1 | rc=2 |
| hostile_ev5.py | n8n_api:list, no key file set | rc=1 | rc=4 |
| hostile_ev5.py | n8n_api:list, N8N_URL bad | rc=1 | rc=4 |
| hostile_ev5.py | n8n_api:reply big20mb | rc=0 | rc=0 |
| hostile_ev5.py | n8n_api:reply cutoff | rc=0 | rc=0 |
| hostile_ev5.py | n8n_api:reply ok-small | rc=0 | rc=0 |
| hostile_ev5.py | secret:smtp_password:BOM | rc=0 | rc=0 |
| hostile_ev5.py | secret:smtp_password:two-line | rc=0 | rc=0 |
| hostile_ev5.py | secret:smtp_password:space | rc=0 | rc=0 |
| hostile_ev5.py | secret:smtp_password:control | rc=0 | rc=0 |
| hostile_ev5.py | secret:smtp_password:empty | rc=0 | rc=0 |
| hostile_ev5.py | secret:smtp_password:FIFO | rc=TIMEOUT | rc=0 |
| hostile_ev5.py | secret:smtp_password:100KB | rc=0 | rc=0 |
| hostile_ev5.py | secret:hubspot_key:BOM | rc=0 | rc=0 |
| hostile_ev5.py | secret:hubspot_key:two-line | rc=0 | rc=0 |
| hostile_ev5.py | secret:hubspot_key:space | rc=0 | rc=0 |
| hostile_ev5.py | secret:hubspot_key:control | rc=0 | rc=0 |
| hostile_ev5.py | secret:hubspot_key:empty | rc=0 | rc=0 |
| hostile_ev5.py | secret:hubspot_key:FIFO | rc=TIMEOUT | rc=0 |
| hostile_ev5.py | secret:hubspot_key:100KB | rc=0 | rc=0 |
| hostile_ev5.py | secret:live_key:BOM | rc=0 | rc=0 |
| hostile_ev5.py | secret:live_key:two-line | rc=0 | rc=0 |
| hostile_ev5.py | secret:live_key:space | rc=0 | rc=0 |
| hostile_ev5.py | secret:live_key:control | rc=0 | rc=0 |
| hostile_ev5.py | secret:live_key:empty | rc=0 | rc=0 |
| hostile_ev5.py | secret:live_key:FIFO | rc=TIMEOUT | rc=0 |
| hostile_ev5.py | secret:live_key:100KB | rc=0 | rc=0 |
| hostile_ev5.py | ssl:CERT_NONE context to SmtpProviderOutbox | rc=0 | rc=0 |
| hostile_ev5.py | ssl:check_hostname False context to SmtpProviderOutbox | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:qualify key-file=greek | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:run_live_check key-file=greek | rc=0 TRACEBACK | rc=0 |
| run6.py (hostile_r6.py) | a:hubspot_probe env token=greek | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:n8n_api key-file=greek (unreachable) | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:qualify key-file=fullwidth | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:run_live_check key-file=fullwidth | rc=0 TRACEBACK | rc=0 |
| run6.py (hostile_r6.py) | a:hubspot_probe env token=fullwidth | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:n8n_api key-file=fullwidth (unreachable) | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:qualify key-file=ctl-esc | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:run_live_check key-file=ctl-esc | rc=0 TRACEBACK | rc=0 |
| run6.py (hostile_r6.py) | a:hubspot_probe env token=ctl-esc | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:n8n_api key-file=ctl-esc (unreachable) | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:qualify key-file=ctl-nul | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:run_live_check key-file=ctl-nul | rc=0 TRACEBACK | rc=0 |
| run6.py (hostile_r6.py) | a:hubspot_probe env token=ctl-nul | rc=None | rc=None |
| run6.py (hostile_r6.py) | a:n8n_api key-file=ctl-nul (unreachable) | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:qualify key-file=bom-ok | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:run_live_check key-file=bom-ok | rc=0 TRACEBACK | rc=0 |
| run6.py (hostile_r6.py) | a:hubspot_probe env token=bom-ok | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:n8n_api key-file=bom-ok (unreachable) | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:qualify key-file=tab | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:run_live_check key-file=tab | rc=0 TRACEBACK | rc=0 |
| run6.py (hostile_r6.py) | a:hubspot_probe env token=tab | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:n8n_api key-file=tab (unreachable) | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:qualify key-file=good | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:run_live_check key-file=good | rc=0 TRACEBACK | rc=0 |
| run6.py (hostile_r6.py) | a:hubspot_probe env token=good | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:n8n_api key-file=good (unreachable) | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:run_live_check key-file=fifo | rc=0 TRACEBACK | rc=0 |
| run6.py (hostile_r6.py) | a:qualify key-file=fifo | rc=-9 HANG | rc=0 |
| run6.py (hostile_r6.py) | a:n8n_api key-file=fifo | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:imap user=cr | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:imap user=lf | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:imap user=crlf | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:imap user=esc | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:imap user=nul | rc=None | rc=None |
| run6.py (hostile_r6.py) | a:imap user=tab | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | a:imap user=greek | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | b:smtp context AND ca_file | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | b:smtp ca_file only, WRONG-name cert (control) | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | b:smtp context strict, WRONG-name cert (control) | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | b:smtp context weakened AFTER construction, WRONG-name cert | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | b:imap context strict, WRONG-name cert (control) | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | b:imap context weakened AFTER construction, WRONG-name cert | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | c:n8n_api list key-file=bom-5chars (port closed) | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | c:n8n_api list key-file=5chars (port closed) | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | c:n8n_api list key-file=two-lines (port closed) | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | c:n8n_api list key-file=bom-ok (port closed) | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | c:n8n_api list unreachable port, good key | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | c:n8n_api activate typed name, port closed | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | c:n8n_api activate typed name, n8n answers empty list | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | d:catcher 1 MiB line | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | e:fakes_server Content-Length=huge | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | e:fakes_server Content-Length=neg | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | e:fakes_server Content-Length=nonnum | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | e:fakes_server Content-Length=missing | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | e:fakes_server Content-Length=slow | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | e:fake_model_server Content-Length=huge | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | e:fake_model_server Content-Length=neg | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | e:fake_model_server Content-Length=nonnum | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | e:fake_model_server Content-Length=missing | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | e:fake_model_server Content-Length=slow | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | e:fake_hubspot Content-Length=huge | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | e:fake_hubspot Content-Length=neg | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | e:fake_hubspot Content-Length=nonnum | rc=0 | rc=0 |
| run6.py (hostile_r6.py) | e:fake_hubspot Content-Length=missing | rc=0 TRACEBACK | rc=0 |
| run6.py (hostile_r6.py) | e:fake_hubspot Content-Length=slow | rc=0 | rc=0 |
| run6b g (scripts) | g:start_all.sh, python stand-in exits at once | rc=0 | rc=3 |
| run6b g (scripts) | g:start_all.sh, desk.pid is a FIFO | rc=1 | rc=1 |
| run6b g (scripts) | g:reset.sh, desk.pid is a FIFO | rc=-9 HANG | rc=6 |
| run6b g (scripts) | g:reset.sh, fakes.pid is a FIFO | rc=-9 HANG | rc=6 |
| run6b h (burst url) | h:burst.py --url http://evil.example:1 | rc=1 | rc=2 |
| run6b h (burst url) | h:burst.py --url http://192.0.2.1:1 | rc=1 | rc=2 |
| run6b f | f:100,000-row real-shape log, valid facts | rc=1 | rc=2 |
| run6b f | f:LOAD_TOTAL_MAX short rows (the limit itself) | rc=1 | rc=1 |
| run6b f | f:LOAD_TOTAL_MAX+1 short rows | rc=1 | rc=4 |
| run6b f | f:300 MB file of A as --requests | rc=2 | rc=2 |
| run6b f | f:300 MB file of NUL as --requests | rc=2 | rc=2 |
| run6b f2 | f2:100,000-row log, ~881-byte rows, valid facts | rc=1 | rc=1 |
