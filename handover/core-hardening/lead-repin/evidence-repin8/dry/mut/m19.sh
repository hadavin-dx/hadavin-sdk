#!/bin/sh
# lead-repin-verify.sh (version 8): checklist printer for the lead at re-pin.
#
# WHAT IT DOES TO YOUR MACHINE (exact):
#   - reads files: grep, sed, awk, tr, wc, find, sha256sum, git rev-parse / log / status
#     (git runs with --no-optional-locks, so it does not rewrite the git index to refresh it, with
#     core.fsmonitor=false, so the folder's file-system-monitor program is not started, with log.showSignature=false
#     and gpg.program=/bin/false, so no signature program of the folder's settings runs for "git log", and with
#     core.hooksPath=/dev/null, so no hook runs. v8: "git status" does NOT run by default, because it can still start
#     programs the folder's own git settings name (a clean or smudge filter, for example for large files); set
#     LEAD_REPIN_GIT_STATUS=1 only for a folder you trust. Every GIT_* variable of the caller is removed at the start,
#     and the system and user git configuration files are not read);
#   - reads the list of listening ports (ss, or netstat, or /proc/net/tcp);
#   - writes ONLY into one private work folder it makes with mktemp (permissions 700, files 600 because of
#     umask 077; on a Windows-mounted drive under WSL these modes may NOT be enforced, so set TMPDIR to a
#     Linux folder). During a normal run the work folder holds: a copy of this output (already masked),
#     lists of file names (paths only, no file content), the masking rule files (no secret in them) and small
#     masked helper files. NO unmasked line of any searched file is ever written to disk: every search pipes
#     grep straight into the masking filter. The canary self-test (below) makes a file of made-up secrets in
#     the work folder and deletes it again at once. AT THE END OF A NORMAL RUN every file except the masked
#     output copy and the three masking rule files is deleted (the lists of file names could hold a name that
#     is itself private);
#   - DELETES only inside the work folder it made itself (the path is checked to be of the form
#     .../lead-repin.XXXXXX before rm -rf). It deletes the whole work folder: in the modes --self-test and
#     --mask; when the canary test fails or the setup fails; and when the run is interrupted (INT, TERM, HUP, QUIT or
#     PIPE signal). A normal run that reaches its end keeps the work folder with the masked output copy; delete
#     it yourself;
#   - makes NO network call and NO model call. Apart from the tools named above it starts no other program of
#     the test program. It never starts the model program.
# It judges NOTHING: it prints what it found, with line numbers, for the lead to read.
# Values that look like secrets are hidden by ONE masking filter (see "mask") that every search uses, and a
# canary self-test of that filter runs FIRST in every mode that prints search results (normal run, --mask):
# if the canary test fails, the script stops before it opens any test-program file or reads any input. A filter is
# still a safety net, not a guarantee: THE LEAD READS THE OUTPUT BEFORE SHARING IT.
#
# usage:
#   sh lead-repin-verify.sh [TAKE_DIR]        run the checklist (TAKE_DIR defaults to the current folder)
#   sh lead-repin-verify.sh --self-test       test the masking filter with made-up secrets, print PASS/FAIL
#   <command> | sh lead-repin-verify.sh --mask   pass any text through the same masking filter
#   (test aid, --self-test only) SELFTEST_FILTER="sh other-version.sh --mask" sh lead-repin-verify.sh --self-test
#              runs the same test cases against another filter, to show that an old filter fails them.
#              In every other mode SELFTEST_FILTER is removed from the environment.
#
# Exit codes: 0 the checklist ran to its end (this does NOT mean the answers are good: read the output);
#   2 setup problem (no work folder, test-program folder missing); 3 the masking filter is not usable or failed its
#   own test, no test-program file or input was opened; 4 the output pipeline failed; 129/130/131/141/143 stopped by
#   HUP/INT/QUIT/PIPE/TERM (the work folder is removed, and so are the programs the run had started); for --self-test:
#   0 all cases passed, 1 at least one failed.
#
# Needs: GNU sed (or a sed that knows the s///I flag; the canary stops the run otherwise), grep, awk, tr, find.
# Every file name below is "adjust if different": set the variable in the environment.
# If TAKE_PY, CRM_PY, DRIVE_PY or N8N_PY is not set, the script looks for the file BY NAME (in files that
# have at most 3 folders between the test-program folder and the file, preferring a scripts/ folder below the test-program folder
# folder) and prints which one it used.
#   TAKE_PY CRM_PY DRIVE_PY N8N_PY FLOWS_DIR MODEL_DIR MODEL_SETTINGS ONE_STORE END_RE MODEL_RE DELETE_RE LEAD_REPIN_NO_STATUS
# v8: a shell function inherited from the caller (bash: export -f sed) would replace the real program; remove them first
unset -f sed awk grep tr find git ps head sort wc cat kill sleep date mktemp rm ls cut tee id uname mkdir cp mv chmod basename dirname env printf test 2>/dev/null
set +x +v 2>/dev/null          # a trace option from the caller (sh -x, sh -v) would print every line, secret values included
# PATH: keep only absolute folders. An empty or relative entry (a dot, for example) would let a program planted
# in the current folder run instead of the real sed, awk, grep or git.
SAVE_IFS=$IFS; NEWPATH=; IFS=:
for pth_d in ${PATH:-}; do case $pth_d in /*) NEWPATH=${NEWPATH:+$NEWPATH:}$pth_d ;; esac; done
IFS=$SAVE_IFS; PATH=${NEWPATH:-/usr/bin:/bin}; export PATH
# (ENV and BASH_ENV are read by a shell when it STARTS, before this line: unsetting them here protects only the programs started below, not this shell itself)
unset ENV BASH_ENV CDPATH GREP_OPTIONS GREP_COLOR GREP_COLORS SED_OPTIONS AWKPATH AWKLIBPATH POSIXLY_CORRECT SHELLOPTS BASHOPTS BASH_XTRACEFD PS4 LOCPATH NLSPATH MALLOC_CONF
# v8: every GIT_*, LD_* and DYLD_* variable of the caller is removed (GIT_DIR or GIT_WORK_TREE would point git at another
# folder; LD_PRELOAD would load a library into every program below), and git gets a fixed, safe setting set of its own
for env_v in $(env 2>/dev/null | sed -n 's/^\(\(GIT\|LD\|DYLD\)_[A-Za-z0-9_]*\)=.*/\1/p'); do unset "$env_v" 2>/dev/null; done
GIT_CONFIG_NOSYSTEM=1; GIT_CONFIG_GLOBAL=/dev/null; GIT_TERMINAL_PROMPT=0; GIT_OPTIONAL_LOCKS=0; export GIT_CONFIG_NOSYSTEM GIT_CONFIG_GLOBAL GIT_TERMINAL_PROMPT GIT_OPTIONAL_LOCKS
IFS=$(printf ' \t\n_'); IFS=${IFS%_}   # v8: the word-splitting characters are reset (a caller's IFS would change every unquoted expansion below)
LC_ALL=C; export LC_ALL        # byte-wise matching: a byte that is not valid text cannot make a tool skip a line
set -u
umask 077

# ---------------------------------------------------------------- work folder, signals, clean-up
SELF=$0
case ${1:-} in --self-test) ;; *) unset SELFTEST_FILTER ;; esac
case ${TMPDIR:-/tmp} in /*) ;; *) echo "TMPDIR must be an absolute path (it is: ${TMPDIR})" >&2; exit 2 ;; esac
WORK=$(mktemp -d "${TMPDIR:-/tmp}/lead-repin.XXXXXX") || { echo "cannot make the private work folder with mktemp" >&2; exit 2; }
MASKSED=$WORK/mask.sed        # full filter: line rules AND multi-line rules (used on every search result)
MASKLINE=$WORK/mask-line.sed  # line rules only (the final belt over the whole output: it can never hide a following line)
MASKAWK=$WORK/mask.awk        # second stage: opaque strings, containers, pairs of lines, cutting long lines
SHAOK=$WORK/sha-ok.txt        # the checksum lines THIS script printed itself (block R00): only these may stay unmasked
OUT=$WORK/lead-repin-verify-out.txt
LENCUT=$WORK/lencut.txt       # one line per input line that the length guard cut before masking (a count for the summary)
NL=$(printf '\n_'); NL=${NL%_}
CLEAN=1                       # 1 = remove the work folder on exit; set to 0 only after the canary passed in a normal run
FINISHED=0                    # set to 1 only when a normal run has reached its end and removed the file-name lists
BGPID=
cleanup() {
  [ -n "$WDPID" ] && { kill_tree "$WDPID"; WDPID=; }

  [ -d "$WORK" ] || return 0
  rm -f "$WORK"/st-in.txt "$WORK"/st-out*.txt "$WORK"/canary.out 2>/dev/null   # canary files go away on every exit path
  # a normal run that did NOT reach its end (an error, an unset variable) must not keep file-name lists: remove all
  [ "$CLEAN" = 0 ] && [ "$FINISHED" = 0 ] && CLEAN=1
  [ "$CLEAN" = 1 ] && rm -rf "$WORK"
  return 0
}
# kill_tree PID: send TERM to PID and to every process below it (found with ps -A -o pid= -o ppid=), so that the
# grep, sed, awk and git programs of a stopped pipeline do not keep running. It only ever touches PID and its descendants.
kill_tree() {
  kt_all=$1; kt_new=$1; kt_i=0
  [ "${2:-}" = kids ] && kt_all=   # kids: only the programs below PID, not PID itself
  while [ -n "$kt_new" ] && [ "$kt_i" -lt 8 ]; do
    kt_new=$(ps -A -o pid= -o ppid= 2>/dev/null | awk -v roots="$kt_new" 'BEGIN { n = split(roots, r, " "); for (i = 1; i <= n; i++) R[r[i]] = 1 } ($2 in R) && !($1 in R) { print $1 }')
    kt_all="$kt_all $kt_new"; kt_i=$((kt_i + 1))
  done
  # shellcheck disable=SC2086
  kill $kt_all 2>/dev/null
  return 0
}
MAINPID=$$; WDPID=
start_watchdog() { # ends the whole run (as a TERM signal) after LEAD_REPIN_MAX_SECONDS (default 1200); stopped again by cleanup
  MAXSEC=${LEAD_REPIN_MAX_SECONDS:-1200}
  case $MAXSEC in ''|*[!0-9]*) MAXSEC=1200 ;; esac   # not a whole number: the default
  case ${#MAXSEC} in [1-6]) ;; *) MAXSEC=1200 ;; esac   # v8: more than 6 digits (an absurd limit, or a number the shell cannot compare): the default
  ( wd_i=0; while [ "$wd_i" -lt "$MAXSEC" ]; do kill -0 "$MAINPID" 2>/dev/null || exit 0; sleep 1; wd_i=$((wd_i + 1)); done; : > "$WORK/timeout.flag"; kill -TERM "$MAINPID" 2>/dev/null ) &
  WDPID=$!
}
on_signal() { [ -f "$WORK/timeout.flag" ] && echo "STOP: the run took longer than ${MAXSEC:-1200} seconds (LEAD_REPIN_MAX_SECONDS) and was ended; the work folder was removed" >&2; CLEAN=1; trap '' INT TERM HUP PIPE QUIT; [ -n "$BGPID" ] && kill_tree "$BGPID"; kill_tree "$MAINPID" kids; cleanup; exit "$1"; }
trap cleanup EXIT
trap 'on_signal 130' INT
trap 'on_signal 143' TERM
trap 'on_signal 129' HUP
trap 'on_signal 141' PIPE
trap 'on_signal 131' QUIT
# bg_wait CMD...: run CMD in the background and wait for it, so a signal that reaches this shell is handled
# at once (a plain foreground command would delay the trap until the command ends)
bg_wait() { "$@" & BGPID=$!; wait "$BGPID"; bg_rc=$?; BGPID=; return "$bg_rc"; }

# ---------------------------------------------------------------- masking filter (the ONE choke point)
# Two stages. Stage 1 is a sed script (name rules, shape rules, multi-line rules). Stage 2 is an awk
# program (mask.awk) that hides what no name gives away (long opaque strings, mixed-letter-and-digit
# words), hides JSON / YAML containers and pairs of lines, and cuts long lines.
# Names that look secret are matched as whole WORDS of an identifier (words are split at _ . - and
# spaces), so  key_file  token  api_key  X-Api-Key  accessToken  PASS  pat  API_KEYS  are secret names, but
# author  desk  task  risk  tokenizer  max_tokens  prompt_tokens  bypass  are not. Words that END in key,
# token, secret, password, passwd, pwd or credential(s) (also in the plural) count too (apiKey, accessToken,
# monkey: it errs on the side of hiding). The token counters max_ num_ n_ total_ prompt_ completion_ input_
# output_ cached_ reserved_ + tokens are not secret.
# Rules (extended regular expressions, case-insensitive):
#  L1 YAML name alone on a line, value on the next line(s): hide the next line and indented lines after it
#     (also inside grep output, which prefixes "12-" or "path:12-").                       [full filter only]
#  L2 text between triple quotes after  name =  : same line, or all lines up to the closing quotes. [full only]
#  L3 a private-key block: every line between BEGIN ... PRIVATE ... and END is hidden.      [full only]
#  1  JSON / dict:  "name": value  and  'name': value  and  {name: value}  (value may hold escaped quotes or
#     several strings in a row).
#  2  JSON pair  {"name": "X_TOKEN", "value": "..."}: the value is hidden.
#  3  web address with user:password@ ;  curl -u user:password .
#  4  Bearer, Basic and  Authorization: <scheme> <value>  header values, JWT-shaped values.
#  5  well-known value shapes (with a word edge, so desk- task- risk- mask- compat- are not hit):
#     sk- pk- rk- pat- sk_live_ ghp_ gho_ ghs_ ghu_ github_pat_ xox*- AKIA/ASIA ids AIza whsec_
#     (the one example AKIAIOSFODNN7EXAMPLE is allowed to show).
#  6  name = value (also  os.environ["X_TOKEN"] = "v"  and  self.token = v): quoted value hidden alone,
#     unterminated quote and unquoted value hide the rest of the line.  name: value at the START of a line
#     (YAML / header form) hides the rest of the line; name: value in the MIDDLE of a line hides one value.
#     A comparison such as  key == "end"  is NOT hidden.
#  7  name followed by a comma and a quoted value:  ("API_KEY", "v")  and  .get("API_KEY", "default").
#  8  command-line flags:  --token abc  --password abc  --api-key=abc ; Dockerfile  ENV TOKEN v ;
#     passwd "v" ;  the password is v .
#  9  e-mail addresses are replaced by <email-masked>.
# Stage 2 (mask.awk), see the comments in that file.
# planned number of checks (the canary alone; the whole --self-test): a run that passes fewer or more is NOT accepted
CANARY_PLANNED=1534
SELFTEST_PLANNED=1567
SOH=$(printf '\001'); STX=$(printf '\002'); ETX=$(printf '\003'); ENQ=$(printf '\004')
write_mask_sed() {
  # NAME RULE (one general rule, not a list of names): an identifier is secret when
  #  (a) a STRONG word is anywhere inside it (secretValue, tokenString, passwordHash, authTokenValue, secretdata),
  #  (b) it holds a WEAK whole word (key, pass, pat, auth, cookie, session, signature, hmac, dsn, webhook, salt, otp,
  #      cert, ...) at a separator or at the start, also followed by value, string, data, text, hash, bytes or material
  #      (keyValue, saltHash), or
  #  (c) it ENDS in key, token, secret, password, pwd, credential (apiKey, accessToken).
  STRONG='(secret|passw[o0]?r?d|passphrase|credential|token|apikey|requirepass|masterauth|jsessionid|phpsessid|(db|root|admin|user|mysql|pg|redis|master|ssh|smtp|mail|ldap|sql|wifi|wpa|sys|login)(pass|pw|pwd))'
  W='(keys?|tokens?|secrets?|passw[o0]?r?ds?|passphrases?|pass|pwd|pws?|psw|pswd|pat|credentials?|authorization|auth|bearer|private|cookies?|sessions?|signatures?|hmac|dsn|webhooks?|salt|otp|certs?|certificates?)'
  WS='(value|string|data|text|hash|bytes|material|id|url|uri|name|code|list|file|path|ring|store)'
  SUF='(keys?|tokens?|secrets?|passw[o0]?r?ds?|pwd|credentials?)'
  # IDB: an identifier that contains a secret word; IDQ: the same inside quotes (spaces count as separators)
  IDB="(([A-Za-z0-9_.-]*$STRONG[A-Za-z0-9_.-]*)|((([A-Za-z0-9_.-]*[_.-])?$W)(([_.-]|$WS)[A-Za-z0-9_.-]*)?)|([A-Za-z0-9_.-]*$SUF([_.-][A-Za-z0-9_.-]*)?))"
  IDQ="(([A-Za-z0-9_. -]*$STRONG[A-Za-z0-9_. -]*)|((([A-Za-z0-9_. -]*[_. -])?$W)(([_. -]|$WS)[A-Za-z0-9_. -]*)?)|([A-Za-z0-9_. -]*$SUF([_. -][A-Za-z0-9_. -]*)?))"
  ID="(^|[^A-Za-z0-9])$IDB"          # IDB with a left edge (the edge character is part of the match)
  PRE="[\"']?[]]?[[:space:]]*="       # what may stand between the name and  =   ( name"]  = )
  # optional grep prefix: NN:  NN-  path:NN:  path-NN-   (the path may hold spaces and dashes but no colon; a path
  # with a colon is not recognised: search such a file on its own, where the prefix is only NN:)
  PFX0='(([^:]+[:-])?[0-9]+[-:])?'
  YPRE="^${PFX0}[[:space:]]*(- +)?[\"']?"      # start of a line: optional grep prefix, indent, list dash, quote
  DQ='"([^"\\]|\\.)*"'                         # a double-quoted string that may hold \" inside
  SQ="'([^'\\\\]|\\\\.)*'"                     # the same with single quotes
  STR="(${DQ}|${SQ})([[:space:]]*\\+?[[:space:]]*(${DQ}|${SQ}))*"   # one or more strings in a row ("a" "b", 'a' + "b")
  BQ='\\+["'"'"']'
  BQD='\\+"'; BQS="\\\\+'"; EBD='\\"'; EBS="\\\\'"    # escaped double or single quote (one or more backslashes); EBD/EBS: what the replacement puts back so the closing quote stays                           # a backslash followed by a quote character (a quote escaped inside JSON that sits inside a string)
  UNQ='[^][{},[:space:]<"'"'"'][^,}[:space:]]*'  # an unquoted value (does not start a container or a mask mark)
  {
    cat <<EOF
:top
/${YPRE}${IDB}["']?[[:space:]]*:[[:space:]]*((&[^[:space:]]+|![^[:space:]]*)[[:space:]]+)*([|>][-+0-9]*)?[[:space:]]*(#.*)?\$/I{
n
/^${PFX0}[[:space:]]+[^[:space:]]|^${PFX0}- /{
s/^${PFX0}.*/\1<masked>/
:ya
n
/^${PFX0}[[:space:]]+[^[:space:]]|^${PFX0}- /{
s/^${PFX0}.*/\1<masked>/
bya
}
b top
}
/^${PFX0}[[:space:]]*(- +)?["']?[A-Za-z0-9_.-]+["']?[[:space:]]*:|^--\$/b top
s/^${PFX0}.*/\1<masked>/
}
/-----BEGIN [A-Z ]*(PRIVATE|SECRET|ENCRYPTED)[A-Z ]*-----/{
/-----END /!{
s/(-----BEGIN [A-Z ]*-----).*/\1<masked>/
:pem
n
/-----END /!{
s/^${PFX0}.*/\1<masked>/
bpem
}
}
}
/(${ID})${PRE}[[:space:]]*"""/I{
/(${ID})${PRE}[[:space:]]*""".*"""/I!{
s/((${ID})${PRE}[[:space:]]*""").*/\1<masked>/I
:t1
n
/"""/!{
s/^${PFX0}.*/\1<masked>/
bt1
}
s/^(${PFX0})([^"]|"[^"]|""[^"])*"""/\1<masked>"""/
b
}
}
/(${ID})${PRE}[[:space:]]*'''/I{
/(${ID})${PRE}[[:space:]]*'''.*'''/I!{
s/((${ID})${PRE}[[:space:]]*''').*/\1<masked>/I
:t2
n
/'''/!{
s/^${PFX0}.*/\1<masked>/
bt2
}
s/^(${PFX0})([^']|'[^']|''[^'])*'''/\1<masked>'''/
b
}
}
EOF
    xml_rules
    # v8: from here on every raw < of the input is the private byte STX; the only < left are the marks this filter made itself
    # (<masked>, <email-masked>). So a value that starts with < can no longer pass as "already hidden" (MIN-2).
    printf 's/<masked>/%s/g\ns/<email-masked>/%s/g\ns/</%s/g\ns/%s/<masked>/g\ns/%s/<email-masked>/g\n' "$ETX" "$ENQ" "$STX" "$ETX" "$ENQ"
    line_rules
  } > "$MASKSED"
  line_rules > "$MASKLINE"
}
# PWCMDS: commands that take a password as a short flag (-p -P -a -w -k or -pVALUE). THIS IS A LIST: a command that is not on it
# is only covered by the shape rule (a line that starts like a command and has -p, -P or -w and a value that is not a number).
PWCMDS='docker|podman|nerdctl|skopeo|buildah|helm|redis-cli|ldapsearch|ldapmodify|ldapadd|ldapdelete|ldappasswd|ldapwhoami|zip|zipcloak|unzip|7z|7za|7zr|rar|unrar|arj|htpasswd|smbclient|smbget|rpcclient|mount|psql|pg_dump|pg_restore|mongo|mongosh|mongoexport|mongoimport|sqlcmd|bcp|ftp|lftp|ncftp|rclone|openconnect|openssl|ccrypt|gpg|gpg2|mysql|mysqldump|mysqladmin|mariadb|mongodump|mongorestore|sshpass|cqlsh|beeline|impala-shell|influx|svn|hg|az|cryptsetup|ansible|ansible-playbook|vncpasswd|xfreerdp|rdesktop|remmina'
PWCMDS_A="$PWCMDS|http|https|xh"   # v8: the -a (user:password) flag of httpie style programs; only for the -a, -w, -k forms
line_rules() {
  cat <<EOF
s/(^|[^A-Za-z0-9])(((max|num|n|total|prompt|completion|input|output|cached?|reserved)[_.-]?)+)(tok)(ens)/\1\2\5${SOH}\6/Ig
s/(tok)(eniz|enis)/\1${SOH}\2/Ig
s/((${ID})[[:space:]]*:=[[:space:]]*)(${STR}|[^[:space:]<"'][^[:space:]]*)/\1<masked>/Ig
s/(<[A-Za-z]+[[:space:]]([^>]*[[:space:]])?(key|name|var|variable|env|id)=["'](${IDQ})["'][[:space:]]+(value|val|data|content)=)(${STR}|[^[:space:]>/<"'][^[:space:]>/]*)/\1"<masked>"/Ig
s/((${ID})${PRE}[[:space:]]*)(""")([^"]|"[^"]|""[^"])*"""/\1<masked>"""/Ig
s/((${ID})${PRE}[[:space:]]*''')([^']|'[^']|''[^'])*'''/\1<masked>'''/Ig
/(${ID})${PRE}[[:space:]]*""".*"""/I!s/((${ID})${PRE}[[:space:]]*""").*/\1<masked>/I
/(${ID})${PRE}[[:space:]]*'''.*'''/I!s/((${ID})${PRE}[[:space:]]*''').*/\1<masked>/I
s/(-----BEGIN [A-Z ]*(PRIVATE|SECRET|ENCRYPTED)[A-Z ]*-----).*/\1<masked>/
s/(["'](${IDQ})["'][[:space:]]*:[[:space:]]*)(${STR}|${UNQ})/\1"<masked>"/Ig
s/(${BQD}(${IDQ})${BQD}[[:space:]]*:[[:space:]]*${BQD})([^\\\\]|\\\\[^"'])*${BQD}/\1<masked>${EBD}/Ig
s/(${BQS}(${IDQ})${BQS}[[:space:]]*:[[:space:]]*${BQS})([^\\\\]|\\\\[^"'])*${BQS}/\1<masked>${EBS}/Ig
s/(${BQ}(${IDQ})${BQ}[[:space:]]*:[[:space:]]*)[^\\\\[:space:],}<][^,}[:space:]]*/\1<masked>/Ig
s/(["'][^"']*\\\\u[0-9A-Fa-f]{4}[^"']*["'][[:space:]]*:[[:space:]]*)(${STR}|${UNQ})/\1"<masked>"/g
s/(["'](name|key|var|variable|env)["'][[:space:]]*:[[:space:]]*["'](${IDQ})["'][[:space:]]*,[[:space:]]*["'][A-Za-z_]*["'][[:space:]]*:[[:space:]]*)(${STR}|${UNQ})/\1"<masked>"/Ig
s/([{,][[:space:]]*(${IDB})[[:space:]]*:[[:space:]]*)(${STR}|${UNQ})/\1<masked>/Ig
s#(//[^:/@[:space:]]*:)[^[:space:]]*@#\1<masked>@#g
s#(://)[^:/@[:space:]]{4,}@#\1<masked>@#g
s#((\\\\/){2}[^:/@\\\\[:space:]]*:)[^[:space:]]*@#\1<masked>@#g
s#((\\\\/){2})[^:/@\\\\[:space:]]{4,}@#\1<masked>@#g
s#(^|[[:space:]"'=(])([A-Za-z0-9._-]+:)[^[:space:]@/:"']+@([A-Za-z0-9-]+)#\1\2<masked>@\3#g
s#(Bearer)[[:space:]]+[^[:space:]<"',;)]{4,}#\1 <masked>#Ig
s#(Basic)[[:space:]]+[A-Za-z0-9+/=]{16,}#\1 <masked>#Ig
s/((authorization|proxy-authorization)["']?[[:space:]]*:[[:space:]]*[A-Za-z][A-Za-z0-9-]*[[:space:]]+)[^[:space:]"'<]+/\1<masked>/Ig
s/eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_.-]+/<masked>/g
s/(^|[^A-Za-z0-9_])(sk|pk|rk|pat)-[A-Za-z0-9_-]{8,}/\1<masked>/g
s/(^|[^A-Za-z0-9_])(sk|pk|rk)_(live|test)_[A-Za-z0-9]{8,}/\1<masked>/g
s/(^|[^A-Za-z0-9_])whsec_[A-Za-z0-9]{8,}/\1<masked>/g
s/(^|[^A-Za-z0-9_])AIza[A-Za-z0-9_-]{20,}/\1<masked>/g
s/(^|[^A-Za-z0-9_])(ghp|gho|ghs|ghu)_[A-Za-z0-9]{10,}/\1<masked>/g
s/(^|[^A-Za-z0-9_])github_pat_[A-Za-z0-9_]{10,}/\1<masked>/g
s/(^|[^A-Za-z0-9_])xox[abprs]-[A-Za-z0-9-]{8,}/\1<masked>/g
s/AKIAIOSFODNN7EXAMPLE/<<EXAMPLE-KEY>>/g
s/(AKIA|ASIA)[0-9A-Z]{16}/<masked>/g
s/<<EXAMPLE-KEY>>/AKIAIOSFODNN7EXAMPLE/g
/(curl|wget|http)/I s/((^|[[:space:]])(-u|--user|--proxy-user)(=|[[:space:]]+))(${STR}|[^[:space:]<][^[:space:]]*)/\1<masked>/Ig
s/(^${PFX0}[[:space:]]*(ENV|ARG|SET|SETENV|EXPORT|DECLARE)[[:space:]]+(-[A-Za-z]+[[:space:]]+)*${IDB}[[:space:]]+)[^=[:space:]<].*/\1<masked>/I
s/((${ID})${PRE}[[:space:]]*)(${STR})/\1<masked>/Ig
s/((${ID})${PRE}[[:space:]]*)["'].*/\1<masked>/I
s/((${ID})${PRE}[[:space:]]*)([^=[:space:]<"']|<[^em[:space:]]|<m[^a]|<e[^m]).*/\1<masked>/I
s/(${YPRE}${IDB}["']?[[:space:]]*:[[:space:]]*)(${STR})/\1<masked>/I
s/(${YPRE}${IDB}["']?[[:space:]]*:[[:space:]]*)["'].*/\1<masked>/I
s/(${YPRE}${IDB}["']?[[:space:]]*:[[:space:]]*)([^][{[:space:]<"'|>]|<[^em[:space:]]|<m[^a]|<e[^m]).*/\1<masked>/I
s/((${ID})["']?[[:space:]]*,[[:space:]]*)(${STR})/\1<masked>/Ig
s/((${ID})[[:space:]]+)(${STR})/\1<masked>/Ig
s/((${ID})[[:space:]]+(is|was|are|equals|set to|of)[[:space:]]+)[^[:space:]<"']([^]"')}]|[]"')}][^[:space:]])*/\1<masked>/Ig
s/((${ID})["']?[[:space:]]*:[[:space:]]*)(${STR}|[^][{}[:space:]<"']([^]"')}]|[]"')}][^[:space:]])*)/\1<masked>/Ig
s/((^|[[:space:]])--?([A-Za-z0-9]+[_-])*(keys?|tokens?|secrets?|passw[o0]?r?d|passphrase|pass|passin|passout|pwd|pw|psw|pswd|pat|credentials?|creds?|userpass|auth|bearer)([_-][A-Za-z0-9_-]*)?([[:space:]]+|=))(${STR}|[^[:space:]<-][^[:space:]]*)/\1<masked>/Ig
s/((^|[[:space:]])(machine|default)([[:space:]].*)?[[:space:]](password|passwd|passw0rd|account)[[:space:]]+)[^[:space:]<][^[:space:]]*/\1<masked>/Ig
:pwl
s/(((^|[^A-Za-z0-9_])(${PWCMDS})[^|;&]*[[:space:]]-(p|P))[[:space:]]*)(${STR}|[^[:space:]<-][^[:space:]]*)/\1<masked>/I
s/(((^|[^A-Za-z0-9_])(${PWCMDS_A})[^|;&]*[[:space:]]-(a|w|k|pw|pass))[[:space:]]+)(${STR}|[^[:space:]<-][^[:space:]]*)/\1<masked>/I
tpwl
s@(((^${PFX0}[[:space:]]*([\$]|#|>|RUN|CMD|run:|-)?|[;&|(]|\\\$\\()[[:space:]]*([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*[[:space:]]+)*([^[:space:]|;&]*/)?[a-z][a-z0-9._-]*[[:space:]]([^|;&]*[[:space:]])?-(p|P|w)[[:space:]]+))(${STR}|[0-9:.]*[^0-9:.[:space:]<~/-][^[:space:]]{2,})@\1<masked>@I
s@(^${PFX0}[[:space:]]+-(p|P|w)[[:space:]]+)(${STR}|[0-9:.]*[^0-9:.[:space:]<~/-][^[:space:]]{2,})@\1<masked>@I
s/((^|[[:space:]])(-U|--user|--username)(=|[[:space:]]+)[^[:space:]%<]*%)[^[:space:]<][^[:space:]]*/\1<masked>/Ig
s/((^|[^A-Za-z0-9_])htpasswd[^|;&]*[[:space:]]-[A-Za-z]*b[A-Za-z]*([[:space:]]+[^[:space:]|;&<-][^[:space:]|;&]*)*[[:space:]]+)[^[:space:]|;&<-][^[:space:]|;&]*/\1<masked>/I
s/((^|[^A-Za-z0-9_])(echo|printf)([[:space:]]+-[A-Za-z]+)*[[:space:]]+)[^[:space:]<|;&-][^[:space:]|;&]*([[:space:]]*\|[^|].*(stdin|passwd|password|login|chpasswd|sudo[[:space:]]+-S|kinit|ssh-add|passphrase-fd|cryptsetup))/\1<masked>\5/I
s/((${ID})([[:space:]]+[A-Za-z0-9_]+){1,2}[[:space:]]*:[[:space:]]*)[^[:space:]<"'].*/\1<masked>/Ig
s/(<(${IDB})([[:space:]][^>]*)?>)[^<]+<\//\1<masked><\//Ig
s/((^|[^A-Za-z0-9])[A-Za-z0-9_.-]*(secret|passw[o0]?r?d|passphrase|credential|api[_.-]?key)[A-Za-z0-9_.-]*[[:space:]]*[=!]==?[[:space:]]*)(${STR})/\1<masked>/Ig
s/(<masked>[[:space:]]*(\|\||\?\?|or|:-)[[:space:]]*)(${STR})/\1<masked>/Ig
s/(IDENTIFIED[[:space:]]+(WITH[[:space:]]+[A-Za-z_]+[[:space:]]+)?BY[[:space:]]+)(${STR}|[^[:space:];<][^[:space:];]*)/\1<masked>/Ig
s/(^${PFX0}[[:space:]]*(requirepass|masterauth|auth-pass|bindpw|rootpw)[[:space:]]+)[^[:space:]<=].*/\1<masked>/I
s/(<(${IDB})([[:space:]][^>]*)?>)<!\[CDATA\[([^]]|\][^]]|\]\][^>])*\]\]>/\1<masked>/Ig
s/(^${PFX0}[[:space:]]*(- +)?["']?[A-Za-z0-9_.-]*${STRONG}[A-Za-z0-9_.-]*["']?[[:space:]]+)[^][:space:]<"'=:;,(){}][^[:space:]]*/\1<masked>/I
s/((login|authenticate|authorize|sign_?in|basic_?auth|set_?pass(word)?|add_?user)[[:space:]]*\(([^(),]*,)[[:space:]]*)(${STR})/\1<masked>/Ig
s/((set_?pass(word)?|set_?secret|set_?token|set_?api_?key)[[:space:]]*\([[:space:]]*)(${STR})/\1<masked>/Ig
s/[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+\.)+[A-Za-z]{2,}/<email-masked>/g
EOF
}
# xml_rules: the rules that need a raw < (XML and HTML forms). They run BEFORE the step that turns every raw < into a private byte.
xml_rules() {
  cat <<EOF
s/(<[A-Za-z]+[[:space:]]([^>]*[[:space:]])?(key|name|var|variable|env|id)=["'](${IDQ})["'][[:space:]]+(value|val|data|content)=)(${STR}|[^[:space:]>/<"'][^[:space:]>/]*)/\1"<masked>"/Ig
s/(<(${IDB})([[:space:]][^>]*)?>)<!\[CDATA\[([^]]|\][^]]|\]\][^>])*\]\]>/\1<masked>/Ig
s/(<(${IDB})([[:space:]][^>]*)?>)[^<]+<\//\1<masked><\//Ig
EOF
}
# Stage 2 of the filter: an awk program written to the work folder. It needs only POSIX awk (mawk, gawk, busybox).
write_mask_awk() {
  cat > "$MASKAWK" <<'AWKEOF'
# mask.awk: second masking stage.  -v CUT=240  cut lines longer than CUT characters and say so (0 = never cut).
# What it hides that the sed stage cannot know by name:
#  A  opaque strings: any run of 24 or more letters, digits and + / _ - that holds a letter and a digit
#     (base64, hex, tokens), unless it is a plain lowercase snake_case or kebab-case name, a CamelCase
#     name, or a git or file checksum line this script prints itself. A UUID is hidden.
#  B  mixed words: 12 or more letters and digits in a row with an upper case letter, a lower case letter
#     and a digit that are not a CamelCase name (Vq7Lm2Xp9Rt4 style) are hidden anywhere, also in prose.
#  C  secret-named JSON / YAML containers:  "api_keys": [ ... ]  and  "credentials": { ... }  are hidden up
#     to the matching closing bracket, on the same line or over following lines (at most 100 lines).
#  D  pretty-printed pairs:  "name": "X_TOKEN"  on one line and  "value": "..."  on a nearby line (before
#     or after, same object) hide the value;  - name: API_TOKEN / value: abc  likewise.
#  E  control byte 0x01 (a mark of the sed stage) is removed.
function isid_camel(t,   tmp, n, g, i) {
  if (t !~ /[A-Z]/) return 0
  tmp = t; gsub(/[0-9]+/, " ", tmp)
  n = split(tmp, g, " ")
  for (i = 1; i <= n; i++) if (g[i] !~ /^[a-z]*([A-Z][a-z][a-z]+)*$/) return 0
  return 1
}
function is_uuid(t) {
  return (length(t) == 36 && t ~ /^[0-9a-fA-F]+-[0-9a-fA-F]+-[0-9a-fA-F]+-[0-9a-fA-F]+-[0-9a-fA-F]+$/)
}
function snake_name(t,   n, p, i, d) {
  if (t ~ /[A-Z+\/]/ || t !~ /[_-]/) return 0
  n = split(t, p, /[_-]/); d = 0
  for (i = 1; i <= n; i++) { if (length(p[i]) > 14) return 0; if (p[i] ~ /[0-9]/) d++ }
  return (d <= 2)
}
# blob: 1 = hide, 0 = keep, -1 = split at slashes and judge the pieces
function blob(tok,   n, c) {
  n = length(tok)
  if (n < 16) return 0
  if (tok !~ /[0-9]/ || tok !~ /[A-Za-z]/) return 0
  if (n < 24) return (tok ~ /^[0-9a-fA-F]+$/) ? 1 : 0     # 16 to 23 characters: hidden only when all hex (hex keys, short hashes of keys)
  if (tok ~ /\//) {
    c = substr(tok, 1, 1)
    if (c == "/" || c == "." || c == "~") return -1
    if (tok ~ /[A-Z]/ && tok ~ /[a-z]/) return 1     # v6: from 24 characters (v5: 32): a mixed-case secret with slashes is hidden
    return -1
  }
  if (tok ~ /\./ && length(tok) >= 24 && tok ~ /[A-Z]/ && tok ~ /[a-z]/) return dotted_secret(tok)   # every piece a plain name: kept
  if (is_uuid(tok)) return 1
  if (snake_name(tok)) return 0
  if (tok !~ /[-_+]/ && isid_camel(tok)) return 0
  return 1
}
# dotted_secret: a token with dots (a.b.c, 24 or more characters, upper and lower case and a digit) is hidden whole when
# one of its pieces is not a plain name (plain = lower case word, CamelCase name, digits, 3 characters or fewer)
function dotted_secret(tok,   n, p, i, x) {
  if (length(tok) < 24 || tok !~ /[A-Z]/ || tok !~ /[a-z]/ || tok !~ /[0-9]/) return 0
  n = split(tok, p, ".")
  for (i = 1; i <= n; i++) {
    x = p[i]
    if (length(x) <= 3 || x ~ /^[0-9]+$/ || x ~ /^[a-z0-9_-]+$/) continue
    if (isid_camel(x) || x ~ /^[A-Z]?[a-z]+([A-Z][a-z]+)*[0-9]*$/) continue
    return 1
  }
  return 0
}
function shape(tok,   out, st, ln, r) {
  out = ""
  while (match(tok, /[A-Za-z0-9]+/)) {
    st = RSTART; ln = RLENGTH; r = substr(tok, st, ln)
    out = out substr(tok, 1, st - 1)
    if (ln >= 12 && r ~ /[A-Z]/ && r ~ /[a-z]/ && r ~ /[0-9]/ && !isid_camel(r)) out = out "<masked-token>"; else out = out r
    tok = substr(tok, st + ln)
  }
  return out tok
}
function piece(tok,   r, n, parts, i, o) {
  r = blob(tok)
  if (r == 1) return "<masked-blob>"
  if (r == -1) {
    n = split(tok, parts, "/"); o = ""
    for (i = 1; i <= n; i++) o = o (i > 1 ? "/" : "") piece(parts[i])
    return o
  }
  if (tok ~ /\./ && tok !~ /\//) {
    n = split(tok, parts, "."); o = ""
    for (i = 1; i <= n; i++) o = o (i > 1 ? "." : "") piece_nodot(parts[i])
    return o
  }
  return shape(tok)
}
function piece_nodot(tok,   r) {
  r = blob(tok)
  if (r == 1) return "<masked-blob>"
  return shape(tok)
}
function genmask(s,   out, st, ln, tok, tail) {
  out = ""
  while (match(s, /[A-Za-z0-9+\/_.-]+/)) {
    st = RSTART; ln = RLENGTH; tok = substr(s, st, ln)
    tail = ""
    while (length(tok) > 1 && substr(tok, length(tok), 1) == ".") { tail = tail "."; tok = substr(tok, 1, length(tok) - 1) }
    out = out substr(s, 1, st - 1) piece(tok) tail
    s = substr(s, st + ln)
  }
  return out s
}
# camel_split: put a space before each upper case letter that follows a lower case letter or a digit (accessToken -> access Token)
function camel_split(k,   i, n, c, p, o) {
  o = ""; n = length(k); p = ""
  for (i = 1; i <= n; i++) {
    c = substr(k, i, 1)
    if (c ~ /[A-Z]/ && p ~ /[a-z0-9]/) o = o " "
    o = o c; p = c
  }
  return o
}
# secret_name: ONE general rule. A name is secret when a STRONG word (secret, password, passwd, passphrase, credential,
# token, apikey) is anywhere in it, or it holds a WEAK whole word (key, pass, pat, auth, cookie, session, signature, hmac,
# dsn, webhook, salt, otp, cert, ...) alone or followed by value / string / data / text / hash / bytes / material, or a
# word ends in key, token, secret, password, pwd or credential. Token counters (max_tokens ...) and tokenizer are not secret.
function secret_name(k,   n, w, i, x, joined) {
  k = camel_split(k)
  k = tolower(k)
  gsub(/0/, "o", k)    # passw0rd, s3cret style spellings: a zero is read as the letter o
  gsub(/[^a-z0-9]+/, " ", k)
  n = split(k, w, " ")
  joined = ""
  for (i = 1; i <= n; i++) {
    x = w[i]
    if (x ~ /^(max|num|total|prompt|completion|input|output|cached|reserved)tokens$/) continue
    if (x == "tokens" && i > 1 && w[i - 1] ~ /^(max|num|n|total|prompt|completion|input|output|cached|reserved|cache)$/) continue
    if (x ~ /^tokeniz|^tokenis/) continue
    joined = joined x
    if (x in SW) return 1
    if (x ~ /^(db|root|admin|user|mysql|pg|redis|master|ssh|smtp|mail|ldap|sql|wifi|wpa|sys|login)(pass|pw|pwd)$/) return 1
    if (x ~ /(key|keys|token|tokens|secret|secrets|password|passwords|passwd|passwds|pwd|credential|credentials)$/) return 1
    if (x ~ /^(key|keys|pass|pwd|pw|pat|auth|cookie|cookies|session|sessions|signature|hmac|dsn|webhook|salt|otp|cert|certs)(value|string|data|text|hash|bytes|material|id|url|uri|name|code|list|file|path|ring|store)$/) return 1
  }
  if (joined ~ /(secret|passw(or)?d|passphrase|credential|token|apikey|requirepass|masterauth|jsessionid|phpsessid)/) return 1
  return 0
}
# find the bracket that closes a container; CD/CQ keep the depth and quote when the line ends first
function find_close(s, i, depth, inq,   c, n) {
  n = length(s)
  for (; i <= n; i++) {
    c = substr(s, i, 1)
    if (inq != "") {
      if (c == "\\") { i++; continue }
      if (c == inq) inq = ""
      continue
    }
    if (c == "\"" || c == "'") { inq = c; continue }
    if (c == "[" || c == "{") depth++
    else if (c == "]" || c == "}") { depth--; if (depth == 0) { CD = 0; CQ = ""; return i } }
  }
  CD = depth; CQ = inq
  return 0
}
function hide_containers(s,   out, key, kk, open, j, st, ln) {
  out = ""
  if (CD > 0) {
    # a secret container that is still open: hide every line until it closes (or a "--" separator or the end of the
    # input). It never prints the rest raw, however many lines it takes (fail closed).
    j = find_close(s, 1, CD, CQ)
    if (j == 0) return "<masked>"
    return "<masked>" substr(s, j)
  }
  while (match(s, /(["'][^"']*["']|[A-Za-z0-9_.-]+)[ \t]*:[ \t]*[[{]/)) {
    st = RSTART; ln = RLENGTH
    key = substr(s, st, ln)
    sub(/[ \t]*:[ \t]*[[{]$/, "", key)
    kk = key; gsub(/["']/, "", kk)
    open = st + ln - 1
    out = out substr(s, 1, open)
    if (secret_name(kk)) {
      j = find_close(s, open + 1, 1, "")
      out = out "<masked>"
      if (j == 0) return out
      s = substr(s, j)
    } else {
      s = substr(s, open + 1)
    }
  }
  return out s
}
function is_nameline(b,   t, v) {
  t = tolower(b)
  if (t !~ /^[ \t]*(- +)?[{,]?[ \t]*["']?(name|key|var|variable|env|envvar|header|field)["']?[ \t]*:/) return 0
  v = b; sub(/^[^:]*:/, "", v); sub(/^[ \t"']+/, "", v); sub(/[]}, \t"']+$/, "", v)
  if (v == "") return 0
  if (v == "<masked>") return 1
  if (v ~ /[^A-Za-z0-9_. -]/) return 0
  return secret_name(v)
}
function is_valueline(b) {
  return (tolower(b) ~ /^[ \t]*(- +)?[{,]?[ \t]*["']?(value|val|secret|content|data|string|text)["']?[ \t]*:/)
}
function mask_after_colon(b,   p, head, rest, c, q, i, n, ch, j) {
  p = index(b, ":")
  head = substr(b, 1, p); rest = substr(b, p + 1)
  sub(/^[ \t]*/, "", rest)
  c = substr(rest, 1, 1)
  if (c == "[" || c == "{") {
    j = find_close(rest, 2, 1, "")
    if (j == 0) return head " <masked>"
    return head " <masked>" substr(rest, j + 1)
  }
  if (c == "\"" || c == "'") {
    q = c; n = length(rest)
    for (i = 2; i <= n; i++) { ch = substr(rest, i, 1); if (ch == "\\") { i++; continue }; if (ch == q) break }
    return head " <masked>" substr(rest, i + 1)
  }
  match(rest, /^[^]},]*/)
  return head " <masked>" substr(rest, RLENGTH + 1)
}
# yaml_continue: a line that names a secret as a YAML key keeps hiding the lines under it that are indented deeper
# (a multi-line quoted or plain value, or a block value whose header the sed stage did not see)
function indent_of(b,   t) { t = b; sub(/^[ \t]*/, "", t); return length(b) - length(t) }
function yaml_continue(b,   t, ind, nm) {
  if (b ~ /^[ \t]*$/) return b
  ind = indent_of(b)
  if (YIND >= 0) {
    if (ind > YIND) return "<masked>"
    YIND = -1
  }
  t = b
  while (match(t, /^[ \t]*- +/)) t = substr(t, RLENGTH + 1)
  if (match(t, /^[ \t]*["']?[A-Za-z0-9_.-]+["']?[ \t]*:/)) {
    nm = substr(t, 1, RLENGTH)
    sub(/^[ \t]*["']?/, "", nm); sub(/["']?[ \t]*:$/, "", nm)
    if (secret_name(nm)) YIND = length(b) - length(t) + indent_of(t)
  }
  return b
}

# ---------------------------------------------------------------- pre-stage (-v MODE=pre), runs BEFORE the sed stage
#  P1  length guard: a line longer than MAXL characters is cut to MAXL before the sed stage sees it (bounded time); the
#      true length is added as  \005 LENGTH \005  at the end, and a line is appended to the file CF (a count for the summary).
#  P2  a name that holds a byte outside plain ASCII (a zero-width space inside  pass<ZWSP>word, a look-alike letter, a
#      non-English name) followed by  =  or  :  is renamed NONASCII_NAME_SECRET, so the sed stage hides its value (fail closed).
#  P3  a secret-named assignment that opens a bracket it does not close on the line  NAME = (  [  {  $(  , or that ends in a
#      backslash: every following line is hidden until the brackets close (or the backslash chain ends, or a "--" separator, or
#      the end of the input). It never prints the rest raw, however many lines it takes (fail closed).
function ml_scan(s,   i, n, c, pc) {
  n = length(s)
  for (i = 1; i <= n; i++) {
    c = substr(s, i, 1)
    if (ML_Q != "") { if (c == "\\") { i++; continue } ; if (c == ML_Q) ML_Q = ""; continue }
    if (c == "\"" || c == "'") { ML_Q = c; continue }
    if (c == "#") { pc = (i > 1) ? substr(s, i - 1, 1) : " "; if (pc ~ /[ \t]/) break; continue }
    if (c == "(" || c == "[" || c == "{") ML_D++
    else if (c == ")" || c == "]" || c == "}") { ML_D--; if (ML_D <= 0) { ML_D = 0; ML_Q = ""; return } }
  }
}
function nonascii_names(s,   out, st, ln, m) {
  out = ""
  while (match(s, /[A-Za-z0-9_.\200-\377-]*[\200-\377][A-Za-z0-9_.\200-\377-]*["' \t]*[=:]/)) {
    st = RSTART; ln = RLENGTH; m = substr(s, st, ln)
    match(m, /["' \t]*[=:]$/)
    out = out substr(s, 1, st - 1) "NONASCII_NAME_SECRET" substr(m, RSTART)
    s = substr(s, st + ln)
  }
  return out s
}
function ml_start(b,   m, nm, rest, sec, t, tk) {
  sec = 0; rest = b
  if (match(b, /^[ \t]*((export|set|local|declare|readonly|var|let|const)[ \t]+(-[A-Za-z]+[ \t]+)?)?((self|this)\.)?["']?[]A-Za-z0-9_.[-]+["']?\]?[ \t]*(\+?=|:=)[ \t]*/)) {
    m = substr(b, 1, RLENGTH); rest = substr(b, RLENGTH + 1)
    nm = m
    sub(/[ \t]*(\+?=|:=)[ \t]*$/, "", nm)
    sub(/^[ \t]*((export|set|local|declare|readonly|var|let|const)[ \t]+(-[A-Za-z]+[ \t]+)?)?((self|this)\.)?/, "", nm)
    gsub(/["'\]]/, "", nm)
    sec = secret_name(nm)
  }
  if (sec && rest ~ /\\[ \t]*$/) { MLBS = 1; return }
  ML_D = 0; ML_Q = ""
  ml_scan(b)
  if (ML_D <= 0) { ML_D = 0; ML_Q = ""; return }
  if (!sec) {
    # the line opens a bracket it does not close: it is hidden onward when ANY name before an = or : on it is a secret name
    t = b
    while (match(t, /[A-Za-z0-9_.-]+["' \t]*[=:]/)) {
      tk = substr(t, RSTART, RLENGTH); sub(/["' \t]*[=:]$/, "", tk)
      rest = substr(t, RSTART + RLENGTH)
      # NAME: [ or NAME: {  is a container the awk stage already tracks to its closing bracket: leave it to that stage
      if (secret_name(tk) && !(substr(t, RSTART + RLENGTH - 1, 1) == ":" && rest ~ /^[ \t]*[[{]/)) { sec = 1; break }
      t = rest
    }
  }
  if (!sec) { ML_D = 0; ML_Q = "" }
}
# ctl_strip (v8, MAJ-1 / MIN-1): control bytes can hide text on a terminal (ESC sequences, a bare CR that returns to the start of the
# line, backspace) and can split a secret name (pass<byte>word). Removed: a CR at the end of the line (a CRLF file), every other byte
# 0x01-0x08, 0x0B-0x1F and 0x7F (a TAB stays), and the bidirectional controls (UTF-8 of U+200E, U+200F, U+202A-U+202E, U+2066-U+2069,
# U+061C), which can reorder what is shown. CTLN = how many were removed (a CRLF line end is not counted).
function ctl_strip(s,   t, n) {
  CTLN = 0
  sub(/\015+$/, "", s)
  if (s ~ /[\001-\010\013-\037\177]/) { t = s; CTLN = gsub(/[\001-\010\013-\037\177]/, "", t); s = t }
  if (s ~ /\342[\200\201]|\330\234/) { t = s; n = gsub(/\342\200[\216\217\252-\256]|\342\201[\246-\251]|\330\234/, "", t); if (n > 0) { CTLN += n; s = t } }
  return s
}
# decode_forms (v8, MIN-5): HTML entities and URL escapes for the quote, equals, less-than and greater-than signs are turned into the
# plain character BEFORE the sed stage, so the name rules see the same text a reader would. (The printed line shows the plain character.)
function decode_forms(t,   o) {
  if (index(t, "&") > 0) {
    gsub(/&[Qq][Uu][Oo][Tt];|&#0*34;|&#[xX]0*22;/, "\"", t)
    gsub(/&[Aa][Pp][Oo][Ss];|&#0*39;|&#[xX]0*27;/, "'", t)
    gsub(/&[Ll][Tt];|&#0*60;|&#[xX]0*3[Cc];/, "<", t)
    gsub(/&[Gg][Tt];|&#0*62;|&#[xX]0*3[Ee];/, ">", t)
  }
  if (index(t, "%") > 0) {
    gsub(/%3[Dd]/, "=", t); gsub(/%22/, "\"", t); gsub(/%27/, "'", t)
  }
  # a < that starts the text of one of our own marks, in the INPUT, is turned into STX at once (the sed stage turns the other raw < later):
  # the input cannot pass as "already hidden". The main stage turns STX back into <, so the line is printed as it was.
  if (index(tolower(t), "<masked") > 0 || index(tolower(t), "<email-masked") > 0) {
    o = ""
    while (match(t, /<([Mm][Aa][Ss][Kk][Ee][Dd]|[Ee][Mm][Aa][Ii][Ll]-[Mm][Aa][Ss][Kk][Ee][Dd])/)) {
      o = o substr(t, 1, RSTART - 1) "\002" substr(t, RSTART + 1, RLENGTH - 1)
      t = substr(t, RSTART + RLENGTH)
    }
    t = o t
  }
  return t
}
function pre_line(   t, pfx, body, hid, cn, tag) {
  PRE_N++
  t = ctl_strip($0); cn = CTLN
  t = decode_forms(t)
  n0 = length(t)
  if (n0 > MAXL) { t = substr(t, 1, MAXL); if (CF != "") { print n0 >> CF; close(CF) } }
  pfx = ""; body = t
  if (match(t, /^(([^:]+[:-])?[0-9]+[-:])/)) { pfx = substr(t, 1, RLENGTH); body = substr(t, RLENGTH + 1) }
  if (body == "--") { ML_D = 0; ML_Q = ""; MLBS = 0 }
  hid = 0
  if (MLBS) { MLBS = (body ~ /\\[ \t]*$/); hid = 1 }
  else if (ML_D > 0) { ml_scan(body); hid = 1 }
  if (hid) body = "<masked>"
  else {
    if (body ~ /[\200-\377]/) body = nonascii_names(body)
    ml_start(body)
  }
  tag = ""
  if (cn > 0) tag = " [control bytes removed: " cn "]"
  t = pfx body tag
  if (n0 > MAXL) t = t "\005" n0 "\005"
  print t
}
function emit(k,   o, n) {
  o = PFXS[k] BODYS[k]
  n = LEN[k]
  if (CUT > 0 && (length(o) > CUT || n > WIN)) {
    if (n <= WIN) n = length(o)
    if (ATL[k]) n = "at least " n
    o = substr(o, 1, CUT) " ...[CUT: this line has " n " characters; the rest is not shown]"
  }
  print o
}
BEGIN {
  nsw = split("key keys token tokens secret secrets password passwords passwd passwds passphrase passphrases pass pwd pw pws psw pswd pat credential credentials authorization auth bearer private apikey apikeys cookie cookies session sessions signature signatures hmac dsn webhook webhooks salt otp cert certs certificate certificates", sw, " ")
  for (i = 1; i <= nsw; i++) SW[sw[i]] = 1
  WIN = (CUT > 0) ? CUT + 360 : 100000
  head = 1; tail = 0; pend = 0; CD = 0; CQ = ""; YIND = -1
  ML_D = 0; ML_Q = ""; MLBS = 0
}
MODE == "pre" { pre_line(); next }
{
  line = $0
  gsub(/\001/, "", line)
  gsub(/\002/, "<", line)          # v8: the sed stage turned every raw < into STX (see write_mask_sed); it is turned back here
  nmark = 0
  if (match(line, /\005[0-9]+\005$/)) { nmark = substr(line, RSTART + 1, RLENGTH - 2) + 0; line = substr(line, 1, RSTART - 1) }
  line = ctl_strip(line)             # v8: the same control-byte removal in the final stage (also the final belt over the whole output)
  n0 = length(line); atl = 0
  if (nmark > n0) n0 = nmark
  else if (MAXL > 0 && n0 >= MAXL) atl = 1
  if (n0 > WIN) line = substr(line, 1, WIN)
  pfx = ""; body = line
  if (match(line, /^(([^:]+[:-])?[0-9]+[-:])/)) {
    pfx = substr(line, 1, RLENGTH); body = substr(line, RLENGTH + 1)
    if (pfx !~ /^[0-9]+[-:]$/) pfx = genmask(pfx)   # a long prefix may have swallowed text: it is masked too (path pieces stay readable)
  }
  keep = 0
  # a checksum line that THIS script printed itself (R00) stays readable: it must equal, character for character, a line
  # the script wrote to the file OKF. A line that only LOOKS like a checksum line (a hex string and two spaces, from a
  # searched file) is not in that file and is masked like any other text.
  if (OKF != "" && pfx == "" && (body ~ /^[0-9a-f]+  / || body ~ /^HEAD: [0-9a-f]+$/)) {
    while ((getline okl < OKF) > 0) if (okl == body) { keep = 1; break }
    close(OKF)
  }
  if (body == "--") { CD = 0; CQ = ""; YIND = -1 }
  if (!keep) {
    body = yaml_continue(body)
    body = hide_containers(body)
    namel = is_nameline(body)
    if (pend > 0) {
      if (is_valueline(body)) { body = mask_after_colon(body); pend = 0 } else pend--
    }
    if (namel) {
      pend = 3
      for (k = tail; k >= head && k >= tail - 2; k--) {
        if (is_valueline(BODYS[k])) { BODYS[k] = mask_after_colon(BODYS[k]); break }
        if (BODYS[k] ~ /[{}]/) break
      }
    }
    body = genmask(body)
  }
  tail++; PFXS[tail] = pfx; BODYS[tail] = body; LEN[tail] = n0; ATL[tail] = atl
  while (tail - head >= 3) { emit(head); delete PFXS[head]; delete BODYS[head]; delete LEN[head]; delete ATL[head]; head++ }
}
END {
  if (MODE == "pre") exit
  while (head <= tail) { emit(head); delete PFXS[head]; delete BODYS[head]; delete LEN[head]; delete ATL[head]; head++ }
}
AWKEOF
}

# the rule files must exist, be non-empty and be accepted by this sed and awk; otherwise nothing may print
filter_ready() {
  [ -s "$MASKSED" ] && [ -s "$MASKLINE" ] && [ -s "$MASKAWK" ] || return 1
  [ "$(printf 'AbC key=zz\n' | sed -E -f "$MASKSED" 2>/dev/null)" = "AbC key=<masked>" ] || return 1
  [ "$(printf 'AbC key=zz\n' | sed -E -f "$MASKLINE" 2>/dev/null)" = "AbC key=<masked>" ] || return 1
  [ "$(printf 'AbC\n' | sed -E 's/abc/X/I' 2>/dev/null)" = "X" ] || return 1
  [ "$(printf 'plain text\n' | awk -v CUT=240 -f "$MASKAWK" 2>/dev/null)" = "plain text" ] || return 1
  return 0
}

# mask: hide secrets FIRST (name rules, on the whole line), then the awk stage (opaque strings, containers),
# which also cuts long lines and SAYS that the line was cut. A NUL byte would make some tools stop reading a
# line, so it is shown as ? first.
# v8: every stage of the filter reports a failure (not killed by a closed pipe) in $WORK/mask.fail, so a failing stage is not silent
# (the filter then prints less, never more); the end of a run and --mask read that file and stop with exit 4.
mstage() { "$@"; ms_rc=$?; case $ms_rc in 0|141) ;; *) printf '%s %s\n' "$1" "$ms_rc" >> "$WORK/mask.fail" 2>/dev/null ;; esac; return 0; }
mask() {
  mstage tr '\000' '\001' | mstage awk -v MODE=pre -v MAXL=20000 -v CF="$LENCUT" -f "$MASKAWK" | mstage sed -E -f "$MASKSED" | mstage awk -v CUT=240 -v MAXL=20000 -f "$MASKAWK"
}
# mask_line: the line rules only plus the awk stage: the final belt over the whole output
mask_line() { mstage sed -E -f "$MASKLINE" | mstage awk -v CUT=1000 -v OKF="$SHAOK" -f "$MASKAWK"; }
# ---------------------------------------------------------------- self-test (also the canary that runs first in every run)
# Four views of every case: (full) the whole filter = what a search prints; (L) the line rules plus awk = the
# final belt over the whole output; (S) the sed stage alone, so a rule of the sed stage cannot hide behind the awk
# stage; (A) the awk stage alone, so a rule of the awk stage cannot hide behind the sed stage; (M) full filter only
# (multi-line JSON / YAML rules, which need the awk stage and the sed stage together).
# self_test QUIET   (QUIET=1: print only FAIL lines and the tally)
# skip_report ROOT LABEL KIND(code|json): print the count of EVERY category of file the lists leave out,
# so a silent drop cannot hide (a "0 matching lines" can then be told apart from "never looked").
skip_report() {
  sr_root=$1; sr_label=$2; sr_kind=$3
  [ -d "$sr_root" ] || { printf 'left out of "%s": folder %s not found\n' "$sr_label" "$sr_root"; return; }
  ( [ -n "$sr_root" ] && cd "$sr_root" || exit 0
    if [ "$sr_kind" = json ]; then NM='-name *.json'; else NM='-name *.py -o -name *.sh'; fi
    set -f
    printf 'left out of "%s" (%s) and NOT searched, file counts by reason:\n' "$sr_label" "$sr_root"
    sr_n=$(find . -mindepth 5 -type f \( $NM \) -print 2>/dev/null | wc -l | tr -d ' ')
    printf '  path of 5 or more parts (a/b/c/d/file; the search goes at most 3 sub-folders down): %s\n' "$sr_n"
    sr_n=$(find . -type l -print 2>/dev/null | wc -l | tr -d ' ')
    printf '  symbolic links of any kind (find does not follow them): %s\n' "$sr_n"
    sr_n=$(find . 2>&1 >/dev/null | grep -c -i 'permission denied')
    printf '  folders or files the find command could not open (permission denied): %s\n' "$sr_n"
    sr_n=$(find . -name "*${NL}*" -print0 2>/dev/null | tr -cd '\000' | wc -c | tr -d ' ')
    printf '  names with a line break (cannot be listed safely): %s\n' "$sr_n"
    for sr_d in node_modules _local secrets .venv venv __pycache__ tests test; do
      if [ "$sr_kind" = json ] && { [ "$sr_d" = tests ] || [ "$sr_d" = test ]; }; then continue; fi
      sr_n=$(find . -path "*/$sr_d/*" -type f \( $NM \) -print 2>/dev/null | wc -l | tr -d ' ')
      printf '  files inside folders called %s, count %s\n' "$sr_d" "$sr_n"
    done
    sr_n=$(find . -type f ! \( $NM \) -print 2>/dev/null | wc -l | tr -d ' ')
    printf '  files of other types (not searched at all, whatever their content or name; this one number is every file that is not a %s file): %s\n' "$( [ "$sr_kind" = json ] && echo json || echo 'python or shell')" "$sr_n"
    if [ "$sr_kind" != json ]; then
      sr_n=$(find . -type f \( -name 'test_*' -o -name '*_test.py' -o -name conftest.py \) -not -path '*/tests/*' -not -path '*/test/*' -not -path '*/node_modules/*' -not -path '*/_local/*' -not -path '*/secrets/*' -not -path '*/.venv/*' -not -path '*/venv/*' -print 2>/dev/null | wc -l | tr -d ' ')
      printf '  test files outside tests folders (test_*, *_test.py, conftest.py): %s\n' "$sr_n"
    fi
  )
}
self_test() {
  st_quiet=${1:-0}
  p1=qzvx; p2=kwlp; p3=jrmn
  base=$p1$p2$p3
  r1=fhdg; r2=tbcw; r3=syvx; base2=$r1$r2$r3
  a1=AK; a2=IA; fakeid=${a1}${a2}ABCD1234EFGH5678
  gh1=gh; gh2=p_
  em1=jane; em2=.roe; em3=@example; em4=.test; fakemail=$em1$em2$em3$em4
  in=$WORK/st-in.txt; res=$WORK/st-out.txt; res2=$WORK/st-out2.txt; res3=$WORK/st-out3.txt; res4=$WORK/st-out4.txt
  long=$(awk 'BEGIN{for(i=0;i<300;i++) printf "x"}')
  pad=$(awk 'BEGIN{for(i=0;i<200;i++) printf "x"}')
  pad2=$(awk 'BEGIN{for(i=0;i<228;i++) printf "x"}')
  q3='"""'
  j1=eyJ
  b1=VnE3; b2=TG0y; b3=WHA5; b4=UnQ0; blob16=$b1$b2$b3$b4
  blob=$blob16$blob16$blob16$blob16$blob16
  m1=Vq7L; m2=m2Xp; m3=9Rt4; m4=Z1; mixed=$m1$m2$m3$m4
  u1=123e4567; u2=e89b; u3=12d3; u4=a456; u5=426614174000; uuid=$u1-$u2-$u3-$u4-$u5
  h4=ab12; h16=$h4$h4$h4$h4; sha64=$h16$h16$h16$h16; sha40=$h16$h16$h4$h4
  g4=cd34; g16=$g4$g4$g4$g4; hex64=$g16$g16$g16$g16
  printf '%s  some_file.py\nHEAD: %s\n' "$sha64" "$sha40" > "$SHAOK"
  {
    printf 'API_KEY=%s_1_\n' "$base"
    printf 'export MY_TOKEN=%s_2_\n' "$base"
    printf 'password = "%s_3_"\n' "$base"
    printf '{"api_key": "%s_4_", "other": 1}\n' "$base"
    printf '{"client_secret":"%s_5_"}\n' "$base"
    printf 'Authorization: Bearer %s_6_\n' "$base"
    printf 'header Bearer %s_7_ end\n' "$base"
    printf 'value sk-%s_8_ here\n' "$base"
    printf 'value pat-%s_9_ here\n' "$base"
    printf 'value %s%s_10_Abcdef here\n' "$gh1$gh2" "$base"
    printf '11:db_password:\n'
    printf '12-    %s_11_\n' "$base"
    printf '13-other: fine\n'
    printf 'secret: |\n  %s_12a_\n  %s_12b_\nnext_line: stays\n' "$base" "$base"
    printf 'url https://user:%s_13_@host.example/path\n' "$base"
    printf 'id %s\n' "$fakeid"
    printf 'passwd: %s_14_\n' "$base"
    printf 'pwd=%s_15_\n' "$base"
    printf 'credential = %s_16_\n' "$base"
    printf '%s token=%s_17_\n' "$pad" "$base"
    printf '%s token = "%s_17b_"\n' "$pad2" "$base"
    printf '%s\n' "$long"
    printf '{"api_key": "%s_18_", "nodes": [{"method": "DELETE"}]}\n' "$base"
    printf 'x = call(token="%s_19_") # delete path\n' "$base"
    printf 'if key == "end":\n'
    printf 'answer = "end"\n'
    printf 'literal AKIAIOSFODNN7EXAMPLE stays\n'
    printf 'plain line with the word end in it\n'
    # ---- v3 additions: forms the v2 filter missed
    printf 'PASS=%s_20_\n' "$base"
    printf 'passphrase: %s_21_\n' "$base"
    printf 'pat = %s_22_\n' "$base"
    printf 'os.environ["X_TOKEN"] = "%s_23_"\n' "$base"
    printf 'v = cfg.get("API_KEY", "%s_24_")\n' "$base"
    printf 'pair = ("API_KEY", "%s_25_")\n' "$base"
    printf 'run --token %s_26_ --verbose\n' "$base"
    printf 'run --password %s_27_\n' "$base"
    printf 'run --api-key=%s_28_ --other\n' "$base"
    printf 'password = %s%s_29_%s # tail29\n' "$q3" "$base" "$q3"
    printf 'secret = %s\n%s_30a_\n%s_30b_\n%s\nafter_multiline = kept\n' "$q3" "$base" "$base" "$q3"
    printf 'token = "%s_31_\n' "$base"
    printf 'contact %s here\n' "$fakemail"
    printf '{"name": "X_TOKEN", "value": "%s_33_"}\n' "$base"
    printf "{'api_key': '%s_34_', 'n': 2}\n" "$base"
    printf 'self.token = %s_35_\n' "$base"
    printf 'accessToken: %s_36_\n' "$base"
    printf 'apiKey = %s_37_\n' "$base"
    printf 'X-Api-Key: %s_38_\n' "$base"
    printf "const o = {token: '%s_39_', n: 3}\n" "$base"
    printf 'export X_PASSWORD=%s_40_\n' "$base"
    printf 'archive_pw = %s%s_42_\n%s_43_\n%s # tail42\n' "$q3" "$base" "$base" "$q3"
    printf 'db_pswd: %s_44_\n' "$base"
    printf 'secret = %s%s_41a_\n%s_41b_\n%s\n' "'''" "$base" "$base" "'''"
    printf "line_after_triple = %s\n" 'kept2'
    # ---- v3 false-hide cases: evidence that must stay readable
    printf 'if token:\n    return kept_after_if_token\n'
    printf 'author: Someone Else\ntitle: kept_after_author\n'
    printf 'if not key_file:\n    raise kept_after_key_file\n'
    printf 'author = Someone\n'
    printf 'names desk-aaaaaaaaaaaa task-bbbbbbbbbbbb risk-cccccccccccc mask-dddddddddddd compat-eeeeeeeeeeee end\n'
    printf 'max_tokens = 100\n'
    printf 'tokenizer = fine\n'
    printf 'if token == "end":\n'
    printf 'bypass = 1\n'
    # ---- v4 additions: forms the v3 filter missed
    printf 'data = "%s"\n' "$blob"
    printf 'payload: %s\n' "$blob"
    printf 'x = 1  # id %s\n' "$mixed"
    printf 'note: value %s in a sentence\n' "$mixed"
    printf 'see %s for details\n' "$uuid"
    printf 'curl -H "X-Auth-Token: %s_44a_" https://example.invalid/\n' "$base"
    printf "curl -H 'Authorization: token %s_44b_'\n" "$base"
    printf 'ENV TOKEN %s_44c_\n' "$base"
    printf 'passwd "%s_44d_"\n' "$base"
    printf 'API_KEYS=%s_45a_\n' "$base"
    printf 'PASSWORDS: %s_45b_\n' "$base"
    printf 'AUTH_TOKENS = %s_45c_\n' "$base"
    printf 'ALLOWED_API_KEYS=%s_45d_\n' "$base"
    printf 'tokens = %s_45e_\n' "$base"
    printf 'note Password: %s_46a_ end\n' "$base"
    printf 'echo "Api-Key: %s_46b_"\n' "$base"
    printf 'lib/x.py:21:db_password:\nlib/x.py-22-    %s_47a_\nlib/x.py-23-other: kept_pfx_path\n' "$base"
    printf 'lib/x.py:24:token: %s_47b_\n' "$base"
    printf '{\n  "name": "X_TOKEN",\n  "value": "%s_48a_"\n}\n' "$base"
    printf '{\n  "value": "%s_48b_",\n  "name": "API_TOKEN"\n}\n' "$base"
    printf -- '- name: API_TOKEN\n  value: %s_48c_\n' "$base"
    printf '"api_keys": ["%s_49a_", "%s_49b_"]\n' "$base" "$base"
    printf '"tokens": [\n  "%s_49c_",\n  "%s_49d_"\n],\n"after_list": "kept_after_array"\n' "$base" "$base"
    printf '"credentials": {"a": {"b": "%s_49e_"}, "c": "%s_49f_"}, "n_obj": "kept_after_obj"\n' "$base" "$base"
    printf 'password = "%s_50a_\\"%s_50_"\n' "$base" "$base2"
    printf 'password = "%s_51a_" "%s_51b_"\n' "$base" "$base2"
    printf "secret = '%s_51c_' + \"%s_51d_\"\n" "$base" "$base2"
    printf -- '-----BEGIN PRIVATE KEY-----\n%s_52a_\n%s_52b_\n-----END PRIVATE KEY-----\nkept_after_pem\n' "$base" "$base"
    printf 'key sk_live_%s_53_ here\n' "$base"
    printf 'curl -u admin:%s_54_ https://example.invalid/\n' "$base"
    printf 'the password is %s_55_ ok\n' "$base"
    printf 'sess %s.%s.%s_56_\n' "${j1}${base}" "$base2" "$base"
    printf 'caf\351 API_KEY=%s_57_\n' "$base"
    printf 'a\000b token=%s_58_\n' "$base"
    printf 'cfg: {"api_key": "%s_59_"}\n' "$base"
    # ---- v4 evidence that must stay readable
    printf 'test_qs_37_refuses_after_window_end kept_snake\n'
    printf 'calls getOauth2AccessTokenForHubspotUser kept_camel\n'
    printf '%s  some_file.py\n' "$sha64"
    printf 'HEAD: %s\n' "$sha40"
    printf '%s  trailing words\n' "$hex64"
    printf 'max_tokens = 100\nprompt_tokens: 12\ncompletion_tokens=4\ntotal_tokens = 9\nnum_tokens=3\ninput_tokens: 5\noutput_tokens = 6\nmax_output_tokens = 7\n'
    printf 'name: kept_name_line\nvalue: kept_value_line_alone\n'

    # ---- v5 additions: classes the v4 filter missed (every value is built from parts; a check looks at its first 6 and last 6 characters)
    : > "$WORK/st-pt.txt"
    vn=0
    for cls in at sl sc cm sp up dg; do
      for ctx in 1 2 3 4 5 6 7; do
        case $cls$ctx in sp6) continue ;; esac
        vn=$((vn + 1))
        case $cls in
          up) hd=$(printf 'KQ%02dZV' "$vn"); tl=$(printf 'WM%02dXD' "$vn"); vv=$hd$tl ;;
          dg) hd=$(printf '48%02d71' "$vn"); tl=$(printf '33%02d95' "$vn"); vv=$hd$tl ;;
          *) hd=$(printf 'kq%02dzv' "$vn"); tl=$(printf 'wm%02dxd' "$vn")
             case $cls in at) sep=@ ;; sl) sep=/ ;; sc) sep=';' ;; cm) sep=, ;; sp) sep=' ' ;; esac
             vv=$hd$sep$tl ;;
        esac
        case $ctx in
          1) printf 'API_KEY=%s\n' "$vv" ;;
          2) printf 'note Password: %s end\n' "$vv" ;;
          3) printf 'the password is %s ok\n' "$vv" ;;
          4) printf 'password: %s\n' "$vv" ;;
          5) printf 'passphrase = %s\n' "$vv" ;;
          6) printf 'url https://user:%s@host.example/p\n' "$vv" ;;
          7) printf '{"api_key": "%s"}\n' "$vv" ;;
        esac
        printf '%s|%s|%s|%s\n' "$cls$ctx" "$hd" "$tl" LS >> "$WORK/st-pt.txt"
      done
    done
    # names with the secret word anywhere (also cookie, session, signature, hmac, dsn, webhook, salt, otp, cert)
    for nm in secretValue tokenString passwordHash authTokenValue keyValue secretdata cookie session_id sessionId signature hmac dsn webhookUrl salt otp certFile Passw0rd; do
      for ctx in 1 2 3; do
        vn=$((vn + 1)); hd=$(printf 'kq%02dzv' "$vn"); tl=$(printf 'wm%02dxd' "$vn"); vv=$hd-$tl
        case $ctx in 1) printf '%s = %s\n' "$nm" "$vv" ;; 2) printf '"%s": "%s"\n' "$nm" "$vv" ;; 3) printf '%s: %s\n' "$nm" "$vv" ;; esac
        printf 'name %s %s|%s|%s|%s\n' "$nm" "$ctx" "$hd" "$tl" LS >> "$WORK/st-pt.txt"
      done
    done
    # YAML block scalar header forms (body lines are short on purpose: under the 24 character blob limit)
    yn=0
    for hdr in '| # note' '|2' '!!binary |' '&a |' '|-' '>+' '|2-' '&anc !!str |' '|+1 # c' '>'; do
      yn=$((yn + 1)); hd=$(printf 'kq%02dyb' "$yn"); tl=$(printf 'wm%02dyc' "$yn")
      printf 'secret: %s\n  %s\n  %s\nkept_after_header_%s: ok\n' "$hdr" "$hd" "$tl" "$yn"
      printf 'yaml header %s|%s|%s|%s\n' "$yn" "$hd" "$tl" S >> "$WORK/st-pt.txt"
    done
    printf 'secret: "kq91mq\n  wm91mq"\nkept_after_mq: ok\n'
    printf 'secret: kq92mp\n  wm92mp more\nkept_after_mp: ok\n'
    printf 'yaml multi-line quoted|kq91mq|wm91mq|M\nyaml multi-line plain|kq92mp|wm92mp|M\n' >> "$WORK/st-pt.txt"
    # a secret container longer than 100 lines is hidden to its end (fail closed)
    { printf '"api_keys": [\n'; i=0; while [ "$i" -lt 150 ]; do i=$((i + 1)); printf '  "kq%03dcz",\n' "$i"; done; printf '  "wm150cz"\n],\n"kept_after_big": "ok"\n'; } 
    printf 'big container line 120|kq120cz|kq150cz|A\n' >> "$WORK/st-pt.txt"
    # classes found by the independent run on v4
    printf 'mysql -u root -pkq93mr%s\n' wm93mr
    printf "sshpass -p 'kq94ms%s' ssh host\n" wm94ms
    printf 'config = %s\nline one\n%s\n%s\n' "$q3" "a1b2c3d4e5f6a7b8c9d0" "$q3"
    printf '<add key="ApiKey" value="kq96mu%s"/>\n' wm96mu
    printf 'machine h login bob password kq97mv%s\n' wm97mv
    printf 'Passw0rd list: alice=kq98mw%s, bob=kq99mx%s\n' wm98mw wm99mx
    printf 'mysql|kq93mr|wm93mr|LS\nsshpass|kq94ms|wm94ms|LS\nxml attribute pair|kq96mu|wm96mu|LS\nnetrc|kq97mv|wm97mv|LS\nPassw0rd list|kq98mw|wm99mx|LS\n' >> "$WORK/st-pt.txt"
    printf '20 hex characters in a triple-quote body|a1b2c3d4e5f6|b7b8c9d0|LA\n' >> "$WORK/st-pt.txt"
    # only the web-address rule hides these (no secret name stands near them)
    printf 'see https://bob:kq90pw%s@host.example/p for details\n' wm90pw
    printf 'see https://bob:kq91pw@wm91pw@host.example/p for details\n'
    printf 'web address only|kq90pw|wm90pw|LS\nweb address password with an at sign|kq91pw|wm91pw|LS\n' >> "$WORK/st-pt.txt"
    printf -- '-----BEGIN PRIVATE KEY----- kq92pk%s -----END PRIVATE KEY-----\n' wm92pk
    printf 'private key block opener with the body on the same line|kq92pk|wm92pk|S\n' >> "$WORK/st-pt.txt"
    # only the line-start YAML rule hides the whole rest of the line (the value holds a closing bracket and a quote)
    printf 'secret: kq80ya%s) and "more" wm80ya\n' x
    printf 'yaml name at the start of a line hides the whole rest|kq80ya|wm80ya|S\n' >> "$WORK/st-pt.txt"
    printf 'token: "kq81yb%s" note_kept_81\n' x
    printf 'yaml quoted value at the start of a line|kq81yb|kq81yb|S\n' >> "$WORK/st-pt.txt"

    # ---- v6 additions: classes found by the v5 reviews (every value is built from parts; first 6 and last 6 characters are checked)
    v6n=100
    v6() { v6n=$((v6n + 1)); hd=$(printf 'zq%03dv' "$v6n"); tl=$(printf 'xm%03dd' "$v6n"); vv=$hd$tl; }
    v6_reg() { printf '%s|%s|%s|%s\n' "$1" "$hd" "$tl" "$2" >> "$WORK/st-pt.txt"; }
    # (1) userinfo forms of a web address: empty user part, host without a dot, password with a slash or an at sign, user part that is itself the token
    v6; printf 'cache redis://:%s@localhost:6379/0 ok\n' "$vv"; v6_reg 'web address with an empty user part and a host without a dot' LS
    v6; printf 'broker amqp://:%s@mq:5672\n' "$vv"; v6_reg 'web address amqp, empty user part' LS
    v6; printf 'x //:%s@host/p y\n' "$vv"; v6_reg 'web address without a scheme, empty user part' LS
    v6; printf 'mongodb://bob:%s/x@h/db\n' "$vv"; v6_reg 'web address, password holding a slash' LS
    v6; printf 'clone https://%s@github.example/o/r.git\n' "$vv"; v6_reg 'web address whose user part is the token (no colon)' LS
    v6; printf 'ssh://:%s@h\n' "$vv"; v6_reg 'web address ssh, empty user part' LS
    # (2) password as a flag after a command
    v6; printf 'docker login -u bob -p %s registry\n' "$vv"; v6_reg 'docker login -p' LS
    v6; printf 'redis-cli -a %s ping\n' "$vv"; v6_reg 'redis-cli -a' LS
    v6; printf 'ldapsearch -x -D cn=admin -w %s -b dc=x\n' "$vv"; v6_reg 'ldapsearch -w' LS
    v6; printf 'zip -P %s out.zip f.txt\n' "$vv"; v6_reg 'zip -P' LS
    v6; printf '7z a -p%s out.7z f\n' "$vv"; v6_reg '7z -pVALUE' LS
    v6; printf 'unrar x -p%s a.rar\n' "$vv"; v6_reg 'unrar -pVALUE' LS
    v6; printf 'htpasswd -b users.txt bob %s\n' "$vv"; v6_reg 'htpasswd -b' LS
    v6; printf 'htpasswd -nb bob %s | tee f\n' "$vv"; v6_reg 'htpasswd -nb' LS
    v6; printf 'smbclient //h/s -U bob%%%s\n' "$vv"; v6_reg 'smbclient -U user%password' LS
    v6; printf 'openssl enc -aes-256-cbc -k %s -in a\n' "$vv"; v6_reg 'openssl -k' LS
    v6; printf 'echo %s | docker login --password-stdin r\n' "$vv"; v6_reg 'echo value piped into a login' LS
    v6; printf 'skopeo copy --src-creds bob:%s a b\n' "$vv"; v6_reg 'skopeo --src-creds' LS
    v6; printf 'sudo docker login -p %s && echo done\n' "$vv"; v6_reg 'sudo docker login -p, more after it' LS
    v6; printf '$ mytool run -p %s now\n' "$vv"; v6_reg 'unknown command, shape rule -p' LS
    printf 'docker run -p 5678:5678 img kept_docker_port\nmkdir -p 5678 kept_mkdir_port\nls -a kept_ls_a\ngrep -a -n delete f kept_grep_flags\n'
    # (3) a value that continues on the next lines
    v6; printf 'SECRET_NAME = (\n    "%s"\n)\nkept_after_ml_1 = 1\n' "$vv"; v6_reg 'wrapped assignment, bracket opened and closed' M
    v6; printf 'API_KEY = \\\n    %s\nkept_after_ml_2 = 1\n' "$vv"; v6_reg 'assignment continued with a backslash' M
    v6; printf 'TOKENS = [\n  "%s",\n  "%s"\n]\nkept_after_ml_3 = 1\n' "$vv" "$vv"; v6_reg 'list opened after a secret name' M
    v6; printf 'X_SECRET=$(\n  fetch "%s"\n)\nkept_after_ml_4=1\n' "$vv"; v6_reg 'command substitution opened after a secret name' M
    v6; printf 'password = f("a",\n    "%s")\nkept_after_ml_5 = 1\n' "$vv"; v6_reg 'call opened on the line and closed two lines later' M
    v6; printf 'cfg = dict(password=("a"\n   "%s"),\n   other=1)\nkept_after_ml_6 = 1\n' "$vv"; v6_reg 'secret inside a wrapped call' M
    v6; printf '12:API_KEY = (\n13-    "%s"\n14-)\n' "$vv"; v6_reg 'wrapped assignment with a grep prefix' M
    # (8) a name with a zero-width space or another non-ASCII byte in it
    v6; printf 'pass\342\200\213word = %s\n' "$vv"; v6_reg 'zero-width space inside a name (assignment)' M
    v6; printf '"api\342\200\213_key": "%s"\n' "$vv"; v6_reg 'zero-width space inside a quoted JSON name' M
    v6; printf 'passw\303\266rd: %s\n' "$vv"; v6_reg 'letter with an accent inside a name' M
    v6; printf '\345\257\206\347\240\201: %s\n' "$vv"; v6_reg 'name made only of non-ASCII letters' M
    # (7) length guard: a very long line is cut before the sed stage; the notice carries the true length
    v6; printf 'API_KEY=%s%s\n' "$vv" "$(awk 'BEGIN{for(i=0;i<30000;i++) printf "x"}')"; v6_reg 'secret at the start of a 30000-character line' M
    printf 'kept_long_guard %s\n' "$(awk 'BEGIN{for(i=0;i<30000;i++) printf "y"}')"
    # (9) dots and slashes inside one opaque string
    v6; hd=$(printf 'Kq%02dZvAb' "$v6n"); tl=$(printf 'Pq%02dRsDf' "$v6n"); printf 'see %s.Wm%02dXdCe.%s here\n' "$hd" "$v6n" "$tl"; v6_reg 'opaque string cut by dots' A
    v6; hd=$(printf 'Kq%02dZvAb' "$v6n"); tl=$(printf 'Pq%02dRsD' "$v6n"); printf 'see %s/Wm%02dXdCe/%s here\n' "$hd" "$v6n" "$tl"; v6_reg 'opaque string cut by slashes (25 characters)' A
    printf 'class com.example.MyClass2.HandlerFactory kept_dotted_camel\nsee tests/test_qs_37_refuses_after_window_end.py kept_dotted_file\nThe name is kept_sentence_end.\n'
    printf 'nul?b %s\n' x >/dev/null
    printf 'a\000b kept_nul_line\n'

    # ---- v7 additions: classes found by the v6 security review (value built from parts; first 6 and last 6 characters are checked)
    v7n=200
    v7() { v7n=$((v7n + 1)); hd=$(printf 'zr%03dv' "$v7n"); tl=$(printf 'xn%03dd' "$v7n"); vv=$hd$tl; }
    v7_reg() { printf '%s|%s|%s|%s\n' "$1" "$hd" "$tl" "$2" >> "$WORK/st-pt.txt"; }
    BS=$(printf '\134')
    # (M1) quotes escaped inside JSON that sits inside a string; a JSON key written with a \u escape
    v7; printf 'body {%s"password%s": %s"%s%s"}\n' "$BS" "$BS" "$BS" "$vv" "$BS"; v7_reg 'escaped quotes: name and string value' LS
    v7; printf 'body {%s"password%s": %s}\n' "$BS" "$BS" "$vv"; v7_reg 'escaped quotes: name and plain value' LS
    v7; printf "x %s'token%s': %s'%s%s'\n" "$BS" "$BS" "$BS" "$vv" "$BS"; v7_reg 'escaped single quotes: name and value' LS
    v7; printf '{"pa%su0073sword": "%s"}\n' "$BS" "$vv"; v7_reg 'JSON key written with a unicode escape' LS
    # (M2) password flag after other text: after && ; | $( , a path, a variable assignment, on a continuation line, a quoted value with spaces
    v7; printf 'cd x && mytool -p %s now\n' "$vv"; v7_reg 'password flag after &&' LS
    v7; printf 'cat f | mytool -P %s\n' "$vv"; v7_reg 'password flag after a pipe' LS
    v7; printf 'v=$(mytool -w %s)\n' "$vv"; v7_reg 'password flag inside $( )' LS
    v7; printf './bin/mytool -p %s go\n' "$vv"; v7_reg 'password flag, command given with a path' LS
    v7; printf 'FOO=1 mytool -p %s go\n' "$vv"; v7_reg 'password flag after a variable assignment' LS
    v7; printf 'mytool run \\\n  -p %s\n' "$vv"; v7_reg 'password flag on a continuation line' LS
    v7; printf 'mytool -p "abc %s"\n' "$vv"; v7_reg 'password flag, quoted value with a space' LS
    # (M3) names glued to a prefix, XML text, a value that starts with <, comparison, :=, SQL, a second literal, a bracket inside the value
    v7; printf 'DBPASS=%s\n' "$vv"; v7_reg 'glued name DBPASS' LS
    v7; printf 'ROOTPW=%s\n' "$vv"; v7_reg 'glued name ROOTPW' LS
    v7; printf 'requirepass %s\n' "$vv"; v7_reg 'config line requirepass' LS
    v7; printf 'masterauth %s\n' "$vv"; v7_reg 'config line masterauth' LS
    v7; printf 'jsessionid=%s\n' "$vv"; v7_reg 'session id name jsessionid' LS
    v7; printf '<password>%s</password>\n' "$vv"; v7_reg 'XML element text' LS
    v7; printf 'password = <%s>\n' "$vv"; v7_reg 'value that starts with an angle bracket' LS
    v7; printf 'if password == "%s":\n' "$vv"; v7_reg 'comparison of a password with a text' LS
    v7; printf 'x := password := "%s"\n' "$vv"; v7_reg 'name := value in the middle of a line' LS
    v7; printf 'if ok { apikey := "%s" }\n' "$vv"; v7_reg 'name := value inside braces' LS
    v7; printf 'foo := password := %s end\n' "$vv"; v7_reg 'name := unquoted value' LS
    v7; printf "CREATE USER u IDENTIFIED BY '%s';\n" "$vv"; v7_reg 'SQL IDENTIFIED BY' LS
    v7; printf 'password = "a" or "%s"\n' "$vv"; v7_reg 'second text after a hidden one' LS
    v7; printf 'note password is %s]%s end\n' "$hd" "$tl"; v7_reg 'closing bracket inside a mid-line value' LS
    # (M5) user part of a web address
    v7; printf 'x https://%s@localhost/p\n' "$vv"; v7_reg 'web address, token as user part, host without a dot' LS
    v7; printf 'x https:%s/%s/bob:%s@h/p\n' "$BS" "$BS" "$vv"; v7_reg 'web address with escaped slashes' LS
    v7; printf 'x https:%s/%s/%s@h/p\n' "$BS" "$BS" "$vv"; v7_reg 'web address with escaped slashes, no colon' LS
    v7; printf 'conn bob:%s@db port\n' "$vv"; v7_reg 'user:password@host without a scheme' LS
    # (minor 2) tokens with characters outside the plain set, short Bearer values, more password readers
    v7; printf 'Bearer %s#%s end\n' "$hd" "$tl"; v7_reg 'Bearer value with a hash sign' LS
    hd=kq7z2; tl=kq7z2; v7_reg 'Bearer value of 5 characters' LS; printf 'Bearer %s\n' "$hd"
    v7; printf 'echo %s | sudo -S ls\n' "$vv"; v7_reg 'echo piped into sudo -S' LS
    v7; printf 'echo %s | kinit bob\n' "$vv"; v7_reg 'echo piped into kinit' LS
    v7; printf 'echo %s | ssh-add -\n' "$vv"; v7_reg 'echo piped into ssh-add' LS
    printf 'kept_v7_line mkdir -p /tmp/x\n'

    # ---- v8 additions: classes found by the v7 reviews (every value is built from parts; first 6 and last 6 characters are checked)
    v8n=300
    v8() { v8n=$((v8n + 1)); hd=$(printf 'zs%03dv' "$v8n"); tl=$(printf 'xo%03dd' "$v8n"); vv=$hd$tl; }
    v8_reg() { printf '%s|%s|%s|%s\n' "$1" "$hd" "$tl" "$2" >> "$WORK/st-pt.txt"; }
    # (MAJ-1) control bytes and bidi controls: removed and counted; a delete or archive word beside them stays visible
    printf 'a\033[2Kb kept_esc_word\n'
    printf 'row1\rkept_cr_word\n'
    printf 'kept_crlf_line\r\n'
    printf 'back\010space kept_bs_word\n'
    printf 'vt\013ff\014del\177x kept_vtff_word\n'
    printf 'bidi \342\200\256kept_bidi_word \342\201\246 \330\234 \342\200\216x\n'
    printf 'tab\there kept_tab_word\n'
    # (MIN-1) a control byte inside a secret name
    v8; printf 'pass\001word = %s\n' "$vv"; v8_reg 'control byte 0x01 inside the name password' ""
    v8; printf 'pass\033word = %s\n' "$vv"; v8_reg 'ESC inside the name password' ""
    v8; printf 'api_\010key: %s\n' "$vv"; v8_reg 'backspace inside the name api_key' ""
    v8; printf 'pass\000word = %s\n' "$vv"; v8_reg 'NUL inside the name password' ""
    v8; printf 'tok\342\200\256en = %s\n' "$vv"; v8_reg 'bidi control inside the name token' ""
    v8; printf 'secret\r= %s\n' "$vv"; v8_reg 'CR between the name and the equals sign' ""
    # (MIN-2) a value that starts with < or with the beginning of our own mark: only the exact mark may pass as already hidden
    v8; printf 'password = <masked>%s\n' "$vv"; v8_reg 'value that starts with the exact mark and goes on' ""
    v8; printf 'password = <massive%s>\n' "$vv"; v8_reg 'value <massive...>' ""
    v8; printf 'the token is <ma%s>\n' "$vv"; v8_reg 'prose: token is <ma...>' ""
    v8; printf 'run --token <m%s>\n' "$vv"; v8_reg 'flag --token <m...>' ""
    v8; printf 'Bearer <e%s>\n' "$vv"; v8_reg 'Bearer <e...>' ""
    v8; printf 'api_key: <email-masked>%s\n' "$vv"; v8_reg 'YAML value that starts with the exact email mark and goes on' ""
    v8; printf 'secret is <MASKED>%s\n' "$vv"; v8_reg 'upper case mark with a value' ""
    # (MIN-5) other spellings of the same text
    v8; printf 'x &quot;password&quot;: &quot;%s&quot; y\n' "$vv"; v8_reg 'HTML entities for the quotes' ""
    v8; printf '{&#34;api_key&#34;:&#34;%s&#34;}\n' "$vv"; v8_reg 'numeric HTML entities for the quotes' ""
    v8; printf 'GET /x?password%%3D%s&y=1\n' "$vv"; v8_reg 'URL-encoded equals sign' ""
    v8; printf 'x %s%s"password%s%s": %s%s"%s%s"\n' "$BS" "$BS" "$BS" "$BS" "$BS" "$BS" "$vv" "$BS$BS"; v8_reg 'double-escaped quotes' LS
    v8; printf '<password><![CDATA[%s]]></password>\n' "$vv"; v8_reg 'CDATA text of an XML element' LS
    v8; printf '&lt;password&gt;%s&lt;/password&gt;\n' "$vv"; v8_reg 'XML element written with entities' ""
    v8; printf '<connection user="u" password="%s"/>\n' "$vv"; v8_reg 'XML attribute named password' LS
    v8; printf '<add key="password" value="%s"/>\n' "$vv"; v8_reg 'XML key and value attributes' LS
    # (MIN-6) a value given by position, or compared with a literal
    v8; printf 'smtp.login("bob", "%s")\n' "$vv"; v8_reg 'login(user, "value")' LS
    v8; printf 'if api_key == "%s":\n' "$vv"; v8_reg 'api_key == "value"' LS
    v8; printf 'client.set_password("%s")\n' "$vv"; v8_reg 'set_password("value")' LS
    # (evidence) a name followed only by white space and the value
    v8; printf 'password %s\n' "$vv"; v8_reg 'bare password VALUE (one space)' LS
    v8; printf 'password\t%s\n' "$vv"; v8_reg 'bare password TAB VALUE' LS
    v8; printf 'db_password\t%s\n' "$vv"; v8_reg 'bare db_password TAB VALUE' LS
    v8; printf 'secret\t%s\n' "$vv"; v8_reg 'bare secret TAB VALUE' LS
    v8; printf 'token\t%s\n' "$vv"; v8_reg 'bare token TAB VALUE' LS
    v8; printf 'Password   %s\n' "$vv"; v8_reg 'bare Password, several spaces' LS
    v8; printf '  password  \t %s tail_kept_bare\n' "$vv"; v8_reg 'bare password, indented, mixed white space' LS
    v8; printf 'user alice\npassword %s\n' "$vv"; v8_reg 'netrc style: user line, then password line' LS
    v8; printf 'http -a alice:%s example.test\n' "$vv"; v8_reg 'http -a user:password' LS
    v8; printf 'wget --user bob:%s url\n' "$vv"; v8_reg 'wget --user user:password' LS
    v8; printf 'http --proxy-user bob:%s x\n' "$vv"; v8_reg 'http --proxy-user user:password' LS
    printf 'the token counter and a secret handshake are kept_prose_line\n'
    printf -- '-----BEGIN ENCRYPTED DATA-----\n%s_70a_\n%s_70b_\n-----END ENCRYPTED DATA-----\nkept_after_enc_pem\n' "$base" "$base"
    v8; printf '{%s"password%s": %s"%s%s"}\n' "$BS" "$BS" "$BS" "$vv" "$BS"
    v8; printf '{%s'"'"'token%s'"'"': %s'"'"'%s%s'"'"'}\n' "$BS" "$BS" "$BS" "$vv" "$BS"

  } > "$in"
  if [ -n "${SELFTEST_FILTER:-}" ]; then
    # shellcheck disable=SC2086
    $SELFTEST_FILTER < "$in" > "$res"; cp "$res" "$res2"; cp "$res" "$res3"; cp "$res" "$res4"
  else
    mask < "$in" > "$res"; mask_line < "$in" > "$res2"
    sed -E -f "$MASKSED" < "$in" > "$res3"
    awk -v CUT=240 -f "$MASKAWK" < "$in" > "$res4"
  fi
  pass=0; fail=0
  say() { [ "$st_quiet" = 1 ] || printf '%s\n' "$1"; }
  chk_hidden() { # label, fragment, flags (L belt, S sed stage alone, A awk stage alone, M full filter only)
    if grep -a -q -F -- "$2" "$res"; then fail=$((fail + 1)); printf 'FAIL (secret still visible): %s\n' "$1"
    else pass=$((pass + 1)); say "PASS (hidden): $1"; fi
    case ${3:-} in *L*)
      if grep -a -q -F -- "$2" "$res2"; then fail=$((fail + 1)); printf 'FAIL (secret still visible in the line-only final filter): %s\n' "$1"
      else pass=$((pass + 1)); say "PASS (hidden, line-only final filter): $1"; fi ;; esac
    case ${3:-} in *S*)
      if grep -a -q -F -- "$2" "$res3"; then fail=$((fail + 1)); printf 'FAIL (secret still visible after the sed stage alone): %s\n' "$1"
      else pass=$((pass + 1)); say "PASS (hidden, sed stage alone): $1"; fi ;; esac
    case ${3:-} in *A*)
      if grep -a -q -F -- "$2" "$res4"; then fail=$((fail + 1)); printf 'FAIL (secret still visible after the awk stage alone): %s\n' "$1"
      else pass=$((pass + 1)); say "PASS (hidden, awk stage alone): $1"; fi ;; esac
  }
  chk_kept() { # label, fragment
    if grep -a -q -F -- "$2" "$res"; then pass=$((pass + 1)); say "PASS (kept): $1"
    else fail=$((fail + 1)); printf 'FAIL (evidence was hidden): %s\n' "$1"; fi
  }
  chk_hidden 'KEY= form' "${base}_1_" LS
  chk_hidden 'export TOKEN= form' "${base}_2_" LS
  chk_hidden 'password = "..." form' "${base}_3_" LS
  chk_hidden 'JSON quoted key' "${base}_4_" LS
  chk_hidden 'JSON client_secret no spaces' "${base}_5_" LS
  chk_hidden 'Authorization Bearer' "${base}_6_" LS
  chk_hidden 'bare Bearer value' "${base}_7_" LS
  chk_hidden 'sk- value' "${base}_8_" LS
  chk_hidden 'pat- value' "${base}_9_" LS
  chk_hidden 'github token shape' "${base}_10_" LS
  chk_hidden 'YAML next line after grep prefix' "${base}_11_" S
  chk_hidden 'YAML block line a' "${base}_12a_" S
  chk_hidden 'YAML block line b' "${base}_12b_" S
  chk_hidden 'web address with user:password' "${base}_13_" LS
  chk_hidden 'AKIA-shaped id' "$fakeid" LS
  chk_hidden 'passwd: form' "${base}_14_" LS
  chk_hidden 'pwd= form' "${base}_15_" LS
  chk_hidden 'credential = form' "${base}_16_" LS
  chk_hidden 'secret at column 200 of a long line' "${base}_17_" LS
  chk_hidden 'JSON secret followed by more JSON' "${base}_18_" LS
  chk_hidden 'quoted secret inside a call' "${base}_19_" LS
  chk_hidden 'bare PASS= name' "${base}_20_" LS
  chk_hidden 'passphrase: name' "${base}_21_" LS
  chk_hidden 'pat = name (personal access token)' "${base}_22_" LS
  chk_hidden 'os.environ["X_TOKEN"] = "v"' "${base}_23_" LS
  chk_hidden '.get("API_KEY", "default")' "${base}_24_" LS
  chk_hidden '("API_KEY", "value") tuple' "${base}_25_" LS
  chk_hidden '--token value flag' "${base}_26_" LS
  chk_hidden '--password value flag' "${base}_27_" LS
  chk_hidden '--api-key=value flag' "${base}_28_" LS
  chk_hidden 'triple-quoted value on one line' "${base}_29_" LS
  chk_hidden 'triple-quoted value over several lines, line 1' "${base}_30a_" S
  chk_hidden 'triple-quoted value over several lines, line 2' "${base}_30b_" S
  chk_hidden 'unterminated quote' "${base}_31_" LS
  chk_hidden 'e-mail address' "$em1$em2" LS
  chk_hidden 'JSON name/value pair' "${base}_33_" LS
  chk_hidden "single-quoted dict key 'api_key'" "${base}_34_" LS
  chk_hidden 'self.token = value' "${base}_35_" LS
  chk_hidden 'accessToken: value (camel case)' "${base}_36_" LS
  chk_hidden 'apiKey = value (camel case)' "${base}_37_" LS
  chk_hidden 'X-Api-Key: header' "${base}_38_" LS
  chk_hidden 'JS object {token: value}' "${base}_39_" LS
  chk_hidden 'export X_PASSWORD=' "${base}_40_" LS
  chk_hidden 'pw name, triple-quoted over several lines, line 1' "${base}_42_" S
  chk_hidden 'pw name, triple-quoted over several lines, line 2' "${base}_43_" S
  chk_hidden 'pswd: name' "${base}_44_" LS
  chk_kept 'text after a multi-line value closes' '# tail42' 
  chk_hidden "single triple quotes over several lines, line 1" "${base}_41a_" S
  chk_hidden "single triple quotes over several lines, line 2" "${base}_41b_" S
  chk_kept 'text after a quoted JSON secret stays readable (DELETE)' '"method": "DELETE"'
  chk_kept 'text after a quoted secret in a call stays readable' '# delete path'
  chk_kept 'comparison key == "end" is not hidden' 'if key == "end":'
  chk_kept 'plain answer = "end" is not hidden' 'answer = "end"'
  chk_kept 'the one allowed example key shows' 'AKIAIOSFODNN7EXAMPLE'
  chk_kept 'a quoted value at the start of a line hides the string, not the words after it' 'note_kept_81'
  chk_kept 'ordinary line with the word end' 'plain line with the word end in it'
  chk_kept 'unrelated YAML line after a hidden block' 'next_line: stays'
  chk_kept 'unrelated grep line after hidden YAML value' '13-other: fine'
  chk_kept 'long line carries a cut notice' '[CUT: this line has'
  chk_kept 'text after a hidden --token flag' '--verbose'
  chk_kept 'text after a hidden triple-quoted value' '# tail29'
  chk_kept 'line after a multi-line triple-quoted value' 'after_multiline = kept'
  chk_kept 'line after a multi-line single-triple-quoted value' 'line_after_triple = kept2'
  chk_kept 'text after a JSON name/value pair secret: the name stays' '"name": "X_TOKEN"'
  chk_kept 'text after a single-quoted dict secret' "'n': 2"
  chk_kept 'text after a JS object secret' 'n: 3'
  chk_kept 'if token: is not a secret line (the line)' 'if token:'
  chk_kept 'if token: does not hide the next line' 'return kept_after_if_token'
  chk_kept 'author: is not a secret name (the line)' 'author: Someone Else'
  chk_kept 'author: does not hide the next line' 'title: kept_after_author'
  chk_kept 'if not key_file: is not a YAML name (the line after it stays)' 'raise kept_after_key_file'
  chk_kept 'author = value is not hidden' 'author = Someone'
  chk_kept 'desk- word is not mangled' 'desk-aaaaaaaaaaaa'
  chk_kept 'task- word is not mangled' 'task-bbbbbbbbbbbb'
  chk_kept 'risk- word is not mangled' 'risk-cccccccccccc'
  chk_kept 'mask- word is not mangled' 'mask-dddddddddddd'
  chk_kept 'compat- word is not mangled' 'compat-eeeeeeeeeeee'
  chk_kept 'max_tokens is not a secret name' 'max_tokens = 100'
  chk_kept 'tokenizer is not a secret name' 'tokenizer = fine'
  chk_kept 'if token == "end": is not hidden' 'if token == "end":'
  chk_kept 'bypass is not a secret name' 'bypass = 1'
  chk_hidden 'secret that starts before column 240 (mask first, then cut)' "${base}_17b_" LS
  chk_hidden 'opaque blob in quotes' "$blob16" A
  chk_hidden 'opaque blob after a label' "$blob16" A
  chk_hidden 'mixed word in a trailing comment' "$mixed" A
  chk_hidden 'mixed word in a sentence' "$m1$m2" A
  chk_hidden 'UUID' "$u1" A
  chk_hidden 'curl -H "X-Auth-Token: v"' "${base}_44a_" LS
  chk_hidden "curl -H 'Authorization: token v'" "${base}_44b_" LS
  chk_hidden 'ENV TOKEN v (no equals sign)' "${base}_44c_" LS
  chk_hidden 'passwd "v" (no equals sign)' "${base}_44d_" LS
  chk_hidden 'plural API_KEYS=' "${base}_45a_" LS
  chk_hidden 'plural PASSWORDS:' "${base}_45b_" LS
  chk_hidden 'plural AUTH_TOKENS =' "${base}_45c_" LS
  chk_hidden 'plural ALLOWED_API_KEYS=' "${base}_45d_" LS
  chk_hidden 'tokens = (not a counter)' "${base}_45e_" LS
  chk_hidden 'Name: value in the middle of a line' "${base}_46a_" LS
  chk_hidden 'Name: value inside quotes (echo)' "${base}_46b_" LS
  chk_hidden 'YAML next line with path:NN: prefix' "${base}_47a_" S
  chk_hidden 'YAML name: value with path:NN: prefix' "${base}_47b_" LS
  chk_hidden 'pretty JSON: name line then value line' "${base}_48a_" M
  chk_hidden 'pretty JSON: value line then name line' "${base}_48b_" M
  chk_hidden 'YAML list: - name then value' "${base}_48c_" M
  chk_hidden 'JSON array on one line, item 1' "${base}_49a_" M
  chk_hidden 'JSON array on one line, item 2' "${base}_49b_" M
  chk_hidden 'JSON array over several lines, item 1' "${base}_49c_" M
  chk_hidden 'JSON array over several lines, item 2' "${base}_49d_" M
  chk_hidden 'nested JSON object, inner' "${base}_49e_" M
  chk_hidden 'nested JSON object, later key' "${base}_49f_" M
  chk_hidden 'escaped quote inside a value, first part' "${base}_50a_" LS
  chk_hidden 'escaped quote inside a value, second part' "${base2}_50_" LS
  chk_hidden 'two strings in a row, first' "${base}_51a_" LS
  chk_hidden 'two strings in a row, second' "${base2}_51b_" LS
  chk_hidden 'string + string, first' "${base}_51c_" LS
  chk_hidden 'string + string, second' "${base2}_51d_" LS
  chk_hidden 'private key block line 1' "${base}_52a_" S
  chk_hidden 'private key block line 2' "${base}_52b_" S
  chk_hidden 'sk_live_ value' "${base}_53_" LS
  chk_hidden 'curl -u user:password' "${base}_54_" LS
  chk_hidden 'the password is v (prose)' "${base}_55_" LS
  chk_hidden 'JWT-shaped value' "${base}_56_" LS
  chk_hidden 'line with a 0xE9 byte' "${base}_57_" LS
  chk_hidden 'line with a NUL byte' "${base}_58_" S
  chk_hidden 'JSON after a label' "${base}_59_" LS
  chk_kept 'snake_case test name is not hidden' 'test_qs_37_refuses_after_window_end'
  chk_kept 'CamelCase name is not hidden' 'getOauth2AccessTokenForHubspotUser'
  if [ -z "${SELFTEST_FILTER:-}" ]; then
    # the checksum lines the script printed itself stay readable in the final pass (res2); the same lines coming from a
    # search (res) are masked, and a hex string with two spaces that the script did NOT print is masked in both
    if grep -a -q -F -- "$sha64  some_file.py" "$res2" && grep -a -q -F -- "HEAD: $sha40" "$res2"; then pass=$((pass + 2)); say "PASS (kept): checksum and HEAD lines the script printed itself stay (final pass)"
    else fail=$((fail + 1)); printf 'FAIL (evidence was hidden): checksum or HEAD line the script printed itself\n'; fi
    chk_hidden 'a checksum-shaped line that came from a searched file is masked (search view)' "$sha64" ""
  fi
  chk_hidden 'hex string + two spaces from a searched file is not a checksum line' "$g16$g16" LA
  chk_kept 'max_tokens counter stays' 'max_tokens = 100'
  chk_kept 'prompt_tokens counter stays' 'prompt_tokens: 12'
  chk_kept 'completion_tokens counter stays' 'completion_tokens=4'
  chk_kept 'total_tokens counter stays' 'total_tokens = 9'
  chk_kept 'num_tokens counter stays' 'num_tokens=3'
  chk_kept 'input_tokens counter stays' 'input_tokens: 5'
  chk_kept 'output_tokens counter stays' 'output_tokens = 6'
  chk_kept 'max_output_tokens counter stays' 'max_output_tokens = 7'
  chk_kept 'line after YAML path prefix stays' 'kept_pfx_path'
  chk_kept 'line after a hidden JSON array stays' 'kept_after_array'
  chk_kept 'key after a hidden JSON object stays' 'kept_after_obj'
  chk_kept 'line after a private key block stays' 'kept_after_pem'
  chk_kept 'name: alone is not a pair' 'kept_name_line'
  chk_kept 'value: alone is not hidden' 'kept_value_line_alone'
  chk_kept 'private key block markers stay' '-----END PRIVATE KEY-----'
  # ---- v5 checks: first 6 and last 6 characters of every value, per view
  chk_pt() { # label head tail flags
    chk_hidden "$1 (first 6 characters)" "$2" "$4"
    chk_hidden "$1 (last 6 characters)" "$3" "$4"
  }
  while IFS='|' read -r pt_l pt_h pt_t pt_f; do
    [ -n "$pt_l" ] && chk_pt "$pt_l" "$pt_h" "$pt_t" "$pt_f"
  done < "$WORK/st-pt.txt"
  rm -f "$WORK/st-pt.txt"
  chk_kept 'text after a block value header stays (1)' 'kept_after_header_1: ok'
  chk_kept 'text after a block value header stays (10)' 'kept_after_header_10: ok'
  chk_kept 'text after a multi-line quoted value stays' 'kept_after_mq: ok'
  chk_kept 'text after a multi-line plain value stays' 'kept_after_mp: ok'
  chk_kept 'text after a long hidden container stays' '"kept_after_big": "ok"'
  chk_kept 'docker run -p with a port number stays' 'kept_docker_port'
  chk_kept 'mkdir -p with a number stays' 'kept_mkdir_port'
  chk_kept 'ls -a stays' 'kept_ls_a'
  chk_kept 'grep -a -n stays' 'kept_grep_flags'
  chk_kept 'text after a wrapped assignment stays (1)' 'kept_after_ml_1 = 1'
  chk_kept 'text after a wrapped assignment stays (2)' 'kept_after_ml_2 = 1'
  chk_kept 'text after a wrapped assignment stays (3)' 'kept_after_ml_3 = 1'
  chk_kept 'text after a wrapped assignment stays (4)' 'kept_after_ml_4=1'
  chk_kept 'text after a wrapped assignment stays (5)' 'kept_after_ml_5 = 1'
  chk_kept 'text after a wrapped assignment stays (6)' 'kept_after_ml_6 = 1'
  chk_kept 'a 30000-character line carries a cut notice with its true length' 'this line has 30016 characters'
  chk_kept 'dotted CamelCase name stays' 'com.example.MyClass2.HandlerFactory'
  chk_kept 'file name with dots stays' 'tests/test_qs_37_refuses_after_window_end.py'
  chk_kept 'a name followed by a full stop stays' 'kept_sentence_end.'
  chk_kept 'a NUL byte is removed and the removal is shown (tr stage and pre-stage)' 'ab kept_nul_line [control bytes removed: 1]'
  chk_kept 'mkdir -p with a path stays' 'kept_v7_line mkdir -p /tmp/x'
  chk_kept 'a word after an ESC sequence stays and the removal is shown' 'kept_esc_word [control bytes removed: 1]'
  chk_kept 'a word after a bare CR stays (the CR is removed, not shown raw)' 'row1kept_cr_word [control bytes removed: 1]'
  chk_kept 'a CRLF line end is removed without a notice' 'kept_crlf_line'
  chk_kept 'backspace removed' 'backspace kept_bs_word [control bytes removed: 1]'
  chk_kept 'vertical tab, form feed and DEL removed' 'kept_vtff_word [control bytes removed: 3]'
  chk_kept 'bidi controls removed and counted' 'bidi kept_bidi_word   x [control bytes removed: 4]'
  chk_kept 'a TAB stays' "tab$(printf '\011')here kept_tab_word"
  chk_kept 'a line with the word token or secret in prose is not hidden' 'the token counter and a secret handshake are kept_prose_line'
  chk_kept 'text after a hidden bare password value stays' 'tail_kept_bare'
  chk_kept 'text after a block of ENCRYPTED DATA stays' 'kept_after_enc_pem'
  chk_kept 'the escaped closing quote stays after a hidden JSON value' '<masked>'"$BS"'"}'
  chk_kept 'the escaped closing single quote stays after a hidden value' "<masked>${BS}'}"
  chk_hidden 'ENCRYPTED DATA block line 1' "${base}_70a_" S
  chk_hidden 'ENCRYPTED DATA block line 2' "${base}_70b_" S
  # no control byte of any kind reaches the screen (full filter and final belt)
  st_ctlre=$(printf '[\001-\010\013-\037\177]')
  for st_v in "$res" "$res2"; do
    if grep -a -q -- "$st_ctlre" "$st_v"; then fail=$((fail + 1)); printf 'FAIL (a control byte reaches the output)\n'; else pass=$((pass + 1)); say "PASS (no control byte in the output)"; fi
    if grep -a -q -E -- "$(printf '\342\200[\216\217\252-\256]|\342\201[\246-\251]|\330\234')" "$st_v"; then fail=$((fail + 1)); printf 'FAIL (a bidi control reaches the output)\n'; else pass=$((pass + 1)); say "PASS (no bidi control in the output)"; fi
  done
  st_leak=0
  grep -a -q -F -- "$base" "$res" && st_leak=1
  [ "$st_leak" -eq 0 ] || printf 'FAIL (the secret base string is still visible somewhere in the output)\n'
  rm -f "$in" "$res" "$res2" "$res3" "$res4" "$SHAOK"
  # ---- tests of the test machinery itself (explicit --self-test only; the quick canary does not run them)
  if [ "$st_quiet" = 0 ] && [ -z "${SELFTEST_FILTER:-}" ] && [ -z "${LEAD_REPIN_NO_META:-}" ]; then
    self_test_meta
  fi
  printf 'SELF-TEST: passed=%s failed=%s (the made-up input and output files were deleted)\n' "$pass" "$fail"
  [ -n "${LEAD_REPIN_TEST_LATE_FAIL:-}" ] && fail=$((fail + 1))   # test hook: a failure that only the return value shows
  [ "$fail" -eq 0 ] && [ "$st_leak" -eq 0 ]
}
# self_test_meta: proves that the self-test, the abort and the readiness check can themselves FAIL. It runs this
# script again as a child (never inside a child: LEAD_REPIN_NO_META), with a deliberately weakened filter.
self_test_meta() {
  st_child=$WORK/st-child; st_t=$WORK/st-take
  mkdir "$st_child" "$st_t" 2>/dev/null; printf 'x = 1\n' > "$st_t/a.py"
  mt_ok() { pass=$((pass + 1)); say "PASS (machinery): $1"; }
  mt_bad() { fail=$((fail + 1)); printf 'FAIL (machinery): %s\n' "$1"; }
  for st_mode in weak empty; do
    st_o=$(LEAD_REPIN_TEST_BREAK_FILTER=$st_mode LEAD_REPIN_NO_META=1 TMPDIR="$st_child" sh "$SELF" "$st_t" 2>/dev/null); st_r=$?
    st_left=$(ls "$st_child" | wc -l | tr -d ' ')
    if [ "$st_r" -eq 3 ] && [ "$st_left" -eq 0 ] && ! printf '%s' "$st_o" | grep -a -q 'BLOCK'; then mt_ok "a $st_mode filter stops the run with exit 3, opens no test-program file, leaves no folder"
    else mt_bad "a $st_mode filter must stop the run (exit 3=$st_r, folders left=$st_left, BLOCK printed or not)"; fi
  done
  SELFTEST_FILTER=cat LEAD_REPIN_NO_META=1 TMPDIR="$st_child" sh "$SELF" --self-test > "$WORK/st-meta.txt" 2>&1; st_r=$?
  if [ "$st_r" -ne 0 ] && grep -a -q '^FAIL' "$WORK/st-meta.txt"; then mt_ok "an identity filter (cat) makes --self-test fail with a non-zero exit code"
  else mt_bad "an identity filter must make --self-test fail (exit=$st_r)"; fi
  : > "$WORK/st-bad1.sed"; printf 's/a/a/\n' > "$WORK/st-bad2.sed"
  for st_bad in st-bad1.sed st-bad2.sed; do
    if ( MASKSED=$WORK/$st_bad; filter_ready ); then mt_bad "filter_ready accepted the useless rule file $st_bad"; else mt_ok "filter_ready refuses the useless rule file $st_bad"; fi
  done
  if ( MASKAWK=$WORK/st-bad1.sed; filter_ready ); then mt_bad "filter_ready accepted a useless awk program"; else mt_ok "filter_ready refuses a useless awk program"; fi
  st_o=$(printf 'API_KEY=%s_61_\n' "$base" | LEAD_REPIN_TEST_BREAK_FILTER=weak LEAD_REPIN_NO_META=1 TMPDIR="$st_child" sh "$SELF" --mask 2>/dev/null); st_r=$?
  st_left=$(ls "$st_child" | wc -l | tr -d ' ')
  if [ "$st_r" -eq 3 ] && [ -z "$st_o" ] && [ "$st_left" -eq 0 ]; then mt_ok "--mask with a damaged filter prints nothing, exits 3 and leaves no folder"
  else mt_bad "--mask with a damaged filter must print nothing and exit 3 (exit=$st_r, printed=${#st_o} bytes, folders left=$st_left)"; fi
  st_o=$(printf 'API_KEY=%s_60_\n' "$base" | LEAD_REPIN_NO_META=1 TMPDIR="$st_child" sh "$SELF" --mask 2>/dev/null); st_r=$?
  if [ "$st_r" -eq 0 ] && ! printf '%s' "$st_o" | grep -a -q -F -- "${base}_60_" && printf '%s' "$st_o" | grep -a -q '<masked>'; then mt_ok "--mask passes the canary, hides the value and exits 0"
  else mt_bad "--mask must hide the value (exit=$st_r)"; fi
  st_o=$(LEAD_REPIN_NO_META=1 TMPDIR="$st_child" sh "$SELF" "$st_t" 2>/dev/null); st_r=$?
  if [ "$st_r" -eq 0 ] && printf '%s' "$st_o" | grep -a -q '^SUMMARY:'; then mt_ok "a normal run on a one-file folder ends with exit 0 and a SUMMARY line"
  else mt_bad "a normal run must end with exit 0 and a SUMMARY line (exit=$st_r)"; fi
  st_left=$(ls "$st_child" | wc -l | tr -d ' ')
  if [ "$st_left" -eq 1 ]; then mt_ok "a normal run keeps exactly one work folder (the masked output copy)"; else mt_bad "a normal run must keep exactly one work folder (found $st_left)"; fi
  # v8: file modes. st_modes DIR prints how many entries are NOT private (a file other than mode 600, or the folder other than 700)
  st_modes() { find "$1" \( -type f ! -perm 600 \) -o \( -type d ! -perm 700 \) 2>/dev/null | wc -l | tr -d ' '; }
  st_mf=$WORK/st-modefolder; mkdir "$st_mf"; chmod 700 "$st_mf"; : > "$st_mf/a"; chmod 600 "$st_mf/a"
  st_m0=$(st_modes "$st_mf"); chmod 644 "$st_mf/a"; st_m1=$(st_modes "$st_mf"); chmod 600 "$st_mf/a"; chmod 755 "$st_mf"; st_m2=$(st_modes "$st_mf")
  if [ "$st_m0" -eq 0 ] && [ "$st_m1" -eq 1 ] && [ "$st_m2" -eq 1 ]; then mt_ok "the file-mode check accepts mode 600 files in a 700 folder and sees a 644 file and a 755 folder"; else mt_bad "the file-mode check is damaged (private=$st_m0, file 644=$st_m1, folder 755=$st_m2)"; fi
  rm -rf "$st_mf"
  # a run started by a caller whose umask is 022 must still keep only private files (the script sets umask 077 itself)
  st_o=$( (umask 022; LEAD_REPIN_NO_META=1 TMPDIR="$st_child" sh "$SELF" "$st_t" 2>/dev/null) ); st_r=$?
  st_um=1; for st_d in "$st_child"/lead-repin.??????; do [ -d "$st_d" ] && st_um=$(st_modes "$st_d"); done
  if [ "$st_r" -eq 0 ] && [ "$st_um" -eq 0 ]; then mt_ok "a run started with umask 022 keeps only private files: the work folder 700, the output copy and the three rule files 600"; else mt_bad "a run started with umask 022 left a file that is not private (exit=$st_r, entries not private=$st_um)"; fi
  rm -rf "$st_child"/lead-repin.??????
  st_o=$(LEAD_REPIN_NO_META=1 TMPDIR="$st_child" sh "$SELF" "$st_t" 2>/dev/null); st_r=$?
  for st_d in "$st_child"/lead-repin.??????; do
    [ -d "$st_d" ] || continue
    st_um=$(st_modes "$st_d")
    if [ "$st_um" -eq 0 ]; then mt_ok "the kept work folder is mode 700 and every file in it is mode 600"; else mt_bad "the kept work folder holds $st_um entries that are not private (mode 700 folder, 600 files wanted)"; fi
    st_n=$(ls "$st_d" | wc -l | tr -d ' ')
    if [ "$st_n" -le 6 ] && ! grep -a -r -q -F -- 'a.py' "$st_d" 2>/dev/null; then mt_ok "the kept folder holds only the output copy and the rule files ($st_n files, no file name list)"
    else mt_bad "the kept folder still holds lists of file names ($st_n files)"; fi
    rm -rf "$st_d"
  done
  # ---- v5 machinery checks: the return value, the locale, file names with sed characters, PATH, sh -x, signals
  case $SELF in /*) st_sa=$SELF ;; *) st_sa=$PWD/$SELF ;; esac
  st_o=$( (LEAD_REPIN_TEST_LATE_FAIL=1; self_test 1 > /dev/null 2>&1; echo $?) )
  if [ "${st_o:-0}" -ne 0 ]; then mt_ok "a failure that only the return value of the self-test shows is a non-zero return"; else mt_bad "the return value of the self-test must be non-zero when a check failed late (got ${st_o:-none})"; fi
  if [ "${LC_ALL:-}" = C ]; then mt_ok "the filter runs with LC_ALL=C (byte-wise matching)"; else mt_bad "LC_ALL is not C in the filter (it is '${LC_ALL:-unset}')"; fi
  # the two judgements of a self-test result, each tried alone on forged results (a damaged judge must be seen)
  st_fd=$WORK/st-forged; mkdir -p "$st_fd"
  printf 'PASS a\nSELF-TEST: passed=5 failed=0 (x)\n' > "$st_fd/good"
  printf 'PASS a\nFAIL b\nSELF-TEST: passed=5 failed=0 (x)\n' > "$st_fd/failline"
  printf 'PASS a\nSELF-TEST: passed=3 failed=2 (x)\n' > "$st_fd/badtally"
  printf '' > "$st_fd/empty"
  st_jok=1
  for st_j in st_verdict st_recount; do
    "$st_j" "$st_fd/good" 0 || st_jok=0
    "$st_j" "$st_fd/good" 1 && st_jok=0
    "$st_j" "$st_fd/failline" 0 && st_jok=0
    "$st_j" "$st_fd/badtally" 0 && st_jok=0
    "$st_j" "$st_fd/empty" 0 && st_jok=0
  done
  # v6: the planned number of cases is part of the verdict: a good result with another count is refused by both judges
  st_pok=1
  for st_j in st_verdict st_recount; do
    "$st_j" "$st_fd/good" 0 5 || st_pok=0
    "$st_j" "$st_fd/good" 0 6 && st_pok=0
    "$st_j" "$st_fd/good" 0 4 && st_pok=0
  done
  if [ "$st_pok" -eq 1 ]; then mt_ok "each judge refuses a result whose number of passed cases is not the planned number (a forged shorter list)"; else mt_bad "a judge accepted a result with the wrong number of cases"; fi
  if [ "$st_jok" -eq 1 ]; then mt_ok "each judge of the self-test result accepts a good result and rejects a FAIL line, a bad tally, an empty result and a non-zero return"; else mt_bad "a judge of the self-test result accepted a forged result or rejected a good one"; fi
  rm -rf "$st_fd"
  # the report of left-out files counts names with a line break and symbolic links
  st_t3=$WORK/st-take3; mkdir -p "$st_t3"
  : > "$st_t3/a${NL}b.py"; ln -s a.py "$st_t3/link.py" 2>/dev/null
  st_o=$(skip_report "$st_t3" "made-up" code 2>&1)
  if printf '%s\n' "$st_o" | grep -a -q -F -- 'names with a line break (cannot be listed safely): 1' && printf '%s\n' "$st_o" | grep -a -q -F -- 'symbolic links of any kind (find does not follow them): 1'; then mt_ok "the left-out report counts one name with a line break and one symbolic link"; else mt_bad "the left-out report does not count a name with a line break or a symbolic link correctly"; fi
  rm -rf "$st_t3"
  st_t2=$WORK/st-take2; mkdir -p "$st_t2/_local/d#x&y\z" 2>/dev/null
  printf '{"a": "delete"}\n' > "$st_t2/_local/d#x&y\z/a#b&c.json"
  st_o=$(LEAD_REPIN_NO_META=1 TMPDIR="$st_child" sh "$st_sa" "$st_t2" 2>&1); st_r=$?
  if [ "$st_r" -eq 0 ] && printf '%s\n' "$st_o" | grep -a -q -F -- 'a#b&c.json:1:delet'; then mt_ok "a file name with # & and a backslash is printed as file:line:word (no sed expression is built from names)"
  else mt_bad "a file name with # & and a backslash must be printed as file:line:word (exit=$st_r)"; fi
  rm -rf "$st_t2" "$st_child"/lead-repin.??????
  st_plant=$WORK/st-plant; mkdir -p "$st_plant"; printf '#!/bin/sh\ntouch "%s/planted-ran"\nexec /bin/cat\n' "$st_plant" > "$st_plant/sed"; chmod +x "$st_plant/sed"
  st_o=$(cd "$st_plant" && printf 'API_KEY=%s_62_\n' "$base" | PATH=".:$PATH" LEAD_REPIN_NO_META=1 TMPDIR="$st_child" sh "$st_sa" --mask 2>/dev/null)
  if [ ! -e "$st_plant/planted-ran" ] && ! printf '%s' "$st_o" | grep -a -q -F -- "${base}_62_"; then mt_ok "a program planted in the current folder (PATH with a dot) is not run"; else mt_bad "a planted program in the current folder ran or a value showed"; fi
  rm -rf "$st_plant"
  printf 'API_KEY=%s_63_\n' "$base" | LEAD_REPIN_NO_META=1 TMPDIR="$st_child" sh -x "$st_sa" --mask > "$WORK/st-x.out" 2> "$WORK/st-x.err"
  if ! grep -a -q -F -- "${base}_63_" "$WORK/st-x.err" "$WORK/st-x.out"; then mt_ok "sh -x does not print a value (the script turns the trace off)"; else mt_bad "sh -x printed a value"; fi
  rm -f "$WORK/st-x.out" "$WORK/st-x.err"
  # signals in the MAIN phase (a fake git that sleeps keeps the checklist busy), and in --mask with an open input
  # st_alive PID: the program is running (a finished program that nobody has collected yet, state Z, is not running)
  st_alive() { st_s=$(ps -p "$1" -o stat= 2>/dev/null); case $st_s in ''|Z*) return 1 ;; esac; return 0; }
  st_fake=$WORK/st-fakebin; mkdir -p "$st_fake"; printf '#!/bin/sh\necho $$ > "%s/git.pid"\nexec sleep 31\n' "$st_fake" > "$st_fake/git"; chmod +x "$st_fake/git"
  for st_sig in TERM:143 HUP:129; do   # INT and QUIT cannot be tested from a shell: a program started with & by a non-interactive shell ignores them (see evidence-repin5, python launcher)
    st_sn=${st_sig%%:*}; st_se=${st_sig##*:}
    # v7: a caller that started the self-test with HUP ignored (for example nohup) makes every child ignore HUP too, and a signal ignored at entry cannot be caught by any script. Then this one case cannot be tested here: say so in the line (do not fail on the caller's setting)
    if [ "$st_sn" = HUP ] && [ "$(sh -c 'kill -s HUP $$; echo alive' 2>/dev/null)" = alive ]; then
      mt_ok "signal HUP in the main phase: NOT TESTED (the program that started this self-test ignores HUP, for example nohup; start it without nohup to test this case)"
      continue
    fi
    rm -f "$st_fake/git.pid"   # v7: removed BEFORE the run starts (v6 removed it after, and a fast start could lose the new file: a flaky failure under load)
    PATH="$st_fake:$PATH" LEAD_REPIN_NO_META=1 TMPDIR="$st_child" sh "$st_sa" "$st_t" > /dev/null 2>&1 &
    st_p=$!; st_i=0
    while [ "$st_i" -lt 30 ] && [ ! -s "$st_fake/git.pid" ]; do st_i=$((st_i + 1)); sleep 1; done
    st_gp=$(cat "$st_fake/git.pid" 2>/dev/null)
    kill -s "$st_sn" "$st_p" 2>/dev/null; wait "$st_p"; st_r=$?
    sleep 1
    st_stray=0; if [ -n "$st_gp" ] && st_alive "$st_gp"; then st_stray=1; fi; st_left=$(ls "$st_child" | wc -l | tr -d ' ')
    if [ "$st_r" -eq "$st_se" ] && [ "$st_stray" -eq 0 ] && [ "$st_left" -eq 0 ]; then mt_ok "signal $st_sn in the main phase: exit $st_se, no program of the run left running, no folder left"
    else mt_bad "signal $st_sn in the main phase (exit=$st_r wanted $st_se, programs left=$st_stray, folders left=$st_left)"; fi
    [ "$st_stray" -gt 0 ] && kill "$st_gp" 2>/dev/null   # only the process this check itself started (its recorded PID)
    rm -rf "$st_child"/lead-repin.??????
  done
  # v6: a signal during the PRE-MAIN phase (the file lists are being made) must act at once, not after the slow program ends
  rm -f "$st_fake/git" "$st_fake/git.pid"; printf '#!/bin/sh\necho $$ > "%s/find.pid"\nexec sleep 31\n' "$st_fake" > "$st_fake/find"; chmod +x "$st_fake/find"
  PATH="$st_fake:$PATH" LEAD_REPIN_NO_META=1 TMPDIR="$st_child" sh "$st_sa" "$st_t" > /dev/null 2>&1 &
  st_p=$!; st_i=0
  while [ "$st_i" -lt 30 ] && [ ! -s "$st_fake/find.pid" ]; do st_i=$((st_i + 1)); sleep 1; done
  st_gp=$(cat "$st_fake/find.pid" 2>/dev/null); st_t0=$(date +%s)
  kill -s TERM "$st_p" 2>/dev/null; wait "$st_p"; st_r=$?; st_t1=$(date +%s)
  sleep 1; st_stray=0; if [ -n "$st_gp" ] && st_alive "$st_gp"; then st_stray=1; kill "$st_gp" 2>/dev/null; fi
  if [ "$st_r" -eq 143 ] && [ "$st_stray" -eq 0 ] && [ $((st_t1 - st_t0)) -le 5 ]; then mt_ok "signal TERM while the file lists are made: exit 143 within 5 seconds, no program left"
  else mt_bad "signal TERM in the pre-main phase (exit=$st_r, seconds=$((st_t1 - st_t0)), programs left=$st_stray)"; fi
  rm -rf "$st_child"/lead-repin.?????? "$st_fake/find" "$st_fake/find.pid"
  # v6: the time limit ends a stuck run by itself (here 2 seconds), says so, and leaves no folder
  printf '#!/bin/sh\necho $$ > "%s/git.pid"\nexec sleep 31\n' "$st_fake" > "$st_fake/git"; chmod +x "$st_fake/git"
  PATH="$st_fake:$PATH" LEAD_REPIN_MAX_SECONDS=2 LEAD_REPIN_NO_META=1 TMPDIR="$st_child" sh "$st_sa" "$st_t" > /dev/null 2> "$WORK/st-wd.err" &
  st_p=$!; wait "$st_p"; st_r=$?
  st_gp=$(cat "$st_fake/git.pid" 2>/dev/null); sleep 1; st_stray=0; if [ -n "$st_gp" ] && st_alive "$st_gp"; then st_stray=1; kill "$st_gp" 2>/dev/null; fi
  st_left=$(ls "$st_child" | wc -l | tr -d ' ')
  if [ "$st_r" -eq 143 ] && [ "$st_stray" -eq 0 ] && [ "$st_left" -eq 0 ] && grep -a -q 'took longer than 2 seconds' "$WORK/st-wd.err"; then mt_ok "the time limit (2 seconds here) ends a stuck run: exit 143, a message, no program and no folder left"
  else mt_bad "the time limit did not end a stuck run cleanly (exit=$st_r, programs left=$st_stray, folders left=$st_left)"; fi
  rm -rf "$st_child"/lead-repin.?????? "$WORK/st-wd.err"
  # v7/v8: git is started with settings that stop the folder's own signature program, hook folder and file-system monitor.
  # v8: EVERY git call (not only one) carries all four settings; git status is OFF by default and runs only with LEAD_REPIN_GIT_STATUS=1; the GIT_*
  # variables of the caller (GIT_DIR, GIT_WORK_TREE) are not passed on; a fake git that answers --version makes the status call reachable.
  cat > "$st_fake/git" <<EOF
#!/bin/sh
case \$1 in --version) echo "git version 2.40.0"; exit 0 ;; esac
printf 'ARGS %s\\n' "\$*" >> "$st_fake/git.args"
printf 'ENV GIT_DIR=%s GIT_WORK_TREE=%s GIT_CONFIG_GLOBAL=%s\\n' "\${GIT_DIR-unset}" "\${GIT_WORK_TREE-unset}" "\${GIT_CONFIG_GLOBAL-unset}" >> "$st_fake/git.args"
exit 0
EOF
  chmod +x "$st_fake/git"
  st_gok=1
  for st_gm in default status; do
    rm -f "$st_fake/git.args"
    if [ "$st_gm" = status ]; then st_gs=1; else st_gs=; fi
    PATH="$st_fake:$PATH" GIT_DIR=/nonexistent-gitdir GIT_WORK_TREE=/nonexistent-tree LEAD_REPIN_GIT_STATUS=$st_gs LEAD_REPIN_NO_META=1 TMPDIR="$st_child" sh "$st_sa" "$st_t" > /dev/null 2>&1
    [ -s "$st_fake/git.args" ] || st_gok=0
    st_na=$(grep -c '^ARGS ' "$st_fake/git.args" 2>/dev/null); st_nb=$(grep '^ARGS ' "$st_fake/git.args" 2>/dev/null | grep -c -F -e 'log.showSignature=false' )
    st_nc=$(grep '^ARGS ' "$st_fake/git.args" 2>/dev/null | grep -F -e 'log.showSignature=false' | grep -F -e 'gpg.program=/bin/false' | grep -F -e 'core.hooksPath=/dev/null' | grep -F -e 'core.fsmonitor=false' | grep -c -F -e '--no-optional-locks')
    [ "${st_na:-0}" -ge 1 ] && [ "${st_na:-0}" -eq "${st_nc:-1}" ] && [ "${st_nb:-0}" -eq "${st_na:-1}" ] || st_gok=0
    grep -q '^ENV GIT_DIR=unset GIT_WORK_TREE=unset GIT_CONFIG_GLOBAL=/dev/null$' "$st_fake/git.args" 2>/dev/null || st_gok=0
    if grep -c '^ENV ' "$st_fake/git.args" 2>/dev/null | grep -q -v -x "$st_na"; then st_gok=0; fi
    if grep '^ENV ' "$st_fake/git.args" 2>/dev/null | grep -q -v -x 'ENV GIT_DIR=unset GIT_WORK_TREE=unset GIT_CONFIG_GLOBAL=/dev/null'; then st_gok=0; fi
    st_ns=$(grep -c ' status ' "$st_fake/git.args" 2>/dev/null)
    if [ "$st_gm" = status ]; then [ "${st_ns:-0}" -ge 1 ] || st_gok=0; else [ "${st_ns:-0}" -eq 0 ] || st_gok=0; fi
    rm -rf "$st_child"/lead-repin.??????
  done
  if [ "$st_gok" -eq 1 ]; then mt_ok "every git call carries all four safety settings and --no-optional-locks, GIT_DIR and GIT_WORK_TREE of the caller are not passed on, and git status runs only with LEAD_REPIN_GIT_STATUS=1"
  else mt_bad "a git call is missing a safety setting, or a GIT_* variable of the caller reached git, or git status ran without LEAD_REPIN_GIT_STATUS=1 (or did not run with it)"; fi
  rm -rf "$st_child"/lead-repin.?????? "$st_fake/git" "$st_fake/git.args"
  # v8: a failing stage of the masking filter is not silent (unit check of the helper, then a whole run with a program that fails on one marked input line)
  st_mf=$WORK/st-maskfail; mkdir "$st_mf"
  ( WORK=$st_mf; printf 'x\n' | mstage sh -c 'cat > /dev/null; exit 7'; printf 'x\n' | mstage sh -c 'cat > /dev/null; exit 141'; [ "$(cat "$WORK/mask.fail" 2>/dev/null)" = "sh 7" ] ) && st_mu=1 || st_mu=0
  rm -rf "$st_mf"
  st_realtr=$(command -v tr)
  printf '#!/bin/sh\ncat > "%s/tr.in"\nif grep -a -q ZZFAILMARKZZ "%s/tr.in"; then exit 5; fi\nexec "%s" "$@" < "%s/tr.in"\n' "$st_fake" "$st_fake" "$st_realtr" "$st_fake" > "$st_fake/tr"; chmod +x "$st_fake/tr"
  st_o=$(printf 'ZZFAILMARKZZ\n' | PATH="$st_fake:$PATH" LEAD_REPIN_NO_META=1 TMPDIR="$st_child" sh "$st_sa" --mask 2>"$WORK/st-mf.err"); st_r=$?
  if [ "$st_mu" -eq 1 ] && [ "$st_r" -eq 4 ] && grep -a -q 'a stage of the masking filter failed' "$WORK/st-mf.err"; then mt_ok "a failing stage of the masking filter is recorded, and --mask then stops with exit 4 and says so"
  else mt_bad "a failing stage of the masking filter must stop --mask with exit 4 (helper=$st_mu, exit=$st_r)"; fi
  rm -rf "$st_fake/tr" "$st_fake/tr.in" "$WORK/st-mf.err" "$st_child"/lead-repin.??????
  # v8: a time limit that is a very long digit string is not a stop at once
  st_o=$(LEAD_REPIN_MAX_SECONDS=99999999999999999999999999 LEAD_REPIN_NO_META=1 TMPDIR="$st_child" sh "$st_sa" "$st_t" 2>/dev/null); st_r=$?
  if [ "$st_r" -eq 0 ] && printf '%s' "$st_o" | grep -a -q '^SUMMARY:'; then mt_ok "a time limit of 26 digits falls back to the default and the run ends normally"; else mt_bad "a time limit of 26 digits must not end the run (exit=$st_r)"; fi
  rm -rf "$st_child"/lead-repin.??????
  # v8: hostile lines of the longest allowed size (20000 characters of separators, quotes, brackets, name words) cost bounded time: ten lines in under 60 seconds
  st_hl=$WORK/st-hostile.txt
  awk 'BEGIN { split("a-|a:|[|password=|token_|a |\"|_|password\t|k-", u, "|"); for (k = 1; k <= 10; k++) { s = ""; while (length(s) < 20000) s = s u[k]; print substr(s, 1, 20000) } }' > "$st_hl"
  st_t0=$(date +%s); st_o=$(LEAD_REPIN_NO_META=1 TMPDIR="$st_child" sh "$st_sa" --mask < "$st_hl" 2>/dev/null | wc -l | tr -d ' '); st_t1=$(date +%s)
  if [ "$st_o" -eq 10 ] && [ $((st_t1 - st_t0)) -le 60 ]; then mt_ok "ten hostile lines of 20000 characters are masked in under 60 seconds (took $((st_t1 - st_t0)))"; else mt_bad "hostile long lines: ten lines expected, got $st_o, in $((st_t1 - st_t0)) seconds (limit 60)"; fi
  rm -f "$st_hl"; rm -rf "$st_child"/lead-repin.??????
  # v8: a shell function of the caller that replaces sed (bash: export -f) is not used
  if command -v bash > /dev/null 2>&1; then
    st_o=$(printf 'API_KEY=%s_64_\n' "$base" | env 'BASH_FUNC_sed%%=() { cat; }' LEAD_REPIN_NO_META=1 TMPDIR="$st_child" bash "$st_sa" --mask 2>/dev/null); st_r=$?
    if [ "$st_r" -eq 0 ] && ! printf '%s' "$st_o" | grep -a -q -F -- "${base}_64_"; then mt_ok "an exported bash function named sed does not replace the real sed"; else mt_bad "an exported bash function named sed replaced the real sed or the run failed (exit=$st_r)"; fi
  else mt_ok "an exported bash function named sed: NOT TESTED (bash is not installed here)"; fi
  rm -rf "$st_child"/lead-repin.??????
  # v7: a relative TMPDIR is refused (exit 2)
  st_o=$(TMPDIR=relative_dir LEAD_REPIN_NO_META=1 sh "$st_sa" --mask < /dev/null 2>&1); st_r=$?
  if [ "$st_r" -eq 2 ] && printf '%s\n' "$st_o" | grep -a -q -F 'TMPDIR must be an absolute path'; then mt_ok "a relative TMPDIR is refused with exit 2"; else mt_bad "a relative TMPDIR must be refused (exit=$st_r)"; fi
  st_pf=$WORK/st-pid; sh -c 'echo $$ > "$1"; exec sleep 29' sh "$st_pf" | LEAD_REPIN_NO_META=1 TMPDIR="$st_child" sh "$st_sa" --mask > /dev/null 2>&1 &
  st_p=$!; sleep 3
  kill -s TERM "$st_p" 2>/dev/null; wait "$st_p"; st_r=$?; sleep 1
  st_stray=$(ps -A -o args= 2>/dev/null | grep -c -- "$st_child/[l]ead-repin")
  [ -s "$st_pf" ] && kill "$(cat "$st_pf")" 2>/dev/null
  if [ "$st_r" -eq 143 ] && [ "$st_stray" -eq 0 ]; then mt_ok "signal TERM in --mask with the input still open: exit 143 and the masking sed and awk are gone"
  else mt_bad "signal TERM in --mask (exit=$st_r, masking programs left=$st_stray)"; fi
  rm -rf "$st_child"/lead-repin.?????? "$st_fake" "$st_pf"
  rm -rf "$st_child" "$st_t" "$WORK/st-meta.txt" "$WORK/st-bad1.sed" "$WORK/st-bad2.sed"
}

# ---------------------------------------------------------------- start: rule files, test hook, modes
write_mask_sed
write_mask_awk
# test hook (proves that a damaged filter is stopped by the canary): never set it in real use
case ${LEAD_REPIN_TEST_BREAK_FILTER:-} in
  weak)  for bf_f in "$MASKSED" "$MASKLINE"; do grep -v -F 'Bearer' "$bf_f" > "$WORK/brk.tmp"; cat "$WORK/brk.tmp" > "$bf_f"; done; rm -f "$WORK/brk.tmp" ;;
  empty) : > "$MASKSED" ;;
esac

# run_canary: run the quick self-test in the background (so a signal is handled at once), result in $CANARY
# st_verdict FILE RC: the verdict does not trust the return value of self_test alone: the printed text must
# also have no FAIL line and must end with a tally that says failed=0 with at least one case passed
st_verdict() {
  [ "$2" -eq 0 ] || return 1
  grep -a -q '^FAIL' "$1" && return 1
  grep -a -q "^SELF-TEST: passed=${3:-[1-9][0-9]*} failed=0 " "$1" || return 1
  return 0
}
# st_recount FILE RC: the same judgement again, by a different route (awk counts FAIL lines and reads the tally)
st_recount() {
  [ "$2" -eq 0 ] || return 1
  awk -v want="${3:-}" '/^FAIL/ { f++ } /^SELF-TEST: passed=[0-9]+ failed=0 / { split($2, a, "="); if (a[2] + 0 >= 1 && (want == "" || a[2] + 0 == want + 0)) ok++ } END { exit (f == 0 && ok == 1) ? 0 : 1 }' "$1"
}
run_canary() {
  self_test 1 > "$WORK/canary.out" 2>&1 < /dev/null &
  BGPID=$!; wait "$BGPID"; canary_rc=$?; BGPID=
  CANARY=$(cat "$WORK/canary.out" 2>/dev/null)
  if st_verdict "$WORK/canary.out" "$canary_rc" "$CANARY_PLANNED" && st_recount "$WORK/canary.out" "$canary_rc" "$CANARY_PLANNED"; then canary_rc=0; else canary_rc=1; fi
  rm -f "$WORK/canary.out" "$LENCUT"
  return "$canary_rc"
}

case ${1:-} in
  --mask)
    CLEAN=1
    exec 3<&0
    filter_ready || { echo "STOP: the masking filter is not usable here (needs GNU sed or a sed that knows s///I): refusing to print" >&2; exit 3; }
    if ! run_canary; then printf 'STOP: the masking self-test (canary) FAILED, no input was read:\n%s\n' "$CANARY" >&2; exit 3; fi
    mask <&3 &
    BGPID=$!; wait "$BGPID"; mrc=$?; BGPID=
    if [ -s "$WORK/mask.fail" ]; then echo "STOP: a stage of the masking filter failed ($(cut -d' ' -f1 "$WORK/mask.fail" | sort -u | tr '\n' ' ')): the output is NOT complete" >&2; exit 4; fi
    exit "$mrc" ;;
  --self-test)
    CLEAN=1; start_watchdog
    if [ -z "${SELFTEST_FILTER:-}" ]; then filter_ready || { echo "STOP: the masking filter is not usable here (needs GNU sed or a sed that knows s///I)" >&2; exit 3; }; fi
    self_test 0 > "$WORK/st-full.out" 2>&1 < /dev/null &
    BGPID=$!; wait "$BGPID"; strc=$?; BGPID=
    cat "$WORK/st-full.out"
    # two independent judgements: the function st_verdict AND a recount written out here (a damaged function cannot pass alone)
    if [ -n "${SELFTEST_FILTER:-}" ]; then stp=; elif [ -n "${LEAD_REPIN_NO_META:-}" ]; then stp=$CANARY_PLANNED; else stp=$SELFTEST_PLANNED; fi
    if st_verdict "$WORK/st-full.out" "$strc" "$stp" && st_recount "$WORK/st-full.out" "$strc" "$stp"; then exit 0; fi
    exit 1 ;;
esac

# ---------------------------------------------------------------- canary: the masking filter must work BEFORE any test-program file is opened
if ! filter_ready; then
  CLEAN=1
  echo "STOP: the masking filter is not usable here (the rule file is empty or this sed does not know s///I, which GNU sed does). No test-program file was opened." >&2
  exit 3
fi
if ! run_canary; then
  CLEAN=1
  printf 'STOP: the masking self-test (canary) FAILED, so the filter cannot be trusted and no test-program file was opened:\n%s\n' "$CANARY" >&2
  exit 3
fi
start_watchdog
printf 'WORK-FOLDER: %s\nCOPY-OF-OUTPUT (masked): %s\n' "$WORK" "$OUT" >&2   # on the screen even when the output is redirected
CLEAN=0   # the canary passed: a normal run keeps the masked output copy (every other exit above and below removes the folder)

# ---------------------------------------------------------------- settings
TAKE_DIR=${1:-$PWD}
if [ ! -d "$TAKE_DIR" ]; then echo "take folder not found: $TAKE_DIR" >&2; CLEAN=1; exit 2; fi
TAKE_DIR=$(cd "$TAKE_DIR" && pwd -P) || { echo "cannot enter the test-program folder: $TAKE_DIR" >&2; CLEAN=1; exit 2; }
[ -n "$TAKE_DIR" ] || { echo "take folder path is empty" >&2; CLEAN=1; exit 2; }
FLOWS_DIR=${FLOWS_DIR:-$TAKE_DIR}
MODEL_DIR=${MODEL_DIR:-}
MODEL_SETTINGS=${MODEL_SETTINGS:-}
ONE_STORE=${ONE_STORE:-}
LEAD_REPIN_NO_STATUS=${LEAD_REPIN_NO_STATUS:-}
LEAD_REPIN_GIT_STATUS=${LEAD_REPIN_GIT_STATUS:-}   # v8: git status runs ONLY when this is set to 1 (it can start programs named by the folder's own git settings)

END_RE=${END_RE:-"[\"']end[\"']|(^|[^A-Za-z_])END[A-Z_]*[[:space:]]*=|[=!]=[[:space:]]*end([^A-Za-z_]|\$)"}
MODEL_RE=${MODEL_RE:-'anthropic|messages\.create|/v1/messages|model_program|call_model|post_model|post_lead|llm|complete\(|burst|/qualify|/control|n8n_drive|urlopen|requests\.(get|post)|httpx|subprocess|Popen|webhook|127\.0\.0\.1|localhost'}
DELETE_RE=${DELETE_RE:-'delet|archiv|purg|remov|trash|gdpr|clean.?up|unlink|rmtree|method[^A-Za-z]{0,8}(delete|patch)'}
GI=-i   # grep case flag; set to empty for a case-sensitive search

# ---------------------------------------------------------------- file lists and path finding
PRUNE='-name .git -o -name node_modules -o -name _local -o -name secrets -o -name .venv -o -name venv -o -name __pycache__'
make_list() { # make_list OUTFILE ROOT KIND   KIND: code | json | py | pyall | named:NAME
  ml_out=$1; ml_root=$2; ml_kind=$3
  ( [ -n "$ml_root" ] && [ -d "$ml_root" ] && cd "$ml_root" || exit 1
    case $ml_kind in
      code) find . -maxdepth 4 -type d \( $PRUNE -o -name tests -o -name test \) -prune -o -type f \( -name '*.py' -o -name '*.sh' \) ! -name 'test_*' ! -name '*_test.py' ! -name 'conftest.py' ! -name "*${NL}*" -print ;;
      py)   find . -maxdepth 4 -type d \( $PRUNE -o -name tests -o -name test \) -prune -o -type f -name '*.py' ! -name 'test_*' ! -name '*_test.py' ! -name 'conftest.py' ! -name "*${NL}*" -print ;;
      pyall) find . -maxdepth 4 -type d \( $PRUNE \) -prune -o -type f -name '*.py' ! -name "*${NL}*" -print ;;
      json) find . -maxdepth 4 -type d \( $PRUNE \) -prune -o -type f -name '*.json' ! -name "*${NL}*" -print ;;
      named:*) find . -maxdepth 4 -type d \( $PRUNE \) -prune -o -type f -name "${ml_kind#named:}" ! -name "*${NL}*" -print ;;
    esac ) 2>/dev/null | sort | RT=$ml_root awk '{ sub(/^\.\//, ""); print ENVIRON["RT"] "/" $0 }' > "$ml_out"
}
# local_flow_report: flows under _local are NOT searched line by line and NEVER printed (a literal-substituted copy may hold real
# values in plain JSON fields); only the counts are shown (AGENT-SCOPE line 23, BL-wp6-G1: the real take needs such a local copy).
local_flow_report() {
  lf_root=$1
  [ -n "$lf_root" ] && [ -d "$lf_root" ] || return 0
  lf_files=$(cd "$lf_root" && find . -path '*/_local/*' -type f -name '*.json' -print 2>/dev/null | wc -l | tr -d ' ')
  printf '_local flow json files: %s. Only the matched WORD of each delete-word hit is printed (file:line:word), never the line, because a local copy may hold real values; open the lines yourself.\n' "$lf_files"
  if [ "${lf_files:-0}" -gt 0 ]; then
    lf_n=$( (cd "$lf_root" && find . -path '*/_local/*' -type f -name '*.json' -print 2>/dev/null | sort | while IFS= read -r lf_f; do grep -a -n -o -E -i -e "$DELETE_RE" -- "$lf_f" 2>/dev/null | LFF=$lf_f awk '{ print ENVIRON["LFF"] ":" $0 }'; done) | mask | tee "$WORK/lf.txt" | wc -l | tr -d ' ')
    head -50 "$WORK/lf.txt"
    printf '  _local delete-word hits: %s (first 50 shown above)\n' "$lf_n"
    rm -f "$WORK/lf.txt"
  fi
}

PATHNOTES=
resolve() { # resolve VARNAME FILENAME
  eval "rv_cur=\${$1:-}"
  if [ -n "$rv_cur" ]; then PATHNOTES="$PATHNOTES$1 = $rv_cur  (from the environment)
"; return; fi
  bg_wait make_list "$WORK/named.$2.txt" "$TAKE_DIR" "named:$2"
  rv_n=$(wc -l < "$WORK/named.$2.txt" | tr -d ' ')
  if [ "${rv_n:-0}" -eq 0 ]; then
    eval "$1=\"\$TAKE_DIR/$2\""
    PATHNOTES="$PATHNOTES$1 = NOT FOUND by name '$2' below $TAKE_DIR (set $1 to the real path)
"
    return
  fi
  rv_pick=$(awk -v t="$TAKE_DIR/scripts/" 'index($0, t) == 1 { print; exit }' "$WORK/named.$2.txt")
  [ -n "$rv_pick" ] || rv_pick=$(head -1 "$WORK/named.$2.txt")
  eval "$1=\$rv_pick"
  PATHNOTES="$PATHNOTES$1 = $rv_pick  (found by name; $rv_n file(s) with that name)
"
  if [ "$rv_n" -gt 1 ]; then PATHNOTES="$PATHNOTES    other files with that name (NOT used unless you set $1): $(grep -v -F -x "$rv_pick" "$WORK/named.$2.txt" | tr '\n' ' ')
"; fi
}
resolve TAKE_PY run_real_check_n8n.py
resolve CRM_PY crm_hubspot.py
resolve DRIVE_PY n8n_drive.py
resolve N8N_PY n8n.py
[ -n "$ONE_STORE" ] || { bg_wait make_list "$WORK/named.one.txt" "$TAKE_DIR" "named:DECISION-one-store.md"; ONE_STORE=$(head -1 "$WORK/named.one.txt"); [ -n "$ONE_STORE" ] || ONE_STORE=$TAKE_DIR/DECISION-one-store.md; }

bg_wait make_list "$WORK/list-code.txt" "$TAKE_DIR" code
bg_wait make_list "$WORK/list-flows.txt" "$FLOWS_DIR" json
bg_wait make_list "$WORK/list-test-all.txt" "$TAKE_DIR" pyall
if [ -n "$MODEL_DIR" ] && [ -d "$MODEL_DIR" ]; then
  bg_wait make_list "$WORK/list-model.txt" "$MODEL_DIR" py
  bg_wait make_list "$WORK/list-model-all.txt" "$MODEL_DIR" pyall
else : > "$WORK/list-model.txt"; : > "$WORK/list-model-all.txt"; fi
# the four resolved files are always searched first; the general list then leaves them out (no double counting)
: > "$WORK/four.txt"
for f4 in "$TAKE_PY" "$CRM_PY" "$DRIVE_PY" "$N8N_PY"; do [ -f "$f4" ] && printf '%s\n' "$f4" >> "$WORK/four.txt"; done
bg_wait grep -v -F -x -f "$WORK/four.txt" "$WORK/list-code.txt" > "$WORK/list-code-rest.txt" 2>/dev/null
[ -s "$WORK/four.txt" ] || cp "$WORK/list-code.txt" "$WORK/list-code-rest.txt"

# ---------------------------------------------------------------- counters and search helpers
blocks=0; search_blocks=0; with_hits=0; zero_hits=0; info_blocks=0; files_missing=0; files_unreadable=0
bh=0; bf=0; bm=0; bu=0; bkind=search
S_HITS=0; S_FILES=0; S_MISS=0; S_UNR=0; LAST_HITS=0
HIDDEN_VALUES=0; HIDDEN_LINES=0; S_MISMATCH=0; S_WORDHID=0; T_MISMATCH=0; T_WORDHID=0; T_ZEROFILES=0

begin() { # id, title, question
  [ -d "$WORK" ] || exit 9
  blocks=$((blocks + 1)); bh=0; bf=0; bm=0; bu=0; bkind=search
  printf '\n===== BLOCK %s: %s =====\n' "$1" "$2"
  printf 'QUESTION: %s\n' "$3"
}
finish() {
  printf '[block %s] total over all searches in this block: matching lines=%s files_read=%s missing=%s unreadable=%s (a total hides a zero: read the per-search lines above)\n' "$1" "$bh" "$bf" "$bm" "$bu"
  search_blocks=$((search_blocks + 1))
  if [ "$bh" -gt 0 ]; then with_hits=$((with_hits + 1)); else zero_hits=$((zero_hits + 1)); fi
}
finish_info() { # a block that prints facts, not search hits: it is not counted as "with hits" or "zero hits"
  printf '[block %s] information block (not a search with hits): files_read=%s missing=%s unreadable=%s\n' "$1" "$bf" "$bm" "$bu"
  info_blocks=$((info_blocks + 1))
}
search_begin() { S_HITS=0; S_FILES=0; S_MISS=0; S_UNR=0; S_LISTED=0; S_MISMATCH=0; S_WORDHID=0; printf -- '--- search: %s\n' "$1"; S_LABEL=$1; }
search_end() {
  printf '    [search "%s": matching lines=%s in %s file(s) with a match, files_read=%s missing=%s unreadable=%s]' "$S_LABEL" "$S_HITS" "$S_LISTED" "$S_FILES" "$S_MISS" "$S_UNR"
  if [ "$S_FILES" -eq 0 ]; then printf ' ZERO FILES SEARCHED: nothing was looked at'
  elif [ "$S_HITS" -eq 0 ]; then printf ' ZERO HITS: either not there or the search words are wrong; this is not proof of absence'; fi
  if [ "$S_UNR" -gt 0 ]; then printf ' (%s file(s) UNREADABLE: this count is NOT complete)' "$S_UNR"; fi
  printf '\n'
  T_MISMATCH=$((T_MISMATCH + S_MISMATCH)); T_WORDHID=$((T_WORDHID + S_WORDHID))
  [ "$S_FILES" -eq 0 ] && T_ZEROFILES=$((T_ZEROFILES + 1))
  bh=$((bh + S_HITS)); bf=$((bf + S_FILES)); bm=$((bm + S_MISS)); bu=$((bu + S_UNR))
  files_missing=$((files_missing + S_MISS)); files_unreadable=$((files_unreadable + S_UNR))
  LAST_HITS=$S_HITS
}
search_one() { # search_one PATTERN CONTEXT FILE      (files with no match are counted, not listed)
  [ -d "$WORK" ] || exit 9
  so_pat=$1; so_ctx=$2; so_f=$3
  if [ -z "$so_f" ] || [ ! -e "$so_f" ]; then S_MISS=$((S_MISS + 1)); printf 'FILE MISSING (adjust the path): %s\n' "$so_f"; return; fi
  if [ ! -f "$so_f" ] || [ ! -r "$so_f" ]; then S_UNR=$((S_UNR + 1)); printf 'UNREADABLE (not searched, NOT zero matches): %s\n' "$so_f"; return; fi
  so_c=$(grep -a -c -E $GI -e "$so_pat" -- "$so_f" 2>"$WORK/grep.err"); so_rc=$?
  if [ "$so_rc" -ge 2 ]; then S_UNR=$((S_UNR + 1)); printf 'UNREADABLE (grep failed: %s; not searched, NOT zero matches): %s\n' "$(head -1 "$WORK/grep.err" | cut -c1-120)" "$so_f"; return; fi
  so_c=${so_c:-0}
  S_FILES=$((S_FILES + 1)); S_HITS=$((S_HITS + so_c))
  if [ "$so_c" -gt 0 ]; then
    S_LISTED=$((S_LISTED + 1))
    printf '%s: %s match line(s)\n' "$so_f" "$so_c"
    # the grep output goes STRAIGHT into the masking filter: no unmasked copy is ever written to disk
    grep -a -n -E $GI -A "$so_ctx" -e "$so_pat" -- "$so_f" 2>/dev/null | mask > "$WORK/m.txt"
    cat "$WORK/m.txt"
    so_m=$(grep -a -c -E '<masked>|<email-masked>' "$WORK/m.txt"); so_m=${so_m:-0}
    so_w=$(grep -a -c -E '^([0-9]+[-:])?<masked>$' "$WORK/m.txt"); so_w=${so_w:-0}
    HIDDEN_VALUES=$((HIDDEN_VALUES + so_m)); HIDDEN_LINES=$((HIDDEN_LINES + so_w))
    [ "$so_m" -gt 0 ] && printf '    (a value was hidden on %s line(s) above; %s of them were hidden whole)\n' "$so_m" "$so_w"
    # printed lines against the count: every matching line must appear (as NN:) in what was printed
    so_p=$(grep -a -c -E '^[0-9]+:' "$WORK/m.txt"); so_p=${so_p:-0}
    if [ "$so_p" -ne "$so_c" ]; then
      printf '    PRINT MISMATCH: grep counted %s matching line(s) but %s were printed: %s line(s) are missing from the output above\n' "$so_c" "$so_p" "$((so_c - so_p))"
      S_MISMATCH=$((S_MISMATCH + 1))
    fi
    # match word hidden: the searched word itself is not visible on a printed matching line (hidden or cut)
    so_h=$(grep -a -n -o -E $GI -e "$so_pat" -- "$so_f" 2>/dev/null | awk -v ci="${GI:+1}" -v mf="$WORK/m.txt" -F: '
      FILENAME == mf { if ($0 ~ /^[0-9]+:/) { t = $0; sub(/^[0-9]+:/, "", t); L[$1 + 0] = (ci ? tolower(t) : t) } next }
      { n = $1 + 0; w = $0; sub(/^[0-9]+:/, "", w); if (ci) w = tolower(w)
        if (!(n in L) || index(L[n], w) == 0) { c++; if (c <= 20) list = list (list == "" ? "" : ",") n } }
      END { printf "%d %s", c + 0, list }' "$WORK/m.txt" - )
    so_hn=${so_h%% *}; so_hl=${so_h#* }
    if [ "${so_hn:-0}" -gt 0 ]; then
      printf '    MATCH WORD HIDDEN on %s matching line(s) (the filter hid it or the line was cut; open the file at line(s) %s yourself)\n' "$so_hn" "$so_hl"
      S_WORDHID=$((S_WORDHID + so_hn))
    fi
  fi
}
S() { # S LABEL PATTERN CONTEXT FILE...
  sl=$1; sp=$2; sc=$3; shift 3
  search_begin "$sl"
  for sf in "$@"; do search_one "$sp" "$sc" "$sf"; done
  search_end
}
SL() { # SL LABEL PATTERN CONTEXT LISTFILE : one file per line (spaces in names are safe)
  sl=$1; sp=$2; sc=$3; slf=$4
  search_begin "$sl"
  if [ -s "$slf" ]; then
    while IFS= read -r sf; do [ -n "$sf" ] && search_one "$sp" "$sc" "$sf"; done < "$slf"
  fi
  search_end
}
lines() { # lines FILE FROM TO   (prints with line numbers; says when the range is outside the file)
  f=$1; a=$2; b=$3
  if [ ! -e "$f" ]; then bm=$((bm + 1)); files_missing=$((files_missing + 1)); printf 'FILE MISSING (adjust the path): %s\n' "$f"; return; fi
  if [ ! -f "$f" ] || [ ! -r "$f" ]; then bu=$((bu + 1)); files_unreadable=$((files_unreadable + 1)); printf 'UNREADABLE (not read): %s\n' "$f"; return; fi
  bf=$((bf + 1))
  n=$(wc -l < "$f" | tr -d ' '); n=${n:-0}
  printf '%s has %s line(s); lines %s-%s:\n' "$f" "$n" "$a" "$b"
  if [ "$n" -lt "$a" ]; then printf '(file is shorter than line %s: that line number is stale or wrong)\n' "$a"
  else
    if [ "$n" -lt "$b" ]; then printf '(the file ends at line %s: lines %s-%s do not exist)\n' "$n" "$((n + 1))" "$b"; fi
    sed -n "${a},${b}p" -- "$f" | awk -v s="$a" '{ printf "%d:%s\n", NR + s - 1, $0 }' | mask
  fi
}
list_info() { # list_info LABEL LISTFILE
  li_n=$(wc -l < "$2" | tr -d ' ')
  printf 'files searched for "%s": %s' "$1" "${li_n:-0}"
  if [ "${li_n:-0}" -eq 0 ]; then printf '   <<< 0 FILES SEARCHED: the searches below looked at nothing; check TAKE_DIR / FLOWS_DIR / MODEL_DIR'; fi
  printf '\n'
}
g() { git --no-optional-locks -c core.fsmonitor=false -c log.showSignature=false -c gpg.program=/bin/false -c core.hooksPath=/dev/null -C "$TAKE_DIR" "$@"; }
model_notice() {
  if [ -z "$MODEL_DIR" ] || [ ! -d "$MODEL_DIR" ]; then
    printf '*** MODEL_DIR is not set (or not a folder): the MODEL PROGRAM IS NOT SEARCHED. This is "not looked at", not "absent". %s cannot be answered by this run: set MODEL_DIR and run again.\n' "$1"
  fi
}

# ---------------------------------------------------------------- the checklist
main() {
  printf 'lead-repin-verify.sh v6  (reads only; prints, never judges; the lead reads this output before sharing it)\n'
  printf 'masking self-test (canary) before any file was opened: %s\n' "$CANARY"
  printf 'take folder: %s\n' "$TAKE_DIR"
  printf 'private work folder (made by mktemp; after this run it keeps ONLY the masked output copy and the three masking rule files; delete it yourself): %s\n' "$WORK"
  printf 'copy of this output (masked): %s\n' "$OUT"
  printf 'Nothing below was checked against a real test program by the builder of this script.\n'
  printf 'Q27 a, b and c stay UNVERIFIED until the lead shows them at the final head; this script only finds text.\n'
  printf 'Files used:\n%s' "$PATHNOTES"
  for f4 in "$TAKE_PY" "$CRM_PY" "$DRIVE_PY" "$N8N_PY"; do
    case $f4 in "$TAKE_DIR"/*) ;; *) printf 'NOTE: %s is OUTSIDE the test-program folder (it is still searched, because it is one of the four named files).\n' "$f4" ;; esac
  done
  printf 'FLOWS_DIR = %s\nMODEL_DIR = %s\n' "$FLOWS_DIR" "${MODEL_DIR:-<not set: the model program folder is NOT SEARCHED>}"
  printf 'Left out on purpose (counts are printed in block Q23-1): folders .git node_modules _local secrets .venv venv __pycache__ tests test; files test_*, *_test.py, conftest.py (only below the test-program folder, so a test-program folder under a test_ parent is still searched); files whose path has 5 or more parts (a/b/c/d/file; at most 3 sub-folders below the folder are searched); symbolic links; every file that is not python, shell or json.\n'
  list_info "python and shell files of the test program (the four named files are searched first and left out of this list)" "$WORK/list-code-rest.txt"
  list_info "flow json files" "$WORK/list-flows.txt"
  list_info "model program python files (tests left out)" "$WORK/list-model.txt"
  model_notice "Q27 a (model side), Q27 b (model side and qs_37 on the model side) and Q27 c (half B)"

  : > "$SHAOK"
  begin R00 "Final head identity (G1, G26)" "Which commit id and which file checksums are these answers about?"
  if command -v git >/dev/null 2>&1 && g rev-parse --git-dir >/dev/null 2>&1; then
    printf 'git work tree top folder: %s (if this is a PARENT of the test-program folder, the commit id below is the parent repository'"'"'s)\n' "$(g rev-parse --show-toplevel 2>&1)"
    head_l="HEAD: $(g rev-parse HEAD 2>&1)"
    printf '%s\n' "$head_l" >> "$SHAOK"; printf '%s\n' "$head_l"
    # core.fsmonitor=false is read as a true/false switch only by git 2.36 and newer; an older git reads it as the name
    # of a program to run, so git status is skipped there
    gv=$(git --version 2>/dev/null | awk '{ split($3, a, "."); print a[1] * 1000 + a[2] }')
    if [ -n "$LEAD_REPIN_NO_STATUS" ]; then printf 'changed or untracked files (count): NOT READ (LEAD_REPIN_NO_STATUS is set)\n'
    elif [ "$LEAD_REPIN_GIT_STATUS" != 1 ]; then printf 'changed or untracked files (count): NOT READ (git status can start programs named by the folder'"'"'s own git settings, so it is off unless you set LEAD_REPIN_GIT_STATUS=1 for a folder you trust)\n'
    elif [ "${gv:-0}" -lt 2036 ]; then printf 'changed or untracked files (count): NOT READ (git version %s is older than 2.36: the switch core.fsmonitor=false could be read as a program name)\n' "$(git --version 2>&1)"
    else printf 'changed or untracked files (count): %s\n' "$(g status --porcelain 2>&1 | wc -l | tr -d ' ')"; fi
    g log -1 --format='last commit: %h %ci' 2>&1
  else
    printf 'not a git work tree (or git missing): cannot print a commit id here\n'
  fi
  for f in "$TAKE_PY" "$CRM_PY" "$DRIVE_PY" "$N8N_PY"; do
    if [ -f "$f" ] && [ ! -r "$f" ]; then bu=$((bu + 1)); files_unreadable=$((files_unreadable + 1)); printf 'UNREADABLE (checksum not made, NOT zero): %s\n' "$f"
    elif [ -f "$f" ]; then
      bf=$((bf + 1))
      if command -v sha256sum >/dev/null 2>&1; then sha_l=$(sha256sum -- "$f" 2>&1); else sha_l=$(shasum -a 256 -- "$f" 2>&1); fi
      printf '%s\n' "$sha_l" >> "$SHAOK"; printf '%s\n' "$sha_l"
    else bm=$((bm + 1)); files_missing=$((files_missing + 1)); printf 'FILE MISSING (adjust the path): %s\n' "$f"; fi
  done
  finish_info R00

  begin Q23-1 "Any delete or archive path to the CRM (Q23, G1)" "Does any python or shell file of the test program (not tests), the CRM module or any flow json contain a delete, archive, purge, remove or cleanup path to the CRM? Decision 2 (the take never deletes) stays; the r17 review found only a rows_with_prefix GET; two earlier reviews DISAGREE (see the document); this block is the final-head grep the lead shows."
  printf 'NOTE: the flow json files in the folder can differ from what n8n actually holds after import (G3); compare with the G2 checksum step.\n'
  printf 'NOTE: AGENT-SCOPE line 20 (citing review-codebase-1.md F-01) says the test program archives its contacts with a DELETE call at run_real_check_n8n.py:1051 and crm_hubspot.py:504-509; the r17 review (ORDERS Q23) says there is no delete path. This script does not decide between them: block Q23-2 prints what stands at those lines today.\n'
  skip_report "$TAKE_DIR" "take folder, python and shell" code
  skip_report "$FLOWS_DIR" "flows folder, json" json
  local_flow_report "$FLOWS_DIR"
  S "delete words in the four named files (test program, CRM module, n8n_drive.py, n8n.py): always searched" "$DELETE_RE" 1 "$TAKE_PY" "$CRM_PY" "$DRIVE_PY" "$N8N_PY"
  SL "delete words in the other python and shell files of the test program" "$DELETE_RE" 1 "$WORK/list-code-rest.txt"
  SL "delete words in flow json files" "$DELETE_RE" 1 "$WORK/list-flows.txt"
  printf 'READ THE ZERO LINES: "0 matching lines" means "none in the files listed above"; the counts of left-out files above say what was never looked at.\n'
  finish Q23-1

  begin Q23-2 "The old line numbers (Q23)" "What stands today at run_real_check_n8n.py lines 1045-1056 and crm_hubspot.py lines 500-512? (AGENT-SCOPE line 20 cites a DELETE call at line 1051 and at 504-509; the lead's answer calls that UNVERIFIED stale text.)"
  lines "$TAKE_PY" 1045 1056
  lines "$CRM_PY" 500 512
  finish_info Q23-2

  begin Q23-3 "HTTP methods the CRM module uses (Q23, G21)" "Which HTTP methods does the CRM module send? (r17 saw only a rows_with_prefix GET)"
  GI=
  S "HTTP method names, request helpers, rows_with_prefix (case-sensitive)" '(^|[^A-Za-z_])(GET|POST|PUT|PATCH|DELETE|HEAD)([^A-Za-z_]|$)|rows_with_prefix|method[[:space:]]*=|urlopen|requests\.|http\.client|session\.' 0 "$CRM_PY"
  GI=-i
  finish Q23-3

  begin Q23-4 "Delete wording printed to the owner (G1, G17)" "Do the notice or the printed result of any of the four named files still say deleted or archived, or print a delete count?"
  S "delete, archive or purge wording in the four named files" 'delet|archiv|purg' 0 "$TAKE_PY" "$CRM_PY" "$DRIVE_PY" "$N8N_PY"
  finish Q23-4

  begin Q27a "Model call after the word end (Q27 a, G34): UNVERIFIED until the lead shows it" "After the test program reads the word end, can it still call the model? Part 1: lines with the end handling (and 20 lines after). Part 2: every model-call line."
  model_notice "Q27 a (model side)"
  GI=
  S "end handling in the test program (case-sensitive; includes constants; a hit may be help or usage text: read the line)" "$END_RE" 20 "$TAKE_PY"
  GI=-i
  ha=$LAST_HITS
  S "model-call words in the test program, n8n_drive.py and n8n.py" "$MODEL_RE" 0 "$TAKE_PY" "$DRIVE_PY" "$N8N_PY"
  hb=$LAST_HITS
  SL "model-call words in the model program folder (only if MODEL_DIR is set)" "$MODEL_RE" 0 "$WORK/list-model.txt"
  printf 'Q27a reading: end-handling lines=%s, model-call lines=%s. Zero in either means the words are probably wrong, NOT "no model call".\n' "$ha" "$hb"
  printf 'Reading a program cannot show (1) a call already sent before end or (2) an n8n retry or lease that fires a call after end: those need a run or a test shown at the final head. Line order is not always run order.\n'
  finish Q27a

  begin Q27b "End-date refusal (Q27 b, G16, G10): UNVERIFIED until the lead shows it" "Does a setting that refuses a call after the window end exist, and is a refusal SHOWN at the final head (a test run or a startup refusal)?"
  model_notice "Q27 b (model side)"
  printf 'SPEND WARNING: to SEE the refusal run ONLY the named qs_37 test, against the FAKE model. Never start the real model program or the real stage with a real key to "see" a refusal: that can make a paid call. This script starts nothing.\n'
  S "window end, need_seconds, refusal words in the test program" 'window|end_date|not_after|deadline|need_seconds|2026-11-2|refus' 0 "$TAKE_PY"
  SL "same words in the model program folder (only if MODEL_DIR is set)" 'window|end_date|not_after|deadline|2026-11-2|refus|after the' 0 "$WORK/list-model.txt"
  list_info "python files of the test program, tests INCLUDED (for qs_37)" "$WORK/list-test-all.txt"
  list_info "python files of the model program folder, tests INCLUDED (for qs_37)" "$WORK/list-model-all.txt"
  if [ -n "$MODEL_DIR" ] && [ -d "$MODEL_DIR" ]; then skip_report "$MODEL_DIR" "model program folder, python and shell" code; fi
  SL "test name qs_37 in the test-program folder (tests included)" 'qs_37' 0 "$WORK/list-test-all.txt"
  SL "test name qs_37 in the model program folder (tests included; only if MODEL_DIR is set)" 'qs_37' 0 "$WORK/list-model-all.txt"
  if [ -n "$MODEL_SETTINGS" ] && [ -f "$MODEL_SETTINGS" ] && [ -r "$MODEL_SETTINGS" ]; then
    printf -- '--- search: settings lines whose NAME has the whole word end, window, deadline, until or not_after (a value is shown ONLY if it looks like a date or a number; any other value is replaced by a note)\n'
    bf=$((bf + 1))
    cat > "$WORK/val.awk" <<'VALEOF'
{ line = $0; pre = ""
  if (match(line, /^[0-9]+[:-]/)) { pre = substr(line, 1, RLENGTH); line = substr(line, RLENGTH + 1) }
  sep = match(line, /[=:]/); if (!sep) next
  key = substr(line, 1, sep - 1); val = substr(line, sep + 1)
  gsub(/^[ \t]+|[ \t]+$/, "", key); sub(/^export[ \t]+/, "", key)
  gsub(/^[ \t"']+|[ \t"',]+$/, "", val)
  k = tolower(key)
  if (!(k ~ /(^|[^a-z0-9])(end|window|deadline|until)([^a-z0-9]|$)/ || index(k, "not_after"))) next
  if (val ~ /^[0-9][0-9.:+TZtz -]*$/) print pre key " = " val
  else print pre key " = <value not shown: it does not look like a date or a number>"
}
VALEOF
    grep -a -n -E '[=:]' "$MODEL_SETTINGS" 2>/dev/null | awk -f "$WORK/val.awk" | mask | head -20
  else printf 'MODEL_SETTINGS not set, missing or unreadable: settings NOT SEARCHED (adjust)\n'; fi
  printf 'NOTE: to SEE the refusal, run the named test (fake model only) or read the startup refusal at the final head; this script only finds text.\n'
  finish Q27b

  begin Q27c "Go marker before any model call (Q27 c, G33): UNVERIFIED until the lead shows it" "Does the model program refuse to make a paid call until the test program has written a marker after the accepted challenge? BOTH halves are needed."
  model_notice "Q27 c (half B)"
  S "half A: marker words in the test program" 'marker|go_file|ready_file|\.used|\.go([^A-Za-z]|$)|accepted|challenge' 0 "$TAKE_PY"
  hA=$LAST_HITS
  SL "half B: marker words in the model program folder (only if MODEL_DIR is set)" 'marker|go_file|ready_file|\.go([^A-Za-z]|$)|exists\(|isfile' 0 "$WORK/list-model.txt"
  hB=$LAST_HITS
  printf 'Q27c reading: test-program half hits=%s, model-program half hits=%s. Both halves must be shown; a zero in either half means NOT SHOWN by this search. The .used tag marker is not shown to be the go marker.\n' "$hA" "$hB"
  finish Q27c

  begin G35 "Prompts to the owner (G35)" "Does the test program ask the owner to type anything besides y, the challenge line and end?"
  S "input and prompt words in the test program" 'input\(|getpass|readline|stdin|isatty|worst.?case|figure' 0 "$TAKE_PY"
  finish G35

  begin G06 "Exit codes (G6, Q20.4)" "Which exit codes can the test program leave, and which one for person C unknown?"
  S "exit words in the test program" 'sys\.exit|[^a-z_]exit\(|SystemExit|EXIT_|return [0-3]$|unknown' 0 "$TAKE_PY"
  finish G06

  begin G04 "Call ceiling, price and ledger (G4, G14)" "Where are the call ceiling, retries, ledger total and program limit set?"
  S "ceiling words in the test program" 'ceiling|max_calls|retries|retry|ledger|backstop|program.?limit|180|189|price' 0 "$TAKE_PY"
  SL "ceiling words in the model program folder (only if MODEL_DIR is set)" 'ceiling|max_calls|retries|retry|ledger|backstop|limit|180|189|price' 0 "$WORK/list-model.txt"
  finish G04

  begin G18 "Stop, signal and lock behaviour (G18)" "What happens on a wrong line after end, Ctrl-C, a pause that ends without end, a cancelled key; which lock file is left?"
  S "signal and lock words in the test program" 'KeyboardInterrupt|SIGINT|SIGTERM|SIGHUP|\.lock|closing|interrupted|called off|timeout|give.?up' 0 "$TAKE_PY"
  finish G18

  begin G36 "Think time, silence and film cue (G36)" "Which printed line could start the film pause, and what are the minimum think time, silence and give-up values?"
  S "pause words in the test program" 'think|silence|give.?up|pause|film|sleep\(|print\(.*(start|wait)' 0 "$TAKE_PY"
  finish G36

  begin G37-38 "Per-run key file, demo mail subject, prep contact (G37, G38)" "How is the per-run key file made (does it refuse an existing file), what starts the test program mail subjects, and does the prep contact address match the film search?"
  S "file-creation and subject words in the test program" 'set -C|noclobber|O_EXCL|key_file|subject|take-|prep-|label|demo' 0 "$TAKE_PY"
  finish G37-38

  begin G07 "Ports (G7)" "Which of the ports 5678, 5679, 5690-5693, 5701, 5702 are listening now, and does the test program name its own port?"
  if grep -qi microsoft /proc/version 2>/dev/null; then printf 'NOTE: this looks like WSL: ss here does NOT see programs listening on Windows (such as the owner n8n on 5678/5679). Check on Windows with: netstat -ano | findstr "5678 5679".\n'; fi
  if command -v ss >/dev/null 2>&1; then lt=$(ss -tln 2>&1); lt_tool=ss
  elif command -v netstat >/dev/null 2>&1; then lt=$(netstat -tln 2>&1); lt_tool=netstat
  elif [ -r /proc/net/tcp ]; then
    lt=$(awk '$4=="0A"{n=split($2,a,":"); print a[n]}' /proc/net/tcp /proc/net/tcp6 2>/dev/null | while read -r h; do printf '127.0.0.1:%d \n' "0x$h"; done | sort -u); lt_tool='/proc/net/tcp (ports only, address not shown)'
  else lt=; lt_tool=none; fi
  if [ "$lt_tool" = none ]; then bm=$((bm + 1)); files_missing=$((files_missing + 1)); printf 'none of ss, netstat or /proc/net/tcp found: check the ports by hand\n'
  else
    bf=$((bf + 1)); o=$(printf '%s\n' "$lt" | grep -E ':(5678|5679|569[0-3]|570[0-9])[[:space:]]')
    if [ -n "$o" ]; then printf 'listening (from %s):\n%s\n' "$lt_tool" "$o"; else printf 'none of those ports is listening now (from %s)\n' "$lt_tool"; fi
  fi
  S "port numbers in the test program" '5678|5679|569[0-3]|570[0-9]' 0 "$TAKE_PY"
  finish G07

  begin G20 "DECISION-one-store line 14 (G20)" "Does line 14 still say ONE database?"
  lines "$ONE_STORE" 14 14
  finish_info G20

  printf '\n'
  if [ -z "$MODEL_DIR" ] || [ ! -d "$MODEL_DIR" ]; then printf 'CANNOT BE ANSWERED WITHOUT MODEL_DIR: Q27 a model side, Q27 b model side and qs_37 model side, Q27 c half B (so Q27 c cannot be answered at all by this run).\n'; fi
  rc_n=0
  printf 'RUN-CHECK (what this run itself could not do; it does not judge the answers):\n'
  [ "$files_missing" -gt 0 ] && { rc_n=$((rc_n + 1)); printf '  STOP-SIGNAL: %s file(s) MISSING (a wrong path, not a zero count): fix the path and run again.\n' "$files_missing"; }
  [ "$files_unreadable" -gt 0 ] && { rc_n=$((rc_n + 1)); printf '  STOP-SIGNAL: %s file(s) UNREADABLE (not searched): fix the permission or tell the lead.\n' "$files_unreadable"; }
  [ "$T_ZEROFILES" -gt 0 ] && { rc_n=$((rc_n + 1)); printf '  STOP-SIGNAL: %s search(es) looked at ZERO FILES: a "0 matching lines" there means nothing.\n' "$T_ZEROFILES"; }
  [ "$T_MISMATCH" -gt 0 ] && { rc_n=$((rc_n + 1)); printf '  STOP-SIGNAL: %s search(es) printed fewer lines than grep counted (PRINT MISMATCH).\n' "$T_MISMATCH"; }
  [ "$T_WORDHID" -gt 0 ] && { rc_n=$((rc_n + 1)); printf '  STOP-SIGNAL: on %s matching line(s) the searched word itself was hidden: open those lines in the file yourself.\n' "$T_WORDHID"; }
  if [ -z "$MODEL_DIR" ] || [ ! -d "$MODEL_DIR" ]; then printf '  LIMIT: MODEL_DIR not set: the model side of Q27 a, b and c was NOT looked at (that is not a failure of the run; it means those answers are open).\n'; fi
  if [ "$rc_n" -eq 0 ]; then printf '  RUN-CHECK: no stop signal from the run itself. This does NOT mean the answers are good: read every block.\n'
  else printf '  RUN-CHECK: %s stop signal(s). Do not use the zero counts of the searches named above; fix, run again, or ask the lead.\n' "$rc_n"; fi
  printf 'SUMMARY: blocks=%s search_blocks=%s with_hits=%s zero_hits=%s information_blocks=%s files_missing=%s files_unreadable=%s (counts only; nothing judged; the lead reads each block and the per-search ZERO lines)\n' \
    "$blocks" "$search_blocks" "$with_hits" "$zero_hits" "$info_blocks" "$files_missing" "$files_unreadable"
  printf 'Hidden by the masking filter in search results: %s line(s) had a value hidden, %s of them were hidden whole (next-line rule).\n' "$HIDDEN_VALUES" "$HIDDEN_LINES"
  printf 'Search lines that were NOT printed in full: %s search(es) had a PRINT MISMATCH; %s matching line(s) had the match word hidden (read the lines marked above).\n' "$T_MISMATCH" "$T_WORDHID"
  printf 'Length guard: %s input line(s) were longer than 20000 characters and were cut before masking (each is printed cut, with a CUT note when more than 240 characters remain).\n' "$( [ -f "$LENCUT" ] && wc -l < "$LENCUT" | tr -d ' ' || echo 0 )"
  printf 'Masking is a safety net: read this output yourself before you share it.\n'
  return 0
}

# the output goes through: counter, final belt over the whole text, counter, copy to the output file
cnt_awk='{ n += gsub(/<(email-)?masked>/, "&"); print } END { print n + 0 > f }'
( { main 2>&1; echo $? > "$WORK/main.rc"; } | awk -v f="$WORK/cnt-before" "$cnt_awk" | mask_line | awk -v f="$WORK/cnt-after" "$cnt_awk" | tee "$OUT" ) &
BGPID=$!; wait "$BGPID"; pipe_rc=$?; BGPID=
mfail=; [ -s "$WORK/mask.fail" ] && mfail=$(cut -d' ' -f1 "$WORK/mask.fail" | sort -u | tr '\n' ' ')
mrc=$(cat "$WORK/main.rc" 2>/dev/null); cb=$(cat "$WORK/cnt-before" 2>/dev/null); ca=$(cat "$WORK/cnt-after" 2>/dev/null)
# remove every working file except the masked output copy and the three rule files (file name lists may hold private names)
for fin_f in "$WORK"/* "$WORK"/.[!.]*; do
  [ -e "$fin_f" ] || continue
  case $fin_f in "$OUT"|"$MASKSED"|"$MASKLINE"|"$MASKAWK") ;; *) rm -rf "$fin_f" ;; esac
done
FINISHED=1   # the file-name lists are gone. A stop signal after this point still removes the whole work folder (on_signal sets CLEAN=1); only a kill that cannot be caught (SIGKILL, out of memory) leaves the masked output copy and the rule files behind
{
  printf 'Final pass over the whole output above: %s additional value(s) hidden (0 means the search-time filter had already hidden everything the belt knows).\n' "$(( ${ca:-0} - ${cb:-0} ))"
  printf 'The work folder %s now holds only: the masked output copy and the three masking rule files (lists of file names were deleted).\n' "$WORK"
} | mask_line | tee -a "$OUT"
if [ -n "$mfail" ]; then
  echo "STOP: a stage of the masking filter failed ($mfail): the output above is NOT complete" >&2
  exit 4
fi
if [ "$pipe_rc" -ne 0 ] || [ "${mrc:-1}" -ne 0 ]; then
  echo "STOP: the output pipeline failed (pipeline status $pipe_rc, checklist status ${mrc:-none}); the output above is NOT complete" >&2
  exit 4
fi
exit 0
