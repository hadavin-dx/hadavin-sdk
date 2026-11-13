# Independent review (FALLBACK, persona codebase_details), round 1 of cap 2, diff core-fix-v2.patch (sha256 df03b49f...)
Reviewer read only the diff, EVIDENCE-V2.md, EVIDENCE-V6.md; probes on a copy under `unshare -n`, 10 s limit. Not checked: Windows run, macOS, full suite, mutation, gitleaks, Python 3.13. VC full-suite result was not available.
Blockers: none that break the diff's own claims; the classes are not closed at their choke points (Majors below).

## Major
M1 Class A, traceback: port out of range / in use / unresolvable host.
- `python -m load_tools.catcher --out F --port 70000` -> OverflowError, rc 1; `--host canary.invalid --port 1` -> socket.gaierror, rc 1; a second catcher on a taken port -> OSError 98 traceback.
- `python -m demo_only.fake_model_server --port 99999` -> OverflowError; `demo_only.fakes_server --outbox keyed --port 99999` and `--port -1` -> OverflowError.
- Where: load_tools/catcher.py main/serve (~183-199), demo_only/fake_model_server.py main (~244-262), demo_only/fakes_server.py main (~238).
M2 Class A in load_driver.parse_scenario: `burst:nan` -> ValueError (build_schedule, load_driver.py:237); `burst:inf`, `burst:1e400`, `rate:inf:1`, `rate:1:nan` -> OverflowError/ValueError; `burst:1e18` never finishes (rc 124, no upper bound); full-width digits `burst:１０` accepted by float() (class E). Cause: `any(x <= 0 ...)` is False for nan; inf accepted. Fix: math.isfinite + cap in parse_scenario + ASCII digits. No test covers it.
M3 Class C, readers that block on a FIFO (each hangs, rc 124, reproduced unless noted):
- src/lead_desk/smtp_provider.py:211 `ssl.create_default_context(cafile=...)` with DESK_SMTPP_CA_FILE = FIFO (`_context_from_file` catches OSError/ValueError but never checks the file kind);
- scripts/run_real_check.py:663 `_ca_context`;
- load_tools/check_invariants.py `--requests FIFO`, `--facts FIFO` (read_text at L85, L108, L636, L648, L661; `confine_existing` / `_locate_existing` has no kind check; --catcher/--crm/--model-log same code, not confirmed);
- demo_only/fake_model_server.py:77 `control_file.read_text` on every call; load_tools/catcher.py:54 `read_mode`;
- demo_only/portal_demo.py:311 raw `open(hooks.flag_path, "rb")` (by reading); load_tools/load_driver.py:315, 327, 389 and tools/hygiene.py plain read_text (not probed).
Suggest: make `confine_existing` or a shared read helper refuse non-regular files; route all through read_regular_text / load_json_file.
M4 Class A: src/lead_desk/hooks.py:41 (`FlagFileHooks.crash_point`) catches OSError only, `f.read().decode("utf-8")` raises UnicodeDecodeError on a flag file of bytes ff fe -> traceback rc 1, inside the request path; src/lead_desk/trace.py:131-136 (`CrashWindows.hit`) same. Reads in hooks, trace and fake_model_server `--key-file` (`kf.read()`) are unbounded.

## Minor
m1 exit codes differ for the same cause (bad DESK_* setting): desk_setting/crash_desk/server.main 4; scripts/feed.py 2 (`DESK_PORT=canary`), scripts/reset_check.py 2; README says reset exit 4 means two things; n8n_api.py exits 1 for every refusal (not changed by the diff). Behaviour changes are not listed in one place.
m2 Class E: split_url (envnum.py) refuses Cc/Zs/Zl/Zp but not Cf (zero-width, bidi override, BOM accepted); _plain_host_text covers only DESK_BIND/DESK_FAKES_HOST, not DESK_HUBSPOT_BASE_URL, DESK_LIVE_BASE_URL, DESK_FAKES_URL.
m3 tools/scrub_n8n_export.py:209 `dst_path.write_bytes` after confine() (TOCTOU, helper not used); open_output lacks O_NOCTTY.
m4 constants.py LIVE_EFFORTS comment says "NOT checked against the vendor's page"; DESK_LIVE_EFFORT still accepts anything; fix-dont-defer says verify or classify.
m5 demo_only/fake_smtp_tls.py SCRIPTS list is not tied to the code by a test.
m6 scripts/hubspot_probe.py is documented as importing nothing from the desk, now imports tools.refusing_args; copied alone it dies with ModuleNotFoundError.
m7 scripts/crash_desk.py prints `crash flag file: <typed path>` before a refusal (DESK_DB_PATH=/dev/null/x.db).
m8 V2 and V6 failures confirmed fixed in the diff by reading (marker present; test_lead_step_route changed).

## Checked and found fine
Class G fixed (exit 4, one line, no typed text) for /dev/null/x.db, /proc/canary/x.db, FIFO; Class B: no argparse.ArgumentParser( outside tools/refusing_args.py, probes print fixed text only; feed.py unreachable desk exit 3, bad --index exit 2, newline in DESK_BIND exit 2; open_regular/open_output check the kind on the open handle; n8n_api list with FIFO key file refused; start_all.sh/reset.sh `set -eu` makes the subshell exit stop the script; tests/test_hygiene.py 20 passed 4 skipped; the 3+ changed existing tests are not weakened beyond what is stated (test_n8n_api_url exception-name check is the only weaker one; refusal assertion stands); Windows by reading: O_NONBLOCK falls back to 0, ps1 catch exit 4 fine.
