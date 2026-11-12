# Static-analysis triage, lane 3 (in progress; test results filled in at the end)

Repo: public demo, branch initial-code, base 43110e7 (read-only clone /tmp/work/ro-clone, never edited). Work copies: /tmp/work/triage-copy (untouched, "before" runs), /tmp/work/apply-check (both patches applied, "after" runs). Nothing committed or pushed. No model call, no spend, no secret, no sub-agent.

## Read this first: failures, uncertain, not done

- **No REAL (behaviour-risk) instance was found in either cluster.** Every DeepSource item I could reproduce is STYLE or FALSE POSITIVE. So no behaviour-changing fix and no fails-before/passes-after test exist; I did not invent one. If DeepSource shows an item that is not in the table below, I could not reproduce it from the description (see next point).
- **I could not see the DeepSource report itself**, only the two cluster descriptions. I matched them to my own tool output. Two descriptions found nothing as worded: (1) "handlers that immediately re-raise ... in desk.py": desk.py has none (every bare `raise` in desk.py sits after an `if` or other statements); the immediate re-raises are in crm_hubspot.py, live_claude.py, smtp_outbox.py, smtp_provider.py. (2) "overlapping exception clauses" in desk.py: none; they are in other files (table). "missing let/const (implicit var)": I found no assignment to an undeclared name (ESLint `no-undef` and `no-global-assign` are clean for that); the only thing matching is the 504 uses of `var` (STYLE, not patched, see J4).
- **Browser tests did not run** (no Playwright; it is not in the hashed lock file and I did not install from elsewhere). The three portal edits are covered by the node-based portal tests and by an equivalence script, not by a real browser. The `log.js` change (`_open` handler made a named function) is not exercised by any test I could run; it is a mechanical move inside the same scope.
- `python -m pytest` before/after: see "Test runs" below.
- Not patched on purpose: the 504 `var` uses (J4), the 29 unused-variable warnings, test-file probes. Reasons in the table.
- Tools not run: gitleaks, bandit (not part of my findings; bandit 1.9.4 is in the lock file but I did not need it). EGM review was not done by me (lead runs it).

## Tools, versions, sources

| tool | version | source |
|---|---|---|
| ESLint | 10.1.0 | already on the machine at /opt/node-tools (symlink /opt/node22/bin/eslint); not installed by me; I cannot say whether it was pinned or hashed |
| ESLint config | mine, `eslint.config.mjs` in this folder | rules only, no plugins, no download: no-undef, no-use-before-define, no-loop-func, no-implicit-globals, no-var, prefer-const, no-redeclare, no-shadow, no-unused-vars, plus a `no-restricted-syntax` selector that flags ANY function inside a for/while loop |
| ruff 0.17.4, mypy 2.4.1, pytest 9.2.0 | from `requirements-dev.txt` | `pip install --require-hashes` into a venv inside the scratch copy (hashed lock file of the repo; lock says Python 3.12, I ran 3.13.18, the install worked) |
| ruff rules used for the scan | B023, B025, B014, B030, B012, F841, B007, TRY203, PLW0120, PLW2901, F811, E722, B904, S110, F401 | `--isolated`, run on src load_tools scripts tools tests demo_only n8n |
| `astscan.py` (mine, in this folder) | stdlib `ast` | finds except clauses where one class is a subclass of another in the same clause or an earlier clause (real class resolution by importing the module), handlers whose only statement is `raise`, and locals never read. `scripts/n8n_api.py`, `scripts/feed.py`, `scripts/run_real_check.py` could not be imported for class resolution; I read their `except` lines by hand (separate try blocks, no overlap) |
| node | 22 (/opt/node22/bin/node) | preinstalled |

## Table

Class: REAL = behaviour risk, STYLE = harmless but worth tidying, FALSE POSITIVE = the tool is wrong or the code is right as written. Line numbers are in the BASE commit 43110e7. "Patch" = fixed in js-portal.patch (JS) or py-retry.patch (Python); "no" = left alone.

### Cluster (a) JavaScript portal

| id | cluster | file:line | class | reason | fixed in patch | proof |
|---|---|---|---|---|---|---|
| J1 | a | src/lead_desk/portal/portal.js:474 (two uses), :643 (two uses) | FALSE POSITIVE | `Portal` is `window.Portal`, assigned at line 740 inside the same script; both uses are inside functions that only run after that (called from page scripts that load later, and from `boot()` on DOMContentLoaded). ESLint just does not know `window.X` is a global. | yes (cosmetic: now written `window.Portal`, same object) | node portal tests, eslint-after |
| J2 | a | portal.js:471 (booted), :498 (booted, routeForce), :550/:551 (routeForce), :572/:573 (booted, routed); declared at :576 | FALSE POSITIVE | `var` is hoisted; the initial values (`false`) are assigned when the script runs top to bottom, before any of these functions can be called, so no call ever sees `undefined`. | yes (declaration moved up to just after `var demo`) | node portal tests, eslint-after |
| J3 | a | portal.js:640 (stopDemo x3), :641 (demoKnown), :643 (demoLoaded); declared at :661 | FALSE POSITIVE | same reasoning: used in `modeSeen`, which runs from a network answer, long after the script body finished | yes (declaration moved above `modeSeen`) | node portal tests, eslint-after |
| J4 | a | all 7 files in portal/ (422 uses) and demo_only/portal_demo.js (82 uses): e.g. portal.js:6-8, theme.js:5 | STYLE | the whole portal is written with `var` inside strict-mode IIFEs (8 `'use strict'` markers); no global leaks. Switching 504 places to let/const is not mechanical (loop capture and temporal-dead-zone differ), and needs a decision and a browser run. | no | n/a |
| J5 | a | pages/overview.js:122 | FALSE POSITIVE | the `forEach` callback reads loop variable `grp`, but `forEach` runs it immediately, inside the same iteration; nothing keeps it for later | yes (inner loop replaces the callback; no function in the loop) | `equiv-overview-grouping.js`: 20000 random cases identical |
| J6 | a | pages/log.js:68 | FALSE POSITIVE | the `_open` function inside the `while` loop uses only `opened` and `render` (outer variables, not loop variables) and takes `k` as a parameter; no stale loop value is captured | yes (named function `openRun` declared once before the loop) | node portal tests (the clickable path itself is only in browser tests, not run) |
| J7 | a | tests/portal_state_probe.js:100, :124 | FALSE POSITIVE | test probe; an `await` inside the loop body and a synchronous `forEach`; nothing outlives the iteration | no (test file) | n/a |
| J8 | a | tests/portal_*_probe.js (many lines: `require`, `process`, top-level `function`) | FALSE POSITIVE | these are Node CommonJS scripts: `require`/`process` exist, and top-level functions are module-private there. My config had no node environment on purpose, to see them. | no | n/a |
| J9 | a | 29 `no-unused-vars` (e.g. portal.js:545 `stopPage`, :661 `demoKnown` written never read, ~20 unused `catch (e)`), 5 `no-shadow` (portal.js:173, 216, 231, 255; log.js:60) | STYLE | dead variable and unused catch bindings; the shadowed names are harmless (each is a local parameter or variable in its own function). Outside the two clusters. | no | n/a |

Result of `eslint` for the cluster rules (no-undef, no-use-before-define, no-loop-func, function-in-loop): src before 4 + 13 + 1 + 2 = 20 hits, after 0 (`evidence-eslint-before.txt`, `evidence-eslint-after.txt`). Only the `no-var` and warnings remain.

### Cluster (b) Python

| id | cluster | file:line | class | reason | fixed in patch | proof |
|---|---|---|---|---|---|---|
| P1 | b | src/lead_desk/desk.py:773 | STYLE | `tries_before` is unpacked and never read; the code on purpose starts from 1 when no charge was written (comment at desk.py:813-814) | yes (`_tries_before`) | tests, ruff, mypy |
| P2 | b | desk.py:781 (lambda reads loop variables `lead_id`, `email_key`, `owner_sent`, `status_sent`) | FALSE POSITIVE (latent) | the call runs in a worker thread that can be abandoned on timeout, but on a timeout or any error the `except` ends with `return`, and on success the call has finished, so the loop never moves on while a worker still holds the old values. Safe today; one deleted `return` would make it unsafe. | yes (`functools.partial` binds the values at that moment; same call, same arguments) | tests, mypy strict |
| P3 | b | desk.py:796, :809 (`failed` closure reads `tries_now`, created in the loop) | FALSE POSITIVE | `failed` is handed to `_finish_update`, which runs it on the same thread, and the iteration ends with `return`; a fresh `tries_now` is made each iteration and cleared at the start of each attempt | no | tests |
| P4 | b | src/lead_desk/crm_hubspot.py:326 (`except CrmError: raise`) | STYLE | `CrmError` is a `RuntimeError`; the next clause names `OSError, ValueError, HTTPException`, none of which is a parent of it, so it would pass through anyway | yes | `tests/test_except_clause_hierarchy.py`, test_crm_hubspot |
| P5 | b | src/lead_desk/live_claude.py:247 (`except LiveCapReached: raise`) | STYLE | same: not a subclass of anything in the next clause | yes (comment kept) | same test, test_live_claude |
| P6 | b | smtp_outbox.py:242, :283; smtp_provider.py:258, :304 (`except MemoryError: raise`) and smtp_outbox.py:274, smtp_provider.py:296 (`except (SendRefused, SendUnreachable, MemoryError): raise`) | FALSE POSITIVE | each is followed by `except Exception`, which WOULD catch MemoryError and the send errors and turn them into `SendUnreachable`/`SendAmbiguous`. Removing them changes behaviour. | no (must stay) | n/a |
| P7 | b | config.py:266, :389; smtp_outbox.py:224; smtp_provider.py:234 (`UnicodeError` named next to `ValueError`) | STYLE | `UnicodeError` is a `ValueError` | yes | hierarchy test, existing config and smtp tests |
| P8 | b | smtp_outbox.py:292; smtp_provider.py:313; load_tools/catcher.py:91 (`TimeoutError` next to `OSError`) | STYLE | `TimeoutError` is an `OSError` | yes | hierarchy test, test_load_tools, smtp tests |
| P9 | b | live_claude.py:483 (`URLError`, `OSError`, `socket.timeout` together) | STYLE | both others are `OSError`; `import socket` became unused and was removed | yes | hierarchy test, test_live_claude |
| P10 | b | demo_only/fake_imap.py:113; demo_only/fake_smtp_tls.py:89 (`ssl.SSLError` next to `OSError`) | STYLE | `ssl.SSLError` is an `OSError` | yes | hierarchy test |
| P11 | b | src/lead_desk/portal_api.py:493-496 (`tries`, `step_rank`, `owner_done`, `step_done` unpacked, never read) | STYLE | unused tuple targets; probably the "unused `tries`" item | yes (`_` prefixed; the always-None pre-assignment shortened to the three names that are used) | test_portal_api, ruff, mypy |
| P12 | b | load_tools/load_driver.py:238 (`j` unused loop variable) | STYLE | | yes (`_`) | test_load_tools |
| P13 | b | desk.py bare `raise` at 420, 436, 438, 865, 894, 1051, 1082, 1121, 1130, 1135, 1365, 1593, 1675, 1677, 1686, 1712, 1736, 1856, 1897, 1900, 2112 | FALSE POSITIVE | none is an immediate re-raise: each follows a condition, a rollback, a log line or a state change | no | n/a |
| P14 | b | tests/test_http.py:280; tests/test_later_approval.py:190 (ruff B023) | FALSE POSITIVE | the lambda runs to completion (`wait_until`, `run_threads` join) before the loop variable changes | no (tests) | n/a |

## Patches

- `js-portal.patch`: portal.js, pages/overview.js, pages/log.js. Rows J1, J2, J3, J5, J6.
- `py-retry.patch`: desk.py, crm_hubspot.py, live_claude.py, config.py, smtp_outbox.py, smtp_provider.py, portal_api.py, load_tools/catcher.py, load_tools/load_driver.py, demo_only/fake_imap.py, demo_only/fake_smtp_tls.py and the new `tests/test_except_clause_hierarchy.py`. Rows P1, P2, P4, P5, P7 to P12.
- Both apply cleanly to 43110e7 (`git apply --check` then apply in a fresh clone, 15 files changed). ruff check, ruff format --check, mypy --platform linux and win32: clean on the patched tree (run in the dev copy).
- `tests/test_except_clause_hierarchy.py` is a pin, not a bug test: it passes on the old and the new code (`evidence-hierarchy-test.txt`, 3 passed each), because nothing behaves differently. It fails if one of the class relations the shortened clauses rely on ever changes.

## Test runs

(filled in below)
