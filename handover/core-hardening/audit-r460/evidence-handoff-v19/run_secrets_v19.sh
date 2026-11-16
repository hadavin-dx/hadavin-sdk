#!/usr/bin/env bash
# M3 negative test: the audit-reader secret is NOT resolvable through the agent's own secrets kind. Operator = this user (root);
# agent = OS user `nobody`. Made-up secret value built from parts. Usage: bash run_secrets_v19.sh <python> <src> ; prints PASS/FAIL lines.
set -u
PY="${1:?}"; SRC="${2:?}"; HERE="$(cd "$(dirname "$0")" && pwd)"
# v19 (independent runner of v18, finding 2): `nobody` must be able to ENTER the folder that holds this script and the source tree, else 8 of 12 checks fail with Errno 13 and look like leaks.
for d in "$HERE" "$SRC"; do
  if ! runuser -u nobody -- test -r "$d" -a -x "$d" 2>/dev/null; then echo "PRECHECK FAILED: the OS user nobody cannot enter $d (every folder on the path needs the x bit for others); copy this folder and the source to a world-readable place such as /opt and run again; nothing was tested"; exit 3; fi
done
runuser -u nobody -- test -r "$HERE/agent_probe_v19.py" || { echo "PRECHECK FAILED: nobody cannot read $HERE/agent_probe_v19.py; nothing was tested"; exit 3; }
T="$(mktemp -d /tmp/hv19sec.XXXXXX)"; chmod 755 "$T"; trap 'rm -rf "$T"' EXIT
mkdir "$T/ops" "$T/agent"; chmod 755 "$T/ops" "$T/agent"
printf '%s' "postgres""://auditrd:""fake""@db.invalid/x" > "$T/ops/audit-reader-dsn"; chmod 0400 "$T/ops/audit-reader-dsn"
printf '%s' "agent-only-fake" > "$T/agent/llm-key"; chown nobody "$T/agent/llm-key"; chmod 0400 "$T/agent/llm-key"
fails=0
t() { # name expected command... (the first output line is shown)
  local n="$1" want="$2"; shift 2; local out; out="$("$@" 2>&1 | head -1)"; local w="${out%% *}"
  if [ "$w" = "$want" ]; then echo "PASS $n [$out]"; else echo "FAIL $n [want $want, got: $out]"; fails=$((fails+1)); fi; }
AG() { runuser -u nobody -- "$PY" -I -B "$HERE/agent_probe_v19.py" "$SRC" "$@"; }
t "M3a operator (root) resolves the audit-reader name from the operator folder (positive control)" READ "$PY" -I -B "$HERE/agent_probe_v19.py" "$SRC" file "$T/ops" audit-reader-dsn
t "M3b agent user, agent's own file kind pointed at the OPERATOR folder: audit-reader name DENIED" DENIED AG file "$T/ops" audit-reader-dsn
t "M3c agent user, agent's own file kind on the agent folder: its own secret IS readable (positive control)" READ AG file "$T/agent" llm-key
t "M3d agent user, agent's own file kind on the agent folder: the audit-reader name is not there: DENIED" DENIED AG file "$T/agent" audit-reader-dsn
t "M3e agent user, env kind with the agent's environment (no variable): DENIED" DENIED env -i HOME=/nonexistent /usr/sbin/runuser -u nobody -- "$PY" -I -B "$HERE/agent_probe_v19.py" "$SRC" env HADAVIN_SECRET_ audit-reader-dsn
t "M3f operator env kind with the variable set in the OPERATOR shell only resolves it (positive control)" READ env HADAVIN_SECRET_AUDIT_READER_DSN=fake-from-parts "$PY" -I -B "$HERE/agent_probe_v19.py" "$SRC" env HADAVIN_SECRET_ audit-reader-dsn
# mutant (the bad configuration the reviewer described): the same folder readable by the agent's group
chmod 0440 "$T/ops/audit-reader-dsn"; chgrp nogroup "$T/ops/audit-reader-dsn"
t "M3g MUTANT: the operator file is group-readable by the agent's group: the probe says READ (a leak); the check detects it" READ AG file "$T/ops" audit-reader-dsn
# v19 (minor m5): folder mode, strict mode rule, same-user negative
chmod 0440 "$T/ops/audit-reader-dsn"; chgrp nogroup "$T/ops/audit-reader-dsn"; chmod 0700 "$T/ops"
t "M3h folder mode: operator folder 0700 root, the file itself group-readable by the agent's group (0440): the agent still cannot reach it: DENIED" DENIED AG file "$T/ops" audit-reader-dsn
chmod 0755 "$T/ops"
t "M3i MUTANT for M3h: the same folder 0755: the agent READS the group-readable file (a leak the folder mode prevented)" READ AG file "$T/ops" audit-reader-dsn
t "M3j strict rule (mode & 0o077 refused, the S-2b prototype) on the 0440 file: DENIED even though the folder is open" DENIED AG file-strict "$T/ops" audit-reader-dsn
chmod 0400 "$T/ops/audit-reader-dsn"; chown root "$T/ops/audit-reader-dsn"
t "M3k strict rule on a 0400 file of the operator: the operator still READS it (positive control)" READ "$PY" -I -B "$HERE/agent_probe_v19.py" "$SRC" file-strict "$T/ops" audit-reader-dsn
t "M3l same OS user: an agent running as the operator's own user READS the 0400 file (a file mode cannot separate two things run by one user; the agent MUST run as another OS user or in another container; this is stated, not hidden)" READ "$PY" -I -B "$HERE/agent_probe_v19.py" "$SRC" file "$T/ops" audit-reader-dsn
echo "SUMMARY failures=$fails"; exit $fails
