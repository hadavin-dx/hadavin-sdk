# P3a round 6 disposition (ticket revision 8, 2026-11-05 18:20 UTC = 23:50 IST)

Applies `P3a-round6-resolve.md`. Ticket: `handover/tickets/P3a.md`. Text only; nothing run except the read-only probes listed below.

Counts: 16 finding ids (ADV-R6-1 to 9 = 9, COR-C6-1 to 7 = 7). The resolve table has 14 rows. The resolve's own count line says "18 ids covered by 15 rows"; that is wrong (16 ids, 14 rows). I did not edit the resolve. Result: 16 ids applied, 0 contested, 0 declined; 3 applied with a stated extension or deviation (ADV-R6-2, ADV-R6-3, ADV-R6-4).

| id | state | ticket location (by symbol) |
|---|---|---|
| ADV-R6-1 | applied | Files (stub line `tests/test_k2_migrations.py:392` becomes `lambda paths, texts=None: []`); Existing tests; FAIL-BEFORE green-list check; evidence command 5b; coupling table P4d and P2a rows |
| ADV-R6-2 | applied, extended | `statement_text` (CR ends a `--` comment; whitespace set incl. FF, VT); tests `test_comment_ends_at_cr`; mutants M51, M52; Open point 7 (sibling hole in `_scan`, new PENDING LEAD) |
| ADV-R6-3 | applied, extended | refusal rule (d): word match on `keep_identifiers=True` text, `U&"` refused; `test_set_config_in_every_spelling` (6 spellings, 2 allowed texts); M53, M54, M58 |
| ADV-R6-4 | applied, deviation | `hand_recipe` refuses backslash anywhere and bare psql variables (resolve said line-start only: too narrow, probe below); `test_recipe_has_no_include_command` limited to generated parts; `test_recipe_refuses_psql_syntax`; M55, M56 |
| ADV-R6-5 | applied | `test_statement_text_exact_output`; M26(c), M26(e) now killed; M25 restated (15); count table, arithmetic 90 - 3 + 9 = 96 |
| ADV-R6-6 | applied | Tests: `test_ci_has_its_inputs` with `missing_ci_inputs`; M57 |
| ADV-R6-7 | applied | check block cut (hand_recipe, M39, M40, H4 row 2 replaced by double-run row, exemption in refusal list removed, Open point 14 rewritten); `created_relations`/`created_of` dropped; v1.1 row for post-condition check; M59 added |
| ADV-R6-8 | applied | Path class: security |
| ADV-R6-9 | applied | `read_files` interface: `read_text(encoding="utf-8")` |
| COR-C6-1 | applied | same as ADV-R6-1 |
| COR-C6-2 | applied | v1.1 table: two rows (checksum column, `--accept-late`) |
| COR-C6-3 | applied | one description of the not-a-regular-file message (by-product of `is_file()`) in Context, Interface, Tests |
| COR-C6-4 | applied | FAIL-BEFORE 4a/4b (dangling link brought back as pure check) |
| COR-C6-5 | applied | kinds count: 13 kinds, 19 mutants, arithmetic stated |
| COR-C6-6 | applied | `ci.yml` cites: Postgres service 38-49, pytest step 84-88 |
| COR-C6-7 | applied | mutant totals and per-group arithmetic |

Note: COR-C6-4 and COR-C6-5 to 7 follow the resolve's table; if the resolve's numbering differs from my mapping of the correctness review, the ticket text still carries each change.

## Stub grep (tests/, demos/, P4d.md, P2a.md) for patches of `check_grants`, `refused_statements`, `read_files`, `_scan`
- `tests/test_k2_migrations.py:392`: `monkeypatch.setattr(mig, "check_grants", lambda paths: [])`. ONLY patch. Edited by one line in the ticket.
- Direct calls `mig.check_grants(files)` at `test_k2_migrations.py:33, 63, 66, 73, 80, 86, 90, 96, 321, 327, 333, 345, 405, 410`: no change needed (default `texts=None`).
- `refused_statements`, `read_files`: no hits (do not exist on `ce70eb5`).
- `P4d.md:163`, `P4d.md:184`: copy the one-argument stub pattern; coupling table tells the lead to use `lambda paths, texts=None: []`.
- `P2a.md`, `P4b1.md`, `P4b2.md`, `P4c.md`: mention `check_grants` only as the guard; patch nothing.

## schema_migrations.version primary key
`migrate.py:316-317`: `CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, ...)`. It is a primary key, so a second run of a recipe fails at the ledger INSERT and rolls back; cutting the check block is safe. A hand-made ledger without the key is outside P3a (stated in the ticket, UNVERIFIED for such databases).

## Probes I ran (PostgreSQL 16.15, orchestrator's throwaway server, made-up text, no table written)
- CR/FF/VT: CR and FF are whitespace; VT is not (`SELECT 1<VT>, 2` is a syntax error). The lexer keeps VT in its set (safe direction).
- `U&"set\005fconfig"('application_name','q',true)` returned `q`.
- psql `-f`: `SELECT 1 \g` ran the backslash command mid-line and printed `1`; `\! echo hi` ran a shell command; `:'DBNAME'` was replaced by the database name; an unset `:n` such as `x[1:n]` was left alone (printed `{1,2}`).
- Slip to disclose: my first `bs.sql` probe file had a doubled backslash from a printf escaping error and gave "invalid command \". I reran with a single backslash (checked with `od -c`); only the rerun is used.
- Raw outputs of these probes were seen in my session, not saved as separate evidence files; the ticket's evidence command 7c asks the evidence runner to repeat them on 17.10.

## Extensions and disagreements
- ADV-R6-4: the resolve's "line-start backslash" is too narrow; applied backslash-anywhere (cost: extra refusals, stated in ticket).
- ADV-R6-2: the resolve's whitespace set includes VT; the server does not treat VT as whitespace. Kept as superset.
- Found sibling: `_scan` ends `--` comments only at LF (by reading, not run). Ticket Open point 7: recommend fixing in P3a (one token plus one test, M97 total). Not included in the ticket's scope yet: PENDING LEAD.

## UNVERIFIED
Everything on PostgreSQL 17.10; manual section name for `U&"` identifiers; `Path.glob` listing a dangling link; the TypeError of the unedited stub (reading only); H4 row 2 and the mutant counts (arithmetic by hand, no tool); the `_scan` CR hole; the builder's implementation of anything. No suite, no repository script, no code was run or changed.

Rules cited: bible R337 (class-level fixes), R365 (least privilege; recipe runs as the migration role only).
