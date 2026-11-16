#!/bin/bash
# Take-level shell test (round 10, review f8-r10). selftest.py does not run take_check.sh, so this script does, on a temporary copy of the PATCHED real-v5 folder.
# Usage: bash test_take_check.sh PATCHED_REAL_DIR [SCRATCH_DIR]    (SCRATCH_DIR must not exist yet; without it a temporary folder is made and removed again)
# Covers: B1 (writing a pin: never the pin in use, never over an existing file, only on a clean run, never a pass), M1 (environment overrides are exit 4 without the test flag and
# are printed), M3 (a listed flow that is a folder or a dangling link is a FAIL), M4 (the pin header date and sha256 are checked), and a flow whose node count changed while everything
# is still wired (no orphan); round 10b adds M-1 (no deletion promise), M-2 (sha256 of the four flow files), M-3 (pin header must be read by a person; no pin is written when the run has other problems). Round 10d adds A1 (pin comment), B1 (enforced flows sha256), B2 (reviewer line grammar), B3 (exit 5, both folder sources, printed source), B4 (run_all.sh lock), a snapshot-order case, a sha256sum failure case and the refusal of the run_all.sh test hooks. Made-up data only. Exit 0 = every case behaved as expected; exit 1 = at least one did not (each is listed).
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
# f8-r9 (M4): TEST_TAKE_SCRIPT points the whole suite at ANOTHER script, so a leaked variable would test (and pass) the wrong file. It is honoured only with TEST_TAKE_DEV=1, and the path under test is always printed.
if [ -n "${TEST_TAKE_SCRIPT:-}" ] && [ "${TEST_TAKE_DEV:-}" != 1 ]; then echo "REFUSED: TEST_TAKE_SCRIPT is accepted only with TEST_TAKE_DEV=1 (it would test another script than the one in this folder). Unset it for a real run."; exit 2; fi
TAKE="${TEST_TAKE_SCRIPT:-$HERE/take_check.sh}"; echo "script under test: $TAKE"
   # TEST_TAKE_SCRIPT: only to run these cases against an older copy of the script (it must sit in a mirror folder like the one built below)
# f8-r8: the two quick-run hooks below must never leak from an environment into a real run (a leaked RV_DUMP used to make the whole suite exit 0 before any case ran): like the RUN_ALL_* hooks of run_all.sh they are REFUSED (exit 2) unless TEST_TAKE_DEV=1 is set on purpose
if { [ -n "${RV_DUMP:-}" ] || [ -n "${RV_ONLY:-}" ]; } && [ "${TEST_TAKE_DEV:-}" != 1 ]; then echo "REFUSED: RV_DUMP / RV_ONLY are quick-run hooks for editing the word list; they are accepted only with TEST_TAKE_DEV=1 (a leaked variable must not end this suite early)"; exit 2; fi
P=${1:-}; [ -d "$P" ] || { echo "usage: bash test_take_check.sh PATCHED_REAL_DIR [SCRATCH_DIR]"; exit 2; }
P=$(cd "$P" && pwd)
if [ -n "${2:-}" ]; then
  [ -e "$2" ] && { echo "REFUSED: $2 exists"; exit 2; }
  S=$2; mkdir -p -- "$S" || exit 2
else
  S=$(mktemp -d "${TMPDIR:-/tmp}/ttc.XXXXXX") || exit 2
  trap 'rm -rf -- "$S"' EXIT
fi
BAD=0; N=0
ok() { N=$((N+1)); if [ "$1" = 0 ]; then echo "ok   $2"; else echo "FAIL $2"; BAD=$((BAD+1)); fi; }
# tk NAME ARGS...: run the take check with a clean environment (no override, no test flag) plus the extra variables given before "--"
tk() { local nm=$1; shift; local ev=(); while [ "${1:-}" != "--" ]; do ev+=("$1"); shift; done; shift
  env -u TAKE_CHECK_TEST -u TAKE_CHECK_CK -u TAKE_CHECK_WARN_PIN -u TAKE_CHECK_FLOWS -u TAKE_CHECK_DDL -u TAKE_CHECK_FORM_EXPECT ${ev[@]+"${ev[@]}"} bash "$TAKE" "$@" > "$S/$nm.txt" 2>&1; RC=$?; }
has() { grep -q -F -- "$2" "$S/$1.txt"; }
cmp_pins() { cmp -s <(grep -v '^#' "$1") <(grep -v '^#' "$2"); }
PIN="$HERE/take-warns.pin"
PINSUM=$(sha256sum < "$PIN" | cut -d' ' -f1)
# f8-r8: "the output never says a person read the pin" was tested with phrases that appear nowhere (the test could not fail). Now one regex for the claim, and it is first shown to match four sample sentences that make the claim.
SAYS_PERSON_RE='(a|the) person (has |have |had )?(read|reviewed|approved|confirmed|signed)|(read|reviewed|approved|confirmed|signed|checked) by (a|the) person'
says_person() { grep -q -i -E "$SAYS_PERSON_RE" "$1"; }
for s in "a person read the pin" "the person has confirmed these lines" "approved by a person" "Reviewed by the person"; do printf '%s\n' "$s" > "$S/sp.txt"; says_person "$S/sp.txt"; ok $? "negative-claim check: the pattern matches the sample sentence '$s'"; done
PD=$(sed -n 's/^# date (UTC): \([0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}\)$/\1/p' "$PIN" | head -n 1)   # f8-r6: the date used in every reviewer line below is the pin's own date line (never older than the pin, never in the future while the pin is not), so no test breaks when the calendar moves on
TODAY=$(date -u +%Y-%m-%d); YESTERDAY=$(date -u -d "$TODAY -1 day" +%Y-%m-%d); TOMORROW=$(date -u -d "$TODAY +1 day" +%Y-%m-%d); IN2DAYS=$(date -u -d "$TODAY +2 days" +%Y-%m-%d)   # computed ONCE here; the word-check cases below give TODAY to the helper as its fixed today, so none of them can race UTC midnight
OLDDATE=$(date -u -d "$TODAY -400 days" +%Y-%m-%d)   # dates for the old-date cases are computed, never typed
[ -n "$PD" ] || { echo "no date line in the pin"; exit 2; }
LONGX=$(head -c 1100 /dev/zero | tr '\0' x)
BEFOREPIN=$(date -u -d "$PD -1 day" +%Y-%m-%d)
RCPT=$(sed -n 's/^# sha256 of the WARN lines below.*: \([0-9a-f]\{64\}\)$/\1/p' "$PIN" | head -n 1 | cut -c1-8); [ -n "$RCPT" ] || { echo "no WARN-lines hash line in the pin"; exit 2; }
RD="$PD, pin sha256 $RCPT"   # f8-r9 M1: every reviewer line a take accepts carries the receipt (first 8 hex of the WARN-lines hash)
# round 10c (Q1): the committed pin keeps a reviewer line that names a session, so a bare take exits 4 until the lead edits it. Cases that need exit 0 use LEADPIN (same WARN lines, a person's reviewer line); SESSPIN keeps the session wording
{ echo "# reviewed by: Testonly Reviewer, $RD"; grep -v '^# reviewed by' "$PIN"; } > "$S/lead.pin"; LEADPIN="$S/lead.pin"
{ echo "# reviewed by: flows-audit session, $RD, content read by that session only, lead to confirm"; grep -v '^# reviewed by' "$PIN"; } > "$S/sess.pin"

# ---------------------------------------------------------------------------------------------
# The reviewer-line word check, case by case (fast: it calls only `take_check.sh --check-reviewer-line`, nothing else runs). TODAY and the other dates are computed ONCE at the top of this
# file and given to the helper as the fixed "today" (TAKE_CHECK_TODAY, honoured only with the test flag), so no case can race UTC midnight and no date is written into this file.
# Each case reads: want (ok or no) | the line | text that must appear in the reason (for no) | the pin's own date (optional) | extra environment (optional).
# {TODAY} {YESTERDAY} {TOMORROW} {IN2} {PD} {TAB} {ESC} {ZW} {CR} are replaced before the run.
RV_CASES=$(cat <<'EOF'
ok|Pat Smith, {TODAY}
ok|Pat Smith, {YESTERDAY}
ok|Pat Smith, {TOMORROW}
ok|Pat Smith, {TODAY}, read all 4 WARN lines and the code
ok|Pat Smith, {TODAY}, the lead read the sample code and the test notes
ok|Pat Smith, {TODAY}  
ok|Pat Smith, {TODAY}{CR}
ok|Zed Smith, {TODAY}
ok|Aaa Smith, {TODAY}
ok|Al Lee, {TODAY}
ok|Bo Ng, {TODAY}
ok|O'Brien, {TODAY}
ok|Mary-Jane O'Neil, {TODAY}
ok|J.R.R. Tolkien, {TODAY}
ok|Jane Q. Roe-Smith, {TODAY}, read all 4 WARN lines
ok|John Smith Jr., {TODAY}
ok|A. I. Walker, {TODAY}
ok|T. B. Dee, {TODAY}
ok|Pat L. L. M., {TODAY}
ok|Bo Ta, {TODAY}
ok|Jo To Do, {TODAY}
ok|Claudette Smith, {TODAY}
ok|Claudel Dupont, {TODAY}
ok|Pat Robotham, {TODAY}
no|Pat Llamas, {TODAY}|rule: listed word llama
ok|Pat Geminiani, {TODAY}
ok|Aiden Botha, {TODAY}
ok|Sara Gentile, {TODAY}
ok|Mara Gentry, {TODAY}
ok|Sam Pleasant, {TODAY}
ok|Bill Lamar, {TODAY}
ok|Magenta Jones, {TODAY}
ok|Pat Klaude, {TODAY}
no|Pat Cla.ude, {TODAY}|rule: listed word claude
ok|José Müller, {TODAY}
ok|Zoë Nguyễn, {TODAY}
ok|Søren Ørsted, {TODAY}
ok|Иван Петров, {TODAY}
no|Pat O L L M, {TODAY}|rule: name word too short
ok|Pat Smith, {TODAY}, read via O p e n A I
ok|Pat Smith, {TODAY}, read it, all of it
no|Pat Smith|rule: shape
no|TBD|rule: shape
no|, {TODAY}|rule: name characters
no|Pat Smith,{TODAY}|rule: shape
no|Pat Smith,  {TODAY}|rule: shape
no|Pat Smith, 2026-1-5|rule: shape
no|Pat Smith, {TODAY},|rule: shape
no|Pat,Claude Bot, {TODAY}|rule: shape
no|Pat,Gptbot, {TODAY}|rule: shape
no|Pat,Claude, {TODAY}, read all lines|rule: shape
no|Pat,Smith, {TODAY}|rule: shape
no|Roe, Jane, {TODAY}|rule: shape
no|John Smith, Jr., {TODAY}|rule: shape
no|Pat Smith, {TODAY} later|rule: shape
no|Pat Smith, 2026-13-45|rule: bad date
no|Pat Smith, {IN2}|rule: future date
no|Pat Smith, 2999-01-01|rule: future date
no|Pat Smith, {YESTERDAY}|rule: old date|{TODAY}
no|, {TODAY}, x|rule: name characters
no|Pat{TAB}Smith, {TODAY}|rule: hidden character
no|Pat {ESC}[31mSmith, {TODAY}|rule: hidden character
no|Pat Cla{ZW}ude, {TODAY}|rule: hidden character
no|Pat Smith, {TODAY}, ok{ESC}[2J|rule: hidden character
no|R2D2 Four, {TODAY}|rule: name characters
no|Pat O_L_L_M, {TODAY}|rule: name characters
no|Pat C1aude, {TODAY}|rule: name characters
ok|Pat O’Neil, {TODAY}
no|1Pat Smith, {TODAY}|rule: name characters
no|x, {TODAY}|rule: name too short
no|Li, {TODAY}|rule: name too short
no|Claude Monet, {TODAY}|rule: listed word claude
no|Pat Claude, {TODAY}|rule: listed word claude
no|Claude-Code, {TODAY}|rule: listed word claude
no|Cláude Smith, {TODAY}|rule: listed word claude
no|Pat Claudebot, {TODAY}|rule: listed word claudebot
no|Pat Claude Bot, {TODAY}|rule: listed word bot
no|P.a.t C.l.a.u.d.e, {TODAY}|rule: listed word claude
no|Pat C.L.A.U.D.E. Smith, {TODAY}|rule: listed word claude
no|Pat L.L.M., {TODAY}|rule: listed word llm
no|Pat A.I., {TODAY}|rule: listed word ai
no|TBD., {TODAY}|rule: listed word tbd
no|Unknown-, {TODAY}|rule: listed word unknown
no|Agent., {TODAY}|rule: listed word agent
no|Pat Agents, {TODAY}|rule: listed word agents
no|Pat Bots, {TODAY}|rule: listed word bots
no|Pat Chatbot, {TODAY}|rule: listed word chatbot
no|Pat Aibot, {TODAY}|rule: listed word aibot
no|Pat Gptbot, {TODAY}|rule: listed word gptbot
no|Pat Chatgpt, {TODAY}|rule: listed word chatgpt
no|Pat Openai, {TODAY}|rule: listed word openai
no|Pat Fable, {TODAY}|rule: listed word fable
no|Pat Qwen, {TODAY}|rule: listed word qwen
no|Pat Codex, {TODAY}|rule: listed word codex
no|Pat Cursor, {TODAY}|rule: listed word cursor
ok|Pat Devin, {TODAY}
no|Pat Kimi, {TODAY}|rule: listed word kimi
no|Pat Opus, {TODAY}|rule: listed word opus
no|Sonnet Opus, {TODAY}|rule: listed word opus
no|Pat Gemini, {TODAY}|rule: listed word gemini
no|Pat Llama, {TODAY}|rule: listed word llama
no|Pat Mistral, {TODAY}|rule: listed word mistral
no|Pat Grok, {TODAY}|rule: listed word grok
no|Pat Copilot, {TODAY}|rule: listed word copilot
no|Pat Deepseek, {TODAY}|rule: listed word deepseek
no|Pat Anthropic, {TODAY}|rule: listed word anthropic
no|Pat Robot, {TODAY}|rule: listed word robot
no|Some Assistant, {TODAY}|rule: listed word assistant
ok|Ai Nguyen, {TODAY}
no|Pat None, {TODAY}|rule: listed word none
no|Pat Todo, {TODAY}|rule: listed word todo
no|Name Placeholder, {TODAY}|rule: listed word placeholder
ok|Pat Sessions, {TODAY}
no|Test Reviewer, {TODAY}|rule: listed word reviewer
no|Runall Standin, {TODAY}|rule: listed word runall
no|Pat Lead, {TODAY}|rule: listed word lead
no|Pat Sample, {TODAY}|rule: listed word sample
no|Testonly Reviewer, {TODAY}|rule: listed word reviewer
no|Testonly Runall, {TODAY}|rule: listed word runall
no|Testonly Claude, {TODAY}|rule: listed word claude|{PD}|TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN=/x/y
ok|Testonly Reviewer, {TODAY}||{PD}|TAKE_CHECK_WARN_PIN=/x/y
no|Clаude Smith, {TODAY}|rule: mixed alphabets
no|Pat Smith, {TODAY}, written by Claude|rule: listed word claude
no|Pat Smith, {TODAY}, note ChatGPT|rule: listed word chatgpt
no|Pat Smith, {TODAY}, read with C.l.a.u.d.e|rule: listed word claude
no|Pat Smith, {TODAY}, an LLM read it|rule: listed word llm
no|Pat Smith, {TODAY}, an L.L.M. read it|rule: listed word llm
no|Pat Smith, {TODAY}, A.I. wrote it|rule: listed word ai
no|Pat Smith, {TODAY}, read Cl4ude|rule: listed word claude
no|Pat Smith, {TODAY}, read Cláude|rule: listed word claude
no|Pat Smith, {TODAY}, read with cl4ud3|rule: listed word claude
no|Pat Smith, {TODAY}, read by 0pus|rule: listed word opus
no|Pat Smith, {TODAY}, ch4tgpt|rule: listed word chatgpt
no|Pat Smith, {TODAY}, gp7|rule: listed word gpt
no|Pat Smith, {TODAY}, 5onnet|rule: listed word sonnet
no|Pat Smith, {TODAY}, Clаude read it|rule: mixed alphabets
no|Pat Smith, {TODAY}, my assistant helped|rule: listed word assistant
ok|Pat Smith, {TODAY}, no AI used
no|Pat Smith, {TODAY}, TBD|rule: listed word tbd
no|Pat Smith, {TODAY}, not yet read|rule: note says not read
no|Pat Smith, {TODAY}, not read|rule: note says not read
no|Pat Smith, {TODAY}, will read later|rule: note says not read
no|Pat Smith, {TODAY}, read it later|rule: note says not read
no|Pat Smith, {TODAY}, to be read|rule: note says not read
no|Pat Smith, {TODAY}, unread|rule: note says not read
no|Pat Smith, {TODAY}, have not read it|rule: note says not read
ok|Pat Botty, {TODAY}
ok|Pat Agentic, {TODAY}
ok|Pat Possession, {TODAY}
ok|Jane Q. Roe, {TODAY}
ok|Pat Smith, {TODAY}, read-only copy and me@home.net
ok|Pat Smith, {TODAY}, the owner and the team read it
ok|Pat Smith, {TODAY}, checked all lines, nothing missing
ok|Pat Smith, {TODAY}, 11111111111111111111 lines
ok|Jose{MN} Mu{MN}ller, {TODAY}
no|Pat Q Roe, {TODAY}|rule: name word too short
no|Pat Smith -, {TODAY}|rule: name word too short
no|Pat Cl{U034F}aude, {TODAY}|rule: hidden character
no|Pat Smith, {TODAY}, read Cl{U034F}aude|rule: hidden character
no|Pat Smith, {TODAY}, ok{UFE0F}|rule: hidden character
no|Pat{UFE0F} Smith, {TODAY}|rule: hidden character
no|{U3164}{U3164}{U3164}, {TODAY}|rule: hidden character
no|Pat Smith{U3164}, {TODAY}|rule: hidden character
no|Pat Smith, {TODAY}, note{U3164}here|rule: hidden character
no|Pat Smith, {TODAY}, a{U2028}b|rule: hidden character
no|Pat{U115F} Smith, {TODAY}|rule: hidden character
no|Pat{SHY} Smith, {TODAY}|rule: hidden character
no|Pat {MN}{MN}{MN}, {TODAY}|rule: hidden character
no|{MN}{MN}{MN}, {TODAY}|rule: hidden character
no|Pat Smith, {TODAY}, {MN} x|rule: hidden character
no|Pat Smith, {TODAY}, 5{MN}|rule: hidden character
no|Pat Smith, {TODAY}, {LONGX}|rule: too long
no|Pat Cl-aude, {TODAY}|rule: listed word claude
no|Pat Cla'ude, {TODAY}|rule: listed word claude
no|Pat Bo.t, {TODAY}|rule: listed word bot
no|Pat A-I, {TODAY}|rule: listed word ai
no|Pat G-P-T, {TODAY}|rule: listed word gpt
no|Pat L-L-M, {TODAY}|rule: listed word llm
no|Pat Smith, {TODAY}, Cl@ude|rule: listed word claude
no|Pat Smith, {TODAY}, Cl_aude|rule: listed word claude
no|Pat Smith, {TODAY}, Cl-aude|rule: listed word claude
no|ВОТ Smith, {TODAY}|rule: listed word bot
no|Pat ΑΙ, {TODAY}|rule: listed word ai
no|КІМІ Smith, {TODAY}|rule: listed word kimi
no|Pat Smith, {TODAY}, read by КІМІ|rule: listed word kimi
no|Pat Cłaude, {TODAY}|rule: listed word claude
no|Pat Clauđe, {TODAY}|rule: listed word claude
no|Pat Clɑude, {TODAY}|rule: listed word claude
no|Pat Opuѕ, {TODAY}|rule: mixed alphabets
no|John Doe, {TODAY}|rule: listed words john doe
no|Jane Doe, {TODAY}|rule: listed words jane doe
no|Foo Bar, {TODAY}|rule: listed words foo bar
no|Firstname Lastname, {TODAY}|rule: listed word firstname
no|Lorem Ipsum, {TODAY}|rule: listed word ipsum
no|Pat Asdf, {TODAY}|rule: listed word asdf
no|Pat Xxxx, {TODAY}|rule: listed word xxxx
no|Pat Noone, {TODAY}|rule: listed word noone
no|Pat Tba, {TODAY}|rule: listed word tba
no|Pat Tbc, {TODAY}|rule: listed word tbc
no|Pat Pending, {TODAY}|rule: listed word pending
no|Pat Unspecified, {TODAY}|rule: listed word unspecified
no|Pat Owner, {TODAY}|rule: listed word owner
no|Pat Approver, {TODAY}|rule: listed word approver
no|Pat Operator, {TODAY}|rule: listed word operator
no|Pat Maintainer, {TODAY}|rule: listed word maintainer
no|Pat Author, {TODAY}|rule: listed word author
no|Pat Team, {TODAY}|rule: listed word team
no|Pat System, {TODAY}|rule: listed word system
no|Pat Service, {TODAY}|rule: listed word service
no|Pat Support, {TODAY}|rule: listed word support
no|Pat Root, {TODAY}|rule: listed word root
no|Pat Dependabot, {TODAY}|rule: listed word dependabot
no|Pat Renovate, {TODAY}|rule: listed word renovate
ok|Pat Jenkins, {TODAY}
no|Pat Github, {TODAY}|rule: listed word github
no|Pat Bard, {TODAY}|rule: listed word bard
no|Pat Perplexity, {TODAY}|rule: listed word perplexity
no|Pat Siri, {TODAY}|rule: listed word siri
no|Pat Alexa, {TODAY}|rule: listed word alexa
no|Pat Cortana, {TODAY}|rule: listed word cortana
no|Pat Jarvis, {TODAY}|rule: listed word jarvis
no|Pat Windsurf, {TODAY}|rule: listed word windsurf
no|Pat Aider, {TODAY}|rule: listed word aider
no|Pat Manus, {TODAY}|rule: listed word manus
no|Pat Bing, {TODAY}|rule: listed word bing
no|Pat Smith, {TODAY}, read with Perplexity|rule: listed word perplexity
no|Pat Claudes, {TODAY}|rule: listed word claude
no|Pat Sonnets, {TODAY}|rule: listed word sonnet
no|Pat Opuses, {TODAY}|rule: listed word opus
no|Pat Haikus, {TODAY}|rule: listed word haiku
no|Pat Chatbots, {TODAY}|rule: listed word chatbot
no|Pat Copilots, {TODAY}|rule: listed word copilot
no|Pat Geminis, {TODAY}|rule: listed word gemini
no|Pat Codexes, {TODAY}|rule: listed word codex
no|Pat Smith, {TODAY}, written by Claudes|rule: listed word claude
no|Pat Smith, {TODAY}, m1stra1|rule: listed word mistral
no|Pat Smith, {TODAY}, Cop11ot|rule: listed word copilot
no|Pat Smith, {TODAY}, c1aude|rule: listed word claude
no|Pat Smith, {TODAY}, did not read it|rule: note says not read
no|Pat Smith, {TODAY}, will review|rule: note says not read
no|Pat Smith, {TODAY}, to be reviewed|rule: note says not read
no|Pat Smith, {TODAY}, didn't read|rule: note says not read
no|Pat Smith, {TODAY}, haven't read|rule: note says not read
no|Pat Smith, {TODAY}, not checked|rule: note says not read
no|Pat Smith, {TODAY}, skimmed only|rule: note says not read
no|Pat Smith, {TODAY}, pending|rule: note says not read
ok|Pat Sessions, {TODAY}
no|Audit Session, {TODAY}|rule: listed word session
no|Pat Smith, {TODAY}, read with Opuս|rule: mixed alphabets
no|Pat Smith, {TODAY}, read with ĸimi|rule: listed word kimi
no|Pat ĸimi, {TODAY}|rule: listed word kimi
no|Pat Smith, {TODAY}, read with ClaᎠde|rule: mixed alphabets
no|Pat Clаude Smith, {TODAY}|rule: mixed alphabets
no|Pat Smиth, {TODAY}|rule: mixed alphabets
no|Pat Smith, {TODAY}, read with Claʼude|rule: listed word claude
no|Pat Smʰth, {TODAY}|rule: modifier letter
no|Pat ClaudeCode, {TODAY}|rule: listed word claude
no|Pat Smith, {TODAY}, read with c1111111111aude|rule: listed word claude
no|Pat Smith, {TODAY}, read with 0pus|rule: listed word opus
no|Pat Smith, {TODAY}, read with 8ard|rule: listed word bard
no|Pat Smith, {TODAY}, read with 6emini|rule: listed word gemini
no|Pat Smith, {TODAY}, read with Gemini 9|rule: listed word gemini
no|Pat y, {TODAY}|rule: name word too short
ok|張伟, {TODAY}
ok|Ortega y Gasset, {TODAY}
ok|Pat Smith y Jones, {TODAY}
ok|میلان‌الحسینی, {TODAY}
ok|A. Jones, {TODAY}
ok|Pat J., {TODAY}
ok|Pat Smith, {TODAY}, no LLM used
no|Pat Smith, {TODAY}, an LLM read it|rule: listed word llm
no|Pat Llamas, {TODAY}|rule: listed word llama
no|Pat Alexa, {TODAY}, read all lines|rule: listed word alexa
no|Pat Smith, {TODAY}, jenkins read it|rule: listed word jenkins
no|Pat Smith, {TODAY}, lead to confirm|rule: lead to confirm
# f8-r11 (M1, review f8-r10 second angle F1, F2): a Latin sign that is no letter (click, glottal stop) is refused in the name and the note; Greek, Han, Hangul and Arabic letters inside a Latin word; the look-alikes that README promises (o with a stroke, dotless i, the Latin letter script g, small capitals), the note-only signs $ and !, and a name squeezed with a hyphen and a space
ok|Łukasz Þórðarson, {TODAY}
no|Cǀaude Smith, {TODAY}|rule: non-alphabet letter
no|Pat Smith, {TODAY}, Cǀaude read it|rule: non-alphabet letter
no|Claυde Smith, {TODAY}|rule: mixed alphabets
no|Pat Smi李th, {TODAY}|rule: mixed alphabets
no|Pat Smi김th, {TODAY}|rule: mixed alphabets
no|Pat Smiعth, {TODAY}|rule: mixed alphabets
no|øpus Smith, {TODAY}|rule: listed word opus
no|bıng Smith, {TODAY}|rule: listed word bing
no|ɡpt Smith, {TODAY}|rule: listed word gpt
no|ᴄʟᴀᴜᴅᴇ Smith, {TODAY}|rule: listed word claude
no|Pat Smith, {TODAY}, ᴄʟᴀᴜᴅᴇ read it|rule: listed word claude
no|Pat Smith, {TODAY}, read with Opu$|rule: listed word opus
no|Pat Smith, {TODAY}, read with b!ng|rule: listed word bing
no|Cl- aude Smith, {TODAY}|rule: listed word claude
EOF
)
rv_n=0
while IFS='|' read -r want line why pd envx; do
  case "$want" in ok|no) ;; *) continue;; esac
  for tok in TODAY:"$TODAY" YESTERDAY:"$YESTERDAY" TOMORROW:"$TOMORROW" IN2:"$IN2DAYS" PD:"$PD"; do line=${line//\{${tok%%:*}\}/${tok#*:}}; pd=${pd//\{${tok%%:*}\}/${tok#*:}}; done
  line=${line//\{TAB\}/$'\t'}; line=${line//\{ESC\}/$'\033'}; line=${line//\{ZW\}/$'\342\200\213'}; line=${line//\{CR\}/$'\r'}
  line=${line//\{U034F\}/$'\315\217'}; line=${line//\{UFE0F\}/$'\357\270\217'}; line=${line//\{U3164\}/$'\343\205\244'}; line=${line//\{U2028\}/$'\342\200\250'}; line=${line//\{U115F\}/$'\341\205\237'}; line=${line//\{SHY\}/$'\302\255'}; line=${line//\{MN\}/$'\314\201'}; line=${line//\{LONGX\}/$LONGX}
  if [ -n "${RV_DUMP:-}" ]; then printf '%s\037%s\037%s\037%s\037%s\n' "$want" "$line" "$why" "$pd" "$envx" >> "$RV_DUMP"; continue; fi
  rv_n=$((rv_n+1))
  # shellcheck disable=SC2086
  rvout=$(env -u TAKE_CHECK_WARN_PIN TAKE_CHECK_TEST=1 TAKE_CHECK_TODAY="$TODAY" $envx bash "$TAKE" --check-reviewer-line "$line" ${pd:+"$pd"} 2>&1); rvrc=$?
  if [ "$want" = ok ]; then [ "$rvrc" = 0 ] && [ "$rvout" = ok ]; else [ "$rvrc" = 1 ] && case "$rvout" in *"$why"*) true;; *) false;; esac; fi
  ok $? "reviewer line [$want] '$(printf '%s' "${line:0:70}" | tr -d '\000-\037' | sed 's/[^ ]\{16\}/& /g')'$([ ${#line} -gt 70 ] && printf ' [input is %s characters; first 70 shown]' "${#line}") ${why:+reason has '$why'} (got exit $rvrc: ${rvout:0:90})"
done <<< "$RV_CASES"
[ -n "${RV_DUMP:-}" ] && exit 0
# f8-r8: the number of word-check cases is pinned EXACTLY (a floor let 16 cases be deleted without a sound). Change RV_EXPECT together with the case list, and say so in the fix log.
RV_EXPECT=290
RV_LISTED=$(grep -c -E '^(ok|no)\|' <<< "$RV_CASES")
[ "$rv_n" -eq "$RV_EXPECT" ] && [ "$RV_LISTED" -eq "$RV_EXPECT" ]; ok $? "reviewer line: exactly $RV_EXPECT word-check cases ran (ran $rv_n, listed $RV_LISTED)"
# the word list lives in take_check.sh only; the README must print exactly the same two lines
RVW=$(bash "$TAKE" --reviewer-words); RVWRC=$?
[ "$RVWRC" = 0 ] && [ "$(printf '%s\n' "$RVW" | wc -l)" = 6 ]; ok $? "word list: take_check.sh --reviewer-words prints six lines and exits 0 (got exit $RVWRC)"
while IFS= read -r l; do grep -q -x -F -- "$l" "$HERE/README.md"; ok $? "word list: README has this line exactly as take_check.sh prints it: ${l:0:60}..."; done <<< "$RVW"
# the other scripts that call take_check.sh must not hold a copy of the list or of its rules. f8-r8: (a) no variable of the list, (b) the script's own test name appears nowhere, (c) no line holds three or more different listed words (a copy such as grep -E "session|lead to confirm|PLACEHOLDER" holds three), (d) the stand-in name and the pin line check come from take_check.sh
no_list_copy() { # $1 = the script file to look at; prints the offending lines; status 1 when there is a copy. A copy is: a line holding two or more different tool or model names; a line that joins two or more listed words with | (a grep pattern); the script's own test name; a REVIEWER_ variable
  local f=$1 w; w=$(printf '%s\n' "$RVW" | sed -n '1,2p' | sed 's/^[^:]*: //' | tr ' ' '\n' | tr 'A-Z' 'a-z' | grep . | sort -u | tr '\n' ' ')
  awk -v words="$w" 'BEGIN { n = split(words, a, " "); for (i = 1; i <= n; i++) L[a[i]] = 1
      n = split("claude anthropic opus sonnet haiku fable gpt chatgpt openai codex gemini copilot llama mistral grok qwen kimi devin cursor deepseek", a, " "); for (i = 1; i <= n; i++) T[a[i]] = 1 }
    { low = tolower($0); c = 0; delete seen; k = split($0, seg, "|")
      for (i = 1; i <= k; i++) { x = tolower(seg[i]); sub(/^[^a-z]+/, "", x); sub(/[^a-z].*$/, "", x); if ((x in L) && !(x in seen)) { seen[x] = 1; c++ } }
      g = low; gsub(/[^a-z]+/, " ", g); m = split(g, tok, " "); delete tseen; tc = 0
      for (i = 1; i <= m; i++) if ((tok[i] in T) && !(tok[i] in tseen)) { tseen[tok[i]] = 1; tc++ }
      if (c >= 2 || tc >= 2 || index(low, "testonly") > 0 || $0 ~ /REVIEWER_(WORDS|STANDINS)/) { print FILENAME ":" NR ": " substr($0, 1, 120); bad = 1 } }
    END { exit bad }' "$f"
}
NLC=$(no_list_copy "$HERE/run_all.sh" 2>&1); ok $? "word list: run_all.sh holds no copy of the list or of its rules (no line with three listed words, no stand-in test name, no REVIEWER_ variable) ${NLC:0:150}"
printf 'x=1\nif printf "%%s" "$PINREV" | grep -q -i -E "session|lead to confirm|PLACEHOLDER"; then :; fi\n' > "$S/copy-a.sh"; no_list_copy "$S/copy-a.sh" > /dev/null 2>&1; [ $? -ne 0 ]; ok $? "word list: the copy detector flags the old run_all.sh line (so the check above can fail)"
printf '# reviewed by: Testonly Runall, 1\n' > "$S/copy-b.sh"; no_list_copy "$S/copy-b.sh" > /dev/null 2>&1; [ $? -ne 0 ]; ok $? "word list: the copy detector flags the old stand-in name line"
SIN=$(bash "$TAKE" --standin-name); [ "$SIN" = "Testonly Runall" ] && grep -q -F -- '--standin-name' "$HERE/run_all.sh"; ok $? "word list: take_check.sh --standin-name prints the stand-in name and run_all.sh asks for it (got '$SIN')"
grep -q -F -- '--check-reviewer-line' "$HERE/run_all.sh" && grep -q -F -- '--safe-text' "$HERE/run_all.sh"; ok $? "word list: run_all.sh asks take_check.sh for the pin line check and for the printable text"
if [ -n "${RV_ONLY:-}" ]; then echo "test_take_check (RV_ONLY: the word check only): $((N-BAD)) of $N cases as expected, $BAD not as expected"; [ "$BAD" = 0 ]; exit; fi   # a quick way to run just the word-check cases while editing the word list


# the control: the plain take on the patched copy. Exit 0 only when the committed pin carries a reviewer line that is not a session (round 10c); until then exit 4 with the plain reason
tk control -- --flows "$P"
CRL=$(sed -n 's/^# reviewed by: //p' "$PIN" | head -n 1)
CWANT=4; bash "$TAKE" --check-reviewer-line "$CRL" "$PD" "$RCPT" > /dev/null 2>&1 && CWANT=0   # the expected exit is derived from the same helper: 0 only when the committed reviewer line passes it
{ [ "$RC" = "$CWANT" ] && { [ "$CWANT" = 0 ] || has control "pin not yet confirmed by the lead"; }; } && has control "OVERRIDES: none" && has control "Pinned WARN lines:" && has control "known defects" && has control "$CRL"; ok $? "control: the committed pin gives exactly the exit its reviewer line earns (0, or 4 with 'pin not yet confirmed by the lead' while its reviewer line names a session; the reviewer line is printed as written; OVERRIDES says none (got exit $RC)"
# Q1: with a person's reviewer line the same take is exit 0, and the output never says a person read the pin
tk q1ok TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" -- --flows "$P"
[ "$RC" = 5 ] && has q1ok "reviewed by (as written in the pin): Testonly Reviewer, $RD" && has q1ok "The reviewer line is text; not verified." && ! says_person "$S/q1ok.txt"; ok $? "Q1/B3: a pin with a person's reviewer line gives exit 5 (a would-be pass with the pin override; 5, never 0); the line is printed as written; the output does not say a person read the pin (got exit $RC)"
tk q1a TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/sess.pin" -- --flows "$P"
[ "$RC" = 4 ] && has q1a "pin not yet confirmed by the lead" && has q1a "as written: flows-audit session" && ! says_person "$S/q1a.txt"; ok $? "Q1: a reviewer line naming a session and 'lead to confirm' is exit 4 with the plain reason, never 'a person read' (got exit $RC)"
for pair in "only-session:# reviewed by: Audit Session B, $RD" "only-confirm:# reviewed by: A. Person, $RD, Lead To Confirm"; do
  nm=q1-${pair%%:*}; { echo "${pair#*:}"; grep -v '^# reviewed by' "$PIN"; } > "$S/$nm.pin"
  tk "$nm" TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/$nm.pin" -- --flows "$P"
  [ "$RC" = 4 ] && has "$nm" "pin not yet confirmed by the lead"; ok $? "Q1: '${pair#*:}' is exit 4 (got exit $RC)"
done

# B1a: the pin in use as the target is refused, the file stays byte for byte the same
cp -- "$PIN" "$S/inuse.pin"; SUM=$(sha256sum < "$S/inuse.pin")
tk b1a TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/inuse.pin" -- --flows "$P" --write-warn-pin "$S/inuse.pin"
[ "$RC" = 2 ] && has b1a "REFUSED" && [ "$(sha256sum < "$S/inuse.pin")" = "$SUM" ]; ok $? "B1a: --write-warn-pin on the pin in use is refused (exit 2) and leaves it unchanged (got exit $RC)"
# B1b: a new file on a clean run: written, exit 4 (never a pass), has date and sha256 header, same lines as the pin in use
tk b1b -- --flows "$P" --write-warn-pin "$S/new.pin"
[ "$RC" = 4 ] && [ -f "$S/new.pin" ] && has b1b "NEW PIN WRITTEN" && has b1b "never a pass" && grep -q '^# date (UTC): ' "$S/new.pin" && grep -q '^# sha256 of the WARN lines below' "$S/new.pin" && cmp_pins "$S/new.pin" "$PIN"; ok $? "B1b: a clean run writes a NEW pin with date and sha256 and exits 4, not 0 (got exit $RC)"
# a pin written by the script is NOT valid until a person replaces the placeholder in its header (round 10b, M-3); reviewed.pin stands for that person's edit
grep -q '^# flows sha256 (the four flow files, combined, as printed in the top block of take_check.sh): [0-9a-f]\{64\}$' "$S/new.pin"; ok $? "B1: the written pin carries the '# flows sha256' line"
grep -q 'PLACEHOLDER' "$S/new.pin" && grep -q 'NOT YET READ BY A PERSON' "$S/new.pin"; ok $? "M-3: the written pin says it is not yet read and holds the placeholder line"
sed "s/^# reviewed by: .*/# reviewed by: Testonly Reviewer, $RD/" "$S/new.pin" > "$S/reviewed.pin"
tk m3p1 TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/new.pin" -- --flows "$P"
[ "$RC" = 4 ] && has m3p1 "STILL HAS THE PLACEHOLDER"; ok $? "M-3: a pin whose header still has the placeholder is exit 4 (got exit $RC)"
grep -v '^# reviewed by' "$S/reviewed.pin" > "$S/norev.pin"
tk m3p2 TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/norev.pin" -- --flows "$P"
[ "$RC" = 4 ] && has m3p2 "NO '# reviewed by: NAME, DATE' LINE"; ok $? "M-3: a pin with no 'reviewed by' line is exit 4 (got exit $RC)"
# round trip: the written pin, installed by hand, makes the plain take pass
tk b1b2 TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/reviewed.pin" -- --flows "$P"
[ "$RC" = 5 ] && has b1b2 "WARN set equals the pinned set"; ok $? "B1b: the written pin, used as the pin, gives exit 5 (would-be pass with the pin override) (got exit $RC)"
# B1c: an existing file is never overwritten
echo "keep me" > "$S/exists.pin"
tk b1c -- --flows "$P" --write-warn-pin "$S/exists.pin"
[ "$RC" = 2 ] && [ "$(cat "$S/exists.pin")" = "keep me" ]; ok $? "B1c: --write-warn-pin on an existing file is refused (exit 2) and leaves it unchanged (got exit $RC)"
# B1d: a run with a FAIL writes nothing
cp -r -- "$P" "$S/failcopy"
python3 -I - "$S/failcopy/mf-sub-crm-mail.json" <<'PYEOF'
import json, sys
p = sys.argv[1]
j = json.load(open(p, encoding="utf-8"))
for n in j["nodes"]:
    if n["name"] == "SendMail":
        n["disabled"] = True
json.dump(j, open(p, "w", encoding="utf-8"))
PYEOF
tk b1d -- --flows "$S/failcopy" --write-warn-pin "$S/fail.pin"
[ "$RC" = 1 ] && [ ! -e "$S/fail.pin" ] && has b1d "NO PIN WRITTEN"; ok $? "B1d: a run with a FAIL writes no pin and keeps exit 1 (got exit $RC)"
# B1e: a changed WARN set: the run shows the difference, writes the new file, and still exits 4
cp -r -- "$P" "$S/warnnew"
python3 -I - "$S/warnnew/mf-sub-crm-mail.json" <<'PYEOF'
import json, sys
p = sys.argv[1]
j = json.load(open(p, encoding="utf-8"))
for n in j["nodes"]:
    if n["name"] == "MarkDone":
        n["maxTries"] = 3   # a plain WARN: maxTries is ignored without retryOnFail
json.dump(j, open(p, "w", encoding="utf-8"))
PYEOF
tk b1e -- --flows "$S/warnnew" --write-warn-pin "$S/warnnew.pin"
[ "$RC" = 4 ] && [ -f "$S/warnnew.pin" ] && has b1e "THE WARN SET CHANGED" && has b1e "NEW PIN WRITTEN" && grep -q '^  + ' "$S/b1e.txt"; ok $? "B1e: a changed WARN set prints the difference, writes the new file, exits 4 (got exit $RC)"
[ "$(sha256sum < "$PIN" | cut -d' ' -f1)" = "$PINSUM" ]; ok $? "B1: the pin in use (take-warns.pin) is byte for byte unchanged by all cases above"

# M-3: --write-warn-pin writes nothing when the run has any problem other than the WARN difference
cp -r -- "$P" "$S/nosave"
python3 -I - "$S/nosave/mf-form.json" <<'PYEOF'
import json, sys
p = sys.argv[1]
j = json.load(open(p, encoding="utf-8"))
j["settings"]["saveDataSuccessExecution"] = "none"
json.dump(j, open(p, "w", encoding="utf-8"))
PYEOF
tk w1 -- --flows "$S/nosave" --write-warn-pin "$S/w1.pin"
[ "$RC" = 4 ] && [ ! -e "$S/w1.pin" ] && has w1 "NO PIN WRITTEN: this run has other problems"; ok $? "M-3: run saving off (unpatched folder) writes no pin, exit 4 (got exit $RC)"
tk w2 TAKE_CHECK_TEST=1 TAKE_CHECK_DDL="$S/no-such-table.sql" -- --flows "$P" --write-warn-pin "$S/w2.pin"
[ "$RC" = 4 ] && [ ! -e "$S/w2.pin" ] && has w2 "NO PIN WRITTEN: this run has other problems"; ok $? "M-3: table file missing writes no pin, exit 4 (got exit $RC)"
tk w3 TAKE_CHECK_WARN_PIN="$S/reviewed.pin" -- --flows "$P" --write-warn-pin "$S/w3.pin"
[ "$RC" = 4 ] && [ ! -e "$S/w3.pin" ] && has w3 "NO PIN WRITTEN: this run has other problems"; ok $? "M-3: an environment override without the test flag writes no pin, exit 4 (got exit $RC)"
cp -r -- "$P" "$S/nokey"
python3 -I - "$S/nokey/mf-form.json" <<'PYEOF'
import json, sys
p = sys.argv[1]
j = json.load(open(p, encoding="utf-8"))
for n in j["nodes"]:
    if n["name"] == "KeyOk":
        n["name"] = "KeyOkRenamed"   # the key check is gone by name; the wiring in "connections" is left alone on purpose, so the checker may also report a FAIL
json.dump(j, open(p, "w", encoding="utf-8"))
PYEOF
tk w4 -- --flows "$S/nokey" --write-warn-pin "$S/w4.pin"
[ "$RC" = 1 ] && [ ! -e "$S/w4.pin" ] && has w4 "NO PIN WRITTEN"; ok $? "M-3: key check absent writes no pin, exit 1 (the checker FAILs on the renamed step; deterministic) (got exit $RC)"

# M-1 and M-2: the run-saving INFO line promises no deletion; the top block and the FINAL line carry the sha256 of the four flow files
tk sha TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" -- --flows "$P"
EXPECT=$(for f in mf-form.json mf-hook.json mf-recovery.json mf-sub-crm-mail.json; do printf '%s  %s\n' "$(sha256sum < "$P/$f" | cut -d' ' -f1)" "$f"; done | sha256sum | cut -d' ' -f1)
[ "$RC" = 5 ] && has sha "  combined: $EXPECT" && grep -q "^FINAL: .*Flow files sha256 (four files, combined): $EXPECT\." "$S/sha.txt" && has sha "  $(sha256sum < "$P/mf-form.json" | cut -d' ' -f1)  mf-form.json"; ok $? "M-2: the top block and the FINAL line print the combined sha256 of the four flow files (and one per file); exit 5 = would-be pass with the pin override (got exit $RC)"
! has sha "deleted at clean-up" && has sha "This script never deletes them"; ok $? "M-1: the output does not say 'deleted at clean-up'"

# M1: an environment override is printed and is exit 4 without the test flag; with the test flag it is printed and allowed
cp -- "$HERE/check_flows.py" "$S/ck-copy.py"
cp -- "$HERE/../../demo/n8n-flows-v4/mf_leads.sql" "$S/ddl-copy.sql"
tk m1a TAKE_CHECK_WARN_PIN="$S/reviewed.pin" -- --flows "$P"
[ "$RC" = 4 ] && has m1a "ACTIVE ENVIRONMENT OVERRIDES: TAKE_CHECK_WARN_PIN=$S/reviewed.pin" && grep -q '^FINAL: .*ACTIVE ENVIRONMENT OVERRIDES' "$S/m1a.txt"; ok $? "M1: TAKE_CHECK_WARN_PIN without the test flag is exit 4 and is named in the top block and the FINAL line (got exit $RC)"
tk m1-TAKE_CHECK_FLOWS "TAKE_CHECK_FLOWS=$P" --
[ "$RC" = 4 ] && has m1-TAKE_CHECK_FLOWS "ACTIVE ENVIRONMENT OVERRIDES: TAKE_CHECK_FLOWS=$P"; ok $? "M1: TAKE_CHECK_FLOWS without the test flag (and without --flows) is exit 4 and is printed (got exit $RC)"
for pair in "TAKE_CHECK_DDL=$S/ddl-copy.sql" "TAKE_CHECK_CK=$S/ck-copy.py" "TAKE_CHECK_FORM_EXPECT=15:14"; do
  nm=m1-${pair%%=*}
  tk "$nm" "$pair" -- --flows "$P"
  [ "$RC" = 4 ] && has "$nm" "ACTIVE ENVIRONMENT OVERRIDES: $pair"; ok $? "M1: ${pair%%=*} without the test flag is exit 4 and is printed (got exit $RC)"
done
tk m1b TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/reviewed.pin" -- --flows "$P"
[ "$RC" = 5 ] && has m1b "test flag TAKE_CHECK_TEST=1 is set"; ok $? "M1/B3: with the test flag the override is allowed, still printed, and a would-be pass is exit 5 (got exit $RC)"

# M3: a listed flow that is a folder, or a dangling link, is a FAIL (the checker used to skip it silently)
cp -r -- "$P" "$S/dircopy"; rm -f -- "$S/dircopy/mf-hook.json"; mkdir "$S/dircopy/mf-hook.json"
tk m3a -- --flows "$S/dircopy"
[ "$RC" = 1 ] && grep -q '^FAIL .*mf-hook.json this listed flow is not a regular file' "$S/m3a.txt"; ok $? "M3: a folder named mf-hook.json is a FAIL, exit 1 (got exit $RC)"
cp -r -- "$P" "$S/linkcopy"; rm -f -- "$S/linkcopy/mf-recovery.json"; ln -s "$S/does-not-exist.json" "$S/linkcopy/mf-recovery.json"
tk m3b -- --flows "$S/linkcopy"
[ "$RC" = 1 ] && grep -q '^FAIL .*mf-recovery.json this listed flow is not a regular file' "$S/m3b.txt"; ok $? "M3: a dangling link named mf-recovery.json is a FAIL, exit 1 (got exit $RC)"

# M4: the pin header is checked: a hand-edited pin, a pin without the sha256 line and a pin without a date are each exit 4
sed 's/^\(# sha256 of the WARN lines below[^:]*: \)./\1x/' "$S/reviewed.pin" > "$S/badhash.pin"
tk m4a TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/badhash.pin" -- --flows "$P"
[ "$RC" = 4 ] && has m4a "THE PIN HEADER HAS NO SHA-256 LINE"; ok $? "M4: a pin header with a broken sha256 line is exit 4 (got exit $RC)"
sed 's/^\(# sha256 of the WARN lines below[^:]*: [0-9a-f]\{3\}\)./\10/' "$S/reviewed.pin" > "$S/wronghash.pin"
cmp -s "$S/wronghash.pin" "$S/reviewed.pin" && sed 's/^\(# sha256 of the WARN lines below[^:]*: [0-9a-f]\{3\}\)./\11/' "$S/reviewed.pin" > "$S/wronghash.pin"
tk m4b TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/wronghash.pin" -- --flows "$P"
[ "$RC" = 4 ] && has m4b "DOES NOT MATCH ITS OWN SHA-256"; ok $? "M4: a pin whose lines do not match its sha256 is exit 4 (got exit $RC)"
grep -v '^# date' "$S/reviewed.pin" > "$S/nodate.pin"
tk m4c TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/nodate.pin" -- --flows "$P"
[ "$RC" = 4 ] && has m4c "THE PIN HEADER HAS NO DATE"; ok $? "M4: a pin without a date is exit 4 (got exit $RC)"
# a pin edited by hand so that it equals the new WARN set but the header hash is old: caught by the hash, not by the set comparison
{ grep '^#' "$S/reviewed.pin"; grep -v '^#' "$S/reviewed.pin" | head -n 5; } > "$S/short.pin"
tk m4d TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/short.pin" -- --flows "$P"
[ "$RC" = 4 ] && has m4d "DOES NOT MATCH ITS OWN SHA-256" && has m4d "THE WARN SET CHANGED"; ok $? "M4: a pin with lines removed by hand is caught twice (hash and set) (got exit $RC)"

# Q2 (round 10c): a flow file that changes while the check runs is exit 4; every *.json in the folder counts; an unreadable file prints MISSING
cat > "$S/wrap.py" <<PYEOF
import os, subprocess, sys
r = subprocess.run([sys.executable, "-I", "$HERE/check_flows.py"] + sys.argv[1:])
t = os.path.join(os.environ["WRAP_DIR"], os.environ["WRAP_TARGET"])
with open(t, "a", encoding="utf-8") as f:
    f.write("\n")   # the checker has finished; the file changes before this script reads the folder again
sys.exit(r.returncode)
PYEOF
for t in mf-hook.json extra.json; do
  cp -r -- "$P" "$S/chg-$t"; [ "$t" = extra.json ] && printf '%s\n' '{"settings": {"saveDataSuccessExecution": "all", "saveDataErrorExecution": "all", "saveManualExecutions": true}}' > "$S/chg-$t/extra.json"
  tk "q2-$t" TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" TAKE_CHECK_CK="$S/wrap.py" WRAP_TARGET="$t" WRAP_DIR="$S/chg-$t" -- --flows "$S/chg-$t"
  [ "$RC" = 4 ] && has "q2-$t" "A FLOW FILE CHANGED WHILE THIS CHECK RAN"; ok $? "Q2: $t written after the checker ran is exit 4 with the loud line (got exit $RC)"
done
cp -r -- "$P" "$S/extra-ok"; printf '%s\n' '{"settings": {"saveDataSuccessExecution": "all", "saveDataErrorExecution": "all", "saveManualExecutions": true}}' > "$S/extra-ok/extra.json"
tk q2c TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" -- --flows "$S/extra-ok"
[ "$RC" = 1 ] && has q2c "other *.json files in the folder (also read by this script, sha256 taken too): 1" && ! has q2c "A FLOW FILE CHANGED"; ok $? "Q2: an extra *.json that does not change is counted (the checker FAILs on the unexpected file, exit 1; no 'changed' line) (got exit $RC)"
mkdir "$S/stub"; REALSHA=$(command -v sha256sum); printf '#!/bin/bash\ncase "$*" in *mf-hook.json*) exit 1;; esac\nexec %s "$@"\n' "$REALSHA" > "$S/stub/sha256sum"; chmod +x "$S/stub/sha256sum"
tk q2d TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" PATH="$S/stub:$PATH" -- --flows "$P"
[ "$RC" = 4 ] && has q2d "MISSING  mf-hook.json" && has q2d "MISSING or unreadable"; ok $? "Q2: a flow file that sha256sum cannot read is printed as MISSING and is exit 4, never an empty hash (got exit $RC)"
# ---- round 10d ----
# A1: the first line of the committed pin no longer says that a person read each line (only the WARN lines are hashed)
! head -n 1 "$PIN" | grep -q -i "a person read"; ok $? "A1: line 1 of take-warns.pin does not claim that a person read each line"
# B1: a flow file changed in a way the checker does not see (a node position), same counts, same WARN lines: exit 4 because of the enforced flows sha256
cp -r -- "$P" "$S/b1flow"
python3 -I - "$S/b1flow/mf-sub-crm-mail.json" <<'PYEOF'
import json, sys
p = sys.argv[1]
j = json.load(open(p, encoding="utf-8"))
j["nodes"][0]["position"] = [12345, 6789]
json.dump(j, open(p, "w", encoding="utf-8"))
PYEOF
tk b1sha TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" -- --flows "$S/b1flow"
[ "$RC" = 4 ] && has b1sha "THE FLOW FILES DO NOT MATCH THE SHA-256 WRITTEN IN THE PIN" && has b1sha "WARN set equals the pinned set"; ok $? "B1: a changed flow file with the same counts and the same WARN lines is exit 4 (got exit $RC)"
grep -v '^# flows sha256' "$LEADPIN" > "$S/noflowsha.pin"
tk b1nosha TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/noflowsha.pin" -- --flows "$P"
[ "$RC" = 4 ] && has b1nosha "THE PIN HEADER HAS NO '# flows sha256 ...' LINE"; ok $? "B1: a pin without the flows sha256 line is exit 4 (got exit $RC)"
# B2: the reviewer line must read NAME, YYYY-MM-DD (optional note); stand-ins are exit 4
# f8-r8: each case names the ONE message and rule it must give (the old test accepted any of three messages)
for pair in "b2-agent:claude agent, $RD|NOT A PERSON|rule: listed word agent" "b2-tbd:TBD|NOT A PERSON|rule: shape" "b2-x:x, $RD|NOT A PERSON|rule: name too short" "b2-nodate:Testonly Reviewer|NOT A PERSON|rule: shape" "b2-baddate:Testonly Reviewer, 2026-13-45|NOT A PERSON|rule: bad date" "b2-future:Testonly Reviewer, 2999-01-01|NOT A PERSON|rule: future date" "b2-empty-name:, $RD|NOT A PERSON|rule: name characters" "b2-digits:R2D2 4, $RD|NOT A PERSON|rule: name characters" "b2-ai:Some Assistant, $RD|NOT A PERSON|rule: listed word assistant" "b2-placeholder-word:Name Placeholder, $RD|STILL HAS THE PLACEHOLDER|" "b2-session:Audit Session, $RD|pin not yet confirmed by the lead|" "b2-lead-confirm:Pat Smith, $RD, lead to confirm|pin not yet confirmed by the lead|"; do
  nm=${pair%%:*}; spec=${pair#*:}; line=${spec%%|*}; r2=${spec#*|}; msg=${r2%%|*}; rule=${r2#*|}
  { echo "# reviewed by: $line"; grep -v '^# reviewed by' "$PIN"; } > "$S/$nm.pin"
  tk "$nm" TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/$nm.pin" -- --flows "$P"
  [ "$RC" = 4 ] && has "$nm" "$msg" && { [ -z "$rule" ] || has "$nm" "$rule"; } && [ "$(grep -c -E "^!!! (THE 'reviewed by' LINE OF THE PIN IS NOT A PERSON|pin not yet confirmed|THE PIN HEADER STILL HAS THE PLACEHOLDER)" "$S/$nm.txt")" = 1 ]; ok $? "B2: reviewer line '$line' is exit 4 with exactly the message '$msg' ${rule:+and '$rule'} (got exit $RC)"
done
{ echo "# reviewed by: Jane Q. Roe-Smith, $RD, read all 4 WARN lines"; grep -v '^# reviewed by' "$PIN"; } > "$S/b2good.pin"
tk b2good TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/b2good.pin" -- --flows "$P"
[ "$RC" = 5 ] && ! has b2good "NOT A PERSON"; ok $? "B2: 'Jane Q. Roe-Smith, $RD, read all 4 WARN lines' is accepted (would-be pass with the override: exit 5) (got exit $RC)"
# f8-r4 (M1): the bypasses of review f8-r3 (words joined by dots or hyphens, two stand-in words, a repeated letter, the script's own stand-in names, a date far in the past or before the pin's own date). Each must be exit 4 with the reviewer-line message, even with the test flag and the pin override (a name that is not "Testonly ..." gets no test allowance)
for pair in "m1-tbd-dot:TBD., $RD" "m1-claude-code:Claude-Code, $RD" "m1-agent-dot:Agent., $RD" "m1-unknown-dash:Unknown-, $RD" "m1-sonnet-opus:Sonnet Opus, $RD" "m1-runall:Runall Standin, $RD" "m1-test-reviewer:Test Reviewer, $RD" "m1-testonly-no-flag-name:Testonly Reviewer, $RD" "m1-model-in-name:Jane Gemini, $RD" "m1-year-old:Jane Q. Roe-Smith, $OLDDATE" "m1-before-pin:Jane Q. Roe-Smith, $BEFOREPIN" "m1-dotted-llm:Pat L.L.M., $RD" "m1-dotted-claude:P.a.t C.l.a.u.d.e, $RD"; do
  nm=${pair%%:*}; { echo "# reviewed by: ${pair#*:}"; grep -v '^# reviewed by' "$PIN"; } > "$S/$nm.pin"
  tk "$nm" TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/$nm.pin" -- --flows "$P"
  [ "$nm" = m1-testonly-no-flag-name ] && tk "$nm" TAKE_CHECK_WARN_PIN="$S/$nm.pin" -- --flows "$P"   # the test allowance needs BOTH the flag and the override
  [ "$RC" = 4 ] && grep -q -E "^!!! THE 'reviewed by' LINE OF THE PIN IS NOT A PERSON" "$S/$nm.txt"; ok $? "M1: reviewer line '${pair#*:}' is exit 4 with the reviewer-line message (got exit $RC)"
done
# f8-r5: names that must still be accepted (would-be pass with the override: exit 5, never the stand-in message). 'Zed' (3 letters, human-looking) is accepted by design: a script cannot tell it from a real name
for pair in "r5-pat-smith:Pat Smith, $RD" "r5-obrien:O'Brien, $RD" "r5-aiden-botha:Aiden Botha, $RD" "r5-zed:Zed Smith, $RD"; do
  nm=${pair%%:*}; { echo "# reviewed by: ${pair#*:}"; grep -v '^# reviewed by' "$PIN"; } > "$S/$nm.pin"
  tk "$nm" TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/$nm.pin" -- --flows "$P"
  [ "$RC" = 5 ] && ! has "$nm" "NOT A PERSON"; ok $? "f8-r5: reviewer line '${pair#*:}' is accepted (would-be pass with the override: exit 5) (got exit $RC)"
done
# f8-r6 (review f8-r5), updated in f8-r7: refusals of the reviewer-line check run through the whole take (the fuzzy cases of f8-r6 are replaced by the whole-word cases above); dates use computed values, never typed ones.
# each line is refused with exit 4 and the reviewer-line message, even with the test flag and the pin override (these names do not start with Testonly)
for pair in "f8r6-claude-bot:Pat Claude Bot, $RD" "f8r6-claudebot:Pat Claudebot, $RD" "f8r6-chatgpt:Pat Chatgpt, $RD" "f8r6-openai:Pat Openai, $RD" "f8r6-gptbot:Pat Gptbot, $RD" "f8r6-bots:Pat Bots, $RD" "f8r6-agents:Pat Agents, $RD" "f8r6-grok:Pat Grok, $RD" "f8r6-llama:Pat Llama, $RD" "f8r6-mistral:Pat Mistral, $RD" "f8r6-deepseek:Pat Deepseek, $RD" "f8r6-copilot:Pat Copilot, $RD" "f8r6-anthropic:Pat Anthropic, $RD" "f8r6-robot:Pat Robot, $RD" "f8r6-c-l-a-u-d-e-dots-surname:Pat C.L.A.U.D.E. Smith, $RD" "f8r6-underscore:Pat O_L_L_M, $RD" "f8r6-digit:Pat C1aude, $RD" "f8r6-zero-width:Pat Cla$(printf '\342\200\213')ude, $RD" "f8r6-note-claude:Pat Smith, $RD, written by Claude" "f8r6-note-chatgpt:Pat Smith, $RD, note ChatGPT" "f8r6-note-dots:Pat Smith, $RD, read with C.l.a.u.d.e" "f8r6-note-llm:Pat Smith, $RD, an LLM read it"; do
  nm=${pair%%:*}; { echo "# reviewed by: ${pair#*:}"; grep -v '^# reviewed by' "$PIN"; } > "$S/$nm.pin"
  tk "$nm" TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/$nm.pin" -- --flows "$P"
  [ "$RC" = 4 ] && grep -q -E "^!!! THE 'reviewed by' LINE OF THE PIN IS NOT A PERSON" "$S/$nm.txt"; ok $? "f8-r6: reviewer line '${pair#*:}' is exit 4 with the reviewer-line message (got exit $RC)"
done
# 'Sessions' as a surname: any reviewer line containing the word session is refused by the earlier session check (its own message); documented in the README
{ echo "# reviewed by: Audit Session, $RD"; grep -v '^# reviewed by' "$PIN"; } > "$S/f8r6-sessions.pin"
tk f8r6-sessions TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/f8r6-sessions.pin" -- --flows "$P"
[ "$RC" = 4 ] && has f8r6-sessions "pin not yet confirmed by the lead"; ok $? "f8-r6: 'Audit Session' is refused (exit 4, the session message: any line holding the word session is refused) (got exit $RC)"
# names that must be accepted (would-be pass with the override: exit 5, never the reviewer-line message). 'Claudette' passes because only whole words are listed; 'Ai Nguyen' is refused on purpose (the word ai is on the list), see the README
for pair in "f8r6-al-lee:Al Lee, $RD" "f8r6-bo-ng:Bo Ng, $RD" "f8r6-mary-jane:Mary-Jane O'Neil, $RD" "f8r6-tolkien:J.R.R. Tolkien, $RD" "f8r6-botha:Aiden Botha, $RD" "f8r6-claudette:Claudette Smith, $RD" "f8r6-roe:Jane Q. Roe-Smith, $RD" "f8r6-note-ok:Pat Smith, $RD, read all 4 WARN lines and the code" "f8r6-today:Pat Smith, $TODAY, pin sha256 $RCPT" "f8r9-curly:Pat O’Neil, $RD" "f8r9-sessions-surname:Pat Sessions, $RD" "f8r9-devin:Pat Devin, $RD" "f8r9-jenkins:Pat Jenkins, $RD" "f8r9-ai-nguyen:Ai Nguyen, $RD" "f8r7-jose:Jos$(printf '\303\251') M$(printf '\303\274')ller, $RD" "f8r7-initials:A. I. Walker, $RD" "f8r7-bo-ta:Bo Ta, $RD" "f8r7-robotham:Pat Robotham, $RD"; do
  nm=${pair%%:*}; { echo "# reviewed by: ${pair#*:}"; grep -v '^# reviewed by' "$PIN"; } > "$S/$nm.pin"
  tk "$nm" TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/$nm.pin" -- --flows "$P"
  [ "$RC" = 5 ] && ! has "$nm" "NOT A PERSON"; ok $? "f8-r6: reviewer line '${pair#*:}' is accepted (would-be pass with the override: exit 5) (got exit $RC)"
done
# f8-r7: the refusal message names the rule that fired (review f8-r6, design N2), and the cases of the two f8-r6 reviews run through the whole take, not only the helper
for tr in "e7-comma:Pat,Claude Bot, $RD|rule: shape" "e7-comma-gpt:Pat,Gptbot, $RD|rule: shape" "e7-comma-note:Pat,Claude, $RD, read all lines|rule: shape" "e7-roe:Roe, Jane, $RD|rule: shape" "e7-jr-comma:John Smith, Jr., $RD|rule: shape" "e7-chatbot:Pat Chatbot, $RD|rule: listed word chatbot" "e7-future:Pat Smith, 2999-01-01|rule: future date" "e7-before-pin:Pat Smith, $BEFOREPIN|rule: old date" "e7-short:Li, $RD|rule: name too short" "e7-notread:Pat Smith, $RD, not yet read|rule: note says not read" "e7-leet:Pat Smith, $RD, read Cl4ude|rule: listed word claude" "e7-accent-note:Pat Smith, $RD, read Cl$(printf '\303\241')ude|rule: listed word claude" "e7-llm-dots:Pat Smith, $RD, an L.L.M. read it|rule: listed word llm" "e7-ai-dots:Pat Smith, $RD, A.I. wrote it|rule: listed word ai" "e7-fable:Pat Fable, $RD|rule: listed word fable" "e7-bad-date:Pat Smith, 2026-13-45|rule: bad date" "e7-hidden:Pat Cla$(printf '\342\200\213')ude, $RD|rule: hidden character" "e7-cyrillic:Cl$(printf '\320\260')ude Smith, $RD|rule: mixed alphabets" "e7-placeholder-case:Pat Smith, $RD, placeholder|THE PIN HEADER STILL HAS THE PLACEHOLDER"; do
  nm=${tr%%:*}; rest=${tr#*:}; line=${rest%|*}; why=${rest##*|}
  { echo "# reviewed by: $line"; grep -v '^# reviewed by' "$PIN"; } > "$S/$nm.pin"
  tk "$nm" TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/$nm.pin" -- --flows "$P"
  [ "$RC" = 4 ] && grep -q -F -- "$why" "$S/$nm.txt"; ok $? "f8-r7: reviewer line '$line' is exit 4 and the message names '$why' (got exit $RC)"
done
# a trailing space, and a pin saved with Windows line ends (CR LF), are read like the plain form
{ printf '# reviewed by: Pat Smith, %s   \n' "$RD"; grep -v '^# reviewed by' "$PIN"; } > "$S/e7-trail.pin"
tk e7-trail TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/e7-trail.pin" -- --flows "$P"
[ "$RC" = 5 ] && ! has e7-trail "NOT A PERSON" && has e7-trail "WARN set equals the pinned set"; ok $? "f8-r7: a reviewer line with trailing spaces is accepted (exit 5 with the override) (got exit $RC)"
sed 's/$/\r/' "$LEADPIN" > "$S/e7-crlf.pin"
tk e7-crlf TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/e7-crlf.pin" -- --flows "$P"
[ "$RC" = 5 ] && ! has e7-crlf "NOT A PERSON" && ! has e7-crlf "DOES NOT MATCH ITS OWN SHA-256" && has e7-crlf "WARN set equals the pinned set"; ok $? "f8-r7: a whole pin with CR LF line ends is read like the plain pin (exit 5 with the override) (got exit $RC)"
# a reviewer line holding a terminal control character is refused, and the output never repeats that character
{ printf '# reviewed by: Pat \033[31mSmith, %s\n' "$RD"; grep -v '^# reviewed by' "$PIN"; } > "$S/e7-esc.pin"
tk e7-esc TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/e7-esc.pin" -- --flows "$P"
[ "$RC" = 4 ] && has e7-esc "rule: hidden character" && ! grep -q -a "$(printf '\033')" "$S/e7-esc.txt"; ok $? "f8-r7: a reviewer line with an escape character is exit 4 and the output holds no escape character (got exit $RC)"
{ printf '# reviewed by: Audit Session \033[31m, %s\n' "$RD"; grep -v '^# reviewed by' "$PIN"; } > "$S/e7-esc2.pin"
tk e7-esc2 TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/e7-esc2.pin" -- --flows "$P"
[ "$RC" = 4 ] && has e7-esc2 "pin not yet confirmed by the lead" && ! grep -q -a "$(printf '\033')" "$S/e7-esc2.txt"; ok $? "f8-r7: the session message also prints the line without control characters (got exit $RC)"
# the FINAL line says that the reviewer line is only text
grep '^FINAL:' "$S/control.txt" | grep -q -F "The reviewer line is text; not verified."; ok $? "f8-r7: the FINAL line says 'The reviewer line is text; not verified.'"
# the test allowance: flag + override + first word Testonly = exit 5 (never 0); the same name without the flag was refused above
{ echo "# reviewed by: Testonly Runall, $RD"; grep -v '^# reviewed by' "$PIN"; } > "$S/m1-allow.pin"
tk m1-allow TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/m1-allow.pin" -- --flows "$P"
[ "$RC" = 5 ] && ! has m1-allow "NOT A PERSON"; ok $? "M1: with the test flag AND a pin override, a 'Testonly ...' name is accepted and the run is exit 5, never 0 (got exit $RC)"
# the real bypass: the script's own stand-in pin copied in as THE pin (no override, no test flag) must not give exit 0. A mirror folder holds copies of the scripts, the real checker and the pin; demo/ is a link to the real demo folder
MIR="$S/mirror"; mkdir -p "$MIR/flows-audit/flow-check" "$MIR/flows-audit/patches" && ln -s "$HERE/../../demo" "$MIR/demo" && cp -- "$TAKE" "$MIR/flows-audit/flow-check/take_check.sh" && cp -- "$HERE/check_flows.py" "$PIN" "$MIR/flows-audit/flow-check/"
MIRENV=""   # extra variables for one mirror run (a plain shell variable that a person could have exported)
mir() { local nm=$1; shift; env -u TAKE_CHECK_TEST -u TAKE_CHECK_CK -u TAKE_CHECK_WARN_PIN -u TAKE_CHECK_FLOWS -u TAKE_CHECK_DDL -u TAKE_CHECK_FORM_EXPECT $MIRENV bash "$MIR/flows-audit/flow-check/take_check.sh" --flows "$P" > "$S/$nm.txt" 2>&1; RC=$?; }
mir mirbase
MIRSHA=$(sed -n 's/^  combined: \([0-9a-f]\{64\}\)$/\1/p' "$S/mirbase.txt" | head -n 1)
[ -n "$MIRSHA" ]; ok $? "M1: the mirror run printed the combined flows sha256 (needed to build the stand-in pins below)"
for pair in "mir-testrev:Testonly Reviewer, $RD" "mir-test-reviewer:Test Reviewer, $RD" "mir-runall:Runall Standin, $RD" "mir-tbd:TBD., $RD" "mir-claudecode:Claude-Code, $RD"; do
  nm=${pair%%:*}; { echo "# reviewed by: ${pair#*:}"; grep -v '^# reviewed by' "$PIN" | sed "s/^\(# flows sha256 .*: \)[0-9a-f]\{64\}\$/\1$MIRSHA/"; } > "$MIR/flows-audit/flow-check/take-warns.pin"
  mir "$nm"
  [ "$RC" = 4 ] && grep -q "NOT A PERSON" "$S/$nm.txt"; ok $? "M1: '${pair#*:}' in the real pin place, no override, no test flag: exit 4, never 0 (got exit $RC)"
done
{ echo "# reviewed by: Jane Q. Roe-Smith, $RD, read all WARN lines"; grep -v '^# reviewed by' "$PIN" | sed "s/^\(# flows sha256 .*: \)[0-9a-f]\{64\}\$/\1$MIRSHA/"; } > "$MIR/flows-audit/flow-check/take-warns.pin"
mir mir-human
[ "$RC" = 0 ]; ok $? "M1 (honesty check): a made-up human-looking name in the real pin place IS accepted, exit 0: the script cannot know who read the pin; it only turns away stand-ins (got exit $RC)"
# ---- round f8-r8 whole-take cases ----
# M1: a plain shell variable must not move the date rule. The reviewer line below is dated 2998-01-02; the real pin place, no override, no test flag: REVIEWER_TODAY=2999-01-01 used to make it pass (exit 0, OVERRIDES: none)
FUT=2998-01-02
{ echo "# reviewed by: Jane Q. Roe-Smith, $FUT, pin sha256 $RCPT"; grep -v '^# reviewed by' "$PIN" | sed "s/^\(# flows sha256 .*: \)[0-9a-f]\{64\}\$/\1$MIRSHA/"; } > "$MIR/flows-audit/flow-check/take-warns.pin"
for mv in "REVIEWER_TODAY=2999-01-01" "TAKE_CHECK_TODAY=2999-01-01" "REVIEWER_TODAY=2999-01-01 TAKE_CHECK_TODAY=2999-01-01"; do
  MIRENV="$mv"; mir "m1v-${mv//[^A-Z0-9]/}"; MIRENV=""
  nm="m1v-${mv//[^A-Z0-9]/}"
  [ "$RC" = 4 ] && has "$nm" "rule: future date" && has "$nm" "OVERRIDES: none"; ok $? "f8-r8 M1: with '$mv' exported, a pin line dated $FUT is exit 4 'rule: future date' and OVERRIDES says none (got exit $RC)"
done
{ echo "# reviewed by: Pat Smith, $FUT, pin sha256 $RCPT"; grep -v '^# reviewed by' "$PIN"; } > "$S/m1v-test.pin"
tk m1v-test TAKE_CHECK_TEST=1 TAKE_CHECK_TODAY=2999-01-01 REVIEWER_TODAY=2999-01-01 TAKE_CHECK_WARN_PIN="$S/m1v-test.pin" -- --flows "$P"
[ "$RC" = 4 ] && has m1v-test "rule: future date"; ok $? "f8-r8 M1: even with the test flag, TAKE_CHECK_TODAY and REVIEWER_TODAY do not move the date rule in a take (they are read only by --check-reviewer-line) (got exit $RC)"
grep -q 'REVIEWER_TODAY' "$HERE/README.md"; ok $? "f8-r8 M1: the README names REVIEWER_TODAY and says it has no effect"
# a line over 128 KiB (more than a command line can carry) is refused, never read as ok, and the output does not repeat it
{ printf '# reviewed by: Pat Smith, %s, ' "$RD"; head -c 200000 /dev/zero | tr '\0' x; printf '\n'; grep -v '^# reviewed by' "$PIN"; } > "$S/big.pin"
tk big TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/big.pin" -- --flows "$P"
[ "$RC" = 4 ] && has big "rule: too long" && has big "[cut: 300 of 2000" && ! grep -q -E 'x{301}' "$S/big.txt"; ok $? "f8-r8: a reviewer line of 200 KiB is exit 4 with 'rule: too long', printed cut at 300 characters with its length (got exit $RC)"
# a note with shell syntax is only text: accepted (exit 5 with the override), nothing is run
SENT="/tmp/ttc-sentinel-$$"; rm -f -- "$SENT" "$SENT-2"   # a short neutral path: the scratch folder name itself may hold a listed word
{ printf '# reviewed by: Pat Smith, %s, run $(touch %s) and `touch %s-2` and "q" and '"'"'r'"'"' ; touch %s\n' "$RD" "$SENT" "$SENT" "$SENT"; grep -v '^# reviewed by' "$PIN"; } > "$S/shellnote.pin"
tk shellnote TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/shellnote.pin" -- --flows "$P"
[ "$RC" = 5 ] && ! has shellnote "NOT A PERSON" && [ ! -e "$SENT" ] && [ ! -e "$SENT-2" ] && has shellnote 'run $(touch'; ok $? "f8-r8: a note holding \$(...), backticks and quotes is accepted as plain text (exit 5 with the override) and nothing is executed (got exit $RC)"
# the 300-character cut: the printed line is cut and says how long it was
CUTNOTE=$(head -c 400 /dev/zero | tr '\0' y); CUTLINE="Pat Smith, $RD, $CUTNOTE"
{ printf '# reviewed by: %s\n' "$CUTLINE"; grep -v '^# reviewed by' "$PIN"; } > "$S/cut.pin"
tk cut TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/cut.pin" -- --flows "$P"
[ "$RC" = 5 ] && has cut "[cut: 300 of ${#CUTLINE} characters shown]" && ! grep -q -E 'y{301}' "$S/cut.txt"; ok $? "f8-r8: a 400-character note is accepted and printed cut at 300 with '[cut: 300 of ${#CUTLINE} characters shown]' (got exit $RC)"
# hidden characters through the whole take, in the name and in the note (each is exit 4, rule hidden character, and the output holds none of them)
i=0
for hl in "Pat Cl$(printf '\315\217')aude, $RD" "Pat Smith, $RD, ok$(printf '\357\270\217')" "$(printf '\343\205\244\343\205\244\343\205\244'), $RD" "Pat Smith, $RD, a$(printf '\342\200\250')b" "Pat $(printf '\314\201\314\201\314\201'), $RD" "Pat Smith$(printf '\341\205\237'), $RD"; do
  i=$((i+1)); nm=hid$i; { printf '# reviewed by: %s\n' "$hl"; grep -v '^# reviewed by' "$PIN"; } > "$S/$nm.pin"
  tk "$nm" TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/$nm.pin" -- --flows "$P"
  [ "$RC" = 4 ] && has "$nm" "rule: hidden character" && ! LC_ALL=C grep -q -a -E $'\315\217|\357\270\217|\343\205\244|\342\200\250|\314\201|\341\205\237' "$S/$nm.txt"; ok $? "f8-r8 M2: hidden-character line #$i is exit 4 'rule: hidden character' and the output repeats none of the characters (got exit $RC)"
done
# m2: Possession is not the word session (word match, as the README says): accepted; Sessions keeps its own message
{ echo "# reviewed by: Pat Possession, $RD"; grep -v '^# reviewed by' "$PIN"; } > "$S/poss.pin"
tk poss TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/poss.pin" -- --flows "$P"
[ "$RC" = 5 ] && ! has poss "NOT A PERSON" && ! has poss "not yet confirmed by the lead"; ok $? "f8-r8 m2: 'Pat Possession' is not read as the word session (exit 5 with the override) (got exit $RC)"
# helper options
[ "$(bash "$TAKE" --safe-text "a$(printf '\342\200\250')b$(printf '\033')c")" = "abc" ]; ok $? "f8-r8: --safe-text removes line separators and control characters"
[ "$(bash "$TAKE" --safe-text "$(head -c 350 /dev/zero | tr '\0' z)")" = "$(head -c 300 /dev/zero | tr '\0' z) [cut: 300 of 350 characters shown]" ]; ok $? "f8-r8: --safe-text cuts at 300 characters and says the length"
# README: a short blacklist, not a definition of a person; hidden-character and cut wording
grep -q -i 'short blacklist' "$HERE/README.md" && grep -q -F 'cut at 300' "$HERE/README.md"; ok $? "f8-r8: the README says the list is a short blacklist and that the printed line is cut at 300 characters"
! grep -q -i -E 'printed exactly as written|prints the reviewer line as written' "$HERE/README.md" "$TAKE"; ok $? "f8-r8 m4: neither the README nor the script says the reviewer line is printed 'exactly as written'"
# B3: a would-be pass with a leaked override and the test flag is exit 5, never 0; a copy of the real checker given by TAKE_CHECK_CK is shown
tk b3ck TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" TAKE_CHECK_CK="$S/ck-copy.py" -- --flows "$P"
[ "$RC" = 5 ] && has b3ck "ACTIVE ENVIRONMENT OVERRIDES: TAKE_CHECK_CK=$S/ck-copy.py" && has b3ck "a run that would pass exits 5, never 0" && grep -q '^FINAL: take_check exit status 5\.' "$S/b3ck.txt"; ok $? "B3: test flag plus a leaked TAKE_CHECK_CK (and the pin override) is exit 5 with the FINAL line saying 5, not exit 0 (got exit $RC)"
# B3: TAKE_CHECK_FLOWS together with --flows is refused (exit 2) in every mode
tk b3both TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" TAKE_CHECK_FLOWS="$S/b1flow" -- --flows "$P"
[ "$RC" = 2 ] && has b3both "REFUSED: the environment variable TAKE_CHECK_FLOWS and the option --flows are both set"; ok $? "B3: TAKE_CHECK_FLOWS and --flows both set is exit 2 (got exit $RC)"
# B3: the real source of the folder name is printed
tk b3src1 TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" TAKE_CHECK_FLOWS="$P" --
has b3src1 "Flows folder checked: $P (taken from the environment variable TAKE_CHECK_FLOWS, a test override)" && [ "$RC" = 5 ]; ok $? "B3: a folder taken from TAKE_CHECK_FLOWS is printed as coming from the variable (got exit $RC)"
tk b3src2 TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" -- --flows "$P"
has b3src2 "Flows folder checked: $P (given with --flows)"; ok $? "B3: a folder given with --flows is printed as given with --flows"
# snapshot order (minor): the first read of a flow file (has_keyok, python3) must come AFTER the sha256 snapshot, so a write made by that very first read is seen
cp -r -- "$P" "$S/snapord"; mkdir "$S/stubpy"; REALPY=$(command -v python3)
printf '#!/bin/bash\nif [ ! -e "%s/stubpy/done" ]; then : > "%s/stubpy/done"; printf "\\n" >> "%s/snapord/mf-form.json"; fi\nexec %s "$@"\n' "$S" "$S" "$S" "$REALPY" > "$S/stubpy/python3"; chmod +x "$S/stubpy/python3"
tk snapord TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" PATH="$S/stubpy:$PATH" -- --flows "$S/snapord"
[ "$RC" = 4 ] && has snapord "A FLOW FILE CHANGED WHILE THIS CHECK RAN"; ok $? "snapshot order: a flow file written by the first python3 read is caught (got exit $RC)"
# sha256sum failure (minor): a sha256sum that fails when it reads standard input is a loud problem, exit 4, never an empty hash
mkdir "$S/stub3"; printf '#!/bin/bash\n[ $# -eq 0 ] && exit 1\nexec %s "$@"\n' "$(command -v sha256sum)" > "$S/stub3/sha256sum"; chmod +x "$S/stub3/sha256sum"
tk shafail TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" PATH="$S/stub3:$PATH" -- --flows "$P"
[ "$RC" = 4 ] && has shafail "UNAVAILABLE (sha256sum failed)" && grep -q '^!!! sha256sum FAILED' "$S/shafail.txt"; ok $? "sha256sum failure: exit 4 with a loud line, no empty hash (got exit $RC)"
# B4 + f8-r4 (M2): run_all.sh locks the raw FOLDER itself (physical path, pwd -P), so the lock does not depend on TMPDIR, on how the path is written (relative, symbolic link) or on the current folder. The test holds a lock on the folder and starts --lock-only runs in other ways
RA="$HERE/run_all.sh"; mkdir -p "$S/rl-cwd" "$S/rl-raw" "$S/tmpA" "$S/tmpB"; ln -s "$S/rl-raw" "$S/rl-link"
ra() { local nm=$1 cwd=$2 tmpd=$3 raw=$4; ( cd "$cwd" && TMPDIR="$tmpd" RUN_ALL_NESTED=1 RUN_ALL_RAW="$raw" timeout 20 bash "$RA" --lock-only > "$S/$nm.txt" 2>&1; echo $? > "$S/$nm.rc" ); RC=$(cat "$S/$nm.rc" 2>/dev/null); }
# nobody holds the lock: acquired, exit 0, and no lock file is left in either TMPDIR
ra b4free "$S/rl-cwd" "$S/tmpA" "$S/rl-raw"
[ "$RC" = 0 ] && grep -q "lock acquired" "$S/b4free.txt" && [ -z "$(ls -A "$S/tmpA")" ]; ok $? "B4: with nobody holding the lock, run_all.sh --lock-only takes it, exits 0 and leaves no lock file in TMPDIR (got exit $RC)"
# someone holds the lock on the folder (the test itself, on the physical folder)
(
  exec 9< "$S/rl-raw" && flock -n 9 || exit 9
  ra b4held "$S/rl-cwd" "$S/tmpA" "$S/rl-raw";            [ "$RC" = 2 ] && grep -q "REFUSED: another run_all.sh holds the lock" "$S/b4held.txt"; echo $? > "$S/m2a.r"
  ra b4tmp "$S/rl-cwd" "$S/tmpB" "$S/rl-raw";             [ "$RC" = 2 ] && grep -q "REFUSED: another run_all.sh holds the lock" "$S/b4tmp.txt";  echo $? > "$S/m2b.r"
  ra b4link "$S/rl-cwd" "$S/tmpB" "$S/rl-link";           [ "$RC" = 2 ] && grep -q "REFUSED: another run_all.sh holds the lock" "$S/b4link.txt"; echo $? > "$S/m2c.r"
  ra b4rel "$S/rl-cwd" "$S/tmpA" "../rl-raw";             [ "$RC" = 2 ] && grep -q "REFUSED: another run_all.sh holds the lock" "$S/b4rel.txt";  echo $? > "$S/m2d.r"
  ra b4dots "$S/rl-cwd" "$S/tmpB" "$S//rl-link/../rl-raw/"; [ "$RC" = 2 ] && grep -q "REFUSED: another run_all.sh holds the lock" "$S/b4dots.txt"; echo $? > "$S/m2e.r"
  ra b4other "$S/rl-cwd" "$S/tmpA" "$S/rl-raw-other";     [ "$RC" = 0 ] && grep -q "lock acquired" "$S/b4other.txt"; echo $? > "$S/m2f.r"
)
for pair in "m2a:a second run_all.sh on a locked raw folder is refused, exit 2" "m2b:the same raw folder with a DIFFERENT TMPDIR is refused, exit 2" "m2c:the same raw folder given through a symbolic link (and another TMPDIR) is refused, exit 2" "m2d:the same raw folder given as a relative path from another folder is refused, exit 2" "m2e:the same raw folder given with a double slash, a link and .. is refused, exit 2" "m2f:a DIFFERENT raw folder is not blocked by that lock (exit 0)"; do
  [ "$(cat "$S/${pair%%:*}.r" 2>/dev/null)" = 0 ]; ok $? "M2: ${pair#*:}"
done
[ -z "$(ls -A "$S/tmpA")" ] && [ -z "$(ls -A "$S/tmpB")" ]; ok $? "M2: no lock file was left in either TMPDIR"
# minor: the run_all.sh test hooks are refused without RUN_ALL_NESTED
( cd "$S/rl-cwd" && env -u RUN_ALL_NESTED RUN_ALL_TAKE_FLOWS="$S/b1flow" RUN_ALL_RAW="$S/rl-raw2" timeout 20 bash "$RA" --lock-only > "$S/hook.txt" 2>&1; echo $? > "$S/hook.rc" )
[ "$(cat "$S/hook.rc" 2>/dev/null)" = 2 ] && grep -q "REFUSED: RUN_ALL_TAKE_FLOWS is a test hook" "$S/hook.txt"; ok $? "RUN_ALL_TAKE_FLOWS without RUN_ALL_NESTED is refused, exit 2 (got exit $(cat "$S/hook.rc" 2>/dev/null))"

# Q5 (round 10c): a checker exit status above 3 is shown and returned as 3 (also with --write-warn-pin); the real codes of --write-warn-pin are 4 (written), 1 (FAIL), 2 (refused), 3 (checker broke)
for n in 3 4 127 137; do
  printf 'import sys\nsys.exit(%s)\n' "$n" > "$S/exit$n.py"
  tk "q5-$n" TAKE_CHECK_TEST=1 TAKE_CHECK_CK="$S/exit$n.py" -- --flows "$P"
  [ "$RC" = 3 ] && has "q5-$n" "its exit status is $n" && has "q5-$n" "FINAL: take_check exit status 3."; ok $? "Q5: a checker that exits $n is shown as $n and the take exits 3 (got exit $RC)"
done
tk q5w TAKE_CHECK_TEST=1 TAKE_CHECK_CK="$S/exit127.py" -- --flows "$P" --write-warn-pin "$S/q5w.pin"
[ "$RC" = 3 ] && [ ! -e "$S/q5w.pin" ]; ok $? "Q5: --write-warn-pin with a checker that exits 127 writes nothing and exits 3 (got exit $RC)"

# count change without an orphan (coordinator item): one extra step is wired in (Receive -> ExtraNode -> ReplyRan), so nothing is unreachable, but 16 steps are not the expected 15
for f in mf-form.json mf-hook.json; do
  cp -r -- "$P" "$S/count-$f"
  python3 -I - "$S/count-$f/$f" <<'PYEOF'
import json, sys
p = sys.argv[1]
j = json.load(open(p, encoding="utf-8"))
j["nodes"].append({"id": "extra-node-0001", "name": "ExtraNode", "type": "n8n-nodes-base.noOp", "typeVersion": 1, "position": [0, 0], "parameters": {}})
c = j["connections"]
c["Receive"]["main"][0].append({"node": "ExtraNode", "type": "main", "index": 0})
c["ExtraNode"] = {"main": [[{"node": "ReplyRan", "type": "main", "index": 0}]]}
json.dump(j, open(p, "w", encoding="utf-8"))
PYEOF
  tk "count-$f" -- --flows "$S/count-$f"
  [ "$RC" = 1 ] && grep -q "^FAIL .*$f node count 16 != expected 15" "$S/count-$f.txt" && ! grep -q -E "^FAIL .*(unreachable|orphan)" "$S/count-$f.txt"; ok $? "count: $f with one extra wired step is exit 1 with a node-count FAIL and no orphan FAIL (got exit $RC)"
done

# ---------------------------------------------------------------------------------------------
# f8-r9 (review f8-r8): receipt, bad pin date, helper fault, remedy text, hazards, read-once, test-script guard
# M1: the receipt. A reviewer line without it, or with another pin's receipt, is refused in a take (exit 4).
{ echo "# reviewed by: Pat Smith, $PD"; grep -v '^# reviewed by' "$PIN"; } > "$S/r9-norcpt.pin"   # (no receipt on purpose)
tk r9-norcpt TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/r9-norcpt.pin" -- --flows "$P"
[ "$RC" = 4 ] && has r9-norcpt "rule: receipt missing"; ok $? "f8-r9 M1: a reviewer line with no 'pin sha256' receipt is exit 4 (rule: receipt missing) (got exit $RC)"
{ echo "# reviewed by: Pat Smith, $PD, pin sha256 00000000"; grep -v '^# reviewed by' "$PIN"; } > "$S/r9-badrcpt.pin"
tk r9-badrcpt TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/r9-badrcpt.pin" -- --flows "$P"
[ "$RC" = 4 ] && has r9-badrcpt "rule: receipt wrong"; ok $? "f8-r9 M1: a reviewer line with another pin's receipt is exit 4 (rule: receipt wrong) (got exit $RC)"
{ echo "# reviewed by: Pat Smith, $RD"; grep -v '^# reviewed by' "$PIN" | sed '0,/^WARN /s/^\(WARN .*\)$/\1 changed/'; } > "$S/r9-edited.pin"
tk r9-edited TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/r9-edited.pin" -- --flows "$P"
[ "$RC" = 4 ]; ok $? "f8-r9 M1: a pin whose WARN lines were edited after the line was written is exit 4 (got exit $RC)"
tk r9-good TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" -- --flows "$P"
[ "$RC" = 5 ] && has r9-good "pin sha256 ${RCPT}"; ok $? "f8-r9 M1: the top block prints the sha256 whose first 8 characters the reviewer line must carry, and a line with the right receipt is accepted (exit 5, test run) (got exit $RC)"
# the helper itself, with the receipt as third argument
for rc in "ok $RCPT" "no 00000000" "no ${RCPT^^}z"; do
  out=$(TAKE_CHECK_TEST=1 TAKE_CHECK_TODAY="$TODAY" bash "$TAKE" --check-reviewer-line "Pat Smith, $TODAY, pin sha256 ${rc#* }" "" "$RCPT" 2>&1 | head -c 200); x=$?
  case "$rc" in ok*) [ "$out" = ok ];; *) case "$out" in *"receipt wrong"*|*"receipt missing"*) true;; *) false;; esac;; esac; ok $? "f8-r9 M1: helper with the receipt ${RCPT} and a line carrying ${rc#* }: want ${rc%% *} (got: ${out:0:70})"
done
# M3: a bad pin date is the pin's fault and says so (not a refusal of the person)
{ echo "# reviewed by: Pat Smith, $RD"; grep -v '^# reviewed by' "$PIN" | sed 's/^# date (UTC): .*/# date (UTC): 2026-99-99/'; } > "$S/r9-baddate.pin"
tk r9-baddate TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/r9-baddate.pin" -- --flows "$P"
[ "$RC" = 4 ] && has r9-baddate "THE PIN'S OWN DATE LINE IS NOT A REAL DATE" && ! has r9-baddate "NOT A PERSON"; ok $? "f8-r9: a pin with an impossible date line is exit 4 with a message about the pin, not about the person (got exit $RC)"
# a helper that crashes is its own message (a python3 stub that fails on the date parser)
mkdir "$S/pystub"; REALPY=$(command -v python3); printf '#!/bin/bash\ncase "$*" in *fromisoformat*) echo "stub crash" >&2; exit 9;; esac\nexec %s "$@"\n' "$REALPY" > "$S/pystub/python3"; chmod +x "$S/pystub/python3"
tk r9-crash TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" PATH="$S/pystub:$PATH" -- --flows "$P"
[ "$RC" = 4 ] && has r9-crash "THE REVIEWER-LINE HELPER BROKE" && ! has r9-crash "NOT A PERSON"; ok $? "f8-r9: a crashing reviewer-line helper is exit 4 with a helper message, never read as a refusal of the person (got exit $RC)"
# M3 remedy: the refusal for a listed word says how to write the name, and the remedy forms are accepted in a take
{ echo "# reviewed by: Pat Alexa, $RD"; grep -v '^# reviewed by' "$PIN"; } > "$S/r9-alexa.pin"
tk r9-alexa TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/r9-alexa.pin" -- --flows "$P"
[ "$RC" = 4 ] && has r9-alexa "A. Jones" && has r9-alexa "Q31"; ok $? "f8-r9 M3: a refused listed word in a take prints the remedy (an initial plus the rest; Q31) (got exit $RC)"
for nm in "A. Jones" "Pat J."; do
  { echo "# reviewed by: $nm, $RD"; grep -v '^# reviewed by' "$PIN"; } > "$S/r9-rem.pin"
  tk r9-rem TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/r9-rem.pin" -- --flows "$P"
  [ "$RC" = 5 ] && ! has r9-rem "NOT A PERSON"; ok $? "f8-r9 M3: the remedy form '$nm' is accepted in a take (exit 5, test run) (got exit $RC)"
done
# the pin writer prints the receipt and the new line format
tk r9-write TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/r9-nopin-here" -- --flows "$P" --write-warn-pin "$S/r9-written.pin"
if [ -e "$S/r9-written.pin" ]; then WH=$(sed -n 's/^# sha256 of the WARN lines below.*: \([0-9a-f]\{64\}\)$/\1/p' "$S/r9-written.pin" | head -n 1); has r9-write "pin sha256 ${WH:0:8}" && grep -q -F "NAME, YYYY-MM-DD, pin sha256 XXXXXXXX" "$S/r9-written.pin"; ok $? "f8-r9 M1: --write-warn-pin prints the receipt (pin sha256 ${WH:0:8}) and the placeholder line states the new format"; else ok 1 "f8-r9 M1: --write-warn-pin wrote no file (exit $RC)"; fi
# environment hazards: named in the output, a take with one is exit 4
printf 'true\n' > "$S/benv.sh"
tk r9-benv TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" BASH_ENV="$S/benv.sh" -- --flows "$P"
[ "$RC" = 4 ] && has r9-benv "BASH_ENV"; ok $? "f8-r9: BASH_ENV set is named and is exit 4 (got exit $RC)"
tk r9-ldp TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" LD_PRELOAD="$S/none.so" -- --flows "$P"
[ "$RC" = 4 ] && has r9-ldp "LD_PRELOAD"; ok $? "f8-r9: LD_PRELOAD set is named and is exit 4 (got exit $RC)"
r9fn() { :; }; export -f r9fn
tk r9-fn TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" -- --flows "$P"
[ "$RC" = 4 ] && has r9-fn "r9fn"; ok $? "f8-r9: an exported shell function is named and is exit 4 (got exit $RC)"
export -nf r9fn 2>/dev/null; unset -f r9fn
# M4: the test-script guard (the suite itself is started as a child process)
out=$(env -u TEST_TAKE_DEV TEST_TAKE_SCRIPT="$TAKE" bash "$HERE/test_take_check.sh" "$P" 2>&1); x=$?
[ "$x" = 2 ] && case "$out" in *"REFUSED: TEST_TAKE_SCRIPT is accepted only with TEST_TAKE_DEV=1"*) true;; *) false;; esac; ok $? "f8-r9 M4: TEST_TAKE_SCRIPT without TEST_TAKE_DEV=1 is refused with exit 2 (got exit $x)"
# read-once: a flow file that changes after the take copied the folder does not change what the checker read (the copy is hashed against the original again at the end)
cp -r -- "$P" "$S/ro"; cat > "$S/ro.py" <<PYEOF
import os, subprocess, sys
r = subprocess.run([sys.executable, "-I", "$HERE/check_flows.py"] + sys.argv[1:])
with open(os.path.join("$S/ro", "mf-hook.json"), "a", encoding="utf-8") as f:
    f.write("\n")
sys.exit(r.returncode)
PYEOF
tk r9-ro TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" TAKE_CHECK_CK="$S/ro.py" -- --flows "$S/ro"
[ "$RC" = 4 ] && has r9-ro "A FLOW FILE CHANGED WHILE THIS CHECK RAN"; ok $? "f8-r9: a file changed in the ORIGINAL folder while the checker read the private copy is still caught at the end (exit 4) (got exit $RC)"

# f8-r9 (second angle M1): a filled mail setting that is not an address must never be printed, logged or written into a pin (fake value built from parts)
FAKEV="zq""wv""-leak-""probe"
cp -r -- "$P" "$S/leak"; python3 -I - "$S/leak/mf-form.json" "$FAKEV" <<'PYEOF'
import json, sys
p, v = sys.argv[1], sys.argv[2]
j = json.load(open(p, encoding="utf-8"))
for n in j["nodes"]:
    if "Trigger" not in n["type"] and "webhook" not in n["type"].lower() and "stickyNote" not in n["type"]:
        n["parameters"]["toEmail"] = v
        break
else:
    sys.exit(3)
json.dump(j, open(p, "w", encoding="utf-8"))
PYEOF
LKX=$?
tk r9-leak TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" -- --flows "$S/leak" --write-warn-pin "$S/r9-leak.pin"
[ "$LKX" = 0 ] && ! grep -q -F -- "$FAKEV" "$S/r9-leak.txt" && { [ ! -e "$S/r9-leak.pin" ] || ! grep -q -F -- "$FAKEV" "$S/r9-leak.pin"; } && grep -q -F "not shaped like an address" "$S/r9-leak.txt"; ok $? "f8-r9 M1(second angle): a mail field filled with a made-up bad value is reported by name only: the value is absent from stdout, stderr and the written pin (planted: $LKX, exit $RC)"
echo "test_take_check: $((N-BAD)) of $N cases as expected, $BAD not as expected"
[ "$BAD" = 0 ]
