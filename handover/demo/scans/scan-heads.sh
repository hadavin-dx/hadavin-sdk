#!/usr/bin/env bash
# Q6 evidence runner: scan-heads.sh [branch ...]   (default: every remote branch). Records, never judges.
# Env: CLONE (default /tmp/work/q6-clone) GL (gitleaks) PYV (python venv) OUT (output dir)
set -u
CLONE=${CLONE:-/tmp/work/q6-clone}; GL=${GL:-/tmp/work/gl/gitleaks}; PYV=${PYV:-/tmp/work/int2-venv}
OUT=${OUT:-/tmp/demo-push/handover/demo/scans}; WT=${WT:-/tmp/work/q6-wt}; RUFF=${RUFF:-ruff}
cd "$CLONE" || exit 2
git fetch -q --prune origin
if [ $# -eq 0 ]; then set -- $(git for-each-ref --format='%(refname:strip=3)' refs/remotes/origin | grep -vxE 'origin|HEAD'); fi
rules_of(){ python3 -c "
import json,sys,collections
try: d=json.load(open(sys.argv[1]))
except Exception: d=[]
c=collections.Counter(x.get('RuleID') for x in d or [])
print(' '.join(f'{k}({v})' for k,v in c.most_common(3)) or 'none')" "$1"; }
ROWS="$OUT/scan-rows.tsv"; : > "$ROWS"
for b in "$@"; do
  sha=$(git rev-parse --short=12 "origin/$b"); safe=${b//\//_}; ev="$OUT/evidence-q6-$safe.txt"; : > "$ev"
  say(){ echo "$*" >> "$ev"; }
  A=$(mktemp -d /tmp/work/q6-arch.XXXX); rm -rf "$WT"
  git archive "origin/$b" | tar -x -C "$A"
  say "### $b $sha  $(date -u +%FT%TZ)"
  toml=none; [ -f "$A/.gitleaks.toml" ] && toml=present
  say "\$ gitleaks dir . --no-banner   (cwd=archive; .gitleaks.toml: $toml)"
  (cd "$A" && "$GL" dir . --no-banner --redact -r "$A.dir.json" -f json >> "$ev" 2>&1); dx=$?
  dn=$(grep -oE 'leaks found: [0-9]+' "$ev" | grep -oE '[0-9]+$' | tail -1); dn=${dn:-0}; say "exit=$dx (flags added: --redact -r <json> -f json; findings by rule: $(rules_of "$A.dir.json"))"
  git worktree add -q --detach "$WT" "origin/$b" >>"$ev" 2>&1
  say "\$ gitleaks git . --no-banner   (cwd=worktree detached at $sha)"
  start=$(wc -l < "$ev")
  (cd "$WT" && "$GL" git . --no-banner --redact -r "$A.git.json" -f json >> "$ev" 2>&1); gx=$?
  gn=$(tail -n +$((start+1)) "$ev" | grep -oE 'leaks found: [0-9]+' | grep -oE '[0-9]+$' | tail -1); gn=${gn:-0}
  rules=$(rules_of "$A.git.json"); rm -f "$A.dir.json" "$A.git.json"
  say "exit=$gx (flags added: --redact -r <json> -f json; top rules: $rules)"
  hy=n/a
  if [ -f "$WT/tools/hygiene.py" ] && [ -f "$WT/patterns.txt" ] && [ -f "$WT/exceptions.txt" ]; then
    say "\$ python -c 'hygiene.pipeline(REPO, patterns.txt, exceptions.txt)'   (tools/hygiene.py has no CLI entry point; same call test_hygiene makes)"
    hout=$(cd "$WT" && "$PYV/bin/python" -c "
import sys; sys.path.insert(0,'.')
from pathlib import Path
from tools import hygiene
r=hygiene.pipeline(Path('.'),Path('patterns.txt'),Path('exceptions.txt'))
print('\n'.join(map(str,r))); print('FINDINGS',len(r)); sys.exit(1 if r else 0)" 2>&1); hx=$?
    say "$hout"; say "exit=$hx"; hy="exit=$hx, $(echo "$hout"|grep -E '^FINDINGS'|tail -1|sed 's/FINDINGS //') findings"
    [ $hx -ne 0 ] && [ -z "$(echo "$hout"|grep '^FINDINGS')" ] && hy="exit=$hx (error, see evidence)"
  fi
  th=n/a
  if [ -f "$WT/tests/test_hygiene.py" ]; then
    say "\$ GITLEAKS_BIN=$GL DPLD_REQUIRE_SCAN=1 python -m pytest -q -p no:cacheprovider -rs tests/test_hygiene.py"
    tout=$(cd "$WT" && GITLEAKS_BIN=$GL DPLD_REQUIRE_SCAN=1 timeout 600 "$PYV/bin/python" -m pytest -q -p no:cacheprovider -rs tests/test_hygiene.py 2>&1); tx=$?
    say "$tout"; say "exit=$tx"; th="exit=$tx; $(echo "$tout"|tail -1)"
  fi
  rf=n/a
  if [ -f "$WT/pyproject.toml" ] && grep -q '^\[tool.ruff' "$WT/pyproject.toml"; then
    say "\$ ruff check . ; ruff format --check .  ($($RUFF --version))"
    c=$(cd "$WT" && $RUFF check . 2>&1); cx=$?; f=$(cd "$WT" && $RUFF format --check . 2>&1); fx=$?
    say "$c"; say "check exit=$cx"; say "$f"; say "format exit=$fx"
    rf="check exit=$cx; format exit=$fx"
  fi
  git worktree remove --force "$WT" >>"$ev" 2>&1; rm -rf "$A"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$b" "$sha" "exit=$dx, $dn" "exit=$gx, $gn; ${rules:-none}" "$hy" "$th" "$rf" "toml=$toml" >> "$ROWS"
done
git worktree prune
echo "rows: $ROWS"; cat "$ROWS"
