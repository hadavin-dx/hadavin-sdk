# F8 results: review round 1 of cap 2 (non-security path), builder F8

Tree: `/home/user/build/rr6/tree-F8` (copy of tree-V2d = base 61ded9e + core-fix-v2.patch). Date 2026-11-13.
Review being answered: `handover/core/review/F8-input-review-r1.md`. Nothing pushed, nothing applied to a real repo, no live
call, no spend, loopback only (`unshare -n` + `lo_up-q4g.py`), no process left running (checked at the end).

## 1. What failed, what is uncertain, what was not checked (read this first)

1. **4 tests of tree-V2d were ALREADY failing before my change** (`tests/test_real_run_v6.py::test_a_book_path_below_a_regular_file_is_refused_before_the_question[direct|sub|deeper]` and
   `::test_a_book_path_below_a_dangling_link_is_refused_and_a_new_folder_is_fine`). Confirmed on the untouched baseline copy
   `out/F8/base`: v2 made `run_real_check` print `refused: DESK_DB_PATH: <the desk's text>` and exit 4 (`EXIT_BOOK_REFUSED`), the
   V6 tests still expected exit 2 and the old text. I updated those 4 tests to the new, intended behaviour (exit 4, the exact
   line). This is a test change, so it needs the reviewer's eye: the V6 author and the v2 author disagreed and I followed v2.
   (The reviewer's m8 said V2/V6 failures were "confirmed fixed by reading"; they were not, for these 4.)
2. **First evidence run `run1.log` had 11 failures** (my own changes to exit codes and the FIFO check, plus those 4). All fixed
   (section 3 lists each). Current run: see section 2.
3. **One allow-list line added to `exceptions.txt`** (the hardcoded-URL scan): the vendor page URL I cite in
   `constants.py` and in one test comment. The line names only those two files and that one URL. This is a repo-guard
   exception, so it is for you to accept or reject.
4. **Side effect I introduced, disclosed:** `scripts/crash_desk.py` now calls `make_book_folder` before printing the flag path
   (it must know the folder is real before it prints a path). The desk makes that same folder next anyway; the only
   difference is that the folder exists a few milliseconds earlier. A refused path creates nothing.
5. **`--config <FIFO>` in `run_real_check`**: `load_env` now refuses it (PathRefused). Through the command line the terminal
   check refuses earlier (stdin not a terminal), so I could not show the new line from the shell; the claim that `main` prints
   `refused: --config: ...` is from reading `main` (`except ValueError`), and the test goes through `load_env`.
6. **Probe I could not explain, not claimed:** setting `DESK_FAKES_HOST`/`DESK_FAKES_PORT` for `demo_only.fakes_server` did not
   produce a refusal, the server simply bound. I did not find out whether that script reads those names at all. No claim made
   about it; the `--port` option of that script IS covered (it refuses). Next step: the owner or a reviewer says whether the
   script should read those settings.
7. **Not checked:** Windows (`.ps1`, ntpath, `O_NONBLOCK` fallback), macOS, Python 3.13, gitleaks (4 hygiene scans skip, no program
   on PATH), mutation runs, the rest of `tests/` beyond the evidence set below, a run as a non-root user (root-only skip: 1),
   and `hypothesis` is not installed so the "property" tests use a seeded `random.Random` (fixed seeds, fixed seeds 8 and 81, 200 to 3000 cases). The vendor effort list (m4) was checked against the vendor page only (no live call).
8. No finding was deferred as a "limitation". One item is OWNER-ONLY (exit codes of `scripts/n8n_api.py`): it exits 1 for every
   refusal; it was not in the F8 findings, section 5 says why I did not change it.

## 2. Evidence (commands and outputs)

Recipe: `TMPDIR=<out/F8/tmp> PYTHONPATH=<tree>/src PYTHONDONTWRITEBYTECODE=1 venv-br/bin/python -m pytest -q -p no:cacheprovider -rfs <files>`
under `unshare -n python lo_up-q4g.py bash run.sh ...`. First printed line of each log is `lead_desk.__file__` =
`/home/user/build/rr6/tree-F8/src/lead_desk/__init__.py` (the tree under test, not an installed copy).

| Run | Log | Result |
|---|---|---|
| first full set (before the fixes below) | `run1.log` | 11 failed (listed in section 3) |
| new file alone, final code | `new2.log` | `118 passed in 5.91s`, rc=0 |
| same new file against the OLD code (base 61ded9e+v2 plus a 2-line stub so it imports) | `old.log` | `103 failed, 15 passed in 366.03s`, rc=1 (failing-before, section 4) |
| full evidence set, before the line-length/format edits | `full.log` | `2220 passed, 6 skipped in 746.40s (0:12:26)`, rc=0 |
| full evidence set on the FINAL head | `full2.log` | `2220 passed, 6 skipped in 801.47s (0:13:21)`, rc=0 |
| `ruff check .` | | `All checks passed!` |
| `ruff format --check .` | | `178 files already formatted` |
| `bandit -ll -r src tools scripts` | | 0 medium, 0 high (9 low, all high-confidence, below the `-ll` line) |

The evidence set = the 25 changed test files of the v2 diff (`set.txt`: includes `test_book_folder_refusals`,
`test_lead_step_route`, `test_reset_scripts`, `test_clock_steps`) + `test_f8_input_classes` (new) + `test_hygiene`,
`test_load_tools`, `test_bind_refusals`, `test_http`, `test_portal_demo`, `test_crash_points`, `test_mode_safety`.
Skips (6): 4 gitleaks hygiene scans, 1 `ntpath.isreserved` (needs Python 3.13), 1 "root can read a file with no permissions".

## 3. The 11 failures of run1.log and what I did

| Failure | Cause | Fix |
|---|---|---|
| feed/reset bad `DESK_PORT` expected 2 (3 cases + reset case) | my m1 change (4 on purpose) | tests now expect 4 |
| `test_run_real_check_config_that_is_a_pipe...` | `confine_anywhere` now refuses a pipe (PathRefused) | test accepts PathRefused (a ValueError) |
| 4 x V6 book-path | pre-existing (section 1, item 1) | tests updated to the v2 behaviour |
| scrub: unencodable character left a half file | `open_output("w")` creates the file before the write fails | text is encoded BEFORE the file opens |
| `test_hygiene_scan_public` | URL in `constants.py` comment | narrow `exceptions.txt` line (section 1, item 3) |
| (new file) crash script printed `/proc/canary-dir/...` | `book_problem` accepts a path whose folder cannot be made | `crash_desk` also runs `make_book_folder` before printing |

## 4. Per finding: class, choke point, siblings, failing-before

Failing-before = the test fails on the OLD code (`old.log`; one line per test in `failing-before.txt`). The 15 tests that
pass on the old code are the "valid input still works" cases (valid ports, valid scenario forms, the cap edge value, the
SCRIPTS tie-in m5) kept to prove the new check does not refuse good input; I did not list them one by one.

### M1 Class A: traceback on a typed port, host or a port in use (and class B: no typed text)
- Choke point: `tools/refusing_args.py`: `port_arg` (argparse type: `[0-9]{1,5}`, 0..65535, ASCII digits only, fixed text) and
  `refuse_listen` with `LISTEN_ERRORS = (OSError, ValueError, OverflowError)`; ONE refusal line `refused: --host/--port: cannot
  listen there ...` (no host, no port), exit 2. `TCP_PORT_MAX` is pinned to `lead_desk.constants.PORT_MAX` by a test.
- Sibling sweep (every bind or listen site found by grep of `start_server|HTTPServer|.bind(|make_server|serve_forever`):

| Site | Result |
|---|---|
| `load_tools/catcher.py` (`asyncio.start_server`, `--port`, `--host`) | FIXED (probe: bad port rc 2, unknown host rc 2, port in use rc 2) |
| `demo_only/fake_model_server.py` (`--port`) | FIXED |
| `demo_only/fakes_server.py` (`--port`) | FIXED |
| `src/lead_desk/server.py` (`make_server`) | not needed: already exit 4/5 with plain lines (`EXIT_SETTING_REFUSED`, `EXIT_PORT_UNAVAILABLE`), covered by `test_bind_refusals` |
| `demo_only/fake_hubspot.py`, `fake_smtp_tls.py`, `fake_imap.py` (bind) | not needed: library classes used by tests and `run_real_check`, no command line, ports come from code (`127.0.0.1`, port 0); no typed value reaches them |
| `scripts/run_real_check.py:291` (`s.bind(("127.0.0.1", 0))`) | not needed: fixed loopback, port 0, no typed value |
| `load_tools/load_driver.py` (client only, no listener) | not applicable |
| every script that has a `--port` option | a test sweeps all listening scripts and asserts `type=port_arg` |

- Tests: `test_a_bad_port_is_one_refusal_line_with_exit_2` (12 cases), `test_the_catcher_refuses_an_unknown_host_and_a_taken_port`,
  `test_every_port_option_of_a_listening_script_takes_the_shared_port_type`, `test_port_arg_accepts_every_port_and_refuses_everything_else` (property,
  seeded). Old code: all four FAIL (old.log).

### M2 Class A + E: `parse_scenario` (nan, inf, 1e400, full-width digits, no size cap)
- Choke point: `load_tools/load_driver.parse_scenario`: ASCII-only number regex, then `float`, `math.isfinite`, positive, then a cap
  `MAX_SCHEDULE_REQUESTS = 100_000` on the number of requests (`rate:R:D` is R x D, `burst:N` is N). The cap is about 887 bytes of
  memory per request (measured with tracemalloc) = ~89 MB at the cap, and ten times the 10,000-request load in `docs/limits.md`.
  Three fixed refusal texts, exit 2.
- Siblings: `demo_only/burst.py` takes counts as `int` options through `RefusingParser` (no float parsing; not needed). No other
  `float(` of typed text found in `load_tools/`.
- Tests: 21 parametrised bad scenarios, the cap edge (100,000 accepted, 100,001 refused), a seeded generator of 3000 scenarios (seed 81) (every
  result is finite and inside the cap, or one of the three texts), and the driver with `burst:1e18` ends exit 2 at once. Old code: FAIL.

### M3 Class C: readers that block on a FIFO / device
- Choke points: (1) `tools/pathconfine.confine_existing` and `confine_anywhere` now refuse a last element that is not a regular
  file (`_step(read=True)`); (2) the shared helpers `lead_desk.regfile` (`read_regular_text`, `load_json_file`, `open_regular`, with
  `O_NONBLOCK|O_NOCTTY`, kind checked on the open handle); new `ca_context_from_file` for TLS CA files (`ssl` is given the text, never a path).
- Every read site found by `grep -rnE "read_text\(|read_bytes\(|open\(|\.read\(\)|write_text\(|write_bytes\("` over `src scripts tools load_tools demo_only`:

| Site | Result |
|---|---|
| `src/lead_desk/smtp_provider.py` CA file | FIXED (`ca_context_from_file`) |
| `scripts/run_real_check.py` `_ca_context` and `load_env` | FIXED (`ca_context_from_file`; `load_env` via `confine_anywhere`) |
| `load_tools/check_invariants.py` `--requests/--facts/--catcher/--crm/--model-log` (`read_jsonl`, `read_crm`, `_intended`, `_facts_say_live`, `_drain_marker`) | FIXED (shared readers, input cap 256 MiB) |
| `demo_only/fake_model_server.py` control file (each call) and `--key-file` | FIXED (`read_regular_text`, key file capped at 4096 bytes) |
| `load_tools/catcher.py` `read_mode` | FIXED |
| `demo_only/portal_demo.py` armed flag | FIXED (`read_regular_text`, cap) |
| `demo_only/fakes.py` `RecordedQualifier` replies | FIXED (`load_json_file`) |
| `src/lead_desk/hooks.py`, `trace.py` | FIXED (M4) |
| `tools/hygiene.py` `read_lines`, `load_term_list`, `scan_repo` | FIXED (shared readers, 64 MiB per scanned file) |
| `tools/scrub_n8n_export.py` read | already `load_json_file`; write fixed (m3) |
| `src/lead_desk/live_claude.py` ledger and key file | not needed: already `open_regular` (line 241, 426) |
| `src/lead_desk/portal_api.py:89` static files | not needed: filtered by `p.is_file()` (a pipe is not), not a link, size capped, folder is the package's own |
| `demo_only/portal_demo.py:204-205` assets and canned leads | not needed: files of the repository's own `demo_only` folder, `is_file()` guard on assets; canned file name is a constant |
| `src/lead_desk/db.py:122` schema, `scripts/check_schema.py:70` | not needed: package resource / repository constant, not a typed path |
| `load_tools/load_driver.py` `/proc/meminfo` and cgroup reads (lines ~328-349) | not needed: kernel files, constant names |
| `load_tools/load_driver.py:292,402` own part files | not needed: made by the driver itself through `confine`, which now refuses non-regular files |
| `scripts/feed.py:84,86`, `n8n_api.py:137,148`, `run_real_check.py:1040`, `load_driver.py:106-111`, `*_OPENER.open` | not needed: HTTP responses, not files |
| writes: `run_real_check.py:212,213,886,1326`, `check_invariants.py:752`, `load_driver.py:396,407`, `catcher.py:94` | not needed for M3 (writes to files the tool itself names under `confine`, which refuses non-regular files); not probed with a FIFO each |

- Tests: `test_every_reader_refuses_a_pipe_at_once` (13 reader snippets, each run in a child process with a 20 s limit so a hang is
  a failure, not a stuck suite), `test_confine_existing_and_anywhere_refuse_a_pipe_and_confine_still_names_a_new_file`, and a test that walks every input
  option of the checker command line. Old code: FAIL (13 of 13 readers hang or accept).

### M4 Class A: non-UTF-8 flag file and unbounded reads in `hooks.py` / `trace.py` / `--key-file`
- Choke point: `FlagFileHooks.crash_point` and `CrashWindows.hit` read through `read_regular_text` (1 MiB cap, UTF-8 checked) and
  treat `(OSError, ValueError)` as "no flag" (quiet). `fake_model_server --key-file` reads with the 4096-byte cap.
- Siblings: the other crash-flag reader `portal_demo._armed` (fixed, above).
- Tests: 5 contents (UTF-16 BOM, UTF-16 text, a lone continuation byte, a file one byte over 1 MiB, a surrogate) for the hooks (4 failed on the old code), plus tests for the crash windows, the key file, the control file and the checker log. Old code: FAIL.

### m1 Same exit code for the same cause (bad DESK_* setting)
- `scripts/feed.py` and `scripts/reset_check.py` now exit 4 (`EXIT_DESK_SETTING_REFUSED`), like the desk, `crash_desk.py`, `desk_setting.py`.
  Docstrings, `docs/settings.md` and the existing tests updated. One table of every behaviour change of the whole v2 diff plus
  mine: `out/F8/BEHAVIOUR-CHANGES.md` (30 rows; rows marked "read" were not measured).
- Test: `test_a_bad_desk_setting_gives_exit_4_in_every_script` (4 scripts). Old code: FAIL.

### m2 Class E: format characters and plain-host check
- `envnum.split_url` now refuses the categories Cc, Cf, Zs, Zl, Zp anywhere in the text, and a non-ASCII host name. The three URL
  settings (`DESK_HUBSPOT_BASE_URL`, `DESK_LIVE_BASE_URL`, `DESK_FAKES_URL`) go through the same plain-host check.
- Tests: 32 format characters (zero-width, bidi override, BOM, ...) x `split_url`, 4 non-ASCII hosts, one test per URL setting. Old code: FAIL.

### m3 `scrub_n8n_export` write path and `O_NOCTTY`
- Output goes through `open_output` (kind checked on the open handle; text encoded first, so no half file); `O_NOCTTY` added to
  the common flags of `open_regular` and `open_output`. Tests pin both, and that the script has no direct write left. Old code: FAIL.

### m4 `LIVE_EFFORTS` against the vendor page
- Verified 2026-11-13 at https://platform.claude.com/docs/en/build-with-claude/effort : the levels are low, medium, high, xhigh, max.
  Opus 5.5, Sonnet 5.5 and Haiku 5.5 take all five; not every model does (Sonnet 4.6 has no xhigh), so the list is the union the
  desk allows and the model's own answer decides at the call. The comment in `constants.py` cites the URL, the date and the 90-day
  re-check. `DESK_LIVE_EFFORT` is now refused unless it is in `LIVE_EFFORTS` (`DESK_LIVE_EFFORT must be one of: low, medium, high, xhigh, max`),
  and the check script uses the same list (test ties the two). Old code: FAIL (any text was accepted).

### m5 `fake_smtp_tls.SCRIPTS` vs the code
- A test reads `fake_smtp_tls.py`, extracts every `self.script == "<name>"` use and asserts `SCRIPTS` equals the used names plus the default, with no duplicates.
  Passes on the old code too (it pins what was right).

### m6 `hubspot_probe.py` claim
- The comment now reads: it imports nothing from the desk (`lead_desk`) but needs `tools/refusing_args.py` of this repository, so it runs from a
  checkout and cannot be copied alone. A test pins the wording and the real import. Old code: FAIL.

### m7 `crash_desk.py` printed the typed path
- It prints the flag-file line only when `book_problem` is None and `make_book_folder` is None. Tests: `/dev/null/canary-x.db` and
  `/proc/canary-dir/x.db` give exit 4 and no word `canary` in stdout or stderr. Old code: FAIL.

## 5. Open items

- OWNER-ONLY: `scripts/n8n_api.py` exits 1 for every refusal (and 0/1 for HTTP results). Not in the F8 findings; changing it means
  changing its docs and tests; I left it. Next step: the owner decides whether it should join the 2/4 scheme.
- Item 6 of section 1 (`fakes_server` and the `DESK_FAKES_*` names): needs a look by a reviewer.

## 6. Files

Patch: `out/F8/f8-on-v2.patch`; `out/F8/BEHAVIOUR-CHANGES.md`; logs `run1.log new2.log old.log full.log full2.log`;
`failing-before.txt`; `checkpoint.md`.
