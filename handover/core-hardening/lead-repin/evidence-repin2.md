# Evidence note: lead-repin-verify.sh v2 (Mon 16 Nov 2026, about 13:20 UTC / 18:50 IST)
Written by the builder. Raw output: `raw-dummy-run2.txt` in this folder. No real take program was available, so nothing here shows the script is right about the real files.

## Failures and gaps first
- The script was never run against the real take repo, flows or model program. Search words are guesses.
- The unreadable-file branch only works for a non-root user (root can read everything). I ran it once as uid 65534 in a throwaway folder under /tmp (the scratch folder is mode 700 and not reachable by that user); I deleted that throwaway folder myself. That run (RUN 3) used the script just before one wording change in the unreadable message ("missing-type errors" became "UNREADABLE"); the changed wording was syntax-checked but not re-run.
- First dummy run of this pass found 2 bugs in my own v2 draft, fixed before the evidence below: (1) a JSON line `{"api_key": "...", "nodes": [{"method": "DELETE"}]}` lost the DELETE text, because the generic mask hid the rest of the line after a masked key; fixed by hiding a quoted value alone; (2) `qs_37` was not found when a folder name held a space (unquoted loop); fixed by quoting each folder.
- Not run: macOS, busybox, Windows shells, WSL detection. The `ss` branch was not exercised (this machine has no ss and no netstat); the /proc/net/tcp fallback ran and printed "none of those ports is listening".
- bash and dash print identical output (0 differing lines, work-folder name normalised).

## Commands and results
1. `sh -n`, `bash -n`, `dash -n` on lead-repin-verify.sh: all three printed no error (final file, after the last edit). shellcheck is not installed.
2. `sh lead-repin-verify.sh --self-test`: `SELF-TEST: pass=30 fail=0` (30 checks: 19 hidden-secret forms, 11 kept-evidence checks; fake secrets built from parts; the only literal key is AKIAIOSFODNN7EXAMPLE, which is shown unmasked on purpose).
3. Mutation check of the self-test: same script with the v1 mask rule swapped in: `pass=11 fail=19`. So the self-test fails on the old rule.
4. Dummy run (dash as sh) on `repin-dummy2/test_runs/take dir/` (path with a space and a `test_runs` segment): 7 code files searched (not 0), `tests/`, `node_modules/`, `_local/` left out and counted; the files were found by name under `scripts/`; the file `spaced name.py` was searched; fake secrets in JSON, `Authorization: Bearer`, `API_KEY =`, YAML next-line and YAML block forms: the count of the secret fragment in the output is 0 (`grep -c Zq9x raw-dummy-run2.txt` printed 0); `"method": "DELETE"` stays readable; `if key == "end":` stays readable; `qs_37` found in `tests/test_x.py`; settings names printed without values (`WINDOW_END`).
5. Same dummy run with bash: 0 differing lines against dash.
6. Git work tree variant: `HEAD`, changed-file count 1, last commit printed. Before and after one run the `.git` folder was compared (file names, modification times, sizes, sha256 of the index): identical.
7. Unreadable file (RUN 3, uid 65534): `UNREADABLE (not searched, NOT zero matches)` printed, the search line says `unreadable=1` and `ZERO HITS`.
8. Banned vendor words from the BANNED tuple of tests/test_no_reference_material.py scanned over the files in this folder with an inline regex check: count 0.
9. Secret scan: the fake secret fragment count in raw output is 0; no AKIA-shaped id other than the example in any file here.

## Not shown by this evidence
That the mask rules hide every real secret shape (it hides the shapes listed in the script header; the lead reads the output before sharing it); that the default search words match the real names; behaviour on a real take repo.
