#!/usr/bin/env bash
# Start the demo mail/CRM server and the desk in the background (Linux).
# Usage: bash scripts/start_all.sh [keyed|blind]     (default keyed). Run from the repository root.
# Needs bash (it uses [[ ]]): `sh scripts/start_all.sh` fails where sh is dash.
# Ports and paths come from the desk configuration (DESK_* environment variables), not from this file.
# Demo defaults, each used only when you did not set that variable (a value you set, even an empty one, is kept): DESK_LEADFLOW_FILE
# is demo_only/leadflow.json, which turns on the lead owner, the lead stage and the reminder; and, unless DESK_LEADFLOW_FILE is
# off or empty, DESK_NUDGE_TO is reminder@example.test. To turn them off, set DESK_LEADFLOW_FILE=off.
# Logs and process ids go under the folder that holds the database file (git-ignored).
set -eu
# a feature test, not the name BASH_VERSION (dash takes any variable from the environment): only a shell that runs [[ ]] passes
case "$( (eval '[[ a == a ]]') 2>/dev/null && echo bash)" in bash) ;; *) echo "refused: run this script with bash (bash scripts/start_all.sh); this shell is not bash, so its [[ ]] tests would not work and a safety check could be skipped" >&2; exit 2 ;; esac
mode="${1:-keyed}"
case "$mode" in keyed|blind) ;; *) echo "refused: the mode must be keyed or blind" >&2; exit 2 ;; esac
export PYTHONPATH="src:."
export DESK_LEADFLOW_FILE="${DESK_LEADFLOW_FILE-demo_only/leadflow.json}"
if [[ "$DESK_LEADFLOW_FILE" != off ]] && [[ -n "$DESK_LEADFLOW_FILE" ]]; then export DESK_NUDGE_TO="${DESK_NUDGE_TO-reminder@example.test}"; fi
# a bad DESK_* value ends with the desk's one refusal line and exit code 4, not a Python traceback
# (scripts/desk_setting.py)
desk_setting() {
  local out rc=0
  out="$(python scripts/desk_setting.py "$1")" || rc=$?
  if [[ "$rc" -ne 0 ]]; then printf '%s\n' "$out" >&2; exit "$rc"; fi
  printf '%s\n' "$out"
}
data_dir="$(desk_setting data-dir)"
fakes_port="$(desk_setting fakes-port)"
# every setting is read BEFORE anything is started, so a failed read cannot leave a started program behind
tries="$(desk_setting start-tries)"
pause="$(desk_setting start-pause)"
desk_port="$(desk_setting port)"
# the folder cannot be made (a read-only place, a system folder): the desk's refusal line and exit code 4, no typed path
mkdir -p "$data_dir" 2>/dev/null || {
  echo "the desk refuses to start: the lead book folder cannot be made here (no such place, or no write access)" >&2
  exit 4
}
if [[ -e "$data_dir/fakes.pid" ]] || [[ -e "$data_dir/desk.pid" ]]; then
  echo "pid files exist: run scripts/reset.sh first" >&2
  exit 2  # refused (the exit codes of this repository: 2 = refused; 1 is only a failed check)
fi
# a log file that is a pipe, a device or a folder would block the start or write where nobody reads: only a missing path
# or a regular file is used (the same test as src/lead_desk/regfile.py: a regular file); one fixed line, exit code 4
for f in fakes.log desk.log fakes.pid desk.pid; do
  if [[ -L "$data_dir/$f" ]] || { [[ -e "$data_dir/$f" ]] && [[ ! -f "$data_dir/$f" ]]; }; then
    echo "the desk refuses to start: a log or process-number file in the data folder is not a regular file ($f)" >&2
    exit 4
  fi
done
python -m demo_only.fakes_server --outbox "$mode" --port "$fakes_port" >"$data_dir/fakes.log" 2>&1 &
fakes_pid=$!
echo "$fakes_pid" >"$data_dir/fakes.pid"
desk_pid=""
# one place that ends a start that did not work: the programs THIS script started are stopped, their pid files go, and
# the exit code is 3 (the thing started cannot be reached) with ONE fixed line (never the text of a log)
fail_start() {
  local p
  for p in "$desk_pid" "$fakes_pid"; do
    if [[ -n "$p" ]]; then kill "$p" 2>/dev/null || true; wait "$p" 2>/dev/null || true; fi
  done
  rm -f "$data_dir/fakes.pid" "$data_dir/desk.pid"
  echo "$1: the programs started here were stopped; read the log files in the data folder" >&2
  exit 3
}
# a program started here owns its port when (1) it is still running, (2) its own log holds the line it prints once it
# accepts requests (a program that is only a neighbour on the port never wrote that line into OUR log) and, for the
# desk, (3) the port answers /counts over HTTP. The look lasts longer than the desk's own bind retry (BIND_RETRY_SECONDS
# in constants.py), so a port held by another program shows as the desk giving up, not as a false start.
i=0
while [[ "$i" -lt "$tries" ]]; do
  if ! kill -0 "$fakes_pid" 2>/dev/null; then fail_start "the demo servers stopped right after they were started"; fi
  if grep -q '^fakes server ' "$data_dir/fakes.log" 2>/dev/null; then break; fi
  sleep "$pause"
  i=$((i + 1))
done
if [[ "$i" -ge "$tries" ]]; then fail_start "the demo servers did not report that they accept requests"; fi
python -m lead_desk.server >"$data_dir/desk.log" 2>&1 &
desk_pid=$!
echo "$desk_pid" >"$data_dir/desk.pid"
# one GET /counts on the desk's port; succeeds only for an HTTP 200 answer
desk_answers() {
  local first=""
  exec 3<>"/dev/tcp/127.0.0.1/$desk_port" || return 1
  printf 'GET /counts HTTP/1.0\r\nHost: 127.0.0.1\r\n\r\n' >&3
  IFS= read -r -t 2 first <&3 || true
  exec 3<&- 3>&-
  [[ "$first" == "HTTP/1."?" 200 "* ]]
}
i=0
while [[ "$i" -lt "$tries" ]]; do
  if ! kill -0 "$desk_pid" 2>/dev/null; then fail_start "the desk stopped right after it was started"; fi
  if grep -q '^desk listening on ' "$data_dir/desk.log" 2>/dev/null && (desk_answers) 2>/dev/null; then
    kill -0 "$desk_pid" 2>/dev/null || fail_start "the desk stopped right after it was started"
    break
  fi
  sleep "$pause"
  i=$((i + 1))
done
if [[ "$i" -ge "$tries" ]]; then fail_start "the desk did not answer on its port in time"; fi
# the process numbers come from the shell's own variables: the pid files are written here, never read back here
echo "started: demo servers ($mode outbox) pid $fakes_pid, desk pid $desk_pid"
echo "ports: desk $desk_port, demo CRM and outbox $fakes_port (check with: curl http://127.0.0.1:$desk_port/counts)"
echo "logs: $data_dir/fakes.log and $data_dir/desk.log"
