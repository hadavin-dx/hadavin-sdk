# acc5.sh: reference implementation (for tests and for the lead) of the ACCEPTANCE RULE of RE-PIN step (c).
# Usage: bash acc5.sh < output-of-the-wording-diff-command    (prints ACCEPT or STOP (reason))
# What ACCEPT proves, plainly: ONLY that the text `exit 3`, `exit(3)` or `return 3` appears on a "+" line of the
# "== n8n_kill.py" block and that no "+" line with `exit` has another form. It does NOT prove that the line is code:
# print("exit 3") is accepted. The lead still reads the "+" lines of n8n_kill.py before writing the release line.
awk '
BEGIN { q = sprintf("%c", 39) }
/^== n8n_start\.sh$/ { b = "start"; sb = 1; next }
/^== n8n_kill\.py$/ { b = "kill"; kb = 1; next }
/^== end$/ { e = 1; next }
/^(\+\+\+|---)/ { next }
/^\+/ {
  s = substr($0, 2); l = tolower(s)
  comment = (s ~ /^[ \t]*#/)
  if (l ~ /exit/) {
    if (comment) { }
    else if (s ~ /^[ \t]*sys\.exit\(main\(\)\)[ \t]*$/) { }
    else if (l ~ ("exit[ (][23]([ \t);#,\"" q "]|$)")) { if (b == "kill" && l ~ ("exit[ (]3([ \t);#,\"" q "]|$)")) three = 1 }
    else { bad++; badl = badl $0 "|" }
  }
  if (!comment && b == "kill" && l ~ ("return 3([ \t);#,\"" q "]|$)")) three = 1
}
END {
  if (!sb || !kb || !e) { print "STOP (block missing)"; exit }
  if (bad > 0) { print "STOP (other exit text: " badl ")"; exit }
  if (!three) { print "STOP (no exit 3 or return 3 in kill block)"; exit }
  print "ACCEPT"
}'
