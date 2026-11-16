# C3 paste check: ROUND 1 RESOLUTION (2026-11-16, supersedes the patch description below)
Two independent reviewers found 5 Major, 6 Nit each; all fixed in the regenerated patch plan-v5-fixes.patch (dry run output with rc=0 saved in patch-dryrun.txt).
- Fix 1 (PowerShell): the switch exists from PowerShell 6, not 7. Now a plain step with an expected output (6 or higher), STOP on 5; the 5.1 replacement is labelled UNVERIFIED.
- Fix 2 (listener count): one regex that checks 127.0.0.1 for the six fixed ports and any address for 55433 (the earlier form dropped the loopback check).
- Fix 3 (placeholder): no longer a runner substitution (it contradicted rule R5, verbatim code). The literal prefix text is written into the five places; syntax check of the PATCHED plan: the same extractor run on a scratch copy of the patched plan, saved as evidence-c3c.md and spans-index-patched.tsv: 161 spans, the new spans 0.1b, 0.1c, the S13 prefix, 13.1, 13.3, 13.8, 13.9 all have bash -n 0 and dash -n 0; the 19 non-zero rows are the same placeholder or bare '&' fragments as before (12 of them in plan lines 108-112); python spans 0 failures.
- Fix 4 (grep -RhoF) reverted: no evidence it is needed.
- Added to the patch: 0.1b line-ending scan with missing-path guard, 0.1c data-shape check, UNVERIFIED 13, note that UNVERIFIED 2 is partly stale.
- Inline spans now covered: evidence-c3b.md, 158 spans: 0 real failures; 11 fail only because of placeholders (<folder>, <pid>, <n>, <step> <log>) or bare '&' fragments; with placeholders filled 2 fragments remain (plan lines 112). Python spans: 8 compiled, 0 fail. The 7 PowerShell spans are only placeholder-scanned (no pwsh here).
- Still not run: pwsh, shellcheck, n8n, Docker, WSL. Round 2 Major: <folder>, <pid>, <block> and the new <the same log path> were undefined and line 241 said <n> was the only value the runner fills in; the patch now rewrites that sentence and defines all four (lead fills them by hand). Round 2 reviewer read files only and ran nothing.

# C3 paste check of plan-wp6-resmoke-v5.md (2026-11-16, core-hardening)

## What failed or is uncertain (first)
- NOT RUN: shellcheck (not installable here), pwsh (not installed), n8n, Docker, WSL. Every PowerShell finding below rests on reading only.
- Only the 14 FENCED blocks were extracted. The many one-line pastes written inline in backticks (steps 0.2 to S13) were only partly covered: the runner compiled 8 inline Python spans (e05-e12, exit 0) but the inline shell spans were read by the reviewer, not syntax-checked by a tool. Gap: a second extraction of inline shell spans is still needed (next step: the runner pulls every inline span that starts with `. $HOME/hadavin-smoke/env.sh` and runs `bash -n`/`dash -n`).
- Block 14 (step 13.4) fails `bash -n` and `dash -n` (exit 2). Cause: line 1 starts with the plan's shorthand `<prefix>;` (defined at plan line 409). It is a real hazard because plan rule R5 says to write code verbatim: Fix 3 below.
- Result review round 1 only: design reviewer (reads the plan) done; second reviewer not yet run on this report.

## Evidence (raw: evidence-c3.md, blocks-index.tsv)
| block | step id | plan lines | lang | bash -n | dash -n | python compile |
|---|---|---|---|---|---|---|
| 1 | 3 env-resmoke.sh | 133-161 | sh | 0 | 0 | n/a |
| 2 | 3 ctl.sh | 165-171 | sh | 0 | 0 | n/a |
| 3 | 3 sampler.sh | 174-188 | sh | 0 | 0 | n/a |
| 4 | 3 egress.py | 191-210 | python | n/a | n/a | 0 |
| 5 | 3 run.sh | 213-219 | bash | 0 | 0 | n/a |
| 6 | P-2 | 233-237 | powershell | not run | not run | not run (read only) |
| 7 | 0.1 | 245-254 | sh | 0 | 0 | n/a |
| 8 | 1b.2 | 280-283 | sh | 0 | 0 | n/a |
| 9 | 1b.3 | 286-292 | sh | 0 | 0 | n/a |
| 10 | 8.4 | 326-328 | sh | 0 | 0 | n/a |
| 11 | 11.1b | 347-352 | sh | 0 | 0 | n/a |
| 12 | 11.2 | 355-371 | sh | 0 | 0 | embedded python exit 0 |
| 13 | E.1 | 380-396 | sh | 0 | 0 | embedded python exit 0 |
| 14 | 13.4 | 414-416 | sh | 2 | 2 | n/a |
Error text block 14: `<prefix>;` is not valid shell (syntax error near `;`). All embedded Python programs (e01-e12) compile, exit 0. Compile only proves syntax, not behaviour.

## Findings from the independent reader (egm design reviewer, plan read in full; no Blocker)
Major (all fixed by the patch or the insert text below):
1. Plan line 112 wrapper `Tee-Object -Append` does not exist in Windows PowerShell 5.1 (added in 7); 5.1 also writes UTF-16 that WSL `grep -a` scans cannot read. Blocks P-2, P-5, 9.0k, 11.0k, 13.5k, 13.9 tail. FIX 1 in patch.
2. Listener count regexes differ: 1b.1 counts `:55433` on any address, S10 (line 340) and 11.1 (line 345) count only `127.0.0.1:...`. A Docker relay on another address gives a false STOP. FIX 2 in patch (drop the address from the count; add a separate check that the other ports are on 127.0.0.1, text below).
3. `<prefix>` placeholder in S13 pastes (13.1, 13.3, 13.4, 13.8, 13.9). FIX 3 in patch.
4. The CR (carriage return) scan covers only the glue files, not files extracted from the two tars; `git archive` line endings on Windows are not confirmed. Insert after step 0.1: `grep -rlP '\r$' $R/nlite/scripts $R/demo/handover/demo/n8n-mainframe $R/demo/handover/demo/n8n-tests $R/drive.py $R/fill_flows.py; echo "cr-scan done"` -> nothing listed before `cr-scan done`; any file listed = STOP. Also: P-1 runs through `run.sh` before P-3b can scan it: run P-3b by hand first.
5. Steps 11.3, E.2 and 11.1b assume data shapes nobody read: a numeric epoch `t` in `crm.log.jsonl` and `mail.jsonl` (cited only for `crm_stub.py`), and the key `replies` in the driver's last JSON line. Add UNVERIFIED item 13 and an extra 0.1 check: `grep -nE "time[.]time|\bt=" $R/demo/handover/demo/n8n-tests/smtp_catcher.py $R/demo/handover/demo/n8n-mainframe/crm_stub.py; grep -n "replies" $R/drive.py` (both must print).
Nits: 1.3 use `grep -RhoF` (FIX 4 in patch); 0.2 add `ps -o pid=,args= -p $(cat $T/sampler.pid)`; 13.7 say that `pastes/13.7.sh` holds both commands in order; 13.5 only a line starting with `bash` and ending in `P-5.sh` counts; E.2 HIT does not prove the 8 s hold applied; P-5 print `Start-Sleep 5; (Get-Process -Id $k.Id -EA SilentlyContinue) -ne $null` expect True; P-2 add "empty tar commit id = STOP"; `gone` reads only stdout of `n8n_kill.py`.
Unreadable pass lines: 0.1, 4.2 and 2.2 print bare counts: prefix each command with `echo "label:"`.
Not decidable without files that are not here: `drive.py`, `n8n_kill.py`, `smtp_catcher.py` output shapes, PowerShell behaviour, n8n 2.46.6, Docker Desktop relay address.

## Patch
`paste-check/plan-v5-fixes.patch` (unified diff, `patch -p1` from the folder that holds `inputs/`). Dry-run on a pristine copy of the plan: applies cleanly. Covers FIX 1, 2, 3, 4 only; items 4 and 5 and the nits are given as insert text above because they add new lines (the lead decides where). Not run against a real re-smoke.

## Critical path
Fix 1 (PowerShell 7 check) and Fix 3 (`<prefix>`) block the first PowerShell step and the clean-up, so they come before the run; Fix 2 only causes a false STOP at S10/11.1; the data-shape checks (5) are needed before 11.3.

## Rule lines used
Honest reporting; CODE-LAST (no new code proposed, only text edits to a plan); plan wording rule. The bible is not on disk here.
