# Evidence (independent): lead-repin-verify.sh v2

EVIDENCE RUNNER. Raw outputs only; no judgement, no fixes. Date 2026-11-16 (UTC, about 13:10-13:12; IST = UTC+5:30, so 18:40-18:42).
Script under test: handover/core-hardening/lead-repin/lead-repin-verify.sh
sha256 d8f717587afb673cc1382a4677e5cbc9548c628f4a613eae2eb682fcd7d51fa3 (same bytes were used for the non-root copy).
Doc LEAD-REPIN-VERIFY.md sha256 bbcfac8d811aa18ae14ac75c87a495d2fd49501b71a8afedcd6ae8bc24375078.
Fake secrets: body built from four parts (Qm7d Vt3s Hn8c Xe2b) plus a label; the only literal key is AKIAIOSFODNN7EXAMPLE. No network, no spend.

## What failed, what is uncertain, what was not tested (first)
1. Nothing failed in the checks asked for. 0 canary strings in any output (details below).
2. NOT TESTED: shellcheck (not installed). No take program was run; the dummy is not a git tree, so block R00 only printed "not a git work tree" (the git branch of R00 was not exercised here).
3. The unreadable-file case was tested as user nobody (uid 65534) on a copy of the tree. As root the file is readable, so the root runs show it as read (masked); that is expected, not a defect.
4. Repo "nothing changed" check: other people are editing the repo at the same time (git status gained 3 modified files under handover/core-hardening/steps-edits/ and 1 new file under audit-r460/ between my first and later snapshots). Those are not from this script. So the first before/after pair (listing-before-git-status.txt vs listing-after-git-status.txt) DIFFERS for that reason and is kept only for transparency. The clean test is a 1-second window around 3 script runs (section 4): identical.
5. Observation (not a judgement): with an empty take folder there is no single banner at the top; the loud signals are per line ("<<< 0 FILES SEARCHED", "NOT FOUND by name", "FILE MISSING", "ZERO FILES SEARCHED: nothing was looked at") and the SUMMARY line shows files_missing=22, zero_hits=16. See section 5.

## 1. Checksums and syntax (raw-1-syntax.txt)
- sh -n, bash -n, dash -n: all rc=0 (sh is dash on this machine). shellcheck: not installed.

## 2. Self-test (raw-2-selftest-bash.txt, raw-2-selftest-dash.txt)
- bash: SELF-TEST pass=30 fail=0, rc=0. dash: pass=30 fail=0, rc=0.

## 3. Own dummy tree (path "test_runs/my take" with a space)
Tree contained: scripts/{run_real_check_n8n.py (1114 lines, secrets on lines 1045-1050 and after the end handling), crm_hubspot.py, n8n.py, unreadable.py (mode 000), link.py (symlink to a file outside the tree), long line with secret at column 300}, "sub dir/n8n_drive.py", tests/test_a.py, test_helper.py, node_modules/pkg/x.py, _local/secrets/s.py, flows/f.json, linkdir (symlink to a folder outside), DECISION-one-store.md (secret on line 14). Secret forms: API_KEY=, export MY_TOKEN=, JSON "api_key"/"password"/"token", Authorization Bearer, YAML key with value on next line, YAML block (| ), client_secret quoted, URL user:password@, quoted secret in call, and the literal AKIAIOSFODNN7EXAMPLE. Also a `"method": "DELETE"` line and `key == "end"` / `answer = "end"` lines.

| Run | Command (summary) | rc | Canary fragments in stdout / stderr / saved copy |
|---|---|---|---|
| root, bash | TMPDIR=scratch bash script TAKE | 0 | 0 / 0 / 0 (raw-3-run-root-bash.*) |
| root, dash | same with dash | 0 | 0 / 0 / 0 (raw-3-run-root-dash.*) |
| nobody, bash | setpriv --reuid=65534 ... bash | 0 | 0 / 0 (raw-4-run-nobody-bash.*) |
| nobody, dash | same with dash | 0 | 0 / 0 (raw-4-run-nobody-dash.*) |
| qs_37 probe | qs_37 lines with canaries in take, in node_modules, in the symlinked outside folder | 0 | 0 (raw-5-qs37.stdout) |

Count method: grep for the fragments Qm7d, Vt3s, Hn8c, Xe2b (any one of them) and a regex for the full canary plus suffix, on stdout, stderr and the saved copy (lead-repin-verify-out.txt in the work folder).
- Output of bash and dash on the same tree is identical except the random work-folder name.
- Symlink: the symlink target was NOT read. link.py and linkdir never appear in the output (0 mentions); the file list counted 5 code files (crm, n8n, run_real_check, n8n_drive, unreadable), not 6. The qs_37 recursive search found only the take file (masked: `qs_37 API_KEY=<masked>`), not the symlinked outside folder, not node_modules.
- Excluded folders and files: no mention of node_modules/pkg/x.py, _local/secrets/s.py, tests/test_a.py, test_helper.py in the output. Line printed: "Test files left out of the code search: 2".
- A test_runs parent folder did not stop the search (take files found, 5 searched).
- Unreadable file as nobody: printed "UNREADABLE (not searched, NOT zero matches): .../unreadable.py", counted: "unreadable=1 (1 file(s) UNREADABLE: this count is NOT complete)", SUMMARY files_unreadable=1.
- Long line (over 240 characters, secret at column 300): printed cut at 240 with "...[CUT: this line has N characters; the rest is not shown]"; secret not shown.
- `"method": "DELETE"` stays visible while the secrets before and after it on the same line are `<masked>`; `if key == "end":` and `answer = "end"` stay visible; AKIAIOSFODNN7EXAMPLE stays visible.
- Work folder permissions: 700, saved output copy 600.

## 4. Nothing outside the output folder changed
Method: snapshot (type, mode, size, mtime, path; plus sha256 of every readable file in the dummy and outside folders) immediately before and after running the script 3 times (bash, dash, self-test), 13:11:53 to 13:11:54 UTC.
- Dummy tree: identical before and after (listing-dummy-before.txt vs listing-dummy-after.txt).
- /home/user/hadavin-sdk: 32711 entries (type, mode, size, mtime, path, excluding .git and the evidence folder) plus git status --porcelain: identical before and after (listing-repo-before-window.txt vs listing-repo-after-window.txt).
- The script's only writes are the mktemp work folders under my TMPDIR (permissions 700); it deletes nothing, as its header says. I removed only the folder I made under /tmp (/tmp/repin-ind.*). The script work folders and dummy tree under the session scratchpad were left in place (listed below).
- Earlier pair listing-before-git-status.txt / listing-after-git-status.txt: differs by changes from other writers (see item 4 above), not by this script.

## 5. Zero-file case (raw-6-empty.stdout bash, raw-6-empty-dash.stdout dash)
Empty TAKE_DIR, rc=0 in both shells. Printed:
- `files searched for "python and shell files of the take": 0   <<< 0 FILES SEARCHED: the searches below looked at nothing; check TAKE_DIR / FLOWS_DIR / MODEL_DIR` (also for flow json and model files)
- `TAKE_PY = NOT FOUND by name 'run_real_check_n8n.py' below ... (set TAKE_PY to the real path)` (and CRM_PY, DRIVE_PY, N8N_PY)
- `FILE MISSING (adjust the path): ...` lines and per search `ZERO FILES SEARCHED: nothing was looked at`
- `SUMMARY: blocks=16 with_hits=0 zero_hits=16 files_missing=22 files_unreadable=0`
No top banner line exists; the warning is repeated on many lines (22 lines containing the 0-files wording in the dash output).

## Files in this folder
raw-1-syntax.txt, raw-2-selftest-{bash,dash}.txt, raw-3-run-root-{bash,dash}.{stdout,stderr,rc}, raw-4-run-nobody-{bash,dash}.{stdout,stderr,rc}, raw-5-qs37.stdout, raw-6-empty{,-dash}.stdout, listing-dummy-{before,after}.txt, listing-repo-{before,after}-window.txt, listing-{before,after}-git-status.txt (confounded, see above).
Private scratch (mine): /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ind/ (dummy tree with fake data, script work folders tmp-bash/ tmp-dash/). Not deleted (inside the session scratchpad; contains only made-up data).

## R-numbers
None cited: the bible (studio laptop notes) is not in this repository, so I could not grep it. Preamble rules 5, 6, 12, 19 followed. EGM: EVIDENCE RUNNER, no review done by me. Model: Sonnet 5.5; token use not measured by me.
