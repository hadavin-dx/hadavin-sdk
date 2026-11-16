# flow-check: read-only check of the exported n8n flow files

Nothing here starts n8n. The take uses the **real-v5** flows only (lead decision 2026-11-16): `handover/demo/n8n-flows-real-v5`. The `film-v5` folder is **NOT FOR THE TAKE**; the commands below also work on it but you do not need them.

## Commands (from this folder)
- Check the take flows:
  `python3 -I check_flows.py ../../demo/n8n-flows-real-v5 --baseline ../../demo/n8n-flows-real-v5 --expect mf-form.json=12:11 --expect mf-hook.json=12:11 --expect mf-recovery.json=10:9 --expect mf-sub-crm-mail.json=20:26 --quiet-info`
- Everything at once (patches applied to a scratch copy, 4 checker runs, self-test): `bash run_all.sh` (work folder `/tmp/fc8`, deleted and recreated). Add `--strict` to make still-unreplaced placeholder ids a failure.
- Self-test only: `python3 -I selftest.py ../../demo/n8n-flows-real-v5 <patched real folder> ../../demo/n8n-flows-film-v5` (the last two arguments are optional).
- Code checks: from the repository root, `uv run --all-extras --group test ruff check handover/flows-audit/flow-check`, the same with `ruff format --check`, and `bandit -ll -r handover/flows-audit/flow-check`.

## What each exit code means
| Exit | Meaning |
|---|---|
| 0 | No FAIL line. It does NOT mean the flows are ready, safe to import, or that a password is set on the web addresses. Read the last lines: `OPEN LEAD DECISIONS: n webhook(s) without auth, m $env node(s)`. |
| 1 | At least one FAIL line: a definite fault in a file (or, in strict mode, an open decision the owner chose to treat as a fault). |
| 2 | Wrong command line (unknown option, missing value, unknown patch name). |

Line types: `FAIL` = fault. `WARN` = read it, exit stays 0. `WARN-LEAD-DECISION` = a decision for the lead or owner (no password on a web address, steps that read `$env`); exit stays 0 on purpose.

## Options that turn an open decision into a FAIL
`--require-webhook-auth`, `--block-env-access`, `--require-real-credential-ids`. `run_all.sh` runs the first two in its strict runs; `--strict` adds the third to its default runs.

## Not known (said first)
- n8n was never started; import of these files is untested.
- If the n8n setting `N8N_BLOCK_ENV_ACCESS_IN_NODE` is on, the 2 `$env` steps of real-v5 fail on a default install. Check this on the laptop.
- The allowed webhook authentication values and credential kinds come from memory of n8n, not from a source in this repo.

Details, numbers and every raw output file: `REPORT.md`. Latest fix log: `fix-f8-r3.md`.
