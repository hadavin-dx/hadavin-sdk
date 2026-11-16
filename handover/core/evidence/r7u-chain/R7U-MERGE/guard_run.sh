#!/bin/bash
# usage: guard_run.sh <tree> [--list FILE] [--wait] [--name NAME]
# One staged guard run, same recipe as the r7t run (out/R7T/hy-guard-final.log, out/R7T/guard-files-r7t.txt):
# staged git copy (git init + git add -A, no commit), TMPDIR outside the tree, PYTHONPATH, PYTHONDONTWRITEBYTECODE=1,
# no network (unshare -n + lo_up-q4g.py), timeout 2400 s. Detached unless --wait. Log: out/R7U-MERGE/<name>/guard.log, exit code: <name>/guard.rc
set -u
B=/home/user/build/rr6; O=$B/out/R7U-MERGE
TREE=${1:?usage: guard_run.sh <tree> [--list FILE] [--wait] [--name NAME]}; shift
LIST=""; WAIT=0; NAME=guard
while [ $# -gt 0 ]; do case $1 in --list) LIST=$2; shift 2;; --wait) WAIT=1; shift;; --name) NAME=$2; shift 2;; *) echo "bad arg $1"; exit 2;; esac; done
[ -d "$TREE" ] || { echo "no tree $TREE"; exit 2; }
R=$O/$NAME; [ -e "$R" ] && { echo "REFUSE: $R exists (use --name or remove it)"; exit 3; }
mkdir -p "$R/tmp" || exit 2
S=$R/stage
EXC="--exclude=__pycache__ --exclude=.ruff_cache --exclude=.pytest_cache --exclude=.git --exclude=data"
mkdir -p "$S" && (cd "$TREE" && tar cf - $EXC .) | (cd "$S" && tar xf -)
(cd "$S" && git init -q . && git add -A) || { echo "git stage failed"; exit 2; }
echo "staged: $S ($(cd "$S" && git ls-files | wc -l) files in the index)"
# file list
if [ -z "$LIST" ]; then
  LIST=$R/guard-files.txt
  { echo "tests/test_load_tools.py tests/test_load_driver_facts.py tests/test_r7k_findings.py"
    cat "$B/out/R7T/guard-files-r7t.txt"
    for f in tests/test_r7u_a_findings.py tests/test_r7u_b_findings.py tests/test_r7u_c_findings.py; do echo "$f"; done
    (cd "$S" && ls tests/test_*loopback*.py 2>/dev/null)
  } | tr ' ' '\n' | grep -v '^$' | awk '!s[$0]++' > "$LIST.all"
  : > "$LIST"; while read -r f; do if [ -f "$S/$f" ]; then echo "$f" >> "$LIST"; else echo "WARN: $f not in tree, left out of the list" | tee -a "$R/guard.warn"; fi; done < "$LIST.all"
else
  while read -r f; do [ -f "$S/$f" ] || { echo "list names a missing file: $f"; exit 2; }; done < <(tr ' ' '\n' < "$LIST" | grep -v '^$')
  tr ' ' '\n' < "$LIST" | grep -v '^$' > "$R/guard-files.txt"; LIST=$R/guard-files.txt
fi
echo "file list ($(wc -l < "$LIST") files): $LIST"
: > "$R/empty.in"
cat > "$R/inner.sh" <<INNER
#!/bin/bash
echo "start \$(date -u +%FT%TZ) load=\$(cut -d' ' -f1-3 /proc/loadavg) tree=$TREE" > "$R/guard.wrap"
cd "$S"
env -i HOME="$R/tmp" LANG=C.UTF-8 TMPDIR="$R/tmp" PYTHONPATH="$S/src" PYTHONDONTWRITEBYTECODE=1 \\
  PLAYWRIGHT_BROWSERS_PATH="$B/pw-browsers" GITLEAKS_BIN="$B/bin/gitleaks" DPLD_REQUIRE_SCAN=1 DPLD_REQUIRE_DEMO=1 \\
  PATH="$B/bin:/usr/local/bin:/usr/bin:/bin" \\
  timeout -k 20 2400 unshare -n python3 "$B/src-v6/drivers/lo_up-q4g.py" "$B/venv-br/bin/python" -m pytest -q -p no:cacheprovider -rfs \$(cat "$LIST" | tr '\n' ' ') > "$R/guard.log" 2>&1
rc=\$?
echo "end \$(date -u +%FT%TZ) rc=\$rc" >> "$R/guard.wrap"
echo \$rc > "$R/guard.rc"
INNER
chmod +x "$R/inner.sh"
if [ $WAIT -eq 1 ]; then "$R/inner.sh" < "$R/empty.in"; echo "rc=$(cat "$R/guard.rc")"; tail -n 3 "$R/guard.log"
else setsid nohup "$R/inner.sh" < "$R/empty.in" > "$R/inner.out" 2>&1 & echo "detached pid $!; log $R/guard.log ; rc file $R/guard.rc (appears at the end); wrapper $R/guard.wrap"; fi
