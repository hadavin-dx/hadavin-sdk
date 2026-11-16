#!/bin/sh
# apply_matrix.sh - tries every (checkout type x patch file x apply mode) combination of the core-fix patch
# on the frozen demo tree, checks the result, prints one table, and exits 0 only when every combination
# that the README recommends passes.  POSIX sh, no network, made-up data only.
#
# usage: sh apply_matrix.sh [--check] [--no-pytest] [--tests "f1 f2 f3"] [--work DIR] [--keep]
#                           [--base REPO] [--rev REV] [--tree TREEID] [--recommend "a=crlf:plain b=crlf:plain c=lf:plain"]
#                           <patch-crlf> <patch-lf>
#   --check      the quick check (no test run): same matrix, exit code only decides.
#   without it   also runs pytest (3 fast test files, default tests/test_reset_scripts.py) on the recommended cells.
# checkout types:  a = plain git archive (what a zip download or `git archive` gives)
#                  b = git clone with core.autocrlf=true (what a Windows user gets; simulated on Linux, see FIDELITY)
#                  c = archive with every text file converted to LF (the .ps1 files too)
# patch files:     crlf = the patch whose two .ps1 hunks use CRLF;  lf = the patch whose hunks are all LF
# modes:           plain   = git apply
#                  iws     = git apply --ignore-whitespace
#                  iwsfix  = git apply --ignore-whitespace, then the line-ending fix command on the patched .ps1 files
#                  pbin    = patch -p1 --binary
# FIDELITY of type b: it is a real `git -c core.autocrlf=true clone` of the frozen branch, run on Linux. Git
#   applies the same conversion rules on every system, so file contents match what Windows gives. What is NOT
#   simulated: the Windows file system, PowerShell, Git for Windows' own build of `git apply`.
set -u
AM_OUT=${AM_OUT:-/home/user/build/rr6/out/AM}
BASE=/home/user/build/rr6/demo-frozen/repo2
REV=frozen2
TREE=49d3c85938fe5323a3378a49195d3b8da434b3ca
WORK=/home/user/build/rr6/tree-AM/matrix-work
TESTS="tests/test_reset_scripts.py"
RECOMMEND="a=crlf:plain b=crlf:plain c=lf:plain"
PY=/home/user/build/rr6/venv-br/bin/python
LO_UP=/home/user/build/rr6/src-v6/drivers/lo_up-q4g.py
QUICK=0; NOPYTEST=0; KEEP=0
while [ $# -gt 0 ]; do
  case $1 in
    --check) QUICK=1; NOPYTEST=1; shift ;;
    --no-pytest) NOPYTEST=1; shift ;;
    --keep) KEEP=1; shift ;;
    --tests) TESTS=$2; shift 2 ;;
    --work) WORK=$2; shift 2 ;;
    --base) BASE=$2; shift 2 ;;
    --rev) REV=$2; shift 2 ;;
    --tree) TREE=$2; shift 2 ;;
    --recommend) RECOMMEND=$2; shift 2 ;;
    --) shift; break ;;
    -*) echo "unknown option $1" >&2; exit 2 ;;
    *) break ;;
  esac
done
[ $# -eq 2 ] || { echo "usage: sh apply_matrix.sh [--check] <patch-crlf> <patch-lf>" >&2; exit 2; }
case $1 in /*) PCRLF=$1 ;; *) PCRLF=$(pwd)/$1 ;; esac
case $2 in /*) PLF=$2 ;; *) PLF=$(pwd)/$2 ;; esac
[ -f "$PCRLF" ] && [ -f "$PLF" ] || { echo "patch file missing" >&2; exit 2; }
CR=$(printf '\r')

RUN=$WORK/run.$$
RES=$RUN/res
rm -rf "$RUN"; mkdir -p "$RES" "$RUN/tmp" "$RUN/logs" || exit 2
TSV=$RES/matrix.tsv; : > "$TSV"
[ "$KEEP" = 1 ] || trap 'rm -rf "$RUN"' EXIT

# ---- fixed facts about the inputs ---------------------------------------------------------------------------
got=$(git -C "$BASE" rev-parse "$REV^{tree}" 2>/dev/null) || { echo "FATAL: cannot read $REV in $BASE" >&2; exit 2; }
[ "$got" = "$TREE" ] || { echo "FATAL: tree of $REV is $got, expected $TREE" >&2; exit 2; }
echo "frozen tree $got  patch-crlf=$PCRLF  patch-lf=$PLF"
( cd /tmp && git apply --numstat "$PCRLF" ) > "$RES/numstat-crlf.txt" 2>"$RES/numstat-crlf.err" || { echo "FATAL: crlf patch is not readable by git apply --numstat"; cat "$RES/numstat-crlf.err"; }
( cd /tmp && git apply --numstat "$PLF" ) > "$RES/numstat-lf.txt" 2>"$RES/numstat-lf.err" || { echo "FATAL: lf patch is not readable by git apply --numstat"; cat "$RES/numstat-lf.err"; }
if [ -s "$RES/numstat-crlf.err" ] || [ -s "$RES/numstat-lf.err" ] || [ ! -s "$RES/numstat-crlf.txt" ] || [ ! -s "$RES/numstat-lf.txt" ]; then
  echo "APPLY MATRIX: FAIL - a patch file is not a readable patch (git apply --numstat failed); cells not run"; exit 1
fi
NF_crlf=$(wc -l < "$RES/numstat-crlf.txt" | tr -d ' ')
NF_lf=$(wc -l < "$RES/numstat-lf.txt" | tr -d ' ')
awk '{print $3}' "$RES/numstat-lf.txt" "$RES/numstat-crlf.txt" | grep '\.ps1$' | sort -u > "$RES/ps1.txt"
echo "files touched: crlf patch $NF_crlf, lf patch $NF_lf; .ps1 files: $(tr '\n' ' ' < "$RES/ps1.txt")"

# ---- helpers ------------------------------------------------------------------------------------------------
ending() { # prints CRLF | LF | MIXED | MISSING for one file
  f=$1; [ -f "$f" ] || { echo MISSING; return; }
  cr=$(tr -cd '\r' < "$f" | wc -c | tr -d ' '); lf=$(tr -cd '\n' < "$f" | wc -c | tr -d ' ')
  lcr=$(grep -c "${CR}\$" "$f")
  if [ "$cr" = 0 ]; then echo LF
  elif [ "$cr" = "$lcr" ] && [ "$lcr" = "$lf" ]; then echo CRLF
  else echo MIXED; fi
}
manifest() { # sha256 of every file (CR removed) + path, .git left out
  ( cd "$1" && find . -path ./.git -prune -o -type f -print | LC_ALL=C sort | while IFS= read -r f; do
      printf '%s %s\n' "$(tr -d '\r' < "$f" | sha256sum | cut -c1-64)" "$f"; done )
}
fixcmd() { # $1 = CRLF|LF ; prints the fix command text (the one printed in the README)
  if [ "$1" = CRLF ]; then printf '%s\n' "sed -i 's/\\r*\$/\\r/' <ps1 files>"; else printf '%s\n' "sed -i 's/\\r\$//' <ps1 files>"; fi
}
dofix() { # $1 = CRLF|LF ; run from the tree root
  while IFS= read -r f; do
    [ -f "$f" ] || continue
    if [ "$1" = CRLF ]; then sed -i 's/\r*$/\r/' "$f"; else sed -i 's/\r$//' "$f"; fi
  done < "$RES/ps1.txt"
}

# ---- three base checkouts -----------------------------------------------------------------------------------
B=$RUN/base; mkdir -p "$B/a" "$B/c"
git -C "$BASE" archive "$REV" | tar -x -C "$B/a" || { echo "FATAL archive a" >&2; exit 2; }
git -C "$BASE" archive "$REV" | tar -x -C "$B/c" || { echo "FATAL archive c" >&2; exit 2; }
( cd "$B/c" && find . -type f -print | while IFS= read -r f; do grep -Iq . "$f" 2>/dev/null && sed -i 's/\r$//' "$f"; done )
git -c core.autocrlf=true clone -q --branch "$REV" "$BASE" "$B/b" 2>"$RUN/logs/clone.err" || { echo "FATAL clone b"; cat "$RUN/logs/clone.err"; exit 2; }
git -C "$B/b" config core.autocrlf true
[ "$(git -C "$B/b" rev-parse 'HEAD^{tree}')" = "$TREE" ] || { echo "FATAL: clone tree differs" >&2; exit 2; }
git -C "$B/b" status --short | head -3 > "$RUN/logs/clone-status.txt"
for t in a b c; do
  e=""; for f in $(cat "$RES/ps1.txt"); do x=$(ending "$B/$t/$f"); e="$e $x"; done
  set -- $e; first=$1; for x in "$@"; do [ "$x" = "$first" ] || first=MIXED; done
  echo "$first" > "$RES/baseend-$t.txt"
  echo "checkout $t: .ps1 line endings before patching:$e"
done
[ -s "$RUN/logs/clone-status.txt" ] && { echo "WARNING: fresh clone is not clean:"; cat "$RUN/logs/clone-status.txt"; }
# first line of every .ps1 as the frozen tree has it (CR removed): the patch must not damage it
: > "$RES/ps1-first.txt"
for f in $(cat "$RES/ps1.txt"); do printf '%s\t%s\n' "$f" "$(head -n 1 "$B/c/$f" | tr -d '\r')" >> "$RES/ps1-first.txt"; done

# ---- reference result: lf patch, --ignore-whitespace, on the all-LF tree; content compared ignoring CR -----------
REF=$RUN/ref; cp -a "$B/c" "$REF"
( cd "$REF" && git apply --ignore-whitespace "$PLF" ) > "$RUN/logs/ref.log" 2>&1; refrc=$?
if [ $refrc -ne 0 ]; then REFOK=0; echo "REFERENCE FAILED (lf patch + --ignore-whitespace on the all-LF tree, rc=$refrc): content comparison impossible"; sed -n 1,5p "$RUN/logs/ref.log"
else REFOK=1; manifest "$REF" > "$RES/ref.manifest"; fi

# ---- the matrix ---------------------------------------------------------------------------------------------
fmt="%-3s %-5s %-6s %-5s %-4s %-6s %-9s %-7s %-7s %-6s %s\n"
printf "$fmt" TYP PATCH MODE CHK APPLY PS1END FILES CONTENT PYTEST RESULT NOTE
printf "$fmt" --- ----- ---- --- ----- ------ ----- ------- ------ ------ ----
for t in a b c; do
 for p in crlf lf; do
  if [ $p = crlf ]; then P=$PCRLF; EXPF=$NF_crlf; else P=$PLF; EXPF=$NF_lf; fi
  for m in plain iws iwsfix pbin; do
    id=$t-$p-$m; D=$RUN/cell-$id; cp -a "$B/$t" "$D"; L=$RUN/logs/$id
    note=""
    case $m in
      plain)  ( cd "$D" && git apply --check "$P" ) > "$L.check" 2>&1; chk=$? ;;
      iws|iwsfix) ( cd "$D" && git apply --check --ignore-whitespace "$P" ) > "$L.check" 2>&1; chk=$? ;;
      pbin)   ( cd "$D" && patch -p1 --binary --dry-run < "$P" ) > "$L.check" 2>&1; chk=$? ;;
    esac
    case $m in
      plain)  ( cd "$D" && git apply "$P" ) > "$L.apply" 2>&1; app=$? ;;
      iws|iwsfix) ( cd "$D" && git apply --ignore-whitespace "$P" ) > "$L.apply" 2>&1; app=$? ;;
      pbin)   ( cd "$D" && patch -p1 --binary --no-backup-if-mismatch < "$P" ) > "$L.apply" 2>&1; app=$? ;;
    esac
    want=$(cat "$RES/baseend-$t.txt")
    if [ $m = iwsfix ] && [ $app -eq 0 ]; then ( cd "$D" && dofix "$want" ); fi
    # (2) .ps1 line endings (all one kind, same as the checkout had) and still text with the expected first line
    ps1=OK; for f in $(cat "$RES/ps1.txt"); do
      e=$(ending "$D/$f")
      if [ "$e" != "$want" ]; then ps1=BAD; note="$note $f=$e(want $want);"; fi
      if [ -f "$D/$f" ]; then
        { grep -Iq . "$D/$f" && iconv -f UTF-8 -t UTF-8 "$D/$f" > /dev/null 2>&1; } || { ps1=BAD; note="$note $f:not-text;"; }
        wf=$(grep "^$f	" "$RES/ps1-first.txt" | cut -f2-); gf=$(head -n 1 "$D/$f" | tr -d '\r')
        [ "$wf" = "$gf" ] || { ps1=BAD; note="$note $f:first-line-changed;"; }
      fi
    done
    # (3) number of changed files (git diff --numstat); only meaningful when apply worked
    if [ $t = b ]; then nf=$( cd "$D" && git add -N -A . >/dev/null 2>&1; git diff --numstat 2>/dev/null | wc -l | tr -d ' ')
    else nf=$( cd "$RUN" && git diff --no-index --numstat "base/$t" "cell-$id" 2>/dev/null | grep -v '/\.git/' | wc -l | tr -d ' '); fi
    if [ "$nf" = "$EXPF" ]; then files="$nf/$EXPF"; else files="$nf/$EXPF!"; fi
    # content: every file equal to the reference once CR is ignored
    if [ $app -eq 0 ] && [ $REFOK = 1 ]; then
      manifest "$D" > "$L.manifest"
      if cmp -s "$L.manifest" "$RES/ref.manifest"; then content=SAME; else content=DIFF; note="$note content-differs($(diff "$L.manifest" "$RES/ref.manifest" | grep -c '^<') files);"; fi
    else content=n/a; fi
    py=-
    if [ $chk -eq 0 ] && [ $app -eq 0 ] && [ "$ps1" = OK ] && [ "$nf" = "$EXPF" ] && [ "$content" = SAME ]; then res=PASS; else res=FAIL; fi
    printf "$fmt" $t $p $m $chk $app $ps1 "$files" $content $py $res "$note"
    echo "$t $p $m $chk $app $ps1 $nf/$EXPF $content $res" >> "$TSV"
  done
 done
done

# ---- pytest on the recommended cells (only without --check) -------------------------------------------------------
PYRES=$RES/pytest.tsv; : > "$PYRES"
runpy() { # $1 = id ; prints ok | FAIL(rc) | skipped(reason)
  rid=$1; D=$RUN/cell-$rid; have=""
  for f in $TESTS; do [ -f "$D/$f" ] && have="$have $f"; done
  [ -n "$have" ] || { echo "skipped(no such test file: $TESTS)"; return; }
  [ -x "$PY" ] && [ -f "$LO_UP" ] || { echo "skipped(python or lo_up-q4g.py missing)"; return; }
  unshare -n true 2>/dev/null || { echo "skipped(unshare -n not allowed)"; return; }
  mkdir -p "$RUN/tmp/$rid"
  ( cd "$D" && TMPDIR=$RUN/tmp/$rid PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$D/src timeout 420 unshare -n "$PY" "$LO_UP" "$PY" -m pytest -q -p no:cacheprovider $have ) > "$RUN/logs/$rid.pytest" 2>&1
  rc=$?; tail -n 1 "$RUN/logs/$rid.pytest" > "$RUN/logs/$rid.pytest.last"
  if [ $rc -eq 0 ]; then echo ok; else echo "FAIL(rc=$rc)"; fi
}

# ---- derive the recommendation from the matrix, then judge the README's recommended cells -----------------------------
status() { awk -v t="$1" -v p="$2" -v m="$3" '$1==t && $2==p && $3==m {print $9}' "$TSV"; }
order_for() { if [ "$1" = c ]; then echo "lf:plain crlf:plain lf:pbin crlf:pbin lf:iws crlf:iws lf:iwsfix crlf:iwsfix"; else echo "crlf:plain lf:plain crlf:pbin lf:pbin crlf:iws lf:iws crlf:iwsfix lf:iwsfix"; fi; }
OVERALL=0
echo
echo "RECOMMENDED CELLS (from the README table: $RECOMMEND)"
DERIVED=""
for t in a b c; do
  d=none
  for pm in $(order_for $t); do
    s=$(status $t ${pm%%:*} ${pm##*:})
    if [ "$s" = PASS ]; then d=$pm; break; fi
  done
  DERIVED="$DERIVED $t=$d"
  rec=""; for kv in $RECOMMEND; do [ "${kv%%=*}" = $t ] && rec=${kv#*=}; done
  [ -n "$rec" ] || { echo "type $t: NO recommendation given"; OVERALL=1; continue; }
  rp=${rec%%:*}; rm_=${rec##*:}
  s=$(status $t $rp $rm_)
  pyr="not run"
  if [ "$NOPYTEST" = 0 ] && [ "$s" = PASS ]; then
    pyr=$(runpy $t-$rp-$rm_)
    case $pyr in ok) : ;; *) case $pyr in skipped*) : ;; *) s=FAIL ;; esac ;; esac
    echo "$t-$rp-$rm_ $pyr" >> "$PYRES"
    [ -f "$RUN/logs/$t-$rp-$rm_.pytest.last" ] && pyr="$pyr [$(cat "$RUN/logs/$t-$rp-$rm_.pytest.last")]"
  fi
  if [ "$s" = PASS ]; then echo "type $t: cell $t-$rp-$rm_ PASS   pytest: $pyr   (best cell by the matrix: $d)"
  else
    echo "type $t: cell $t-$rp-$rm_ FAIL  <<< the README recommendation does not work; pytest: $pyr; best working cell by the matrix: $d"
    OVERALL=1
  fi
done
if [ $REFOK = 0 ]; then echo "REFERENCE could not be built: content check not possible"; OVERALL=1; fi

# ---- the exact commands per type, derived from the matrix ------------------------------------------------------------
echo
echo "COMMANDS (derived from the matrix; run from the top folder of the checkout):"
for kv in $DERIVED; do
  t=${kv%%=*}; d=${kv#*=}
  [ $t = a ] && lab="plain archive / zip download (no .git folder)"
  [ $t = b ] && lab="git clone on Windows (core.autocrlf=true)"
  [ $t = c ] && lab="archive with every text file converted to LF"
  if [ "$d" = none ]; then echo "  [$t] $lab: NO WORKING COMBINATION IN THE MATRIX"; continue; fi
  p=${d%%:*}; m=${d##*:}; if [ $p = crlf ]; then pf=$PCRLF; else pf=$PLF; fi
  case $m in
    plain) cmd="git apply --check $(basename "$pf") && git apply $(basename "$pf")" ;;
    pbin) cmd="patch -p1 --binary < $(basename "$pf")" ;;
    iws) cmd="git apply --check --ignore-whitespace $(basename "$pf") && git apply --ignore-whitespace $(basename "$pf")" ;;
    iwsfix) cmd="git apply --check --ignore-whitespace $(basename "$pf") && git apply --ignore-whitespace $(basename "$pf") && $(fixcmd "$(cat "$RES/baseend-$t.txt")" | sed "s#<ps1 files>#$(tr '\n' ' ' < "$RES/ps1.txt" | sed 's/ $//')#")" ;;
  esac
  echo "  [$t] $lab:  $cmd"
done
echo
printf '%s\n' "FIX COMMAND check: cells *-iwsfix prove the line-ending fix (CRLF: sed -i 's/\\r*\$/\\r/' ; LF: sed -i 's/\\r\$//'); status per type:"
for t in a b c; do echo "  $t: crlf-patch=$(status $t crlf iwsfix) lf-patch=$(status $t lf iwsfix)"; done
echo
if [ $OVERALL -eq 0 ]; then echo "APPLY MATRIX: OK (every recommended cell passes)"; else echo "APPLY MATRIX: FAIL (see lines marked FAIL / <<<)"; fi
cp "$TSV" "$AM_OUT/last-matrix.tsv" 2>/dev/null
exit $OVERALL
