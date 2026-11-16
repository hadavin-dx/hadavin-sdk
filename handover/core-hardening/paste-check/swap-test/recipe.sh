. $HOME/hadavin-smoke/env.sh; TAR="$W/_local/scratch/wp6-smoke/film-crm.tar"; P='import json,sys; d=json.load(open(sys.argv[1])); w=d[0] if isinstance(d,list) else d; print(json.dumps([x for x in w["nodes"] if x["name"]=="CrmUpsert"][0]["parameters"],sort_keys=True,indent=1))'
if [ ! -s "$TAR" ]; then echo "RECIPE STOP: film-crm.tar is missing or empty"
elif ! tar -xOf "$TAR" handover/demo/n8n-flows-film-v5/mf-sub-crm-mail.json > $T/film-crm.json || [ ! -s $T/film-crm.json ]; then echo "RECIPE STOP: the film file could not be read from the tar"
elif ! python3 -I -c "$P" $T/film-crm.json > $T/p-film.txt || ! python3 -I -c "$P" $T/flows/mf-sub-crm-mail.json > $T/p-swap.txt || [ ! -s $T/p-film.txt ] || [ ! -s $T/p-swap.txt ]; then echo "RECIPE STOP: the CrmUpsert parameters could not be read from one of the two files"
else
  diff $T/p-film.txt $T/p-swap.txt > $T/p.diff; rc=$?; cat $T/p.diff
  if [ $rc -eq 1 ] && [ "$(grep -c '^[<>]' $T/p.diff)" = 2 ] && [ "$(grep -c '^< *"url": "={{ $env.MF_CRM_URL }}/upsert"' $T/p.diff)" = 1 ] && [ "$(grep -c '^> *"url": "http://127.0.0.1:8771/upsert"' $T/p.diff)" = 1 ]; then echo "RECIPE PASS: exactly the url line differs"; else echo "RECIPE STOP: the difference is not exactly the url line (diff rc=$rc)"; fi
fi
