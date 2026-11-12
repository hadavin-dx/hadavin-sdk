# Q8a-1 fix batch b10 (base f0febfb6): builder notes

Builder records, not an independent review. Gate rows are filled in at the end of this file.

## What was NOT done or could not be checked (first)
- Question q-q8a1-hide-ids is NOT changed (owner/lead decision still open): module, host, operation and source names that DEFINE a thing stay printed (safe default). Only the wrong `_HOST` reason text was corrected.
- Not run: security-job steps of ci.yml (pip-audit, Semgrep, zizmor), perf, live Vault (no server here).
- The known timing test `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in` fails alone on main too; not touched.
- First full pytest run had 1 failure that was my own Postgres setup (the `dblink_connect` test needs the server process to carry PGHOST/PGPORT); I restarted the server with them and re-ran the full suite once more at the same head (both logs kept).
- "Mutant runner for the package" is `tests/stage_mutants.py` (the only mutant list CI runs); there is no separate second runner, so one row is recorded for it.

## Findings and what changed
1. C1 (Major): `sources/kubernetes.py` printed configured namespace entries at 8 sites. `rules_problems(where, rules)` now takes a position label and `_probe_scope` passes "namespace entry N" (1-based). `namespace` and `ns` are added to `CONFIG_DERIVED` in the guard; the two URL-building f-strings with `{ns}` are allowed as "never put in a message". Sibling search: the only other source module text is `sources/__init__.py` (source key via `shown_name`) and `sources/kinds.py` (kind names registered in code, already allowed); the guard now walks all of src with the two new spellings and found only the kubernetes sites. Tests: `test_a_configured_kubernetes_namespace_is_never_printed_only_its_position` (8 rows, one per print site, three namespaces incl. a plain word and a secret-shaped value, also through `scope_problems`, the route into app start-up) and `test_the_rules_problems_label_is_said_as_given_and_holds_no_namespace`. Mutants M20a (rule problems labelled with the configured text again) and M20b (the incomplete-review refusal names the namespace again).
   Fail-before: with `src/hadavin_sdk/sources/kubernetes.py` from f0febfb6 and the new tests, `test_a_configured_kubernetes_namespace_is_never_printed_only_its_position`, `test_the_rules_problems_label_is_said_as_given_and_holds_no_namespace` and `test_no_config_derived_name_is_put_in_a_message_outside_the_one_filter` FAIL (3 failed, 4260 passed over the 5 test files that touch this; log `/home/user/build/B-Q8a1-b10-failbefore.txt`).
2. D2/C3: each killer assertion now has its own message and each mutant its own `expect` fragment, shown killed by that assertion: M18g "first characters of a pasted pin" (new assertion before the existing one; skipped for the real-digest case, which prints 12 characters by design), M18n "unset variable name is printed" (name check moved before the equality), M18o: the mutant now appends the model id AFTER the asserted sentence so the sentence check passes and "model id of the route is printed" fails, M19g "named by its values". M19e was an exact duplicate of M17u (same file, old, new, killer, expect) and is removed; M17u keeps "swordfish". Count 175 -> 176 (-1 duplicate, +2 new).
3. C2 (part): `_HOST` reason rewritten: a bare hostname is a defining id (open question q-q8a1-hide-ids), a login or path in a host was refused earlier by `safe_url`. No printed id changed.
4. Old-code passes (6 tests, from `f0febfb6/RESULTS.md`), one line each:
   - `test_the_guard_finds_each_way_of_printing_a_configured_name_and_a_stale_allowance`: tests the scan helper inside the test file, so no change of src can fail it. Checked by hand: switching off the `raise` branch of `_message_nodes` in a scratch copy makes it fail (raw output: first E lines list the missed `raise` sites).
   - `test_a_tool_call_with_a_login_in_the_url_is_a_tool_refusal`: the refusal existed on main already (behaviour kept); killed by mutant M17zb.
   - `test_a_tool_name_in_the_app_is_pattern_bound_so_shown_name_there_changes_nothing`: the pattern existed on main (behaviour kept); killed by M17za.
   - `test_an_empty_tools_manifest_does_not_refuse_tools_allowed_but_a_manifest_with_tools_does`: on main nothing refused either way for the empty case; killed by M18k.
   - `test_every_probe_row_either_raises_or_is_listed_with_its_reason`: checks only the data table of accepted rows (each has a reason of 30+ characters, all are probe rows); no src involved, nothing to mutate.
   - `test_the_marker_is_in_no_error_text_in_any_probe_row` (mixed): the rows listed as accepted raise nothing on old and new code, so those parameters pass; the other rows fail on main code and are covered by the mutants M16*-M19*.
5. Nits:
   - D3 fixed (CHANGELOG no longer says `shown_name` covers secret names in tools.py).
   - D4 stated in CHANGELOG: an allowance is keyed by module and site text, so an identical second site is covered (not changed: counting per site would make every moved line a new allowance; the reason must be read).
   - D5: test `test_the_platform_secret_probe_shows_a_configured_name_and_hides_a_pasted_one` renamed to `..._names_a_secret_by_position_and_never_by_name` (it asserts none shown). CHANGELOG now says that an unknown caller-passed agent id is `<not shown>` (the change is by decision) and that agent_loop counts physical lines while the golden gate counts non-empty lines (its message already says so). `secrets_env.py` not naming the variable follows the decision (nothing to change). `tools.py:387` wording: see C5.
   - C4 fixed: comment beside M19c/M19d (they rely on pytest printing the chained error; if that changes they turn BAD, not good); the provider test uses `tmp_path` instead of unremoved `mkdtemp` folders.
   - C5 fixed in CHANGELOG: header no longer says "rounds 1 to 8", the process note became plain words, and `load_tool_module` is stated to read pinned files directly with a type-only error. NOT changed in code: switching it to `read_configured` is a behaviour change on a security path with no failing test behind it; stated here for the lead (no secret can be read from it: the error is type only).
   - C6 fixed: the wildcard `match` in `tests/test_p1b_backends.py` is the exact sentence "action executor secret 1 of 1 (sorted by name) cannot be read at start-up". The absence checks in `test_p4_secrets.py` were judged stricter and correct by the reviewer; unchanged.

## Gates (final head, tree clean except this commit)
| Step | Command | Exit | Last line |
|---|---|---|---|
| ruff check | ruff check src tests demos tools | 0 | All checks passed! |
| ruff format | ruff format --check src tests demos tools | 0 | 321 files already formatted |
| bandit | bandit -q -r src demos tools -ll | 0 | only the existing nosec warning (tools.py:410) |
| scan_repo | python tools/scan_repo.py | 0 | (no output) |
| stage mutants / mutant runner | python tests/stage_mutants.py via heavy.sh | 0 | 176 of 176 good; problems: [] |
| full pytest | pytest -q -m "not live and not perf" via heavy.sh, own Postgres 16 port 56331 | 0 | 11043 passed, 1 skipped, 28 deselected in 252.79s |
| full pytest, first run | same | 1 | 1 failed (dblink test, my server lacked PGHOST/PGPORT), 11042 passed; log B-Q8a1-b10-full-run1-envfail.log |
| gitleaks | gitleaks git origin/main..HEAD (before commit) and gitleaks dir . | 0, 0 | no leaks found |
