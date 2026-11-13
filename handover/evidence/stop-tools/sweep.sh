#!/bin/bash
# for each worktree line "path|ref": commit dirty files (filtered) on a branch, gitleaks, push
GL=/home/user/build/bin/gitleaks
TRL="Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_014pRo36xK6rXQgBKwtTHfac"
MAIN=/home/user/hadavin-sdk
while IFS='|' read w b; do
  [ "$w" = "$MAIN" ] && continue
  [ -d "$w" ] || continue
  rm -rf "$w/.git/rebase-merge" 2>/dev/null
  d=$(git -C "$w" status --porcelain | wc -l)
  name=$(echo "${w#/home/user/build/}" | tr '/ ' '--')
  h=$(git -C "$w" rev-parse HEAD)
  if [ "$b" = "DETACHED" ] || [ -z "$b" ]; then br="scratch/stop-1113-$name"; git -C "$w" checkout -q -B "$br" || { echo "$w|CHECKOUT_FAIL"; continue; }
  else br=${b#refs/heads/}; fi
  if [ "$d" -gt 0 ]; then
    git -C "$w" add -A -- . ':!*.xml' ':!*junit*' ':!*.log' ':!**/raw/**' ':!handover' 2>/dev/null
    # drop files >5MB from index
    git -C "$w" diff --cached --name-only | while read f; do s=$(stat -c %s "$w/$f" 2>/dev/null||echo 0); [ "$s" -gt 5000000 ] && git -C "$w" reset -q -- "$f"; done
    git -C "$w" -c user.name=claude -c user.email=noreply@anthropic.com commit -q -m "WIP: uncommitted worktree state at STOP 2026-11-13 ($name)" -m "$TRL" 2>/dev/null
  fi
  if git -C "$w" ls-remote --exit-code origin "refs/heads/$br" >/dev/null 2>&1 && [ "$(git -C "$w" ls-remote origin refs/heads/$br | cut -c1-40)" = "$(git -C "$w" rev-parse HEAD)" ]; then echo "$w|$br|already-pushed"; continue; fi
  n=$(git -C "$w" rev-list --count "origin/$br..HEAD" 2>/dev/null || echo 99)
  # gitleaks over commits not on any remote
  if (cd "$w" && $GL git --redact --no-banner --exit-code 1 --config /home/user/hadavin-sdk/.gitleaks.toml --log-opts="-1" . >/dev/null 2>&1); then
    if git -C "$w" push -q origin "HEAD:refs/heads/$br" 2>/tmp/pusherr; then echo "$w|$br|pushed"; else echo "$w|$br|PUSH_FAIL $(head -c 120 /tmp/pusherr)"; fi
  else echo "$w|$br|GITLEAKS_FAIL_NOT_PUSHED"; fi
done < /tmp/wtl.txt
