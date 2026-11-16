# fix-f8-r8 (FIXER log; made-up data only; nothing ran in n8n)
Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-f8r8/ (selftest.py, run_all.sh, check_flows.py). check_flows.py NOT changed (no real bug found).

## Failures and unfixed items first
- ruff check / ruff format --check over the whole flow-check folder still report problems ONLY in raw-e7/mutants/mk.py (the evidence runner's file, not mine, not deleted). My two files are clean (ruff check selftest.py check_flows.py: All checks passed).
- Installed ruff differs from the repo pin (evidence-f8-r7 noted 0.16.9 vs 0.17.1); not re-checked by me.
- selftest-output/ in git still holds the old committed content (not regenerated); it is no longer rewritten by a run.

## Changes
1. selftest.py: new mutator g_extra_conn + case `wrong_count_more_connections` (one extra link to an already linked node, expected counts kept from the unmutated file, must FAIL with "connection count"). 4 real files, cases print as expected.
2. selftest.py: new unit case `r8_value_is_safe_rejects_no_block_and_non_reference_block_and_accepts_a_reference` (values "abc", "={{ $env.SOME_NAME }}", "={{ foo.bar }}", "={{ $json.a }}{{ foo.bar }}").
3. Output folder: selftest.py default OUT is now a new temp folder (path printed on the line "case output folder:"); the committed selftest-output/ is rewritten only when FC_OUT names it. run_all.sh passes FC_OUT="${FC_OUT:-$W/selftest-out}" (inside its own work folder). After bash run_all.sh, git status shows 0 selftest-output changes.

## Mutant proof (copies in scratchpad mut8/, live files untouched)
- N04 (check_flows.py:1200 `!=` -> `<`): selftest 503 ok, 4 NOT AS EXPECTED (all four wrong_count_more_connections cases, rc=0 named=0). Live: all pass.
- N11 (check_flows.py:604 `or` -> `and`): selftest 506 ok, 1 NOT AS EXPECTED (the r8_value_is_safe case, got all True). Live: passes.
## M10 (take_check.sh:64, dropping `|^WARN accept-no-save`)
Read and reproduced: equivalent today. The checker's accept-no-save WARN text (check_flows.py:1824) contains "its run-saving settings are not off", so the first alternative `^WARN .*run-saving settings` already matches it (checked with grep: count 1). Full run_all.sh on a mutated copy: rc=0, selftest 668/0, take_check none missing, and the tcfail recovery-accept-idle case still exits 4. It would stop being equivalent only if that message text lost the words "run-saving settings".

## Gates (live folder, own exit codes)
- bash run_all.sh: rc=0; SELFTEST: 668 as expected, 0 not as expected, 62 skipped; take_check.sh exit=0 missing lines: none
- ruff check (selftest.py, check_flows.py, repo config): rc=0
- ruff format --check (these two files): clean after `ruff format` on selftest.py; whole folder rc=1 only because of mk.py
- bandit -ll -c pyproject.toml check_flows.py selftest.py: rc=0
- sh handover/flows-audit/tools/check_patches.sh: rc=0, PASS 4 patches
