#!/bin/bash
# Static checks on the read-only copy of the audited tree (no n8n, nothing paid). Output: static-checks-output.txt (c6m: adds C-10c, C-10e and the ORDERS answer lines)
T=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/c6/tree/handover
H=/home/user/hadavin-sdk/handover/core-hardening
echo "## C-7: diff of the two flow folders (names only)"; diff -rq $T/demo/n8n-flows-real-v5 $T/demo/n8n-flows-film-v5 | sed "s#$T/##g"
echo "## C-9 static: claim table definition and insert"
grep -n -E "CREATE TABLE mf_leads|ON CONFLICT \(lead_key\)" $T/demo/n8n-mainframe/mf.py $T/demo/n8n-mainframe/build_mainframe.py | cut -c1-210 | sed "s#$T/##"
for f in mf-form mf-hook mf-recovery mf-sub-crm-mail; do echo -n "$f ON CONFLICT hits: "; grep -c "ON CONFLICT" $T/demo/n8n-flows-real-v5/$f.json; done
echo "## C-11a static: the plan row for the take's saving settings"
grep -n -E "EXECUTIONS_DATA_SAVE_ON_(SUCCESS|ERROR)=all" $H/inputs/plan-wp6-resmoke-v5.md | cut -c1-260
echo "## DECISIONS file line of 'never deletes'"; grep -n "never deletes" $H/inputs/DECISIONS-2026-11-16.md | cut -c1-80
echo "## QUEUE header rule 6 present"; grep -n -c "^6\. Inputs copied" $H/QUEUE.md
echo "## R460 in the bible folder (hits)"; grep -rn "R460" /home/user/hadavin-sdk/handover/bible | wc -l
echo "## files named in reports but absent from the copy"
for p in scripts/run_real_check.py scripts/run_real_check_n8n.py scripts/hubspot_probe.py; do n=$(find $T -name "$(basename $p)" | wc -l); echo "$p: $n found"; done
for p in HB171 HB180 HB186 HB189 HB194; do n=$(find $T $H -iname "*$p*" | wc -l); echo "report file for $p: $n found"; done
echo -n "owner sheets steps-edits/ (v9..v19): "; find $T $H -ipath "*steps-edits*" | wc -l

S=$H/steps-edits
echo "## C-10c: owner sheets, hits per phrase (grep -c -i, one number per phrase: never deletes / read, create and change only / does not delete / key read-only)"
for f in $S/OWNER-SHEET-v19.md $S/OWNER-SHEET-v2[0-3].md $S/OWNER-SHEET-v24-A.md $S/OWNER-SHEET-v24-B.md $S/OWNER-SHEET-v25-A.md $S/OWNER-SHEET-v25-B.md $S/OWNER-SHEET-v26-SOURCE.md; do
  echo "$(basename $f): $(grep -c -i 'never deletes' $f) / $(grep -c -i 'read, create and change only' $f) / $(grep -c -i 'does not delete' $f) / $(grep -c -i -E 'read-only|read only' $f)"; done
echo "## C-10c line text: v19 hit"; grep -n -i -E "never deletes|read, create and change only|does not delete" $S/OWNER-SHEET-v19.md | cut -c1-200
echo "## v25-A R7 (owner deletes by hand) present"; grep -c "You delete only made-up contacts of this run" $S/OWNER-SHEET-v25-A.md
echo "## newest file in steps-edits (by modification time, UTC)"; ls -l --time-style=+%FT%TZ $S | sort -k6 | tail -3 | awk '{print $6, $7}'
echo "## ORDERS answers read (line numbers)"; grep -n -E "^Q2[0-7]|^Q21\.|^## ANSWER" $H/ORDERS.md | cut -c1-90 | tail -14
echo "## stale-notice and script names in plan 4 and help text (hits)"; grep -n -c "up to 3 HubSpot contacts archived" $T/demo/PLAN-4-NLITE-FROM-LEAD.md
grep -n -E "run_real_check_n8n|run_real_check\.py" $H/ORDERS.md | cut -c1-120 | head -5
