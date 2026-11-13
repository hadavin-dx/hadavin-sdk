# R6 whole-patch review (FALLBACK general-purpose reviewer a6ebd11d; condensed by core lead)
Could not check: end-to-end run of run_real_check with a control char in REAL_IMAP_1_USER (command DENIED, not retried; F1 proved at function level); no mutation of weak tests (none run); suppressions only partly; docs numbers (81 planted shapes) not counted; console_scripts not separately enumerated; entry-point runs under unshare -n with stdin /dev/null so success paths needing a desk were not run.
Verdict: NOT CLEAN. 4 Majors (F1-F4), Minors, Nits. Lead verified by reading code: F1 (ImapCountError is a RuntimeError, scripts/run_real_check.py:1007 catches only ValueError/OSError/ArithmeticError) and F3 (start_all.sh polls only a TCP connect at line 51).
| id | sev | where | finding | fix |
|---|---|---|---|---|
| F1 | Major | imap_count.py ImapSettings.__post_init__; run_real_check.py ~1007 | control char in REAL_IMAP_n_USER raises ImapCountError (RuntimeError): traceback | raise a ValueError subclass or catch it with one line, exit 2; test via main |
| F2 | Major | demo_only/fake_hubspot.py | bad bodies/queries (`{}`, `[]`, non-JSON, `{"properties":[]}`, search `[]`, no filterGroups, ?limit=abc, ?after=abc) give server traceback and no reply | catch (KeyError, TypeError, ValueError, AttributeError) in dispatcher, 400 fixed line; test per shape |
| F3 | Major | scripts/start_all.sh | false "started" rc 0 when another listener holds the port (poll is TCP only; desk bind retry 5 s > 3 s window) | poll desk /counts over HTTP while kill -0 holds, exit 3 and stop fakes if it dies |
| F4 | Major | scripts/n8n_api.py (~11 SystemExit("text")) | setting/path refusals rc 1 (spec: 2 or 4) | map to 4 / 2 via constants; docs |
| F5a | Minor | load_tools/check_invariants.py:91 | local exit constants; bad path gives 2 not 4 | shared constants |
| F5b | Minor | check_invariants read_jsonl | model-log cap = LOAD_TOTAL_MAX but 3 model calls per lead | own cap 3 x LOAD_TOTAL_MAX |
| F5c | Nit | same | BOM refused; lone CR no longer a line break | state rule or strip BOM |
| F6 | Minor | load_tools/load_driver.py:412,496 | /proc/net/tcp and part files read whole (256 MiB) | stream |
| F7 | Minor | demo_only/portal_demo.py _fetch_json/_post_once | /fake/crm over 1 MiB (~5,890 rows) -> None "unreachable"; _post_once truncates silently | use script cap, read cap+1 |
| F8 | Nit | scripts/http_guard.py announced_length | leading zeros 413, duplicate Content-Length first value, HEAD 501 | strip zeros |
| F9 | Minor | tests/test_file_call_guard.py | ~17 of ~50 new shapes missed (sys.stdin reads, os.read, input(), requests.get, os.stat, getsize, ...); docstring claims a bare .read() check that does not exist | add shapes + check or delete claim |
| F10 | Minor | tests/test_r6_refusals.py class-name guard | only print(__name__) in scripts/*.py, demo_only/*.py (not load_tools, tools, src, not logging/write/SystemExit/repr/type) | walk all .py, flag all forms |
| F11 | Minor | docs | settings.md:136 n8n exits "1 or 2" (code uses 3); load_tools/README.md:98 omits 4; limits.md:113 meaning of 1/3; "81 planted shapes" uncounted; CHANGELOG points to RESULTS.md | fix |
| F12 | Nit | tls_trust.py | cert_store_stats guard removal safe (10 shapes refused by ssl) | docstring |
| F13 | Nit | regfile.read_secret_line(spaced) | drops all whitespace incl. \x0b..; hubspot_probe env token no max length | drop ASCII space only; cap |
| F14 | Nit | scripts/reset_check.py | DESK_DB_PATH FIFO exits 0 silently (desk gives 4) | same path check |
| S1 | Minor | suppressions | partial | grep before merge |
Weak tests (read-only, no mutation run): duplicate-name constants test (ast), start poll constants sign only, exit-code pair pin does not prove scripts use them, class-name guard, context-weakened test calls helper not send/_wrap, bounded secret read test not shown to fail, request-body tests use BytesIO not a socket, start_all stub test lacks foreign-listener case.
Entry point table (17 scripts x 3 bad args, unshare -n, timeout 5): no traceback, no class name, no hang, no echo in any row; rc 2 for nearly all; n8n_api rc 1 (F4); check_invariants 2 (F5a); reset_check FIFO rc 0 (F14); crash_desk 2 lines.
