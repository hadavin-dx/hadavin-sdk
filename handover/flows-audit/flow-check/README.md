# flow-check: read-only check of the exported n8n flow files

Nothing here starts n8n. The take uses the **real-v5** flows only (lead decision 2026-11-16): `handover/demo/n8n-flows-real-v5`. The `film-v5` folder is **NOT FOR THE TAKE**; `run_all.sh` still runs it, in a separate block that never changes the exit status and is never added to the real-v5 numbers. Needs **Python 3.10 or newer** (the checker says so and exits 3 on an older one).

## OPEN LEAD DECISIONS (read these first)
1. **Two web addresses have no password** (`mf-form`, `mf-hook` in real-v5). Exit 0 does NOT mean authentication was checked.
2. **Two steps read environment variables** (`AlertSend` in `mf-recovery`, `Qualify` in `mf-sub-crm-mail`). If the n8n on the filming machine blocks environment-variable access inside steps, they stop working. **No static tool can see that n8n setting** (it belongs to the running n8n, not to the flow files; its name is also not verified here). Check it on the filming machine. To see which steps depend on it, add `--block-env-access` (exit 1 expected today).
3. **Two yes/no steps lack a second branch** (`StuckRow`, `AlertRow` in `mf-recovery`). This is recorded as an accepted decision (`--accept-if`, see below), not hidden.

## Commands (from this folder)
- **The take check** (prints the open decisions first, then the full output; exit status = the checker's): `bash take_check.sh`
  It runs: `python3 -I check_flows.py ../../demo/n8n-flows-real-v5 --accept-if mf-recovery.json=StuckRow:1 --accept-if mf-recovery.json=AlertRow:1 --expect mf-form.json=12:11 --expect mf-hook.json=12:11 --expect mf-recovery.json=10:9 --expect mf-sub-crm-mail.json=20:26 --expect-credential postgres=n8n-publish-pg --expect-credential smtp=mf-mail-smtp --expect-credential hubspotAppToken=hubspot-app-token --quiet-info`
- Everything at once (patches applied to a scratch copy, 11 checker runs, self-test): `bash run_all.sh`. Its exit status and its last line are about **real-v5 only**. The scratch folder is made with `mktemp` and removed at the end. Add `--strict` to make still-unreplaced placeholder ids a failure.
- Self-test only: `python3 -I selftest.py ../../demo/n8n-flows-real-v5 <patched real folder> ../../demo/n8n-flows-film-v5` (the last two arguments are optional).
- Code checks: from the repository root, `uv run --all-extras --group test ruff check handover/flows-audit/flow-check`, the same with `ruff format --check`, and `bandit -ll -r handover/flows-audit/flow-check`.

## What each exit code means
| Exit | Meaning |
|---|---|
| 0 | No FAIL line. It does NOT mean the flows are ready, safe to import, or that a password is set on the web addresses. Read the closing block: `OPEN LEAD DECISIONS: n webhook(s) without auth, m $env node(s)`. |
| 1 | At least one FAIL line: a definite fault in a file (or, with the options below, an open decision treated as a fault). |
| 2 | Wrong command line (unknown option, missing value, unknown patch name). |
| 3 | The checker itself broke, or it could not write its `--diff-out` file. This is never a verdict about the flows. |

Line types: `FAIL` = fault. `WARN` = read it, exit stays 0. `WARN-LEAD-DECISION` = a decision for the lead or owner (no password on a web address, steps that read the environment); exit stays 0 on purpose.

## Rules that come from memory of n8n (tag `n8n rule UNVERIFIED`)
No source in this repository backs these: the allowed webhook `authentication` values (webhook: none, basicAuth, headerAuth, jwtAuth; form trigger: none, basicAuth), the credential kind each needs, the credential kinds of postgres, smtp and hubspot steps, the position of the error output, the default `responseMode`, and "two webhooks may not share method+path or webhookId" (compared across **all folders given in one run**, form triggers included). They are **WARN** by default. `--fail-unverified` makes them FAIL. Import into n8n is the real test.

## Options that turn an open decision into a FAIL
`--require-webhook-auth`, `--block-env-access`, `--require-real-credential-ids`, `--fail-unverified`. `run_all.sh` runs the first two in its strict runs; `--strict` adds the third to its default runs.

## What `--accept-if` and `--baseline` do (said loudly)
- `--accept-if FILE=NODE:OUT` records one decision: this yes/no step of this file is accepted to lack exactly this output (0 or 1). It prints as a WARN, counts as a known open problem and is listed in the closing block. Any other missing branch is a FAIL. **The take check uses this.**
- `--baseline DIR` compares with a folder of the unpatched flows: a yes/no step that already lacks the same branch there is only a WARN. **If you point it at the folder you are checking, it excuses EVERY missing branch in that folder, now and in future. Do not do that.** (Round 3 did; round 4 removed it from the take command and from `run_all.sh`. `selftest.py` still uses it against a copy.)
- Without either option, the two gaps are FAIL: `raw/pristine-no-baseline.txt` (written by `run_all.sh`, exit 1, 2 FAIL).

## Not known (said first)
- n8n was never started; import of these files is untested.
- Whether n8n blocks environment-variable access inside steps on the filming machine: not visible to any file check.
- Every rule tagged `n8n rule UNVERIFIED` above.
- Who calls a web address, whether a flow is active, and test versus production web address: not checked.
- `run_all.sh` and `take_check.sh` have no test of their own; their numbers come from running them.

Details, numbers and every raw output file: `REPORT.md`. Latest fix log: `fix-f8-r4.md`.
