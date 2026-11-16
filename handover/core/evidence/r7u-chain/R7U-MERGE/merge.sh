#!/bin/bash
# usage: merge.sh <new-tree-path>        (refuses if the path exists)
# env overrides: BASE (default tree-R7T), DIFF_A/DIFF_C/DIFF_B (default out/R7U-X/r7u-X.diff), TREE_A/TREE_B/TREE_C (builder trees, for the comparison)
# Applies A, then C, then B with patch -p1 --fuzz=0; each one is dry-run first. A rejected hunk stops the script (exit 5); nothing is auto-resolved.
set -u
B=/home/user/build/rr6
BASE=${BASE:-$B/tree-R7T}
DEST=${1:?usage: merge.sh <new-tree-path>}
for x in A B C; do
  eval "DIFF_$x=\${DIFF_$x:-\$B/out/R7U-$x/r7u-$x.diff}"
  eval "TREE_$x=\${TREE_$x:-\$B/tree-R7U-$x}"
done
if [ -e "$DEST" ]; then echo "REFUSE: $DEST exists"; exit 3; fi
[ -d "$BASE" ] || { echo "no base tree $BASE"; exit 4; }
for x in A B C; do eval "f=\$DIFF_$x"; [ -f "$f" ] || { echo "MISSING diff for $x: $f"; exit 4; }; done
REP=$DEST-merge-report; mkdir -p "$REP" || exit 4
EXC="--exclude=__pycache__ --exclude=.ruff_cache --exclude=.pytest_cache --exclude=.git"
mkdir -p "$DEST" && (cd "$BASE" && tar cf - $EXC .) | (cd "$DEST" && tar xf -) || { echo "copy failed"; exit 4; }
echo "copied $BASE -> $DEST"

names() { # file names touched by a diff (first path component stripped, like -p1); skips absolute paths (the no-file side)
  grep -aE '^(--- |\+\+\+ )' "$1" | sed -E 's/^(--- |\+\+\+ )//; s/\t.*$//; s/\r$//' | grep -v '^/' | sed 's#^[^/]*/##' | sort -u
}
for x in A B C; do eval "f=\$DIFF_$x"; names "$f" > "$REP/files-$x.txt"; echo "diff $x: $(wc -c < "$f") bytes, $(wc -l < "$REP/files-$x.txt") files"; done

for x in A C B; do
  eval "f=\$DIFF_$x"
  if [ ! -s "$f" ]; then echo "diff $x is empty: nothing to apply"; continue; fi
  if ! patch -p1 -d "$DEST" --binary --fuzz=0 --no-backup-if-mismatch -r "$REP/rej-$x" --dry-run < "$f" > "$REP/dry-$x.log" 2>&1; then
    echo "REJECTED: diff $x does not apply cleanly on top of the previous steps (dry run, nothing changed by this step). Tree so far: $DEST"
    echo "failing files and hunks:"; awk '/^(checking|patching) file/{file=$0} /FAILED|can.t find file|malformed|No such file/{print "  " file " -> " $0}' "$REP/dry-$x.log"
    echo "full dry-run output: $REP/dry-$x.log"; exit 5
  fi
  patch -p1 -d "$DEST" --binary --fuzz=0 --no-backup-if-mismatch -r "$REP/rej-$x" < "$f" > "$REP/apply-$x.log" 2>&1 || { echo "REAL APPLY of $x FAILED after a clean dry run: $REP/apply-$x.log"; exit 6; }
  grep -aE 'offset|fuzz' "$REP/apply-$x.log" | sed "s/^/  note ($x): /"
  echo "applied $x: $(grep -ac '^patching file' "$REP/apply-$x.log") files"
done

echo "== overlapping files (touched by 2 or more diffs) =="
cat "$REP"/files-[ABC].txt | sort | uniq -d > "$REP/overlap.txt"
if [ -s "$REP/overlap.txt" ]; then while read -r p; do w=""; for x in A B C; do grep -qxF "$p" "$REP/files-$x.txt" && w="$w$x"; done; echo "  $p  [$w]"; done < "$REP/overlap.txt"; else echo "  none"; fi

echo "== each builder's changed files vs the merged tree =="
for x in A B C; do
  eval "t=\$TREE_$x"
  if [ ! -d "$t" ]; then echo "  $x: builder tree $t not found, comparison skipped"; continue; fi
  same=0; difr=0
  while read -r p; do
    [ -z "$p" ] && continue
    if [ -e "$t/$p" ] || [ -e "$DEST/$p" ]; then
      if cmp -s "$t/$p" "$DEST/$p"; then same=$((same+1)); else difr=$((difr+1)); echo "  $x: $p DIFFERS between builder tree and merged tree"; fi
    fi
  done < "$REP/files-$x.txt"
  diff -rqN "$BASE" "$t" -x .git -x data -x __pycache__ -x .ruff_cache -x .pytest_cache > "$REP/builder-$x-vs-base.txt" 2>&1
  grep -aE '^Files ' "$REP/builder-$x-vs-base.txt" | sed -E "s#^Files $BASE/([^ ]+) and .*#\1#" | sort -u > "$REP/builder-$x-changed.txt"
  miss=$(grep -vxFf "$REP/files-$x.txt" "$REP/builder-$x-changed.txt" | head -n 10 | tr '\n' ' ')
  echo "  $x: $same files identical in merged tree, $difr differ; changed in builder tree but not in its diff (first 10 names): ${miss:-none}"
done

echo "== diff -rq merged tree vs $BASE =="
diff -rq "$BASE" "$DEST" -x .git -x data -x __pycache__ -x .ruff_cache -x .pytest_cache > "$REP/summary-vs-base.txt" 2>&1
sed -E "s#$BASE#BASE#g; s#$DEST#NEW#g" "$REP/summary-vs-base.txt" | head -n 80
echo "total lines: $(wc -l < "$REP/summary-vs-base.txt")  (full: $REP/summary-vs-base.txt)"
echo "MERGE OK: $DEST"
