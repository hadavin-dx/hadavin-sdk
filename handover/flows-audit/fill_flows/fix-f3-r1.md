# F3 fix, review round 1 (fixer, 2026-11-16). Files changed: fill_flows.py, test_fill_flows.py, README.md (all in fill_flows/).

Final counts: `python3 -I -m unittest` -> Ran 50 tests, OK (before: 27). `ruff check .` -> All checks passed. `ruff format --check .` -> already formatted.
Mutant M2 (whole values dict appended to the "cannot fill these names" refusal) re-run on a copy: now CAUGHT by 4 tests (test_missing_key, test_empty_value, test_leftover_token_unknown_name, test_other_name_refused_even_with_value). Extra mutant (mode check disabled): caught by test_values_file_modes_and_places.

## Design review
- R1-01/02/06: Subst._expr/_expr_part: token refused outside a clean {{ }}, with nested/odd braces, in a quoted JS string (' " `), with // or /* comment; refused in jsCode/functionCode/pythonCode (any value); values containing {{ or }} refused in read_values. Tests: Negative.test_token_* / broken_braces / comment, Unit.test_token_refusals_in_process.
- R1-03: manifest written first; created list includes it; cleanup removes it; `delete --no-manifest` (only plain .json files, no symlinks); delete also removes a manifest left without a folder. Tests: failed_write..., Delete.no_manifest_*, manifest_left_without_folder.
- R1-04: read_values refuses inside git, under /mnt, symlink, non-regular file, group/other bits; --out under /mnt refused. Tests: values_file_modes_and_places, values_file_under_mnt, output_under_mnt.
- R1-05: six placeholder names fillable (whole string equals name, raw text, keys too); fill prints "NOT READY TO IMPORT: N placeholders left" while any remain; exit 0 kept. Old substring PLACEHOLDER list replaced by the six exact names (check counts them too). Test: placeholders_filled_when_keys_given.
- R1-07: README rewritten top-down. R1-08: quotes, edge spaces, BOM refused; " #" warns. Tests: test_bad_values, inline_comment, bom.
- R1-09: README clean-up checklist (delete, values file, imported workflows, saved executions; unlink is not a secure wipe).
- Nits done: README says do not move the output folder (R1-10), exit 4 explained (R1-12/13), empty-value message tested, dead test condition removed, .JSON upper case refused, O_NOFOLLOW on input and values reads, NaN/Infinity refused, mkdir now inside the cleanup path, tests use tempfile.mkdtemp (no fixed /tmp/ff13), literal exit codes 1/2/4.
## Codebase review
- R1-01: do_check parses JSON, scans walked strings and keys, handles "$env.X" plain and $env["X"] (tests check_reads_parsed_json_forms, check_bad_json_and_nan).
- R1-02: PATH test uses a clean one-node flow, asserts exit 1 and PATH in stderr. R1-03: bad values asserted by specific message, newline tested ("line 2: no '='").
- R1-04: Base.cli helper fails any test if a VALS or placeholder value is in stdout/stderr; used by every fill/check/delete call in Negative and Delete (and most Positive).
- R1-05: film (and real) expressions asserted exactly. R1-06: token-in-every-location fixture (dict key, list element, node name, credential name, pinData).
## Not fixed (with reason, per resolve-f3-r1.md)
- Bare-repo detection (codebase R1-09), TOCTOU / dir_fd unlink (R1-13/14), sibling manifest (design R1-10): declined in the resolve; README says "do not move the folder" and has a "Known limit" paragraph.
- Template literals `${...}` and JS regex literals are not parsed: a token inside any quote/backtick is refused, comments with a token are refused; a regex literal holding a quote could mis-lex (would refuse or leave a token, which the final $env scan then refuses). Not verified beyond that reasoning.
- Loopback re-smoke on a filled copy (design R1-06 "named take-day gate") is not run here: it needs n8n; it stays a take-day step for the lead/owner.
- Check does not yet refuse on `$env` text inside non-string JSON (impossible in JSON). Nothing else open that I know of.
