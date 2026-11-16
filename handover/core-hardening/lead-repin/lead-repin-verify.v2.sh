#!/bin/sh
# lead-repin-verify.sh (version 2): checklist printer for the lead at re-pin.
#
# WHAT IT DOES TO YOUR MACHINE (exact):
#   - reads files: grep, sed, awk, wc, find, sha256sum, git rev-parse / log / status
#     (git runs with --no-optional-locks and the file-system monitor switched off, so it
#     does not refresh or rewrite the git index; it still reads the folder metadata);
#   - reads the list of listening ports (ss, or netstat if ss is missing);
#   - writes ONLY into one private work folder it makes with mktemp (permissions 700,
#     files 600, because umask is 077 below). The work folder holds the copy of this
#     output and a few small helper files. The script never deletes anything, not even
#     its own work folder (you may delete that folder yourself afterwards);
#   - makes NO network call and NO model call; it starts no other program of the take.
# It judges NOTHING: it prints what it found, with line numbers, for the lead to read.
# Values that look like secrets are hidden by a masking filter (see "mask"), but a
# filter is a safety net, not a guarantee: THE LEAD READS THE OUTPUT BEFORE SHARING IT.
#
# usage:
#   sh lead-repin-verify.sh [TAKE_DIR]        run the checklist (TAKE_DIR defaults to the current folder)
#   sh lead-repin-verify.sh --self-test       test the masking filter with made-up secrets, print PASS/FAIL
#   <command> | sh lead-repin-verify.sh --mask   pass any text through the same masking filter
#
# Every file name below is "adjust if different": set the variable in the environment.
# If TAKE_PY, CRM_PY, DRIVE_PY or N8N_PY is not set, the script looks for the file BY NAME
# (up to 4 folders deep below TAKE_DIR, preferring a scripts/ folder) and prints which one it used.
#   TAKE_PY CRM_PY DRIVE_PY N8N_PY FLOWS_DIR MODEL_DIR MODEL_SETTINGS ONE_STORE END_RE MODEL_RE DELETE_RE
set -u
umask 077

# ---------------------------------------------------------------- work folder
SELF=$0
WORK=$(mktemp -d "${TMPDIR:-/tmp}/lead-repin.XXXXXX") || { echo "cannot make the private work folder with mktemp" >&2; exit 2; }
MASKSED=$WORK/mask.sed
OUT=$WORK/lead-repin-verify-out.txt
NL=$(printf '\n_'); NL=${NL%_}

NAMES='key|token|secret|passw(or)?d|pwd|credential|auth|bearer|private'

# ---------------------------------------------------------------- masking filter
# Rules (extended regular expressions, case-insensitive on names):
#  1 YAML: a line whose name looks secret and has no value on it: the next line and the
#    indented lines after it are hidden (also inside grep output, which prefixes "12-").
#  2 JSON: "name": value  where the name contains key/token/secret/password/passwd/pwd/credential/auth/bearer/private.
#  3 web address with user:password@ .
#  4 Bearer and Basic header values, JWT-shaped values.
#  5 well-known value shapes: sk-, pk-, rk-, pat-, ghp_/gho_/ghs_/github_pat_, xox*-, AKIA/ASIA ids
#    (the one example AKIAIOSFODNN7EXAMPLE is allowed to show).
#  6 name = value or name: value (also export NAME=...): a quoted value is hidden alone (so the
#    rest of the line stays readable); an unquoted value hides the rest of the line.
#    A comparison such as  key == "end"  is NOT hidden, because "=" must be followed by something other than "=".
write_mask_sed() {
  sed "s/@NAMES@/$NAMES/g" > "$MASKSED" <<'EOF'
/(@NAMES@)[A-Za-z0-9_.-]*["']?[[:space:]]*:[[:space:]]*([|>][-+]?)?[[:space:]]*$/I{
n
s/^([0-9]+[-:])?.*/\1<masked>/
:a
n
/^([0-9]+[-:])?[[:space:]]+[^[:space:]]/{
s/^([0-9]+[-:])?.*/\1<masked>/
ba
}
}
s/("[A-Za-z0-9_. -]*(@NAMES@)[A-Za-z0-9_. -]*"[[:space:]]*:[[:space:]]*)("[^"]*"|[^,}[:space:]]+)/\1"<masked>"/Ig
s#(://[^:/@[:space:]]+:)[^@[:space:]]+@#\1<masked>@#g
s/(Bearer)[[:space:]]+[A-Za-z0-9._~+\/=-]{6,}/\1 <masked>/Ig
s/(Basic)[[:space:]]+[A-Za-z0-9+\/=]{16,}/\1 <masked>/Ig
s/eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_.-]+/<masked>/g
s/(sk|pk|rk|pat)-[A-Za-z0-9_-]{8,}/<masked>/g
s/(ghp|gho|ghs|ghu)_[A-Za-z0-9]{10,}/<masked>/g
s/github_pat_[A-Za-z0-9_]{10,}/<masked>/g
s/xox[abprs]-[A-Za-z0-9-]{8,}/<masked>/g
s/AKIAIOSFODNN7EXAMPLE/<<EXAMPLE-KEY>>/g
s/(AKIA|ASIA)[0-9A-Z]{16}/<masked>/g
s/<<EXAMPLE-KEY>>/AKIAIOSFODNN7EXAMPLE/g
s/((@NAMES@)[A-Za-z0-9_.-]*["']?[[:space:]]*[=:][[:space:]]*)("[^"]*"|'[^']*')/\1<masked>/Ig
s/((@NAMES@)[A-Za-z0-9_.-]*["']?[[:space:]]*[=:][[:space:]]*)[^=[:space:]<"'].*/\1<masked>/I
EOF
}

mask_only() { sed -E -f "$MASKSED"; }
# mask: hide secrets FIRST (on the whole line), then cut long lines and SAY that the line was cut.
mask() {
  sed -E -f "$MASKSED" | awk '{ if (length($0) > 240) print substr($0, 1, 240) " ...[CUT: this line has " length($0) " characters; the rest is not shown]"; else print }'
}

# ---------------------------------------------------------------- self-test
self_test() {
  p1=Zq9x; p2=W4kL; p3=7pR2; p4=mN5v
  base=$p1$p2$p3$p4
  a1=AK; a2=IA; fakeid=${a1}${a2}ABCD1234EFGH5678
  gh1=gh; gh2=p_
  in=$WORK/st-in.txt; res=$WORK/st-out.txt
  long=$(awk 'BEGIN{for(i=0;i<300;i++) printf "x"}')
  {
    printf 'API_KEY=%s1\n' "$base"
    printf 'export MY_TOKEN=%s2\n' "$base"
    printf 'password = "%s3"\n' "$base"
    printf '{"api_key": "%s4", "other": 1}\n' "$base"
    printf '{"client_secret":"%s5"}\n' "$base"
    printf 'Authorization: Bearer %s6\n' "$base"
    printf 'header Bearer %s7 end\n' "$base"
    printf 'value sk-%s8 here\n' "$base"
    printf 'value pat-%s9 here\n' "$base"
    printf 'value %s%s10Abcdef here\n' "$gh1$gh2" "$base"
    printf '11:db_password:\n'
    printf '12-    %s11\n' "$base"
    printf '13-other: fine\n'
    printf 'secret: |\n  %s12a\n  %s12b\nnext_line: stays\n' "$base" "$base"
    printf 'url https://user:%s13@host.example/path\n' "$base"
    printf 'id %s\n' "$fakeid"
    printf 'passwd: %s14\n' "$base"
    printf 'pwd=%s15\n' "$base"
    printf 'credential = %s16\n' "$base"
    printf '%s token=%s17\n' "$long" "$base"
    printf '{"api_key": "%s18", "nodes": [{"method": "DELETE"}]}\n' "$base"
    printf 'x = call(token="%s19") # delete path\n' "$base"
    printf 'if key == "end":\n'
    printf 'answer = "end"\n'
    printf 'literal AKIAIOSFODNN7EXAMPLE stays\n'
    printf 'plain line with the word end in it\n'
  } > "$in"
  mask < "$in" > "$res"
  pass=0; fail=0
  chk_hidden() { # label, fragment
    if grep -q -F -- "$2" "$res"; then fail=$((fail + 1)); printf 'FAIL (secret still visible): %s\n' "$1"
    else pass=$((pass + 1)); printf 'PASS (hidden): %s\n' "$1"; fi
  }
  chk_kept() { # label, fragment
    if grep -q -F -- "$2" "$res"; then pass=$((pass + 1)); printf 'PASS (kept): %s\n' "$1"
    else fail=$((fail + 1)); printf 'FAIL (evidence was hidden): %s\n' "$1"; fi
  }
  chk_hidden 'KEY= form' "${base}1"
  chk_hidden 'export TOKEN= form' "${base}2"
  chk_hidden 'password = "..." form' "${base}3"
  chk_hidden 'JSON quoted key' "${base}4"
  chk_hidden 'JSON client_secret no spaces' "${base}5"
  chk_hidden 'Authorization Bearer' "${base}6"
  chk_hidden 'bare Bearer value' "${base}7"
  chk_hidden 'sk- value' "${base}8"
  chk_hidden 'pat- value' "${base}9"
  chk_hidden 'github token shape' "${base}10"
  chk_hidden 'YAML next line after grep prefix' "${base}11"
  chk_hidden 'YAML block line a' "${base}12a"
  chk_hidden 'YAML block line b' "${base}12b"
  chk_hidden 'web address with user:password' "${base}13"
  chk_hidden 'AKIA-shaped id' "$fakeid"
  chk_hidden 'passwd: form' "${base}14"
  chk_hidden 'pwd= form' "${base}15"
  chk_hidden 'credential = form' "${base}16"
  chk_hidden 'secret at column 300 (hidden before the cut)' "${base}17"
  chk_hidden 'JSON secret followed by more JSON' "${base}18"
  chk_hidden 'quoted secret inside a call' "${base}19"
  chk_kept 'text after a quoted JSON secret stays readable (DELETE)' '"method": "DELETE"'
  chk_kept 'text after a quoted secret in a call stays readable' '# delete path'
  chk_kept 'comparison key == "end" is not hidden' 'if key == "end":'
  chk_kept 'plain answer = "end" is not hidden' 'answer = "end"'
  chk_kept 'the one allowed example key shows' 'AKIAIOSFODNN7EXAMPLE'
  chk_kept 'ordinary line with the word end' 'plain line with the word end in it'
  chk_kept 'unrelated YAML line after a hidden block' 'next_line: stays'
  chk_kept 'unrelated grep line after hidden YAML value' '13-other: fine'
  chk_kept 'long line carries a cut notice' '[CUT: this line has'
  printf 'SELF-TEST: pass=%s fail=%s (input and output copies: %s and %s)\n' "$pass" "$fail" "$in" "$res"
  [ "$fail" -eq 0 ]
}

write_mask_sed
case ${1:-} in
  --mask) mask; exit $? ;;
  --self-test) self_test; exit $? ;;
esac

# ---------------------------------------------------------------- settings
TAKE_DIR=${1:-$PWD}
if [ ! -d "$TAKE_DIR" ]; then echo "take folder not found: $TAKE_DIR" >&2; exit 2; fi
TAKE_DIR=$(cd "$TAKE_DIR" && pwd -P)
FLOWS_DIR=${FLOWS_DIR:-$TAKE_DIR}
MODEL_DIR=${MODEL_DIR:-}
MODEL_SETTINGS=${MODEL_SETTINGS:-}
ONE_STORE=${ONE_STORE:-}

END_RE=${END_RE:-"[\"']end[\"']|(^|[^A-Za-z_])END[A-Z_]*[[:space:]]*=|[=!]=[[:space:]]*end([^A-Za-z_]|\$)"}
MODEL_RE=${MODEL_RE:-'anthropic|messages\.create|/v1/messages|model_program|call_model|post_model|post_lead|llm|complete\(|burst|/qualify|/control|n8n_drive|urlopen|requests\.(get|post)|httpx|subprocess|Popen|webhook|127\.0\.0\.1|localhost'}
DELETE_RE=${DELETE_RE:-'(^|[^A-Za-z_])DELETE([^A-Za-z_]|$)|\.delete\(|requests\.delete|archive|purge|remove|trash|gdpr|cleanup|clean_up|unlink|rmtree|method[[:space:]]*=[[:space:]]*["'"'"'](DELETE|PATCH)'}
GI=-i   # grep case flag; set to empty for a case-sensitive search

# ---------------------------------------------------------------- file lists and path finding
PRUNE='-name .git -o -name node_modules -o -name _local -o -name secrets -o -name .venv -o -name venv -o -name __pycache__'
make_list() { # make_list OUTFILE ROOT KIND   KIND: code | json | py | named:NAME
  ml_out=$1; ml_root=$2; ml_kind=$3
  ( cd "$ml_root" || exit 1
    case $ml_kind in
      code) find . -maxdepth 4 -type d \( $PRUNE -o -name tests -o -name test \) -prune -o -type f \( -name '*.py' -o -name '*.sh' \) ! -name 'test_*' ! -name '*_test.py' ! -name 'conftest.py' ! -name "*${NL}*" -print ;;
      py)   find . -maxdepth 4 -type d \( $PRUNE -o -name tests -o -name test \) -prune -o -type f -name '*.py' ! -name 'test_*' ! -name '*_test.py' ! -name 'conftest.py' ! -name "*${NL}*" -print ;;
      json) find . -maxdepth 4 -type d \( $PRUNE \) -prune -o -type f -name '*.json' ! -name "*${NL}*" -print ;;
      named:*) find . -maxdepth 4 -type d \( $PRUNE \) -prune -o -type f -name "${ml_kind#named:}" ! -name "*${NL}*" -print ;;
    esac ) 2>/dev/null | sort | RT=$ml_root awk '{ sub(/^\.\//, ""); print ENVIRON["RT"] "/" $0 }' > "$ml_out"
}
count_left_out() { # tests and names with a line break, reported so a silent drop cannot hide
  ( cd "$TAKE_DIR" && find . -maxdepth 4 -type f \( -name '*.py' -o -name '*.sh' \) \( -path '*/tests/*' -o -path '*/test/*' -o -name 'test_*' -o -name '*_test.py' -o -name conftest.py \) -print 2>/dev/null | wc -l )
}
count_newline_names() { ( cd "$1" && find . -maxdepth 4 -name "*${NL}*" -print 2>/dev/null | wc -l ); }

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
if [ -n "$MODEL_DIR" ] && [ -d "$MODEL_DIR" ]; then make_list "$WORK/list-model.txt" "$MODEL_DIR" py; else : > "$WORK/list-model.txt"; fi

# ---------------------------------------------------------------- counters and search helpers
blocks=0; with_hits=0; zero_hits=0; files_missing=0; files_unreadable=0
bh=0; bf=0; bm=0; bu=0
S_HITS=0; S_FILES=0; S_MISS=0; S_UNR=0; LAST_HITS=0

begin() { # id, title, question
  blocks=$((blocks + 1)); bh=0; bf=0; bm=0; bu=0
  printf '\n===== BLOCK %s: %s =====\n' "$1" "$2"
  printf 'QUESTION: %s\n' "$3"
}
finish() {
  printf '[block %s] total over all searches in this block: matching lines=%s files_read=%s missing=%s unreadable=%s (a total hides a zero: read the per-search lines above)\n' "$1" "$bh" "$bf" "$bm" "$bu"
  if [ "$bh" -gt 0 ]; then with_hits=$((with_hits + 1)); else zero_hits=$((zero_hits + 1)); fi
}
search_begin() { S_HITS=0; S_FILES=0; S_MISS=0; S_UNR=0; printf -- '--- search: %s\n' "$1"; S_LABEL=$1; }
search_end() {
  printf '    [search "%s": matching lines=%s files_read=%s missing=%s unreadable=%s]' "$S_LABEL" "$S_HITS" "$S_FILES" "$S_MISS" "$S_UNR"
  if [ "$S_FILES" -eq 0 ]; then printf ' ZERO FILES SEARCHED: nothing was looked at'
  elif [ "$S_HITS" -eq 0 ]; then printf ' ZERO HITS: either not there or the search words are wrong; this is not proof of absence'; fi
  if [ "$S_UNR" -gt 0 ]; then printf ' (%s file(s) UNREADABLE: this count is NOT complete)' "$S_UNR"; fi
  printf '\n'
  bh=$((bh + S_HITS)); bf=$((bf + S_FILES)); bm=$((bm + S_MISS)); bu=$((bu + S_UNR))
  files_missing=$((files_missing + S_MISS)); files_unreadable=$((files_unreadable + S_UNR))
  LAST_HITS=$S_HITS
}
search_one() { # search_one PATTERN CONTEXT FILE
  so_pat=$1; so_ctx=$2; so_f=$3
  if [ -z "$so_f" ] || [ ! -e "$so_f" ]; then S_MISS=$((S_MISS + 1)); printf 'FILE MISSING (adjust the path): %s\n' "$so_f"; return; fi
  if [ ! -f "$so_f" ] || [ ! -r "$so_f" ]; then S_UNR=$((S_UNR + 1)); printf 'UNREADABLE (not searched, NOT zero matches): %s\n' "$so_f"; return; fi
  so_c=$(grep -c -E $GI -e "$so_pat" -- "$so_f" 2>"$WORK/grep.err"); so_rc=$?
  if [ "$so_rc" -ge 2 ]; then S_UNR=$((S_UNR + 1)); printf 'UNREADABLE (grep failed: %s; not searched, NOT zero matches): %s\n' "$(head -1 "$WORK/grep.err" | cut -c1-120)" "$so_f"; return; fi
  so_c=${so_c:-0}
  S_FILES=$((S_FILES + 1)); S_HITS=$((S_HITS + so_c))
  printf '%s: %s match line(s)\n' "$so_f" "$so_c"
  if [ "$so_c" -gt 0 ]; then
    grep -n -E $GI -A "$so_ctx" -e "$so_pat" -- "$so_f" 2>/dev/null > "$WORK/g.txt"
    mask < "$WORK/g.txt" > "$WORK/m.txt"
    cat "$WORK/m.txt"
    so_m=$(grep -c '<masked>' "$WORK/m.txt"); so_m=${so_m:-0}
    [ "$so_m" -gt 0 ] && printf '    (a value was hidden on %s line(s) above)\n' "$so_m"
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
lines() { # lines FILE FROM TO
  f=$1; a=$2; b=$3
  if [ ! -e "$f" ]; then bm=$((bm + 1)); files_missing=$((files_missing + 1)); printf 'FILE MISSING (adjust the path): %s\n' "$f"; return; fi
  if [ ! -f "$f" ] || [ ! -r "$f" ]; then bu=$((bu + 1)); files_unreadable=$((files_unreadable + 1)); printf 'UNREADABLE (not read): %s\n' "$f"; return; fi
  bf=$((bf + 1))
  n=$(wc -l < "$f" | tr -d ' '); n=${n:-0}
  printf '%s has %s line(s); lines %s-%s:\n' "$f" "$n" "$a" "$b"
  if [ "$n" -lt "$a" ]; then printf '(file is shorter than line %s: that line number is stale or wrong)\n' "$a"
  else sed -n "${a},${b}p" "$f" | mask; bh=$((bh + 1)); fi
}
list_info() { # list_info LABEL LISTFILE
  li_n=$(wc -l < "$2" | tr -d ' ')
  printf 'files searched for "%s": %s' "$1" "${li_n:-0}"
  if [ "${li_n:-0}" -eq 0 ]; then printf '   <<< 0 FILES SEARCHED: the searches below looked at nothing; check TAKE_DIR / FLOWS_DIR / MODEL_DIR'; fi
  printf '\n'
}
g() { git --no-optional-locks -c core.fsmonitor=false -C "$TAKE_DIR" "$@"; }

# ---------------------------------------------------------------- the checklist
main() {
  printf 'lead-repin-verify.sh v2  (reads only; prints, never judges; the lead reads this output before sharing it)\n'
  printf 'take folder: %s\n' "$TAKE_DIR"
  printf 'private work folder (made by mktemp, you may delete it): %s\n' "$WORK"
  printf 'copy of this output: %s\n' "$OUT"
  printf 'Nothing below was checked against a real take program by the builder of this script.\n'
  printf 'Q27 a, b and c stay UNVERIFIED until the lead shows them at the final head; this script only finds text.\n'
  printf 'Files used:\n%s' "$PATHNOTES"
  printf 'FLOWS_DIR = %s\nMODEL_DIR = %s\n' "$FLOWS_DIR" "${MODEL_DIR:-<not set: the model program folder is NOT SEARCHED>}"
  printf 'Left out on purpose: folders .git node_modules _local secrets .venv venv __pycache__ tests test; files test_*, *_test.py, conftest.py (only below the take folder, so a take folder under a test_ parent is still searched).\n'
  printf 'Test files left out of the code search: %s. Files with a line break in the name (cannot be listed safely, skipped): %s in the take folder.\n' "$(count_left_out | tr -d ' ')" "$(count_newline_names "$TAKE_DIR" | tr -d ' ')"
  list_info "python and shell files of the take" "$WORK/list-code.txt"
  list_info "flow json files" "$WORK/list-flows.txt"
  list_info "model program python files" "$WORK/list-model.txt"

  begin R00 "Final head identity (G1, G26)" "Which commit id and which file checksums are these answers about?"
  if command -v git >/dev/null 2>&1 && g rev-parse --git-dir >/dev/null 2>&1; then
    printf 'HEAD: %s\n' "$(g rev-parse HEAD 2>&1)"
    printf 'changed or untracked files (count): %s\n' "$(g status --porcelain 2>&1 | wc -l | tr -d ' ')"
    g log -1 --format='last commit: %h %ci' 2>&1
    bh=1
  else
    printf 'not a git work tree (or git missing): cannot print a commit id here\n'
  fi
  for f in "$TAKE_PY" "$CRM_PY" "$DRIVE_PY" "$N8N_PY"; do
    if [ -f "$f" ]; then
      bf=$((bf + 1))
      if command -v sha256sum >/dev/null 2>&1; then sha256sum "$f" 2>&1; else shasum -a 256 "$f" 2>&1; fi
    else bm=$((bm + 1)); files_missing=$((files_missing + 1)); printf 'FILE MISSING (adjust the path): %s\n' "$f"; fi
  done
  finish R00

  begin Q23-1 "Any delete or archive path to the CRM (Q23, G1)" "Does any python or shell file of the take (not tests), the CRM module or any flow json contain a delete, archive, purge, remove or cleanup path to the CRM? Decision 2 (the take never deletes) stays; the r17 review found only a rows_with_prefix GET; this block is the final-head grep the lead shows."
  printf 'NOTE: the flow json files in the folder can differ from what n8n actually holds after import (G3); compare with the G2 checksum step.\n'
  SL "delete words in python and shell files" "$DELETE_RE" 1 "$WORK/list-code.txt"
  SL "delete words in flow json files" "$DELETE_RE" 1 "$WORK/list-flows.txt"
  finish Q23-1

  begin Q23-2 "The old line numbers (Q23)" "What stands today at run_real_check_n8n.py lines 1045-1056 and crm_hubspot.py lines 500-512? (The old reading said a DELETE call at line 1051; the lead's answer calls that UNVERIFIED stale text.)"
  lines "$TAKE_PY" 1045 1056
  lines "$CRM_PY" 500 512
  finish Q23-2

  begin Q23-3 "HTTP methods the CRM module uses (Q23, G21)" "Which HTTP methods does the CRM module send? (r17 saw only a rows_with_prefix GET)"
  GI=
  S "HTTP method names, request helpers, rows_with_prefix (case-sensitive)" '(^|[^A-Za-z_])(GET|POST|PUT|PATCH|DELETE|HEAD)([^A-Za-z_]|$)|rows_with_prefix|method[[:space:]]*=|urlopen|requests\.|http\.client|session\.' 0 "$CRM_PY"
  GI=-i
  finish Q23-3

  begin Q23-4 "Delete wording printed to the owner (G1, G17)" "Do the notice or the printed result still say deleted or archived, or print a delete count?"
  S "delete or archive wording in the take program" 'delet|archiv|purg' 0 "$TAKE_PY"
  finish Q23-4

  begin Q27a "Model call after the word end (Q27 a, G34): UNVERIFIED until the lead shows it" "After the take program reads the word end, can it still call the model? Part 1: lines with the end handling (and 20 lines after). Part 2: every model-call line."
  GI=
  S "end handling in the take program (case-sensitive; includes constants)" "$END_RE" 20 "$TAKE_PY"
  GI=-i
  ha=$LAST_HITS
  S "model-call words in the take program, n8n_drive.py and n8n.py" "$MODEL_RE" 0 "$TAKE_PY" "$DRIVE_PY" "$N8N_PY"
  hb=$LAST_HITS
  SL "model-call words in the model program folder (only if MODEL_DIR is set)" "$MODEL_RE" 0 "$WORK/list-model.txt"
  printf 'Q27a reading: end-handling lines=%s, model-call lines=%s. Zero in either means the words are probably wrong, NOT "no model call".\n' "$ha" "$hb"
  printf 'Reading a program cannot show (1) a call already sent before end or (2) an n8n retry or lease that fires a call after end: those need a run or a test shown at the final head. Line order is not always run order.\n'
  finish Q27a

  begin Q27b "End-date refusal (Q27 b, G16, G10): UNVERIFIED until the lead shows it" "Does a setting that refuses a call after the window end exist, and is a refusal SHOWN at the final head (a test run or a startup refusal)?"
  S "window end, need_seconds, refusal words in the take program" 'window|end_date|not_after|deadline|need_seconds|2026-11-2|refus' 0 "$TAKE_PY"
  SL "same words in the model program folder (only if MODEL_DIR is set)" 'window|end_date|not_after|deadline|2026-11-2|refus|after the' 0 "$WORK/list-model.txt"
  printf -- '--- search: test qs_37 (AGENT-SCOPE says it ends spending)\n'
  if [ -z "$MODEL_DIR" ] || [ ! -d "$MODEL_DIR" ]; then printf 'MODEL_DIR not set: qs_37 NOT SEARCHED on the model side (this is not "qs_37 absent")\n'; fi
  : > "$WORK/qs.txt"
  for qd in "$TAKE_DIR" "$MODEL_DIR"; do
    [ -n "$qd" ] && [ -d "$qd" ] && grep -rn -E 'qs_37' --include='*.py' --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=_local --exclude-dir=secrets -- "$qd" 2>/dev/null | mask | head -20 >> "$WORK/qs.txt"
  done
  if [ -s "$WORK/qs.txt" ]; then cat "$WORK/qs.txt"; bh=$((bh + 1)); else printf 'no qs_37 found in the searched folders\n'; fi
  printf -- '--- search: settings NAMES only (values never printed)\n'
  if [ -n "$MODEL_SETTINGS" ] && [ -f "$MODEL_SETTINGS" ] && [ -r "$MODEL_SETTINGS" ]; then
    bf=$((bf + 1)); grep -o -i -E '^[[:space:]]*(export[[:space:]]+)?[A-Za-z0-9_.]*(end|window|deadline|until)[A-Za-z0-9_.]*' "$MODEL_SETTINGS" 2>/dev/null | mask | head -20
  else printf 'MODEL_SETTINGS not set, missing or unreadable: settings NOT SEARCHED (adjust)\n'; fi
  printf 'NOTE: to SEE the refusal, run the named test or the startup refusal yourself at the final head; this script only finds text.\n'
  finish Q27b

  begin Q27c "Go marker before any model call (Q27 c, G33): UNVERIFIED until the lead shows it" "Does the model program refuse to make a paid call until the take program has written a marker after the accepted challenge? BOTH halves are needed."
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
    if [ -n "$o" ]; then printf 'listening (from %s):\n%s\n' "$lt_tool" "$o"; bh=$((bh + 1)); else printf 'none of those ports is listening now (from %s)\n' "$lt_tool"; fi
  fi
  S "port numbers in the take program" '5678|5679|569[0-3]|570[0-9]' 0 "$TAKE_PY"
  finish G07

  begin G20 "DECISION-one-store line 14 (G20)" "Does line 14 still say ONE database?"
  lines "$ONE_STORE" 14 14
  finish G20

  printf '\nSUMMARY: blocks=%s with_hits=%s zero_hits=%s files_missing=%s files_unreadable=%s (counts only; nothing judged; the lead reads each block and the per-search ZERO lines)\n' \
    "$blocks" "$with_hits" "$zero_hits" "$files_missing" "$files_unreadable"
  printf 'Masking is a safety net: read this output yourself before you share it.\n'
}

main 2>&1 | mask_only | tee "$OUT"
exit 0
