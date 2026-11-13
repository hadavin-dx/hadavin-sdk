# P2 v2.1: clear-text http, identity regexes, one bug (sonar-p2-regex-http-bug-v2.1.patch) plus the two optional patches (unchanged)

Base db54e13. v2.1 is a COMPLETE replacement of sonar-p2-regex-http-bug-v2.patch (do not apply both). The optional patches
sonar-p2-regex-optional.patch and sonar-p2-feed-optional.patch are unchanged and still apply after it (matrix in evidence-p2v21-5).
Touches (new vs v2): demo_only/portal_demo.py (one import line). Overlap with P1 v3 / P3 v2: server.py, desk.py (clean in every order tried).

## What failed or is uncertain (read first)
1. Sonar not seen: every Sonar expectation below is judgement carried over from review rv15, unmeasured.
2. test_model_stamp_and_reaper.py::test_reserve_covers_its_items (counts open files) failed ONCE in my first 24-file run (run while ruff/mypy ran
   in parallel; other agents also use this machine). It passes alone 3 of 3, passed in the 12-file prefix on v2 and v2.1 and on db54e13,
   failed once in the 12-file prefix on v2 (not v2.1). Conclusion: a timing-sensitive open-file count, not caused by this patch; not proven.
   Run 2 result is in evidence-p2v21-3.
3. Not run: full suite (lead), Sonar, CodeQL, CodeRabbit, real Windows (win32 bind: faked platform + mypy win32), EGM (not invokable by me; lead runs it).
4. The v2 stage mutant M3 was killed only by the reviewer's scratch test; now by a repo test (below).

## Changes against v2 (review rv15 nits)
| nit | change | proof |
|---|---|---|
| 1 mutant "flag true when rc==1 and state=='sent', ignoring _mark_contacted" survived | new test test_a_sent_result_when_the_stage_is_already_further_keeps_the_copy_wait (adapted from rv15 test_f8: lead already at a later stage; row becomes sent, stage stays, wait stays) | evidence-p2v21-1 A: with the mutant the v2 tests all pass (17 passed), the new test fails; real code 18 passed |
| 2 lambda wrapper hid caller qualnames (`_finish_update.<locals>.<lambda>`) | restructured: `_finish_update` and `_finish_update_moved` both call one helper `_finish_with(attempt, what, rows)` which hands `attempt` itself to `_locked_retry`. Callers' qualnames (`copied`, `failed`, `record`, `give_back`, `attempt`) are stable and `is_write(fn, "copied")` works. Same log lines, same swallow of a locked database, same return values. | two new tests: one spies `_locked_retry` and checks it receives the exact functions and `is_write` matches; one checks that every `_finish_update*(...)` call in desk.py passes a plain name (no lambda). Both fail on v2 desk.py (evidence-p2v21-1 B) |
| 3 DESK_SCHEME duplicate | single source: `lead_desk.urls.DESK_SCHEME`; `demo_only/portal_demo.py` now imports it (demo_only already imports lead_desk; src never imports demo_only, so the direction is right). No duplicate left. | portal_demo tests are in the affected set (test_http etc.) |
| 4 `_Server` lists ThreadingHTTPServer | possible without behaviour change: new empty class `_ExclusiveHTTPServer(_ExclusiveBind, ThreadingHTTPServer)`, `_Server(_ExclusiveHTTPServer)`. MRO is the same chain with one extra link after `_Server`. Only a class order test and a double-bind test were added. | evidence-p2v21-2: v2 vs v2.1 probe identical: double bind EADDRINUSE (98), serve + request 204, shutdown + server_close + immediate rebind OK, server_name/port, faked win32 sets SO_EXCLUSIVEADDRUSE then SO_REUSEADDR then bind in the same order; the class-order test fails on v2 server.py. Whether Sonar's check looks at indirect bases is unknown: it is a possible gain, not a certain one. |

## Gates (evidence-p2v21-3/4)
ruff check, ruff format --check (148 files), mypy linux and win32 (27 files), bandit -ll as lint.yml (no Medium/High): clean. Slip: my first
lint run showed E501 and a format difference in my new text; fixed and re-run.
Hygiene + gitleaks: see evidence-p2v21-6 (DPLD_REQUIRE_SCAN=1, gitleaks 8.30.1, tree git-added with `git add -A` first).

## Per-issue odds (judgement, unmeasured; carried over from rv15)
| issue | patch | odds | why |
|---|---|---|---|
| S8786 identity.py PLAIN_ADDRESS | main | ~80% | anchored, first repeat excludes @; 3.1 million texts equal (rv15) |
| S8786 identity.py _EMAIL_RE | main | ~80% | anchored, first dot found once |
| S5332 config.py, server.py x2, feed.py | main | ~88% | f"{DESK_SCHEME}://..." element does not start with the clear-text scheme text |
| S5332 server.py:492 | main | ~75-80% | enclosing class no longer extends the HTTP server directly (Nit 4 may add a little) |
| S2583 desk.py | main | ~85% | no variable assigned by an inner function remains; closed rule |
| S8786 run_real_check.py | regex-optional | ~70% | mandatory char before the repeat; @ out of the repeated class |
| S8786 scrub MAIL | regex-optional | ~50% | old pattern was not slow; change is for the analyser only |
| S8703 feed.py:49 | feed-optional | ~65% | no argparse value reaches the address; environment configuration may still count as a source |
Main alone: about 6.5 to 7 of 8 issues expected cleared. With both optionals: about 8.5 to 9 of 11. All judgement.

## Rung table (R448)
| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| `_finish_with` helper | share the busy/row-count handling without hiding caller names | none higher | tests above | one place for the log text | KEEP-CODE (tiny; removes the lambda) |
| `_ExclusiveHTTPServer` | analyser-visible structure | none | evidence-p2v21-2 | nothing | KEEP-CODE (4 lines) |
| DESK_SCHEME single source | one scheme constant | import from src into demo_only | tests | - | CUT duplicate |
Other components as in NOTES-p2-v2.md.
R-numbers: R448, preamble rules 5, 6, 7, 8, 12 (bible not readable here). Tokens: not measured.

## Evidence files (this folder)
evidence-p2v21-1-fails-before-and-mutant.txt, -2-bind-behaviour.txt (+ evidence-p2v21-bindprobe.py), -3-pytest-affected.txt (24 files: the 20 of v2 plus those rv15 listed),
-4-lint-mypy-bandit.txt, -5-apply-matrix.txt, -6-hygiene-gitleaks.txt.
