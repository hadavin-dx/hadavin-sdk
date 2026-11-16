# F3 review round 2: egm:egm-codebase-details (agent ae8d39dfab6305959), condensed by flows-audit 2026-11-16
No Blocker, 4 Majors, 7 Nits. Ran nothing; counted 50 tests by hand (Positive 10, Negative 25, Delete 10, Unit 5). All fixes named in fix-f3-r1.md exist; all bypass attempts closed (spaced/optional-chain/bracket tokens, key, list, comment, '$' + 'env.', backslash, U+2028/9, delete outside folder).
| id | sev | where | finding | fix |
|---|---|---|---|---|
| F1 | Major | fill_flows.py:303-306, 383-386 | partial write after os.open succeeded leaves a file not in `created`; re-run blocked; test mocks _write_new before open | unlink own file on BaseException in _write_new; test with a write that raises mid-file; re-run must succeed |
| F2 | Major (test) | test_fill_flows.py:582-587 | symlinked-out-dir assertion vacuous (manifest missing refusal) | also test delete --out link --no-manifest; assert files survive |
| F3 | Major | fill_flows.py:481-486 | delete --no-manifest removes any plain *.json folder | require 0700 folder, 0600 files, current owner (or parse as JSON); test 0644 refused (same as design M1) |
| F4 | Major (test) | test_fill_flows.py:102-108, 340-342 | leak helper checks only static VALS; PATH value 'xyz' unchecked; in-process calls bypass it | cli checks every value written by write_values; distinctive PATH value |
| F5..F11 | Nit | untested cases ($ before env., $env . X, \x85, mode 0o604, comment before token, delete of half-filled folder); README:98 overclaim; check on empty folder exits 0; --out directly inside --in; truncated file needs --force-hash (README); regex literal lexer gap; value starting with '=' | add tests/refusals/README lines |
