#!/bin/bash
# usage: package.sh <tree-R7U> [outdir]      env: BASE (default tree-R7T)
# Builds in outdir: core-fix-on-frozen-r7u-crlf.patch.gz, core-fix-on-frozen-r7u-lf.patch, core-fix-r7t-to-r7u-delta-crlf.patch.gz,
# sha256-r7u.txt, apply-matrix-r7u.txt (cells a-crlf, b-crlf, c-lf), snapshot-r7u/ (MANIFEST.txt, files/, delta diff). Method as out/R7T/build_patches.sh + apply_matrix.sh.
set -eu
B=/home/user/build/rr6; BASE=${BASE:-$B/tree-R7T}
TREE=$(cd "${1:?usage: package.sh <tree-R7U> [outdir]}" && pwd)
OUT=${2:-/home/user/build/rr6/out/R7U-MERGE/pkg}
[ -e "$OUT" ] && { echo "REFUSE: $OUT exists"; exit 3; }
mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd); W=$OUT/scr; mkdir -p "$W"
GIT="git -c user.name=pkg -c user.email=pkg@example.invalid -c core.autocrlf=false"
clean() { rm -rf "$1/.git" "$1/.ruff_cache" "$1/.pytest_cache" "$1/data"; find "$1" -name __pycache__ -prune -exec rm -rf {} + ; }
cp -a "$TREE" "$W/R7U-copy"; clean "$W/R7U-copy"
# frozen archive committed as scratch base
mkdir "$W/scratch-frozen"; (cd "$W/scratch-frozen" && git -C $B/demo-frozen/repo2 archive frozen2 | tar -x && $GIT init -q . && echo "* -text" > .git/info/attributes && $GIT add -A && $GIT commit -q -m frozen2)
(cd "$W/scratch-frozen"; find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +; cp -a "$W/R7U-copy/." .; $GIT add -A; $GIT diff --cached --binary --no-color > "$W/crlf.patch")
python3 - "$W" <<'PY'
import re,sys
W=sys.argv[1]+'/'
b=open(W+'crlf.patch','rb').read()
parts=re.split(rb'(?m)^(?=diff --git )',b)
out=[p.replace(b'\r\n',b'\n') if p.startswith((b'diff --git a/scripts/reset.ps1',b'diff --git a/scripts/start_all.ps1')) else p for p in parts]
open(W+'lf.patch','wb').write(b''.join(out))
PY
# delta base = tree-R7T committed, then R7U content
mkdir "$W/scratch-delta"; (cd "$W/scratch-delta"; cp -a "$BASE/." .; clean .; $GIT init -q . && echo "* -text" > .git/info/attributes && $GIT add -A && $GIT commit -q -m r7t
  find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +; cp -a "$W/R7U-copy/." .; $GIT add -A; $GIT diff --cached --binary --no-color > "$W/delta.patch")
# gzip -9, no name, no mtime (-n); assert the unpacked sha256
gz() { gzip -9 -n -c "$1" > "$2"; a=$(sha256sum < "$1" | cut -d' ' -f1); b=$(gzip -dc "$2" | sha256sum | cut -d' ' -f1); [ "$a" = "$b" ] || { echo "UNPACKED SHA MISMATCH $2"; exit 7; }; echo "unpacked sha256 asserted for $(basename "$2"): $a"; }
gz "$W/crlf.patch" "$OUT/core-fix-on-frozen-r7u-crlf.patch.gz"
cp "$W/lf.patch" "$OUT/core-fix-on-frozen-r7u-lf.patch"
gz "$W/delta.patch" "$OUT/core-fix-r7t-to-r7u-delta-crlf.patch.gz"
CRLF=$OUT/core-fix-on-frozen-r7u-crlf.patch.gz; LF=$OUT/core-fix-on-frozen-r7u-lf.patch; DEL=$OUT/core-fix-r7t-to-r7u-delta-crlf.patch.gz
# sha256 list (packed files plus the unpacked patch of each gz)
{ cd "$OUT"; sha256sum core-fix-on-frozen-r7u-crlf.patch.gz core-fix-on-frozen-r7u-lf.patch core-fix-r7t-to-r7u-delta-crlf.patch.gz
  echo "unpacked:"; echo "$(sha256sum < "$W/crlf.patch" | cut -d' ' -f1)  core-fix-on-frozen-r7u-crlf.patch (unpacked)"; echo "$(sha256sum < "$W/delta.patch" | cut -d' ' -f1)  core-fix-r7t-to-r7u-delta-crlf.patch (unpacked)"; } > "$OUT/sha256-r7u.txt"
# apply matrix
set +e
F=$B/demo-frozen/repo2; AM=$W/am; mkdir -p "$AM"
CMP="-x .git -x data -x .ruff_cache -x .pytest_cache -x __pycache__"
{
echo "frozen tree $(git -C $F rev-parse frozen2^{tree}) patch-crlf=$CRLF patch-lf=$LF target=$TREE"
for t in a b c; do
  mkdir $AM/$t; git -C $F archive frozen2 | tar -x -C $AM/$t
  [ $t = c ] && sed -i 's/\r$//' $AM/$t/scripts/reset.ps1 $AM/$t/scripts/start_all.ps1
  e=$(for f in reset start_all; do if grep -q "$(printf '\r')" $AM/$t/scripts/$f.ps1; then printf CRLF; else printf LF; fi; printf ' '; done)
  echo "checkout $t: .ps1 line endings before patching: $e"
done
for spec in "a crlf $CRLF" "b crlf $CRLF" "c lf $LF"; do
  set -- $spec
  case $3 in *.gz) gzip -dc "$3" > $AM/p-$1.patch;; *) cp "$3" $AM/p-$1.patch;; esac
  (cd $AM/$1 && git apply --check --binary $AM/p-$1.patch > $AM/chk.txt 2>&1; rc=$?; echo "cell $1-$2: git apply --check rc=$rc"; [ $rc -eq 0 ] || head -n 3 $AM/chk.txt)
done
for t in a b c; do
  (cd $AM/$t && git apply --binary $AM/p-$t.patch; rc=$?; echo "cell $t: git apply rc=$rc"
   for f in scripts/reset.ps1 scripts/start_all.ps1; do echo "  $f lines=$(wc -l < $f) lines-with-CR=$(grep -c "$(printf '\r')" $f)"; done
   rm -rf .pytest_cache; find . -name __pycache__ -prune -exec rm -rf {} +
   if diff -r . $TREE $CMP > $AM/d.txt 2>&1; then echo "  tree equals the R7U tree byte for byte"
   elif [ $t = c ] && diff -r --strip-trailing-cr . $TREE $CMP > $AM/d2.txt 2>&1; then echo "  equals the R7U tree once the .ps1 line endings are ignored (expected for the lf patch)"
   else echo "  DIFFERS from the R7U tree:"; head -n 5 $AM/d.txt; fi)
done
# delta on top of R7T gives R7U
rm -rf $AM/d; cp -a "$BASE" $AM/d; clean $AM/d
(cd $AM/d && gzip -dc "$DEL" | git apply --binary; rc=$?; echo "delta: git apply (r7t tree + delta) rc=$rc"; if diff -r . $TREE $CMP > $AM/d3.txt 2>&1; then echo "  r7t tree + delta equals the R7U tree byte for byte"; else echo "  DELTA RESULT DIFFERS:"; head -n 5 $AM/d3.txt; fi)
} > "$OUT/apply-matrix-r7u.txt" 2>&1
cat "$OUT/apply-matrix-r7u.txt"
# snapshot
S=$OUT/snapshot-r7u; mkdir -p $S/files
(cd "$B"; diff -rqN "$BASE" "$TREE" $CMP | sed -E "s#^Files $BASE/([^ ]+) and .*#\1#") > $S/changed-files.txt || true
while read -r f; do [ -z "$f" ] && continue; if [ -f "$TREE/$f" ]; then mkdir -p "$S/files/$(dirname "$f")"; cp "$TREE/$f" "$S/files/$f"; else echo "removed in R7U: $f" >> $S/removed-files.txt; fi; done < $S/changed-files.txt
(diff -ruN -x __pycache__ -x .pytest_cache -x data -x .ruff_cache -x .git "$BASE" "$TREE" > $S/delta-r7t-to-r7u.diff) || true
cp "$OUT/sha256-r7u.txt" "$OUT/apply-matrix-r7u.txt" $S/
(cd $S && find . -type f ! -name MANIFEST.txt | sort | xargs sha256sum > MANIFEST.txt; echo "manifest: $(wc -l < MANIFEST.txt) files")
rm -rf "$W"
echo "PACKAGE OK: $OUT"; cat "$OUT/sha256-r7u.txt"
