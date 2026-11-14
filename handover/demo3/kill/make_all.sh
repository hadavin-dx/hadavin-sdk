#!/bin/bash
# Builds RESULTS.md from results.jsonl (my own numbers only; written before comparing with the demo table).
cd "$(dirname "$0")" || exit 1
{
echo "# lane3 kill and fault results (own harness; counts taken outside n8n per lead id)"
echo "Generated $(date -u '+%Y-%m-%d %H:%MZ'). n = number of runs behind each row. Flow sets: 11:05Z (59202078), 61e3804b (fixed), 6ebb7f62-v3, 7709d058-v4, 873a908a-film-v4-lease45. Voided runs (my slips) are labelled VOID- in results.jsonl."
echo; echo "## Part 1: kill points, faults, ERROR, burst, GREP"; echo
python3 make_results.py
echo; echo "## Part 2: alert cases on the v3 and v4 flows (case column: v3A means case A, whichever flows column; )"; echo
python3 make_results_v.py
echo; echo "## Part 3: recovery seconds on v4 (lease 120 s) and film-v4 (lease 45 s)"; echo
python3 make_results_l45.py
echo; echo "## Part 4: comparison with the demo table"; echo
cat COMPARE-demo.md
} > RESULTS.md
