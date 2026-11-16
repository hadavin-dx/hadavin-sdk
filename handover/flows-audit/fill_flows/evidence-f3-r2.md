# Evidence F3 round 2 (raw, no judging)
Date 2026-11-16. Python 3.13.18, ruff from /root/.local/bin. Files under test copied unchanged to a scratch dir (tests expect ../../demo, so the copy holds handover/flows-audit/fill_flows + demo). Originals never written.

## 1. Full suite twice: python3 -I -m unittest
run1 exit=0
----------------------------------------------------------------------
Ran 50 tests in 4.175s

OK
run2 exit=0
----------------------------------------------------------------------
Ran 50 tests in 3.835s

OK

## 2. Classes alone (python3 -m unittest test_fill_flows.<Class>; with -I the module name is not importable, rc=1 ImportError, so -I was dropped for these)
Positive exit=0: Ran 10 tests in 0.840s  OK 
Negative exit=0: Ran 25 tests in 2.040s  OK 
Delete exit=0: Ran 10 tests in 0.911s  OK 
Unit exit=0: Ran 5 tests in 0.070s  OK 
Reversed order (Unit Delete Negative Positive) exit=0: Ran 50 tests in 3.930s  OK 

## 3. Lint (repo pyproject, line-length 100)
ruff check --no-cache fill_flows.py test_fill_flows.py -> All checks passed! (exit 0)
ruff format --check --no-cache ... -> 2 files already formatted (exit 0)
(Run in a copy outside the repo, without the repo pyproject, ruff reports 2 RUF100 and wants reformatting at width 88; not the repo config.)

## 4. End to end (made-up values; values file mode 600; output under scratch /tmp, outside any repo)
Values: DESK_URL=http://127.0.0.1:9123 DESK_TIMEOUT_MS=2750 DESK_ALERT_TO=ops-x@example.invalid MF_CRM_URL=http://127.0.0.1:9456 MF_STAGE_TIMEOUT_MS=3150 MF_STAGE_URL=http://127.0.0.1:9789
```
fill real-v5: exit 0; 'filled 4 files, 3 names and 0 placeholders'; 'NOT READY TO IMPORT: 23 placeholders left'; 3 key-unused warnings (MF_* keys)
check: exit 1, '4 files, 23 problem(s)' (all placeholders); check --tokens-only: exit 0, '0 problem(s)'
nodes in/out: form 12/12, hook 12/12, recovery 10/10, sub-crm-mail 20/20; connections equal: True x4; $env left in output: 0 (input had 3)
modes: out dir 700, 4 files 600, manifest 600; value strings in fill stdout/stderr: 0 lines
fill film-v5: exit 0; 'filled 4 files, 3 names and 0 placeholders'; 'NOT READY: 19 placeholders left'; check exit 1 '19 problem(s)'; --tokens-only exit 0; counts same 12/12/10/10, connections equal, $env left 0, modes 700/600/600, leak 0
delete --out out-real: exit 0 'deleted 4 files, the folder and the manifest'; folder and manifest gone
crash sim (film): manifest removed by hand; delete --out -> exit 1 'refused: manifest is missing; nothing deleted (... use --no-manifest ...)'; delete --out --no-manifest -> exit 0 'deleted 4 files, the folder and the manifest'
no-manifest with extra note.txt in folder: exit 1 'note.txt: not a plain .json file; nothing deleted' (folder kept)
```

## 5. Hostile inputs (fill on real-v5 unless noted; secret marker SeCrEt-v4lue-zz9; leak = lines of stdout+stderr containing any value)
```
case            exit leak out_created  refusal text
quotes           1    0    no   value of DESK_URL starts or ends with a quote mark
trailing space   1    0    no   value of DESK_URL has a space at its start or end
BOM              1    0    no   values file starts with a BOM
inside repo      1    0    no   values file is inside a git repository (fake repo with .git dir in scratch)
/mnt path        1    0    no   values file is under /mnt (path /mnt/nonexistent-ff/e.env; the file did not exist: refusal came from the path check, not from a read; not retried with a real file under /mnt because creating and removing there was blocked by a safety check)
mode 644         1    0    no   values file can be read by other users
value with {{    1    0    no   value of DESK_URL contains '{{' or '}}'
control (good)   0    0    yes  (sanity)
token in quoted JS string (double-quoted in expr)  1 0 no  a $env token sits inside a quoted JS string in an expression
token in quoted JS string (single-quoted in expr)  1 0 no  same message
token in jsCode field                              1 0 no  a $env token sits in a jsCode field
```

## 6. Mutation sample (each mutant = copy of fill_flows.py with one edit, full suite python3 -I -m unittest; baseline copy: 50 tests OK)
```
mutant                        suite result            failing tests
remove leftover scan          FAILED (failures=1)     Negative.test_dynamic_env_use_refused
ignore missing key            FAILED (failures=4)     test_empty_value, test_leftover_token_unknown_name, test_missing_key, Unit.test_token_forms
output files mode 0644        FAILED (failures=2)     Delete.test_manifest_has_no_values, Positive.test_real_and_film
print value in refusal text   FAILED (failures=1)     Negative.test_bad_values (only the quote-refusal was mutated)
drop the {{ value check       FAILED (failures=1)     Negative.test_bad_values
manifest written after files  FAILED (failures=1)     Negative.test_failed_write_removes_everything_and_manifest_goes_first
```
Survivors: none of the 6. Not covered by this sample: the other refusal texts that could print a value (only the quote-refusal was mutated); the 60-mutant sample was not run.
