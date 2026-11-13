#!/bin/bash
# usage: fs_cases.sh WORKTREE LOGFILE ; runs each case with hard timeout 8, PYTHONPATH=worktree, cwd=scratch/fs/cwd, TMPDIR=scratch/fs/tmp
W=$1; L=$2; S=/home/user/hadavin-sdk/handover/demo3/scratch/fs
: > $L
case_(){ # label then args
  lab=$1; shift
  echo "##### [$(basename $W)] $lab :: args: $*" >> $L
  ( cd $S/cwd && env PYTHONPATH=$W TMPDIR=$S/tmp timeout 8 /usr/bin/python3.12 -m demo_only.fake_model_server --port 0 "$@" >> $L 2>&1; echo "exit $?" >> $L )
}
O=$S/outside
case_ "key abs outside"            --key-file $O/outside.key
case_ "key ../ outside"            --key-file ../outside/outside.key
case_ "key sub/../../ outside"     --key-file sub/../../outside/outside.key
case_ "key symlink->outside (cwd)" --key-file sym_key
case_ "key symlink->outside (tmp)" --key-file $S/tmp/sym_key_tmp
case_ "key via dir symlink"        --key-file dirlink/k.key
case_ "key via outlink/outside.key" --key-file outlink/outside/outside.key
case_ "key inside cwd (ok)"        --key-file in.key
case_ "key inside tmp (ok)"        --key-file $S/tmp/tmp.key
case_ "key sub/../in.key (ok)"     --key-file sub/../in.key
case_ "key empty file"             --key-file empty.key
case_ "key a directory"            --key-file sub
case_ "key nonexistent"            --key-file nope.key
case_ "key /etc/hostname"          --key-file /etc/hostname
case_ "key /proc/self/environ"     --key-file /proc/self/environ
case_ "call-log abs outside new"   --call-log $O/new.jsonl
case_ "call-log ../ outside new"   --call-log ../outside/new.jsonl
case_ "call-log symlink->outside existing" --call-log sym_log
case_ "call-log dangling symlink->outside" --call-log dangling_log
case_ "call-log via dir symlink new" --call-log outlink/new2.jsonl
case_ "call-log inside new (ok)"   --call-log log1.jsonl
case_ "call-log tmp new (ok)"      --call-log $S/tmp/log2.jsonl
case_ "call-log bad name (space)"  --call-log "my log.jsonl"
case_ "call-log device name nul.txt" --call-log nul.txt
case_ "call-log trailing dot"      --call-log "log."
case_ "call-log control char"      --call-log $'a\x01b.jsonl'
case_ "call-log /etc/passwd"       --call-log /etc/passwd
case_ "call-log missing parent"    --call-log nodir/x.jsonl
case_ "control abs outside"        --control-file $O/outmode.txt
case_ "control ../ outside new"    --control-file ../outside/ctl.txt
case_ "control symlink->outside"   --control-file sym_ctl
case_ "control via dir symlink"    --control-file outlink/ctl3.txt
case_ "control inside (ok)"        --control-file ctl1.txt
case_ "control tmp (ok)"           --control-file $S/tmp/ctl2.txt
case_ "control UNC-like \\\\h\\s\\x" --control-file '\\h\s\x'
case_ "control //host/share/x"     --control-file //host/share/x
case_ "control LEAD_DESK_PATH_ROOTS=outside abs" --control-file $O/outmode.txt
