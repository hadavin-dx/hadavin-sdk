#!/bin/bash
# prints: worktree | branch | dirty files | ahead-of-origin | remote==local
while IFS='|' read w b; do
  [ -d "$w" ] || { echo "$w|MISSING"; continue; }
  d=$(git -C "$w" status --porcelain 2>/dev/null | wc -l)
  h=$(git -C "$w" rev-parse HEAD 2>/dev/null)
  if [ "$b" = "DETACHED" ] || [ -z "$b" ]; then
    onr=$(git -C "$w" branch -r --contains $h 2>/dev/null | wc -l)
    echo "$w|detached|dirty=$d|on-remote-branches=$onr|${h:0:8}"
  else
    br=${b#refs/heads/}
    rs=$(git ls-remote origin "refs/heads/$br" 2>/dev/null | cut -c1-40)
    ah=$(git -C "$w" rev-list --count "origin/$br..HEAD" 2>/dev/null || echo NOUP)
    eq=no; [ "$rs" = "$h" ] && eq=yes
    echo "$w|$br|dirty=$d|ahead=$ah|remote==local:$eq|${h:0:8}"
  fi
done < /tmp/wtl.txt
