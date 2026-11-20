#!/usr/bin/env bash
# Rewrites handover/core-b/STATUS-BOARD.md from board-head.env + board-body.md, adds live CAPACITY/DISK, commits, rebases, pushes.
# One run per call; no loop. Only touches handover/core-b/ on branch cloud/core-b.
set -u
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)" || exit 1
D=handover/core-b
[ "$(git rev-parse --abbrev-ref HEAD)" = "cloud/core-b" ] || { echo "not on cloud/core-b"; exit 1; }
GD=$(git rev-parse --git-dir)
for f in CHERRY_PICK_HEAD MERGE_HEAD REBASE_HEAD; do [ -e "$GD/$f" ] && { echo "refusing to commit a board: $f is present (finish or abort it first)"; exit 1; }; done
git diff --name-only --diff-filter=U | grep -q . && { echo "refusing: unmerged files"; exit 1; }
. "$D/board-head.env"
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ); IST=$(TZ=Asia/Kolkata date '+%H:%M IST')
BOOT=$(cut -c1-8 /proc/sys/kernel/random/boot_id)
CORES=$(nproc); LOAD=$(cut -d' ' -f1 /proc/loadavg)
MEM=$(free -g | awk 'NR==2{print $3"/"$2}')
DFREE=$(df -h / | awk 'NR==2{print $4" free, "$5" used"}')
WT=$(du -sh /tmp/core-b-wt 2>/dev/null | cut -f1); WT=${WT:-0}
PREV=$(git log -1 --format=%cd --date=format-local:%Y-%m-%dT%H:%M:%SZ origin/cloud/core-b 2>/dev/null)
{
echo "UPDATED_UTC: $NOW"
echo "SESSION: core-b"
echo "ORDER: $ORDER"
echo "STATE: $STATE"
echo "BOOT_ID: $BOOT"
echo "ITEMS_TOTAL: $ITEMS_TOTAL"
echo "ITEMS_OPEN: $ITEMS_OPEN"
echo "PERCENT: $PERCENT"
echo "AGENTS_RUNNING: $AGENTS_RUNNING"
echo "CAPACITY: load $LOAD of $CORES cores, mem $MEM GB, disk $DFREE, agents light $LIGHT heavy $HEAVY"
echo "DISK: / $DFREE; worktrees /tmp/core-b-wt $WT"
echo "SESSION_RESTARTS: $SESSION_RESTARTS"
echo "CONTAINER_RESTARTS: $CONTAINER_RESTARTS"
echo "INTERRUPTED: $INTERRUPTED"
echo "FAILED: $FAILED"
echo "NEXT: $NEXT"
echo "PUSHED_UTC: ${PREV:-none} (previous push; this board is pushed right after writing)"
echo "IST: $IST"
echo
cat "$D/board-body.md"
} > "$D/STATUS-BOARD.md"
git add "$D" && git commit -q -m "board $NOW

Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_014pRo36tfL8utoaXvQYNzGy"
for i in 1 2 3; do
  git pull -q --rebase origin cloud/core-b && git push -q origin cloud/core-b && { echo "pushed $NOW $(git rev-parse --short HEAD)"; exit 0; }
  echo "push try $i failed"
done
exit 2
