# v4 changes: finding -> change -> test that proves it (16 Nov 2026, times UTC; IST = UTC + 5:30)

The findings are the ones named in the lead's brief for v4 (ids M6, M7, M9, M10, D36, D39, D54, D65, D88, N6, N7 as the brief gave them; the review files themselves were not given to me, so every other row names the finding by its description). "Self-test case" means a case printed by `sh lead-repin-verify.sh --self-test`; "evidence" means a file in `evidence-repin4/`. Result at the final file: `--self-test` 299 passed, 0 failed, under dash and bash (evidence 03). Nothing here was run against a real take program. Independent review has NOT been done; this table is the builder's claim.

| Finding | Change in v4 | Test that proves it |
|---|---|---|
| Leak: bare base64 or long opaque blob | second masking stage (awk): any word of 24+ letters/digits with a letter and a digit is replaced by `<masked-blob>` (sha256, 40-character git ids, UUIDs and camel-case names are kept) | self-test cases "blob", "sha256 kept", "UUID kept"; evidence 02 (3 blob lines masked) |
| Leak: mixed-letter word | awk: mixed upper/lower/digit words of 12+ characters hidden (`<masked-token>`) | case "mixed token"; evidence 03 (0 of `Vq7Lm2Xp9Rt4`) |
| Leak: secret in a trailing comment, prose lines | name rules now match mid-line `name: value`, "the password is v", `# ... name = v` | cases "trailing comment", "prose" |
| Leak: `curl -H "X-Auth-Token: v"`, `-H 'Authorization: token v'`, `curl -u` | new header and flag rules | cases "curl X-Auth-Token", "curl Authorization token", "curl -u"; evidence 02 |
| Leak: `ENV TOKEN v`, `passwd "v"` | new rules | cases "ENV no equals", "passwd quoted"; evidence 02 |
| Leak: plural names (API_KEYS, PASSWORDS, AUTH_TOKENS); tokens secret unless a counter | name words accept the plural; counters (max_, num_, total_, prompt_, completion_, input_, output_, cached_, reserved_ + tokens) are kept | cases "plural names", "token counters kept" |
| Leak: `path:NN:` prefix | every line rule accepts the grep prefix `path:12:` / `path-12-` | cases "path prefix" (sed alone and whole filter) |
| Leak: nested, array, pretty-printed JSON and YAML, value on next line | awk hides secret-named containers to the matching bracket (carry at most 100 lines) and pairs of lines (`name:` then `value:`); sed hides YAML next line; sed no longer eats a `[`/`{` opener so awk can hide the whole container (found by the first self-test run) | cases "JSON array over several lines", "nested object", "pretty-printed name/value", "YAML next line" |
| Leak: escaped quotes, adjacent strings, PEM, `sk_live_` | JSON string pattern allows `\"` and several strings in a row; PEM block rule; `sk_live_` shape | cases "escaped quote", "two strings in a row", the private-key block cases, "sk_live" |
| Leak: JWT | shape rule `eyJ...` | case "JWT" (lowercase parts, so the generic blob rule cannot hide it); mutant m1 killed (evidence 06) |
| Default-deny for Q27b value printing | settings values shown only if date or number shaped (`val.awk`); any other value replaced by a note | by reading the code and the main run: MODEL_SETTINGS was not set in the main run, so this branch was NOT exercised on a settings file (UNVERIFIED, see below) |
| M7 / locale: `LC_ALL=C`, `grep -a` | `LC_ALL=C` exported at the start; every grep uses `-a`; `tr '\000' '?'` before sed | cases "0xE9 byte line", "NUL byte line" |
| Printed lines against the count | after each search the script counts printed `NN:` lines against grep's count and prints `PRINT MISMATCH` | main run: summary prints the number of mismatching searches (0); NOT forced to show a mismatch (UNVERIFIED that the alarm fires) |
| M7 "match word hidden" report | per search: line numbers where the searched word is not visible in the printed line (`MATCH WORD HIDDEN`) | main run on the made-up tree prints it (114 lines in evidence 08, from a hidden triple-quote block) |
| M9 `_local` flows as file:line:word | `grep -a -n -o` through the masking filter; prints at most 50 lines | by reading the code; the made-up tree has no `_local` flow json (count 0), so UNVERIFIED |
| M6 DELETE_RE `delet` over all four named files; skipped file types | default `delet\|archiv\|purg\|remov\|trash\|gdpr\|clean.?up\|unlink\|rmtree\|method...(delete\|patch)`; Q23-4 searches all four named files; skip report counts every other file type | main run block Q23-1 / Q23-4 (evidence 08) |
| Maxdepth wording | text says "path of 5 or more parts (a/b/c/d/file)"; doc has a section "How deep the search goes" | reading |
| Canary: SELFTEST_FILTER only in `--self-test` | unset at start unless the mode is `--self-test` | self-test machinery check "identity filter (cat) makes --self-test fail" |
| Canary in `--mask` too | `--mask` runs the canary before reading input | machinery checks "--mask hides the value" and "--mask with a damaged filter prints nothing, exits 3, leaves no folder"; mutant m5 killed |
| Canary cases: JWT, new forms, 0xE9 byte, case 17 fixed, abort path | see the leak rows; case 17 split into a 200-character pad and a straddle case at 228; abort-path tests in the machinery checks | self-test output (evidence 03) |
| The 3 mutations v3 missed (JWT rule dropped; filter_ready always OK; self_test always 0 / abort disabled) | JWT case; `filter_ready` is itself tested with useless rule and awk files; the verdict reads the printed FAIL lines and tally and not only the return value; the abort of the normal run and of `--mask` are tested with a damaged filter | evidence 06: m1 (JWT dropped) killed, m2 (filter_ready always OK) killed, m4 and m5 (abort disabled) killed, m6 (Bearer rule dropped) killed, m7 killed. **m3 (return value forced to 0) is NOT killed: it is an equivalent mutant now, because the verdict no longer uses the return value.** |
| Signals: INT TERM HUP PIPE traps; CLEAN=1 during canary; canary files removed on every exit; truthful exit status; D36 | traps run cleanup and exit with 130/143/129/141; canary and the main run go in the background and the shell `wait`s, so a signal is handled at once; the run exit code is 0, 2, 3, 4 or the signal code | evidence 05: 104 runs (dash and bash, three modes, three signals, to pid and to process group, three delays); every run that was still running when the signal came ended with 129, 130 or 143 and left 0 folders; 0 stray processes |
| N6 `cd ""` | every `cd` is guarded for an empty path | by reading; not run with an empty path (UNVERIFIED) |
| N6 exit status always 0 | exit 4 when the output pipeline fails | evidence: `take \| head -1` exits 4 (run in my shell) |
| N6 `/scripts/` match | only a path that starts with `TAKE_DIR/scripts/` (awk `index`) | by reading; made-up tree has `scripts/` |
| N6 `grep '\|'` GNU only | `grep -E` with `\|`-free alternation | by reading |
| N6 redundant line | the junk no-op rules and awk lines were removed | by reading |
| N6 paths with e-mail parts stay on disk | at the end of a normal run every file except the output copy and the three rule files is deleted | evidence 08: each kept folder holds 4 files; machinery check "kept folder holds only the output copy and rule files" |
| N7 D65 fsmonitor | doc and header now say the two git switches do not stop every folder-configured program; `LEAD_REPIN_NO_STATUS=1` | evidence 09: git index sha256 and mtime unchanged on a made-up git folder |
| N7 D39 counts, "read nothing" | exact counts in the doc (288 canary checks, 11 machinery checks, 299 in all); wording "no take file or input was opened" | evidence 03 |
| N7 D88 skip list, D54 vs D39 | skip report lists every category incl. other file types; the doc describes one and the same behaviour (4 files kept) | evidence 08 |
| N7 1 MB single line | measured | evidence 04: about 0.6 s for 0.98 MB and 1.08 MB, both shells |
| M10 doc wording | plain-words section at the top of the guide (script, masking filter, canary test, work folder, umask, exit code, sed/awk/grep/find, WSL, sha256, porcelain, qs_37, stage, BL-wp6-G1); times in UTC and IST | reading only; NOT tested with a reader who has never seen the project |

## Not verified (read first)
- GNU sed 4.9 and mawk 1.3.4 on Linux only, run as root. Non-GNU sed, other awks, Windows, macOS, WSL, busybox: UNVERIFIED.
- No real take program, flows or model program. The made-up tree has no `_local` flow json and no MODEL_SETTINGS file, so those two branches were read, not run.
- The `PRINT MISMATCH` alarm and the empty `cd ""` guard were never forced to fire.
- Unreadable-file behaviour as an ordinary user: not re-run (root).
- The rows marked "by reading" have no test output.
