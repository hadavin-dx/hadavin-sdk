# Re-pin v8 security review (egm-design, condensed copy of the inline report), 2026-11-16T18:42:48Z
Redaction and secret path, uncapped. Read, Grep, Glob only: every "shows" is a prediction worked out by hand until an evidence runner pipes the probe lines through --mask. Verdict: v8 does NOT pass.
## Failures first
- F1 BLOCKER bare "NAME VALUE" class still open (script:330; neighbours 309, 311, 312). Rule 330 hides one token and only for STRONG names at line start. Predicted to show: api_key kq7z+2m9x, pass/pwd/key/auth/cookie VALUE, "password correct horse battery" (tail kept by design: self-test tail_kept_bare, line 1170), "# TODO my password VALUE", "echo password VALUE", "user bob password VALUE", "password ;VALUE", unterminated quote. Fix: hide the rest of the line, same weak-word list, name anywhere after a start or comment prefix, case per spelling.
- F2 MAJOR camel-case or glued flags with a space value not at line start (312): --apiKey, --accessToken, --authToken, --dbPassword, --clientSecret, --apikey.
- F3 MAJOR value on the line after "NAME =" (605-631 ml_start): const apiKey = then "VALUE"; Go :=.
- F4 MAJOR secret literal compared with a name is deliberately kept (325; keep case at 900 token == "end"): x_token == "VALUE". Narrow the exemption to the literal end.
- F5 MAJOR JSON pair whose name field is not name/key (279; 526-536): CloudFormation ParameterKey/ParameterValue shows the value.
- F6 MAJOR look-alike separators and names (597): full-width = and : after password, Cyrillic letter in a name; builder lists them as open, which the fix-dont-defer rule does not allow.
- F7 MAJOR evidence claim "same sha256 as the delivered file" is false: v8-final2-for-plants.sh has CANARY_PLANNED at line 165 (delivered 166) and lacks unset SHELLOPTS; the 31 other plants ran on copies planning 1615 and 1567; counts 40/41/42 and "24 + 16" disagree; n04 printed PLANT-FAILED.
- F8 BLOCKER for the guide: stale pass lines (1567/1372 vs 1635/1601; appendix 1398; banner prints v6); Quick start names .sh vs .v8.sh; git status contradictions (lines 121, 128, 133, 162); line 149 passwd NAME claim.
- F9 MAJOR builder ran chmod 755 on /home/user and /home/user/hadavin-sdk, earlier modes not recorded; any local user can list and enter and read group/world-readable files (.git, handover, .claude). Needs the owner's decision; the lead checks stat and restores (probably 750 or 700).
- F10 minor control byte on a name-alone line defeats the next-line rule (667-688 vs 198). F11 minor unset SHELLOPTS BASHOPTS under bash --posix untested; unset -f list incomplete; empty folder in the window before traps. F12 minor HUP never executed (nohup), INT/QUIT not run, busybox ps -o untested.
## Held by reading
Bare password VALUE with STRONG name at line start hidden (also with comment prefix and TAB); http/https/xh -a user:VALUE covered; --auth and --proxy-user covered; m13 test written correctly; umask 077 before mktemp; cleanup name guard; no unmasked search line on disk; st-in.txt made-up only; NOT TESTED row exists; no secret shape beyond AKIAIOSFODNN7EXAMPLE.
## Probe lines for the evidence runner (build from parts)
api_key kq7z2m9x | pass | pwd | password correct horse battery | # TODO my password VALUE | deploy --apiKey VALUE run | tool --dbPassword VALUE go | const apiKey = / "VALUE"; | if x_token == "VALUE": | {"ParameterKey": "DbPassword", "ParameterValue": "VALUE"} | password U+FF1D VALUE | password: ESC then "- VALUE".
## Not checked
Nothing executed; sha256 of delivered file; uid 65534 evidence line by line; ReDoS timing; gawk/busybox/macOS; WSL; UTF-16; Terraform variable default, Kubernetes Secret data, Azure SAS sig=, login=user:pw, pin/seed names; modes unreadable by the reviewer.
