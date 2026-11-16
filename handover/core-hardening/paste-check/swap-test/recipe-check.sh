#!/bin/bash
# Re-run: bash recipe-check.sh. Swaps a scratch copy of the real-v5 file (2.1b.sh), then runs the lead's diff recipe against the film file copy (in the plan the film file comes from `git -C $HD show 5fdc659d1:...`; here `cp` stands in for git show).
H=$(cd "$(dirname "$0")" && pwd); S=$(mktemp -d); export T=$S/t HOME=$S/home; mkdir -p $T/flows $HOME/hadavin-smoke; : > $HOME/hadavin-smoke/env.sh
cp $H/input/mf-sub-crm-mail.json $T/flows/; printf 'CRM_URL=http://127.0.0.1:8771\n' > $T/flow-values.env
bash $H/2.1b.sh > /dev/null 2>&1
P='import json,sys; d=json.load(open(sys.argv[1])); w=d[0] if isinstance(d,list) else d; print(json.dumps([x for x in w["nodes"] if x["name"]=="CrmUpsert"][0]["parameters"],sort_keys=True,indent=1))'
cp $H/input-film/mf-sub-crm-mail.json $T/film-crm.json
python3 -I -c "$P" $T/film-crm.json > $T/p-film.txt; python3 -I -c "$P" $T/flows/mf-sub-crm-mail.json > $T/p-swap.txt; diff $T/p-film.txt $T/p-swap.txt; echo "diff rc=$? (1 = the files differ, expected; only the url line may be listed)"
rm -rf $S
