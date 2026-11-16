#!/usr/bin/env bash
# M3 negative test: the audit-reader secret is NOT resolvable through the agent's own secrets kind. Operator = this user (root);
# agent = OS user `nobody`. Made-up secret value built from parts. Usage: bash run_secrets_v17.sh <python> <src> ; prints PASS/FAIL lines.
set -u
PY="${1:?}"; SRC="${2:?}"; HERE="$(cd "$(dirname "$0")" && pwd)"
T="$(mktemp -d /tmp/hv17sec.XXXXXX)"; chmod 755 "$T"; trap 'rm -rf "$T"' EXIT
mkdir "$T/ops" "$T/agent"; chmod 755 "$T/ops" "$T/agent"
printf '%s' "postgres""://auditrd:""fake""@db.invalid/x" > "$T/ops/audit-reader-dsn"; chmod 0400 "$T/ops/audit-reader-dsn"
printf '%s' "agent-only-fake" > "$T/agent/llm-key"; chown nobody "$T/agent/llm-key"; chmod 0400 "$T/agent/llm-key"
fails=0
t() { # name expected command... (the first output line is shown)
  local n="$1" want="$2"; shift 2; local out; out="$("$@" 2>&1 | head -1)"; local w="${out%% *}"
  if [ "$w" = "$want" ]; then echo "PASS $n [$out]"; else echo "FAIL $n [want $want, got: $out]"; fails=$((fails+1)); fi; }
AG() { runuser -u nobody -- "$PY" -I -B "$HERE/agent_probe_v17.py" "$SRC" "$@"; }
t "M3a operator (root) resolves the audit-reader name from the operator folder (positive control)" READ "$PY" -I -B "$HERE/agent_probe_v17.py" "$SRC" file "$T/ops" audit-reader-dsn
t "M3b agent user, agent's own file kind pointed at the OPERATOR folder: audit-reader name DENIED" DENIED AG file "$T/ops" audit-reader-dsn
t "M3c agent user, agent's own file kind on the agent folder: its own secret IS readable (positive control)" READ AG file "$T/agent" llm-key
t "M3d agent user, agent's own file kind on the agent folder: the audit-reader name is not there: DENIED" DENIED AG file "$T/agent" audit-reader-dsn
t "M3e agent user, env kind with the agent's environment (no variable): DENIED" DENIED env -i HOME=/nonexistent /usr/sbin/runuser -u nobody -- "$PY" -I -B "$HERE/agent_probe_v17.py" "$SRC" env HADAVIN_SECRET_ audit-reader-dsn
t "M3f operator env kind with the variable set in the OPERATOR shell only resolves it (positive control)" READ env HADAVIN_SECRET_AUDIT_READER_DSN=fake-from-parts "$PY" -I -B "$HERE/agent_probe_v17.py" "$SRC" env HADAVIN_SECRET_ audit-reader-dsn
# mutant (the bad configuration the reviewer described): the same folder readable by the agent's group
chmod 0440 "$T/ops/audit-reader-dsn"; chgrp nogroup "$T/ops/audit-reader-dsn"
t "M3g MUTANT: the operator file is group-readable by the agent's group: the probe says READ (a leak); the check detects it" READ AG file "$T/ops" audit-reader-dsn
echo "SUMMARY failures=$fails"; exit $fails
