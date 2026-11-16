# Re-pin v3 review round 3 (egm-design, read-only, ran nothing), condensed copy, 2026-11-16
Target: lead-repin-verify.sh v3 + LEAD-REPIN-VERIFY.md v3. Secret path: uncapped. Verdict: NOT ready to rely on. No confirmed Blocker (reviewer ran nothing); M1 and M4 could become Blockers on a real run.
## Major
- M1 no LC_ALL=C and no grep -a: a Latin-1 byte or NUL makes grep call a file binary; count printed with no lines; sed may fail to hide a value after a bad byte. Fix: export LC_ALL=C, grep -a, canary line with byte 0xE9, compare printed N: lines with count.
- M2 plural names not hidden: API_KEYS, PASSWORDS, AUTH_TOKENS, ALLOWED_API_KEYS. Add plurals; tokens secret unless allowlisted (max_, num_, n_, total_, prompt_, completion_, input_, output_ + tokens); canary both ways.
- M3 `Name: value` in mid-line not covered (curl -H "X-Api-Key: .."), and multi-file greps give path:NN:text so the ^NN: anchor misses. Fix rule + YPRE accept path prefix + canary, or tell hand commands to use grep -h.
- M4 nested/array/pretty-printed JSON or YAML leaks (value on the next line after "name": "X_TOKEN"). Fix: hide next `value` line; hide to end of line after { or [ values; canary.
- M5 canary may test another filter: SELFTEST_FILTER env honoured in normal run; --mask runs no canary. Fix: unset it in normal and --mask, run self_test 1 in both; soften D54.
- M6 DELETE_RE misses delete_contact(, deleteContact(, hard_delete(; Q23-4 only searches take program. Fix: plain substring delet, all four named files; report skipped file types.
- M7 masking can hide the match word with no notice. Fix: count printed lines that no longer show the match word and print the line numbers.
- M8 Q27b settings search prints values from the file holding the real key; substring `end` matches SENDGRID etc. Fix: value only if date/number-shaped, whole-word names.
- M9 `_local` flows (the ones that run) never shown. Fix: print file:line:matched-word via grep -o (no values).
- M10 doc wording: many terms unexplained (canary, masking filter, work folder, umask, WSL, GNU sed, sha256, porcelain, exit code 3, qs_37, stage, BL-wp6-G1 ...). Fix: one plain glossary.
## Nits / wrong doc claims
N1 work folder not removed on INT/TERM/HUP/PIPE (doc says it is; D36); canary input file left. Fix traps; CLEAN=1 before canary. N2 belt hits not counted. N3 canary case 17 vacuous (secret at col 308, cut at 240). N4 maxdepth wording off by one. N5 escaped quotes, adjacent strings, PEM, sk_live_, curl -u. N6 small script defects (cd "" , exit status always 0, /scripts/ match, grep '\|' GNU only, redundant line 508, paths with e-mail parts stay on disk). N7 doc claims: D65 fsmonitor, D39 counts (about 48/32), D88 skip list, D39 "read nothing", D54 vs D39. Performance on a 1 MB single line unchecked.
Closure of 12 round-2 findings: 9 closed, #2 mostly, #4 not closed for --mask/env override, #11 wording not closed.
