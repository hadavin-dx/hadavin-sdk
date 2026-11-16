#!/bin/bash
# F8 runner (round 6; f8-r11: scratch raw folder; f8-r12: limits, clean-up of helper processes, narrower environment). Usage: bash run_all.sh [--strict] [--refresh] [--keep] [--raw-dir FOLDER] [WORKDIR]
#   --raw-dir : the folder that is LOCKED (default: raw/ next to this script). With --refresh only raw/ next to this script may be published into (exit 2 otherwise), whatever --raw-dir says.
# f8-r12: every long step has a time limit (timeout -k 10, limits in ONE place below, a timeout is a failure), a run that is interrupted or aborted stops every process it started before it removes anything, an unknown option is refused (it used to be taken as the work folder), and --refresh publishes only after a run that passed.
#   --refresh : at the very end, and only when the run got that far, copy this run's raw files into the tracked folder raw/ (each file is written under a temporary name and then renamed, so a reader never sees half a file). Without --refresh the tracked raw/ folder is NOT touched (git status stays clean).
#   --keep    : do not delete this run's scratch raw folder at the end (its path is printed). A run that fails keeps it anyway (except the nested test runs), so the raw output of a failure is never lost.
# f8-r11 (the intermittent exit 1 'SELFTEST summary line missing'): every run writes ALL its raw output into its own new scratch folder (mktemp), never into a folder another run, another script or a reader can also touch. Before f8-r11 every run wrote into the one tracked raw/ folder; the lock made a second run refuse, but any other writer of those files (a person's or an agent's second run through another copy of the script, a reader that opens the file while it is rewritten) could mix with this run, and the run could only report 'line missing' without its raw output.
# THE TAKE USES real-v5 ONLY (lead decision 2026-11-16). This script's exit status and its last line are about real-v5 only.
# film-v5 is NOT FOR THE TAKE: it is run and shown in its own block, it never changes the exit status and its numbers are never added to the real-v5 numbers.
#   --strict : also pass --require-real-credential-ids to the default-mode runs, so a credential id or sub-workflow id that is still a placeholder makes this script exit 1.
#   Last line printed is always 'OPEN LEAD DECISIONS (real-v5, the take): n webhook(s) without auth, m $env node(s)' (or 'unknown' when a checker run is missing): exit 0 does NOT mean authentication was checked.
# Default WORKDIR is a new folder made with mktemp (removed again when the script ends; it is a folder this script made itself). Any other WORKDIR must not exist yet or must be empty; it is never deleted.
# What it does (nothing is run in n8n):
#   1. copies the committed real-v5 flows to a scratch folder, applies patch F-002 then F-008 there, runs the flow generator for "real" and "film"
#   2. runs the checker on the committed folders (pristine) and on the generated patched folders, in two modes each, for real-v5 (gating) and film-v5 (shown only):
#        default mode : exit status of the 2 real-v5 runs decides this script's exit status (must be 0). The two known IF branch gaps are recorded with --accept-if (not a self-baseline).
#        strict mode  : --require-webhook-auth --block-env-access (the owner decides these two; expected to exit 1 today; for real-v5 only exit codes other than 0 or 1 count as failure)
#      plus one informational run of real-v5 pristine without any excuse (raw/pristine-no-baseline.txt, expected exit 1 with 2 FAIL, never gating)
#   3. runs take_check.sh on the PATCHED copy (exit 0 required; on the committed unpatched real-v5 it must exit 4 because run saving is off there) and requires its fixed top-block lines (raw/take-check.txt); the lines about placeholders, credential ids and environment variables are required only while the checker reports them, so this script can exit 0 once the files are fixed and filled; then selftest.py (exit status counts; it also exercises the checker on a film-v5 file, which tests the checker, not the film flows)
# Raw output of every step goes to ./raw/ (files without a suffix = real-v5, files ending -film = film-v5).
# Exit status: 0 only if every real-v5 default-mode run and the self-test exit 0 and no step aborted. Exit 3 = a build step aborted, 2 = usage/bad folder.
set -u
# f8-r12 (M3): SHELLOPTS and BASHOPTS can switch on tracing (xtrace) before the first line runs and cannot be unset here (read-only). If either one came in through the environment, stop now, before anything is traced, and say which.
for v in SHELLOPTS BASHOPTS; do read -r _ DECLFLAGS _ < <(declare -p "$v" 2>/dev/null); [[ ${DECLFLAGS:-} == -*x* ]] && { echo "REFUSED: the environment variable $v is exported to this script and would change how it runs (for example switch on tracing); start the script without it (env -u $v bash run_all.sh)"; exit 2; }; done
HERE=$(cd "$(dirname "$0")" && pwd); D="$HERE/../../demo"; PT="$HERE/../patches"; CK="$HERE/check_flows.py"; RAWFINAL="$HERE/raw"   # RAWFINAL = the raw folder that is locked (default: the tracked raw/ next to this script; written only with --refresh, and only when it IS that folder); RAW (the scratch folder of this run) is made below   # f8-r12 (review f8-r12 M1): RUN_ALL_RAW is no longer an input of a plain run (refused); a person or a test names another folder to lock with --raw-dir. RUN_ALL_RAW, RUN_ALL_TAKE_FLOWS and RUN_ALL_NESTED exist only for the nested failure tests below (second runs of this script that are made to fail); RUN_ALL_DROP_LEAD and RUN_ALL_PLANT_TCFAIL_FLOWS (round 10c) are honoured only together with RUN_ALL_NESTED
# f8-r12 (M2): time limits in seconds, ONE place. A step that runs longer is stopped (SIGTERM, then SIGKILL after 10 s) and counts as a failure (exit 124 or 137 is not 0). A limit is never a way to pass: a smaller number only makes a run fail sooner; each can be changed with the RUN_ALL_LIMIT_* variable of the same name (a whole number from 1 to 99999, else exit 2).
LIM_CHECKER=${RUN_ALL_LIMIT_CHECKER:-300}; LIM_SELFTEST=${RUN_ALL_LIMIT_SELFTEST:-900}; LIM_TAKE=${RUN_ALL_LIMIT_TAKE:-300}; LIM_SUITE=${RUN_ALL_LIMIT_SUITE:-1200}; LIM_NESTED=${RUN_ALL_LIMIT_NESTED:-1800}
for v in LIM_CHECKER LIM_SELFTEST LIM_TAKE LIM_SUITE LIM_NESTED; do [[ ${!v} =~ ^[1-9][0-9]{0,4}$ ]] || { echo "REFUSED: the time limit $v (RUN_ALL_${v/LIM_/LIMIT_}) must be a whole number of seconds from 1 to 99999"; exit 2; }; done
lim() { local l=$1; shift; timeout -k 10 "$l" "$@" & wait $!; }   # run in the background and wait, so that a signal sent to this script is handled at once (bash holds a signal until a foreground command ends); the status is the command's (124 / 137 = stopped by the limit)
TCUNSET=(-u TAKE_CHECK_TEST -u TAKE_CHECK_CK -u TAKE_CHECK_WARN_PIN -u TAKE_CHECK_FLOWS -u TAKE_CHECK_DDL -u TAKE_CHECK_FORM_EXPECT)   # round 10c (Q4): every take_check.sh call below starts from a clean TAKE_CHECK_* environment, whatever the caller exported
# f8-r11: the pinned case counts, in ONE place (expected-counts.pin next to this script). count_check SELFTEST_FILE TTC_FILE [PIN]: prints one line, returns 0 when both programs ran exactly the pinned number of cases, 1 otherwise (the number drifted, a line is missing or printed twice, or a case was not as expected).
count_check() {
  local st=$1 tt=$2 pin=${3:-$HERE/expected-counts.pin} k v e_ok="" e_bad="" e_skip="" e_tt="" e_ttbad="" msg="" n
  [ -f "$pin" ] || { echo "COUNT DRIFT: the pin file $pin is missing"; return 1; }
  local seen=" "
  while IFS='=' read -r k v; do   # f8-r12 (m2): a key written twice or a key of another name is a failure, not "the last one wins" / "ignored"
    case $seen in *" $k "*) echo "COUNT DRIFT: the pin file $pin names $k twice"; return 1;; esac
    seen="$seen$k "
    case $k in selftest_as_expected) e_ok=$v;; selftest_not_as_expected) e_bad=$v;; selftest_skipped) e_skip=$v;; take_suite_cases) e_tt=$v;; take_suite_not_as_expected) e_ttbad=$v;; *) echo "COUNT DRIFT: the pin file $pin has a key that is not one of the five ($k)"; return 1;; esac
  done < <(grep -E '^[a-z_]+=[0-9]+$' "$pin")
  for v in "$e_ok" "$e_bad" "$e_skip" "$e_tt" "$e_ttbad"; do [[ $v =~ ^[0-9]+$ ]] || { echo "COUNT DRIFT: $pin does not hold all five numbers"; return 1; }; done
  n=$(grep -c -E '^SELFTEST: [0-9]+ as expected, [0-9]+ not as expected, [0-9]+ skipped \(not applicable\)$' "$st" 2>/dev/null)
  if [ "$n" != 1 ]; then msg="$msg [self-test summary line found $n times (want 1) in $st]"
  elif [ "$(grep -c '^SELFTEST: ' "$st" 2>/dev/null)" != 1 ]; then msg="$msg [$(grep -c '^SELFTEST: ' "$st") lines start with 'SELFTEST: ' in $st (want exactly 1: the summary line)]"   # f8-r12 (m1)
  else
    local l; l=$(grep -m 1 -E '^SELFTEST: [0-9]+ as expected, [0-9]+ not as expected, [0-9]+ skipped \(not applicable\)$' "$st")   # f8-r12 (m1): the SAME line that was counted above
    [[ $l =~ ^SELFTEST:\ ([0-9]+)\ as\ expected,\ ([0-9]+)\ not\ as\ expected,\ ([0-9]+)\ skipped ]]
    [ "${BASH_REMATCH[1]}" = "$e_ok" ] || msg="$msg [self-test as expected: ${BASH_REMATCH[1]}, pinned $e_ok]"
    [ "${BASH_REMATCH[2]}" = "$e_bad" ] || msg="$msg [self-test not as expected: ${BASH_REMATCH[2]}, pinned $e_bad]"
    [ "${BASH_REMATCH[3]}" = "$e_skip" ] || msg="$msg [self-test skipped: ${BASH_REMATCH[3]}, pinned $e_skip]"
  fi
  n=$(grep -c -E '^test_take_check: [0-9]+ of [0-9]+ cases as expected, [0-9]+ not as expected$' "$tt" 2>/dev/null)
  if [ "$n" != 1 ]; then msg="$msg [take-suite summary line found $n times (want 1) in $tt]"
  elif [ "$(grep -c '^test_take_check: ' "$tt" 2>/dev/null)" != 1 ]; then msg="$msg [$(grep -c '^test_take_check: ' "$tt") lines start with 'test_take_check: ' in $tt (want exactly 1: the summary line)]"
  else
    local l; l=$(grep -m 1 -E '^test_take_check: [0-9]+ of [0-9]+ cases as expected, [0-9]+ not as expected$' "$tt")
    [[ $l =~ ^test_take_check:\ ([0-9]+)\ of\ ([0-9]+)\ cases\ as\ expected,\ ([0-9]+)\ not ]]
    [ "${BASH_REMATCH[2]}" = "$e_tt" ] || msg="$msg [take suite cases: ${BASH_REMATCH[2]}, pinned $e_tt]"
    [ "${BASH_REMATCH[1]}" = "${BASH_REMATCH[2]}" ] || msg="$msg [take suite: only ${BASH_REMATCH[1]} of ${BASH_REMATCH[2]} as expected]"
    [ "${BASH_REMATCH[3]}" = "$e_ttbad" ] || msg="$msg [take suite not as expected: ${BASH_REMATCH[3]}, pinned $e_ttbad]"
  fi
  if [ -n "$msg" ]; then echo "COUNT DRIFT (expected-counts.pin):$msg"; return 1; fi
  echo "COUNTS match expected-counts.pin: self-test $e_ok as expected / $e_bad not / $e_skip skipped; take suite $e_tt of $e_tt cases"; return 0
}
# publish_raw SRC DST: copies every plain file of SRC into DST, each under a temporary name and then renamed (a reader never sees half a file); files of DST that SRC does not have are left alone; prints the number copied; returns 1 if one copy failed
# f8-r12 (review f8-r12 M1): DST must be the raw/ folder next to THIS script (compared as physical paths), whoever calls this and however; any other folder is refused (return 2). The one writer of that folder is therefore this function; no environment variable or option can point it at another folder. After the copies, refresh-manifest.txt is written the same way: the run id, the time (UTC) and the sha256 of each file this run published, so a reader can tell which files of raw/ belong to one run (files of older runs that this run did not make are not listed).
publish_raw() {
  local src=$1 dst=$2 f b n=0 bad=0 want got mf
  want=$(realpath -m -- "$HERE/raw") && got=$(realpath -m -- "$dst") && [ -n "$want" ] && [ "$want" = "$got" ] || { echo "REFUSED: publishing is only allowed into the raw/ folder next to this script ($HERE/raw), not into $dst" >&2; return 2; }
  mkdir -p -- "$dst" || return 1
  mf=$(mktemp "$dst/.refresh-manifest.tmp.XXXXXX") && chmod 644 -- "$mf" || return 1
  { echo "# files published by one run_all.sh --refresh (run id $$-$(date -u +%Y%m%dT%H%M%SZ)); files of raw/ that are not listed here come from an older run"; } > "$mf"
  for f in "$src"/*; do
    [ -f "$f" ] || continue
    b=$(basename -- "$f")
    if cp -- "$f" "$dst/.$b.tmp.$$" && mv -f -- "$dst/.$b.tmp.$$" "$dst/$b"; then n=$((n+1)); echo "$(sha256sum -- "$dst/$b" | cut -c1-64)  $b" >> "$mf"; else bad=$((bad+1)); rm -f -- "$dst/.$b.tmp.$$"; echo "REFRESH FAILED for $b" >&2; fi
  done
  if [ "$bad" = 0 ]; then mv -f -- "$mf" "$dst/refresh-manifest.txt" || bad=$((bad+1)); else rm -f -- "$mf"; fi
  echo "$n"; [ "$bad" = 0 ]
}
if [ "${1:-}" = "--publish-raw" ]; then publish_raw "${2:?SRC}" "${3:?DST}"; exit $?; fi
if [ "${1:-}" = "--check-counts" ]; then count_check "${2:?SELFTEST_FILE}" "${3:?TTC_FILE}" "${4:-}"; exit $?; fi
STRICT_IDS=(); ARGS=(); LOCKONLY=""; REFRESH=""; KEEP=""
# f8-r12 (m6): an option that is not known is refused (it used to be taken as the work folder); at most one work folder; --raw-dir names the folder to lock
while [ $# -gt 0 ]; do
  case "$1" in
    --strict) STRICT_IDS=(--require-real-credential-ids);; --lock-only) LOCKONLY=1;; --refresh) REFRESH=1;; --keep) KEEP=1;;
    --raw-dir) [ $# -ge 2 ] && [ -n "$2" ] || { echo "REFUSED: --raw-dir needs a folder name"; exit 2; }; RAWFINAL=$2; shift;;
    -*) echo "REFUSED: unknown option $1 (known: --strict --refresh --keep --raw-dir FOLDER; a work folder whose name starts with - is not accepted)"; exit 2;;
    *) ARGS+=("$1");;
  esac; shift
done
[ "${#ARGS[@]}" -le 1 ] || { echo "REFUSED: more than one work folder given (${#ARGS[@]}); give none or one"; exit 2; }
# f8-r11 (review f8-r10 M2, F12): the variables that change WHAT is checked or HOW MANY cases run are refused (exit 2) when they are set, whatever the caller meant: a stray one must never make this script pass without the whole suite. The names only are printed, never a value.
# The test hooks of the nested failure tests are listed in the next block; these are the hooks of the other scripts.
for v in FC_CK TEST_TAKE_DEV TEST_TAKE_SCRIPT RV_DUMP RV_ONLY; do
  [ -z "${!v:-}" ] || { echo "REFUSED: $v is set. It is a test hook of selftest.py / test_take_check.sh and would change what this script checks; unset it (env -u $v bash run_all.sh)."; exit 2; }
done
[ -z "${FC_OUT:-}" ] || [ -n "${RUN_ALL_NESTED:-}" ] || { echo "REFUSED: FC_OUT is set. This script chooses the self-test output folder itself (only the nested failure tests set it); unset it."; exit 2; }
# f8-r11: names (never values) of environment variables that are removed so that a stray cloud, vendor, interpreter or shell-startup variable cannot reach the checks. One list, here.
SCRUBBED=""
# prefixes and exact names, one group per line (no alternation, so the repo word-list test finds no copy of any list here)
SCRUB_PREFIX=(AWS_ AZURE_ ARM_ GOOGLE_ GCP_ GCLOUD_ CLOUDSDK_
  ANTHROPIC_
  OPENAI_
  N8N_ HUBSPOT_ SLACK_ GITHUB_ GH_ GIT_ SMTP_ POSTGRES PGHOST PGPORT PGUSER PGPASSWORD PGDATABASE PGSERVICE PGOPTIONS PGSSL
  PYTHON)
SCRUB_NAME=(DATABASE_URL LD_PRELOAD LD_LIBRARY_PATH LD_AUDIT BASH_ENV ENV CDPATH GLOBIGNORE SHELLOPTS BASHOPTS PS4 IFS_DEBUG)
for v in $(compgen -e); do
  hit=""
  for x in "${SCRUB_PREFIX[@]}"; do case $v in "$x"*) hit=1;; esac; done
  for x in "${SCRUB_NAME[@]}"; do [ "$v" = "$x" ] && hit=1; done
  case $v in *_API_KEY) hit=1;; *_TOKEN) hit=1;; *_SECRET) hit=1;; *_PASSWORD) hit=1;; *_CREDENTIALS) hit=1;; esac
  case $v in PYTHONDONTWRITEBYTECODE) hit="";; PYTHONHASHSEED) hit="";; esac
  # f8-r12 (M3): the status of unset is checked. A variable that cannot be removed (SHELLOPTS and BASHOPTS are read-only in bash) is not reported as removed: the run is refused and the name is printed (never a value).
  [ -z "$hit" ] || { if unset "$v" 2>/dev/null; then SCRUBBED="$SCRUBBED $v"; else echo "REFUSED: the environment variable $v would change how this script runs and cannot be removed here; start the script without it (env -u $v bash run_all.sh)"; exit 2; fi; }
done
[ -z "$SCRUBBED" ] || echo "environment variables removed for this run (names only):$SCRUBBED"
# round 10d (Q: review f8-r10c): the test hooks are refused (not silently ignored) when RUN_ALL_NESTED is not set, so a stray variable in a person's shell can never change what is checked
# f8-r12 (M1): RUN_ALL_RAW is one of these hooks now (it used to be honoured by any run, so a stray value made --refresh write into any folder); a person or a test locks another folder with --raw-dir, and --refresh never writes anywhere but raw/ next to this script
if [ -z "${RUN_ALL_NESTED:-}" ]; then
  for v in RUN_ALL_TAKE_FLOWS RUN_ALL_DROP_LEAD RUN_ALL_PLANT_TCFAIL_FLOWS RUN_ALL_PLANT_TCFAIL_WANT RUN_ALL_RAW; do
    [ -z "${!v:-}" ] || { echo "REFUSED: $v is a test hook of the nested failure tests and is only honoured together with RUN_ALL_NESTED=1; unset it."; exit 2; }
  done
fi
# f8-r11 + f8-r12 (M3): RUN_ALL_NESTED is honoured only when RUN_ALL_PARENT_PID names a run of this script that is still alive AND is an ancestor of this process (its parent, or its parent through the time-limit command). It used to pass for any live process whose command line held run_all.sh, so a stray RUN_ALL_NESTED=1 could silently skip the four nested failure tests. Checked before anything is locked or written.
is_run_all_ancestor() { # PID: 0 when PID is an ancestor of this shell and its command line names run_all.sh
  local want=$1 p=$$ i
  [[ $want =~ ^[1-9][0-9]*$ ]] || return 1
  for i in 1 2 3 4 5 6; do
    p=$(sed -n 's/^PPid:[[:space:]]*//p' "/proc/$p/status" 2>/dev/null)
    [[ $p =~ ^[1-9][0-9]*$ ]] && [ "$p" -gt 1 ] || return 1
    if [ "$p" = "$want" ]; then tr '\0' ' ' < "/proc/$p/cmdline" 2>/dev/null | grep -q -F 'run_all.sh'; return $?; fi
  done
  return 1
}
if [ -n "${RUN_ALL_NESTED:-}" ]; then
  is_run_all_ancestor "${RUN_ALL_PARENT_PID:-}" || { echo "REFUSED: RUN_ALL_NESTED is set but RUN_ALL_PARENT_PID does not name a running run_all.sh that started this run. RUN_ALL_NESTED belongs to the nested test runs this script starts itself; unset it (env -u RUN_ALL_NESTED bash run_all.sh)."; exit 2; }
  [ -z "${RUN_ALL_RAW:-}" ] || RAWFINAL=$RUN_ALL_RAW   # honoured only here, in a nested test run
  [ -z "$REFRESH" ] || { echo "REFUSED: --refresh is not allowed in a nested test run"; exit 2; }
fi
# f8-r12 (M1): --refresh writes only into the raw/ folder next to this script (compared as physical paths; nothing is created by this check)
if [ -n "$REFRESH" ]; then
  [ "$(realpath -m -- "$RAWFINAL")" = "$(realpath -m -- "$HERE/raw")" ] || { echo "REFUSED: --refresh publishes only into $HERE/raw, but the raw folder of this run is $RAWFINAL; drop --raw-dir or --refresh"; exit 2; }
fi
# f8-r12 (m5): the folder for scratch files must be an absolute path to an existing writable folder (a relative one would point somewhere else after the script changes folder)
TMPROOT=${TMPDIR:-/tmp}
case $TMPROOT in /*) ;; *) echo "REFUSED: TMPDIR must be an absolute path (it is relative); unset it or give the full path"; exit 2;; esac
[ -d "$TMPROOT" ] && [ -w "$TMPROOT" ] || { echo "REFUSED: the scratch folder $TMPROOT (TMPDIR) is not a folder this script can write into"; exit 2; }
for v in pgrep timeout realpath; do command -v "$v" >/dev/null 2>&1 || { echo "REFUSED: $v is not installed; this script needs it to limit its steps and to stop the processes it starts"; exit 2; }; done
# round 10d (B4) + f8-r4 (M2): one run at a time per raw folder. The raw folder is shared, so two runs at once would overwrite each other's files and mix their results. The lock (flock) is taken on the raw FOLDER ITSELF (opened read-only; Linux allows a lock on a folder), after mkdir -p, and is held until this script ends. So the lock belongs to the physical folder: it does not depend on TMPDIR, on how the path is written (relative, absolute, through a symbolic link, with .. or a double slash) or on the current folder, and no lock file is left anywhere. A second run on the same raw folder is refused (exit 2).
command -v flock >/dev/null 2>&1 || { echo "REFUSED: flock is not installed, so this script cannot make sure that no second run uses the raw folder at the same time"; exit 2; }
mkdir -p -- "$RAWFINAL" || { echo "REFUSED: cannot make the raw folder $RAWFINAL"; exit 2; }
RAWABS=$(cd -- "$RAWFINAL" && pwd -P) || { echo "REFUSED: cannot enter the raw folder $RAWFINAL"; exit 2; }
exec 9< "$RAWABS" || { echo "REFUSED: cannot open the raw folder $RAWABS to lock it"; exit 2; }
flock -n 9 || { echo "REFUSED: another run_all.sh holds the lock for the raw folder $RAWABS; wait for it to end, or lock another folder (--raw-dir FOLDER)"; exit 2; }
[ -z "$LOCKONLY" ] || { echo "lock acquired: $RAWABS (--lock-only: nothing else was run)"; exit 0; }
RUN_ALL_SELF=$$   # the nested runs started below get this as RUN_ALL_PARENT_PID
# f8-r11: this run's own scratch folder for ALL raw output; never shared, removed at the end unless the run failed or --keep (never in the nested test runs)
RAW=$(mktemp -d "$TMPROOT/fc8raw.XXXXXX") || { echo "REFUSED: cannot make the scratch raw folder"; exit 2; }
W=""; MADE_W=""; WORKSTARTED=""
# f8-r12 (M2): every process this run started in the background (the nine checker runs, the four nested test runs) is stopped BEFORE any folder is removed, on a normal end, an abort, and on INT / TERM / HUP. Children are found through their parent id (pgrep -P) and stopped with all their descendants (SIGTERM, up to 5 s, then SIGKILL).
desc_of() { local c; for c in $(pgrep -P "$1" 2>/dev/null); do DESC+=("$c"); desc_of "$c"; done; }
reap_children() {
  DESC=(); local p i alive
  for p in $(jobs -p); do DESC+=("$p"); desc_of "$p"; done
  [ "${#DESC[@]}" -gt 0 ] || return 0
  kill -TERM "${DESC[@]}" 2>/dev/null
  for i in 1 2 3 4 5 6 7 8 9 10; do alive=0; for p in "${DESC[@]}"; do kill -0 "$p" 2>/dev/null && alive=1; done; [ "$alive" = 0 ] && break; sleep 0.5; done
  kill -KILL "${DESC[@]}" 2>/dev/null
  wait 2>/dev/null
  return 0
}
# f8-r12 (M2): a signal can arrive while a step runs with its output sent to a file (lim ... > file 2>&1); the handler would then write into that file. Descriptors 5 and 6 keep the real stdout and stderr, and the messages of the handlers and of cleanup use them.
exec 5>&1 6>&2
cleanup() {
  reap_children
  [ -z "$MADE_W" ] || rm -rf -- "$W"   # only a folder this script made itself (mktemp below)
  # keep the scratch raw folder when --keep, or when a run that had started its work ended with a status other than 0 (never in the nested test runs, which fail on purpose)
  if [ -n "${RAW:-}" ] && [ -d "$RAW" ]; then
    if [ -z "$KEEP" ] && { [ -n "${RUN_ALL_NESTED:-}" ] || [ -z "$WORKSTARTED" ] || [ "${RUN_ALL_RC:-1}" = 0 ]; }; then rm -rf -- "$RAW"; else echo "raw output of this run is kept in: $RAW   (it is not removed later by this script; delete it with rm -rf when it is no longer needed)" >&5; fi
  fi
}
trap cleanup EXIT
trap 'echo "INTERRUPTED (INT): stopping every process this run started" >&6; exit 130' INT
trap 'echo "INTERRUPTED (TERM): stopping every process this run started" >&6; exit 143' TERM
trap 'echo "INTERRUPTED (HUP): stopping every process this run started" >&6; exit 129' HUP
if [ -n "${ARGS[0]:-}" ]; then
  W=$(realpath -m -- "${ARGS[0]}") || { echo "REFUSED: cannot resolve the work folder ${ARGS[0]}"; exit 2; }   # f8-r12 (m5): absolute, so a later change of folder cannot move it
  if [ -e "$W" ] && [ -n "$(ls -A -- "$W" 2>/dev/null)" ]; then echo "REFUSED: $W exists and is not empty; this script never deletes a folder it did not make"; exit 2; fi
else
  W=$(mktemp -d "$TMPROOT/fc8.XXXXXX") || exit 2   # f8-r12 (m4): under TMPDIR like the raw folder, no longer a fixed /tmp
  MADE_W=1
fi
mkdir -p -- "$W/c/handover/demo/n8n-flows" "$W/c/handover/demo/n8n-mainframe" "$W/g" "$RAW" || exit 2
cp -- "$D"/n8n-flows/*.json "$D/n8n-flows/mf_leads.sql" "$D/n8n-flows/PAGE-STATEMENTS-V4.md" "$W/c/handover/demo/n8n-flows/" || exit 2
cp -- "$D/VIDEO-RUNSHEET.md" "$W/c/handover/demo/" && cp -- "$D/n8n-mainframe/build_mainframe.py" "$W/c/handover/demo/n8n-mainframe/" || exit 2
: > "$RAW/apply.log"; WORKSTARTED=1
# f8-r12 (M3, m3): git reads settings from the user and the machine (GIT_* variables are removed above; here also the global and system config files are switched off) and every status is checked (git init used to be followed by "; true")
GITENV=(env GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null GIT_CONFIG_NOSYSTEM=1)
( cd "$W/c" && "${GITENV[@]}" git init -q . ) >> "$RAW/apply.log" 2>&1 || { echo "ABORT: git init (see raw/apply.log)"; exit 3; }
for p in F-002-take-key-check-and-claim-error-path F-008-save-runs-for-the-take; do
  ( cd "$W/c" && "${GITENV[@]}" git apply --check "$PT/$p.patch" && "${GITENV[@]}" git apply "$PT/$p.patch" ) >> "$RAW/apply.log" 2>&1 || { echo "ABORT: git apply $p (see raw/apply.log)"; exit 3; }
  echo "applied $p" | tee -a "$RAW/apply.log"
done
cd "$W/c/handover/demo/n8n-mainframe" || exit 3
MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py "$W/g/real" PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER > "$RAW/gen-real.log" 2>&1 || { echo "ABORT gen real (raw/gen-real.log)"; exit 3; }
MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py "$W/g/film" PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 > "$RAW/gen-film.log" 2>&1 || { echo "ABORT gen film (raw/gen-film.log)"; exit 3; }
( set -o pipefail; cd "$W/g" && find . -type f | sort | while IFS= read -r f; do h=$(sha256sum -- "$f") || exit 1; printf '%s  %s\n' "${h:0:16}" "$f"; done ) > "$RAW/patched-flows-list.txt" || { echo "ABORT: the list of generated flow files could not be made (raw/patched-flows-list.txt)"; exit 3; }
cd "$HERE" || exit 3
DDLF="$D/n8n-flows-v4/mf_leads.sql"; DDLO=(); [ -f "$DDLF" ] && DDLO=(--ddl "$DDLF")
# f8-r12 (m7): argument lists are arrays (no word splitting of a text), so a folder name with a space cannot split an option
E=("${DDLO[@]}" --expect mf-recovery.json=10:9 --expect mf-sub-crm-mail.json=20:26 --expect-credential postgres=n8n-publish-pg --expect-credential smtp=mf-mail-smtp --expect-credential hubspotAppToken=hubspot-app-token "${STRICT_IDS[@]}")
ACC=(--accept-if mf-recovery.json=StuckRow:1 --accept-if mf-recovery.json=AlertRow:1 --accept-no-save mf-recovery.json)
STRICT=(--require-webhook-auth --block-env-access)
T0=$(date +%s)
# one background process per (state, mode, flow set); each writes its own file, ending with its own exit code line
run_set() { # name variant state(pristine|patched|bare) extra-args...
  name=$1; v=$2; state=$3; shift 3
  suffix=""; [ "$v" = film ] && suffix="-film"
  out="$RAW/$name$suffix.txt"
  {
    echo "######## $name $v"
    case $state in
      pristine) timeout -k 10 "$LIM_CHECKER" python3 -I "$CK" "$D/n8n-flows-$v-v5" "${ACC[@]}" --expect mf-form.json=12:11 --expect mf-hook.json=12:11 "${E[@]}" --table "$@";;
      patched)  timeout -k 10 "$LIM_CHECKER" python3 -I "$CK" "$W/g/$v" "${ACC[@]}" --expect mf-form.json=15:14 --expect mf-hook.json=15:14 "${E[@]}" --patch-checks F002,F008 --diff-base "$D/n8n-flows-$v-v5" --allow F002,F008 --diff-out "$RAW/diff-$v.txt" --table "$@";;
      bare)     timeout -k 10 "$LIM_CHECKER" python3 -I "$CK" "$D/n8n-flows-$v-v5" --expect mf-form.json=12:11 --expect mf-hook.json=12:11 --expect mf-recovery.json=10:9 --expect mf-sub-crm-mail.json=20:26 --quiet-info "$@";;
    esac
    echo "exit=$?"
  } > "$out" 2>&1
}
for v in real film; do
  run_set pristine $v pristine 9<&- &
  run_set patched $v patched 9<&- &
  run_set pristine-strict $v pristine "${STRICT[@]}" 9<&- &
  run_set patched-strict $v patched "${STRICT[@]}" 9<&- &
done
run_set pristine-no-baseline real bare 9<&- &
wait
T1=$(date +%s)
FC_OUT="${FC_OUT:-$W/selftest-out}" lim "$LIM_SELFTEST" python3 -I "$HERE/selftest.py" "$D/n8n-flows-real-v5" "$W/g/real" "$D/n8n-flows-film-v5" > "$RAW/selftest-new.txt" 2>&1; ST=$?
T2=$(date +%s)
# the take script itself: exit 0 and the lines the owner must see (a missing line sets this script's exit status to 1)
# the take runs on the PATCHED copy (F-002 and F-008 applied, lead answers Q17-4 and Q18): exit 0 required, and the run-saving block must hold ACCEPTED lines only (no WARN)
# round 10c (Q1): the committed take-warns.pin keeps the flows-audit reviewer line, so a bare take exits 4 ("pin not yet confirmed by the lead") until the lead edits it. This script tests the FILES, so it runs the take with a copy of the pin whose reviewer line is a stand-in (same WARN lines, same hash); the committed pin's own state is printed near the end.
STANDIN=$(timeout -k 10 "$LIM_TAKE" bash "$HERE/take_check.sh" --standin-name) && [ -n "$STANDIN" ] || { echo "ABORT: take_check.sh --standin-name gave no name (round f8-r8: the stand-in name and the word lists live in take_check.sh only)"; exit 3; }
PINDATE=$(sed -n 's/^# date (UTC): \([0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}\)$/\1/p' "$HERE/take-warns.pin" | head -n 1)   # round f8-r8: the stand-in line carries the pin's own date (never older than the pin), not the clock date
PINRCPT=$(sed -n 's/^# sha256 of the WARN lines below.*: \([0-9a-f]\{64\}\)$/\1/p' "$HERE/take-warns.pin" | head -n 1 | cut -c1-8)   # round f8-r9 (M1): the reviewer line carries the first 8 characters of the WARN-lines hash
mkdir -p "$W/tc" && { echo "# reviewed by: $STANDIN, ${PINDATE:-$(date -u +%Y-%m-%d)}, pin sha256 ${PINRCPT:-missing}"; grep -v '^# reviewed by' "$HERE/take-warns.pin"; } > "$W/tc/test-lead.pin"; TESTPIN="$W/tc/test-lead.pin"
lim "$LIM_TAKE" env "${TCUNSET[@]}" TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$TESTPIN" bash "$HERE/take_check.sh" --flows "${RUN_ALL_TAKE_FLOWS:-$W/g/real}" > "$RAW/take-check.txt" 2>&1; TC=$?   # round 10d (B3): this call has an override (the stand-in pin), so a pass is exit 5, never 0; exit 5 is what is required below   # --flows is the documented way for the folder; the pin override needs the test flag (round 10, M1)
TCMISS=""   # set BEFORE the first use below (round 7 fix: it used to be set after the first two checks, so a failing take script ended this script with "TCMISS: unbound variable" and the first two checks were thrown away)
# the FINAL line of take_check.sh must print the same number as its real exit status (a line that always says 0 would hide a failure)
grep -q -F "FINAL: take_check exit status $TC." "$RAW/take-check.txt" || TCMISS="$TCMISS [FINAL line does not print exit status $TC]"
grep -q -E "^WARN .*run-saving settings|^WARN accept-no-save" "$RAW/take-check.txt" && TCMISS="$TCMISS [a run-saving WARN on the patched copy]"
grep -q -F "ACCEPTED: recovery flow not part of the take (decision 4)" "$RAW/take-check.txt" || TCMISS="$TCMISS [ACCEPTED line for the recovery flow]"
for w in "RESULT: 0 FAIL," "WARN set equals the pinned set" "NOTHING RAN IN n8n" "READ THIS BLOCK BEFORE ANYTHING ELSE" "Query strings read AND compared:" "GATE BEFORE THE FIRST SEND" "Is saving of past runs off" "key check" "FINAL: take_check exit status"; do
  grep -q -F -- "$w" "$RAW/take-check.txt" || TCMISS="$TCMISS [$w]"
done
# lines that exist only while the checker itself reports the matching problem: required when it reports it, not otherwise (so this script can exit 0 on files that are fixed and filled)
grep -q -F "PLACEHOLDERS IN NODE SETTINGS" "$RAW/pristine.txt" && { grep -q -F "PLACEHOLDERS IN NODE SETTINGS" "$RAW/take-check.txt" || TCMISS="$TCMISS [PLACEHOLDERS IN NODE SETTINGS]"; }
grep -q -F "CREDENTIAL IDS STILL PLACEHOLDERS" "$RAW/pristine.txt" && { grep -q -F "CREDENTIAL IDS STILL PLACEHOLDERS" "$RAW/take-check.txt" || TCMISS="$TCMISS [CREDENTIAL IDS STILL PLACEHOLDERS]"; }
grep -q -F "STEPS THAT READ ENVIRONMENT VARIABLES" "$RAW/pristine.txt" && { grep -q -F "STEPS THAT READ ENVIRONMENT VARIABLES" "$RAW/take-check.txt" || TCMISS="$TCMISS [STEPS THAT READ ENVIRONMENT VARIABLES]"; }
for f in mf-form.json mf-hook.json; do grep -q -F "$f: key check" "$RAW/take-check.txt" || TCMISS="$TCMISS [key check line for $f]"; done
grep -q -F "SQL COLUMNS NOT CHECKED" "$RAW/take-check.txt" && TCMISS="$TCMISS [columns not checked]"
grep -q -F "deleted at clean-up" "$RAW/take-check.txt" && TCMISS="$TCMISS [the take output promises 'deleted at clean-up' (the take never deletes anything)]"
grep -q -E "^  combined: [0-9a-f]{64}$" "$RAW/take-check.txt" || TCMISS="$TCMISS [the sha256 of the four flow files is not printed in the top block]"
grep -q -E "^FINAL: .*Flow files sha256 \(four files, combined\): [0-9a-f]{64}\." "$RAW/take-check.txt" || TCMISS="$TCMISS [the sha256 of the four flow files is not printed in the FINAL line]"
grep -q -F "!!!" "$RAW/take-check.txt" && TCMISS="$TCMISS [a !!! line: the take script found a table or column problem]"
# take_check.sh failure exits (each must be 4 with its own loud line): table file missing, old table without the alert columns, no query text to read
mkdir -p "$W/tc" && cp -r -- "$W/g/real" "$W/tc/noquery" || TCMISS="$TCMISS [could not make the no-query test folder]"
python3 -I - "$W/tc/noquery" <<'PYEOF' || TCMISS="$TCMISS [no-query test folder not built]"
import glob, json, sys
for p in glob.glob(sys.argv[1] + "/*.json"):
    j = json.load(open(p, encoding="utf-8"))
    for n in j["nodes"]:
        n.get("parameters", {}).pop("query", None)
    json.dump(j, open(p, "w", encoding="utf-8"))
PYEOF
tcfail() { # name expected-line env-assignments...
  nm=$1; want=$2; shift 2
  # round 10c (Q4): clean TAKE_CHECK_* environment (env -u), the stand-in pin by default (a case may give its own TAKE_CHECK_WARN_PIN after it), TAKE_CHECK_TEST=1 = the documented test flag (round 10, M1)
  lim "$LIM_TAKE" env "${TCUNSET[@]}" TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$TESTPIN" "$@" bash "$HERE/take_check.sh" > "$RAW/take-check-$nm.txt" 2>&1; x=$?
  # f8-r4 (A2): the stand-in pin names the flows sha256 of the PATCHED folder, so a planted fault in another folder would be exit 4 for that reason alone and the case would prove nothing. Unless the case gives its own pin, the run is repeated with a copy of the stand-in pin whose flows sha256 line holds the sha of the folder that was run (read from the first output), so the exit 4 has to come from the planted fault; the output must then NOT contain the flows-sha mismatch line.
  case " $* " in *" TAKE_CHECK_WARN_PIN="*) ;; *)
    fsha=$(grep -m 1 -E '^  combined: [0-9a-f]{64}$' "$RAW/take-check-$nm.txt" | sed 's/^  combined: //')
    if [ -n "$fsha" ]; then
      sed "s/^\(# flows sha256 .*: \)[0-9a-f]\{64\}\$/\1$fsha/" "$TESTPIN" > "$W/tc/pin-$nm.pin"
      lim "$LIM_TAKE" env "${TCUNSET[@]}" TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$W/tc/pin-$nm.pin" "$@" bash "$HERE/take_check.sh" > "$RAW/take-check-$nm.txt" 2>&1; x=$?
      if grep -q -F "THE FLOW FILES DO NOT MATCH THE SHA-256" "$RAW/take-check-$nm.txt"; then TCMISS="$TCMISS [take_check $nm: the exit 4 still comes partly from the flows sha256 mismatch although the pin was matched to the folder]"; fi
    else TCMISS="$TCMISS [take_check $nm: no flows sha256 in the first output, the case cannot be matched to a pin]"; fi;;
  esac
  first=$(grep -m 1 -E '^FAIL ' "$RAW/take-check-$nm.txt" | cut -c1-240); [ -n "$first" ] || first=$(grep -m 1 -E '^!!! ' "$RAW/take-check-$nm.txt" | cut -c1-240); first=${first:-none}   # a FAIL (a definite fault in a file) is shown before a !!! line (a problem of this script)
  # say which condition failed and show the first FAIL or !!! line of the raw output (the output file is written by the redirect above, so no guess about another run is made)
  if [ "$x" != 4 ]; then TCMISS="$TCMISS [take_check $nm: want exit 4, got exit $x; first FAIL or !!! line of $RAW/take-check-$nm.txt: $first]"
  elif [ ! -s "$RAW/take-check-$nm.txt" ]; then TCMISS="$TCMISS [take_check $nm: exit 4 but the output file $RAW/take-check-$nm.txt is empty]"
  else
    # round 10d (A2): the wanted text must be on a line that starts with "!!! " or "FAIL " (the loud lines), not on any line: a line printed for another reason must not satisfy a case
    grep -E '^(FAIL|!!!) ' "$RAW/take-check-$nm.txt" | grep -q -F -- "$want" || TCMISS="$TCMISS [take_check $nm: exit 4 but the text '$want' is not on a !!! or FAIL line; first FAIL or !!! line: $first]"
    grep -q -F "FINAL: take_check exit status 4." "$RAW/take-check-$nm.txt" || TCMISS="$TCMISS [take_check $nm: exit 4 but the FINAL line does not say 4; first FAIL or !!! line: $first]"
  fi
}
# Q18: the take on the patched copy with ONE run-saving fault planted: each must be exit 4 with its own loud line (the checker must not hide it)
for nm in form-off sub-off rec-saves; do cp -r -- "$W/g/real" "$W/tc/$nm" || TCMISS="$TCMISS [could not make the $nm test folder]"; done
python3 -I - "$W/tc" <<'PYEOF' || TCMISS="$TCMISS [run-saving test folders not built]"
import json, sys
def edit(folder, fn, **kw):
    p = f"{sys.argv[1]}/{folder}/{fn}"
    j = json.load(open(p, encoding="utf-8"))
    j["settings"].update(kw)
    json.dump(j, open(p, "w", encoding="utf-8"))
edit("form-off", "mf-form.json", saveDataSuccessExecution="none", saveDataErrorExecution="none")
edit("sub-off", "mf-sub-crm-mail.json", saveDataSuccessExecution="none", saveDataErrorExecution="none")
edit("rec-saves", "mf-recovery.json", saveDataSuccessExecution="all", saveDataErrorExecution="all", saveManualExecutions=True)
PYEOF
# Q18 extras: (1) key check reads the node list, not any text; (2) checker exit 2 and 3 through take_check.sh give the "no verdict" line and the same exit status
cp -r -- "$W/g/real" "$W/tc/keyok-gone" || TCMISS="$TCMISS [could not make keyok-gone folder]"
python3 -I - "$W/tc/keyok-gone/mf-form.json" <<'PYEOF' || TCMISS="$TCMISS [keyok-gone not built]"
import json, sys
p = sys.argv[1]
j = json.load(open(p, encoding="utf-8"))
j["nodes"] = [n for n in j["nodes"] if n["name"] != "KeyOk"]   # the connections that name KeyOk stay: the old text match still saw "KeyOk" there
json.dump(j, open(p, "w", encoding="utf-8"))
PYEOF
lim "$LIM_TAKE" env "${TCUNSET[@]}" TAKE_CHECK_TEST=1 TAKE_CHECK_FLOWS="$W/tc/keyok-gone" TAKE_CHECK_FORM_EXPECT=15:14 bash "$HERE/take_check.sh" > "$RAW/take-check-keyok-gone.txt" 2>&1
grep -q -F "mf-form.json: key check ABSENT" "$RAW/take-check-keyok-gone.txt" && ! grep -q -F "mf-form.json: key check present" "$RAW/take-check-keyok-gone.txt" || TCMISS="$TCMISS [take_check: a removed KeyOk node must print 'key check ABSENT' for mf-form.json]"
printf '\377\376 not utf-8 \200\n' > "$W/tc/bad-ddl.sql"
printf 'import sys\nsys.exit(3)\n' > "$W/tc/exit3.py"
for pair in "2:bad-ddl:TAKE_CHECK_DDL=$W/tc/bad-ddl.sql" "3:exit3:TAKE_CHECK_CK=$W/tc/exit3.py"; do
  want=${pair%%:*}; rest=${pair#*:}; nm=${rest%%:*}; assign=${rest#*:}
  lim "$LIM_TAKE" env "${TCUNSET[@]}" "$assign" TAKE_CHECK_TEST=1 TAKE_CHECK_FLOWS="$W/g/real" TAKE_CHECK_FORM_EXPECT=15:14 bash "$HERE/take_check.sh" > "$RAW/take-check-$nm.txt" 2>&1; x=$?
  [ "$x" = "$want" ] && grep -q -F "THE CHECKER DID NOT GIVE A VERDICT (its exit status is $want" "$RAW/take-check-$nm.txt" && grep -q -F "FINAL: take_check exit status $want." "$RAW/take-check-$nm.txt" || TCMISS="$TCMISS [take_check $nm: want exit $want and the no-verdict line, got exit $x]"
done
# (3) the saving-ON flows must be named in the top block with their reason (INFO), not shown silently
[ "$(grep -c '^INFO: mf-.* run saving is ON' "$RAW/take-check.txt")" = 3 ] || TCMISS="$TCMISS [take_check: want 3 INFO lines saying run saving is ON on purpose (form, hook, sub-workflow)]"
# Round 9 (review f8-design-r3), each case below must fail on the round-8 take_check.sh:
# M2: run saving must be exactly all / all / True on every flow except the recovery flow (an odd word, a missing key, an empty settings block)
# M3: a patched copy without the F-002 key check (only F-008 applied) must be exit 4
# M1: the set of WARN lines is pinned (a new WARN, a missing pin file) and a disabled external-call node is a FAIL
for nm in form-odd sub-nokey hook-emptyset warn-new; do cp -r -- "$W/g/real" "$W/tc/$nm" || TCMISS="$TCMISS [could not make the $nm test folder]"; done
cp -r -- "$D/n8n-flows-real-v5" "$W/tc/f008-only-src" || TCMISS="$TCMISS [could not make the f008-only source]"
python3 -I - "$W/tc" <<'PYEOF' || TCMISS="$TCMISS [round 9 test folders not built]"
import json, sys
def load(folder, fn):
    return f"{sys.argv[1]}/{folder}/{fn}", json.load(open(f"{sys.argv[1]}/{folder}/{fn}", encoding="utf-8"))
def save(p, j):
    json.dump(j, open(p, "w", encoding="utf-8"))
p, j = load("form-odd", "mf-form.json"); j["settings"]["saveDataSuccessExecution"] = "off"; save(p, j)
p, j = load("sub-nokey", "mf-sub-crm-mail.json"); del j["settings"]["saveManualExecutions"]; save(p, j)
p, j = load("hook-emptyset", "mf-hook.json"); j["settings"] = {}; save(p, j)
p, j = load("warn-new", "mf-sub-crm-mail.json")
for n in j["nodes"]:
    if n["name"] == "MarkDone":
        n["maxTries"] = 3   # a plain WARN: maxTries is ignored without retryOnFail
save(p, j)
# a patched copy that has F-008 but NOT F-002: the committed unpatched flows with run saving switched on (all / all / True) on the three flows that need it
for fn in ("mf-form.json", "mf-hook.json", "mf-sub-crm-mail.json"):
    p, j = load("f008-only-src", fn)
    j.setdefault("settings", {}).update(saveDataSuccessExecution="all", saveDataErrorExecution="all", saveManualExecutions=True)
    save(p, j)
PYEOF
cp -r -- "$W/g/real" "$W/tc/disabled-send" && python3 -I - "$W/tc/disabled-send/mf-sub-crm-mail.json" <<'PYEOF' || TCMISS="$TCMISS [disabled-send test folder not built]"
import json, sys
p = sys.argv[1]
j = json.load(open(p, encoding="utf-8"))
for n in j["nodes"]:
    if n["name"] == "SendMail":
        n["disabled"] = True
json.dump(j, open(p, "w", encoding="utf-8"))
PYEOF
tcfail form-run-saving-odd-word "RUN SAVING IS NOT EXACTLY all / all / True" TAKE_CHECK_FLOWS="$W/tc/form-odd"
tcfail sub-run-saving-key-missing "RUN SAVING IS NOT EXACTLY all / all / True" TAKE_CHECK_FLOWS="$W/tc/sub-nokey"
tcfail hook-run-saving-block-empty "RUN SAVING IS NOT EXACTLY all / all / True" TAKE_CHECK_FLOWS="$W/tc/hook-emptyset"
tcfail key-check-absent-is-exit-4 "The take needs F-002: this script exits 4" TAKE_CHECK_FLOWS="$W/tc/f008-only-src"
tcfail new-warn-changes-the-pin "THE WARN SET CHANGED against take-warns.pin" TAKE_CHECK_FLOWS="$W/tc/warn-new"
tcfail warn-pin-file-missing "THE WARN BASELINE FILE IS MISSING" TAKE_CHECK_FLOWS="$W/g/real" TAKE_CHECK_WARN_PIN="$W/tc/no-such.pin"
lim "$LIM_TAKE" env "${TCUNSET[@]}" bash "$HERE/take_check.sh" --flows "$W/tc/disabled-send" > "$RAW/take-check-disabled-send.txt" 2>&1; x=$?
[ "$x" = 1 ] && grep -q -F "is an external-call node and is disabled" "$RAW/take-check-disabled-send.txt" || TCMISS="$TCMISS [take_check disabled-send: want exit 1 and the disabled external-call FAIL, got exit $x]"
# Round 10 (review f8-r10): the take-level shell test (B1 pin writing, M1 overrides, M3 flow that is not a file, M4 pin hash, count change without an orphan) lives in test_take_check.sh; it runs on a temporary copy
lim "$LIM_SUITE" bash "$HERE/test_take_check.sh" "$W/g/real" "$W/tc/ttc" > "$RAW/test-take-check.txt" 2>&1; TT=$?
[ "$TT" = 0 ] || TCMISS="$TCMISS [test_take_check.sh exit $TT (see raw/test-take-check.txt)]"
grep -q -x -F "script under test: $HERE/take_check.sh" "$RAW/test-take-check.txt" || TCMISS="$TCMISS [test_take_check.sh did not print 'script under test: $HERE/take_check.sh' (round f8-r9: a leaked TEST_TAKE_SCRIPT must be visible)]"
tcfail unpatched-run-saving "A FLOW THAT THE TAKE USES HAS RUN SAVING OFF"
tcfail form-run-saving-off "A FLOW THAT THE TAKE USES HAS RUN SAVING OFF" TAKE_CHECK_FLOWS="$W/tc/form-off" TAKE_CHECK_FORM_EXPECT=15:14
grep -q -F "WARN mf-form.json this flow's run-saving settings" "$RAW/take-check-form-run-saving-off.txt" || TCMISS="$TCMISS [take_check form-run-saving-off: the file-specific WARN line for mf-form.json is missing]"
tcfail sub-run-saving-off "A FLOW THAT THE TAKE USES HAS RUN SAVING OFF" TAKE_CHECK_FLOWS="$W/tc/sub-off" TAKE_CHECK_FORM_EXPECT=15:14
grep -q -F "WARN mf-sub-crm-mail.json this flow's run-saving settings" "$RAW/take-check-sub-run-saving-off.txt" || TCMISS="$TCMISS [take_check sub-run-saving-off: the file-specific WARN line for mf-sub-crm-mail.json is missing]"
tcfail recovery-accept-idle "THE RECOVERY FLOW IS NOT PRINTED AS ACCEPTED" TAKE_CHECK_FLOWS="$W/tc/rec-saves" TAKE_CHECK_FORM_EXPECT=15:14
grep -q -F "WARN accept-no-save --accept-no-save mf-recovery.json excused nothing" "$RAW/take-check-recovery-accept-idle.txt" || TCMISS="$TCMISS [take_check recovery-accept-idle: the file-specific WARN line is missing]"
tcfail no-table-file "THE TABLE FILE IS MISSING" TAKE_CHECK_FLOWS="$W/g/real" TAKE_CHECK_DDL="$W/tc/does-not-exist.sql"
tcfail old-table "A COLUMN OR TABLE IS MISSING" TAKE_CHECK_FLOWS="$W/g/real" TAKE_CHECK_DDL="$D/n8n-flows/mf_leads.sql"
tcfail zero-queries "0 QUERY STRINGS WERE READ" TAKE_CHECK_FLOWS="$W/tc/noquery"
# Round 7: a failing take script must give a clean report, not a crash. A second run of this script is made on a copy whose form flow has run saving off:
# its take check exits 4, so the nested run must end with exit status 1, show "take_check.sh exit=4" and a named missing line, and must not crash ("unbound variable").
# Round 10c: two more nested runs, started in parallel with the first. (Q3) RUN_ALL_DROP_LEAD=1 hides the OPEN LEAD DECISIONS line while everything else is fine: the printed run_all exit status must be 1 (the old script printed 0 and then exited 1).
# (Q4) a caller that exported TAKE_CHECK_* variables must not change any result, and a take case that goes wrong must print its first FAIL or !!! line: RUN_ALL_PLANT_TCFAIL_FLOWS points one extra case at a folder with a disabled mail step (exit 1, a FAIL line).
if [ -z "${RUN_ALL_NESTED:-}" ]; then
  mkdir -p "$W/tc/nested-raw" "$W/tc/nested-raw-b" "$W/tc/nested-raw-c" "$W/tc/nested-raw-d"
  RUN_ALL_NESTED=1 RUN_ALL_PARENT_PID=$RUN_ALL_SELF RUN_ALL_RAW="$W/tc/nested-raw" RUN_ALL_TAKE_FLOWS="$W/tc/form-off" FC_OUT="$W/tc/nested-selftest-out" timeout -k 10 "$LIM_NESTED" bash "$HERE/run_all.sh" "$W/tc/nested-work" 9<&- > "$W/tc/nested.txt" 2>&1 & NPID=$!
  RUN_ALL_NESTED=1 RUN_ALL_PARENT_PID=$RUN_ALL_SELF RUN_ALL_DROP_LEAD=1 RUN_ALL_RAW="$W/tc/nested-raw-b" FC_OUT="$W/tc/nested-selftest-out-b" timeout -k 10 "$LIM_NESTED" bash "$HERE/run_all.sh" "$W/tc/nested-work-b" 9<&- > "$W/tc/nested-b.txt" 2>&1 & NPIDB=$!
  TAKE_CHECK_TEST=1 TAKE_CHECK_DDL="$W/tc/does-not-exist.sql" TAKE_CHECK_WARN_PIN="$W/tc/does-not-exist.pin" TAKE_CHECK_FLOWS="$W/tc/does-not-exist" RUN_ALL_NESTED=1 RUN_ALL_PARENT_PID=$RUN_ALL_SELF RUN_ALL_PLANT_TCFAIL_FLOWS="$W/tc/disabled-send" RUN_ALL_RAW="$W/tc/nested-raw-c" FC_OUT="$W/tc/nested-selftest-out-c" timeout -k 10 "$LIM_NESTED" bash "$HERE/run_all.sh" "$W/tc/nested-work-c" 9<&- > "$W/tc/nested-c.txt" 2>&1 & NPIDC=$!
  # round 10d (A2): the planted case wants a text that IS printed (the title line of the take) but not on a !!! or FAIL line, in a take that exits 4 for another reason: tcfail must still report it
  RUN_ALL_NESTED=1 RUN_ALL_PARENT_PID=$RUN_ALL_SELF RUN_ALL_PLANT_TCFAIL_FLOWS="$W/tc/form-off" RUN_ALL_PLANT_TCFAIL_WANT="NOTHING RAN IN n8n" RUN_ALL_RAW="$W/tc/nested-raw-d" FC_OUT="$W/tc/nested-selftest-out-d" timeout -k 10 "$LIM_NESTED" bash "$HERE/run_all.sh" "$W/tc/nested-work-d" 9<&- > "$W/tc/nested-d.txt" 2>&1 & NPIDD=$!
  wait "$NPID"; NX=$?; wait "$NPIDB"; NXB=$?; wait "$NPIDC"; NXC=$?; wait "$NPIDD"; NXD=$?
  for nf in nested nested-b nested-c nested-d; do nr=$(grep -m 1 '^REFUSED' "$W/tc/$nf.txt" 2>/dev/null | cut -c1-200); [ -z "$nr" ] || TCMISS="$TCMISS [nested run $nf was REFUSED: $nr (its raw folder: $W/tc/nested-raw*; a refusal there exits 2, not the exit the checks below want)]"; done   # f8-r9 (second angle M2): say so, do not only fail the exit-status check
  [ "$NX" = 1 ] && grep -q -F "[take_check.sh exit=4] missing lines:" "$W/tc/nested.txt" && grep -q -F "run_all exit status (real-v5 default runs + self-test): 1" "$W/tc/nested.txt" && ! grep -q -i "unbound variable" "$W/tc/nested.txt" || TCMISS="$TCMISS [nested run with a failing take check: want exit 1, a clean 'take_check.sh exit=4' report and no crash, got exit $NX]"
  [ "$NXB" = 1 ] && grep -q -F "run_all exit status (real-v5 default runs + self-test): 1" "$W/tc/nested-b.txt" && grep -q -F "OPEN LEAD DECISIONS (real-v5, the take): unknown" "$W/tc/nested-b.txt" && grep -q -F "[take_check.sh exit=5] missing lines: none" "$W/tc/nested-b.txt" || TCMISS="$TCMISS [nested run without the OPEN LEAD DECISIONS line: want real exit 1 AND the printed run_all exit status 1, got exit $NXB (see nested-take-failure-b.txt)]"
  [ "$NXC" = 1 ] && grep -q -F "[take_check.sh exit=5] missing lines: [take_check planted: want exit 4, got exit 1; first FAIL or !!! line of" "$W/tc/nested-c.txt" && grep -q -F "is an external-call node and is disabled" "$W/tc/nested-c.txt" && ! grep -q -F "does-not-exist" "$W/tc/nested-c.txt" || TCMISS="$TCMISS [nested run with exported TAKE_CHECK_* variables and one planted take case: want a clean take (exit=0), only the planted case missing, with its first FAIL line shown, got exit $NXC (see nested-take-failure-c.txt)]"
  [ "$NXD" = 1 ] && grep -q -F "[take_check planted: exit 4 but the text 'NOTHING RAN IN n8n' is not on a !!! or FAIL line" "$W/tc/nested-d.txt" || TCMISS="$TCMISS [nested run with a planted wanted text on a non-loud line: want exit 1 and the 'not on a !!! or FAIL line' report, got exit $NXD (see nested-take-failure-d.txt)]"
  for nf in nested-d:nested-take-failure-d nested:nested-take-failure nested-b:nested-take-failure-b nested-c:nested-take-failure-c; do   # f8-r12 (m3): a failed copy is reported, not hidden
    cp -- "$W/tc/${nf%%:*}.txt" "$RAW/${nf#*:}.txt" || TCMISS="$TCMISS [could not save the output of nested run ${nf%%:*} as raw/${nf#*:}.txt]"
  done
fi
# the take runs of the nested cases that must not be affected by the caller's variables: the caller's TAKE_CHECK_* above point at files that do not exist
[ -n "${RUN_ALL_NESTED:-}" ] && [ -n "${RUN_ALL_PLANT_TCFAIL_FLOWS:-}" ] && tcfail planted "${RUN_ALL_PLANT_TCFAIL_WANT:-this line is never printed}" TAKE_CHECK_FLOWS="$RUN_ALL_PLANT_TCFAIL_FLOWS"
echo "checker runs wall time: $((T1-T0)) s; self-test wall time: $((T2-T1)) s" | tee "$RAW/timing.txt"
RC=0
for f in pristine patched; do   # gating: real-v5 default mode, exactly one exit line each
  [ "$(grep -c '^exit=' "$RAW/$f.txt")" = 1 ] || RC=1
  for x in $(grep -h '^exit=' "$RAW/$f.txt" | cut -d= -f2); do [ "$x" = 0 ] || RC=1; done
done
for f in pristine-strict patched-strict; do   # real-v5 strict: 0 or 1 are both fine, anything else (a crash) is not
  [ "$(grep -c '^exit=' "$RAW/$f.txt")" = 1 ] || RC=1
  for x in $(grep -h '^exit=' "$RAW/$f.txt" | cut -d= -f2); do case $x in 0|1) ;; *) RC=1;; esac; done
done
[ "$ST" = 0 ] || RC=1
[ "$TC" = 5 ] && [ -z "$TCMISS" ] || RC=1   # 5 = a would-be pass of a take call that has the test override (stand-in pin)
show() { for f in "$@"; do echo "[$f]"; grep -h -E '^(######## |exit=|RESULT|Known open problems)' "$RAW/$f.txt"; done; }
echo "==== real-v5 (THE TAKE) ===="
echo "---- default mode must be exit 0; strict mode shows what the owner's two open decisions would do ----"
show pristine patched pristine-strict patched-strict
echo "[pristine-no-baseline] (information only: no excuse for the 2 IF gaps; exit 1 with 2 FAIL is expected)"; grep -h -E '^(exit=|RESULT)' "$RAW/pristine-no-baseline.txt"
echo "==== film-v5 (NOT FOR THE TAKE; shown only, not gating, not added to the real-v5 numbers) ===="
show pristine-film patched-film pristine-strict-film patched-strict-film
STLINE=$(grep -h -m 1 -E '^SELFTEST: [0-9]+ as expected, [0-9]+ not as expected, [0-9]+ skipped \(not applicable\)$' "$RAW/selftest-new.txt")   # round 10d: the summary line by its text, not the last line of the file; f8-r12 (m1): by the same full pattern that count_check counts and parses, so the printed line and the checked line are one line
[ -n "$STLINE" ] || { STLINE="SELFTEST summary line missing in raw/selftest-new.txt"; RC=1; }
echo "[selftest exit=$ST] $STLINE"
CNTMSG=$(count_check "$RAW/selftest-new.txt" "$RAW/test-take-check.txt") || RC=1   # f8-r11 (review f8-r10 M2, F12): both case counts are pinned in expected-counts.pin; a drift fails loudly
echo "$CNTMSG"
[ "$ST" = 0 ] || tail -n 5 "$RAW/selftest-new.txt" 2>/dev/null | cut -c1-300 | sed 's/^/  selftest tail: /'   # f8-r11: a failing self-test shows where its output ended
echo "[take_check.sh exit=$TC] missing lines:${TCMISS:- none}"
[ "$TT" = 0 ] || grep -h '^FAIL' "$RAW/test-take-check.txt" 2>/dev/null | head -n 8 | cut -c1-300 | sed 's/^/  take suite: /'   # f8-r11: a failing take suite shows which cases failed (nested runs delete their raw folder, so this is the only trace)
LW=$(grep -h '^OPEN LEAD DECISIONS:' "$RAW/pristine.txt" | sed -E 's/OPEN LEAD DECISIONS: ([0-9]+) webhook.* ([0-9]+) \$env.*/\1 \2/')
[ -n "${RUN_ALL_NESTED:-}" ] && [ -n "${RUN_ALL_DROP_LEAD:-}" ] && LW=""   # test hook (round 10c, Q3)
# round 10c (Q3): RC is final BEFORE it is printed; the printed status is the real exit status
case $LW in
  [0-9]*\ [0-9]*) LEADMSG="OPEN LEAD DECISIONS (real-v5, the take): ${LW% *} webhook(s) without auth, ${LW#* } \$env node(s); n8n's env-access setting is NOT visible to any static check";;
  *) LEADMSG="OPEN LEAD DECISIONS (real-v5, the take): unknown (the real-v5 checker run did not finish; see raw/pristine.txt)"; RC=1;;
esac
PINREV=$(sed -n 's/^# reviewed by: \(.*\)$/\1/p' "$HERE/take-warns.pin" | head -n 1)
PINSHOWN=$(timeout -k 10 "$LIM_TAKE" bash "$HERE/take_check.sh" --safe-text "$PINREV")   # round f8-r8: the word rules (session, lead to confirm, placeholder, stand-ins, hidden characters) are asked of take_check.sh, never copied here
if [ -z "$PINREV" ]; then PINMSG="COMMITTED PIN (take-warns.pin) has no reviewer line. NOT confirmed by the lead: a bare take_check.sh exits 4 until the lead adds one (this run used a stand-in line, so its take check could pass)."
elif PINWHY=$(env -u TAKE_CHECK_TEST -u TAKE_CHECK_WARN_PIN timeout -k 10 "$LIM_TAKE" bash "$HERE/take_check.sh" --check-reviewer-line "$PINREV" "$PINDATE" "${PINRCPT:-nohash!!}"); then PINMSG="COMMITTED PIN (take-warns.pin) reviewer line (hidden characters removed, cut at 300): '$PINSHOWN' (this script cannot tell who really read it)."
else PINMSG="COMMITTED PIN (take-warns.pin) reviewer line (hidden characters removed, cut at 300): '$PINSHOWN'. NOT confirmed by the lead: take_check.sh refuses it ($(printf '%s' "$PINWHY" | cut -c1-120)), so a bare take_check.sh exits 4 until the lead replaces that line (this run used a stand-in line, so its take check could pass)."; fi
[ -n "$STLINE" ] && [ "${STLINE#SELFTEST summary line missing}" != "$STLINE" ] && { echo "  selftest output (last 5 lines of $RAW/selftest-new.txt):"; tail -n 5 "$RAW/selftest-new.txt" 2>/dev/null | cut -c1-300 | sed 's/^/    /'; }
# f8-r11: publish into the tracked raw/ folder only when asked, only at the very end, each file under a temporary name and then renamed
# f8-r12 (m3b, m6): the publish is done BEFORE the status line, so the printed status is the real exit status (a failed copy used to be printed after "0"); a run that did not pass (RC not 0) publishes nothing, so raw/ never holds the files of a failed run
PUBMSG=""
if [ -n "$REFRESH" ]; then
  if [ "$RC" != 0 ]; then PUBMSG="raw/ was NOT refreshed: this run did not pass (its raw files are kept in $RAW)"
  elif PUBN=$(publish_raw "$RAW" "$RAWABS"); then PUBMSG="raw files refreshed in $RAWABS: $PUBN (listed with their sha256 in refresh-manifest.txt)"
  else RC=1; PUBMSG="raw files refreshed in $RAWABS: NOT all copied (${PUBN:-0} copied); the run fails"; fi
else
  PUBMSG="tracked raw folder $RAWABS was NOT changed (pass --refresh to publish this run's raw files)"
fi
echo "run_all exit status (real-v5 default runs + self-test): $RC"
echo "real-v5 placeholder ids: $(grep -c 'still placeholders' "$RAW/pristine.txt") file(s) warn in the committed flows (pass --strict to make that a failure)"
echo "$PINMSG"
echo "$LEADMSG"
echo "$PUBMSG"
RUN_ALL_RC=$RC
exit $RC
