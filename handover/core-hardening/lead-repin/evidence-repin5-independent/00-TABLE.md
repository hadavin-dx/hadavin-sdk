# Independent evidence, repin5 (EVIDENCE RUNNER: runs and records, does not judge)
Frozen copy: frozen.sh, sha256 3dfebbce5c14ac2bd80257efee62091bc09d2086f1ab0855ee5a380544e4d72e (same as lead-repin-verify.sh at start and at end). Run as root unless noted. shellcheck: NOT installed (not run).

| # | file | command | exit | one-line result |
|---|---|---|---|---|
| 1 | 01-syntax.txt | bash -n / dash -n / sh -n frozen.sh | 0,0,0 | no syntax errors; shellcheck not installed |
| 2 | 02-selftest-dash.txt | dash frozen.sh --self-test | 0 | passed=1022 failed=0, 51 s |
| 2 | 02-selftest-bash.txt | bash frozen.sh --self-test | 0 | passed=1022 failed=0, 51 s |
| 3 | 03-hostile-lines-result.txt | 80-line own input (67 key forms + multi-line, PEM, binary) via --mask, dash and bash | 0,0 | 151 fake values checked (plain + base64 forms), 0 still shown, both shells; output line count equals input (80) |
| 3 | 04-partial-leak.txt | 7-character inner piece of each value searched in output | - | 0 pieces visible |
| 3 | 05-big-bin-crlf.txt | 1 MB single line, 256-byte binary block, CRLF input, via --mask, dash and bash | 0 x6 | 0 values shown; the 1 MB line is cut after about 240 chars with a "[CUT ...]" note (6.8-7.3 s) |
| 3 | 06-empty.txt | empty stdin --mask | 0,0 | 0 bytes out |
| 4 | 07-signals.txt | INT TERM HUP QUIT, main phase (fake git sleeping) and --mask with stdin open, dash and bash | 130/143/129/131 as designed (16 cases) | folders left 0 in all 16; stray processes 0 in 15, 1 "sleep 29" in dash/main/INT once |
| 4 | 07b-dash-main-INT-x5.txt | the odd case repeated 5 times | 130 x5 | 0 stray, 0 folders; not reproduced |
| 5 | 08-nonroot.txt | as user nobody: --self-test, --mask (80 lines), normal run on made-up folder | 0,0,0 | passed=1022 failed=0; 0 of 151 values shown; normal run printed 213 lines, 0 secret hits, kept its 700 work folder (by design) |
| 6 | 09-damage-summary.txt | 5 planted damages (no Bearer rule, awk blob threshold, no email rule, no TERM trap, no PEM rule), dash --self-test on copies | 1 x5 | all 5 detected: failed=9, 8, 10, 1, 11 |
