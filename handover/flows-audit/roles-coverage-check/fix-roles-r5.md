# Fix round 5: roles coverage check

Date 2026-11-16. Files touched: check_grants_cover_queries.py, test_check_grants.py, README.md, this log. Nothing committed by me. Note: an automatic "board" job commits the working tree every few minutes (commits 27e5ea0ef, 1e343c542, 001d8ab3e), so git HEAD already contains my edits; the "old script" below is commit 27e5ea0ef (before my edits).

## Failures, gaps and what I did NOT check (first)
- No failures remain in what I ran. Not run: any database, any n8n instance, CodeQL/SonarCloud/CodeRabbit, the full repo pytest suite (only this folder's 64 tests).
- Slip found on the way: my first "old script" came from `git show HEAD`, which already held my edits (auto board commits); all 20 new tests "passed on old", which proved nothing. Redone from 27e5ea0ef (below).
- Still open, by nature: the split-string case ('DEL'+'ETE' in a Code node) is caught only when the text still names mf_leads (H22 in evidence-r4). A Code node can build any text at run time; no text check can close that. Next step if wanted: refuse any Code node in the four flows (needs the owner's decision, the flows may use Code nodes). The parser stays a "rough parser"; the database tests are the real proof.

## Gate (run from /home/user/hadavin-sdk on handover/flows-audit/roles-coverage-check), all rc=0
- `ruff check <folder>` -> All checks passed (system ruff 0.16.9, and `uv run --all-extras --group test ruff check` with the repo-pinned ruff).
- `ruff format --check <folder>` -> 8 files already formatted (both).
- `bandit -ll -r <folder>` -> rc 0, Medium 0, High 0.
- No `noqa`, no suppressions. The 21 errors were fixed in code: imports sorted; `re.I` etc. written as `re.IGNORECASE`; list literal for COLS; file opened with a context manager; S603/PLW1510: the tests now run the script in this process with `runpy.run_path(..., run_name="__main__")` (same `__main__` path and exit code, output captured; an uncaught error is written as "Traceback" text so tests still catch it) instead of `subprocess`; S608/B608: the test uses a whole literal query instead of `q + " DELETE ..."`; RUF012: the credential map and shape lists are module-level constants or tuples. A new BLE001 showed up for my first safety net `except Exception`; replaced by the named tuple `UNEXPECTED`.

## Items
1. Lint, format, bandit: done, above.
2. `"nodes": null` and other malformed shapes: new `flow_nodes()` validates before use. One FAIL line, rc=1, no traceback; `main()` also has a safety net. 19 shapes tested: nodes null / string / object / number / missing; top level list / null; node string / null / list; parameters string / list; name list / number; type number; credentials string; credentials.postgres string; 100000-deep nested JSON; non-UTF-8 bytes. Real run: `FAIL f mf-hook: malformed flow file: 'nodes' is null, expected a list` (rc=1).
3. SQL text in a Postgres node's notes or other parameter (not its query field): decision = FAIL ("SQL-like text ... in the notes or another parameter of a Postgres node"). Tests: notes, `options.queryReplacement`; control: plain notes not flagged.
4. Disabled node: decision = still counted and fully checked as if enabled, AND flagged FAIL ("node is disabled ... remove it or enable it") for any `disabled` value other than absent/null/false (text "true" included). Tests: true, "true", false (not flagged), disabled with `DROP TABLE` (both messages appear).
5. Size limit 5 MB (5242880 bytes), checked with `stat` before reading, for flow files and the roles document; rc=1, "file is N bytes, over the 5242880 byte limit (not read)". Tests: 5 MB + 10 refused, 4 MB read OK, big roles document refused.
6. Forbidden keyword inside a string literal: old behaviour = literals blanked, passed silently (rc=0, H03). Decision = FAIL ("forbidden keyword DELETE inside a string literal (the check cannot tell data from SQL; pass it as a parameter)"). Literals now handle `''` escapes; dollar-quoted strings and an unbalanced quote are also flagged. Tests: DELETE in literal, DROP in escaped-quote literal, `$$x$$`, `'x;`; control: the real flows (no forbidden word in their literals) stay rc=0.
7. README: working command is `python3 -m unittest -v test_check_grants` from the folder, no `-I`; README and test docstring corrected (the old docstring said `-I -m unittest`, which gives ModuleNotFoundError, evidence-r4 1a); a test pins it.

## Evidence (raw results)
- Full tests, from the folder: `python3 -m unittest test_check_grants` -> "Ran 64 tests ... OK" (44 old + 20 new).
- Baseline: `python3 -I check_grants_cover_queries.py ../../demo/n8n-flows-real-v5 ../../demo/n8n-flows-film-v5` -> rc=0, 14 postgres nodes each, TOTAL PROBLEMS: 0.
- New tests against the OLD script (commit 27e5ea0ef; `SCRIPT=<old copy> python3 -m unittest test_check_grants.Round5`): Ran 20, FAILED (failures=22, errors=7, counting sub-tests). Failing on old: every shape case except non-UTF-8, deep nesting, notes, other parameter, disabled (3 tests), big flow file, big roles document, literal DELETE, literal DROP, dollar quote, unbalanced quote. Passing on old by design (guards against over-flagging, or already right): non-UTF-8 file, plain notes, disabled=false, 4 MB file, harmless literal, README text.
- Not re-run: the evidence-r4 mutation script and 24 hostile files (the runner's scratch files, not in this folder). Next step: a fresh EVIDENCE RUNNER pass on the final head.
