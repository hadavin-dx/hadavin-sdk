# NOTES: tests that fail when demo_only/ is deleted (patch nodemo-fix.patch)

Rules used: the repo's own rule (deleting demo_only/ must leave build and tests green; that is how a client copy is cut). Studio rules R6 (failures first), R7 (class-level fix, siblings, old-code proof), R19 (one process at a time). Not an EGM-reviewed change: this is a small test-only edit; the lead runs the EGM step.

## What failed (measured, plain db54e13 copied, demo_only/ deleted)
Chunked run of all 81 test files (9 chunks, one pytest at a time): 867 passed, 74 skipped, **6 failed**. All 6 are in `tests/test_except_clause_hierarchy.py` (FileNotFoundError on demo_only/fake_imap.py and demo_only/fake_smtp_tls.py): 2 files x 3 tests (handler order, no class named twice, shortened clause still catches). No other file fails. evidence-nodemo-1-before.txt, evidence-nodemo-6-chunked-before.txt.

## Why the siblings are not failing
tests/conftest.py already skips, as ONE item, every test FILE that imports demo_only, support, edge_case_helpers or another test_*.py, or that takes the `env` fixture. This file imports none of them: it reads the demo files with `Path.read_text`, so the guard missed it. I grepped tests/ for 'demo_only' and for `/demo/` (those are URL paths, not files), and ran the whole suite without the folder: the only un-skipped file that reads a demo file directly is this one. test_env_numbers.py, test_vendor_hosts.py and test_clock_steps.py also name demo_only/, but only inside folder lists that they glob (absent folder = nothing to scan; they pass, 354 and 6 items ran). Docs/src: src/ names demo_only only in loader.py (guarded by test_hygiene). No demo/ folder or docs file is read by a test.

## Fix (generic, small): tests/test_except_clause_hierarchy.py, +16/-4 lines
A helper `_present(rows)` turns each parametrize row into `pytest.param(..., marks=skipif(not (REPO/row[0]).is_file()))`. The three parametrized tests use it. Rows about src/ and load_tools/ are never skipped. When demo_only/ is there the six rows run exactly as before. The 6 rows show as 6 named skips (reason "demo_only/fake_imap.py: demo_only/ was removed"), not one silent drop.

## Proof
| rung | result | file |
|---|---|---|
| fails before: db54e13, demo_only/ deleted, that file | 6 failed, 43 passed | evidence-nodemo-1-before.txt |
| after, same tree + patch, chunked whole suite no-demo | **0 failed**, 867 passed, 80 skipped | evidence-nodemo-7-chunked-after-A.txt |
| after, demo_only/ present (DPLD_REQUIRE_DEMO=1), 4 affected files | 110 passed; the 6 demo rows PASSED | evidence-nodemo-3-demo-present-after.txt |
| mutant, demo present: edit the fake_imap.py handler | 2 failed (still checks the demo file) | evidence-nodemo-4-mutants.txt |
| mutant, demo deleted: edit smtp_outbox.py handler | 1 failed (product rows still checked) | same file |
| apply check | applies on db54e13 alone; on db54e13+P1v2+P2+P3 together; on each of P1v2, P2, P3(v1), P3-v2 alone | evidence-nodemo-2-apply-check.txt |
| gates ruff check, ruff format --check, mypy linux, mypy win32, bandit -ll | all clean, on db54e13+patch and on the stack | evidence-nodemo-5-gates.txt |
Not run: the full suite WITH demo_only/ (the lead runs it); a Windows run; gitleaks history scan (DPLD_REQUIRE_SCAN was not set for the demo-present run of test_hygiene).
No-demo run set-up: venv with playwright; browser tests that need the demo skip anyway, so browsers were not exercised.

## Line for RUN ON LAPTOP (no-demo)
`demo_only/ deleted, chunked 9 x pytest on db54e13 + nodemo-fix.patch: 0 failed, 867 passed, 80 skipped` (74 of the skips are whole-file or single-item demo skips from conftest, 6 are the new named rows; 13 of the 81 files run in full in a client copy).

## Optional second patch: nodemo-optional-hygiene-repo.patch (decision for the lead)
Finding, not a failure: tests/test_hygiene.py and tests/test_no_placeholders.py use `from support import REPO` only for the repo path, but `support` imports demo_only, so in a client copy both whole files are skipped: the portal "no demo words" scan, the no-demo_only-outside-loader rule, the gitleaks pattern scans and the placeholder scan never run exactly where they matter. The optional patch computes REPO from `__file__` (2 lines per file). Built on db54e13+P1v2+P2+P3 (it does NOT apply on db54e13 alone: P1v2 edits the neighbouring import lines). test_gitleaks_exceptions.py still skips because it imports test_hygiene (conftest rule); left alone.
Result with it, no-demo chunked run of the stack (evidence-nodemo-7-chunked-after-B.txt): 937 passed, 1 failed, 79 skipped. The 1 failure, `test_hygiene_scan_public`, is NOT caused by this work: it also fails on that stack WITH demo_only/ present (evidence-nodemo-8-...): the literal scan flags `tests/test_sonar_p2_choke_points.py:202 desk.corp.` and `:224 169.254.169.254` (from P2 v1; P2 v2 is being rebuilt elsewhere, so that line needs checking against it). Without the optional patch the failure is hidden in a client copy; with demo present it already shows.

Files: sonar/nodemo-fix.patch (main), sonar/nodemo-optional-hygiene-repo.patch, NOTES-nodemo.md, evidence-nodemo-1..8. Nothing pushed; no network writes. Process hygiene: all my pytest runs finished; no background process left.
