# evidence-f3-r3 (EVIDENCE RUNNER: raw results, no judgement)
Run: 2026-11-16 09:23-09:35 UTC (date -u at start: Mon Nov 16 09:23:37 UTC 2026). AWS_* unset, all commands under `timeout`.
Scratch copy: /tmp/evr2/handover/{flows-audit/fill_flows,demo/n8n-flows-real-v5,demo/n8n-flows-film-v5} (relative layout the tests default to). TMPDIR=/tmp/evr2/t. Source in repo untouched.

## 1 Unit tests
`cd /tmp/evr2/handover/flows-audit/fill_flows && python3 -I -m unittest` -> rc=0; "Ran 68 tests in 6.364s / OK".

## 2 Lint
`/tmp/core-venv/bin/ruff check flows-audit/fill_flows --config pyproject.toml` -> rc=0 "All checks passed!"
`/tmp/core-venv/bin/ruff format --check ...` -> rc=0 "12 files already formatted" (12 includes more than the 2 .py files; not investigated).

## 3 Bandit
`/tmp/core-venv/bin/bandit -ll flows-audit/fill_flows/fill_flows.py` -> rc=0; issues Low/Medium/High: 0/0/0.

## 4 README 7-step walk-through, film-v5, made-up values (127.0.0.1 URLs, made-up-* ids)
- 3 fill into filled-1 (no SUB_WORKFLOW_ID): rc=3 "NOT READY TO IMPORT: 3 placeholders left"; "filled 4 files, 3 names and 2 placeholders"
- check filled-1: rc=1 (3 problems, SUB_WORKFLOW_ID in form/hook/recovery) [README only says the fill ends rc 3; check rc 1 is not stated]
- 5 delete filled-1: rc=0 "deleted 4 files, the folder and the manifest"
- 6 fill into filled (with SUB_WORKFLOW_ID): rc=0 "no placeholders left"; check: rc=0 "0 problem(s)"
- delete filled: rc=0.

## 5 Hostile values for MF_STAGE_URL (fill rc / check rc)
double quote 0/0; apostrophe 0/0; backslashes 0/0 (output is valid JSON, value present in escaped JS string); `${x}` 0/0 (written as `${x\u...`, i.e. the `{` is escaped, not literal); `{{x}}` refused rc=1 (values file line 6); `$env.X` refused rc=1; unicode (e-acute, CJK, emoji) 0/0 present; 10 KB value 0/0 present in mf-sub-crm-mail.json; CR char refused rc=1; value with a real newline: second line "b" refused rc=1 "no '='".
Output dir already exists: rc=1 "output folder or its manifest already exists". Output dir is a symlink: rc=1 same message. Output path whose PARENT is a symlink (linkparent/sub): rc=0, filled into the link target (sub + sub.manifest.json created in target). Unwritable parent: ran as uid 0 so chmod 500 does not bind; used /proc/1/nope instead: rc=1 "failed: FileNotFoundError". Output files mode 600, folder 700. No test log contained any value (grep of 10KB/quote values: 0 hits).

## 6 delete --no-manifest
plain folder with mf-form.json + other.txt (mode 755): rc=1 "not marked as this tool's output"; nothing deleted.
Tool-made folder, a file mutated to other VALID json without $env: rc=0, deleted (README says it checks only JSON-parse and $env).
Tool-made, file with `$env` text: rc=1 refused. Truncated JSON: rc=1 refused (needs --force-hash). Extra non-json file: rc=1. Folder mode 755: rc=1. Symlink z.json: rc=1, /etc/hostname intact.
With manifest, file mutated (trailing space): rc=1 "content changed since it was written"; folder kept; then `--force-hash` rc=0 deleted.

## 7 Mutation sample (no mutation script in folder; 13 hand mutants of refusal conditions on copy /tmp/evr2/mut; full unittest each)
KILLED (9): M1 values-file mode mask 0o077->0o070; M2 delete folder mode check !=0o700 -> !=0o777; M3 uid check removed; M4 file mode !=0o600 -> 0o666; M6 `$env` text check off; M9 out-inside-input check off; M10 `$env`-in-value refusal off; M11 /mnt check off; M12 out-folder symlink check off.
SURVIVED (4, full suite stayed OK): M5 line 512 `not S_ISREG` removed (a later mode/uid check may cover it); M7 line 366 manifest-exists refusal removed (`or lexists(manifest_path)`); M8 line 364 `inside_git(out_dir)` removed (parent check remains); M13 line 541 manifest-is-symlink check removed.
Source restored (mut copy only; repo file untouched). Only this file written in the repo.
