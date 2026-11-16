#!/bin/bash
# acc5-cases.sh: 18 test cases for acc5.sh (made-up outputs). Usage: bash acc5-cases.sh (run in paste-check/). Prints one line per case and a final "cases ok=<n> bad=<n>".
D=$(dirname "$0"); ok=0; bad=0
t() { # name, expected-prefix, kill-plus-lines (printed inside the n8n_kill.py block)
  local out; out=$(printf '== n8n_start.sh\n%s\n== n8n_kill.py\n-print("confirmed gone")\n+print("), confirmed gone")\n%s\n== end\n' "${4:-}" "$3" | bash "$D/acc5.sh")
  if [ "${out:0:${#2}}" = "$2" ]; then ok=$((ok+1)); echo "case: $1 -> $out"; else bad=$((bad+1)); echo "BAD case: $1 -> $out (expected $2)"; fi; }
t "good" ACCEPT '+sys.exit(3)'
t "good with comment tail" ACCEPT '+sys.exit(3)  # exit code 3'
t "exit 30 only" "STOP (other" '+sys.exit(30)'
t "exit 3x" "STOP (other" '+sys.exit(3x)'
t "upper case Exit(3)" ACCEPT '+Exit(3)'
t "main() plus exit 3" ACCEPT $'+sys.exit(main())\n+    sys.exit(3)'
t "main() plus return 3" ACCEPT $'+sys.exit(main())\n+    return 3'
t "main() alone" "STOP (no exit 3" '+sys.exit(main())'
t "return 31" "STOP (no exit 3" '+    return 31'
t "exit 3 only in the start.sh block" "STOP (no exit 3" '+print("x")' '+ exit 3'
t "no exit 3" "STOP (no exit 3" '+print("x")'
t "exit 4 with 3" "STOP (other" $'+sys.exit(4)\n+sys.exit(3)'
t "named constant" "STOP (other" $'+EXIT_CODE = 3'
t "exit 20 in start" "STOP (other" $'+sys.exit(3)' '+ exit 20'
t 'print("exit 3") text only (ACCEPT, documented)' ACCEPT '+print("exit 3")'
t "comment line only" "STOP (no exit 3" '+# exit code 3'
t "comment line plus exit 3" ACCEPT $'+# exit code 3\n+sys.exit(3)'
t "comment return 3 only" "STOP (no exit 3" '+# return 3'
echo "cases ok=$ok bad=$bad"
printf '== n8n_start.sh\n+x\n== n8n_kill.py\n+sys.exit(3)\n' | bash "$D/acc5.sh"; echo "(above: no == end line, expect STOP (block missing))"
