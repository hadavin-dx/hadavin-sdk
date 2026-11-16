#!/bin/bash
# v8 re-run: bash recipe-check.sh. Swaps a scratch copy of the real-v5 file (2.1b.sh), then runs the lead's diff recipe against the film file.
# v8: the film file now reaches bash through a tar made by `git archive -o` (the PowerShell half of the recipe is replaced here by the same git command in a scratch repo); the bash half is exactly the plan's bash line.
H=$(cd "$(dirname "$0")" && pwd); S=$(mktemp -d); export T=$S/t HOME=$S/home; mkdir -p $T/flows $HOME/hadavin-smoke; : > $HOME/hadavin-smoke/env.sh
W=$S/w; mkdir -p $W/_local/scratch/wp6-smoke $S/repo/handover/demo/n8n-flows-film-v5; export W
cp $H/input-film/mf-sub-crm-mail.json $S/repo/handover/demo/n8n-flows-film-v5/
( cd $S/repo && git init -q && git add -A && git -c user.name=t -c user.email=t@example.invalid commit -qm film && git archive -o $W/_local/scratch/wp6-smoke/film-crm.tar HEAD handover/demo/n8n-flows-film-v5/mf-sub-crm-mail.json )
cp $H/input/mf-sub-crm-mail.json $T/flows/; printf 'CRM_URL=http://127.0.0.1:8771\n' > $T/flow-values.env
bash $H/2.1b.sh > /dev/null 2>&1
# ---- the plan's bash line (edit 13) starts here
P='import json,sys; d=json.load(open(sys.argv[1])); w=d[0] if isinstance(d,list) else d; print(json.dumps([x for x in w["nodes"] if x["name"]=="CrmUpsert"][0]["parameters"],sort_keys=True,indent=1))'; tar -xOf "$W/_local/scratch/wp6-smoke/film-crm.tar" handover/demo/n8n-flows-film-v5/mf-sub-crm-mail.json > $T/film-crm.json; python3 -I -c "$P" $T/film-crm.json > $T/p-film.txt; python3 -I -c "$P" $T/flows/mf-sub-crm-mail.json > $T/p-swap.txt; diff $T/p-film.txt $T/p-swap.txt; echo "diff rc=$? (1 = the files differ, expected; only the url line may be listed)"
# ---- end of the plan's bash line
cmp $T/film-crm.json $H/input-film/mf-sub-crm-mail.json && echo "film file from the tar is byte-identical to the input copy"
rm -rf $S
