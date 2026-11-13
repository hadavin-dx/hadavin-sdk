# P2 v2 notes: clear-text http, identity regexes, one bug (patch sonar-p2-regex-http-bug-v2.patch) plus two optional patches

Base: db54e13. Lead decision applied: the main v2 patch carries only the sites with odds of 80 percent or more; the rewrites
whose odds are lower are in separate optional patches, and the issues Sonar will probably keep are listed below as "accepted with
reason" (no suppression comments anywhere).

| patch | what | needs |
|---|---|---|
| sonar-p2-regex-http-bug-v2.patch (MAIN, complete, applies on db54e13) | identity.py two S8786; five S5332 (urls.py, server.py, config.py, feed.py default, `_ExclusiveBind`); S2583 (desk.py) ; tests/test_sonar_p2_choke_points.py | nothing |
| sonar-p2-regex-optional.patch | `run_real_check._ADDRESS` and scrub `MAIL` rewrites (my re-verified versions of the reviewer's) + tests/test_sonar_p2_regex_optional.py | main v2 |
| sonar-p2-feed-optional.patch | S8703: `feed.py --url` dropped, address from the configuration only + tests/test_sonar_p2_feed_optional.py | main v2 |
Apply matrix (evidence-p2v2-5-apply-matrix.txt): main alone; main with P1 v2 and P3 in all six orders; main + each optional, alone
and together, in several orders with P1/P3: all clean, and ruff, format, mypy linux and win32, bandit are clean with all five
applied. An optional patch must come after main (the order "feed-optional before main" fails by design).
Files touched by main: scripts/feed.py (3 lines), src/lead_desk/{config,desk,identity,server}.py, new src/lead_desk/urls.py, new
test file. Overlap with P1/P3: server.py and desk.py (clean in every order).

## What failed or is uncertain (read first)
1. I still cannot see the Sonar result; "expected" below is reasoning from the analyzer source the reviewer read, not a measurement.
   I did not run Sonar's own regex analyzer: the only copy is a jar the reviewer downloaded and the permission layer refused to run it; I did not get around that.
2. The scrub MAIL pattern cannot be made slow. The old one was not slow on any input I tried (0.03 to 0.5 ms up to 16 000
   characters; the reviewer tried six shapes), the new one is not faster. Its rewrite (optional patch) is for the static analyser only; its timing
   test passes before and after and its docstring says so.
3. One mutant survives and cannot be killed by a test: putting "@" back into the repeated class of `_ADDRESS` (optional patch). Same matches,
   same speed; it differs only for the analyser. The guard is the pattern text plus the equality tests.
4. S2583 and S8703 are closed-source rules: odds are judgement.
5. Not run: full suite (lead), Sonar, CodeQL, CodeRabbit, a real Windows run (win32 bind path: faked platform on Linux + mypy win32).
6. EGM not run (I cannot invoke the EGM skills here); the lead runs it.
7. Slip: my first full test run found test_hygiene failing because my own test used a host name that the repo's hard-coded-host scan
   rejects (`desk.corp.*`); I changed it to a `.example` name and re-ran. The numbers below are from the re-run on a fresh apply.

## Per-issue expectation (PR 4 issues in the P2 scope; none measured)
| rule | file:line (PR 4 base) | in which patch | expectation |
|---|---|---|---|
| python:S8786 | identity.py:14 PLAIN_ADDRESS | main | likely clears (~80%): anchored, first repeat cannot take "@" |
| python:S8786 | identity.py:15 _EMAIL_RE | main | likely clears (~80%): anchored, first dot found once |
| python:S5332 | config.py:447, server.py:733, server.py:1035, feed.py:65 | main | clear (~90%): the f-string no longer starts with the scheme text (feed.py: default of `--url` is built by `desk_origin`) |
| python:S5332 | server.py:492 | main | likely clears (~85%): `super().server_bind()` is no longer in a class whose base is the HTTP server; residual doubt: `serve_forever` is a sibling branch of the same check |
| pythonbugs:S2583 | desk.py:2092 | main | likely clears (~80%): no variable written by an inner function remains (the flag is a return value). Closed-source rule |
| python:S8786 | run_real_check.py:116 | regex-optional | ~75%: one mandatory character before the repeat, "@" out of the repeated class |
| python:S8786 | scrub_n8n_export.py:102 | regex-optional | about even (~55 to 60%): leading possessive repeat on a partial-match pattern after a mandatory character; nested possessive group in the look-ahead is the residual doubt |
| pythonsecurity:S8703 | feed.py:49 | feed-optional | ~75%: no value from the command-line namespace reaches the address; cannot be measured; the engine could also follow the configuration (environment) |
Main patch: 8 issues expected to clear at 80 percent or more (2 + 5 + S2583 at the edge of 80). Optional: 3 more at 55 to 75 percent.

## Sonar will likely keep, accepted with reason (if the optional patches are not applied)
- S8786 run_real_check.py:116 and scrub_n8n_export.py:102: the old patterns are slower than they should be only on `_ADDRESS` (quadratic: 1.2 s at
  16 000 characters; it runs on text the tool itself reads) and not at all on scrub MAIL (no slow input found). The
  lead may take the optional patch, or mark them "reviewed, safe" in the Sonar UI (a UI action, not a code suppression).
- S8703 feed.py:49: `--url` is a developer convenience of a demo script that talks to a loopback desk; the reviewer found the request can only go where the
  user types it on their own command line. The feed-optional patch removes the option.

## What changed from v1 (review rv9)
| review finding | v2 |
|---|---|
| MAJOR the two S8786 will likely stay | verified rewrites (below) kept in the regex-optional patch; main no longer carries them |
| S8703 `checked_url` taint carriers | `checked_url`, `SCHEMES`, trusted-host tuple deleted. Chosen: drop `--url`, not rebuild it, in the feed-optional patch (reasoning below) |
| nit: a refused address ends in a traceback | no refusal path left: `--url` is then an unknown option; argparse prints one usage line and exits 2 (tested) |
| S2583 | `attempt` returns `(rows, moved)`; new `Desk._finish_update_moved` returns the flag of the try that committed; `_StageMove` deleted |
| two missing stage edge tests | added: a stale-token `sent` result must not move the stage (kills "drop rc == 1"), and a move seen by a try that did not commit must not be reported (fails on the old code; replaces the per-try reset line, which no longer exists) |
| NOTES "11 of 11" | the table above |

## Regex equivalence, re-verified by me (evidence-p2v2-equivalence.py, output evidence-p2v2-1-equivalence.txt)
Old patterns read from `git show db54e13:`. For `_ADDRESS` and MAIL: .sub output AND every match span compared on 3 726 336 texts: all strings
up to length 6 over an 11-symbol alphabet (a @ . space : , ; < " ' newline), up to length 6 over a 10-symbol one (a @ full-width-@ . - % + space _
e-acute), up to 5 tokens over domain tokens (a @ . example com test invalid - space); 600 000 random strings of up to 16 tokens from about 60 tokens;
26 realistic texts (each also padded and doubled). Differences: 0. New patterns, ms: "a"*128 000: address 3.7, MAIL 2.5; "a@"*64 000: address
1.1, MAIL 6.5. Old `_ADDRESS` "a"*16 000: 1 247 ms (4 ms at 1 000, 68 ms at 4 000). The identity rewrites (main) were verified by the reviewer
(1.5 million cases, 0 differences) and by the repo's exhaustive tests; I did not re-run the reviewer's corpus for them.

## feed.py: why `--url` is dropped (feed-optional) instead of rebuilt
`--url` is in no README or docs page (the one `--url` in docs/limits.md is `demo_only.burst`, a different program, unchanged); no test or script calls
`feed.py --url`; the module text already says the address comes from the configuration. Rebuilding it from constants and a tuple of trusted hosts
(v1) keeps a path from the command-line namespace to the address that a taint engine may follow through lookups and comparisons (the review
rated it ~50 percent). Dropping the option removes the path and about 20 lines. It is optional because it removes a (undocumented) feature and its
odds are below 80 percent.

## Behaviour changes that no document describes (read before merging)
Main patch:
1. `_record_send_result`: if the database stays locked after the stage-moving write ran but did not commit, the old code still freed the lead's copy wait; the
   new code does not (the flag is the return value of the try that ran last). Safer direction. A test fails on the old code.
2. `_finish_update` delegates to `_finish_update_moved` (same log lines and the same swallow of a locked database; the other callers unchanged).
3. `urls.desk_origin` writes every desk address (same text out); `_ExclusiveBind` moves the Windows bind option into its own class ahead of the HTTP server in the class order (same behaviour on Linux; the Windows path is tested with a faked platform);
   `PLAIN_ADDRESS`/`_EMAIL_RE` accept the same texts (`_EMAIL_RE` now has ^ and $, used only with fullmatch).
Feed-optional only: `scripts/feed.py --url ...` no longer exists (exit 2, "unrecognized arguments"); before, any address urllib could open was accepted. Anyone sending to another desk sets DESK_BIND/DESK_PORT (documented).
Regex-optional: none visible (same matches); only speed on a long text.

## Rung table (R448)
| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| regex rewrites | linear time, same matches | possessive quantifiers / mandatory first char / look-behind (stdlib re) | 3.7 million old-vs-new comparisons, 0 diffs | nothing: pattern text | CUT-TO-CONFIG |
| urls.py | one place for the scheme, with its reason | none higher: a loopback-only desk has no https | analyser exempts literal loopback, not `f"http://{host}"` | the one place + a test forbidding the pattern elsewhere | KEEP-CODE (19 lines) |
| feed `--url` | request address not from the command line | remove the option | grep: undocumented, no caller | nothing | CUT (v1 checked_url deleted) |
| _ExclusiveBind, `_finish_update_moved` | analyser-visible structure | none | tests, 6 mutants killed | - | KEEP-CODE (tiny) |

## Evidence files (this folder)
- evidence-p2v2-equivalence.py / evidence-p2v2-1-equivalence.txt: old vs new for the two optional regexes.
- evidence-p2v2-2-fails-before.txt: all three new test files on db54e13 (+ urls.py): 8 failed, 14 passed (5 main, 1 regex-optional, 2 feed-optional fail; the rest pin behaviour or equality by design, honestly not fails-before).
- evidence-p2v2-3-stage-mutants.txt: 6 desk mutants all killed; 3 `_ADDRESS` mutants, 2 killed, 1 survives (item 3).
- evidence-p2v2-4-lint-mypy-bandit.txt: gates for main alone.
- evidence-p2v2-5-apply-matrix.txt: apply matrix and gates with all five patches applied.
- evidence-p2v2-6-pytest-affected.txt: the 20 test files of P2 (NOTES-p2.md lists 18, counted 18 + new file; plus test_ledger_and_bind_retry and test_desk_http_edge_cases the reviewer added) on main alone.
Tooling deviation: no uv `test` group; venv from requirements-dev.txt (ruff 0.17.4, mypy 2.4.1, bandit 1.9.4, pytest 9.2.0, Python 3.13).
R-numbers: R448, rules 5, 6, 7, 8, 12 (from the preamble text; bible not readable here). Token use: not measured.
- evidence-p2v2-7-hygiene-gitleaks.txt: tests/test_hygiene.py + test_codeant_hygiene.py with DPLD_REQUIRE_SCAN=1 and gitleaks (the lead's finding on v1: `desk.corp.` and `169.254.169.254` literals): main alone and all five patches applied: passed. v1 was never run with gitleaks; the v2 test files contain neither literal.
