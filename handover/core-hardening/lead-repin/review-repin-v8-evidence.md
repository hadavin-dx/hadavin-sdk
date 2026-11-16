# re-pin v8 independent evidence (EVIDENCE RUNNER, condensed copy), 2026-11-16
Raw: lead-repin/evidence-repin8-independent/ (00-TABLE.md). Recorded, not judged. Delivered file sha256 b0b2f142...829c matches the builder's final-sha256.txt.

## Failures and deviations first
1. Filter misses (the secret value stays in the output) with the runner's own hostile spellings, mostly letters-only values (digit values are often caught by the long-token rule as <masked-token>): `password==VALUE` and more equals signs; `secret to VALUE`; full-width colon or equals (U+FF1A, U+FF1D); `login ok password VALUE`; markdown table row `| password | VALUE |`; `ConvertTo-SecureString 'VALUE' -AsPlainText`; HCL line with the key only in a trailing comment; chat-webhook URL with the secret as last path segment; key alone on one line, value on the next; `<input value="VALUE" name="password">`. Two further "shown" results (url-userinfo-pct, empty-value) were checker artifacts, verified by hand. Totals: 86-case digit batch 2 shown (both artifacts); 49-case batch 2 shown; letters-only 86-case batch 6 shown on dash; letters-only 49-case batch 8 shown on dash.
2. `BASH_XTRACEFD=1` or `=2` in bash: `--mask` exits 3 with no output (fd 2: nothing printed, silent stop; fd 1: awk "close failed" line first). Fails closed; no secret printed. dash unaffected.
3. `SHELLOPTS=xtrace:verbose` in bash: about 60 comment lines of the script go to stderr before `set +x +v`; no secret. `SHELLOPTS=xtrace` prints 2 trace lines; `BASHOPTS=extdebug` prints a debugger warning; the `unset SHELLOPTS BASHOPTS` error is hidden by 2>/dev/null.
4. The builder ran chmod 755 on /home/user and the repo folder; current modes /home/user 750, repo 750, handover 755 (runner changed none).
5. Plants m01-m22 ran in both shells at once before the 18:55Z order at load 6.6-7.3; m23 jobs stopped and re-run through heavy-slot.sh serially; verdicts exit-code based. Slot waits 70 s (root dash self-test), 0 s others.
6. m10 is KILLED-startcheck (script refuses to start, exit 3): does not test the filter.
7. Runner slips: first signal run also counted its plant jobs (redone by process group); first hostile checker misread two cases.

## Passes
Self-test on delivered file: passed=1635 failed=0, exit 0 in dash root, bash root, dash uid 65534, bash uid 65534 (setpriv --clear-groups, world-readable /tmp copy). All 42 plants (m01-m24, n01-n18), both shells: 31 KILLED-phase1, 10 KILLED-phase2, 1 KILLED-startcheck; 0 survived, 0 invalid, 0 plant-failed. Signals HUP/INT/TERM/QUIT at 3 delays, both shells (24 runs): exits 129/130/143/131; work folder removed in 23 of 24 (exception: dash QUIT at 2.5 s, run had finished and kept its output copy by design); no live children after 3 s. Work folder drwx------, files -rw-------. Relative TMPDIR and TERM during --mask cases passed. Banned scan of the evidence folder (10 terms read at run time): 0 hits. No stray processes.

## Not run
Letters-only hostile batches on bash (digit batches ran on both shells); random multi-line secret fuzzing; non-GNU sed or awk; the builder's own plants on the earlier copy not re-read.
