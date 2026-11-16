#!/bin/sh
# lead-repin-verify.sh : READ-ONLY checklist printer for the lead at re-pin.
# It only reads files (grep, sed, wc, find, sha256sum, git rev-parse/status/log, ss).
# It writes ONE file: the copy of its own output named in OUT below.
# It makes no network call and no model call, and deletes nothing.
# It judges NOTHING: it prints what it found, with line numbers, for the lead to read.
# Every path below is "adjust if different": set the variable in the environment
# or pass the take folder as the first argument.
#   usage: sh lead-repin-verify.sh [TAKE_DIR]
set -u

TAKE_DIR=${1:-$PWD}                                   # adjust if different
TAKE_PY=${TAKE_PY:-$TAKE_DIR/run_real_check_n8n.py}   # adjust if different
CRM_PY=${CRM_PY:-$TAKE_DIR/crm_hubspot.py}            # adjust if different
DRIVE_PY=${DRIVE_PY:-$TAKE_DIR/n8n_drive.py}          # adjust if different
N8N_PY=${N8N_PY:-$TAKE_DIR/n8n.py}                    # adjust if different
FLOWS_DIR=${FLOWS_DIR:-$TAKE_DIR}                     # adjust if different (folder holding the flow .json files)
MODEL_DIR=${MODEL_DIR:-}                              # adjust: folder of the model program (empty = not searched)
MODEL_SETTINGS=${MODEL_SETTINGS:-}                    # adjust: model settings file (only setting NAMES are printed)
ONE_STORE=${ONE_STORE:-$TAKE_DIR/DECISION-one-store.md}  # adjust if different
OUT=${LEAD_REPIN_OUT:-/tmp/lead-repin-verify-out.txt}    # the only file this script writes

# Words to adjust to the real code (extended regular expressions):
END_RE=${END_RE:-"[\"']end[\"']"}
MODEL_RE=${MODEL_RE:-'anthropic|messages\.create|/v1/messages|model_program|call_model|llm|complete\(|post_model'}
DELETE_RE=${DELETE_RE:-'DELETE|\.delete\(|archive|requests\.delete|urlopen'}

blocks=0; with_hits=0; zero_hits=0; files_missing=0
bh=0; bf=0; bm=0

mask() { # hide values of anything named like a secret, shorten long lines
  sed -E 's/((KEY|key|Key|TOKEN|token|Token|SECRET|secret|Secret|PASSWORD|password|Password)[A-Za-z0-9_]*[[:space:]]*[=:][[:space:]]*)[^[:space:]].*/\1<masked>/' | cut -c1-240
}

begin() { # id, title, question
  blocks=$((blocks + 1)); bh=0; bf=0; bm=0
  printf '\n===== BLOCK %s: %s =====\n' "$1" "$2"
  printf 'QUESTION: %s\n' "$3"
}

finish() {
  printf '[block %s] HITS=%s FILES_READ=%s FILES_MISSING=%s\n' "$1" "$bh" "$bf" "$bm"
  if [ "$bh" -gt 0 ]; then with_hits=$((with_hits + 1)); else zero_hits=$((zero_hits + 1)); fi
}

search() { # search PATTERN CONTEXT_AFTER FILE...   (grep -n, case-insensitive)
  pat=$1; ctx=$2; shift 2
  for f in "$@"; do
    if [ -f "$f" ]; then
      bf=$((bf + 1))
      c=$(grep -c -E -i -e "$pat" -- "$f" 2>/dev/null); c=${c:-0}
      bh=$((bh + c))
      printf '%s: %s match line(s)\n' "$f" "$c"
      if [ "$c" -gt 0 ]; then
        grep -n -E -i -A "$ctx" -e "$pat" -- "$f" 2>/dev/null | mask
      fi
    else
      bm=$((bm + 1)); files_missing=$((files_missing + 1))
      printf 'FILE MISSING (adjust the path): %s\n' "$f"
    fi
  done
}

lines() { # lines FILE FROM TO : print a line range, say so if the file is shorter
  f=$1; a=$2; b=$3
  if [ -f "$f" ]; then
    bf=$((bf + 1))
    n=$(wc -l < "$f"); n=${n:-0}
    printf '%s has %s line(s); lines %s-%s:\n' "$f" "$n" "$a" "$b"
    if [ "$n" -lt "$a" ]; then printf '(file is shorter than line %s: that line number is stale or wrong)\n' "$a"
    else sed -n "${a},${b}p" "$f" | mask; bh=$((bh + 1)); fi
  else
    bm=$((bm + 1)); files_missing=$((files_missing + 1))
    printf 'FILE MISSING (adjust the path): %s\n' "$f"
  fi
}

list_py() { find "$TAKE_DIR" -maxdepth 3 -name '*.py' -not -path '*/.git/*' -not -path '*/tests/*' -not -path '*/test_*' 2>/dev/null; }
list_json() { find "$FLOWS_DIR" -maxdepth 3 -name '*.json' -not -path '*/.git/*' 2>/dev/null; }
list_model() { if [ -n "$MODEL_DIR" ] && [ -d "$MODEL_DIR" ]; then find "$MODEL_DIR" -maxdepth 3 -name '*.py' 2>/dev/null; fi; }

main() {
  printf 'lead-repin-verify.sh  (read-only; prints, never judges)\n'
  printf 'take dir: %s\nnothing below was run by the builder against a real take program.\n' "$TAKE_DIR"

  begin R00 "Final head identity (G1, G26)" "Which commit id and which file checksums are these answers about?"
  if command -v git >/dev/null 2>&1 && git -C "$TAKE_DIR" rev-parse --git-dir >/dev/null 2>&1; then
    printf 'HEAD: %s\n' "$(git -C "$TAKE_DIR" rev-parse HEAD 2>&1)"
    printf 'dirty files (count): %s\n' "$(git -C "$TAKE_DIR" status --porcelain 2>/dev/null | wc -l)"
    git -C "$TAKE_DIR" log -1 --format='last commit: %h %ci' 2>/dev/null
    bh=1
  else
    printf 'not a git work tree (or git missing): cannot print a commit id here\n'
  fi
  for f in "$TAKE_PY" "$CRM_PY" "$DRIVE_PY" "$N8N_PY"; do
    if [ -f "$f" ]; then bf=$((bf + 1)); sha256sum "$f"; else bm=$((bm + 1)); files_missing=$((files_missing + 1)); printf 'FILE MISSING (adjust the path): %s\n' "$f"; fi
  done
  finish R00

  begin Q23-1 "Any delete or archive path to the CRM (Q23, G1)" "Does any python file of the take (not tests) or any flow file contain a delete or archive call to the CRM?"
  search "$DELETE_RE" 1 $(set -f; list_py)
  search "$DELETE_RE" 1 $(set -f; list_json)
  finish Q23-1

  begin Q23-2 "The old line numbers (Q23)" "What stands today at run_real_check_n8n.py lines 1045-1056 and crm_hubspot.py lines 500-512 (the old reading said a DELETE call)?"
  lines "$TAKE_PY" 1045 1056
  lines "$CRM_PY" 500 512
  finish Q23-2

  begin Q23-3 "HTTP methods the CRM module uses (Q23, G21)" "Which HTTP methods does the CRM module send? (r17 saw only a rows_with_prefix GET)"
  search 'GET|POST|PUT|PATCH|DELETE|rows_with_prefix|method' 0 "$CRM_PY"
  finish Q23-3

  begin Q23-4 "Delete wording printed to the owner (G1, G17)" "Do the notice or the printed result still say deleted or archived, or print a delete count?"
  search 'delete|archiv' 0 "$TAKE_PY"
  finish Q23-4

  begin Q27a "Model call after the word end (Q27 a, G34)" "After the take program reads the word end, can it still call the model? Lines with the end handling (and 20 lines after it), then every model-call line."
  search "$END_RE" 20 "$TAKE_PY"
  printf -- '--- model-call lines in the take program (read their line numbers against the end handling above) ---\n'
  search "$MODEL_RE" 0 "$TAKE_PY"
  finish Q27a

  begin Q27b "End-date refusal (Q27 b, G16, G10)" "Does a setting that refuses a call after the window end exist, and is a refusal shown at the final head (a test or a startup refusal)?"
  printf -- '--- take program: window end, need_seconds, refusals ---\n'
  search 'window|end_date|not_after|deadline|need_seconds|2026-11-2|refus' 0 "$TAKE_PY"
  printf -- '--- model program files (only if MODEL_DIR is set) ---\n'
  search 'window|end_date|not_after|deadline|2026-11-2|refus|after the' 0 $(set -f; list_model)
  printf -- '--- test qs_37 (AGENT-SCOPE says it ends spending) ---\n'
  c=$(grep -rn -E 'qs_37' --include='*.py' "$TAKE_DIR" ${MODEL_DIR:+"$MODEL_DIR"} 2>/dev/null | cut -c1-200 | head -20)
  if [ -n "$c" ]; then printf '%s\n' "$c"; bh=$((bh + 1)); else printf 'no qs_37 found under the searched folders\n'; fi
  printf -- '--- settings NAMES only (values hidden) ---\n'
  if [ -n "$MODEL_SETTINGS" ] && [ -f "$MODEL_SETTINGS" ]; then
    bf=$((bf + 1)); grep -o -i -E '^[A-Za-z0-9_.]*(end|window|deadline|until)[A-Za-z0-9_.]*' "$MODEL_SETTINGS" 2>/dev/null | head -20
  else printf 'MODEL_SETTINGS not set or missing (adjust)\n'; fi
  printf 'NOTE: to SEE the refusal, run the named test or the startup refusal yourself; this script only finds text.\n'
  finish Q27b

  begin Q27c "Go marker before any model call (Q27 c, G33)" "Does the model program refuse to make a paid call until the take program has written a marker after the accepted challenge?"
  search 'marker|go_file|ready_file|\.used|\.go\b|accepted|challenge' 0 "$TAKE_PY"
  printf -- '--- model program (only if MODEL_DIR is set) ---\n'
  search 'marker|go_file|ready_file|\.go\b|exists\(|isfile' 0 $(set -f; list_model)
  finish Q27c

  begin G35 "Prompts to the owner (G35)" "Does the take program ask the owner to type anything besides y, the challenge line and end?"
  search 'input\(|getpass|readline|stdin|isatty|worst.?case|figure' 0 "$TAKE_PY"
  finish G35

  begin G06 "Exit codes (G6, Q20.4)" "Which exit codes can the take program leave, and which one for person C unknown?"
  search 'sys\.exit|[^a-z_]exit\(|SystemExit|EXIT_|return [0-3]$|unknown' 0 "$TAKE_PY"
  finish G06

  begin G04 "Call ceiling, price and ledger (G4, G14)" "Where are the call ceiling, retries, ledger total and program limit set?"
  search 'ceiling|max_calls|retries|retry|ledger|backstop|program.?limit|180|189|price' 0 "$TAKE_PY"
  search 'ceiling|max_calls|retries|retry|ledger|backstop|limit|180|189|price' 0 $(set -f; list_model)
  finish G04

  begin G18 "Stop, signal and lock behaviour (G18)" "What happens on a wrong line after end, Ctrl-C, a pause that ends without end, a cancelled key; which lock file is left?"
  search 'KeyboardInterrupt|SIGINT|SIGTERM|SIGHUP|\.lock|closing|interrupted|called off|timeout|give.?up' 0 "$TAKE_PY"
  finish G18

  begin G36 "Think time, silence and film cue (G36)" "Which printed line could start the film pause, and what are the minimum think time, silence and give-up values?"
  search 'think|silence|give.?up|pause|film|sleep\(|print\(.*(start|wait)' 0 "$TAKE_PY"
  finish G36

  begin G37-38 "Key file, demo mail subject, prep contact (G37, G38)" "How is the per-run key file made, what starts the take mail subjects, and does the prep contact address match the film search?"
  search 'set -C|noclobber|O_EXCL|key_file|subject|take-|prep-|label|demo' 0 "$TAKE_PY"
  finish G37-38

  begin G07 "Ports (G7)" "Which of the ports 5678, 5679, 5690-5693, 5701, 5702 are listening now, and does the take program name its own port?"
  if command -v ss >/dev/null 2>&1; then
    bf=$((bf + 1))
    o=$(ss -tln 2>/dev/null | grep -E ':(5678|5679|569[0-3]|570[0-9])[[:space:]]')
    if [ -n "$o" ]; then printf '%s\n' "$o"; bh=$((bh + 1)); else printf 'none of those ports is listening now\n'; fi
  else
    bm=$((bm + 1)); files_missing=$((files_missing + 1)); printf 'ss not found: use netstat -tln by hand\n'
  fi
  search '5678|5679|569[0-3]|570[0-9]' 0 "$TAKE_PY"
  finish G07

  begin G20 "DECISION-one-store line 14 (G20)" "Does line 14 still say ONE database?"
  lines "$ONE_STORE" 14 14
  finish G20

  printf '\nSUMMARY: blocks=%s with_hits=%s zero_hits=%s files_missing=%s (counts only; nothing judged, the lead reads each block)\n' \
    "$blocks" "$with_hits" "$zero_hits" "$files_missing"
}

main | tee "$OUT"
