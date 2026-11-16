#!/bin/sh
# lead-repin-verify.sh (version 3): checklist printer for the lead at re-pin.
#
# WHAT IT DOES TO YOUR MACHINE (exact):
#   - reads files: grep, sed, awk, wc, find, sha256sum, git rev-parse / log / status
#     (git runs with --no-optional-locks and the file-system monitor switched off, so it
#     does not refresh or rewrite the git index; it still reads the folder metadata;
#     "git status" can start a program that the folder's own git settings name (a clean or
#     smudge filter, for example for large files): if you do not trust the folder, run with
#     LEAD_REPIN_NO_STATUS=1 and git status is skipped);
#   - reads the list of listening ports (ss, or netstat, or /proc/net/tcp);
#   - writes ONLY into one private work folder it makes with mktemp (permissions 700,
#     files 600 because of umask 077; on a Windows-mounted drive under WSL these modes may
#     NOT be enforced, so set TMPDIR to a Linux folder). What the work folder holds:
#       * a copy of this output (already masked),
#       * lists of file names (paths only, no file content),
#       * the masking rule files (no secret in them),
#       * small masked or empty helper files.
#     NO unmasked line of any searched file is ever written to disk: every search pipes
#     grep straight into the masking filter. The canary self-test (below) makes a file of
#     made-up secrets in the work folder and DELETES it again in the same second.
#   - DELETES only: (a) those two canary files, and (b) in the two helper modes
#     (--self-test and --mask) and when the canary test fails, the work folder it made
#     itself (the path is checked to be of the form .../lead-repin.XXXXXX before rm -rf).
#     A normal run keeps its work folder (it holds the masked output copy); delete it yourself;
#   - makes NO network call and NO model call. Apart from the tools named above it starts
#     no other program of the take. It never starts the model program.
# It judges NOTHING: it prints what it found, with line numbers, for the lead to read.
# Values that look like secrets are hidden by ONE masking filter (see "mask") that every
# search uses, and a canary self-test of that filter runs FIRST in every normal run: if the
# canary test fails, the script stops before it opens any take file. A filter is still a
# safety net, not a guarantee: THE LEAD READS THE OUTPUT BEFORE SHARING IT.
#
# usage:
#   sh lead-repin-verify.sh [TAKE_DIR]        run the checklist (TAKE_DIR defaults to the current folder)
#   sh lead-repin-verify.sh --self-test       test the masking filter with made-up secrets, print PASS/FAIL
#   <command> | sh lead-repin-verify.sh --mask   pass any text through the same masking filter
#   (test aid) SELFTEST_FILTER="sh other-version.sh --mask" sh lead-repin-verify.sh --self-test
#              runs the same test cases against another filter, to show that an old filter fails them.
#
# Needs: GNU sed (or a sed that knows the s///I flag; the canary stops the run otherwise), grep, awk, find.
# Every file name below is "adjust if different": set the variable in the environment.
# If TAKE_PY, CRM_PY, DRIVE_PY or N8N_PY is not set, the script looks for the file BY NAME
# (up to 4 folders deep below TAKE_DIR, preferring a scripts/ folder) and prints which one it used.
#   TAKE_PY CRM_PY DRIVE_PY N8N_PY FLOWS_DIR MODEL_DIR MODEL_SETTINGS ONE_STORE END_RE MODEL_RE DELETE_RE LEAD_REPIN_NO_STATUS
set -u
umask 077

# ---------------------------------------------------------------- work folder
SELF=$0
WORK=$(mktemp -d "${TMPDIR:-/tmp}/lead-repin.XXXXXX") || { echo "cannot make the private work folder with mktemp" >&2; exit 2; }
MASKSED=$WORK/mask.sed        # full filter: line rules AND multi-line rules (used on every search result)
MASKLINE=$WORK/mask-line.sed  # line rules only (the final belt over the whole output: it can never hide a following line)
OUT=$WORK/lead-repin-verify-out.txt
NL=$(printf '\n_'); NL=${NL%_}
CLEAN=0
cleanup() {
  [ "$CLEAN" = 1 ] || return 0
  case $WORK in */lead-repin.??????) [ -d "$WORK" ] && rm -rf "$WORK" ;; esac
  return 0
}
trap cleanup EXIT

# ---------------------------------------------------------------- masking filter (the ONE choke point)
# Names that look secret are matched as whole WORDS of an identifier (words are split at _ . - and
# spaces), so  key_file  token  api_key  X-Api-Key  accessToken  PASS  pat  are secret names, but
# author  desk  task  risk  tokenizer  max_tokens  bypass  are not. Words that END in key, token,
# secret, password, passwd, pwd or credential(s) also count (apiKey, accessToken, monkey: it errs
# on the side of hiding).
# Rules (extended regular expressions, case-insensitive):
#  L1 YAML name alone on a line, value on the next line(s): hide the next line and indented lines after it
#     (also inside grep output, which prefixes "12-"). Only when the name stands at the START of the line
#     (so  if token:  and  author:  are not hidden).                                    [full filter only]
#  L2 text between triple quotes after  name =  : same line, or all lines up to the closing quotes. [full only]
#  1  JSON / dict:  "name": value  and  'name': value  and  {name: value}.
#  2  JSON pair  {"name": "X_TOKEN", "value": "..."}: the value is hidden.
#  3  web address with user:password@ .
#  4  Bearer and Basic header values, JWT-shaped values.
#  5  well-known value shapes (with a word edge, so desk- task- risk- mask- compat- are not hit):
#     sk- pk- rk- pat- ghp_ gho_ ghs_ ghu_ github_pat_ xox*- AKIA/ASIA ids
#     (the one example AKIAIOSFODNN7EXAMPLE is allowed to show).
#  6  name = value (also  os.environ["X_TOKEN"] = "v"  and  self.token = v): quoted value hidden alone,
#     unterminated quote and unquoted value hide the rest of the line.  name: value only when the name
#     starts the line (YAML / header form).  A comparison such as  key == "end"  is NOT hidden.
#  7  name followed by a comma and a quoted value:  ("API_KEY", "v")  and  .get("API_KEY", "default").
#  8  command-line flags:  --token abc  --password abc  --api-key=abc .
#  9  e-mail addresses are replaced by <email-masked>.
write_mask_sed() {
  W='(key|token|secrets?|passw(or)?d|passphrase|pass|pwd|pw|psw|pswd|pat|credentials?|authorization|auth|bearer|private)'
  SUF='(key|token|secret|passw(or)?d|pwd|credentials?)'
  # IDB: an identifier that contains a secret word; IDQ: the same inside quotes (spaces count as separators)
  IDB="((([A-Za-z0-9_.-]*[_.-])?$W)|([A-Za-z0-9_.-]*$SUF))([_.-][A-Za-z0-9_.-]*)?"
  IDQ="((([A-Za-z0-9_. -]*[_. -])?$W)|([A-Za-z0-9_. -]*$SUF))([_. -][A-Za-z0-9_. -]*)?"
  ID="(^|[^A-Za-z0-9])$IDB"          # IDB with a left edge (the edge character is part of the match)
  PRE="[\"']?[]]?[[:space:]]*="       # what may stand between the name and  =   ( name"]  = )
  YPRE='^([0-9]+[-:])?[[:space:]]*(- +)?["'"'"']?'  # start of a line: optional grep prefix, indent, list dash, quote
  {
    cat <<EOF
:top
/${YPRE}${IDB}["']?[[:space:]]*:[[:space:]]*([|>][-+]?)?[[:space:]]*\$/I{
n
/^([0-9]+[-:])?[[:space:]]+[^[:space:]]|^([0-9]+[-:])?- /{
s/^([0-9]+[-:])?.*/\1<masked>/
:ya
n
/^([0-9]+[-:])?[[:space:]]+[^[:space:]]|^([0-9]+[-:])?- /{
s/^([0-9]+[-:])?.*/\1<masked>/
bya
}
b top
}
/^([0-9]+[-:])?[[:space:]]*(- +)?["']?[A-Za-z0-9_.-]+["']?[[:space:]]*:|^--\$/b top
s/^([0-9]+[-:])?.*/\1<masked>/
}
/(${ID})${PRE}[[:space:]]*"""/I{
/(${ID})${PRE}[[:space:]]*""".*"""/I!{
s/((${ID})${PRE}[[:space:]]*""").*/\1<masked>/I
:t1
n
/"""/!{
s/^([0-9]+[-:])?.*/\1<masked>/
bt1
}
s/^(([0-9]+[-:])?)([^"]|"[^"]|""[^"])*"""/\1<masked>"""/
b
}
}
/(${ID})${PRE}[[:space:]]*'''/I{
/(${ID})${PRE}[[:space:]]*'''.*'''/I!{
s/((${ID})${PRE}[[:space:]]*''').*/\1<masked>/I
:t2
n
/'''/!{
s/^([0-9]+[-:])?.*/\1<masked>/
bt2
}
s/^(([0-9]+[-:])?)([^']|'[^']|''[^'])*'''/\1<masked>'''/
b
}
}
EOF
    line_rules
  } > "$MASKSED"
  line_rules > "$MASKLINE"
}
line_rules() {
  cat <<EOF
s/((${ID})${PRE}[[:space:]]*""")([^"]|"[^"]|""[^"])*"""/\1<masked>"""/Ig
s/((${ID})${PRE}[[:space:]]*''')([^']|'[^']|''[^'])*'''/\1<masked>'''/Ig
/(${ID})${PRE}[[:space:]]*""".*"""/I!s/((${ID})${PRE}[[:space:]]*""").*/\1<masked>/I
/(${ID})${PRE}[[:space:]]*'''.*'''/I!s/((${ID})${PRE}[[:space:]]*''').*/\1<masked>/I
s/(["'](${IDQ})["'][[:space:]]*:[[:space:]]*)("[^"]*"|'[^']*'|[^,}[:space:]]+)/\1"<masked>"/Ig
s/(["'](name|key|var|variable|env)["'][[:space:]]*:[[:space:]]*["'](${IDQ})["'][[:space:]]*,[[:space:]]*["'][A-Za-z_]*["'][[:space:]]*:[[:space:]]*)("[^"]*"|'[^']*'|[^,}[:space:]]+)/\1"<masked>"/Ig
s/([{,][[:space:]]*(${IDB})[[:space:]]*:[[:space:]]*)("[^"]*"|'[^']*'|[^,}[:space:]]+)/\1<masked>/Ig
s#(://[^:/@[:space:]]+:)[^@[:space:]]+@#\1<masked>@#g
s#(Bearer)[[:space:]]+[A-Za-z0-9._~+/=-]{6,}#\1 <masked>#Ig
s#(Basic)[[:space:]]+[A-Za-z0-9+/=]{16,}#\1 <masked>#Ig
s/eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_.-]+/<masked>/g
s/(^|[^A-Za-z0-9_])(sk|pk|rk|pat)-[A-Za-z0-9_-]{8,}/\1<masked>/g
s/(^|[^A-Za-z0-9_])(ghp|gho|ghs|ghu)_[A-Za-z0-9]{10,}/\1<masked>/g
s/(^|[^A-Za-z0-9_])github_pat_[A-Za-z0-9_]{10,}/\1<masked>/g
s/(^|[^A-Za-z0-9_])xox[abprs]-[A-Za-z0-9-]{8,}/\1<masked>/g
s/AKIAIOSFODNN7EXAMPLE/<<EXAMPLE-KEY>>/g
s/(AKIA|ASIA)[0-9A-Z]{16}/<masked>/g
s/<<EXAMPLE-KEY>>/AKIAIOSFODNN7EXAMPLE/g
s/((${ID})${PRE}[[:space:]]*)("[^"]*"|'[^']*')/\1<masked>/Ig
s/((${ID})${PRE}[[:space:]]*)["'].*/\1<masked>/I
s/((${ID})${PRE}[[:space:]]*)[^=[:space:]<"'].*/\1<masked>/I
s/(${YPRE}${IDB}["']?[[:space:]]*:[[:space:]]*)("[^"]*"|'[^']*')/\1<masked>/I
s/(${YPRE}${IDB}["']?[[:space:]]*:[[:space:]]*)["'].*/\1<masked>/I
s/(${YPRE}${IDB}["']?[[:space:]]*:[[:space:]]*)[^[:space:]<"'|>].*/\1<masked>/I
s/((${ID})["']?[[:space:]]*,[[:space:]]*)("[^"]*"|'[^']*')/\1<masked>/Ig
s/((^|[[:space:]])--?([A-Za-z0-9]+[_-])*(key|token|secret|passw(or)?d|passphrase|pass|pwd|pw|psw|pswd|pat|credentials?|auth|bearer)([_-][A-Za-z0-9_-]*)?([[:space:]]+|=))("[^"]*"|'[^']*'|[^[:space:]<-][^[:space:]]*)/\1<masked>/Ig
s/[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+\.)+[A-Za-z]{2,}/<email-masked>/g
EOF
}

# the rule files must exist, be non-empty and be accepted by this sed; otherwise nothing may print
filter_ready() {
  [ -s "$MASKSED" ] && [ -s "$MASKLINE" ] || return 1
  [ "$(printf 'AbC key=zz\n' | sed -E -f "$MASKSED" 2>/dev/null)" = "AbC key=<masked>" ] || return 1
  [ "$(printf 'AbC key=zz\n' | sed -E -f "$MASKLINE" 2>/dev/null)" = "AbC key=<masked>" ] || return 1
  [ "$(printf 'AbC\n' | sed -E 's/abc/X/I' 2>/dev/null)" = "X" ] || return 1
  return 0
}

# mask: hide secrets FIRST (on the whole line), then cut long lines and SAY that the line was cut.
mask() {
  sed -E -f "$MASKSED" | awk '{ if (length($0) > 240) print substr($0, 1, 240) " ...[CUT: this line has " length($0) " characters; the rest is not shown]"; else print }'
}
mask_line() { sed -E -f "$MASKLINE"; }

# ---------------------------------------------------------------- self-test (also the canary that runs first in every run)
# self_test QUIET   (QUIET=1: print only FAIL lines and the tally)
self_test() {
  st_quiet=${1:-0}
  p1=Zq9x; p2=W4kL; p3=7pR2; p4=mN5v
  base=$p1$p2$p3$p4
  a1=AK; a2=IA; fakeid=${a1}${a2}ABCD1234EFGH5678
  gh1=gh; gh2=p_
  em1=jane; em2=.roe; em3=@example; em4=.test; fakemail=$em1$em2$em3$em4
  in=$WORK/st-in.txt; res=$WORK/st-out.txt; res2=$WORK/st-out2.txt
  long=$(awk 'BEGIN{for(i=0;i<300;i++) printf "x"}')
  q3='"""'
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
    printf '%s token=%s_17_\n' "$long" "$base"
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
  } > "$in"
  if [ -n "${SELFTEST_FILTER:-}" ]; then
    # shellcheck disable=SC2086
    $SELFTEST_FILTER < "$in" > "$res"; cp "$res" "$res2"
  else
    mask < "$in" > "$res"; mask_line < "$in" > "$res2"
  fi
  pass=0; fail=0
  say() { [ "$st_quiet" = 1 ] || printf '%s\n' "$1"; }
  chk_hidden() { # label, fragment, L = also tested against the line-only filter
    if grep -q -F -- "$2" "$res"; then fail=$((fail + 1)); printf 'FAIL (secret still visible): %s\n' "$1"
    else pass=$((pass + 1)); say "PASS (hidden): $1"; fi
    if [ "${3:-}" = L ]; then
      if grep -q -F -- "$2" "$res2"; then fail=$((fail + 1)); printf 'FAIL (secret still visible in the line-only final filter): %s\n' "$1"
      else pass=$((pass + 1)); say "PASS (hidden, line-only final filter): $1"; fi
    fi
  }
  chk_kept() { # label, fragment
    if grep -q -F -- "$2" "$res"; then pass=$((pass + 1)); say "PASS (kept): $1"
    else fail=$((fail + 1)); printf 'FAIL (evidence was hidden): %s\n' "$1"; fi
  }
  chk_hidden 'KEY= form' "${base}_1_" L
  chk_hidden 'export TOKEN= form' "${base}_2_" L
  chk_hidden 'password = "..." form' "${base}_3_" L
  chk_hidden 'JSON quoted key' "${base}_4_" L
  chk_hidden 'JSON client_secret no spaces' "${base}_5_" L
  chk_hidden 'Authorization Bearer' "${base}_6_" L
  chk_hidden 'bare Bearer value' "${base}_7_" L
  chk_hidden 'sk- value' "${base}_8_" L
  chk_hidden 'pat- value' "${base}_9_" L
  chk_hidden 'github token shape' "${base}_10_" L
  chk_hidden 'YAML next line after grep prefix' "${base}_11_"
  chk_hidden 'YAML block line a' "${base}_12a_"
  chk_hidden 'YAML block line b' "${base}_12b_"
  chk_hidden 'web address with user:password' "${base}_13_" L
  chk_hidden 'AKIA-shaped id' "$fakeid" L
  chk_hidden 'passwd: form' "${base}_14_" L
  chk_hidden 'pwd= form' "${base}_15_" L
  chk_hidden 'credential = form' "${base}_16_" L
  chk_hidden 'secret at column 300 (hidden before the cut)' "${base}_17_" L
  chk_hidden 'JSON secret followed by more JSON' "${base}_18_" L
  chk_hidden 'quoted secret inside a call' "${base}_19_" L
  chk_hidden 'bare PASS= name' "${base}_20_" L
  chk_hidden 'passphrase: name' "${base}_21_" L
  chk_hidden 'pat = name (personal access token)' "${base}_22_" L
  chk_hidden 'os.environ["X_TOKEN"] = "v"' "${base}_23_" L
  chk_hidden '.get("API_KEY", "default")' "${base}_24_" L
  chk_hidden '("API_KEY", "value") tuple' "${base}_25_" L
  chk_hidden '--token value flag' "${base}_26_" L
  chk_hidden '--password value flag' "${base}_27_" L
  chk_hidden '--api-key=value flag' "${base}_28_" L
  chk_hidden 'triple-quoted value on one line' "${base}_29_" L
  chk_hidden 'triple-quoted value over several lines, line 1' "${base}_30a_"
  chk_hidden 'triple-quoted value over several lines, line 2' "${base}_30b_"
  chk_hidden 'unterminated quote' "${base}_31_" L
  chk_hidden 'e-mail address' "$em1$em2" L
  chk_hidden 'JSON name/value pair' "${base}_33_" L
  chk_hidden "single-quoted dict key 'api_key'" "${base}_34_" L
  chk_hidden 'self.token = value' "${base}_35_" L
  chk_hidden 'accessToken: value (camel case)' "${base}_36_" L
  chk_hidden 'apiKey = value (camel case)' "${base}_37_" L
  chk_hidden 'X-Api-Key: header' "${base}_38_" L
  chk_hidden 'JS object {token: value}' "${base}_39_" L
  chk_hidden 'export X_PASSWORD=' "${base}_40_" L
  chk_hidden 'pw name, triple-quoted over several lines, line 1' "${base}_42_"
  chk_hidden 'pw name, triple-quoted over several lines, line 2' "${base}_43_"
  chk_hidden 'pswd: name' "${base}_44_" L
  chk_kept 'text after a multi-line value closes' '# tail42' 
  chk_hidden "single triple quotes over several lines, line 1" "${base}_41a_"
  chk_hidden "single triple quotes over several lines, line 2" "${base}_41b_"
  chk_kept 'text after a quoted JSON secret stays readable (DELETE)' '"method": "DELETE"'
  chk_kept 'text after a quoted secret in a call stays readable' '# delete path'
  chk_kept 'comparison key == "end" is not hidden' 'if key == "end":'
  chk_kept 'plain answer = "end" is not hidden' 'answer = "end"'
  chk_kept 'the one allowed example key shows' 'AKIAIOSFODNN7EXAMPLE'
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
  st_leak=0
  grep -q -F -- "$base" "$res" && st_leak=1
  rm -f "$in" "$res" "$res2"
  printf 'SELF-TEST: passed=%s failed=%s (the made-up input and output files were deleted)\n' "$pass" "$fail"
  [ "$fail" -eq 0 ] && [ "$st_leak" -eq 0 ]
}

write_mask_sed
case ${1:-} in
  --mask)
    CLEAN=1
    filter_ready || { echo "masking filter is not usable here (needs GNU sed or a sed that knows s///I): refusing to print" >&2; exit 3; }
    mask; exit $? ;;
  --self-test)
    CLEAN=1
    if [ -z "${SELFTEST_FILTER:-}" ]; then filter_ready || { echo "masking filter is not usable here (needs GNU sed or a sed that knows s///I)" >&2; exit 3; }; fi
    self_test 0; exit $? ;;
esac

# ---------------------------------------------------------------- canary: the masking filter must work BEFORE any take file is opened
if ! filter_ready; then
  CLEAN=1
  echo "STOP: the masking filter is not usable here (the rule file is empty or this sed does not know s///I, which GNU sed does). Nothing was read." >&2
  exit 3
fi
CANARY=$(self_test 1); canary_rc=$?
if [ "$canary_rc" -ne 0 ]; then
  CLEAN=1
  printf 'STOP: the masking self-test (canary) FAILED, so the filter cannot be trusted and no take file was opened:\n%s\n' "$CANARY" >&2
  exit 3
fi

# ---------------------------------------------------------------- settings
TAKE_DIR=${1:-$PWD}
if [ ! -d "$TAKE_DIR" ]; then echo "take folder not found: $TAKE_DIR" >&2; CLEAN=1; exit 2; fi
TAKE_DIR=$(cd "$TAKE_DIR" && pwd -P)
FLOWS_DIR=${FLOWS_DIR:-$TAKE_DIR}
MODEL_DIR=${MODEL_DIR:-}
MODEL_SETTINGS=${MODEL_SETTINGS:-}
ONE_STORE=${ONE_STORE:-}
LEAD_REPIN_NO_STATUS=${LEAD_REPIN_NO_STATUS:-}

END_RE=${END_RE:-"[\"']end[\"']|(^|[^A-Za-z_])END[A-Z_]*[[:space:]]*=|[=!]=[[:space:]]*end([^A-Za-z_]|\$)"}
MODEL_RE=${MODEL_RE:-'anthropic|messages\.create|/v1/messages|model_program|call_model|post_model|post_lead|llm|complete\(|burst|/qualify|/control|n8n_drive|urlopen|requests\.(get|post)|httpx|subprocess|Popen|webhook|127\.0\.0\.1|localhost'}
DELETE_RE=${DELETE_RE:-'(^|[^A-Za-z_])DELETE([^A-Za-z_]|$)|\.delete\(|requests\.delete|archive|purge|remove|trash|gdpr|cleanup|clean_up|unlink|rmtree|method[[:space:]]*=[[:space:]]*["'"'"'](DELETE|PATCH)'}
GI=-i   # grep case flag; set to empty for a case-sensitive search

# ---------------------------------------------------------------- file lists and path finding
PRUNE='-name .git -o -name node_modules -o -name _local -o -name secrets -o -name .venv -o -name venv -o -name __pycache__'
make_list() { # make_list OUTFILE ROOT KIND   KIND: code | json | py | pyall | named:NAME
  ml_out=$1; ml_root=$2; ml_kind=$3
  ( cd "$ml_root" || exit 1
    case $ml_kind in
      code) find . -maxdepth 4 -type d \( $PRUNE -o -name tests -o -name test \) -prune -o -type f \( -name '*.py' -o -name '*.sh' \) ! -name 'test_*' ! -name '*_test.py' ! -name 'conftest.py' ! -name "*${NL}*" -print ;;
      py)   find . -maxdepth 4 -type d \( $PRUNE -o -name tests -o -name test \) -prune -o -type f -name '*.py' ! -name 'test_*' ! -name '*_test.py' ! -name 'conftest.py' ! -name "*${NL}*" -print ;;
      pyall) find . -maxdepth 4 -type d \( $PRUNE \) -prune -o -type f -name '*.py' ! -name "*${NL}*" -print ;;
      json) find . -maxdepth 4 -type d \( $PRUNE \) -prune -o -type f -name '*.json' ! -name "*${NL}*" -print ;;
      named:*) find . -maxdepth 4 -type d \( $PRUNE \) -prune -o -type f -name "${ml_kind#named:}" ! -name "*${NL}*" -print ;;
    esac ) 2>/dev/null | sort | RT=$ml_root awk '{ sub(/^\.\//, ""); print ENVIRON["RT"] "/" $0 }' > "$ml_out"
}
# skip_report ROOT LABEL KIND(code|json): print the count of EVERY category of file the lists leave out,
# so a silent drop cannot hide (a "0 matching lines" can then be told apart from "never looked").
skip_report() {
  sr_root=$1; sr_label=$2; sr_kind=$3
  [ -d "$sr_root" ] || { printf 'left out of "%s": folder %s not found\n' "$sr_label" "$sr_root"; return; }
  ( cd "$sr_root" || exit 0
    if [ "$sr_kind" = json ]; then NM='-name *.json'; else NM='-name *.py -o -name *.sh'; fi
    set -f
    printf 'left out of "%s" (%s) and NOT searched, file counts by reason:\n' "$sr_label" "$sr_root"
    sr_n=$(find . -mindepth 5 -type f \( $NM \) -print 2>/dev/null | wc -l | tr -d ' ')
    printf '  deeper than 4 folders below the folder (anywhere): %s\n' "$sr_n"
    sr_n=$(find . -type l -print 2>/dev/null | wc -l | tr -d ' ')
    printf '  symbolic links of any kind (find does not follow them): %s\n' "$sr_n"
    sr_n=$(find . 2>&1 >/dev/null | grep -c -i 'permission denied')
    printf '  folders or files the find command could not open (permission denied): %s\n' "$sr_n"
    sr_n=$(find . -name "*${NL}*" -print0 2>/dev/null | tr -cd '\000' | wc -c | tr -d ' ')
    printf '  names with a line break (cannot be listed safely): %s\n' "$sr_n"
    for sr_d in node_modules _local secrets .venv venv __pycache__ tests test; do
      if [ "$sr_kind" = json ] && { [ "$sr_d" = tests ] || [ "$sr_d" = test ]; }; then continue; fi
      sr_n=$(find . -path "*/$sr_d/*" -type f \( $NM \) -print 2>/dev/null | wc -l | tr -d ' ')
      printf '  inside folders named %s: %s\n' "$sr_d" "$sr_n"
    done
    if [ "$sr_kind" != json ]; then
      sr_n=$(find . -type f \( -name 'test_*' -o -name '*_test.py' -o -name conftest.py \) -not -path '*/tests/*' -not -path '*/test/*' -not -path '*/node_modules/*' -not -path '*/_local/*' -not -path '*/secrets/*' -not -path '*/.venv/*' -not -path '*/venv/*' -print 2>/dev/null | wc -l | tr -d ' ')
      printf '  test files outside tests folders (test_*, *_test.py, conftest.py): %s\n' "$sr_n"
    fi
  )
}
# local_flow_report: flows under _local are NOT searched line by line and NEVER printed (a literal-substituted copy may hold real
# values in plain JSON fields); only the counts are shown (AGENT-SCOPE line 23, BL-wp6-G1: the real take needs such a local copy).
local_flow_report() {
  lf_root=$1
  [ -d "$lf_root" ] || return 0
  lf_files=$(cd "$lf_root" && find . -path '*/_local/*' -type f -name '*.json' -print 2>/dev/null | wc -l | tr -d ' ')
  lf_hits=0
  if [ "$lf_files" -gt 0 ]; then
    lf_hits=$( (cd "$lf_root" && find . -path '*/_local/*' -type f -name '*.json' -print 2>/dev/null | while IFS= read -r lf_f; do grep -c -E -i -e "$DELETE_RE" -- "$lf_f" 2>/dev/null; done) | awk '{s+=$1} END{print s+0}')
  fi
  printf '_local flow json files: %s, delete-word matching lines inside them: %s (these lines are NOT printed because a local copy may hold real values; open them yourself)\n' "$lf_files" "$lf_hits"
}

PATHNOTES=
resolve() { # resolve VARNAME FILENAME
  eval "rv_cur=\${$1:-}"
  if [ -n "$rv_cur" ]; then PATHNOTES="$PATHNOTES$1 = $rv_cur  (from the environment)
"; return; fi
  make_list "$WORK/named.$2.txt" "$TAKE_DIR" "named:$2"
  rv_n=$(wc -l < "$WORK/named.$2.txt" | tr -d ' ')
  if [ "${rv_n:-0}" -eq 0 ]; then
    eval "$1=\"\$TAKE_DIR/$2\""
    PATHNOTES="$PATHNOTES$1 = NOT FOUND by name '$2' below $TAKE_DIR (set $1 to the real path)
"
    return
  fi
  rv_pick=$(grep '/scripts/' "$WORK/named.$2.txt" | head -1)
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
[ -n "$ONE_STORE" ] || { make_list "$WORK/named.one.txt" "$TAKE_DIR" "named:DECISION-one-store.md"; ONE_STORE=$(head -1 "$WORK/named.one.txt"); [ -n "$ONE_STORE" ] || ONE_STORE=$TAKE_DIR/DECISION-one-store.md; }

make_list "$WORK/list-code.txt" "$TAKE_DIR" code
make_list "$WORK/list-flows.txt" "$FLOWS_DIR" json
make_list "$WORK/list-test-all.txt" "$TAKE_DIR" pyall
if [ -n "$MODEL_DIR" ] && [ -d "$MODEL_DIR" ]; then
  make_list "$WORK/list-model.txt" "$MODEL_DIR" py
  make_list "$WORK/list-model-all.txt" "$MODEL_DIR" pyall
else : > "$WORK/list-model.txt"; : > "$WORK/list-model-all.txt"; fi
# the four resolved files are always searched first; the general list then leaves them out (no double counting)
: > "$WORK/four.txt"
for f4 in "$TAKE_PY" "$CRM_PY" "$DRIVE_PY" "$N8N_PY"; do [ -f "$f4" ] && printf '%s\n' "$f4" >> "$WORK/four.txt"; done
grep -v -F -x -f "$WORK/four.txt" "$WORK/list-code.txt" > "$WORK/list-code-rest.txt" 2>/dev/null
[ -s "$WORK/four.txt" ] || cp "$WORK/list-code.txt" "$WORK/list-code-rest.txt"

# ---------------------------------------------------------------- counters and search helpers
blocks=0; search_blocks=0; with_hits=0; zero_hits=0; info_blocks=0; files_missing=0; files_unreadable=0
bh=0; bf=0; bm=0; bu=0; bkind=search
S_HITS=0; S_FILES=0; S_MISS=0; S_UNR=0; LAST_HITS=0
HIDDEN_VALUES=0; HIDDEN_LINES=0

begin() { # id, title, question
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
search_begin() { S_HITS=0; S_FILES=0; S_MISS=0; S_UNR=0; S_LISTED=0; printf -- '--- search: %s\n' "$1"; S_LABEL=$1; }
search_end() {
  printf '    [search "%s": matching lines=%s in %s file(s) with a match, files_read=%s missing=%s unreadable=%s]' "$S_LABEL" "$S_HITS" "$S_LISTED" "$S_FILES" "$S_MISS" "$S_UNR"
  if [ "$S_FILES" -eq 0 ]; then printf ' ZERO FILES SEARCHED: nothing was looked at'
  elif [ "$S_HITS" -eq 0 ]; then printf ' ZERO HITS: either not there or the search words are wrong; this is not proof of absence'; fi
  if [ "$S_UNR" -gt 0 ]; then printf ' (%s file(s) UNREADABLE: this count is NOT complete)' "$S_UNR"; fi
  printf '\n'
  bh=$((bh + S_HITS)); bf=$((bf + S_FILES)); bm=$((bm + S_MISS)); bu=$((bu + S_UNR))
  files_missing=$((files_missing + S_MISS)); files_unreadable=$((files_unreadable + S_UNR))
  LAST_HITS=$S_HITS
}
search_one() { # search_one PATTERN CONTEXT FILE      (files with no match are counted, not listed)
  so_pat=$1; so_ctx=$2; so_f=$3
  if [ -z "$so_f" ] || [ ! -e "$so_f" ]; then S_MISS=$((S_MISS + 1)); printf 'FILE MISSING (adjust the path): %s\n' "$so_f"; return; fi
  if [ ! -f "$so_f" ] || [ ! -r "$so_f" ]; then S_UNR=$((S_UNR + 1)); printf 'UNREADABLE (not searched, NOT zero matches): %s\n' "$so_f"; return; fi
  so_c=$(grep -c -E $GI -e "$so_pat" -- "$so_f" 2>"$WORK/grep.err"); so_rc=$?
  if [ "$so_rc" -ge 2 ]; then S_UNR=$((S_UNR + 1)); printf 'UNREADABLE (grep failed: %s; not searched, NOT zero matches): %s\n' "$(head -1 "$WORK/grep.err" | cut -c1-120)" "$so_f"; return; fi
  so_c=${so_c:-0}
  S_FILES=$((S_FILES + 1)); S_HITS=$((S_HITS + so_c))
  if [ "$so_c" -gt 0 ]; then
    S_LISTED=$((S_LISTED + 1))
    printf '%s: %s match line(s)\n' "$so_f" "$so_c"
    # the grep output goes STRAIGHT into the masking filter: no unmasked copy is ever written to disk
    grep -n -E $GI -A "$so_ctx" -e "$so_pat" -- "$so_f" 2>/dev/null | mask > "$WORK/m.txt"
    cat "$WORK/m.txt"
    so_m=$(grep -c '<masked>\|<email-masked>' "$WORK/m.txt"); so_m=${so_m:-0}
    so_w=$(grep -c -E '^([0-9]+[-:])?<masked>$' "$WORK/m.txt"); so_w=${so_w:-0}
    HIDDEN_VALUES=$((HIDDEN_VALUES + so_m)); HIDDEN_LINES=$((HIDDEN_LINES + so_w))
    [ "$so_m" -gt 0 ] && printf '    (a value was hidden on %s line(s) above; %s of them were hidden whole)\n' "$so_m" "$so_w"
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
    sed -n "${a},${b}p" "$f" | awk -v s="$a" '{ printf "%d:%s\n", NR + s - 1, $0 }' | mask
  fi
}
list_info() { # list_info LABEL LISTFILE
  li_n=$(wc -l < "$2" | tr -d ' ')
  printf 'files searched for "%s": %s' "$1" "${li_n:-0}"
  if [ "${li_n:-0}" -eq 0 ]; then printf '   <<< 0 FILES SEARCHED: the searches below looked at nothing; check TAKE_DIR / FLOWS_DIR / MODEL_DIR'; fi
  printf '\n'
}
g() { git --no-optional-locks -c core.fsmonitor=false -C "$TAKE_DIR" "$@"; }
model_notice() {
  if [ -z "$MODEL_DIR" ] || [ ! -d "$MODEL_DIR" ]; then
    printf '*** MODEL_DIR is not set (or not a folder): the MODEL PROGRAM IS NOT SEARCHED. This is "not looked at", not "absent". %s cannot be answered by this run: set MODEL_DIR and run again.\n' "$1"
  fi
}

# ---------------------------------------------------------------- the checklist
main() {
  printf 'lead-repin-verify.sh v3  (reads only; prints, never judges; the lead reads this output before sharing it)\n'
  printf 'masking self-test (canary) before any file was opened: %s\n' "$CANARY"
  printf 'take folder: %s\n' "$TAKE_DIR"
  printf 'private work folder (made by mktemp; it stays after this run; delete it yourself): %s\n' "$WORK"
  printf 'copy of this output (masked): %s\n' "$OUT"
  printf 'Nothing below was checked against a real take program by the builder of this script.\n'
  printf 'Q27 a, b and c stay UNVERIFIED until the lead shows them at the final head; this script only finds text.\n'
  printf 'Files used:\n%s' "$PATHNOTES"
  for f4 in "$TAKE_PY" "$CRM_PY" "$DRIVE_PY" "$N8N_PY"; do
    case $f4 in "$TAKE_DIR"/*) ;; *) printf 'NOTE: %s is OUTSIDE the take folder (it is still searched, because it is one of the four named files).\n' "$f4" ;; esac
  done
  printf 'FLOWS_DIR = %s\nMODEL_DIR = %s\n' "$FLOWS_DIR" "${MODEL_DIR:-<not set: the model program folder is NOT SEARCHED>}"
  printf 'Left out on purpose (counts are printed in block Q23-1): folders .git node_modules _local secrets .venv venv __pycache__ tests test; files test_*, *_test.py, conftest.py (only below the take folder, so a take folder under a test_ parent is still searched); anything deeper than 4 folders; symbolic links.\n'
  list_info "python and shell files of the take (the four named files are searched first and left out of this list)" "$WORK/list-code-rest.txt"
  list_info "flow json files" "$WORK/list-flows.txt"
  list_info "model program python files (tests left out)" "$WORK/list-model.txt"
  model_notice "Q27 a (model side), Q27 b (model side and qs_37 on the model side) and Q27 c (half B)"

  begin R00 "Final head identity (G1, G26)" "Which commit id and which file checksums are these answers about?"
  if command -v git >/dev/null 2>&1 && g rev-parse --git-dir >/dev/null 2>&1; then
    printf 'git work tree top folder: %s (if this is a PARENT of the take folder, the commit id below is the parent repository'"'"'s)\n' "$(g rev-parse --show-toplevel 2>&1)"
    printf 'HEAD: %s\n' "$(g rev-parse HEAD 2>&1)"
    if [ -n "$LEAD_REPIN_NO_STATUS" ]; then printf 'changed or untracked files (count): NOT READ (LEAD_REPIN_NO_STATUS is set)\n'
    else printf 'changed or untracked files (count): %s\n' "$(g status --porcelain 2>&1 | wc -l | tr -d ' ')"; fi
    g log -1 --format='last commit: %h %ci' 2>&1
  else
    printf 'not a git work tree (or git missing): cannot print a commit id here\n'
  fi
  for f in "$TAKE_PY" "$CRM_PY" "$DRIVE_PY" "$N8N_PY"; do
    if [ -f "$f" ]; then
      bf=$((bf + 1))
      if command -v sha256sum >/dev/null 2>&1; then sha256sum "$f" 2>&1; else shasum -a 256 "$f" 2>&1; fi
    else bm=$((bm + 1)); files_missing=$((files_missing + 1)); printf 'FILE MISSING (adjust the path): %s\n' "$f"; fi
  done
  finish_info R00

  begin Q23-1 "Any delete or archive path to the CRM (Q23, G1)" "Does any python or shell file of the take (not tests), the CRM module or any flow json contain a delete, archive, purge, remove or cleanup path to the CRM? Decision 2 (the take never deletes) stays; the r17 review found only a rows_with_prefix GET; two earlier reviews DISAGREE (see the document); this block is the final-head grep the lead shows."
  printf 'NOTE: the flow json files in the folder can differ from what n8n actually holds after import (G3); compare with the G2 checksum step.\n'
  printf 'NOTE: AGENT-SCOPE line 20 (citing review-codebase-1.md F-01) says the take archives its contacts with a DELETE call at run_real_check_n8n.py:1051 and crm_hubspot.py:504-509; the r17 review (ORDERS Q23) says there is no delete path. This script does not decide between them: block Q23-2 prints what stands at those lines today.\n'
  skip_report "$TAKE_DIR" "take folder, python and shell" code
  skip_report "$FLOWS_DIR" "flows folder, json" json
  local_flow_report "$FLOWS_DIR"
  S "delete words in the four named files (take program, CRM module, n8n_drive.py, n8n.py): always searched" "$DELETE_RE" 1 "$TAKE_PY" "$CRM_PY" "$DRIVE_PY" "$N8N_PY"
  SL "delete words in the other python and shell files of the take" "$DELETE_RE" 1 "$WORK/list-code-rest.txt"
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

  begin Q23-4 "Delete wording printed to the owner (G1, G17)" "Do the notice or the printed result still say deleted or archived, or print a delete count?"
  S "delete or archive wording in the take program" 'delet|archiv|purg' 0 "$TAKE_PY"
  finish Q23-4

  begin Q27a "Model call after the word end (Q27 a, G34): UNVERIFIED until the lead shows it" "After the take program reads the word end, can it still call the model? Part 1: lines with the end handling (and 20 lines after). Part 2: every model-call line."
  model_notice "Q27 a (model side)"
  GI=
  S "end handling in the take program (case-sensitive; includes constants; a hit may be help or usage text: read the line)" "$END_RE" 20 "$TAKE_PY"
  GI=-i
  ha=$LAST_HITS
  S "model-call words in the take program, n8n_drive.py and n8n.py" "$MODEL_RE" 0 "$TAKE_PY" "$DRIVE_PY" "$N8N_PY"
  hb=$LAST_HITS
  SL "model-call words in the model program folder (only if MODEL_DIR is set)" "$MODEL_RE" 0 "$WORK/list-model.txt"
  printf 'Q27a reading: end-handling lines=%s, model-call lines=%s. Zero in either means the words are probably wrong, NOT "no model call".\n' "$ha" "$hb"
  printf 'Reading a program cannot show (1) a call already sent before end or (2) an n8n retry or lease that fires a call after end: those need a run or a test shown at the final head. Line order is not always run order.\n'
  finish Q27a

  begin Q27b "End-date refusal (Q27 b, G16, G10): UNVERIFIED until the lead shows it" "Does a setting that refuses a call after the window end exist, and is a refusal SHOWN at the final head (a test run or a startup refusal)?"
  model_notice "Q27 b (model side)"
  printf 'SPEND WARNING: to SEE the refusal run ONLY the named qs_37 test, against the FAKE model. Never start the real model program or the real stage with a real key to "see" a refusal: that can make a paid call. This script starts nothing.\n'
  S "window end, need_seconds, refusal words in the take program" 'window|end_date|not_after|deadline|need_seconds|2026-11-2|refus' 0 "$TAKE_PY"
  SL "same words in the model program folder (only if MODEL_DIR is set)" 'window|end_date|not_after|deadline|2026-11-2|refus|after the' 0 "$WORK/list-model.txt"
  list_info "python files of the take, tests INCLUDED (for qs_37)" "$WORK/list-test-all.txt"
  list_info "python files of the model program folder, tests INCLUDED (for qs_37)" "$WORK/list-model-all.txt"
  if [ -n "$MODEL_DIR" ] && [ -d "$MODEL_DIR" ]; then skip_report "$MODEL_DIR" "model program folder, python and shell" code; fi
  SL "test name qs_37 in the take folder (tests included)" 'qs_37' 0 "$WORK/list-test-all.txt"
  SL "test name qs_37 in the model program folder (tests included; only if MODEL_DIR is set)" 'qs_37' 0 "$WORK/list-model-all.txt"
  if [ -n "$MODEL_SETTINGS" ] && [ -f "$MODEL_SETTINGS" ] && [ -r "$MODEL_SETTINGS" ]; then
    printf -- '--- search: settings lines whose NAME looks like a window end (the value is shown unless it looks secret; the window end is not secret)\n'
    bf=$((bf + 1)); grep -n -i -E '^[[:space:]]*(export[[:space:]]+)?[A-Za-z0-9_.]*(end|window|deadline|until)[A-Za-z0-9_.]*[[:space:]]*[=:]' "$MODEL_SETTINGS" 2>/dev/null | mask | head -20
  else printf 'MODEL_SETTINGS not set, missing or unreadable: settings NOT SEARCHED (adjust)\n'; fi
  printf 'NOTE: to SEE the refusal, run the named test (fake model only) or read the startup refusal at the final head; this script only finds text.\n'
  finish Q27b

  begin Q27c "Go marker before any model call (Q27 c, G33): UNVERIFIED until the lead shows it" "Does the model program refuse to make a paid call until the take program has written a marker after the accepted challenge? BOTH halves are needed."
  model_notice "Q27 c (half B)"
  S "half A: marker words in the take program" 'marker|go_file|ready_file|\.used|\.go([^A-Za-z]|$)|accepted|challenge' 0 "$TAKE_PY"
  hA=$LAST_HITS
  SL "half B: marker words in the model program folder (only if MODEL_DIR is set)" 'marker|go_file|ready_file|\.go([^A-Za-z]|$)|exists\(|isfile' 0 "$WORK/list-model.txt"
  hB=$LAST_HITS
  printf 'Q27c reading: take-program half hits=%s, model-program half hits=%s. Both halves must be shown; a zero in either half means NOT SHOWN by this search. The .used tag marker is not shown to be the go marker.\n' "$hA" "$hB"
  finish Q27c

  begin G35 "Prompts to the owner (G35)" "Does the take program ask the owner to type anything besides y, the challenge line and end?"
  S "input and prompt words in the take program" 'input\(|getpass|readline|stdin|isatty|worst.?case|figure' 0 "$TAKE_PY"
  finish G35

  begin G06 "Exit codes (G6, Q20.4)" "Which exit codes can the take program leave, and which one for person C unknown?"
  S "exit words in the take program" 'sys\.exit|[^a-z_]exit\(|SystemExit|EXIT_|return [0-3]$|unknown' 0 "$TAKE_PY"
  finish G06

  begin G04 "Call ceiling, price and ledger (G4, G14)" "Where are the call ceiling, retries, ledger total and program limit set?"
  S "ceiling words in the take program" 'ceiling|max_calls|retries|retry|ledger|backstop|program.?limit|180|189|price' 0 "$TAKE_PY"
  SL "ceiling words in the model program folder (only if MODEL_DIR is set)" 'ceiling|max_calls|retries|retry|ledger|backstop|limit|180|189|price' 0 "$WORK/list-model.txt"
  finish G04

  begin G18 "Stop, signal and lock behaviour (G18)" "What happens on a wrong line after end, Ctrl-C, a pause that ends without end, a cancelled key; which lock file is left?"
  S "signal and lock words in the take program" 'KeyboardInterrupt|SIGINT|SIGTERM|SIGHUP|\.lock|closing|interrupted|called off|timeout|give.?up' 0 "$TAKE_PY"
  finish G18

  begin G36 "Think time, silence and film cue (G36)" "Which printed line could start the film pause, and what are the minimum think time, silence and give-up values?"
  S "pause words in the take program" 'think|silence|give.?up|pause|film|sleep\(|print\(.*(start|wait)' 0 "$TAKE_PY"
  finish G36

  begin G37-38 "Per-run key file, demo mail subject, prep contact (G37, G38)" "How is the per-run key file made (does it refuse an existing file), what starts the take mail subjects, and does the prep contact address match the film search?"
  S "file-creation and subject words in the take program" 'set -C|noclobber|O_EXCL|key_file|subject|take-|prep-|label|demo' 0 "$TAKE_PY"
  finish G37-38

  begin G07 "Ports (G7)" "Which of the ports 5678, 5679, 5690-5693, 5701, 5702 are listening now, and does the take program name its own port?"
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
  S "port numbers in the take program" '5678|5679|569[0-3]|570[0-9]' 0 "$TAKE_PY"
  finish G07

  begin G20 "DECISION-one-store line 14 (G20)" "Does line 14 still say ONE database?"
  lines "$ONE_STORE" 14 14
  finish_info G20

  printf '\n'
  if [ -z "$MODEL_DIR" ] || [ ! -d "$MODEL_DIR" ]; then printf 'CANNOT BE ANSWERED WITHOUT MODEL_DIR: Q27 a model side, Q27 b model side and qs_37 model side, Q27 c half B (so Q27 c cannot be answered at all by this run).\n'; fi
  printf 'SUMMARY: blocks=%s search_blocks=%s with_hits=%s zero_hits=%s information_blocks=%s files_missing=%s files_unreadable=%s (counts only; nothing judged; the lead reads each block and the per-search ZERO lines)\n' \
    "$blocks" "$search_blocks" "$with_hits" "$zero_hits" "$info_blocks" "$files_missing" "$files_unreadable"
  printf 'Hidden by the masking filter in search results: %s line(s) had a value hidden, %s of them were hidden whole (next-line rule).\n' "$HIDDEN_VALUES" "$HIDDEN_LINES"
  printf 'Files left in the work folder (names and sizes; none holds an unmasked line of a searched file):\n'
  ls -l "$WORK" 2>&1 | sed 's/^/  /'
  printf 'Masking is a safety net: read this output yourself before you share it.\n'
}

main 2>&1 | mask_line | tee "$OUT"
exit 0
