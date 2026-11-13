# rv15: fresh review of sonar-p2-regex-http-bug-v2 (+ regex-optional, feed-optional), base db54e13
Reviewer: fresh, shell, no pushes. Scratch /tmp/work/rv15-1 (clone, trees main/ and all/, scripts s/). Preamble rules used: 5,6,7,8,12,19,20 (bible not readable; no R-numbers beyond the preamble text). Sonar not run; all Sonar odds are judgement. EGM not run (I am the reviewer).

## Failures / findings first
No Blocker. No Major.
- Nit 1 (test gap, measured): mutant "flag = True whenever rc==1 and state=='sent', ignoring what _mark_contacted returned" SURVIVES the builder's tests and all 166 tests of 8 affected files. Effect: copy wait freed although the stage did not move (lead already further, or no step file). My test (tests/zz_rv15_flows.py::test_f8, scratch only, not in the repo) kills it. Suggest adding it to test_sonar_p2_choke_points.py.
- Nit 2: `_finish_update` now wraps the attempt in a lambda, so for every caller (mirror, mirror_failed, record_nudge_result, give_back_nudge) `fn.__qualname__` seen by `_locked_retry` is `Desk._finish_update.<locals>.<lambda>`, not the caller's inner function. tests/support.py::is_write selects faults by qualname; today it only names "store" and "_touch" (not _finish_update callers), so nothing breaks, but a future test using is_write(fn, "copied") would silently never fire. Undocumented in NOTES.
- Nit 3: `lead_desk.urls.DESK_SCHEME` duplicates `demo_only/portal_demo.py:77 DESK_SCHEME` (demo_only is Sonar-excluded; harmless).
- Nit 4: new `_Server(_ExclusiveBind, ThreadingHTTPServer)`: Sonar's ClearTextProtocolsCheck (I read master, ct.java) checks any class whose bases include ThreadingHTTPServer for `super().server_bind/serve_forever`; there are none left in _Server (grep). Could not check the analyzer version SonarCloud runs.
- Not done: Sonar, CodeQL, CodeRabbit, real Windows, full suite, EGM. Win32 bind path only via faked platform + mypy win32.

## Apply matrix (git apply --check + apply, fresh clone db54e13)
OK: main alone; main+P1v2+P3 in orders M P1 P3 / P1 M P3 / P3 P1 M / P3 M P1 / P1 P3 M(+R+F); main+R; main+F; main+R+F; main+F+R; P1 M R P3 F; P3 P1 M F R; M P1 P3 F R; R before M (ok, regex-optional is independent of main). Fail by design: F before M, M twice.
Gates (ruff check, ruff format --check, mypy linux, mypy --platform win32, bandit -ll): clean on main alone (148 files / 27 mypy files) and on all five applied (152 / 28); bandit shows only comment-parse warnings, no issues.

## Regex equivalence (my own corpus, scripts s/corpus.py; old patterns read via git show db54e13:)
Four patterns: PLAIN_ADDRESS, _EMAIL_RE (fullmatch), run_real_check._ADDRESS, scrub MAIL (match spans AND .sub output). 3,110,382 texts x 4 patterns: 0 differences. Corpus: exhaustive all strings up to length 8 over {a @ . space newline}; up to 8 over 12 punctuation symbols (@ . , ; : < > " ' ( )); up to 6 over a 14-symbol set incl. full-width @, é, Arabic digit, NBSP, NUL, U+2028, CR, %, +, _; up to 6 over 12 domain tokens (example, .com, test, invalid, ＠...); plus 1.5M random 0-18 token strings from 38 tokens. Timing (ms, new; old in brackets, N=2000 and 20000): addresses/plain/email worst shapes 0.0-0.1 at 2k (old 13-54 ms at 2k-4k, 2143 ms for _ADDRESS "a"*20000, new 0.6); at 200k-1M chars new 4-21 ms. MAIL old is not slow on any shape (as the builder says); new not slower.
Python floor: possessive quantifiers need 3.11; repo requires >=3.12 (pyproject, CI 3.12). OK.

## _ExclusiveBind (measured, s/bind.py, old vs new tree)
MRO: _Server, _ExclusiveBind, ThreadingHTTPServer, ThreadingMixIn, HTTPServer, TCPServer. Real Linux behaviour identical old/new: second listener on a listening port -> EADDRINUSE (98); serve + request OK; shutdown()+server_close() then immediate rebind of the same port OK (SO_REUSEADDR). server_name/port set (HTTPServer.server_bind still runs). Faked win32: builder's test records setsockopt before bind; passes. No Linux behaviour change.

## desk.py refactor line by line
- attempt returns (rc, flag) inside `with self._write`; the return is evaluated before COMMIT, but an exception from COMMIT replaces the return, so the flag of a try that failed to commit never reaches the caller. Expression is bool on every path (rc!=1 -> False; state!='sent' -> False).
- `_finish_update_moved`: unpack, busy -> log same text -> return False; non-busy re-raised; changed!=1 warning same; returns flag. `_finish_update` = delegate with False; same logs; other callers' return value unchanged (they ignore it).
- Caller: `if self._finish_update_moved(...)`: clear slot. Same as old `if moved`.
Behaviour change (locked DB after an uncommitted stage move): CORRECT. Old: try 1 ran the UPDATE (flag set), COMMIT busy -> rolled back; later tries busy before reaching `moved.clear()`; old freed the copy wait though nothing was recorded. New keeps it. Consequences checked: row stays `sending` and stage `new` in both old and new (identical, tested); the wait is monotonic-time bounded and entries are dropped when expired and ignored at another stage rank (_MirrorWait), so the copy cannot get stuck (my f1: waiting(now+10000)==[]); a later retry with the same token records, moves stage, frees the wait (f1). No send is lost or duplicated by this change: it touches only the in-memory copy wait, not followup state or the outbox. Same philosophy as the existing mirror_failed comment ("the write stayed locked: the first wait still applies").
My 10 flow tests (s/zz_rv15_flows.py): locked throughout; commit fails once then succeeds (moves, frees, state sent, 2 tries); non-busy IntegrityError propagates, wait kept; _GateBusy swallowed; unknown/pending/failed never move (3); same token twice no-op; no step file; stage already further (f8). All pass on new code; all but p2's own s-4 test also pass on the OLD desk.py (confirms the only behavioural difference is the stated one; s-4 fails on old, passes on new).
Mutants (15, in a copy, run against 8 test files incl. the builder's new ones + mine): killed 14. M1 drop rc==1, M2 drop state=='sent', M4 never moved, M5 moved when rc==1 regardless of state, M6 busy swallow returns True (old behaviour), M7 swapped unpack, M8 inverted if, M9 no slot clear, M10 mark_contacted run before rc check, M11 flag carried across tries, M12 True if changed==1, M13 _finish_update drops attempt result, M14 clear wrong key, M15 failed results also move: all killed by the builder's tests. M3 (ignore _mark_contacted result) survived the builder's suite, killed only by my f8 (Nit 1).

## Tests run (affected files only)
main alone: 24 files (choke_points, bind_refusals, ledger_and_bind_retry, server_stop_guard/hardening/main_reaper, mirror_gate, lead_crm_copy, followup_edge_cases, claim_checks, desk_http_edge_cases, http, lead_step_route, mutation_guards, real_check_dry, scrub_n8n_export, reminder_email, smtp_outbox/provider, http_guard, codeant_desk, stamp_locks, model_stamp, slow_sender): 923 passed, 1 skipped. All five applied: same files + both optional test files + test_portal_api: 1111 passed, 1 skipped.
Hygiene + gitleaks (DPLD_REQUIRE_SCAN=1, GITLEAKS_BIN=/tmp/work/gl/gitleaks 8.30.1, tree committed locally so new files are tracked): test_hygiene + test_codeant_hygiene: main alone 22 passed; all five 45 passed. Plain `gitleaks detect` on history: no leaks. (A `gitleaks dir` on a tree containing .mypy_cache/.ruff_cache printed ~110 hits; they come from my cache dirs, a `git archive` copy gives none.)

## Optional patches
regex-optional: equivalence is the corpus above (0 diffs, spans and sub). Independent of main. Behaviour change: none visible.
feed-optional (--url removal): grep of the whole clone (README, docs, contract.md, scripts incl. start_all/reset .sh/.ps1, n8n, tests, workflows, tools) and the handover folders: no caller of feed.py --url. The only `--url` hits are demo_only/burst.py and its callers (tests/test_http.py, docs/limits.md, contract.md), a different program, untouched. README uses `feed.py --source ... --index`. tests/test_portal_api.py only uses feed.target_host. `--url` becomes exit 2 "unrecognized arguments" (argparse; also `--ur` prefix abbreviations now fail). docs/settings.md mention of feed.py unaffected. Undocumented loss: sending to a non-configured desk (note says set DESK_BIND/DESK_PORT).

## Undocumented behaviour changes
Beyond the NOTES list: Nit 2 (qualname), and `_EMAIL_RE` gained ^/$ (only used with fullmatch; search semantics differ, no such user). The `desk listening on` line and serve_in_thread return text unchanged (same string).

## Closure of rv9 findings
Major 1 (two regexes stay): addressed by the optional patch with the rewrites rv9 proposed (same text as rv9's); odds below. S8703 taint carriers: checked_url deleted. S2583 robust alternative: done. Two missing stage edge tests: present and fail correctly (s-4 on old; s-5 kills drop rc==1). Nit traceback on refused address: gone with --url. Nit upper-case host test: moot.

## Honest odds for Sonar clearing (judgement, unmeasured)
| issue | patch | odds | why |
|---|---|---|---|
| S8786 identity.py PLAIN | main | ~80% | anchored, first repeat excludes @, my corpus: same language |
| S8786 identity.py _EMAIL_RE | main | ~80% | anchored, first dot found once |
| S5332 config.py, server.py x2, feed.py | main | ~88% | rule reads each string element; f"{DESK_SCHEME}://..." element does not start with http:// (ct.java read) |
| S5332 server.py:492 | main | ~75% | enclosing class no longer extends HTTPServer/ThreadingHTTPServer; residual: _Server still lists ThreadingHTTPServer as base, serve_forever call sites (1033,1202) were not flagged before but typing of a 2-base class may differ |
| S2583 desk.py | main | ~85% | no variable assigned by an inner function remains; closed source |
| S8786 run_real_check | regex-opt | ~70% | mandatory char before repeat, @ out of repeated class; reasoning from RedosFinder source read by rv9 |
| S8786 scrub MAIL | regex-opt | ~50% | leading possessive repeat on a partial-match pattern; old pattern was not slow, change is for the analyser only |
| S8703 feed.py:49 | feed-opt | ~65% | no argparse value reaches the address; urlopen target still derives from env config (Config.from_env), which a taint engine might treat as a source; closed source |
Main alone: ~8 issues at 75-88 each; expected clears about 6.5-7 of 8. With optionals about 8.5-9 of 11.

## Files
Report: /tmp/work/rv15-report.md. Scratch: /tmp/work/rv15-1/s/{corpus.py,bind.py,mut.py,zz_rv15_flows.py,*.log}. Patches reviewed: /tmp/demo-lead/handover/demo/sonar/sonar-p2-*.patch (v2 main + two optionals). Head: db54e13 + patches (not committed upstream). Tokens: not measured.
