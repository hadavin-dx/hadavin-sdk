#!/bin/bash
# final_gate.sh - one command that records the whole evidence set for a demo tarball. It never judges.
# usage: final_gate.sh TARBALL [--only N[,N]] [--quick] [--workdir DIR] [--out-dir DIR] [--force]
# See README-final-gate.md. Single runner: a lock file stops two gates running at the same time.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; FG="$HERE/final_gate"
REPO="$(cd "$HERE/../../.." && pwd)"
TARBALL=""; ONLY=""; QUICK=0; WORK=""; OUTDIR="$REPO/handover/demo/reports"; FORCE=0
while [ $# -gt 0 ]; do case "$1" in
  --only) ONLY="$2"; shift 2;; --quick) QUICK=1; shift;; --workdir) WORK="$2"; shift 2;;
  --out-dir) OUTDIR="$2"; shift 2;; --force) FORCE=1; shift;;
  -h|--help) sed -n 2,4p "$0"; exit 0;; -*) echo "unknown option $1" >&2; exit 64;; *) TARBALL="$1"; shift;; esac; done
[ -f "$TARBALL" ] || { echo "tarball not found: $TARBALL" >&2; exit 64; }
TARBALL="$(readlink -f "$TARBALL")"
exec 9>/tmp/final-gate.lock; flock -n 9 || { echo "another final_gate.sh is running (lock /tmp/final-gate.lock); one runner only" >&2; exit 75; }
BASE="$(basename "$TARBALL" .tar.gz)"; SHORT="${BASE##*-}"; MODE=full; [ $QUICK = 1 ] && MODE=quick
[ -n "$WORK" ] || WORK="$(mktemp -d /tmp/final-gate-"$SHORT"-XXXXXX)"; mkdir -p "$WORK"; WORK="$(readlink -f "$WORK")"
SEED_PY="${FINAL_GATE_SEED_PY:-/tmp/dpld-venv/bin/python}"   # only used to choose the interpreter and as the offline fallback
echo "final_gate: tarball=$TARBALL mode=$MODE workdir=$WORK" 
want() { [ -z "$ONLY" ] && return 0; case ",$ONLY," in *",$1,"*) return 0;; esac; return 1; }
need() { want "$1" || return 1; [ -n "$ONLY" ] && return 0; [ $FORCE = 1 ] && return 0; [ -f "$WORK/done-$1" ] && { echo "[stage $1] already done in this workdir (use --only $1 or --force to repeat)"; return 1; }; return 0; }
STEP() { python3 -I "$FG/step.py" "$WORK" "$@"; }   # STEP STAGE NAME TIMEOUT [--cwd D] [--env K=V] -- cmd

# ---------- stage 0: set-up
if [ ! -f "$WORK/done-0" ]; then
  mkdir -p "$WORK/src"; tar xzf "$TARBALL" -C "$WORK/src" || { echo "unpack failed" >&2; exit 70; }
  TREE="$(find "$WORK/src" -mindepth 1 -maxdepth 1 -type d | head -n1)"; echo "$TREE" > "$WORK/tree.txt"
  BASEPY="$(readlink -f "$SEED_PY" 2>/dev/null || true)"; [ -x "$BASEPY" ] || BASEPY="$(command -v python3.12 || command -v python3)"
  STEP 0 venv-create 300 -- "$BASEPY" -m venv "$WORK/venv"
  STEP 0 pip-install-hashed 900 --cwd "$TREE" -- "$WORK/venv/bin/python" -m pip install --require-hashes -r requirements-dev.txt
  if [ "$(python3 -I -c "import json,sys;print([r['exit'] for r in map(json.loads,open('$WORK/stages.jsonl')) if r['name']=='pip-install-hashed'][-1])")" != 0 ]; then
    SP="$("$SEED_PY" -c 'import sysconfig;print(sysconfig.get_paths()["purelib"])' 2>/dev/null)"
    if [ -d "$SP" ]; then   # offline fallback: own venv, seed packages added through a .pth file; stated in the report header
      "$WORK/venv/bin/python" -c "import sysconfig;open(sysconfig.get_paths()['purelib']+'/seed.pth','w').write('$SP\n')"
      echo "pip install failed; fell back to seed site-packages $SP" > "$WORK/venv-note.txt"
      for t in ruff mypy bandit pytest; do ln -sf "$(dirname "$SEED_PY")/$t" "$WORK/venv/bin/$t" 2>/dev/null; done
    else echo "pip install failed and no seed venv at $SEED_PY" >&2; exit 71; fi
  fi
  python3 -I "$FG/patch_hooks.py" "$TREE" > "$WORK/raw-patch.txt" 2>&1; PRC=$?
  STEP 0 patch-server-hooks 60 -- cat "$WORK/raw-patch.txt"
  [ $PRC = 0 ] || { echo "PATCH FAILED (stop): $(cat "$WORK/raw-patch.txt")" >&2; exit 72; }
  touch "$WORK/done-0"
fi
TREE="$(cat "$WORK/tree.txt")"; PY="$WORK/venv/bin/python"; BIN="$WORK/venv/bin"
python3 -I - "$WORK" "$TARBALL" "$TREE" "$MODE" "$PY" <<'PYEOF'
import hashlib, json, os, platform, subprocess, sys, datetime
w, tb, tree, mode, py = sys.argv[1:6]
note = open(w + "/venv-note.txt").read().strip() if os.path.exists(w + "/venv-note.txt") else "own venv, packages from requirements-dev.txt (hashes checked)"
m = {"tarball": tb, "tarball_name": os.path.basename(tb), "tarball_sha256": hashlib.sha256(open(tb, "rb").read()).hexdigest(), "tree": tree, "workdir": w,
     "host": platform.platform(), "cores": os.cpu_count(), "python": subprocess.run([py, "--version"], capture_output=True, text=True).stdout.strip(),
     "venv": f"{w}/venv ({note})", "started_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), "mode": mode,
     "server_py_hooks": open(w + "/raw-patch.txt").read().strip() if os.path.exists(w + "/raw-patch.txt") else "(not recorded)"}
open(w + "/meta.json", "w").write(json.dumps(m, indent=1))
PYEOF
CLEAN() { env "$@"; }
export PYTHONDONTWRITEBYTECODE=1
for v in $(env | grep -o '^DESK_[A-Z_]*'); do unset "$v"; done   # no desk settings leak into tests
ports() { python3 -I "$FG/freeport.py" "${1:-2}"; }

# ---------- stage 1: lint, types, security, schema
if need 1; then
  STEP 1 ruff-check 300 --cwd "$TREE" -- "$BIN/ruff" check
  STEP 1 ruff-format-check 300 --cwd "$TREE" -- "$BIN/ruff" format --check
  STEP 1 mypy-linux 900 --cwd "$TREE" -- "$BIN/mypy" --platform linux
  STEP 1 bandit 300 --cwd "$TREE" -- "$BIN/bandit" -q -ll -r src tools -c pyproject.toml
  STEP 1 check-schema 300 --cwd "$TREE" --env PYTHONPATH="$TREE/src:$TREE" -- "$PY" scripts/check_schema.py
  touch "$WORK/done-1"
fi
# ---------- stage 2: full pytest
if need 2; then
  N=3; [ $QUICK = 1 ] && N=1
  for i in $(seq 1 $N); do
    STEP 2 "pytest-run-$i" 1200 --cwd "$TREE" --env PYTHONPATH="$TREE/src" -- "$PY" -m pytest -q -rf -p no:cacheprovider --no-header
  done; touch "$WORK/done-2"
fi
# ---------- stage 3: the four concurrency tests (names taken from /tmp/dpld-out/conc50-dpld4.txt runs)
if need 3; then
  N=50; [ $QUICK = 1 ] && N=3
  for t in test_concurrent_same_source_ref test_retry_twice_concurrent test_ten_parallel test_reconcile_counts; do
    python3 -I "$FG/conc.py" "$WORK" 3 "$TREE" "$PY" "$t" "$N" 120
  done; touch "$WORK/done-3"
fi
# ---------- stage 4: hostile matrix (one runner): all classes except A, then class A
if need 4; then
  if [ $QUICK = 1 ]; then echo "[stage 4] skipped in --quick mode (runs only in full mode)"
  else
    read -r DP FP <<< "$(ports 2)"; rm -f "$TREE/_hostile_rows.jsonl"
    python3 -I "$FG/prep_hostile.py" "$HERE/hostile_run.py" "$TREE" "$PY" "$DP" "$FP" || exit 73
    STEP 4 hostile-classes-B-to-H 1800 --cwd "$TREE" --env SKIPA=1 -- "$PY" hostile_run.py
    cp "$TREE/_hostile_rows.jsonl" "$WORK/rows-BH.jsonl" 2>/dev/null
    read -r DP FP <<< "$(ports 2)"; rm -f "$TREE/_hostile_rows.jsonl"
    python3 -I "$FG/prep_hostile.py" "$HERE/hostile_run.py" "$TREE" "$PY" "$DP" "$FP" || exit 73
    STEP 4 hostile-class-A 1800 --cwd "$TREE" --env HTREE="$TREE" -- "$PY" "$FG/runA.py"
    cp "$TREE/_hostile_rows.jsonl" "$WORK/rows-A.jsonl" 2>/dev/null
    touch "$WORK/done-4"
  fi
fi
# ---------- stage 5: load and kill -9
if need 5; then
  if [ $QUICK = 1 ]; then SC="same:10 same:100 diff:100"; KR="1"; else SC="same:10 same:100 same:500 same:1000 diff:100 diff:1000"; KR="1 2 3 4 5"; fi
  for mode in keyed blind; do
    for s in $SC; do
      kind="${s%%:*}"; n="${s##*:}"; read -r DP FP <<< "$(ports 2)"
      STEP 5 "load-$mode-$kind-$n" 900 --cwd "$FG" --env LOAD_ROOT="$TREE" --env LOAD_DATA="$WORK/data-$mode-$kind-$n" --env LOAD_PY="$PY" \
        --env LOAD_DESK_PORT="$DP" --env LOAD_FAKES_PORT="$FP" -- "$PY" "$FG/load.py" scen "$mode" "$kind" "$n"
    done
    for r in $KR; do
      read -r DP FP <<< "$(ports 2)"
      STEP 5 "kill9-$mode-round$r" 900 --cwd "$FG" --env LOAD_ROOT="$TREE" --env LOAD_DATA="$WORK/data-$mode-kill$r" --env LOAD_PY="$PY" \
        --env LOAD_DESK_PORT="$DP" --env LOAD_FAKES_PORT="$FP" -- "$PY" "$FG/load.py" kill "$mode" "$r"
    done
  done; touch "$WORK/done-5"
fi
# ---------- report
SUF=""; [ $QUICK = 1 ] && SUF="-quick"; mkdir -p "$OUTDIR"
python3 -I "$FG/report.py" "$WORK" "$OUTDIR/final-gate-$SHORT$SUF.md" && {
  rm -rf "$OUTDIR/final-gate-$SHORT$SUF-raw"; mkdir -p "$OUTDIR/final-gate-$SHORT$SUF-raw"
  cp -r "$WORK/raw" "$WORK/stages.jsonl" "$WORK/meta.json" "$OUTDIR/final-gate-$SHORT$SUF-raw/"; cp "$WORK"/*.jsonl "$OUTDIR/final-gate-$SHORT$SUF-raw/" 2>/dev/null; }
echo "final_gate: done (workdir $WORK). No verdict is given; read the report."
