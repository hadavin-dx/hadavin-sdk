# R5 whole-patch review (FALLBACK general-purpose reviewer a31190d2; condensed by core lead)
Reviewer could not check: realistic 100,000-row check_invariants run; CHANGELOG/docs sentence-by-sentence; class names in check_schema.py:46/85, run_real_check.py:565, run_live_check.py:115; closed-stdin prompt probe was denied by the permission classifier and never ran; no pytest run; scratch deleted so "how proved" is in words only (re-confirm each row with one command).
Verdict: NOT CLEAN. 0 Blockers, 7 Majors, 4 Minors, 2 Nits.
Lead verified by reading tree-R5 (grep): #2 (duplicate REPLY_MAX_BYTES at constants.py:272 and :504), #3 (type(e).__name__ in n8n_api.py:147,177,178), #5 (type(e.reason).__name__ in demo_only/burst.py:119,121 and portal_demo.py:522,525), #10 (EXIT_UNREACHABLE and EXIT_CHECK_FAILED both 3; EXIT_STOPPED and EXIT_ADAPTERS_UNREACHABLE both 1). Others not yet re-checked by me.
| id | sev | where | finding | fix |
|---|---|---|---|---|
| 1 | Major | tests/test_file_call_guard.py | closed name lists; ~35 of 49 planted shapes not caught | deny-by-default guard resolving aliases/getattr; test plants all shapes |
| 2 | Major | constants.py:272,504 | REPLY_MAX_BYTES defined twice (1 MiB then 4 MiB, later wins) | one definition, ast duplicate-name test, docs |
| 3 | Major | scripts/n8n_api.py:147,176-178 | class name shown; exit 1 not 3; activate echoes typed name | fixed line, exit 3, no typed args |
| 4 | Minor | server.py:1146-1150, lockfile.py:78 | lock-file line shows class name | fixed line |
| 5 | Major | demo_only/burst.py:112-121, portal_demo.py:519-525 | class name as status word; burst --url not loopback-only | fixed word; loopback_host() |
| 6 | Major | load_tools/catcher.py handle | over-limit line raises ValueError traceback; UNPARSEABLE line prints class name | catch ValueError, fixed line, test |
| 7 | Major | demo_only/fakes_server.py:71-72, fake_model_server.py:150-151 | Content-Length unbounded, no timeout (fake_hubspot has MAX_BODY_BYTES) | shared helper in http_guard.py |
| 8 | Minor | scripts/start_all.sh | does not check the desk survived start | bounded health poll, exit 3 |
| 9 | Major | load_tools/check_invariants.py:139-160 | no row cap, 256 MiB of short rows -> several GB | stream, row cap, exit 4 |
| 10 | Minor | constants.py | two exit-code pairs share a number | separate or document |
| 11 | Nit | check_schema.py:46/85, run_real_check.py:565, run_live_check.py:115 | suspects, unverified | grep and route |
| 12 | Minor | tests | several assert only rc!=0 / no "Traceback" | assert exact rc, one line, no canary |
| 13 | Nit | docs | 4 MiB reply cap and shared exit codes undocumented | docs/changelog |
Solid (probed): desk HTTP server bad input; desk_setting.py; fake_model_server path options; run_real_check/run_live_check/hubspot_probe args (closed-stdin case unchecked); scrub_n8n_export; n8n JSON loopback only; no regression on valid loopback URLs/localhost/CA/Windows paths.
