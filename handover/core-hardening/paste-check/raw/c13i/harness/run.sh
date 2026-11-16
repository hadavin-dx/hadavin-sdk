#!/bin/bash
# usage: run.sh <vars-file> <block-id|file>...  : runs in unshare mount ns with /z bound; each block in a fresh bash, same header
W=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev13i
exec unshare -m bash -c '
mkdir -p /z; mount --bind '$W'/hb /z || exit 99
V=$1; shift
for b in "$@"; do
  case $b in b[0-9][0-9]) f='$W'/blocks/$b.sh;; *) f=$b;; esac
  echo "##### $b"
  PATH=/z/bin:${PATHX:-$PATH} bash -c "set +e; HB=/z; $(cat $V)
$(sed -n "2,\$p" '$W'/blocks/b01.sh | sed "\$d")
$(cat $f)"
  echo "##### $b exit=$?"
done' _ "$@"
