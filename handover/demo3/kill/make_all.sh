#!/bin/bash
# Builds RESULTS.md from results.jsonl (my own numbers only; written before comparing with the demo table).
cd "$(dirname "$0")"
{
echo "# lane3 kill and fault results (own harness; counts taken outside n8n per lead id)"
echo "Generated $(date -u +%Y-%m-%d\ %H:%MZ). n = number of runs behind each row. Flow sets: 11:05Z (59202078), 61e3804b (fixed), 6ebb7f62-v3, 7709d058-v4."
echo; echo "## Part 1: kill points, faults, ERROR, burst, GREP (flows 11:05Z and 61e3804b)"; echo
python3 make_results.py
echo; echo "## Part 2: alert cases on the v3 and v4 flows (case column: v3A means case A, whichever flows column)"; echo
python3 make_results_v.py
echo; echo "## Part 3: recovery seconds (K1, K2, K3, K6) on v4 (lease 120 s, folder n8n-flows-v4) and film-v4 (lease 45 s). Voided runs are labelled VOID- in results.jsonl and left out."; echo
python3 make_results_l45.py
echo; echo "
