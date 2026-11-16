# Review of lead-repin-verify.sh and LEAD-REPIN-VERIFY.md (egm codebase-details, condensed copy), 2026-11-16
Read only; nothing run. No Blocker, 11 Major. Not checked: take/model programs (absent), gates in the sheet and note, macOS/dash/WSL/Windows, mask regex on real strings.
1 mask rule hides a value only for KEY/TOKEN/SECRET/PASSWORD followed by = or :; clear: quoted JSON keys, Bearer, sk-/pat- values, YAML next-line, passwd/pwd/credential/auth; 240-char cut runs after sed (no defence) and hides a late match while count says 1; sed can hide evidence (`key == "end"`). Add rules, a self-test with fake secrets, say lead reads output before sharing.
2 :130 qs_37 grep and :134 settings-name grep skip mask.
3 fixed output name /tmp/lead-repin-verify-out.txt: symlink overwrite, silent overwrite, default umask; `git status` not read-only (index, hooks, fsmonitor): use mktemp + umask 077, `git --no-optional-locks` or drop it; header "only reads" false as written.
4 :101-102,128,142,155 `$(set -f; list_py)` splits on spaces and globs: use find -print0 loop or -exec.
5 :78 -not -path '*/tests/*' '*/test_*' match whole path: a take folder under test_runs drops every file, FILES_READ=0 looks clean. Apply below TAKE_DIR only; print "0 files searched" loudly.
6 default paths wrong: take program is scripts/run_real_check_n8n.py (AGENT-SCOPE:18), script looks in $TAKE_DIR/run_real_check_n8n.py: find by name or state sub-folder.
7 MODEL_RE misses the real call path (post_lead, burst, /qualify, /control, n8n_drive.py via n8n over loopback); only $TAKE_PY searched; zero hits would mean wrong words; calls sent before end and n8n retry/lease cannot be shown by reading the program; END_RE matches prose and misses constants.
8 block HITS totals hide a zero (Q27a/b/c sum several searches; Q27c needs both halves): count per search, print ZERO HITS under each.
9 unreadable file shows as 0 matches: check -r, print UNREADABLE.
10 delete search noisy/incomplete (urlopen flags every call; Q23-3 pattern matches target/.get/budget; misses purge/remove/trash/gdpr/cleanup/method=; .sh helpers); imported flow can differ from folder .json (G3); FLOWS_DIR may sweep node_modules and _local/secrets (AGENT-SCOPE:27 forbids): exclude.
11 doc :50 vs ORDERS 189: no take on 23 Nov unless Q27 a, b and c shown at final head; doc lets (b) alone "become possible"; no owner-sheet meaning for "a model call CAN still follow end".
Nits: pasted-by-hand grep commands unmasked and different from script; glossary needed (head, final head, second reader, FREEZE, R5, R7, decision 2, ban-list item 10, numbers message, need_seconds, FILES_READ); ss in WSL misses Windows listeners (5678/5679); ^ anchor misses `export WINDOW_END=`; qs_37 only searched under TAKE_DIR/MODEL_DIR (unset = "not searched" not "absent"); no sha256sum error captured by tee.
Right: default-if-not-shown stated for Q23, Q27b, Q27c; hit is not behaviour; .used marker is not the go marker; Q23 outcomes follow ORDERS 187.
