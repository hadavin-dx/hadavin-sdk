# Re-pin v7 independent evidence (EVIDENCE RUNNER, condensed copy), 2026-11-16
Raw output: evidence-repin7-independent/ (33 files). Recorded, not judged. lead-repin-verify.sh is still v6 (sha e419fdeb...2617); v7 copy and lead-repin-verify.v7.sh both d8ba8c28...75eb, matching evidence-repin7/10-sha256.txt.

## Failures and deviations first
1. The v7 filter lets some secret shapes through (made-up lowercase values; mixed case would be hidden by the generic long-string rule for the wrong reason). A bare `password VALUE` with no punctuation survives in dash and bash after a space, several spaces or a tab: `password<TAB>VAL`, `db_password<TAB>VAL`, `secret<TAB>VAL`, `token<TAB>VAL`, `Password<TAB>VAL`, and `user alice` then a line `password VAL`. Hidden: `password: VAL`, `password<TAB>"VAL"`, `password=<TAB>VAL`. The guide lists `passwd NAME` as a known gap but not plain `password VALUE`. Batch 3: 10 of 13 spacing cases survive. `http -a alice:VALUE example.test` is not hidden (`http` not in the command list); `http --auth=` is hidden.
2. Two plants survived the self-test (1398/0): m13 (`umask 077` to `022`): the kept output copy and the three masking rule files become mode 644 instead of 600 (real run, 07-probe-m13-file-modes.txt); the self-test does not check file modes. m17 (`curl|wget|http` guard shortened to `curl`): outputs identical to v7 for two httpie-style inputs, possibly equivalent, not proved.
3. Only 17 of 24 planned plants ran (m18 to m24 not run, for time; dash only). m16 (ENCRYPTED removed from the PEM header rule) SURVIVED, probably equivalent (`ENCRYPTED PRIVATE KEY` still matches `PRIVATE`); not tested with `BEGIN ENCRYPTED DATA`.
4. Over-hiding side effect: an escaped closing quote is eaten (`{\"password\": \"<masked>}`).

## Results
- Self-test: root dash 1398/0, root bash 1398/0, uid 65534 dash 1398/0, uid 65534 bash 1398/0, control copy under another name 1398/0 (all exit 0).
- Hostile masking: batch 1 (80 cases built from parts) 0 survivors in dash and bash; batch 2 (same 80 with lowercase 10-letter values) 1 survivor each (the tab case); batch 3 (13 spacing cases) 10 survive; dash and bash byte-identical for batches 1 and 2. Hidden: escaped-quote names, `\u` escape names, `-p` positions, `&&`, `;`, `|`, `$(`, NAME= prefix, path before command, quoted values with spaces, glued names, XML names, `:=`, IDENTIFIED BY, requirepass, masterauth, user-info URLs, git settings and extraheader.
- Plants (17 of 24, dash): killed 14 (m01-m09, m10 by the filter's own start check, m11, m12, m14, m15); survived 3 (m13, m16, m17).
- Signals: BAD rows 0 of 16, launcher exit 0 (the builder's signals.py copied unchanged).
- Banned strings: 0 hits in the 33 files and 0 hits over the 301 files of lead-repin/ (3 undecodable files, earlier outputs).

## Not run
Plants m18-m24 and every plant under bash; v6 comparison; a full run on a real take folder; large-tree timing; Windows, macOS, busybox. No spend, no real secrets.
