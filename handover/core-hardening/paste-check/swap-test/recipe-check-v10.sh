#!/bin/bash
# v10 re-run: bash recipe-check-v10.sh. Runs recipe.sh (the plan's bash paste of edit 13, byte for byte) on scratch copies: 1 positive case and 7 failing cases (tests 2 to 8). The PowerShell half is replaced by `git archive -o` in a scratch repo.
H=$(cd "$(dirname "$0")" && pwd); S=$(mktemp -d); trap 'rm -rf "$S"' EXIT
mkdir -p $S/home/hadavin-smoke; : > $S/home/hadavin-smoke/env.sh
mktar() {  # $1 = film file to archive ("" = make no tar)
  rm -rf $S/repo $S/w; mkdir -p $S/w/_local/scratch/wp6-smoke $S/repo/handover/demo/n8n-flows-film-v5
  [ -n "$1" ] || return 0
  cp "$1" $S/repo/handover/demo/n8n-flows-film-v5/mf-sub-crm-mail.json
  ( cd $S/repo && git init -q && git add -A && git -c user.name=t -c user.email=t@example.invalid commit -qm film && git archive -o $S/w/_local/scratch/wp6-smoke/film-crm.tar HEAD handover/demo/n8n-flows-film-v5/mf-sub-crm-mail.json )
}
swapped() {  # $1 = real-v5 file to swap with 2.1b.sh
  export T=$S/t HOME=$S/home W=$S/w; rm -rf $T; mkdir -p $T/flows; cp "$1" $T/flows/mf-sub-crm-mail.json; for f in mf-form mf-hook mf-recovery; do echo '[]' > $T/flows/$f.json; done
  printf 'CRM_URL=http://127.0.0.1:8771\n' > $T/flow-values.env; bash $H/2.1b.sh > /dev/null 2>&1
}
run() { echo "=== $1"; bash $H/recipe.sh 2>&1 | sed "s#$S#\$S#g"; }
FILM=$H/input-film/mf-sub-crm-mail.json; REAL=$H/input/mf-sub-crm-mail.json
mktar $FILM; swapped $REAL; run "1 POSITIVE: real film file vs swapped copy (must print RECIPE PASS)"
echo "=== 1b the film file read from the tar is byte-identical to the input copy"; cmp $T/film-crm.json $FILM && echo identical
echo "=== 2 NEGATIVE: tar missing"; mktar ""; swapped $REAL; run "tar missing (must print RECIPE STOP)"
echo "=== 3 NEGATIVE: tar empty (0 bytes)"; mktar ""; : > $S/w/_local/scratch/wp6-smoke/film-crm.tar; run "tar empty (must print RECIPE STOP)"
echo "=== 4 NEGATIVE: tar holds the wrong path (extraction fails)"; mktar $FILM; ( cd $S/repo && git archive -o $S/w/_local/scratch/wp6-smoke/film-crm.tar HEAD handover/demo/n8n-flows-film-v5 ) ; mkdir -p $S/x && cd $S/x && mkdir -p other && cp $FILM other/a.json && tar -cf $S/w/_local/scratch/wp6-smoke/film-crm.tar other/a.json; cd $H; run "wrong path inside the tar (must print RECIPE STOP)"
echo "=== 5 NEGATIVE: film file is not valid JSON (python traceback)"; echo 'not json' > $S/bad.json; mktar $S/bad.json; swapped $REAL; run "corrupt film file (must print RECIPE STOP)"
echo "=== 6 NEGATIVE: a second line differs (film timeout changed)"; python3 -I - $FILM $S/film2.json <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); w=d[0] if isinstance(d,list) else d
for x in w["nodes"]:
    if x["name"]=="CrmUpsert": x["parameters"]["options"]["timeout"]=5
json.dump(d,open(sys.argv[2],"w"))
PY
mktar $S/film2.json; swapped $REAL; run "timeout differs too (must print RECIPE STOP)"
echo "=== 7 NEGATIVE: no swap done (swap file still the HubSpot node: its parameters differ in many lines)"; mktar $FILM; export T=$S/t HOME=$S/home W=$S/w; rm -rf $T; mkdir -p $T/flows; cp $REAL $T/flows/mf-sub-crm-mail.json; run "2.1b not run (must print RECIPE STOP)"
echo "=== 8 NEGATIVE: film file identical to the swapped copy's parameters except url text is the same too (no url difference at all)"; python3 -I - $REAL $S/film3.json <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); json.dump(d,open(sys.argv[2],"w"))
PY
mktar $FILM; swapped $REAL; python3 -I - $T/flows/mf-sub-crm-mail.json $S/film4.json <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); json.dump(d,open(sys.argv[2],"w"))
PY
mktar $S/film4.json; run "film node already equal to the swapped node (diff rc 0, must print RECIPE STOP)"
