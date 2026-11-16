# Re-pin v7 security review (egm-design, uncapped, condensed copy), 2026-11-16T16:59:32Z
Read-only, nothing run. 0 blockers, 1 major, 9 minors. Not clean (new major).
- MAJ-1 mask() (v7.sh 704-706) only strips NUL; ESC sequences, bare CR, bidi overrides print raw, can hide a delete/archive hit on screen. Fix: replace all control bytes except TAB/LF before sed; strip trailing CR; mark bidi; self-tests.
- MIN-1 control byte inside secret name (pass<0x01>word = x) bypasses name rules (line 644 strips after sed): delete control bytes in pre-stage.
- MIN-2 "<masked>" prefix test too loose: "password = <masked>hunter2" leaks; values starting < after is/name:/--token shown. Accept only exact tokens.
- MIN-3 git status runs by default in untrusted folder; GIT_* env not unset (GIT_DIR redirects).
- MIN-4 self-test "every git call carries all four settings" weaker than claimed; fake git prints no version so status call never tested.
- MIN-5 encoding variants (double-escaped quotes, HTML entities, URL-encoded, CDATA, attribute-name settings) not covered nor listed in "can still show".
- MIN-6 positional secrets (.login("u","pw"), api_key == "literal") not hidden; not in guide list.
- MIN-7 hostile-line time cost unproven (O(n^2) separator runs); huge MAX_SECONDS digit string errors.
- MIN-8 pipeline status of mask filter silent outside search_one (--mask, lines(), m.txt).
- MIN-9 IFS/PATH/AWKPATH/LD_*/TEST env vars not reset.
Nits: sha/HEAD lines with -digits- false-hidden; forged "N characters" notice; guide says //token@host but needs ://; UTF-16 NULs; belt ignores multi-line.
Checked fine: writes only in mktemp dir; every search through mask and belt; allowlist for model settings; no eval of file data; git hooks neutralised.
Not checked: nothing run; terminal behaviour; WSL/macOS/busybox.
