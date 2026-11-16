# Independent evidence, lead-repin-verify.v8.sh (EVIDENCE RUNNER: records, does not judge)
Delivered file sha256 b0b2f142400ee0f6aff0e06b8360d58819ec5ffd447aa3d2c627d3c0a83f829c (same as the builder's final-sha256.txt). Run from a world-readable copy /tmp/hd8i/v8.sh (mode 644). Run date 2026-11-16 18:36-19:26 UTC (00:06-00:56 IST on 17 Nov).

## Failures and deviations first
1. FILTER MISSES (hostile spellings, values written by me at run time; a "miss" = the secret value is still in the output). Raw: 05*-hostile*.txt, 05c/05d (letters-only values). Values that contain digits are often rescued by the generic long-token rule (they print as <masked-token>); values of letters only show these misses (dash; bash only run on the digit batches, see "not run"):
   - `password==VALUE`, `password===VALUE`, `password====VALUE` (two or more equals signs): VALUE shown (letters-only; with digits it printed <masked-token>).
   - `secret to VALUE` / "note: set secret to VALUE" (prose, word "to"): shown.
   - full-width colon and full-width equals after the key (U+FF1A, U+FF1D): shown.
   - `login ok password VALUE` (key then bare value inside a log line): shown (letters-only).
   - markdown table row `| password | VALUE |`: shown. `ConvertTo-SecureString 'VALUE' -AsPlainText`: shown. HCL line with the key only in a trailing comment: shown. Chat-webhook URL with the secret as last path segment: shown. Key alone on one line, value on the next line: shown. `<input value="VALUE" name="password">` (value before name): shown.
   - Not misses (my checker artifacts, verified by hand): url-userinfo-pct (host text matched), empty-value (no value).
   Case ids per run are in the raw files; totals: 86-case digit batch: 2 shown (both artifacts) in dash and bash; 49-case batch (digits likely): 2 shown (many-equals, cap-key-in-value) in dash and bash; letters-only 86-case: 6 shown in dash (2 artifacts + fullwidth colon, fullwidth equals, log-space-kv, empty-then-next); letters-only 49-case: 8 shown in dash.
2. `BASH_XTRACEFD=1` or `=2` in bash: `--mask` exits 3 with no stdout; for fd 2 nothing at all is printed (a silent stop), for fd 1 the stop text is preceded by "awk: close failed on file /dev/stdout (Bad file descriptor)". Fails closed, no secret printed, but the person gets no reason for fd 2. (dash unaffected, exit 0.)
3. `SHELLOPTS=xtrace:verbose` in bash: the script's own source lines up to the `set +x +v` line (about 60 lines of comment text) go to stderr. No secret (the secret was on stdin). `SHELLOPTS=xtrace` prints two trace lines. `BASHOPTS=extdebug` prints a debugger warning (bashdb missing) to stderr. The `unset SHELLOPTS BASHOPTS` error itself is hidden by 2>/dev/null (no error shown). No secret in any of these outputs.
4. Modes: the builder said it ran chmod 755 on /home/user and the repo folder (earlier mode unknown). CURRENT modes (stat): /home/user 750 root, /home/user/hadavin-sdk 750 root, handover 755, /tmp/hd8i 755. So they are 750 now, not 755 (someone changed them back after the builder; I did not touch them).
5. Load: the first plant batches m01-m22 (both shells, 2 jobs at once) ran BEFORE the lead's 18:55Z order, under load 6.6-7.3 on 4 cores (above the 8 limit? no: below 8). m23 phase 2 of both shells was in flight when the order came; I stopped those jobs (my own) and re-ran m23-n18 wrapped and serial. All verdicts are exit-code based, not timing based.
6. m10 verdict is KILLED-startcheck (the script refuses to start, exit 3): the plant does not test the filter. Same as the builder's note.
7. Two of my own slips: my first signal run counted processes by name and also counted the plant jobs; I redid it by process group. The first hostile checker read two cases wrongly (artifacts above).

## Passes
| # | Command | Exit | Counts | Slot wait | Load at start |
|---|---|---|---|---|---|
| 1 | dash v8.sh --self-test, root | 0 | passed=1635 failed=0 | 70 s | 1.68 |
| 2 | bash v8.sh --self-test, root | 0 | passed=1635 failed=0 | 0 s | 1.43 |
| 3 | dash, setpriv uid/gid 65534, --clear-groups, TMPDIR owned by 65534 | 0 | passed=1635 failed=0 | 0 s | 2.10 |
| 4 | bash, uid 65534 | 0 | passed=1635 failed=0 | 0 s | 1.67 |
| 5 | plants, dash, all 42 (mutate8.py on the delivered file) | | 31 KILLED-phase1, 10 KILLED-phase2, 1 KILLED-startcheck (m10); 0 survived, 0 invalid, 0 plant-failed | m01-m22: not wrapped; m23-n18: 0 s | 6.75 (m23-n18) |
| 6 | plants, bash, all 42 | | same split: 31/10/1; 0 survived | 0 s | 2.46 |
| 7 | signals HUP INT TERM QUIT x delays 0.4/1.2/2.5 s x dash/bash (24 runs, 06-signals.txt) | 129/130/143/131 | work folder removed in 23 of 24; the one exception (dash QUIT at 2.5 s) finished normally first (exit 0, output copy kept, by design); no live child left after 3 s (06b: only zombie entries, gone in 3 s) | | |
| 8 | work folder modes of a normal run | | folder drwx------, files -rw------- (4 files, as designed) | | |
Plant files: 04-plants-dash.txt, 04-plants-dash-part2.txt, 04-plants-bash.txt, 04-plants-bash-part2.txt. Self-tests: 02-*, 03-*. Plant counts: dash and bash each have all 42 ids (m01-m24, n01-n18).

## Not run
- Letters-only hostile batches on bash (digit batches were run on both).
- Hostile secrets split across lines were only the few cases listed (key then value on next line); no random multi-line fuzz.
- No Windows or macOS sed/awk (GNU sed and mawk/awk of this machine only).
- No commit, no push, no secrets, no spend. Banned-term scan of this folder (terms read from tests/test_no_reference_material.py at run time): 0 hits (10 terms).
- Builder's other evidence (earlier copy plants) not re-read.
